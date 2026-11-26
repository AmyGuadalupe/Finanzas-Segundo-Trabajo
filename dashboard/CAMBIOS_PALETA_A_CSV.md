# Cambio A · Paleta guindo suave, marfil y descargas de tablas

**Ámbito:** únicamente `dashboard/`, no altera archivos de la investigación.

- Guindo profundo suave `#783F53` (botones y estados activos), rosa empolvado `#B78A99` (detalles), marfil `#F8F6F3` (fondos), gris nacarado `#E9E4E6` (líneas) y texto gris azulado `#303744`.
- Se conservan el menú radial de siete secciones, las animaciones, la navegación, las pestañas, los filtros, los gráficos y sus colores por tipo de fondo.
- En Resultados se añade **Descargar las tablas oficiales en CSV**. Incluye selector de tabla, bytes originales de `salidas/`, copia regional para Excel de Perú y ZIP con las tablas oficiales.
- No se reejecuta ningún script, no se escriben datos procesados y no se modifica el journal.
- `python3 aplicar_paleta_A_guindo_marfil_CSV.py .` muestra una vista previa. `--aplicar` solo modifica archivos locales, sin commit ni push.
- Recomendable: ejecutar `python -m pytest dashboard/tests -q`; visitar Resultados y comprobar descargas en Chrome/Excel antes de publicar.
