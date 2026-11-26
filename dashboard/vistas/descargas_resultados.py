"""Descarga verificable de CSV originales de las tablas del pipeline.

Separación crucial: las tablas oficiales de /salidas son independientes de
los filtros exploratorios del dashboard; sus CSV no se reestiman ni alteran.
"""
from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
import streamlit as st
import exportes

ETIQUETAS = {
    'tabla1_metricas_por_fondo_serie': 'Tabla 1 · Métricas por fondo-serie',
    'tabla2_riesgo_rentabilidad_por_tipo': 'Tabla 2 · Rentabilidad, riesgo y Sharpe por tipo',
    'tabla3_modelo_principal': 'Tabla 3 · Modelo econométrico principal',
    'tabla14_contrastes_tipo': 'Tabla 14 · Contrastes frente a Deuda',
    'tabla23_indice_riqueza': 'Tabla 23 · Índice de riqueza y caídas',
    'tabla24_diferencias_mensuales_deuda': 'Tabla 24 · Diferencias mensuales frente a Deuda',
    'tabla25_regresion_parcial_mensual': 'Tabla 25 · Regresión parcial mensual',
}


def listar_tablas(raiz: Path) -> list[Path]:
    """Solo CSV oficiales con prefijo tabla, no el panel ni archivos crudos."""
    salida = Path(raiz) / 'salidas'
    return sorted((p for p in salida.glob('tabla*.csv') if p.is_file()), key=lambda p: p.name)


@lru_cache(maxsize=6)
def paquete_csv_original(firma: tuple[tuple[str, int, int], ...]) -> bytes:
    """Empaqueta bytes originales con nombres intactos y sin transformaciones."""
    memoria = io.BytesIO()
    with ZipFile(memoria, 'w', compression=ZIP_DEFLATED) as z:
        for path, _mtime, _size in firma:
            archivo = Path(path)
            z.writestr(archivo.name, archivo.read_bytes())
    return memoria.getvalue()


def mostrar(proy) -> None:
    """Accesible desde Resultados sin cambiar ninguna tabla existente."""
    tablas = listar_tablas(proy.raiz)
    with st.expander('Descargar las tablas oficiales (CSV / Excel)', expanded=False):
        st.caption('Archivos originales del pipeline, sin filtros del dashboard. Los CSV se descargan completos.')
        if not tablas:
            st.warning('No se encontraron tablas CSV en salidas/. Revise el enlace de la Carpeta N.º 3.')
            return
        rutas = {p.stem: p for p in tablas}
        preferida = 'tabla2_riesgo_rentabilidad_por_tipo'
        opciones = list(rutas)
        seleccion = st.selectbox('Elegir tabla de resultados', opciones,
                                  index=opciones.index(preferida) if preferida in opciones else 0,
                                  format_func=lambda x: ETIQUETAS.get(x, x.replace('_', ' ').capitalize()),
                                  key='descarga_tabla_oficial')
        ruta = rutas[seleccion]
        originales = ruta.read_bytes()
        marco = pd.read_csv(io.BytesIO(originales), encoding='utf-8-sig')
        st.caption(f'{len(marco):,} filas · {len(marco.columns)} columnas · {ruta.name}'.replace(',', ' '))
        st.dataframe(marco.head(8), hide_index=True, width='stretch')
        c1, c2 = st.columns(2)
        c1.download_button('CSV original (Python / R)', data=originales, file_name=ruta.name,
                           mime='text/csv', key='desc_csv_original', icon=':material/download:', width='stretch')
        c2.download_button('CSV para Excel de Perú', data=exportes.csv_excel_bytes(marco),
                           file_name=f'{ruta.stem}_excel_peru.csv', mime='text/csv',
                           key='desc_csv_peru', icon=':material/download:', width='stretch')
        firma = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in tablas)
        st.download_button(f'Descargar todas las tablas oficiales ({len(tablas)} CSV) en ZIP',
                           data=paquete_csv_original(firma), file_name='resultados_oficiales_csv.zip',
                           mime='application/zip', key='desc_todas_tablas_csv',
                           icon=':material/folder_zip:', width='stretch')
        st.caption('El CSV original preserva exactamente los bytes de salidas/. El archivo para Excel '
                   'utiliza punto y coma, coma decimal y UTF-8 con BOM; es una copia de visualización.')
