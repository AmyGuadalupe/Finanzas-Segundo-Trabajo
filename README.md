# Fondos mutuos en el Perú: rentabilidad y riesgo por tipo de fondo
Amy Pamela Guadalupe Cordova · 2024200501G · UNCP · Finanzas I (055D) · Unidad II · Tema 79

Objetivo: comparar desempeño ajustado por riesgo. Periodo objetivo 2019-01 a 2025-12; observado 2022-12 a 2025-11, 34 meses; 8038 filas de fondo/serie-mes; 772 denominaciones identificadas; 4454 filas completas de estimación. No son fondos únicos verificados por código registral. Modelo Y = rent_mes, X1=vol12, X2=var_tc, X3=rent_lag1, controles de tipo y moneda; errores agrupados por serie y mes. El número de meses independientes es menor que el número de filas del panel. No se dispone de patrimonio y partícipes individuales de forma homogénea ni de rentabilidad diaria. Ver metodología y límites en el cuaderno. No se declara autorización de sustitución sin constancia.

## Fuentes y endpoints
API BCRP: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{inicio}/{fin}/esp`; PN01216PM, PD04692MD, PD04693MD. Fechas reales en log. AAF: `https://fondosmutuos.pe/estadisticas/`, PDF exactos y hashes en `datos_crudos/scraping/descargas_boletines_2024200501G.csv`. Llave: mes, armonización desde días efectivos de tasas. Boletines PDF originales intactos. Rutas relativas a cada script. Python 3.13.18, versiones exactas en requirements.txt.

## Reproducción por el docente (sin consultar fuentes)
```
git clone https://github.com/AmyGuadalupe/Finanzas-Segundo-Trabajo.git
cd Finanzas-Segundo-Trabajo
python -m pip install -r requirements.txt
python codigo/05_verificacion_fuente.py --sin-internet
```
05 coteja hash de lo entregado antes de ejecutar, copia originales a un directorio temporal, ejecuta 01 y 02 localmente para reparsear JSON/PDF, 03 y 04 para regenerar la base y tablas. 03 y 04 son ejecutables independientemente. No necesita token ni Drive. Para una nueva extracción, usar otra copia del repositorio y ejecutar 01, 02, 03 y 04 en orden; no modificar originales entregados. Demostración en vivo: `python codigo/01_extraccion_api.py --demo` y `python codigo/02_scraping_web.py --demo`, solo si el acceso está permitido. No confundir esta demostración con la reproducción local.

## Integridad
SHA-256 de la base: `218d06420bc257a2ce6f336295a18bc184444d2fa8b3d9164bb6e0e4dbc97dd2`. Manifiesto `hash_sha256.txt`. Cobertura por variable: `salidas/tabla_cobertura_variables.csv`. Tablas y figuras en `salidas/`; cada archivo empírico es generado por código. Integridad y equivalencia se verifican en el paso siguiente; no se anticipa el veredicto.

## Fuentes en formato APA
Banco Central de Reserva del Perú. (s. f.). *BCRPData: Series estadísticas de tipo de cambio e interbancarias* [Conjunto de datos]. Recuperado el 19 de noviembre de 2026, de https://estadisticas.bcrp.gob.pe/estadisticas/series/

Asociación de Administradoras de Fondos del Perú. (s. f.). *Estadísticas mensuales de fondos mutuos* [Informes estadísticos]. Recuperado el 19 de noviembre de 2026, de https://fondosmutuos.pe/estadisticas/ (consultas registradas del 19 de noviembre de 2026 al 19 de noviembre de 2026).

Repositorio: https://github.com/AmyGuadalupe/Finanzas-Segundo-Trabajo
