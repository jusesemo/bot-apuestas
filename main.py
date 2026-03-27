from radar import obtener_partidos
from scraper import extraer_datos
from analyzer import analizar_marcadores
from model import calcular_probabilidad, calcular_value


print("\n🔥 BOT DE APUESTAS INICIADO 🔥\n")

partidos = obtener_partidos()

# limitar para pruebas
partidos = partidos[:5]

for partido in partidos:

    print("\n==========================")
    print("Analizando:", partido["nombre"])
    print("==========================")

    datos = extraer_datos(partido["link"])

    h2h_stats = analizar_marcadores(datos["h2h"])
    local_stats = analizar_marcadores(datos["local_form"])
    visitante_stats = analizar_marcadores(datos["visitante_form"])

    modelo = calcular_probabilidad(h2h_stats, local_stats, visitante_stats)

    if not modelo:
        print("Sin datos suficientes")
        continue

    cuota_btts = 1.80
    cuota_over = 1.90

    value_btts = calcular_value(modelo["btts"], cuota_btts)
    value_over = calcular_value(modelo["over25"], cuota_over)

    print("BTTS:", modelo["btts"], "% | Value:", value_btts)
    print("OVER:", modelo["over25"], "% | Value:", value_over)

    if value_btts > 5:
        print("👉 BTTS VALUE")

    if value_over > 5:
        print("👉 OVER VALUE")