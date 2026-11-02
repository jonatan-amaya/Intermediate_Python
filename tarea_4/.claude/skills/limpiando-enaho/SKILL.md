---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas con pobreza y factor de expansión. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por región, sexo, área o edad.
argument-hint: "[año]"
---
# Limpiar la ENAHO

1. Si faltan los zips en `datos/`, pídele al usuario bajarlos del INEI
   (código 966 = ENAHO 2024): módulos 34 y 02 desde
   https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/
2. Corre exactamente (desde la raíz del proyecto):
   `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py`
3. Lee `salidas/validacion.txt`. Si alguna validación esencial falla, DETENTE y
   reporta el error: no se corrigen cifras a mano para que coincidan.
4. Responde con `salidas/personas_2024.parquet`; toda cifra de personas va
   ponderada con `facpob07`.
5. Antes de usar una variable que no está en la base, lee `reference.md`.
