"""Reestimación exploratoria del modelo de la investigación sobre el subconjunto filtrado.

Misma especificación y misma inferencia que codigo/04_analisis.py:
  rent_mes ~ vol12 + var_tc + rent_lag1 + C(tipo) + C(moneda)
  MCO con errores estándar agrupados en dos vías (fondo-serie y mes),
  use_correction=True, df_correction=True, distribución t.
Sin filtros, el resultado coincide con salidas/tabla3_modelo_principal.csv;
con la serie original coincide con el bloque "misma_muestra_sin_winsorizar"
de salidas/tabla5_robustez.csv. Los controles C(tipo) y C(moneda) se omiten
solo cuando el filtro deja una única categoría (serían constantes).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

FACTORES = ["vol12", "var_tc", "rent_lag1"]
NOMBRES = {
    "vol12": "Volatilidad histórica de 12 meses (X1, vol12)",
    "var_tc": "Variación del tipo de cambio (X2, var_tc)",
    "rent_lag1": "Rentabilidad del mes previo (X3, rent_lag1)",
}
DESCRIPCION = {
    "vol12": "la volatilidad mensual de los 12 meses previos",
    "var_tc": "la variación logarítmica mensual del tipo de cambio (depreciación del sol)",
    "rent_lag1": "la rentabilidad del mes anterior de la misma serie",
}


def preparar(df: pd.DataFrame, retorno: str) -> pd.DataFrame:
    d = df.copy()
    if retorno == "original":
        d[["rent_mes", "vol12", "rent_lag1"]] = d[["rent_original", "vol12_original", "rent_lag1_original"]].to_numpy()
    return d


def estimar(df: pd.DataFrame, retorno: str = "tratada") -> dict:
    d = preparar(df, retorno)
    res = {"ok": False, "advertencias": [], "tabla": pd.DataFrame(), "n": len(d),
           "series": d.id_fondo_serie.nunique(), "meses": d.mes.nunique()}
    if res["series"] < 2 or res["meses"] < 3:
        res["advertencias"].append("Se necesitan al menos 2 fondos-series y 3 meses para estimar con errores agrupados en dos vías.")
        return res
    controles = []
    if d.tipo.nunique() > 1:
        controles.append("C(tipo)")
    if d.moneda.nunique() > 1:
        controles.append("C(moneda)")
    formula = "rent_mes ~ " + " + ".join(FACTORES + controles)
    if d.var_tc.nunique() < 2:
        res["advertencias"].append("var_tc no varía en el periodo elegido; amplía la línea de tiempo.")
        return res
    ajuste = smf.ols(formula, data=d).fit()
    exog = ajuste.model.exog
    if np.linalg.matrix_rank(exog) < exog.shape[1] or len(d) <= exog.shape[1] + 1:
        res["advertencias"].append("El modelo no tiene rango completo con este filtro (variables colineales o muy pocas filas).")
        return res
    grupos = np.column_stack([pd.factorize(d.id_fondo_serie)[0], pd.factorize(d.mes)[0]])
    with warnings.catch_warnings():  # varianza no definida: se informa como faltante, no como error
        warnings.simplefilter("ignore", RuntimeWarning)
        rob = ajuste.get_robustcov_results(cov_type="cluster", groups=grupos, use_correction=True, df_correction=True, use_t=True)
        ic = rob.conf_int()
    tabla = pd.DataFrame({
        "variable": ajuste.model.exog_names,
        "coeficiente": rob.params,
        "error_estandar": rob.bse,
        "p_valor": rob.pvalues,
        "ic95_inf": ic[:, 0],
        "ic95_sup": ic[:, 1],
    })
    tabla["inferencia_valida"] = np.isfinite(tabla.error_estandar) & (tabla.error_estandar > 0)
    res.update(ok=True, tabla=tabla, formula=formula, r2=float(ajuste.rsquared),
               gl=int(min(res["series"], res["meses"]) - 1), error_mco=ajuste.bse.to_numpy())
    if not tabla.inferencia_valida.all():
        res["advertencias"].append("La varianza agrupada en dos vías no es estimable para algún coeficiente; esos errores se muestran como faltantes.")
    if res["meses"] < 24:
        res["advertencias"].append(f"Solo {res['meses']} meses: var_tc es común a todas las series de un mes, por lo que su precisión depende del número de meses, no de las filas.")
    if res["series"] < 10:
        res["advertencias"].append(f"Solo {res['series']} fondos-series: los errores agrupados por serie son poco fiables con tan pocos grupos.")
    return res


def interpretar(tabla: pd.DataFrame) -> list[str]:
    """Texto prudente generado desde los valores (no se escribe a mano)."""
    textos = []
    for v in FACTORES:
        fila = tabla[tabla.variable.eq(v)]
        if fila.empty:
            continue
        f = fila.iloc[0]
        if not (np.isfinite(f.error_estandar) and f.error_estandar > 0):
            textos.append(f"**{NOMBRES[v]}**: coeficiente {f.coeficiente:+.3f}; su error estándar no es estimable, por lo que no se interpreta.")
            continue
        incluye_cero = f.ic95_inf <= 0 <= f.ic95_sup
        conclusion = (
            "El intervalo incluye el cero: los datos no permiten descartar una asociación nula."
            if incluye_cero else
            "El intervalo excluye el cero: la asociación es estadísticamente distinta de cero al 5 %."
        )
        textos.append(
            f"**{NOMBRES[v]}**: un punto porcentual adicional en {DESCRIPCION[v]} se asocia, en promedio, "
            f"con {f.coeficiente:+.3f} puntos porcentuales de rentabilidad mensual, con las demás variables constantes "
            f"(IC 95 %: {f.ic95_inf:+.3f} a {f.ic95_sup:+.3f}; p = {f.p_valor:.3f}). {conclusion}"
        )
    return textos


ADVERTENCIA_GENERAL = (
    "Lectura responsable: el modelo mide asociaciones en un diseño observacional, no efectos causales ni "
    "pronósticos. Las tres variables explican una fracción pequeña de la variación mensual (ver R²). "
    "La variación cambiaria es la misma para todas las series en un mes, de modo que su precisión depende "
    "del número de meses del panel y no de la cantidad de filas. Las comparaciones dan igual peso a cada "
    "fondo-serie (no a patrimonio ni partícipes) y las filas interpoladas se tratan como dato."
)
