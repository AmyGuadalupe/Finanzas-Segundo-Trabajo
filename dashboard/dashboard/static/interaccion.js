/* =====================================================================
   Motor de interacción del portal (mejora progresiva)
   ---------------------------------------------------------------------
   · Se inyecta una sola vez en el documento de la aplicación (idempotente).
   · Los botones de Streamlit siguen siendo la capa funcional: este script solo
     añade profundidad (inclinación, paralaje, luz), teclado, contadores,
     transición de apertura, foco y avisos accesibles.
   · Respeta prefers-reduced-motion y el interruptor «Reducir animaciones».
   · Sin bucle permanente: el cuadro de animación solo corre mientras hay
     movimiento del cursor y se detiene al estabilizarse.
   ===================================================================== */
(function () {
  'use strict';

  var D = document, R = D.documentElement, W = window;
  if (W.__fmMotor && typeof W.__fmMotor.destruir === 'function') {
    try { W.__fmMotor.destruir(); } catch (e) { /* versión anterior */ }
  }

  var VERSION = '2.0';
  var oyentes = [];          // [objetivo, tipo, función, opciones] para poder desmontar
  var observadores = [];     // MutationObserver / IntersectionObserver
  var temporizadores = [];
  var destruido = false;

  var mqReducir = W.matchMedia ? W.matchMedia('(prefers-reduced-motion: reduce)') : null;
  var mqTactil = W.matchMedia ? W.matchMedia('(pointer: coarse)') : null;

  function $(sel, raiz) { return (raiz || D).querySelector(sel); }
  function $$(sel, raiz) { return Array.prototype.slice.call((raiz || D).querySelectorAll(sel)); }
  function meta() { return D.getElementById('fm-meta'); }
  function reducir() {
    var m = meta();
    return !!((mqReducir && mqReducir.matches) || (m && m.getAttribute('data-reducir') === '1'));
  }
  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }
  function escuchar(obj, tipo, fn, op) { obj.addEventListener(tipo, fn, op); oyentes.push([obj, tipo, fn, op]); }
  function esperar(fn, ms) { var t = setTimeout(fn, ms); temporizadores.push(t); return t; }

  R.classList.add('fm-js');
  if (!R.getAttribute('lang') || R.getAttribute('lang') === 'en') { R.setAttribute('lang', 'es'); }

  /* ------------------------------------------------------------------
     1. Puntero: luz, paralaje, proximidad e inclinación (rAF con inercia)
     ------------------------------------------------------------------ */
  var puntero = { x: 0, y: 0, activo: false, objetivo: null };
  var pendiente = false;
  var rad = { px: 0, py: 0, lx: 50, ly: 44 };
  var paralajes = new WeakMap();
  var inclinado = null;

  var SEL_INCLINAR = '.st-key-radial [class*="st-key-nav_"] button, .st-key-acceso1 button, .st-key-acceso2 button, [class*="st-key-card_"], .fm-inclinar';

  function pedirCuadro() {
    if (!pendiente && !destruido) { pendiente = true; W.requestAnimationFrame(cuadro); }
  }

  function alPuntero(e) {
    if (e.pointerType === 'touch' || reducir()) { return; }
    puntero.x = e.clientX; puntero.y = e.clientY; puntero.activo = true; puntero.objetivo = e.target;
    pedirCuadro();
  }
  function alSalir() { puntero.activo = false; puntero.objetivo = null; pedirCuadro(); }

  function cuadro() {
    pendiente = false;
    if (destruido) { return; }
    var seguir = false;
    if (reducir()) { restablecerTodo(); return; }
    seguir = cuadroRadial() || seguir;
    seguir = cuadroParalaje('.fm-portada') || seguir;
    cuadroInclinacion();
    if (seguir) { pedirCuadro(); }
  }

  function cuadroRadial() {
    var el = $('.st-key-radial');
    if (!el) { return false; }
    var r = el.getBoundingClientRect();
    var ancho = r.width;
    var tarjetas = $$('[class*="st-key-nav_"]', el);
    var lecturas = tarjetas.map(function (t) { var b = t.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; });
    var escritorio = ancho > 480 && !(mqTactil && mqTactil.matches);
    var dentro = escritorio && puntero.activo && puntero.x >= r.left - 70 && puntero.x <= r.right + 70 && puntero.y >= r.top - 70 && puntero.y <= r.bottom + 70;
    var tx = 0, ty = 0, tlx = 50, tly = 44;
    if (dentro) {
      tx = clamp((puntero.x - (r.left + ancho / 2)) / (ancho / 2), -1, 1);
      ty = clamp((puntero.y - (r.top + r.height / 2)) / (r.height / 2), -1, 1);
      tlx = clamp((puntero.x - r.left) / ancho * 100, -8, 108);
      tly = clamp((puntero.y - r.top) / r.height * 100, -8, 108);
    }
    rad.px += (tx - rad.px) * 0.13; rad.py += (ty - rad.py) * 0.13;
    rad.lx += (tlx - rad.lx) * 0.16; rad.ly += (tly - rad.ly) * 0.16;
    var activo = Math.abs(tx - rad.px) > 0.002 || Math.abs(ty - rad.py) > 0.002 || Math.abs(tlx - rad.lx) > 0.05 || Math.abs(tly - rad.ly) > 0.05;
    if (!activo) { rad.px = tx; rad.py = ty; rad.lx = tlx; rad.ly = tly; }
    el.style.setProperty('--px', rad.px.toFixed(3));
    el.style.setProperty('--py', rad.py.toFixed(3));
    el.style.setProperty('--lx', rad.lx.toFixed(2) + '%');
    el.style.setProperty('--ly', rad.ly.toFixed(2) + '%');
    var rango = ancho * 0.26;
    tarjetas.forEach(function (t, i) {
      var objetivo = 0;
      if (dentro) { objetivo = clamp(1 - Math.hypot(puntero.x - lecturas[i][0], puntero.y - lecturas[i][1]) / rango, 0, 1); }
      var actual = typeof t.__prox === 'number' ? t.__prox : 0;
      actual += (objetivo - actual) * 0.18;
      if (Math.abs(objetivo - actual) < 0.004) { actual = objetivo; } else { activo = true; }
      t.__prox = actual;
      t.style.setProperty('--prox', actual.toFixed(3));
    });
    return activo;
  }

  function cuadroParalaje(sel) {
    var el = $(sel);
    if (!el) { return false; }
    var st = paralajes.get(el) || { px: 0, py: 0 };
    var r = el.getBoundingClientRect();
    var dentro = puntero.activo && puntero.x >= r.left && puntero.x <= r.right && puntero.y >= r.top && puntero.y <= r.bottom && !(mqTactil && mqTactil.matches);
    var tx = dentro ? clamp((puntero.x - (r.left + r.width / 2)) / (r.width / 2), -1, 1) : 0;
    var ty = dentro ? clamp((puntero.y - (r.top + r.height / 2)) / (r.height / 2), -1, 1) : 0;
    st.px += (tx - st.px) * 0.1; st.py += (ty - st.py) * 0.1;
    var activo = Math.abs(tx - st.px) > 0.002 || Math.abs(ty - st.py) > 0.002;
    if (!activo) { st.px = tx; st.py = ty; }
    paralajes.set(el, st);
    el.style.setProperty('--px', st.px.toFixed(3));
    el.style.setProperty('--py', st.py.toFixed(3));
    return activo;
  }

  function maximoInclinacion(el) {
    if (el.matches('.st-key-radial button')) { return 9; }
    if (el.matches('.st-key-acceso1 button, .st-key-acceso2 button')) { return 4.5; }
    return 4;
  }
  function soltarInclinacion(el) {
    el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg');
    el.style.removeProperty('--gx'); el.style.removeProperty('--gy');
  }
  function cuadroInclinacion() {
    var t = null;
    if (puntero.activo && puntero.objetivo && puntero.objetivo.closest && !(mqTactil && mqTactil.matches)) { t = puntero.objetivo.closest(SEL_INCLINAR); }
    if (inclinado && inclinado !== t) { soltarInclinacion(inclinado); }
    inclinado = t;
    if (!t) { return; }
    var b = t.getBoundingClientRect();
    if (!b.width || !b.height) { return; }
    var nx = clamp((puntero.x - b.left) / b.width, 0, 1), ny = clamp((puntero.y - b.top) / b.height, 0, 1);
    var m = maximoInclinacion(t);
    t.style.setProperty('--ry', ((nx - 0.5) * 2 * m).toFixed(2) + 'deg');
    t.style.setProperty('--rx', ((0.5 - ny) * 2 * m).toFixed(2) + 'deg');
    t.style.setProperty('--gx', (nx * 100).toFixed(1) + '%');
    t.style.setProperty('--gy', (ny * 100).toFixed(1) + '%');
  }
  function restablecerTodo() {
    var el = $('.st-key-radial');
    if (el) {
      ['--px', '--py'].forEach(function (k) { el.style.setProperty(k, '0'); });
      $$('[class*="st-key-nav_"]', el).forEach(function (t) { t.style.setProperty('--prox', '0'); });
    }
    var p = $('.fm-portada');
    if (p) { p.style.setProperty('--px', '0'); p.style.setProperty('--py', '0'); }
    if (inclinado) { soltarInclinacion(inclinado); inclinado = null; }
  }

  /* ------------------------------------------------------------------
     2. Transición de apertura (cortina circular desde la tarjeta pulsada)
     ------------------------------------------------------------------ */
  var velo = null, veloActivo = false, veloMinimo = 0, veloTemp = 0;
  var SEL_NAVEGA = '.st-key-radial [class*="st-key-nav_"], .st-key-acceso1, .st-key-acceso2, .st-key-tb_inicio, .st-key-tb_s1, .st-key-tb_s2';

  function asegurarVelo() {
    if (velo && velo.isConnected) { return; }
    velo = D.createElement('div');
    velo.className = 'fm-velo';
    velo.setAttribute('aria-hidden', 'true');
    D.body.appendChild(velo);
  }
  function alPulsar(e) {
    if (reducir() || !e.target || !e.target.closest) { return; }
    var b = e.target.closest('button');
    if (!b || b.disabled || !b.closest(SEL_NAVEGA)) { return; }
    asegurarVelo();
    var r = b.getBoundingClientRect();
    velo.style.setProperty('--vx', (r.left + r.width / 2) + 'px');
    velo.style.setProperty('--vy', (r.top + r.height / 2) + 'px');
    velo.classList.remove('off');
    velo.classList.add('on');
    veloActivo = true;
    veloMinimo = Date.now() + 460;
    clearTimeout(veloTemp);
    veloTemp = esperar(cerrarVelo, 1700);   // nunca bloquea más de este tiempo
  }
  function cerrarVelo() {
    if (!veloActivo || !velo) { return; }
    var falta = veloMinimo - Date.now();
    if (falta > 0) { esperar(cerrarVelo, falta + 10); return; }
    velo.classList.add('off');
    esperar(function () {
      if (!velo) { return; }
      velo.classList.add('reinicio');
      velo.classList.remove('on', 'off');
      void velo.offsetWidth;
      velo.classList.remove('reinicio');
      veloActivo = false;
    }, 560);
  }

  /* ------------------------------------------------------------------
     3. Teclado: recorrer las tarjetas, atajos de sección y de ficha
     ------------------------------------------------------------------ */
  function enCampo(t) {
    return !!(t && t.closest && t.closest('input, textarea, select, [contenteditable="true"], [role="slider"], [role="combobox"], [role="listbox"], [role="dialog"], [data-baseweb="popover"], .js-plotly-plot, [data-testid="stDataFrame"]'));
  }
  /* El primer selector que exista decide: si su botón está desactivado no se salta al siguiente
     (p. ej. en el póster 01 la flecha izquierda no debe ir a la sección anterior). */
  function pulsar() {
    for (var i = 0; i < arguments.length; i++) {
      var b = $(arguments[i]);
      if (b) { if (!b.disabled) { b.click(); return true; } return false; }
    }
    return false;
  }
  function tarjetasRadial() { return $$('.st-key-radial [class*="st-key-nav_"] button'); }

  function alTeclear(e) {
    if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) { return; }
    var t = e.target;
    var tarjeta = t && t.closest ? t.closest('.st-key-radial [class*="st-key-nav_"] button') : null;
    var lista, i;
    if (tarjeta) {
      lista = tarjetasRadial(); i = lista.indexOf(tarjeta);
      var k = e.key, destino = null;
      if (k === 'ArrowRight' || k === 'ArrowDown') { destino = lista[(i + 1) % lista.length]; }
      else if (k === 'ArrowLeft' || k === 'ArrowUp') { destino = lista[(i - 1 + lista.length) % lista.length]; }
      else if (k === 'Home') { destino = lista[0]; }
      else if (k === 'End') { destino = lista[lista.length - 1]; }
      else if (/^[1-7]$/.test(k)) { destino = lista[parseInt(k, 10) - 1]; }
      if (destino) { e.preventDefault(); destino.focus(); }
      return;
    }
    if (enCampo(t)) { return; }
    if (e.key === 'Escape') {
      if (pulsar('.st-key-f_volver button', '.st-key-p_menu button')) { e.preventDefault(); }
      return;
    }
    var libre = (D.activeElement === D.body || D.activeElement === R || !D.activeElement);
    if (!libre) { return; }
    if (e.key === 'ArrowLeft') {
      if (pulsar('.st-key-f_ant button', '.st-key-p_ant button')) { e.preventDefault(); }
    } else if (e.key === 'ArrowRight') {
      if (pulsar('.st-key-f_sig button', '.st-key-p_sig button')) { e.preventDefault(); }
    } else if (/^[1-7]$/.test(e.key)) {
      lista = tarjetasRadial();
      if (lista.length) { e.preventDefault(); lista[parseInt(e.key, 10) - 1].focus(); }
    }
  }

  /* ------------------------------------------------------------------
     4. Contadores (cifras que suben una sola vez al aparecer) y revelado
     ------------------------------------------------------------------ */
  var ioContador = null, ioRevelar = null;
  var visto = new WeakSet();

  function fmt(v, dec, sepMiles, sepDec) {
    var s = Math.abs(v).toFixed(dec);
    var partes = s.split('.');
    if (sepMiles) { partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, sepMiles); }
    var out = partes.join(sepDec || '.');
    return (v < 0 && parseFloat(s) !== 0 ? '-' : '') + out;
  }
  function animar(el) {
    if (visto.has(el)) { return; }
    visto.add(el);
    var original = el.textContent;
    if (reducir()) { return; }
    var tramos, partes;
    if (el.hasAttribute('data-fm-count')) {
      var valor = parseFloat(el.getAttribute('data-fm-count'));
      if (!isFinite(valor)) { return; }
      var dec = parseInt(el.getAttribute('data-fm-dec') || '0', 10);
      var sm = el.getAttribute('data-fm-sep') || '';
      var sd = el.getAttribute('data-fm-dsep') || '.';
      tramos = null;
      partes = { texto: function (p) { return fmt(valor * p, dec, sm, sd); } };
    } else {
      var trozos = original.split(/(-?\d+(?:[.,]\d+)?)/);
      if (trozos.length < 3) { return; }
      partes = {
        texto: function (p) {
          return trozos.map(function (tz, k) {
            if (k % 2 === 0) { return tz; }
            var d = (tz.split(/[.,]/)[1] || '').length;
            var coma = tz.indexOf(',') >= 0;
            return fmt(parseFloat(tz.replace(',', '.')) * p, d, '', coma ? ',' : '.');
          }).join('');
        }
      };
    }
    var dur = 1000, t0 = null;
    el.setAttribute('aria-label', original);
    function paso(ts) {
      if (destruido) { return; }
      if (t0 === null) { t0 = ts; }
      var p = clamp((ts - t0) / dur, 0, 1);
      var e = 1 - Math.pow(1 - p, 4);
      el.textContent = p < 1 ? partes.texto(e) : original;
      if (p < 1) { W.requestAnimationFrame(paso); }
    }
    el.textContent = partes.texto(0);
    W.requestAnimationFrame(paso);
  }
  function prepararContadores() {
    if (!('IntersectionObserver' in W)) { return; }
    if (!ioContador) {
      ioContador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (en) { if (en.isIntersecting) { ioContador.unobserve(en.target); animar(en.target); } });
      }, { threshold: 0.4 });
      observadores.push(ioContador);
    }
    $$('[data-fm-count], .fm-card .v').forEach(function (el) {
      if (!visto.has(el) && !el.__fmObs) { el.__fmObs = true; ioContador.observe(el); }
    });
  }
  function prepararRevelado() {
    if (!('IntersectionObserver' in W)) { $$('.fm-rev').forEach(function (e) { e.classList.add('fm-vis'); }); return; }
    if (!ioRevelar) {
      ioRevelar = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('fm-vis'); ioRevelar.unobserve(en.target); } });
      }, { threshold: 0.15 });
      observadores.push(ioRevelar);
    }
    $$('.fm-rev:not(.fm-vis)').forEach(function (el) { if (!el.__fmRev) { el.__fmRev = true; ioRevelar.observe(el); } });
  }

  /* ------------------------------------------------------------------
     5. Accesibilidad: roles, etiquetas, foco tras navegar y aviso en voz
     ------------------------------------------------------------------ */
  var vivo = null, ultimoRun = null;

  function asegurarVivo() {
    if (vivo && vivo.isConnected) { return vivo; }
    vivo = D.createElement('div');
    vivo.id = 'fm-vivo';
    vivo.className = 'fm-solo-sr';
    vivo.setAttribute('role', 'status');
    vivo.setAttribute('aria-live', 'polite');
    vivo.setAttribute('aria-atomic', 'true');
    D.body.appendChild(vivo);
    return vivo;
  }
  function parcharAria() {
    var motor = $('.st-key-fm_motor');
    if (motor && motor.getAttribute('aria-hidden') !== 'true') { motor.setAttribute('aria-hidden', 'true'); }
    var radial = $('.st-key-radial');
    var m = meta();
    var activa = m ? m.getAttribute('data-activa') : '';
    if (radial) {
      if (radial.getAttribute('role') !== 'group') {
        radial.setAttribute('role', 'group');
        radial.setAttribute('aria-label', 'Menú circular de las siete secciones de la investigación');
      }
      var tarjetas = $$('[class*="st-key-nav_"]', radial);
      tarjetas.forEach(function (t, i) {
        var b = $('button', t);
        if (!b) { return; }
        var clave = (t.className.match(/st-key-nav_([a-z]+)/) || [])[1] || '';
        var nombre = (b.textContent || '').trim();
        var etiqueta = 'Sección ' + (i + 1) + ' de ' + tarjetas.length + ': ' + nombre;
        if (b.getAttribute('aria-label') !== etiqueta) { b.setAttribute('aria-label', etiqueta); }
        if (clave && clave === activa) { b.setAttribute('aria-current', 'true'); } else { b.removeAttribute('aria-current'); }
      });
    }
    $$('.st-key-topbar button[data-testid="stBaseButton-primary"]').forEach(function (b) { b.setAttribute('aria-current', 'page'); });
    $$('.st-key-topbar button[data-testid="stBaseButton-secondary"]').forEach(function (b) { b.removeAttribute('aria-current'); });
  }
  function irArriba() {
    var contenedores = [$('[data-testid="stMain"]'), $('section.main'), D.scrollingElement];
    contenedores.forEach(function (c) { if (c && c.scrollTo) { try { c.scrollTo({ top: 0, behavior: 'auto' }); } catch (e) { c.scrollTop = 0; } } });
  }
  function tratarNavegacion() {
    var m = meta();
    if (!m) { return; }
    var run = m.getAttribute('data-run');
    if (run === ultimoRun) { return; }
    ultimoRun = run;
    if (m.getAttribute('data-foco') !== '1') { return; }
    irArriba();
    var destino = $('[data-fm-foco]');
    if (destino) { try { destino.focus({ preventScroll: true }); } catch (e) { destino.focus(); } }
    var texto = m.getAttribute('data-anuncio') || '';
    var v = asegurarVivo();
    v.textContent = '';
    esperar(function () { v.textContent = texto; }, 80);
  }

  /* ------------------------------------------------------------------
     6. Fin de cada ejecución de Streamlit y observación del DOM
     ------------------------------------------------------------------ */
  var temporizadorEscaneo = 0;
  function escanear() {
    if (destruido) { return; }
    parcharAria();
    prepararContadores();
    prepararRevelado();
  }
  function programarEscaneo() {
    clearTimeout(temporizadorEscaneo);
    temporizadorEscaneo = setTimeout(escanear, 90);
  }
  function finDeEjecucion() {
    escanear();
    tratarNavegacion();
    cerrarVelo();
  }
  function vigilarEstado() {
    var app = $('[data-testid="stApp"]');
    if (!app) { esperar(vigilarEstado, 250); return; }
    var mo = new MutationObserver(function (lista) {
      for (var i = 0; i < lista.length; i++) {
        if (lista[i].type === 'attributes' && lista[i].attributeName === 'data-test-script-state') {
          if (app.getAttribute('data-test-script-state') === 'notRunning') { esperar(finDeEjecucion, 70); }
          return;
        }
      }
    });
    mo.observe(app, { attributes: true, attributeFilter: ['data-test-script-state'] });
    observadores.push(mo);
    var mo2 = new MutationObserver(programarEscaneo);
    mo2.observe(app, { childList: true, subtree: true });
    observadores.push(mo2);
    if (app.getAttribute('data-test-script-state') === 'notRunning') { esperar(finDeEjecucion, 120); }
  }

  /* ------------------------------------------------------------------
     Arranque y desmontaje
     ------------------------------------------------------------------ */
  escuchar(D, 'pointermove', alPuntero, { passive: true });
  escuchar(D, 'pointerdown', function (e) { if (e.pointerType === 'touch') { puntero.activo = false; } }, { passive: true });
  escuchar(R, 'mouseleave', alSalir, { passive: true });
  escuchar(W, 'blur', alSalir, { passive: true });
  escuchar(D, 'click', alPulsar, true);
  escuchar(D, 'keydown', alTeclear, false);
  if (mqReducir && mqReducir.addEventListener) { escuchar(mqReducir, 'change', restablecerTodo); }
  vigilarEstado();
  escanear();

  function destruir() {
    destruido = true;
    oyentes.forEach(function (o) { try { o[0].removeEventListener(o[1], o[2], o[3]); } catch (e) { /* ya retirado */ } });
    observadores.forEach(function (o) { try { o.disconnect(); } catch (e) { /* ya retirado */ } });
    temporizadores.forEach(clearTimeout);
    if (velo && velo.parentNode) { velo.parentNode.removeChild(velo); }
    if (vivo && vivo.parentNode) { vivo.parentNode.removeChild(vivo); }
    R.classList.remove('fm-js');
    restablecerTodo();
    W.__fmMotor = null;
  }

  W.__fmMotor = { version: VERSION, escanear: escanear, destruir: destruir, reducir: reducir };
})();
