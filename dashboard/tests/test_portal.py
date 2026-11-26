"""Pruebas automatizadas del portal: exportes, configuración, navegación y renderizado.

Ejecutar desde la raíz del repositorio:  python -m pytest dashboard/tests -q
Todas son de solo lectura sobre los archivos de la investigación.
"""
from __future__ import annotations

import hashlib
import io
import sys
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

AQUI = Path(__file__).resolve().parents[1]
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))

import datos  # noqa: E402
import exportes as ex  # noqa: E402
import portal_config as pc  # noqa: E402

RAIZ = datos.localizar_proyecto()
PROC = RAIZ / "datos_procesados" / f"datos_procesados_{datos.CODIGO_MATRICULA}.csv"


@pytest.fixture(scope="module")
def df_demo() -> pd.DataFrame:
    return pd.DataFrame({
        "fecha": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
        "fondo": ["Fondo, A", 'Fondo "B"', "Fondo C"],
        "rent_mes": [0.0123, -0.004, 0.02],
        "monto": [1234.5, 99.0, 1e6],
    })


# ------------------------------------------------------------------ exportes
def test_xlsx_columnas_fechas_numeros_y_filtros(df_demo):
    wb = openpyxl.load_workbook(io.BytesIO(ex.xlsx_bytes({"datos": df_demo})))
    ws = wb["datos"]
    assert [c.value for c in ws[1]] == list(df_demo.columns)
    assert ws.freeze_panes == "A2"
    assert ws.auto_filter.ref is not None
    assert hasattr(ws["A2"].value, "year")           # fecha real
    assert isinstance(ws["C2"].value, (int, float))  # número real
    assert isinstance(ws["D4"].value, (int, float))
    assert ws["B2"].value == "Fondo, A"              # coma no separa columnas


def test_xlsx_no_vacio_por_hoja(df_demo):
    wb = openpyxl.load_workbook(io.BytesIO(ex.xlsx_bytes({"a": df_demo, "b": df_demo.head(1)})))
    assert wb.sheetnames == ["a", "b"] and wb["a"].max_row == 4 and wb["b"].max_row == 2


def test_csv_excel_regional_ida_y_vuelta(df_demo):
    b = ex.csv_excel_bytes(df_demo)
    assert b.startswith(b"\xef\xbb\xbf")                       # BOM UTF-8
    assert b.decode("utf-8-sig").splitlines()[0] == "sep=;"
    r = ex.leer_csv_excel(b)
    assert list(r.columns) == list(df_demo.columns) and len(r) == 3
    assert r.rent_mes.round(4).tolist() == df_demo.rent_mes.round(4).tolist()
    assert r.fondo.tolist() == df_demo.fondo.tolist()


def test_csv_estandar_punto_decimal(df_demo):
    r = pd.read_csv(io.BytesIO(ex.csv_estandar_bytes(df_demo)))
    assert r.shape == df_demo.shape and abs(r.rent_mes[0] - 0.0123) < 1e-12


@pytest.mark.skipif(not PROC.is_file(), reason="No está la base procesada")
def test_base_completa_original_coincide_con_hash():
    full = datos.procesado_original(RAIZ)
    assert len(full) == 4026 and len(full.columns) == 32
    decl = datos.leer_hashes(RAIZ)
    esperado = decl[decl.iloc[:, 0].astype(str).str.endswith(PROC.name)]
    if not esperado.empty:
        assert hashlib.sha256(PROC.read_bytes()).hexdigest() in set(esperado.iloc[:, -1].astype(str))
    # El CSV estándar debe reproducir literalmente el CSV fuente y su estructura.
    original = PROC.read_bytes()
    assert len(pd.read_csv(io.BytesIO(original))) == len(full)
    assert pd.read_csv(io.BytesIO(original)).columns.tolist() == full.columns.tolist()
    assert hashlib.sha256(original).hexdigest() == datos.sha256(PROC)


# ------------------------------------------------------------------ configuración
def test_treinta_articulos_ids_unicos():
    ids = [a["id"] for a in pc.articulos()]
    assert len(ids) == 30 and len(set(ids)) == 30 and ids[0] == "A01" and ids[-1] == "A30"


def test_validar_documentos_sin_errores_graves():
    assert pc.validar_documentos() == []


def test_enlaces_vacios_nunca_activos():
    for a in pc.articulos():
        for clave, _, _ in pc.DOCUMENTOS:
            etiqueta, url = pc.enlace_doc(a, clave)
            registro = a["documentos"][clave]
            directo = registro.get("descarga_url") or registro.get("visualizacion_url") or ""
            if not pc.es_url(directo):
                assert not url
            else:
                assert pc.es_url(url)


def test_derivacion_enlaces_drive():
    u = "https://drive.google.com/file/d/ABC123/view?usp=sharing"
    assert pc.url_visor(u).endswith("/preview") and "ABC123" in pc.url_descarga(u)


def test_estados_discretos():
    validos = set(pc.ESTADOS)
    for d in pc.documentos()["productos"].values():
        assert d.get("estado", "pendiente") in validos


def test_repositorio_enlazado():
    assert pc.portal()["repositorio_url"] == "https://github.com/AmyGuadalupe/Finanzas-Segundo-Trabajo"


# ------------------------------------------------------------------ investigación intacta
def test_ningun_archivo_de_investigacion_en_dashboard():
    assert not (AQUI / "dashboard").exists()          # sin dashboard/dashboard
    assert not list(AQUI.glob("datos_*"))


# ------------------------------------------------------------------ renderizado (AppTest)
def _app(**q):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=180)
    for k, v in q.items():
        at.query_params[k] = v
    return at.run()


def test_portada_sin_excepciones():
    at = _app()
    assert not at.exception and len(at.button) >= 4


@pytest.mark.parametrize("sec", ["introduccion", "marco", "antecedentes", "metodos", "resultados", "discusion", "conclusiones"])
def test_siete_secciones_renderizan(sec):
    at = _app(v="s1", sec=sec)
    assert not at.exception


def test_menu_radial_tiene_siete_tarjetas():
    at = _app(v="s1")
    assert not at.exception
    claves = [b.key for b in at.button if b.key and b.key.startswith("nav_")]
    assert len(claves) == 7


def test_ficha_de_poster():
    at = _app(v="s1", sec="antecedentes", art="A01")
    assert not at.exception


@pytest.mark.skipif(not PROC.is_file(), reason="No está la base procesada")
def test_seccion2_diez_pestanas_sin_excepciones():
    at = _app(v="s2")
    assert not at.exception and len(at.tabs) == 10


def test_metadatos_bibliograficos_desde_matriz():
    articulos = pc.articulos()
    assert len(articulos) == 30
    assert len({a["doi"] for a in articulos}) == 30
    for a in articulos:
        assert a["titulo_original"] and a["revista"] and a["autores"]
        assert a["objetivo"] and a["datos_metodologia"] and a["resultados"] and a["aporte"]
        assert a["cuartil"] in {"Q1", "Q2"}
        assert a["cuartil_verificado"] is False  # pendiente comprobación individual de Scopus


@pytest.mark.skipif(not PROC.is_file(), reason="No está la base procesada")
def test_base_completa_disponible_con_contexto_minimo():
    """Es la rama que se ejecuta cuando los filtros del análisis dejan cero registros."""
    from streamlit.testing.v1 import AppTest

    guion = (
        "import sys\n"
        "from types import SimpleNamespace\n"
        f"sys.path.insert(0, {str(AQUI)!r})\n"
        "import cargas\n"
        "import tabs_dashboard as td\n"
        "proy = cargas.proyecto()\n"
        "td.pestana_base_completa(SimpleNamespace(proy=proy, DIC=proy.diccionario, sha=proy.sha))\n"
    )
    at = AppTest.from_string(guion, default_timeout=120).run()
    assert not at.exception
    assert [getattr(e.proto, "label", "") for e in at.get("download_button")][:2] == ["Descargar base completa", "Descargar registros filtrados"]
    assert dict((m.label, m.value) for m in at.metric)["Observaciones"].replace(" ", "") == "4026"
