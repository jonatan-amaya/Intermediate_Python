# -*- coding: utf-8 -*-
"""Precarga los modelos de HuggingFace usados en la tarea."""
from huggingface_hub import snapshot_download

for repo in ["joeddav/xlm-roberta-large-xnli", "distilbert-base-multilingual-cased"]:
    p = snapshot_download(repo)
    print("OK", repo, "->", p, flush=True)
