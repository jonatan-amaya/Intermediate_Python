# -*- coding: utf-8 -*-
"""Skill mapeando-enaho: mapa coroplético de pobreza por departamento.

Une por codigo (ubigeo[:2] = FIRST_IDDP, texto), exige 25/25 con dato y valida
contra referencias/pobreza_departamento_2024.csv. Salida: mapas/ + validacion.
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
BASE = RAIZ / "salidas" / "personas_2024.parquet"
GEO = RAIZ / "datos" / "peru_departamental_simple.geojson"
REF = RAIZ / "referencias" / "pobreza_departamento_2024.csv"
MAPAS = RAIZ / "mapas"


def main():
    for ruta in (BASE, GEO, REF):
        if not ruta.exists():
            sys.exit(f"Falta {ruta}.")
    MAPAS.mkdir(exist_ok=True)

    df = pd.read_parquet(BASE)
    ind = (df.groupby("departamento")
             .apply(lambda d: d.loc[d.pobre, "facpob07"].sum() / d.facpob07.sum() * 100,
                    include_groups=False)
             .rename("pobreza_pct")
             .reset_index())

    geo = gpd.read_file(GEO)
    geo["FIRST_IDDP"] = geo["FIRST_IDDP"].astype(str).str.zfill(2)
    ind["departamento"] = ind["departamento"].astype(str).str.zfill(2)
    if geo["FIRST_IDDP"].duplicated().any():
        sys.exit("ERROR: geometrias con FIRST_IDDP duplicado.")

    mapa = geo.merge(ind, left_on="FIRST_IDDP", right_on="departamento",
                     how="left", validate="1:1")
    faltan = mapa[mapa.pobreza_pct.isna()]
    if len(faltan):
        sys.exit(f"ERROR: departamentos sin dato: {faltan.FIRST_IDDP.tolist()}")
    if len(mapa) != 25:
        sys.exit(f"ERROR: se esperaban 25 unidades, hay {len(mapa)}.")

    # validacion numerica por departamento (referencia de la sesion 16)
    ref = pd.read_csv(REF, dtype={"ccdd": str})
    ref2 = ref.set_index("ccdd")["pobreza_pct"]

    fig, ax = plt.subplots(figsize=(9.5, 11))
    mapa.plot(column="pobreza_pct", ax=ax, cmap="OrRd", vmin=0,
              edgecolor="white", linewidth=0.7,
              legend=True,
              legend_kwds={"label": "Pobreza monetaria (% de personas)",
                           "orientation": "horizontal", "shrink": 0.6,
                           "pad": 0.03})
    mapa.apply(lambda r: ax.annotate(
        f"{r.NOMBDEP.title()}\n{r.pobreza_pct:.1f}",
        xy=r.geometry.representative_point().coords[0],
        ha="center", va="center", fontsize=7.2), axis=1)
    ax.set_title("Pobreza monetaria por departamento, ENAHO 2024\n"
                 "(25 unidades territoriales; Lima y Callao separados)",
                 fontsize=13, fontweight="bold")
    ax.axis("off")
    fig.text(0.01, 0.008,
             "Fuente: INEI, ENAHO 2024 · % de personas (ponderado, facpob07)",
             fontsize=8, color="#555")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(MAPAS / "pobreza_departamento.png", dpi=200)
    plt.close(fig)

    # validacion numerica por departamento
    lineas = ["VALIDACION MAPA · Skill mapeando-enaho",
              f"Unidades territoriales: {len(mapa)}/25 (todas con dato)",
              f"Lima (15) y Callao (07) separados: "
              f"{'OK' if {'15', '07'} <= set(mapa.FIRST_IDDP) else 'FALTA'}", ""]
    ref2 = ref.set_index("ccdd")["pobreza_pct"]
    ind2 = ind.set_index("departamento")["pobreza_pct"]
    maxdif = 0.0
    for ccdd in sorted(ref2.index):
        esperado, calculado = ref2[ccdd], ind2.get(ccdd)
        dif = abs(esperado - calculado)
        maxdif = max(maxdif, dif)
        lineas.append(f"  [{ 'OK' if dif <= 0.6 else 'REVISAR' }] {ccdd}: "
                      f"calculado {calculado:.1f} vs referencia {esperado:.1f} (dif {dif:.2f})")
    lineas.append(f"\nMaxima diferencia vs referencia: {maxdif:.2f} puntos")
    (RAIZ / "salidas" / "validacion_mapa.txt").write_text(
        "\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas[:4]))
    print(f"[ok] mapas/pobreza_departamento.png · max dif vs referencia: {maxdif:.2f} pts")


if __name__ == "__main__":
    main()
