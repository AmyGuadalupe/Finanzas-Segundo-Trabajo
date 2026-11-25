# Verificación computacional local

Fecha de ejecución: 2026-11-25T18:20:33-05:00

Prueba 1. Integridad: 128 hashes originales conformes.

Prueba 2. Reparseo de JSON de BCRP y PDF AAF entregados.

Prueba 3. Reestimación de limpieza, variables calculadas, tablas y modelos desde los crudos.

Prueba 4. 39 CSV equivalentes al umbral del 95%; mínimo observado 100.00%. 6 figuras regeneradas; no se exige identidad de bytes PNG entre plataformas.

- datos_crudos/datos_crudos_2024200501G_aaf.csv: 186552/186552 celdas (100.00%); tipos y claves conformes.

- datos_crudos/datos_crudos_2024200501G_bcrp.csv: 30248/30248 celdas (100.00%); tipos y claves conformes.

- datos_crudos/scraping/control_parseo_2024200501G.csv: 539/539 celdas (100.00%); tipos y claves conformes.

- datos_crudos/scraping/descargas_boletines_2024200501G.csv: 462/462 celdas (100.00%); tipos y claves conformes.

- datos_crudos/scraping/filas_no_reconocidas_2024200501G.csv: 204/204 celdas (100.00%); tipos y claves conformes.

- datos_procesados/base_integrada_observada.csv: 175318/175318 celdas (100.00%); tipos y claves conformes.

- datos_procesados/datos_procesados_2024200501G.csv: 128832/128832 celdas (100.00%); tipos y claves conformes.

- salidas/duplicados_conflictivos.csv: 832/832 celdas (100.00%); tipos y claves conformes.

- salidas/filas_excluidas.csv: 4082/4082 celdas (100.00%); tipos y claves conformes.

- salidas/tabla10_control_cuotas.csv: 60/60 celdas (100.00%); tipos y claves conformes.

- salidas/tabla11_robustez_ventana_saltos.csv: 216/216 celdas (100.00%); tipos y claves conformes.

- salidas/tabla12_efectos_fijos.csv: 168/168 celdas (100.00%); tipos y claves conformes.

- salidas/tabla13_sensibilidad_inferencia.csv: 162/162 celdas (100.00%); tipos y claves conformes.

- salidas/tabla14_contrastes_tipo.csv: 66/66 celdas (100.00%); tipos y claves conformes.

- salidas/tabla15_distribucion_sharpe.csv: 60/60 celdas (100.00%); tipos y claves conformes.

- salidas/tabla16_descriptivos.csv: 100/100 celdas (100.00%); tipos y claves conformes.

- salidas/tabla17_desempeno_sensibilidad.csv: 60/60 celdas (100.00%); tipos y claves conformes.

- salidas/tabla18_muestras.csv: 16/16 celdas (100.00%); tipos y claves conformes.

- salidas/tabla19_sharpe_contraste_exploratorio.csv: 84/84 celdas (100.00%); tipos y claves conformes.

- salidas/tabla1_metricas_por_fondo_serie.csv: 528/528 celdas (100.00%); tipos y claves conformes.

- salidas/tabla20_cobertura_tipos_observados.csv: 140/140 celdas (100.00%); tipos y claves conformes.

- salidas/tabla21_desempeno_observado_contextual.csv: 2205/2205 celdas (100.00%); tipos y claves conformes.

- salidas/tabla22_desempeno_sin_winsorizar.csv: 462/462 celdas (100.00%); tipos y claves conformes.

- salidas/tabla2_riesgo_rentabilidad_por_tipo.csv: 70/70 celdas (100.00%); tipos y claves conformes.

- salidas/tabla3_modelo_principal.csv: 108/108 celdas (100.00%); tipos y claves conformes.

- salidas/tabla4_modelo_inicial_mco.csv: 36/36 celdas (100.00%); tipos y claves conformes.

- salidas/tabla5_robustez.csv: 324/324 celdas (100.00%); tipos y claves conformes.

- salidas/tabla6_vif.csv: 18/18 celdas (100.00%); tipos y claves conformes.

- salidas/tabla7_diagnosticos.csv: 5/5 celdas (100.00%); tipos y claves conformes.

- salidas/tabla8_rentabilidades_mensuales.csv: 2440/2440 celdas (100.00%); tipos y claves conformes.

- salidas/tabla9_auditoria_financiera.csv: 680/680 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_cobertura_mensual.csv: 305/305 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_cobertura_variables.csv: 16/16 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_contexto_bcrp.csv: 595/595 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_homologacion.csv: 75920/75920 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_limites_tukey.csv: 84/84 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_seleccion_series.csv: 2217/2217 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_tratamientos.csv: 18732/18732 celdas (100.00%); tipos y claves conformes.

- salidas/tabla_ventanas_candidatas.csv: 90/90 celdas (100.00%); tipos y claves conformes.

APROBADO: reproducción computacional local. No equivale a acreditar una consulta nueva de las fuentes vivas.
