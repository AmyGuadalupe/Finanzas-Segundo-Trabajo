# Portal científico interactivo · Fondos mutuos en el Perú

Tema 79 · Finanzas I, Unidad II, 2026-II · Universidad Nacional del Centro del Perú.
Autora: Amy Pamela Guadalupe Cordova. Docente: Ciro Iván Machacuay Meza.

## Qué es
Una aplicación Streamlit de tres vistas: portada, sección 01 (productos académicos con menú circular de siete secciones y biblioteca de pósteres) y sección 02 (base de datos y análisis financiero, con todos los filtros del dashboard anterior). El punto de entrada sigue siendo `dashboard/app.py`.

## Estructura
- `app.py`: enrutador de las tres vistas.
- `panel_financiero.py` y `tabs_dashboard.py`: sección 02 (diez pestañas).
- `vistas/`: portada, menú radial, secciones, biblioteca de pósteres y productos principales.
- `config/portal.json`, `config/documentos.json`, `config/contenido_secciones.json`: textos, enlaces y estados de documentos. Es el único lugar que se edita para incorporar documentos.
- `nav.py`, `estilos.py`, `portal_config.py`, `cargas.py`, `datos.py`, `exportes.py`, `graficos.py`, `metricas.py`, `econometria.py`, `descargas.py`: módulos de apoyo.
- `assets/`: escudo, fotografía y miniaturas (ver `assets/LEEME.md`).
- `tests/`: pruebas automatizadas.

## Principios de diseño
- Solo lectura sobre la investigación: nunca se modifican los cinco scripts, el pipeline ni los datos crudos o procesados, y al abrir el portal no se extrae nada.
- Sin datos simulados ni credenciales.
- Documentos externos (artículos, traducciones, pósteres, proyectos Typst, journal) en Google Drive u otro servicio, enlazados por el JSON con un identificador único por póster. Un enlace vacío nunca se muestra como botón activo.
- Estados de disponibilidad discretos: disponible, en elaboración, pendiente, no distribuible.

## Descargas
Cada descarga ofrece XLSX nativo (columnas separadas, fechas y números reales, filtros de encabezado, primera fila inmovilizada, comentarios con la definición de cada variable), CSV para Excel (UTF-8 con BOM, separador punto y coma, coma decimal y línea inicial de separador) y CSV estándar (coma y punto decimal). La base completa y la base por tipo siempre se entregan íntegras; la selección filtrada se entrega aparte. En la base completa, el CSV estándar es el archivo original byte a byte.

## Cuidados metodológicos
Diseño observacional con datos de la AAF y BCRPData; no hay extracción directa desde la SMV y la documentación no contiene una autorización docente escrita de sustitución de fuente. Las estimaciones dinámicas con filtros son exploratorias y se distinguen de los resultados oficiales de la investigación.
