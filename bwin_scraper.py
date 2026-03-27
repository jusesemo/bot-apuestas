from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ==============================
# INPUT LINK
# ==============================

link = input("Pega el link de Bwin: ")

service = Service("chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.maximize_window()
driver.get(link)

wait = WebDriverWait(driver, 15)

# ==============================
# COOKIES
# ==============================

try:
    boton_cookies = wait.until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    boton_cookies.click()
    print("✅ Cookies aceptadas")
except:
    print("⚠️ No apareció cookies")

# ==============================
# CERRAR MODAL
# ==============================

try:
    botones = driver.find_elements(By.XPATH, "//button")

    for b in botones:
        try:
            if "cerrar" in b.text.lower() or b.get_attribute("aria-label") == "Cerrar":
                b.click()
                print("✅ Modal cerrado")
                break
        except:
            pass
except:
    pass

time.sleep(2)

# ==============================
# IR A "TIEMPO REGLAMENTARIO"
# ==============================

try:
    tab_tiempo = wait.until(
        EC.element_to_be_clickable((
            By.XPATH, "//button[@role='tab']//span[contains(text(),'Tiempo reglamentario')]"
        ))
    )
    
    driver.execute_script("arguments[0].click();", tab_tiempo)
    print("✅ Tiempo reglamentario seleccionado")

except:
    print("❌ No se pudo seleccionar 'Tiempo reglamentario'")

# ==============================
# SCROLL PARA CARGAR MERCADOS
# ==============================

print("🔄 Cargando mercados...")

for _ in range(8):
    driver.execute_script("window.scrollBy(0, 1000);")
    time.sleep(1)

# ==============================
# FUNCIONES SCRAPER
# ==============================

def obtener_btts(driver):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    wait = WebDriverWait(driver, 10)

    # 🔍 encontrar mercado
    mercados = driver.find_elements(By.XPATH, "//button[contains(@class,'ds-accordion-header-clickable-area')]")

    for mercado in mercados:
        if "ambos equipos marcan" in mercado.text.lower():

            print("✅ BTTS encontrado")

            driver.execute_script("arguments[0].scrollIntoView();", mercado)
            time.sleep(1)

            # 🔥 click real
            ActionChains(driver).move_to_element(mercado).pause(1).click().perform()

            time.sleep(2)

            # 🔥 encontrar bloque correcto por TEXTO (clave)
            bloques = driver.find_elements(By.XPATH, "//div[contains(@class,'option-group')]")

            for bloque in bloques:
                texto = bloque.text.lower()

                if "sí" in texto and "no" in texto:

                    cuotas = bloque.find_elements(By.XPATH, ".//div[contains(@class,'option-value')]")

                    print("Cuotas dentro del bloque:", len(cuotas))

                    for c in cuotas:
                        print("CUOTA:", c.text)

                    if len(cuotas) >= 2:
                        return cuotas[0].text.strip(), cuotas[1].text.strip()

    return None, None


def obtener_over25(driver):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    import time

    mercados = driver.find_elements(By.XPATH, "//button[contains(@class,'ds-accordion-header-clickable-area')]")

    for mercado in mercados:
        titulo = mercado.text.lower()

        # 🔥 FILTRO MÁS PRECISO
        if titulo.strip() == "total de goles":

            print("✅ Mercado TOTAL DE GOLES encontrado")

            driver.execute_script("arguments[0].scrollIntoView();", mercado)
            time.sleep(1)

            # click igual que BTTS
            ActionChains(driver).move_to_element(mercado).pause(1).click().perform()
            time.sleep(2)

            # 🔥 mismo enfoque que BTTS
            bloques = driver.find_elements(By.XPATH, "//div[contains(@class,'option-group')]")

            for bloque in bloques:
                texto = bloque.text.lower()

                # 🔥 ESTE ES EL BLOQUE CORRECTO
                if "más de 2.5" in texto and "menos de 2.5" in texto:

                    print("🎯 BLOQUE OVER/UNDER 2.5 encontrado")

                    cuotas = bloque.find_elements(By.XPATH, ".//div[contains(@class,'option-value')]")

                    cuotas_limpias = [c.text.strip() for c in cuotas if c.text.strip() != ""]

                    print("Cuotas:", cuotas_limpias)

                    if len(cuotas_limpias) >= 2:
                        return cuotas_limpias[0], cuotas_limpias[1]

    return None, None
# ==============================
# EJECUCIÓN
# ==============================

btts_si, btts_no = obtener_btts(driver)
over25, under25 = obtener_over25(driver)

print("\n==========================")
print("📊 RESULTADOS")
print("==========================")

print(f"BTTS SI: {btts_si}")
print(f"BTTS NO: {btts_no}")

print(f"OVER 2.5: {over25}")
print(f"UNDER 2.5: {under25}")

# ==============================
# CERRAR
# ==============================

driver.quit()