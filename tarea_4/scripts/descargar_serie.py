# -*- coding: utf-8 -*-
"""Descarga JSON de series del BCRP usando un navegador real (Playwright).

El BCRP activo proteccion anti-bot (PerimeterX) que bloquea httpx; el navegador
la resuelve. Las respuestas se guardan en datos/cache_bcrp/ y el servidor MCP
las usa como respaldo cuando la API en vivo no responde JSON.

Uso: uv run scripts/descargar_serie.py CODIGO DESDE HASTA [CODIGO2 DESDE2 HASTA2 ...]
"""
import json
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "datos" / "cache_bcrp"
CACHE.mkdir(parents=True, exist_ok=True)
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"


def norma_fecha(fecha: str, frecuencia: str) -> str:
    base = fecha.strip()
    if frecuencia == "Anual":
        return base[:4]
    if frecuencia == "Diaria":
        return base
    anio, mes = base.split("-")[:2]
    return f"{anio}-{int(mes)}"


def frecuencia_de(codigo: str) -> str:
    import pandas as pd
    cat = Path(__file__).resolve().parent.parent / "datos" / "catalogo_bcrp.csv"
    df = pd.read_csv(cat, sep=";", dtype=str, encoding="latin-1").fillna("")
    fila = df[df["Código de serie"] == codigo]
    if fila.empty:
        raise SystemExit(f"codigo no esta en el catalogo: {codigo}")
    return fila.iloc[0]["Frecuencia"]


def descargar(pagina, codigo: str, desde: str, hasta: str) -> Path:
    frec = frecuencia_de(codigo)
    d, h = norma_fecha(desde, frec), norma_fecha(hasta, frec)
    destino = CACHE / f"{codigo}_{d}_{h}.json"
    if destino.exists():
        print(f"[cache] {destino.name}")
        return destino
    url = f"{API}/{codigo}/json/{d}/{h}"
    print(f"[browser] {url}")
    pagina.goto(url, wait_until="domcontentloaded", timeout=90000)
    pagina.wait_for_timeout(1500)
    texto = pagina.locator("body").inner_text().strip()
    datos = json.loads(texto)
    if "periods" not in datos:
        raise SystemExit(f"respuesta sin periods: {texto[:120]}")
    destino.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] {destino.name} ({len(datos['periods'])} periodos)")
    return destino


def main():
    args = sys.argv[1:]
    if len(args) < 3 or len(args) % 3:
        raise SystemExit("uso: descargar_serie.py CODIGO DESDE HASTA [mas trios...]")
    trios = [(args[i], args[i + 1], args[i + 2]) for i in range(0, len(args), 3)]
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        for codigo, desde, hasta in trios:
            try:
                descargar(pagina, codigo, desde, hasta)
            except Exception as e:
                print(f"[error] {codigo}: {e}")
        navegador.close()


if __name__ == "__main__":
    main()
