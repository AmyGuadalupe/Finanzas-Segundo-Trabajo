"""Pruebas del dashboard con los datos reales del proyecto.

Ejecutar desde la raíz del repositorio:
    python -m pytest dashboard/tests -q
Comprueban: columnas, integridad del panel, reproducción exacta de las tablas
oficiales, filtros, matemática de los indicadores, que las descargas contengan
solo lo filtrado, interacción con la app y que no se escriba en la investigación.
"""
from __future__ import annotations

import hashlib
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

DASH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASH))

import datos  # noqa: E402
import descargas as dl  # noqa: E402
import econometria as eco  # noqa: E402
import graficos as gr  # noqa: E402
import metricas as mt  # noqa: E402

TOL = 1e-8
RAIZ = datos.localizar_proyecto()


@pytest.fixture(scope="session")
def panel():
    return datos.cargar_panel(RAIZ)


def completo(p) -> mt.Filtros:
    return mt.Filtros(mes_ini=p.mes.min(), mes_fin=p.mes.max())


def huella_proyecto() -> dict[str, str]:
    """SHA-256 de todos los archivos de la investigación (todo menos dashboard/)."""
    out = {}
    for f in sorted(RAIZ.rglob("*")):
        if f.is_file() and DASH not in f.parents and ".git" not in f.parts:
            out[str(f.relative_to(RAIZ))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


HUELLA_INICIAL = huella_proyecto()


# --------------------------------------------------------------------------- columnas
def test_columnas_documentadas_existen(panel):
    faltan = [c for c in datos.COLUMNAS_PANEL if c not in panel.columns]
    assert not faltan, faltan
    assert len(datos.COLUMNAS_PANEL) == 32


@pytest.mark.parametrize("nombre", sorted(datos.TABLAS))
def test_tablas_de_salidas_con_columnas(nombre):
    t = datos.cargar_tabla(RAIZ, nombre)
    assert t is not None, f"salidas/{nombre}.csv falta o cambió sus columnas"
    assert len(t) > 0


def test_diccionario_cubre_las_32_columnas():
    d = datos.diccionario_variables(RAIZ)
    assert d is not None and set(d.iloc[:, 0]) == set(datos.COLUMNAS_PANEL)


# --------------------------------------------------------------------------- integridad
def test_panel_balanceado_sin_faltantes(panel):
    base = panel[datos.COLUMNAS_PANEL]
    assert base.isna().sum().sum() == 0
    assert not panel.duplicated(["id_fondo_serie", "mes"]).any()
    meses = sorted(panel.mes.unique())
    assert meses == pd.period_range(meses[0], meses[-1], freq="M").astype(str).tolist()
    assert panel.groupby("id_fondo_serie").mes.nunique().eq(len(meses)).all()
    assert len(panel) == len(meses) * panel.id_fondo_serie.nunique()


def test_etf_y_estructurados_fuera_del_panel(panel):
    assert not panel.tipo.isin(["ETF", "Estructurados"]).any()


def test_estado_dato_coherente_con_banderas(panel):
    imp, win = panel.imputado.eq(1), panel.atipico.eq(1)
    assert (panel.estado_dato.eq("Observado") == (~imp & ~win)).all()
    assert (panel.estado_dato.eq("Interpolado y winsorizado") == (imp & win)).all()
    assert panel.loc[imp, "archivo"].eq("INTERPOLACION").all()
    assert (panel.loc[~win, "rent_mes"] == panel.loc[~win, "rent_original"]).all()


def test_etiquetas_unicas(panel):
    e = panel.drop_duplicates("id_fondo_serie").etiqueta
    assert e.is_unique


# --------------------------------------------------------------------------- reproducción
def test_metricas_reproducen_tabla1(panel):
    m = mt.metricas_por_serie(mt.aplicar_filtros(panel, completo(panel)), "tratada")
    t1 = datos.cargar_tabla(RAIZ, "tabla1_metricas_por_fondo_serie").merge(m, on="id_fondo_serie", suffixes=("_of", ""))
    assert len(t1) == len(m) == panel.id_fondo_serie.nunique()
    for c in ["rent_anualizada", "vol_anualizada", "sharpe_anualizado", "meses_con_perdida"]:
        assert np.allclose(t1[c + "_of"], t1[c], atol=TOL), c


def test_metricas_originales_reproducen_tabla22(panel):
    m = mt.metricas_por_serie(mt.aplicar_filtros(panel, completo(panel)), "original")
    t = datos.cargar_tabla(RAIZ, "tabla22_desempeno_sin_winsorizar").merge(m, on="id_fondo_serie", suffixes=("_of", ""))
    for c in ["rent_anualizada", "vol_anualizada", "sharpe_anualizado"]:
        assert np.allclose(t[c + "_of"], t[c], atol=TOL), c


def test_resumen_reproduce_tablas_2_y_15(panel):
    r = mt.resumen_por_categoria(mt.metricas_por_serie(panel, "tratada"))
    t2 = datos.cargar_tabla(RAIZ, "tabla2_riesgo_rentabilidad_por_tipo").merge(r, on=["tipo", "moneda"], suffixes=("_of", ""))
    for c in ["rent_mediana", "vol_mediana", "sharpe_mediana"]:
        assert np.allclose(t2[c + "_of"], t2[c], atol=TOL)
    t15 = pd.read_csv(RAIZ / "salidas/tabla15_distribucion_sharpe.csv").merge(r, on=["tipo", "moneda"])
    assert np.allclose(t15.q25, t15.sharpe_q25, atol=TOL) and np.allclose(t15.q75, t15.sharpe_q75, atol=TOL)


def test_descriptivos_y_mensual_reproducen_tablas_16_y_8(panel):
    d = mt.descriptivos(panel, "tratada").merge(pd.read_csv(RAIZ / "salidas/tabla16_descriptivos.csv"), on=["tipo", "moneda"], suffixes=("", "_of"))
    for c in ["media", "mediana", "desv", "p05", "p95", "minimo", "maximo"]:
        assert np.allclose(d[c], d[c + "_of"], atol=TOL), c
    c8 = mt.rent_mensual_categoria(panel, "tratada").merge(pd.read_csv(RAIZ / "salidas/tabla8_rentabilidades_mensuales.csv", dtype={"mes": str}),
                                                           on=["mes", "tipo", "moneda"])
    assert len(c8) == len(pd.read_csv(RAIZ / "salidas/tabla8_rentabilidades_mensuales.csv"))
    assert np.allclose(c8.rent, c8.rent_mes, atol=TOL)


def test_modelo_reproduce_tabla3_y_tabla5(panel):
    e = eco.estimar(panel, "tratada")
    t3 = datos.cargar_tabla(RAIZ, "tabla3_modelo_principal")
    assert e["ok"] and list(e["tabla"].variable) == list(t3.variable)
    for a, b in [("coeficiente", "coeficiente"), ("error_estandar", "error_estandar"), ("p_valor", "p_valor"), ("ic95_inf", "ic95_inf")]:
        assert np.allclose(e["tabla"][a], t3[b], atol=1e-9)
    assert abs(e["r2"] - t3.r2.iloc[0]) < 1e-9
    o = eco.estimar(panel, "original")
    t5 = datos.cargar_tabla(RAIZ, "tabla5_robustez")
    t5 = t5[t5.modelo.eq("misma_muestra_sin_winsorizar")]
    assert np.allclose(o["tabla"].error_estandar, t5.error_estandar, atol=1e-9)


def test_modelo_con_una_sola_categoria_omite_control(panel):
    sub = panel[panel.tipo.eq("Deuda") & panel.moneda.eq("USD")]
    e = eco.estimar(sub, "tratada")
    assert e["ok"] and "C(tipo)" not in e["formula"] and "C(moneda)" not in e["formula"]
    assert any("fondos-series" in a for a in e["advertencias"])


# --------------------------------------------------------------------------- filtros
@pytest.mark.parametrize("f", [
    dict(tipos=("Deuda",)), dict(monedas=("USD",)), dict(tipos=("Acciones", "Mixtos"), monedas=("PEN",)),
    dict(administradoras=("Scotia Fondos",)), dict(mes_ini="2022-01", mes_fin="2022-12"),
])
def test_filtros_restringen_exactamente(panel, f):
    base = dict(mes_ini=panel.mes.min(), mes_fin=panel.mes.max())
    base.update(f)
    F = mt.Filtros(**base)
    d = mt.aplicar_filtros(panel, F)
    assert len(d) > 0
    if F.tipos:
        assert set(d.tipo) == set(F.tipos)
    if F.monedas:
        assert set(d.moneda) == set(F.monedas)
    if F.administradoras:
        assert set(d.administradora) == set(F.administradoras)
    assert d.mes.min() >= F.mes_ini and d.mes.max() <= F.mes_fin
    # complemento: nada que cumpla el filtro quedó fuera
    esperado = panel[panel.mes.between(F.mes_ini, F.mes_fin)
                     & (panel.tipo.isin(F.tipos) if F.tipos else True)
                     & (panel.moneda.isin(F.monedas) if F.monedas else True)
                     & (panel.administradora.isin(F.administradoras) if F.administradoras else True)]
    assert len(d) == len(esperado)


def test_filtro_por_series_y_periodo(panel):
    ids = tuple(sorted(panel.id_fondo_serie.unique())[:3])
    d = mt.aplicar_filtros(panel, mt.Filtros(series=ids, mes_ini="2023-03", mes_fin="2024-02"))
    assert set(d.id_fondo_serie) == set(ids) and d.mes.nunique() == 12 and len(d) == 36


def test_seleccion_vacia_equivale_a_todo(panel):
    assert len(mt.aplicar_filtros(panel, completo(panel))) == len(panel)


# --------------------------------------------------------------------------- matemática
def test_capitalizacion_compuesta_y_caida(panel):
    d = mt.aplicar_filtros(panel, mt.Filtros(mes_ini="2021-06", mes_fin="2023-05"))
    m = mt.metricas_por_serie(d, "tratada").set_index("id_fondo_serie")
    for id_, g in d.groupby("id_fondo_serie"):
        r = g.sort_values("mes").rent_mes.to_numpy()
        assert abs(m.loc[id_, "rent_acumulada"] - (np.prod(1 + r) - 1)) < 1e-12
        idx = np.cumprod(1 + r)
        caida = min(0.0, (idx / np.maximum.accumulate(np.r_[1, idx])[1:] - 1).min())
        assert abs(m.loc[id_, "max_caida"] - caida) < 1e-12
    ind = mt.indice_acumulado(d, "tratada", "serie")
    ultimo = ind[~ind.es_base].sort_values("fecha").groupby("id_fondo_serie").indice.last() / 100 - 1
    assert np.allclose(ultimo.sort_index(), m.rent_acumulada.sort_index(), atol=1e-12)
    assert ind[ind.es_base].indice.eq(100).all()


def test_sharpe_y_anualizacion_manual(panel):
    g = panel[panel.id_fondo_serie.eq(panel.id_fondo_serie.iloc[0])].sort_values("mes")
    r, rf, e = g.rent_mes.to_numpy(), g.rf_mensual.to_numpy(), g.exceso.to_numpy()
    assert np.allclose(e, r - rf, atol=1e-9)  # exceso = r − rf (guardado con 10 cifras significativas)
    m = mt.metricas_por_serie(g, "tratada").iloc[0]
    assert abs(m.sharpe_anualizado - e.mean() / e.std(ddof=1) * np.sqrt(12)) < 1e-12
    assert abs(m.rent_anualizada - (np.exp(12 * np.log1p(r).mean()) - 1)) < 1e-12
    assert abs(m.vol_anualizada - r.std(ddof=1) * np.sqrt(12)) < 1e-12


def test_menos_de_12_meses_no_se_anualiza(panel):
    d = mt.aplicar_filtros(panel, mt.Filtros(mes_ini="2024-01", mes_fin="2024-06"))
    m = mt.metricas_por_serie(d, "tratada")
    assert m.sharpe_anualizado.isna().all() and m.rent_anualizada.isna().all()
    assert m.rent_acumulada.notna().all()


def test_monedas_nunca_se_mezclan(panel):
    cat = mt.rent_mensual_categoria(panel, "tratada")
    assert cat.groupby(["mes", "tipo", "moneda"]).size().eq(1).all()
    k = mt.kpis_por_moneda(panel, mt.metricas_por_serie(panel))
    assert list(k.moneda) == ["PEN", "USD"]
    assert k.observaciones.sum() == len(panel)
    lt = mt.linea_tiempo(panel, "tratada")
    assert set(lt.moneda) == {"PEN", "USD"} and lt.groupby(["mes", "moneda"]).size().eq(1).all()


def test_volatilidad_historica_es_vol12_anualizada(panel):
    v = mt.volatilidad_historica(panel, "tratada", "serie")
    assert np.allclose(v.vol_anual.to_numpy(), panel.vol12.to_numpy() * np.sqrt(12))


# --------------------------------------------------------------------------- descargas
def _filtro_ejemplo(panel):
    return mt.Filtros(tipos=("Deuda", "Flexibles"), monedas=("USD",), mes_ini="2022-04", mes_fin="2023-09")


def test_csv_y_excel_contienen_solo_lo_filtrado(panel):
    F = _filtro_ejemplo(panel)
    d = mt.aplicar_filtros(panel, F)
    cols = datos.COLUMNAS_PANEL + ["estado_dato", "etiqueta"]
    csv = pd.read_csv(io.BytesIO(dl.csv_bytes(d[cols])), dtype={"mes": str}, encoding="utf-8-sig")
    assert len(csv) == len(d) and set(csv.tipo) == {"Deuda", "Flexibles"} and set(csv.moneda) == {"USD"}
    assert csv.mes.min() == "2022-04" and csv.mes.max() == "2023-09"
    assert np.allclose(csv.rent_mes, d.rent_mes)
    xl = pd.read_excel(io.BytesIO(dl.excel_bytes({"filtros": dl.hoja_filtros(F.describir(), {}), "observaciones": d[cols]})),
                       sheet_name=None, dtype={"mes": str})
    assert set(xl) == {"filtros", "observaciones"}
    assert len(xl["observaciones"]) == len(d) and xl["observaciones"].mes.between("2022-04", "2023-09").all()
    assert "2022-04 a 2023-09" in xl["filtros"].Valor.tolist()


def test_zip_de_tablas_y_reporte(panel):
    F = _filtro_ejemplo(panel)
    d = mt.aplicar_filtros(panel, F)
    m = mt.metricas_por_serie(d)
    z = zipfile.ZipFile(io.BytesIO(dl.zip_bytes({"metricas.csv": dl.csv_bytes(m)})))
    leido = pd.read_csv(z.open("metricas.csv"), encoding="utf-8-sig")
    assert set(leido.id_fondo_serie) == set(d.id_fondo_serie)
    html = dl.reporte_html("R", F.describir(), {"Filas": len(d)}, [("Métricas", "", m)], [], "aviso")
    assert "2022-04 a 2023-09" in html and "Deuda, Flexibles" in html and str(len(d)) in html


def test_png_alta_resolucion(panel):
    d = mt.aplicar_filtros(panel, _filtro_ejemplo(panel))
    fig = gr.fig_dispersion(mt.metricas_por_serie(d), "Deuda", gr.PALETAS["light"], "prueba")
    png = dl.png_bytes(gr.para_exportar(fig, "nota"))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    ancho = int.from_bytes(png[16:20], "big")
    assert ancho >= 2400


# --------------------------------------------------------------------------- código
def test_sin_rutas_absolutas_ni_drive():
    for f in DASH.glob("*.py"):
        t = f.read_text(encoding="utf-8")
        assert not re.search(r"(/home/|/content/|C:\\\\|/Users/|drive/MyDrive)", t), f.name


# --------------------------------------------------------------------------- aplicación
def test_app_interactua_y_descarga_lo_filtrado(panel, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.chdir(RAIZ)
    at = AppTest.from_file(str(DASH / "app.py"), default_timeout=240)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.tabs) == 7 and len(at.get("plotly_chart")) >= 12

    # Filtros: tipo, moneda y periodo mediante botón de la línea de tiempo
    at.multiselect(key="f_tipos").set_value(["Deuda"])
    at.radio(key="f_moneda").set_value("USD")
    at.run()
    next(b for b in at.button if b.label == "Últimos 12 meses").click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    ini, fin = at.session_state["f_periodo"]
    meses = sorted(panel.mes.unique())
    assert (ini, fin) == (meses[-12], meses[-1])

    # Descarga Excel preparada con esos filtros
    at.button(key="b_xlsx").click()
    at.run()
    firma, contenido = at.session_state["prep_xlsx"]
    obs = pd.read_excel(io.BytesIO(contenido), sheet_name="observaciones", dtype={"mes": str})
    esperado = panel[panel.tipo.eq("Deuda") & panel.moneda.eq("USD") & panel.mes.between(ini, fin)]
    assert len(obs) == len(esperado) and set(obs.tipo) == {"Deuda"} and set(obs.moneda) == {"USD"}
    assert obs.mes.min() == ini and obs.mes.max() == fin
    etiquetas = lambda: [getattr(e.proto, "label", "") for e in at.get("download_button")]  # noqa: E731
    assert "Descargar Excel de observaciones" in etiquetas()

    # Cambiar un filtro invalida el archivo preparado: el botón de descarga desaparece
    at.radio(key="f_moneda").set_value("PEN")
    at.run()
    assert at.session_state["prep_xlsx"][0] == firma
    assert "Descargar Excel de observaciones" not in etiquetas()

    # Restablecer
    next(b for b in at.button if b.label == "Restablecer filtros").click()
    at.run()
    assert at.session_state["f_tipos"] == [] and at.session_state["f_moneda"] == "Ambas"
    assert tuple(at.session_state["f_periodo"]) == (meses[0], meses[-1])
    assert not at.exception


def test_vista_por_fondo_serie_y_reporte(panel, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.chdir(DASH)  # también debe funcionar ejecutando desde dashboard/
    at = AppTest.from_file(str(DASH / "app.py"), default_timeout=240)
    at.run()
    ids = sorted(panel.id_fondo_serie.unique())[:3]
    at.multiselect(key="f_series").set_value(ids)
    at.radio(key="f_vista").set_value("serie")
    at.radio(key="f_retorno").set_value("original")
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert set(at.session_state["slots_series"]) == set(ids)
    at.button(key="b_rep").click()
    at.run()
    html = at.session_state["prep_reporte"][1].decode("utf-8")
    assert "Retorno original" in html and all(panel.loc[panel.id_fondo_serie.eq(i), "etiqueta"].iloc[0] in html for i in ids)
    assert "data:image/png;base64" in html or "plotly" in html.lower()


def test_no_se_modifico_ningun_archivo_de_la_investigacion():
    """Se ejecuta al final: compara con la huella tomada al importar el módulo."""
    assert huella_proyecto() == HUELLA_INICIAL
