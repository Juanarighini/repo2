import os
import time
import requests
import urllib.parse
import threading
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# --- CONTROL DE CONCURRENCIA ---
# Este candado evita que dos hilos modifiquen la variable 'ejecutando' al mismo tiempo
lock_ejecucion = threading.Lock()
ejecutando = False

# --- CONFIGURACIÓN DESDE RENDER ---
INSTANCE_ID = os.getenv('INSTANCE_ID')
TOKEN = os.getenv('ULTRAMSG_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASS = os.getenv('USER_PASS')

def get_prices():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/google-chrome"
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 25)
    
    try:
        driver.get("https://energymanagergame.com/weblogin/")
        
        # Login
        wait.until(EC.presence_of_element_located((By.ID, "loginMail"))).send_keys(USER_EMAIL)
        driver.find_element(By.ID, "loginPass").send_keys(USER_PASS)
        
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signin-form"]/div[5]/div/input')))
        driver.execute_script("arguments[0].click();", login_btn)
        
        time.sleep(12) 
        
        # Abrir Fuel
        fuel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div[3]/div/div[2]/div')))
        driver.execute_script("arguments[0].click();", fuel_btn)
        
        time.sleep(4)
        # Leer CO2
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="popup-content"]/div[1]/div/div/div/div[4]/button')))
        co2 = driver.find_element(By.XPATH, "//span[contains(@class, 'text-success') and contains(@class, 'fw-bold')]").text
        
        # Cambiar a OIL
        oil_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-power-exchange"]')))
        driver.execute_script("arguments[0].click();", oil_tab)
        time.sleep(3)
        
        # Leer OIL
        oil = driver.find_element(By.XPATH, "//div[contains(text(), 'Current price')]/following-sibling::span[contains(@class, 'fw-bold')]").text
        
        return f"Precio Petróleo={oil} | Precio CO2={co2}"

    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        driver.quit()

def send_whatsapp(text):
    if not INSTANCE_ID or not TOKEN: return
    url = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"
    payload = {"token": TOKEN, "to": CHAT_ID, "body": text, "priority": 10}
    requests.post(url, data=urllib.parse.urlencode(payload), headers={'content-type': 'application/x-www-form-urlencoded'})

def run_bot_task():
    global ejecutando
    
    # Intentamos marcar como ejecutando
    with lock_ejecucion:
        if ejecutando:
            print("Bot ya en curso. Ignorando petición duplicada.")
            return
        ejecutando = True
    
    try:
        mensaje = get_prices()
        send_whatsapp(mensaje)
    finally:
        # Esperamos un minuto antes de permitir otra ejecución para evitar bucles de reintento
        time.sleep(60)
        with lock_ejecucion:
            ejecutando = False

@app.route('/')
def webhook():
    global ejecutando
    
    # Verificación rápida antes de lanzar el hilo
    if ejecutando:
        return "El bot ya está procesando una solicitud. Por favor, espera.", 429
    
    # Lanzamos el hilo y respondemos inmediatamente al navegador/cron-job
    threading.Thread(target=run_bot_task).start()
    return "Solicitud recibida. El bot está trabajando en segundo plano.", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
