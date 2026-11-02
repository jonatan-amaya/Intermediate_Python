# 04 · Evaluación del agente con y sin MCP/Skills (Parte 4)

**Asistente:** Kimi Code · **Fecha:** 2026-11-02

---

**Asistente:** Diseño 10 preguntas con respuestas esperadas **verificadas antes
del experimento** (4 BCRP, 4 ENAHO, 2 combinadas), tolerancias definidas a priori.
Las esperadas salen de fuentes oficiales o de cálculo propio (p. ej. Cusco 18.54 %
procesado; tasa de referencia 4.25 % de `PD04722MM` oct-2026).

**Usuario:** (revisa avances; sin cambios al diseño)

**Asistente:** Implemento `scripts/evaluar_agente.py`:
- **Modo B** responde con las herramientas reales (MCP para BCRP, parquet
  procesado para ENAHO) midiendo tiempos.
- **Modo A** registra las respuestas que redacté en sesión independiente **sin**
herramientas (conocimiento del modelo), con la misma consigna.

**Asistente:** Primera corrida: 8/10 (A) vs 10/10 (B). Diagnóstico honesto del
fallo de A en E4: el checker leía "40-45 %" como 40 y −45 (guión interpretado
como signo). Corregí el extractor numérico (magnitudes, no signos) —E4-A pasó a
correcta— y en C2 el fallo de A es sustantivo: "brecha de género menor a 1 punto"
sin cuantificar (real: 0.3 pts) no supera la tolerancia previa. **Resultado final:
A = 9/10, B = 10/10.**

**Asistente:** Escribo `evaluacion/comparacion.md`: aciertos, tiempos (B: 26.6 s
con reintentos anti-bot; ~2 s con caché caliente), errores principales del modo A
(precisión sin fuente, indecisión nominal, no verificabilidad), mejora en las
combinadas y conclusión: la ventaja del modo B no es solo el 10/10 sino respuestas
exactas, citables y reproducibles.

Decisiones relevantes:
- Las respuestas esperadas NO se tocaron tras ver los resultados (C2-A sigue
  contando como incorrecta).
- Las respuestas del Modo A se transcribieron tal cual se redactaron; la sesión
  sin herramientas se documentó como condición experimental.

**Commit:** `feat(tarea_4): evaluacion A/B 9-10 vs 10-10 + comparacion.md`
