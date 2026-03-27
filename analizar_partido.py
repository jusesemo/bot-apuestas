from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time


# ==============================
# FUNCION ANALISIS MARCADORES
# ==============================

def analizar_marcadores(lista):

    goles_totales = 0
    btts = 0
    over25 = 0
    partidos = 0

    for marcador in lista:
        try:
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

        except:
            pass

    if partidos == 0:
        return None

    return {
        "promedio": round(goles_totales / partidos, 2),
        "btts": round((btts / partidos) * 100, 1),
        "over25": round((over25 / partidos) * 100, 1)
    }

# ==============================
# CALCULAR PROBABILIDAD FINAL
# ==============================

def calcular_probabilidad(h2h, local, visitante):

    if not h2h or not local or not visitante:
        return None

    btts = (h2h["btts"] + local["btts"] + visitante["btts"]) / 3
    over25 = (h2h["over25"] + local["over25"] + visitante["over25"]) / 3

    return {
        "btts": round(btts, 1),
        "over25": round(over25, 1)
    }


# ==============================
# CALCULAR VALUE BET
# ==============================

def calcular_value(prob, cuota):

    prob_real = prob / 100
    prob_casa = 1 / cuota

    value = prob_real - prob_casa

    return round(value * 100, 2)  # en %

# ==============================
# INICIO DRIVER
# ==============================

link = input("Pega el link del partido: ")

service = Service("chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.maximize_window()

wait = WebDriverWait(driver, 20)

driver.get(link)

# ==============================
# ACEPTAR COOKIES (CLAVE)
# ==============================

try:
    aceptar = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    aceptar.click()
    print("Cookies aceptadas")
    time.sleep(2)

except:
    print("No apareció popup de cookies")
# ==============================
# DETECTAR EQUIPOS
# ==============================

wait.until(
    EC.presence_of_element_located((By.CLASS_NAME, "participant__participantName"))
)

equipos = driver.find_elements(By.CLASS_NAME, "participant__participantName")

nombres = []

for e in equipos:
    nombre = e.text.strip()
    if nombre != "" and nombre not in nombres:
        nombres.append(nombre)

local = nombres[0]
visitante = nombres[1]

print("\n==========================")
print("PARTIDO DETECTADO")
print("==========================")
print("LOCAL:", local)
print("VISITANTE:", visitante)


# ==============================
# ABRIR H2H
# ==============================

h2h = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'H2H')]"))
)

h2h.click()

print("\nPestaña H2H abierta")


# ==============================
# ESPERAR CONTENEDOR H2H
# ==============================

wait.until(
    EC.presence_of_element_located((By.CLASS_NAME, "tabContent__h2h"))
)

time.sleep(3)


# ==============================
# ACTIVAR CARGA (HOVER + SCROLL INTERNO)
# ==============================

contenedor = driver.find_element(By.CLASS_NAME, "tabContent__h2h")

# mover mouse (activa render)
actions = ActionChains(driver)
actions.move_to_element(contenedor).perform()

time.sleep(2)

# scroll dentro del contenedor
for i in range(10):
    driver.execute_script("arguments[0].scrollTop += 400", contenedor)
    time.sleep(1)

# ==============================
# EXTRAER MARCADORES (FORMA REAL)
# ==============================

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
                marcador = f"{g1}-{g2}"
                marcadores.append(marcador)

    except:
        pass

print("\nMarcadores encontrados:", marcadores)


# ==============================
# SEPARAR BLOQUES
# ==============================

h2h_scores = marcadores[:5]
local_scores = marcadores[5:10]
visitante_scores = marcadores[10:15]


# ==============================
# ANALISIS H2H
# ==============================

print("\n==========================")
print("ANALISIS H2H")
print("==========================")

h2h_stats = analizar_marcadores(h2h_scores)

if h2h_stats:
    print("Promedio goles:", h2h_stats["promedio"])
    print("BTTS %:", h2h_stats["btts"])
    print("OVER 2.5 %:", h2h_stats["over25"])
else:
    print("No se encontraron datos H2H")


# ==============================
# FORMA RECIENTE
# ==============================

print("\n==========================")
print("FORMA RECIENTE")
print("==========================")

print("\nUltimos 5 LOCAL:", local_scores)

local_stats = analizar_marcadores(local_scores)

if local_stats:
    print(local)
    print("Promedio goles:", local_stats["promedio"])
    print("BTTS %:", local_stats["btts"])
    print("OVER 2.5 %:", local_stats["over25"])


print("\nUltimos 5 VISITANTE:", visitante_scores)

visitante_stats = analizar_marcadores(visitante_scores)

if visitante_stats:
    print(visitante)
    print("Promedio goles:", visitante_stats["promedio"])
    print("BTTS %:", visitante_stats["btts"])
    print("OVER 2.5 %:", visitante_stats["over25"])

# ==============================
# CALCULO FINAL
# ==============================

print("\n==========================")
print("MODELO DE APUESTA")
print("==========================")

modelo = calcular_probabilidad(h2h_stats, local_stats, visitante_stats)

if modelo:

    print("Probabilidad BTTS:", modelo["btts"], "%")
    print("Probabilidad Over 2.5:", modelo["over25"], "%")

    # 👇 AQUÍ METES CUOTAS MANUAL (por ahora)
    cuota_btts = 1.80
    cuota_over = 1.90

    value_btts = calcular_value(modelo["btts"], cuota_btts)
    value_over = calcular_value(modelo["over25"], cuota_over)

    print("\n--- VALUE BET ---")

    print("BTTS Value:", value_btts, "%")
    print("Over 2.5 Value:", value_over, "%")

    if value_btts > 0:
        print("👉 BTTS ES VALUE BET")

    if value_over > 0:
        print("👉 OVER 2.5 ES VALUE BET")

else:
    print("No se pudo calcular modelo")

print("Probabilidad BTTS:", modelo["btts"], "%")
print("Probabilidad Over 2.5:", modelo["over25"], "%")

print("\n--- VALUE BET ---")

print("BTTS Value:", value_btts, "%")
print("Over 2.5 Value:", value_over, "%")


print("\n==========================")
print("DECISION FINAL")
print("==========================")

if value_btts > 5:
    print("🔥 APOSTAR BTTS")

if value_over > 5:
    print("🔥 APOSTAR OVER 2.5")

if value_btts <= 5 and value_over <= 5:
    print("❌ NO APOSTAR ESTE PARTIDO")
# ==============================
# CERRAR DRIVER
# ==============================

driver.quit()