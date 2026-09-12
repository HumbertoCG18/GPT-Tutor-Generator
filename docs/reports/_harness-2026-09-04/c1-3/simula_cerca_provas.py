"""Simulacao estatica (read-only): CERCA DE PROVAS. O plano (AVALIACAO) diz quais unidades cada prova cobre; o SARC diz a data da prova.
Bloco-aula antes da P1 so pode ser das unidades da P1; entre P1 e P2, das unidades da P2; depois da P2 (G2 = tudo), livre.
Mede nos snapshots ZERO (e no FR do zero) quantos blocos violam a cerca e o que o gold de unidade diz nos materiais desses blocos.
Uso: simula_cerca_provas.py"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
SNAP = GEN / "docs/reports/_harness-2026-09-04/c1-3/snap_placar/zero"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402

# escopo lido do plano (AVALIACAO), indices 1-based das unidades na ordem do plano
CERCA = {
    "MF": ("Metodos-Formais-Tutor", {"p1": [1, 2], "p2": [3]}),
    "TCC": ("TCC-Tutor", {"p1": [1, 2, 3], "p2": [4]}),
    "ES2": ("Engenharia-Software-2-Tutor", {"p1": [1], "p2": [2, 3]}),
    "FR": ("Fundamentos-de-Redes-Tutor", {"p1": [1, 2, 3], "p2": [4, 5, 6]}),
}
UNI = {"MF", "TCC", "ES2"}
P1_RE = re.compile(r"\b(p1|prova 1)\b")
P2_RE = re.compile(r"\b(p2|prova 2)\b")


def carregar(sig, repo):
    if sig == "FR":
        root = next(d for d in [GEN / ".ablacao/FR-rebuild", *sorted((GEN / ".ablacao/FR-rebuild").glob("*/"))] if (d / "manifest.json").exists())
        man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
        ti = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]
        tax = json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
    else:
        man = json.loads((SNAP / f"{repo}.manifest.json").read_text(encoding="utf-8"))["entries"]
        ti = json.loads((SNAP / f"{repo}.timeline.json").read_text(encoding="utf-8"))["blocks"]
        tax = json.loads((GH / repo / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
    return man, ti, tax


TOT = Counter()
for sig, (repo, cerca) in CERCA.items():
    man, blocks, tax = carregar(sig, repo)
    order = {u["slug"]: i + 1 for i, u in enumerate(tax["units"])}
    blocks = sorted(blocks, key=lambda b: str(b.get("period_start") or ""))
    p1 = p2 = None
    for b in blocks:
        lab = " ".join(str(s.get("label") or "") for s in (b.get("sessions") or []))
        if b.get("kind") == "assessment":
            if p1 is None and P1_RE.search(lab):
                p1 = str(b.get("period_start"))
            elif p2 is None and P2_RE.search(lab):
                p2 = str(b.get("period_start"))
    print(f"\n== {sig}: unidades {len(order)} · P1 {p1} · P2 {p2} · cerca {cerca}")
    gu = _load_truth(sig) if sig in UNI else {}
    by_block = {}
    for e in man:
        by_block.setdefault(str(e.get("temporal_block_id") or ""), []).append(e)
    viol = 0
    for b in blocks:
        if b.get("kind") != "class":
            continue
        d = str(b.get("period_start") or "")
        if p1 and d < p1:
            allowed = set(cerca["p1"]); faixa = "antes P1"
        elif p2 and d < p2:
            allowed = set(cerca["p2"]); faixa = "P1..P2"
        else:
            allowed = set(order.values()); faixa = "depois P2"
        u = str(b.get("unit_slug") or "")
        ui = order.get(u)
        ok = ui in allowed if ui else True
        ents = by_block.get(b["block_uuid"], []) + by_block.get(b["id"], [])
        golds = [(e["id"], gu[e["id"]]) for e in ents if e["id"] in gu]
        g_in = sum(1 for _, g in golds if order.get(g) in allowed)
        g_out = len(golds) - g_in
        g_motor_ok = sum(1 for e in ents if e["id"] in gu and str(e.get("computed_unit_slug") or "") == gu[e["id"]])
        TOT["blocos"] += 1
        TOT["gold entries"] += len(golds); TOT["gold dentro da cerca"] += g_in; TOT["gold FORA da cerca"] += g_out
        if not ok:
            viol += 1; TOT["blocos violando"] += 1
            TOT["gold em bloco violador"] += len(golds)
            TOT["motor certo em bloco violador"] += g_motor_ok
            lab = (b.get("sessions") or [{}])[0].get("label", "")[:40]
            print(f"   VIOLA {b['id']} {d[5:10]} '{lab}' unidade={u[-26:]} (u{ui}) conf={b.get('unit_confidence')} faixa={faixa} permitido={sorted(allowed)} · materiais {len(ents)} · gold: {g_in} dentro, {g_out} fora, motor certo {g_motor_ok}")
        elif g_out:
            lab = (b.get("sessions") or [{}])[0].get("label", "")[:40]
            print(f"   ok    {b['id']} {d[5:10]} '{lab}' u{ui} faixa={faixa} · GOLD FORA DA CERCA em {g_out}/{len(golds)}: {[i[:26] for i, g in golds if order.get(g) not in allowed][:6]}")
    print(f"   blocos-aula violando a cerca: {viol}")
print("\n[TOTAL]", dict(TOT))
