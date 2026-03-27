from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def extraer_datos(link):

    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    driver.maximize_window()
    wait = WebDriverWait(driver, 20)

    driver.get(link)

    # cookies
    try:
        aceptar = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        aceptar.click()
        time.sleep(2)
    except:
        pass

    # equipos
    wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "participant__participantName"))
    )

    equipos = driver.find_elements(By.CLASS_NAME, "participant__participantName")

    nombres = []
    for e in equipos:
        nombre = e.text.strip()
        if nombre and nombre not in nombres:
            nombres.append(nombre)

    local = nombres[0]
    visitante = nombres[1]

    # H2H
    h2h = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'H2H')]"))
    )
    h2h.click()
    time.sleep(2)

    # GENERAL
    try:
        general = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'GENERAL')]"))
        )
        general.click()
        time.sleep(3)
    except:
        pass

    wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "h2h__row"))
    )

    rows = driver.find_elements(By.CLASS_NAME, "h2h__row")

    marcadores = []

    for row in rows:
        try:
            resultado = row.find_element(By.CLASS_NAME, "h2h__result")
            goles = resultado.find_elements(By.TAG_NAME, "span")

            if len(goles) == 2:
                g1 = goles[0].text.strip()
                g2 = goles[1].text.strip()

                if g1.isdigit() and g2.isdigit():
                    marcadores.append(f"{g1}-{g2}")
        except:
            pass

    driver.quit()

    return {
        "local": local,
        "visitante": visitante,
        "h2h": marcadores[:5],
        "local_form": marcadores[5:10],
        "visitante_form": marcadores[10:15]
    }