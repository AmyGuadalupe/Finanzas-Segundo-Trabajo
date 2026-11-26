# Compatibilidad de imágenes del journal con el portal (26/11/2026)

Esta revisión modifica **solo la representación de las figuras oficiales en la sección Resultados** y una mejora discreta de la indicación de sección en los botones anterior/siguiente. No modifica los filtros del dashboard, las vistas de análisis interactivo, el modelo econométrico ni los datos procesados.

| Figura nueva | Archivo de `salidas/` | Vista del portal |
|---|---|---|
| 1. Rentabilidad y volatilidad de las series | `figura1_riesgo_rentabilidad.png` | Desempeño por tipo y moneda |
| 2. Índice de riqueza y caídas desde máximos | `figura2_indice_riqueza.png` | Desempeño por tipo y moneda |
| 3. Sharpe de todas las series, ordenadas | `figura3_sharpe_ordenado.png` | Contrastes y distribución |
| 4. Mapa mensual de diferencias frente a Deuda | `figura4_diferencias_deuda.png` | Contrastes y distribución |
| 5. Regresión parcial de tipo de cambio | `figura5_regresion_parcial.png` | Modelo econométrico |

Las tablas 23 a 25 pueden consultarse en los desplegables junto a las figuras. El gráfico no se reconstruye en el navegador: es la salida auténtica de `codigo/04_analisis.py`. El resto del análisis del dashboard sigue siendo interactivo y filtrable.

El módulo `catalogo_figuras.py` incluye la visualización de archivos anteriores cuando la Carpeta 3 no se ha actualizado todavía, sin asignar títulos falsos. Cuando se encuentren los cinco nuevos, solo se muestran los oficiales.

**Importante:** `Carpeta3_actualizada.zip` no incluye `datos_crudos/` ni `datos_procesados/`. No debe reemplazarse toda la Carpeta 3 por ese ZIP ni eliminarse el archivo procesado. La validación local se realiza con `python dashboard/verificar_actualizacion.py` y la prueba final con `python -m pytest dashboard/tests -q` en un entorno que tenga instaladas las dependencias de `dashboard/requirements.txt` y `dashboard/requirements-dev.txt`.
