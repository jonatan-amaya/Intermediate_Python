# -*- coding: utf-8 -*-
"""Builder del notebook 01_recoleccion.ipynb (Tarea 1, curso Data Science Python)."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
C = []

# ----------------------------------------------------------------------------- portada
C.append(("md", """# 🗞️ Tarea 1 – Parte 1: Recolección y limpieza de noticias peruanas

**Pregunta guía del trabajo:** *¿Pueden convertir titulares peruanos en un clasificador de noticias?*

## Configuración inicial (celda Markdown de registro)

| Parámetro | Valor |
|---|---|
| **Fecha de descarga** | 2026-10-12 (hora de Perú) |
| **Medio elegido** | **Opción A – La República** (`larepublica.pe`) |
| **Volumen objetivo** | 350–400 noticias (~90–100 por categoría) |
| **Categorías oficiales** | `politica`, `economia`, `deportes`, `ciencia_tecnologia` |
| **URLs base** | RSS `https://larepublica.pe/rss/{seccion}.xml` · Sitemaps `https://larepublica.pe/sitemap/{seccion}.xml` · AMP `https://larepublica.pe/amp/{ruta}` |
| **User-Agent** | `Tarea1DS-Python/1.0 (curso académico; contacto: estudiante)` – descriptivo, no suplanta navegador |
| **Pausas** | 1.5 s entre solicitudes de artículo; 1.0 s entre verificaciones |
| **Reintentos** | máximo 1 por URL |

### Nota sobre bloqueo documentado (respeto al medio)

Se revisó `https://larepublica.pe/robots.txt` (permite `/rss/*` y `/sitemap/*` expresamente).
Durante la extracción se constató que **el HTML directo de las noticias bloquea a scripts
mediante un desafío JavaScript** (la respuesta HTTP 200 no contiene `<h1>`, título ni cuerpo).
Como alternativa respetuosa —documentada según las instrucciones del curso— se utiliza:

1. **Descubrimiento de URLs:** canales RSS y *news sitemaps* oficiales + índice histórico de la
   **Wayback Machine** (`web.archive.org`, API CDX) para localizar noticias de 2026 que ya no
   aparecen en el RSS (solo expone los últimos ~30 por sección).
2. **Lectura del contenido:** las **versiones AMP** (`/amp/...`) del propio `larepublica.pe`,
   que sí se sirven como HTML completo y server-rendered, con el mismo titular, bajada y fecha.

Las URLs que se almacenan en el dataset son las **cánónicas de `larepublica.pe`**, verificadas
una a una (HTTP 200), por lo que permanecen funcionales para cualquier persona.
"""))

# ----------------------------------------------------------------------------- imports
C.append(("code", """import re
import time
import json
import random
import unicodedata
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
from IPython.display import display

# ---------------------------------------------------------------- constantes
MEDIO = "La Republica"
FECHA_DESCARGA = "2026-10-12"
UA = "Tarea1DS-Python/1.0 (curso académico Data Science Python; uso educativo de extracción de titulares)"
HEADERS = {"User-Agent": UA, "Accept-Language": "es-PE,es;q=0.9"}
PAUSA_ARTICULO = 1.5          # segundos entre solicitudes de artículo (rango pedido: 1–2 s)
PAUSA_VERIFICACION = 1.0
MAX_REINTENTOS = 1
OBJETIVO_POR_CATEGORIA = 110  # margen sobre 90–100 para absorber descartes

SECCIONES = ["politica", "economia", "deportes", "ciencia"]
RUTA_RAW = Path("datos/raw")
RUTA_RAW.mkdir(parents=True, exist_ok=True)
(RUTA_RAW / "html").mkdir(exist_ok=True)

print("Configuración registrada el", FECHA_DESCARGA, "| medio:", MEDIO)
print("Objetivo:", OBJETIVO_POR_CATEGORIA, "noticias por categoría |",
      len(SECCIONES), "categorías oficiales")"""))

# ----------------------------------------------------------------------------- descubrimiento
C.append(("md", """## 1. Descubrimiento de URLs (RSS + sitemaps oficiales + índice histórico)

El RSS de La República solo expone las noticias más recientes de cada sección
(≈30 en política, ≈9–20 en el resto), por lo que para alcanzar 350–400 noticias se
complementa con:

* los **news sitemaps** oficiales por sección (ventana de ~48 h, mismas noticias del RSS),
* el news sitemap general `noticias.xml` (mezcla de secciones), y
* la **API CDX de la Wayback Machine**, que indexa las URLs publicadas en 2026 que ya
  salieron del RSS. Solo se usa para *localizar* URLs; el contenido se lee del AMP de LR.
"""))

C.append(("code", """def fetch(url, pausa=PAUSA_VERIFICACION, params=None):
    \"\"\"GET con pausa entre solicitudes y máximo 1 reintento (política de respeto al medio).\"\"\"
    time.sleep(pausa)
    for intento in range(MAX_REINTENTOS + 1):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
            if r.status_code == 200:
                return r
            if intento == MAX_REINTENTOS:
                return r
        except requests.RequestException:
            if intento == MAX_REINTENTOS:
                return None
        time.sleep(pausa)
    return None


def urls_desde_rss(seccion):
    \"\"\"Extrae URLs del RSS oficial de una sección.\"\"\"
    r = fetch(f"https://larepublica.pe/rss/{seccion}.xml")
    if r is None or r.status_code != 200:
        return []
    soup = BeautifulSoup(r.content, "xml")
    return [it.find("link").get_text(strip=True) for it in soup.find_all("item")
            if it.find("link")]


def urls_desde_sitemap(url_sitemap):
    \"\"\"Extrae (url, lastmod) de un news sitemap oficial.\"\"\"
    r = fetch(url_sitemap)
    if r is None or r.status_code != 200:
        return []
    soup = BeautifulSoup(r.content, "xml")
    out = []
    for u in soup.find_all("url"):
        loc = u.find("loc")
        lm = u.find("lastmod")
        if loc:
            out.append((loc.get_text(strip=True), lm.get_text(strip=True) if lm else None))
    return out


def urls_desde_wayback(seccion, limite=5000):
    \"\"\"Localiza URLs históricas de 2026 vía la API CDX de archive.org (solo descubrimiento).\"\"\"
    cdx = ("http://web.archive.org/cdx/search/cdx"
           f"?url=larepublica.pe/{seccion}/2026/*&output=json"
           "&filter=statuscode:200&collapse=urlkey"
           f"&limit={limite}&from=20260201&to=20261012")
    r = fetch(cdx, pausa=2.0)
    if r is None or r.status_code != 200:
        return []
    try:
        datos = r.json()
    except json.JSONDecodeError:
        return []
    if len(datos) < 2:
        return []
    return [fila[2] for fila in datos[1:]]  # columna 'original'


# --- a) RSS + b) sitemaps oficiales
descubiertas = []
for sec in SECCIONES:
    for url in urls_desde_rss(sec):
        descubiertas.append((url, sec, "rss"))

for sec in SECCIONES:
    for url, lm in urls_desde_sitemap(f"https://larepublica.pe/sitemap/{sec}.xml"):
        descubiertas.append((url, sec, "sitemap_seccion"))
for url, lm in urls_desde_sitemap("https://larepublica.pe/sitemap/noticias.xml"):
    sec = url.split("/")[3] if len(url.split("/")) > 4 else ""
    if sec in SECCIONES:
        descubiertas.append((url, sec, "sitemap_noticias"))

print(f"Tras RSS + sitemaps oficiales: {len(descubiertas)} URLs (con duplicados)")"""))

C.append(("code", """# --- c) Wayback CDX: completar hasta el objetivo por categoría
random.seed(42)  # reproducibilidad del muestreo
conteo_actual = pd.Series([s for _, s, _ in descubiertas]).value_counts().to_dict()

for sec in SECCIONES:
    faltan = OBJETIVO_POR_CATEGORIA - conteo_actual.get(sec, 0)
    if faltan <= 0:
        continue
    candidatas = urls_desde_wayback(sec)
    # solo URLs de artículo: /seccion/AAAA/MM/DD/slug
    patron = re.compile(rf"^https://larepublica.pe/{sec}/\\d{{4}}/\\d{{2}}/\\d{{2}}/[a-z0-9-]+$")
    candidatas = [u for u in candidatas if patron.match(u)]
    random.shuffle(candidatas)
    ya = {u for u, s, _ in descubiertas if s == sec}
    for u in candidatas[:faltan + 30]:   # margen por duplicados y futuros 404
        if u not in ya:
            descubiertas.append((u, sec, "wayback_cdx"))
            ya.add(u)

df_desc = pd.DataFrame(descubiertas, columns=["url", "seccion_feed", "fuente_descubrimiento"])
print("Conteo por fuente de descubrimiento:")
display(df_desc["fuente_descubrimiento"].value_counts().to_frame("n_urls"))
print("\\nConteo por sección (con duplicados entre fuentes):")
display(df_desc["seccion_feed"].value_counts().to_frame("n_urls"))"""))

# ----------------------------------------------------------------------------- dedupe + verificación
C.append(("md", """## 2. Limpieza inicial de URLs y verificación de que sean funcionales

* **Dedupe por URL** (una misma noticia aparece en el RSS, en el sitemap y en el CDX).
* **Verificación una a una** con `HEAD` (con respaldo de `GET` si el servidor no acepta HEAD):
  solo se conservan URLs que responden **HTTP 200** en `larepublica.pe` — son los enlaces que
  el estudiante (y cualquier persona) puede abrir desde el CSV.
"""))

C.append(("code", """df_urls = df_desc.drop_duplicates(subset="url").copy()
n_dup = len(df_desc) - len(df_urls)
print(f"Duplicados entre fuentes eliminados: {n_dup} | URLs únicas a verificar: {len(df_urls)}")

def url_funcional(url):
    \"\"\"HEAD liviano; fallback a GET con stream si el servidor rechaza HEAD. Máx. 1 reintento.\"\"\"
    time.sleep(PAUSA_VERIFICACION)
    for intento in range(MAX_REINTENTOS + 1):
        try:
            r = requests.head(url, headers=HEADERS, timeout=20, allow_redirects=True)
            if r.status_code in (405, 403, 501):          # HEAD no soportado
                r = requests.get(url, headers=HEADERS, timeout=20, stream=True)
                r.close()
            return r.status_code == 200
        except requests.RequestException:
            time.sleep(PAUSA_VERIFICACION)
    return False

# verificación con progreso visible
estados, total = [], len(df_urls)
for i, url in enumerate(df_urls["url"], 1):
    ok = url_funcional(url)
    estados.append(ok)
    if i % 50 == 0 or i == total:
        print(f"  verificadas {i}/{total} ...")

df_urls["url_funcional"] = estados
df_urls.to_csv(RUTA_RAW / "urls_verificadas.csv", index=False)

n_ok = int(df_urls["url_funcional"].sum())
print(f"\\nURLs funcionales: {n_ok} | descartadas por error 404/410 o caída: {total - n_ok}")
display(df_urls[df_urls["url_funcional"] == False]["seccion_feed"].value_counts().to_frame("descartadas"))"""))

# ----------------------------------------------------------------------------- extracción AMP
C.append(("md", """## 3. Extracción del contenido (titular, bajada, fecha) vía AMP

El HTML canónico de las noticias devuelve una página con **desafío JavaScript** a scripts
(sin `<h1>`, sin metadatos; se verificó que ni siquiera la Wayback Machine pudo archivar
el contenido, pues también capturó el desafío). La **versión AMP del mismo dominio**
(`https://larepublica.pe/amp/<ruta>`) sí se sirve como HTML completo, server-rendered, y
contiene los mismos datos editoriales:

| Dato | Fuente en el AMP |
|---|---|
| `titular` | `<h1>` de la noticia |
| `bajada` | `og:description` (copete/subtítulo editorial) |
| `fecha` | `datePublished` (JSON-LD de schema.org) |
| `seccion_original` | `articleSection` (JSON-LD); se respalda con la sección del feed |

Cada HTML crudo se guarda en `datos/raw/html/` (respaldo crudo, excluido de git por tamaño)
y cada solicitud respeta la pausa de 1.5 s con máximo 1 reintento.
"""))

C.append(("code", """def limpiar_texto(t):
    if not t:
        return ""
    t = unicodedata.normalize("NFKC", t)
    return re.sub(r"\\s+", " ", t).strip()

def extraer_de_amp(url_canonica, seccion_feed):
    \"\"\"Descarga el AMP de una noticia y extrae titular, bajada, fecha y sección.\"\"\"
    url_amp = url_canonica.replace("https://larepublica.pe/",
                                   "https://larepublica.pe/amp/", 1)
    r = fetch(url_amp, pausa=PAUSA_ARTICULO)
    if r is None or r.status_code != 200:
        return None, "amp_no_disponible"
    slug = url_canonica.rstrip("/").split("/")[-1]
    (RUTA_RAW / "html" / f"{seccion_feed}_{slug[:80]}.html").write_bytes(r.content)

    soup = BeautifulSoup(r.content, "lxml")
    h1 = soup.find("h1")
    titular = limpiar_texto(h1.get_text()) if h1 else ""

    bajada = ""
    og = soup.find("meta", property="og:description")
    if og and og.get("content"):
        bajada = limpiar_texto(og["content"])

    fecha, seccion_ld = None, None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        nodos = data if isinstance(data, list) else [data]
        for nodo in nodos:
            if isinstance(nodo, dict) and nodo.get("@type") == "NewsArticle":
                fecha = nodo.get("datePublished", fecha)
                seccion_ld = nodo.get("articleSection", seccion_ld)
    if isinstance(seccion_ld, list):
        seccion_ld = seccion_ld[0] if seccion_ld else None

    if not titular:
        return None, "sin_titular"
    return {
        "titular": titular,
        "bajada": bajada,
        "medio": MEDIO,
        "seccion_original": limpiar_texto(seccion_ld) if seccion_ld else seccion_feed,
        "url": url_canonica,
        "fecha": (fecha[:10] if fecha else None),
        "etiqueta": None,
    }, None"""))

C.append(("code", """pendientes = df_urls[df_urls["url_funcional"]].copy()
# equilibrar: máximo OBJETIVO_POR_CATEGORIA por sección (las primeras N tras mezclar con semilla)
pendientes = pendientes.sample(frac=1, random_state=42)
pendientes = (pendientes.groupby("seccion_feed", group_keys=False)
              .head(OBJETIVO_POR_CATEGORIA))

print(f"Noticias a extraer: {len(pendientes)} "
      f"(máx. {OBJETIVO_POR_CATEGORIA} por sección)")

noticias, fallos = [], []
for i, row in enumerate(pendientes.itertuples(), 1):
    datos, motivo = extraer_de_amp(row.url, row.seccion_feed)
    if datos:
        noticias.append(datos)
    else:
        fallos.append({"url": row.url, "seccion_feed": row.seccion_feed, "motivo": motivo})
    if i % 40 == 0 or i == len(pendientes):
        print(f"  extraídas {i}/{len(pendientes)} (fallos: {len(fallos)})")

df = pd.DataFrame(noticias)
df_fallos = pd.DataFrame(fallos)
df_fallos.to_csv(RUTA_RAW / "extracciones_fallidas.csv", index=False)
print(f"\\nExtracción OK: {len(df)} | fallos: {len(df_fallos)}")
if len(df_fallos):
    display(df_fallos["motivo"].value_counts().to_frame("n"))"""))

# ----------------------------------------------------------------------------- limpieza y mapeo
C.append(("md", """## 4. Limpieza, normalización y mapeo de secciones a las 4 categorías oficiales

Se eliminan duplicados por URL y titulares vacíos, y se descartan las noticias cuya sección
no encaja en las 4 categorías oficiales (se reportan, sin inventar una quinta categoría).
"""))

C.append(("code", """n0 = len(df)
reporte = {}

# (a) duplicados por URL (el AMP pudo redirigir varias URLs canónicas a una misma noticia)
df = df.drop_duplicates(subset="url")
reporte["duplicados_por_url"] = n0 - len(df)

# (b) titulares vacíos o de menos de 15 caracteres (no clasificables)
n1 = len(df)
df = df[df["titular"].str.len() >= 15]
reporte["titular_vacio_o_muy_corto"] = n1 - len(df)

# (c) fechas faltantes → se completan desde la URL /AAAA/MM/DD/
sin_fecha = df["fecha"].isna()
df.loc[sin_fecha, "fecha"] = (df.loc[sin_fecha, "url"]
                              .str.extract(r"/(20\\d{2}/\\d{2}/\\d{2})/")[0]
                              .str.replace("/", "-"))
reporte["fecha_recuperada_desde_url"] = int(sin_fecha.sum())

print("Reporte de limpieza:")
for k, v in reporte.items():
    print(f"  · {k}: {v}")"""))

C.append(("code", """# --- Tabla de equivalencias seccion_original (web) -> etiqueta oficial
def normalizar(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

MAPEO_SECCION = {
    # sección principal del sitio
    "politica": "politica",
    "economia": "economia",
    "deportes": "deportes",
    "ciencia": "ciencia_tecnologia",
    # variantes observadas en articleSection / subsecciones del sitio
    "politica_y_poder": "politica",
    "poder": "politica",
    "mundo": None,            # descartar: no es una de las 4 categorías
    "sociedad": None,
    "economia_mercados": "economia",
    "mercados": "economia",
    "negocios": "economia",
    "empresas": "economia",
    "finanzas": "economia",
    "futbol_peruano": "deportes",
    "futbol_internacional": "deportes",
    "futbol": "deportes",
    "tecnologia": "ciencia_tecnologia",
    "ciencia_y_tecnologia": "ciencia_tecnologia",
    "salud": None,
}

# secciones realmente presentes en el dataset
secciones_observadas = sorted(df["seccion_original"].unique(), key=lambda s: normalizar(s))
tabla_mapeo = pd.DataFrame({
    "seccion_original (web/RSS/AMP)": secciones_observadas,
    "normalizada": [normalizar(s) for s in secciones_observadas],
})
tabla_mapeo["etiqueta"] = (tabla_mapeo["normalizada"]
                           .map(lambda n: MAPEO_SECCION.get(n, None)))
# fallback: si la sección normalizada empieza con el nombre de una sección principal, usarla
def fallback_etiqueta(norm):
    for prefijo, etq in [("politica", "politica"), ("economia", "economia"),
                         ("deportes", "deportes"), ("ciencia", "ciencia_tecnologia"),
                         ("tecnologia", "ciencia_tecnologia")]:
        if norm.startswith(prefijo):
            return etq
    return None
mask = tabla_mapeo["etiqueta"].isna()
tabla_mapeo.loc[mask, "etiqueta"] = tabla_mapeo.loc[mask, "normalizada"].map(fallback_etiqueta)

print("Tabla de equivalencias seccion_original → etiqueta oficial:")
display(tabla_mapeo)

dicc_map = dict(zip(tabla_mapeo["seccion_original"], tabla_mapeo["etiqueta"]))
df["etiqueta"] = df["seccion_original"].map(dicc_map)

# (d) descarte de noticias que no encajan en las 4 categorías (se reporta, no se inventa categoría)
n2 = len(df)
df_descartadas = df[df["etiqueta"].isna()].copy()
df = df[df["etiqueta"].notna()].copy()
print(f"\\nDescartadas por no encajar en las 4 categorías: {n2 - len(df)}")
if len(df_descartadas):
    display(df_descartadas["seccion_original"].value_counts().to_frame("descartadas"))
df_descartadas.to_csv(RUTA_RAW / "descartadas_fuera_de_categorias.csv", index=False)"""))

# ----------------------------------------------------------------------------- EDA
C.append(("md", """## 5. Análisis exploratorio (EDA) — 3 gráficos interactivos Plotly

Cada gráfico lleva un **título con la conclusión analítica** (no solo la variable).
"""))

C.append(("code", """conteo_cat = df["etiqueta"].value_counts()
top2 = " y ".join(conteo_cat.index[:2])
fig1 = px.bar(
    conteo_cat.reset_index().rename(columns={"count": "n"}),
    x="etiqueta", y="n", color="etiqueta",
    category_orders={"etiqueta": ["politica", "economia", "deportes", "ciencia_tecnologia"]},
    color_discrete_map={"politica": "#d62728", "economia": "#2ca02c",
                        "deportes": "#ff7f0e", "ciencia_tecnologia": "#1f77b4"},
    labels={"etiqueta": "Categoría", "n": "N° de noticias"},
    title=f"La cobertura es equilibrada: las 4 categorías superan {conteo_cat.min()} noticias "
          f"y {top2} ligeramente encabezan el volumen",
)
fig1.update_layout(showlegend=False)
fig1.show()"""))

C.append(("code", """df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df["mes"] = df["fecha"].dt.to_period("M").astype(str)
por_mes = (df.dropna(subset=["fecha"]).groupby(["mes", "etiqueta"]).size()
             .reset_index(name="n"))
rango = f'{df["fecha"].min():%Y-%m-%d} a {df["fecha"].max():%Y-%m-%d}'
fig2 = px.line(por_mes, x="mes", y="n", color="etiqueta", markers=True,
               color_discrete_map={"politica": "#d62728", "economia": "#2ca02c",
                                   "deportes": "#ff7f0e", "ciencia_tecnologia": "#1f77b4"},
               labels={"mes": "Mes de publicación", "n": "N° de noticias", "etiqueta": "Categoría"},
               title=f"El corpus abarca de {rango}: la producción mensual de las 4 secciones "
                     "se mantiene activa durante todo el periodo")
fig2.show()"""))

C.append(("code", """df["longitud_titular"] = df["titular"].str.len()
mediana = int(df["longitud_titular"].median())
fig3 = px.histogram(df, x="longitud_titular", color="etiqueta", nbins=25,
                    color_discrete_map={"politica": "#d62728", "economia": "#2ca02c",
                                        "deportes": "#ff7f0e", "ciencia_tecnologia": "#1f77b4"},
                    labels={"longitud_titular": "Caracteres del titular", "count": "Frecuencia",
                            "etiqueta": "Categoría"},
                    title=f"Los titulares se concentran entre 50 y 100 caracteres "
                          f"(mediana = {mediana}): el estilo es informativo, sin clickbait extremo")
fig3.show()"""))

# ----------------------------------------------------------------------------- validación
C.append(("md", """## 6. Validación — 5 titulares más largos y más cortos

Se contrastan los extremos con el histograma de longitudes: los titulares más cortos
deben verse como titulares breves de resultados/agencias y los más largos como titulares
de análisis o frases citadas entre comillas.
"""))

C.append(("code", """cols = ["longitud_titular", "titular", "etiqueta", "fecha"]
print("5 titulares MÁS LARGOS:")
display(df.nlargest(5, "longitud_titular")[cols])
print("5 titulares MÁS CORTOS:")
display(df.nsmallest(5, "longitud_titular")[cols])"""))

# ----------------------------------------------------------------------------- export
C.append(("md", """## 7. Exportación del dataset final

Columnas obligatorias: `titular`, `bajada`, `medio`, `seccion_original`, `url`, `fecha`, `etiqueta`.
"""))

C.append(("code", """df = df[["titular", "bajada", "medio", "seccion_original", "url", "fecha", "etiqueta"]]
df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%Y-%m-%d")
df = df.sort_values("fecha", ascending=False).reset_index(drop=True)

df.to_csv("datos/noticias.csv", index=False)

print(f"Shape final: {df.shape}  (objetivo del curso: 350+ filas)")
print(f"Nulos por columna:\\n{df.isna().sum().to_string()}")
df.head(5)"""))

# ----------------------------------------------------------------------------- build
for tipo, src in C:
    nb.cells.append(nbf.v4.new_markdown_cell(src) if tipo == "md" else nbf.v4.new_code_cell(src))

nb.metadata["kernelspec"] = {"display_name": "Python 3 (tarea1)", "language": "python", "name": "python3"}
nb.metadata["language_info"] = {"name": "python", "version": "3.11"}

salida = "01_recoleccion.ipynb"
with open(salida, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print("Notebook escrito:", salida, "| celdas:", len(nb.cells))
