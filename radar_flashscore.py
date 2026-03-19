from selenium import webdriver
from selenium.webdriver.common.by import By
import time

print("INICIANDO RADAR...")

url = "https://www.flashscore.co/futbol/"

driver = webdriver.Chrome()

driver.get(url)

time.sleep(5)

partidos = driver.find_elements(By.CLASS_NAME, "event__match")

print("\nRADAR PARTIDOS FILTRADOS\n")

bloquear = [
   "SRF",
    "SUB",
    "U20",
    "U21",
    "U23",
    "WOMEN",
    "JPN",
    "TOCHIGI",
    "BLAUBLITZ"
]


for partido in partidos:

    texto = partido.text.upper()

    if any(x in texto for x in bloquear):
        continue

    if "FINALIZADO" in texto:
        continue

    if ":" not in texto:
        continue

    try:
        link = partido.find_element(By.TAG_NAME, "a").get_attribute("href")

        print(texto)
        print("LINK:", link)
        print("-------------")

    except:
        pass

driver.quit()