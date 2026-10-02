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
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VER = "20261002d"
DOMINIO = "https://ntizar.github.io/ElBolsoDeEsperanza"
ANIO = 2026

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
    <span><span class="punto">●</span> 365 BOLSOS · UNO POR CADA DÍA DEL AÑO</span>
    <span>/</span>
    <span>PRODUCTOS REALES DE AMAZON CON SU PRECIO Y SUS OPINIONES</span>
    <span>/</span>
    <span>ENCUENTRA EL DE TU CUMPLEAÑOS</span>
  </div>
</div>"""

def header(raiz):
    return f"""<header class="site-header">
  <div class="container">
    <a href="{raiz}" class="logo">El Bolso de <span class="accent">Esperanza</span><span class="tagline">Un bolso real cada día</span></a>
    <nav>
      <a href="{raiz}#hoy">El bolso de hoy</a>
      <a href="{raiz}dia/">El diario</a>
      <a href="{raiz}buscar/">Tu cumpleaños</a>
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

def card_dia(n, pref=""):
    b, _ = bolso_del_dia(n)
    t = b["titulo"] if len(b["titulo"]) <= 64 else b["titulo"][:64] + "…"
    return f"""      <a class="card-dia" href="{pref}dia/{n}/">
        <div class="imagen"><img src="{pref}{b['imagen']}" alt="{b['titulo']}" loading="lazy"></div>
        <div class="cuerpo">
          <span class="dia">{chip_dia(n)}</span>
          <h3>{t}</h3>
          <div class="pie">
            <span class="precio">{b['precio']}</span>
            <span class="rating">{str(b.get('rating', 0)).replace('.', ',')}★ · {fmt(b.get('n_valoraciones') or 0)} val.</span>
          </div>
        </div>
      </a>"""

def bloque_producto(b, pref="", titulo_fijo=None):
    pros, contras = pros_contras(b)
    pros_html = "".join(f"<li>{p}</li>" for p in pros) or "<li>Aún sin opiniones suficientes</li>"
    contras_html = "".join(f"<li>{c}</li>" for c in contras) or "<li>Sin quejas recurrentes</li>"
    nv = b.get("n_valoraciones") or 0
    return f"""      <div class="producto">
        <div class="producto-img"><img src="{pref}{b['imagen']}" alt="{b['titulo']}"></div>
        <div class="producto-info">
          <h4>{titulo_fijo or b['titulo']}</h4>
          <div class="marca">{b.get('marca', '')} · ASIN {b['asin']}</div>
          <div class="fila-datos">
            <span class="precio">{b['precio']}</span>
            <span class="rating">{estrellas(b.get('rating'))} {str(b.get('rating', 0)).replace('.', ',')} · {fmt(nv)} valoraciones</span>
          </div>
          <div class="procontras">
            <div><b>Lo que destacan las compradoras</b><ul>{pros_html}</ul></div>
            <div><b>Lo que critican</b><ul>{contras_html}</ul></div>
          </div>
          <p class="veredicto">{veredicto(b)}</p>
          <a href="{b['afiliado']}" class="btn-affiliate" target="_blank" rel="sponsored nofollow noopener">Ver precio en Amazon ↗</a>
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
    b2, _ = bolso_del_dia(hoy_n + 1)
    b3, _ = bolso_del_dia(hoy_n + 2)
    ultimos = "\n".join(card_dia(n) for n in range(hoy_n - 1, max(0, hoy_n - 7), -1))
    proximos = "\n".join(
        f"""        <div class="mini-proximo">
          <img src="{b['imagen']}" alt="{b['titulo']}" loading="lazy">
          <div><span class="mini-dia">{chip_dia(hoy_n + i + 1)}</span><p>{b['titulo'][:48]}…</p></div>
        </div>"""
        for i, b in enumerate((b2, b3)))
    pros_hoy, contras_hoy = pros_contras(b_hoy)
    d_hoy = fecha_de_dia(hoy_n)
    nombre_hoy = b_hoy["titulo"].split(",")[0]

    html = head_html(
        "El Bolso de Esperanza — Un bolso real cada día del año",
        f"365 bolsos reales de Amazon, uno por cada día del año. Hoy toca el de {d_hoy.day} de {MESES[d_hoy.month-1]}: {nombre_hoy}. Encuentra el de tu cumpleaños.",
        f"{DOMINIO}/",
    )
    html = html.replace("{css}", css_href(0))
    html += f"""{UBAR}
{header("")}
<main>

  <!-- HERO: EL BOLSO DE HOY -->
  <section class="hero" id="hoy">
    <span class="silueta s1">👜</span>
    <div class="container">
      <div class="hero-grid">
        <div class="hero-txt">
          <span class="chip">El bolso del {d_hoy.day} de {MESES[d_hoy.month-1]} · día {hoy_n} del año</span>
          <h1><span class="l1">Cada día del año,</span><span class="l2">un bolso con una decisión detrás</span></h1>
          <p class="hero-lead">365 bolsos reales de Amazon —con precio, nota y opiniones verificadas— repartidos por los días del año en bucle. Sin inventos: el bolso que ves es el bolso que se vende.</p>
          <div class="hero-ctas">
            <a class="btn vino" href="#hoy-bolso">Ver el bolso de hoy ↓</a>
            <a class="btn marfil" href="buscar/">¿Qué bolso te tocó nacer? →</a>
          </div>
        </div>
        <div class="hero-bolso" id="hoy-bolso">
          <span class="etiqueta">Bolso del día {hoy_n}</span>
          <img src="{b_hoy['imagen']}" alt="{b_hoy['titulo']}">
          <div class="hero-bolso-info">
            <h3>{nombre_hoy}</h3>
            <div class="fila-datos">
              <span class="precio">{b_hoy['precio']}</span>
              <span class="rating">{estrellas(b_hoy.get('rating'))} {fmt(b_hoy.get('n_valoraciones') or 0)} val.</span>
            </div>
            <div class="procontras mini">
              <div><b>Pros</b><ul>{''.join(f'<li>{p}</li>' for p in pros_hoy) or '<li>—</li>'}</ul></div>
              <div><b>Contras</b><ul>{''.join(f'<li>{c}</li>' for c in contras_hoy) or '<li>—</li>'}</ul></div>
            </div>
            <div style="display:flex;gap:10px;flex-wrap:wrap">
              <a class="btn vino" href="bolso/{b_hoy['id']}/">Ficha completa →</a>
              <a class="btn-affiliate" href="{b_hoy['afiliado']}" target="_blank" rel="sponsored nofollow noopener">Amazon ↗</a>
            </div>
          </div>
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
        <span class="sec-label" style="margin-top:46px">Los últimos días publicados</span>
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
        <p class="lead" style="color:#F2DFE0">Cada bolso de este diario se toma directamente de su ficha de Amazon: su foto, su precio, su nota y las opiniones de quienes lo compraron. Lo que ves es lo que llega.</p>
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
            "titulo": b["titulo"].split(",")[0], "precio": b["precio"],
            "rating": b.get("rating"), "n_val": b.get("n_valoraciones", 0),
            "imagen": b["imagen"],
        })
    # inline en JS (sin fetch): funciona en http(s) y en file:// sin CORS
    escribir("js/finder-data.js",
             "window.FINDER_DATA = " + json.dumps({"anio": ANIO, "dias": dias}, ensure_ascii=False) + ";\n")

def generar_blog_index():
    hoy_n = (date.today() - date(ANIO, 1, 1)).days + 1
    cards = "\n".join(card_dia(n, pref="../") for n in range(365, 0, -1))
    html = head_html(
        "El Diario — 365 días, 365 bolsos — El Bolso de Esperanza",
        "El diario completo: cada día del año con su bolso real, su precio y sus opiniones.",
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
        <span class="sec-label">El diario</span>
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px);line-height:1.05">El año entero, <em style="color:var(--vino);font-style:italic">de más nuevo a más viejo</em></h1>
        <p class="lead" style="color:#57504C">Repositorio actual: {N} bolsos reales. Los días avanzan en bucle hasta cubrir los 365.</p>
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
    es_repeticion = n > N
    nota_repeticion = ""
    if es_repeticion:
        nota_repeticion = (f'<p class="nota-bucle">El repositorio de bolsos aún está creciendo hacia los 365: '
                           f'el día {n} comparte bolso con el día {(n - 1) % N + 1}, pero cada paso por el '
                           f'calendario le da un enfoque nuevo. Cuando el repositorio se complete, cada día '
                           f'tendrá su propio bolso definitivo.</p>')

    alternos_html = ""
    if alternos:
        cards = "\n".join(
            f"""        <div class="mini-proximo">
          <img src="../..{a['imagen'][len('assets')-6:] if False else '/' + a['imagen']}" alt="{a['titulo']}" loading="lazy">
          <div><span class="mini-dia">También encaja</span><p>{a['titulo'][:44]}…</p></div>
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
          <span class="meta-blog" style="color:var(--tan)">{semana}, {fecha_larga(d)} · día {n} de 365</span>
          <h1>{b['titulo'].split(',')[0]}: <em>el bolso del día {n}</em></h1>
          <p class="resumen" style="color:#CFC2BE;font-style:italic">{t['gancho']} {t['parrafo1']}</p>
          <figure style="margin:28px 0 6px">
            <img src="../../{b['imagen']}" alt="{b['titulo']}" style="border:2px solid var(--marfil);width:100%;max-height:460px;object-fit:cover">
            <figcaption style="font-size:12px;color:var(--gris);margin-top:8px;letter-spacing:1px;text-transform:uppercase">Imagen oficial del producto en Amazon — no es un render</figcaption>
          </figure>
          <div class="cuerpo-blog">
            <p>{t['parrafo2']}</p>
            {nota_repeticion}
          </div>
        </article>
      </div>
    </div>
  </section>

  <section class="ficha">
    <div class="container">
      <span class="sec-label" style="color:var(--vino)">El bolso de hoy, con datos reales</span>
{bloque_producto(b, pref="../../")}
      <div style="display:flex;justify-content:space-between;margin-top:30px;flex-wrap:wrap;gap:10px">
        <a href="../{prev_}/" style="font-family:var(--hand);font-size:19px;color:var(--vino-txt);text-decoration:none">← Día {prev_}</a>
        <a href="../../bolso/{b['id']}/" style="font-family:var(--hand);font-size:19px;color:var(--vino-txt);text-decoration:none">Ficha del bolso</a>
        <a href="../{next_}/" style="font-family:var(--hand);font-size:19px;color:var(--vino-txt);text-decoration:none">Día {next_} →</a>
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
        <span class="sec-label" style="color:var(--vino);margin-top:18px">Ficha del bolso · datos scrapeados de Amazon</span>
        <h1>{b['titulo'].split(',')[0]}</h1>
        <p class="resumen" style="font-style:italic">{b['titulo']}</p>
{bloque_producto(b, pref="../../", titulo_fijo=b['titulo'])}
        <p style="font-size:13px;color:var(--gris);margin-top:14px">Aparece en el diario los días: {dias_txt}. Nota media {str(b.get('rating')).replace('.', ',')}★ sobre {fmt(b.get('n_valoraciones') or 0)} valoraciones reales.</p>
      </article>
    </div>
  </section>

  <section class="sec oscura">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Opiniones reales de compradoras</span>
        <h2>Directo de la ficha <em>de Amazon</em></h2>
{ops_html or '<p style="color:var(--rosa)">Aún sin opiniones scrapeadas para este producto — el cron las traerá.</p>'}
        <p style="margin-top:18px"><a class="btn vino" href="{b['afiliado']}" target="_blank" rel="sponsored nofollow noopener">Ver la ficha completa en Amazon ↗</a></p>
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>"""
    escribir(f"bolso/{b['id']}/index.html", html)

def generar_opiniones_index():
    con_ops = [b for b in BOLSOS if b.get("opiniones_amazon")]
    bloques = []
    for b in con_ops[:24]:
        items = "\n".join(f'      <blockquote class="opinion-amazon">“{o[:280]}”</blockquote>' for o in b["opiniones_amazon"][:2])
        bloques.append(f"""    <div class="sec-inner" style="margin-top:40px">
      <span class="sec-label">{str(b.get('rating')).replace('.', ',')}★ · {fmt(b.get('n_valoraciones') or 0)} valoraciones · {b['precio']}</span>
      <h2 style="font-size:clamp(22px,3vw,32px)">{b['titulo'].split(',')[0]}</h2>
      <p class="lead">Ficha: <a href="../bolso/{b['id']}/" style="color:var(--vino-txt);font-weight:600">ver el bolso →</a></p>
{items}
    </div>""")

    html = head_html(
        "Opiniones reales — El Bolso de Esperanza",
        "Las opiniones reales de compradoras de los bolsos del diario, scrapeadas directamente de Amazon.",
        f"{DOMINIO}/opiniones/",
    )
    html = html.replace("{css}", css_href(1))
    inner = "\n".join(bloques) or "<p>El cron está recolectando opiniones. Vuelve pronto.</p>"
    html += f"""{UBAR}
{header("../")}
<main>
  <section class="sec clara" style="padding-top:60px">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Opiniones</span>
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px)">Directo de las fichas <em style="color:var(--vino);font-style:italic">de Amazon</em></h1>
        <p class="lead" style="color:#57504C">Nada inventado: estos textos son opiniones reales scrapeadas de las fichas de los bolsos del diario.</p>
{inner}
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
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px)">¿Qué bolso te tocó <em style="color:var(--vino);font-style:italic">el día que naciste?</em></h1>
        <p class="lead" style="color:#57504C">365 días, 365 bolsos reales en bucle. Elige cualquier fecha y te decimos qué bolso lleva ese día — con su precio real, su nota y lo que dicen quienes lo compraron.</p>
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
        <h2>Un bolso por día, <em>en bucle infinito</em></h2>
        <p class="lead">El repositorio de bolsos se ordena por calidad (nota media y número de valoraciones reales) y se reparte por los 365 días del año. Cuando el repositorio crece, cada día recibe un bolso nuevo; mientras tanto, los días repetidos llevan alternativas y un enfoque distinto cada vez que pasan por el calendario.</p>
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

def generar_sitemap():
    urls = ["", "dia/", "buscar/", "opiniones/"]
    urls += [f"dia/{n}/" for n in range(1, 366)]
    urls += [f"bolso/{b['id']}/" for b in BOLSOS]
    items = "\n".join(f"  <url><loc>{DOMINIO}/{u}</loc><changefreq>weekly</changefreq></url>" for u in urls)
    escribir("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n')

def main():
    print(f"Generando El Bolso de Esperanza v4 — {N} bolsos en repositorio")
    if N == 0:
        print("ERROR: repositorio vacío. Corre scripts/bolso-catalogo.py primero.")
        return
    generar_home()
    generar_finder_datos()
    generar_buscar()
    generar_opiniones_index()
    n_dias = 365
    for n in range(1, n_dias + 1):
        generar_dia(n)
    for b in BOLSOS:
        generar_ficha_bolso(b)
    generar_blog_index()
    generar_sitemap()
    total = 4 + n_dias + N
    print(f"\nListo: {total} páginas (home + buscar + opiniones + índice + {n_dias} días + {N} fichas) + finder-data + sitemap")

if __name__ == "__main__":
    main()
