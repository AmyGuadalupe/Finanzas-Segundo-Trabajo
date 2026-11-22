"""Gráficos Plotly del dashboard.

Reglas de diseño aplicadas:
- Las monedas nunca se mezclan: cada moneda tiene su propio panel.
- El color sigue a la entidad (tipo de fondo), no a su posición; los colores
  categóricos siguen un orden fijo validado para daltonismo en pares adyacentes.
- En la dispersión (todos los pares en pantalla) se resalta un solo tipo y el
  resto queda en gris, en lugar de usar cinco colores a la vez.
- Un solo eje Y por gráfico; líneas de 2 px; rejilla fina y discreta.
- Cada constructor recibe la paleta (clara u oscura) para poder exportar PNG
  siempre con la versión clara.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ORDEN_TIPOS = ["Acciones", "Deuda", "Flexibles", "Fondo de fondos", "Mixtos", "ETF", "Estructurados"]
ORDEN_MONEDAS = ["PEN", "USD"]
NOMBRE_MONEDA = {"PEN": "Soles (PEN)", "USD": "Dólares (USD)"}

_SLOTS_CLARO = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
_SLOTS_OSCURO = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"]

PALETAS = {
    "light": dict(
        modo="light", superficie="#fcfcfb", texto="#0b0b0b", texto2="#52514e", tenue="#8a8984",
        rejilla="#ebeae6", eje="#d6d5d0", neutro="#c9c8c2", observado="#e6e5e0",
        slots=_SLOTS_CLARO, resalte="rgba(42,120,214,0.10)",
    ),
    "dark": dict(
        modo="dark", superficie="#1a1a19", texto="#f0efec", texto2="#c3c2b7", tenue="#8f8e88",
        rejilla="#2c2c2a", eje="#3a3a37", neutro="#55554f", observado="#2f2f2c",
        slots=_SLOTS_OSCURO, resalte="rgba(57,135,229,0.16)",
    ),
}
FUENTE = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"


def color_tipo(tipo: str, p: dict) -> str:
    i = ORDEN_TIPOS.index(tipo) if tipo in ORDEN_TIPOS else 7
    return p["slots"][i]


def colores_estado(p: dict) -> dict:
    s = p["slots"]
    return {"Observado": p["observado"], "Interpolado": s[0], "Winsorizado": s[1], "Interpolado y winsorizado": s[2]}


def _monedas(*dfs) -> list[str]:
    presentes = set()
    for d in dfs:
        if d is not None and len(d) and "moneda" in d:
            presentes |= set(d.moneda.unique())
    return [m for m in ORDEN_MONEDAS if m in presentes]


def estilo(fig: go.Figure, p: dict, titulo: str, subtitulo: str = "", alto: int = 420, leyenda: bool = True,
           paneles: bool = False) -> go.Figure:
    """Título, subtítulo y leyenda anclados en píxeles para que no se superpongan."""
    cab = 34 + (22 if subtitulo else 0)            # alto del título y subtítulo
    ley = 30 if leyenda else 0                      # fila de la leyenda
    pan = 24 if paneles else 0                      # títulos de los paneles por moneda
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", x=0, xanchor="left", xref="container", y=1, yref="container", yanchor="top",
                   pad=dict(t=10, l=8), font=dict(size=15, color=p["texto"]),
                   subtitle=dict(text=subtitulo, font=dict(size=12, color=p["texto2"]))),
        font=dict(family=FUENTE, size=12, color=p["texto2"]),
        paper_bgcolor=p["superficie"], plot_bgcolor=p["superficie"],
        height=alto, margin=dict(l=10, r=18, t=cab + ley + pan + 10, b=10),
        hovermode="closest",
        hoverlabel=dict(bgcolor=p["superficie"], bordercolor=p["eje"], font=dict(color=p["texto"], family=FUENTE, size=12)),
        legend=dict(orientation="h", yref="container", y=1 - (cab + 6) / alto, yanchor="top", xanchor="left", x=0,
                    title_text="", font=dict(color=p["texto"], size=12), bgcolor="rgba(0,0,0,0)", itemclick="toggle"),
        showlegend=leyenda,
    )
    fig.update_xaxes(showgrid=False, linecolor=p["eje"], linewidth=1, ticks="outside", tickcolor=p["eje"],
                     tickfont=dict(color=p["texto2"]), zeroline=False, automargin=True)
    fig.update_yaxes(showgrid=True, gridcolor=p["rejilla"], gridwidth=1, linecolor=p["eje"], zeroline=False,
                     tickfont=dict(color=p["texto2"]), automargin=True)
    fig.update_annotations(font=dict(color=p["texto"], size=12))
    return fig


MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fechas_es(fig: go.Figure, fechas) -> go.Figure:
    """Marcas del eje de tiempo en español (Plotly no trae la configuración regional)."""
    f = pd.to_datetime(pd.Series(fechas)).dropna()
    if f.empty:
        return fig
    ini, fin = f.min(), f.max()
    meses = (fin.year - ini.year) * 12 + fin.month - ini.month + 1
    paso = 1 if meses <= 8 else 2 if meses <= 16 else 3 if meses <= 30 else 6
    marcas = [d for d in pd.date_range(ini.to_period("M").to_timestamp(), fin, freq="MS") if (d.month - 1) % paso == 0]
    fig.update_xaxes(tickvals=marcas, ticktext=[f"{MESES_ES[d.month - 1]} {d.year}" for d in marcas], hoverformat="%Y-%m")
    return fig


def _cero(fig, p, filas=1, cols=1, eje="y"):
    for r in range(1, filas + 1):
        for c in range(1, cols + 1):
            if eje == "y":
                fig.add_hline(y=0, line=dict(color=p["eje"], width=1), row=r, col=c)
            else:
                fig.add_vline(x=0, line=dict(color=p["eje"], width=1), row=r, col=c)


def _vacio(p: dict, titulo: str, mensaje: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=mensaje, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                       font=dict(color=p["texto2"], size=13))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return estilo(fig, p, titulo, alto=260, leyenda=False)


# --------------------------------------------------------------------------
# Línea de tiempo (reemplaza al mapa del video de referencia)
# --------------------------------------------------------------------------
def fig_linea_tiempo(lt: pd.DataFrame, ini: str, fin: str, p: dict) -> go.Figure:
    titulo = "Línea de tiempo financiera"
    if lt.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    fig = go.Figure()
    tinta = {"PEN": p["texto"], "USD": p["tenue"]}
    f_ini = pd.Timestamp(ini + "-01") - pd.Timedelta(days=15)
    f_fin = pd.Timestamp(fin + "-01") + pd.Timedelta(days=15)
    fig.add_vrect(x0=f_ini, x1=f_fin, fillcolor=p["resalte"], line_width=0, layer="below")
    for mon in _monedas(lt):
        g = lt[lt.moneda.eq(mon)].sort_values("fecha")
        fig.add_trace(go.Scatter(
            x=g.fecha, y=100 * g.rent, mode="lines", name=NOMBRE_MONEDA[mon],
            line=dict(color=tinta[mon], width=2, shape="linear"),
            customdata=np.c_[g.series, g.mes],
            hovertemplate="%{customdata[1]} · " + mon + ": %{y:.2f} %<br>%{customdata[0]} series (promedio simple)<extra></extra>",
        ))
    _cero(fig, p)
    estilo(fig, p, titulo, f"Rentabilidad mensual promedio por moneda · periodo seleccionado: {ini} a {fin} (franja sombreada)", alto=290)
    fig.update_yaxes(title_text="% mensual", ticksuffix="")
    fechas_es(fig, lt.fecha)
    fig.update_layout(hovermode="x unified")
    return fig


# --------------------------------------------------------------------------
# Series temporales por moneda (categoría o fondo-serie)
# --------------------------------------------------------------------------
def _paneles(monedas, alto_panel=260):
    fig = make_subplots(rows=len(monedas), cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=[NOMBRE_MONEDA[m] for m in monedas])
    return fig, max(320, alto_panel * len(monedas) + 140)


def _lineas(fig, datos, ycol, escala, vista, p, colores_series, fmt, etiqueta_y, n_col=None):
    monedas = _monedas(datos)
    vistos = set()
    for i, mon in enumerate(monedas, start=1):
        d = datos[datos.moneda.eq(mon)]
        if vista == "categoria":
            for tipo in [t for t in ORDEN_TIPOS if t in set(d.tipo)]:
                g = d[d.tipo.eq(tipo)].sort_values("fecha")
                extra = g[n_col] if n_col and n_col in g else pd.Series([""] * len(g))
                fig.add_trace(go.Scatter(
                    x=g.fecha, y=escala * g[ycol], mode="lines", name=tipo, legendgroup=tipo,
                    showlegend=tipo not in vistos, line=dict(color=color_tipo(tipo, p), width=2),
                    customdata=np.c_[g.mes, extra],
                    hovertemplate=f"<b>{tipo}</b> · {mon}<br>%{{customdata[0]}}: %{{y:{fmt}}}{etiqueta_y}"
                                  + ("<br>%{customdata[1]} series" if n_col else "") + "<extra></extra>",
                ), row=i, col=1)
                vistos.add(tipo)
        else:
            for id_ in sorted(d.id_fondo_serie.unique(), key=lambda x: colores_series.get(x, (99, ""))[0]):
                g = d[d.id_fondo_serie.eq(id_)].sort_values("fecha")
                nombre = g.etiqueta.iloc[0]
                color = colores_series.get(id_, (0, p["slots"][0]))[1]
                fig.add_trace(go.Scatter(
                    x=g.fecha, y=escala * g[ycol], mode="lines", name=nombre, legendgroup=id_,
                    line=dict(color=color, width=2), customdata=np.c_[g.mes, g.tipo],
                    hovertemplate=f"<b>{nombre}</b><br>%{{customdata[1]}} · %{{customdata[0]}}: %{{y:{fmt}}}{etiqueta_y}<extra></extra>",
                ), row=i, col=1)
    return monedas


def _marcas_estado(fig, datos, ycol, escala, p, monedas):
    """Marca los meses interpolados y winsorizados sobre las líneas de cada serie."""
    simbolos = {"Interpolado": "circle-open", "Winsorizado": "x-thin-open", "Interpolado y winsorizado": "diamond-open"}
    for estado, simbolo in simbolos.items():
        primero = True
        for i, mon in enumerate(monedas, start=1):
            g = datos[datos.moneda.eq(mon) & datos.estado_dato.eq(estado)]
            if g.empty:
                continue
            fig.add_trace(go.Scatter(
                x=g.fecha, y=escala * g[ycol], mode="markers", name=estado, legendgroup="estado_" + estado,
                showlegend=primero, marker=dict(symbol=simbolo, size=10, color=p["texto"], line=dict(width=2, color=p["texto"])),
                customdata=np.c_[g.etiqueta, g.mes],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}: " + estado.lower() + "<extra></extra>",
            ), row=i, col=1)
            primero = False


def fig_rent_mensual(cat: pd.DataFrame, ser: pd.DataFrame, vista: str, retorno: str, p: dict, colores_series: dict, sub: str) -> go.Figure:
    titulo = "Evolución mensual de la rentabilidad"
    datos = cat if vista == "categoria" else ser
    if datos is None or datos.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    ycol = "rent" if vista == "categoria" else ("rent_mes" if retorno == "tratada" else "rent_original")
    monedas = _monedas(datos)
    fig, alto = _paneles(monedas)
    _lineas(fig, datos, ycol, 100, vista, p, colores_series, ".2f", " %", n_col="series")
    if vista == "serie":
        _marcas_estado(fig, ser, ycol, 100, p, monedas)
    _cero(fig, p, filas=len(monedas))
    estilo(fig, p, titulo, sub, alto=alto, paneles=True)
    fig.update_yaxes(title_text="% mensual")
    fechas_es(fig, datos.fecha)
    return fig


def fig_acumulada(ind: pd.DataFrame, vista: str, p: dict, colores_series: dict, sub: str) -> go.Figure:
    titulo = "Rentabilidad acumulada (capitalización compuesta, base 100)"
    if ind is None or ind.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    monedas = _monedas(ind)
    fig, alto = _paneles(monedas)
    _lineas(fig, ind, "indice", 1, vista, p, colores_series, ".1f", "", n_col="series" if vista == "categoria" else None)
    for i in range(1, len(monedas) + 1):
        fig.add_hline(y=100, line=dict(color=p["eje"], width=1), row=i, col=1)
    estilo(fig, p, titulo, sub, alto=alto, paneles=True)
    fig.update_yaxes(title_text="Índice (inicio = 100)")
    fechas_es(fig, ind.fecha)
    return fig


def fig_volatilidad(vol: pd.DataFrame, vista: str, p: dict, colores_series: dict, sub: str) -> go.Figure:
    titulo = "Volatilidad histórica móvil (12 meses previos, anualizada)"
    if vol is None or vol.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    monedas = _monedas(vol)
    fig, alto = _paneles(monedas)
    _lineas(fig, vol, "vol_anual", 100, vista, p, colores_series, ".2f", " %", n_col="series" if vista == "categoria" else None)
    estilo(fig, p, titulo, sub, alto=alto, paneles=True)
    fig.update_yaxes(title_text="% anual", rangemode="tozero")
    fechas_es(fig, vol.fecha)
    return fig


def fig_caidas(cai: pd.DataFrame, vista: str, p: dict, colores_series: dict, sub: str) -> go.Figure:
    titulo = "Caída desde el máximo previo (drawdown)"
    if cai is None or cai.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    monedas = _monedas(cai)
    fig, alto = _paneles(monedas)
    _lineas(fig, cai, "caida", 100, vista, p, colores_series, ".2f", " %", n_col="series" if vista == "categoria" else None)
    _cero(fig, p, filas=len(monedas))
    estilo(fig, p, titulo, sub, alto=alto, paneles=True)
    fig.update_yaxes(title_text="% bajo el máximo")
    fechas_es(fig, cai.fecha)
    return fig


# --------------------------------------------------------------------------
# Riesgo-rentabilidad y comparación de categorías
# --------------------------------------------------------------------------
def fig_dispersion(m: pd.DataFrame, resaltar: str, p: dict, sub: str) -> go.Figure:
    titulo = "Dispersión riesgo-rentabilidad por fondo-serie"
    m = m.dropna(subset=["vol_anualizada", "rent_anualizada"]) if not m.empty else m
    if m.empty:
        return _vacio(p, titulo, "Se necesitan al menos 12 meses para anualizar")
    monedas = _monedas(m)
    fig = make_subplots(rows=1, cols=len(monedas), subplot_titles=[NOMBRE_MONEDA[x] for x in monedas],
                        horizontal_spacing=0.08)
    otros_vistos = resalt_visto = False
    for j, mon in enumerate(monedas, start=1):
        d = m[m.moneda.eq(mon)]
        for es_resalte in (False, True):
            g = d[d.tipo.eq(resaltar)] if es_resalte else d[~d.tipo.eq(resaltar)]
            if g.empty:
                continue
            color = color_tipo(resaltar, p) if es_resalte else p["neutro"]
            nombre = resaltar if es_resalte else "Otros tipos"
            fig.add_trace(go.Scatter(
                x=100 * g.vol_anualizada, y=100 * g.rent_anualizada, mode="markers", name=nombre,
                legendgroup=nombre, showlegend=not (resalt_visto if es_resalte else otros_vistos),
                marker=dict(size=11 if es_resalte else 9, color=color, opacity=1 if es_resalte else 0.75,
                            line=dict(width=2, color=p["superficie"])),
                customdata=np.c_[g.etiqueta, g.tipo, g.sharpe_anualizado.round(3), g.n_meses],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · " + mon +
                              "<br>Rentabilidad anualizada: %{y:.2f} %<br>Volatilidad anualizada: %{x:.2f} %"
                              "<br>Sharpe: %{customdata[2]}<br>%{customdata[3]} meses<extra></extra>",
            ), row=1, col=j)
            if es_resalte:
                resalt_visto = True
            else:
                otros_vistos = True
    _cero(fig, p, cols=len(monedas))
    estilo(fig, p, titulo, sub, alto=480, paneles=True)
    fig.update_xaxes(title_text="Volatilidad anualizada (%)", rangemode="tozero")
    fig.update_yaxes(title_text="Rentabilidad anualizada (%)", col=1)
    return fig


def fig_sharpe_categorias(res: pd.DataFrame, p: dict, sub: str) -> go.Figure:
    titulo = "Sharpe anualizado por tipo de fondo: mediana e intervalo intercuartílico"
    res = res.dropna(subset=["sharpe_mediana"]) if not res.empty else res
    if res.empty:
        return _vacio(p, titulo, "Se necesitan al menos 12 meses para calcular el Sharpe")
    monedas = _monedas(res)
    fig = make_subplots(rows=1, cols=len(monedas), subplot_titles=[NOMBRE_MONEDA[x] for x in monedas],
                        shared_yaxes=True, horizontal_spacing=0.06)
    vistos = set()
    tipos_eje = [t for t in ORDEN_TIPOS if t in set(res.tipo)][::-1]
    for j, mon in enumerate(monedas, start=1):
        d = res[res.moneda.eq(mon)]
        for _, f in d.iterrows():
            fig.add_trace(go.Scatter(
                x=[f.sharpe_mediana], y=[f.tipo], mode="markers", name=f.tipo, legendgroup=f.tipo,
                showlegend=f.tipo not in vistos,
                marker=dict(size=12, color=color_tipo(f.tipo, p), line=dict(width=2, color=p["superficie"])),
                error_x=dict(type="data", symmetric=False, array=[f.sharpe_q75 - f.sharpe_mediana],
                             arrayminus=[f.sharpe_mediana - f.sharpe_q25], color=color_tipo(f.tipo, p), thickness=2, width=6),
                hovertemplate=f"<b>{f.tipo}</b> · {mon}<br>Mediana: {f.sharpe_mediana:.3f}<br>"
                              f"Q1–Q3: {f.sharpe_q25:.3f} a {f.sharpe_q75:.3f}<br>{int(f.unidades)} series<extra></extra>",
            ), row=1, col=j)
            vistos.add(f.tipo)
    _cero(fig, p, cols=len(monedas), eje="x")
    estilo(fig, p, titulo, sub, alto=max(340, 70 * len(tipos_eje) + 170), paneles=True)
    fig.update_yaxes(categoryorder="array", categoryarray=tipos_eje)
    fig.update_xaxes(title_text="Sharpe anualizado")
    return fig


def fig_caja(df: pd.DataFrame, retorno: str, p: dict, sub: str) -> go.Figure:
    titulo = "Distribución de la rentabilidad mensual por tipo de fondo"
    if df.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    col = "rent_mes" if retorno == "tratada" else "rent_original"
    monedas = _monedas(df)
    fig = make_subplots(rows=1, cols=len(monedas), subplot_titles=[NOMBRE_MONEDA[x] for x in monedas],
                        shared_yaxes=True, horizontal_spacing=0.05)
    vistos = set()
    for j, mon in enumerate(monedas, start=1):
        d = df[df.moneda.eq(mon)]
        for tipo in [t for t in ORDEN_TIPOS if t in set(d.tipo)]:
            g = d[d.tipo.eq(tipo)]
            c = color_tipo(tipo, p)
            fig.add_trace(go.Box(
                y=100 * g[col], name=tipo, legendgroup=tipo, showlegend=tipo not in vistos,
                marker=dict(color=c, size=4), line=dict(color=c, width=1.5), fillcolor=_alfa(c, 0.12),
                boxpoints="outliers", hoverinfo="y+name",
            ), row=1, col=j)
            vistos.add(tipo)
    _cero(fig, p, cols=len(monedas))
    estilo(fig, p, titulo, sub, alto=460, paneles=True)
    fig.update_yaxes(title_text="% mensual", col=1)
    fig.update_xaxes(showticklabels=False)
    return fig


def fig_ranking_sharpe(m: pd.DataFrame, p: dict, sub: str) -> go.Figure:
    titulo = "Ranking de Sharpe anualizado por fondo-serie"
    m = m.dropna(subset=["sharpe_anualizado"]) if not m.empty else m
    if m.empty:
        return _vacio(p, titulo, "Se necesitan al menos 12 meses para calcular el Sharpe")
    monedas = _monedas(m)
    total = int(m.shape[0])
    alto = max(340, 22 * total + 150 * len(monedas))
    fig = make_subplots(rows=len(monedas), cols=1, subplot_titles=[NOMBRE_MONEDA[x] for x in monedas],
                        vertical_spacing=(90 / alto) if len(monedas) > 1 else 0.05,
                        row_heights=[max(1, m.moneda.eq(x).sum()) for x in monedas])
    vistos = set()
    for i, mon in enumerate(monedas, start=1):
        d = m[m.moneda.eq(mon)].sort_values("sharpe_anualizado")
        for tipo in [t for t in ORDEN_TIPOS if t in set(d.tipo)]:
            g = d[d.tipo.eq(tipo)]
            fig.add_trace(go.Bar(
                x=g.sharpe_anualizado, y=g.etiqueta, orientation="h", name=tipo, legendgroup=tipo,
                showlegend=tipo not in vistos, marker=dict(color=color_tipo(tipo, p), cornerradius=4),
                customdata=np.c_[g.tipo, 100 * g.rent_anualizada, 100 * g.vol_anualizada],
                hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>Sharpe: %{x:.3f}<br>"
                              "Rentabilidad: %{customdata[1]:.2f} % · Volatilidad: %{customdata[2]:.2f} %<extra></extra>",
            ), row=i, col=1)
            vistos.add(tipo)
        fig.update_yaxes(categoryorder="array", categoryarray=list(d.etiqueta), row=i, col=1)
    _cero(fig, p, filas=len(monedas), eje="x")
    estilo(fig, p, titulo, sub, alto=alto, paneles=True)
    fig.update_layout(bargap=0.25, barmode="overlay")
    fig.update_xaxes(title_text="Sharpe anualizado")
    fig.update_yaxes(tickfont=dict(size=11))
    return fig


# --------------------------------------------------------------------------
# Econometría
# --------------------------------------------------------------------------
def fig_coeficientes(oficial: pd.DataFrame | None, filtrada: pd.DataFrame | None, p: dict, sub: str) -> go.Figure:
    titulo = "Coeficientes de los tres factores e intervalos de confianza al 95 %"
    factores = ["vol12", "var_tc", "rent_lag1"]
    fig = go.Figure()
    for nombre, tabla, color, simbolo, desfase in [
        ("Panel completo (tabla 3 oficial)", oficial, p["texto"], "circle", 0.12),
        ("Subconjunto filtrado (exploratorio)", filtrada, p["slots"][0], "diamond", -0.12),
    ]:
        if tabla is None or tabla.empty:
            continue
        t = tabla[tabla.variable.isin(factores)].set_index("variable").reindex(factores).dropna(subset=["coeficiente"])
        if t.empty:
            continue
        y = [factores[::-1].index(v) + desfase for v in t.index]
        fig.add_trace(go.Scatter(
            x=t.coeficiente, y=y, mode="markers", name=nombre,
            marker=dict(size=11, symbol=simbolo, color=color, line=dict(width=2, color=p["superficie"])),
            error_x=dict(type="data", symmetric=False, array=t.ic95_sup - t.coeficiente,
                         arrayminus=t.coeficiente - t.ic95_inf, color=color, thickness=2, width=6),
            customdata=np.c_[t.index, t.p_valor, t.ic95_inf, t.ic95_sup],
            hovertemplate="<b>%{customdata[0]}</b> · " + nombre + "<br>Coeficiente: %{x:.4f}"
                          "<br>IC 95 %: %{customdata[2]:.4f} a %{customdata[3]:.4f}<br>p = %{customdata[1]:.4f}<extra></extra>",
        ))
    fig.add_vline(x=0, line=dict(color=p["eje"], width=1))
    estilo(fig, p, titulo, sub, alto=360)
    fig.update_yaxes(tickvals=[0, 1, 2], ticktext=["rent_lag1 (X3)", "var_tc (X2)", "vol12 (X1)"][::1], range=[-0.6, 2.6], showgrid=False)
    fig.update_xaxes(title_text="Coeficiente (pp de rentabilidad mensual por pp del factor)", showgrid=True, gridcolor=p["rejilla"])
    return fig


def fig_robustez(espec: pd.DataFrame, p: dict, variable: str, sub: str) -> go.Figure:
    titulo = f"Estabilidad del coeficiente de {variable} entre especificaciones"
    if espec is None or espec.empty:
        return _vacio(p, titulo, "Tablas de robustez no disponibles")
    e = espec.iloc[::-1]
    fig = go.Figure(go.Scatter(
        x=e.coeficiente, y=e.especificacion, mode="markers", showlegend=False,
        marker=dict(size=11, color=p["texto"], line=dict(width=2, color=p["superficie"])),
        error_x=dict(type="data", symmetric=False, array=e.ic95_sup - e.coeficiente,
                     arrayminus=e.coeficiente - e.ic95_inf, color=p["texto2"], thickness=2, width=6),
        customdata=np.c_[e.p_valor],
        hovertemplate="<b>%{y}</b><br>Coeficiente: %{x:.4f}<br>p = %{customdata[0]:.4f}<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color=p["eje"], width=1))
    estilo(fig, p, titulo, sub, alto=max(300, 46 * len(e) + 140), leyenda=False)
    fig.update_xaxes(title_text="Coeficiente e IC 95 %", showgrid=True, gridcolor=p["rejilla"])
    fig.update_yaxes(showgrid=False)
    return fig


# --------------------------------------------------------------------------
# Calidad de datos
# --------------------------------------------------------------------------
def fig_calidad_mapa(df: pd.DataFrame, p: dict, sub: str) -> go.Figure:
    titulo = "Mapa de calidad: estado de cada observación (fondo-serie × mes)"
    if df.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    estados = ["Observado", "Interpolado", "Winsorizado", "Interpolado y winsorizado"]
    cod = {e: i for i, e in enumerate(estados)}
    orden = df.drop_duplicates("id_fondo_serie").assign(o=lambda x: x.tipo.map({t: i for i, t in enumerate(ORDEN_TIPOS)}))
    orden = orden.sort_values(["moneda", "o", "etiqueta"])
    piv = df.pivot(index="etiqueta", columns="fecha", values="estado_dato").reindex(orden.etiqueta)
    z = piv.apply(lambda c: c.map(cod)).to_numpy(float)
    colores = colores_estado(p)
    escala = []
    for i, e in enumerate(estados):
        escala += [[i / 4, colores[e]], [(i + 1) / 4, colores[e]]]
    texto = piv.to_numpy(object)
    fig = go.Figure(go.Heatmap(
        z=z, x=piv.columns, y=piv.index, zmin=0, zmax=4, colorscale=escala, showscale=False,
        xgap=1, ygap=1, customdata=texto,
        hovertemplate="<b>%{y}</b><br>%{x|%Y-%m}: %{customdata}<extra></extra>",
    ))
    for e in estados:  # leyenda manual
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=e,
                                 marker=dict(symbol="square", size=12, color=colores[e])))
    estilo(fig, p, titulo, sub, alto=max(340, 15 * len(piv) + 190))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=10), autorange="reversed")
    fechas_es(fig, piv.columns)
    fig.update_layout(plot_bgcolor=p["superficie"])
    return fig


def fig_calidad_mes(df: pd.DataFrame, p: dict, sub: str) -> go.Figure:
    titulo = "Observaciones interpoladas y winsorizadas por mes"
    if df.empty:
        return _vacio(p, titulo, "Sin datos para los filtros elegidos")
    colores = colores_estado(p)
    c = df.groupby(["fecha", "estado_dato"]).size().unstack(fill_value=0)
    fig = go.Figure()
    for e in ["Interpolado", "Winsorizado", "Interpolado y winsorizado"]:
        if e in c and c[e].sum() > 0:
            fig.add_trace(go.Bar(x=c.index, y=c[e], name=e, marker=dict(color=colores[e], line=dict(width=0)),
                                 hovertemplate="%{x|%Y-%m}: %{y} filas · " + e.lower() + "<extra></extra>"))
    if not fig.data:
        return _vacio(p, titulo, "Ninguna observación interpolada ni winsorizada en el filtro")
    estilo(fig, p, titulo, sub, alto=330)
    fig.update_layout(barmode="stack", bargap=0.2)
    fig.update_yaxes(title_text="Filas")
    fechas_es(fig, c.index)
    return fig


def _alfa(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def para_exportar(fig: go.Figure, nota: str) -> go.Figure:
    """Copia con nota de fuente y filtros al pie, lista para PNG."""
    f = go.Figure(fig)
    alto = int(f.layout.height or 420) + 56
    m = f.layout.margin
    inferior = 118
    zona = alto - (m.t or 0) - inferior          # alto del área de trazado en píxeles
    f.update_layout(height=alto, margin=dict(l=m.l, r=m.r, t=m.t, b=inferior))
    f.add_annotation(text=nota, x=0, xref="paper", y=-(inferior - 10) / zona, yref="paper", yanchor="bottom",
                     xanchor="left", showarrow=False, align="left", font=dict(size=10, color=PALETAS["light"]["texto2"]))
    return f
