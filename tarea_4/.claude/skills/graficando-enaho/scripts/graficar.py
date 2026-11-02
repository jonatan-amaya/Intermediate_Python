# -*- coding: utf-8 -*-
"""Skill graficando-enaho: indicadores de pobreza ponderados (facpob07).

Uso: python graficar.py [area|sexo|departamentos|todos]
Salida: figuras/*.png (200 dpi)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
BASE = RAIZ / "salidas" / "personas_2024.parquet"
FIGS = RAIZ / "figuras"
FUENTE = "Fuente: INEI, ENAHO 2024 · % de personas (estimación ponderada, facpob07)"
COLOR = "#2a9d8f"


def tasa(df, cond):
    den = df.loc[cond, "facpob07"].sum()
    return df.loc[cond & df.pobre, "facpob07"].sum() / den * 100


def barras(etiquetas, valores, titulo, ylabel, ruta, xmax=None):
    fig, ax = plt.subplots(figsize=(8, 5.2))
    b = ax.bar(etiquetas, valores, color=COLOR, width=0.58)
    for r, v in zip(b, valores):
        ax.text(r.get_x() + r.get_width() / 2, v + (xmax or max(valores)) * 0.015,
                f"{v:.1f}%", ha="center", fontsize=11, fontweight="bold")
    ax.set_title(titulo, fontsize=12.5, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, (xmax or max(valores) * 1.18))
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.012, FUENTE, fontsize=8, color="#555")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    print(f"[ok] {ruta.name}: " + ", ".join(f"{e} {v:.1f}%" for e, v in zip(etiquetas, valores)))


def graf_area(df):
    valores = [tasa(df, df.urbano), tasa(df, ~df.urbano)]
    barras(["Urbana", "Rural"], valores,
           "La pobreza rural supera en ~15 puntos a la urbana (ENAHO 2024)",
           "Pobreza monetaria (%)", FIGS / "pobreza_area.png", xmax=50)


def graf_sexo(df):
    valores = [tasa(df, df.sexo == "Hombre"), tasa(df, df.sexo == "Mujer")]
    barras(["Hombres", "Mujeres"], valores,
           "La pobreza es apenas mayor en mujeres: brecha de género menor a 1 punto",
           "Pobreza monetaria (%)", FIGS / "pobreza_sexo.png")


def graf_departamentos(df):
    t = (df.groupby("departamento")
           .apply(lambda d: d.loc[d.pobre, "facpob07"].sum() / d.facpob07.sum() * 100,
                  include_groups=False)
           .sort_values())
    nombres = pd.read_csv(RAIZ / "referencias" / "pobreza_departamento_2024.csv",
                          dtype={"ccdd": str}).set_index("ccdd")["departamento"]
    etq = [f"{nombres.get(i, i).title()}" for i in t.index]
    fig, ax = plt.subplots(figsize=(8.6, 8.2))
    b = ax.barh(etq, t.values, color=COLOR)
    for r, v in zip(b, t.values):
        ax.text(v + 0.6, r.get_y() + r.get_height() / 2, f"{v:.1f}%",
                va="center", fontsize=9)
    ax.set_title("Pobreza monetaria por departamento, 2024: 6 de cada 10 personas pobres\n"
                 "están en el sur andino y la selva norte", fontsize=12, fontweight="bold")
    ax.set_xlabel("Pobreza monetaria (%)")
    ax.set_xlim(0, max(t.values) * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.008, FUENTE, fontsize=8, color="#555")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(FIGS / "pobreza_departamentos.png", dpi=200)
    plt.close(fig)
    print(f"[ok] pobreza_departamentos.png: min {t.min():.1f}% ({etq[0]}), "
          f"max {t.max():.1f}% ({etq[-1]})")


def main():
    tema = sys.argv[1] if len(sys.argv) > 1 else "todos"
    if not BASE.exists():
        sys.exit("No existe salidas/personas_2024.parquet. Ejecuta primero limpiando-enaho.")
    FIGS.mkdir(exist_ok=True)
    df = pd.read_parquet(BASE)
    if tema in ("area", "todos"):
        graf_area(df)
    if tema in ("sexo", "todos"):
        graf_sexo(df)
    if tema in ("departamentos", "todos"):
        graf_departamentos(df)


if __name__ == "__main__":
    main()
