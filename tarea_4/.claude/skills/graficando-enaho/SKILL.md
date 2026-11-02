---
name: graficando-enaho
description: Grafica indicadores de pobreza de la ENAHO procesada (área urbana/rural, sexo, departamentos) con estimaciones ponderadas. Úsala cuando pidan graficar, comparar o visualizar la pobreza de la ENAHO del INEI.
argument-hint: "[tema: area | sexo | departamentos]"
---
# Graficar la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill
   **`limpiando-enaho`** y luego vuelve aquí.
2. Corre exactamente (desde la raíz del proyecto):
   `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py $0`
   (`$0` puede ser `area`, `sexo`, `departamentos` o `todos`; por defecto: todos).
3. Los gráficos se guardan en `figuras/` a 200 dpi. Todo va ponderado con
   `facpob07`; títulos que dicen qué y cuándo, valor escrito en cada barra y
   nota al pie «Fuente: INEI, ENAHO 2024 · % de personas (ponderado)».
4. Responde citando las cifras principales de cada gráfico y su archivo.
