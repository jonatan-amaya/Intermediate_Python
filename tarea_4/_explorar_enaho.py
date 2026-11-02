# -*- coding: utf-8 -*-
"""Explora columnas clave de los modulos ENAHO 2024."""
import pandas as pd

SUM = "datos/raw34/966-Modulo34/sumaria-2024.dta"
MIE = "datos/raw02/966-Modulo02/enaho01-2024-200.dta"

s = pd.read_stata(SUM, convert_categoricals=False,
                  columns=["conglome", "vivienda", "hogar", "ubigeo", "factor07",
                           "pobreza", "estrato", "dominio", "mieperho"])
print("sumaria:", s.shape)
print(s.dtypes)
print("pobreza:", s.pobreza.value_counts().sort_index().to_dict())
print("hogares (llave unica):", not s.duplicated(["conglome", "vivienda", "hogar"]).any())

m = pd.read_stata(MIE, convert_categoricals=False,
                  columns=["conglome", "vivienda", "hogar", "codperso", "ubigeo",
                           "facpob07", "p204", "p205", "p206", "p207"])
print("\nmiembros:", m.shape)
print(m.dtypes.head(10))
res = m[((m.p204 == 1) & (m.p205 == 2)) | ((m.p204 == 2) & (m.p206 == 1))]
print("residentes habituales:", len(res))
print("p207 en residentes:", res.p207.value_counts().sort_index().to_dict())
print("ubigeo muestra:", res.ubigeo.head(3).tolist(), "| tipo:", type(res.ubigeo.iloc[0]))
