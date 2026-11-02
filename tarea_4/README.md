# 🤖 Tarea 4 – Agente de investigación socioeconómica (MCP BCRP + Skills ENAHO)

**Pregunta guía:** *¿Pueden construir un agente de IA capaz de investigar la realidad
socioeconómica peruana con datos oficiales del INEI y el BCRP, combinando servidores
MCP, Skills y análisis reproducible?*

**Autor:** Jonatan Amaya (@jonatan-amaya) · Noviembre 2026

---

## 1. Objetivo del proyecto

Construir un **agente de investigación** que, ante una pregunta en lenguaje natural,
use herramientas especializadas —un servidor MCP del BCRP y tres Skills de
procesamiento ENAHO— para producir respuestas **verificables y reproducibles**, no
respuestas de memoria. Incluye la integración (una investigación real) y un
experimento de evaluación con y sin herramientas.

## 2. Arquitectura general

```
pregunta (lenguaje natural)
   │
   ├─► Servidor MCP "bcrp" (mcp/server.py, FastMCP, stdio)
   │      buscar_series · serie · resumen · correlacion  (herramientas)
   │      bcrp://serie/{codigo}                          (recurso)
   │      informe(tema)                                  (prompt)
   │      └── API oficial BCRP (anti-bot: reintentos + caché real en datos/cache_bcrp)
   │
   └─► Skills (.claude/skills/)
          limpiando-enaho ──► salidas/personas_2024.parquet + validacion.txt
          graficando-enaho ──► figuras/*.png   (necesita la base limpia)
          mapeando-enaho  ──► mapas/pobreza_departamento.png (necesita la base limpia)
```

## 3. Herramientas MCP

| Herramienta | Qué hace |
|---|---|
| `buscar_series(texto, frecuencia, limite)` | Busca series por palabras clave en el catálogo oficial (17,167 series) |
| `serie(codigo, desde, hasta)` | Descarga datos de una serie (mensual/diaria/trimestral/anual), periodos en ISO, omite `n.d.` |
| `resumen(codigo, desde, hasta)` | primero/último, cambio, variación %, promedio, máximo y mínimo (con periodo) |
| `correlacion(codigo_a, codigo_b, desde, hasta)` | **(herramienta propia)** Pearson con alineación por periodo y pares completos; exige misma frecuencia y ≥4 pares |

**Recurso:** `bcrp://serie/{codigo}` (ficha descriptiva). **Prompt:** `informe(tema)`
(plantilla de análisis que exige citar código, periodo y fuente).

## 4. Las tres Skills

| Skill | Entrada | Salida | Validación |
|---|---|---|---|
| `limpiando-enaho` | zips módulos 34 + 02 | `salidas/personas_2024.parquet`, `validacion.txt` | pobreza 27.53 % (±0.1 vs 27.6), 108,664 residentes, 25 deptos, unión `m:1` sin pérdidas |
| `graficando-enaho` | base limpia + tema (área/sexo/departamentos) | `figuras/*.png` (200 dpi) | ponderado `facpob07`, títulos analíticos, fuente |
| `mapeando-enaho` | base limpia + GeoJSON | `mapas/pobreza_departamento.png` + `validacion_mapa.txt` | unión por código (`ubigeo[:2]`=`FIRST_IDDP`), 25/25 con dato, dif. máx. 0.52 pts vs referencia |

Coordinación: las skills de gráficos y mapas **exigen** la base limpia; si no existe,
se ejecuta primero `limpiando-enaho` (demostrado en `salidas/bitacora_agente.json`).

## 5. Fuentes y enlaces de datos

| Fuente | Enlace |
|---|---|
| ENAHO 2024 · Módulo 34 (sumaria) | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip |
| ENAHO 2024 · Módulo 02 (miembros) | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip |
| GeoJSON departamental (curso) | `datos/peru_departamental_simple.geojson` (sesión 06-geoespacial) |
| Series BCRP | https://estadisticas.bcrp.gob.pe/estadisticas/series/ |
| Catálogo BCRP | snapshot oficial del 2026-11-02 en `datos/catalogo_bcrp.csv` (el endpoint pasó a exigir navegador) |

Los zips se descomprimen a `datos/raw34/` y `datos/raw02/` (ignorados por git).

## 6. Instalación con `uv`

```bash
cd tarea_4
uv venv .venv --python 3.11
uv pip install --python .venv/Scripts/python.exe fastmcp httpx pandas pyarrow pytest geopandas matplotlib playwright
# (playwright solo si se requiere renovar la caché BCRP ante el anti-bot)
uv pip install --python .venv/Scripts/python.exe pytest
```

En Linux/macOS cambie `.venv/Scripts/python.exe` por `.venv/bin/python`.
Dependencias declaradas en `pyproject.toml`.

## 7. Conectar el MCP a Claude Code

El archivo `.mcp.json` ya apunta al servidor:

```json
{ "mcpServers": { "bcrp": { "command": "uv", "args": ["run", "mcp/server.py"] } } }
```

Con Claude Code en la carpeta del proyecto, el servidor se conecta automáticamente
(`claude mcp add --scope project bcrp -- uv run mcp/server.py` si se prefiere manual).
Las Skills se cargan desde `.claude/skills/` al iniciar Claude Code en el proyecto.

## 8. Reproducir procesamiento y pruebas

```bash
# ENAHO (con los zips en datos/)
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py
uv run .claude/skills/graficando-enaho/scripts/graficar.py todos
uv run .claude/skills/mapeando-enaho/scripts/mapear.py

# Integración MCP + Skills (una sola ejecución; deja bitácora)
uv run scripts/ejecutar_investigacion.py

# Pruebas del servidor MCP (contrato: 10/10)
cd mcp && uv run pytest -q

# Evaluación del agente (modos A y B)
uv run scripts/evaluar_agente.py
```

## 9. Resultados de la evaluación

| Modo | Correctas | Detalle |
|---|---|---|
| A · sin MCP/Skills | **9/10** | falla la combinada C2 (brecha de género sin cuantificar) |
| B · con MCP + Skills | **10/10** | cifras exactas con código de serie/periodo/fuente |

Análisis completo en `evaluacion/comparacion.md`; datos en `evaluacion/resultados.csv`.

## 10. Limitaciones y problemas encontrados

- **Anti-bot del BCRP (nov-2026):** el sitio activó PerimeterX; `httpx` recibe HTML.
  Solución documentada: `scripts/descargar_serie.py` usa navegador real (Playwright)
  y guarda respuestas oficiales en `datos/cache_bcrp/`; el servidor intenta la API en
  vivo y recurre a la caché (con cobertura de rangos) cuando es bloqueado. Las series
  usadas están cacheadas y son citables.
- **Datos transversales:** la pobreza ENAHO 2024 es un corte anual; no hay panel.
- **Agregados distintos:** frecuencias monetarias mensuales vs. indicadores anuales de
  hogares; el informe evita inferencias causales entre niveles.

## 11. Ejemplo de una ejecución completa

Pregunta de investigación: *«¿Cómo evolucionaron la inflación y el tipo de cambio
2020-2024 y qué brechas mostraba la pobreza al cierre?»* → Ejecución integrada en
`uv run scripts/ejecutar_investigacion.py`:

1. `MCP.buscar_series` localiza `PN01273PM` (IPC interanual) y `PN01215PM` (TC venta fin de periodo).
2. `MCP.serie/resumen` descargan y resumen ambas series (pico inflación 8.81 % en 2022-06; TC 3.3784→3.7688, +11.6 %).
3. `MCP.correlacion` calcula r = 0.4973 (n = 60).
4. Skills: `limpiando-enaho` (27.53 %, 108,664 personas, 25 deptos) → `graficando-enaho` → `mapeando-enaho` (25/25).
5. Bitácora completa: `salidas/bitacora_agente.json`. Informe: `informes/informe_final.md`.

## 12. Evidencias del uso de IA

Conversaciones completas del desarrollo (MCP, Skills, integración, evaluación) en
`evidencias_ia/` —exportación en Markdown, organizada cronológicamente, sin claves ni
datos sensibles—. Se utilizó un agente de código (Kimi Code) como asistente principal;
no se evalúa el código escrito a mano, sino la funcionalidad y reproducibilidad.
