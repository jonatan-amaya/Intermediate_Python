# -*- coding: utf-8 -*-
"""Prueba una escena sin el hack de comas y con mas pasos de inferencia."""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

REC = Path("reel/recursos")
guion_escena1 = ("¿Sabías que en un solo año la pobreza en Perú saltó de veinte a "
                 "treinta por ciento? En 2020, la pandemia empujó a casi tres "
                 "millones de personas a la pobreza.")

from voxcpm import VoxCPM
modelo = VoxCPM.from_pretrained("openbmb/VoxCPM2")
prompt_text = ("¿Sabías que en una en solo año la pobreza en Perú saltó de 20 a 30%? "
               "En 2020 la pandemia empujó a casi 3 millones de personas a la "
               "pobreza extrema.")

for pasos in (20, 50):
    print(f"[prueba] inference_timesteps={pasos}")
    wav = modelo.generate(text=guion_escena1,
                          prompt_wav_path=str(REC / "mi_voz.wav"),
                          prompt_text=prompt_text,
                          inference_timesteps=pasos)
    out = REC / f"_prueba_escena1_t{pasos}.wav"
    sf.write(str(out), np.asarray(wav), 16000)
    print(f"[prueba] {out}")

# diagnostico inmediato
from faster_whisper import WhisperModel
wm = WhisperModel("small", device="cpu", compute_type="int8")
for pasos in (20, 50):
    ruta = str(REC / f"_prueba_escena1_t{pasos}.wav")
    segs, _ = wm.transcribe(ruta, language="es")
    print(f"t={pasos} dice:", " ".join(s.text for s in segs).strip()[:160])
