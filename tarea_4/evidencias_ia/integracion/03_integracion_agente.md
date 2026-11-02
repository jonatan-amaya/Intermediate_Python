# 03 · Integración del agente e informe (Parte 3)

**Asistente:** Kimi Code · **Fecha:** 2026-11-02

---

**Asistente:** Elijo la pregunta de investigación (requiere ambas fuentes):
*"¿Cómo evolucionaron la inflación y el tipo de cambio en el Perú entre 2020 y
2024, y qué brechas —urbana/rural y territorial— mostraba la pobreza monetaria al
cierre de ese período?"*

**Asistente:** Precargo las series necesarias vía navegador real (anti-bot):
`PN01273PM` (IPC interanual) y `PN01215PM` (TC interbancario venta fin de
periodo), 2020-01..2024-12; también `PD04722MM` (tasa de referencia) y
`PN38063GM` (desempleo Lima) para la evaluación.

*(Escritura de `scripts/ejecutar_investigacion.py`: en una sola corrida usa las
herramientas MCP en proceso —buscar_series, serie, resumen, correlacion— y lanza
las tres skills por subprocess, registrando cada paso en una bitácora JSON.)*

**Asistente:** Ejecución integrada (una sola corrida demostrable):

```
[01|MCP.buscar_series] ipc 12 meses -> PN01273PM Índice de precios Lima …
[02|MCP.buscar_series] tipo de cambio fin de periodo venta -> PN01215PM …
[03|MCP.serie] PN01273PM 2020-01..2024-12 -> 60 periodos
[04|MCP.resumen] min 1.60 (2020-06), max 8.81 (2022-06), promedio 4.47
[05|MCP.serie+resumen] TC 3.3784 -> 3.7688 (+11.6 %)
[06|MCP.correlacion] r = 0.4973 (n = 60) correlación positiva moderada
[07|Skill.limpiando-enaho] OK    [08|Skill.graficando-enaho] OK    [09|Skill.mapeando-enaho] OK
```

Bitácora: `salidas/bitacora_agente.json` (evidencia de orquestación MCP+Skills).

*(Escritura de `scripts/grafico_bcrp_informe.py`: figura BCRP del informe;
cifras para hallazgos y verificación.)*

**Asistente:** Redacto `informes/informe_final.md` con: pregunta, fuentes y
metodología, **3 hallazgos** (desinflación 8.81→1.97 %; depreciación +11.6 % con
correlación moderada r=0.4973 sin causalidad; pobreza 27.53 % con brecha
urbano-rural de 14.7 pts y territorial de 39 pts Ica-Cajamarca), las 3
visualizaciones (gráfico BCRP, gráficos ENAHO, mapa 25/25), interpretación,
limitaciones y **verificación de 4 cifras** de ambas fuentes (ENAHO vs INEI;
IPC y TC con reconsulta de serie por código y periodo).

**Commit:** `feat(tarea_4): ejecucion agente + informe final …`

Nota: cuando una herramienta no resuelve (p. ej., búsqueda que devuelve serie
"bancaria" en vez de "interbancaria"), el agente verificó el código contra el
catálogo antes de usarlo — registrado en la bitácora.
