#!/usr/bin/env python3
"""Pos-condicao do re-import IA (mundo-42 -> mundo-63).

READ-ONLY. Falha barulhenta. Nomeia os faltantes por source_path.

Roda DEPOIS do re-import incremental dos 21 notebooks do stash. Verifica:
  1. manifest IA tem exatamente 63 entries (42 pre-import + 21 novos).
  2. Cada um dos 21 notebooks byte-unicos novos esta presente (match por source_path).

Os 21 esperados NAO sao hardcoded: derivam do baseline pre-import (backup datado)
vs stash -> stash .ipynb com path-novo E conteudo-novo (md5) contra o baseline.
Reproduz o quadrante "new_path+new_content (SAFE-append)" da auditoria 4-quadrantes.
Assim o script pega: enqueue parcial (importou 20), bug de processamento, e
qualquer divergencia GUI-vs-headless. Exit 0 = PASS, exit 1 = FAIL.

Uso:  python scripts/postcond_reimport_IA.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

# --- alvos (re-aponte BASE se usar outro backup pre-import) ---
REPO = r"C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor"
LIVE = os.path.join(REPO, "manifest.json")
BASE = os.path.join(REPO, "manifest.json.postpoda-42-prereimport.20260623.bak")
STASH = r"C:/Users/Humberto/Desktop/Moodle/inteligencia-artificial"

EXPECT_TOTAL = 63   # mandato: assert len(entries) == 63
EXPECT_NEW = 21     # 21 notebooks byte-unicos novos


def md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(p) -> str:
    return (p or "").replace("\\", "/").lower()


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fail(msg: str) -> None:
    bar = "=" * 64
    print(bar)
    print("POS-CONDICAO RE-IMPORT IA  ==  FALHOU")
    print(bar)
    print(msg)
    print(bar)
    sys.exit(1)


def main() -> None:
    for p in (LIVE, BASE):
        if not os.path.isfile(p):
            fail(f"arquivo ausente: {p}")
    if not os.path.isdir(STASH):
        fail(f"stash ausente: {STASH}")

    base = load(BASE)
    base_entries = base.get("entries", [])
    base_paths = {norm(e.get("source_path")) for e in base_entries}
    base_md5: set[str] = set()
    for e in base_entries:
        rt = e.get("raw_target")
        if not rt:
            continue
        rp = os.path.join(REPO, rt.replace("/", os.sep))
        if os.path.isfile(rp):
            base_md5.add(md5(rp))

    # sanidade: baseline tem de ser o mundo-42
    if len(base_entries) != EXPECT_TOTAL - EXPECT_NEW:
        fail(
            f"baseline tem {len(base_entries)} entries, esperado "
            f"{EXPECT_TOTAL - EXPECT_NEW}. Backup errado -> re-aponte BASE."
        )

    # 21 esperados: stash .ipynb com path-novo E conteudo-novo vs baseline
    expected = []
    for root, _, files in os.walk(STASH):
        for fn in files:
            if not fn.lower().endswith(".ipynb"):
                continue
            p = os.path.join(root, fn)
            if norm(p) in base_paths:
                continue            # ja estava no manifest (skip no import)
            if md5(p) in base_md5:
                continue            # byte-dup de live (nao deve anexar)
            expected.append(p)

    if len(expected) != EXPECT_NEW:
        nomes = "\n  ".join(sorted(os.path.basename(x) for x in expected))
        fail(
            f"baseline produz {len(expected)} notebooks novos esperados, nao "
            f"{EXPECT_NEW}. Stash mudou desde a auditoria. Derivados:\n  {nomes}"
        )

    live = load(LIVE)
    live_entries = live.get("entries", [])
    live_paths = {norm(e.get("source_path")) for e in live_entries}

    missing = [p for p in expected if norm(p) not in live_paths]

    problems = []
    if len(live_entries) != EXPECT_TOTAL:
        problems.append(
            f"CONTAGEM: manifest tem {len(live_entries)} entries, esperado "
            f"{EXPECT_TOTAL} (delta {len(live_entries) - EXPECT_TOTAL:+d})."
        )
    if missing:
        problems.append(f"FALTANDO {len(missing)}/{EXPECT_NEW} notebooks (nao anexados):")
        for p in missing:
            problems.append(f"    - {os.path.basename(p)}")
            problems.append(f"          source_path: {p}")

    if problems:
        fail("\n".join(problems))

    bar = "=" * 64
    print(bar)
    print(
        f"POS-CONDICAO RE-IMPORT IA  ==  OK   "
        f"({len(live_entries)} entries, {EXPECT_NEW}/{EXPECT_NEW} notebooks presentes)"
    )
    print(bar)
    sys.exit(0)


if __name__ == "__main__":
    main()
