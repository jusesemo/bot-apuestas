from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time

print("🚀 INICIANDO RADAR PROFESIONAL...")

# ==============================
# INPUT USUARIO
# ==============================
dias = int(input("📅 Ingresa días (ej: 2 = adelante, -2 = atrás): "))

url = "https://www.flashscore.co/futbol/"
driver = webdriver.Chrome() 
driver.maximize_window()
driver.get(url)

time.sleep(5)

# ==============================
# FUNCIONES DE APOYO
# ==============================
def obtener_primer_partido(driver):
    try:
        partidos = driver.find_elements(By.CLASS_NAME, "event__match")
        if partidos:
            return partidos[0].text
    except:
        pass
    return ""

def mover_dias(driver, dias):
    if dias == 0: return
    xpath = "//button[@data-day-picker-arrow='next']" if dias > 0 else "//button[@data-day-picker-arrow='prev']"
    direccion = "➡️" if dias > 0 else "⬅️"
    
    print(f"📅 Moviendo {abs(dias)} días {direccion}")

    for i in range(abs(dias)):
        try:
            antes = obtener_primer_partido(driver)
            boton = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", boton)

            # Esperar cambio real de contenido
            for _ in range(10):
                time.sleep(1)
                despues = obtener_primer_partido(driver)
                if despues != antes:
                    break
        except Exception as e:
            print(" Error al cambiar de día:", e)

from selenium.webdriver.common.by import By

def obtener_partidos_de_liga(liga):
    partidos = []
    elemento = liga

    while True:
        try:
            elemento = elemento.find_element(By.XPATH, "following-sibling::*[1]")
            
            clases = elemento.get_attribute("class")

            # 🚨 Si encontramos otra liga → paramos
            if "headerLeague__wrapper" in clases:
                break

            # ✅ Si es partido → lo guardamos
            if "event__match" in clases:
                partidos.append(elemento)

        except:
            break

    return partidos
# ==============================
# SISTEMA VIP (EQUIPOS ESPECIALES)
# ==============================
equipos_vip = [
    "PSG",    
    "ROMA", 
    "JUNIOR"   
]

def es_equipo_vip(texto):
    texto = texto.upper()
    return any(eq in texto for eq in equipos_vip)

# ==============================
# EJECUCIÓN
# ==============================
mover_dias(driver, dias)
time.sleep(3)

partidos = driver.find_elements(By.CLASS_NAME, "event__match")
links_para_txt = [] #  LISTA VACÍA PARA ACUMULAR LINKS

bloquear = ["SRF", "SUB", "U20", "U21", "U23", "WOMEN", "JPN", "TOCHIGI", "BLAUBLITZ"]

print("\n--- FILTRANDO PARTIDOS ---")

ligas = driver.find_elements(By.CLASS_NAME, "headerLeague__wrapper")

ligas_under = ["COLOMBIA", "ESPAÑA", "ITALIA", "ARGENTINA","FRANCIA"]
ligas_over = ["ALEMANIA", "PAÍSES BAJOS","BÉLGICA"]
ligas_btts = ["INGLATERRA", "ESTADOS UNIDOS"]

for liga in ligas:
    try:
        # 📌 SACAR INFO DE LA LIGA
        body = liga.find_element(By.CLASS_NAME, "headerLeague__body")
        
        liga_nombre = body.find_element(By.CLASS_NAME, "headerLeague__title-text").text.upper()
        pais = body.find_element(By.CLASS_NAME, "headerLeague__category-text").text.upper()

        print(f"DEBUG → {pais} | {liga_nombre}")

    except:
        continue
    
    # 🎯 FILTRO DE LIGAS (AQUÍ ESTÁ EL PODER REAL)
    if not (
        (pais == "COLOMBIA" and "PRIMERA A" in liga_nombre) or
        (pais == "ESPAÑA" and "LALIGA" in liga_nombre) or
        (pais == "ALEMANIA" and "BUNDESLIGA" in liga_nombre) or
        (pais == "ARGENTINA" and "LIGA PROFESIONAL" in liga_nombre) or 
        (pais == "INGLATERRA" and "PREMIER LEAGUE" in liga_nombre) or
        (pais == "ITALIA" and "SERIE A" in liga_nombre) or 
        (pais == "FRANCIA" and "LIGUE 1" in liga_nombre) or 
        (pais == "PAÍSES BAJOS" and "KEUKEN KAMPIOEN DIVISIE" in liga_nombre) or 
        (pais == "BÉLGICA" and "JUPILER PRO LEAGUE" in liga_nombre) 
    ):
        continue 
    
     # 🎯 TIPO DE LIGA
    if pais in ligas_under:
        tipo_liga = "UNDER"
    elif pais in ligas_over:
        tipo_liga = "OVER"
    elif pais in ligas_btts:
        tipo_liga = "BTTS"
    else:
        continue

    print(f"\n🌍 {pais} | 🏆 {liga_nombre}")

    # 📌 BAJAR A LOS PARTIDOS DE ESA LIGA
    partidos = obtener_partidos_de_liga(liga)

    for partido in partidos:
        texto = partido.text.upper()

        if len(texto) < 25:
            continue

        if len(texto.splitlines()) < 3:
            continue

        equipos = texto.splitlines()
        
        if any(x in texto for x in ["U20","U21","U23","WOMEN","FEMENINA","RESERVA","SUB","2. BUNDESLIGA"]):
            continue

        if len(equipos[1]) < 4 or len(equipos[2]) < 4:
            continue

        if "FINALIZADO" in texto:
            continue

        if ":" not in texto:
            continue

        try:
            id_partido = partido.get_attribute("id").split("_")[-1]
            link = f"https://www.flashscore.co/partido/{id_partido}/#/h2h/overall"

            links_para_txt.append(link)

            print(f"✅ {equipos[1]} vs {equipos[2]}")
            print(f"🔗 {link}")
            print(f"📊 {tipo_liga}")
            print("-" * 30)

        except:
            continue

# ==============================
# GUARDADO FINAL (FUERA DEL BUCLE)
# ==============================
if links_para_txt:
    with open("links_radar.txt", "w") as f:
        for l in links_para_txt:
            f.write(l + "\n")
    
    print(f"\n[DONE] {len(links_para_txt)} links guardados en 'links_radar.txt'")
    print("👉 Ahora puedes ejecutar: analizar_partido_premium.py")
else:
    print("\n⚠️ No se encontraron partidos válidos con esos filtros.")

driver.quit()