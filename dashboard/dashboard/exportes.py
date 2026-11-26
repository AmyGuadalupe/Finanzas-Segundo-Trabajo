"""Exportaciones verificadas: Excel nativo (XLSX), CSV para Excel regional, CSV estándar y gráficos.

Corrige el problema de las versiones anteriores: un CSV separado por comas abierto en un Excel configurado
con coma decimal mostraba todo en una sola columna. Aquí:

* XLSX nativo (formato principal): columnas independientes, fechas reales, números como números,
  porcentajes con formato de porcentaje (el valor guardado conserva toda la precisión), filtros de
  encabezado, primera fila inmovilizada y anchos de columna adecuados.
* CSV para Excel (regional): UTF-8 con BOM, separador «;», coma decimal y la directiva «sep=;» en la
  primera línea, de modo que Excel separe las columnas en cualquier configuración regional.
* CSV estándar (Python y reproducibilidad): UTF-8 sin BOM, separador «,» y punto decimal.
"""
from __future__ import annotations

import io

import pandas as pd

# Columnas del panel que están en decimal (0,01 = 1 %): Excel las muestra como porcentaje.
PCT_PANEL = {"rent_mes", "rent_original", "rf_mensual", "rf_pen", "rf_usd", "exceso", "vol12", "vol12_original",
             "rent_lag1", "rent_lag1_original", "var_tc"}
PCT_TABLAS = {
    "rent_acumulada", "rent_anualizada", "vol_anualizada", "max_caida", "meses_con_perdida", "rent_acumulada_mediana",
    "rent_mediana", "vol_mediana", "max_caida_mediana", "meses_perdida_mediana", "media", "mediana", "desv", "p05", "p95",
    "minimo", "maximo", "rent_anualizada_mediana", "vol_anualizada_mediana", "pct_interpoladas", "pct_winsorizadas", "rent",
}
PORCENTAJES = PCT_PANEL | PCT_TABLAS
ENTEROS = {"pagina", "atipico", "imputado", "muestra_modelo", "historia_imputada", "historia_atipica", "historia_n", "n", "series",
           "observaciones", "meses", "n_meses", "unidades", "fondos_series"}


def con_fechas(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte «mes» (AAAA-MM) en fecha real (primer día del mes) para que Excel la reconozca."""
    d = df.copy()
    for c in ("mes", "inicio", "fin", "mes_inicio", "mes_fin"):
        if c in d and (d[c].dtype == object or str(d[c].dtype).startswith("str")):
            conv = pd.to_datetime(d[c].astype(str) + "-01", format="%Y-%m-%d", errors="coerce")
            if conv.notna().all():
                d[c] = conv
    return d


def xlsx_bytes(hojas: dict[str, pd.DataFrame], notas: dict[str, str] | None = None, texto_inicial: dict[str, pd.DataFrame] | None = None) -> bytes:
    """Libro de Excel nativo. `hojas`: nombre → DataFrame. `notas`: columna → comentario del encabezado."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter", datetime_format="mmm-yyyy", date_format="mmm-yyyy") as w:
        libro = w.book
        f_cab = libro.add_format({"bold": True, "bg_color": "#1D2A44", "font_color": "#FFFFFF", "border": 1, "valign": "vcenter"})
        f_pct = libro.add_format({"num_format": "0.00%"})
        f_num = libro.add_format({"num_format": "0.0000"})
        f_ent = libro.add_format({"num_format": "0"})
        f_fecha = libro.add_format({"num_format": "mmm-yyyy"})
        for nombre, df in hojas.items():
            d = con_fechas(df).reset_index(drop=True)
            hoja = nombre[:31]
            d.to_excel(w, sheet_name=hoja, index=False)
            ws = w.sheets[hoja]
            n = len(d)
            for j, col in enumerate(d.columns):
                ws.write(0, j, col, f_cab)
                if notas and col in notas:
                    ws.write_comment(0, j, notas[col], {"x_scale": 2.2, "y_scale": 1.6})
                serie = d[col]
                if pd.api.types.is_datetime64_any_dtype(serie):
                    formato, ancho = f_fecha, 12
                elif pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_bool_dtype(serie):
                    if col in PORCENTAJES and pd.api.types.is_float_dtype(serie):
                        formato = f_pct
                    elif col in ENTEROS or pd.api.types.is_integer_dtype(serie):
                        formato = f_ent
                    else:
                        formato = f_num
                    ancho = max(11, len(str(col)) + 3)
                else:
                    formato = None
                    largo = max([len(str(col))] + [len(str(v)) for v in serie.head(300).tolist()])
                    ancho = min(60, max(10, largo + 2))
                ws.set_column(j, j, max(ancho, len(str(col)) + 3), formato)
            if len(d.columns):
                ws.autofilter(0, 0, max(n, 1), len(d.columns) - 1)
            ws.freeze_panes(1, 0)
    return buf.getvalue()


def csv_estandar_bytes(df: pd.DataFrame) -> bytes:
    """UTF-8, coma como separador y punto decimal: para Python/R y reproducibilidad."""
    return df.to_csv(index=False).encode("utf-8")


def csv_excel_bytes(df: pd.DataFrame) -> bytes:
    """UTF-8 con BOM, separador «;», coma decimal y directiva «sep=;» (Excel separa las columnas en cualquier región)."""
    cuerpo = df.to_csv(index=False, sep=";", decimal=",")
    return ("﻿" + "sep=;\n" + cuerpo).encode("utf-8")


def leer_csv_excel(datos: bytes, **kw) -> pd.DataFrame:
    """Lee de vuelta un CSV generado con csv_excel_bytes (para pruebas y para quien lo cargue en Python)."""
    return pd.read_csv(io.BytesIO(datos), sep=";", decimal=",", skiprows=1, encoding="utf-8-sig", **kw)


# ------------------------------------------------------------------ gráficos
def grafico_bytes(fig, formato: str, nota_fig=None, ancho: int = 1400, escala: float = 2.0, plotly_js: str | bool = True) -> bytes:
    """Gráfico exportado: png (alta resolución), svg (vectorial) o html (interactivo)."""
    if formato == "html":
        return fig.to_html(full_html=True, include_plotlyjs=plotly_js, config={"displaylogo": False, "responsive": True}).encode("utf-8")
    alto = int(fig.layout.height or 450)
    if formato == "svg":
        return fig.to_image(format="svg", width=ancho, height=alto, engine="kaleido")
    return fig.to_image(format="png", width=ancho, height=alto, scale=escala, engine="kaleido")
