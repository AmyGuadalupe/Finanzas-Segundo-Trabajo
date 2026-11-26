"""Menú circular interactivo de las siete secciones (núcleo, anillos y tarjetas radiales).

Las tarjetas son botones reales de Streamlit (abren la sección con ``nav.ir``); la capa decorativa (anillos, rayos,
barridos y rótulo del núcleo) es SVG/CSS y la profundidad (inclinación, luz, paralaje) la añade el motor JS.
"""
from __future__ import annotations

import streamlit as st

import estilos as es
import nav


def render(activa: str | None = None) -> None:
    claves = nav.CLAVES_SECCION
    activa = activa or st.session_state.get("nav_ultima", "introduccion")
    st.markdown(es.css_radial(claves, activa), unsafe_allow_html=True)
    with st.container(key="radial"):
        with st.container(key="radial_fondo"):
            st.markdown(es.capa_radial(nav.SECCIONES, activa), unsafe_allow_html=True)
        for clave, nombre in nav.SECCIONES:
            st.button(nombre, key=f"nav_{clave}", on_click=nav.ir, args=("s1", clave), help=f"Abrir: {nombre}")
    st.markdown("<p class='fm-teclas'><kbd>←</kbd><kbd>→</kbd> recorrer las tarjetas · <kbd>Enter</kbd> abrir · "
                "<kbd>1</kbd>–<kbd>7</kbd> ir directo a una sección</p>", unsafe_allow_html=True)
