#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sonda: extrae opiniones incrustadas y badge de ventas de un HTML /dp/ guardado."""
import re
import sys
from html import unescape

RUTA = sys.argv[1] if len(sys.argv) > 1 else "probe-dp.html"
html = open(RUTA, encoding="utf-8").read()

bloques = re.split(r'data-hook="review"', html)[1:]
print("BLOQUES_REVIEW:", len(bloques))

utiles = []
for b in bloques:
    mt = re.search(r'data-hook="reviewTitle"[^>]*>([^<]+)<', b)
    titulo = unescape(mt.group(1)).strip() if mt else None
    cuerpo = None
    i = b.find("_review_text")
    if i >= 0:
        m = re.search(r'<p[^>]*>(.*?)</p>', b[i:i + 6000], re.S)
        if m:
            cuerpo = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(m.group(1)))).strip()
    if titulo and cuerpo and len(cuerpo) >= 25:
        utiles.append((titulo[:70], cuerpo[:200]))

print("UTILES:", len(utiles))
for t, c in utiles[:6]:
    print(" *", t)
    print("   ", c)

m = re.search(r'([\d.,]+K?\+?)\+?\s*comprados el mes pasado', html)
print("BADGE_VENTAS:", m.group(1) if m else "NO")
