# -*- coding: utf-8 -*-
"""Intenta extraer el cuadro de pobreza por departamento con pypdf (modo layout)."""
from pypdf import PdfReader

reader = PdfReader("datos/originales/inei_pobreza_2015_2024.pdf")
salida = []
for i in range(210, 228):
    try:
        txt = reader.pages[i].extract_text(extraction_mode="layout") or ""
    except TypeError:
        txt = reader.pages[i].extract_text() or ""
    salida.append(f"===== pagina {i + 1} =====\n{txt[:1500]}")
with open("scripts/_pypdf_layout.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))
print("listo")
