# Cambios visuales — rediseño animado e interactivo

## Resumen
El portal conserva íntegros la lógica, los datos y los filtros aprobados, y añade
una capa visual animada e interactiva construida con CSS y un motor JavaScript
idempotente. Toda la navegación y las descargas siguen funcionando sin JavaScript.

## Qué se mejoró, sin reemplazar nada

### Menú circular
- Se preserva el layout aprobado: siete tarjetas en las mismas posiciones, con sus
  iconos y etiquetas.
- Se dibujan los anillos concéntricos, las marcas de orbita, el barrido cónico, y
  el núcleo central con la serie que respira y la onda que sale en el último
  punto.
- Al pasar el cursor por una tarjeta se traza el rayo verde desde el núcleo hasta
  ella, aparece la etiqueta de la sección en el núcleo y la tarjeta reacciona con
  inclinación sutil y profundidad.
- La navegación por teclado (1–7, flechas y Esc) se documenta en pantalla.

### Portada
- Entrada escalonada: palabra por palabra del título, instituciones, metadatos,
  botones de acceso y cifras.
- Fondo con malla financiera (líneas sutiles de rentabilidad y barras) que se
  anima sin distraer.
- Cinco chips reales de categorías del panel con el mismo color que el dashboard
  y el número de fondos-series por categoría.
- Dos botones grandes con efecto de inclinación 3D sutil y brillo que sigue al
  cursor, para entrar a cada sección.

### Biblioteca de 30 pósteres
- Se mantiene el total, el filtrado y las claves de navegación.
- Cada tarjeta trae ahora la vista previa del póster (o un placeholder decente
  cuando aún no existe), el número a gran formato, el título y los autores, y
  una tira de badges que incluye el cuartil **solo cuando está verificado**.
- Al pasar el cursor se eleva, se destaca el borde y el número cambia al color
  de acento.
- La ficha individual vuelve con una presentación tipográfica más clara, con
  bloques de objetivo, método, resultados, contribución y referencia APA.

### Dashboard financiero (sección 02)
- Se mantienen la barra lateral de filtros, la línea de tiempo, los deslizadores,
  los atajos del periodo y las diez pestañas.
- Encabezado oscuro con malla y acento verde animado que respira, chips con
  separación correcta.
- Tarjetas KPI con elevación en hover, línea de acento que crece y entrada
  escalonada.
- Pestañas con subrayado que crece al cambiar de panel.
- Gráficos envueltos en marco redondeado con sombra suave al pasar el cursor.

### Transversales
- Se reduce el cromo de Streamlit no necesario: botón **Deploy**, decoración
  superior, iconos de ancla, status *running* visibles, scrollbars pesadas y el
  footer "Made with Streamlit".
- Se añade una barra superior con enlace a la portada, a las dos secciones, al
  repositorio y el toggle **Reducir animaciones**, que respeta además la
  preferencia del sistema `prefers-reduced-motion`.
- Se incorpora un enlace "Saltar al contenido" invisible hasta que recibe foco,
  y la entrada escalonada se desactiva por completo con el toggle.

## Qué no se tocó
- No se reemplazó el menú radial.
- No se reconstruyeron los filtros del dashboard ni de la biblioteca.
- No se modificaron `codigo/`, `datos_crudos/`, `datos_procesados/`, ni `salidas/`.
- No se publicó la aplicación ni se tocó el repositorio GitHub.

## Rendimiento y accesibilidad
- Las hojas CSS se cargan una sola vez por cambio de archivo.
- El motor JavaScript se inyecta una sola vez por versión al documento padre; si
  el navegador impide la inyección, el portal sigue funcionando.
- Las animaciones usan `transform` y `opacity`; evitan `box-shadow` animado en
  elementos grandes para no cargar el GPU.
- `prefers-reduced-motion` y el toggle manual eliminan las animaciones de reloj
  (barridos, orbitas, respiración) y reducen las transiciones a 1 ms.
