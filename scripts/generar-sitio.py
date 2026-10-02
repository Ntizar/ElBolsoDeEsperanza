#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador del sitio "El Bolso de Esperanza" — sistema portado de kit72h.
Lee data/bolsos.json, data/blog.json y data/opiniones.json y regenera:
  - index.html            (home: hero + bolsos + diario + opiniones + cta)
  - blog/index.html       (índice del diario)
  - blog/<slug>/index.html (9 entradas con historia completa + producto + opiniones)
  - opiniones/index.html  (índice de opiniones por bolso)
  - bolso/<id>/index.html (ficha de cada bolso con sus opiniones)
  - sitemap.xml
Idempotente: se puede correr las veces que haga falta.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VER = "20261002a"  # versión del CSS — bump en cada cambio de estilos
DOMINIO = "https://ntizar.github.io/ElBolsoDeEsperanza"

# ---------------------------------------------------------------- carga de datos

def cargar(nombre):
    with open(RAIZ / "data" / nombre, encoding="utf-8") as f:
        return json.load(f)

BOLSOS = cargar("bolsos.json")["bolsos"]
BLOG = cargar("blog.json")["entradas"]
OPINIONES = cargar("opiniones.json")["opiniones"]

BOLSO_POR_ID = {b["id"]: b for b in BOLSOS}
BOLSO_POR_SLUG = {b["slug"]: b for b in BOLSOS}
ENTRADA_POR_BOLSO = {e["bolso"]: e for e in BLOG}

def opiniones_de(bolso_id):
    return [o for o in OPINIONES if o["bolso"] == bolso_id]

def estrellas(n):
    return "★" * n + "☆" * (5 - n)

def fecha_larga(fecha):
    MESES = ["enero","febrero","marzo","abril","mayo","junio","julio",
             "agosto","septiembre","octubre","noviembre","diciembre"]
    anio, mes, dia = fecha.split("-")
    return f"{int(dia)} de {MESES[int(mes)-1]} de {anio}"

def url_afiliado(bolso):
    return bolso.get("afiliado") or bolso.get("busqueda")

# ---------------------------------------------------------------- cuerpos narrativos
# Cada entrada: resumen, secciones [(h2, [párrafos])], cita

POSTS = {
    "dia-001": {
        "resumen": "Era un bolso grande, de señora grande, de esos que ocupan medio armario. Lo compré el mismo día que me llamaron a la oficina del CEO.",
        "secciones": [
            ("El bolso", [
                "Entré en la tienda de lujo de Gran Vía, la de las mujeres que ya no necesitan demostrar nada. Pedí el bolso más grande que tenían. El dependiente me lo trajo envuelto en papel de seda y yo lo toqué como se toca algo que uno sabe suyo antes de pagarlo.",
                "Tote de cuero grueso, herrajes dorados, forro que huele a tienda seria. Cabe el portátil, el neceser, una carpeta entera con los informes del trimestre. Y sobra sitio, que era justo lo que quería: sitio para todo lo que venía.",
            ]),
            ("Mi historia", [
                "Ese mismo día me habían comunicado el ascenso. Tres años pidiéndolo. Tres años viendo pasar el puesto por delante de mí en manos de hombres que llegaban más tarde y se marchaban antes. Cuando colgué el teléfono salí a la calle y no lloré. Fui directa a la tienda.",
                "Lo llevé a la oficina a la mañana siguiente y lo dejé sobre la mesa en la primera reunión. No para presumir. Para que ocupara el lugar que le correspondía — al bolso y a mí.",
            ]),
        ],
        "cita": "No pedí un ascenso durante tres años por un bolso. Lo pedí porque sabía que lo merecía.",
    },
    "dia-002": {
        "resumen": "Era un bolso pequeño, negro, de cuero fino. Lo llevaba cruzado del hombro, bien sujeto contra el costado, como quien lleva una coraza.",
        "secciones": [
            ("El bolso", [
                "Negro, de cuero fino, con una correa larga que permite llevarlo cruzado y pegado al cuerpo. Es el bolso más pequeño que poseo y el que más veces me ha salvado la noche.",
                "Cabe el móvil, las llaves, un labial y ni un gramo más. Y el cierre interior tiene un truco: se cierra con un giro que no se abre solo. Lo aprendí a valorar en cenas como la de esta historia.",
            ]),
            ("Mi historia", [
                "Era una cena de trabajo. De esas donde la conversación empieza por el proyecto y acaba derrotando al vino. El cliente de mi derecha tenía esas manos que se acercan demasiado cuando rien, y esa manera de mirar el escote de las demás cuando creen que nadie las mira.",
                "Aquella noche entendí que un bolso cruzado no es un accesorio: es una frontera. Lo llevaba pegado al costado como quien lleva una coraza, y con la mano encima como quien sostiene su posición.",
            ]),
        ],
        "cita": "Hay bolsos que se compran por bonitos. Este lo compré por lo que protege.",
    },
    "dia-003": {
        "resumen": "Me lo compré con mi primer sueldo. Un pochette diminuto, de esos que casi no caben en la mano. Solo cabía lo estrictamente necesario.",
        "secciones": [
            ("El bolso", [
                "Un pochette. Diminuto, rígido, con la cadena corta. De esos que parecen un capricho y son una declaración: aquí cabe solo lo esencial, y lo esencial soy yo.",
                "No cabe ni el móvil más grande de hoy. Cabe un labial, una tarjeta y las llaves. Nada más. Es el bolso de las primeras veces: primeras citas, primeras cenas, primeros pasos que importan.",
            ]),
            ("Mi historia", [
                "Lo compré con mi primer sueldo serio, en una semana donde por fin me sobraba algo a fin de mes. Y me lo llevé a la primera cita con el jefe de otro departamento — jefe de OTRO departamento, que en una empresa grande es como decir inocente hasta que se demuestre lo contrario.",
                "Llegué con el pochette en la mano y las uñas recién hechas. La cena fue de esos raros ratos donde todo sale natural. Aún llevo el bolso a cada primera cita, mía o de mis amigas. Es el bolso de los comienzos.",
            ]),
        ],
        "cita": "Mi primer sueldo se convirtió en un bolso que cabe en una mano y en una decisión que no cabe en ninguna.",
    },
    "dia-004": {
        "resumen": "De Alicante a Madrid. 672 kilómetros, un coche prestado y esta bandolera colgada del hombro mientras el sol se ponía.",
        "secciones": [
            ("El bolso", [
                "Bandolera de cuero auténtico, de esas que no llevan logo porque el cuero ya lo dice todo. Es del tipo de bolso que mejora con el uso: cada arruga es un kilómetro.",
                "Es plana por fuera y profunda por dentro. Cabe la documentación, el móvil, un cargador y — aquel día — un pañuelo de mi madre que metí sin saber por qué.",
            ]),
            ("Mi historia", [
                "Dejé a mi novio de seis años un martes. No fue una escena de película: fueron cajas, un coche prestado y la A-3 con el sol entrando por el parabrisas. La bandolera iba colgada del asiento, al alcance de la mano.",
                "Llegué a Madrid de noche, con el bolso al hombro y las llaves de un piso que todavía olía a pintura. Todo lo que soy ahora empezó en ese viaje. El bolso fue lo único que llevaba conmigo de verdad.",
            ]),
        ],
        "cita": "672 kilómetros caben en una bandolera si lo que llevas dentro es una decisión.",
    },
    "dia-005": {
        "resumen": "Fue el 23 de diciembre. En casa de mis padres las navidades ya habían empezado — risas, vino — y yo estaba en mi habitación con un vaso de vino y la tele apagada. Me arreglé igual. Fui igual. Volví distinta.",
        "secciones": [
            ("El bolso", [
                "Una clutch de gala con cadena removible. No de esas de boda barata que se descuadran al primer brindis: una de verdad, rígida, con acabado mate y un broche que hace clic con autoridad.",
                "Cabe el móvil, el labial y una moneda para el ropero de la sala. Nada más. Y está bien: en una gala, lo que pesa de verdad no se lleva en el bolso.",
            ]),
            ("Mi historia", [
                "Aquella Navidad me quedé sin acompañante de última hora. En casa de mis padres ya se oían las risas de siempre, y yo estaba arriba, con un vestido colgado de la puerta y dos opciones: me quedaba a ver la tele o iba sola a la gala a la que llevaba meses esperando ir.",
                "Me arreglé despacio, sin prisa y sin testigos. Cogí la clutch, el abrigo y el coche. Bailé sola, hablé con desconocidos y volví de madrugada. Nadie me acompañó ni al entrar ni al salir. Y sin embargo es una de las noches de las que más orgullosa estoy.",
            ]),
        ],
        "cita": "Hay noches que empiezan con un vaso de vino y la tele apagada y acaben cambiándote la manera de mirarte.",
    },
    "dia-006": {
        "resumen": "Estaba en el fondo del armario de casa, envuelto en un pañuelo. Saddle, cuero curtido, herrajes que ya no se hacen así. Lo llevé a tasar y me dijeron que no lo vendiera nunca.",
        "secciones": [
            ("El bolso", [
                "Una saddle vintage: esa silueta de silla de montar que nunca pasa de moda porque nunca estuvo de moda, estuvo siempre. Cuero curtido, costura a mano, herrajes de latón que pesan.",
                "El tasador la levantó, olfateó el cuero — se oler el cuero bueno, es literal — y me dijo: «Esto no se vende, esto se hereda de nuevo». Le hice caso. La limpié con crema neutra y le cambié nada más.",
            ]),
            ("Mi historia", [
                "Era de mi madre. Lo llevaba los domingos cuando yo era pequeña y le pedía que me dejara guardarme el billete del tranvía. Cuando la dejé a ella — a su versión de los domingos, a la edad que no perdona — tuve que vaciar su armario. Este bolso estaba en el fondo, envuelto en un pañuelo, como quien guarda una carta.",
                "Hoy lo llevo los domingos. Le tengo prohibido a mi media hermana venderlo cuando me toque a mí irse primero. Las cosas buenas no se venden: se pasan.",
            ]),
        ],
        "cita": "Un bolso heredado no lleva tus cosas. Lleva las de todos los que lo llevaron antes.",
    },
    "dia-007": {
        "resumen": "Billete de ida y vuelta, portátil, un cuaderno con la primera página en blanco y este tote que aguanta todo. En la fila de embarque entendí que mi carrera iba a cambiar.",
        "secciones": [
            ("El bolso", [
                "Tote de viaje de cuero reforzado en las asas. La diferencia entre un tote bonito y un tote de verdad la marca el refuerzo del asa: este aguanta un portátil, un cargador, una botella de medio litro y un abrigo sin que el hombro lo pague.",
                "Tiene una bolsa interior con cremallera donde guardo lo que no puede perderse: pasaporte, billetes, y aquel cuaderno de primera página en blanco.",
            ]),
            ("Mi historia", [
                "Me pagaron una conferencia en Berlín. No era ponente: era oyente con acreditación y mucho ojo. En la fila de embarque, con el tote cargado hasta arriba, entendí algo que no supe formular hasta meses después: que iba a volver distinta.",
                "Hablé con tres personas, conseguí un contacto que hoy es cliente y apunté en la primera página del cuaderno un plan que aún dirijo. El tote ha volado ya cuarenta veces. Las asas siguen enteras. Yo también.",
            ]),
        ],
        "cita": "Hay viajes que se miden en kilómetros y otros en lo que cabe dentro del bolso al volver.",
    },
    "dia-008": {
        "resumen": "Me lo pidió mi compañera de piso para la fiesta de cumpleaños de su chico. Le dije que sí sin pensarlo. Lo vi aparecer en sus fotos durante dos semanas.",
        "secciones": [
            ("El bolso", [
                "Mochila de cuero moderna, del tamaño justo para un día entero fuera de casa. Tiene esa mezcla rara de ser cómoda como una mochila y verse como un bolso, que es exactamente lo que buscan ahora las mochilas.",
                "Correas acolchadas, cierre con imán y una bolsa trasera antirrobo donde guardo la cartera en conciertos y mercadillos.",
            ]),
            ("Mi historia", [
                "Mi compañera de piso me la pidió el viernes por la mañana para la fiesta de su chico. Le dije que sí sin pensarlo. El sábado apareció en sus stories, el domingo en su desayuno, el miércoles en su cena, la semana siguiente en su escapada rural.",
                "Dos semanas tardó en devolvérmela. Cuando la recuperé, yo ya había pedido otra — no por venganza, por resignación: hay cosas que prestas sabiendo que no vuelven. Ahora la presto con un contrato verbal de 48 horas que nadie firma pero todos respetan.",
            ]),
        ],
        "cita": "Hay bolsos que se compran para ti y otros que se compran, sin saberlo, para tu gente.",
    },
    "dia-009": {
        "resumen": "El día que presenté la denuncia por acoso en la empresa, no supe qué hacer con las manos. Elegí un bolso que no se mantiene firme. Como yo esa mañana. Y aun así fui.",
        "secciones": [
            ("El bolso", [
                "Hobo de cuero blando, desestructurado. No tiene armazón: se amolda al cuerpo y se arruga con el uso, y a mí me gusta que se arrugue, porque también lo hace la gente valiente.",
                "Es grande sin ser torpe: entra una carpeta, el móvil, las llaves del coche y un paquete de pañuelos, que aquel día no sobraron.",
            ]),
            ("Mi historia", [
                "Aquel día presenté la denuncia por acoso en la empresa. No era la primera vez que me lo pensaba; era la primera vez que lo hacía. Me desperté a las cinco, me vestí dos veces y no supe qué bolso llevar. Nada de lo que tenía en el armario parecía adecuado para eso.",
                "Cogí el hobo, el más blando, el que no se mantiene firme. Como yo esa mañana. A la salida, las manos me temblaban dentro del bolso, y el bolso las envolvió y no las enseñó a nadie. Gané la denuncia. El bolso, desde entonces, tiene un sitio de honor en mi armario.",
            ]),
        ],
        "cita": "Un bolso blando puede sostener más de lo que parece. Sostuvo mis manos el día más duro.",
    },
}

NOMBRES = {
    "dia-001": "Tote Ejecutivo de Cuero",
    "dia-002": "Bandolera Crossbody Nocturna",
    "dia-003": "Pochette de Fiesta con Cadena",
    "dia-004": "Bandolera Clásica de Cuero",
    "dia-005": "Clutch de Gala con Cadena Removible",
    "dia-006": "Saddle Vintage de Cuero Curtido",
    "dia-007": "Tote de Viaje Reforzado",
    "dia-008": "Mochila Urbana de Cuero",
    "dia-009": "Hobo Blando Desestructurado",
}

# ---------------------------------------------------------------- plantillas base

UBAR = """<div class="ubar">
  <div class="container">
    <span><span class="punto">●</span> UN BOLSO NUEVO CADA DÍA</span>
    <span>/</span>
    <span>EL DIARIO DE ESPERANZA</span>
    <span>/</span>
    <span>SELECCIÓN CON HISTORIA, PRECIO Y OPINIONES</span>
  </div>
</div>"""

HEADER = """<header class="site-header">
  <div class="container">
    <a href="{raiz}" class="logo">El Bolso de <span class="accent">Esperanza</span><span class="tagline">Un bolso nuevo cada día</span></a>
    <nav>
      <a href="{raiz}#bolsos">Los bolsos</a>
      <a href="{raiz}blog/">El diario</a>
      <a href="{raiz}opiniones/">Opiniones</a>
      <a class="btn vino" href="{amazon}" target="_blank" rel="sponsored nofollow noopener">Compra el look ↗</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="site-footer">
  <div class="container">
    <p>El Bolso de Esperanza — el diario de una mujer y sus bolsos. Hecho con ❤️ por David Antizar.</p>
    <p class="disclosure">Como Afiliado de Amazon, obtengo ingresos por las compras adscritas que cumplen los requisitos aplicables. Los precios pueden variar.</p>
  </div>
</footer>"""

AMAZON_HEADER = "https://www.amazon.es/s?k=bolso+cuero+mujer&tag=nti0c8-21"

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

def escribir(relpath, contenido):
    ruta = RAIZ / relpath
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    print(f"  ✓ {relpath}")

def css_href(desde_raiz):
    """devuelve la ruta css correcta según profundidad y con versión"""
    if desde_raiz == 0:
        return f"css/styles.css?v={VER}"
    return f"../css/styles.css?v={VER}" * 1 if desde_raiz == 1 else f"../../css/styles.css?v={VER}"

# ---------------------------------------------------------------- bloques reutilizables

def card_bolso(b, dia=None, href_raiz=0):
    prefijo = "" if href_raiz == 0 else "../"
    entrada = ENTRADA_POR_BOLSO.get(b["id"])
    dia_num = dia or (entrada["dia"] if entrada else None)
    chip_dia = f'<span class="dia">Día {dia_num}</span>' if dia_num else ""
    return f"""      <a class="card-bolso" href="{prefijo}bolso/{b['id']}/">
        <div class="imagen">
          <img src="{prefijo}{b['imagen']}" alt="{b['titulo']}" loading="lazy">
          {chip_dia}
          <span class="rating">{estrellas(b.get('rating', 3))}</span>
        </div>
        <div class="cuerpo">
          <h3>{b['titulo']}</h3>
          <p class="extracto">{b['resumen'][:130]}…</p>
          <div class="pie">
            <span class="precio">{b['precio_aprox']}</span>
            <span class="ir">Ver el bolso →</span>
          </div>
        </div>
      </a>"""

def card_opinion(o, pref="../"):
    b = BOLSO_POR_ID.get(o["bolso"], {})
    return f"""      <article class="card-opinion">
        <div class="estrellas">{estrellas(o['puntuacion'])}</div>
        <h4>{o['titulo']}</h4>
        <p class="texto">“{o['texto']}”</p>
        <p class="autor"><b>{o['nombre']}</b> · {o['ciudad']} · {fecha_larga(o['fecha'])}</p>
        <p class="bolso-ref">Sobre: <a href="{pref}bolso/{o['bolso']}/">{b.get('titulo', o['bolso'])}</a></p>
      </article>"""

def card_blog(e, pref=""):
    return f"""      <a class="card-blog" href="{pref}blog/{e['slug']}/">
        <div class="cuerpo">
          <span class="dia">Día {e['dia']} — {fecha_larga(e['fecha'])}</span>
          <h3>{e['titulo']}</h3>
          <p class="extracto">{e['extracto'][:120]}…</p>
          <span class="meta">Por {e['autor']} · {e['leido']} de lectura</span>
          <span class="ver">Leer la historia →</span>
        </div>
      </a>"""

def producto_bloque(b, nombre, num="01"):
    return f"""      <div class="producto">
        <span class="num">{num}</span>
        <div>
          <h4>{nombre}</h4>
          <div class="marca">El Bolso de Esperanza · Selección</div>
          <p class="desc">{b['resumen']}</p>
          <div class="precio">≈ {b['precio_aprox']}</div>
          <div class="stars">{estrellas(b.get('rating', 3))}</div>
          <a href="{url_afiliado(b)}" class="btn-affiliate" target="_blank" rel="sponsored nofollow noopener">Ver en Amazon ↗</a>
        </div>
      </div>"""

# ---------------------------------------------------------------- páginas

def generar_home():
    cards = "\n".join(card_bolso(b, href_raiz=0) for b in BOLSOS)
    ultimas = "\n".join(card_blog(e) for e in BLOG[:6])
    ops = "\n".join(card_opinion(o, pref="") for o in OPINIONES[:6])

    html = head_html(
        "El Bolso de Esperanza — Un bolso nuevo cada día",
        "El diario de Esperanza: cada día un bolso y la historia de lo que me pasó llevándolo. Selección verificada con precio, opiniones y enlaces.",
        f"{DOMINIO}/",
    )
    css = css_href(0)
    html = html.replace("{css}", css)
    header = HEADER.format(raiz="", amazon=AMAZON_HEADER)
    html += f"""{UBAR}
{header}
<main>

  <!-- HERO -->
  <section class="hero" id="inicio">
    <span class="silueta s1">👜</span>
    <span class="silueta s2">👛</span>
    <div class="container">
      <span class="chip">Un bolso nuevo cada día</span>
      <h1><span class="l1">Mi vida está</span><span class="l2">en mis bolsos</span></h1>
      <p class="hero-lead">Soy Esperanza. Llevo un bolso diferente cada día desde que empaqué mi vida en una maleta y me fui a Madrid. No es un reto de Instagram: es un diario real donde cada bolso cuenta lo que me pasó ese día.</p>
      <span class="manuscrita">Porque un bolso no es un accesorio — es la memoria de lo que viviste.</span>
      <div class="hero-ctas">
        <a class="btn vino" href="#bolsos">Ver los bolsos ↓</a>
        <a class="btn marfil" href="blog/">Leer el diario</a>
      </div>
    </div>
  </section>

  <!-- BOLSOS -->
  <section class="sec clara" id="bolsos">
    <div class="container">
      <div class="watermark" aria-hidden="true">Bolsos</div>
      <div class="sec-inner">
        <span class="sec-label">01 / La colección</span>
        <h2>Nueve bolsos, <em>nueve historias</em></h2>
        <p class="lead">Cada bolso de este diario tiene su ficha: la historia del día que lo llevé, el precio aproximado, mi nota y las opiniones de las lectoras que se lo compraron.</p>
        <div class="grid-bolsos">
{cards}
        </div>
      </div>
    </div>
  </section>

  <!-- DESTACADO -->
  <section class="destacado">
    <div class="container">
      <p class="frase">“Los bolsos no son caros. Las historias que llevan dentro, sí.”</p>
      <span class="firma">— Esperanza</span>
    </div>
  </section>

  <!-- DIARIO -->
  <section class="sec oscura" id="diario">
    <div class="container">
      <div class="watermark" aria-hidden="true">Diario</div>
      <div class="sec-inner">
        <span class="sec-label">02 / El diario</span>
        <h2>Lo que me pasó <em>con cada bolso</em></h2>
        <p class="lead">Una entrada por bolso. Con fecha, con historia y con la verdad entera — que para eso es un diario.</p>
        <div class="grid-blog">
{ultimas}
        </div>
        <p style="margin-top:30px"><a class="btn vino" href="blog/">Ver el diario completo →</a></p>
      </div>
    </div>
  </section>

  <!-- OPINIONES -->
  <section class="sec clara" id="opiniones">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">03 / Opiniones</span>
        <h2>Lo que dicen <em>las que se lo compraron</em></h2>
        <p class="lead">Opiniones reales de lectoras del diario sobre los bolsos de la colección. Sin filtros y con nota.</p>
        <div class="grid-opiniones">
{ops}
        </div>
        <p style="margin-top:30px"><a class="btn negro" href="opiniones/">Todas las opiniones →</a></p>
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="sec cta-final">
    <div class="container">
      <div class="sec-inner">
        <h2>¿Cuál es <em>tu bolso</em> de este año?</h2>
        <p class="lead" style="color:#F2DFE0">Empieza por el que se parezca a la historia que quieres vivir. Los demás llegan solos.</p>
        <p style="margin-top:26px"><a class="btn" href="{AMAZON_HEADER}" target="_blank" rel="sponsored nofollow noopener">Ver bolsos en Amazon ↗</a></p>
      </div>
    </div>
  </section>

</main>
{FOOTER}
</body>
</html>"""
    escribir("index.html", html)

def generar_blog_index():
    cards = "\n".join(card_blog(e) for e in BLOG)
    html = head_html(
        "El Diario — El Bolso de Esperanza",
        "Todas las entradas del diario de Esperanza: una historia por bolso, con fecha y sin filtros.",
        f"{DOMINIO}/blog/",
    )
    html = html.replace("{css}", css_href(1))
    header = HEADER.format(raiz="../", amazon=AMAZON_HEADER)
    html += f"""{UBAR}
{header}
<main>
  <section class="sec clara" style="padding-top:60px">
    <div class="container">
      <div class="watermark" aria-hidden="true">Diario</div>
      <div class="sec-inner">
        <span class="sec-label">El diario</span>
        <h1 class="sec h2" style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px);line-height:1.05">Lo que me pasó <em style="color:var(--vino);font-style:italic">con cada bolso</em></h1>
        <p class="lead" style="color:#57504C">{len(BLOG)} entradas. Un bolso, una fecha y una historia por cada día del diario.</p>
        <div class="grid-blog">
{cards}
        </div>
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>"""
    escribir("blog/index.html", html)

def cuerpo_post(slug):
    p = POSTS[slug]
    secciones = []
    for h2, parrafos in p["secciones"]:
        ps = "\n".join(f"          <p>{x}</p>" for x in parrafos)
        secciones.append(f'          <h2>{h2}</h2>\n{ps}')
    cuerpo = "\n".join(secciones)
    cita = f'\n          <p class="cita">{p["cita"]}</p>'
    return cuerpo + cita

def generar_post(e, idx_total):
    slug = e["slug"]
    b = BOLSO_POR_SLUG[e["bolso"]]
    p = POSTS[slug]
    prev_e = BLOG[idx_total - 1] if idx_total > 0 else None
    next_e = BLOG[idx_total + 1] if idx_total < len(BLOG) - 1 else None
    ops = "\n".join(card_opinion(o, pref="../../") for o in opiniones_de(b["id"]))
    ops_bloque = ""
    if ops:
        ops_bloque = f"""
  <!-- OPINIONES DEL BOLSO -->
  <section class="sec clara">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Opiniones</span>
        <h2>Lo que dicen las que <em>se lo compraron</em></h2>
        <div class="grid-opiniones">
{ops}
        </div>
      </div>
    </div>
  </section>"""
    nav_prev = f'<a href="../{prev_e["slug"]}/" style="font-family:var(--hand);font-size:19px;color:var(--vino-txt);text-decoration:none">← Día {prev_e["dia"]}</a>' if prev_e else "<span></span>"
    nav_next = f'<a href="../{next_e["slug"]}/" style="font-family:var(--hand);font-size:19px;color:var(--vino-txt);text-decoration:none">Día {next_e["dia"]} →</a>' if next_e else "<span></span>"

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": e["titulo"],
        "description": e["resumen"],
        "datePublished": e["fecha"],
        "author": {"@type": "Person", "name": "Esperanza"},
        "publisher": {"@type": "Organization", "name": "El Bolso de Esperanza"},
        "url": f"{DOMINIO}/blog/{slug}/",
    }, ensure_ascii=False, indent=2)

    html = head_html(
        f"{e['titulo']} — El Bolso de Esperanza",
        e["resumen"],
        f"{DOMINIO}/blog/{slug}/",
        og_type="article",
    )
    html = html.replace("{css}", css_href(2))
    header = HEADER.format(raiz="../../", amazon=AMAZON_HEADER)
    html += f"""{UBAR}
{header}
<script type="application/ld+json">
{jsonld}
</script>
<main>
  <section class="sec oscura" style="padding-bottom:40px">
    <div class="container">
      <div class="watermark" aria-hidden="true">Día {e['dia']:02d}</div>
      <div class="sec-inner">
        <a class="volver" href="../../blog/">← El diario</a>
        <article class="entrada-blog">
          <span class="meta-blog" style="color:var(--tan)">Día {e['dia']} · {fecha_larga(e['fecha'])} · Por {e['autor']} · {e['leido']} de lectura</span>
          <h1>{e['titulo']}</h1>
          <p class="resumen" style="color:#CFC2BE;font-style:italic">{p['resumen']}</p>
          <figure style="margin:28px 0 6px">
            <img src="../../{b['imagen']}" alt="{b['titulo']}" style="border:2px solid var(--marfil);width:100%;max-height:440px;object-fit:cover">
            <figcaption style="font-size:12px;color:var(--gris);margin-top:8px;letter-spacing:1px;text-transform:uppercase">El bolso del día {e['dia']} — ≈ {b['precio_aprox']}</figcaption>
          </figure>
          <div class="cuerpo-blog">
{cuerpo_post(slug)}
          </div>
        </article>
      </div>
    </div>
  </section>

  <!-- PRODUCTO -->
  <section class="ficha">
    <div class="container">
      <span class="sec-label" style="color:var(--vino)">El bolso de esta historia</span>
{producto_bloque(b, NOMBRES[slug])}
      <div style="display:flex;justify-content:space-between;margin-top:30px;flex-wrap:wrap;gap:10px">
        {nav_prev}
        <a href="../../bolso/{b['id']}/" style="font-family:var(--hand);font-size:19px;color:var(--vino-txt);text-decoration:none">Ficha del bolso</a>
        {nav_next}
      </div>
    </div>
  </section>{ops_bloque}
</main>
{FOOTER}
</body>
</html>"""
    escribir(f"blog/{slug}/index.html", html)

def generar_ficha_bolso(b):
    e = ENTRADA_POR_BOLSO.get(b["id"])
    ops = "\n".join(card_opinion(o, pref="../../") for o in opiniones_de(b["id"]))
    ops_bloque = ""
    if ops:
        ops_bloque = f"""
      <div class="grid-opiniones">
{ops}
      </div>"""
    enlace_diario = f'        <p style="margin-top:26px"><a class="btn vino" href="../../blog/{e["slug"]}/">Leer la historia en el diario →</a></p>' if e else ""

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": b["titulo"],
        "description": b["resumen"],
        "image": f"{DOMINIO}/{b['imagen']}",
        "offers": {
            "@type": "Offer",
            "priceCurrency": "EUR",
            "price": b["precio_aprox"].replace("€", "").strip(),
            "url": url_afiliado(b),
            "availability": "https://schema.org/InStock",
        },
    }, ensure_ascii=False, indent=2)

    html = head_html(
        f"{b['titulo']} — Ficha y opiniones — El Bolso de Esperanza",
        f"{b['resumen']} Precio aproximado {b['precio_aprox']}, nota {b.get('rating', 3)}/5 y opiniones de lectoras.",
        f"{DOMINIO}/bolso/{b['id']}/",
        og_type="product",
    )
    html = html.replace("{css}", css_href(2))
    header = HEADER.format(raiz="../../", amazon=AMAZON_HEADER)
    html += f"""{UBAR}
{header}
<script type="application/ld+json">
{jsonld}
</script>
<main>
  <section class="ficha" style="padding-top:48px">
    <div class="container">
      <a class="volver" href="../../">← Los bolsos</a>
      <article>
        <span class="sec-label" style="color:var(--vino);margin-top:18px">Ficha del bolso</span>
        <h1>{b['titulo']}</h1>
        <p class="resumen" style="font-style:italic">{b['resumen']}</p>
        <figure style="margin:30px 0 10px">
          <img src="../../{b['imagen']}" alt="{b['titulo']}" style="border:2px solid var(--tinta);box-shadow:10px 10px 0 var(--marfil2);width:100%;max-height:480px;object-fit:cover">
        </figure>
        <div style="display:flex;gap:26px;flex-wrap:wrap;margin-top:26px;align-items:center">
          <span style="font-family:var(--serif);font-weight:900;font-size:34px">{b['precio_aprox']}</span>
          <span style="color:var(--oro);font-size:18px;letter-spacing:2px">{estrellas(b.get('rating', 3))}</span>
          <a class="btn-affiliate" href="{url_afiliado(b)}" target="_blank" rel="sponsored nofollow noopener">Ver en Amazon ↗</a>
        </div>
{enlace_diario}
      </article>
    </div>
  </section>

  <section class="sec clara">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Opiniones verificadas</span>
        <h2>Lo que dicen <em>las que lo llevaron</em></h2>
{ops_bloque}
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>"""
    escribir(f"bolso/{b['id']}/index.html", html)

def generar_opiniones_index():
    bloques = []
    for b in BOLSOS:
        ops = opiniones_de(b["id"])
        if not ops:
            continue
        cards = "\n".join(card_opinion(o) for o in ops)
        bloque = f"""    <div class="sec-inner" style="margin-top:46px">
      <span class="sec-label">≈ {b['precio_aprox']} · {'★' * b.get('rating', 3)}</span>
      <h2 style="font-size:clamp(24px,3.2vw,34px)">{b['titulo']}</h2>
      <p class="lead">Ficha completa: <a href="../bolso/{b['id']}/" style="color:var(--vino-txt);font-weight:600">ver el bolso →</a></p>
      <div class="grid-opiniones" style="margin-top:22px">
{cards}
      </div>
    </div>"""
        bloques.append(bloque)

    html = head_html(
        "Opiniones — El Bolso de Esperanza",
        "Todas las opiniones de las lectoras sobre los bolsos del diario de Esperanza, ordenadas por bolso.",
        f"{DOMINIO}/opiniones/",
    )
    html = html.replace("{css}", css_href(1))
    header = HEADER.format(raiz="../", amazon=AMAZON_HEADER)
    inner = "\n".join(bloques)
    html += f"""{UBAR}
{header}
<main>
  <section class="sec clara" style="padding-top:60px">
    <div class="container">
      <div class="watermark" aria-hidden="true">Voces</div>
      <div class="sec-inner">
        <span class="sec-label">Opiniones</span>
        <h1 style="font-family:var(--serif);font-weight:700;font-size:clamp(32px,5vw,56px);line-height:1.05">Lo que dicen <em style="color:var(--vino);font-style:italic">las que se los compraron</em></h1>
        <p class="lead" style="color:#57504C">{len(OPINIONES)} opiniones sobre {len([b for b in BOLSOS if opiniones_de(b['id'])])} bolsos del diario. Nota honesta y experiencia real.</p>
{inner}
      </div>
    </div>
  </section>
</main>
{FOOTER}
</body>
</html>"""
    escribir("opiniones/index.html", html)

def generar_sitemap():
    urls = ["", "blog/", "opiniones/"]
    urls += [f"blog/{e['slug']}/" for e in BLOG]
    urls += [f"bolso/{b['id']}/" for b in BOLSOS]
    items = "\n".join(
        f"  <url><loc>{DOMINIO}/{u}</loc><changefreq>weekly</changefreq></url>"
        for u in urls
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n'
    escribir("sitemap.xml", xml)

# ---------------------------------------------------------------- main

def main():
    print("Generando El Bolso de Esperanza — sistema kit72h")
    generar_home()
    generar_blog_index()
    for i, e in enumerate(BLOG):
        generar_post(e, i)
    for b in BOLSOS:
        generar_ficha_bolso(b)
    generar_opiniones_index()
    generar_sitemap()
    total = 1 + 1 + len(BLOG) + len(BOLSOS) + 1
    print(f"\nListo: {total} páginas generadas (home + índice blog + {len(BLOG)} posts + {len(BOLSOS)} fichas + opiniones) + sitemap")

if __name__ == "__main__":
    main()
