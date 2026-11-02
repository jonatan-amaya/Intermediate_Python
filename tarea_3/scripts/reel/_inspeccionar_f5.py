# -*- coding: utf-8 -*-
import inspect
from f5_tts.api import F5TTS
print(inspect.signature(F5TTS.infer))
src = inspect.getsource(F5TTS.infer)
print(src[:2000])
