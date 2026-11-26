# Diccionario de variables · 2024200501G

Llave: `id_fondo_serie` y `mes`. Decimal 0,01 equivale a 1 %. La base definitiva es completa. Los datos crudos y la base integrada observada tienen sus propios controles; las estimaciones están marcadas.

## Fuentes y endpoints

- AAF: https://fondosmutuos.pe/estadisticas/; URL de cada PDF en `datos_crudos/scraping/descargas_boletines_2024200501G.csv`, página y fila en columnas de trazabilidad.
- PN01216PM: https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01216PM/json/2018-12/2025-12/esp
- PD04692MD: https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04692MD/json/2018-12-01/2025-12-31/esp
- PD04693MD: https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04693MD/json/2018-12-01/2025-12-31/esp

## Base procesada (32 columnas)

| Variable | Definición | Unidad | Frecuencia | Fuente (URL arriba) | Naturaleza |
|---|---|---|---|---|---|
| mes | Periodo calendario observado o imputado | AAAA-MM | Mensual | AAF | Observado |
| tipo | Categoría de encabezado | Texto | Mensual | AAF | Observado |
| fondo | Nombre sin administradora si se identifica | Texto | Mensual | AAF | Identificación derivada |
| administradora | Administradora leída; casos sin identificar excluidos | Texto | Mensual | AAF | Identificación derivada |
| denominacion_original | Denominación publicada; con prefijo ESTIMADO si se interpola | Texto | Mensual | AAF | Observado |
| moneda | Moneda de cuota | PEN/USD | Mensual | AAF | Observado |
| estado | No informado o estimado; no equivale a estado registral SMV | Texto | Mensual | AAF | No observado |
| valor_cuota | Cuota positiva observada o estimada en hueco interior | Moneda del fondo | Mensual | AAF | Observado |
| rent_mes | Retorno pretratamiento recortado en límites Tukey; Y | Decimal | Mensual | AAF | Calculado |
| archivo | Nombre del PDF original o INTERPOLACION | Texto | Mensual | AAF | Trazabilidad |
| pagina | Página PDF desde 1; 0 solo si interpolado | Entero | Mensual | AAF | Trazabilidad |
| fila_original | Texto de fila publicada o descripción de estimación | Texto | Mensual | AAF | Trazabilidad |
| id_fondo_serie | Administradora homologada, denominación y moneda; no código registral | Texto | Mensual | AAF | Llave calculada |
| tc_fin | TC interbancario promedio fin de periodo | PEN/USD | Mensual | PN01216PM | Observado |
| tasa_pen | Media de días numéricos tasa interbancaria PEN | % anual | Diaria a mensual | PD04692MD | Calculado |
| tasa_usd | Media de días numéricos tasa interbancaria USD | % anual | Diaria a mensual | PD04693MD | Calculado |
| var_tc | ln(TC_t)-ln(TC_t-1); X2 | Decimal | Mensual | PN01216PM | Calculado |
| rf_pen | (1+tasa_pen/100)^(1/12)-1; proxy | Decimal | Mensual | PD04692MD | Calculado |
| rf_usd | (1+tasa_usd/100)^(1/12)-1; proxy | Decimal | Mensual | PD04693MD | Calculado |
| rf_mensual | Selecciona referencia según moneda | Decimal | Mensual | PD04692MD y PD04693MD | Calculado |
| exceso | rent_mes menos rf_mensual | Decimal | Mensual | AAF y BCRP | Calculado |
| vol12 | Desviación muestral de retornos tratados de t-12 a t-1; mínimo seis disponibles; X1 | Decimal | Mensual | AAF | Calculado |
| rent_lag1 | Retorno tratado del mes calendario previo de misma serie; X3 | Decimal | Mensual | AAF | Calculado |
| atipico | 1 si se sustituyó por límite extremo de Tukey por tipo y moneda | 0/1 | Mensual | AAF | Calculado |
| imputado | 1: retorno y cuota estimados geométricamente; 0: observados | 0/1 | Mensual | AAF y BCRP | Control |
| muestra_modelo | 1 en todas las filas del panel definitivo | 0/1 | Mensual | AAF y BCRP | Control |
| rent_original | Retorno previo a winsorizar; publicado si imputado=0, estimado si imputado=1 | Decimal | Mensual | AAF | Observado o estimado |
| vol12_original | Volatilidad histórica del retorno previo a winsorizar, ventana 12, mínimo 6 | Decimal | Mensual | AAF | Calculado |
| rent_lag1_original | Retorno del mes previo antes de winsorizar | Decimal | Mensual | AAF | Calculado |
| historia_imputada | Cantidad de retornos interpolados en ventana previa | Entero | Mensual | AAF | Control |
| historia_atipica | Cantidad de retornos winsorizados en ventana previa | Entero | Mensual | AAF | Control |
| historia_n | Número de retornos disponibles en ventana previa | Entero | Mensual | AAF | Control |

## Variables de las salidas

`rent_anualizada`: retorno geométrico equivalente anual de meses observados. `vol_anualizada`: desviación muestral por raíz de doce. `sharpe_anualizado`: media del exceso sobre su desviación muestral por raíz de doce. `diferencia_pp`: 100 × (rent_original - retorno_cuota) en cuotas consecutivas observadas. `ventana_salto` y `ventana_alerta`: alertas entre t y t-12, solo sensibilidad. `p_holm`: ajuste de Holm. Los intervalos bootstrap de Sharpe son exploratorios. Todos los resultados econométricos se generan en 04. `rent_promedio`, `indice` y `caida_desde_maximo` (tabla23): rentabilidad media mensual de las series de cada tipo y moneda, índice de riqueza con base 100 en julio de 2020 de esa cartera equiponderada rebalanceada cada mes, y caída relativa respecto de su máximo previo. `diferencia_exceso_pp` (tabla24): diferencia mensual entre la mediana del exceso del tipo y la de Deuda, en puntos porcentuales; su media es `diferencia_media_pp` de tabla14. `rent_parcial_media` (tabla25): promedio mensual del residuo del modelo principal más el componente β·`var_tc`; su pendiente frente a `var_tc` es igual al coeficiente cambiario de tabla3.
