# -*- coding: utf-8 -*-
"""Vuelca las primeras lineas de cada pagina del anexo para ubicar el cuadro."""
import pdfplumber

pdf = pdfplumber.open("datos/originales/inei_pobreza_2015_2024.pdf")
salida = []
for i in range(164, len(pdf.pages)):
    txt = (pdf.pages[i].extract_text() or "").strip()
    primeras = " | ".join(txt.split("\n")[:4])
    salida.append(f"p{i + 1}: {primeras[:220]}")
with open("scripts/_exploracion3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))
print("listo")
