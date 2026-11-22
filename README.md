# Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo

## 1. Identificación académica

- **Autora:** Amy Pamela Guadalupe Cordova
- **Código:** 2024200501G
- **Universidad:** Universidad Nacional del Centro del Perú, Facultad de Economía, Escuela Profesional de Economía.
- **Curso:** Finanzas I (055D), 2026-II, Unidad II.
- **Docente:** Dr. Ciro Iván Machacuay Meza.
- **Tema 79 (S12):** Diversificación y gestión del riesgo.
- **Repositorio:** https://github.com/AmyGuadalupe/Finanzas-Segundo-Trabajo

## 2. Objetivo y alcance

Comparar el desempeño ajustado por riesgo de los fondos mutuos peruanos por tipo y moneda.

Objetivos específicos operativos:

1. Construir un panel mensual a partir de boletines publicados y series del BCRP.
2. Medir rentabilidad, volatilidad y Sharpe anualizados por denominación/serie y resumir sus distribuciones por categoría.
3. Estimar la asociación de tres factores con la rentabilidad mensual y examinar la sensibilidad de la inferencia.
4. Comparar el exceso de rentabilidad y el Sharpe de grupos en ventanas comunes, declarando las limitaciones.

El diseño es observacional, longitudinal, de panel balanceado. No identifica causalidad ni recomienda comprar fondos.
La unidad es fondo-serie homologado por administradora, denominación y moneda, observado o estimado en un mes; no es un identificador registral SMV. Varias clases pueden pertenecer al mismo fondo. La homologación conserva series y moneda; se registran las variantes exactas y se excluyen conflictos. No se usa coincidencia difusa automática. Las comparaciones dan igual peso a las series observadas, no a patrimonio ni partícipes.

## 3. Fuentes y endpoints exactos

**Vía 1: API REST BCRPData**, pública y sin clave de API. Los nombres de las series proceden de los metadatos JSON. El script 01 consulta directamente los tres endpoints en cada ejecución del notebook, sin recuperar respuestas de GitHub ni de archivos personales. El 20/11/2026 se registró HTTP 403 en un intento anterior; en la presente versión no se usa esa recuperación histórica como sustituto de la extracción. Si la API rechaza el acceso, se registra el error y no se continúa con una entrega incompleta. La opción `--local` se reserva para la reproducción de los datos entregados mediante el script 05.

| Código | Serie publicada | Frecuencia | Unidad | Endpoint congelado |
|---|---|---|---|---|
| PN01216PM | Tipo de cambio - fin de periodo (S/ por US$) - Interbancario - Promedio | mensual | S/ por USD | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01216PM/json/2018-12/2025-12/esp` |
| PD04692MD | Tasas de interés - Interbancaria, S/ | diaria | % anual | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04692MD/json/2018-12-01/2025-12-31/esp` |
| PD04693MD | Tasas de interés - Interbancaria, US$ | diaria | % anual | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04693MD/json/2018-12-01/2025-12-31/esp` |

- `FECHA_INICIO = 2018-12-01`; `FECHA_CORTE = 2025-12-31`. El mes previo permite calcular la variación cambiaria desde enero de 2019.
- Se conserva cada respuesta JSON íntegra en `datos_crudos/api/` y su CSV tabular asociado, incluyendo valores no numéricos originales.
- La media mensual de las tasas diarias usa solo valores numéricos observados. El tipo de cambio mensual ya corresponde a fin de periodo; no se inventan días.

**Vía 2: descarga programática de boletines AAF** (Asociación de Administradoras de Fondos del Perú).

- Catálogo: https://fondosmutuos.pe/estadisticas/.
- Reglas de rastreo: https://fondosmutuos.pe/robots.txt.
- Boletín piloto: https://fondosmutuos.pe/wp-content/uploads/2025/02/Boletin-Enero-2025-9.pdf.
- El inventario `datos_crudos/scraping/descargas_boletines_2024200501G.csv` contiene cada URL consultada con resultado PDF válido, fecha, HTTP y SHA-256. El archivo `listado_aaf.html` conserva el catálogo consultado.
- Ventana congelada del catálogo: `2019-01` a `2025-12`, constantes del script 02. Se analizan hipervínculos `a[href]` a PDF de boletines y sus encabezados `h1` a `h6` y nombres de archivo; no se inventa una paginación. La lectura usa PyMuPDF (formatos anteriores a diciembre de 2022) y pdfplumber (formatos modernos), área visible, portada, encabezados de categoría y patrones de columnas. Se comprueban ambos formatos con dos pilotos. Se rechazan los PDF cuya portada no coincide o con capas superpuestas que impiden validar el tipo: por ejemplo, el enlace de junio de 2024 no declara junio y diciembre de 2025 tiene texto superpuesto. El control de parseo registra las incidencias.
- Se exige al menos 25 filas reconocidas y 90 % de líneas candidatas identificadas por boletín. Esta tasa se refiere al parser, no prueba que el universo publicado esté completo. Se guarda el texto de cada fila, página y archivo.
- Se respetan robots.txt, redirecciones normales del portal, User-Agent identificable y pausas de 1,5 segundos. Ante rechazo explícito se detiene el acceso; enlaces 404/410 o que no son PDF se registran. No se navega alrededor de un bloqueo.

**Justificación y límite institucional.** El tema 79 del temario sugiere SMV diaria y BCRPData; AAF no aparece nombrada como fuente sugerida. La rúbrica 2.4.1 admite otras fuentes y 2.4.3 permite PDF descargados y parseados programáticamente, preservando su original. El bloqueo de SMV (HTTP 418) está descrito en `incidencias_fuente.md`. No se afirma contar con autorización docente de sustitución sin constancia real. Los boletines son publicaciones de la asociación, no una descarga directa de la SMV. El boletín de enero de 2025, página 7, declara que sus datos se obtuvieron del portal SMV para el periodo correspondiente; precisa que las rentabilidades no incluyen comisiones de suscripción/rescate ni impuesto a la renta. La captura original `documentos/captura_bloqueo_smv.png` acredita el rechazo HTTP 418 del intento de la Unidad II. Sigue siendo necesario registrar la autorización escrita prevista en 2.4.3 si corresponde.

## 4. Cobertura observada y control de tamaño

Fecha de consulta API: 2026-11-21; consultas AAF: 2026-11-21 a 2026-11-21.

| Indicador | Valor |
|---|---:|
| Registros crudos BCRP (diarios y mensuales) | 3781 |
| Filas crudas reconocidas AAF | 15546 |
| PDF originales conservados | 77 |
| Boletines aceptados por parser | 75 |
| Boletines descargados excluidos por parser | 2 |
| Periodo observado en panel | 2020-08 a 2025-08 |
| Meses calendario del panel | 61 |
| Meses legibles en crudo AAF | 75 |
| Filas interpoladas del panel | 175 |
| Filas con retorno winsorizado | 133 |
| Valores faltantes de la base definitiva | 0 |
| Tipos presentes en panel | Acciones, Deuda, Flexibles, Fondo de fondos, Mixtos |
| Tipos solo en análisis contextual | ETF, Estructurados |
| Meses faltantes dentro del periodo observado | Ninguno |
| Filas finales y columnas | 4026 × 32 |
| Denominaciones/series distintas | 66 |
| Filas completas en MCO | 4026 |
| Meses de estimación | 61 |
| Series de estimación | 66 |

| Variable | Filas válidas | Meses distintos |
|---|---:|---:|
| rent_mes | 4026 | 61 |
| vol12 | 4026 | 61 |
| var_tc | 4026 | 61 |
| rent_lag1 | 4026 | 61 |

El control del script 03 exige al menos 4 000 filas completas y 60 meses comunes, sin NA ni duplicados, con todas las unidades sobre exactamente los mismos meses. Esta es una meta interna superior al mínimo general de la rúbrica. Cada Y y X dispone de igual número de filas. La frecuencia es mensual y la cantidad de observaciones macroeconómicas independientes corresponde a los meses del panel, no a sus filas. El mínimo se interpreta como datos de panel; el tipo de cambio se repite entre fondos del mismo mes y no convierte esas repeticiones en observaciones macroeconómicas independientes. La cobertura lograda es inferior a la sugerida de 2018 a 2025 diaria y 60 000 filas; No se generan observaciones diarias artificiales ni se extrapolan series. Las interpolaciones limitadas están identificadas y no se presentan como datos publicados. No se dispone de patrimonio ni partícipes por serie de manera homogénea.

## 5. Estructura del repositorio (Carpeta N.º 3)

```text
codigo/
  00_pipeline_colab.ipynb      Cuaderno completo, ejecutable en Colab, con salidas visibles
  01_extraccion_api.py         API, JSON y crudo BCRP
  02_scraping_web.py           Catálogo, robots, boletines y crudo AAF
  03_limpieza_datos.py         Limpieza, llave, unión y variables
  04_analisis.py               Tablas, gráficos, estimación y sensibilidad
  05_verificacion_fuente.py    Integridad, reproducción y cotejo con fuente viva
datos_crudos/
  datos_crudos_2024200501G_bcrp.csv
  datos_crudos_2024200501G_aaf.csv
  api/                         Respuestas JSON completas
  scraping/                    Catálogo, robots, inventario y controles de parseo
    pdf_boletines/             Archivos PDF originales
datos_procesados/
  datos_procesados_2024200501G.csv  Panel balanceado definitivo, completo
  base_integrada_observada.csv    Registros originales depurados, antes de selección y tratamiento
salidas/                      Tablas, figuras, exclusiones y verificaciones
documentos/                   Bitácora de IA, estado de ejecución, documentación de evidencias
README.md                     Este instructivo
requirements.txt              Dependencias directas y versiones exactas
.env.example                  Nombre de la variable GitHub, sin clave
.gitignore                    Exclusiones de credenciales y caché
hash_sha256.txt                Huellas de crudos, procesado y productos empíricos
log_ejecucion.txt              Eventos, fecha, hora, HTTP y filas
incidencias_fuente.md          Bloqueo SMV y procedimiento alternativo
diccionario_variables.md       Variables, unidades, frecuencias y origen
enlace_repositorio_github.txt   URL del proyecto
```

La Carpeta N.º 1 (productos) y la N.º 2 (desarrollo de plantillas) corresponden a la entrega académica, no se declaran terminadas por ejecutar este notebook.

## 6. Reproducción desde un computador limpio

En una terminal (sin Drive ni credenciales personales):

```bash
git clone https://github.com/AmyGuadalupe/Finanzas-Segundo-Trabajo.git
cd Finanzas-Segundo-Trabajo
python -m pip install -r requirements.txt
python codigo/05_verificacion_fuente.py --sin-internet
```

La verificación local comprueba primero los hashes originales, reparsea ambos crudos en una carpeta temporal y vuelve a ejecutar 03 y 04. Compara las dimensiones, tipos inferidos, claves y celdas de cada CSV. El umbral mínimo por archivo es 95 %. En particular, las figuras deben regenerarse; no se requiere igualdad binaria de PNG entre distintas plataformas.

Para reejecutar solamente los scripts de análisis sobre los crudos ya entregados, en una copia independiente:

```bash
python codigo/03_limpieza_datos.py
python codigo/04_analisis.py
```

Para extraer nuevamente desde las fuentes (solo en una copia de trabajo NUEVA, con carpetas de datos vacías; no sobrescribir la entrega sellada):

```bash
python codigo/01_extraccion_api.py
python codigo/02_scraping_web.py
python codigo/03_limpieza_datos.py
python codigo/04_analisis.py
```

La reextracción puede diferir por revisiones o disponibilidad del portal. Nunca se recalcula el hash original para ocultar diferencias. Las fechas permanecen congeladas. El notebook prepara directorios y escribe los scripts, ejecuta las etapas, genera documentación y manifiesto, verifica, guarda sus salidas visibles, descarga ZIP y publica cambios reales. Estos últimos pasos son exclusivos del flujo de la estudiante, no de la reproducción docente.

## 7. Demostración de autenticidad en vivo

Desde el clon anterior, el docente puede ejecutar:

```bash
python codigo/05_verificacion_fuente.py --en-vivo
```

El comando sin argumentos hace ambas verificaciones: `python codigo/05_verificacion_fuente.py`.
El modo de exposición es acotado y evita volver a descargar todos los boletines. Selecciona diez filas completas al azar dentro del último mes elegible, antes de consultar las fuentes (semilla 501). Consulta dos PDF consecutivos y las tres series BCRP de esa ventana, coteja cuota, rentabilidad publicada antes de winsorizar, rezago original, TC y tasa mensual de referencia; la muestra excluye filas interpoladas de t y t-1 con sus URL y página. Las series macro se cotejan también en sus fechas originales. La volatilidad histórica se verifica por reparseo y recálculo local; no se afirma consultarla íntegramente en la demostración corta.

Los informes `salidas/verificacion_equivalencia.csv` y `salidas/verificacion_local.md` documentan la reproducción local; `salidas/verificacion_cotejo_vivo.csv` y `salidas/verificacion_en_vivo.md` se crean al ejecutar el cotejo en vivo. El segundo requiere acceso real y distingue coincidencia, discrepancia y acceso no verificable. Si falla una consulta, no se usa la copia local como si fuera una respuesta nueva. El verificador no altera los originales ni los hashes; sus informes posteriores no son parte del manifiesto previo.

## 8. Versiones y credenciales

| Componente | Versión de ejecución |
|---|---|
| Python | 3.13.18 |
| requests | 2.32.5 |
| pandas | 2.2.3 |
| numpy | 2.3.5 |
| scipy | 1.17.0 |
| statsmodels | 0.14.6 |
| matplotlib | 3.10.8 |
| beautifulsoup4 | 4.14.3 |
| pdfplumber | 0.11.9 |
| PyMuPDF | 1.26.7 |

Las API y boletines son públicos y no requieren claves. `GITHUB-TOKEN` es el nombre del secreto de Colab que utiliza únicamente la celda de publicación; `GITHUB_TOKEN` es la variable temporal de entorno usada por Git. No se incluye valor en la entrega ni se agrega el token a la URL. El script 05 no necesita token. La estudiante configura el secreto en Colab a partir de un token de su cuenta con permisos de escritura únicamente en el repositorio correspondiente. No se publica un commit si no existen cambios.

## 9. Limpieza, unión y memoria de cálculo

- Se convierte cada rentabilidad publicada en porcentaje a decimal. PDF, captura textual y CSV crudo permanecen intactos. Se excluyen retornos no numéricos, inferiores a -100 %, cuotas no positivas y administradoras no identificadas del conjunto candidato. Los registros excluidos y los duplicados conflictivos se documentan.
- Llave `id_fondo_serie`: administradora homologada mediante alias explícitos, denominación normalizada y moneda; se conservan los sufijos de clase, numerales y características distintivas. Se eliminan etiquetas genéricas de categoría/administradora repetidas y FMIV/FM como sufijos o tokens legales. Las colisiones conflictivas se excluyen, no se promedian. Se restringe a categorías estables en la historia observada. La continuidad de cuatro fondos SURA (Corto Plazo y Ultra Cash, en soles y dólares) con la Serie A se documenta mediante el historial anterior a 2025 que la administradora publica para la Serie A y el inicio de la Serie B el 16 de mayo de 2025. Fuente: Fondos SURA, sección Productos, https://www.fondossura.pe/productos (consulta: 20/11/2026). No se fusiona la Serie B ni se altera el nombre publicado. Consultar `tabla_homologacion.csv` para las variantes, no asumir que son identificadores registrales. BCRP se une mediante `mes` con cardinalidad `many_to_one`.
- Interpolación geométrica únicamente en huecos interiores de una a tres filas totalmente ausentes y delimitados por cuotas positivas. Si faltan k retornos, sea C_a la cuota anterior, C_b la cuota posterior y r_b el retorno publicado de ese mes posterior. La tasa estimada de cada mes faltante es (C_b / (C_a × (1+r_b)))^(1/k) − 1. Las cuotas intermedias se calculan acumulando esa tasa. Se preserva el retorno posterior publicado; no se reemplazan valores observados. Se rechaza la interpolación si el factor no es positivo o el retorno implícito absoluto es ≥50 %. Nunca se inventan datos antes del inicio o después del último registro, ni se interpola una tasa BCRP. Se identifica `imputado=1`, `archivo=INTERPOLACION`, `pagina=0` y se registra la evidencia de ambos meses. Posibles distribuciones o cambios de escala impiden considerar la estimación un retorno observado.
- Winsorización de retornos pretratamiento: límites Q1−3RIQ y Q3+3RIQ calculados por tipo y moneda con registros observados (no interpolados); límite inferior no menor que −100 %. Si RIQ=0 no se recorta automáticamente. El retorno utilizado es el original o estimado recortado al límite correspondiente; la cuota no se recorta. Se registran `rent_original`, `atipico`, los límites y el historial. Las X derivadas se recalculan desde la serie de retornos tratada; los crudos se conservan.
- Panel balanceado: se examinan ventanas consecutivas de mínimo 60 meses, al menos 4 tipos, historia suficiente para X1/X3, todas las variables y trazabilidad presentes. Se admite un máximo del 15 % de retornos imputados por serie en la ventana y su historial efectivamente disponible al inicio. Se exige una ventana de ≥60 meses y ≥4 000 filas; entre las candidatas se prioriza el número de categorías, las filas y la duración. Si no se alcanza el mínimo, se detiene la entrega. La lista de ventanas y selección se guarda. No se usa R², p ni resultados de Sharpe como criterio. Todas las series seleccionadas tienen las mismas fechas; no se obliga a los grupos a tener el mismo número de fondos. Las categorías sin suficiente historia se describen por separado con datos observados.
- Variable dependiente Y: `rent_mes`, rentabilidad mensual en decimal tras winsorización, con interpolaciones marcadas. Esta no es una función algebraica de las X del mismo periodo.
- X1 `vol12`: desviación estándar muestral de las rentabilidades tratadas de los 12 meses calendario anteriores, con mínimo 6 retornos disponibles. `historia_n`, `historia_imputada` y `historia_atipica` describen esa ventana. Se calcula también X1 sin winsorizar para sensibilidad.
- X2 `var_tc`: ln(TC_t) - ln(TC_(t-1)), con TC expresado en soles por dólar. Positivo indica depreciación del sol.
- X3 `rent_lag1`: rentabilidad tratada del mes inmediatamente anterior de la misma serie. No se usa el último dato si hubo un hueco calendario.
- Referencia `rf_mensual`: (1 + tasa_anual/100)^(1/12) - 1, seleccionada por moneda, usando la tasa interbancaria promedio de días observados como aproximación anualizada. No es una tasa libre de riesgo invertible directamente ni se afirma equivalencia exacta de convenciones de cotización.
- Exceso = retorno menos referencia. Retorno anualizado = exp(12 × promedio de ln(1+r)) - 1; cuando hay -100 % el valor se define como -100 %. Volatilidad anualizada = desviación muestral de r × raíz(12). Sharpe anualizado = media del exceso / desviación muestral del exceso × raíz(12); puede no estar definido si la desviación es cero. En la comparación principal se utilizan los meses comunes del panel (observados o estimados). En la comparación contextual se exigen al menos 12 meses observados consecutivos y se declara el horizonte de cada serie. Con autocorrelación, anualizar por raíz(12) es una convención, no una estimación garantizada del riesgo anual.
- La tasa y el TC del BCRP alimentan resultados financieros y regresiones; no son una fuente decorativa. El archivo diccionario describe cada columna por separado.

## 10. Metodología econométrica y análisis financiero

**Modelo inicial:** MCO de rent_mes sobre vol12, var_tc, rent_lag1, indicadores del tipo de fondo y moneda. Son tres regresores sustantivos; tipo/moneda son controles. Se muestra el resultado clásico como referencia y el mismo modelo con errores estándar agrupados por serie y mes como inferencia principal. Se informa R², intervalos de confianza y valores p; esto no demuestra causalidad. La variable cambiaria tiene variación temporal común; la inferencia es limitada por la cantidad de meses, aun cuando haya miles de filas.

**Diagnóstico:** VIF, rango de la matriz y correlación residual rezagada dentro de segmentos mensuales consecutivos. No se interpreta esta correlación descriptiva como prueba formal de ausencia de autocorrelación. No se aplican ADF, Durbin-Watson, Breusch-Godfrey, White o CUSUM a la concatenación de fondos como si fuera una serie univariada. Los errores agrupados admiten dependencia intra-serie e intra-mes, pero no solucionan automáticamente todos los sesgos de especificación. Covarianzas no estimables se conservan como faltantes y se identifican, sin reemplazar por cero.

**Atípicos y robustez:** winsorización con los límites de Tukey descritos arriba, siguiendo el criterio utilizado en Unidad I. Se estima nuevamente Y, X1 y X3 sin winsorizar sobre exactamente las mismas filas. Se realiza una segunda sensibilidad excluyendo las filas interpoladas o cuyos 12 meses previos contengan interpolaciones, sin afirmar que ese subconjunto siga siendo balanceado. La auditoría de cuota contrasta únicamente retornos publicados PREVIOS al tratamiento y cuotas originales consecutivas (sin interpolación). Alertas por salto absoluto ≥50 % o discrepancia ≥1 punto porcentual; no se presume error o fraude. Se reporta sensibilidad de ventanas de saltos, sin usar el R² como criterio de selección. Si se incluyen valores estimados, la inferencia es condicional a esos valores y no incorpora incertidumbre completa de imputación. No es un modelo de pronóstico: los huecos internos se completan utilizando información posterior dentro del periodo histórico. Se calcula desempeño con y sin winsorización sobre las mismas filas. Los datos no tratados e imputados se identifican por separado.

**Alternativas de inferencia:** MCO agrupado solo por serie o solo por mes, como sensibilidad; efectos fijos de serie mediante transformación dentro de la unidad, sin controles invariantes ni efectos fijos mensuales que absorberían el TC. Se excluyen unidades con una sola observación para ese cálculo; se informa ajuste finito por interceptos absorbidos. El rezago de Y en modelos dinámicos de efectos fijos puede inducir sesgo: son alternativas exploratorias y no modelos causales. Las ventanas de atípicos pueden modificar la muestra y su composición.

**Comparación por tipo y moneda:** mediana e intervalo intercuartílico de Sharpe de series, con tamaño del grupo. Comparación temporal complementaria: diferencia de medianas mensuales de exceso frente a Deuda, exige tres series por categoría/mes y al menos doce meses consecutivos comunes; se utiliza el bloque común más largo (si empatan, el primero cronológicamente), MCO de intercepto con errores HAC de tres rezagos y corrección Holm de los valores p. Se calcula también la diferencia de Sharpe de esas series agregadas de medianas con remuestreo pareado circular por bloques de tres meses, 1 999 réplicas y semilla 501. Estos intervalos son exploratorios, no simultáneos ni corregidos por multiplicidad. Los grupos con pocos fondos y otros periodos no son comparables inferencialmente; no representan portafolios ponderados por patrimonio. Con pocos meses hay incertidumbre considerable. Ninguna prueba adicional se añade solo para aparentar rigor.

## 11. Inventario de resultados y trazabilidad

- `salidas/duplicados_conflictivos.csv`
- `salidas/figura1_riesgo_rentabilidad.png`
- `salidas/figura2_sharpe_por_tipo.png`
- `salidas/figura3_rentabilidad_mensual.png`
- `salidas/figura4_coeficientes.png`
- `salidas/figura5_distribucion_sharpe.png`
- `salidas/figura6_contrastes_tipo.png`
- `salidas/filas_excluidas.csv`
- `salidas/tabla10_control_cuotas.csv`
- `salidas/tabla11_robustez_ventana_saltos.csv`
- `salidas/tabla12_efectos_fijos.csv`
- `salidas/tabla13_sensibilidad_inferencia.csv`
- `salidas/tabla14_contrastes_tipo.csv`
- `salidas/tabla15_distribucion_sharpe.csv`
- `salidas/tabla16_descriptivos.csv`
- `salidas/tabla17_desempeno_sensibilidad.csv`
- `salidas/tabla18_muestras.csv`
- `salidas/tabla19_sharpe_contraste_exploratorio.csv`
- `salidas/tabla1_metricas_por_fondo_serie.csv`
- `salidas/tabla20_cobertura_tipos_observados.csv`
- `salidas/tabla21_desempeno_observado_contextual.csv`
- `salidas/tabla22_desempeno_sin_winsorizar.csv`
- `salidas/tabla2_riesgo_rentabilidad_por_tipo.csv`
- `salidas/tabla3_modelo_principal.csv`
- `salidas/tabla4_modelo_inicial_mco.csv`
- `salidas/tabla5_robustez.csv`
- `salidas/tabla6_vif.csv`
- `salidas/tabla7_diagnosticos.csv`
- `salidas/tabla8_rentabilidades_mensuales.csv`
- `salidas/tabla9_auditoria_financiera.csv`
- `salidas/tabla_cobertura_mensual.csv`
- `salidas/tabla_cobertura_variables.csv`
- `salidas/tabla_contexto_bcrp.csv`
- `salidas/tabla_homologacion.csv`
- `salidas/tabla_limites_tukey.csv`
- `salidas/tabla_seleccion_series.csv`
- `salidas/tabla_tratamientos.csv`
- `salidas/tabla_ventanas_candidatas.csv`

Las tablas y figuras se producen exclusivamente desde los datos y scripts. `tabla20_cobertura_tipos_observados.csv` muestra categorías representadas y omitidas del panel. `tabla21_desempeno_observado_contextual.csv` conserva métricas contextuales de tramos observados de al menos 12 meses, no directamente comparables a la muestra balanceada. `tabla22_desempeno_sin_winsorizar.csv` usa el mismo panel antes de winsorizar. El artículo, presentación y póster deben citar sus números y resultados auténticos, no valores copiados a mano. `tabla_contexto_bcrp.csv` muestra el procesamiento mensual de la API y `tabla_cobertura_variables.csv` permite controlar el mínimo. La trazabilidad a PDF utiliza `archivo`, `pagina`, `fila_original` y el inventario de URL.

## 12. Integridad y reproducibilidad

SHA-256 del archivo procesado entregado:

```text
77da558e99a819df5496dd7385767b1b90e34ae44cfa98589100684e4162c669
```

El manifiesto `hash_sha256.txt` se genera antes de ejecutar 05, incluye crudos, procesado y salidas empíricas y excluye los informes posteriores de verificación. Consultar `salidas/verificacion_local.md` para el resultado real después de la ejecución. No se anticipa una aprobación; si el verificador falla el cuaderno no ofrece ZIP ni publica. El cotejo vivo se ejecuta aparte para no depender de la red al preparar la entrega. Revisiones oficiales deben documentarse, no asumirse.

## 13. Cumplimiento, límites y ética

| Numeral | Evidencia disponible / condición |
|---|---|
| 2.4.1 | Dos vías automatizadas, panel balanceado con al menos 4 000 filas, 60 meses y más de seis columnas, integración mensual; cobertura menor a sugerida y serie macro común por mes. |
| 2.4.2 | Cuatro scripts obligatorios y quinto voluntario, README, requisitos, plantilla de entorno, log y diccionario; encabezados de cuatro líneas y matrícula en nombres de bases. |
| 2.4.3 | Solicitud programática y parseo de PDF, originales intactos; incidente SMV documentado; no se presume autorización escrita. |
| 2.4.4 | Rutas relativas, comentarios en español, semilla 501, GitHub; mínimo tres fechas de commits debe comprobarse en historial, nunca simularse. |
| 2.4.5 | Fechas congeladas, SHA antes de reejecutar y equivalencia de CSV, tipos y dimensiones. |
| 2.4.6 | Muestra aleatoria de diez observaciones, comparación URL/página y valores en vivo; no se afirma verificación sin ejecutar. |
| 2.4.7 | Trabajo individual; no se atribuye una prueba de duplicidad del curso no realizada. |
| 2.4.8 | Pausas, User-Agent, reglas robots y no elusión de bloqueos; citar fuentes con fecha real de consulta. |

Limitaciones: selección de boletines legibles, faltantes temporales, ausencia de identificador SMV y datos homogéneos de patrimonio/partícipes, posibles cambios de denominación/clase, sesgo de supervivencia del panel balanceado (ETF y estructurados pueden quedar fuera), suavizado de retornos por interpolación y winsorización, comparación por moneda, tasa de referencia aproximada, pocas unidades temporales para inferencia, resultados sensibles a movimientos extremos. No se extrapola al universo de fondos ni se asegura desempeño futuro. La autorización (si corresponde), verificación viva, commits y productos académicos completos son condiciones que deben constar en evidencia real.

Uso de IA: la programación se desarrolló con asistencia de Claude y ChatGPT; se conserva bitácora en `documentos/bitacora_ia.md`. La estudiante debe ejecutar, cotejar y defender el contenido; no se afirma que revisó algo que aún no ha revisado.

## 14. Referencias de las fuentes de datos (APA 7)

Banco Central de Reserva del Perú. (s. f.). *BCRPData: Series estadísticas de tipo de cambio e interbancarias* [Conjunto de datos]. Recuperado el 21 de noviembre de 2026, de https://estadisticas.bcrp.gob.pe/estadisticas/series/

Asociación de Administradoras de Fondos del Perú. (s. f.). *Estadísticas mensuales de fondos mutuos* [Informes estadísticos]. Recuperado el 21 de noviembre de 2026, de https://fondosmutuos.pe/estadisticas/ (consultas registradas del 21 de noviembre de 2026 al 21 de noviembre de 2026).
