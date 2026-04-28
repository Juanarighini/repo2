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
    wait = WebDriverWait(driver, 25) # Un poco más de tiempo por si el servidor está lento
    
    try:
        # 1. Login
        driver.get("https://energymanagergame.com/weblogin/")
        
        # Cargar credenciales
        wait.until(EC.presence_of_element_located((By.ID, "loginMail"))).send_keys(USER_EMAIL)
        driver.find_element(By.ID, "loginPass").send_keys(USER_PASS)
        
        # CLICK LOGIN (XPath proporcionado)
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signin-form"]/div[5]/div/input')))
        driver.execute_script("arguments[0].click();", login_btn)
        
        # 2. Esperar Dashboard y abrir menú Fuel
        time.sleep(12) 
        
        # CLICK TRIGGER FUEL (XPath proporcionado)
        fuel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div[3]/div/div[2]/div')))
        driver.execute_script("arguments[0].click();", fuel_btn)
        
        # 3. Leer CO2 (Abre por defecto)
        time.sleep(4)
        # XPath de CO2 proporcionado para asegurar que la ventana cargó
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="popup-content"]/div[1]/div/div/div/div[4]/button')))
        
        # Buscamos el valor numérico (usando el selector de éxito que ya funcionaba)
        co2 = driver.find_element(By.XPATH, "//span[contains(@class, 'text-success') and contains(@class, 'fw-bold')]").text
        
        # 4. Cambiar a OIL
        # CLICK PESTAÑA OIL (XPath proporcionado)
        oil_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-power-exchange"]')))
        driver.execute_script("arguments[0].click();", oil_tab)
        time.sleep(3)
        
        # 5. Leer OIL
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
    mensaje = get_prices()
    send_whatsapp(mensaje)

@app.route('/')
def webhook():
    threading.Thread(target=run_bot_task).start()
    return "Ejecutando bot con XPaths verificados...", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
