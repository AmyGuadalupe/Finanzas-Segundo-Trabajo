"""Puente entre Streamlit y el motor de interacción (``static/interaccion.js``).

El motor se inyecta una sola vez en el documento de la aplicación desde un componente HTML invisible
(``components.html``); en cada ejecución solo se actualiza un marcador oculto (``#fm-meta``) con la vista actual.
Si el navegador o la plataforma impidieran la inyección, el portal sigue funcionando: la navegación, los
filtros y las descargas no dependen del script, y las animaciones de entrada son CSS puro.
"""
from __future__ import annotations

import hashlib
import html
import json
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import nav

RUTA_JS = Path(__file__).resolve().parent / "static" / "interaccion.js"


@lru_cache(maxsize=2)
def _fuente(firma: float) -> str:
    return RUTA_JS.read_text(encoding="utf-8")


def fuente_js() -> str:
    return _fuente(RUTA_JS.stat().st_mtime)


def version_js() -> str:
    return hashlib.sha1(fuente_js().encode("utf-8")).hexdigest()[:10]


def cargador_html() -> str:
    """Documento del iframe invisible: copia el motor al documento padre una sola vez por versión."""
    texto = json.dumps(fuente_js()).replace("</", "<\\/")
    return f"""<!doctype html><html><body><script>
(function () {{
  try {{
    var P = window.parent, D = P.document, V = "{version_js()}";
    var previo = D.getElementById('fm-motor');
    if (previo && previo.getAttribute('data-v') === V) {{ if (P.__fmMotor && P.__fmMotor.escanear) {{ P.__fmMotor.escanear(); }} return; }}
    if (previo) {{ try {{ if (P.__fmMotor && P.__fmMotor.destruir) {{ P.__fmMotor.destruir(); }} }} catch (e) {{}} previo.remove(); }}
    var s = D.createElement('script');
    s.id = 'fm-motor'; s.setAttribute('data-v', V); s.text = {texto};
    D.head.appendChild(s);
  }} catch (e) {{ /* sin acceso al documento padre: el portal funciona solo con CSS */ }}
}})();
</script></body></html>"""


def anuncio(vista: str, seccion: str | None, art: str | None) -> str:
    """Texto que se anuncia a lectores de pantalla tras navegar."""
    if vista == "s2":
        return "Sección 02: base de datos y análisis financiero"
    if vista == "s1":
        if seccion:
            i = nav.CLAVES_SECCION.index(seccion) + 1
            base = f"Sección {i} de {len(nav.CLAVES_SECCION)}: {nav.NOMBRE_SECCION[seccion]}"
            return f"{base}, póster {art[1:]}" if art else base
        return "Menú circular de las siete secciones de la investigación"
    return "Portada del portal científico"


def marcador(vista: str, seccion: str | None, art: str | None, activa: str | None, reducir: bool) -> str:
    run = st.session_state.get("_fm_run", 0) + 1
    st.session_state["_fm_run"] = run
    foco = "1" if st.session_state.pop("_fm_foco", False) else "0"
    return (f'<div id="fm-meta" hidden data-run="{run}" data-vista="{html.escape(vista)}" data-seccion="{html.escape(seccion or "")}" '
            f'data-art="{html.escape(art or "")}" data-activa="{html.escape(activa or "")}" data-reducir="{"1" if reducir else "0"}" '
            f'data-foco="{foco}" data-anuncio="{html.escape(anuncio(vista, seccion, art), quote=True)}"></div>')


def montar(vista: str, seccion: str | None, art: str | None, reducir: bool) -> None:
    """Enlace de salto, marcador de estado y motor de interacción. Se llama una vez por ejecución, antes de la barra superior."""
    st.markdown('<a class="fm-saltar" href="#fm-contenido">Saltar al contenido</a>', unsafe_allow_html=True)
    activa = st.session_state.get("nav_ultima", "introduccion") if (vista == "s1" and not seccion) else (seccion or "")
    with st.container(key="fm_motor"):
        st.markdown(marcador(vista, seccion, art, activa, reducir), unsafe_allow_html=True)
        components.html(cargador_html(), height=0)
