#!/usr/bin/env python3
"""Scan md5 do corpus IA inteiro -> grupos de colisao de conteudo.

READ-ONLY. Nao altera manifest, nao deduplica, nao commita. So ENUMERA.

Motivo: dedup-por-nome e cego. Achou-se no dado vivo uma dup byte-identica
cujo nome veio do TITULO DO SLIDE, nao do filename -> nomes diferentes,
bytes iguais. So md5 pega. Logo todo denominador (34/40/51) e nao-confiavel
ate o md5 varrer TUDO. Este script varre tudo e mostra os grupos; a decisao
de substituicao fica com o humano DEPOIS de ver.

Hash: do raw_target (copia original armazenada no repo) -> byte-level.
  - file_type url (sem raw_target) -> inhashavel, reportado a parte.
  - raw_target ausente em disco -> inhashavel, reportado a parte (gap nao-silencioso).

Saida (enumerada, nao agregada):
  - contagem de entries vivo + quantos hashaveis / inhashaveis;
  - por grupo de colisao: md5, e cada membro (id, title, file_type, source_path, raw_target);
  - marca KNOWN (3 pares conhecidos) vs NOVO -- advisory; humano confirma.

Uso:  python scripts/dedup_md5_IA.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

REPO = r"C:/Users/Humberto/Documents/GitHub/Inteligencia-Artifical-Tutor"
LIVE = os.path.join(REPO, "manifest.json")

# 3 grupos PDF conhecidos (pares NOVO==NOVO ja mapeados antes). Advisory.
KNOWN_PAIRS = [
    ("minimax-teoria", "minimax"),
    ("lista1", "lista-de-exercicios-i"),
    ("prova-1-2024-02", "prova-1-202402"),
]


def md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def stem(p: str) -> str:
    base = os.path.basename((p or "").replace("\\", "/"))
    return os.path.splitext(base)[0].lower()


def safe(s) -> str:
    """Imprime sem estourar em mojibake/encoding do console."""
    return (s if isinstance(s, str) else str(s)).encode(
        sys.stdout.encoding or "utf-8", "replace"
    ).decode(sys.stdout.encoding or "utf-8", "replace")


def classify(stems: list[str]) -> str:
    sset = [s for s in stems if s]
    for a, b in KNOWN_PAIRS:
        hit_a = any(s == a or a in s for s in sset)
        hit_b = any(s == b or b in s for s in sset)
        if hit_a and hit_b:
            return f"KNOWN ({a} == {b})"
    return "NOVO"


def main() -> None:
    if not os.path.isfile(LIVE):
        print("manifest ausente:", LIVE)
        sys.exit(1)

    m = json.load(open(LIVE, encoding="utf-8"))
    entries = m.get("entries", [])
    bar = "=" * 70

    hashed: dict[int, str] = {}        # idx -> md5
    unhashable: list[tuple[int, str]] = []   # (idx, motivo)
    ext_counter: Counter = Counter()

    for i, e in enumerate(entries):
        rt = e.get("raw_target")
        sp = e.get("source_path")
        path = None
        if rt:
            cand = os.path.join(REPO, rt.replace("/", os.sep))
            if os.path.isfile(cand):
                path = cand
        if path is None and sp and os.path.isfile(sp):
            path = sp  # fallback: source local existente
        if path is None:
            reason = "url/sem-bytes" if (e.get("file_type") == "url" or not rt) else "raw_target-ausente-em-disco"
            unhashable.append((i, reason))
            continue
        ext_counter[os.path.splitext(path)[1].lower()] += 1
        hashed[i] = md5(path)

    # agrupa por md5
    groups: dict[str, list[int]] = defaultdict(list)
    for i, h in hashed.items():
        groups[h].append(i)
    collisions = {h: idxs for h, idxs in groups.items() if len(idxs) > 1}

    print(bar)
    print("SCAN MD5 CORPUS IA  (READ-ONLY)")
    print(bar)
    print(f"entries no manifest vivo : {len(entries)}")
    print(f"  hashaveis (bytes)      : {len(hashed)}")
    print(f"  inhashaveis            : {len(unhashable)}")
    print(f"  ext dos hashaveis      : {dict(ext_counter)}")
    print(f"grupos de colisao (>1)   : {len(collisions)}")
    n_known = sum(1 for idxs in collisions.values()
                  if classify([stem(entries[i].get('raw_target') or entries[i].get('source_path')) for i in idxs]).startswith("KNOWN"))
    print(f"  KNOWN (dos 3 pares)    : {n_known}")
    print(f"  NOVO                   : {len(collisions) - n_known}")
    print(bar)

    if not collisions:
        print("nenhuma colisao de conteudo. (mundo-42)")
    for gi, (h, idxs) in enumerate(sorted(collisions.items(), key=lambda kv: -len(kv[1])), 1):
        stems = [stem(entries[i].get("raw_target") or entries[i].get("source_path")) for i in idxs]
        kind = classify(stems)
        print(f"\n[grupo {gi}]  {kind}   md5={h}   ({len(idxs)} membros)")
        for i in idxs:
            e = entries[i]
            print(f"    - id        : {safe(e.get('id'))}")
            print(f"      title     : {safe(e.get('title'))}")
            print(f"      file_type : {e.get('file_type')}")
            print(f"      source    : {safe(e.get('source_path'))}")
            print(f"      raw_target: {safe(e.get('raw_target'))}")

    if unhashable:
        print(f"\n{bar}\nINHASHAVEIS ({len(unhashable)}) -- nao entram na deteccao de dup:")
        for i, reason in unhashable:
            e = entries[i]
            print(f"    - [{reason}] {safe(e.get('id'))}  ({e.get('file_type')})  {safe(e.get('source_path'))}")

    print(f"\n{bar}")
    nb_h = ext_counter.get(".ipynb", 0)
    print(f"NOTA: scan sobre manifest vivo = {len(entries)} entries "
          f"({nb_h} ipynb hashaveis).")
    if len(entries) < 63:
        print("  < 63 -> PRE-reimport: os 21 notebooks novos ainda NAO entraram;")
        print("  dups internas aos 21 ou 21-vs-42 so aparecem POS-import.")
    else:
        print("  >= 63 -> POS-reimport: notebooks incluidos no scan.")
    print(bar)


if __name__ == "__main__":
    main()
