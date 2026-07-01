"""Censo subunit/bands: distribuicao de subunidade + calibracao de band num
repo gerado real. Eval-gate do P0.2 (subunit restrita a unidade).

Uso: python scripts/eval_subunit_census.py <caminho-do-repo-gerado>
Le manifest.json + course/.content_taxonomy.json. Nao escreve nada.

Saida: tabela por material + sumario (cobertura, calibracao de band,
distribuicao de subunit) + FLAGS:
 - subunit SEM unidade (orfa)
 - subunit FORA da unidade (taxonomia aponta outra unidade) = viola P0.2
 - subunit DESCONHECIDO (nao esta na taxonomia gerada = stale)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_UNIT = "unit:"
_SUBUNIT = "subunit:"
_BLOCO = "bloco:"


def _tag(entry: dict, prefix: str) -> str:
    for t in entry.get("auto_tags") or []:
        t = str(t)
        if t.startswith(prefix):
            return t[len(prefix):]
    return ""


def _is_material(e: dict) -> bool:
    # Mesma definicao de "material" do scripts/reprocess_assignments._coverage.
    return str(e.get("file_type") or "") == "pdf" or bool(e.get("category"))


def _load_subunit_unit_map(repo: Path):
    """subunit_slug -> set(unit_slug) pela taxonomia gerada. None se ausente.
    Set (nao escalar): um topico pode aparecer em +1 unidade no plano; mismatch
    so quando a unidade da entry NAO esta entre as donas do slug."""
    path = repo / "course" / ".content_taxonomy.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict = {}
    for unit in data.get("units", []) or []:
        uslug = str(unit.get("slug") or "")
        for topic in unit.get("topics", []) or []:
            tslug = str(topic.get("slug") or "")
            if tslug:
                mapping.setdefault(tslug, set()).add(str(topic.get("unit_slug") or uslug))
    return mapping


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print("uso: python scripts/eval_subunit_census.py <repo-gerado>")
        return 2
    repo = Path(sys.argv[1])
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    sub2unit = _load_subunit_unit_map(repo)

    rows = []
    for e in manifest.get("entries", []):
        if not _is_material(e):
            continue
        rows.append({
            "id": str(e.get("id") or ""),
            "unit": _tag(e, _UNIT) or str(e.get("computed_unit_slug") or ""),
            "subunit": _tag(e, _SUBUNIT),
            "bloco": _tag(e, _BLOCO) or str(e.get("computed_block_id") or ""),
            "band": str(e.get("computed_block_band") or ""),
        })

    print(f"=== Censo subunit/bands ({len(rows)} materiais) ===")
    print(f"{'id':28} {'unidade':22} {'subunidade':26} {'bloco':10} {'band'}")
    for r in rows:
        print(f"{r['id'][:28]:28} {r['unit'][:22]:22} {r['subunit'][:26]:26} "
              f"{r['bloco'][:10]:10} {r['band']}")

    n = len(rows)
    with_block = sum(1 for r in rows if r["bloco"])
    with_unit = sum(1 for r in rows if r["unit"])
    with_sub = sum(1 for r in rows if r["subunit"])
    print()
    print(f"Cobertura: bloco {with_block}/{n}  unidade {with_unit}/{n}  subunidade {with_sub}/{n}")

    bands = Counter(r["band"] or "(sem)" for r in rows if r["bloco"])
    print("Calibracao de band (com bloco):")
    for b in ("alta", "media", "baixa", "(sem)"):
        if bands.get(b):
            print(f"  {b:8} {bands[b]}")

    subdist = Counter(r["subunit"] for r in rows if r["subunit"])
    print(f"Distribuicao de subunidade ({len(subdist)} distintas; sem subunit: {n - with_sub}):")
    for slug, c in subdist.most_common():
        print(f"  {c:>3}  {slug}")

    print("\nFLAGS:")
    orphan_sub = [r for r in rows if r["subunit"] and not r["unit"]]
    print(f"  subunit SEM unidade (orfa): {len(orphan_sub)}")
    for r in orphan_sub:
        print(f"     {r['id']}  subunit={r['subunit']}")

    if sub2unit is None:
        print("  (sem course/.content_taxonomy.json -> pulei checagem subunit<->unidade)")
        return 0

    mismatch = []
    unknown = []
    for r in rows:
        if not r["subunit"]:
            continue
        owners = sub2unit.get(r["subunit"])
        if owners is None:
            unknown.append(r)
        elif r["unit"] and r["unit"] not in owners:
            mismatch.append((r, owners))
    print(f"  subunit FORA da unidade (viola P0.2): {len(mismatch)}")
    for r, owners in mismatch:
        print(f"     {r['id']}  subunit={r['subunit']} -> taxonomia={sorted(owners)}, entry={r['unit']}")
    print(f"  subunit DESCONHECIDO (stale, fora da taxonomia): {len(unknown)}")
    for r in unknown:
        print(f"     {r['id']}  subunit={r['subunit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
