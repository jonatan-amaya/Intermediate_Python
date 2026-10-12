# -*- coding: utf-8 -*-
"""Replica la ruta de inferencia de app.py para validarla sin el navegador."""
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RUTA_MODELO = Path("modelo")
CATEGORIAS = ["politica", "economia", "deportes", "ciencia_tecnologia"]

modelo = AutoModelForSequenceClassification.from_pretrained(str(RUTA_MODELO))
tokenizer = AutoTokenizer.from_pretrained(str(RUTA_MODELO))
modelo.eval()

pruebas = [
    ("Congreso aprueba nueva ley de pensiones y reforma del sistema de AFP", "economia"),
    ("Alianza Lima venció 2-0 a Universitario en el clásico por la Liga 1", "deportes"),
    ("Científicos peruanos descubren nueva especie de rana en la Amazonía", "ciencia_tecnologia"),
    ("Presidenta Fujimori anuncia cambios en el gabinete tras crisis política", "politica"),
]

ok = 0
for texto, esperado in pruebas:
    entradas = tokenizer(texto, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        probs = torch.softmax(modelo(**entradas).logits, dim=-1)[0]
    idx = int(probs.argmax())
    marca = "OK " if CATEGORIAS[idx] == esperado else "FALLO"
    ok += CATEGORIAS[idx] == esperado
    print(f"{marca} pred={CATEGORIAS[idx]:<20} conf={probs[idx]:.3f} | {texto[:60]}")

print(f"\n{ok}/{len(pruebas)} titulares de prueba clasificados como se esperaba")
