"""Carga y validación de los archivos reales del proyecto (solo lectura).

El dashboard nunca escribe en las carpetas de la investigación. Localiza la raíz
del proyecto a partir de su propia ubicación, de modo que funciona igual en el
repositorio (dashboard/ junto a datos_procesados/, salidas/, ...) y en una copia
local. No usa rutas absolutas, Google Drive ni credenciales.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

DIR_DASHBOARD = Path(__file__).resolve().parent
CODIGO_MATRICULA = "2024200501G"
NOMBRE_CARPETA_3 = "3_Base_de_datos_y_codigo_Amy_Pamela_Guadalupe_Cordova"
NOMBRE_GENERAL = "Amy_Pamela_Guadalupe_Cordova_UNIDAD_II"

# Columnas documentadas en diccionario_variables.md (32). Se exige su existencia.
COLUMNAS_PANEL = [
    "mes", "tipo", "fondo", "administradora", "denominacion_original", "moneda", "estado",
    "valor_cuota", "rent_mes", "archivo", "pagina", "fila_original", "id_fondo_serie",
    "tasa_pen", "tasa_usd", "tc_fin", "var_tc", "rf_pen", "rf_usd", "rf_mensual", "exceso",
    "vol12", "rent_lag1", "atipico", "imputado", "muestra_modelo", "rent_original",
    "vol12_original", "rent_lag1_original", "historia_imputada", "historia_atipica", "historia_n",
]

# Tablas de salidas/ que el dashboard muestra y las columnas que necesita de cada una.
TABLAS = {
    "tabla1_metricas_por_fondo_serie": ["id_fondo_serie", "tipo", "moneda", "n_meses", "rent_anualizada", "vol_anualizada", "sharpe_anualizado", "meses_con_perdida"],
    "tabla2_riesgo_rentabilidad_por_tipo": ["tipo", "moneda", "unidades", "rent_mediana", "vol_mediana", "sharpe_mediana"],
    "tabla3_modelo_principal": ["modelo", "variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup", "n", "r2", "fondos_series", "meses"],
    "tabla4_modelo_inicial_mco": ["variable", "coeficiente", "error_estandar_mco", "p_valor_mco"],
    "tabla5_robustez": ["modelo", "variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup", "n", "r2", "fondos_series", "meses"],
    "tabla6_vif": ["variable", "VIF"],
    "tabla7_diagnosticos": ["n", "fondos_series", "meses", "corr_residuos_lag1"],
    "tabla9_auditoria_financiera": ["mes", "id_fondo_serie", "tipo", "moneda", "valor_cuota", "cuota_previa", "rent_original", "retorno_cuota", "diferencia_pp", "estado_auditoria"],
    "tabla12_efectos_fijos": ["modelo", "agrupacion", "variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup"],
    "tabla13_sensibilidad_inferencia": ["agrupacion", "variable", "coeficiente", "error_estandar", "p_valor", "ic95_inf", "ic95_sup", "clusters"],
    "tabla14_contrastes_tipo": ["moneda", "tipo", "referencia", "inicio", "fin", "n_meses", "diferencia_media_pp", "ic95_inf_pp", "ic95_sup_pp", "p_valor", "p_holm"],
    "tabla20_cobertura_tipos_observados": ["tipo", "moneda", "series_observadas", "filas_observadas", "meses_observados", "series_panel"],
    "tabla21_desempeno_observado_contextual": ["id_fondo_serie", "tipo", "moneda", "inicio", "fin", "meses", "rent_anualizada", "vol_anualizada", "sharpe_anualizado"],
    "tabla22_desempeno_sin_winsorizar": ["id_fondo_serie", "tipo", "moneda", "meses", "rent_anualizada", "vol_anualizada", "sharpe_anualizado"],
    "tabla_limites_tukey": ["tipo", "moneda", "q1", "q3", "lim_inf", "lim_sup"],
    "tabla_contexto_bcrp": ["mes", "tasa_pen", "tasa_usd", "tc_fin", "var_tc", "rf_pen", "rf_usd"],
}

ESTADOS = ["Observado", "Interpolado", "Winsorizado", "Interpolado y winsorizado"]


class ErrorDatos(RuntimeError):
    """Error legible para mostrar en la aplicación."""


def _es_raiz(p: Path) -> bool:
    return (p / "datos_procesados").is_dir() and any((p / "datos_procesados").glob("datos_procesados_*.csv"))


def localizar_proyecto() -> Path:
    """Devuelve la carpeta que contiene datos_procesados/ y salidas/.

    Orden: variable FM_PROYECTO_RAIZ (opcional, para pruebas), carpeta padre de
    dashboard/ (estructura anterior), carpeta N.º 3 junto a dashboard/,
    carpeta general con nombre completo / carpeta N.º 3 (rúbrica actual),
    y el directorio de trabajo.
    """
    candidatos = []
    if os.environ.get("FM_PROYECTO_RAIZ"):
        candidatos.append(Path(os.environ["FM_PROYECTO_RAIZ"]))
    padre = DIR_DASHBOARD.parent
    candidatos += [padre, padre / NOMBRE_CARPETA_3, padre / NOMBRE_GENERAL / NOMBRE_CARPETA_3, Path.cwd(), Path.cwd() / NOMBRE_CARPETA_3]
    for c in candidatos:
        if _es_raiz(c):
            return c.resolve()
    raise ErrorDatos(
        "No se encontró la carpeta datos_procesados/ del proyecto. El dashboard debe "
        "estar dentro del repositorio, junto a datos_procesados/ y salidas/."
    )


def ruta_procesado(raiz: Path) -> Path:
    fija = raiz / "datos_procesados" / f"datos_procesados_{CODIGO_MATRICULA}.csv"
    if fija.is_file():
        return fija
    otros = sorted((raiz / "datos_procesados").glob("datos_procesados_*.csv"))
    if len(otros) == 1:
        return otros[0]
    raise ErrorDatos("No se pudo identificar un único archivo datos_procesados_<código>.csv.")


def firma_archivo(p: Path) -> str:
    """Tamaño y fecha de modificación: invalida la caché tras una nueva ejecución."""
    s = p.stat()
    return f"{p.name}:{s.st_size}:{int(s.st_mtime)}"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _etiquetas(panel: pd.DataFrame) -> pd.Series:
    """Nombre legible por fondo-serie: último nombre publicado (no estimado) + moneda."""
    obs = panel[panel.imputado.eq(0)].sort_values("mes")
    nombre = obs.groupby("id_fondo_serie").fondo.last()
    faltan = set(panel.id_fondo_serie) - set(nombre.index)
    if faltan:
        nombre = pd.concat([nombre, panel[panel.id_fondo_serie.isin(faltan)].groupby("id_fondo_serie").fondo.last()])
    moneda = panel.groupby("id_fondo_serie").moneda.first()
    etiqueta = nombre.str.strip() + " (" + moneda.reindex(nombre.index) + ")"
    repetidas = etiqueta[etiqueta.duplicated(keep=False)].index
    etiqueta.loc[repetidas] = etiqueta.loc[repetidas] + " · " + pd.Series(repetidas, index=repetidas).str.split("|").str[0].str.strip()
    return etiqueta


def cargar_panel(raiz: Path) -> pd.DataFrame:
    """Lee el panel balanceado y agrega columnas de presentación (no altera valores)."""
    ruta = ruta_procesado(raiz)
    panel = pd.read_csv(ruta, dtype={"mes": str})
    faltan = [c for c in COLUMNAS_PANEL if c not in panel.columns]
    if faltan:
        raise ErrorDatos("Faltan columnas documentadas en el panel: " + ", ".join(faltan))
    if not panel.mes.str.fullmatch(r"\d{4}-\d{2}").all():
        raise ErrorDatos("La columna mes no tiene el formato AAAA-MM esperado.")
    if panel.duplicated(["id_fondo_serie", "mes"]).any():
        raise ErrorDatos("El panel contiene llaves fondo-serie/mes duplicadas.")
    panel = panel.sort_values(["id_fondo_serie", "mes"]).reset_index(drop=True)
    panel["fecha"] = pd.to_datetime(panel.mes + "-01")
    imp = panel.imputado.eq(1)
    win = panel.atipico.eq(1)
    panel["estado_dato"] = np.select(
        [imp & win, imp, win], ["Interpolado y winsorizado", "Interpolado", "Winsorizado"], default="Observado"
    )
    # Exceso con el retorno previo a winsorizar (para la vista "original").
    panel["exceso_original"] = panel.rent_original - panel.rf_mensual
    etiquetas = _etiquetas(panel)
    panel["etiqueta"] = panel.id_fondo_serie.map(etiquetas)
    return panel


def cargar_tabla(raiz: Path, nombre: str) -> pd.DataFrame | None:
    """Lee una tabla de salidas/; devuelve None si falta o si cambió su estructura."""
    p = raiz / "salidas" / f"{nombre}.csv"
    if not p.is_file():
        return None
    t = pd.read_csv(p, dtype={"mes": str, "inicio": str, "fin": str})
    requeridas = TABLAS.get(nombre, [])
    if any(c not in t.columns for c in requeridas):
        return None
    return t


def leer_texto(raiz: Path, nombre: str) -> str | None:
    p = raiz / nombre
    return p.read_text(encoding="utf-8") if p.is_file() else None


def diccionario_variables(raiz: Path) -> pd.DataFrame | None:
    """Convierte la tabla Markdown de diccionario_variables.md en un DataFrame."""
    texto = leer_texto(raiz, "diccionario_variables.md")
    if not texto:
        return None
    filas = []
    for linea in texto.splitlines():
        if linea.startswith("|") and not re.match(r"^\|\s*-", linea):
            celdas = [c.strip().strip("`") for c in linea.strip().strip("|").split("|")]
            filas.append(celdas)
    if len(filas) < 2:
        return None
    cab, *cuerpo = filas
    cuerpo = [f for f in cuerpo if len(f) == len(cab) and f[0] in COLUMNAS_PANEL]
    return pd.DataFrame(cuerpo, columns=cab) if cuerpo else None


# --------------------------------------------------------------------------- complementarios y transparencia
def cargar_complementaria(raiz: Path) -> pd.DataFrame | None:
    """Base integrada observada (antes de seleccionar el panel): contiene ETF y Estructurados.

    Es un archivo de apoyo de la investigación; no forma parte del panel econométrico balanceado.
    """
    p = raiz / "datos_procesados" / "base_integrada_observada.csv"
    if not p.is_file():
        return None
    d = pd.read_csv(p, dtype={"mes": str})
    d["fecha"] = pd.to_datetime(d.mes + "-01")
    return d


def leer_hashes(raiz: Path) -> pd.DataFrame:
    """Manifiesto hash_sha256.txt como tabla (sha256, archivo); vacío si no existe."""
    p = raiz / "hash_sha256.txt"
    filas = []
    if p.is_file():
        for linea in p.read_text(encoding="utf-8").splitlines():
            partes = linea.strip().split(maxsplit=1)
            if len(partes) == 2 and re.fullmatch(r"[0-9a-f]{64}", partes[0]):
                filas.append({"sha256": partes[0], "archivo": partes[1].strip()})
    return pd.DataFrame(filas, columns=["sha256", "archivo"])


def verificar_hashes(raiz: Path, manifiesto: pd.DataFrame) -> pd.DataFrame:
    """Recalcula el SHA-256 de cada archivo del manifiesto y lo compara (solo lectura)."""
    estados, calc = [], []
    for ruta in manifiesto.archivo:
        f = raiz / ruta
        if not f.is_file():
            estados.append("No está en esta copia")
            calc.append("")
            continue
        h = sha256(f)
        calc.append(h)
        estados.append("Coincide" if h == manifiesto.loc[manifiesto.archivo.eq(ruta), "sha256"].iloc[0] else "NO coincide")
    out = manifiesto.copy()
    out["sha256_recalculado"] = calc
    out["estado"] = estados
    return out


@lru_cache(maxsize=2)
def _procesado_original(ruta: str, firma: str) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype={"mes": str})


def procesado_original(raiz: Path) -> pd.DataFrame:
    """Base procesada tal como se entregó (mismas filas, columnas y orden); sin columnas de presentación."""
    ruta = ruta_procesado(raiz)
    return _procesado_original(str(ruta), firma_archivo(ruta)).copy()
