# -*- coding: utf-8 -*-
from pathlib import Path

ruta = Path("datos/catalogo_bcrp.csv")
malas = []
with open(ruta, encoding="latin-1") as f:
    for i, linea in enumerate(f, 1):
        n = linea.count(";")
        if i > 1 and n != 18:
            malas.append((i, n, linea[:90]))
print("lineas con != 18 ';':", len(malas))
for m in malas[:5]:
    print(m)
