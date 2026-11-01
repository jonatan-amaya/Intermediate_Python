# -*- coding: utf-8 -*-
"""Verifica el reel generado (duracion, resolucion, audio, frame de control)."""
from moviepy.editor import VideoFileClip

v = VideoFileClip("reel/reel.mp4")
print(f"duracion: {v.duration:.1f} s | resolucion: {v.w}x{v.h} | fps: {v.fps}")
print("audio presente:", v.audio is not None)
v.save_frame("reel/recursos/_verificacion_frame.png", t=v.duration * 0.5)
v.save_frame("reel/recursos/_verificacion_inicio.png", t=1.0)
print("frames guardados")
