"""Portal científico interactivo · Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo.

Tema 79 · Finanzas I (055D) · UNCP · Amy Pamela Guadalupe Cordova (2024200501G).
Router de tres vistas (inicio, sección 01, sección 02). Solo lee los archivos entregados
de la investigación; nunca vuelve a extraer datos al abrirse.
Ejecutar desde la raíz del repositorio:  streamlit run dashboard/app.py
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

import streamlit as st

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import estilos as es  # noqa: E402
import interaccion  # noqa: E402
import nav  # noqa: E402
import portal_config as pc  # noqa: E402
from vistas import comunes as cm  # noqa: E402

st.set_page_config(page_title="Fondos mutuos en el Perú · Portal científico", page_icon=":material/monitoring:",
                   layout="wide", initial_sidebar_state="auto")

nav.iniciar()
v = nav.vista()
reducir = bool(st.session_state.get("fm_reducir", False))
es.inyectar(solo_portal=(v != "s2"), reducir=reducir)
interaccion.montar(v, nav.seccion(), nav.ficha(), reducir)
cm.barra_superior()
st.markdown('<div id="fm-contenido" tabindex="-1"></div>', unsafe_allow_html=True)

if v == "s2":
    runpy.run_path(str(AQUI / "panel_financiero.py"), run_name="__panel__")
elif v == "s1":
    from vistas import seccion1
    seccion1.render()
    cm.pie()
else:
    from vistas import portada
    portada.render()
    cm.pie()

nav.sincronizar_url()
