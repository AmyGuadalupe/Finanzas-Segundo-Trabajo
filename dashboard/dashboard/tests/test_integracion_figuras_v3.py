"""Regresión de integración entre salidas de Claude y dashboard.
No modifica la investigación ni requiere descargar boletines.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

DASH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASH))
import catalogo_figuras as cf
import datos
import nav

RAIZ = datos.localizar_proyecto()


def test_archivos_figuras_oficiales_presentes():
    assert cf.nueva_version_completa(RAIZ)
    assert all(cf.resolver(RAIZ, f)[2] for f in cf.FIGURAS)


@pytest.mark.parametrize("nombre", ["tabla23_indice_riqueza", "tabla24_diferencias_mensuales_deuda", "tabla25_regresion_parcial_mensual"])
def test_tablas_soporte_disponibles_con_sus_columnas(nombre):
    t = datos.cargar_tabla(RAIZ, nombre)
    assert t is not None and len(t) > 0


def test_figuras_versión_anterior_tienen_rotulo_correcto(tmp_path):
    s = tmp_path / "salidas"
    s.mkdir()
    (s / "figura2_sharpe_por_tipo.png").write_bytes(b"antigua")
    r, titulo, nueva = cf.resolver(tmp_path, cf.FIGURAS[1])
    assert r.name == "figura2_sharpe_por_tipo.png" and not nueva
    assert "Sharpe" in titulo and "Índice de riqueza" not in titulo


def test_navegacion_boton_siguiente_y_anterior():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(DASH / "app.py"), default_timeout=90)
    at.query_params["v"] = "s1"
    at.query_params["sec"] = "introduccion"
    at.run()
    assert not at.exception
    assert at.button(key="p_sig")
    at.button(key="p_sig").click().run()
    assert not at.exception
    assert at.query_params.get("sec") == "marco" or any("Marco teórico" in m.value for m in at.markdown)
    at.button(key="p_ant").click().run()
    assert not at.exception
    assert at.query_params.get("sec") == "introduccion" or any("Introducción" in m.value for m in at.markdown)
