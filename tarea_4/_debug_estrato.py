# -*- coding: utf-8 -*-
import pandas as pd

b = pd.read_parquet("salidas/personas_2024.parquet")
print("estratos:", b.estrato.value_counts(dropna=False).sort_index().to_dict())
print("dominio:", b.dominio.value_counts(dropna=False).sort_index().to_dict())
print("pobreza NaN:", int(b.pobreza.isna().sum()), "| estrato NaN:", int(b.estrato.isna().sum()))
# pobreza por estrato
t = b.groupby("estrato", dropna=False).apply(
    lambda d: pd.Series({"n": len(d), "pobre_pct": d.loc[d.pobre, "facpob07"].sum() / d.facpob07.sum() * 100}),
    include_groups=False)
print(t.round(2))
