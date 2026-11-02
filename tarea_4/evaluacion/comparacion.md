# Comparación del agente con y sin MCP/Skills (Tarea 4, Parte 4)

**Diseño:** 10 preguntas con respuestas esperadas verificadas (4 BCRP, 4 ENAHO, 2
combinadas), mismas instrucciones y modelo en ambos modos. **Modo A:** sesión sin
servidor MCP ni Skills (conocimiento del modelo, sin citas verificables). **Modo B:**
sesión con el MCP del BCRP y las Skills ENAHO activos; cada respuesta sale de una
llamada a herramientas (ver `herramientas` en `resultados.csv`). Sesiones
independientes para evitar contaminación.

## Resultado global

| Métrica | Modo A (sin herramientas) | Modo B (con MCP + Skills) |
|---|---|---|
| Respuestas correctas (tolerancia previa) | **9/10** | **10/10** |
| Incorrectas / no contestadas | 1 (C2) | 0 |
| Tiempo total | 0 s de herramientas (redacción directa) | 26.6 s totales de herramientas |
| Tiempo medio por pregunta | n/a (sin cómputo) | 2.7 s (0.3–4.9 s) |

Nota: el Modo B incluye reintentos ante la protección anti-bot del BCRP
(PerimeterX); con la caché local caliente el cómputo baja a ~2 s total. El Modo A
no tiene "tiempo de herramientas" porque no usa ninguna: su costo es de redacción
del modelo, no medible de forma comparable.

## Pregunta a pregunta

| ID | Tipo | Modo A | Modo B | Comentario |
|---|---|---|---|---|
| B1 | BCRP | ✅ ~2 % | ✅ 1.97 (exacto) | A acierta el orden de magnitud |
| B2 | BCRP | ✅ ~3.75 | ✅ 3.7688 (exacto) | A redondea correctamente |
| B3 | BCRP | ✅ 2022-mitad, ~8.8 | ✅ 2022-06, 8.81 (exacto) | A no precisa el mes |
| B4 | BCRP | ✅ 4.25 % | ✅ 4.25 (exacto) | coincidente |
| E1 | ENAHO | ✅ ~27.5 | ✅ 27.53 | A acierta por conocimiento del dato oficial |
| E2 | ENAHO | ✅ ~39-40 | ✅ 39.44 | ok en ambos |
| E3 | ENAHO | ✅ ~19 | ✅ 18.54 | A en el borde de tolerancia |
| E4 | ENAHO | ✅ "Cajamarca… 40-45" | ✅ Cajamarca 44.99 | A da un rango y duda entre 3 departamentos |
| C1 | Combinada | ✅ | ✅ (ambas cifras exactas) | A cualitativo, B con datos |
| C2 | Combinada | ❌ | ✅ 14.70 / 0.31 / 3.7688 | **A falla:** dice "brecha de género menor a 1 punto" sin cuantificarla (0.3 pts); mezcla intervalos y redondeos. B la calcula de la base. |

## Principales errores encontrados (Modo A)

1. **Precisión cuantitativa sin fuente:** las cifras de A son aproximaciones de
   memoria sin código de serie ni periodo; en C2 la imprecisión ("menor a 1 punto")
   no supera el criterio de tolerancia definido antes del experimento.
2. **Indecisión nominal en E4:** el modelo sin herramientas no distingue cuál de
   tres departamentos es el máximo; con datos es Cajamarca (44.99 %) sin ambigüedad.
3. **No verificabilidad:** ninguna cifra del Modo A es citable ni reproducible;
   todas las del Modo B llevan código, periodo y fuente (columna `herramientas`).

## Preguntas que mejoraron

- **C2 (y en general las combinadas):** la integración MCP+ENAHO permite responder
  con 3 cifras verificadas en una sola ejecución; sin herramientas la respuesta se
  vuelve cualitativa.
- **B3/E3:** el Modo B precisa mes (2022-06) y valor departamental (18.54) exactos.

## Conclusión sobre la utilidad de MCP y Skills

El Modo A sorprendentemente acierta 9/10 en preguntas de hechos ampliamente
publicados (pobreza 27.6 %, tasa 4.25 %), lo que muestra que el conocimiento
paramétrico cubre bien los "titulares". La ventaja del Modo B no es solo el
10/10 sino la **naturaleza de la respuesta**: exacta, con tolerancia explícita,
con código de serie/periodo/fuente y 100 % reproducible; además es la única que
puede desagregar (mes exacto, departamento exacto, brechas calculadas) y la única
que cumple el estándar de evidencia del informe. En preguntas combinadas la
diferencia es cualitativa: sin herramientas la respuesta se vuelve imprecisa
exactamente donde el análisis requiere cifras.

**Reproducibilidad:** `uv run scripts/evaluar_agente.py` regenera
`preguntas.csv` y `resultados.csv`. Las respuestas del Modo A se registraron tal
cual se redactaron en su sesión independiente; no se modificaron las respuestas
esperadas después de observar los resultados.
