"""Antecedentes: biblioteca de 30 pósteres bibliográficos y ficha académica individual."""
from __future__ import annotations

import html
import unicodedata

import streamlit as st

import nav
import portal_config as pc
from vistas import comunes as cm


def _norm(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")


def _opciones(arts: list[dict], campo: str) -> list:
    return sorted({a[campo] for a in arts if a.get(campo)})


def _filtrar(arts: list[dict]) -> list[dict]:
    q = _norm(st.session_state.get("b_q", ""))
    anios, cuart = st.session_state.get("b_anio", []), st.session_state.get("b_cuartil", [])
    revs, ejes = st.session_state.get("b_revista", []), st.session_state.get("b_eje", [])
    out = []
    for a in arts:
        if q and q not in _norm(" ".join([a.get("titulo_original", ""), a.get("titulo_es", ""), " ".join(a.get("autores", []))])):
            continue
        if anios and a.get("anio") not in anios:
            continue
        if cuart and a.get("cuartil") not in cuart:
            continue
        if revs and a.get("revista") not in revs:
            continue
        if ejes and a.get("eje_tematico") not in ejes:
            continue
        out.append(a)
    return out


def _restablecer() -> None:
    for k in ("b_q", "b_anio", "b_cuartil", "b_revista", "b_eje"):
        st.session_state.pop(k, None)


def _poster_html(a: dict) -> str:
    """HTML para el área de póster (imagen si existe, placeholder suave si no)."""
    m = a.get("miniatura", "") or a.get("poster_pdf", "")
    local = pc.ruta_asset(m)
    if local and str(local).lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return f'<div class="fm-poster"><img alt="Vista previa del póster {a["numero"]:02d}" src="{cm.imagen_data_uri(local)}"></div>'
    if pc.es_url(m) and m.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        return f'<div class="fm-poster"><img alt="Vista previa del póster {a["numero"]:02d}" src="{html.escape(m)}"></div>'
    return f'<div class="fm-poster"><span style="position:absolute;inset:auto 0 12px 0;text-align:center;font-size:.72rem;color:#7a7360;letter-spacing:.06em;text-transform:uppercase">Vista previa pendiente</span></div>'


def _badges_html(a: dict) -> str:
    chips: list[str] = []
    cuartil = a.get("cuartil", "")
    verif = bool(a.get("cuartil_verificado"))
    if cuartil and verif:
        clase = "q1" if cuartil == "Q1" else "q2" if cuartil == "Q2" else ""
        chips.append(f'<span class="fm-badge {clase}">{html.escape(cuartil)}</span>')
    if a.get("revista"):
        chips.append(f'<span class="fm-badge rev">{html.escape(a["revista"][:22])}</span>')
    docs = sum(1 for k in ("poster_pdf", "paper_pdf", "resumen_pdf", "presentacion_pdf") if pc.enlace_doc(a, k)[1])
    if docs:
        chips.append(f'<span class="fm-badge doc">{docs}/4 docs</span>')
    return f'<div class="fm-tags">{"".join(chips)}</div>' if chips else ""


def _tarjeta(a: dict, i: int) -> None:
    """Una tarjeta de artículo. El botón «Abrir ficha» cubre toda la tarjeta (CSS)."""
    titulo = a.get("titulo_es") or a.get("titulo_original") or f"Póster {a['numero']:02d}"
    autores = ", ".join(a.get("autores", [])[:2]) or "Autores pendientes"
    anio = a.get("anio") or ""
    with st.container(key=f"art_{a['id']}"):
        st.markdown(
            f"{_poster_html(a)}"
            f'<span class="num">{a["numero"]:02d}</span>'
            f'<h4>{html.escape(titulo[:110])}</h4>'
            f'<small>{html.escape(autores)} · {html.escape(str(anio))}</small>'
            f'{_badges_html(a)}',
            unsafe_allow_html=True,
        )
        st.button(f"Abrir ficha del póster {a['numero']:02d}", key=f"a_{a['id']}", on_click=nav.ir,
                  args=("s1", "antecedentes", a["id"]))


def biblioteca() -> None:
    arts = pc.articulos()
    total = len(arts)
    con_meta = sum(pc.tiene_metadatos(a) for a in arts)
    con_poster = sum(pc.enlace_doc(a, "poster_pdf")[1] != "" for a in arts)
    st.markdown(f"<div class='fm-dato'><div><small>Pósteres bibliográficos</small><span>{total}</span></div>"
                f"<div><small>Fichas con metadatos</small><span>{con_meta} de {total}</span></div>"
                f"<div><small>Pósteres con enlace</small><span>{con_poster} de {total}</span></div></div>", unsafe_allow_html=True)
    if con_meta == 0:
        st.info("Los artículos y sus metadatos definitivos se incorporarán más adelante en config/documentos.json. "
                "Las 30 fichas ya existen, numeradas del 01 al 30, y se completarán sin modificar el código.",
                icon=":material/info:")
    with st.container(key="biblio_filtros", border=True):
        f1, f2 = st.columns([2, 1])
        f1.text_input("Buscar por título o autor", key="b_q", placeholder="Ej.: Sharpe, Markowitz, mutual funds…")
        f2.button("Limpiar filtros", on_click=_restablecer, icon=":material/restart_alt:", width="stretch")
        g = st.columns(4)
        g[0].multiselect("Año", _opciones(arts, "anio"), key="b_anio", placeholder="Todos", disabled=not _opciones(arts, "anio"))
        g[1].multiselect("Cuartil", ["Q1", "Q2"], key="b_cuartil", placeholder="Q1 y Q2",
                         help="Solo se marca un cuartil cuando está verificado en Scimago.")
        g[2].multiselect("Revista", _opciones(arts, "revista"), key="b_revista", placeholder="Todas", disabled=not _opciones(arts, "revista"))
        g[3].multiselect("Eje temático", _opciones(arts, "eje_tematico"), key="b_eje", placeholder="Todos", disabled=not _opciones(arts, "eje_tematico"))
    lista = _filtrar(arts)
    st.markdown(f"<p class='fm-contador'><b>{len(lista)}</b> de {total} fichas</p>", unsafe_allow_html=True)
    if not lista:
        st.warning("Ninguna ficha cumple los filtros elegidos.", icon=":material/search_off:")
        return
    por_fila = 5
    for i in range(0, len(lista), por_fila):
        cols = st.columns(por_fila, gap="small")
        for j, (col, a) in enumerate(zip(cols, lista[i:i + por_fila])):
            with col:
                _tarjeta(a, i + j)


def _par(k: str, v) -> str:
    v = html.escape(str(v)) if v not in (None, "", []) else "<em style='color:#8a8577;font-weight:400'>Pendiente</em>"
    return f"<div><small>{k}</small><span>{v}</span></div>"


def ficha(id_: str) -> None:
    arts = pc.articulos()
    a = pc.articulo(id_)
    if a is None:
        st.warning("La ficha solicitada no existe.")
        st.button("Volver a la biblioteca", on_click=nav.ir, args=("s1", "antecedentes", None))
        return
    idx = arts.index(a)
    ant, sig = (arts[idx - 1] if idx > 0 else None), (arts[idx + 1] if idx < len(arts) - 1 else None)
    with st.container(key=f"ficha_{a['id']}"):
        st.markdown(f"<div class='fm-ficha'><h2>Póster {a['numero']:02d} {cm.chip_estado(a['estado'])}</h2></div>", unsafe_allow_html=True)
        titulo = a.get("titulo_es") or a.get("titulo_original") or "Ficha pendiente de metadatos"
        autores = ", ".join(a.get("autores", [])) or "Autores pendientes"
        rev = " · ".join(x for x in [a.get("revista", ""), str(a.get("anio", "")), a.get("cuartil", "") if a.get("cuartil_verificado") else ""] if x)
        st.markdown(f"<div class='fm-ficha'><div class='fm-meta-ficha'><div><b>{html.escape(titulo)}</b></div></div>"
                    f"<div class='fm-meta-ficha'><span>{html.escape(autores)}</span><span>{html.escape(rev)}</span></div></div>",
                    unsafe_allow_html=True)
        c = st.columns([3, 2])
        with c[0]:
            pares = "".join(_par(k, v) for k, v in [
                ("Objetivo", a.get("objetivo")), ("Método", a.get("metodo")),
                ("Resultados", a.get("resultados")), ("Contribución", a.get("contribucion")),
                ("Referencia APA", a.get("referencia_apa"))])
            st.markdown(f"<div class='fm-bloque'>{pares}</div>", unsafe_allow_html=True)
        with c[1]:
            st.markdown(f"<div class='fm-bloque'>{_par('DOI', a.get('doi', ''))}</div>", unsafe_allow_html=True)
            doi_url = pc.url_doi(a.get("doi", ""))
            if doi_url:
                st.link_button(f"Abrir DOI · {a['doi']}", doi_url, width="stretch")
            st.markdown("<small style='color:#6a7284'>Documentos disponibles para esta ficha:</small>", unsafe_allow_html=True)
            for clave, nombre in [("poster_pdf", "Póster"), ("paper_pdf", "Paper"), ("resumen_pdf", "Resumen"), ("presentacion_pdf", "Presentación")]:
                ruta, url = pc.enlace_doc(a, clave)
                estado = "disponible" if url else "pendiente"
                st.markdown(f"<div style='font-size:.82rem;font-weight:600;margin-bottom:4px'>{nombre}</div>{cm.chip_estado(estado)}", unsafe_allow_html=True)
                from pathlib import Path as _P
                if ruta and _P(str(ruta)).exists():
                    with open(ruta, "rb") as fh:
                        st.download_button(f"Descargar {nombre.lower()}", data=fh.read(), file_name=ruta.name,
                                           mime="application/pdf", key=f"dl_{a['id']}_{clave}", width="stretch")
                elif url:
                    st.link_button(f"Abrir {nombre.lower()}", url, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
        st.divider()
        b = st.columns([1, 1, 1])
        b[0].button("Póster anterior", icon=":material/chevron_left:", key="f_ant", disabled=ant is None,
                    on_click=nav.ir, args=("s1", "antecedentes", ant["id"] if ant else None, -1), width="stretch")
        b[1].button("Volver a la biblioteca", icon=":material/apps:", key="f_volver",
                    on_click=nav.ir, args=("s1", "antecedentes", None), width="stretch")
        b[2].button("Póster siguiente", icon=":material/chevron_right:", key="f_sig", disabled=sig is None,
                    on_click=nav.ir, args=("s1", "antecedentes", sig["id"] if sig else None, 1), width="stretch")
