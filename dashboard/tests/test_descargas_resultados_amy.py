"""Pruebas de las descargas de resultados oficiales, sin conexión y sin editar datos."""
from __future__ import annotations

import io
from zipfile import ZipFile

import pandas as pd
from pandas.testing import assert_frame_equal

import exportes
from vistas.descargas_resultados import listar_tablas, paquete_csv_original


def test_csv_original_y_zip_sin_alteracion(tmp_path):
    salida = tmp_path / 'salidas'
    salida.mkdir()
    original = b'tipo,mes,valor\nDeuda,2020-08,1.25\n'
    archivo = salida / 'tabla3_modelo_principal.csv'
    archivo.write_bytes(original)
    assert listar_tablas(tmp_path) == [archivo]
    firma = ((str(archivo), archivo.stat().st_mtime_ns, archivo.stat().st_size),)
    with ZipFile(io.BytesIO(paquete_csv_original(firma))) as z:
        assert z.namelist() == [archivo.name]
        assert z.read(archivo.name) == original


def test_csv_excel_peru_lectura_regional():
    original = pd.DataFrame({'categoria': ['Acciones', 'Deuda'], 'volatilidad': [0.125, 1.2345]})
    b = exportes.csv_excel_bytes(original)
    assert b.decode('utf-8-sig').startswith('sep=;\n')
    destino = exportes.leer_csv_excel(b)
    assert_frame_equal(original, destino, check_dtype=False)
