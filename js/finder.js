/* finder.js v6 — buscador "¿qué bolso te tocó el día que naciste?" (anatomía de galería) */
(function () {
  "use strict";

  var datos = null;
  var input = document.getElementById("finder-fecha");
  var boton = document.getElementById("finder-btn");
  var random = document.getElementById("finder-random");
  var salida = document.getElementById("finder-resultado");
  if (!input || !boton || !salida) return;

  function cargar(cb) {
    if (datos) return cb();
    if (window.FINDER_DATA) { datos = window.FINDER_DATA; return cb(); }
    datos = { dias: [] };
    cb();
  }

  function dia_de(fechaISO) {
    var parts = fechaISO.split("-");
    var d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    var inicio = new Date(Number(parts[0]), 0, 1);
    return Math.floor((d - inicio) / 86400000) + 1;
  }

  function nombre_fecha(fechaISO) {
    var p = fechaISO.split("-");
    var mes = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
    return Number(p[2]) + " de " + mes[Number(p[1]) - 1];
  }

  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }

  function html_card(via) {
    var rutaBase = location.pathname.indexOf("/buscar/") >= 0 ? "../" : "";
    return "" +
      '<div class="finder-card">' +
      '  <div class="fc-foto"><img src="' + rutaBase + via.imagen + '" alt="' + via.titulo + '"></div>' +
      '  <div class="fc-info">' +
      '    <span class="fc-fecha">' + nombre_fecha(via.fecha) + " · carta Nº " + String(via.n).padStart(3, "0") + "</span>" +
      '    <h3>' + via.titulo + "</h3>" +
      '    <span class="fc-meta">' + (via.tipo || "Bolso") + " · Nota <b>" + String(via.rating).replace(".", ",") + "★</b> · " + fmt(via.n_val) + " valoraciones</span>" +
      '    <span class="fc-precio">' + via.precio + " €</span>" +
      '    <a class="btn negro" href="' + rutaBase + "dia/" + via.n + '/">Ver la carta del día →</a>' +
      "  </div>" +
      "</div>";
  }

  function buscar(fechaISO) {
    if (!fechaISO) { salida.innerHTML = '<p class="finder-vacio">Elige una fecha para empezar.</p>'; return; }
    cargar(function () {
      var n = dia_de(fechaISO);
      var dia = null;
      for (var i = 0; i < datos.dias.length; i++) {
        if (datos.dias[i].n === n) { dia = datos.dias[i]; break; }
      }
      salida.innerHTML = dia ? html_card(dia) :
        '<p class="finder-vacio">Elige una fecha dentro de 2026 para ver su carta.</p>';
    });
  }

  boton.addEventListener("click", function () { buscar(input.value); });
  if (random) {
    random.addEventListener("click", function () {
      var hoy = new Date();
      input.value = hoy.toISOString().slice(0, 10);
      buscar(input.value);
    });
  }
  input.addEventListener("change", function () { buscar(input.value); });
})();
