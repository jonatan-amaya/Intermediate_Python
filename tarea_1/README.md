# 🗞️ Tarea 1 – Noticias peruanas: del titular al clasificador

> **Pregunta guía:** *¿Pueden convertir titulares peruanos en un clasificador de noticias?*

Pipeline completo: extracción de titulares reales de **La República** (`larepublica.pe`),
etiquetado semiautomático con LLM, *fine-tuning* de un Transformer ligero
(**DistilBERT multilingüe**) y un **dashboard interactivo en Streamlit** que clasifica
titulares nuevos en vivo con su nivel de confianza.

**Estudiante:** Jonatan Amaya ([@jonatan-amaya](https://github.com/jonatan-amaya))

---

## 📊 Resultados (conjunto de test reservado, 15 %)

| Enfoque | Accuracy | F1 macro | Base de evaluación |
|---|---|---|---|
| Zero-shot (`joeddav/xlm-roberta-large-xnli`, sin entrenar) | 0.650 | 0.648 | 40 titulares (muestra) |
| LLM débil (prompt estructurado, Kimi Code) | 0.995 | 0.995 | 439 titulares (completo) |
| **DistilBERT fine-tuned (elegido)** | **0.909** | **0.911** | 66 titulares (test aislado) |

Auditoría humana de 20 predicciones del LLM: **20/20 de acuerdo (100 %)**; la concordancia
global LLM–sección editorial sobre las 439 noticias es 99,5 % (ver `02_clasificacion.ipynb`).

## 📰 Medio y fechas de extracción

* **Medio elegido:** Opción A — **La República** (`larepublica.pe`).
* **Fecha de descarga:** 2026-10-12 (hora de Perú).
* **Rango de publicación de las noticias:** 2026-01-01 a 2026-10-12.
* **Volumen:** **439 noticias** (política 110 · economía 110 · deportes 110 · ciencia y tecnología 109),
  con las 7 columnas obligatorias: `titular`, `bajada`, `medio`, `seccion_original`, `url`, `fecha`, `etiqueta`.
* **Categorías oficiales:** `politica`, `economia`, `deportes`, `ciencia_tecnologia`.

### Cómo se recolectó (y el bloqueo documentado)

1. Se revisó `robots.txt` (permite expresamente `/rss/*` y `/sitemap/*`).
2. El **HTML canónico de las noticias bloquea a scripts con un desafío JavaScript**
   (HTTP 200 sin contenido; ni siquiera la Wayback Machine archivó el cuerpo). Se
   documenta en `01_recoleccion.ipynb`.
3. Descubrimiento de URLs: **RSS** y **news sitemaps** oficiales (últimas ~48 h) +
   **API CDX de la Wayback Machine** para las noticias de 2026 que ya salieron del RSS.
4. Lectura del contenido: versiones **AMP** del propio `larepublica.pe` (`/amp/...`), que sí
   se sirven como HTML completo y contienen titular, bajada (`og:description`), fecha
   (`datePublished`) y sección (`articleSection`).
5. Cada URL almacenada fue **verificada una a una (HTTP 200)**; las solicitudes usaron
   `User-Agent` descriptivo, pausas de 1–2 s y máximo 1 reintento. Respaldo crudo en
   `datos/raw/` (excluido de git por tamaño; ver `.gitignore`).

## 🔍 Hallazgos analíticos

1. **El corpus quedó equilibrado por categoría (110/110/110/109), pero no por tiempo:**
   octubre 2026 concentra 126 noticias (29 % del total) por la cobertura de las Elecciones
   Regionales y Municipales del 4 de octubre —incluida una serie formulaica de resultados
   ONPE en política— y por la ventana natural del RSS. El split estratificado mitiga el
   sesgo temporal, pero es un riesgo a vigilar si se reentrena con otra ventana de fechas.
2. **Los titulares de La República son largos e informativos** (mediana 106 caracteres,
   rango 49–162) y suelen incluir la cita textual del protagonista
   (`...: "No se puede permitir estas actitudes"`), lo que da al modelo vocabulario
   muy discriminatorio por categoría (instituciones en política, clubes y torneos en
   deportes, cifras y reguladores en economía).

## ⚠️ Limitaciones técnicas

1. **Dependencia del AMP y del archivo histórico:** si La República retira o cambia sus
   páginas AMP, habrá que rehacer la extracción (el HTML canónico sigue bloqueado a bots);
   y la cobertura de noticias antiguas depende de que la Wayback Machine las haya indexado
   (sesgo de disponibilidad que el RSS no tiene).
2. **Taxonomía editorial heredada:** el modelo aprende la sección donde el diario publicó
   la noticia, no una verdad temática absoluta —la sección *ciencia* mezcla tecnología,
   salud, arqueología y curiosidades, y una nota de cultura o sociedad publicada en
   *política* seguirá etiquetándose como política; el LLM y el fine-tuning reproducen esa
   convención (concordancia LLM–humano de 20/20 en la auditoría muestral).

## 🗂️ Estructura del repositorio

```text
tarea_1/
├── 01_recoleccion.ipynb        # Scraping, limpieza, mapeo de secciones y EDA (ejecutado)
├── 02_clasificacion.ipynb      # Zero-shot, LLM, split, fine-tuning y evaluación (ejecutado)
├── app.py                      # Dashboard interactivo Streamlit
├── requirements.txt            # Dependencias exactas (Python 3.11)
├── .gitignore                  # Excluye pesos del modelo y respaldo crudo
├── datos/
│   ├── noticias.csv            # Dataset: 439 noticias x 7 columnas
│   ├── etiquetas_llm.csv       # Etiquetas del LLM (prompt estructurado)
│   └── raw/                    # Respaldo crudo (HTML y CSV intermedios, no versionado)
├── modelo/
│   ├── metrics.json            # Métricas clave usadas por el dashboard
│   └── (pesos .safetensors excluidos de git por >100 MB; se regeneran con el notebook)
└── notebooks_build/            # Scripts que generan y ejecutan los notebooks
```

## 🚀 Ejecución en local

Requisito: **Python 3.11** (se recomienda un entorno virtual o conda).

```bash
# 1) Crear el entorno e instalar dependencias
conda create -n tarea1 python=3.11 -y
conda activate tarea1
# PyTorch CPU (primero el índice propio; con GPU basta con el requirements estándar)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 2) Ejecutar los notebooks (desde la carpeta tarea_1/)
jupyter nbconvert --to notebook --execute --inplace 01_recoleccion.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_clasificacion.ipynb

# 3) Levantar el dashboard
cd tarea_1
streamlit run app.py
```

El dashboard muestra: indicadores clave (total de noticias, F1 macro en test,
concordancia LLM–humano), filtros por medio y categoría, gráfico Plotly de la
distribución, tabla con descarga CSV y un **probador en vivo** que clasifica cualquier
titular escrito por el usuario. Si la carpeta `modelo/` no contiene los pesos
(excluidos de git), el probador cae automáticamente al clasificador zero-shot.
