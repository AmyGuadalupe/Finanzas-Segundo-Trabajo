"""Página principal institucional: portada animada, accesos a las dos secciones y cifras reales de la investigación."""
from __future__ import annotations

import html

import streamlit as st

import cargas
import estilos as es
import nav
import portal_config as pc
from vistas import comunes as cm

ORDEN_TIPOS = ["Acciones", "Deuda", "Flexibles", "Fondo de fondos", "Mixtos"]


def _escudo(p: dict) -> str:
    ruta = pc.ruta_asset(p.get("escudo_institucional", ""))
    if ruta:
        return f"<div class='fm-escudo'><img alt='Escudo institucional' src='{cm.imagen_data_uri(ruta)}'></div>"
    return "<div class='fm-escudo'>Escudo oficial<br>(pendiente de entrega)</div>"


def _foto(p: dict) -> str:
    ruta = pc.ruta_asset(p.get("foto_autora", ""))
    if ruta:
        return f"<div class='fm-foto'><img alt='Fotografía de la autora' src='{cm.imagen_data_uri(ruta)}'></div>"
    return "<div class='fm-foto'>Fotografía de la autora<br>(se incorporará después)</div>"


def _tipos(panel) -> str:
    """Categorías reales del panel con su número de fondos-series (mismos colores que los gráficos)."""
    cuentas = panel.groupby("tipo").id_fondo_serie.nunique().to_dict()
    chips = []
    for i, t in enumerate([t for t in ORDEN_TIPOS if t in cuentas]):
        chips.append(f"<span class='tipo' style='--c:{es.COLOR_TIPO[t]};--i:{i}'><i></i>{html.escape(t)} <small>{cuentas[t]} series</small></span>")
    return f"<div class='fm-tipos' aria-label='Categorías de fondos en el panel'>{''.join(chips)}</div>" if chips else ""


def render() -> None:
    p = pc.portal()
    docs = pc.documentos()["productos"]
    j = docs["journal"]
    j_url = j.get("visualizacion_url") or j.get("descarga_pdf_url")
    journal_html = (f"<a href='{html.escape(pc.url_visor(j_url))}' target='_blank' rel='noopener'>Journal científico</a>"
                    if j.get("estado") == "disponible" and pc.es_url(j_url)
                    else "<a class='off' href='#' tabindex='-1'>Journal científico · en elaboración</a>")
    datos_meta = [("Autora", p["autora"]), ("Docente", p["docente"]), ("Curso", p["curso"]),
                  ("Unidad", p["unidad"]), ("Periodo académico", p["periodo"]), ("Tema", p["tema"].replace("Tema ", "N.º "))]
    meta = "".join(f"<div><small>{html.escape(k)}</small><span>{html.escape(v)}</span></div>" for k, v in datos_meta)
    proy = cargas.proyecto()
    tipos = _tipos(proy.panel) if proy is not None else ""
    st.markdown(
        f"""
<div class="fm-portada">
  {es.fondo_financiero()}
  <div class="fm-portada-grid">
    <div>
      <div class="fm-inst">{_escudo(p)}<div><b>{html.escape(p['universidad'])}</b><span>{html.escape(p['facultad'])}</span></div></div>
      <div class="fm-etiqueta">Portal científico interactivo</div>
      <h1 class="fm-titulo" tabindex="-1" data-fm-foco>{es.titulo_palabras(p['titulo'])}</h1>
      <span class="fm-subraya" aria-hidden="true"></span>
      <p class="fm-sub">Investigación de {html.escape(p['curso'])}, {html.escape(p['unidad'])}: rentabilidad, riesgo y desempeño ajustado por riesgo de los fondos mutuos peruanos,
      con base de datos propia construida mediante API y descarga programática.</p>
      <div class="fm-meta">{meta}</div>
      {tipos}
      <div class="fm-enlaces">
        <a href="{html.escape(p['repositorio_url'])}" target="_blank" rel="noopener">&#9741; Repositorio GitHub</a>
        {journal_html}
      </div>
    </div>
    <div class="fm-foto-col">{_foto(p)}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.write("")
    a, b = st.columns(2, gap="large")
    a.button("**01 · Productos académicos y desarrollo científico**  \nMenú circular con introducción, marco teórico, biblioteca de 30 pósteres "
             "bibliográficos, métodos, resultados, discusión y conclusiones, más el journal, el póster y la presentación.",
             key="acceso1", on_click=nav.ir, args=("s1",), width="stretch")
    b.button("**02 · Base de datos y análisis financiero**  \nPanel procesado completo, filtros, línea de tiempo, análisis por tipo de fondo, "
             "gráficos interactivos, resultados econométricos y descargas verificadas.",
             key="acceso2", on_click=nav.ir, args=("s2",), width="stretch")

    if proy is not None:
        pan = proy.panel
        cifras = [(len(pan), "observaciones"), (pan.id_fondo_serie.nunique(), "fondos-series"),
                  (pan.mes.nunique(), "meses comunes"), (pan.tipo.nunique(), "categorías en el panel balanceado")]
        celdas = "".join(
            f"<div class='fm-cifra fm-rev' style='--i:{i}'><span class='n' data-fm-count='{v}' data-fm-sep=' '>{f'{v:,}'.replace(',', ' ')}</span><small>{k}</small></div>"
            for i, (v, k) in enumerate(cifras))
        st.markdown(f"<div class='fm-cifras'>{celdas}</div>", unsafe_allow_html=True)
        st.caption(f"Datos reales de la investigación, de {pan.mes.min()} a {pan.mes.max()} (frecuencia mensual). Fuentes: boletines de la AAF y API de BCRPData.")
