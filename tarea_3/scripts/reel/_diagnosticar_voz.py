# -*- coding: utf-8 -*-
"""Diagnostica una o varias voces: duracion + transcripcion."""
import sys
from faster_whisper import WhisperModel
from moviepy.editor import AudioFileClip

modelo = WhisperModel("small", device="cpu", compute_type="int8")
for i in range(1, 7):
    ruta = f"reel/recursos/voz_escena{i}.wav"
    a = AudioFileClip(ruta)
    segs, _ = modelo.transcribe(ruta, language="es")
    texto = " ".join(s.text for s in segs).strip()
    print(f"--- escena {i}: {a.duration:.1f} s")
    print(f"    dice: {texto[:170]}")
    a.close()
