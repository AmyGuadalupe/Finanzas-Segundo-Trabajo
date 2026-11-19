# Diccionario de variables
Frecuencia final mensual; clave `id_fondo_serie` + `mes`. AAF: https://fondosmutuos.pe/estadisticas/ (URL de cada PDF en manifiesto). BCRP: https://estadisticas.bcrp.gob.pe/estadisticas/series/api/ (código exacto abajo).

| Variable | Definición | Unidad / origen | Rol |
|---|---|---|---|
| mes | Mes del boletín | AAAA-MM, AAF | Tiempo |
| tipo | Clasificación de la tabla de origen | Categoría, AAF | Control y agrupación |
| fondo, administradora | Nombre reportado; administradora cuando se reconoce | Texto, AAF | Identificación |
| denominacion_original | Denominación original, incluye administradora cuando figura | Texto, AAF | Evidencia |
| id_fondo_serie | Denominación normalizada + moneda | Texto, calculada | Llave |
| moneda | Moneda de la cuota | PEN/USD, AAF | Control |
| estado | No informado por el boletín | Texto | Evidencia, no filtro |
| valor_cuota | Valor publicado de cuota | Moneda del fondo, AAF | Descriptivo |
| rent_mes | Rentabilidad mensual publicada | Decimal, AAF | Y |
| rent_lag1 | Rentabilidad del mes calendario previo, faltante si no existe | Decimal, calculada | X3 |
| tc_fin | Tipo cambio interbancario promedio fin de periodo | PEN/USD, BCRP PN01216PM | Insumo |
| tasa_pen / tasa_usd | Media mensual de observaciones diarias interbancarias | % anual, BCRP PD04692MD / PD04693MD | Insumo |
| var_tc | Diferencia logarítmica del TC fin de mes | Decimal, calculada | X2 |
| rf_pen / rf_usd | (1+tasa/100)^(1/12)-1 | Decimal mensual, calculada | Referencia |
| rf_mensual | Referencia de la moneda del fondo | Decimal, calculada | Insumo |
| exceso | rent_mes - rf_mensual | Decimal, calculada | Sharpe |
| vol12 | Desv. estándar muestral de los 12 meses anteriores; mínimo 6 | Decimal mensual, calculada | X1 |
| atipico | Fuera de Q1–3RIQ a Q3+3RIQ por tipo y moneda | 0/1, calculada | Robustez |
| imputado | No se imputan valores | 0, calculada | Control |
| muestra_modelo | Y y X1–X3 disponibles | 0/1, calculada | Control |
| archivo / pagina / fila_original | Ubicación y texto leído del PDF | Texto/número, AAF | Trazabilidad |
