#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cron diario de El Bolso de Esperanza: hace crecer el repositorio hacia 365 bolsos.
Cada ejecucion:
  1. bolso-catalogo.py  -> busca bolsos nuevos reales en Amazon (objetivo: +N nuevos)
  2. scrapa-fichas.py   -> opiniones reales para los bolsos que no tengan
  3. generar-sitio.py   -> regenera las 365 paginas con el pool actualizado
  4. git commit + push  -> Pages redeploya solo
Resumible e idempotente: si un paso falla, el siguiente dia lo retoma.
Uso: python scripts/crece-diario.py [nuevos]   (defecto: 6)
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path("C:/Users/d_ant/Projects/ElBolsoDeEsperanza")  # absoluto: el cron copia este script a hermes/scripts/
LOG = RAIZ / "cron-diario.log"
NUEVOS_DEFECTO = 2  # 2/dia: cada tick dura ~90s, holgado bajo el corte de 3 min del cron


def log(msg):
    linea = f"[{date.today().isoformat()}] {msg}"
    print(linea, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linea + "\n")


def paso(nombre, cmd):
    log(f"--- {nombre}: {' '.join(cmd)}")
    r = subprocess.run([sys.executable] + cmd, cwd=RAIZ, capture_output=True, text=True)
    cola = (r.stdout or "").strip().splitlines()
    for l in cola[-4:]:
        log(f"    {l}")
    if r.returncode != 0:
        log(f"!!! {nombre} FALLO (exit {r.returncode}): {(r.stderr or '')[-300:]}")
        return False
    log(f"--- {nombre} OK")
    return True


def main():
    nuevos = int(sys.argv[1]) if len(sys.argv) > 1 else NUEVOS_DEFECTO
    log(f"=== CRECE-DIARIO inicio (objetivo +{nuevos} nuevos) ===")

    paso("1 catalogo", ["scripts/bolso-catalogo.py", "--objetivo", str(nuevos)])
    paso("2 opiniones", ["scripts/scrapa-fichas.py"])

    if not paso("3 generar", ["scripts/generar-sitio.py"]):
        sys.exit(1)

    r = subprocess.run(["git", "status", "--short"], cwd=RAIZ, capture_output=True, text=True)
    cambios = len(r.stdout.strip().splitlines())
    if cambios == 0:
        log("=== sin cambios que publicar ===")
        return
    log(f"--- 4 publicar: {cambios} ficheros cambiados")
    subprocess.run(["git", "add", "-A"], cwd=RAIZ)
    c = subprocess.run(["git", "commit", "-q", "-m",
                        f"cron diario {date.today().isoformat()}: crece repositorio, refresca opiniones y regenera 365 dias"],
                       cwd=RAIZ, capture_output=True, text=True)
    if c.returncode != 0:
        log(f"!!! commit fallo: {(c.stderr or '')[-200:]}")
        sys.exit(1)
    p = subprocess.run(["git", "push", "-q", "origin", "main"], cwd=RAIZ, capture_output=True, text=True)
    if p.returncode != 0:
        log(f"!!! push fallo: {(p.stderr or '')[-200:]}")
        sys.exit(1)
    log("=== CRECE-DIARIO fin: publicado ===")


if __name__ == "__main__":
    main()
