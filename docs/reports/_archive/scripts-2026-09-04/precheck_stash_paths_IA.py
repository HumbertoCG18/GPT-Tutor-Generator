#!/usr/bin/env python3
"""Pre-check READ-ONLY (PRE-import): paths distintos dos 21 notebooks do stash.

Motivo: incremental_build:29 deduplica por source_path-string. len(manifest)==63
so vale se os 21 notebooks novos tiverem 21 paths DISTINTOS. Se dois colidirem
(ex.: .ipynb herdando titulo-de-slide), o alvo do postcond (63 hardcoded) fica
errado E o sintoma (manifest fecha < 63) fica indistinguivel de "import pulou um".

Este script NAO importa, NAO altera nada. So:
  - deriva os 21 esperados igual ao postcond (path-novo E content-novo vs baseline);
  - conta distintos sob chave EXATA (a do import) e NORM (lower+slash);
  - se houver colisao sob qualquer chave -> mostra o par/grupo com path + md5
    (path-igual no stash = um notebook pode ter sobrescrito outro silenciosamente);
  - imprime o ALVO correto = 42 + paths_distintos.

Uso:  python scripts/precheck_stash_paths_IA.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict

REPO = r"C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor"
BASE = os.path.join(REPO, "manifest.json.postpoda-42-prereimport.20260623.bak")
STASH = r"C:/Users/Humberto/Desktop/Moodle/inteligencia-artificial"
BASE_COUNT = 42


def md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(p) -> str:
    return (p or "").replace("\\", "/").lower()


def main() -> None:
    if not os.path.isfile(BASE):
        print("baseline ausente:", BASE); sys.exit(1)
    if not os.path.isdir(STASH):
        print("stash ausente:", STASH); sys.exit(1)

    base = json.load(open(BASE, encoding="utf-8"))
    base_entries = base.get("entries", [])
    base_paths = {norm(e.get("source_path")) for e in base_entries}
    base_md5 = set()
    for e in base_entries:
        rt = e.get("raw_target")
        if not rt:
            continue
        rp = os.path.join(REPO, rt.replace("/", os.sep))
        if os.path.isfile(rp):
            base_md5.add(md5(rp))

    # 21 esperados: stash .ipynb path-novo E content-novo vs baseline (== postcond)
    expected = []
    for root, _, files in os.walk(STASH):
        for fn in files:
            if not fn.lower().endswith(".ipynb"):
                continue
            p = os.path.join(root, fn)
            if norm(p) in base_paths:
                continue
            if md5(p) in base_md5:
                continue
            expected.append(p)

    n = len(expected)
    # distintos sob chave EXATA (a do import: source_path string) e NORM (lower)
    by_exact = defaultdict(list)
    by_norm = defaultdict(list)
    for p in expected:
        by_exact[p].append(p)
        by_norm[norm(p)].append(p)
    n_exact = len(by_exact)
    n_norm = len(by_norm)
    col_exact = {k: v for k, v in by_exact.items() if len(v) > 1}
    col_norm = {k: v for k, v in by_norm.items() if len(v) > 1}

    bar = "=" * 70
    print(bar)
    print("PRE-CHECK STASH PATHS IA  (READ-ONLY, PRE-IMPORT)")
    print(bar)
    print(f"notebooks .ipynb esperados (path-novo + content-novo) : {n}")
    print(f"  paths distintos  (chave EXATA = dedup do import)    : {n_exact}")
    print(f"  paths distintos  (NORM lower+slash)                 : {n_norm}")
    print(f"baseline                                              : {BASE_COUNT}")
    print(f"ALVO correto do postcond = {BASE_COUNT} + distintos     : "
          f"{BASE_COUNT + n_exact}  (NORM: {BASE_COUNT + n_norm})")
    print(bar)

    if not col_exact and not col_norm:
        print(f"OK: {n} notebooks, {n_exact} paths distintos. "
              f"Sem colisao -> alvo {BASE_COUNT + n_exact} valido.")
        if n_exact == n:
            print("63 hardcoded confere SE n==21." if n == 21 else
                  f"ATENCAO: n={n} != 21 -> stash mudou desde a auditoria.")
    else:
        if col_exact:
            print(f"COLISAO sob chave EXATA ({len(col_exact)} grupo(s)) "
                  f"-- import NAO tem rede aqui:")
            for k, v in col_exact.items():
                print(f"  key={k}")
                for p in v:
                    print(f"    - {p}   md5={md5(p)}")
        if col_norm and not col_exact:
            print(f"COLISAO so sob NORM ({len(col_norm)} grupo(s)) "
                  f"-- difere so por caixa/slash:")
            for k, v in col_norm.items():
                print(f"  norm={k}")
                for p in v:
                    print(f"    - {p}   md5={md5(p)}")
        print(f"\n-> alvo NAO e 63. Use {BASE_COUNT + n_exact} e inspecione o par acima.")
    print(bar)


if __name__ == "__main__":
    main()
