# Referencia rápida · ENAHO 2024 (módulos 34 y 02)

## Unidad y llaves
- Módulo 34 (sumaria): una fila por **hogar** (33,691). Factor: `factor07`.
- Módulo 02 (miembros): una fila por **persona** (117,721). Factor: `facpob07`.
- Llaves `conglome`, `vivienda`, `hogar`: siempre **texto** (conservan ceros a la
  izquierda). La unión personas←hogares es `m:1` con `validate="m:1"`.

## Variables que construye la base
| Variable | Definición |
|---|---|
| `departamento` | `ubigeo[:2]` (texto, con cero a la izquierda) |
| `urbano` | `estrato <= 5` |
| `pobre` | `pobreza <= 2` (1 = pobre extremo, 2 = pobre no extremo, 3 = no pobre) |
| `pobre_ext` | `pobreza == 1` |
| `sexo` | `p207` (1 = hombre, 2 = mujer) |

## Filtro de residentes habituales
`((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))` → 108,664 personas.

## Cifras de validación oficiales (ENAHO 2024)
| Indicador | Referencia |
|---|---|
| Pobreza monetaria nacional (personas, facpob07) | 27.53 % (oficial 27.6 %) |
| Pobreza extrema | 5.5 % |
| Pobreza urbana / rural | 24.8 % / 39.3 % |
| Lima Metropolitana (dominio == 8) | 28.2 % |
| Residentes habituales | 108,664 |
| Departamentos | 25 |

La tolerancia aceptada para la pobreza nacional es ±0.1 puntos frente a 27.6 %.
