# -*- coding: utf-8 -*-
"""Inspecciona el esquema del catalogo BCRP descargado."""
import pandas as pd

df = pd.read_csv("datos/catalogo_bcrp.csv", sep=None, engine="python",
                 dtype=str, nrows=5, encoding="latin-1")
print("columnas:", list(df.columns))
print(df.head(3).to_string())
full = pd.read_csv("datos/catalogo_bcrp.csv", sep=None, engine="python",
                   dtype=str, encoding="latin-1")
print("filas:", len(full))
