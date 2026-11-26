"""Comprueba la compatibilidad del dashboard con Carpeta 3, sin usar Streamlit.

Desde la raíz del repositorio:
    python dashboard/verificar_actualizacion.py
Es un proceso de solo lectura: no crea ni modifica archivos de la investigación.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import catalogo_figuras as cf
import datos


def verificar() -> int:
    errores: list[str] = []
    try:
        raiz = datos.localizar_proyecto()
        ruta = datos.ruta_procesado(raiz)
    except datos.ErrorDatos as exc:
        print(f"ERROR DE RUTA: {exc}")
        return 1
    with ruta.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if len(reader.fieldnames or []) != 32:
            errores.append("El panel no contiene las 32 columnas previstas.")
        n = sum(1 for _ in reader)
    if n != 4026:
        errores.append(f"El panel tiene {n} observaciones; se esperaban 4026.")
    print(f"Panel: {n} observaciones, SHA-256 {hashlib.sha256(ruta.read_bytes()).hexdigest()}")
    for fig in cf.FIGURAS:
        path, titulo, nueva = cf.resolver(raiz, fig)
        if not path or not nueva:
            errores.append(f"Figura {fig.numero} ausente o anterior: {titulo}")
        else:
            with path.open("rb") as f:
                if f.read(8) != b"\x89PNG\r\n\x1a\n":
                    errores.append(f"Figura {fig.numero} no es PNG válido: {path.name}")
            print(f"Figura {fig.numero}: {path.name}")
    nombres = (
        "tabla23_indice_riqueza",
        "tabla24_diferencias_mensuales_deuda",
        "tabla25_regresion_parcial_mensual",
    )
    for nombre in nombres:
        t = datos.cargar_tabla(raiz, nombre)
        if t is None or t.empty:
            errores.append(f"Tabla nueva ausente o incompleta: {nombre}")
        else:
            print(f"{nombre}: {len(t)} filas")
    if errores:
        print("CORREGIR:\n" + "\n".join(f"- {e}" for e in errores))
        return 1
    print("Compatibilidad de archivos: CORRECTA. Falta comprobar la interacción en Streamlit Cloud.")
    return 0


if __name__ == "__main__":
    raise SystemExit(verificar())
