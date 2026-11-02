# -*- coding: utf-8 -*-
"""Calibra whisper: transcribe las voces de referencia (edge-tts, audio integro)."""
from faster_whisper import WhisperModel

modelo = WhisperModel("small", device="cpu", compute_type="int8")
for i in (2, 5):
    ruta = f"reel/recursos/_respaldo_ref/voz_escena{i}.mp3"
    segs, _ = modelo.transcribe(ruta, language="es")
    texto = " ".join(s.text for s in segs).strip()
    print(f"--- referencia escena {i}:")
    print(f"    dice: {texto[:170]}")
