# -*- coding: utf-8 -*-
"""Tarea 3 - Parte 1: obtención de datos (Banco Mundial, API pública sin token).

Indicadores:
- SI.POV.NAHC : Pobreza (linea nacional, % de la poblacion)
- SI.POV.GINI : Indice de Gini (desigualdad)
- NY.GDP.PCAP.CD : PBI per capita (US$ actuales)

Cobertura: 18 paises de America Latina y el Caribe, 2000-2024.
Salida: datos/originales/wb_<indicador>.json (respuesta cruda de la API).
"""
import json
from pathlib import Path

import requests

RUTA = Path(__file__).resolve().parent.parent / "datos" / "originales"

PAISES = ["ARG", "BOL", "BRA", "CHL", "COL", "CRI", "DOM", "ECU", "SLV",
          "GTM", "HND", "MEX", "NIC", "PAN", "PRY", "PER", "URY", "VEN"]
INDICADORES = {
    "SI.POV.NAHC": "Pobreza (% poblacion, linea nacional)",
    "SI.POV.GINI": "Indice de Gini",
    "NY.GDP.PCAP.CD": "PBI per capita (US$ actuales)",
}
ANIOS = "2000:2024"


def descargar(indicador):
    destino = RUTA / f"wb_{indicador.replace('.', '_')}.json"
    if destino.exists() and destino.stat().st_size > 100:
        print(f"[ok] ya existe {destino.name}")
        return
    url = (f"https://api.worldbank.org/v2/country/{';'.join(PAISES)}"
           f"/indicator/{indicador}?format=json&date={ANIOS}&per_page=2000")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    destino.write_bytes(r.content)
    datos = r.json()[1] or []
    n = sum(1 for x in datos if x["value"] is not None)
    print(f"[ok] {indicador}: {len(datos)} registros ({n} con valor) -> {destino.name}")


def main():
    RUTA.mkdir(parents=True, exist_ok=True)
    for ind in INDICADORES:
        descargar(ind)


if __name__ == "__main__":
    main()
