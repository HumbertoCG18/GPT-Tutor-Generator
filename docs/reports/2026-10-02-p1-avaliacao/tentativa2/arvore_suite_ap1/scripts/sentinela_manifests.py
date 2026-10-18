"""Sentinela de gate: manifest atual vs git HEAD, campo a campo, nos tutores.

    python scripts/sentinela_manifests.py

Promovido do scratchpad em 01/09 (rodado 15+ vezes na campanha)."""
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GH = Path(r"C:\Users\Humberto\Documents\GitHub")
REPOS = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor",
         "Engenharia-Software-2-Tutor", "TCC-Tutor", "Computacao-Grafica-Tutor",
         "Laboratorio-de-Redes-Tutor", "Fundamentos-de-Redes-Tutor"]
CAMPOS = ["temporal_block_id", "temporal_block_method", "computed_block_id", "computed_block_method",
          "computed_unit_slug", "computed_subunit_slug", "unit_match_confidence",
          "subunit_match_confidence", "subunit_match_reasons", "auto_tags", "coverage_units", "duplicate_of",
          "revisar"]

total = 0
for repo in REPOS:
    head = json.loads(subprocess.run(
        ["git", "show", "HEAD:manifest.json"], cwd=GH / repo,
        capture_output=True, text=True, encoding="utf-8").stdout)
    atual = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))
    h = {str(e.get("id")): e for e in head["entries"]}
    a = {str(e.get("id")): e for e in atual["entries"]}
    mudancas = []
    for eid in sorted(set(h) | set(a)):
        eh, ea = h.get(eid, {}), a.get(eid, {})
        for c in CAMPOS:
            if eh.get(c) != ea.get(c):
                mudancas.append((eid, c, eh.get(c), ea.get(c)))
    print(f"{repo}: {len(mudancas)} campos mudados")
    for eid, c, antes, depois in mudancas:
        antes_s = json.dumps(antes, ensure_ascii=False)
        depois_s = json.dumps(depois, ensure_ascii=False)
        if len(antes_s) > 90:
            antes_s = antes_s[:90] + "..."
        if len(depois_s) > 90:
            depois_s = depois_s[:90] + "..."
        print(f"   {eid[:50]} .{c}: {antes_s} -> {depois_s}")
    total += len(mudancas)
print(f"\nTOTAL: {total} campos")
