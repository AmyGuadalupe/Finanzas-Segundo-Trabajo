# Instrucciones de uso y publicación

## Incorporar documentos de Google Drive
1. Suba cada archivo a Drive y compártalo con la opción de que cualquiera con el enlace pueda ver.
2. Copie el enlace de compartir.
3. Abra `config/documentos.json`, busque el póster por su identificador (A01 a A30) o el producto principal, pegue el enlace en el campo correspondiente (artículo en inglés, traducción, póster o proyecto) y cambie su estado a «disponible».
4. Si un artículo no puede distribuirse públicamente, use el enlace editorial o el DOI y el estado «no distribuible».
5. Guarde. El portal deriva solo la vista previa y la descarga; un campo vacío no genera botón.

## Actualizar el repositorio sin tocar la investigación
Reemplace únicamente el contenido de la carpeta `dashboard/` del repositorio con esta carpeta. No modifique `codigo/`, `datos_crudos/`, `datos_procesados/`, `salidas/` ni `documentos/`. No cree una carpeta `dashboard/dashboard/`. La ruta de ejecución sigue siendo `dashboard/app.py`. Conserve la versión publicada hasta aprobar esta, y cambie la rama de publicación solo después de la aprobación.

## Comprobar la aplicación tras publicar
1. Abra el enlace público y confirme que carga la portada sin errores.
2. Entre a la sección 01 y pruebe las siete tarjetas, el retorno al menú y la biblioteca de pósteres.
3. Entre a la sección 02, mueva la línea de tiempo y cambie tipo, moneda y administradora.
4. En la pestaña Descargas, descargue el XLSX y ábralo en Excel; luego el CSV para Excel; verifique que no haya archivos vacíos.
5. Prepare un gráfico en PNG; si falla, avise para revisar Kaleido.
6. En Transparencia, recalcule los hashes.
7. Revise la vista móvil.
