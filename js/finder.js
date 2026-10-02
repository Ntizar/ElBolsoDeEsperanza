/* finder.js v4 — buscador "¿qué bolso te tocó el día que naciste?" */
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
    var meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
    return Number(p[2]) + " de " + meses[Number(p[1]) - 1];
  }

  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }

  function html_card(dia) {
    var rutaBase = location.pathname.indexOf("/buscar/") >= 0 ? "../" : "";
    return "" +
      '<div class="finder-card">' +
      '  <img src="' + rutaBase + dia.imagen + '" alt="' + dia.titulo + '">' +
      '  <div class="fc-info">' +
      '    <span class="fc-fecha">' + nombre_fecha(dia.fecha) + " · día " + dia.n + " del año</span>" +
      '    <h3>' + dia.titulo + "</h3>" +
      '    <div class="fc-datos">' +
      "      <span>Precio <b>" + dia.precio + "</b></span>" +
      "      <span>Nota <b>" + String(dia.rating).replace(".", ",") + "★</b></span>" +
      "      <span><b>" + fmt(dia.n_val) + "</b> valoraciones</span>" +
      "    </div>" +
      '    <a class="btn vino" href="' + rutaBase + "dia/" + dia.n + '/">Ver el bolso del día →</a>' +
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
        '<p class="finder-vacio">Aún no tenemos el bolso de ese día — el diario sigue creciendo.</p>';
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
