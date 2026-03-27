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