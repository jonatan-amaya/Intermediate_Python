# 02 · Desarrollo de las Skills ENAHO (Parte 2)

**Asistente:** Kimi Code · **Fecha:** 2026-11-02

---

**Asistente:** Con los módulos descompridos (`sumaria-2024.dta`, 33,691 hogares;
`enaho01-2024-200.dta`, 117,721 personas), exploro los esquemas: las llaves
`conglome/vivienda/hogar` son texto (ceros a la izquierda seguros); el filtro
`((p204==1)&(p205==2))|((p204==2)&(p206==1))` da exactamente **108,664** residentes
habituales, igual que la referencia de la sesión 16.

*(Escritura de las tres skills: SKILL.md con YAML name/description, scripts y
reference.md, siguiendo las reglas de la sesión 16.)*

**Asistente:** Primera corrida de `limpiar.py`: error mío al verificar
"duplicados" — la llave triple se repite en personas porque un hogar tiene varios
miembros (la unión es m:1). Verificación correcta: unicidad en la sumaria + conteo
de filas preservado.

**Asistente:** Segunda corrida: `KeyError: ubigeo/estrato` — ambos módulos traen
`ubigeo`, `estrato` y `dominio`; la unión los sufija. Solución: del lado personas
selecciono solo llaves + `codperso` + `facpob07` + `p207`.

**Asistente:** Validaciones: nacional 27.53 % ✓, extrema 5.50 % ✓, pero
urbana/rural salían 20.0 %/7.5 % — bug de denominador: calculaba pobreza del
subgrupo sobre el TOTAL nacional (20.0 + 7.5 = 27.5 lo delató). Corrijo con tasa
dentro del subgrupo: **urbana 24.74 %, rural 39.44 %** ✓ (referencia 24.8/39.3).

**Asistente:** `graficar.py`: tres figuras ponderadas con títulos analíticos y
fuente — área (24.7 vs 39.4), sexo (27.4 vs 27.7), departamentos (Ica 5.9 % –
Cajamarca 45.0 %).

**Asistente:** `mapear.py`: unión por código (`ubigeo[:2]` = `FIRST_IDDP`, texto
con zfill), 25/25 con dato, Lima (15) y Callao (07) separados, escala única
OrRd desde 0, leyenda "% de personas". Validación contra
`referencias/pobreza_departamento_2024.csv`: **diferencia máxima 0.52 puntos**.

**Commit:** `feat(tarea_4): 3 skills ENAHO con validaciones oficiales OK …`

Decisiones relevantes:
- Las cifras nunca se ajustaron a mano: los fallos se corrigieron en el código
  (denominador, sufijos, verificación de unicidad) hasta reproducir las referencias.
- Los microdatos originales quedan fuera de git (`.gitignore`), como exige el
  enunciado.
