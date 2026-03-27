from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

def obtener_partidos():

    url = "https://www.flashscore.co/futbol/"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get(url)
    time.sleep(5)

    partidos = driver.find_elements(By.CLASS_NAME, "event__match")

    lista = []

    for partido in partidos:

        texto = partido.text.upper()

        if "FINALIZADO" in texto:
            continue

        if ":" not in texto:
            continue

        try:
            link = partido.find_element(By.TAG_NAME, "a").get_attribute("href")

            lista.append({
                "nombre": texto,
                "link": link
            })

        except:
            pass

    driver.quit()

    return lista