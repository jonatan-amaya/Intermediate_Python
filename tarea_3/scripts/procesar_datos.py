# -*- coding: utf-8 -*-
"""Tarea 3 - Parte 1: procesamiento.

Limpia y transforma las respuestas crudas de la API del Banco Mundial:
- datos/procesados/panel_long.csv : (pais, iso3, anio, indicador, valor)
- datos/procesados/pobreza_pais_anio.csv : matriz pobreza pais x anio
- web/data/datos.json : insumo del dashboard (matrices por indicador + metadatos)
"""
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RUTA_ORIG = BASE / "datos" / "originales"
RUTA_PROC = BASE / "datos" / "procesados"
RUTA_WEB = BASE / "web" / "data"

INDICADORES = {
    "SI_POV_NAHC": ("pobreza", "Pobreza (% de la poblacion, linea nacional)"),
    "SI_POV_GINI": ("gini", "Indice de Gini (0-100)"),
    "NY_GDP_PCAP_CD": ("pbi_pc", "PBI per capita (US$ actuales)"),
}

NOMBRES = {
    "ARG": "Argentina", "BOL": "Bolivia", "BRA": "Brasil", "CHL": "Chile",
    "COL": "Colombia", "CRI": "Costa Rica", "DOM": "Rep. Dominicana",
    "ECU": "Ecuador", "SLV": "El Salvador", "GTM": "Guatemala", "HND": "Honduras",
    "MEX": "Mexico", "NIC": "Nicaragua", "PAN": "Panama", "PRY": "Paraguay",
    "PER": "Peru", "URY": "Uruguay", "VEN": "Venezuela",
}


def main():
    RUTA_PROC.mkdir(parents=True, exist_ok=True)
    RUTA_WEB.mkdir(parents=True, exist_ok=True)

    filas = []
    for archivo, (clave, _) in INDICADORES.items():
        crudo = json.loads((RUTA_ORIG / f"wb_{archivo}.json").read_text("utf-8"))
        for r in crudo[1] or []:
            if r["value"] is None:
                continue
            filas.append({
                "iso3": r["countryiso3code"],
                "pais": NOMBRES.get(r["countryiso3code"], r["country"]["value"]),
                "anio": int(r["date"]),
                "indicador": clave,
                "valor": round(float(r["value"]), 2),
            })

    df = pd.DataFrame(filas).drop_duplicates(["iso3", "anio", "indicador"])
    df = df[df["anio"] <= 2024]
    df.to_csv(RUTA_PROC / "panel_long.csv", index=False)
    print(f"panel_long: {df.shape[0]} filas | paises: {df['iso3'].nunique()} | "
          f"anios {df['anio'].min()}-{df['anio'].max()}")

    # matrices pais x anio por indicador (para el dashboard)
    datos_web = {"paises": NOMBRES, "indicadores": {
        clave: {"nombre": nombre} for clave, nombre in INDICADORES.values()}}
    for clave, _ in INDICADORES.values():
        mat = (df[df["indicador"] == clave]
               .pivot(index="iso3", columns="anio", values="valor")
               .sort_index())
        mat.to_csv(RUTA_PROC / f"{clave}_pais_anio.csv")
        datos_web[clave] = {
            "anios": [int(a) for a in mat.columns],
            "series": {iso: [None if pd.isna(v) else float(v) for v in fila]
                       for iso, fila in mat.iterrows()},
        }
        n = df[df["indicador"] == clave].shape[0]
        print(f"{clave}: {mat.shape[0]} paises x {mat.shape[1]} anios ({n} datos)")

    (RUTA_WEB / "datos.json").write_text(
        json.dumps(datos_web, ensure_ascii=False), encoding="utf-8")
    print("web/data/datos.json listo")


if __name__ == "__main__":
    main()
