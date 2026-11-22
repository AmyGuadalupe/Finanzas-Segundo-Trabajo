"""Construcción de archivos descargables a partir de los datos YA filtrados.

Ninguna función lee el panel completo: todas reciben los DataFrames que el
dashboard filtró con la línea de tiempo y los selectores activos.
"""
from __future__ import annotations

import base64
import html
import io
import zipfile
from datetime import datetime, timedelta, timezone

import pandas as pd

HORA_PERU = timezone(timedelta(hours=-5))

COLUMNAS_PORCENTAJE = {
    "rent_acumulada", "rent_anualizada", "vol_anualizada", "max_caida", "meses_con_perdida",
    "rent_acumulada_mediana", "rent_mediana", "vol_mediana", "max_caida_mediana", "meses_perdida_mediana",
    "media", "mediana", "desv", "p05", "p95", "minimo", "maximo", "rent_anualizada_mediana",
    "vol_anualizada_mediana", "pct_interpoladas", "pct_winsorizadas",
}

NOMBRES_COLUMNAS = {
    "id_fondo_serie": "Fondo-serie (llave)", "etiqueta": "Fondo-serie", "tipo": "Tipo", "moneda": "Moneda",
    "administradora": "Administradora", "mes_inicio": "Desde", "mes_fin": "Hasta", "n_meses": "Meses",
    "rent_acumulada": "Rent. acumulada", "rent_anualizada": "Rent. anualizada", "vol_anualizada": "Vol. anualizada",
    "sharpe_anualizado": "Sharpe", "sortino_anualizado": "Sortino", "max_caida": "Máx. caída",
    "meses_con_perdida": "% meses con pérdida", "meses_interpolados": "Meses interpolados",
    "meses_winsorizados": "Meses winsorizados", "unidades": "Series", "rent_acumulada_mediana": "Rent. acumulada (mediana)",
    "rent_mediana": "Rent. anualizada (mediana)", "vol_mediana": "Vol. anualizada (mediana)",
    "sharpe_mediana": "Sharpe (mediana)", "sharpe_q25": "Sharpe Q1", "sharpe_q75": "Sharpe Q3",
    "sortino_mediana": "Sortino (mediana)", "max_caida_mediana": "Máx. caída (mediana)",
    "meses_perdida_mediana": "% meses con pérdida (mediana)", "n": "Obs.", "series": "Series", "media": "Media",
    "mediana": "Mediana", "desv": "Desv. estándar", "p05": "P5", "p95": "P95", "minimo": "Mínimo", "maximo": "Máximo",
    "variable": "Variable", "coeficiente": "Coeficiente", "error_estandar": "Error estándar", "p_valor": "Valor p",
    "ic95_inf": "IC 95 % inf.", "ic95_sup": "IC 95 % sup.", "inferencia_valida": "Inferencia válida",
    "observaciones": "Observaciones", "meses": "Meses", "rent_anualizada_mediana": "Rent. anualizada (mediana)",
    "vol_anualizada_mediana": "Vol. anualizada (mediana)", "pct_interpoladas": "% interpoladas",
    "pct_winsorizadas": "% winsorizadas",
}


def ahora_peru() -> str:
    return datetime.now(HORA_PERU).strftime("%Y-%m-%d %H:%M (hora de Lima)")


def csv_bytes(df: pd.DataFrame) -> bytes:
    # utf-8-sig para que Excel en español abra tildes correctamente; punto decimal.
    return df.to_csv(index=False, float_format="%.10g").encode("utf-8-sig")


def excel_bytes(hojas: dict[str, pd.DataFrame]) -> bytes:
    """Libro Excel con una hoja por tabla (motor xlsxwriter, más rápido que openpyxl)."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        for nombre, df in hojas.items():
            hoja = nombre[:31]
            df.to_excel(w, sheet_name=hoja, index=False)
            ws = w.sheets[hoja]
            ws.freeze_panes(1, 0)
            for i, col in enumerate(df.columns):
                largo = max([len(str(col))] + [len(str(v)) for v in df[col].head(200).tolist()])
                ws.set_column(i, i, min(60, max(10, largo + 2)))
    return buf.getvalue()


def zip_bytes(archivos: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for nombre, datos in archivos.items():
            z.writestr(nombre, datos)
    return buf.getvalue()


def png_bytes(fig, ancho: int = 1400, escala: float = 2.0) -> bytes:
    """PNG de alta resolución (por defecto 2800 px de ancho) con Kaleido."""
    alto = int(fig.layout.height or 450)
    return fig.to_image(format="png", width=ancho, height=alto, scale=escala, engine="kaleido")


def hoja_filtros(descripcion: dict, extra: dict) -> pd.DataFrame:
    filas = [{"Campo": k, "Valor": v} for k, v in descripcion.items()]
    filas += [{"Campo": k, "Valor": v} for k, v in extra.items()]
    return pd.DataFrame(filas)


def formatear(df: pd.DataFrame) -> pd.DataFrame:
    """Versión legible (porcentajes y decimales) para el reporte HTML."""
    out = df.copy()
    for c in out.columns:
        if c in COLUMNAS_PORCENTAJE and pd.api.types.is_numeric_dtype(out[c]):
            out[c] = out[c].map(lambda v: "" if pd.isna(v) else f"{100 * v:.2f} %")
        elif pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].map(lambda v: "" if pd.isna(v) else f"{v:.4f}")
    return out.rename(columns=NOMBRES_COLUMNAS)


def _tabla_html(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "<p class='nota'>Sin filas para los filtros elegidos.</p>"
    return formatear(df).to_html(index=False, border=0, classes="tabla", escape=True, na_rep="")


def reporte_html(titulo: str, filtros: dict, extra: dict, secciones: list[tuple[str, str, object]],
                 figuras: list[tuple[str, bytes | str]], advertencia: str) -> str:
    """secciones: (titulo, texto_markdown_simple, DataFrame|None). figuras: (titulo, png|html)."""
    css = """
    body{font-family:Inter,'Segoe UI',system-ui,sans-serif;color:#0b0b0b;background:#fcfcfb;margin:0;padding:32px;max-width:1100px;margin:auto}
    h1{font-size:24px;margin:0 0 4px} h2{font-size:18px;margin:32px 0 8px;border-bottom:1px solid #ebeae6;padding-bottom:6px}
    .sub{color:#52514e;margin:0 0 20px} .nota{color:#52514e;font-size:13px}
    table.tabla{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0 16px}
    table.tabla th{background:#f3f2ee;text-align:left;padding:6px 8px;border-bottom:1px solid #d6d5d0}
    table.tabla td{padding:5px 8px;border-bottom:1px solid #ebeae6;font-variant-numeric:tabular-nums}
    figure{margin:16px 0 28px;page-break-inside:avoid} figure img{width:100%;border:1px solid #ebeae6;border-radius:8px}
    figcaption{font-size:12px;color:#52514e;margin-top:4px} .aviso{background:#f3f2ee;border-left:3px solid #2a78d6;padding:10px 14px;font-size:13px}
    @media print{body{padding:0} h2{page-break-after:avoid}}
    """
    partes = [f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'><title>{html.escape(titulo)}</title><style>{css}</style></head><body>",
              f"<h1>{html.escape(titulo)}</h1><p class='sub'>Generado el {ahora_peru()} desde el dashboard. Fuentes: AAF (boletines mensuales) y BCRPData (API).</p>",
              "<h2>Filtros aplicados</h2>", _tabla_html(hoja_filtros(filtros, extra).rename(columns=str))]
    for t, texto, tabla in secciones:
        partes.append(f"<h2>{html.escape(t)}</h2>")
        if texto:
            for parrafo in str(texto).split("\n\n"):
                p = html.escape(parrafo).replace("**", "")
                partes.append(f"<p class='nota'>{p}</p>")
        if isinstance(tabla, pd.DataFrame):
            partes.append(_tabla_html(tabla))
    if figuras:
        partes.append("<h2>Gráficos</h2>")
        for t, contenido in figuras:
            if isinstance(contenido, bytes):
                b64 = base64.b64encode(contenido).decode()
                partes.append(f"<figure><img alt='{html.escape(t)}' src='data:image/png;base64,{b64}'><figcaption>{html.escape(t)}</figcaption></figure>")
            else:
                partes.append(f"<figure>{contenido}<figcaption>{html.escape(t)}</figcaption></figure>")
    partes.append(f"<h2>Advertencias de interpretación</h2><div class='aviso'>{html.escape(advertencia)}</div></body></html>")
    return "\n".join(partes)
