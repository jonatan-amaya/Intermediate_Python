# -*- coding: utf-8 -*-
"""Tarea 3 - Parte 3: clona la voz del estudiante (referencia mi_voz.wav) y
regenera las 6 narraciones del reel con VoxCPM2 (modelo local).

Uso: python scripts/reel/clonar_voz.py
Salida: sobrescribe reel/recursos/voz_escena{1..6}.mp3 (respaldo en _respaldo_ref/)
"""
import json
import shutil
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent.parent.parent
REC = BASE / "reel" / "recursos"
REFERENCIA = REC / "mi_voz.wav"

CANDIDATOS = ["openbmb/VoxCPM2", "openbmb/VoxCPM-1.5B", "openbmb/VoxCPM2-1.5B"]


def cargar_modelo():
    from voxcpm import VoxCPM
    for repo in CANDIDATOS:
        try:
            print(f"[modelo] intentando {repo} ...")
            modelo = VoxCPM.from_pretrained(repo)
            print(f"[modelo] OK: {repo}")
            return modelo
        except Exception as e:
            print(f"[modelo] fallo: {e}")
    raise RuntimeError("No se pudo cargar ningun modelo VoxCPM")


def transcribir_referencia():
    """VoxCPM2 exige prompt_text junto al audio: se transcribe la grabacion."""
    from faster_whisper import WhisperModel
    print("[whisper] transcribiendo tu grabacion de referencia...")
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segmentos, info = modelo.transcribe(str(REFERENCIA), language="es")
    texto = " ".join(s.text for s in segmentos).strip()
    print(f"[whisper] idioma={info.language} prob={info.language_probability:.2f}")
    print(f"[whisper] dijiste: {texto}")
    return texto


def main():
    guion = json.loads((BASE / "reel" / "guion.json").read_text("utf-8"))
    escenas = guion["escenas"]

    respaldo = REC / "_respaldo_ref"
    respaldo.mkdir(exist_ok=True)
    for i in range(1, len(escenas) + 1):
        viejo = REC / f"voz_escena{i}.mp3"
        if viejo.exists():
            shutil.copy2(viejo, respaldo / viejo.name)

    import soundfile as sf
    modelo = cargar_modelo()
    prompt_text = transcribir_referencia()

    for i, esc in enumerate(escenas, 1):
        destino = REC / f"voz_escena{i}.wav"
        texto = esc["narracion"].replace(",", "，")  # separacion natural
        print(f"[clone] escena {i}/{len(escenas)}: {texto[:50]}...")
        wav = modelo.generate(
            text=texto,
            prompt_wav_path=str(REFERENCIA),
            prompt_text=prompt_text,
            inference_timesteps=8,
        )
        datos = np.asarray(wav)
        sf.write(str(destino), datos, 16000)
        print(f"[clone] escena {i} OK -> {destino.name}")

    print("listo: narraciones con voz clonada")


if __name__ == "__main__":
    main()
