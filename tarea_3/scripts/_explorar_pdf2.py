# -*- coding: utf-8 -*-
"""Localiza en el anexo estadistico el cuadro de pobreza por departamento."""
import pdfplumber

pdf = pdfplumber.open("datos/originales/inei_pobreza_2015_2024.pdf")
salida = []
for i in range(164, len(pdf.pages)):
    txt = pdf.pages[i].extract_text() or ""
    tl = txt.lower()
    if "departamento" in tl and ("incidencia de la pobreza monetaria" in tl
                                 or "pobreza monetaria total" in tl):
        salida.append(f"===== pagina {i + 1} =====")
        salida.append(txt[:900])
with open("scripts/_exploracion2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))
print("listo")
