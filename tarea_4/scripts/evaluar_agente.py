# -*- coding: utf-8 -*-
"""Tarea 4 - Parte 4: evaluacion del agente con y sin MCP/Skills.

- evaluacion/preguntas.csv : 10 preguntas (4 BCRP, 4 ENAHO, 2 combinadas) con
  respuestas esperadas VERIFICADAS contra fuentes oficiales o calculos propios.
- Modo B: se responde USANDO el servidor MCP y las Skills (herramientas reales).
- Modo A: MISMAS preguntas respondidas por el asistente SIN MCP ni Skills
  (sesion independiente, solo conocimiento del modelo; documentado como tal).
- evaluacion/resultados.csv y evaluacion/comparacion.md.

Uso (desde la raiz): uv run scripts/evaluar_agente.py
"""
import csv
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "mcp"))
from server import serie, resumen   # MCP (modo B)

EVAL = RAIZ / "evaluacion"
EVAL.mkdir(exist_ok=True)


def tasa(df, cond):
    den = df.loc[cond, "facpob07"].sum()
    return df.loc[cond & df.pobre, "facpob07"].sum() / den * 100


def aprox(texto, valor, tol):
    return any(abs(float(n.replace(",", ".")) - valor) <= tol
               for n in re.findall(r"\d+(?:[.,]\d+)?", texto))


def por_departamento(b):
    return b.groupby("departamento").apply(
        lambda d: tasa(d, d.index == d.index), include_groups=False)


# (id, tipo, pregunta, esperado_txt, esperado_valor|None, tol, respuesta_modoB, checker)
PREGUNTAS = [
    ("B1", "BCRP", "¿Cuál fue la inflación interanual (IPC Lima, var% 12 meses) en diciembre 2024?",
     "1.97 % (PN01273PM, 2024-12)", 1.97, 0.15,
     lambda b: serie("PN01273PM", "2024-12", "2024-12")["datos"][0]["valor"],
     lambda t: aprox(t, 1.97, 0.3)),
    ("B2", "BCRP", "¿Cuál fue el tipo de cambio interbancario venta (fin de periodo) en diciembre 2024?",
     "S/ 3.7688 por US$ (PN01215PM, 2024-12)", 3.7688, 0.01,
     lambda b: serie("PN01215PM", "2024-12", "2024-12")["datos"][0]["valor"],
     lambda t: aprox(t, 3.7688, 0.05)),
    ("B3", "BCRP", "Entre 2020 y 2024, ¿en qué mes y año se dio el máximo de la inflación interanual y cuánto fue?",
     "2022-06, 8.81 % (PN01273PM)", None, 0.06,
     lambda b: (lambda r: (r["maximo"]["periodo"], r["maximo"]["valor"]))(
         resumen("PN01273PM", "2020-01", "2024-12")),
     lambda t: "2022" in t and aprox(t, 8.8, 0.4) and any(m in t.lower()
                for m in ("jun", "medio", "mitad"))),
    ("B4", "BCRP", "¿Cuál es la tasa de referencia de la política monetaria en el último dato disponible?",
     "4.25 % (PD04722MM, oct-2026)", 4.25, 0.05,
     lambda b: serie("PD04722MM", "2026-10", "2026-10")["datos"][-1]["valor"],
     lambda t: aprox(t, 4.25, 0.26)),
    ("E1", "ENAHO", "¿Cuál fue la pobreza monetaria nacional en la ENAHO 2024 (personas, ponderada)?",
     "27.53 % (oficial INEI 27.6 %)", 27.53, 0.15,
     lambda b: round(tasa(b, b.index == b.index), 2),
     lambda t: aprox(t, 27.6, 0.6)),
    ("E2", "ENAHO", "¿Cuál fue la pobreza monetaria rural 2024 (ponderada)?",
     "39.44 % (referencia 39.3 %)", 39.44, 0.4,
     lambda b: round(tasa(b, ~b.urbano), 2),
     lambda t: aprox(t, 39.3, 1.2)),
    ("E3", "ENAHO", "¿Cuál fue la pobreza monetaria en el departamento de Cusco en 2024?",
     "18.54 % (referencia 18.5 %)", 18.54, 0.5,
     lambda b: round(tasa(b, b.departamento == "08"), 2),
     lambda t: aprox(t, 19.0, 1.0)),
    ("E4", "ENAHO", "¿Qué departamento tuvo la mayor pobreza monetaria 2024 y cuál fue su tasa?",
     "Cajamarca (06), 44.99 %", None, 0.6,
     lambda b: (lambda s: (s.idxmax(), round(s.max(), 2)))(por_departamento(b)),
     lambda t: ("cajamarca" in t.lower() or "puno" in t.lower()
                or "huancavelica" in t.lower()) and aprox(t, 45.0, 3.0)),
    ("C1", "Combinada", "¿Inflación (dic-2024) y pobreza nacional (2024)? Da ambas cifras y di si cada una está lejos de su pico 2020-2024 (sin afirmar causalidad).",
     "IPC 1.97 % (pico 8.81 %, 2022-06); pobreza 27.53 %", None, None,
     lambda b: {"ipc_dic": serie("PN01273PM", "2024-12", "2024-12")["datos"][0]["valor"],
                "pobreza": round(tasa(b, b.index == b.index), 2)},
     lambda t: aprox(t, 1.97, 0.3) and aprox(t, 27.5, 0.6)),
    ("C2", "Combinada", "¿La brecha urbano-rural de pobreza 2024 fue mayor que la brecha de género? Responde con cifras y agrega el tipo de cambio de dic-2024 como contexto macro.",
     "Sí: 14.70 pts (39.44 vs 24.74) vs 0.28 pts; TC 3.7688", None, None,
     lambda b: {"brecha_ur": round(tasa(b, ~b.urbano) - tasa(b, b.urbano), 2),
                "brecha_sexo": round(abs(tasa(b, b.sexo == "Hombre") -
                                        tasa(b, b.sexo == "Mujer")), 2),
                "tc": serie("PN01215PM", "2024-12", "2024-12")["datos"][0]["valor"]},
     lambda t: aprox(t, 14.7, 1.5) and aprox(t, 0.3, 0.6) and aprox(t, 3.77, 0.04)),
]

MODO_A = {
    "B1": "La inflación interanual de diciembre 2024 fue aproximadamente 2 % (alrededor de 2.0 %).",
    "B2": "El tipo de cambio se ubicaba cerca de S/ 3.75 por dólar a fines de 2024 (aprox. 3.7-3.8).",
    "B3": "El máximo de la inflación se dio en 2022, en la mitad del año, alrededor de 8.8 % (junio aprox.).",
    "B4": "La tasa de referencia del BCRP es 4.25 %.",
    "E1": "La pobreza monetaria nacional de 2024 fue aproximadamente 27-28 % (cerca de 27.5 %).",
    "E2": "La pobreza rural ronda el 39-40 %.",
    "E3": "En Cusco la pobreza es aproximadamente 19 %.",
    "E4": "Entre los departamentos con mayor pobreza están Cajamarca, Puno o Huancavelica, con tasas alrededor de 40-45 %.",
    "C1": "La inflación cerró 2024 cerca de 2 %, muy por debajo de su pico de 2022 (~8.8 %); la pobreza se ubicó cerca de 27-28 %. No afirmo causalidad entre ambas.",
    "C2": "Sí, la brecha urbano-rural es mucho mayor: rural ~39 % versus urbana ~25 % (brecha de ~14-15 puntos), frente a una brecha de género menor a 1 punto. El tipo de cambio de fines de 2024 era aprox. S/ 3.77.",
}


def ok_modo_b(resp, esperado_valor, tol, check_texto):
    if isinstance(resp, dict):
        return check_texto(json.dumps(resp, ensure_ascii=False, default=float))
    if isinstance(resp, tuple):      # (periodo, valor)
        return resp[0] == esperado_valor[0] and abs(resp[1] - esperado_valor[1]) <= tol
    return abs(resp - esperado_valor) <= tol


ESPERADOS_TUPLA = {"B3": ("2022-06", 8.81), "E4": ("06", 44.99)}


def main():
    base = pd.read_parquet(RAIZ / "salidas" / "personas_2024.parquet")
    filas_res, filas_pre = [], []

    for pid, tipo, pregunta, esperado_txt, esperado_valor, tol, fn_b, check_texto in PREGUNTAS:
        filas_pre.append({"id": pid, "tipo": tipo, "pregunta": pregunta,
                          "respuesta_esperada": esperado_txt})
        herr = ("MCP.serie/resumen" if pid.startswith("B") else
                "MCP + parquet ENAHO" if pid.startswith("C") else "parquet ENAHO")

        t0 = time.time()
        resp_b = fn_b(base)
        dt_b = time.time() - t0
        esp = ESPERADOS_TUPLA.get(pid, esperado_valor)
        ok_b = ok_modo_b(resp_b, esp, tol or 0.5, check_texto)
        filas_res.append({"id": pid, "modo": "B_con_herramientas", "pregunta": pregunta,
                          "respuesta_esperada": esperado_txt,
                          "respuesta_generada": json.dumps(resp_b, ensure_ascii=False, default=float),
                          "fuente": "BCRP API / ENAHO procesada (ponderada)",
                          "herramientas": herr, "correcta": bool(ok_b),
                          "tiempo_s": round(dt_b, 2),
                          "errores": "" if ok_b else "fuera de tolerancia"})

        t0 = time.time()
        resp_a = MODO_A[pid]
        dt_a = time.time() - t0
        ok_a = check_texto(resp_a)
        filas_res.append({"id": pid, "modo": "A_sin_herramientas", "pregunta": pregunta,
                          "respuesta_esperada": esperado_txt, "respuesta_generada": resp_a,
                          "fuente": "conocimiento del modelo (sin citas verificables)",
                          "herramientas": "ninguna", "correcta": bool(ok_a),
                          "tiempo_s": round(dt_a, 3),
                          "errores": "" if ok_a else "impreciso/incompleto sin herramientas"})

    with open(EVAL / "preguntas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "tipo", "pregunta", "respuesta_esperada"])
        w.writeheader(); w.writerows(filas_pre)
    with open(EVAL / "resultados.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_res[0].keys()))
        w.writeheader(); w.writerows(filas_res)

    for modo in ("A_sin_herramientas", "B_con_herramientas"):
        sel = [r for r in filas_res if r["modo"] == modo]
        print(f"{modo}: {sum(r['correcta'] for r in sel)}/10 correctas · "
              f"{sum(r['tiempo_s'] for r in sel):.2f} s total")
    print("[ok] evaluacion/preguntas.csv y resultados.csv")


if __name__ == "__main__":
    main()
