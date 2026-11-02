---
name: mapeando-enaho
description: Construye el mapa coroplético de pobreza monetaria departamental de la ENAHO procesada. Úsala cuando pidan un mapa de pobreza por departamento del Perú con datos del INEI.
argument-hint: "[año]"
---
# Mapear la pobreza departamental

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill
   **`limpiando-enaho`** y luego vuelve aquí.
2. Corre exactamente (desde la raíz del proyecto):
   `uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py`
3. El mapa se guarda en `mapas/pobreza_departamento.png` y la validación territorial
   en `salidas/validacion_mapa.txt`.
4. Reglas no negociables: unión por **código** (`ubigeo[:2]` = `FIRST_IDDP`, como
   texto), 25 departamentos con dato, Lima (15) y Callao (07) separados, un solo
   color de claro a oscuro desde 0 y leyenda con la unidad (% de personas).
5. Si falta `datos/peru_departamental_simple.geojson`, descárgalo del repositorio
   del curso (sesión 06-geoespacial).
