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
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. Login
        driver.get("https://energymanagergame.com/weblogin/")
        
        # CORRECCIÓN 1: presence_of_element_located + tupla (By.ID, "...")
        wait.until(EC.presence_of_element_located((By.ID, "loginMail"))).send_keys(USER_EMAIL)
        driver.find_element(By.ID, "loginPass").send_keys(USER_PASS)
        
        login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]")
        driver.execute_script("arguments[0].click();", login_btn)
        
        # 2. Esperar Dashboard y abrir menú Fuel
        time.sleep(10) 
        
        # CORRECCIÓN 2: element_to_be_clickable + tupla (By.XPATH, "...")
        fuel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'consumable-wrapper')]")))
        driver.execute_script("arguments[0].click();", fuel_btn)
        
        # 3. Leer CO2
        time.sleep(3)
        # CORRECCIÓN 3: presence_of_element_located + tupla (By.XPATH, "...")
        co2 = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'text-success') and contains(@class, 'fw-bold')]"))).text
        
        # 4. Cambiar a Oil
        oil_tab = driver.find_element(By.ID, "header-power-exchange")
        driver.execute_script("arguments[0].click();", oil_tab)
        time.sleep(2)
        
        # 5. Leer Oil
        oil = driver.find_element(By.XPATH, "//div[contains(text(), 'Current price')]/following-sibling::span[contains(@class, 'fw-bold')]").text
        
        return f"Precio Petróleo={oil} | Precio CO2={co2}"

    except Exception as e:
        # Esto te ayudará a ver en qué línea exacta falla si vuelve a pasar
        return f"❌ Error: {str(e)}"
    finally:
        driver.quit()
        
def send_whatsapp(text):
    url = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"
    payload = {"token": TOKEN, "to": CHAT_ID, "body": text, "priority": 10}
    requests.post(url, data=urllib.parse.urlencode(payload), headers={'content-type': 'application/x-www-form-urlencoded'})

def run_bot_task():
    mensaje = get_prices()
    send_whatsapp(mensaje)

@app.route('/')
def webhook():
    # Iniciamos el bot en un hilo separado para no bloquear la respuesta a Cron-job
    threading.Thread(target=run_bot_task).start()
    return "Ejecutando bot...", 200

if __name__ == "__main__":
    # Render asigna un puerto dinámico
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
