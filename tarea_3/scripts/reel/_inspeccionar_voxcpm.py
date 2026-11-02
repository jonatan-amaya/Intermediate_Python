# -*- coding: utf-8 -*-
import inspect
from voxcpm import VoxCPM

print("generate (fuente):", inspect.getsource(VoxCPM.generate)[:1500])
print("==================================")
for nombre in dir(VoxCPM):
    if "gen" in nombre.lower():
        metodo = getattr(VoxCPM, nombre)
        try:
            print(nombre, inspect.signature(metodo))
        except (TypeError, ValueError):
            print(nombre, "(sin firma)")
