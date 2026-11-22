"""Cálculos financieros sobre el panel filtrado (funciones puras, sin Streamlit).

Definiciones idénticas a codigo/04_analisis.py para que, sin filtros, los
resultados coincidan con las tablas oficiales:
- Rentabilidad anualizada = exp(12 × media(ln(1+r))) − 1 (−100 % si algún r = −100 %).
- Volatilidad anualizada = desviación muestral (ddof=1) de r × √12.
- Sharpe anualizado = media(exceso) / desviación muestral(exceso) × √12,
  exceso = r − rf_mensual (tasa interbancaria de la moneda, proxy).
Medidas complementarias calculadas solo en el dashboard (no están en la
investigación): rentabilidad acumulada compuesta, Sortino y máxima caída.
Nunca se promedian rentabilidades de monedas distintas.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

MIN_MESES = 12  # mismo umbral que 04_analisis.py para anualizar
RAIZ12 = np.sqrt(12.0)
COLUMNAS_RETORNO = {
    "tratada": ("rent_mes", "exceso", "vol12"),
    "original": ("rent_original", "exceso_original", "vol12_original"),
}
ETIQUETA_RETORNO = {
    "tratada": "Retorno tratado (winsorizado, usado en la investigación)",
    "original": "Retorno original (antes de winsorizar)",
}


@dataclass(frozen=True)
class Filtros:
    tipos: tuple = ()
    monedas: tuple = ()
    administradoras: tuple = ()
    series: tuple = ()
    mes_ini: str = ""
    mes_fin: str = ""
    retorno: str = "tratada"

    def firma(self) -> str:
        return hashlib.sha1(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:12]

    def describir(self) -> dict:
        def lista(x, todos):
            return ", ".join(x) if x else todos
        return {
            "Periodo": f"{self.mes_ini} a {self.mes_fin}",
            "Tipo de fondo": lista(self.tipos, "Todos"),
            "Moneda": lista(self.monedas, "PEN y USD (siempre por separado)"),
            "Administradora": lista(self.administradoras, "Todas"),
            "Fondos-series": lista(self.series, "Todos los que cumplen los filtros"),
            "Serie de retorno": ETIQUETA_RETORNO[self.retorno],
        }


def aplicar_filtros(panel: pd.DataFrame, f: Filtros, con_periodo: bool = True) -> pd.DataFrame:
    """Selección vacía en una dimensión = sin restricción en esa dimensión."""
    m = pd.Series(True, index=panel.index)
    if f.tipos:
        m &= panel.tipo.isin(f.tipos)
    if f.monedas:
        m &= panel.moneda.isin(f.monedas)
    if f.administradoras:
        m &= panel.administradora.isin(f.administradoras)
    if f.series:
        m &= panel.id_fondo_serie.isin(f.series)
    if con_periodo and f.mes_ini and f.mes_fin:
        m &= panel.mes.between(f.mes_ini, f.mes_fin)
    return panel.loc[m].copy()


def _anualizada(r: np.ndarray) -> float:
    if (r == -1).any():
        return -1.0
    return float(np.expm1(np.log1p(r).mean() * 12))


def metricas_por_serie(df: pd.DataFrame, retorno: str = "tratada", min_meses: int = MIN_MESES) -> pd.DataFrame:
    r_col, e_col, _ = COLUMNAS_RETORNO[retorno]
    filas = []
    for id_, g in df.sort_values("mes").groupby("id_fondo_serie", sort=True):
        r = g[r_col].to_numpy(float)
        e = g[e_col].to_numpy(float)
        n = len(r)
        indice = np.cumprod(1 + r)
        pico = np.maximum.accumulate(np.r_[1.0, indice])[1:]
        fila = {
            "id_fondo_serie": id_,
            "etiqueta": g.etiqueta.iloc[0],
            "tipo": g.tipo.iloc[0],
            "moneda": g.moneda.iloc[0],
            "administradora": g.administradora.iloc[0],
            "mes_inicio": g.mes.iloc[0],
            "mes_fin": g.mes.iloc[-1],
            "n_meses": n,
            "rent_acumulada": float(indice[-1] - 1),
            "rent_anualizada": np.nan,
            "vol_anualizada": np.nan,
            "sharpe_anualizado": np.nan,
            "sortino_anualizado": np.nan,
            "max_caida": float((indice / pico - 1).min()),
            "meses_con_perdida": float((r < 0).mean()),
            "meses_interpolados": int(g.imputado.sum()),
            "meses_winsorizados": int(g.atipico.sum()),
        }
        if n >= min_meses:
            sd_e = e.std(ddof=1)
            abajo = np.sqrt(np.mean(np.minimum(e, 0.0) ** 2))
            fila.update(
                rent_anualizada=_anualizada(r),
                vol_anualizada=float(r.std(ddof=1) * RAIZ12),
                sharpe_anualizado=float(e.mean() / sd_e * RAIZ12) if sd_e > 0 else np.nan,
                sortino_anualizado=float(e.mean() / abajo * RAIZ12) if abajo > 0 else np.nan,
            )
        filas.append(fila)
    return pd.DataFrame(filas)


def resumen_por_categoria(m: pd.DataFrame) -> pd.DataFrame:
    """Medianas entre fondos-series (igual peso por serie, no por patrimonio)."""
    if m.empty:
        return pd.DataFrame()
    q = lambda p: (lambda x: x.quantile(p))  # noqa: E731
    out = (
        m.groupby(["tipo", "moneda"])
        .agg(
            unidades=("id_fondo_serie", "nunique"),
            rent_acumulada_mediana=("rent_acumulada", "median"),
            rent_mediana=("rent_anualizada", "median"),
            vol_mediana=("vol_anualizada", "median"),
            sharpe_mediana=("sharpe_anualizado", "median"),
            sharpe_q25=("sharpe_anualizado", q(0.25)),
            sharpe_q75=("sharpe_anualizado", q(0.75)),
            sortino_mediana=("sortino_anualizado", "median"),
            max_caida_mediana=("max_caida", "median"),
            meses_perdida_mediana=("meses_con_perdida", "median"),
        )
        .reset_index()
    )
    return out


def descriptivos(df: pd.DataFrame, retorno: str = "tratada") -> pd.DataFrame:
    """Estadísticos de la rentabilidad mensual por tipo y moneda (como tabla16)."""
    r_col = COLUMNAS_RETORNO[retorno][0]
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby(["tipo", "moneda"])[r_col]
        .agg(
            n="size", media="mean", mediana="median", desv="std",
            p05=lambda x: x.quantile(0.05), p95=lambda x: x.quantile(0.95), minimo="min", maximo="max",
        )
        .reset_index()
        .merge(df.groupby(["tipo", "moneda"]).id_fondo_serie.nunique().rename("series").reset_index(), on=["tipo", "moneda"])
    )


def rent_mensual_categoria(df: pd.DataFrame, retorno: str = "tratada") -> pd.DataFrame:
    """Promedio simple mensual por tipo y moneda (como tabla8)."""
    r_col = COLUMNAS_RETORNO[retorno][0]
    return (
        df.groupby(["mes", "fecha", "tipo", "moneda"])
        .agg(rent=(r_col, "mean"), series=("id_fondo_serie", "nunique"),
             interpoladas=("imputado", "sum"), winsorizadas=("atipico", "sum"))
        .reset_index()
    )


def _base_100(g: pd.DataFrame, col: str) -> pd.DataFrame:
    g = g.sort_values("fecha")
    valores = 100 * np.cumprod(1 + g[col].to_numpy(float))
    base = g.iloc[[0]].copy()
    base["fecha"] = base.fecha - pd.offsets.MonthBegin(1)
    base["mes"] = base.fecha.dt.strftime("%Y-%m")
    base["indice"] = 100.0
    base["es_base"] = True
    g = g.assign(indice=valores, es_base=False)
    return pd.concat([base, g], ignore_index=True)


def indice_acumulado(df: pd.DataFrame, retorno: str, nivel: str) -> pd.DataFrame:
    """Índice base 100 al inicio del periodo, por capitalización compuesta.

    nivel='serie': cada fondo-serie. nivel='categoria': cartera de igual
    ponderación por tipo y moneda, rebalanceada cada mes (no por patrimonio).
    """
    r_col = COLUMNAS_RETORNO[retorno][0]
    if df.empty:
        return pd.DataFrame()
    if nivel == "serie":
        cols = ["id_fondo_serie", "etiqueta", "tipo", "moneda", "fecha", "mes", r_col, "estado_dato"]
        return pd.concat([_base_100(g[cols], r_col) for _, g in df.groupby("id_fondo_serie")], ignore_index=True)
    cat = rent_mensual_categoria(df, retorno)
    return pd.concat([_base_100(g, "rent") for _, g in cat.groupby(["tipo", "moneda"])], ignore_index=True)


def caidas(indice: pd.DataFrame, claves: list[str]) -> pd.DataFrame:
    """Caída desde el máximo previo del índice acumulado."""
    if indice.empty:
        return indice
    out = indice.sort_values("fecha").copy()
    out["caida"] = out.indice / out.groupby(claves).indice.cummax() - 1
    return out


def volatilidad_historica(df: pd.DataFrame, retorno: str, nivel: str) -> pd.DataFrame:
    """X1 de la investigación (desviación de los 12 meses previos) anualizada ×√12."""
    v_col = COLUMNAS_RETORNO[retorno][2]
    d = df.assign(vol_anual=df[v_col] * RAIZ12)
    if nivel == "serie":
        return d[["id_fondo_serie", "etiqueta", "tipo", "moneda", "fecha", "mes", "vol_anual", "historia_n"]]
    return (
        d.groupby(["mes", "fecha", "tipo", "moneda"])
        .agg(vol_anual=("vol_anual", "median"), series=("id_fondo_serie", "nunique"))
        .reset_index()
    )


def linea_tiempo(df_sin_periodo: pd.DataFrame, retorno: str) -> pd.DataFrame:
    """Rentabilidad mensual promedio (igual peso) por moneda, periodo completo."""
    r_col = COLUMNAS_RETORNO[retorno][0]
    return (
        df_sin_periodo.groupby(["mes", "fecha", "moneda"])
        .agg(rent=(r_col, "mean"), series=("id_fondo_serie", "nunique"))
        .reset_index()
    )


def calidad(df: pd.DataFrame) -> dict:
    n = len(df)
    conteo = df.estado_dato.value_counts().to_dict()
    return {
        "filas": n,
        "series": df.id_fondo_serie.nunique(),
        "meses": df.mes.nunique(),
        "observadas": int(conteo.get("Observado", 0)),
        "interpoladas": int(df.imputado.sum()),
        "winsorizadas": int(df.atipico.sum()),
        "ambas": int(conteo.get("Interpolado y winsorizado", 0)),
        "faltantes": int(df.isna().sum().sum()),
        "pct_interpoladas": float(df.imputado.mean()) if n else 0.0,
        "pct_winsorizadas": float(df.atipico.mean()) if n else 0.0,
    }


def kpis_por_moneda(df: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Indicadores de cabecera, siempre separados por moneda."""
    filas = []
    for mon in sorted(df.moneda.unique()):
        d = df[df.moneda.eq(mon)]
        mm = m[m.moneda.eq(mon)]
        filas.append({
            "moneda": mon,
            "series": d.id_fondo_serie.nunique(),
            "observaciones": len(d),
            "meses": d.mes.nunique(),
            "rent_acumulada_mediana": mm.rent_acumulada.median(),
            "rent_anualizada_mediana": mm.rent_anualizada.median(),
            "vol_anualizada_mediana": mm.vol_anualizada.median(),
            "sharpe_mediana": mm.sharpe_anualizado.median(),
            "max_caida_mediana": mm.max_caida.median(),
            "pct_interpoladas": d.imputado.mean(),
            "pct_winsorizadas": d.atipico.mean(),
        })
    return pd.DataFrame(filas)
