"""Contenido de las siete secciones del menú circular.

Los textos definitivos proceden del journal (config/contenido_secciones.json). Lo que ya existe en la
documentación de la investigación (README, diccionario, tablas y figuras de salidas/) se muestra tal cual,
con su origen indicado; nada se redacta como resultado si no está en esos archivos.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import cargas
import catalogo_figuras as cf
import econometria as eco
import nav
import portal_config as pc
from vistas import biblioteca, comunes as cm

PAGINA_DOCS = "Explorar en el dashboard financiero"


def _bloques(clave: str) -> None:
    for b in pc.contenido()[clave]:
        cm.bloque(b["titulo"], b.get("texto", ""), b.get("origen", ""))


def introduccion() -> None:
    _bloques("introduccion")


def marco() -> None:
    _bloques("marco_teorico")
    st.markdown("<h4 style='margin-top:1.4rem;font-family:var(--serif)'>Medidas y especificación empleadas en el estudio</h4>", unsafe_allow_html=True)
    st.caption("Formulación tomada de la metodología efectivamente utilizada (README y diccionario de variables del proyecto).")
    with st.container(border=True):
        st.markdown("**Referencia mensual y exceso de rentabilidad** · tasa interbancaria anual $i_t$ (BCRPData) por moneda")
        st.latex(r"rf_t=\left(1+\frac{i_t}{100}\right)^{1/12}-1\qquad e_{i,t}=r_{i,t}-rf_{t}")
        st.markdown("**Rentabilidad y volatilidad anualizadas** (mínimo 12 meses)")
        st.latex(r"R_i^{anual}=\exp\!\Big(12\cdot\tfrac{1}{T}\sum_{t}\ln(1+r_{i,t})\Big)-1\qquad \sigma_i^{anual}=s(r_i)\sqrt{12}")
        st.markdown("**Ratio de Sharpe anualizado** · usa el exceso sobre la tasa interbancaria de la misma moneda")
        st.latex(r"Sharpe_i=\frac{\bar{e}_i}{s(e_i)}\sqrt{12}")
        st.markdown("**Factores del modelo** · $X_1$ volatilidad histórica, $X_2$ riesgo cambiario, $X_3$ persistencia")
        st.latex(r"vol12_{i,t}=s\big(r_{i,t-1},\dots,r_{i,t-12}\big)\;(\ge 6\text{ datos})\qquad var\_tc_t=\ln TC_t-\ln TC_{t-1}\qquad rent\_lag1_{i,t}=r_{i,t-1}")
        st.markdown("**Especificación econométrica** · MCO con errores estándar agrupados por fondo-serie y mes")
        st.latex(r"r_{i,t}=\beta_0+\beta_1\,vol12_{i,t}+\beta_2\,var\_tc_t+\beta_3\,rent\_lag1_{i,t}+\gamma_{tipo(i)}+\delta_{moneda(i)}+\varepsilon_{i,t}")
        st.markdown("**Winsorización por tipo y moneda** (límites de Tukey con registros observados)")
        st.latex(r"\big[\,Q_1-3\,RIQ,\;\;Q_3+3\,RIQ\,\big]")
    st.caption("El tipo de cambio es común a todas las series de un mes: la precisión de $\\beta_2$ depende del número de meses (61), no de las 4 026 filas. "
               "Los coeficientes son asociaciones de un diseño observacional.")


def _tabla_pct(df: pd.DataFrame, cols_pct: list[str]) -> pd.DataFrame:
    d = df.copy()
    for c in cols_pct:
        if c in d:
            d[c] = 100 * d[c]
    return d


def resultados() -> None:
    proy = cargas.proyecto()
    if proy is None:
        return
    st.markdown("<div class='fm-bloque'><h4>Resultados oficiales de la investigación</h4><p class='vacio'>Tablas y figuras generadas por <code>codigo/04_analisis.py</code> "
                "a partir del panel procesado (carpeta <code>salidas/</code>). No cambian con los filtros del dashboard: el dashboard produce cálculos exploratorios aparte.</p></div>",
                unsafe_allow_html=True)
    pan = proy.panel
    t3 = proy.tabla("tabla3_modelo_principal")
    c = st.columns(4)
    c[0].metric("Observaciones", f"{len(pan):,}".replace(",", " "))
    c[1].metric("Fondos-series", pan.id_fondo_serie.nunique())
    c[2].metric("Meses comunes", pan.mes.nunique())
    c[3].metric("R² del modelo principal", f"{t3.r2.iloc[0]:.3f}" if t3 is not None else "n.d.")
    st.button(PAGINA_DOCS, icon=":material/monitoring:", key="res_a_dash", on_click=nav.ir, args=("s2",), type="primary")
    nuevo = cf.nueva_version_completa(proy.raiz)
    if not nuevo:
        st.info("Los archivos de gráficos actuales todavía no están completos en GitHub. "
                "Se muestran los disponibles, con un aviso cuando proceden de la versión anterior. "
                "La base de datos y los modelos no se modifican.")
    tabs = st.tabs(["Desempeño por tipo y moneda", "Modelo econométrico", "Contrastes y distribución"])

    def _figura(f: cf.Figura) -> None:
        ruta, titulo, es_nueva = cf.resolver(proy.raiz, f)
        if ruta:
            st.markdown(f"**{titulo}**")
            st.image(str(ruta), width="stretch")
            if es_nueva:
                st.caption(f.descripcion + " Fuente: AAF y BCRPData; figura generada por 04_analisis.py.")
            else:
                st.caption("Versión anterior del gráfico; se sustituirá al publicar las salidas nuevas del pipeline.")
        else:
            st.warning(f"No se encontró la figura {f.numero} entre las salidas de la investigación.")

    with tabs[0]:
        t2 = proy.tabla("tabla2_riesgo_rentabilidad_por_tipo")
        if t2 is not None:
            st.markdown("**Tabla 2 · Rentabilidad, volatilidad y Sharpe anualizados (mediana entre series, por tipo y moneda)**")
            st.dataframe(_tabla_pct(t2, ["rent_mediana", "vol_mediana", "meses_perdida_mediana"]), hide_index=True, width="stretch", column_config={
                "tipo": "Tipo", "moneda": "Moneda", "unidades": "Series",
                "rent_mediana": st.column_config.NumberColumn("Rent. anualizada (%)", format="%.2f"),
                "vol_mediana": st.column_config.NumberColumn("Vol. anualizada (%)", format="%.2f"),
                "sharpe_mediana": st.column_config.NumberColumn("Sharpe", format="%.3f"),
                "meses_perdida_mediana": st.column_config.NumberColumn("Meses con pérdida (%)", format="%.1f")})
            st.caption("Medianas entre fondos-series, igual peso por serie; las monedas no se mezclan. Los grupos de 2 o 3 series son descriptivos.")
        _figura(cf.FIGURAS[0])
        _figura(cf.FIGURAS[1])
        if not nuevo:
            ruta_anterior = proy.raiz / "salidas" / "figura3_rentabilidad_mensual.png"
            if ruta_anterior.is_file():
                st.markdown("**Gráfico anterior · Rentabilidad mensual por tipo (versión previa)**")
                st.image(str(ruta_anterior), width="stretch")

    with tabs[1]:
        if t3 is not None:
            st.markdown(f"**Tabla 3 · Modelo principal** · MCO con errores agrupados por fondo-serie y mes · n = {int(t3.n.iloc[0])} · "
                        f"{int(t3.fondos_series.iloc[0])} series · {int(t3.meses.iloc[0])} meses")
            st.dataframe(t3[["variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup"]], hide_index=True, width="stretch",
                         column_config={k: st.column_config.NumberColumn(format="%.4f") for k in ["coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup"]})
            st.markdown("**Lectura (generada desde los valores de la tabla)**")
            for t in eco.interpretar(t3):
                st.markdown("- " + t)
            st.info(eco.ADVERTENCIA_GENERAL, icon=":material/balance:")
        _figura(cf.FIGURAS[4])
        t25 = proy.tabla("tabla25_regresion_parcial_mensual")
        if t25 is not None:
            with st.expander("Consultar los 61 valores mensuales que sustentan la Figura 5"):
                st.dataframe(t25, hide_index=True, width="stretch")
                st.caption("Los valores son resultados oficiales del pipeline; la gráfica no depende de filtros de la interfaz.")

    with tabs[2]:
        t14 = proy.tabla("tabla14_contrastes_tipo")
        if t14 is not None:
            st.markdown("**Tabla 14 · Contrastes del exceso mensual frente a Deuda** (diferencia de medianas, HAC(3), corrección de Holm)")
            st.dataframe(t14, hide_index=True, width="stretch")
            st.caption("Exploratorio, no causal. Las diferencias se expresan en puntos porcentuales mensuales.")
        _figura(cf.FIGURAS[2])
        _figura(cf.FIGURAS[3])
        for nombre, rotulo in [("tabla24_diferencias_mensuales_deuda", "Diferencias mensuales de la Figura 4"),
                              ("tabla23_indice_riqueza", "Índice de riqueza y caídas de la Figura 2")]:
            t = proy.tabla(nombre)
            if t is not None:
                with st.expander(f"Consultar datos originales: {rotulo}"):
                    st.dataframe(t, hide_index=True, width="stretch")
                    st.caption("Archivo CSV oficial de salidas/, sin aplicar los filtros interactivos.")


def _flujo() -> None:
    pasos = [("API BCRPData", "Tipo de cambio e interbancarias (JSON)"), ("Boletines AAF", "Descarga programática de PDF mensuales"),
             ("Parseo", "PyMuPDF y pdfplumber; control por boletín"), ("Limpieza y llave", "Homologación, exclusiones, interpolación y winsorización"),
             ("Panel balanceado", "66 series × 61 meses"), ("Análisis", "Tablas, figuras y modelos"), ("Verificación", "SHA-256 y reproducción local")]
    st.markdown("<div class='fm-flujo'>" + "".join(f"<div><b>{a}</b>{b}</div>" for a, b in pasos) + "</div>", unsafe_allow_html=True)


def metodos() -> None:
    proy = cargas.proyecto()
    st.markdown("**Flujo de trabajo de la investigación**")
    _flujo()
    st.caption("Fuente: README y scripts del proyecto (carpeta N.º 3). Despliega cada apartado.")
    with st.expander("Diseño de investigación", expanded=True):
        st.markdown("Diseño **observacional, longitudinal, de panel balanceado**. Compara el desempeño ajustado por riesgo de fondos mutuos peruanos por tipo y moneda. "
                    "No identifica causalidad ni recomienda comprar fondos. Las comparaciones dan igual peso a cada fondo-serie, no a patrimonio ni partícipes.")
    with st.expander("Población y muestra"):
        if proy is not None:
            pan = proy.panel
            sel = proy.tabla("tabla_seleccion_series")
            extra = f" Se evaluaron {len(sel)} series candidatas y se seleccionaron {int(sel.seleccionado.sum())}." if sel is not None else ""
            st.markdown(f"Panel balanceado definitivo: **{pan.id_fondo_serie.nunique()} fondos-series × {pan.mes.nunique()} meses = {len(pan):,} observaciones** "
                        f"({pan.mes.min()} a {pan.mes.max()}), {pan.administradora.nunique()} administradoras, cinco tipos y dos monedas (PEN y USD).{extra} "
                        "ETF y Estructurados no integran el panel: se describen aparte con tramos observados.".replace(",", " "))
            st.dataframe(pan.groupby(["tipo", "moneda"]).agg(series=("id_fondo_serie", "nunique"), observaciones=("mes", "size")).reset_index(),
                         hide_index=True, width="stretch")
    with st.expander("Fuentes de información y extracción mediante API"):
        st.markdown("**Vía 1 · API REST de BCRPData** (pública, sin clave). Consulta directa a tres series; `FECHA_INICIO = 2018-12-01` y `FECHA_CORTE = 2025-12-31`.")
        st.dataframe(pd.DataFrame([
            ("PN01216PM", "Tipo de cambio fin de periodo (S/ por US$), interbancario, promedio", "Mensual", "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01216PM/json/2018-12/2025-12/esp"),
            ("PD04692MD", "Tasa interbancaria en soles", "Diaria", "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04692MD/json/2018-12-01/2025-12-31/esp"),
            ("PD04693MD", "Tasa interbancaria en dólares", "Diaria", "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04693MD/json/2018-12-01/2025-12-31/esp")],
            columns=["Código", "Serie", "Frecuencia", "Endpoint"]), hide_index=True, width="stretch",
            column_config={"Endpoint": st.column_config.LinkColumn("Endpoint")})
    with st.expander("Scraping y descarga documental"):
        st.markdown("**Vía 2 · Descarga programática de boletines mensuales de la AAF** (https://fondosmutuos.pe/estadisticas/). Se analizan los hipervínculos a PDF del catálogo, "
                    "se respetan `robots.txt`, un User-Agent identificable y pausas de 1,5 s; ante rechazo explícito se detiene el acceso. Los PDF originales se conservan intactos, "
                    "con su URL, fecha, código HTTP y SHA-256. Lectura con PyMuPDF (formatos anteriores a diciembre de 2022) y pdfplumber (formatos modernos).")
        st.warning(pc.portal()["nota_fuentes"] + " El intento de rastreo de la SMV fue rechazado (HTTP 418) y está documentado en `incidencias_fuente.md`. "
                   "No consta en la documentación una autorización docente escrita de sustitución de fuente.", icon=":material/info:")
    with st.expander("Limpieza y tratamiento de datos"):
        st.markdown("- Rentabilidades publicadas en porcentaje convertidas a decimal; se excluyen retornos no numéricos o inferiores a −100 %, cuotas no positivas y administradoras no identificadas (los excluidos y duplicados conflictivos se documentan).\n"
                    "- **Interpolación geométrica** solo en huecos interiores de 1 a 3 meses (`imputado = 1`, `archivo = INTERPOLACION`); nunca antes del inicio ni después del último registro.\n"
                    "- **Winsorización** con límites de Tukey (Q1 − 3·RIQ, Q3 + 3·RIQ) por tipo y moneda, calculados con registros observados; se conserva `rent_original`.\n"
                    "- Llave `id_fondo_serie`: administradora homologada + denominación normalizada + moneda; las colisiones conflictivas se excluyen, no se promedian.")
    with st.expander("Construcción del panel"):
        st.markdown("Se examinan ventanas consecutivas de al menos 60 meses con al menos 4 tipos, historia suficiente para las variables rezagadas y trazabilidad completa. "
                    "Se admite un máximo de 15 % de retornos imputados por serie. La ventana elegida no usa R², valores p ni resultados de Sharpe como criterio.")
    with st.expander("Diccionario y operacionalización de variables"):
        dic = proy.diccionario if proy else None
        if dic is not None:
            st.dataframe(dic, hide_index=True, width="stretch", height=380)
        st.caption("Y = rent_mes · X1 = vol12 · X2 = var_tc · X3 = rent_lag1 · controles: tipo de fondo y moneda.")
    with st.expander("Fórmulas financieras y especificación econométrica"):
        st.markdown("Consulta el apartado **Marco teórico** para las fórmulas renderizadas. Inferencia principal: MCO con errores estándar agrupados por fondo-serie y mes; "
                    "alternativas de sensibilidad: agrupación solo por serie o por mes, efectos fijos de serie, estimación sin winsorizar y sin filas interpoladas.")
    with st.expander("Verificación y reproducibilidad"):
        st.markdown("- Manifiesto SHA-256 de crudos, procesado y salidas (`hash_sha256.txt`).\n- `05_verificacion_fuente.py` comprueba hashes, reparsea los crudos y reejecuta limpieza y análisis; umbral de equivalencia del 95 % por archivo.\n"
                    "- Parámetros congelados (`FECHA_INICIO`, `FECHA_CORTE`, semilla 501). El detalle de los registros está en la sección 02, pestaña **Transparencia**.")
        st.button("Ir a transparencia y reproducibilidad", icon=":material/verified:", key="m_a_transp", on_click=nav.ir, args=("s2",))


def discusion() -> None:
    _bloques("discusion")


def conclusiones() -> None:
    _bloques("conclusiones")


def _antecedentes():
    art = __import__("nav").ficha()
    if art:
        biblioteca.ficha(art)
    else:
        biblioteca.biblioteca()


RENDER = {"introduccion": introduccion, "marco": marco, "antecedentes": _antecedentes, "metodos": metodos,
          "resultados": resultados, "discusion": discusion, "conclusiones": conclusiones}
