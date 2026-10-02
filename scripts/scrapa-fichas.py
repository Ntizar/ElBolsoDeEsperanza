#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapa fichas y opiniones reales de Amazon para cada bolso del repositorio.
- Fuente de opiniones: la propia ficha /dp/ (bloques data-hook="review" incrustados;
  /product-reviews/ pide login y no sirve).
- Badge de ventas: se intenta "N+ comprados el mes pasado" (si la ficha lo trae).
- Guarda tras CADA bolso (resumible). Sin opiniones previas -> las extrae;
  con --todo re-scrapea aunque ya tenga.
Uso: python scripts/scrapa-fichas.py [--todo]
"""
import json
import re
import sys
import time
import ssl
import urllib.request
from html import unescape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FICHERO = RAIZ / "data" / "bolsos.json"
FICHAS = RAIZ / "data" / "fichas-amazon.json"
MAX_OPS = 8
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def descargar(url, intentos=2):
    for k in range(intentos):
        try:
            peticion = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept-Language": "es-ES,es;q=0.9",
            })
            with urllib.request.urlopen(peticion, timeout=25, context=CTX) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"    intento {k+1} fallo: {type(e).__name__}", flush=True)
            time.sleep(4)
    return None


def extraer_opiniones(html):
    """Devuelve lista de textos (titulo: cuerpo) de los bloques de review de la ficha."""
    resultado = []
    for b in re.split(r'data-hook="review"', html)[1:]:
        mt = re.search(r'data-hook="reviewTitle"[^>]*>([^<]+)<', b)
        titulo = unescape(mt.group(1)).strip() if mt else ""
        cuerpo = ""
        i = b.find("_review_text")
        if i >= 0:
            m = re.search(r'<p[^>]*>(.*?)</p>', b[i:i + 6000], re.S)
            if m:
                cuerpo = re.sub(r"\s+", " ",
                                re.sub(r"<[^>]+>", " ", unescape(m.group(1)))).strip()
        if cuerpo and len(cuerpo) >= 25:
            texto = f"{titulo}: {cuerpo}" if titulo else cuerpo
            resultado.append(texto[:350])
        if len(resultado) >= MAX_OPS:
            break
    return resultado


def extraer_ventas(html):
    m = re.search(r'>([\d.,]+K?\+?)\+?\s*comprados el mes pasado', html)
    if m:
        return m.group(1) + " comprados el mes pasado"
    return None


def main():
    todo = "--todo" in sys.argv
    d = json.loads(FICHERO.read_text(encoding="utf-8"))
    bolsos = d["bolsos"]
    fichas = json.loads(FICHAS.read_text(encoding="utf-8")) if FICHAS.exists() else {}

    pendientes = [b for b in bolsos if todo or not b.get("opiniones_amazon")]
    print(f"Bolsos a scrapear: {len(pendientes)} de {len(bolsos)}", flush=True)

    hechos, con_ops = 0, 0
    for b in pendientes:
        asin, bid = b["asin"], b["id"]
        html = descargar(f"https://www.amazon.es/dp/{asin}")
        if not html or "Enter the characters" in html:
            print(f"  ✗ {bid} ({asin}): bloqueado/404", flush=True)
            time.sleep(3)
            continue
        ops = extraer_opiniones(html)
        ventas = extraer_ventas(html)
        b["opiniones_amazon"] = ops
        if ventas:
            b["ventas_badge"] = ventas
        ficha = fichas.get(asin, {"asin": asin})
        ficha.update({"titulo": b["titulo"], "precio": b["precio"],
                      "precio_num": b.get("precio_num"), "rating": b.get("rating"),
                      "n_valoraciones": b.get("n_valoraciones"),
                      "opiniones_amazon": ops})
        if ventas:
            ficha["ventas_badge"] = ventas
        fichas[asin] = ficha
        # guardar SIEMPRE tras cada bolso
        FICHERO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        FICHAS.write_text(json.dumps(fichas, ensure_ascii=False, indent=2), encoding="utf-8")
        hechos += 1
        con_ops += 1 if ops else 0
        print(f"  ✓ {bid}: {len(ops)} opiniones" + (f" | {ventas}" if ventas else ""),
              flush=True)
        time.sleep(2.5)

    total_con = sum(1 for x in bolsos if x.get("opiniones_amazon"))
    print(f"\nRESUMEN: {hechos} scrapeados ahora, {con_ops} con opiniones; "
          f"total repo con opiniones: {total_con}/{len(bolsos)}", flush=True)


if __name__ == "__main__":
    main()
