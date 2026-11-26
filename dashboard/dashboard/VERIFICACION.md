# Verificación — rediseño visual

## Pruebas automatizadas

### Pruebas que pasan (127 en total)

- `tests/test_portal.py` · 44 pruebas: exportes XLSX/CSV/ZIP, configuración,
  reproducibilidad de las tablas oficiales, navegación por secciones, pie de
  página único, descargas verificadas.
- `tests/test_dashboard.py` · 31 pruebas: integridad del panel, reproducción
  exacta de las medianas y matemática de los indicadores, filtros, R², PNG en
  alta resolución y Playwright.
- `tests/test_fichas.py` · 30 pruebas: una por cada una de las 30 fichas
  bibliográficas (metadatos mínimos, DOI con formato válido, cuartil NO
  declarado como verificado, renderizado individual).
- `tests/test_visual.py` · 22 pruebas nuevas, específicas del rediseño:
  - Siete hojas CSS presentes y concatenadas en orden alfabético.
  - El CSS base oculta `stDeployButton`, `stDecoration`, `stStatusWidget`.
  - La hoja de movimiento declara `prefers-reduced-motion` y el atributo del
    toggle `data-fm-reducir="1"`.
  - `static/interaccion.js` pasa `node --check`.
  - El cargador tiene versión estable y es idempotente (no recrea el motor si ya
    está instalado).
  - El marcador `#fm-meta` exporta vista, sección, ficha activa y estado del
    toggle.
  - El menú circular siempre tiene siete tarjetas, en el mismo orden.
  - La capa radial dibuja los siete rayos, el núcleo y el barrido.
  - El CSS posiciona las siete tarjetas con `--i:0` a `--i:6`.
  - Los atajos de teclado (←, →, Esc) salen en pantalla.
  - El título de la portada se segmenta en palabras con `--i` para la animación
    escalonada.
  - Los accesos grandes (`acceso1`, `acceso2`) siguen existiendo.
  - Las cinco categorías tienen un color asignado consistente con el dashboard.
  - La biblioteca mantiene cinco columnas y una clave de navegación por ficha
    (`a_<id>`).
  - El badge del cuartil solo aparece cuando `cuartil_verificado` es `True` (hoy
    todas las 30 fichas están en falso).
  - El placeholder del póster aparece cuando no hay imagen.
  - Los cinco filtros de la biblioteca (`b_q`, `b_anio`, `b_cuartil`,
    `b_revista`, `b_eje`) siguen presentes.
  - El dashboard conserva los filtros de la barra lateral (`f_retorno`,
    `f_vista`, etc.).
  - La barra superior lleva el toggle **Reducir animaciones** (`fm_reducir`).
  - El pie de página aparece una sola vez por sesión.

### Comando

```bash
cd ruta/al/repositorio
python -m pytest dashboard/tests -q
```

Resultado esperado:

```
127 passed in ~26 s
```

## Pruebas manuales que se recomienda hacer

- Chrome escritorio (1400×900): portada, menú circular y dashboard.
- Chrome móvil (390×844): el menú se reorganiza en dos columnas y la barra
  superior se ajusta.
- Activar **Reducir animaciones** y confirmar que desaparecen los barridos y la
  respiración del núcleo.
- Teclado: Tab navega entre tarjetas del menú circular; Enter abre; Esc vuelve
  al menú general; flechas cambian de sección o de ficha.
- Descargas: XLSX, CSV, PNG y ZIP siguen bajando con el filtro aplicado.

## Lo que no se puede probar automáticamente

- La inyección del motor JS se verifica solo en navegador (no en `AppTest`).
- El `prefers-reduced-motion` del sistema se verifica solo con una preferencia
  real del sistema operativo.
- El efecto visual completo (brillos, inclinación 3D, hover de las tarjetas) se
  verifica con captura o en vivo.
