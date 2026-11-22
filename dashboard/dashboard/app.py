"""Dashboard · Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo.

Tema 79 · Finanzas I (055D) · UNCP · Amy Pamela Guadalupe Cordova (2024200501G).
Lee exclusivamente los archivos reales del proyecto (datos_procesados/ y
salidas/) en modo de solo lectura. Ejecutar desde la raíz del repositorio:
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Los módulos del dashboard viven junto a este archivo (ejecución desde cualquier carpeta).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import datos  # noqa: E402
import descargas as dl  # noqa: E402
import econometria as eco  # noqa: E402
import graficos as gr  # noqa: E402
import metricas as mt  # noqa: E402

st.set_page_config(
    page_title="Fondos mutuos en el Perú · Dashboard",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="auto",
)

MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
CLAVES_FILTRO = ["f_tipos", "f_moneda", "f_admin", "f_series", "f_periodo", "f_retorno", "f_vista", "f_resaltar"]
# Nota: el periodo se guarda en f_periodo (no es un widget). El control deslizante se
# crea con value= y una clave versionada; así se evita un error de Streamlit 1.51 con
# deslizantes de rango cuyo valor se fija desde session_state.
CLAVES_PREPARADAS = ["prep_png", "prep_zip_png", "prep_reporte", "prep_xlsx", "slots_series", "sel_anio", "rob_var", "png_sel"]


def mes_corto(m):
    if isinstance(m, (tuple, list)):  # AppTest pasa el rango completo al formateador
        return tuple(mes_corto(x) for x in m)
    a, mm = m.split("-")
    return f"{MESES_ES[int(mm) - 1]} {a}"


def pct(v, dec=2) -> str:
    return "n.d." if v is None or pd.isna(v) else f"{100 * v:.{dec}f} %"


def num(v, dec=3) -> str:
    return "n.d." if v is None or pd.isna(v) else f"{v:.{dec}f}"


# ---------------------------------------------------------------------------
# Datos (caché invalidada por tamaño y fecha de los archivos)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando el panel de la investigación…")
def cargar_panel(ruta: str, firma: str) -> pd.DataFrame:
    return datos.cargar_panel(Path(ruta))


@st.cache_data(show_spinner=False)
def cargar_tabla(ruta: str, nombre: str, firma: str):
    return datos.cargar_tabla(Path(ruta), nombre)


@st.cache_data(show_spinner=False)
def sha_procesado(ruta: str, firma: str) -> str:
    return datos.sha256(Path(ruta))


@st.cache_data(show_spinner=False)
def diccionario(ruta: str, firma: str):
    return datos.diccionario_variables(Path(ruta))


try:
    RAIZ = datos.localizar_proyecto()
    RUTA_PROC = datos.ruta_procesado(RAIZ)
    FIRMA = datos.firma_archivo(RUTA_PROC)
    PANEL = cargar_panel(str(RAIZ), FIRMA)
except datos.ErrorDatos as e:
    st.error(f"No se pudo cargar la base de la investigación: {e}")
    st.stop()


def tabla(nombre: str):
    return cargar_tabla(str(RAIZ), nombre, FIRMA)


MESES = sorted(PANEL.mes.unique())
TIPOS = [t for t in gr.ORDEN_TIPOS if t in set(PANEL.tipo)]
MONEDAS = [m for m in gr.ORDEN_MONEDAS if m in set(PANEL.moneda)]
ETIQUETAS = PANEL.drop_duplicates("id_fondo_serie").set_index("id_fondo_serie").etiqueta.to_dict()

# ---------------------------------------------------------------------------
# Estado de filtros y restablecimiento
# ---------------------------------------------------------------------------
DEFAULTS = {
    "f_tipos": [], "f_moneda": "Ambas", "f_admin": [], "f_series": [],
    "f_periodo": (MESES[0], MESES[-1]), "f_retorno": "tratada", "f_vista": "categoria",
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("v_periodo", 0)
if st.session_state.f_periodo[0] not in MESES or st.session_state.f_periodo[1] not in MESES:
    st.session_state.f_periodo = (MESES[0], MESES[-1])


def restablecer():
    version = st.session_state.get("v_periodo", 0) + 1
    for k in CLAVES_FILTRO + CLAVES_PREPARADAS:
        st.session_state.pop(k, None)
    st.session_state.v_periodo = version


def fijar_periodo(ini: str, fin: str):
    st.session_state.f_periodo = (ini, fin)
    st.session_state.v_periodo = st.session_state.get("v_periodo", 0) + 1


def leer_deslizador():
    st.session_state.f_periodo = tuple(st.session_state[f"deslizador_{st.session_state.v_periodo}"])


def fijar_anio():
    año = st.session_state.get("sel_anio", "—")
    meses_año = [m for m in MESES if m.startswith(año)]
    if meses_año:
        fijar_periodo(meses_año[0], meses_año[-1])
    st.session_state.sel_anio = "—"


# ---------------------------------------------------------------------------
# Tema visual (claro/oscuro según la configuración de Streamlit del usuario)
# ---------------------------------------------------------------------------
try:
    MODO = st.context.theme.type or "light"
except Exception:  # versiones sin st.context.theme
    MODO = "light"
P = gr.PALETAS.get(MODO, gr.PALETAS["light"])
PCLARO = gr.PALETAS["light"]
borde = "#e3e2dd" if MODO == "light" else "#34342f"
chip = "#f1f0ec" if MODO == "light" else "#2a2a27"

st.markdown(
    f"""
<style>
.block-container{{padding-top:1.4rem;padding-bottom:3rem;max-width:1400px}}
.fm-hero{{background:linear-gradient(135deg,#0e2741 0%,#17426e 60%,#1f5a93 100%);color:#f5f7fa;border-radius:16px;padding:22px 26px;margin-bottom:14px}}
.fm-hero h1{{font-size:clamp(1.25rem,2.4vw,1.85rem);margin:0 0 4px;color:#fff;font-weight:700;letter-spacing:-.01em}}
.fm-hero p{{margin:0;color:#c9d6e6;font-size:.95rem}}
.fm-chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.fm-chips span{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:3px 11px;font-size:.78rem;color:#eef3f9}}
.fm-moneda{{font-weight:650;font-size:.95rem;margin:10px 0 6px;color:{P['texto']}}}
.fm-moneda small{{font-weight:400;color:{P['texto2']};margin-left:6px}}
.fm-kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:10px;margin-bottom:6px}}
.fm-card{{background:{P['superficie']};border:1px solid {borde};border-radius:12px;padding:12px 14px}}
.fm-card .l{{font-size:.76rem;color:{P['texto2']};line-height:1.25;min-height:1.9em}}
.fm-card .v{{font-size:1.45rem;font-weight:680;color:{P['texto']};font-variant-numeric:tabular-nums;margin-top:2px}}
.fm-card .t{{display:inline-block;font-size:.66rem;padding:1px 7px;border-radius:999px;background:{chip};color:{P['texto2']};margin-top:4px}}
.fm-leyenda{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}}
.fm-leyenda div{{border:1px solid {borde};border-radius:12px;padding:10px 12px;font-size:.84rem;color:{P['texto2']}}}
.fm-leyenda b{{color:{P['texto']}}}
.fm-sw{{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
@media (max-width:640px){{.fm-hero{{padding:16px}} .fm-card .v{{font-size:1.2rem}}}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Barra lateral: filtros en cascada
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Filtros")
    st.button("Restablecer filtros", on_click=restablecer, icon=":material/restart_alt:", width="stretch")

    st.multiselect("Tipo de fondo", TIPOS, key="f_tipos", placeholder="Todos los tipos")
    st.radio("Moneda", ["Ambas"] + MONEDAS, key="f_moneda", horizontal=True,
             format_func=lambda m: "Ambas" if m == "Ambas" else m,
             help="PEN = soles, USD = dólares. Con «Ambas», cada moneda se muestra en su propio panel: las rentabilidades "
                  "en soles y en dólares nunca se promedian entre sí.")
    st.session_state.f_monedas = [] if st.session_state.f_moneda == "Ambas" else [st.session_state.f_moneda]

    base = PANEL
    if st.session_state.f_tipos:
        base = base[base.tipo.isin(st.session_state.f_tipos)]
    if st.session_state.f_monedas:
        base = base[base.moneda.isin(st.session_state.f_monedas)]
    opc_admin = sorted(base.administradora.unique())
    st.session_state.f_admin = [a for a in st.session_state.f_admin if a in opc_admin]
    st.multiselect("Administradora", opc_admin, key="f_admin", placeholder="Todas las administradoras")
    if st.session_state.f_admin:
        base = base[base.administradora.isin(st.session_state.f_admin)]
    opc_series = sorted(base.id_fondo_serie.unique(), key=lambda i: ETIQUETAS[i])
    st.session_state.f_series = [s for s in st.session_state.f_series if s in opc_series]
    st.multiselect("Fondos-series", opc_series, key="f_series", format_func=lambda i: ETIQUETAS[i],
                   placeholder=f"Todos ({len(opc_series)})",
                   help="Elige uno o varios para compararlos. Vacío = todos los que cumplen los filtros anteriores.")

    st.radio("Serie de retorno", ["tratada", "original"], key="f_retorno",
             format_func=lambda x: {"tratada": "Tratada (winsorizada · investigación)", "original": "Original (antes de winsorizar)"}[x],
             help="La serie tratada recorta los extremos con límites de Tukey (Q1−3·RIQ, Q3+3·RIQ) por tipo y moneda. La original es el retorno publicado o, si fue interpolado, el estimado.")
    st.radio("Nivel de los gráficos", ["categoria", "serie"], key="f_vista",
             format_func=lambda x: {"categoria": "Por tipo de fondo", "serie": "Por fondo-serie (hasta 8)"}[x])

    st.divider()
    n_series_total = PANEL.id_fondo_serie.nunique()
    st.caption(
        f"**Panel balanceado:** {n_series_total} fondos-series × {len(MESES)} meses = {len(PANEL)} observaciones "
        f"mensuales ({mes_corto(MESES[0])} – {mes_corto(MESES[-1])}). Tipos en el panel: {', '.join(TIPOS)}. "
        "ETF y Estructurados figuran solo en el análisis contextual (pestaña Calidad de datos)."
    )

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
sha = sha_procesado(str(RUTA_PROC), FIRMA)
st.markdown(
    f"""
<div class="fm-hero">
  <h1>Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo</h1>
  <p>Tema 79 · Finanzas I · UNCP · Panel mensual construido con boletines de la AAF y la API de BCRPData</p>
  <div class="fm-chips">
    <span>{n_series_total} fondos-series</span><span>{len(MESES)} meses comunes</span><span>{len(PANEL)} observaciones</span>
    <span>Frecuencia mensual</span><span>{mes_corto(MESES[0])} – {mes_corto(MESES[-1])}</span>
    <span title="SHA-256 del archivo procesado">SHA-256 {sha[:12]}…</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Línea de tiempo (sustituye al mapa del video de referencia)
# ---------------------------------------------------------------------------
f_sin_periodo = mt.Filtros(tuple(st.session_state.f_tipos), tuple(st.session_state.f_monedas),
                           tuple(st.session_state.f_admin), tuple(st.session_state.f_series),
                           MESES[0], MESES[-1], st.session_state.f_retorno)
df_todo = mt.aplicar_filtros(PANEL, f_sin_periodo, con_periodo=False)
ini, fin = st.session_state.f_periodo
lt = mt.linea_tiempo(df_todo, st.session_state.f_retorno)
CFG = lambda nombre: {  # noqa: E731
    "displaylogo": False, "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 3, "filename": f"{nombre}_{ini}_{fin}"},
}
with st.container(border=True):
    st.plotly_chart(gr.fig_linea_tiempo(lt, ini, fin, P), config=CFG("linea_tiempo"), key="g_linea", theme=None)
    st.select_slider("Arrastra los extremos para elegir el mes inicial y el mes final", options=MESES,
                     value=tuple(st.session_state.f_periodo), format_func=mes_corto,
                     key=f"deslizador_{st.session_state.v_periodo}", on_change=leer_deslizador)
    b = st.columns(5)
    b[0].button("Todo el periodo", on_click=fijar_periodo, args=(MESES[0], MESES[-1]), width="stretch")
    b[1].button("Últimos 12 meses", on_click=fijar_periodo, args=(MESES[-12], MESES[-1]), width="stretch", disabled=len(MESES) < 12)
    b[2].button("Últimos 36 meses", on_click=fijar_periodo, args=(MESES[-36], MESES[-1]), width="stretch", disabled=len(MESES) < 36)
    b[3].button("Primeros 24 meses", on_click=fijar_periodo, args=(MESES[0], MESES[23]), width="stretch", disabled=len(MESES) < 24)
    años = sorted({m[:4] for m in MESES})
    b[4].selectbox("Año calendario", ["—"] + años, label_visibility="collapsed", key="sel_anio",
                   on_change=fijar_anio, help="Atajo: fija la línea de tiempo en un año calendario")

ini, fin = st.session_state.f_periodo
F = mt.Filtros(tuple(st.session_state.f_tipos), tuple(st.session_state.f_monedas), tuple(st.session_state.f_admin),
               tuple(st.session_state.f_series), ini, fin, st.session_state.f_retorno)
DF = mt.aplicar_filtros(PANEL, F)
if DF.empty:
    st.warning("Ningún fondo-serie cumple los filtros elegidos. Amplía la selección o pulsa «Restablecer filtros».")
    st.stop()

RET = F.retorno
N_MESES = DF.mes.nunique()
M = mt.metricas_por_serie(DF, RET)
RES = mt.resumen_por_categoria(M)
DESC = mt.descriptivos(DF, RET)
CAT = mt.rent_mensual_categoria(DF, RET)
CAL = mt.calidad(DF)
etiqueta_ret = "serie tratada" if RET == "tratada" else "serie original (sin winsorizar)"
SUB = f"{mes_corto(ini)} – {mes_corto(fin)} · {N_MESES} meses · {DF.id_fondo_serie.nunique()} series · {etiqueta_ret}"

# Vista por fondo-serie: máximo 8 colores, asignados de forma estable
vista = st.session_state.f_vista
ids = sorted(DF.id_fondo_serie.unique())
if vista == "serie" and len(ids) > 8:
    st.info(f"La vista por fondo-serie admite hasta 8 series a la vez (hay {len(ids)}). Se muestra la vista por tipo de fondo; "
            "elige hasta 8 fondos-series en la barra lateral para verlos individualmente.", icon=":material/info:")
    vista = "categoria"
COLORES = {}
if vista == "serie":
    slots = {k: v for k, v in st.session_state.get("slots_series", {}).items() if k in ids}
    libres = [i for i in range(8) if i not in slots.values()]
    for i in ids:
        if i not in slots:
            slots[i] = libres.pop(0)
    st.session_state.slots_series = slots
    COLORES = {i: (s, P["slots"][s]) for i, s in slots.items()}
    COLORES_CLARO = {i: (s, PCLARO["slots"][s]) for i, s in slots.items()}
else:
    COLORES_CLARO = {}

if N_MESES < mt.MIN_MESES:
    st.info(f"El periodo elegido tiene {N_MESES} meses. Igual que en la investigación, la rentabilidad anualizada, la volatilidad "
            f"anualizada y el Sharpe se calculan solo con al menos {mt.MIN_MESES} meses; se muestran la rentabilidad acumulada, "
            "la máxima caída y los estadísticos mensuales.", icon=":material/info:")

# ---------------------------------------------------------------------------
# Indicadores principales (siempre por moneda)
# ---------------------------------------------------------------------------
KPI = mt.kpis_por_moneda(DF, M)
for _, k in KPI.iterrows():
    tarjetas = [
        ("Rentabilidad acumulada (mediana entre series)", pct(k.rent_acumulada_mediana), "calculado · compuesto"),
        ("Rentabilidad anualizada (mediana)", pct(k.rent_anualizada_mediana), "calculado"),
        ("Volatilidad anualizada (mediana)", pct(k.vol_anualizada_mediana), "calculado"),
        ("Sharpe anualizado (mediana)", num(k.sharpe_mediana, 2), "calculado · vs. interbancaria"),
        ("Máxima caída (mediana)", pct(k.max_caida_mediana), "calculado · dashboard"),
        ("Interpoladas / winsorizadas", f"{pct(k.pct_interpoladas, 1)} / {pct(k.pct_winsorizadas, 1)}", "calidad de datos"),
    ]
    html_cards = "".join(f"<div class='fm-card'><div class='l'>{a}</div><div class='v'>{b}</div><span class='t'>{c}</span></div>" for a, b, c in tarjetas)
    st.markdown(
        f"<div class='fm-moneda'>{gr.NOMBRE_MONEDA[k.moneda]}<small>{int(k.series)} series · {int(k.meses)} meses · "
        f"{int(k.observaciones)} observaciones</small></div><div class='fm-kpis'>{html_cards}</div>",
        unsafe_allow_html=True,
    )

# Registro de gráficos para la descarga PNG (se reconstruyen con la paleta clara)
REG: dict[str, tuple[str, callable]] = {}


def mostrar(nombre: str, titulo: str, constructor, nota: str | None = None):
    """Dibuja el gráfico con la paleta activa y lo registra para exportarlo."""
    fig = constructor(P)
    st.plotly_chart(fig, config=CFG(nombre), key=f"g_{nombre}", theme=None)
    REG[nombre] = (titulo, constructor)
    if nota:
        st.caption(nota)


tabs = st.tabs([":material/show_chart: Evolución", ":material/speed: Riesgo y desempeño",
                ":material/compare_arrows: Categorías y fondos", ":material/table_chart: Estadísticos",
                ":material/functions: Econometría", ":material/fact_check: Calidad de datos",
                ":material/download: Descargas"])

# ---------------------------------------------------------------------------
# 1. Evolución
# ---------------------------------------------------------------------------
with tabs[0]:
    SER = DF if vista == "serie" else None
    mostrar("rentabilidad_mensual", "Evolución mensual de la rentabilidad",
            lambda p: gr.fig_rent_mensual(CAT, SER, vista, RET, p, COLORES if p is P else COLORES_CLARO, SUB),
            "Rentabilidad mensual publicada por la AAF (observada), estimada si fue interpolada y recortada si fue winsorizada. "
            + ("Por tipo: promedio simple entre las series del filtro (igual peso, no por patrimonio). " if vista == "categoria" else
               "Marcas: ○ interpolado · × winsorizado · ◇ ambos. ")
            + "Datos mensuales; no se generan observaciones diarias.")
    IND = mt.indice_acumulado(DF, RET, vista)
    mostrar("rentabilidad_acumulada", "Rentabilidad acumulada (base 100)",
            lambda p: gr.fig_acumulada(IND, vista, p, COLORES if p is P else COLORES_CLARO, SUB),
            "Calculado: índice = 100 × ∏(1 + r) desde el inicio del periodo elegido. "
            + ("Cada línea por tipo es una cartera de igual ponderación rebalanceada mensualmente." if vista == "categoria" else ""))

# ---------------------------------------------------------------------------
# 2. Riesgo y desempeño ajustado por riesgo
# ---------------------------------------------------------------------------
with tabs[1]:
    VOL = mt.volatilidad_historica(DF, RET, vista)
    mostrar("volatilidad_historica", "Volatilidad histórica móvil",
            lambda p: gr.fig_volatilidad(VOL, vista, p, COLORES if p is P else COLORES_CLARO, SUB),
            "Variable X1 de la investigación (vol12): desviación muestral de los 12 meses previos (mínimo 6), multiplicada por √12. "
            + ("Por tipo: mediana entre series." if vista == "categoria" else ""))
    CAI = mt.caidas(IND, ["tipo", "moneda"] if vista == "categoria" else ["id_fondo_serie"])
    mostrar("caidas", "Caída desde el máximo previo",
            lambda p: gr.fig_caidas(CAI, vista, p, COLORES if p is P else COLORES_CLARO, SUB),
            "Calculado en el dashboard (no forma parte de las tablas de la investigación).")

    tipos_m = [t for t in gr.ORDEN_TIPOS if t in set(M.dropna(subset=['vol_anualizada']).tipo)]
    if tipos_m:
        if st.session_state.get("f_resaltar") not in tipos_m:
            st.session_state.f_resaltar = tipos_m[0]
        st.radio("Resaltar tipo de fondo en la dispersión", tipos_m, key="f_resaltar", horizontal=True)
        resaltar = st.session_state.f_resaltar or tipos_m[0]
        mostrar("dispersion_riesgo_rentabilidad", "Dispersión riesgo-rentabilidad",
                lambda p: gr.fig_dispersion(M, resaltar, p, SUB + f" · resaltado: {resaltar}"),
                "Cada punto es un fondo-serie del filtro (calculado con ≥ 12 meses). Se resalta un tipo y el resto queda en gris para "
                "que los colores se distingan con cualquier visión; pasa el cursor sobre un punto para ver su nombre y su Sharpe.")
    else:
        st.info("La dispersión riesgo-rentabilidad necesita al menos 12 meses en la línea de tiempo.")

    st.markdown("##### Desempeño ajustado por riesgo por fondo-serie")
    vista_m = M.copy()
    for c in ["rent_acumulada", "rent_anualizada", "vol_anualizada", "max_caida", "meses_con_perdida"]:
        vista_m[c] = 100 * vista_m[c]
    st.dataframe(
        vista_m.drop(columns=["id_fondo_serie"]).sort_values(["moneda", "tipo", "sharpe_anualizado"], ascending=[True, True, False]),
        hide_index=True, width="stretch",
        column_config={
            "etiqueta": st.column_config.TextColumn("Fondo-serie", width="large"), "tipo": "Tipo", "moneda": "Moneda",
            "administradora": "Administradora", "mes_inicio": "Desde", "mes_fin": "Hasta", "n_meses": "Meses",
            "rent_acumulada": st.column_config.NumberColumn("Rent. acumulada (%)", format="%.2f"),
            "rent_anualizada": st.column_config.NumberColumn("Rent. anualizada (%)", format="%.2f"),
            "vol_anualizada": st.column_config.NumberColumn("Vol. anualizada (%)", format="%.2f"),
            "sharpe_anualizado": st.column_config.NumberColumn("Sharpe", format="%.3f"),
            "sortino_anualizado": st.column_config.NumberColumn("Sortino", format="%.3f"),
            "max_caida": st.column_config.NumberColumn("Máx. caída (%)", format="%.2f"),
            "meses_con_perdida": st.column_config.NumberColumn("Meses con pérdida (%)", format="%.1f"),
            "meses_interpolados": "Meses interpolados", "meses_winsorizados": "Meses winsorizados",
        },
    )
    with st.expander("Definiciones de las medidas"):
        st.markdown(
            "- **Rentabilidad anualizada** = exp(12 × media de ln(1 + r)) − 1 · igual que la investigación.\n"
            "- **Volatilidad anualizada** = desviación muestral de r × √12 · igual que la investigación.\n"
            "- **Sharpe** = media del exceso / desviación del exceso × √12; exceso = r − tasa interbancaria mensual de la "
            "misma moneda (BCRPData). La tasa es una aproximación, no un activo libre de riesgo invertible.\n"
            "- **Sortino** (dashboard) = media del exceso / desviación a la baja del exceso × √12.\n"
            "- **Máxima caída** (dashboard) = mayor descenso del índice acumulado respecto de su máximo previo.\n"
            "- Las medidas anualizadas exigen al menos 12 meses, como en la investigación. Con autocorrelación, multiplicar por √12 es una convención."
        )

# ---------------------------------------------------------------------------
# 3. Categorías y fondos
# ---------------------------------------------------------------------------
with tabs[2]:
    mostrar("sharpe_por_tipo", "Sharpe por tipo de fondo",
            lambda p: gr.fig_sharpe_categorias(RES, p, SUB),
            "Mediana e intervalo intercuartílico del Sharpe entre los fondos-series de cada tipo y moneda (igual peso por serie).")
    st.markdown("##### Comparación de categorías y monedas")
    if not RES.empty:
        r = RES.copy()
        for c in ["rent_acumulada_mediana", "rent_mediana", "vol_mediana", "max_caida_mediana", "meses_perdida_mediana"]:
            r[c] = 100 * r[c]
        st.dataframe(r, hide_index=True, width="stretch", column_config={
            "tipo": "Tipo", "moneda": "Moneda", "unidades": "Series",
            "rent_acumulada_mediana": st.column_config.NumberColumn("Rent. acumulada (%)", format="%.2f"),
            "rent_mediana": st.column_config.NumberColumn("Rent. anualizada (%)", format="%.2f"),
            "vol_mediana": st.column_config.NumberColumn("Vol. anualizada (%)", format="%.2f"),
            "sharpe_mediana": st.column_config.NumberColumn("Sharpe (mediana)", format="%.3f"),
            "sharpe_q25": st.column_config.NumberColumn("Sharpe Q1", format="%.3f"),
            "sharpe_q75": st.column_config.NumberColumn("Sharpe Q3", format="%.3f"),
            "sortino_mediana": st.column_config.NumberColumn("Sortino", format="%.3f"),
            "max_caida_mediana": st.column_config.NumberColumn("Máx. caída (%)", format="%.2f"),
            "meses_perdida_mediana": st.column_config.NumberColumn("Meses con pérdida (%)", format="%.1f"),
        })
        st.caption("Medianas entre fondos-series. Los grupos con 2 o 3 series son descriptivos; no permiten inferencia.")
    mostrar("distribucion_mensual", "Distribución de la rentabilidad mensual",
            lambda p: gr.fig_caja(DF, RET, p, SUB),
            "Cajas: mediana y cuartiles de la rentabilidad mensual; bigotes hasta 1,5 × RIQ; puntos fuera de ese rango.")
    titulo_rank = f"Comparación de los {len(ids)} fondos-series elegidos" if st.session_state.f_series else "Comparación de fondos-series"
    st.markdown(f"##### {titulo_rank}")
    mostrar("ranking_sharpe", "Ranking de Sharpe por fondo-serie",
            lambda p: gr.fig_ranking_sharpe(M, p, SUB),
            "Elige fondos-series en la barra lateral para compararlos directamente. Cada moneda se ordena por separado.")

# ---------------------------------------------------------------------------
# 4. Estadísticos
# ---------------------------------------------------------------------------
with tabs[3]:
    st.markdown("##### Estadísticos descriptivos de la rentabilidad mensual")
    d = DESC.copy()
    for c in ["media", "mediana", "desv", "p05", "p95", "minimo", "maximo"]:
        d[c] = 100 * d[c]
    st.dataframe(d, hide_index=True, width="stretch", column_config={
        "tipo": "Tipo", "moneda": "Moneda", "n": "Observaciones", "series": "Series",
        **{c: st.column_config.NumberColumn(n_, format="%.3f") for c, n_ in
           [("media", "Media (%)"), ("mediana", "Mediana (%)"), ("desv", "Desv. estándar (%)"), ("p05", "P5 (%)"),
            ("p95", "P95 (%)"), ("minimo", "Mínimo (%)"), ("maximo", "Máximo (%)")]},
    })
    st.caption(f"Rentabilidad mensual en porcentaje ({etiqueta_ret}). Sin filtros reproduce salidas/tabla16_descriptivos.csv.")
    st.markdown("##### Observaciones filtradas")
    cols_vista = ["mes", "etiqueta", "tipo", "moneda", "administradora", "estado_dato", "valor_cuota", "rent_original", "rent_mes",
                  "rf_mensual", "exceso", "vol12", "rent_lag1", "var_tc", "tc_fin", "archivo", "pagina"]
    st.dataframe(DF[cols_vista], hide_index=True, width="stretch", height=360, column_config={
        "etiqueta": st.column_config.TextColumn("Fondo-serie", width="medium"),
        "estado_dato": "Estado del dato",
        "rent_original": st.column_config.NumberColumn("rent_original", format="%.4f", help="Decimal; 0,01 = 1 %"),
        "rent_mes": st.column_config.NumberColumn("rent_mes (Y)", format="%.4f", help="Decimal, tras winsorizar"),
        "rf_mensual": st.column_config.NumberColumn(format="%.6f"), "exceso": st.column_config.NumberColumn(format="%.5f"),
        "vol12": st.column_config.NumberColumn("vol12 (X1)", format="%.5f"), "rent_lag1": st.column_config.NumberColumn("rent_lag1 (X3)", format="%.4f"),
        "var_tc": st.column_config.NumberColumn("var_tc (X2)", format="%.5f"), "tc_fin": st.column_config.NumberColumn("TC fin (S/ por US$)", format="%.4f"),
    })
    st.caption(f"{len(DF)} filas. Columnas en decimal, tal como en datos_procesados. «Estado del dato» distingue observado, interpolado y winsorizado.")

# ---------------------------------------------------------------------------
# 5. Econometría
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Reestimando el modelo con los filtros…")
def estimar_filtrado(firma_filtros: str, firma_datos: str, _df: pd.DataFrame, retorno: str):
    return eco.estimar(_df, retorno)


with tabs[4]:
    T3 = tabla("tabla3_modelo_principal")
    EST = estimar_filtrado(F.firma(), FIRMA, DF, RET)
    filtro_completo = len(DF) == len(PANEL)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Panel completo · resultado oficial")
        if T3 is not None:
            st.markdown(f"MCO · errores agrupados por fondo-serie y mes · n = {int(T3.n.iloc[0])} · "
                        f"{int(T3.fondos_series.iloc[0])} series · {int(T3.meses.iloc[0])} meses · R² = {T3.r2.iloc[0]:.3f}")
        else:
            st.warning("No se encontró salidas/tabla3_modelo_principal.csv.")
    with c2:
        st.markdown("##### Subconjunto filtrado · reestimación exploratoria")
        if EST["ok"]:
            st.markdown(f"Misma especificación · n = {EST['n']} · {EST['series']} series · {EST['meses']} meses · "
                        f"R² = {EST['r2']:.3f} · gl de la t = {EST['gl']}")
        for a in EST["advertencias"]:
            st.warning(a, icon=":material/warning:")
        if filtro_completo and RET == "tratada" and EST["ok"]:
            st.success("Sin filtros: la reestimación reproduce la tabla 3 oficial.", icon=":material/check_circle:")
    mostrar("coeficientes", "Coeficientes del modelo",
            lambda p: gr.fig_coeficientes(T3, EST["tabla"] if EST["ok"] else None, p,
                                          "rent_mes ~ vol12 + var_tc + rent_lag1 + C(tipo) + C(moneda) · IC 95 % agrupados en dos vías"),
            None)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Lectura del resultado oficial (panel completo)**")
        if T3 is not None:
            for t in eco.interpretar(T3):
                st.markdown("- " + t)
    with c2:
        st.markdown("**Lectura de la reestimación con los filtros activos**")
        if EST["ok"]:
            for t in eco.interpretar(EST["tabla"]):
                st.markdown("- " + t)
        else:
            st.caption("No estimable con los filtros actuales.")
    st.info(eco.ADVERTENCIA_GENERAL, icon=":material/balance:")

    tabla_cfg = {c: st.column_config.NumberColumn(format="%.5f") for c in ["coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup"]}
    with st.expander("Tabla de coeficientes: reestimación filtrada"):
        if EST["ok"]:
            st.dataframe(EST["tabla"], hide_index=True, width="stretch", column_config=tabla_cfg)
            st.caption(f"Fórmula: {EST['formula']}")
    with st.expander("Tabla 3 oficial y modelo MCO clásico (tabla 4)"):
        if T3 is not None:
            st.dataframe(T3[["variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup"]], hide_index=True,
                         width="stretch", column_config=tabla_cfg)
        T4 = tabla("tabla4_modelo_inicial_mco")
        if T4 is not None:
            st.caption("Errores MCO clásicos (referencia; la inferencia principal usa errores agrupados):")
            st.dataframe(T4, hide_index=True, width="stretch")

    st.markdown("##### Robustez del resultado principal (panel completo, referencia fija)")
    T5, T12, T13 = tabla("tabla5_robustez"), tabla("tabla12_efectos_fijos"), tabla("tabla13_sensibilidad_inferencia")
    st.session_state.setdefault("rob_var", "var_tc")
    var_rob = st.radio("Coeficiente", eco.FACTORES, key="rob_var", horizontal=True)
    filas = []
    if T5 is not None:
        nombres5 = {"principal_cluster_fondo_mes": "Principal (dos vías)", "misma_muestra_sin_winsorizar": "Sin winsorizar",
                    "sin_imputacion_actual_ni_historica": "Sin filas interpoladas"}
        for k, v in nombres5.items():
            x = T5[(T5.modelo == k) & (T5.variable == var_rob)]
            if len(x):
                filas.append({"especificacion": v, **x.iloc[0][["coeficiente", "ic95_inf", "ic95_sup", "p_valor"]].to_dict()})
    if T13 is not None:
        for k, v in {"serie": "Agrupado solo por serie", "mes": "Agrupado solo por mes"}.items():
            x = T13[(T13.agrupacion == k) & (T13.variable == var_rob)]
            if len(x):
                filas.append({"especificacion": v, **x.iloc[0][["coeficiente", "ic95_inf", "ic95_sup", "p_valor"]].to_dict()})
    if T12 is not None:
        x = T12[(T12.modelo == "efectos_fijos") & (T12.agrupacion == "serie_mes") & (T12.variable == var_rob)]
        if len(x):
            filas.append({"especificacion": "Efectos fijos de serie", **x.iloc[0][["coeficiente", "ic95_inf", "ic95_sup", "p_valor"]].to_dict()})
    ESPEC = pd.DataFrame(filas)
    mostrar("robustez", "Robustez del coeficiente",
            lambda p: gr.fig_robustez(ESPEC, p, var_rob, "Panel completo · tablas 3, 5, 12 y 13 de salidas/"),
            "Resultados oficiales del panel completo: no dependen de los filtros. Sirven para juzgar si el signo y la magnitud se mantienen.")
    T14 = tabla("tabla14_contrastes_tipo")
    if T14 is not None:
        t14 = T14.copy()
        if F.monedas:
            t14 = t14[t14.moneda.isin(F.monedas)]
        if F.tipos:
            t14 = t14[t14.tipo.isin(F.tipos) | t14.referencia.isin(F.tipos)]
        st.markdown("##### Contrastes de exceso mensual frente a Deuda (oficial, panel completo)")
        st.dataframe(t14, hide_index=True, width="stretch")
        st.caption("Diferencia de medianas mensuales del exceso, HAC(3) y corrección de Holm. Filtrado por tipo y moneda; "
                   "el periodo es el del panel completo. Exploratorio, no causal.")
    with st.expander("Diagnósticos (VIF y correlación residual)"):
        for n_ in ["tabla6_vif", "tabla7_diagnosticos"]:
            t = tabla(n_)
            if t is not None:
                st.dataframe(t, hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# 6. Calidad de datos
# ---------------------------------------------------------------------------
with tabs[5]:
    ce = gr.colores_estado(P)
    st.markdown(
        f"""<div class="fm-leyenda">
<div><span class="fm-sw" style="background:{ce['Observado']};border:1px solid {borde}"></span><b>Observado</b><br>Valor publicado en el boletín AAF (cuota, rentabilidad) o en BCRPData (TC, tasas).</div>
<div><span class="fm-sw" style="background:{P['texto2']}"></span><b>Calculado</b><br>Derivado por código: exceso, vol12, rent_lag1, var_tc, rf y todas las métricas del dashboard.</div>
<div><span class="fm-sw" style="background:{ce['Interpolado']}"></span><b>Interpolado</b><br>Hueco interior de 1 a 3 meses estimado geométricamente (imputado = 1). No es un dato publicado.</div>
<div><span class="fm-sw" style="background:{ce['Winsorizado']}"></span><b>Winsorizado</b><br>Retorno recortado al límite de Tukey de su tipo y moneda (atipico = 1). El original se conserva en rent_original.</div>
</div>""",
        unsafe_allow_html=True,
    )
    st.write("")
    q = st.columns(6)
    q[0].metric("Filas", CAL["filas"])
    q[1].metric("Observadas", CAL["observadas"])
    q[2].metric("Interpoladas", CAL["interpoladas"], help="Incluye las que además fueron winsorizadas")
    q[3].metric("Winsorizadas", CAL["winsorizadas"], help="Incluye las que además fueron interpoladas")
    q[4].metric("Faltantes", CAL["faltantes"])
    q[5].metric("Duplicados", int(DF.duplicated(["id_fondo_serie", "mes"]).sum()))
    mostrar("calidad_por_mes", "Interpoladas y winsorizadas por mes", lambda p: gr.fig_calidad_mes(DF, p, SUB))
    mostrar("mapa_calidad", "Mapa de calidad", lambda p: gr.fig_calidad_mapa(DF, p, SUB))

    st.markdown("##### Filas interpoladas o winsorizadas en el filtro")
    LIM = tabla("tabla_limites_tukey")
    tratadas = DF[DF.estado_dato.ne("Observado")]
    if LIM is not None:
        tratadas = tratadas.merge(LIM[["tipo", "moneda", "lim_inf", "lim_sup"]], on=["tipo", "moneda"], how="left")
    cols_t = [c for c in ["mes", "etiqueta", "tipo", "moneda", "estado_dato", "rent_original", "rent_mes", "lim_inf", "lim_sup",
                          "valor_cuota", "archivo", "pagina", "fila_original"] if c in tratadas]
    st.dataframe(tratadas[cols_t], hide_index=True, width="stretch", height=300)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Límites de Tukey (Q1 − 3·RIQ, Q3 + 3·RIQ)")
        if LIM is not None:
            lim = LIM[LIM.tipo.isin(DF.tipo.unique()) & LIM.moneda.isin(DF.moneda.unique())]
            st.dataframe(lim, hide_index=True, width="stretch")
            st.caption("Calculados con registros observados (no interpolados) por tipo y moneda.")
    with c2:
        st.markdown("##### Alertas de coherencia cuota-rentabilidad")
        T9 = tabla("tabla9_auditoria_financiera")
        if T9 is not None:
            t9 = T9[T9.id_fondo_serie.isin(DF.id_fondo_serie.unique()) & T9.mes.between(ini, fin)]
            st.dataframe(t9[["mes", "id_fondo_serie", "valor_cuota", "cuota_previa", "rent_original", "retorno_cuota", "diferencia_pp", "estado_auditoria"]],
                         hide_index=True, width="stretch", height=240)
            st.caption("Diferencias ≥ 1 pp entre la rentabilidad publicada y la implícita en cuotas consecutivas. No se presumen errores; "
                       "el modelo usa la rentabilidad publicada, no la cuota.")

    st.markdown("##### Fuera del panel balanceado: análisis contextual")
    st.warning("ETF y Estructurados (y las series sin historia suficiente) **no integran** el panel balanceado de 61 meses. "
               "Sus métricas usan tramos observados de al menos 12 meses consecutivos con horizontes distintos: no son comparables "
               "directamente con la muestra principal.", icon=":material/do_not_disturb_on:")
    T20, T21 = tabla("tabla20_cobertura_tipos_observados"), tabla("tabla21_desempeno_observado_contextual")
    if T20 is not None:
        t20 = T20[T20.moneda.isin(F.monedas)] if F.monedas else T20
        st.dataframe(t20, hide_index=True, width="stretch")
    if T21 is not None:
        t21 = T21[T21.tipo.isin(["ETF", "Estructurados"])]
        if F.monedas:
            t21 = t21[t21.moneda.isin(F.monedas)]
        t21 = t21[(t21.fin >= ini) & (t21.inicio <= fin)]
        st.markdown(f"ETF y Estructurados con tramos observados que se superponen al periodo elegido: **{len(t21)}** series")
        st.dataframe(t21, hide_index=True, width="stretch", height=240)
    DIC = diccionario(str(RAIZ), FIRMA)
    with st.expander("Diccionario de variables (diccionario_variables.md)"):
        if DIC is not None:
            st.dataframe(DIC, hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# 7. Descargas: todas usan DF (filtros + línea de tiempo)
# ---------------------------------------------------------------------------
COLS_EXPORT = datos.COLUMNAS_PANEL + ["estado_dato", "etiqueta"]
FIRMA_TOTAL = F.firma() + "|" + vista + "|" + FIRMA
sufijo = f"{ini}_{fin}"
info_extra = {"Filas": len(DF), "Fondos-series": DF.id_fondo_serie.nunique(), "Meses": N_MESES,
              "Archivo fuente": RUTA_PROC.name, "SHA-256 del archivo fuente": sha, "Generado": dl.ahora_peru(),
              "Unidades": "Rentabilidades y tasas en decimal (0,01 = 1 %)"}


@st.cache_data(show_spinner=False, max_entries=6)
def _excel_obs(clave: str, _df: pd.DataFrame, _meta: pd.DataFrame, _dic) -> bytes:
    hojas = {"filtros": _meta, "observaciones": _df}
    if _dic is not None:
        hojas["diccionario"] = _dic
    return dl.excel_bytes(hojas)


def tablas_estadisticas() -> dict[str, pd.DataFrame]:
    t = {"metricas_por_serie": M, "resumen_por_categoria": RES, "descriptivos": DESC,
         "rent_mensual_por_tipo": CAT.drop(columns=["fecha"]), "calidad_por_mes": DF.groupby("mes").agg(
             filas=("id_fondo_serie", "size"), interpoladas=("imputado", "sum"), winsorizadas=("atipico", "sum")).reset_index()}
    if EST["ok"]:
        t["modelo_filtrado"] = EST["tabla"]
    return t


@st.cache_data(show_spinner=False, max_entries=6)
def _excel_tablas(clave: str, _hojas: dict) -> bytes:
    return dl.excel_bytes(_hojas)


def _vigente(k: str):
    v = st.session_state.get(k)
    return v[1:] if v and v[0] == FIRMA_TOTAL else None


with tabs[6]:
    meta = dl.hoja_filtros(F.describir(), info_extra)
    st.markdown("##### Lo que contienen las descargas")
    st.dataframe(meta.astype(str), hide_index=True, width="stretch")
    st.caption("Todas las descargas se generan con exactamente estos filtros y esta línea de tiempo. Si cambias un filtro, "
               "los archivos ya preparados se descartan y deben generarse de nuevo.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1 · Observaciones filtradas**")
        st.download_button("CSV de observaciones", dl.csv_bytes(DF[COLS_EXPORT]), f"fondos_observaciones_{sufijo}.csv",
                           "text/csv", icon=":material/csv:", width="stretch", key="dl_csv")
        if st.button("Preparar Excel de observaciones", width="stretch", icon=":material/table_view:", key="b_xlsx"):
            with st.spinner("Generando Excel…"):
                st.session_state.prep_xlsx = (FIRMA_TOTAL, _excel_obs(FIRMA_TOTAL, DF[COLS_EXPORT], meta.astype(str), DIC))
        v = _vigente("prep_xlsx")
        if v:
            st.download_button("Descargar Excel de observaciones", v[0], f"fondos_observaciones_{sufijo}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/download:",
                               width="stretch", type="primary", key="dl_xlsx")
        st.caption(f"{len(DF)} filas × {len(COLS_EXPORT)} columnas (32 originales + estado del dato + etiqueta).")
    with c2:
        st.markdown("**2 · Tablas estadísticas**")
        hojas = {"filtros": meta.astype(str), **tablas_estadisticas()}
        st.download_button("Excel de tablas estadísticas", _excel_tablas(FIRMA_TOTAL + RET, hojas), f"tablas_estadisticas_{sufijo}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/summarize:",
                           width="stretch", key="dl_tablas_xlsx")
        st.download_button("ZIP de tablas en CSV", dl.zip_bytes({f"{k}_{sufijo}.csv": dl.csv_bytes(v) for k, v in hojas.items()}),
                           f"tablas_estadisticas_{sufijo}.zip", "application/zip", icon=":material/folder_zip:",
                           width="stretch", key="dl_tablas_zip")
        st.caption("Métricas por serie, resumen por tipo y moneda, descriptivos, rentabilidad mensual por tipo, calidad y modelo filtrado.")
    with c3:
        st.markdown("**3 · Gráficos en PNG**")
        nombres = list(REG)
        elegido = st.selectbox("Gráfico", nombres, format_func=lambda n: REG[n][0], key="png_sel", label_visibility="collapsed")
        nota = (f"Fuente: AAF (boletines mensuales) y BCRPData; elaboración propia. Filtros: {mes_corto(ini)} – {mes_corto(fin)}; "
                f"{F.describir()['Tipo de fondo']}; {F.describir()['Moneda']}; {etiqueta_ret}.")

        if st.button("Preparar PNG del gráfico elegido", width="stretch", icon=":material/image:", key="b_png"):
            with st.spinner("Generando PNG de alta resolución…"):
                try:
                    st.session_state.prep_png = (FIRMA_TOTAL, elegido, dl.png_bytes(gr.para_exportar(REG[elegido][1](PCLARO), nota)))
                except Exception as e:  # Kaleido no disponible en el servidor
                    st.session_state.prep_png = (FIRMA_TOTAL, elegido, repr(e))
        v = _vigente("prep_png")
        if v and v[0] == elegido:
            if isinstance(v[1], bytes):
                st.download_button("Descargar PNG (2800 px de ancho)", v[1], f"{elegido}_{sufijo}.png", "image/png",
                                   width="stretch", type="primary", key="dl_png", icon=":material/download:")
            else:
                st.error(f"No se pudo generar el PNG en el servidor ({v[1]}). Usa el ícono de cámara del gráfico.")
        if st.button("Preparar ZIP con todos los gráficos", width="stretch", icon=":material/photo_library:", key="b_zip"):
            archivos, errores = {}, []
            with st.spinner(f"Generando {len(REG)} gráficos en PNG…"):
                for n_, (t_, cons) in REG.items():
                    try:
                        archivos[f"{n_}_{sufijo}.png"] = dl.png_bytes(gr.para_exportar(cons(PCLARO), nota))
                    except Exception as e:
                        errores.append(f"{n_}: {e!r}")
                archivos[f"filtros_{sufijo}.csv"] = dl.csv_bytes(meta.astype(str))
            st.session_state.prep_zip_png = (FIRMA_TOTAL, dl.zip_bytes(archivos), errores)
        v = _vigente("prep_zip_png")
        if v:
            st.download_button("Descargar ZIP de gráficos", v[0], f"graficos_{sufijo}.zip", "application/zip",
                               width="stretch", type="primary", key="dl_zip_png", icon=":material/download:")
            for e in v[1]:
                st.error(e)
        st.caption("También puedes usar el ícono de cámara de cada gráfico (PNG a 3× de resolución con el mismo filtro).")

    st.divider()
    st.markdown("**4 · Reporte de resultados filtrados (HTML imprimible)**")

    def preparar_reporte() -> bytes:
        nota = (f"Fuente: AAF y BCRPData; elaboración propia. {mes_corto(ini)} – {mes_corto(fin)}.")
        figuras, primera = [], True
        for n_, (t_, cons) in REG.items():
            fig = cons(PCLARO)
            try:
                figuras.append((t_, dl.png_bytes(gr.para_exportar(fig, nota), ancho=1200, escala=1.5)))
            except Exception:
                figuras.append((t_, fig.to_html(full_html=False, include_plotlyjs="inline" if primera else False)))
                primera = False
        kpi = KPI.copy()
        secciones = [
            ("Indicadores principales por moneda", "Medianas entre fondos-series; las monedas no se mezclan.", kpi),
            ("Comparación por tipo de fondo y moneda", "", RES),
            ("Estadísticos descriptivos de la rentabilidad mensual", "", DESC),
            ("Desempeño por fondo-serie", "", M.drop(columns=["id_fondo_serie"])),
            ("Calidad de datos", f"Filas: {CAL['filas']} · observadas: {CAL['observadas']} · interpoladas: {CAL['interpoladas']} · "
                                 f"winsorizadas: {CAL['winsorizadas']} · faltantes: {CAL['faltantes']}.", None),
        ]
        if T3 is not None:
            secciones.append(("Modelo oficial (panel completo, tabla 3)", "\n\n".join(eco.interpretar(T3)),
                              T3[["variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup"]]))
        if EST["ok"]:
            secciones.append(("Reestimación exploratoria con los filtros", "\n\n".join(eco.interpretar(EST["tabla"]) + EST["advertencias"]),
                              EST["tabla"]))
        html_txt = dl.reporte_html("Fondos mutuos en el Perú · Reporte de resultados filtrados", F.describir(), info_extra,
                                   secciones, figuras, eco.ADVERTENCIA_GENERAL)
        return html_txt.encode("utf-8")

    a, b_ = st.columns([1, 1])
    if a.button("Preparar reporte con los filtros activos", width="stretch", icon=":material/description:", key="b_rep"):
        with st.spinner("Armando el reporte (tablas, gráficos y lectura econométrica)…"):
            st.session_state.prep_reporte = (FIRMA_TOTAL, preparar_reporte())
    v = _vigente("prep_reporte")
    if v:
        b_.download_button("Descargar reporte HTML", v[0], f"reporte_fondos_{sufijo}.html", "text/html",
                           width="stretch", type="primary", key="dl_reporte", icon=":material/download:")
    st.caption("El reporte incluye filtros, indicadores, tablas, gráficos y la lectura econométrica. Ábrelo en el navegador y usa "
               "Imprimir → Guardar como PDF si necesitas un PDF.")

st.caption("Elaboración propia con datos de la Asociación de Administradoras de Fondos del Perú (boletines mensuales) y del BCRP "
           "(BCRPData). Diseño observacional: los resultados no constituyen recomendación de inversión.")
