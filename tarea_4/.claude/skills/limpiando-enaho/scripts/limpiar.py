# -*- coding: utf-8 -*-
"""Pipeline de limpieza ENAHO 2024 (Skill limpiando-enaho).

Lee los modulos 34 (sumaria) y 02 (miembros), filtra residentes habituales,
une personas-hogares (validate='m:1'), construye indicadores y valida contra
las cifras oficiales. Salida: salidas/personas_2024.parquet y
salidas/validacion.txt. Si una validacion esencial falla, exit 1.
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
SUMARIA = RAIZ / "datos" / "raw34" / "966-Modulo34" / "sumaria-2024.dta"
MIEMBROS = RAIZ / "datos" / "raw02" / "966-Modulo02" / "enaho01-2024-200.dta"
SALIDAS = RAIZ / "salidas"
LLAVES = ["conglome", "vivienda", "hogar"]

REFS = {
    "pobreza_nacional": 27.6, "tolerancia_pp": 0.1,
    "pobreza_extrema": 5.5, "pobreza_urbana": 24.8, "pobreza_rural": 39.3,
    "residentes": 108664, "departamentos": 25,
}


def tasa_pobreza(df, condicion):
    """Pobreza ponderada DENTRO del subgrupo definido por condicion (facpob07)."""
    den = df.loc[condicion, "facpob07"].sum()
    num = df.loc[condicion & df.pobre, "facpob07"].sum()
    return num / den * 100


def ponderada(df, condicion):
    """Pobreza ponderada como share nacional (denominador = todas las personas)."""
    num = df.loc[condicion, "facpob07"].sum()
    den = df["facpob07"].sum()
    return num / den * 100


def main():
    SALIDAS.mkdir(exist_ok=True)
    for ruta in (SUMARIA, MIEMBROS):
        if not ruta.exists():
            sys.exit(f"Falta {ruta}. Descargue los zips del INEI (codigo 966).")

    sumaria = pd.read_stata(SUMARIA, convert_categoricals=False)
    miembros = pd.read_stata(MIEMBROS, convert_categoricals=False)
    sumaria.columns = sumaria.columns.str.lower()
    miembros.columns = miembros.columns.str.lower()

    for c in LLAVES:                       # llaves siempre texto (ceros a la izquierda)
        sumaria[c] = sumaria[c].astype(str).str.strip()
        miembros[c] = miembros[c].astype(str).str.strip()
        miembros[c] = miembros[c].str.replace(r"\.0$", "", regex=True)
        sumaria[c] = sumaria[c].str.replace(r"\.0$", "", regex=True)

    # 1) filtro de residentes habituales (sesion 16)
    residentes = miembros[
        ((miembros.p204 == 1) & (miembros.p205 == 2)) |
        ((miembros.p204 == 2) & (miembros.p206 == 1))].copy()

    # 2) union m:1 personas <- hogares (el ubigeo oficial es el de la vivienda/hogar;
    #    del lado personas solo llaves + factor + sexo, sin colisiones)
    base = residentes[LLAVES + ["codperso", "facpob07", "p207"]].merge(
        sumaria[LLAVES + ["ubigeo", "pobreza", "estrato", "dominio", "factor07"]],
        on=LLAVES, how="left", validate="m:1")
    if sumaria[LLAVES].duplicated().any():
        sys.exit("ERROR: la sumaria tiene llaves de hogar duplicadas.")
    if len(base) != len(residentes):
        sys.exit(f"ERROR: la union altero el numero de personas "
                 f"({len(residentes):,} -> {len(base):,}).")

    # 3) indicadores
    base["departamento"] = base["ubigeo"].astype(str).str[:2]
    base["urbano"] = base["estrato"] <= 5
    base["pobre"] = base["pobreza"] <= 2
    base["pobre_ext"] = base["pobreza"] == 1
    base["sexo"] = base["p207"].map({1.0: "Hombre", 2.0: "Mujer"})

    # 4) validaciones
    checks = []
    checks.append(("Residentes habituales == 108,664",
                   len(base) == REFS["residentes"], f"{len(base):,}"))
    checks.append(("Pobreza nacional dentro de 27.6 +/- 0.1",
                   abs(ponderada(base, base.pobre) - REFS["pobreza_nacional"]) <= REFS["tolerancia_pp"],
                   f"{ponderada(base, base.pobre):.2f} %"))
    checks.append(("Pobreza extrema ~ 5.5 %",
                   abs(ponderada(base, base.pobre_ext) - REFS["pobreza_extrema"]) <= 0.4,
                   f"{ponderada(base, base.pobre_ext):.2f} %"))
    checks.append(("Pobreza urbana ~ 24.8 %",
                   abs(tasa_pobreza(base, base.urbano) - REFS["pobreza_urbana"]) <= 0.4,
                   f"{tasa_pobreza(base, base.urbano):.2f} %"))
    checks.append(("Pobreza rural ~ 39.3 %",
                   abs(tasa_pobreza(base, ~base.urbano) - REFS["pobreza_rural"]) <= 0.4,
                   f"{tasa_pobreza(base, ~base.urbano):.2f} %"))
    checks.append(("25 departamentos identificados",
                   base["departamento"].nunique() == REFS["departamentos"],
                   f"{base['departamento'].nunique()}"))
    checks.append(("Sin perdidas en la union (todos tienen pobreza)",
                   base["pobreza"].notna().all(),
                   f"faltan {int(base['pobreza'].isna().sum())}"))
    checks.append(("Factor de expansion presente y positivo",
                   bool((base["facpob07"] > 0).all()),
                   f"min {base['facpob07'].min():.2f}"))

    lineas = ["VALIDACION ENAHO 2024 · Skill limpiando-enaho",
              f"Modulos: {SUMARIA.name} + {MIEMBROS.name}",
              f"Personas (residentes habituales): {len(base):,}",
              f"Pobreza nacional ponderada (facpob07): {ponderada(base, base.pobre):.2f} %",
              "", "Checks:"]
    esencial_falla = False
    for nombre, ok, detalle in checks:
        lineas.append(f"  [{'OK' if ok else 'FALLA'}] {nombre} -> {detalle}")
        if not ok and ("nacional" in nombre or "Residentes" in nombre or "duplicados" in nombre):
            esencial_falla = True
    (SALIDAS / "validacion.txt").write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas))

    if esencial_falla:
        sys.exit("ERROR: validacion esencial fallida; no se guarda la base.")
    base.to_parquet(SALIDAS / "personas_2024.parquet", index=False)
    print(f"\nBase guardada: salidas/personas_2024.parquet ({len(base):,} personas)")


if __name__ == "__main__":
    main()
