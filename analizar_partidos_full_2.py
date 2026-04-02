import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# ==============================
# FUNCIONES DE LÓGICA ORIGINAL
# ==============================

def analizar_marcadores(lista):
    goles_totales = 0
    btts = 0
    over25 = 0
    under25 = 0
    clean_sheet_local = 0
    clean_sheet_visitante = 0
    partidos = 0
    for marcador in lista:
        try:
            g1, g2 = marcador.split("-")
            g1, g2 = int(g1), int(g2)
            total = g1 + g2
            goles_totales += total
            partidos += 1
            if g1 > 0 and g2 > 0: btts += 1
            if total > 2: over25 += 1
            if total <= 2: under25 += 1
            if g2 == 0: clean_sheet_local += 1
            if g1 == 0: clean_sheet_visitante += 1
        except: pass
    if partidos == 0: return None
    return {
        "promedio": round(goles_totales / partidos, 2),
        "btts": round((btts / partidos) * 100, 1),
        "over25": round((over25 / partidos) * 100, 1),
        "under25": round((under25 / partidos) * 100, 1),
        "clean_sheet_local": round((clean_sheet_local / partidos) * 100, 1),
        "clean_sheet_visitante": round((clean_sheet_visitante / partidos) * 100, 1)
    }

def calcular_probabilidad(h2h, local, visitante):
    if not h2h or not local or not visitante: return None
    btts = (h2h["btts"] * 0.3 + local["btts"] * 0.35 + visitante["btts"] * 0.35)
    over25 = (h2h["over25"] * 0.3 + local["over25"] * 0.35 + visitante["over25"] * 0.35)
    under25 = (h2h["under25"] * 0.3 + local["under25"] * 0.35 + visitante["under25"] * 0.35)
    clean_sheet_local = (h2h["clean_sheet_local"] * 0.3 + local["clean_sheet_local"] * 0.35 + visitante["clean_sheet_local"] * 0.35)
    clean_sheet_visitante = (h2h["clean_sheet_visitante"] * 0.3 + local["clean_sheet_visitante"] * 0.35 + visitante["clean_sheet_visitante"] * 0.35)
    return {
        "btts": round(btts, 1), 
        "over25": round(over25, 1), 
        "under25": round(under25, 1),
        "clean_sheet_local": round(clean_sheet_local, 1),
        "clean_sheet_visitante": round(clean_sheet_visitante, 1)
    }

def calcular_value(prob, cuota):
    prob_real = prob / 100
    prob_casa = 1 / cuota
    value = prob_real - prob_casa
    return round(value * 100, 2)

# ==============================
# EJECUCIÓN MASIVA
# ==============================

def ejecutar_analisis():
    archivo_links = "links_radar.txt"
    if not os.path.exists(archivo_links):
        print(f"Error: No existe {archivo_links}")
        return

    with open(archivo_links, "r") as f:
        links = [line.strip() for line in f if "http" in line]

    # CONFIGURACIÓN DRIVER (Silenciando errores de Handshake/SSL)
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3") # Silencia errores de consola (Nivel 3 = FATAL)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 20)

    for index, link in enumerate(links):
        try:
            driver.get(link)

            # ACEPTAR COOKIES
            if index == 0:
                try:
                    aceptar = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                    )
                    aceptar.click()
                    print("Cookies aceptadas")
                    time.sleep(2)
                except: pass

            # DETECTAR EQUIPOS
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "participant__participantName")))
            equipos = driver.find_elements(By.CLASS_NAME, "participant__participantName")
            nombres = []
            for e in equipos:
                nombre = e.text.strip()
                if nombre != "" and nombre not in nombres:
                    nombres.append(nombre)

            local, visitante = nombres[0], nombres[1]

            print("\n==========================")
            print("PARTIDO DETECTADO")
            print("==========================")
            print("LOCAL:", local)
            print("VISITANTE:", visitante)

            # ABRIR H2H
            h2h_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'H2H')]")))
            h2h_btn.click()
            print("\nPestaña H2H abierta")

            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tabContent__h2h")))
            time.sleep(3)

            # ACTIVAR CARGA
            contenedor = driver.find_element(By.CLASS_NAME, "tabContent__h2h")
            actions = ActionChains(driver)
            actions.move_to_element(contenedor).perform()
            time.sleep(2)

            for _ in range(10):
                driver.execute_script("arguments[0].scrollTop += 400", contenedor)
                time.sleep(1)

            # EXTRAER MARCADORES
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "h2h__row")))
            rows = driver.find_elements(By.CLASS_NAME, "h2h__row")
            marcadores = []
            for row in rows:
                try:
                    resultado = row.find_element(By.CLASS_NAME, "h2h__result")
                    goles = resultado.find_elements(By.TAG_NAME, "span")
                    if len(goles) == 2:
                        g1, g2 = goles[0].text.strip(), goles[1].text.strip()
                        if g1.isdigit() and g2.isdigit():
                            marcadores.append(f"{g1}-{g2}")
                except: pass

            print("\nMarcadores encontrados:", marcadores)

            h2h_scores = marcadores[:5]
            local_scores = marcadores[5:10]
            visitante_scores = marcadores[10:15]

            # BLOQUE DE IMPRESIÓN ORIGINAL
            print("\n==========================")
            print("ANALISIS H2H")
            print("==========================")
            h2h_stats = analizar_marcadores(h2h_scores)
            if h2h_stats:
                print("Promedio goles:", h2h_stats["promedio"])
                print("BTTS %:", h2h_stats["btts"])
                print("OVER 2.5 %:", h2h_stats["over25"])
                print("UNDER 2.5 %:", h2h_stats["under25"])
                print("CLEAN SHEET LOCAL %:", h2h_stats["clean_sheet_local"])
                print("CLEAN SHEET VISITANTE %:", h2h_stats["clean_sheet_visitante"])

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
                print("UNDER 2.5 %:", local_stats["under25"])
                print("CLEAN SHEET LOCAL %:", local_stats["clean_sheet_local"])
                print("CLEAN SHEET VISITANTE %:", local_stats["clean_sheet_visitante"])

            print("\nUltimos 5 VISITANTE:", visitante_scores)
            visitante_stats = analizar_marcadores(visitante_scores)
            if visitante_stats:
                print(visitante)
                print("Promedio goles:", visitante_stats["promedio"])
                print("BTTS %:", visitante_stats["btts"])
                print("OVER 2.5 %:", visitante_stats["over25"])
                print("UNDER 2.5 %:", visitante_stats["under25"])
                print("CLEAN SHEET LOCAL %:", visitante_stats["clean_sheet_local"])
                print("CLEAN SHEET VISITANTE %:", visitante_stats["clean_sheet_visitante"])

            print("\n==========================")
            print("MODELO DE APUESTA")
            print("==========================")
            modelo = calcular_probabilidad(h2h_stats, local_stats, visitante_stats)

            if modelo:
                print("Probabilidad BTTS:", modelo["btts"], "%")
                print("Probabilidad Over 2.5:", modelo["over25"], "%")
                print("Probabilidad Under 2.5:", modelo["under25"], "%")
                print("Probabilidad Clean Sheet Local:", modelo["clean_sheet_local"], "%")
                print("Probabilidad Clean Sheet Visitante:", modelo["clean_sheet_visitante"], "%")

                # FUERZA REAL DEL PARTIDO
                print("\n==========================")
                print("FUERZA REAL DEL PARTIDO")
                print("==========================")
                if local_stats and visitante_stats:
                    indice_goles = (local_stats["promedio"] + visitante_stats["promedio"]) / 2
                    print("Índice de Goles:", round(indice_goles, 2))
                    
                    if indice_goles < 2.0:
                        print("Interpretación: partido cerrado ")
                    elif 2.0 <= indice_goles <= 2.5:
                        print("Interpretación: neutro ")
                    else:
                        print("Interpretación: partido abierto ")

                # DETECCIÓN DE DESBALANCE (CLAVE PARA HANDICAP)
                print("\n==========================")
                print("DETECCIÓN DE DESBALANCE")
                print("==========================")
                if local_stats and visitante_stats:
                    diff_btts = abs(local_stats["btts"] - visitante_stats["btts"])
                    print("Diferencia BTTS:", round(diff_btts, 1), "%")
                    
                    if diff_btts > 30:
                        print(" Hay mucha diferencia: Partido NO equilibrado")
                        print("   Ideal para: Handicap, Ganador directo")
                    elif diff_btts > 15:
                        print(" Diferencia moderada: Considerar apuestas de lado")
                    else:
                        print(" Partido equilibrado: Evitar handicap/ganador")

                cuota_btts, cuota_over = 1.80, 1.90
                value_btts = calcular_value(modelo["btts"], cuota_btts)
                value_over = calcular_value(modelo["over25"], cuota_over)

                print("\n--- VALUE BET ---")
                print("BTTS Value:", value_btts, "%")
                print("Over 2.5 Value:", value_over, "%")

                if value_btts > 0: print(" BTTS ES VALUE BET")
                if value_over > 0: print(" OVER 2.5 ES VALUE BET")

                # Repetición solicitada
                print("Probabilidad BTTS:", modelo["btts"], "%")
                print("Probabilidad Over 2.5:", modelo["over25"], "%")
                print("\n--- VALUE BET ---")
                print("BTTS Value:", value_btts, "%")
                print("Over 2.5 Value:", value_over, "%")

                print("\n==========================")
                print("REGLAS ESPECIALIZADAS")
                print("==========================")
                
                # BTTS SÓLIDO
                if modelo["btts"] > 60 and value_btts > 5:
                    print(" BTTS FUERTE")
                
                # UNDER FUERTE
                if modelo["over25"] < 45:
                    print(" UNDER 2.5 RECOMENDADO")
                
                # PARTIDO TRAMPA
                if 45 < modelo["btts"] < 55:
                    print(" PARTIDO INESTABLE")
                
                # GOLES LOCALES
                if local_stats and local_stats["promedio"] > 1.5:
                    print(" LOCAL +1.5 GOLES")
                
                # GOLES VISITANTES
                if visitante_stats and visitante_stats["promedio"] > 1.2:
                    print(" VISITANTE +1.2 GOLES")
                
                # CLEAN SHEET FUERTE
                if modelo["clean_sheet_local"] > 40:
                    print(" CLEAN SHEET LOCAL POSIBLE")
                if modelo["clean_sheet_visitante"] > 40:
                    print(" CLEAN SHEET VISITANTE POSIBLE")

                print("\n==========================")
                print("DECISION FINAL")
                print("==========================")
                if value_btts > 5: print(" APOSTAR BTTS")
                if value_over > 5: print(" APOSTAR OVER 2.5")
                if value_btts <= 5 and value_over <= 5: print(" NO APOSTAR ESTE PARTIDO")

        except Exception as e:
            print(f"\n Error procesando link: {link}\nDetalle: {e}")
            continue

    driver.quit()

if __name__ == "__main__":
    ejecutar_analisis()