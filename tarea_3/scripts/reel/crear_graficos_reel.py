# -*- coding: utf-8 -*-
"""Tarea 3 - Parte 3: genera las 6 escenas (PNG 1080x1920) del reel.

Las escenas combinan graficos matplotlib (datos reales de datos/procesados)
con titulares y subtitulos horneados, en la paleta oscura del dashboard.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

BASE = Path(__file__).resolve().parent.parent.parent
PROC = BASE / "datos" / "procesados"
SALIDA = BASE / "reel" / "recursos"
SALIDA.mkdir(parents=True, exist_ok=True)

# ---------- paleta oscura (igual que el dashboard) ----------
BG = "#0f1620"; PANEL = "#17222f"; TEXT = "#e8eef5"; MUTED = "#93a5b6"
ROJO = "#e63946"; VERDE = "#2a9d8f"; AZUL = "#4d96ff"; AMARILLO = "#ffd166"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": TEXT, "axes.edgecolor": "#27394c", "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 26,
    "axes.grid": True, "grid.color": "#27394c", "grid.linewidth": 0.8,
})
FIGSIZE = (10.8, 19.2)   # 1080 x 1920 px a dpi=100

df = pd.read_csv(PROC / "panel_long.csv")
pob = df[df["indicador"] == "pobreza"].pivot(index="iso3", columns="anio", values="valor")
gini = df[df["indicador"] == "gini"].pivot(index="iso3", columns="anio", values="valor")
NOMBRES = json.loads((BASE / "web" / "data" / "datos.json").read_text("utf-8"))["paises"]


def lienzo(kicker, titulo, pie, izq=0.12):
    fig = plt.figure(figsize=FIGSIZE, dpi=100)
    fig.text(0.08, 0.955, kicker, color=VERDE, fontsize=30, weight="bold")
    fig.text(0.08, 0.915, titulo, fontsize=48, weight="bold", va="top", wrap=True)
    fig.text(0.08, 0.035, pie, color=MUTED, fontsize=20)
    ax = fig.add_axes([izq, 0.14, 0.92 - izq - 0.06, 0.66])
    return fig, ax


def guardar(fig, nombre):
    fig.savefig(SALIDA / nombre, dpi=100)
    plt.close(fig)
    print("escena:", nombre)


# ---------- Escena 1: gancho - linea de tiempo del Peru ----------
fig, ax = lienzo("TAREA 3 · DATOS DEL BANCO MUNDIAL",
                 "En un solo año, la pobreza en Perú\nsaltó de 20% a 30%",
                 "Fuente: Banco Mundial · línea nacional · 2000-2024")
per = pob.loc["PER"].dropna()
ax.plot(per.index, per.values, color=ROJO, lw=5)
ax.fill_between(per.index, per.values, 15, color=ROJO, alpha=0.18)
ax.annotate("2020: +9.9 puntos\npor la pandemia", xy=(2020, 30.1), xytext=(2008, 38),
            color=TEXT, fontsize=26, arrowprops=dict(color=MUTED, lw=2))
ax.set_ylim(15, 62); ax.set_ylabel("Pobreza (%)")
guardar(fig, "escena1_gancho.png")

# ---------- Escena 2: Peru aun no cierra la brecha ----------
fig, ax = lienzo("HALLAZGO 1 · PERÚ",
                 "En 2024 la pobreza es 27.6%,\ntodavía 7.4 puntos sobre el 2019",
                 "Fuente: Banco Mundial · INEI (línea nacional)")
vals = [per.loc[2019], per.loc[2020], per.loc[2024]]
barras = ax.bar(["2019", "2020", "2024"], vals,
                color=[VERDE, ROJO, AMARILLO], width=0.55)
for b, v in zip(barras, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%",
            ha="center", color=TEXT, fontsize=34, weight="bold")
ax.set_ylim(0, 40); ax.set_ylabel("Pobreza en Perú (%)")
guardar(fig, "escena2_peru.png")

# ---------- Escena 3: brecha regional ----------
ult = pob[2024].dropna().sort_values(ascending=False)
top = list(ult.head(10).index)          # los 10 mas altos
if "PER" not in top:                     # asegurar que Perú aparezca
    top.append("PER")
fig, ax = lienzo("HALLAZGO 2 · LA REGIÓN ESTÁ DIVIDIDA",
                 "Honduras lidera el ranking:\n6 de cada 10 personas en pobreza",
                 "Pobreza 2024, línea nacional, % de población", izq=0.32)
vals3 = [ult[i] for i in top]
colores = [ROJO if i == "HND" else (AMARILLO if i == "PER" else VERDE)
           for i in top]
ax.barh([NOMBRES[i] for i in top], vals3, color=colores)
ax.invert_yaxis()
for y, v in enumerate(vals3):
    ax.text(v + 1, y, f"{v:.1f}%", va="center", color=TEXT, fontsize=26)
ax.set_xlim(0, 72); ax.set_xlabel("Pobreza 2024 (%)")
ax.tick_params(labelsize=22)
guardar(fig, "escena3_region.png")

# ---------- Escena 4: quien mas redujo ----------
red = {}
for iso in pob.index:
    s = pob.loc[iso].dropna()
    if len(s) >= 8 and s.index.min() <= 2002 and 2024 in s.index:
        red[iso] = s.loc[2024] - s.iloc[0]
mejor = min(red, key=red.get)
peor = max(red, key=red.get)
fig, ax = lienzo("HALLAZGO 3 · REDUCCIONES 2000-2024",
                 f"{NOMBRES[mejor]} cayó {abs(red[mejor]):.0f} puntos;\n"
                 f"{NOMBRES[peor]}, apenas {abs(red[peor]):.1f}",
                 "Cambio de la pobreza en puntos porcentuales, 2000→2024", izq=0.32)
sel = sorted(red, key=red.get)
etq = [NOMBRES[i] for i in sel]
vals = [red[i] for i in sel]
colores = [VERDE if v == vals[0] else (ROJO if v == vals[-1] else "#3a5068")
           for v in vals]
ax.barh(etq, vals, color=colores)
ax.invert_yaxis()
ax.set_xlabel("Cambio 2000 → 2024 (puntos, negativo = mejora)")
ax.tick_params(labelsize=22)
guardar(fig, "escena4_reducciones.png")

# ---------- Escena 5: desigualdad (Gini) ----------
g24 = gini[2024].dropna().sort_values()
fig, ax = lienzo("DESIGUALDAD · ÍNDICE DE GINI 2024",
                 "Perú redujo su Gini a 40.1,\npero aún no alcanza a Uruguay",
                 "Índice de Gini (0 = igualdad total) · Banco Mundial", izq=0.32)
colores = [AMARILLO if i == "PER" else (VERDE if i == "URY" else "#3a5068")
           for i in g24.index]
ax.barh([NOMBRES[i] for i in g24.index], g24.values, color=colores)
ax.invert_yaxis()
for y, v in enumerate(g24.values):
    ax.text(v + 0.6, y, f"{v:.1f}", va="center", color=TEXT, fontsize=24)
ax.set_xlim(0, 60); ax.set_xlabel("Gini 2024")
ax.tick_params(labelsize=22)
guardar(fig, "escena5_gini.png")

# ---------- Escena 6: cierre / CTA ----------
fig = plt.figure(figsize=FIGSIZE, dpi=100)
fig.text(0.08, 0.62, "Explora el dashboard\ninteractivo con los 18 países\n2000 – 2024",
         fontsize=52, weight="bold", va="top")
fig.text(0.08, 0.44, "jonatan-amaya.github.io/\nIntermediate_Python/tarea_3/web/",
         fontsize=34, color=AZUL, weight="bold")
fig.text(0.08, 0.10, "Voz clonada con IA a partir de la voz del autor (F5-TTS) · "
         "Musica sintetizada · Datos: Banco Mundial\n"
         "Tarea 3 - Data Science Python - Jonatan Amaya",
         fontsize=22, color=MUTED)
img = plt.imread(BASE / "imgs" / "dashboard_kpis_mapa.png")
ax_img = fig.add_axes([0.08, 0.68, 0.84, 0.27]); ax_img.imshow(img)
ax_img.axis("off")
guardar(fig, "escena6_cierre.png")

print("listo ->", SALIDA)
