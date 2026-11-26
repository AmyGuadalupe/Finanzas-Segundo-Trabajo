# Cambios realizados durante la auditoría independiente

- Se importaron metadatos de 30 artículos desde la **matriz bibliográfica Typst proporcionada por la estudiante**. El DOI, año, revista, objetivo, muestra, método, hallazgos y relación con el tema se transcribieron del documento; la indexación individual Scopus y el cuartil individual siguen pendientes de verificación directa (no se inventa).
- Las traducciones, las imágenes, los enlaces de Drive, las justificaciones individuales desarrolladas por la autora y el journal siguen pendientes; las descargas continúan desactivadas.
- La exploración de la base completa es accesible incluso cuando una combinación de filtros de la sección financiera da cero filas.
- Se reforzaron las pruebas: se revisan los identificadores de documentos **reales**, la estructura del CSV y la integridad de los 30 metadatos, en vez de aserciones vacías.
- No se tocó ningún archivo fuera de `dashboard/` ni los datos fuente o procesados.

**Validación:** se pudieron ejecutar los módulos sin Streamlit y la generación de XLSX/CSV; las pruebas interactivas completas y Kaleido requieren el entorno desplegado.

## Ajuste posterior (corrección técnica final)
- Se corrigió el recorte de la fila de botones de secciones en `estilos.py`.
- Se añadió `tests/test_fichas.py` (30 fichas, DOI y navegación) y una prueba de la base completa con contexto mínimo en `tests/test_portal.py`.
