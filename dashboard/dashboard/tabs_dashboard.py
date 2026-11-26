"""Pestañas nuevas de la sección 02: indicadores, tipo de fondo, base completa, descargas y transparencia.

Cada función recibe `c` (contexto con los filtros activos, el proyecto y utilidades de panel_financiero).
Todo es solo lectura sobre los archivos de la investigación.
"""
from __future__ import annotations

import html
import io
import re
import unicodedata

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import datos
import descargas as dl
import econometria as eco
import exportes as ex
import graficos as gr
import metricas as mt
import nav
import portal_config as pc

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FORMATOS = {"Excel (XLSX)": ("xlsx", XLSX), "CSV para Excel (;)": ("csv", "text/csv"), "CSV estándar (,)": ("csv", "text/csv")}
AYUDA_FORMATOS = ("**XLSX**: formato principal (columnas separadas, fechas y números reales, filtros). **CSV para Excel**: UTF-8 con BOM, separador «;», coma decimal y "
                  "línea «sep=;» (en Python: `pd.read_csv(f, sep=';', decimal=',', skiprows=1)`). **CSV estándar**: UTF-8, separador «,» y punto decimal, para Python/R.")


def _pct(v, dec=2) -> str:
    return "n.d." if v is None or pd.isna(v) else f"{100 * v:.{dec}f} %"


def _num(v, dec=3) -> str:
    return "n.d." if v is None or pd.isna(v) else f"{v:.{dec}f}"


def _norm(t: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(ch) != "Mn")


# --------------------------------------------------------------------------- indicadores
def ficha_indicadores() -> None:
    with st.expander("Ficha de los indicadores: unidad, frecuencia, metodología y alcance", icon=":material/rule:"):
        st.dataframe(pd.DataFrame([
            ("Rentabilidad acumulada", "% del periodo elegido", "Mensual", "Producto de (1 + r) − 1 con la serie de retorno elegida", "Mediana entre fondos-series; por moneda"),
            ("Rentabilidad anualizada", "% anual", "Mensual → anual", "exp(12 × media de ln(1 + r)) − 1; exige ≥ 12 meses (como la investigación)", "Mediana entre fondos-series; por moneda"),
            ("Volatilidad anualizada", "% anual", "Mensual → anual", "Desviación muestral de r × √12; exige ≥ 12 meses", "Mediana entre fondos-series; por moneda"),
            ("Sharpe anualizado", "Adimensional", "Mensual → anual", "Media del exceso / desviación del exceso × √12; exceso = r − tasa interbancaria mensual de la misma moneda (BCRPData)", "Mediana; la tasa es aproximación, no un activo libre de riesgo invertible"),
            ("Máxima caída", "% desde el máximo previo", "Mensual", "Mayor descenso del índice acumulado (cálculo propio del dashboard)", "Mediana entre fondos-series"),
            ("Interpoladas / winsorizadas", "% de las filas", "Mensual", "imputado = 1 / atipico = 1 en el panel", "Filas del filtro activo"),
        ], columns=["Indicador", "Unidad", "Frecuencia", "Metodología", "Alcance"]), hide_index=True, width="stretch")
        st.caption("Rentabilidades y tasas del panel están en decimal (0,01 = 1 %). Las monedas PEN y USD nunca se promedian entre sí. "
                   "Las métricas con ≥ 12 meses reproducen las tablas oficiales cuando no hay filtros.")


def tarjetas_kpi(KPI: pd.DataFrame) -> None:
    for _, k in KPI.iterrows():
        tarjetas = [
            ("Rentabilidad acumulada (mediana entre series)", _pct(k.rent_acumulada_mediana), "calculado · compuesto"),
            ("Rentabilidad anualizada (mediana)", _pct(k.rent_anualizada_mediana), "calculado"),
            ("Volatilidad anualizada (mediana)", _pct(k.vol_anualizada_mediana), "calculado"),
            ("Sharpe anualizado (mediana)", _num(k.sharpe_mediana, 2), "calculado · vs. interbancaria"),
            ("Máxima caída (mediana)", _pct(k.max_caida_mediana), "calculado · dashboard"),
            ("Interpoladas / winsorizadas", f"{_pct(k.pct_interpoladas, 1)} / {_pct(k.pct_winsorizadas, 1)}", "calidad de datos"),
        ]
        cards = "".join(f"<div class='fm-card'><div class='l'>{a}</div><div class='v'>{b}</div><span class='t'>{t}</span></div>" for a, b, t in tarjetas)
        st.markdown(f"<div class='fm-moneda'>{gr.NOMBRE_MONEDA[k.moneda]}<small>{int(k.series)} series · {int(k.meses)} meses · {int(k.observaciones)} observaciones</small></div>"
                    f"<div class='fm-kpis'>{cards}</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- descargas (bytes en caché)
@st.cache_data(show_spinner=False, max_entries=24)
def _bytes_tabla(clave: str, formato: str, _hojas: dict, _notas: dict | None) -> bytes:
    if formato == "Excel (XLSX)":
        return ex.xlsx_bytes(_hojas, _notas)
    primera = next(iter(_hojas.values()))
    return ex.csv_excel_bytes(primera) if formato.startswith("CSV para Excel") else ex.csv_estandar_bytes(primera)


def notas_diccionario(dic: pd.DataFrame | None) -> dict[str, str]:
    """Comentario de cada encabezado del XLSX: definición, unidad, frecuencia y fuente."""
    if dic is None:
        return {}
    out = {}
    for _, f in dic.iterrows():
        out[f["Variable"]] = f"{f.get('Definición', '')}\nUnidad: {f.get('Unidad', '')} · Frecuencia: {f.get('Frecuencia', '')} · Fuente: {f.get('Fuente (URL arriba)', '')}"
    return out


def boton_descarga(etiqueta: str, hojas: dict[str, pd.DataFrame], nombre: str, clave: str, firma: str, notas=None, csv_estandar: bytes | None = None,
                   key_extra: str = "") -> None:
    """Selector de formato + botón de descarga. `csv_estandar`: bytes literales (p. ej. el archivo original)."""
    fmt = st.radio("Formato", list(FORMATOS), key=f"fmt_{clave}{key_extra}", horizontal=True, label_visibility="collapsed")
    ext, mime = FORMATOS[fmt]
    if fmt == "CSV estándar (,)" and csv_estandar is not None:
        datos_b = csv_estandar
    else:
        datos_b = _bytes_tabla(f"{clave}|{firma}", fmt, hojas, notas)
    sufijo = {"Excel (XLSX)": "", "CSV para Excel (;)": "_excel", "CSV estándar (,)": ""}[fmt]
    st.download_button(etiqueta, datos_b, f"{nombre}{sufijo}.{ext}", mime, key=f"dl_{clave}{key_extra}", icon=":material/download:", width="stretch")


def _hojas_obs(df: pd.DataFrame, meta: pd.DataFrame, dic, columnas: list[str]) -> dict[str, pd.DataFrame]:
    h = {"observaciones": df[columnas]}
    h["filtros"] = meta.astype(str)
    if dic is not None:
        h["diccionario"] = dic
    return h


# --------------------------------------------------------------------------- por tipo de fondo
def pestana_tipo(c) -> None:
    panel, comp = c.panel, c.proy.complementaria
    tipos = [t for t in gr.ORDEN_TIPOS if t in set(panel.tipo)]
    extra = "ETF y Estructurados (fuera del panel)"
    opciones = tipos + ([extra] if comp is not None else [])
    st.markdown("##### Análisis por tipo de fondo")
    sel = st.radio("Categoría", opciones, key="tipo_sel", horizontal=True)
    st.caption("Elige aquí la categoría. Esta pestaña respeta el periodo de la línea de tiempo, la moneda, la administradora y la serie de retorno activos; "
               "el tipo y los fondos-series los define esta selección. Las estadísticas se calculan solo con los registros de la categoría.")
    if sel == extra:
        _complementarios(c, comp)
        return
    ff = mt.Filtros((sel,), c.F.monedas, c.F.administradoras, (), c.F.mes_ini, c.F.mes_fin, c.RET)
    D = mt.aplicar_filtros(panel, ff)
    if D.empty:
        st.warning("Esta categoría no tiene registros con los filtros de moneda, administradora y periodo activos.", icon=":material/search_off:")
        return
    M = mt.metricas_por_serie(D, c.RET)
    sub = f"{c.mes_corto(c.ini)} – {c.mes_corto(c.fin)} · {sel} · {D.id_fondo_serie.nunique()} series · {c.etiqueta_ret}"
    st.markdown(f"**{sel}**: {len(D)} observaciones · {D.id_fondo_serie.nunique()} fondos-series · {D.administradora.nunique()} administradoras · {D.mes.nunique()} meses")
    if D.id_fondo_serie.nunique() < 4:
        st.info("Menos de cuatro fondos-series: las estadísticas son descriptivas y no permiten inferencia.", icon=":material/info:")
    tarjetas_kpi(mt.kpis_por_moneda(D, M))
    if c.vista == "serie":
        pass
    # comparación con las demás categorías (mismos filtros salvo el tipo)
    DA = mt.aplicar_filtros(panel, mt.Filtros((), c.F.monedas, c.F.administradoras, (), c.F.mes_ini, c.F.mes_fin, c.RET))
    MA = mt.metricas_por_serie(DA, c.RET)
    n_mes = D.mes.nunique()
    if n_mes >= mt.MIN_MESES and not MA.dropna(subset=["vol_anualizada"]).empty:
        c.mostrar("tipo_dispersion", f"Riesgo y rentabilidad: {sel} frente a las demás categorías", lambda p: gr.fig_dispersion(MA, sel, p, sub),
                  "Cada punto es un fondo-serie; la categoría elegida se resalta y el resto queda en gris para comparar rentabilidad y riesgo.")
        c.mostrar("tipo_sharpe", "Sharpe por tipo de fondo (todas las categorías)", lambda p: gr.fig_sharpe_categorias(mt.resumen_por_categoria(MA), p, sub),
                  "Mediana e intervalo intercuartílico entre fondos-series de cada categoría y moneda.")
    else:
        st.info(f"El periodo elegido tiene {n_mes} meses: la comparación de riesgo y rentabilidad anualizados exige al menos {mt.MIN_MESES}.", icon=":material/info:")
    CAT = mt.rent_mensual_categoria(D, c.RET)
    c.mostrar("tipo_evolucion", f"Evolución mensual · {sel}", lambda p: gr.fig_rent_mensual(CAT, None, "categoria", c.RET, p, {}, sub),
              "Promedio simple mensual entre los fondos-series de la categoría (igual peso, no por patrimonio), por moneda.")
    IND = mt.indice_acumulado(D, c.RET, "categoria")
    c.mostrar("tipo_acumulada", f"Rentabilidad acumulada (base 100) · {sel}", lambda p: gr.fig_acumulada(IND, "categoria", p, {}, sub),
              "Cartera de igual ponderación rebalanceada mensualmente, desde el inicio del periodo elegido.")
    st.markdown("##### Fondos y series que integran la categoría")
    v = M.copy()
    for col in ["rent_acumulada", "rent_anualizada", "vol_anualizada", "max_caida", "meses_con_perdida"]:
        v[col] = 100 * v[col]
    st.dataframe(v.drop(columns=["id_fondo_serie"]).sort_values(["moneda", "sharpe_anualizado"], ascending=[True, False]), hide_index=True, width="stretch", column_config={
        "etiqueta": st.column_config.TextColumn("Fondo-serie", width="large"), "tipo": "Tipo", "moneda": "Moneda", "administradora": "Administradora",
        "mes_inicio": "Desde", "mes_fin": "Hasta", "n_meses": "Meses",
        "rent_acumulada": st.column_config.NumberColumn("Rent. acumulada (%)", format="%.2f"), "rent_anualizada": st.column_config.NumberColumn("Rent. anualizada (%)", format="%.2f"),
        "vol_anualizada": st.column_config.NumberColumn("Vol. anualizada (%)", format="%.2f"), "sharpe_anualizado": st.column_config.NumberColumn("Sharpe", format="%.3f"),
        "sortino_anualizado": st.column_config.NumberColumn("Sortino", format="%.3f"), "max_caida": st.column_config.NumberColumn("Máx. caída (%)", format="%.2f"),
        "meses_con_perdida": st.column_config.NumberColumn("Meses con pérdida (%)", format="%.1f")})
    st.markdown("##### Observaciones de la categoría")
    cols = ["mes", "etiqueta", "moneda", "administradora", "estado_dato", "valor_cuota", "rent_original", "rent_mes", "exceso", "vol12", "rent_lag1", "var_tc"]
    st.dataframe(D[cols], hide_index=True, width="stretch", height=320,
                 column_config={k: st.column_config.NumberColumn(format="%.5f") for k in ["rent_original", "rent_mes", "exceso", "vol12", "rent_lag1", "var_tc"]})
    st.caption(f"{len(D)} filas del filtro activo; columnas en decimal (0,01 = 1 %).")
    st.markdown("##### Descargar")
    completa = panel[panel.tipo.eq(sel)][datos.COLUMNAS_PANEL]
    meta = dl.hoja_filtros({**ff.describir()}, {"Filas": len(D), "Categoría": sel, "Generado": dl.ahora_peru()})
    a, b = st.columns(2)
    with a:
        st.markdown(f"**Base procesada completa de «{sel}»** · {len(completa)} filas × {len(completa.columns)} columnas, todos los meses y monedas (ignora los filtros)")
        boton_descarga(f"Descargar base completa de {sel}", {"base_procesada": completa, "diccionario": c.DIC} if c.DIC is not None else {"base_procesada": completa},
                       f"base_procesada_{_slug(sel)}", f"tipo_comp_{_slug(sel)}", c.proy.firma, notas_diccionario(c.DIC))
    with b:
        st.markdown(f"**Selección filtrada de «{sel}»** · {len(D)} filas con los filtros activos")
        boton_descarga("Descargar selección filtrada", _hojas_obs(D, meta, c.DIC, datos.COLUMNAS_PANEL + ["estado_dato", "etiqueta"]),
                       f"seleccion_{_slug(sel)}_{c.ini}_{c.fin}", f"tipo_filt_{_slug(sel)}", c.F.firma() + c.proy.firma, notas_diccionario(c.DIC))


def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _norm(t)).strip("_")


def _complementarios(c, comp: pd.DataFrame) -> None:
    st.warning("ETF y Estructurados **no integran** el panel balanceado ni el modelo econométrico. Se muestran solo de forma descriptiva, con registros observados "
               "y horizontes distintos: no son comparables directamente con la muestra principal.", icon=":material/do_not_disturb_on:")
    base = comp[comp.tipo.isin(["ETF", "Estructurados"])]
    mon = c.F.monedas
    if mon:
        base = base[base.moneda.isin(mon)]
    tipo = st.radio("Tipo complementario", ["Estructurados", "ETF"], key="tipo_comp_sel", horizontal=True)
    d = base[base.tipo.eq(tipo)]
    if d.empty:
        st.info("No hay registros observados de este tipo con la moneda activa.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Observaciones", len(d)); c2.metric("Series", d.id_fondo_serie.nunique()); c3.metric("Meses", d.mes.nunique()); c4.metric("Periodo", f"{d.mes.min()} – {d.mes.max()}")
    g = d.groupby(["fecha", "moneda"]).rent_mes.mean().reset_index()
    fig = go.Figure()
    for i, m in enumerate(sorted(g.moneda.unique())):
        h = g[g.moneda.eq(m)]
        fig.add_trace(go.Scatter(x=h.fecha, y=100 * h.rent_mes, mode="lines+markers", name=gr.NOMBRE_MONEDA[m], line=dict(color=c.P["slots"][i], width=2),
                                 hovertemplate="%{x|%Y-%m}: %{y:.2f} %<extra></extra>"))
    gr.estilo(fig, c.P, f"{tipo}: rentabilidad mensual observada (promedio simple)", "Registros observados de base_integrada_observada.csv; sin tratamiento ni interpolación", alto=360)
    fig.update_yaxes(title_text="% mensual")
    gr.fechas_es(fig, g.fecha)
    st.plotly_chart(fig, config=c.CFG(f"complementario_{_slug(tipo)}"), key=f"g_comp_{_slug(tipo)}", theme=None)
    T20, T21 = c.proy.tabla("tabla20_cobertura_tipos_observados"), c.proy.tabla("tabla21_desempeno_observado_contextual")
    if T20 is not None:
        st.markdown("**Cobertura por tipo observado (tabla 20)**")
        st.dataframe(T20[T20.tipo.eq(tipo)], hide_index=True, width="stretch")
    if T21 is not None:
        st.markdown("**Desempeño contextual de tramos observados ≥ 12 meses (tabla 21)**")
        t21 = T21[T21.tipo.eq(tipo)]
        if mon:
            t21 = t21[t21.moneda.isin(mon)]
        st.dataframe(t21, hide_index=True, width="stretch", height=260)
    st.markdown("**Observaciones**")
    st.dataframe(d.drop(columns=["fecha"]), hide_index=True, width="stretch", height=300)
    boton_descarga(f"Descargar observaciones de {tipo}", {"observaciones": d.drop(columns=["fecha"])}, f"complementarios_{_slug(tipo)}", f"comp_{_slug(tipo)}", c.proy.firma)


# --------------------------------------------------------------------------- base procesada completa
def pestana_base_completa(c) -> None:
    proy = c.proy
    full = datos.procesado_original(proy.raiz)  # exactamente como el archivo entregado (orden y columnas)
    st.markdown("##### Base de datos procesada completa")
    st.caption("Esta pestaña es independiente de los filtros de la barra lateral y de la línea de tiempo: muestra siempre la totalidad de la base procesada.")
    p = full
    cc = st.columns(4)
    cc[0].metric("Observaciones", f"{len(full):,}".replace(",", " "))
    cc[1].metric("Variables", len(full.columns))
    cc[2].metric("Fondos-series", full.id_fondo_serie.nunique())
    cc[3].metric("Periodo completo", f"{full.mes.min()} a {full.mes.max()}")
    st.caption(f"Archivo: {proy.ruta_proc.name} · SHA-256 {c.sha[:16]}… · {full.mes.nunique()} meses · frecuencia mensual · llave: id_fondo_serie + mes.")

    estado = pd.Series("Observado", index=full.index)
    estado[full.imputado.eq(1)] = "Interpolado"
    estado[full.atipico.eq(1)] = "Winsorizado"
    estado[full.imputado.eq(1) & full.atipico.eq(1)] = "Interpolado y winsorizado"
    vista = full.copy()
    vista.insert(len(vista.columns), "estado_dato", estado)

    with st.container(border=True):
        q = st.text_input("Buscar en la base", key="bc_q", placeholder="Fondo, administradora, tipo, archivo, mes…")
        f = st.columns(4)
        sel_tipo = f[0].multiselect("Tipo", sorted(full.tipo.unique()), key="bc_tipo", placeholder="Todos")
        sel_mon = f[1].multiselect("Moneda", sorted(full.moneda.unique()), key="bc_mon", placeholder="Todas")
        sel_adm = f[2].multiselect("Administradora", sorted(full.administradora.unique()), key="bc_adm", placeholder="Todas")
        sel_est = f[3].multiselect("Estado del dato", sorted(estado.unique()), key="bc_est", placeholder="Todos")
        meses = sorted(full.mes.unique())
        per = st.select_slider("Periodo", options=meses, value=(meses[0], meses[-1]), key="bc_per")
        with st.expander("Más filtros individuales (fondo y columna numérica)"):
            sel_fondo = st.multiselect("Fondo", sorted(full.fondo.unique()), key="bc_fondo", placeholder="Todos")
            numericas = [k for k in full.columns if pd.api.types.is_numeric_dtype(full[k]) and full[k].nunique() > 2]
            col_num = st.selectbox("Columna numérica", ["—"] + numericas, key="bc_num")
            rango = None
            if col_num != "—":
                lo, hi = float(full[col_num].min()), float(full[col_num].max())
                rango = st.slider(f"Rango de {col_num}", lo, hi, (lo, hi), key=f"bc_rango_{col_num}")
        st.markdown("**Columnas y orden**")
        o = st.columns([3, 1.3, 1])
        cols = o[0].multiselect("Columnas visibles", list(vista.columns), default=list(full.columns), key="bc_cols")
        orden = o[1].selectbox("Ordenar por", ["(orden original)"] + list(vista.columns), key="bc_orden")
        asc = o[2].radio("Sentido", ["Asc.", "Desc."], key="bc_asc", horizontal=True)

    m = pd.Series(True, index=vista.index)
    if q:
        texto = (vista.mes.astype(str) + " " + vista.tipo + " " + vista.fondo + " " + vista.administradora + " " + vista.moneda + " " +
                 vista.id_fondo_serie + " " + vista.archivo).map(_norm)
        for palabra in _norm(q).split():
            m &= texto.str.contains(re.escape(palabra), regex=True)
    if sel_tipo: m &= vista.tipo.isin(sel_tipo)
    if sel_mon: m &= vista.moneda.isin(sel_mon)
    if sel_adm: m &= vista.administradora.isin(sel_adm)
    if sel_est: m &= vista.estado_dato.isin(sel_est)
    if sel_fondo: m &= vista.fondo.isin(sel_fondo)
    m &= vista.mes.between(per[0], per[1])
    if rango is not None:
        m &= vista[col_num].between(rango[0], rango[1])
    sub = vista[m]
    if orden != "(orden original)":
        sub = sub.sort_values(orden, ascending=(asc == "Asc."), kind="stable")
    if not cols:
        st.warning("Elige al menos una columna para mostrar.")
        cols = list(full.columns)
    st.markdown(f"**{len(sub):,} de {len(vista):,} registros** coinciden con la búsqueda y los filtros de esta pestaña.".replace(",", " "))
    if sub.empty:
        st.warning("Ningún registro cumple los filtros. Amplía la selección.", icon=":material/search_off:")
    cfg = {k: st.column_config.NumberColumn(format="%.5f") for k in ["rent_mes", "rent_original", "exceso", "vol12", "vol12_original", "rent_lag1", "rent_lag1_original", "var_tc", "rf_mensual", "rf_pen", "rf_usd"]}
    cfg.update({"valor_cuota": st.column_config.NumberColumn(format="%.4f"), "tc_fin": st.column_config.NumberColumn("tc_fin", format="%.4f")})
    st.dataframe(sub[cols], hide_index=True, width="stretch", height=520, column_config={k: v for k, v in cfg.items() if k in cols})
    st.caption("Todas las filas son consultables con desplazamiento; haz clic en un encabezado para ordenar. Rentabilidades y tasas están en decimal (0,01 = 1 %).")

    st.markdown("##### Descargas de la base procesada")
    a, b = st.columns(2)
    notas = notas_diccionario(c.DIC)
    with a:
        st.markdown(f"**Base procesada completa** · {len(full)} filas × {len(full.columns)} columnas · siempre la totalidad, sin importar ningún filtro")
        hojas = {"base_procesada": full}
        if c.DIC is not None:
            hojas["diccionario"] = c.DIC
        boton_descarga("Descargar base completa", hojas, f"datos_procesados_{datos.CODIGO_MATRICULA}", "base_completa", proy.firma, notas,
                       csv_estandar=proy.ruta_proc.read_bytes(), key_extra="_bc")
        st.caption("El CSV estándar es el archivo original, byte por byte (su SHA-256 coincide con el declarado).")
    with b:
        st.markdown(f"**Registros filtrados en esta pestaña** · {len(sub)} filas × {len(cols)} columnas")
        meta = pd.DataFrame([{"Campo": "Búsqueda", "Valor": q or "—"}, {"Campo": "Periodo", "Valor": f"{per[0]} a {per[1]}"},
                             {"Campo": "Filas", "Valor": len(sub)}, {"Campo": "Archivo fuente", "Valor": proy.ruta_proc.name},
                             {"Campo": "Generado", "Valor": dl.ahora_peru()}])
        firma_f = f"{q}|{sel_tipo}|{sel_mon}|{sel_adm}|{sel_est}|{sel_fondo}|{per}|{col_num}|{rango}|{cols}|{orden}|{asc}"
        boton_descarga("Descargar registros filtrados", {"registros": sub[cols], "filtros": meta}, f"datos_procesados_filtrados", "base_filtrada", firma_f + proy.firma, notas, key_extra="_bc")
    st.markdown("##### Diccionario de variables y unidades de medida")
    if c.DIC is not None:
        st.dataframe(c.DIC, hide_index=True, width="stretch", height=360)
    st.info(AYUDA_FORMATOS, icon=":material/info:")


# --------------------------------------------------------------------------- descargas
def pestana_descargas(c) -> None:
    proy, DF, F = c.proy, c.DF, c.F
    sufijo = f"{c.ini}_{c.fin}"
    COLS = datos.COLUMNAS_PANEL + ["estado_dato", "etiqueta"]
    firma_total = F.firma() + "|" + c.vista + "|" + proy.firma
    info = {"Filas": len(DF), "Fondos-series": DF.id_fondo_serie.nunique(), "Meses": DF.mes.nunique(), "Archivo fuente": proy.ruta_proc.name,
            "SHA-256 del archivo fuente": c.sha, "Generado": dl.ahora_peru(), "Unidades": "Rentabilidades y tasas en decimal (0,01 = 1 %)"}
    meta = dl.hoja_filtros(F.describir(), info)
    notas = notas_diccionario(c.DIC)
    st.markdown("##### Lo que contienen las descargas")
    st.dataframe(meta.astype(str), hide_index=True, width="stretch")
    st.caption("Las descargas de esta pestaña usan exactamente estos filtros y esta línea de tiempo, salvo la base completa y la base por tipo, que siempre entregan todos los registros.")
    st.info(AYUDA_FORMATOS, icon=":material/info:")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**1 · Registros de los filtros activos** · {len(DF)} filas")
        boton_descarga("Descargar registros filtrados", _hojas_obs(DF, meta, c.DIC, COLS), f"fondos_observaciones_{sufijo}", "d_obs", firma_total, notas, key_extra="_d")
    with c2:
        st.markdown(f"**2 · Base procesada completa** · {len(proy.panel)} filas, sin filtros")
        full = datos.procesado_original(proy.raiz)
        hojas = {"base_procesada": full}
        if c.DIC is not None:
            hojas["diccionario"] = c.DIC
        boton_descarga("Descargar base completa", hojas, f"datos_procesados_{datos.CODIGO_MATRICULA}", "d_full", proy.firma, notas, csv_estandar=proy.ruta_proc.read_bytes(), key_extra="_d")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**3 · Base procesada por tipo de fondo** (todos los meses y monedas)")
        t = st.selectbox("Tipo de fondo", [x for x in gr.ORDEN_TIPOS if x in set(proy.panel.tipo)], key="d_tipo", label_visibility="collapsed")
        completa = proy.panel[proy.panel.tipo.eq(t)][datos.COLUMNAS_PANEL]
        boton_descarga(f"Descargar base de {t} ({len(completa)} filas)", {"base_procesada": completa}, f"base_procesada_{_slug(t)}", f"d_tipo_{_slug(t)}", proy.firma, notas, key_extra="_d")
    with c4:
        st.markdown("**4 · Resultados econométricos existentes** (salidas/ de la investigación)")
        res = {}
        for n in ["tabla3_modelo_principal", "tabla4_modelo_inicial_mco", "tabla5_robustez", "tabla6_vif", "tabla7_diagnosticos", "tabla12_efectos_fijos",
                  "tabla13_sensibilidad_inferencia", "tabla14_contrastes_tipo"]:
            tt = proy.tabla(n)
            if tt is not None:
                res[n[:31]] = tt
        if res:
            boton_descarga(f"Descargar resultados econométricos ({len(res)} tablas)", res, "resultados_econometricos", "d_eco", proy.firma, key_extra="_d")
            st.caption("XLSX con una hoja por tabla. En CSV se entrega la tabla 3 (modelo principal); use el XLSX para el conjunto.")

    st.markdown("**5 · Tablas estadísticas de los filtros activos**")
    tablas = {"filtros": meta.astype(str), "metricas_por_serie": c.M, "resumen_por_categoria": c.RES, "descriptivos": c.DESC,
              "rent_mensual_por_tipo": c.CAT.drop(columns=["fecha"]),
              "calidad_por_mes": DF.groupby("mes").agg(filas=("id_fondo_serie", "size"), interpoladas=("imputado", "sum"), winsorizadas=("atipico", "sum")).reset_index()}
    if c.EST["ok"]:
        tablas["modelo_filtrado"] = c.EST["tabla"]
    a, b = st.columns(2)
    with a:
        boton_descarga("Descargar tablas estadísticas", tablas, f"tablas_estadisticas_{sufijo}", "d_tablas", firma_total + c.RET, key_extra="_d")
    with b:
        st.download_button("ZIP con las tablas en CSV estándar", dl.zip_bytes({f"{k}_{sufijo}.csv": ex.csv_estandar_bytes(v) for k, v in tablas.items()}),
                           f"tablas_estadisticas_{sufijo}.zip", "application/zip", icon=":material/folder_zip:", width="stretch", key="d_tablas_zip")

    st.markdown("**6 · Gráficos seleccionados**")
    nombres = list(c.REG)
    g1, g2 = st.columns([3, 1])
    elegidos = g1.multiselect("Gráficos", nombres, default=[nombres[0]] if nombres else [], format_func=lambda n: c.REG[n][0], key="png_sel", label_visibility="collapsed")
    formato = g2.radio("Formato del gráfico", ["PNG", "SVG", "HTML"], key="graf_fmt", horizontal=True, label_visibility="collapsed")
    nota = (f"Fuente: AAF (boletines mensuales) y BCRPData; elaboración propia. Filtros: {c.mes_corto(c.ini)} – {c.mes_corto(c.fin)}; "
            f"{F.describir()['Tipo de fondo']}; {F.describir()['Moneda']}; {c.etiqueta_ret}.")

    def construir():
        archivos, errores = {}, []
        for n in elegidos:
            fig = c.REG[n][1](c.PCLARO)
            try:
                if formato == "PNG":
                    archivos[f"{n}_{sufijo}.png"] = ex.grafico_bytes(gr.para_exportar(fig, nota), "png")
                elif formato == "SVG":
                    archivos[f"{n}_{sufijo}.svg"] = ex.grafico_bytes(gr.para_exportar(fig, nota), "svg")
                else:
                    archivos[f"{n}_{sufijo}.html"] = ex.grafico_bytes(fig, "html", plotly_js=True if len(elegidos) == 1 else "cdn")
            except Exception as e:  # el exportador estático (Kaleido) puede no estar disponible en el servidor
                errores.append(f"{c.REG[n][0]}: {e!r}")
        return archivos, errores

    if st.button("Preparar gráficos", key="b_graf", icon=":material/image:", disabled=not elegidos):
        with st.spinner("Generando gráficos…"):
            archivos, errores = construir()
        st.session_state.prep_png = (firma_total, formato, tuple(elegidos), archivos, errores)
    v = st.session_state.get("prep_png")
    if v and v[0] == firma_total and v[1] == formato and v[2] == tuple(elegidos):
        archivos, errores = v[3], v[4]
        if len(archivos) == 1:
            nom, b_ = next(iter(archivos.items()))
            st.download_button(f"Descargar {nom}", b_, nom, {"png": "image/png", "svg": "image/svg+xml", "html": "text/html"}[nom.rsplit('.', 1)[1]],
                               key="d_graf1", type="primary", icon=":material/download:")
        elif archivos:
            archivos["filtros.csv"] = ex.csv_estandar_bytes(meta.astype(str))
            st.download_button(f"Descargar ZIP con {len(archivos) - 1} gráficos", dl.zip_bytes(archivos), f"graficos_{sufijo}.zip", "application/zip",
                               key="d_grafz", type="primary", icon=":material/download:")
        for e in errores:
            st.error(f"No se pudo generar: {e}. Usa el icono de cámara del gráfico como alternativa.")
    st.caption("PNG a 2800 px de ancho, SVG vectorial y HTML interactivo (autónomo). También puedes usar el icono de cámara de cada gráfico.")

    st.divider()
    st.markdown("**7 · Reporte HTML imprimible con los filtros activos**")

    def preparar_reporte() -> bytes:
        nota_r = f"Fuente: AAF y BCRPData; elaboración propia. {c.mes_corto(c.ini)} – {c.mes_corto(c.fin)}."
        figuras, primera = [], True
        for n_, (t_, cons) in c.REG.items():
            fig = cons(c.PCLARO)
            try:
                figuras.append((t_, dl.png_bytes(gr.para_exportar(fig, nota_r), ancho=1200, escala=1.5)))
            except Exception:
                figuras.append((t_, fig.to_html(full_html=False, include_plotlyjs="inline" if primera else False)))
                primera = False
        secciones = [("Indicadores principales por moneda", "Medianas entre fondos-series; las monedas no se mezclan.", c.KPI),
                     ("Comparación por tipo de fondo y moneda", "", c.RES), ("Estadísticos descriptivos de la rentabilidad mensual", "", c.DESC),
                     ("Desempeño por fondo-serie", "", c.M.drop(columns=["id_fondo_serie"])),
                     ("Calidad de datos", f"Filas: {c.CAL['filas']} · observadas: {c.CAL['observadas']} · interpoladas: {c.CAL['interpoladas']} · "
                                          f"winsorizadas: {c.CAL['winsorizadas']} · faltantes: {c.CAL['faltantes']}.", None)]
        if c.T3 is not None:
            secciones.append(("Modelo oficial (panel completo, tabla 3)", "\n\n".join(eco.interpretar(c.T3)), c.T3[["variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup"]]))
        if c.EST["ok"]:
            secciones.append(("Reestimación exploratoria con los filtros", "\n\n".join(eco.interpretar(c.EST["tabla"]) + c.EST["advertencias"]), c.EST["tabla"]))
        return dl.reporte_html("Fondos mutuos en el Perú · Reporte de resultados filtrados", F.describir(), info, secciones, figuras, eco.ADVERTENCIA_GENERAL).encode("utf-8")

    a, b = st.columns(2)
    if a.button("Preparar reporte con los filtros activos", width="stretch", icon=":material/description:", key="b_rep"):
        with st.spinner("Armando el reporte (tablas, gráficos y lectura econométrica)…"):
            st.session_state.prep_reporte = (firma_total, preparar_reporte())
    v = st.session_state.get("prep_reporte")
    if v and v[0] == firma_total:
        b.download_button("Descargar reporte HTML", v[1], f"reporte_fondos_{sufijo}.html", "text/html", width="stretch", type="primary", key="dl_reporte", icon=":material/download:")
    st.caption("Ábrelo en el navegador y usa Imprimir → Guardar como PDF si necesitas un PDF.")


# --------------------------------------------------------------------------- transparencia
def pestana_transparencia(c) -> None:
    proy = c.proy
    p = pc.portal()
    st.markdown("##### Transparencia y reproducibilidad")
    st.caption("Información técnica de apoyo; no forma parte del análisis financiero. Todo se lee de los archivos entregados de la investigación (solo lectura).")
    st.warning(p["nota_fuentes"] + " El rastreo de la SMV fue rechazado (HTTP 418) y está registrado en incidencias_fuente.md; la documentación no contiene una autorización docente escrita de sustitución de fuente.",
               icon=":material/info:")
    st.link_button("Repositorio GitHub de la investigación", p["repositorio_url"], icon=":material/code:")

    st.markdown("**Fuentes**")
    st.dataframe(pd.DataFrame([
        ("AAF · boletines mensuales", "Descarga programática y parseo de PDF (scraping)", "https://fondosmutuos.pe/estadisticas/", "Cuota, rentabilidad, tipo, administradora, moneda"),
        ("BCRPData · PN01216PM", "API REST (JSON)", "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01216PM/json/2018-12/2025-12/esp", "Tipo de cambio fin de periodo"),
        ("BCRPData · PD04692MD", "API REST (JSON)", "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04692MD/json/2018-12-01/2025-12-31/esp", "Tasa interbancaria PEN"),
        ("BCRPData · PD04693MD", "API REST (JSON)", "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04693MD/json/2018-12-01/2025-12-31/esp", "Tasa interbancaria USD")],
        columns=["Fuente", "Vía", "URL / endpoint", "Contenido"]), hide_index=True, width="stretch", column_config={"URL / endpoint": st.column_config.LinkColumn("URL / endpoint")})

    st.markdown("**Integridad: hashes SHA-256**")
    man = datos.leer_hashes(proy.raiz)
    if man.empty:
        st.info("No se encontró hash_sha256.txt en esta copia de la investigación.")
    else:
        st.caption(f"El manifiesto declara {len(man)} archivos. El archivo procesado entregado tiene SHA-256 {c.sha}.")
        if st.button("Recalcular y comparar los hashes de los archivos presentes", key="t_hash", icon=":material/fingerprint:"):
            with st.spinner("Calculando SHA-256…"):
                st.session_state.t_hash_res = datos.verificar_hashes(proy.raiz, man)
        res = st.session_state.get("t_hash_res")
        if res is not None:
            cuenta = res.estado.value_counts().to_dict()
            st.success(f"Coinciden: {cuenta.get('Coincide', 0)} · No coinciden: {cuenta.get('NO coincide', 0)} · No están en esta copia: {cuenta.get('No está en esta copia', 0)}",
                       icon=":material/check_circle:") if cuenta.get("NO coincide", 0) == 0 else st.error(f"Hay {cuenta['NO coincide']} archivos que NO coinciden con el manifiesto.")
            st.dataframe(res, hide_index=True, width="stretch", height=260)
        else:
            st.dataframe(man, hide_index=True, width="stretch", height=240)

    st.markdown("**Datos crudos, complementarios y base procesada**")
    archivos = {
        "Datos crudos · BCRP (CSV)": f"datos_crudos/datos_crudos_{datos.CODIGO_MATRICULA}_bcrp.csv",
        "Datos crudos · AAF (CSV)": f"datos_crudos/datos_crudos_{datos.CODIGO_MATRICULA}_aaf.csv",
        "Datos complementarios · base integrada observada": "datos_procesados/base_integrada_observada.csv",
        "Base procesada (panel balanceado)": f"datos_procesados/datos_procesados_{datos.CODIGO_MATRICULA}.csv",
        "Inventario de descargas de boletines": f"datos_crudos/scraping/descargas_boletines_{datos.CODIGO_MATRICULA}.csv",
    }
    disp = {k: v for k, v in archivos.items() if (proy.raiz / v).is_file()}
    if disp:
        k = st.selectbox("Archivo", list(disp), key="t_arch")
        ruta = proy.raiz / disp[k]
        vista = pd.read_csv(ruta, nrows=200, dtype=str)
        total = sum(1 for _ in ruta.open("rb")) - 1
        st.caption(f"{disp[k]} · {total:,} filas · se muestran las primeras 200; descarga el archivo original abajo.".replace(",", " "))
        st.dataframe(vista, hide_index=True, width="stretch", height=260)
        st.download_button("Descargar archivo original (CSV)", ruta.read_bytes(), ruta.name, "text/csv", key="t_dl_arch", icon=":material/download:")

    st.markdown("**Código Python y pipeline de Google Colab**")
    codigos = sorted((proy.raiz / "codigo").glob("*.py")) if (proy.raiz / "codigo").is_dir() else []
    if codigos:
        nombre = st.selectbox("Script", [x.name for x in codigos], key="t_script")
        txt = (proy.raiz / "codigo" / nombre).read_text(encoding="utf-8")
        st.caption(f"codigo/{nombre} · {len(txt.splitlines())} líneas · solo lectura (el portal nunca ejecuta estos scripts ni vuelve a extraer datos).")
        with st.expander("Ver el código", icon=":material/code:"):
            st.code(txt, language="python", line_numbers=True)
        st.download_button("Descargar script", txt.encode("utf-8"), nombre, "text/x-python", key="t_dl_script", icon=":material/download:")
    nb = proy.raiz / "codigo" / "00_pipeline_colab.ipynb"
    if nb.is_file():
        st.markdown(f"Pipeline de Google Colab: `codigo/{nb.name}` ({nb.stat().st_size // 1024} KB).")
        st.download_button("Descargar el cuaderno de Colab (.ipynb)", nb.read_bytes(), nb.name, "application/x-ipynb+json", key="t_dl_nb", icon=":material/download:")
    if pc.es_url(p.get("colab_url", "")):
        st.link_button("Abrir en Google Colab", p["colab_url"], icon=":material/open_in_new:")
    else:
        st.caption("Enlace directo a Colab: pendiente (se configura en config/portal.json → colab_url).")

    st.markdown("**Registros de extracción, ejecución y verificación**")
    for etiqueta, ruta in [("Registro de ejecución (log_ejecucion.txt)", "log_ejecucion.txt"), ("Incidencias técnicas de las fuentes", "incidencias_fuente.md"),
                           ("Verificación local de la reproducción", "salidas/verificacion_local.md"), ("Bitácora de uso de IA", "documentos/bitacora_ia.md"),
                           ("README de la investigación", "README.md")]:
        txt = proy.texto(ruta)
        if txt:
            with st.expander(etiqueta):
                st.text(txt[:60000]) if ruta.endswith(".txt") else st.markdown(txt[:60000])
    st.markdown("**Diccionario de variables**")
    if c.DIC is not None:
        st.dataframe(c.DIC, hide_index=True, width="stretch", height=300)
    st.markdown("**Limitaciones metodológicas**")
    lim = next((b for b in pc.contenido()["discusion"] if b["clave"] == "limitaciones"), None)
    if lim and lim.get("texto"):
        st.markdown(lim["texto"])
    st.info(eco.ADVERTENCIA_GENERAL, icon=":material/balance:")
