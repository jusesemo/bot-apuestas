import pandas as pd

df = pd.read_csv("analisis_partidos_full.csv")

print("Columnas exactas en el CSV:")
print(df.columns)

# 🔥 FILTRO PICKS REALES
filtro = (
    (df["Pick"].notna()) &
    (df["Confianza"] == "ALTA") &
    (df["Partido_Trampa"] == False)
)

df_filtrado = df[filtro].copy()

# 🔥 SCORE INTELIGENTE (ranking real)
# #610 - SCORE INTELIGENTE BASADO EN VALOR REAL
def calcular_score(row):
    score = 0

    if row["Pick"] == "OVER 2.5":
        score += row.get("Prob_Over2.5", 0)
        score += row.get("Value_Over2.5", 0) * 2

    elif row["Pick"] == "UNDER 2.5":
        score += row.get("Prob_Under2.5", 0)
        score += (100 - row.get("Prob_Over2.5", 50)) * 0.5

    elif "BTTS" in str(row["Pick"]):
        score += row.get("Prob_BTTS", 0)
        score += row.get("Value_BTTS", 0) * 2

    # BONUS POR CONFIANZA
    if row.get("Confianza") == "ALTA":
        score += 15
    elif row.get("Confianza") == "MEDIA":
        score += 7

    # PENALIZAR PARTIDOS TRAMPA
    if row.get("Partido_Trampa"):
        score -= 20

    return score

df_filtrado["Score"] = df_filtrado.apply(calcular_score, axis=1)

df_filtrado = df_filtrado.sort_values(by="Score", ascending=False)

print("\n PICKS TOP DEL DÍA\n")

contador = 1

for _, row in df_filtrado.head(10).iterrows():
    
    local = row['Local']
    visitante = row['Visitante']
    pick = row['Pick']
    confianza = row['Confianza']
    
    score_base = row.get("Score_Base", 0)
    score = row.get("Score", 0)
    
    # 🎯 PROBABILIDAD ESTIMADA
    if row["Pick"] == "OVER 2.5":
        prob = row["Prob_Over2.5"]
        value = row["Value_Over2.5"]

    elif row["Pick"] == "UNDER 2.5":
        prob = row["Prob_Under2.5"]
        value = 100 - row["Prob_Over2.5"]

    elif "BTTS" in row["Pick"]:
        prob = row["Prob_BTTS"]
        value = row["Value_BTTS"]
    
    print(f"{contador}. {local} vs {visitante}")
    
    if pick:
        print(f"👉 {pick}")
    else:
        print("👉 SIN PICK CLARO")
    
    print(f"📊 Prob: {prob}%")
    
    # Mostrar value solo si es positivo
    if value > 0:
        print(f"💰 Value: {value}%")
    
    print(f"🔥 Confianza: {confianza}")
    print("-" * 40)
    
    contador += 1