"""Configuración centralizada del portal (documentos, productos y portada).

Todo lo que cambia con el tiempo (enlaces de Google Drive, metadatos de los 30
artículos, fotografía, escudo) vive en config/*.json y assets/. Este módulo solo
lee, valida y deriva enlaces; nunca inventa un enlace ni un dato bibliográfico.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

DIR = Path(__file__).resolve().parent
CONFIG = DIR / "config"
ASSETS = DIR / "assets"

ESTADOS = {
    "disponible": ("Disponible", "ok"),
    "en_elaboracion": ("En elaboración", "wip"),
    "pendiente": ("Pendiente", "pend"),
    "no_distribuible": ("Acceso editorial", "ed"),
}
DOCUMENTOS = [
    ("articulo_en", "Artículo original (inglés)", "PDF"),
    ("traduccion_es", "Artículo traducido (español)", "PDF"),
    ("poster_pdf", "Póster bibliográfico", "PDF"),
    ("proyecto_zip", "Proyecto editable del póster", "ZIP"),
]
CAMPOS_FICHA = [
    ("problema", "Problema abordado"), ("objetivo", "Objetivo de la investigación"),
    ("datos_metodologia", "Datos y metodología"), ("resultados", "Principales resultados"),
    ("conclusiones", "Conclusiones relevantes"), ("justificacion_seleccion", "Por qué elegí este artículo"),
    ("aporte", "Aporte a mi investigación"), ("relacion_estudio", "Relación con las variables y resultados de mi estudio"),
]


def _leer(nombre: str) -> dict:
    return json.loads((CONFIG / nombre).read_text(encoding="utf-8"))


@lru_cache(maxsize=4)
def _cache(nombre: str, firma: float) -> dict:
    return _leer(nombre)


def cargar(nombre: str) -> dict:
    """Lee un JSON de config/ y lo recarga si el archivo cambió."""
    return _cache(nombre, (CONFIG / nombre).stat().st_mtime)


def portal() -> dict:
    return cargar("portal.json")


def documentos() -> dict:
    return cargar("documentos.json")


def contenido() -> dict:
    return cargar("contenido_secciones.json")


# ---------------------------------------------------------------- enlaces
def es_url(u) -> bool:
    if not isinstance(u, str) or not u.strip():
        return False
    p = urlparse(u.strip())
    return p.scheme in ("http", "https") and bool(p.netloc)


def _id_drive(u: str) -> str | None:
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=\w+&)?id=)([\w-]+)", u or "")
    return m.group(1) if m else None


def url_visor(u: str) -> str:
    """URL incrustable: vista previa de Drive si es un enlace de Drive; si no, el mismo enlace."""
    i = _id_drive(u)
    return f"https://drive.google.com/file/d/{i}/preview" if i else u


def url_descarga(u: str) -> str:
    i = _id_drive(u)
    return f"https://drive.google.com/uc?export=download&id={i}" if i else u


def estado_visible(estado: str) -> tuple[str, str]:
    return ESTADOS.get(estado, ESTADOS["pendiente"])


def ruta_asset(nombre_relativo: str) -> Path | None:
    """Ruta de un archivo de assets/ si existe (fotografía, escudo, miniaturas locales)."""
    if not nombre_relativo:
        return None
    p = (DIR / nombre_relativo).resolve()
    return p if p.is_file() and DIR in p.parents else None


# ---------------------------------------------------------------- artículos
def articulos() -> list[dict]:
    return documentos()["articulos"]


def articulo(id_: str) -> dict | None:
    return next((a for a in articulos() if a["id"] == id_), None)


def tiene_metadatos(a: dict) -> bool:
    return bool(a.get("titulo_original") or a.get("titulo_es"))


def enlace_doc(a: dict, clave: str) -> tuple[str, str]:
    """(estado, url_descarga) de uno de los cuatro documentos de la ficha; url vacía si no hay enlace válido."""
    d = a["documentos"].get(clave, {})
    url = d.get("descarga_url") or d.get("visualizacion_url") or ""
    return d.get("estado", "pendiente"), (url_descarga(url) if es_url(url) else "")


def validar_documentos() -> list[str]:
    """Problemas de consistencia del JSON (lista vacía = correcto)."""
    cfg, p = documentos(), []
    arts = cfg.get("articulos", [])
    ids = [a.get("id") for a in arts]
    if len(set(ids)) != len(ids):
        p.append("Hay identificadores de artículo repetidos.")
    for a in arts:
        if not re.fullmatch(r"A\d{2}", str(a.get("id"))):
            p.append(f"Identificador inválido: {a.get('id')}")
        if set(a.get("documentos", {})) != {c for c, _, _ in DOCUMENTOS}:
            p.append(f"{a.get('id')}: los cuatro documentos deben compartir la ficha (articulo_en, traduccion_es, poster_pdf, proyecto_zip).")
        for k in ("doi", "enlace_editorial", "miniatura"):
            v = a.get(k, "")
            if v and k != "miniatura" and not (es_url(v) or (k == "doi" and v.startswith("10."))):
                p.append(f"{a.get('id')}: {k} no es un enlace válido.")
        if a.get("cuartil") and a["cuartil"] not in ("Q1", "Q2"):
            p.append(f"{a.get('id')}: el cuartil debe ser Q1 o Q2.")
        for c, d in a.get("documentos", {}).items():
            for k in ("visualizacion_url", "descarga_url"):
                if d.get(k) and not es_url(d[k]):
                    p.append(f"{a.get('id')}.{c}.{k}: enlace inválido.")
    return p


def url_doi(doi: str) -> str:
    doi = (doi or "").strip()
    if not doi:
        return ""
    return doi if es_url(doi) else f"https://doi.org/{doi}"
