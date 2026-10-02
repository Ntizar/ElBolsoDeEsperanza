#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descubridor de bolsos reales para El Bolso de Esperanza.
Amplía data/bolsos.json hasta el objetivo (365 = uno por día del año) buscando en
Amazon.es consultas variadas ("bolso bandolera cuero mujer", "mochila cuero", ...),
scrapeando fichas, filtrando por calidad mínima y descargando la imagen oficial.

Filtros de calidad (todos verificados contra HTML real de Amazon.es):
  - título ≥ 25 caracteres con palabra "bolso/bandolera/mochila/cartera"
  - precio ≥ 12 € (evita fundas/accesorios) y ≤ 400 € (evita chollos absurdos)
  - rating ≥ 4.0★ y ≥ 30 valoraciones (prueba social mínima para opinar)

Dedup por ASIN y por similitud de título (normalizado + Trigram Jaccard ≥ 0.45).
Guarda imágenes en assets/real/<id>.jpg.
Uso:  python scripts/bolso-catalogo.py [--objetivo N] [--batch N]
"""
import json
import re
import sys
import time
import unicodedata
import html as htmllib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
F_BOLSOS = RAIZ / "data" / "bolsos.json"
F_FICHAS = RAIZ / "data" / "fichas-amazon.json"
DIR_IMGS = RAIZ / "assets" / "real"

OBJETIVO_DEFECTO = 365
PRECIOMIN, PRECIOMAX = 12.0, 400.0
RATINGMIN, NVALMIN = 4.0, 30
TAG = "nti0c8-21"

RE_ASIN = re.compile(r"data-asin=\"([A-Z0-9]{10})\"")
RE_TITULO = re.compile(r"<title>(.*?)</title>", re.S)
RE_PRECIO = re.compile(r'<span class="a-offscreen">([\d.,]+)\s*€</span>')
RE_RATING = re.compile(r'a-icon-alt">([\d.,]+) de 5')
RE_NVAL_ARIA = re.compile(r'id="acrCustomerReviewText"[^>]*aria-label="([\d.,]+)\s*')
RE_NVAL_PAR = re.compile(r'id="acrCustomerReviewText"[^>]*>\(([\d.,]+)\)')
RE_HIRES = re.compile(r'"hiRes"\s*:\s*"(https://m\.media-amazon\.com/images/I/[^"]+)"')
RE_LANDING = re.compile(r'"landingImageUrl"\s*:\s*"(https://m\.media-amazon\.com/images/I/[^"]+)"')
RE_OPINION = re.compile(r'<span[^>]*data-hook="review-body"[^>]*>(.*?)</span>', re.S)
RE_IMG_ALT = re.compile(r'<img[^>]*alt="([^"]{20,})"')
RE_IMG_ASIN = re.compile(r'/images/I/([A-Za-z0-9+._-]{20,})\.')
RE_PALABRA = re.compile(r"\bbolso|bandolera|mochila|cartera\b", re.I)

CONSULTAS = [
    "bolso tote cuero mujer", "bolso bandolera cuero mujer", "mochila cuero mujer",
    "bolso mano mujer cuero autentico", "bolso hobo mujer", "bolso clutch mujer fiesta",
    "bolso Bandolera peque\u00f1o mujer", "bolso shopper mujer", "bolso satchel mujer",
    "bolso bowl mujer", "bolso imagen cruzado mujer", "cartera grande mujer cuero",
    "bolso piel mujer espana", "bolso trabajo mujer", "bolso viaje mujer",
    "bolso beige mujer", "bolso negro mujer cuero", "bolso marron mujer",
    "bolso rojo mujer", "bolso blanco mujer", "bolso azul mujer",
    "bolso camel mujer", "bolso verde mujer", "bolso burdeos mujer",
    "bolso caballero mujer", "bolso basket mujer", "bolso trenzado mujer",
    "bolso borlas mujer", "bolso hebilla mujer", "bolso estampado mujer",
    "bolso ante mujer", "bolso vernis mujer", "bolso lona mujer",
    "bolso rafia mujer", "bolso mini mujer", "bolso maxi mujer",
    "mochila antirrobo mujer", "mochila cuero blanda mujer", "bandolera hombre lona",
    "bolso bebe cambiador", "bolso gimnasio mujer", "bolso ordenador mujer",
    "bolso cremallera mujer", "bolso asa corta mujer", "bolso compartimentos mujer",
]

PAL_NEGATIVAS = ("funda", "organizador", "kit", "juguete", "muñeca", "mascota", "perro",
                 "tarjetero", "monedero solo", "llavero", "cordón", "correa ", "straps",
                 "niña", "niño", "bautizo", "candy", "piñata", "adorno", "colgante")


def get(url, intentos=3):
    for i in range(intentos):
        try:
            req = Request(url, headers={
                "User-Agent": UA,
                "Accept-Language": "es-ES,es;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            })
            with urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"    red ({i+1}): {e}")
            time.sleep(6 + i * 6)
    return None


def limpiar(t):
    t = re.sub(r"<[^>]+>", " ", t)
    t = htmllib.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", s)


def num_es(s):
    try:
        return float(s.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def num_plain(s):
    try:
        return int(s.replace(".", "").replace(",", ""))
    except ValueError:
        return None


def similitud(a, b):
    na, nb = norm(a), norm(b)
    ga = {na[i:i + 3] for i in range(max(len(na) - 2, 1))}
    gb = {nb[i:i + 3] for i in range(max(len(nb) - 2, 1))}
    inter = len(ga & gb)
    return inter / (len(ga) + len(gb) - inter) if inter else 0.0


def parsear_ficha(html, asin):
    f = {"asin": asin}
    m = RE_TITULO.search(html)
    if not m:
        return None
    titulo = htmllib.unescape(m.group(1)).strip()
    titulo = re.sub(r"\s*:\s*Amazon\.es.*$", "", titulo, flags=re.S).strip()
    f["titulo"] = limpiar(titulo)
    precios = RE_PRECIO.findall(html)
    if not precios:
        return None
    f["precio"] = precios[0].replace("\u00a0", "").strip()
    f["precio_num"] = num_es(precios[0])
    r = RE_RATING.findall(html)
    f["rating"] = num_es(r[0]) if r else None
    m = RE_NVAL_ARIA.search(html) or RE_NVAL_PAR.search(html)
    f["n_valoraciones"] = num_plain(m.group(1)) if m else 0
    m = RE_HIRES.search(html) or RE_LANDING.search(html)
    f["url_imagen"] = m.group(1) if m else None
    ops = [limpiar(b) for b in RE_OPINION.findall(html)[:8]]
    f["opiniones_amazon"] = [o for o in ops if 40 < len(o) < 600]
    return f


def pasa_filtros(f):
    t = f.get("titulo", "")
    if len(t) < 25 or not RE_PALABRA.search(t):
        return "titulo"
    if any(p in t.lower() for p in PAL_NEGATIVAS):
        return "palabra-prohibida"
    p = f.get("precio_num")
    if not p or p < PRECIOMIN or p > PRECIOMAX:
        return "precio"
    r = f.get("rating")
    if r is None or r < RATINGMIN:
        return "rating"
    if (f.get("n_valoraciones") or 0) < NVALMIN:
        return "valoraciones"
    return None


def buscar_asins(consulta, paginas=2):
    vistos = []
    for pag in range(1, paginas + 1):
        url = f"https://www.amazon.es/s?k={quote(consulta)}&i=fashion&page={pag}"
        html = get(url)
        if not html:
            continue
        for m in RE_ASIN.finditer(html):
            a = m.group(1)
            if a and a not in vistos:
                vistos.append(a)
        time.sleep(2.5)
    return vistos


def descargar_imagen(url, destino):
    try:
        req = Request(url, headers={"User-Agent": UA, "Referer": "https://www.amazon.es/"})
        with urlopen(req, timeout=30) as r, open(destino, "wb") as fo:
            fo.write(r.read())
        return destino.stat().st_size > 5000
    except Exception as e:
        print(f"    img: {e}")
        return False


def cargar():
    bolsos = json.loads(F_BOLSOS.read_text(encoding="utf-8"))["bolsos"]
    fichas = json.loads(F_FICHAS.read_text(encoding="utf-8")) if F_FICHAS.exists() else {}
    return bolsos, fichas


def guardar(bolsos, fichas):
    F_BOLSOS.write_text(json.dumps({"meta": {
        "sitio": "El Bolso de Esperanza",
        "descripcion": "Un bolso real para cada día del año. Historias de decisiones, productos reales de Amazon.",
        "afiliado_tag": TAG,
    }, "bolsos": bolsos}, ensure_ascii=False, indent=2), encoding="utf-8")
    F_FICHAS.write_text(json.dumps(fichas, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    DIR_IMGS.mkdir(parents=True, exist_ok=True)
    objetivo = OBJETIVO_DEFECTO
    batch = 6
    if "--objetivo" in sys.argv:
        objetivo = int(sys.argv[sys.argv.index("--objetivo") + 1])
    if "--batch" in sys.argv:
        batch = int(sys.argv[sys.argv.index("--batch") + 1])

    bolsos, fichas = cargar()
    asins_en_repo = {b["asin"] for b in bolsos if b.get("asin")}
    titulos_norm = {norm(b["titulo"]): b["titulo"] for b in bolsos if b.get("titulo")}
    n0 = len(bolsos)
    print(f"Repositorio: {n0} bolsos (objetivo {objetivo}) | fichas cacheadas: {len(fichas)}")

    consultas = CONSULTAS[:]
    n_aceptados = n_duplicados = n_filtrados = 0

    for consulta in consultas:
        if len(bolsos) >= objetivo:
            break
        print(f"\n=== BÚSQUEDA: {consulta}", flush=True)
        asins = buscar_asins(consulta, paginas=1)[:14]
        print(f"    {len(asins)} asins en resultados", flush=True)
        kws = [w for w in norm(consulta).split() if len(w) > 3]

        for asin in asins:
            if len(bolsos) >= objetivo:
                break
            if asin in asins_en_repo:
                n_duplicados += 1
                continue

            f = fichas.get(asin)
            if not f or not f.get("precio"):
                html = get(f"https://www.amazon.es/dp/{asin}")
                time.sleep(2.5)
                if not html:
                    continue
                f = parsear_ficha(html, asin)
                if not f:
                    continue
                fichas[asin] = f

            motivo = pasa_filtros(f)
            if motivo:
                n_filtrados += 1
                continue

            # dedup por título
            dup = next((orig for tn, orig in titulos_norm.items()
                        if similitud(norm(f["titulo"]), tn) >= 0.45), None)
            if dup:
                n_duplicados += 1
                continue

            bid = f"bolso-{asin.lower()}"
            ok_img = False
            if f.get("url_imagen"):
                ok_img = descargar_imagen(f["url_imagen"], DIR_IMGS / f"{bid}.jpg")
                time.sleep(1.5)
            if not ok_img:
                n_filtrados += 1
                continue

            ficha_limpia = {k: f[k] for k in f if k != "url_imagen"}
            fichas[asin] = ficha_limpia
            bolsos.append({
                "id": bid,
                "slug": bid,
                "asin": asin,
                "titulo": f["titulo"],
                "marca": f["titulo"].split()[0],
                "precio": f["precio"],
                "precio_num": f["precio_num"],
                "rating": f.get("rating"),
                "n_valoraciones": f.get("n_valoraciones", 0),
                "imagen": f"assets/real/{bid}.jpg",
                "afiliado": f"https://www.amazon.es/dp/{asin}?tag={TAG}",
                "opiniones_amazon": f.get("opiniones_amazon", []),
                "fecha_scrapeo": time.strftime("%Y-%m-%d"),
                "consigna": None,
                "origen": consulta,
            })
            asins_en_repo.add(asin)
            titulos_norm[norm(f["titulo"])] = f["titulo"]
            n_aceptados += 1
            print(f"    ✓ [{len(bolsos)}/{objetivo}] {f['titulo'][:55]} | {f['precio']} | {f.get('rating')}★ x{f.get('n_valoraciones')}", flush=True)

            guardar(bolsos, fichas)  # guardado en cada aceptación: resistente a cortes

    guardar(bolsos, fichas)
    print(f"\nRESUMEN: +{n_aceptados} nuevos | {n_duplicados} duplicados | {n_filtrados} filtrados")
    print(f"Total repositorio: {len(bolsos)} bolsos (antes {n0}) → data/bolsos.json")


if __name__ == "__main__":
    main()
