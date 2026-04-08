import time
import os
import re
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

def limpiar_nombre(nombre):
    return re.sub(r"\s*\(.*?\)", "", nombre).strip()

def cambiar_tab(wait, nombre_tab):
    try:
        tab = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//button[@role='tab' and contains(., '{nombre_tab}')]")
        ))
        tab.click()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"⚠️ No se pudo abrir tab: {nombre_tab}")
        return False

def extraer_marcadores(driver, wait):
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "h2h__row")))
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

    return marcadores[:5]  # solo 5 partidos

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

    # 🔥 CASO SIN H2H
    if not h2h:
        print("⚠️ MODELO SIN H2H (solo forma reciente)")
        return {
            "btts": round((local["btts"] * 0.5 + visitante["btts"] * 0.5), 1),
            "over25": round((local["over25"] * 0.5 + visitante["over25"] * 0.5), 1),
            "under25": round((local["under25"] * 0.5 + visitante["under25"] * 0.5), 1),
            "clean_sheet_local": round((local["clean_sheet_local"] * 0.5 + visitante["clean_sheet_local"] * 0.5), 1),
            "clean_sheet_visitante": round((local["clean_sheet_visitante"] * 0.5 + visitante["clean_sheet_visitante"] * 0.5), 1)
        }

    # 🔥 CASO NORMAL
    if not local or not visitante:
        return None

    btts = (h2h["btts"] * 0.2 + local["btts"] * 0.4 + visitante["btts"] * 0.4)
    over25 = (h2h["over25"] * 0.2 + local["over25"] * 0.4 + visitante["over25"] * 0.4)
    under25 = (h2h["under25"] * 0.2 + local["under25"] * 0.4 + visitante["under25"] * 0.4)
    clean_sheet_local = (h2h["clean_sheet_local"] * 0.2 + local["clean_sheet_local"] * 0.4 + visitante["clean_sheet_local"] * 0.4)
    clean_sheet_visitante = (h2h["clean_sheet_visitante"] * 0.2 + local["clean_sheet_visitante"] * 0.4 + visitante["clean_sheet_visitante"] * 0.4)

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

            # ==============================
            # EXTRAER DATOS REALES POR TAB
            # ==============================

            # 1. H2H REAL (GENERAL)
            cambiar_tab(wait, "General")
            time.sleep(2)

            # 🔍 DETECTAR SI NO HAY H2H
            no_h2h = False
            try:
                no_data = driver.find_element(By.CLASS_NAME, "noData")
                if "Ningún partido encontrado" in no_data.text:
                    no_h2h = True
            except:
                pass

            if no_h2h:
                print("⚠️ NO HAY H2H REAL - se omite")
                h2h_scores = []
                h2h_stats = None
            else:
                rows = driver.find_elements(By.CLASS_NAME, "h2h__row")

                marcadores_general = []

                for row in rows:
                    try:
                        resultado = row.find_element(By.CLASS_NAME, "h2h__result")
                        goles = resultado.find_elements(By.TAG_NAME, "span")

                        if len(goles) == 2:
                            g1 = goles[0].text.strip()
                            g2 = goles[1].text.strip()

                            if g1.isdigit() and g2.isdigit():
                                marcadores_general.append(f"{g1}-{g2}")
                    except:
                        pass

                h2h_scores = marcadores_general[-5:]

            # 2. LOCAL EN CASA
            local_tab = limpiar_nombre(local)
            visitante_tab = limpiar_nombre(visitante)
            
            home_scores = []
            if cambiar_tab(wait, f"{local_tab} - Local"):
                time.sleep(2)
                home_scores = extraer_marcadores(driver, wait)
            else:
                print(f" No se pudo acceder a pestaña Local: {local_tab}")

            # 3. VISITANTE FUERA
            away_scores = []
            if cambiar_tab(wait, f"{visitante_tab} - Visitante"):
                time.sleep(2)
                away_scores = extraer_marcadores(driver, wait)
            else:
                print(f" No se pudo acceder a pestaña Visitante: {visitante_tab}")

            print("\nH2H:", h2h_scores)
            print("LOCAL CASA:", home_scores)
            print("VISITANTE FUERA:", away_scores)

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
            
            print("\nUltimos 5 LOCAL:", home_scores)
            local_stats = analizar_marcadores(home_scores)
            if local_stats:
                print(local)
                print("Promedio goles:", local_stats["promedio"])
                print("BTTS %:", local_stats["btts"])
                print("OVER 2.5 %:", local_stats["over25"])
                print("UNDER 2.5 %:", local_stats["under25"])
                print("CLEAN SHEET LOCAL %:", local_stats["clean_sheet_local"])
                print("CLEAN SHEET VISITANTE %:", local_stats["clean_sheet_visitante"])

            print("\nUltimos 5 VISITANTE:", away_scores)
            visitante_stats = analizar_marcadores(away_scores)
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
                if local_stats and visitante_stats and h2h_stats:
                    if modelo["over25"] < 45:
                        print("Interpretación: partido cerrado ")
                    elif modelo["over25"] > 55:
                        print("Interpretación: partido abierto ")
                    else:
                        print("Interpretación: partido neutro ")

                # DETECCIÓN DE DESBALANCE (CLAVE PARA HANDICAP)
                print("\n==========================")
                print("DETECCIÓN DE DESBALANCE")
                print("==========================")
                if local_stats and visitante_stats:
                    diff_btts = abs(local_stats["btts"] - visitante_stats["btts"])
                    print("   Diferencia BTTS:", round(diff_btts, 1), "%")
                    
                    if diff_btts > 30:
                        print("   Hay mucha diferencia: Partido NO equilibrado")
                        print("   Ideal para: Handicap, Ganador directo")
                    elif diff_btts > 15:
                        print(" Diferencia moderada: Considerar apuestas de lado")
                    else:
                        print(" Partido equilibrado: Evitar handicap/ganador")

                # 🔥 PERFIL UNILATERAL (clave real)
                if local_stats and visitante_stats:
                    diff_btts = abs(local_stats["btts"] - visitante_stats["btts"])

                    if diff_btts >= 50:
                        print("🔥 PERFIL: PARTIDO DE UN SOLO EQUIPO")

                        if local_stats["btts"] > visitante_stats["btts"]:
                            print("👉 ESCENARIO: GANA LOCAL SIN ENCAJAR")
                        else:
                            print("👉 ESCENARIO: GANA VISITANTE SIN ENCAJAR")

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
                
                # FILTRO ANTI BTTS FALSO
                btts_riesgoso = False
                
                if visitante_stats and visitante_stats["clean_sheet_local"] >= 40:
                    btts_riesgoso = True
                    
                if local_stats and local_stats["clean_sheet_visitante"] >= 40:
                    btts_riesgoso = True
                
                # FILTRO ANTI ENGAÑO BTTS (equipos inconsistentes)
                if local_stats and visitante_stats:
                    if local_stats["btts"] < 40 or visitante_stats["btts"] < 40:
                        print(" 🔁❓ BTTS ENGAÑOSO (uno de los equipos no marca fiable)")
                        btts_riesgoso = True
                
                # FILTRO DE CLEAN SHEET PELIGROSO
                if modelo and (modelo["clean_sheet_local"] > 50 or modelo["clean_sheet_visitante"] > 50):
                    print(" ⚠️ RIESGO ALTO: POSIBLE PORTERÍA EN CERO")
                    btts_riesgoso = True
                
                if btts_riesgoso:
                    print(" 🔁❓ BTTS RIESGOSO (posible gol de un solo equipo)")
                
                # BTTS SÓLIDO
                if modelo["btts"] > 60 and value_btts > 5:
                    print(" 💪 BTTS FUERTE ")
                
                # UNDER FUERTE
                if modelo["over25"] < 45:
                    print(" 🥇 UNDER TOP ")
                
                # PARTIDO TRAMPA
                if 45 < modelo["btts"] < 55 and modelo["over25"] > 50:
                    print(" PARTIDO INESTABLE")
                
                # GOLES LOCALES
                if modelo["over25"] > 50:
                    if local_stats and local_stats["promedio"] > 1.5:
                        print(" ⚽LOCAL +1.5 GOLES")

                    if visitante_stats and visitante_stats["promedio"] > 1.2:
                        print(" ⚽ VISITANTE +1.2 GOLES")
                
                # CLEAN SHEET FUERTE
                if modelo["clean_sheet_local"] > 40:
                    print(" CLEAN SHEET LOCAL POSIBLE")
                if modelo["clean_sheet_visitante"] > 40:
                    print(" CLEAN SHEET VISITANTE POSIBLE")

                print("\n==========================")
                print("DECISION FINAL (MODO ESTADISTICO)")
                print("==========================")

                pick = None

                # UNDER PRIORIDAD (tu fuerte)
                if modelo["under25"] >= 60:
                    pick = "UNDER 2.5"
                    print(" 🔽 PICK ESTADISTICO: UNDER 2.5 ")
                    
                    # 🚨 FILTRO ANTI-TRAMPA (MUY IMPORTANTE)
                    under_fuerte = (
                        modelo["under25"] >= 65 and
                        modelo["btts"] < 50
                    )
                    
                    # ❌ CANCELAR UNDER SI:
                    if modelo["btts"] >= 55:
                        print(" ❌ UNDER CANCELADO: alto riesgo de ambos marcan")
                        under_fuerte = False
                        pick = None
                    
                    # 🎯 CLASIFICACIÓN DE UNDER
                    # 🔥 UNDER TOP (APUESTA REAL)
                    if modelo["under25"] >= 70 and modelo["btts"] < 45:
                        print(" 🥇 UNDER TOP (APUESTA REAL GOLD)")
                        print(" 👉 Escenario probable: 0-0, 1-0, 2-0")
                        confianza = "ALTA"
                    
                    # ⚠️ UNDER MEDIO (con cuidado)
                    elif modelo["under25"] >= 65 and modelo["btts"] < 50:
                        print(" 🚧 UNDER MEDIO (con cuidado)")
                        print(" 👉 Puede salir… pero riesgo de 1-1")  
                        confianza = "MEDIA"
                    
                    # ❌ UNDER TRAMPA
                    elif modelo["btts"] >= 55:
                        print(" ❌ UNDER TRAMPA")
                        pick = None

                    if modelo["under25"] >= 65:
                        confianza = "MEDIA"
                    if modelo["under25"] >= 70:
                        confianza = "ALTA"

                    if modelo["btts"] < 50:
                        print(" 💎 UNDER 2.5 MUY SOLIDO ")
                    else:
                        print(" ☢️ UNDER 2.5 CON RIESGO  (posible 1-1)")

                    # PERFIL: PARTIDO DE UN SOLO EQUIPO
                    if modelo["btts"] < 40:
                        if modelo["btts"] < 35:
                            print(" 🚪 PERFIL: DOMINIO DEFENSIVO / PARTIDO CERRADO")
                        else:
                            print(" 1️⃣🔁❓ PERFIL: PARTIDO DE UN SOLO EQUIPO ")

                        if visitante_stats and local_stats:
                            if visitante_stats["promedio"] > local_stats["promedio"] and visitante_stats["btts"] > local_stats["btts"]:
                                print(" ⚽  ESCENARIO PROBABLE: 0-1 / 0-2  (VISITANTE)")
                            elif local_stats["promedio"] > visitante_stats["promedio"] and local_stats["btts"] > visitante_stats["btts"]:
                                print(" ⚽ ESCENARIO PROBABLE: 1-0 / 2-0  (LOCAL)")
                            else:
                                print(" ⚽ ESCENARIO PROBABLE: 1-0 / 0-1  (PARTIDO CERRADO)")

                # OVER PRIMERO (más rentable a largo plazo)
                elif modelo["over25"] >= 65:
                    pick = "OVER 2.5"
                    print(" 🔝 PICK ESTADISTICO: OVER 2.5 ")

                    if modelo["btts"] < 50:
                        print(" 🥅 OVER 2.5 PERFIL DOMINANTE (un equipo genera el over)")
                    else:
                        print(" 1️⃣🔁2️⃣ OVER 2.5 ABIERTO (ambos equipos aportan)")

                # LUEGO BTTS
                elif modelo["btts"] >= 65 and not btts_riesgoso:
                    pick = "BTTS "
                    print(" 🟰 PICK ESTADISTICO: BTTS ")

                    if modelo["over25"] >= 55:
                        print(" PERFIL: PARTIDO ABIERTO (ambos equipos generan goles)")
                        print(" ⚽ ESCENARIO PROBABLE: 1-1 / 2-1 / 2-2")
                    else:
                        print(" PERFIL: BTTS CERRADO")
                        print(" ⚽ ESCENARIO PROBABLE: 1-1")

                # VALUE REAL (aunque no cumpla filtros estrictos)
                elif value_over > 3 and modelo["over25"] >= 58:
                    pick = "OVER 2.5"
                    print(" 🔝🤑 PICK ESTADISTICO: OVER 2.5 (VALUE DETECTADO)")

                elif value_btts > 3 and modelo["btts"] >= 58:
                    pick = "BTTS "
                    print(" 🟰🤑 PICK ESTADISTICO: BTTS (VALUE DETECTADO)")

                # PARTIDO TRAMPA
                elif 45 < modelo["btts"] < 60:
                    print(" 🪤 PARTIDO TRAMPA  (EVITAR GOLES)")

                else:
                    print(" SIN PICK CLARO")

                # ESCENARIO PROBABLE ADICIONAL
                if modelo["under25"] >= 60 and modelo["clean_sheet_visitante"] > 40:
                    print(" ⚽ ESCENARIO PROBABLE: 0-1 / 0-2 ")
                
                if pick:
                    # FILTRO FINAL ANTI TRAMPA
                    riesgo = False
                    
                    if local_stats and visitante_stats:
                        if local_stats["btts"] < 40 or visitante_stats["btts"] < 40:
                            riesgo = True
                    
                    if modelo and (modelo["clean_sheet_local"] > 50 or modelo["clean_sheet_visitante"] > 50):
                        riesgo = True
                    
                    # BLOQUEO
                    if riesgo and pick in ["BTTS SI", "OVER 2.5"]:
                        print(" ❌ PICK CANCELADO POR ALTO RIESGO")
                        pick = None
                    
                    # BLOQUEO FINAL DE SEGURIDAD
                    if pick == "BTTS SI" and local_stats and visitante_stats:
                        if local_stats["btts"] < 50 or visitante_stats["btts"] < 50:
                            print(" ❌ BTTS CANCELADO POR INCONSISTENCIA")
                            pick = None
                    
                    if pick:
                        # CONFIANZA ALTA (más realista)
                        if (
                            (modelo and modelo["over25"] >= 60 and value_over > 5) or
                            (modelo and modelo["btts"] >= 60 and value_btts > 5) or
                            (modelo and modelo["under25"] >= 70 and modelo["btts"] < 45)
                        ):
                            confianza = "ALTA"
                        
                        # CONFIANZA MEDIA
                        elif (
                            (modelo and modelo["over25"] >= 55 and value_over > 3) or
                            (modelo and modelo["btts"] >= 55 and value_btts > 3) or
                            (modelo and modelo["under25"] >= 65)
                        ):
                            confianza = "MEDIA"
                        
                        # CANCELAR PICKS ENGAÑOSOS
                        if modelo and 45 < modelo["btts"] < 60:
                            print(" ❌ PICK CANCELADO: partido trampa")
                            pick = None
                        
                        # SOLO cancelar por value si es OVER o BTTS
                        if pick in ["OVER 2.5", "BTTS SI"]:
                            if value_over < 3 and value_btts < 3:
                                print(" ❌ PICK CANCELADO: sin value real")
                                pick = None
                        
                        if pick:
                            print(f" 🏁 RECOMENDACION FINAL: {pick}")
                            print(f" 🔝  CONFIANZA: {confianza}")
                            
        except Exception as e:
            print(f"\n Error procesando link: {link}\nDetalle: {e}")
            continue
        else:
            if not pick:
                print(" ❌ SIN PICK FINAL")

    # BLOQUE EXTRA: GUARDAR TODO EN EXCEL
    # =======================================
    import pandas as pd
    
    if 'partidos_data' not in locals():
        partidos_data = []
    
    # Al final de cada partido, después de calcular pick, confianza, value, etc.
    partido_info = {
        "Local": local,
        "Visitante": visitante,
        # Últimos 5 resultados
        **{f"H2H_{i+1}": h2h_scores[i] if i < len(h2h_scores) else None for i in range(5)},
        **{f"Local_{i+1}": home_scores[i] if i < len(home_scores) else None for i in range(5)},
        **{f"Visitante_{i+1}": away_scores[i] if i < len(away_scores) else None for i in range(5)},
        # Estadísticas
        "H2H_Promedio": h2h_stats["promedio"] if h2h_stats else None,
        "H2H_BTTS": h2h_stats["btts"] if h2h_stats else None,
        "H2H_Over2.5": h2h_stats["over25"] if h2h_stats else None,
        "H2H_Under2.5": h2h_stats["under25"] if h2h_stats else None,
        "H2H_CS_Local": h2h_stats["clean_sheet_local"] if h2h_stats else None,
        "H2H_CS_Visitante": h2h_stats["clean_sheet_visitante"] if h2h_stats else None,
        
        "Local_Promedio": local_stats["promedio"] if local_stats else None,
        "Local_BTTS": local_stats["btts"] if local_stats else None,
        "Local_Over2.5": local_stats["over25"] if local_stats else None,
        "Local_Under2.5": local_stats["under25"] if local_stats else None,
        "Local_CS_Local": local_stats["clean_sheet_local"] if local_stats else None,
        "Local_CS_Visitante": local_stats["clean_sheet_visitante"] if local_stats else None,
        
        "Visitante_Promedio": visitante_stats["promedio"] if visitante_stats else None,
        "Visitante_BTTS": visitante_stats["btts"] if visitante_stats else None,
        "Visitante_Over2.5": visitante_stats["over25"] if visitante_stats else None,
        "Visitante_Under2.5": visitante_stats["under25"] if visitante_stats else None,
        "Visitante_CS_Local": visitante_stats["clean_sheet_local"] if visitante_stats else None,
        "Visitante_CS_Visitante": visitante_stats["clean_sheet_visitante"] if visitante_stats else None,
        
        # Modelo
        "Prob_BTTS": modelo["btts"] if modelo else None,
        "Prob_Over2.5": modelo["over25"] if modelo else None,
        "Prob_Under2.5": modelo["under25"] if modelo else None,
        "Prob_CS_Local": modelo["clean_sheet_local"] if modelo else None,
        "Prob_CS_Visitante": modelo["clean_sheet_visitante"] if modelo else None,
        
        # Value
        "Value_BTTS": value_btts if modelo else None,
        "Value_Over2.5": value_over if modelo else None,
        
        # Interpretaciones
        "Fuerza_Partido": "Cerrado" if modelo and modelo["over25"] < 45 else ("Abierto" if modelo and modelo["over25"] > 55 else "Neutro"),
        "Diff_BTTS": abs(local_stats["btts"] - visitante_stats["btts"]) if local_stats and visitante_stats else None,
        
        # Pick y confianza
        "Pick": pick if 'pick' in locals() else None,
        "Confianza": confianza if 'confianza' in locals() else None,
        
        # Escenarios probables
        "Escenario_Probable": escenario if 'escenario' in locals() else None,
        
        # Flags especiales
        "BTTS_Fuerte": modelo["btts"] > 60 and value_btts > 5 if modelo else False,
        "Under_Fuerte": modelo["over25"] < 45 if modelo else False,
        "Value_Bet": (value_btts > 5 or value_over > 5) if modelo else False,
        "Partido_Trampa": 45 < modelo["btts"] < 60 if modelo else False,
        "CleanSheet_Local_Fuerte": modelo["clean_sheet_local"] > 40 if modelo else False,
        "CleanSheet_Visitante_Fuerte": modelo["clean_sheet_visitante"] > 40 if modelo else False
    }
    
    partidos_data.append(partido_info)
    
    # Al final de ejecutar_analisis(), fuera del for:
    if partidos_data:
        df = pd.DataFrame(partidos_data)
        df.to_excel("analisis_partidos_full.xlsx", index=False)
        df.to_csv("analisis_partidos_full.csv", index=False)
        print("\n✅ Archivo Excel y CSV generado: analisis_partidos_full.xlsx / analisis_partidos_full.csv")

    driver.quit()

if __name__ == "__main__":
    ejecutar_analisis()