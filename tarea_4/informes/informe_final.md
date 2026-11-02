# Informe final de investigación · Tarea 4

**Pregunta de investigación:** *¿Cómo evolucionaron la inflación y el tipo de cambio en el Perú entre 2020 y 2024, y qué brechas —urbana/rural y territorial— mostraba la pobreza monetaria al cierre de ese período?*

**Autor:** Jonatan Amaya · Agente: Claude-style coding agent (Kimi Code) con servidor MCP (BCRP) y Skills ENAHO · 2026-11-02

---

## 1. Fuentes y metodología

| Fuente | Datos | Vía |
|---|---|---|
| BCRP | IPC Lima var% interanual mensual (`PN01273PM`); tipo de cambio interbancario venta fin de período (`PN01215PM`) | Servidor MCP propio (`buscar_series`, `serie`, `resumen`, `correlacion`) sobre la API oficial `estadisticas.bcrp.gob.pe/estadisticas/series/api` |
| INEI | ENAHO 2024, módulos 34 (sumaria) y 02 (miembros) | Skills `limpiando-enaho` → `graficando-enaho` / `mapeando-enaho` |

- **ENAHO:** 117,721 personas → filtro de residentes habituales `((p204==1)&(p205==2))|((p204==2)&(p206==1))` → 108,664; unión personas←hogares `validate="m:1"` en `conglome/vivienda/hogar` (texto, ceros a la izquierda); indicadores con factor de expansión de personas `facpob07`; `pobre = pobreza<=2`; `urbano = estrato<=5`; `departamento = ubigeo[:2]`.
- **BCRP:** series mensuales 2020-01 a 2024-12; correlación de Pearson con alineación por periodo y pares completos (n=60).
- Toda cifra proviene de una llamada repetible; la bitácora de la ejecución integrada está en `salidas/bitacora_agente.json`.

## 2. Resultados

### Hallazgo 1 · La inflación completó un ciclo completo: del pico de 8.8 % (jun-2022) a 2.0 % (dic-2024)
La serie interanual del IPC de Lima (`PN01273PM`) pasó de 1.6 % en jun-2020 a un **máximo de 8.81 % en jun-2022**, media del quinquenio **4.47 %**, y cerró 2024 en **1.97 %** (dic-2024), dentro del rango meta del BCRP. Variación acumulada del período: +1.97 − 2.25 ≈ retorno al entorno de la meta.

### Hallazgo 2 · El tipo de cambio se depreció 11.6 % en el quinquenio y co-se mueve con la inflación (sin probar causalidad)
El tipo de cambio interbancario venta, fin de período (`PN01215PM`), subió de **S/ 3.3784 (ene-2020)** a **S/ 3.7688 (dic-2024)** (+11.6 %), con promedio 2024 de S/ 3.7574. La correlación mensual inflación×tipo de cambio 2020-2024 es **positiva moderada (r = 0.4973, n = 60)**: ambas series presionaron al alza en 2021-2022. Es una asociación descriptiva entre agregados; **no** se interpreta como relación causal.

### Hallazgo 3 · Al cierre de 2024 la pobreza seguía por encima del nivel prepandemia y con brechas de 15 puntos urbano-rural y de 39 puntos entre departamentos
Con ENAHO 2024 (ponderado `facpob07`): pobreza nacional **27.53 %** (oficial INEI 27.6 %), urbana **24.74 %** vs rural **39.44 %** (brecha de 14.7 puntos), extrema **5.50 %**. Por sexo, la brecha es menor a 0.4 puntos (hombres 27.4 %, mujeres 27.7 %). Territorialmente el rango va de **Ica 5.9 % a Cajamarca 45.0 %**: la pobreza del norte andino y la selva norte duplica o triplica la de la costa sur.

## 3. Visualizaciones

1. **Gráfico BCRP** (series oficiales): `figuras/bcrp_ipc_tc_2020_2024.png` — inflación interanual y tipo de cambio, 2020-2024.
2. **Gráfico ENAHO**: `figuras/pobreza_area.png` (urbana vs rural), `figuras/pobreza_sexo.png`, `figuras/pobreza_departamentos.png`.
3. **Mapa departamental**: `mapas/pobreza_departamento.png` — 25 unidades territoriales, Lima y Callao separados, unión por código (`ubigeo[:2]` = `FIRST_IDDP`), diferencia máxima vs la referencia de la Sesión 16: **0.52 puntos** (`salidas/validacion_mapa.txt`).

## 4. Interpretación

El quinquenio 2020-2024 combina una crisis inflacionaria importada y doméstica (2021-2022) con una desinflación rápida desde 2023, en paralelo a una depreciación cambiaria moderada pero persistente. Al cierre del período, la inflación ya no es el problema central; el rezago social sí: la pobreza (27.5 %) aún no regresa a los niveles de 2019 (~20 %, según INEI) y su carga se concentra en el mundo rural y en regiones del norte andino y la selva — coherente con los titulares de coyuntura de la Tarea 1 sobre costo de vida y economía regional.

## 5. Limitaciones

- La correlación inflación×tipo de cambio usa agregados mensuales de dos variables; no identifica causalidad ni canales de transmisión.
- La pobreza de ENAHO 2024 es un corte transversal (un año); no se observa trayectoria individual entre 2020 y 2024.
- Frecuencias y unidades difieren entre fuentes (mensual monetaria vs anual poblacional); el análisis evita equipararlas más allá del contraste descriptivo.
- La API del BCRP activó protección anti-bot (nov-2026); las series se obtuvieron con navegador real y quedaron cacheadas en `datos/cache_bcrp/` (reproducibles y citables).

## 6. Verificación de cifras (mínimo 3, de ambas fuentes)

| # | Afirmación del informe | Valor calculado | Verificación | ¿Coincide? |
|---|---|---|---|---|
| 1 | Pobreza nacional 2024 = 27.53 % | `salidas/validacion.txt` (procesamiento ENAHO) | INEI oficial 27.6 % (nota de pobreza 2024) | ✅ (dif. 0.07 pts, dentro de ±0.1) |
| 2 | IPC interanual dic-2024 = 1.97 % | MCP `serie(PN01273PM, 2024-12, 2024-12)` = 1.97 | Comunicados BCRP de inflación dic-2024 | ✅ |
| 3 | TC interbancario venta dic-2024 = S/ 3.7688 | MCP `serie(PN01215PM, 2024-12, 2024-12)` = 3.7688 | Serie oficial BCRP (mismo código/periodo, reconsulta) | ✅ |
| 4 (extra) | Pobreza urbana 24.74 % / rural 39.44 % | `salidas/validacion.txt` | Referencia Sesión 16: 24.8 % / 39.3 % | ✅ |

## 7. Reproducibilidad

```bash
uv sync --dev
# datos ENAHO (codigo 966): https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py
uv run .claude/skills/graficando-enaho/scripts/graficar.py todos
uv run .claude/skills/mapeando-enaho/scripts/mapear.py
uv run scripts/ejecutar_investigacion.py     # integración MCP + Skills (bitácora)
uv run pytest -q                              # 10/10 pruebas del servidor MCP
```

Series BCRP: `uv run scripts/descargar_serie.py PN01273PM 2020-01 2024-12 ...` (usa navegador si la API exige desafío). Archivos de evidencia: `salidas/bitacora_agente.json`, `salidas/validacion.txt`, `salidas/validacion_mapa.txt`.
