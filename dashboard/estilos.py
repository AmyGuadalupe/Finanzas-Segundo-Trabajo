"""Identidad visual del portal: tokens, iconografía SVG, capas del menú circular y carga de las hojas de estilo.

Las hojas de estilo están en ``static/css/*.css`` (se concatenan por orden alfabético) y son CSS puro:
si el motor de interacción (``static/interaccion.js``) no llegara a cargarse, el portal conserva sus animaciones
de entrada y todos los botones de navegación siguen siendo botones reales de Streamlit.
"""
from __future__ import annotations

import html
import math
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import streamlit as st

AQUI = Path(__file__).resolve().parent
CARPETA_CSS = AQUI / "static" / "css"

TINTA = "#1d2a44"
TINTA2 = "#4a5368"
ACENTO = "#13917f"
PAPEL = "#f8f7f4"
LINEA = "#e1ded6"

# Colores de cada categoría del panel (idénticos a los de los gráficos: graficos.color_tipo con la paleta clara).
COLOR_TIPO = {"Acciones": "#2a78d6", "Deuda": "#eb6834", "Flexibles": "#1baf7a", "Fondo de fondos": "#eda100", "Mixtos": "#e87ba4"}

# ------------------------------------------------------------------ iconos (viewBox 48)
_N, _T, _A = TINTA, ACENTO, "#5aa6c4"


def _svg(contenido: str) -> str:
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48' fill='none' stroke-linecap='round' stroke-linejoin='round'>{contenido}</svg>"


ICONOS = {
    "introduccion": _svg(f"<path d='M24 12c-4-3-10-3.5-16-2v26c6-1.5 12-1 16 2 4-3 10-3.5 16-2V10c-6-1.5-12-1-16 2z' fill='{_N}' stroke='{_N}' stroke-width='2'/>"
                         f"<path d='M24 12v26' stroke='#fff' stroke-width='1.6'/><path d='M27 17c3-1 6-1.2 9-.6M27 22c3-1 6-1.2 9-.6M27 27c3-1 6-1.2 9-.6' stroke='#fff' stroke-width='1.4'/>"
                         f"<path d='M8 38c6-1.5 12-1 16 2 4-3 10-3.5 16-2' stroke='{_A}' stroke-width='3' opacity='.55'/>"),
    "marco": _svg(f"<circle cx='24' cy='7' r='3.4' fill='{_A}'/><circle cx='13' cy='16' r='2.8' fill='{_N}'/><circle cx='35' cy='16' r='2.8' fill='{_N}'/>"
                  f"<path d='M24 10.4v8M15.5 17.5l6 3M32.5 17.5l-6 3' stroke='{_N}' stroke-width='1.8'/>"
                  f"<path d='M7 24l17 4 17-4v16L24 44 7 40z' fill='{_N}' stroke='{_N}' stroke-width='1.6'/><path d='M24 28v16' stroke='#fff' stroke-width='1.4'/>"
                  f"<path d='M11 30l9 2M11 34l9 2M28 32l9-2M28 36l9-2' stroke='#fff' stroke-width='1.2'/>"),
    "antecedentes": _svg(f"<rect x='9' y='8' width='26' height='32' rx='3' fill='#fff' stroke='{_N}' stroke-width='2.2'/><rect x='14' y='4' width='26' height='32' rx='3' fill='#fff' stroke='{_N}' stroke-width='2.2'/>"
                         f"<path d='M19 14h10M19 20h16M19 26h16' stroke='{_N}' stroke-width='2'/><path d='M32 4v13l3.5-2.6L39 17V4z' fill='{_A}' stroke='{_N}' stroke-width='1.4'/>"),
    "metodos": _svg(f"<rect x='6' y='6' width='24' height='32' rx='3' fill='#fff' stroke='{_N}' stroke-width='2.2'/><path d='M11 14h14M11 20h9M11 26h7' stroke='{_N}' stroke-width='2'/>"
                    f"<path d='M10 44h14l-4-8V30h-6v6z' fill='{_A}' stroke='{_N}' stroke-width='1.8'/><circle cx='33' cy='30' r='8' fill='#fff' stroke='{_N}' stroke-width='2.4'/>"
                    f"<path d='M39 36l6 6' stroke='{_N}' stroke-width='3'/><path d='M29.5 32l2.5-3 2 2 2.5-3.5' stroke='{_T}' stroke-width='1.8'/>"),
    "resultados": _svg(f"<path d='M6 42h36' stroke='{_N}' stroke-width='2.4'/><rect x='9' y='28' width='7' height='14' fill='{_N}'/><rect x='19' y='22' width='7' height='20' fill='{_N}'/>"
                       f"<rect x='29' y='15' width='7' height='27' fill='{_N}'/><path d='M8 22l11-8 9 4 13-12' stroke='{_A}' stroke-width='2.4'/><circle cx='41' cy='6' r='2.6' fill='{_T}'/>"),
    "discusion": _svg(f"<path d='M24 6v34M16 40h16' stroke='{_N}' stroke-width='2.8'/><path d='M8 14h32' stroke='{_N}' stroke-width='2.6'/><circle cx='24' cy='7' r='2.6' fill='{_A}'/>"
                      f"<path d='M8 14l-5 12h10zM40 14l-5 12h10z' fill='#fff' stroke='{_N}' stroke-width='2'/><path d='M3 26c0 4 10 4 10 0M35 26c0 4 10 4 10 0' fill='{_N}' stroke='{_N}' stroke-width='2'/>"),
    "conclusiones": _svg(f"<path d='M12 5h17l9 9v26a3 3 0 0 1-3 3H12a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3z' fill='#fff' stroke='{_N}' stroke-width='2.4'/>"
                         f"<path d='M29 5v9h9' stroke='{_N}' stroke-width='2.2'/><path d='M15 21h14M15 27h9M15 33h7' stroke='{_N}' stroke-width='2'/>"
                         f"<circle cx='34' cy='36' r='8.5' fill='{_N}'/><path d='M30 36l3 3 6-6.5' stroke='#fff' stroke-width='2.4'/>"),
}


def _uri(svg: str) -> str:
    return "url(\"data:image/svg+xml;utf8," + quote(svg, safe="/:=' <>,;()#-.") .replace("#", "%23").replace("<", "%3C").replace(">", "%3E") + "\")"


# ------------------------------------------------------------------ menú circular: geometría
RADIO_TARJETAS = 37.5
PROFUNDIDAD = (0.7, 1.0, 0.85, 1.15, 0.9, 1.05, 0.8)   # cuánto se desplaza cada tarjeta con el paralaje


def posiciones_radial(claves: list[str], radio: float = RADIO_TARJETAS, inicio: float = 0.0) -> dict[str, tuple[float, float]]:
    """Centro (x %, y %) de cada tarjeta: reparto uniforme sobre una circunferencia, sentido horario desde el este."""
    n = len(claves)
    out = {}
    for i, c in enumerate(claves):
        a = math.radians(inicio + i * 360 / n)
        out[c] = (round(50 + radio * math.cos(a), 3), round(50 + radio * math.sin(a), 3))
    return out


def svg_anillos(claves: list[str], activa: str | None = None) -> str:
    """Anillos concéntricos, marcas, rayos hacia cada tarjeta y núcleo con símbolo financiero (viewBox 100×100)."""
    n = len(claves)
    rayos = []
    for i, c in enumerate(claves):
        a = math.radians(i * 360 / n)
        x1, y1 = 50 + 14.2 * math.cos(a), 50 + 14.2 * math.sin(a)
        x2, y2 = 50 + 31.2 * math.cos(a), 50 + 31.2 * math.sin(a)
        act = " act" if c == activa else ""
        rayos.append(f'<line class="rb" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>'
                     f'<line class="rh rh-{c}{act}" x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    marcas = []
    for k in range(72):
        a = math.radians(k * 5)
        largo = k % 6 == 0
        r1, r2 = (43.4 if largo else 44.3), 45.5
        marcas.append(f'<line x1="{50 + r1 * math.cos(a):.2f}" y1="{50 + r1 * math.sin(a):.2f}" x2="{50 + r2 * math.cos(a):.2f}" y2="{50 + r2 * math.sin(a):.2f}" '
                      f'stroke="#cbc6ba" stroke-width="{.34 if largo else .2}"/>')
    return f"""
<svg class="fm-anillos" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
  <defs>
    <radialGradient id="fmN" cx="50%" cy="38%" r="70%"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#f3f1ec"/></radialGradient>
    <filter id="fmS" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="1.2" stdDeviation="1.6" flood-color="#2a2418" flood-opacity=".16"/></filter>
  </defs>
  <circle class="r k1" cx="50" cy="50" r="48.2" fill="none" stroke="#dcd8cf" stroke-width=".28"/>
  <circle class="r k1" cx="50" cy="50" r="46.6" fill="none" stroke="#d3cfc5" stroke-width=".42"/>
  <g class="fm-marcas">{''.join(marcas)}</g>
  <circle class="r k2" cx="50" cy="50" r="38.5" fill="none" stroke="#ebe8e1" stroke-width="6.4"/>
  <circle class="r k2" cx="50" cy="50" r="38.5" fill="none" stroke="#e1ddd4" stroke-width=".3"/>
  <g class="fm-punteado"><circle cx="50" cy="50" r="34.2" fill="none" stroke="#cfc9bb" stroke-width=".32" stroke-dasharray=".4 1.7" stroke-linecap="round"/></g>
  <circle class="r k3" cx="50" cy="50" r="30.8" fill="none" stroke="#d9d5cb" stroke-width=".36"/>
  {''.join(rayos)}
  <circle class="r k4" cx="50" cy="50" r="23.5" fill="#f1efea" stroke="#ddd9cf" stroke-width=".36"/>
  <circle class="r k5" cx="50" cy="50" r="18.6" fill="#ece9e2"/>
  <g class="fm-orbita"><circle cx="50" cy="3.4" r=".95" fill="{ACENTO}"/><circle cx="96.6" cy="50" r=".55" fill="#b9b3a5"/></g>
  <g class="fm-orbita2"><circle cx="50" cy="19.2" r=".7" fill="#b9b3a5"/><circle cx="50" cy="80.8" r=".7" fill="{ACENTO}" opacity=".7"/></g>
  <g class="fm-orbita3"><circle cx="50" cy="15.8" r=".5" fill="#5aa6c4"/></g>
  <g class="fm-nucleo">
    <circle class="fm-halo" cx="50" cy="50" r="15.2" fill="none" stroke="{ACENTO}" stroke-opacity=".2" stroke-width=".5"/>
    <circle cx="50" cy="50" r="12.6" fill="url(#fmN)" stroke="#dcd8ce" stroke-width=".4" filter="url(#fmS)"/>
    <g class="fm-glifo">
      <rect x="43.2" y="43.2" width="13.6" height="13.6" rx="2.6" fill="#eeece6"/>
      <polyline class="fm-serie" points="46.2,53.2 48.8,50.4 51,51.7 54,47.2" fill="none" stroke="{TINTA}" stroke-width=".95" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="46.2" cy="53.2" r="1" fill="{TINTA}"/><circle cx="48.8" cy="50.4" r="1" fill="{TINTA}"/><circle cx="51" cy="51.7" r="1" fill="{TINTA}"/>
      <circle cx="54" cy="47.2" r="1.35" fill="{ACENTO}"/>
      <circle class="fm-onda" cx="54" cy="47.2" r="1.35"/>
    </g>
  </g>
</svg>"""


def capa_radial(secciones: list[tuple[str, str]], activa: str | None = None) -> str:
    """Capa decorativa del menú circular: barridos de luz, anillos y rótulo del núcleo (todo aria-hidden)."""
    claves = [c for c, _ in secciones]
    textos = "".join(
        f'<span class="s s-{c}"><small>Sección {i + 1} de {len(secciones)}</small><b>{html.escape(n)}</b></span>'
        for i, (c, n) in enumerate(secciones))
    return (f'<div class="fm-radial-capa" aria-hidden="true"><div class="fm-barrido"></div><div class="fm-barrido b"></div>'
            f'{svg_anillos(claves, activa)}<div class="fm-nucleo-txt">{textos}</div></div>')


def css_radial(claves: list[str], activa: str | None) -> str:
    """Posición de cada tarjeta, icono, número, rayo resaltado y rótulo del núcleo; estilo de la tarjeta activa."""
    pos = posiciones_radial(claves)
    reglas = []
    for i, c in enumerate(claves):
        x, y = pos[c]
        sel = f".st-key-radial:has(.st-key-nav_{c} button:is(:hover,:focus-visible))"
        reglas.append(
            f".st-key-nav_{c}{{left:{x}%!important;top:{y}%!important;width:21.8%!important;height:19.4%!important;"
            f"--i:{i};--dx:{round(50 - x, 3)};--dy:{round(50 - y, 3)};--depth:{PROFUNDIDAD[i % len(PROFUNDIDAD)]}}}"
            f".st-key-nav_{c} button::before{{background-image:{_uri(ICONOS[c])}}}"
            f".st-key-nav_{c} button::after{{content:\"{i + 1:02d}\"}}"
            f"{sel} .rh-{c}{{stroke-dashoffset:0;opacity:.95}}"
            f"{sel} .s-{c}{{opacity:1;transform:none}}")
        if c == activa:
            reglas.append(
                f".st-key-nav_{c} button{{background:linear-gradient(180deg,#e9e4db,#e3ddd2)!important;border-color:#a8998a!important;"
                f"box-shadow:0 14px 30px rgba(60,48,30,.18),inset 0 1px 0 rgba(255,255,255,.6)!important}}"
                f".st-key-nav_{c}::before{{content:\"\";position:absolute;inset:0;border-radius:18px;z-index:-1;pointer-events:none;animation:fmAnilloPulso 3.4s ease-out infinite}}")
    reglas.append("@keyframes fmAnilloPulso{0%{box-shadow:0 0 0 0 rgba(19,145,127,.38)}72%,100%{box-shadow:0 0 0 13px rgba(19,145,127,0)}}")
    return "<style>" + "".join(reglas) + "</style>"


def rueda_mini(claves: list[str], activa: str) -> str:
    """Rueda orbital de la cabecera de cada sección: siete puntos y el activo resaltado (decorativa)."""
    n = len(claves)
    pts = []
    for i, c in enumerate(claves):
        a = math.radians(i * 360 / n)
        x, y = 30 + 21 * math.cos(a), 30 + 21 * math.sin(a)
        if c == activa:
            pts.append(f'<circle class="halo" cx="{x:.1f}" cy="{y:.1f}" r="3.6"/><circle class="pt on" cx="{x:.1f}" cy="{y:.1f}" r="3.6"/>')
        else:
            pts.append(f'<circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="2.1"/>')
    return ('<svg class="fm-rueda" viewBox="0 0 60 60" aria-hidden="true" focusable="false"><circle class="anillo" cx="30" cy="30" r="21"/>'
            '<circle class="anillo" cx="30" cy="30" r="11" stroke-dasharray="1 3"/>' + "".join(pts) + '<circle cx="30" cy="30" r="3.2" fill="#1d2a44"/></svg>')


# ------------------------------------------------------------------ portada: fondo financiero y títulos
def fondo_financiero() -> str:
    """Rejilla, barras de volumen y tres series que se dibujan: decorativo, sin datos reales ni cifras."""
    barras = "".join(
        f'<rect class="vol" x="{14 + i * 40}" y="{600 - h:.1f}" width="20" height="{h:.1f}" rx="3" style="animation-delay:{0.2 + i * 0.035:.2f}s"/>'
        for i in range(30) for h in [34 + 78 * abs(math.sin(i * 0.63) + 0.45 * math.sin(i * 1.71 + 1)) / 1.45])
    rejilla = "".join(f'<line class="rej" x1="0" y1="{y}" x2="1200" y2="{y}"/>' for y in (100, 200, 300, 400, 500)) + \
        "".join(f'<line class="rej" x1="{x}" y1="0" x2="{x}" y2="600"/>' for x in range(150, 1200, 150))
    a = "M0,430 C90,400 150,455 240,420 S390,330 480,365 S640,455 740,385 S900,300 990,330 S1120,250 1200,215"
    return f"""<svg class="fm-fondo" viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
  <defs><linearGradient id="fmArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#13917f" stop-opacity=".16"/><stop offset="1" stop-color="#13917f" stop-opacity="0"/></linearGradient></defs>
  {rejilla}{barras}
  <path class="area" d="{a} L1200,600 L0,600 Z"/>
  <path class="lin c" d="M0,350 C100,330 200,380 310,345 S480,280 590,310 S760,360 880,300 S1060,240 1200,270"/>
  <path class="lin b" d="M0,500 C110,470 190,520 300,480 S470,420 560,455 S720,520 820,470 S1000,400 1090,420 S1160,380 1200,350"/>
  <path class="lin a" d="{a}"/>
  <circle class="punto" cx="990" cy="330" r="5"/><circle class="onda" cx="990" cy="330" r="5"/>
</svg>"""


def titulo_palabras(texto: str) -> str:
    """Título dividido en palabras para la entrada escalonada (el texto completo se conserva para lectores de pantalla)."""
    palabras = html.escape(texto).split()
    return "".join(f'<span class="w" style="--i:{i}">{p}</span> ' for i, p in enumerate(palabras)).strip()


def _prev_svg(tipo: str) -> str:
    n, a, g = TINTA, "#13917f", "#cfc9bb"
    if tipo == "poster":
        cuerpo = (f"<rect x='6' y='4' width='88' height='112' rx='6' fill='#fff' stroke='{n}' stroke-width='2'/><rect x='14' y='12' width='72' height='16' rx='3' fill='{n}'/>"
                  f"<rect x='14' y='36' width='34' height='30' rx='3' fill='{a}' opacity='.8'/><rect x='52' y='36' width='34' height='30' rx='3' fill='{g}'/>"
                  f"<path d='M14 76h72M14 84h58M14 92h66M14 100h40' stroke='{n}' stroke-width='2' opacity='.55'/>")
        return f"<svg viewBox='0 0 100 120' fill='none' stroke-linecap='round' aria-hidden='true'>{cuerpo}</svg>"
    if tipo == "presentacion":
        cuerpo = (f"<rect x='4' y='6' width='112' height='66' rx='6' fill='#fff' stroke='{n}' stroke-width='2'/><rect x='12' y='14' width='56' height='8' rx='2' fill='{n}'/>"
                  f"<path d='M12 32h46M12 40h38M12 48h42' stroke='{n}' stroke-width='2' opacity='.55'/><path d='M70 62l12-14 10 8 16-20' stroke='{a}' stroke-width='3' stroke-linejoin='round'/>"
                  f"<path d='M60 72v10M48 82h24' stroke='{n}' stroke-width='3'/>")
        return f"<svg viewBox='0 0 120 90' fill='none' stroke-linecap='round' aria-hidden='true'>{cuerpo}</svg>"
    cuerpo = (f"<rect x='10' y='4' width='80' height='112' rx='6' fill='#fff' stroke='{n}' stroke-width='2'/><rect x='18' y='12' width='64' height='10' rx='2' fill='{n}'/>"
              f"<path d='M18 30h30M18 36h30M18 42h26M52 30h30M52 36h30M52 42h24' stroke='{n}' stroke-width='2' opacity='.5'/><rect x='18' y='52' width='64' height='26' rx='3' fill='{a}' opacity='.75'/>"
              f"<path d='M18 86h30M18 92h30M18 98h22M52 86h30M52 92h28M52 98h24' stroke='{n}' stroke-width='2' opacity='.5'/>")
    return f"<svg viewBox='0 0 100 120' fill='none' stroke-linecap='round' aria-hidden='true'>{cuerpo}</svg>"


def vista_previa_pendiente(tipo: str) -> str:
    """Ilustración neutra de «vista previa pendiente» para un producto sin archivo (nunca simula un documento real)."""
    return f'<div class="fm-prev">{_prev_svg(tipo)}<span class="et">Vista previa pendiente</span></div>'


# ------------------------------------------------------------------ hojas de estilo
@lru_cache(maxsize=4)
def _hojas(firma: float) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(CARPETA_CSS.glob("*.css")))


def hojas_css() -> str:
    """CSS completo del portal (se relee solo si cambia algún archivo de static/css)."""
    firma = max((p.stat().st_mtime for p in CARPETA_CSS.glob("*.css")), default=0.0)
    return _hojas(firma)


def css_portada() -> str:
    """Iconos de los dos accesos grandes de la portada (derivados de los iconos del menú)."""
    return ("<style>"
            f".st-key-acceso1 button::before{{background-image:{_uri(ICONOS['introduccion'])}}}"
            f".st-key-acceso2 button::before{{background-image:{_uri(ICONOS['resultados'])}}}"
            "</style>")


OCULTAR_BARRA_LATERAL = """
<style>[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"],[data-testid="stExpandSidebarButton"]{display:none!important}</style>
"""

REDUCIR_MOVIMIENTO = """
<style>*,*::before,*::after{animation-duration:.001ms!important;animation-delay:0s!important;animation-iteration-count:1!important;
transition-duration:.001ms!important;transition-delay:0s!important;scroll-behavior:auto!important}</style>
"""


def inyectar(solo_portal: bool = True, reducir: bool = False) -> None:
    """Carga las hojas de estilo; en la vista de datos conserva la barra lateral de filtros."""
    st.markdown(f"<style>{hojas_css()}</style>", unsafe_allow_html=True)
    extra = css_portada()
    if solo_portal:
        extra += OCULTAR_BARRA_LATERAL
    if reducir:
        extra += REDUCIR_MOVIMIENTO
    st.markdown(extra, unsafe_allow_html=True)


def chip(texto: str, clase: str = "") -> str:
    return f"<span class='fm-chip {clase}'>{texto}</span>"


def icono_html(clave: str) -> str:
    return ICONOS[clave]
