# -*- coding: utf-8 -*-
"""Tarea 4 - Parte 3: ejecución del agente de investigación.

Orquesta en UNA sola corrida:
  - herramientas del MCP del BCRP (buscar_series, serie, resumen, correlacion),
  - las Skills ENAHO (limpiando -> graficando -> mapeando),
y guarda una bitácora de cada llamada (evidencia de integración).

Uso (desde la raíz): uv run scripts/ejecutar_investigacion.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "mcp"))
from server import buscar_series, serie, resumen, correlacion   # herramientas MCP

PY = sys.executable
BITACORA = []


def registrar(paso, tipo, detalle, resultado):
    BITACORA.append({"paso": paso, "tipo": tipo, "detalle": detalle,
                     "resultado": resultado})
    print(f"[{paso:02d}|{tipo}] {detalle} -> {str(resultado)[:110]}")


def skill(ruta, *args):
    t0 = time.time()
    r = subprocess.run([PY, str(ruta), *args], capture_output=True, text=True,
                       cwd=RAIZ)
    return r.returncode, time.time() - t0, (r.stdout + r.stderr)[-400:]


def main():
    print("=" * 72)
    print("AGENTE: inflacion y tipo de cambio 2020-2024 (BCRP) + pobreza")
    print("territorial 2024 (ENAHO)")
    print("=" * 72)

    # --- fase MCP: identificar series -------------------------------------
    ipc = buscar_series(texto="ipc 12 meses", frecuencia="Mensual", limite=3)
    registrar(1, "MCP.buscar_series", "ipc 12 meses (Mensual)",
              [f"{x['codigo']} {x['nombre'][:60]}" for x in ipc])
    tc = buscar_series(texto="tipo de cambio fin de periodo venta",
                       frecuencia="Mensual", limite=3)
    registrar(2, "MCP.buscar_series", "tipo de cambio fin de periodo venta",
              [f"{x['codigo']} {x['nombre'][:60]}" for x in tc])

    COD_IPC, COD_TC = "PN01273PM", "PN01215PM"

    s_ipc = serie(codigo=COD_IPC, desde="2020-01", hasta="2024-12")
    registrar(3, "MCP.serie", f"{COD_IPC} 2020-01..2024-12",
              f"{len(s_ipc['datos'])} periodos; fuente {s_ipc['fuente'][:60]}")
    r_ipc = resumen(codigo=COD_IPC, desde="2020-01", hasta="2024-12")
    registrar(4, "MCP.resumen", f"{COD_IPC} 2020-2024",
              {"min": r_ipc["minimo"], "max": r_ipc["maximo"],
               "promedio": r_ipc["promedio"]})
    s_tc = serie(codigo=COD_TC, desde="2020-01", hasta="2024-12")
    r_tc = resumen(codigo=COD_TC, desde="2020-01", hasta="2024-12")
    registrar(5, "MCP.serie+resumen", f"{COD_TC} 2020-2024",
              {"primero": r_tc["primero"], "ultimo": r_tc["ultimo"],
               "variacion_pct": r_tc["variacion_pct"]})
    corr = correlacion(codigo_a=COD_IPC, codigo_b=COD_TC,
                       desde="2020-01", hasta="2024-12")
    registrar(6, "MCP.correlacion", f"{COD_IPC} vs {COD_TC} 2020-2024",
              {"r": corr["r"], "n": corr["n"], "guia": corr["interpretacion"]})

    # --- fase Skills: ENAHO ------------------------------------------------
    rc, dt, out = skill(RAIZ / ".claude/skills/limpiando-enaho/scripts/limpiar.py")
    registrar(7, "Skill.limpiando-enaho", f"limpiar.py ({dt:.1f}s)",
              "OK" if rc == 0 else f"FALLO: {out[-200:]}")
    rc, dt, out = skill(RAIZ / ".claude/skills/graficando-enaho/scripts/graficar.py",
                        "todos")
    registrar(8, "Skill.graficando-enaho", f"graficar.py todos ({dt:.1f}s)",
              "OK" if rc == 0 else f"FALLO: {out[-200:]}")
    rc, dt, out = skill(RAIZ / ".claude/skills/mapeando-enaho/scripts/mapear.py")
    registrar(9, "Skill.mapeando-enaho", f"mapear.py ({dt:.1f}s)",
              "OK" if rc == 0 else f"FALLO: {out[-200:]}")

    (RAIZ / "salidas").mkdir(exist_ok=True)
    (RAIZ / "salidas" / "bitacora_agente.json").write_text(
        json.dumps(BITACORA, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[ok] salidas/bitacora_agente.json ({len(BITACORA)} pasos)")
    print("Insumos del informe listos: figuras/, mapas/, validaciones y series BCRP.")


if __name__ == "__main__":
    main()
