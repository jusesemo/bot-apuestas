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
            print("⚠️ Error al cambiar de día:", e)

# ==============================
# EJECUCIÓN
# ==============================
mover_dias(driver, dias)
time.sleep(3)

partidos = driver.find_elements(By.CLASS_NAME, "event__match")
links_para_txt = [] # 🔥 LISTA VACÍA PARA ACUMULAR LINKS

bloquear = ["SRF", "SUB", "U20", "U21", "U23", "WOMEN", "JPN", "TOCHIGI", "BLAUBLITZ"]

print("\n--- FILTRANDO PARTIDOS ---")

for partido in partidos:
    texto = partido.text.upper()

    # Filtros de seguridad
    if any(x in texto for x in bloquear): continue
    if "FINALIZADO" in texto: continue
    if ":" not in texto: continue # Solo partidos que no han empezado

    try:
        # Extraer el ID del partido para construir el link limpio
        # Flashscore usa IDs en los elementos, es más seguro que buscar el <a>
        id_partido = partido.get_attribute("id").split("_")[-1]
        link_limpio = f"https://www.flashscore.co/partido/{id_partido}/#/h2h/overall"
        
        links_para_txt.append(link_limpio) # 🚩 Guardamos en la lista
        
        print(f"✅ Detectado: {texto.splitlines()[1]} vs {texto.splitlines()[2]}")
        print(f"🔗 Link: {link_limpio}")
        print("-" * 30)

    except Exception as e:
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