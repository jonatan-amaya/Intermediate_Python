# -*- coding: utf-8 -*-
"""Genera datos/etiquetas_llm.csv a partir de las etiquetas dictadas por el LLM.

El LLM (Kimi Code, Moonshot AI) clasificó cada titular con el prompt documentado en
02_clasificacion.ipynb. ETIQUETAS se completa una vez conocido noticias.csv.
"""
import json
import sys

import pandas as pd

MODELO_LLM = "Kimi Code (Moonshot AI)"
FECHA = "2026-10-12"


def generar(ruta_etiquetas_json: str, ruta_noticias: str = "datos/noticias.csv",
            salida: str = "datos/etiquetas_llm.csv") -> None:
    with open(ruta_etiquetas_json, encoding="utf-8") as f:
        etiquetas = json.load(f)  # {titular: [etiqueta_llm, confianza]}

    df = pd.read_csv(ruta_noticias)
    filas, faltantes = [], []
    for titular in df["titular"]:
        if titular in etiquetas:
            etq, conf = etiquetas[titular]
            filas.append({"titular": titular, "etiqueta_llm": etq,
                          "confianza": conf, "modelo_llm": MODELO_LLM,
                          "fecha": FECHA})
        else:
            faltantes.append(titular)

    out = pd.DataFrame(filas)
    out.to_csv(salida, index=False)
    print(f"etiquetas_llm.csv: {len(out)} filas -> {salida}")
    if faltantes:
        print(f"AVISO: {len(faltantes)} titulares sin etiquetar:")
        for t in faltantes:
            print("  -", t)
        sys.exit(1)


if __name__ == "__main__":
    generar(sys.argv[1])
