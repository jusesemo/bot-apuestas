def calcular_probabilidad(h2h, local, visitante):

    if not h2h or not local or not visitante:
        return None

    btts = (h2h["btts"] + local["btts"] + visitante["btts"]) / 3
    over25 = (h2h["over25"] + local["over25"] + visitante["over25"]) / 3

    return {
        "btts": round(btts, 1),
        "over25": round(over25, 1)
    }


def calcular_value(prob, cuota):

    prob_real = prob / 100
    prob_casa = 1 / cuota

    return round((prob_real - prob_casa) * 100, 2)