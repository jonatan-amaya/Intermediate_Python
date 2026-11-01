# -*- coding: utf-8 -*-
"""Exploración del PDF del INEI: localiza el cuadro de pobreza por departamento."""
import pdfplumber

salida = []
pdf = pdfplumber.open("datos/originales/inei_pobreza_2015_2024.pdf")
salida.append(f"paginas: {len(pdf.pages)}")
for i, pag in enumerate(pdf.pages):
    t = (pag.extract_text() or "").lower()
    if "departamento" in t and ("evoluci" in t or "cuadro" in t):
        txt = pag.extract_text() or ""
        salida.append(f"--- pagina {i + 1}")
        salida.append(txt[:500].replace("\n", " | "))
with open("scripts/_exploracion.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))
print("listo")
