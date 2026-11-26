# Incidencias de fuente
- SMV: `https://www.smv.gob.pe/robots.txt`, 19/11/2026, 11:47 (Lima), HTTP 418, según captura de Colab de la estudiante. El programa anterior se detuvo. Este proyecto no vuelve a consultar la SMV ni cambia de conexión para eludir restricciones.
- Vía alternativa: boletines mensuales públicos de AAF, https://fondosmutuos.pe/estadisticas/. Se preserva la evidencia original descargada y las reglas de rastreo.
- Autorización (numeral 2.4.3): el 25/11/2026 el docente del curso, Dr. Ciro Iván Machacuay Meza, autorizó el uso de los boletines de la AAF como fuente alternativa a la SMV.
- Los nuevos errores y el resultado del parseo se registran en el log y en los archivos de control; se distinguen los meses observados de los huecos interiores estimados y se registra su tratamiento; no se inventan datos diarios.

- BCRP: HTTP 403 en un intento anterior del 20/11/2026. En este notebook se exige una consulta directa nueva; no se recuperan JSON desde GitHub como sustitución. El resultado nuevo queda en el log.

- Evidencia primaria: `documentos/captura_bloqueo_smv.png`, captura del intento del 19/11/2026 a las 11:47:14. Se conserva íntegra; muestra el intento histórico con Drive, no una dependencia del cuaderno vigente.
