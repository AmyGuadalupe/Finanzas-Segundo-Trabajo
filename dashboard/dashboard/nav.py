"""Navegación del portal: vista, sección y ficha activas, sincronizadas con la URL.

La URL conserva el enlace público existente; los parámetros (?v=, ?sec=, ?art=)
permiten compartir una sección concreta y usar el botón «atrás» del navegador.
"""
from __future__ import annotations

import streamlit as st

VISTAS = ("inicio", "s1", "s2")
SECCIONES = [
    ("introduccion", "Introducción"),
    ("marco", "Marco teórico"),
    ("antecedentes", "Antecedentes"),
    ("metodos", "Materiales y métodos"),
    ("resultados", "Resultados"),
    ("discusion", "Discusión e implicaciones"),
    ("conclusiones", "Conclusiones"),
]
CLAVES_SECCION = [c for c, _ in SECCIONES]
NOMBRE_SECCION = dict(SECCIONES)


def iniciar() -> None:
    """Carga el estado desde la URL en la primera ejecución de la sesión."""
    if st.session_state.get("_nav_listo"):
        return
    q = st.query_params
    v = q.get("v", "inicio")
    sec = q.get("sec")
    art = q.get("art")
    st.session_state.nav_vista = v if v in VISTAS else "inicio"
    st.session_state.nav_sec = sec if sec in CLAVES_SECCION else None
    st.session_state.nav_art = art if (art and art.startswith("A") and len(art) == 3) else None
    st.session_state.nav_ultima = st.session_state.nav_sec or "introduccion"
    st.session_state.nav_dir = 0
    st.session_state._fm_foco = False
    st.session_state._nav_listo = True


def ir(vista: str = "inicio", sec: str | None = None, art: str | None = None, direccion: int = 0) -> None:
    """Callback de botones: cambia de vista, sección o ficha.

    ``direccion`` (-1 anterior, +1 siguiente, 0 apertura) solo decide por qué lado entra el contenido nuevo;
    la bandera ``_fm_foco`` indica al motor visual que debe mover el foco al título y anunciar el cambio.
    """
    st.session_state.nav_vista = vista if vista in VISTAS else "inicio"
    st.session_state.nav_sec = sec if sec in CLAVES_SECCION else None
    st.session_state.nav_art = art
    st.session_state.nav_dir = direccion
    st.session_state._fm_foco = True
    if sec in CLAVES_SECCION:
        st.session_state.nav_ultima = sec


def vista() -> str:
    return st.session_state.get("nav_vista", "inicio")


def seccion() -> str | None:
    return st.session_state.get("nav_sec")


def ficha() -> str | None:
    return st.session_state.get("nav_art")


def lado_entrada() -> str:
    """Sufijo para la clave del contenedor de página: por qué lado entra el contenido (izq, der o n)."""
    return {-1: "izq", 1: "der"}.get(st.session_state.get("nav_dir", 0), "n")


def sincronizar_url() -> None:
    """Refleja el estado en la URL (sin recargar la página)."""
    nuevo = {}
    if vista() != "inicio":
        nuevo["v"] = vista()
    if vista() == "s1" and seccion():
        nuevo["sec"] = seccion()
        if seccion() == "antecedentes" and ficha():
            nuevo["art"] = ficha()
    if dict(st.query_params) != nuevo:
        st.query_params.from_dict(nuevo)


def vecinas(clave: str) -> tuple[str | None, str | None]:
    i = CLAVES_SECCION.index(clave)
    return (CLAVES_SECCION[i - 1] if i > 0 else None, CLAVES_SECCION[i + 1] if i < len(CLAVES_SECCION) - 1 else None)
