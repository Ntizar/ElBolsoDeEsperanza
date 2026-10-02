#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnóstico: por qué el regex de review-title/body no casa con probe-dp.html."""
import re
from html import unescape

html = open("probe-dp.html", encoding="utf-8").read()
bloques = re.split(r'data-hook="review"', html)[1:]
print("BLOQUES:", len(bloques))

b = bloques[0]
print("HOOKS en bloque:", sorted(set(re.findall(r'data-hook="([^"]+)"', b))))
i = b.find("reviewTitle")
print("IDX reviewTitle:", i)
if i >= 0:
    print("--- contexto titulo (400 chars):")
    print(b[i - 80:i + 320])
# candidatos a cuerpo de review
i = b.find("_review_text")
print("IDX _review_text:", i)
if i >= 0:
    print("--- contexto slot review_text (600 chars):")
    print(b[i - 80:i + 520])
