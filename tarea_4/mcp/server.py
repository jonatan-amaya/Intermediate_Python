"""Servidor MCP del BCRP (Tarea 4, Parte 1).

Completado a partir del esqueleto de la Sesión 04: buscar_series ya venía dado;
aquí se implementan serie(), resumen(), la herramienta propia correlacion(),
un recurso bcrp://serie/{codigo} y el prompt informe(tema).

    uv run pytest            # el contrato: 10 pruebas (8 originales + 2 propias)
    uv run mcp/server.py     # el servidor, por stdio

Las cuentas las hace Python, no el modelo: cada cifra sale de una llamada repetible.
"""
import csv
import json
import re
import time
import unicodedata
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
RAIZ = AQUI.parent                    # server.py vive en mcp/; datos/ está en la raíz
CATALOGO = RAIZ / "datos" / "catalogo_bcrp.csv"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, y serie para los datos. No calcules a mano: "
    "cita siempre el código de la serie y el periodo."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: ~17 mil series en unos 7 MB. Se baja una vez y queda en datos/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str, encoding="latin-1",
                     quoting=csv.QUOTE_NONE).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


# ---------------------------------------------------------------- helpers de la API
_CACHE = RAIZ / "datos" / "cache_bcrp"
_MESES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Ago": 8, "Set": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12}
_FREC_NORMA = {"diaria": "Diaria", "mensual": "Mensual", "trimestral": "Trimestral", "anual": "Anual"}


def _norma_fecha(fecha: str, frecuencia: str) -> str:
    """La API pide 2025-1 (mensual/trimestral), 2025-01-15 (diaria), 2025 (anual)."""
    base = fecha.strip()
    if frecuencia == "Anual":
        return base[:4]
    if frecuencia == "Diaria":
        return base
    # mensual o trimestral: sin cero a la izquierda en el mes
    anio, mes = base.split("-")[:2]
    return f"{anio}-{int(mes)}"


def _periodo_iso(nombre: str, frecuencia: str) -> str:
    """'Ene.2025'->'2025-01', '01.Oct.26'->'2026-10-01', 'T1.25'->'2025-T1', '2025'->'2025'."""
    partes = nombre.strip().split(".")
    if frecuencia == "Anual":
        return partes[0]
    if frecuencia == "Trimestral":
        trim = partes[0].upper().replace("T", "")
        return f"20{partes[1]}-T{trim}"
    if frecuencia == "Diaria":
        return f"20{partes[2]}-{_MESES[partes[1]]:02d}-{int(partes[0]):02d}"
    return f"{partes[1]}-{_MESES[partes[0]]:02d}"


def _clave_periodo(p: str):
    if "-T" in p:
        a, t = p.split("-T")
        return (int(a), int(t))
    if p.count("-") == 2:
        a, m, d = p.split("-")
        return (int(a), int(m), int(d))
    a, m = p.split("-")
    return (int(a), int(m))


@cache
def _descargar(codigo: str, desde: str, hasta: str) -> list[dict]:
    """GET a la API con reintentos; si el BCRP responde HTML (anti-bot), usa la
    caché local (datos/cache_bcrp/) buscando un archivo que CUBRA el rango."""
    url = f"{API}/{codigo}/json/{desde}/{hasta}"
    respuesta = None
    ultimo = None
    for intento in range(2):
        try:
            r = httpx.get(url, timeout=60)
            if r.text.lstrip().startswith("{"):
                datos = r.json()
                if isinstance(datos, dict) and "periods" in datos:
                    respuesta = datos["periods"]
                    break
            ultimo = "respuesta HTML (anti-bot o rate limit)"
        except Exception as e:
            ultimo = str(e)
        time.sleep(2 + 2 * intento)
    if respuesta is None:
        cubre = []
        for cache in sorted(_CACHE.glob(f"{codigo}_*.json")):
            try:
                _, d, h = cache.stem.split("_")
                if _clave_periodo(d) <= _clave_periodo(desde) and \
                   _clave_periodo(h) >= _clave_periodo(hasta):
                    cubre.append((cache, d, h))
            except ValueError:
                continue
        if cubre:
            # preferir el archivo mas chico que cubra el rango
            cache = min(cubre, key=lambda t: len(t[0].read_text(encoding="utf-8")))[0]
            periodos = json.loads(cache.read_text(encoding="utf-8"))["periods"]
            respuesta = [p for p in periodos
                         if _clave_periodo(_periodo_iso(p["name"], _ficha(codigo)["frecuencia"]))
                         >= _clave_periodo(desde)
                         and _clave_periodo(_periodo_iso(p["name"], _ficha(codigo)["frecuencia"]))
                         <= _clave_periodo(hasta)]
        else:
            raise ToolError(
                f"La API del BCRP no respondió JSON para {codigo} ({desde} a {hasta}): {ultimo}. "
                f"Precarguen con: uv run scripts/descargar_serie.py {codigo} {desde} {hasta}")
    return respuesta


def _datos_serie(codigo: str, desde: str, hasta: str) -> dict:
    """Devuelve {'codigo', 'nombre', 'frecuencia', 'datos': [{'periodo','valor'}], 'fuente'}."""
    ficha = _ficha(codigo)
    frec = ficha["frecuencia"]
    periodos = _descargar(codigo, _norma_fecha(desde, frec), _norma_fecha(hasta, frec))
    datos = []
    for p in periodos:
        valor = p["values"][0].strip()
        if valor in ("", "n.d."):
            continue
        datos.append({"periodo": _periodo_iso(p["name"], frec), "valor": float(valor)})
    return {**ficha, "datos": datos,
            "fuente": f"{API}/{codigo}/json/{_norma_fecha(desde, frec)}/{_norma_fecha(hasta, frec)}"}


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Datos de una serie oficial del BCRP entre dos periodos.

    Fechas según frecuencia: '2025-1' o '2025-01' (mensual y trimestral),
    '2025-01-15' (diaria), '2025' (anual). Devuelve periodo en ISO ('2025-01',
    '2026-10-01', '2025-T1', '2025') y omite los 'n.d.'.
    """
    return _datos_serie(codigo, desde, hasta)


@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Estadísticos de una serie en un período: primero, último, cambio absoluto,
    variación porcentual, promedio, máximo y mínimo (los tres últimos con su periodo).
    Usarla para que el modelo nunca haga cuentas a mano.
    """
    d = _datos_serie(codigo, desde, hasta)
    datos = d["datos"]
    if not datos:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}.")
    vals = [x["valor"] for x in datos]
    primero, ultimo = datos[0], datos[-1]
    cambio = ultimo["valor"] - primero["valor"]
    variacion_pct = (cambio / primero["valor"] * 100) if primero["valor"] else None
    imax = max(range(len(vals)), key=lambda i: vals[i])
    imin = min(range(len(vals)), key=lambda i: vals[i])
    return {"codigo": d["codigo"], "nombre": d["nombre"], "frecuencia": d["frecuencia"],
            "periodo": {"desde": primero["periodo"], "hasta": ultimo["periodo"]},
            "n": len(datos),
            "primero": primero, "ultimo": ultimo,
            "cambio": round(cambio, 4), "variacion_pct": round(variacion_pct, 2),
            "promedio": round(sum(vals) / len(vals), 4),
            "maximo": datos[imax], "minimo": datos[imin],
            "fuente": d["fuente"]}


@mcp.tool(annotations=SOLO_LECTURA)
def correlacion(codigo_a: str, codigo_b: str, desde: str, hasta: str) -> dict:
    """Correlación de Pearson entre dos series del BCRP en períodos compatibles.

    Alinea las observaciones por periodo (solo pares con dato en ambas) y descarta
    faltantes de forma pareada. Exige la misma frecuencia y al menos 4 pares.
    Devuelve n, r, el período común y una guía de interpretación del signo.
    """
    fa, fb = _ficha(codigo_a), _ficha(codigo_b)
    if fa["frecuencia"] != fb["frecuencia"]:
        raise ToolError(f"Frecuencias distintas: {codigo_a} es {fa['frecuencia']} y "
                        f"{codigo_b} es {fb['frecuencia']}. Usen series de la misma frecuencia.")
    da, db = _datos_serie(codigo_a, desde, hasta), _datos_serie(codigo_b, desde, hasta)
    va = {x["periodo"]: x["valor"] for x in da["datos"]}
    vb = {x["periodo"]: x["valor"] for x in db["datos"]}
    comunes = sorted(set(va) & set(vb))
    pares = [(va[p], vb[p]) for p in comunes]
    if len(pares) < 4:
        raise ToolError(f"Solo {len(pares)} pares de observaciones comunes "
                        f"({codigo_a} vs {codigo_b}); se requieren al menos 4.")
    s = pd.Series([p[0] for p in pares]).corr(pd.Series([p[1] for p in pares]))
    r = round(float(s), 4)
    guia = ("positiva fuerte" if r > 0.7 else "positiva moderada" if r > 0.3 else
            "débil" if r > -0.3 else "negativa moderada" if r > -0.7 else "negativa fuerte")
    return {"codigo_a": codigo_a, "nombre_a": fa["nombre"],
            "codigo_b": codigo_b, "nombre_b": fb["nombre"],
            "frecuencia": fa["frecuencia"], "n": len(pares),
            "periodo": {"desde": comunes[0], "hasta": comunes[-1]},
            "r": r, "interpretacion": f"correlacion {guia} (r={r})",
            "fuente": "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"}


@mcp.resource("bcrp://serie/{codigo}")
def ficha_serie(codigo: str) -> str:
    """Ficha descriptiva de una serie oficial: nombre, categoría, frecuencia e inicio."""
    f = _ficha(codigo)
    return (f"{f['codigo']} · {f['nombre']}\n"
            f"Categoría: {f['categoria']}\nFrecuencia: {f['frecuencia']}\n"
            f"Disponible desde: {f['inicio']} · Última actualización: {f['actualizada']}\n"
            f"Fuente: {API}/{f['codigo']}")


@mcp.prompt
def informe(tema: str) -> str:
    """Plantilla para interpretar indicadores del BCRP con citas verificables."""
    return (f"Escribe un análisis breve sobre: {tema}.\n\n"
            "Reglas obligatorias:\n"
            "1. Toda cifra debe llevar código de serie, período y fuente (BCRP).\n"
            "2. Obtén los números con las herramientas del servidor (buscar_series, serie, "
            "resumen, correlacion); nunca calcules ni recuerdes cifras de memoria.\n"
            "3. Separa hechos (dato + código) de interpretación.\n"
            "4. Si una serie no existe o no tiene datos, dilo y propone un código alternativo.\n"
            "5. Cierra con las limitaciones del análisis (período, cobertura).")


if __name__ == "__main__":
    mcp.run()
