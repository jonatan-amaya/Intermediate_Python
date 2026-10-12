# -*- coding: utf-8 -*-
"""Ejecuta un notebook in-place con nbclient (entorno tarea1)."""
import sys

import nbformat
from nbclient import NotebookClient

ruta = sys.argv[1]
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 3600

nb = nbformat.read(ruta, as_version=4)
client = NotebookClient(
    nb,
    timeout=timeout,
    kernel_name="python3",
    resources={"metadata": {"path": "."}},
)
client.execute()
nbformat.write(nb, ruta)
print("EJECUCION OK:", ruta)
