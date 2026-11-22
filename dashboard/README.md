# Dashboard · Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo

Tema 79 · Finanzas I (055D) · UNCP · Amy Pamela Guadalupe Cordova (2024200501G).

Aplicación interactiva en **Streamlit + Plotly** que lee directamente los archivos reales del proyecto
(sin copias, sin Google Drive, sin credenciales ni rutas absolutas) y muestra la rentabilidad, el riesgo
y el desempeño ajustado por riesgo del panel balanceado mensual construido con los boletines de la AAF
y la API de BCRPData.

## 1. Qué archivos lee (solo lectura)

| Archivo | Uso |
|---|---|
| `datos_procesados/datos_procesados_2024200501G.csv` | Panel balanceado (las 32 columnas documentadas) |
| `salidas/tabla3_…`, `tabla4_…`, `tabla5_…`, `tabla6_…`, `tabla7_…`, `tabla12_…`, `tabla13_…`, `tabla14_…` | Resultados econométricos oficiales |
| `salidas/tabla9_…`, `tabla20_…`, `tabla21_…`, `tabla_limites_tukey.csv` | Auditoría de cuotas, cobertura, análisis contextual y límites de Tukey |
| `diccionario_variables.md` | Diccionario mostrado en la app y anexado al Excel |

El dashboard **no escribe** en `codigo/`, `datos_crudos/`, `datos_procesados/`, `salidas/` ni `documentos/`,
y no altera los hashes del manifiesto. Las pruebas lo verifican comparando el SHA-256 de todos esos archivos
antes y después de usar la aplicación.

## 2. Estructura

```text
dashboard/
  app.py               Aplicación (filtros, línea de tiempo, pestañas, descargas)
  datos.py             Localiza el proyecto y valida columnas y tablas
  metricas.py          Cálculos financieros (idénticos a codigo/04_analisis.py)
  econometria.py       Reestimación exploratoria con la misma especificación del modelo
  graficos.py          Gráficos Plotly (paleta clara y oscura)
  descargas.py         CSV, Excel, PNG, ZIP y reporte HTML
  requirements.txt     Dependencias de la app (versiones exactas)
  requirements-dev.txt Dependencias para ejecutar las pruebas
  tests/               Pruebas automáticas con los datos reales
  .streamlit/          Tema visual (uso local)
```

## 3. Ejecutar en una computadora

Desde la **raíz del repositorio** (la carpeta que contiene `datos_procesados/` y `dashboard/`):

```bash
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Se abre en `http://localhost:8501`. Funciona con Python 3.12 y 3.13.

## 4. Publicar gratis en Streamlit Community Cloud

1. Sube la carpeta `dashboard/` completa a la rama `main` del repositorio, junto a las carpetas de la
   investigación (en GitHub: *Add file → Upload files* y arrastra la carpeta; luego *Commit changes*).
2. Entra a <https://share.streamlit.io> e inicia sesión con la cuenta de GitHub dueña del repositorio.
3. Pulsa **Create app → Deploy a public app from GitHub** y completa:
   - Repository: `AmyGuadalupe/Finanzas-Segundo-Trabajo`
   - Branch: `main`
   - Main file path: `dashboard/app.py`
   - App URL: el nombre que prefieras (por ejemplo, `fondos-mutuos-peru`).
4. En **Advanced settings**, elige **Python 3.12** (o 3.13). No se necesitan secretos.
5. Pulsa **Deploy**. La primera instalación tarda unos minutos. Copia la URL pública que aparece al terminar.

Detalles que ya están resueltos:

- Community Cloud usa primero el `requirements.txt` que está junto a `app.py`, así que **no** instala las
  dependencias de extracción del `requirements.txt` de la raíz.
- La app localiza los datos a partir de su propia ubicación, por lo que funciona aunque Cloud ejecute
  `streamlit run` desde la raíz.
- Community Cloud solo lee `.streamlit/config.toml` en la raíz del repositorio. Como el tema está dentro de
  `dashboard/`, en la nube se usa el tema por defecto (claro u oscuro según el usuario). La app detecta el
  tema y ajusta los colores de los gráficos; no hace falta cambiar nada.

## 5. Por qué sobrevive a una nueva ejecución del notebook

- La celda de publicación del notebook solo elimina del repositorio los archivos listados en el manifiesto
  `hash_sha256.txt` dentro de `datos_crudos/`, `datos_procesados/` y `salidas/`. `dashboard/` no figura en él.
- El notebook reescribe el `.gitignore` y el `requirements.txt` de la raíz; el dashboard tiene los suyos.
- Los meses, tipos, monedas, administradoras y fondos-series se leen de los datos en cada carga. Si una nueva
  ejecución cambia el periodo o el número de series, la app se adapta sola. La caché se invalida cuando cambia
  el tamaño o la fecha del archivo procesado.
- Si falta alguna tabla de `salidas/` o cambia su estructura, la sección correspondiente se omite sin detener la app.

## 6. Funciones

- **Filtros**: tipo de fondo, moneda (PEN, USD o ambas por separado), administradora, fondos-series (uno o
  varios), serie de retorno (tratada o antes de winsorizar) y nivel de los gráficos (por tipo o por fondo-serie).
- **Línea de tiempo financiera**: deslizador de rango mensual (mes inicial y final), atajos de periodo y año
  calendario. Afecta a todos los gráficos, indicadores, tablas y descargas.
- **Restablecer filtros**: devuelve todo al panel completo.
- **Pestañas**: Evolución · Riesgo y desempeño · Categorías y fondos · Estadísticos · Econometría · Calidad de datos · Descargas.
- **Descargas** (todas con los filtros y el periodo activos): CSV y Excel de observaciones (con hoja de
  filtros y diccionario), Excel y ZIP de tablas estadísticas, PNG de cada gráfico (2 800 px de ancho) o ZIP con
  todos, y reporte HTML imprimible. Si cambias un filtro, los archivos ya preparados se descartan.

## 7. Reglas de cálculo e interpretación

- Rentabilidad anualizada, volatilidad y Sharpe se calculan exactamente como en `codigo/04_analisis.py`
  (sin filtros reproducen las tablas 1, 2, 3, 8, 15, 16 y 22). Se exigen al menos 12 meses para anualizar.
- La rentabilidad acumulada usa capitalización compuesta: índice = 100 × ∏(1 + r).
- Sortino y máxima caída son medidas complementarias calculadas solo en el dashboard.
- Las monedas nunca se promedian entre sí: cada una tiene su propio panel e indicadores.
- Los promedios por tipo dan igual peso a cada fondo-serie (no hay patrimonio ni partícipes homogéneos).
- Datos **observados** (AAF, BCRP), **calculados**, **interpolados** (`imputado = 1`) y **winsorizados**
  (`atipico = 1`) se distinguen en tablas, marcas de los gráficos, mapa de calidad y descargas (`estado_dato`).
- ETF y Estructurados **no** integran el panel balanceado; aparecen solo en el análisis contextual.
- La reestimación del modelo con filtros es exploratoria; la inferencia oficial es la del panel completo.

## 8. Pruebas

```bash
python -m pip install -r dashboard/requirements-dev.txt
python -m pytest dashboard/tests -q
```

Las 47 pruebas usan los datos reales. Comprueban las columnas documentadas, la integridad del panel, la
reproducción numérica de las tablas oficiales, los filtros, la matemática de los indicadores, que las
descargas contengan solo lo filtrado, la interacción con la app (filtros, línea de tiempo, descargas y
restablecer) y que ningún archivo de la investigación cambie.
