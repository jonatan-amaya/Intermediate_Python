# -*- coding: utf-8 -*-
"""Genera el grafico BCRP del informe (IPC anual y tipo de cambio 2020-2024)
y vuelca las cifras clave para el informe."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
C = RAIZ / "datos" / "cache_bcrp"

def cargar(nombre):
    return json.loads((C / nombre).read_text(encoding="utf-8"))["periods"]

ipc = [(p["name"], float(p["values"][0])) for p in cargar("PN01273PM_2020-1_2024-12.json")
       if p["values"][0].strip() not in ("", "n.d.")]
tc = [(p["name"], float(p["values"][0])) for p in cargar("PN01215PM_2020-1_2024-12.json")
      if p["values"][0].strip() not in ("", "n.d.")]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7.4), sharex=False)
ax1.plot(range(len(ipc)), [v for _, v in ipc], color="#e63946", lw=2)
ax1.set_xticks(range(0, len(ipc), 12))
ax1.set_xticklabels([n.split(".")[1] for n, _ in ipc][::12])
ax1.set_title("Inflación interanual Lima (IPC, var% 12 meses): pico de 8.8% en jun-2022\n"
              "y retorno al rango meta desde mediados de 2023 (BCRP PN01273PM)",
              fontsize=11.5, fontweight="bold")
ax1.set_ylabel("var% anual")
ax1.spines[["top", "right"]].set_visible(False)
pico = max(ipc, key=lambda t: t[1])
ax1.annotate(f"pico {pico[1]:.1f}% ({pico[0]})", xy=(ipc.index(pico), pico[1]),
             xytext=(ipc.index(pico) - 14, pico[1] - 0.6),
             arrowprops=dict(color="#555", lw=1), fontsize=9)

ax2.plot(range(len(tc)), [v for _, v in tc], color="#2a9d8f", lw=2)
ax2.set_xticks(range(0, len(tc), 12))
ax2.set_xticklabels([n.split(".")[1] for n, _ in tc][::12])
ax2.set_title("Tipo de cambio interbancario venta, fin de periodo (S/ por US$):\n"
              "de 3.38 (ene-2020) a 3.77 (dic-2024), depreciación acumulada ~11.6% (BCRP PN01215PM)",
              fontsize=11.5, fontweight="bold")
ax2.set_ylabel("S/ por US$")
ax2.spines[["top", "right"]].set_visible(False)

fig.text(0.01, 0.006, "Fuente: BCRP, series oficiales vía servidor MCP (estadisticas.bcrp.gob.pe)",
         fontsize=8, color="#555")
fig.tight_layout(rect=[0, 0.02, 1, 1])
(RAIZ / "figuras").mkdir(exist_ok=True)
fig.savefig(RAIZ / "figuras" / "bcrp_ipc_tc_2020_2024.png", dpi=200)
print("[ok] figuras/bcrp_ipc_tc_2020_2024.png")

# cifras para el informe
import statistics
vals = [v for _, v in ipc]
print("IPC anual 2020-2024: min %.2f (%s), max %.2f (%s), promedio %.2f" %
      (min(vals), ipc[vals.index(min(vals))][0], max(vals), ipc[vals.index(max(vals))][0],
       statistics.mean(vals)))
print("IPC dic-2024: %.2f" % vals[-1])
tcv = [v for _, v in tc]
print("TC: ene-2020 %.4f -> dic-2024 %.4f (var %.1f%%)" %
      (tcv[0], tcv[-1], (tcv[-1] / tcv[0] - 1) * 100))
t24 = [v for n, v in tc if n.endswith("2024")]
print("TC promedio 2024: %.4f" % statistics.mean(t24))
