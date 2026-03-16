from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

link = input("Pega el link del partido: ")

service = Service("chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.get(link)

wait = WebDriverWait(driver, 20)

# detectar equipos
equipos = driver.find_elements(By.CLASS_NAME, "participant__participantName")

nombres = []

for e in equipos:
    nombre = e.text.strip()

    if nombre != "" and nombre not in nombres:
        nombres.append(nombre)

local = nombres[0]
visitante = nombres[1]

print("\nPARTIDO DETECTADO\n")
print("LOCAL:", local)
print("VISITANTE:", visitante)

# abrir pestaña H2H
try:
    h2h = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'H2H')]"))
    )
    h2h.click()

    print("\nPestaña H2H abierta correctamente")

except:
    print("\nNo se pudo abrir H2H")

# esperar a que carguen resultados
try:
    wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class,'h2h')]"))
    )
except:
    pass

time.sleep(3)

# leer toda la página
html = driver.page_source

# buscar marcadores tipo 2-1
marcadores = re.findall(r'\b\d{1,2}-\d{1,2}\b', html)

# eliminar duplicados
marcadores = list(dict.fromkeys(marcadores))

# tomar solo los primeros 5
marcadores = marcadores[:5]

goles_totales = 0
btts = 0
over25 = 0
partidos = 0

for marcador in marcadores:

    g1, g2 = marcador.split("-")

    g1 = int(g1)
    g2 = int(g2)

    total = g1 + g2

    goles_totales += total
    partidos += 1

    if g1 > 0 and g2 > 0:
        btts += 1

    if total > 2:
        over25 += 1

if partidos > 0:

    print("\nANALISIS H2H\n")

    print("Marcadores detectados:", marcadores)
    print("Partidos analizados:", partidos)
    print("Promedio goles:", round(goles_totales / partidos,2))
    print("BTTS %:", round((btts/partidos)*100,1))
    print("OVER 2.5 %:", round((over25/partidos)*100,1))

else:

    print("\nNo se encontraron marcadores H2H")

driver.quit()