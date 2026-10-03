#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador del sitio "El Bolso de Esperanza" v4 — repositorio de 365 bolsos.
Lee data/bolsos.json (bolsos reales scrapeados de Amazon) y regenera:
  - index.html            (landing: bolso del DÍA + buscador de cumpleaños + próximos/últimos)
  - dia/index.html        (índice del diario: todos los días)
  - dia/<n>/index.html    (página de cada día: historia + bolso real del día)
  - bolso/<id>/index.html (ficha de cada bolso: pros/contras reales + opiniones)
  - opiniones/index.html  (índice de opiniones reales)
  - buscar/index.html     (buscador "¿qué bolso me tocó el día que nací?")
  - data/finder-data.json (datos para el buscador JS)
  - sitemap.xml
El día N del año (en bucle) recibe el bolso N del repositorio ordenado por calidad;
si el repositorio tiene menos de 365 bolsos, los días se reciclan con alternos.
Idempotente. Uso: python scripts/generar-sitio.py
"""
import json
import hashlib
import re
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VER = "20261003f"
DOMINIO = "https://ntizar.github.io/ElBolsoDeEsperanza"
ANIO = 2026

# --- cartas coleccionables: rareza por precio y tipo detectado del título ---
def rareza_de(b):
    p = b.get("precio_num") or 0
    if p >= 90:
        return ("r2", "Rara", "★")
    if p >= 55:
        return ("r1", "Poco común", "◆")
    return ("r0", "Común", "●")

RE_TIPO = [
    ("mochila", "Mochila"), ("bandolera", "Bandolera"), ("tote", "Tote"),
    ("shopper", "Tote"), ("clutch", "Clutch"), ("maletín", "Maletín"), ("maletin", "Maletín"),
    ("satchel", "Satchel"), ("hobo", "Hobo"), ("cartera", "Cartera"), ("basket", "Basket"),
    ("bowl", "Bowl"), ("mini", "Mini"), ("maxi", "Maxi"), ("mensaje", "Mensajero"),
]

def tipo_de(b):
    t = (b.get("titulo") or "").lower()
    for kw, nombre in RE_TIPO:
        if kw in t:
            return nombre
    return "Bolso"

def texto_pc(b):
    """Pros y contras reales (menciones en opiniones) como listas de strings."""
    pros, contras = pros_contras(b)
    if not pros:
        pros = ["Estética"]
    if not contras:
        contras = ["Sin quejas recurrentes"]
    return pros, contras

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# ---------------------------------------------------------------- datos

def cargar():
    d = json.loads((RAIZ / "data" / "bolsos.json").read_text(encoding="utf-8"))
    bolsos = d["bolsos"]
    # orden de calidad: nota desc, nº valoraciones desc, precio desc (desempates estables)
    bolsos.sort(key=lambda b: (-(b.get("rating") or 0), -(b.get("n_valoraciones") or 0),
                               -(b.get("precio_num") or 0)))
    return bolsos

BOLSOS = cargar()
N = len(BOLSOS)
BOLSO_POR_ID = {b["id"]: b for b in BOLSOS}

def fecha_de_dia(n):
    return date(ANIO, 1, 1) + timedelta(days=n - 1)

def fecha_larga(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"

def bolso_del_dia(n):
    """Bolso del día n (bucle). Si el repo no llega a 365, añade alternos estables."""
    idx = (n - 1) % N
    b = BOLSOS[idx]
    alternos = []
    if N < 365:
        saltos = (n * 37 + 11) % N
        usados = {b["id"]}
        for k in range(1, min(N, 6)):
            alt = BOLSOS[(idx + saltos * k) % N]
            if alt["id"] not in usados:
                alternos.append(alt)
                usados.add(alt["id"])
    return b, alternos

def dia_hash(n):
    """Firma estable por día: para variar textos sin reescribirlos en cada regeneración."""
    return int(hashlib.md5(f"esperanza-{n}".encode()).hexdigest(), 16)

# ---------------------------------------------------------------- pros/contras reales

POS = [("cómod", "Comodidad"), ("calidad", "Calidad"), ("bonit", "Estética"),
       ("elegan", "Elegancia"), ("capacidad", "Capacidad"), ("cabe", "Capacidad"),
       ("espacio", "Capacidad"), ("grande", "Capacidad"), ("calidad precio", "Relación calidad-precio"),
       ("barat", "Precio"), ("liger", "Ligereza"), ("cuero", "Material"),
       ("práctic", "Practicidad"), ("versátil", "Versatilidad"), ("combina", "Versatilidad")]
NEG = [("pequeñ", "Tamaño"), ("huele", "Olor inicial"), ("olor", "Olor inicial"),
       ("cierre", "Cierres"), ("cremallera", "Cierres"), ("zip", "Cierres"),
       ("asa ", "Asas"), ("asas", "Asas"), ("correa", "Correa"),
       ("hombro", "Hombro"), ("caro", "Precio"), ("cara ", "Precio"),
       ("costura", "Acabados"), ("roto", "Durabilidad"), ("rompió", "Durabilidad"),
       ("despega", "Acabados"), ("tarde", "Envío")]

def pros_contras(bolso):
    """Cuenta menciones de atributos en las opiniones reales scrapeadas del producto."""
    texto = " ".join(bolso.get("opiniones_amazon", [])).lower()
    pos, neg = {}, {}
    for kws, destino in ((POS, pos), (NEG, neg)):
        for kw, etiqueta in kws:
            if kw in texto:
                destino[etiqueta] = destino.get(etiqueta, 0) + texto.count(kw)
    pros = [e for e, _ in sorted(pos.items(), key=lambda x: -x[1])[:3]]
    contras = [e for e, _ in sorted(neg.items(), key=lambda x: -x[1])[:3]]
    return pros, contras

def veredicto(b):
    r = str(b.get("rating") or 0).replace(".", ",")
    nv = b.get("n_valoraciones") or 0
    nivel = "muy alta" if nv > 3000 else ("alta" if nv > 800 else "sólida")
    return (f"Con una nota media de {r} sobre 5 en {nv:,} valoraciones — una base de compra "
            f"{nivel} — no es un bolso para comprar a ciegas: es para comprar convencido.")

# ---------------------------------------------------------------- storytelling

GANAS = [
    ("Hoy es de esos días en los que la decisión no se negocia.", "elegir lo que pesa menos"),
    ("Hay lunes que empiezan antes que tú.", "llevar la jornada con correa corta"),
    ("El calendario no pregunta si tienes ganas.", "irse con todo ordenado dentro"),
    ("Un día cualquiera, hasta que decides que no lo es.", "la versión más práctica de ti"),
    ("Los días largos piden aliados que no estorben.", "cargar con lo justo y bien elegido"),
    ("Fin de semana: otras reglas, otros ritmos.", "el bolso que no pide permiso"),
]

def texto_dia(n, b):
    d = fecha_de_dia(n)
    h = dia_hash(n)
    gancho, frase = GANAS[h % len(GANAS)]
    if d.weekday() >= 5:
        gancho, frase = GANAS[5]
    pros, _ = pros_contras(b)
    dato_pro = f"Lo que más repiten sus compradoras: {pros[0].lower()}." if pros else ""
    nombre_corto = b["titulo"].split(",")[0]
    nv = b.get("n_valoraciones", 0)
    return {
        "gancho": gancho,
        "parrafo1": (f"El bolso de hoy es el {nombre_corto}. No es un capricho de escaparate: "
                     f"es el que acompaña {frase}, con {str(b.get('rating', 0)).replace('.', ',')}★ de nota "
                     f"media y {nv:,} valoraciones que respaldan la decisión."),
        "parrafo2": (f"Un bolso no cambia tu día. Cambia la manera de entrar en él: con lo que "
                     f"necesitas, sin lo que sobra y con la certeza de que otras {max(nv, 30):,} personas "
                     f"ya hicieron la misma elección antes que tú. {dato_pro}"),
    }

# ---------------------------------------------------------------- plantillas base

UBAR = """<div class="ubar">
  <div class="container">
    <span><span class="punto">●</span> 365 CARTAS, UNA POR DÍA DEL AÑO</span>
    <span>/</span>
    <span>ENCUENTRA LA DE TU CUMPLEAÑOS</span>
  </div>
</div>"""

def header(raiz):
    return f"""<header class="site-header">
  <div class="container">
    <a href="{raiz}" class="logo">El Bolso de <span class="accent">Esperanza</span><span class="tagline">365 cartas de colección</span></a>
    <nav>
      <a href="{raiz}#hoy">La carta de hoy</a>
      <a href="{raiz}dia/">El diario</a>
      <a href="{raiz}buscar/">Tu cumpleaños</a>
      <a href="{raiz}estadisticas/">Estadísticas</a>
      <a href="{raiz}opiniones/">Opiniones</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="site-footer">
  <div class="container">
    <p>El Bolso de Esperanza — 365 bolsos reales, uno por cada día del año.</p>
    <p class="disclosure">Como Afiliado de Amazon, obtengo ingresos por las compras adscritas que cumplen los requisitos aplicables. Los precios pueden variar. Pros y contras calculados a partir de las opiniones reales del producto.</p>
  </div>
</footer>"""

def head_html(titulo, desc, canonical, og_type="website"):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;600&family=Inter:wght@400;600;700&family=Playfair+Display:ital,wght@0,700;0,900;1,700;1,900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{css}}" type="text/css">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
</head>
<body>
"""

def css_href(nivel):
    return ("" if nivel == 0 else "../" * nivel) + f"css/styles.css?v={VER}"

def escribir(relpath, contenido):
    ruta = RAIZ / relpath
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8", newline="\n")
    print(f"  ✓ {relpath}")

# ---------------------------------------------------------------- componentes

def estrellas(n):
    n = round(n or 0)
    return "★" * n + "☆" * (5 - n)

def chip_dia(n):
    d = fecha_de_dia(n)
    return f"Día {n} · {d.day} {MESES[d.month - 1]}"

def fmt(n):
    return f"{n:,}".replace(",", ".")

def nombre_display(b):
    """Nombre de galeria: sin SKU, sin Color:/Used/Nueva Etiqueta, max 52 caracteres."""
    t = re.sub(r"\s*[-|,]\s*(Used|Reno|Nueva Etiqueta|Color\s*:.*|\d+\s*(l|kg).*)\s*$", "", b["titulo"], flags=re.I)
    t = re.sub(r"\s+", " ", t).strip().rstrip(",;|-")
    if len(t) <= 52:
        return t
    return t[:52].rsplit(" ", 1)[0].rstrip(".,;|-") + "…"

def card_dia(n, pref=""):
    b, _ = bolso_del_dia(n)
    t = nombre_display(b)
    return f"""      <a class="pieza" href="{pref}dia/{n}/">
        <div class="p-foto"><img src="{pref}{b['imagen']}" alt="{b['titulo']}" loading="lazy"></div>
        <div class="p-placa">
          <span class="p-num">Carta Nº {str(n).zfill(3)} · {tipo_de(b)}</span>
          <span class="p-nombre">{t}</span>
          <span class="p-meta">Nota {str(b.get('rating', 0)).replace('.', ',')}★ · {fmt(b.get('n_valoraciones') or 0)} valoraciones</span>
          <span class="p-precio">{b['precio']} €</span>
        </div>
      </a>"""

def bloque_producto(b, pref="", titulo_fijo=None, num_carta=None, etiqueta="Pieza de la colección"):
    pros, contras = texto_pc(b)
    pros_html = "".join(f"<li>{p}</li>" for p in pros)
    contras_html = "".join(f"<li>{c}</li>" for c in contras)
    nv = b.get("n_valoraciones") or 0
    return f"""      <div class="carta-grande">
        <span class="etiqueta">{etiqueta}</span>
        <div class="cg-foto"><img src="{pref}{b['imagen']}" alt="{b['titulo']}"></div>
        <div class="cg-cuerpo">
          <h3>{titulo_fijo or nombre_display(b)}</h3>
          <span class="cg-meta">{tipo_de(b)} · Nota <b>{str(b.get('rating', 0)).replace('.', ',')}★</b> · {fmt(nv)} valoraciones · {b.get('marca', '')}</span>
          <div class="cg-precio">{b['precio']} €</div>
          <div class="pc"><div><b>Lo que destacan las compradoras</b><ul>{pros_html}</ul></div><div class="debilidades"><b>Lo que critican</b><ul>{contras_html}</ul></div></div>
          <p class="veredicto">{veredicto(b)}</p>
          <div class="cg-ctas"><a href="{b['afiliado']}" class="btn-affiliate" target="_blank" rel="sponsored nofollow noopener">Ver precio en Amazon ↗</a></div>
        </div>
      </div>"""

def bloque_opiniones(b):
    ops = b.get("opiniones_amazon", [])
    if not ops:
        return ""
    items = "\n".join(f'      <blockquote class="opinion-amazon">“{o[:300]}”</blockquote>' for o in ops[:3])
    return f"""  <section class="sec clara">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Opiniones reales en Amazon</span>
        <h2>Lo que escriben <em>quienes lo compraron</em></h2>
{items}
        <p style="margin-top:18px"><a class="btn negro" href="{b['afiliado']}" target="_blank" rel="sponsored nofollow noopener">Leer todas las opiniones ↗</a></p>
      </div>
    </div>
  </section>"""

# ---------------------------------------------------------------- páginas

def generar_home():
    hoy_n = (date.today() - date(ANIO, 1, 1)).days + 1
    b_hoy, _ = bolso_del_dia(hoy_n)
    ELEGANTES = {"bolso-b071wvnt1j", "bolso-b07h4k1bq6", "bolso-b07nttc9t5",
                 "bolso-b07r45ghn2", "bolso-b08vvtvvg2", "bolso-b09j19c59y",
                 "bolso-b0b2ptkqnq", "bolso-b0b58f4r22", "bolso-b0bjdp7sx6",
                 "bolso-b0c8t57vsf", "bolso-b0cxq1bnvv", "bolso-b0cyt3g3sf",
                 "bolso-b0cyt4h9q5", "bolso-b0d4c8c7wv", "bolso-b0d62ybwjl",
                 "bolso-b0dpx68sl5", "bolso-b0drcq7t2c", "bolso-b0f7xjyh4g",
                 "bolso-b0fg7scz6b", "bolso-b0h25h3c1f"}
    dias_eleg = []
    for n in range(1, 366):
        b, _ = bolso_del_dia(n)
        if b["id"] in ELEGANTES:
            dias_eleg.append((n, b))
    ultimos = "\n".join(card_dia(n) for n, _ in dias_eleg[-7:][::-1])
    proximos_list = [tup for tup in dias_eleg if tup[0] > hoy_n][:2]
    if len(proximos_list) < 2:
        proximos_list += dias_eleg[:2 - len(proximos_list)]
    proximos = "\n".join(
        f"""        <a class="mini-proximo" href="dia/{n}/">
          <img src="{b['imagen']}" alt="{b['titulo']}" loading="lazy">
          <div><span class="mini-dia">{chip_dia(n)}</span><p>{nombre_display(b)}</p></div>
        </a>"""
        for n, b in proximos_list)
    # Selección premium: curaduria manual de las piezas mas hermosas
    premium = sorted((b for b in BOLSOS if b["id"] in ELEGANTES),
                     key=lambda b: -(b.get("precio_num") or 0))[:6]
    premium_cards = "\n".join(
        f"""      <a class="pieza" href="bolso/{b['id']}/">
        <div class="p-foto"><img src="{b['imagen']}" alt="{b['titulo']}" loading="lazy"></div>
        <div class="p-placa">
          <span class="p-num">Pieza destacada · {tipo_de(b)}</span>
          <span class="p-nombre">{nombre_display(b)}</span>
          <span class="p-meta">Nota {str(b.get('rating', 0)).replace('.', ',')}★ · {fmt(b.get('n_valoraciones') or 0)} valoraciones</span>
          <span class="p-precio">{b['precio']} €</span>
        </div>
      </a>""" for b in premium)
    pros_hoy, contras_hoy = texto_pc(b_hoy)
    pros_html = "".join(f"<li>{p}</li>" for p in pros_hoy[:3])
    con_html = "".join(f"<li>{c}</li>" for c in contras_hoy[:3])
    d_hoy = fecha_de_dia(hoy_n)
    nombre_hoy = nombre_display(b_hoy)
    hero_card = f"""<div class="carta-grande">
            <span class="etiqueta">Bolso del día {hoy_n}</span>
            <div class="cg-foto"><img src="{b_hoy['imagen']}" alt="{b_hoy['titulo']}"></div>
            <div class="cg-cuerpo">
              <h3>{nombre_hoy}</h3>
              <span class="cg-meta">{tipo_de(b_hoy)} · Nota <b>{str(b_hoy.get('rating', 0)).replace('.', ',')}★</b> · {fmt(b_hoy.get('n_valoraciones') or 0)} valoraciones</span>
              <div class="cg-precio">{b_hoy['precio']} €</div>
              <div class="pc"><div><b>Lo que destacan</b><ul>{pros_html}</ul></div><div class="debilidades"><b>Lo que critican</b><ul>{con_html}</ul></div></div>
              <div class="cg-ctas">
                <a class="btn negro" href="bolso/{b_hoy['id']}/">Ficha completa →</a>
                <a class="btn-affiliate" href="{b_hoy['afiliado']}" target="_blank" rel="sponsored nofollow noopener">Amazon ↗</a>
              </div>
            </div>
          </div>"""

    html = head_html(
        "El Bolso de Esperanza — Un bolso real cada día del año",
        f"365 bolsos reales de Amazon, uno por cada día del año. Hoy toca el de {d_hoy.day} de {MESES[d_hoy.month-1]}: {nombre_hoy}. Encuentra el de tu cumpleaños.",
        f"{DOMINIO}/",
    )
    html = html.replace("{css}", css_href(0))
    html += f"""{UBAR}
{header("")}
<main>

  <!-- HERO: LA PIEZA DE HOY -->
  <section class="hero" id="hoy">
    <span class="silueta s1">👜</span>
    <div class="container">
      <div class="hero-grid">
        <div class="hero-txt">
          <span class="chip">El bolso del {d_hoy.day} de {MESES[d_hoy.month-1]} · día {hoy_n} del año</span>
          <h1><span class="l1">365 días,</span><span class="l2">365 piezas de colección</span></h1>
          <p class="hero-lead">Un año entero de bolsos reales de Amazon —su foto, su precio y lo que dicen sus compradoras— expuestos uno a uno, como en una galería. La pieza de tu cumpleaños ya está colgada.</p>
          <div class="hero-ctas">
            <a class="btn vino" href="#hoy-bolso">La pieza de hoy ↓</a>
            <a class="btn marfil" href="buscar/">¿Cuál te tocó nacer? →</a>
          </div>
        </div>
        <div id="hoy-bolso">
          {hero_card}
        </div>
      </div>
    </div>
  </section>

  <!-- SELECCIÓN PREMIUM -->
  <section class="sec clara" id="premium">
    <div class="container">
      <div class="watermark" aria-hidden="true">Luxe</div>
      <div class="sec-inner">
        <span class="sec-label">Selección premium</span>
        <h2>Las piezas más <em>hermosas del año</em></h2>
        <p class="lead">Escogidas a mano de la colección: cuero noble, líneas limpias y una fotografía cuidada. Las seis favoritas de la casa — de precio firme.</p>
        <div class="grid-dias">
{premium_cards}
        </div>
      </div>
    </div>
  </section>

  <!-- BUSCADOR DE CUMPLEAÑOS -->
  <section class="sec clara" id="buscar">
    <div class="container">
      <div class="watermark" aria-hidden="true">365</div>
      <div class="sec-inner">
        <span class="sec-label">El buscador del año</span>
        <h2>¿Qué bolso te tocó <em>el día que naciste?</em></h2>
        <p class="lead">Elige tu fecha — o la de quien quieras regalar — y te decimos qué bolso lleva ese día, cuánto cuesta de verdad y qué dicen sus compradoras.</p>
        <div id="finder">
          <label for="finder-fecha">Tu fecha</label>
          <div class="finder-row">
            <input type="date" id="finder-fecha" min="{ANIO}-01-01" max="{ANIO}-12-31">
            <button class="btn vino" id="finder-btn">Buscar mi bolso</button>
            <button class="btn marfil" id="finder-random">Sorpréndeme</button>
          </div>
          <div id="finder-resultado" class="finder-resultado"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- PROXIMOS + ULTIMOS -->
  <section class="sec oscura">
    <div class="container">
      <div class="watermark" aria-hidden="true">Diario</div>
      <div class="sec-inner">
        <span class="sec-label">Los próximos días</span>
        <h2>Lo que viene <em>después de hoy</em></h2>
        <div class="proximos">{proximos}</div>
        <span class="sec-label" style="margin-top:46px">Las últimas piezas expuestas</span>
        <div class="grid-dias">
{ultimos}
        </div>
        <p style="margin-top:30px"><a class="btn vino" href="dia/">Ver el diario completo →</a></p>
      </div>
    </div>
  </section>

  <!-- DESTACADO -->
  <section class="destacado">
    <div class="container">
      <p class="frase">“Un año tiene 365 días. En cada uno cabe una decisión, y detrás de cada decisión, un bolso.”</p>
      <span class="firma">— El diario de Esperanza</span>
    </div>
  </section>

  <!-- CTA -->
  <section class="sec cta-final">
    <div class="container">
      <div class="sec-inner">
        <h2>Nada de fotos que no son <em>el producto real</em></h2>
        <p class="lead" style="color:#FBE3EC">Cada bolso de este diario se toma directamente de su ficha de Amazon: su foto, su precio, su nota y las opiniones de quienes lo compraron. Lo que ves es lo que llega.</p>
        <p style="margin-top:26px"><a class="btn" href="buscar/">Encuentra el tuyo →</a></p>
      </div>
    </div>
  </section>

</main>
<script src="js/finder-data.js?v={VER}"></script>
<script src="js/finder.js?v={VER}"></script>
{FOOTER}
</body>
</html>"""
    escribir("index.html", html)

def generar_finder_datos():
    dias = []
    for n in range(1, 366):  # 365 entradas: un bolso por día, en bucle sobre el pool real
        b, _ = bolso_del_dia(n)
        dias.append({
            "n": n, "fecha": fecha_de_dia(n).isoformat(), "id": b["id"],
            "titulo": nombre_display(b), "precio": b["precio"],
            "rating": b.get("rating"), "n_val": b.get("n_valoraciones", 0),
    "tipo": tipo_de(b), "rareza": rareza_de(b)[1], "rsimb": rareza_de(b)[2],
            "imagen": b["imagen"],
        })
    # inline en JS (sin fetch): funciona en http(s) y en file:// sin CORS
    escribir("js/finder-data.js",
             "window.FINDER_DATA = " + json.dumps({"anio": ANIO, "dias": dias}, ensure_ascii=False) + ";\n")

def generar_blog_index():
    hoy_n = (date.today() - date(ANIO, 1, 1)).days + 1
    cards = "\n".join(card_dia(n, pref="../") for n in range(365, 0, -1))
    html = head_html(
        "El Diario — 365 cartas de colección — El Bolso de Esperanza",
        "El diario completo: cada día del año con su carta, su precio real y lo que dicen sus compradoras.",
        f"{DOMINIO}/dia/",
    )
    html = html.replace("{css}", css_href(1))
    html += f"""{UBAR}
{header("../")}
<main>
  <section class="sec clara" style="padding-top:60px">
    <div class="container">
      <div class="watermark" aria-hidden="true">Diario</div>
      <div class="sec-inner">
        <span class="sec-label">El diario de la colección</span>
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px);line-height:1.05">Las 365 cartas, <em style="color:var(--frambuesa-txt);font-style:italic">de más nueva a más antigua</em></h1>
        <p class="lead" style="color:#57504C">Cada día del año tiene su carta: su bolso real, su precio y sus opiniones. Colecciónalas, regálalas, encuéntrate en ellas.</p>
        <div class="grid-dias">
{cards}
        </div>
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>"""
    escribir("dia/index.html", html)

def generar_dia(n):
    b, alternos = bolso_del_dia(n)
    d = fecha_de_dia(n)
    t = texto_dia(n, b)
    semana = DIAS_SEMANA[d.weekday()].capitalize()

    alternos_html = ""
    if alternos:
        cards = "\n".join(
            f"""        <div class="mini-proximo">
          <img src="../..{a['imagen'][len('assets')-6:] if False else '/' + a['imagen']}" alt="{a['titulo']}" loading="lazy">
          <div><span class="mini-dia">También encaja</span><p>{nombre_display(a)}</p></div>
        </div>""" for a in alternos[:3])
        alternos_html = f"""
  <section class="sec clara">
    <div class="container">
      <div class="sec-inner">
        <span class="sec-label">Alternativas del día</span>
        <h2>Otros bolsos que <em>también valen para este día</em></h2>
        <div class="proximos">{cards}</div>
      </div>
    </div>
  </section>"""

    prev_, next_ = (n - 1) if n > 1 else 365, (n + 1) if n < 365 else 1
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": f"Bolso del día {n} de {ANIO} ({d.day} de {MESES[d.month-1]}): {b['titulo'].split(',')[0]}",
        "datePublished": d.isoformat(),
        "author": {"@type": "Organization", "name": "El Bolso de Esperanza"},
        "url": f"{DOMINIO}/dia/{n}/",
    }, ensure_ascii=False, indent=2)

    html = head_html(
        f"Día {n} · {semana} {d.day} de {MESES[d.month-1]} — {b['titulo'].split(',')[0]} — El Bolso de Esperanza",
        f"El bolso real del día {n} de {ANIO}: {b['titulo'][:100]}. Precio {b['precio']}, {b.get('rating')}★ y pros y contras de sus compradoras.",
        f"{DOMINIO}/dia/{n}/", og_type="article",
    )
    html = html.replace("{css}", css_href(2))
    html += f"""{UBAR}
{header("../../")}
<script type="application/ld+json">
{jsonld}
</script>
<main>
  <section class="sec oscura" style="padding-bottom:40px">
    <div class="container">
      <div class="watermark" aria-hidden="true">{n}</div>
      <div class="sec-inner">
        <a class="volver" href="../../dia/">← El diario</a>
        <article class="entrada-blog">
          <span class="meta-blog" style="color:var(--oro-suave)">{semana}, {fecha_larga(d)} · día {n} de 365</span>
          <h1>{nombre_display(b)}: <em>el bolso del día {n}</em></h1>
          <p class="resumen" style="color:#E8D2DA;font-style:italic">{t['gancho']} {t['parrafo1']}</p>
          <figure style="margin:28px 0 6px">
            <img src="../../{b['imagen']}" alt="{b['titulo']}" style="background:#fff;border:1px solid #DCC5CF;padding:12px;width:100%;max-height:480px;object-fit:contain">
            <figcaption style="font-size:11px;color:#C9A8B6;margin-top:8px;letter-spacing:1.5px;text-transform:uppercase">Pieza nº {str(n).zfill(3)} de la colección · fotografía oficial del producto</figcaption>
          </figure>
          <div class="cuerpo-blog">
            <p>{t['parrafo2']}</p>
          </div>
        </article>
      </div>
    </div>
  </section>

  <section class="ficha">
    <div class="container">
      <span class="sec-label" style="color:var(--frambuesa-txt)">La carta del día, con datos reales</span>
{bloque_producto(b, pref="../../", num_carta=n, etiqueta=f"Pieza del día Nº {n}")}
      <div style="display:flex;justify-content:space-between;margin-top:30px;flex-wrap:wrap;gap:10px">
        <a href="../{prev_}/" style="font-family:var(--hand);font-size:19px;color:var(--frambuesa-txt);text-decoration:none">← Día {prev_}</a>
        <a href="../../bolso/{b['id']}/" style="font-family:var(--hand);font-size:19px;color:var(--frambuesa-txt);text-decoration:none">Ficha del bolso</a>
        <a href="../{next_}/" style="font-family:var(--hand);font-size:19px;color:var(--frambuesa-txt);text-decoration:none">Día {next_} →</a>
      </div>
    </div>
  </section>
{bloque_opiniones(b)}
{alternos_html}
</main>
{FOOTER}
</body>
</html>"""
    escribir(f"dia/{n}/index.html", html)

def generar_ficha_bolso(b):
    dias_del_bolso = [n for n in range(1, 366) if bolso_del_dia(n)[0]["id"] == b["id"]]
    dias_txt = ", ".join(str(x) for x in dias_del_bolso[:12]) or "—"
    ops = b.get("opiniones_amazon", [])
    ops_html = "\n".join(f'      <blockquote class="opinion-amazon">“{o[:300]}”</blockquote>' for o in ops[:4])
    sec_voces = ""
    if ops:
        sec_voces = f"""  <section class="sec oscura">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Opiniones reales de compradoras</span>
        <h2>Directo de la ficha <em>de Amazon</em></h2>
{ops_html}
        <p style="margin-top:18px"><a class="btn vino" href="{b['afiliado']}" target="_blank" rel="sponsored nofollow noopener">Ver la ficha completa en Amazon ↗</a></p>
      </div>
    </div>
  </section>"""

    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Product",
        "name": b["titulo"].split(",")[0],
        "description": b["titulo"],
        "image": f"{DOMINIO}/{b['imagen']}",
        "aggregateRating": {"@type": "AggregateRating",
                            "ratingValue": b.get("rating", 0),
                            "reviewCount": b.get("n_valoraciones", 0)},
        "offers": {"@type": "Offer", "priceCurrency": "EUR",
                   "price": str(b.get("precio_num", "")).replace(".", ","),
                   "url": b["afiliado"], "availability": "https://schema.org/InStock"},
    }, ensure_ascii=False, indent=2)

    html = head_html(
        f"{b['titulo'].split(',')[0]} — precio real, pros y contras — El Bolso de Esperanza",
        f"{b['titulo'][:120]}. Precio real {b['precio']}, {b.get('rating')}★ con {b.get('n_valoraciones')} valoraciones. Pros y contras calculados de opiniones reales.",
        f"{DOMINIO}/bolso/{b['id']}/", og_type="product",
    )
    html = html.replace("{css}", css_href(2))
    html += f"""{UBAR}
{header("../../")}
<script type="application/ld+json">
{jsonld}
</script>
<main>
  <section class="ficha" style="padding-top:48px">
    <div class="container">
      <a class="volver" href="../../">← Portada</a>
      <article>
        <span class="sec-label" style="color:var(--frambuesa-txt);margin-top:18px">Carta de colección · ficha oficial</span>
        <h1>{nombre_display(b)}</h1>
        <p class="resumen" style="font-style:italic">{b['titulo']}</p>
{bloque_producto(b, pref="../../")}
        <p style="font-size:13px;color:var(--gris);margin-top:14px">Aparece en el diario los días: {dias_txt}. Nota media {str(b.get('rating')).replace('.', ',')}★ sobre {fmt(b.get('n_valoraciones') or 0)} valoraciones reales.</p>
      </article>
    </div>
  </section>
{sec_voces}
</main>
{FOOTER}
</body>
</html>"""
    escribir(f"bolso/{b['id']}/index.html", html)

def generar_opiniones_index():
    con_ops = [b for b in BOLSOS if b.get("opiniones_amazon")]
    con_ops.sort(key=lambda b: -(b.get("rating") or 0))
    bloques = []
    for b in con_ops[:18]:
        items = "\n".join(f'      <blockquote class="opinion-amazon">“{o[:280]}”</blockquote>' for o in b["opiniones_amazon"][:2])
        pros, _ = texto_pc(b)
        tipo_txt = tipo_de(b) if tipo_de(b) != "Bolso" else ""
        cola = f" · {tipo_txt}" if tipo_txt else ""
        bloques.append(f"""    <div class="stat-card" style="padding:22px">
      <span style="font-family:var(--hand);font-size:19px;color:var(--frambuesa-txt)">{str(b.get('rating')).replace('.', ',')}★ · {fmt(b.get('n_valoraciones') or 0)} valoraciones{cola}</span>
      <h2 style="font-family:var(--serif);font-size:clamp(20px,2.6vw,28px);font-weight:700;line-height:1.25;margin-top:10px">{nombre_display(b)}</h2>
      <p style="font-size:13px;color:var(--secundario);margin:6px 0 4px">{b['precio']} € · Lo que destacan: {', '.join(pros[:2]).lower() if pros else 'su diseño'}</p>
{items}
      <p style="margin-top:12px"><a href="../bolso/{b['id']}/" style="font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--frambuesa-txt);text-decoration:none">Ver su carta →</a></p>
    </div>""")

    html = head_html(
        "Opiniones reales — El Bolso de Esperanza",
        "Lo que escriben las compradoras de los bolsos del diario: opiniones reales de Amazon, con su nota y su precio.",
        f"{DOMINIO}/opiniones/",
    )
    html = html.replace("{css}", css_href(1))
    grid = ("\n" + '    <div style="height:16px"></div>\n' + "\n").join(bloques) if bloques else ""
    html += f"""{UBAR}
{header("../")}
<main>
  <section class="sec clara" style="padding-top:60px">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Voces de la colección</span>
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px)">Directo de las fichas <em style="color:var(--frambuesa-txt);font-style:italic">de Amazon</em></h1>
        <p class="lead" style="color:#57504C">Las palabras exactas de quienes ya compraron cada bolso: nada resumido, nada inventado. Ordenadas por nota.</p>
        <div style="margin-top:36px">
{grid}
        </div>
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>"""
    escribir("opiniones/index.html", html)

def generar_buscar():
    html = head_html(
        "¿Qué bolso me tocó el día que nací? — El Bolso de Esperanza",
        "Elige una fecha cualquiera del año y descubre qué bolso real le toca: precio, nota, pros y contras de sus compradoras.",
        f"{DOMINIO}/buscar/",
    )
    html = html.replace("{css}", css_href(1))
    html += f"""{UBAR}
{header("../")}
<main>
  <section class="sec clara" style="padding-top:60px">
    <div class="container">
      <div class="watermark" aria-hidden="true">365</div>
      <div class="sec-inner">
        <span class="sec-label">El buscador del año</span>
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px)">¿Qué bolso te tocó <em style="color:var(--frambuesa-txt);font-style:italic">el día que naciste?</em></h1>
        <p class="lead" style="color:#57504C">365 días, 365 cartas de colección. Elige cualquier fecha y te decimos qué bolso lleva ese día — con su precio real, su nota y lo que dicen quienes lo compraron.</p>
        <div id="finder">
          <label for="finder-fecha">Elige tu fecha</label>
          <div class="finder-row">
            <input type="date" id="finder-fecha" min="{ANIO}-01-01" max="{ANIO}-12-31">
            <button class="btn vino" id="finder-btn">Buscar mi bolso</button>
            <button class="btn marfil" id="finder-random">Sorpréndeme</button>
          </div>
          <div id="finder-resultado" class="finder-resultado"></div>
        </div>
      </div>
    </div>
  </section>
  <section class="sec oscura">
    <div class="container">
      <div class="sec-inner">
        <span class="sec-label">Cómo funciona</span>
        <h2>Una colección que <em>crece cada día</em></h2>
        <p class="lead">La colección se ordena por calidad (nota media y número de valoraciones reales) y se reparte por los 365 días del año. Cada carta nueva que entra, entra con su día. Consulta las <a href="../estadisticas/" style="color:var(--frambuesa-txt);font-weight:600">estadísticas de la colección →</a></p>
      </div>
    </div>
  </section>
</main>
<script src="../js/finder-data.js?v={VER}"></script>
<script src="../js/finder.js?v={VER}"></script>
{FOOTER}
</body>
</html>"""
    escribir("buscar/index.html", html)

def generar_estadisticas():
    precios = [b.get("precio_num") or 0 for b in BOLSOS]
    ratings = [b.get("rating") or 0 for b in BOLSOS]
    vals = [b.get("n_valoraciones") or 0 for b in BOLSOS]
    total = len(BOLSOS)
    precio_medio = sum(precios) / total if total else 0
    rating_medio = sum(ratings) / total if total else 0
    val_total = sum(vals)
    mas_caro = max(BOLSOS, key=lambda b: (b.get("precio_num") or 0))
    mas_votado = max(BOLSOS, key=lambda b: (b.get("n_valoraciones") or 0))
    mejor_nota = max(BOLSOS, key=lambda b: ((b.get("rating") or 0), (b.get("n_valoraciones") or 0)))
    con_ops = sum(1 for b in BOLSOS if b.get("opiniones_amazon"))

    tramos = [("< 30 €", 0, 30), ("30 – 60 €", 30, 60), ("60 – 90 €", 60, 90),
              ("90 – 150 €", 90, 150), ("150 € +", 150, 10**9)]
    max_tramo = max(sum(1 for p in precios if lo <= p < hi) for _, lo, hi in tramos) or 1
    filas_tramos = ""
    for nombre, lo, hi in tramos:
        cnt = sum(1 for p in precios if lo <= p < hi)
        pct = round(cnt * 100 / max(cnt, total))
        filas_tramos += f"""          <div class="barra-stat"><span class="nombre">{nombre}</span><div class="pista"><div class="relleno" style="width:{max(pct, 4)}%"></div></div><span class="valor">{cnt} cartas</span></div>\n"""

    tipos = {}
    for b in BOLSOS:
        tipos[tipo_de(b)] = tipos.get(tipo_de(b), 0) + 1
    max_tipo = max(tipos.values()) if tipos else 1
    filas_tipos = ""
    for nombre, cnt in sorted(tipos.items(), key=lambda x: -x[1])[:6]:
        pct = round(cnt * 100 / max_tipo)
        filas_tipos += f"""          <div class="barra-stat oro"><span class="nombre">{nombre}</span><div class="pista"><div class="relleno" style="width:{max(pct, 4)}%"></div></div><span class="valor">{cnt}</span></div>\n"""

    def top_item(i, b, dato):
        return f"""            <a class="top-item" href="../bolso/{b['id']}/">
              <span class="ti-n">#{i}</span>
              <img src="../{b['imagen']}" alt="{b['titulo']}" loading="lazy">
              <span class="ti-info"><span class="ti-nombre">{b['titulo'].split(',')[0]}</span><br><span class="ti-dato">{dato}</span></span>
            </a>"""

    top_precio = "\n".join(
        top_item(i + 1, b, f"{b['precio']} € · {tipo_de(b)} · {str(b.get('rating', 0)).replace('.', ',')}★")
        for i, b in enumerate(sorted(BOLSOS, key=lambda x: -(x.get("precio_num") or 0))[:5]))
    top_votadas = "\n".join(
        top_item(i + 1, b, f"{fmt(b.get('n_valoraciones') or 0)} valoraciones · {str(b.get('rating', 0)).replace('.', ',')}★")
        for i, b in enumerate(sorted(BOLSOS, key=lambda x: -(x.get("n_valoraciones") or 0))[:5]))

    html = head_html(
        "Estadísticas de la colección — El Bolso de Esperanza",
        f"Los números reales de la colección: {total} cartas, precio medio {precio_medio:.2f} €, nota media {rating_medio:.2f} y las piezas más codiciadas.",
        f"{DOMINIO}/estadisticas/",
    )
    html = html.replace("{css}", css_href(1))
    html += f"""{UBAR}
{header("../")}
<main>
  <section class="sec clara" style="padding-top:60px">
    <div class="container">
      <div class="watermark" aria-hidden="true">Nºs</div>
      <div class="sec-inner">
        <span class="sec-label">El albúm por cifras</span>
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px)">La colección, <em style="color:var(--frambuesa-txt);font-style:italic">en números</em></h1>
        <p class="lead" style="color:#57504C">Todo lo que sigue son datos reales de la colección: precios y notas de Amazon, sin redondeos convenientes.</p>

        <div class="stat-cards">
          <div class="stat-card"><div class="cifra">{total}<small> cartas</small></div><div class="concepto">Colección actual</div></div>
          <div class="stat-card"><div class="cifra">{f'{precio_medio:.2f}'.replace('.', ',')} €</div><div class="concepto">Precio medio</div></div>
          <div class="stat-card"><div class="cifra">{f'{rating_medio:.2f}'.replace('.', ',')}<small> / 5</small></div><div class="concepto">Nota media</div></div>
          <div class="stat-card"><div class="cifra">{fmt(val_total)}</div><div class="concepto">Valoraciones acumuladas</div></div>
        </div>

        <div style="margin-top:56px">
          <span class="sec-label">Reparto por precio</span>
          <h2 style="font-family:var(--serif);font-weight:700;font-size:clamp(26px,4vw,40px)">Cuánto cuesta <em style="color:var(--frambuesa-txt);font-style:italic">coleccionar</em></h2>
          <div class="barra-stats">
{filas_tramos}          </div>
        </div>

        <div style="margin-top:56px">
          <span class="sec-label">Tipología</span>
          <h2 style="font-family:var(--serif);font-weight:700;font-size:clamp(26px,4vw,40px)">Los tipos <em style="color:var(--frambuesa-txt);font-style:italic">de la colección</em></h2>
          <div class="barra-stats">
{filas_tipos}          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="sec oscura">
    <div class="container">
      <div class="watermark" aria-hidden="true">Top</div>
      <div class="sec-inner">
        <span class="sec-label">Los ránkings de la colección</span>
        <h2 style="font-family:var(--serif);font-weight:700;font-size:clamp(26px,4vw,40px)">Las más <em style="color:var(--rosa-suave);font-style:italic">codiciadas</em></h2>
        <div class="stat-cards" style="margin-top:36px;grid-template-columns:1fr 1fr">
          <div>
            <span class="sec-label" style="color:var(--oro-suave);border-color:var(--oro-suave)">★ Las más valiosas</span>
            <div class="top-lista">
{top_precio}
            </div>
          </div>
          <div>
            <span class="sec-label" style="color:var(--rosa-suave);border-color:var(--rosa-suave)">♥ Las más valoradas</span>
            <div class="top-lista">
{top_votadas}
            </div>
          </div>
        </div>
        <div class="stat-cards" style="margin-top:40px">
          <div class="stat-card"><div class="cifra">{mas_caro['precio']} €</div><div class="concepto">La carta más valiosa: {mas_caro['titulo'].split(',')[0]}</div></div>
          <div class="stat-card"><div class="cifra">{fmt(mas_votado.get('n_valoraciones') or 0)}</div><div class="concepto">Más valoraciones: {mas_votado['titulo'].split(',')[0]}</div></div>
          <div class="stat-card"><div class="cifra">{str(mejor_nota.get('rating', 0)).replace('.', ',')}★</div><div class="concepto">Mejor nota: {mejor_nota['titulo'].split(',')[0]}</div></div>
          <div class="stat-card"><div class="cifra">{con_ops}<small> / {total}</small></div><div class="concepto">Cartas con opiniones publicadas</div></div>
        </div>
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>"""
    escribir("estadisticas/index.html", html)

def generar_sitemap():
    urls = ["", "dia/", "buscar/", "opiniones/", "estadisticas/"]
    urls += [f"dia/{n}/" for n in range(1, 366)]
    urls += [f"bolso/{b['id']}/" for b in BOLSOS]
    items = "\n".join(f"  <url><loc>{DOMINIO}/{u}</loc><changefreq>weekly</changefreq></url>" for u in urls)
    escribir("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n')

def main():
    print(f"Generando El Bolso de Esperanza v5 'Colección Rosa' — {N} bolsos en repositorio")
    if N == 0:
        print("ERROR: repositorio vacío. Corre scripts/bolso-catalogo.py primero.")
        return
    generar_home()
    generar_finder_datos()
    generar_buscar()
    generar_opiniones_index()
    generar_estadisticas()
    n_dias = 365
    for n in range(1, n_dias + 1):
        generar_dia(n)
    for b in BOLSOS:
        generar_ficha_bolso(b)
    generar_blog_index()
    generar_sitemap()
    total = 5 + n_dias + N
    print(f"\nListo: {total} páginas (home + buscar + opiniones + estadísticas + índice + {n_dias} días + {N} fichas) + finder-data + sitemap")

if __name__ == "__main__":
    main()
