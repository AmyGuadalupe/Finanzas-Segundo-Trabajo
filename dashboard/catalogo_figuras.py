"""Catálogo de figuras oficiales de la investigación.

La versión del 26-11-2026 genera cinco figuras. Si los datos todavía
no se han actualizado en GitHub, se puede mostrar provisionalmente
la figura correspondiente anterior, rotulada como tal. Nunca se
reemplaza una figura por otra con un título que no le corresponde.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Figura:
    numero: int
    archivo_nuevo: str
    titulo_nuevo: str
    pestaña: str
    descripcion: str
    archivo_anterior: str = ""
    titulo_anterior: str = ""


FIGURAS = (
    Figura(1, "figura1_riesgo_rentabilidad.png", "Rentabilidad y volatilidad de las 66 fondo-series", "desempeno",
           "Cada punto representa una fondo-serie; los valores se presentan por moneda.",
           "figura1_riesgo_rentabilidad.png", "Riesgo y rentabilidad por fondo-serie"),
    Figura(2, "figura2_indice_riqueza.png", "Índice de riqueza base 100 y caídas desde máximos", "desempeno",
           "Trayectorias de inversión hipotética de igual peso por tipo y moneda, sin representar un pronóstico.",
           "figura2_sharpe_por_tipo.png", "Mediana del Sharpe por tipo de fondo"),
    Figura(3, "figura3_sharpe_ordenado.png", "Razón de Sharpe de cada fondo-serie, ordenada", "contrastes",
           "Se visualizan las razones de las series individuales; no son intervalos de confianza.",
           "figura5_distribucion_sharpe.png", "Distribución del Sharpe por tipo"),
    Figura(4, "figura4_diferencias_deuda.png", "Diferencias mensuales de exceso de rentabilidad frente a Deuda", "contrastes",
           "Mapa de calor por mes, categoría y moneda; los contrastes inferenciales se conservan en la tabla 14.",
           "figura6_contrastes_tipo.png", "Contrastes por tipo y moneda, con intervalos"),
    Figura(5, "figura5_regresion_parcial.png", "Residuos parciales y variación del tipo de cambio", "econometria",
           "La relación representa la asociación parcial del modelo, no un efecto causal.",
           "figura4_coeficientes.png", "Coeficientes e intervalos del modelo principal"),
)


def resolver(raiz: Path, figura: Figura) -> tuple[Path | None, str, bool]:
    """Devuelve (ruta, título, es_nueva) sin copiar ni cambiar la investigación."""
    s = Path(raiz) / "salidas"
    nueva = s / figura.archivo_nuevo
    if nueva.is_file():
        return nueva, f"Figura {figura.numero} · {figura.titulo_nuevo}", True
    if figura.archivo_anterior:
        antigua = s / figura.archivo_anterior
        if antigua.is_file():
            return antigua, f"Gráfico anterior · {figura.titulo_anterior} (pendiente de actualización)", False
    return None, f"Figura {figura.numero} no disponible", False


def nueva_version_completa(raiz: Path) -> bool:
    return all((Path(raiz)/"salidas"/f.archivo_nuevo).is_file() for f in FIGURAS)
