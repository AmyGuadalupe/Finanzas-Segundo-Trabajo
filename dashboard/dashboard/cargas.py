"""Cargas en caché de los archivos reales de la investigación (solo lectura)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import datos


@st.cache_data(show_spinner="Cargando el panel de la investigación…")
def panel(ruta: str, firma: str) -> pd.DataFrame:
    return datos.cargar_panel(Path(ruta))


@st.cache_data(show_spinner=False)
def tabla(ruta: str, nombre: str, firma: str):
    return datos.cargar_tabla(Path(ruta), nombre)


@st.cache_data(show_spinner=False)
def sha_procesado(ruta: str, firma: str) -> str:
    return datos.sha256(Path(ruta))


@st.cache_data(show_spinner=False)
def diccionario(ruta: str, firma: str):
    return datos.diccionario_variables(Path(ruta))


@st.cache_data(show_spinner=False)
def complementaria(ruta: str, firma: str):
    return datos.cargar_complementaria(Path(ruta))


@st.cache_data(show_spinner=False)
def texto(ruta: str, nombre: str, firma: str):
    return datos.leer_texto(Path(ruta), nombre)


class Proyecto:
    """Acceso perezoso y cacheado a la investigación; falla con un mensaje legible."""

    def __init__(self):
        self.raiz = datos.localizar_proyecto()
        self.ruta_proc = datos.ruta_procesado(self.raiz)
        self.firma = datos.firma_archivo(self.ruta_proc)

    @property
    def panel(self) -> pd.DataFrame:
        return panel(str(self.raiz), self.firma)

    def tabla(self, nombre: str):
        return tabla(str(self.raiz), nombre, self.firma)

    @property
    def sha(self) -> str:
        return sha_procesado(str(self.ruta_proc), self.firma)

    @property
    def diccionario(self):
        return diccionario(str(self.raiz), self.firma)

    @property
    def complementaria(self):
        return complementaria(str(self.raiz), self.firma)

    def texto(self, nombre: str):
        return texto(str(self.raiz), nombre, self.firma)


def proyecto() -> Proyecto | None:
    """Proyecto o None (con aviso en pantalla) si no se encuentran los datos."""
    try:
        return Proyecto()
    except datos.ErrorDatos as e:
        st.error(f"No se pudo cargar la base de la investigación: {e}")
        return None
