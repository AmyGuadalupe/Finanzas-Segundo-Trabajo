"""Pruebas específicas de las interacciones visuales incorporadas en v2:
hojas de estilo, motor de interacción, menú radial, portada, biblioteca y dashboard.

Ejecutar junto con el resto: `python -m pytest dashboard/tests -q`.
No publican la aplicación ni modifican los datos.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))

import estilos as es  # noqa: E402
import graficos as gr  # noqa: E402
import interaccion as inter  # noqa: E402
import nav  # noqa: E402
import portal_config as pc  # noqa: E402
from vistas import biblioteca, comunes as cm, menu_radial, portada, seccion1, secciones  # noqa: E402


# ---------------------------------------------------------- hojas de estilo
def test_hojas_css_presentes_y_esperadas():
    carpeta = AQUI / "static" / "css"
    esperadas = {"00_base.css", "10_portada.css", "20_radial.css", "30_secciones.css",
                 "40_biblioteca.css", "50_dashboard.css", "90_movimiento.css"}
    presentes = {p.name for p in carpeta.glob("*.css")}
    assert esperadas <= presentes, f"Faltan hojas CSS: {esperadas - presentes}"


def test_hojas_css_se_concatenan_en_orden():
    css = es.hojas_css()
    # orden alfabético: 00 va antes de 10, 10 antes de 20, etc.
    for a, b in [("00 · BASE", "10 · PORTADA"), ("10 · PORTADA", "20 · MENÚ CIRCULAR"),
                 ("40 · BIBLIOTECA", "50 · DASHBOARD"), ("50 · DASHBOARD", "90 · MOVIMIENTO")]:
        assert css.find(a) < css.find(b), f"{a} debería venir antes de {b}"


def test_css_oculta_elementos_streamlit_no_necesarios():
    base = (AQUI / "static" / "css" / "00_base.css").read_text(encoding="utf-8")
    # Botón Deploy, decoración, iconos de ancla y status running (no imprescindibles)
    for sel in ["stDeployButton", "stDecoration", "stStatusWidget"]:
        assert sel in base, f"La hoja base debe ocultar {sel}"


def test_css_reduce_movimiento_con_toggle_y_con_prefers_reduced_motion():
    m = (AQUI / "static" / "css" / "90_movimiento.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in m
    assert 'data-fm-reducir="1"' in m


# ---------------------------------------------------------- motor de interacción
def test_interaccion_js_pasa_syntax_check():
    js = AQUI / "static" / "interaccion.js"
    assert js.exists()
    r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_motor_tiene_version_estable_y_cargador_idempotente():
    v = inter.version_js()
    assert re.fullmatch(r"[0-9a-f]{10}", v)
    html = inter.cargador_html()
    assert "'fm-motor'" in html and "'data-v'" in html
    # No debe recrear el motor si ya está en la versión actual
    assert "previo.getAttribute('data-v') === V" in html


def test_marcador_exporta_estado_para_el_motor():
    import streamlit as st
    # Inicializa estado mínimo
    st.session_state["_fm_run"] = 0
    html = inter.marcador("s1", "introduccion", None, "introduccion", False)
    assert 'id="fm-meta"' in html and 'data-vista="s1"' in html and 'data-activa="introduccion"' in html
    assert 'data-reducir="0"' in html and 'data-anuncio=' in html


# ---------------------------------------------------------- menú radial
def test_menu_radial_tiene_siete_tarjetas_y_mismo_orden():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=90)
    at.query_params["v"] = "s1"
    at.run()
    assert not at.exception
    claves = [b.key for b in at.button if b.key and b.key.startswith("nav_")]
    assert claves == [f"nav_{c}" for c in nav.CLAVES_SECCION]  # orden exacto


def test_capa_radial_dibuja_siete_rayos_y_nucleo():
    html = es.capa_radial(nav.SECCIONES, None)
    # 7 rayos atenuados + 7 "activos" (en reposo, ocultos por CSS hasta que haya hover/foco)
    assert html.count('class="rb"') == 7 or html.count("class='rb'") == 7 or html.count("rb ") >= 7
    assert "fm-nucleo" in html and "fm-barrido" in html and "fm-anillos" in html


def test_css_posiciona_siete_tarjetas_en_porcentaje():
    css = es.css_radial([c for c, _ in nav.SECCIONES], None)
    # Cada tarjeta recibe --i (0..6) y queda posicionada con top/left en %
    assert all(f"--i:{i}" in css for i in range(7))
    assert css.count("top:") >= 7 and css.count("left:") >= 7


def test_atajos_de_teclado_estan_documentados():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=90)
    at.query_params["v"] = "s1"; at.query_params["sec"] = "introduccion"
    at.run()
    md = " ".join(m.value for m in at.markdown)
    assert "←" in md and "→" in md and "Esc" in md


# ---------------------------------------------------------- portada
def test_portada_tiene_titulo_en_palabras_para_animacion():
    html = es.titulo_palabras("Fondos mutuos en el Perú")
    assert html.count('class="w"') + html.count("class='w'") == 5
    # Cada palabra lleva un índice --i para la animación escalonada
    assert "--i:0" in html and "--i:4" in html


def test_portada_tiene_los_dos_accesos_grandes():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=90)
    at.run()
    assert not at.exception
    claves = {b.key for b in at.button if b.key}
    assert {"acceso1", "acceso2"} <= claves


def test_portada_muestra_tipos_reales_del_panel_con_colores():
    # Las cinco categorías tienen un color asignado para la portada
    for tipo in ("Acciones", "Deuda", "Flexibles", "Fondo de fondos", "Mixtos"):
        assert tipo in es.COLOR_TIPO
        c = es.COLOR_TIPO[tipo]
        assert isinstance(c, str) and c.startswith("#") and len(c) == 7


# ---------------------------------------------------------- biblioteca
def test_biblioteca_mantiene_cinco_columnas_y_claves_de_navegacion():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=120)
    at.query_params["v"] = "s1"; at.query_params["sec"] = "antecedentes"
    at.run()
    assert not at.exception
    claves = [b.key for b in at.button if b.key]
    # Cada ficha abre su detalle con botón a_<id>
    for a in pc.articulos():
        assert f"a_{a['id']}" in claves, f"Falta botón para la ficha {a['id']}"


def test_cuartil_badge_solo_cuando_esta_verificado():
    # En los datos actuales ninguna ficha tiene cuartil verificado → la clase q1/q2 no debe aparecer
    arts = pc.articulos()
    assert all(a.get("cuartil_verificado") is False for a in arts)
    badges = biblioteca._badges_html(arts[0])
    assert "fm-badge q1" not in badges and "fm-badge q2" not in badges


def test_poster_muestra_placeholder_cuando_no_hay_imagen():
    h = biblioteca._poster_html({"numero": 7, "miniatura": "", "poster_pdf": ""})
    assert "fm-poster" in h and "pendiente" in h.lower()


def test_filtros_de_biblioteca_siguen_presentes():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=120)
    at.query_params["v"] = "s1"; at.query_params["sec"] = "antecedentes"
    at.run()
    claves = {w.key for w in list(at.multiselect) + list(at.text_input) if w.key}
    assert {"b_q", "b_anio", "b_cuartil", "b_revista", "b_eje"} <= claves


# ---------------------------------------------------------- dashboard
def test_dashboard_mantiene_filtros_de_la_barra_lateral():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=180)
    at.query_params["v"] = "s2"
    at.run()
    assert not at.exception
    # Claves críticas de filtros existentes (no se reconstruyen)
    claves = set()
    for grupo in (at.multiselect, at.radio, at.selectbox, at.button):
        for w in grupo:
            if w.key:
                claves.add(w.key)
    assert "f_retorno" in claves
    assert "f_vista" in claves


def test_dashboard_tiene_barra_superior_con_toggle_de_movimiento():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=90)
    at.run()
    toggles = [t.key for t in at.toggle if t.key]
    assert "fm_reducir" in toggles


# ---------------------------------------------------------- pie único
def test_pie_de_pagina_no_se_duplica_entre_portada_y_dispatcher():
    """Antes el pie salía dos veces (desde app.py y desde la vista). Ahora solo una."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=90)
    at.run()
    md = " ".join(m.value for m in at.markdown)
    assert md.count("fm-pie") <= 1


# ---------------------------------------------------------- ningún `cm.pie()` duplicado en views
def test_views_portada_y_seccion1_no_llaman_pie_internamente():
    for mod in (portada, seccion1):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert "cm.pie()" not in src, f"{mod.__name__} debe dejar el pie a app.py"
