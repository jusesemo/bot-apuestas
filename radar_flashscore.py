from selenium import webdriver
from selenium.webdriver.common.by import By
import time

print("INICIANDO RADAR...")

# ==============================
# INPUT USUARIO
# ==============================

dias = int(input("📅 Ingresa días (ej: 2 = adelante, -2 = atrás): "))

url = "https://www.flashscore.co/futbol/"
driver = webdriver.Chrome()
driver.get(url)

time.sleep(5)

# ==============================
# FUNCIÓN OBTENER PRIMER PARTIDO (para detectar cambio)
# ==============================

def obtener_primer_partido(driver):
    try:
        partidos = driver.find_elements(By.CLASS_NAME, "event__match")
        if partidos:
            return partidos[0].text
    except:
        pass
    return ""

# ==============================
# FUNCIÓN CLICK DÍAS (SIN REFRESH)
# ==============================

def mover_dias(driver, dias):

    if dias == 0:
        return

    if dias > 0:
        xpath = "//button[@data-day-picker-arrow='next']"
        direccion = "➡️"
    else:
        xpath = "//button[@data-day-picker-arrow='prev']"
        direccion = "⬅️"

    print(f"📅 Moviendo {abs(dias)} días {direccion}")

    for i in range(abs(dias)):
        try:
            antes = obtener_primer_partido(driver)

            boton = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", boton)

            # 🔥 esperar a que cambie el contenido REAL
            for _ in range(10):
                time.sleep(1)
                despues = obtener_primer_partido(driver)
                if despues != antes:
                    break

        except Exception as e:
            print("⚠️ Error al hacer click:", e)

# ==============================
# EJECUTAR CAMBIO DE DÍA
# ==============================

mover_dias(driver, dias)

# ==============================
# EXTRAER PARTIDOS (TU CÓDIGO)
# ==============================

time.sleep(3)

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

contador = 0

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

        # 🟡 LIGA (NUEVO)
        liga = ""
        try:
            liga = partido.find_element(
                By.XPATH,
                "./ancestor::div[contains(@class,'sportName')]//div[contains(@class,'header')]"
            ).text.upper()
        except:
            pass

        print("🏆 LIGA:", liga)
        print(texto)
        print("LINK:", link)
        print("-------------")

        contador += 1

    except:
        pass
# ==============================
# VALIDACIÓN
# ==============================

if contador == 0:
    print("⚠️ No hay partidos para ese día")

driver.quit()

