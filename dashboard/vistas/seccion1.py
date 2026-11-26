"""Sección 01: productos académicos y desarrollo científico."""
from __future__ import annotations

import html

import streamlit as st

import estilos as es
import nav
from vistas import menu_radial, productos, secciones


def _cabecera_menu() -> None:
    st.markdown("<div class='fm-entra'><div style='text-transform:uppercase;letter-spacing:.14em;font-size:.7rem;font-weight:700;color:#13917f'>Sección 01</div>"
                "<h1 tabindex='-1' data-fm-foco style='margin:.1rem 0 .2rem;font-size:clamp(1.6rem,3.4vw,2.4rem)'>Productos académicos y desarrollo científico</h1>"
                "<p style='color:#4a5368;max-width:70ch'>Recorre la investigación en siete secciones. Selecciona una tarjeta del menú circular para desplegar su contenido.</p></div>",
                unsafe_allow_html=True)


def _vista_seccion(clave: str) -> None:
    nombre = nav.NOMBRE_SECCION[clave]
    with st.container(key="chips"):
        cols = st.columns([1.5] + [1] * len(nav.SECCIONES), gap="small")
        cols[0].button("Menú general", icon=":material/donut_large:", key="c_menu", on_click=nav.ir, args=("s1",), type="primary", width="stretch")
        for col, (k, n) in zip(cols[1:], nav.SECCIONES):
            col.button(n.split(" e ")[0] if k == "discusion" else n, key=f"c_{k}", on_click=nav.ir, args=("s1", k), width="stretch",
                       type="secondary", disabled=(k == clave), help=n)
    idx = nav.CLAVES_SECCION.index(clave) + 1
    st.markdown(f"<div class='fm-secc-cab'><div class='ic'>{es.icono_html(clave)}</div><div><small>Sección {idx} de 7</small>"
                f"<h2 tabindex='-1' data-fm-foco>{html.escape(nombre)}</h2></div>{es.rueda_mini(nav.CLAVES_SECCION, clave)}</div>", unsafe_allow_html=True)
    if not (clave == "antecedentes" and nav.ficha()):
        st.markdown("<p class='fm-atajos'>Teclado: <kbd>←</kbd> <kbd>→</kbd> sección anterior o siguiente · <kbd>Esc</kbd> volver al menú circular</p>", unsafe_allow_html=True)
    secciones.RENDER[clave]()
    ant, sig = nav.vecinas(clave)
    st.divider()
    b = st.columns([1, 1, 1])
    if ant:
        b[0].button(f"← {nav.NOMBRE_SECCION[ant]}", key="p_ant", on_click=nav.ir, args=("s1", ant, None, -1), width="stretch")
    b[1].button("Volver al menú general", icon=":material/donut_large:", key="p_menu", on_click=nav.ir, args=("s1",), width="stretch")
    if sig:
        b[2].button(f"{nav.NOMBRE_SECCION[sig]} →", key="p_sig", on_click=nav.ir, args=("s1", sig, None, 1), width="stretch")


def render() -> None:
    sec = nav.seccion()
    with st.container(key=f"pagina_{nav.lado_entrada()}_s1_{sec or 'menu'}_{nav.ficha() or 'x'}"):
        if sec:
            _vista_seccion(sec)
        else:
            _cabecera_menu()
            menu_radial.render()
            productos.render()
