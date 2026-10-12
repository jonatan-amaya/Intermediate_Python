# -*- coding: utf-8 -*-
"""Dashboard interactivo – Tarea 1: clasificador de noticias peruanas (La República)."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
RUTA_DATOS = BASE / "datos"
RUTA_MODELO = BASE / "modelo"

CATEGORIAS = ["politica", "economia", "deportes", "ciencia_tecnologia"]
COLORES = {"politica": "#d62728", "economia": "#2ca02c",
           "deportes": "#ff7f0e", "ciencia_tecnologia": "#1f77b4"}

st.set_page_config(page_title="Clasificador de noticias peruanas",
                   page_icon="🗞️", layout="wide")

st.title("🗞️ ¿Pueden convertir titulares peruanos en un clasificador de noticias?")
st.caption("Tarea 1 – Data Science Python | Medio: La República (Opción A) | "
           "Extracción: 2026-10-12")

with st.expander("📋 Resumen metodológico"):
    st.markdown(
        """
        1. **Recolección:** 350+ titulares reales de `larepublica.pe` vía RSS/sitemaps
        oficiales e índice histórico (Wayback CDX); lectura del contenido por las
        versiones AMP del medio (el HTML directo bloquea bots con un desafío JS,
        situación documentada en `01_recoleccion.ipynb`).
        2. **Etiquetado:** las 4 categorías oficiales provienen del mapeo de secciones
        editoriales; un LLM etiquetó el corpus completo con *prompt* estructurado
        (`etiquetas_llm.csv`) y se auditó una muestra de 20 casos contra criterio humano.
        3. **Modelo:** *fine-tuning* de **DistilBERT multilingüe** (3 épocas, split
        70/15/15 estratificado) con F1 macro como métrica de optimización. Detalles en
        `02_clasificacion.ipynb`.
        """)


# ----------------------------------------------------------------- datos
@st.cache_data
def cargar_datos() -> pd.DataFrame:
    df = pd.read_csv(RUTA_DATOS / "noticias.csv")
    ruta_llm = RUTA_DATOS / "etiquetas_llm.csv"
    if ruta_llm.exists():
        llm = pd.read_csv(ruta_llm).drop_duplicates(subset="titular")
        df = df.merge(llm[["titular", "etiqueta_llm", "confianza"]],
                      on="titular", how="left")
    return df


@st.cache_data
def cargar_metricas() -> dict:
    ruta = RUTA_MODELO / "metrics.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return {}


df = cargar_datos()
metricas = cargar_metricas()

# ----------------------------------------------------------------- filtros (sidebar)
st.sidebar.header("🔎 Filtros")
medios = ["Todos"] + sorted(df["medio"].unique().tolist())
medio = st.sidebar.selectbox("Medio", medios)
cats_sel = st.sidebar.multiselect("Categoría", CATEGORIAS, default=CATEGORIAS)

filtrado = df[df["etiqueta"].isin(cats_sel)]
if medio != "Todos":
    filtrado = filtrado[filtrado["medio"] == medio]

# ----------------------------------------------------------------- indicadores
c1, c2, c3 = st.columns(3)
c1.metric("Total de noticias recolectadas", f"{len(df):,}")
c2.metric("F1 macro del modelo (test)",
          metricas.get("f1_macro_test", "—"))
c3.metric("Concordancia LLM vs. auditoría humana",
          metricas.get("acuerdo_llm_humano", "—"))

st.divider()

# ----------------------------------------------------------------- exploración
izq, der = st.columns([2, 3])

with izq:
    st.subheader("Distribución de categorías (filtrada)")
    if len(filtrado):
        conteo = (filtrado["etiqueta"].value_counts().reindex(cats_sel).fillna(0)
                  .reset_index().rename(columns={"index": "etiqueta", "etiqueta": "n"}))
        fig = px.bar(conteo, x="etiqueta", y="n", color="etiqueta",
                     color_discrete_map=COLORES,
                     labels={"etiqueta": "Categoría", "n": "N° de noticias"},
                     title="Volumen de noticias por categoría seleccionada")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para los filtros elegidos.")

with der:
    st.subheader("Noticias (vista filtrada)")
    st.dataframe(filtrado, use_container_width=True, height=380)
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=filtrado.to_csv(index=False).encode("utf-8-sig"),
        file_name="noticias_filtradas.csv",
        mime="text/csv",
    )

st.divider()

# ----------------------------------------------------------------- probador en vivo
st.subheader("🧪 Probador en vivo: clasifica un titular nuevo")
titular_nuevo = st.text_input(
    "Escribe o pega un titular de noticia peruana:",
    placeholder="Ej.: Congreso aprueba nueva ley de pensiones tras intenso debate",
)


@st.cache_resource
def cargar_clasificador():
    """Carga el modelo fine-tuned de modelo/; si no está, cae a zero-shot."""
    try:
        import torch
        from transformers import (AutoModelForSequenceClassification,
                                  AutoTokenizer)
        modelo = AutoModelForSequenceClassification.from_pretrained(str(RUTA_MODELO))
        tokenizer = AutoTokenizer.from_pretrained(str(RUTA_MODELO))
        return "fine-tuned", (modelo, tokenizer)
    except Exception:
        from transformers import pipeline
        clasificador = pipeline(
            "zero-shot-classification",
            model="joeddav/xlm-roberta-large-xnli")
        return "zero-shot (respaldo)", clasificador


if st.button("Clasificar titular", type="primary"):
    if not titular_nuevo or len(titular_nuevo.strip()) < 10:
        st.warning("Ingresa un titular válido (mínimo ~10 caracteres).")
    else:
        with st.spinner("Clasificando…"):
            modo, obj = cargar_clasificador()
            if modo.startswith("fine-tuned"):
                import torch
                modelo, tokenizer = obj
                entradas = tokenizer(titular_nuevo, return_tensors="pt",
                                     truncation=True, max_length=128)
                with torch.no_grad():
                    logits = modelo(**entradas).logits
                probs = torch.softmax(logits, dim=-1)[0].tolist()
            else:
                nat = {"politica": "política", "economia": "economía",
                       "deportes": "deportes", "ciencia_tecnologia":
                       "ciencia y tecnología"}
                r = obj(titular_nuevo, candidate_labels=list(nat.values()))
                probs = [0.0] * 4
                for lab, p in zip(r["labels"], r["scores"]):
                    for oficial, natural in nat.items():
                        if lab == natural:
                            probs[CATEGORIAS.index(oficial)] = p

        idx = int(probs.index(max(probs)))
        conf = probs[idx]
        c1, c2 = st.columns(2)
        c1.metric("Categoría predicha", CATEGORIAS[idx])
        c2.metric("Confianza", f"{conf:.1%}")
        st.caption(f"Motor de inferencia: {modo}")
        fig_p = px.bar(x=CATEGORIAS, y=probs, color=CATEGORIAS,
                       color_discrete_map=COLORES,
                       labels={"x": "Categoría", "y": "Probabilidad"},
                       title="Probabilidad por categoría")
        fig_p.update_layout(showlegend=False)
        st.plotly_chart(fig_p, use_container_width=True)
