# -*- coding: utf-8 -*-
"""Top-up de URLs de politica: consulta CDX, verifica HEAD y agrega a los respaldos."""
import re
import time

import pandas as pd
import requests

UA = {"User-Agent": "Tarea1DS-Python/1.0 (curso académico; uso educativo)"}
OBJETIVO = 45

cdx = ("http://web.archive.org/cdx/search/cdx?url=larepublica.pe/politica/2026/*"
       "&output=json&filter=statuscode:200&collapse=urlkey"
       "&limit=5000&from=20260201&to=20261012")
r = requests.get(cdx, headers=UA, timeout=180)
datos = r.json()
urls = [f[2] for f in datos[1:]]

patron = re.compile(r"^https://larepublica.pe/politica/\d{4}/\d{2}/\d{2}/[a-z0-9-]+$")
ya = set(pd.read_csv("datos/raw/urls_descubiertas.csv")["url"])
nuevas = [u for u in urls if patron.match(u) and u not in ya]
nuevas = sorted(nuevas, reverse=True)[:OBJETIVO + 15]  # las más recientes
print(f"candidatas nuevas: {len(nuevas)}")

aceptadas = []
for u in nuevas:
    time.sleep(1.0)
    try:
        ok = requests.head(u, headers=UA, timeout=20, allow_redirects=True).status_code == 200
    except requests.RequestException:
        ok = False
    if ok:
        aceptadas.append(u)
    if len(aceptadas) >= OBJETIVO:
        break

print(f"aceptadas (HTTP 200): {len(aceptadas)}")
for f, cols in [("datos/raw/urls_descubiertas.csv",
                 ["url", "seccion_feed", "fuente_descubrimiento"]),
                ("datos/raw/urls_verificadas.csv",
                 ["url", "seccion_feed", "fuente_descubrimiento", "url_funcional"])]:
    df = pd.read_csv(f)
    add = pd.DataFrame([{c: v for c, v in
                         zip(cols, [u, "politica",
                                    "wayback_cdx", True][:len(cols)])}
                        for u in aceptadas])
    df = pd.concat([df, add], ignore_index=True)
    df.to_csv(f, index=False)
    print(f, "->", len(df))
