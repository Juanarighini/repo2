import time
import requests
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURACIÓN ---
INSTANCE_ID = "instance172179"
TOKEN = "wyedawcvk4ebpjqo"
CHAT_ID = "120363425322589609@g.us"

USER_EMAIL = "TU_EMAIL"
USER_PASS = "TU_PASS"

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
        wait.until(EC.presence_of_element_by_id("loginMail")).send_keys(USER_EMAIL)
        driver.find_element(By.ID, "loginPass").send_keys(USER_PASS)
        login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]")
        driver.execute_script("arguments[0].click();", login_btn)
        
        # 2. Esperar Dashboard y abrir menú Fuel
        time.sleep(8) 
        # Selector basado en tu imagen: div con clase consumable-wrapper que abre commodities
        fuel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'consumable-wrapper')]")))
        driver.execute_script("arguments[0].click();", fuel_btn)
        
        # 3. Leer CO2 (abre por defecto según tu captura)
        time.sleep(3)
        co2 = wait.until(EC.presence_of_element_by_xpath("//span[contains(@class, 'text-success') and contains(@class, 'fw-bold')]")).text
        
        # 4. Cambiar a Oil (Usando el ID que aparece en tu inspector)
        # ID: header-power-exchange
        oil_tab = driver.find_element(By.ID, "header-power-exchange")
        driver.execute_script("arguments[0].click();", oil_tab)
        time.sleep(2)
        
        # 5. Leer Oil
        oil = driver.find_element(By.XPATH, "//div[contains(text(), 'Current price')]/following-sibling::span[contains(@class, 'fw-bold')]").text
        
        return f"⚡ *ENERGY MANAGER REPORT* ⚡\n\n🌱 *CO2:* {co2} per 1000\n🛢️ *Oil:* {oil}"

    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        driver.quit()

def send_whatsapp(text):
    url = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"
    payload = {"token": TOKEN, "to": CHAT_ID, "body": text, "priority": 10}
    requests.post(url, data=urllib.parse.urlencode(payload), headers={'content-type': 'application/x-www-form-urlencoded'})

if __name__ == "__main__":
    resultado = get_prices()
    send_whatsapp(resultado)