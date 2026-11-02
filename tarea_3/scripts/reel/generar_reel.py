# -*- coding: utf-8 -*-
"""Tarea 3 - Parte 3: genera guion.json, narracion TTS (edge-tts), musica
sintetizada y ensambla reel.mp4 (1080x1920) + subtitulos.srt.

Nota de transparencia: la narracion usa una voz neuronal de referencia
(es-PE-AlexNeural). Para clonar la voz propia, grabar 15-25 s y regenerar
con una herramienta de clonacion (ver reel/README nota en README principal).
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from moviepy.editor import (AudioFileClip, CompositeAudioClip, ImageClip,
                            concatenate_videoclips)

BASE = Path(__file__).resolve().parent.parent.parent
REC = BASE / "reel" / "recursos"
REEL = BASE / "reel"
VOZ = "clonada del estudiante (F5-TTS, referencia reel/recursos/mi_voz.wav)"

ESCENAS = [
    {"imagen": "escena1_gancho.png",
     "texto": "¿Sabías que en un solo año la pobreza en Perú saltó de veinte a treinta "
              "por ciento? En 2020, la pandemia empujó a casi tres millones de personas "
              "a la pobreza."},
    {"imagen": "escena2_peru.png",
     "texto": "Hoy, en 2024, la pobreza se ubica en 27 coma 6 por ciento: sigue siete "
              "puntos por encima del nivel prepandemia. La recuperación aún no cierra "
              "la brecha."},
    {"imagen": "escena3_region.png",
     "texto": "La región está profundamente dividida: Honduras registra 62 coma 9 por "
              "ciento de pobreza, más del doble que Uruguay, con 17 coma 3. Perú se "
              "ubica en la mitad de la tabla."},
    {"imagen": "escena4_reducciones.png",
     "texto": "Los caminos también difieren. Entre 2000 y 2024, Ecuador redujo su "
              "pobreza en 36 puntos. Costa Rica, en cambio, apenas avanzó tres décimas."},
    {"imagen": "escena5_gini.png",
     "texto": "Y la desigualdad también preocupa: Perú redujo su coeficiente de "
              "Gini a 40 coma 1, pero sigue por encima de referentes como Uruguay."},
    {"imagen": "escena6_cierre.png",
     "texto": "Explora el dashboard interactivo con los datos de dieciocho países, de "
              "2000 a 2024. El enlace está en la descripción. Fuente: Banco Mundial."},
]


def a_numero(t):
    return t.replace(" coma ", ",")


async def narrar(texto, destino):
    import edge_tts
    comunica = edge_tts.Communicate(texto, VOZ, rate="+8%")
    await comunica.save(str(destino))


def generar_narraciones():
    """Genera voces solo cuando no existe ni la voz clonada (.wav) ni la de referencia (.mp3)."""
    for i, esc in enumerate(ESCENAS, 1):
        if (REC / f"voz_escena{i}.wav").exists() or (REC / f"voz_escena{i}.mp3").exists():
            print(f"[ok] voz escena {i} (existente)")
            continue
        mp3 = REC / f"voz_escena{i}.mp3"
        print(f"[tts] escena {i} ({VOZ})...")
        asyncio.run(narrar(esc["texto"], mp3))


def voz_escena(i):
    wav = REC / f"voz_escena{i}.wav"
    return wav if wav.exists() else REC / f"voz_escena{i}.mp3"


def generar_musica(duracion, ruta):
    """Pad ambiental propio (sin derechos): acordes Am - F - C - G, 4 s c/u."""
    sr = 22050
    acordes = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63],
               [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
    t_acorde = 4.0
    ondas = []
    t = np.linspace(0, t_acorde, int(sr * t_acorde), endpoint=False)
    env = np.minimum(t / 0.8, 1.0) * np.minimum((t_acorde - t) / 0.8, 1.0)
    for acorde in acordes:
        o = sum(np.sin(2 * np.pi * f * t) * 0.28 for f in acorde)
        o += 0.4 * np.sin(2 * np.pi * (acorde[0] / 2) * t)
        ondas.append(o * env)
    ciclo = np.concatenate(ondas)
    reps = int(np.ceil(duracion / t_acorde)) + 1
    senal = np.tile(ciclo, reps)[: int(sr * duracion)]
    senal = (senal / np.abs(senal).max() * 0.9) * 0.14   # musica de fondo: bajo el volumen
    fade = int(sr * 1.5)
    senal[:fade] *= np.linspace(0, 1, fade)
    senal[-fade:] *= np.linspace(1, 0, fade)
    import wave
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((senal * 32767).astype(np.int16).tobytes())
    print(f"[ok] musica: {ruta.name} ({duracion:.0f} s)")


def ensamblar():
    clips_video, tiempos = [], []
    inicio = 0.0
    for i, esc in enumerate(ESCENAS, 1):
        audio = AudioFileClip(str(voz_escena(i)))
        dur = max(audio.duration + 0.3, 5.0)
        clip = (ImageClip(str(REC / esc["imagen"]))
                .set_duration(dur).set_audio(audio))
        clips_video.append(clip)
        tiempos.append((inicio, inicio + audio.duration, esc["texto"]))
        inicio += dur

    video = concatenate_videoclips(clips_video, method="compose")
    musica = AudioFileClip(str(REC / "musica.wav"))
    musica = musica.subclip(0, min(video.duration, musica.duration))
    video = video.set_audio(CompositeAudioClip([video.audio, musica]))

    salida = REEL / "reel.mp4"
    video.write_videofile(str(salida), fps=30, codec="libx264",
                          audio_codec="aac", bitrate="2500k",
                          preset="medium", threads=4)
    print(f"[ok] {salida.name}: {video.duration:.1f} s")

    # subtitulos sincronizados
    def fmt(s):
        h, m = int(s // 3600), int(s // 60) % 60
        return f"{h:02d}:{m:02d}:{int(s % 60):02d},{int((s % 1) * 1000):03d}"
    srt = "\n\n".join(
        f"{k}\n{fmt(a)} --> {fmt(b)}\n{a_numero(t)}"
        for k, (a, b, t) in enumerate(tiempos, 1))
    (REEL / "subtitulos.srt").write_text(srt, encoding="utf-8")
    print("[ok] subtitulos.srt")

    guion = {"voz": VOZ, "formato": "1080x1920 (9:16)", "duracion_s": round(video.duration, 1),
             "escenas": [{"imagen": e["imagen"], "narracion": e["texto"],
                          "inicio_s": round(t[0], 1), "fin_s": round(t[1], 1)}
                         for e, t in zip(ESCENAS, tiempos)]}
    (REEL / "guion.json").write_text(
        json.dumps(guion, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[ok] guion.json")


if __name__ == "__main__":
    if "--solo-musica" in sys.argv:
        generar_musica(90, REC / "musica.wav")
    else:
        generar_narraciones()
        dur_aprox = 95.0
        if not (REC / "musica.wav").exists():
            generar_musica(dur_aprox, REC / "musica.wav")
        ensamblar()
