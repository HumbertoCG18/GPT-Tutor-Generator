"""Censo código->bloco: compara primary_block_id (Gemini) x computed_block_id
(funil + consenso band-gated do D1) num repo gerado real. Eval-gate do D1.

Uso: python scripts/eval_code_block_census.py <caminho-do-repo-gerado>
Lê manifest.json + code_curation.json. Não escreve nada.

Saída: tabela por entry de código + sumário das mudanças, separadas em:
 - carded: tinha card -> funil/card autoritativo (mudança = melhora esperada)
 - faixa do meio (sem card, band != baixa): REVISAR no ground truth
 - fraca (sem card, band baixa): o consenso band-gated deveria ter adotado o Gemini
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

CODE_TYPES = {"code", "zip"}


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python scripts/eval_code_block_census.py <repo-gerado>")
        return 2
    repo = Path(sys.argv[1])
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    cur_path = repo / "code_curation.json"
    curation = json.loads(cur_path.read_text(encoding="utf-8")) if cur_path.exists() else {"entries": {}}
    cur_entries = curation.get("entries", {})

    rows = []
    for e in manifest.get("entries", []):
        if str(e.get("file_type") or "") not in CODE_TYPES:
            continue
        eid = str(e.get("id") or "")
        summary = (cur_entries.get(eid) or {}).get("summary") or {}
        rows.append({
            "id": eid,
            "carded": bool(str(e.get("source_section") or "").strip()),
            "band": str(e.get("computed_block_band") or ""),
            "gemini": str(summary.get("primary_block_id") or ""),
            "computed": str(e.get("computed_block_id") or ""),
        })
        rows[-1]["changed"] = rows[-1]["gemini"] != rows[-1]["computed"]

    print(f"=== Censo codigo->bloco ({len(rows)} entries) ===")
    print(f"{'id':28} {'card':5} {'band':6} {'gemini':10} {'computed':10} {'mudou'}")
    for r in rows:
        print(f"{r['id'][:28]:28} {str(r['carded']):5} {r['band']:6} "
              f"{r['gemini'][:10]:10} {r['computed'][:10]:10} {'SIM' if r['changed'] else ''}")

    changed = [r for r in rows if r["changed"]]
    carded = [r for r in changed if r["carded"]]
    mid = [r for r in changed if not r["carded"] and r["band"] != "baixa"]
    weak = [r for r in changed if not r["carded"] and r["band"] == "baixa"]
    print()
    print(f"Mudaram (gemini != computed): {len(changed)}/{len(rows)}")
    print(f"  - carded (funil/card autoritativo; conferir se melhora): {len(carded)}")
    print(f"  - faixa do meio (sem card, band!=baixa — REVISAR ground truth): {len(mid)}")
    print(f"  - fraca (sem card, band baixa — consenso deveria ter adotado Gemini): {len(weak)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
