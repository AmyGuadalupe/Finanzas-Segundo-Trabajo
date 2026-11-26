"""Pruebas de las 30 fichas bibliográficas: metadatos, DOI y navegación."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))

import portal_config as pc  # noqa: E402

ARTS = pc.articulos()


def test_treinta_fichas_con_metadatos_minimos():
    assert len(ARTS) == 30
    for a in ARTS:
        for campo in ("titulo_original", "autores", "anio", "revista", "doi", "referencia_apa", "objetivo", "resultados"):
            assert str(a.get(campo, "")).strip(), (a["id"], campo)


def test_doi_con_formato_valido_y_unicos():
    dois = [str(a["doi"]).replace("https://doi.org/", "").strip() for a in ARTS]
    assert all(re.fullmatch(r"10\.\d{4,9}/\S+", d) for d in dois)
    assert len(set(dois)) == 30
    assert all(pc.url_doi(a["doi"]).startswith("https://doi.org/10.") for a in ARTS)


def test_cuartil_no_se_declara_verificado():
    assert all(a.get("cuartil_verificado") is False for a in ARTS)


@pytest.mark.parametrize("n", range(1, 31))
def test_ficha_renderiza(n):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(AQUI / "app.py"), default_timeout=120)
    at.query_params["v"] = "s1"; at.query_params["sec"] = "antecedentes"; at.query_params["art"] = f"A{n:02d}"
    at.run()
    assert not at.exception
    etiquetas = [b.label for b in at.button]
    assert "Póster anterior" in etiquetas and "Póster siguiente" in etiquetas
