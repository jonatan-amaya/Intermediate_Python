# -*- coding: utf-8 -*-
"""Tarea 3 - Parte 1: analisis - KPIs y hallazgos, guardados en web/data/hallazgos.json."""
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / "datos" / "procesados" / "panel_long.csv")

pob = df[df["indicador"] == "pobreza"].pivot(index="iso3", columns="anio", values="valor")
gini = df[df["indicador"] == "gini"].pivot(index="iso3", columns="anio", values="valor")
NOMBRES = json.loads((BASE / "web" / "data" / "datos.json").read_text("utf-8"))["paises"]

ANIO_ULT = int(pob.columns.max())


def cambio_pp(iso, anio_ini, anio_fin):
    try:
        return round(pob.loc[iso, anio_fin] - pob.loc[iso, anio_ini], 1)
    except KeyError:
        return None


# --- hallazgo 1: evolucion nacional de Peru y la region ---
per = pob.loc["PER"].dropna()
latam = df[df["indicador"] == "pobreza"].groupby("anio")["valor"].mean()

# --- hallazgo 2: paises con mayor pobreza reciente y mayor reduccion 2000s->2024 ---
ult = pob[ANIO_ULT].dropna().sort_values(ascending=False)
reducciones = []
for iso in pob.index:
    serie = pob.loc[iso].dropna()
    if len(serie) >= 8 and serie.index.min() <= 2005 and ANIO_ULT in serie.index:
        reducciones.append((iso, round(serie.loc[ANIO_ULT] - serie.iloc[0], 1),
                            int(serie.index.min())))
reducciones.sort(key=lambda t: t[1])
mejor = reducciones[0]
peor = reducciones[-1]

# --- hallazgo 3: desigualdad (Gini): evolucion de Peru y posicion regional ---
anio_gini = int(gini.columns.max())
gini_rec = gini[anio_gini].dropna().sort_values(ascending=False)
gini_per = gini.loc["PER"].dropna()
rank_per = int(list(gini_rec.index).index("PER")) + 1
gini_2000 = float(gini_per.iloc[0])
gini_ult = float(gini_per.loc[anio_gini])

kpis = {
    "pobreza_peru_ult": {"valor": float(per.loc[ANIO_ULT]), "anio": ANIO_ULT},
    "pobreza_peru_prepandemia": {"valor": float(per.loc[2019]), "anio": 2019},
    "pobreza_peru_max": {"valor": float(per.max()), "anio": int(per.idxmax())},
    "pais_mas_pobre": {"pais": NOMBRES[ult.index[0]], "valor": float(ult.iloc[0]),
                       "anio": ANIO_ULT},
    "pais_menos_pobre": {"pais": NOMBRES[ult.index[-1]], "valor": float(ult.iloc[-1]),
                         "anio": ANIO_ULT},
    "promedio_region_ult": {"valor": round(float(latam.loc[ANIO_ULT]), 1), "anio": ANIO_ULT},
}

hallazgos = [
    {
        "titulo": f"Perú: la pandemia borró una década de avances y la recuperación aún no cierra",
        "detalle": (f"La pobreza en Perú pasó de {per.loc[2019]:.1f}% en 2019 a "
                    f"{per.loc[2020]:.1f}% en 2020 (+{per.loc[2020]-per.loc[2019]:.1f} puntos, "
                    f"el mayor salto de la serie) y se ubicó en {per.loc[ANIO_ULT]:.1f}% en "
                    f"{ANIO_ULT}, todavía {per.loc[ANIO_ULT]-per.loc[2019]:.1f} puntos por encima "
                    f"del nivel prepandemia."),
    },
    {
        "titulo": f"Reducciones estructurales: {NOMBRES[mejor[0]]} lidera la caída, "
                  f"{NOMBRES[peor[0]]} la menor",
        "detalle": (f"Entre {mejor[2]} y {ANIO_ULT}, {NOMBRES[mejor[0]]} redujo la pobreza en "
                    f"{abs(mejor[1])} puntos. En el otro extremo, {NOMBRES[peor[0]]} muestra la "
                    f"menor reducción ({abs(peor[1])} puntos en el mismo horizonte). "
                    f"El contraste muestra trayectorias de desarrollo muy distintas en la región."),
    },
    {
        "titulo": "Desigualdad: el Gini de Perú cayó ~9 puntos en dos décadas, pero sigue "
                  "por encima de los mejores casos regionales",
        "detalle": (f"El índice de Gini de Perú pasó de {gini_2000:.1f} en "
                    f"{int(gini_per.index[0])} a {gini_ult:.1f} en {anio_gini} "
                    f"(puesto {rank_per} de {gini_rec.shape[0]} países con datos). La caída es "
                    f"clara, aunque aún dista de referentes como Uruguay "
                    f"({gini_rec.min():.1f}): la desigualdad sigue siendo un desafío estructural "
                    f"para la movilidad social."),
    },
]

salida = {"anio_ultimo": ANIO_ULT, "kpis": kpis, "hallazgos": hallazgos}
ruta = BASE / "web" / "data" / "hallazgos.json"
ruta.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(salida, ensure_ascii=False, indent=2))
