# -*- coding: utf-8 -*-
"""Inspecciona el catalogo BCRP descargado (xls vnd.ms-excel desde Wayback)."""
import pandas as pd

try:
    df = pd.read_excel("catalogo_raw.xls", dtype=str)
    print("XLS OK:", df.shape)
    print("columnas:", list(df.columns))
    print(df.head(3).to_string())
except Exception as e:
    print("read_excel fallo:", repr(e)[:200])
    head = open("catalogo_raw.xls", "rb").read(300)
    print("cabecera bytes:", head[:300])
