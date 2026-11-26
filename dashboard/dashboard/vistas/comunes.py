"""Elementos comunes del portal: barra superior, pie y bloques de contenido."""
from __future__ import annotations

import base64
import html
import mimetypes

import streamlit as st

import nav
import portal_config as pc
import estilos as es


def barra_superior() -> None:
    """Navegación general: inicio, las dos secciones, el repositorio y el interruptor de movimiento (visible en todas las vistas)."""
    repo = pc.portal()["repositorio_url"]
    with st.container(key="topbar"):
        c = st.columns([0.95, 2.15, 2.15, 1.5, 1.45], gap="small", vertical_alignment="center")
        c[0].button("Inicio", icon=":material/home:", key="tb_inicio", on_click=nav.ir, args=("inicio",), width="stretch",
                    type="primary" if nav.vista() == "inicio" else "secondary")
        c[1].button("01 · Productos académicos", icon=":material/menu_book:", key="tb_s1", on_click=nav.ir, args=("s1",), width="stretch",
                    type="primary" if nav.vista() == "s1" else "secondary")
        c[2].button("02 · Base de datos y análisis", icon=":material/monitoring:", key="tb_s2", on_click=nav.ir, args=("s2",), width="stretch",
                    type="primary" if nav.vista() == "s2" else "secondary")
        c[3].link_button("Repositorio GitHub", repo, icon=":material/code:", width="stretch")
        c[4].toggle("Reducir animaciones", key="fm_reducir",
                    help="Desactiva las animaciones y transiciones del portal. También se respeta la preferencia de movimiento reducido del sistema.")


def pie() -> None:
    p = pc.portal()
    st.markdown(
        f"<div class='fm-pie'>{html.escape(p['universidad'])} · {html.escape(p['facultad'])} · {html.escape(p['curso'])} ({html.escape(p['unidad'])}) · "
        f"{html.escape(p['periodo'])} · {html.escape(p['autora'])}. Diseño observacional: los resultados no constituyen recomendación de inversión. "
        f"<a href='{html.escape(p['repositorio_url'])}' target='_blank' rel='noopener'>Repositorio de la investigación</a>.</div>",
        unsafe_allow_html=True,
    )


def imagen_data_uri(ruta) -> str | None:
    if not ruta:
        return None
    tipo = mimetypes.guess_type(str(ruta))[0] or "image/png"
    return f"data:{tipo};base64," + base64.b64encode(ruta.read_bytes()).decode()


def chip_estado(estado: str) -> str:
    texto, clase = pc.estado_visible(estado)
    return es.chip(texto, clase)


def bloque(titulo: str, texto: str, origen: str = "") -> None:
    """Bloque de contenido: si no hay texto, muestra un marcador discreto de pendiente."""
    if texto and texto.strip():
        etiqueta = es.chip("Documentación del proyecto", "proy") if origen == "proyecto" else (es.chip("Journal", "ok") if origen == "journal" else "")
        st.markdown(f"<div class='fm-bloque'><h4>{html.escape(titulo)} {etiqueta}</h4></div>", unsafe_allow_html=True)
        st.markdown(texto)
    else:
        st.markdown(
            f"<div class='fm-bloque pend'><h4>{html.escape(titulo)} {es.chip('Pendiente', 'pend')}</h4>"
            "<p class='vacio'>Este apartado se incorporará desde el journal definitivo (config/contenido_secciones.json).</p></div>",
            unsafe_allow_html=True,
        )
