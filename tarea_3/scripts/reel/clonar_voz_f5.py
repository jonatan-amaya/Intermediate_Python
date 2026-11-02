# -*- coding: utf-8 -*-
"""Tarea 3 - Parte 3 (clonacion con F5-TTS): regenera narraciones con la voz
del estudiante a partir de reel/recursos/mi_voz.wav (+ transcripcion whisper).

Uso: python scripts/reel/clonar_voz_f5.py [numeros de escena ...]
(sin argumentos: regenera las 6)"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
REC = BASE / "reel" / "recursos"
REF24 = REC / "mi_voz_24k.wav"


def preparar_referencia():
    """F5-TTS espera 24 kHz mono; ademas se parchea torchaudio.load para no
    depender de FFmpeg/torchcodec (se carga con soundfile)."""
    import torch
    import torchaudio

    def _load_sf(path, *a, **k):
        import soundfile as sf
        datos, sr = sf.read(str(path), dtype="float32")
        tensor = torch.from_numpy(datos)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)
        else:
            tensor = tensor.T
        return tensor, sr

    torchaudio.load = _load_sf   # parche: el guardado ya usa soundfile
    if REF24.exists():
        return
    import subprocess
    ffmpeg = subprocess.run(
        ["python", "-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"],
        capture_output=True, text=True).stdout.strip()
    subprocess.run([ffmpeg, "-y", "-i", str(REC / "mi_voz.wav"),
                    "-ac", "1", "-ar", "24000", str(REF24)], check=True,
                   capture_output=True)
    print("[ok] referencia 24k:", REF24.name)


def transcribir():
    from faster_whisper import WhisperModel
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segs, info = modelo.transcribe(str(REF24), language="es")
    texto = " ".join(s.text for s in segs).strip()
    print(f"[whisper] referencia: {texto}")
    return texto


def main():
    solo = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    guion = json.loads((BASE / "reel" / "guion.json").read_text("utf-8"))
    preparar_referencia()
    ref_text = transcribir()

    from f5_tts.api import F5TTS
    print("[modelo] cargando F5TTS_v1_Base ...")
    f5 = F5TTS(model="F5TTS_v1_Base", device="cpu")
    print("[modelo] OK")

    for i, esc in enumerate(guion["escenas"], 1):
        if solo and i not in solo:
            continue
        destino = REC / f"voz_escena{i}.wav"
        print(f"[clone] escena {i}/{len(guion['escenas'])}: {esc['narracion'][:50]}...")
        wav, sr, _ = f5.infer(
            ref_file=str(REF24),
            ref_text=ref_text,
            gen_text=esc["narracion"],
            speed=1.1,
            file_wave=str(destino),
        )
        print(f"[clone] escena {i} OK -> {destino.name}")
    print("listo")


if __name__ == "__main__":
    main()
