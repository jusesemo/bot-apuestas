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

# 🔥 NUEVOS FILTROS DE VOLATILIDAD Y GOLES OCULTOS
def volatilidad_goles(lista):
    totales = []
    
    for marcador in lista:
        try:
            g1, g2 = map(int, marcador.split("-"))
            totales.append(g1 + g2)
        except:
            continue

    if len(totales) < 2:
        return 0

    promedio = sum(totales) / len(totales)
    varianza = sum((x - promedio) ** 2 for x in totales) / len(totales)

    return round(varianza, 2)

def gol_oculto(lista):
    for marcador in lista:
        try:
            g1, g2 = map(int, marcador.split("-"))
            if g1 >= 2 or g2 >= 2:
                return True
        except:
            continue
    return False

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

    # 🔥 CASO SIN H2H (modelo recalibrado)
    if not h2h:
        print("⚠️ MODELO SIN H2H (solo forma reciente)")
        
        # 🔥 BTTS REAL (probabilidad conjunta)
        btts_base = (local["btts"]/100 + visitante["btts"]/100) / 2
        btts_inter = (local["btts"]/100 * visitante["btts"]/100)

        btts = (btts_base * 0.7 + btts_inter * 0.3)
        # 🔥 OVER 2.5 REAL con penalización
        over25 = (
            (local["over25"]/100) * 0.55 +
            (visitante["over25"]/100) * 0.55
        )

        # ajuste por promedio de goles
        factor_goles = (
            (local["promedio"] + visitante["promedio"]) / 2
        ) / 2.5  # 2.5 es línea base

        over25 = over25 * factor_goles
        
        # 🔥 PENALIZACIÓN CLEAN SHEET (definir antes)
        penal_cs = (local["clean_sheet_local"] + visitante["clean_sheet_visitante"]) / 200

        # penalización por under
        penalizacion = ((local["under25"] + visitante["under25"]) / 200) * 0.5
        over25 = over25 * (1 - penalizacion)
        
        # BTTS es MUY sensible a clean sheet
        btts = btts * (1 - penal_cs * 0.9)
        over25 = over25 * (1 - penal_cs * 0.5)
            
        return {
            "btts": round(btts * 100, 1),
            "over25": round(over25 * 100, 1),
            "under25": round((local["under25"] * 0.5 + visitante["under25"] * 0.5), 1),
            "clean_sheet_local": round((local["clean_sheet_local"] * 0.5 + visitante["clean_sheet_local"] * 0.5), 1),
            "clean_sheet_visitante": round((local["clean_sheet_visitante"] * 0.5 + visitante["clean_sheet_visitante"] * 0.5), 1)
    }

    # 🔥 CASO NORMAL (modelo recalibrado)
    if not local or not visitante:
        return None

    # 🔥 BTTS híbrido real
    btts_local = local["btts"]/100
    btts_visitante = visitante["btts"]/100
    btts_h2h = (h2h["btts"]/100) if h2h else 0

    btts_avg = (btts_h2h * 0.2 + btts_local * 0.4 + btts_visitante * 0.4)
    btts_inter = (btts_local * btts_visitante)

    btts = (btts_avg * 0.7 + btts_inter * 0.3)

    # 🔥 OVER real con contexto
    over25 = (
        (h2h["over25"]/100) * 0.3 +
        (local["over25"]/100) * 0.35 +
        (visitante["over25"]/100) * 0.35
    )

    factor_goles = ((local["promedio"] + visitante["promedio"]) / 2) / 2.5
    over25 = over25 * factor_goles
    

    # penalización más realista
    penalizacion = ((local["under25"] + visitante["under25"]) / 200) * 0.6
    over25 = over25 * (1 - penalizacion)
   

    # 🔥 clean sheet inteligente
    penal_cs = (local["clean_sheet_local"] + visitante["clean_sheet_visitante"]) / 200
    btts = btts * (1 - penal_cs * 0.9)
    over25 = over25 * (1 - penal_cs * 0.5)

    # 🔥 coherencia matemática
    under25 = (
        (h2h["under25"]/100) * 0.3 +
        (local["under25"]/100) * 0.35 +
        (visitante["under25"]/100) * 0.35
    )

    return {
        "btts": round(btts * 100, 1), 
        "over25": round(over25 * 100, 1), 
        "under25": round(under25 * 100, 1),
        "clean_sheet_local": round((h2h["clean_sheet_local"] * 0.2 + local["clean_sheet_local"] * 0.4 + visitante["clean_sheet_local"] * 0.4), 1),
        "clean_sheet_visitante": round((h2h["clean_sheet_visitante"] * 0.2 + local["clean_sheet_visitante"] * 0.4 + visitante["clean_sheet_visitante"] * 0.4), 1)
    }

def calcular_value(prob, cuota):
    prob_real = prob / 100
    
    ev = (prob_real * cuota) - 1
    
    return round(ev * 100, 2)

def clasificar_value(ev):
        if ev > 10:
            return "🔥 VALUE TOP"
        elif ev > 5:
            return "✅ VALUE BUENO"
        elif ev > 2:
            return "⚠️ VALUE BAJO"
        else:
            return "❌ SIN VALUE"

def zona_partido_cerrado(scores):
    bajos = 0
    
    for marcador in scores:
        try:
            g1, g2 = map(int, marcador.split("-"))
            total = g1 + g2
            
            if total <= 2:
                bajos += 1
        except:
            continue
    
    return bajos >= 4

def partido_caotico(scores):
    altos = 0
    bajos = 0

    for marcador in scores:
        try:
            g1, g2 = map(int, marcador.split("-"))
            total = g1 + g2

            if total >= 4:
                altos += 1
            elif total <= 1:
                bajos += 1
        except:
            continue

    return altos >= 2 and bajos >= 2

def partido_inestable(local_stats, visitante_stats):
    return (
        (local_stats["over25"] >= 50 and visitante_stats["over25"] >= 50)
        or
        (local_stats["promedio"] >= 2.6 and visitante_stats["promedio"] >= 2.6)
        or
        (
            visitante_stats["over25"] >= 40 and
            visitante_stats["promedio"] >= 2.5 and
            (
                visitante_stats["clean_sheet_local"] >= 40 or
                visitante_stats["btts"] <= 40
            )
        )
    )
def over_intercambio(local_stats, visitante_stats, modelo):
    return (
        local_stats["btts"] >= 60 and
        visitante_stats["btts"] >= 60 and
        modelo["btts"] >= 60
    )

def filtro_under_pro(local_stats, visitante_stats, modelo):
    return (
        modelo["under25"] >= 80
        and modelo["btts"] <= 40
        and (
            local_stats["clean_sheet_local"] >= 40
            or visitante_stats["clean_sheet_local"] >= 40
        )
    )
    
def under_perfecto(local_stats, visitante_stats, modelo, home_scores, away_scores):
    return (
        modelo["under25"] >= 80 and
        modelo["btts"] <= 40 and
        
        local_stats["promedio"] <= 2.0 and
        visitante_stats["promedio"] <= 2.0 and
        
        volatilidad_goles(home_scores) < 1.2 and
        volatilidad_goles(away_scores) < 1.2 and
        
        not partido_caotico(home_scores) and
        not partido_caotico(away_scores) and
        
        not gol_oculto(home_scores) and
        not gol_oculto(away_scores)
    )
    
def calcular_score_partido(local_stats, visitante_stats, modelo, home_scores, away_scores):

    score = {
        "UNDER": 0,
        "OVER": 0,
        "BTTS": 0
    }

    # BASE MODELO
    if modelo["under25"] >= 70:
        score["UNDER"] += 3
    elif modelo["under25"] >= 60:
        score["UNDER"] += 2

    if modelo["over25"] >= 70:
        score["OVER"] += 3
    elif modelo["over25"] >= 60:
        score["OVER"] += 2

    if modelo["btts"] >= 65:
        score["BTTS"] += 3
    elif modelo["btts"] >= 55:
        score["BTTS"] += 2

    # PROMEDIO GOLES
    avg_total = (local_stats["promedio"] + visitante_stats["promedio"]) / 2

    if avg_total <= 2.2:
        score["UNDER"] += 2
    elif avg_total >= 2.8:
        score["OVER"] += 2

    # VOLATILIDAD
    vol_local = volatilidad_goles(home_scores)
    vol_visit = volatilidad_goles(away_scores)
    
    print(f"📉 Volatilidad Local: {vol_local} | Visitante: {vol_visit}")

   # 🚨 ALERTA TEMPRANA DE CAOS
    if vol_local > 2.5 or vol_visit > 2.5:
        print("⚠️ Partido con alta volatilidad detectado")
        score["OVER"] += 2  # castigas directo hacia over

    elif vol_local < 1.2 and vol_visit < 1.2:
        score["UNDER"] += 2

    elif vol_local > 2 or vol_visit > 2:
        score["OVER"] += 1

    # GOLES ALTOS
    if gol_oculto(home_scores) or gol_oculto(away_scores):
        score["OVER"] += 1
        score["UNDER"] -= 1

    # CAOS
    if partido_caotico(home_scores) or partido_caotico(away_scores):
        score["OVER"] += 2
        score["UNDER"] -= 3

    # CLEAN SHEET
    if modelo["clean_sheet_local"] > 50 or modelo["clean_sheet_visitante"] > 50:
        score["UNDER"] += 1
        score["BTTS"] -= 2

    # BTTS PURO
    if local_stats["btts"] >= 60 and visitante_stats["btts"] >= 60:
        score["BTTS"] += 2

    return score

def analizar_resultados(df):

    total = len(df)
    ganadas = len(df[df["Resultado"] == "WIN"])
    perdidas = len(df[df["Resultado"] == "LOSS"])

    winrate = (ganadas / total) * 100 if total > 0 else 0

    profit = 0

    for _, row in df.iterrows():
        if row["Resultado"] == "WIN":
            profit += (row["Cuota"] - 1)
        elif row["Resultado"] == "LOSS":
            profit -= 1

    roi = (profit / total) * 100 if total > 0 else 0

    print("\n==========================")
    print("📊 RESULTADOS REALES")
    print("==========================")
    print(f"Apuestas: {total}")
    print(f"Winrate: {round(winrate,2)}%")
    print(f"ROI: {round(roi,2)}%")
    
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
    partidos_data = []
    
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
                partido_abierto_extremo = modelo["over25"] > 65 and modelo["btts"] > 60
                print("Probabilidad BTTS:", modelo["btts"], "%")
                print("Probabilidad Over 2.5:", modelo["over25"], "%")
                print("Probabilidad Under 2.5:", modelo["under25"], "%")
                print("Probabilidad Clean Sheet Local:", modelo["clean_sheet_local"], "%")
                print("Probabilidad Clean Sheet Visitante:", modelo["clean_sheet_visitante"], "%")
                
                
                # ==========================
                # PERFIL DEL PARTIDO (REAL)
                # ==========================

                perfil = None

                if modelo["over25"] < 45:
                    perfil = "CERRADO"

                elif modelo["over25"] > 60 and modelo["btts"] > 55:
                    perfil = "ABIERTO"

                elif modelo["btts"] > 60 and modelo["over25"] <= 55:
                    perfil = "BTTS_CERRADO"

                else:
                    perfil = "MIXTO"

                print(f"📊 PERFIL DETECTADO: {perfil}")
                
                puede_subir_linea = (
                    modelo["under25"] >= 80 and
                    local_stats["promedio"] <= 2.2 and
                    visitante_stats["promedio"] <= 2.2 and
                    not partido_caotico(home_scores) and
                    not partido_caotico(away_scores)
                )

                # 🔥 AJUSTE EXTRA SI NO HAY H2H
                if not h2h_stats:
                    puede_subir_linea = puede_subir_linea and modelo["under25"] >= 85
                
                partido_cerrado = modelo["over25"] < 45


                # FUERZA REAL DEL PARTIDO
                print("\n==========================")
                print("FUERZA REAL DEL PARTIDO")
                print("==========================")
                if local_stats and visitante_stats and h2h_stats:
                    if modelo["over25"] < 45:
                        print("Interpretación: partido cerrado ")
                    elif modelo["over25"] > 60:
                        print("Interpretación: partido abierto ")
                    else:
                        print("Interpretación: partido neutro ")

                # ===========================
                # GANADOR PROBABLE + HANDICAP (MEJORADO)
                # ===========================

                ganador = None
                handicap = None
                favorito_fuerte = False   # 👈 SIEMPRE inicializado arriba

                if local_stats and visitante_stats and modelo:

                    diff_btts = local_stats["btts"] - visitante_stats["btts"]
                    diff_cs = visitante_stats["clean_sheet_local"] - local_stats["clean_sheet_visitante"]

                    # FILTRO DE FAVORITO FUERTE
                    favorito_fuerte = (
                        modelo["over25"] >= 50 and
                        modelo["btts"] >= 50 and
                        local_stats["promedio"] >= visitante_stats["promedio"] + 0.8 and
                        local_stats["over25"] >= visitante_stats["over25"] + 20 and
                        visitante_stats["clean_sheet_local"] >= 40
    )

                    # FILTRO: evitar partidos locos
                    partido_abierto = modelo["over25"] > 65 and modelo["btts"] > 60

                    # DOMINIO LOCAL
                    if diff_btts >= 25 and diff_cs < -10 and not partido_abierto and not partido_cerrado:
                        ganador = "LOCAL"
                        
                        if diff_btts >= 50:
                            handicap = "LOCAL -1.5"
                        elif diff_btts >= 35:
                            handicap = "LOCAL -1"
                        else:
                            handicap = "LOCAL"

                    # 🔥 DOMINIO VISITANTE
                    elif diff_btts <= -25 and diff_cs > 10 and not partido_abierto and not partido_cerrado:
                        ganador = "VISITANTE"
                        
                        if diff_btts <= -50:
                            handicap = "VISITANTE -1.5"
                        elif diff_btts <= -35:
                            handicap = "VISITANTE -1"
                        else:
                            handicap = "VISITANTE"

                    # ⚖️ PARTIDO EQUILIBRADO
                    else:
                        ganador = "NO CLARO"
                        handicap = None
                        
                        # 🔥 VALIDACIÓN FINAL GANADOR (AQUÍ VA 🔥)
                    if ganador != "NO CLARO":

                    # 🚨 evitar partidos locos (muchos goles)
                        if partido_abierto_extremo:
                            print("⚠️ Partido muy abierto → evitar ganador")
                            ganador = "NO CLARO"
                            handicap = None

                        # 🧱 partido con alta probabilidad de portería en cero
                        elif modelo["clean_sheet_local"] > 55 or modelo["clean_sheet_visitante"] > 55:
                            print("🧱 Partido con tendencia a portería en cero")


                print("\n==========================")
                print("GANADOR Y HANDICAP")
                print("==========================")

                print("Ganador probable:", ganador)

                if handicap:
                    print("Handicap sugerido:", handicap)
                else:
                    print("Sin handicap claro")
                    
                # 💎 FAVORITO FUERTE DETECTADO
                if ganador == "LOCAL" and favorito_fuerte:
                    print("💎 FAVORITO FUERTE (GANADOR)")
                    
                # 🔥 AÚN MEJOR (ANTI-TRAMPA)
                if partido_abierto_extremo:
                    print("⚠️ Partido abierto → evitar ganador")
                    ganador = "NO CLARO"
                    handicap = None
                    
                if ganador != "NO CLARO" and modelo["clean_sheet_local"] > 50:
                    print("⚠️ Posible victoria a cero")
                    
                cuota_btts, cuota_over = 1.75, 1.95
                value_btts = calcular_value(modelo["btts"], cuota_btts)
                value_over = calcular_value(modelo["over25"], cuota_over)
                value_under = calcular_value(modelo["under25"], 1.80)

                print("\n--- VALUE BET ---")
                print("BTTS Value:", value_btts, "%")
                print("Over 2.5 Value:", value_over, "%")
                print("Under 2.5 Value:", value_under, "%")

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
                
                
                print("\n==========================")
                print("DECISION FINAL (SCORE PRO)")
                print("==========================")

                score = calcular_score_partido(local_stats, visitante_stats, modelo, home_scores, away_scores)

                print(f"📊 SCORE: {score}")

                if all(v <= 0 for v in score.values()):
                    pick = None
                    confianza = "BAJA"
                else:
                    pick = max(score, key=score.get)
                    valor = score[pick]

                    if valor >= 6:
                        confianza = "ALTA"
                    elif valor >= 4:
                        confianza = "MEDIA"
                    else:
                        pick = None
                        confianza = "BAJA"
                    
                
                    
                if pick == "BTTS":
                    if modelo["clean_sheet_local"] > 55 or modelo["clean_sheet_visitante"] > 55:
                        print("❌ BTTS cancelado por clean sheet")
                        pick = None
                        confianza = "BAJA"   # 👈 AQUÍ

                if pick == "UNDER":
                    if partido_caotico(home_scores) or partido_caotico(away_scores):
                        print("💣 UNDER cancelado por caos")
                        pick = None
                        confianza = "BAJA"   # 👈 AQUÍ

                if pick == "OVER":

                    # 🔻 OVER débil
                    if modelo["btts"] < 50:
                        print("⚠️ OVER débil sin BTTS")
                        confianza = "MEDIA"

                    # 🔥 recalcular volatilidad
                    vol_local = volatilidad_goles(home_scores)
                    vol_visit = volatilidad_goles(away_scores)

                    # 💀 OVER MUY CAOTICO (bloqueo total)
                    if vol_local > 3 or vol_visit > 3:
                        print("💀 OVER ULTRA CAOTICO → evitar")
                        pick = None
                        confianza = "BAJA"

                    # 💣 OVER CAOTICO (solo baja confianza)
                    elif vol_local > 2.5 or vol_visit > 2.5:
                        print("💣 OVER CAOTICO → bajar confianza")
                        confianza = "MEDIA"
                        
                    
                        
                mapa = {
                        "UNDER": "UNDER 2.5",
                        "OVER": "OVER 2.5",
                        "BTTS": "BTTS"
                    }
                if pick:
                    pick = mapa.get(pick, pick)
        
                # RESULTADO FINAL
                if pick:
                    print(f" 🏁 RECOMENDACION FINAL: {pick}")
                    print(f" 🔝 CONFIANZA: {confianza}")
                    if confianza == "ALTA":
                        print(" 💎 PICK PREMIUM (APTO PARA JUGAR)")
                    
                    # LÓGICA DE DECISIÓN PARA JUGAR (AJUSTADA)
                    
                    jugar = False
                    pick_final = None
                    
                    if value_over >= 8:
                        jugar = True
                        pick_final = "OVER 2.5"
                        print(" 📈 JUGAR: SÍ (OVER con value)")

                    elif value_btts >= 8:
                        jugar = True
                        pick_final = "BTTS"
                        print(" 📈 JUGAR: SÍ (BTTS con value)")

                    elif value_under >= 8:
                        jugar = True
                        pick_final = "UNDER 2.5"
                        print(" 📈 JUGAR: SÍ (UNDER con value)")

                    else:
                        jugar = False
                        print(" ❌ JUGAR: NO (sin value suficiente)")
                    
                    if jugar:
                        print(f"🎯 PICK FINAL REAL: {pick_final}")  
                        
                partido_info = {
                    "Local": local,
                    "Visitante": visitante,
                    "Prob_BTTS": modelo["btts"] if modelo else None,
                    "Prob_Over2.5": modelo["over25"] if modelo else None,
                    "Prob_Under2.5": modelo["under25"] if modelo else None,
                    "Value_BTTS": value_btts if modelo else None,
                    "Value_Over2.5": value_over if modelo else None,
                    "Value_Under2.5": value_under if modelo else None,
                    "Pick": pick,
                    "Confianza": confianza,
                    "Ganador": ganador,
                    "Handicap": handicap,
                    "Cuota": None,
                    "Resultado": None,
                   
                }
        
                partidos_data.append(partido_info)

                                   
        except Exception as e:
            print(f"\n Error procesando link: {link}\nDetalle: {e}")
            continue
        
        
    # BLOQUE EXTRA: GUARDAR TODO EN EXCEL
    # =======================================
    
    
    if partidos_data:
        import pandas as pd
        df = pd.DataFrame(partidos_data)
        df.to_excel("analisis_partidos_full.xlsx", index=False)
        df.to_csv("analisis_partidos_full.csv", index=False)

        print("\n✅ Archivo generado correctamente")
    
     # 🔥 ANALIZAR RESULTADOS (cuando ya tengas WIN/LOSS en el Excel)
    try:
        df_resultados = pd.read_excel("analisis_partidos_full.xlsx")
        analizar_resultados(df_resultados)
    except Exception as e:
        print("⚠️ Aún no hay resultados para analizar (agrega WIN/LOSS en el Excel)")

    driver.quit()

if __name__ == "__main__":
    ejecutar_analisis()