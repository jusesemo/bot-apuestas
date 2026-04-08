import pandas as pd

df = pd.read_csv("analisis_partidos_full.csv")

# 🔥 FILTRO PICKS REALES
filtro = (
    (df["Pick"].notna()) &
    (df["Confianza"] == "ALTA") &
    (df["Partido_Trampa"] == False)
)

df_filtrado = df[filtro]

# 🔥 SCORE INTELIGENTE (ranking real)
df_filtrado["Score"] = (
    df_filtrado["Prob_Over2.5"].fillna(0) +
    df_filtrado["Prob_BTTS"].fillna(0) +
    df_filtrado["Value_Over2.5"].fillna(0) +
    df_filtrado["Value_BTTS"].fillna(0)
)

df_filtrado = df_filtrado.sort_values(by="Score", ascending=False)

print("\n🔥 PICKS TOP DEL DÍA\n")

for _, row in df_filtrado.head(10).iterrows():
    print(f"{row['Local']} vs {row['Visitante']}")
    print(f"👉 {row['Pick']} | Confianza: {row['Confianza']}")
    print(f"📊 Over: {row['Prob_Over2.5']}% | BTTS: {row['Prob_BTTS']}%")
    print(f"💰 Value: {row['Value_Over2.5']} / {row['Value_BTTS']}")
    print("-" * 40)