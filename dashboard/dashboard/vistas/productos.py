"""Productos académicos principales: journal, póster principal, presentación y paquete general."""
from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components

import portal_config as pc
from vistas import comunes as cm


def _miniatura(d: dict, etiqueta: str, ancha: bool = False) -> None:
    url, local = d.get("miniatura", ""), pc.ruta_asset(d.get("miniatura", ""))
    if local:
        st.image(str(local), width="stretch")  # el icono de pantalla completa de st.image amplía la imagen
    elif pc.es_url(url):
        st.image(url, width="stretch")
    else:
        st.markdown(f"<div class='fm-miniatura {'ancha' if ancha else ''}'><b>{html.escape(etiqueta[:1])}</b>Vista previa pendiente</div>", unsafe_allow_html=True)


def _boton(etiqueta: str, url: str, icono: str, clave: str, estado: str) -> None:
    if pc.es_url(url):
        st.link_button(etiqueta, url, icon=icono, width="stretch")
    else:
        st.button(etiqueta, icon=icono, disabled=True, width="stretch", key=clave, help=f"No disponible: {pc.estado_visible(estado)[0].lower()}")


def _visor(url: str, titulo: str, clave: str, alto: int = 620) -> None:
    if pc.es_url(url):
        with st.expander(f"Visualizar · {titulo}", icon=":material/visibility:"):
            components.iframe(pc.url_visor(url), height=alto, scrolling=True)
            st.link_button("Abrir a pantalla completa", pc.url_visor(url), icon=":material/fullscreen:")
    else:
        st.button(f"Visualizar · {titulo}", icon=":material/visibility_off:", disabled=True, width="stretch", key=f"vis_{clave}")


def _tarjeta(clave: str, d: dict, icono: str, ancha: bool = False, extra_repo: str | None = None) -> None:
    st.markdown(f"<div class='fm-prod'><h4 style='margin:0 0 4px;font-family:var(--serif)'>{html.escape(d['titulo'])}</h4>"
                f"{cm.chip_estado(d.get('estado', 'pendiente'))}</div>", unsafe_allow_html=True)
    _miniatura(d, d["titulo"], ancha)
    st.caption(d["descripcion"])
    vis = d.get("visualizacion_url", "")
    _visor(vis, d["titulo"], clave)
    _boton("Descargar PDF", pc.url_descarga(d.get("descarga_pdf_url", "")) if d.get("descarga_pdf_url") else "", ":material/picture_as_pdf:", f"pdf_{clave}", d.get("estado", ""))
    _boton("Proyecto fuente editable (ZIP)", pc.url_descarga(d.get("proyecto_zip_url", "")) if d.get("proyecto_zip_url") else "", ":material/folder_zip:", f"zip_{clave}", d.get("estado", ""))
    if extra_repo:
        st.link_button("Repositorio GitHub", extra_repo, icon=":material/code:", width="stretch")


def render() -> None:
    p = pc.portal()
    pr = pc.documentos()["productos"]
    st.markdown("<h2 style='margin-top:2rem'>Productos académicos principales</h2>", unsafe_allow_html=True)
    st.caption("Los documentos se alojan fuera del repositorio (Google Drive u otro servicio) y se administran desde config/documentos.json. "
               "Mientras estén en elaboración se muestran con su estado, sin enlaces inventados.")
    c = st.columns(3, gap="medium")
    with c[0]:
        _tarjeta("journal", pr["journal"], "article", extra_repo=p["repositorio_url"])
    with c[1]:
        _tarjeta("poster", pr["poster_principal"], "image")
    with c[2]:
        _tarjeta("presentacion", pr["presentacion"], "slideshow", ancha=True)
    g = pr["paquete_general"]
    st.markdown("<div class='fm-bloque' style='margin-top:14px'><h4>Paquete general de plantillas y proyectos académicos "
                f"{cm.chip_estado(g.get('estado', 'pendiente'))}</h4><p class='vacio'>{html.escape(g['descripcion'])} "
                "Los proyectos se desarrollan en Typst, sin perjuicio de los requisitos de LaTeX de la consigna docente.</p></div>", unsafe_allow_html=True)
    _boton("Descargar paquete ZIP general", pc.url_descarga(g.get("descarga_url", "")) if g.get("descarga_url") else "", ":material/folder_zip:", "zip_general", g.get("estado", ""))
