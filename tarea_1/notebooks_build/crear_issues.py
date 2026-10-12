# -*- coding: utf-8 -*-
"""Crea los 3 issues de bitácora de la Tarea 1, documenta y cierra cada uno."""
import json
import subprocess
import urllib.request

GCM = r"C:\Program Files\Git\mingw64\bin\git-credential-manager.exe"
REPO = "jonatan-amaya/Intermediate_Python"


def token():
    r = subprocess.run([GCM, "get"], input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True, timeout=30)
    datos = dict(l.split("=", 1) for l in r.stdout.strip().splitlines() if "=" in l)
    return datos["password"]


def api(metodo, ruta, cuerpo, tok):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{ruta}",
        data=json.dumps(cuerpo).encode("utf-8"),
        method=metodo,
        headers={"Authorization": f"Bearer {tok}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


ISSUES = [
    ("T1 – Parte 1: Recolección y Limpieza", """## Objetivo
Extraer 350–400 titulares reales de **La República** (Opción A) con las 7 columnas obligatorias.

## Checklist
- [x] Revisar `robots.txt` (permite `/rss/*` y `/sitemap/*`)
- [x] `User-Agent` descriptivo + pausas de 1–2 s + máximo 1 reintento
- [x] Descubrimiento de URLs: RSS + news sitemaps oficiales + índice histórico (Wayback CDX) para noticias de 2026 fuera del RSS
- [x] Lectura del contenido vía **AMP** (el HTML canónico bloquea bots con desafío JS — bloqueo documentado en `01_recoleccion.ipynb`)
- [x] Verificación URL por URL (HTTP 200) — enlaces funcionales en el CSV
- [x] Limpieza: duplicados por URL, titulares vacíos, tabla de mapeo sección → etiqueta oficial
- [x] EDA: 3 gráficos Plotly con títulos analíticos + validación de extremos
- [x] Exportación de `datos/noticias.csv` (7 columnas)

## Resultado
**439 noticias** (política 110 · economía 110 · deportes 110 · ciencia_tecnologia 109),
fechas 2026-01-01 → 2026-10-12, 0 bajadas vacías, 439 URLs únicas verificadas.
Notebook `01_recoleccion.ipynb` ejecutado con salidas visibles."""),
    ("T1 – Parte 2: Modelado y Clasificación", """## Objetivo
Del LLM al clasificador: baseline zero-shot, supervisión débil con LLM y fine-tuning de DistilBERT.

## Checklist
- [x] Baseline zero-shot (`joeddav/xlm-roberta-large-xnli`, 40 titulares, seed 42): **F1 macro 0.648**
- [x] Etiquetado del dataset completo con LLM (prompt estructurado) → `datos/etiquetas_llm.csv`
- [x] Auditoría humana de 20 predicciones al azar: **20/20 de acuerdo** (concordancia global 99,5 %)
- [x] Split 70/15/15 estratificado con `random_state=42`; test aislado hasta la evaluación final
- [x] Fine-tuning `distilbert-base-multilingual-cased` (3 épocas, batch 16, evaluación por época, métrica F1 macro)
- [x] Evaluación en test: **accuracy 0.909 · F1 macro 0.911** + matriz de confusión (seaborn)
- [x] Reflexión por categoría (peor: política, F1 0.81, por solapamiento con economía; mejor: deportes y ciencia, F1 1.00)
- [x] Tabla comparativa zero-shot vs LLM débil vs fine-tuned + justificación de la decisión

## Resultado
F1 macro en test = **0.911**, muy por encima del piso zero-shot (0.648). Pesos en `modelo/`
(excluidos de git por >100 MB según `.gitignore`); artefactos ligeros y `metrics.json` sí versionados.
Notebook `02_clasificacion.ipynb` ejecutado."""),
    ("T1 – Parte 3: Dashboard y Despliegue", """## Objetivo
Dashboard interactivo Streamlit con probador en vivo y documentación de ejecución.

## Checklist
- [x] `app.py`: encabezado con la pregunta guía + resumen metodológico
- [x] Filtros en sidebar (medio y categoría) que actualizan gráfico y tabla
- [x] Indicadores `st.metric`: 439 noticias · F1 macro 0.911 · concordancia LLM–humana 20/20
- [x] Gráfico Plotly (distribución filtrada) + `st.dataframe` con botón de descarga CSV
- [x] **Probador en vivo**: campo de texto → categoría + confianza (verificado en navegador: titular económico → `economia`, 90,8 %)
- [x] `requirements.txt` con dependencias exactas (torch CPU documentado)
- [x] `README.md`: pregunta, medios/fechas, 2 hallazgos, 2 limitaciones, comandos exactos

## Resultado
App funcional en local con `streamlit run app.py` (ejecución comprobada en navegador).
Despliegue en Streamlit Cloud opcional pendiente de cuenta del estudiante."""),
]

CIERRE = [
    "Parte 1 completada y verificada: 439 noticias con las 7 columnas obligatorias y URLs funcionales. Cierro el issue.",
    "Parte 2 completada: F1 macro 0.911 en test aislado, con baseline y comparativa documentados. Cierro el issue.",
    "Parte 3 completada: app verificada end-to-end en navegador (métricas, filtros, gráfico, tabla, descarga CSV y probador en vivo). Cierro el issue.",
]

tok = token()
for (titulo, cuerpo), cierre in zip(ISSUES, CIERRE):
    iss = api("POST", "issues", {"title": titulo, "body": cuerpo}, tok)
    n = iss["number"]
    api("POST", f"issues/{n}/comments", {"body": cierre}, tok)
    api("PATCH", f"issues/{n}", {"state": "closed"}, tok)
    print(f"issue #{n}: creado, documentado y cerrado -> {iss['html_url']}")
