"""C0 11b passo 1 (read-only, 8 originais): a via "membro de serie vota MESMO confiante" (anchor_engine.py:269) paga?
Para cada entry com metodo `llm` que e membro de serie same-theme, recomputa a decisao do motor SEM voter (AnchorEngine(voter=None),
mesmo contexto/markdown do produto) e compara: bloco do motor x voto x gold; flag do motor (se flagada, votaria de qualquer jeito)."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_ground_truth import load_predictions  # noqa: E402
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.routing.motor.anchor_engine import AnchorEngine  # noqa: E402
from src.builder.routing.motor.card_stream import card_windows  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.motor.llm_vote import detect_same_theme_series  # noqa: E402

REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "LR": "Laboratorio-de-Redes-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}
tot = Counter()
for c, name in REPOS.items():
    repo = GH / name
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    entries = man["entries"]
    series = detect_same_theme_series(entries)
    gold = {}
    gp = GEN / "docs/reports" / f"ground_truth_{c}.csv"
    if gp.exists():
        with gp.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("scorable", "yes") == "yes" and r.get("true_block_id"):
                    gold[r["id"].strip()] = r["true_block_id"].strip()
    alvo = [e for e in entries if str(e.get("temporal_block_method") or "") == "llm" and e["id"] in series]
    if not alvo:
        continue
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    ctx._card_windows_cache = card_windows(entries, ctx)
    to_id = {}
    for b in ctx.blocks:
        for k in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
            to_id[k] = str(b.get("id"))
    preds = load_predictions(repo)
    eng = AnchorEngine(voter=None, series_ids=series)
    print(f"== {c}: membros de serie com voto: {len(alvo)} (series {len(series)})")
    for e in alvo:
        md = _entry_markdown_text_for_file_map(repo, e) or ""
        d = eng.resolve(e, ctx, md)
        motor = to_id.get(str(d.block_ref), str(d.block_ref)) if d and d.block_ref else "-"
        flag = d.flag if d else None
        voto = preds.get(e["id"], {}).get("block_id", "")
        g = gold.get(e["id"])
        via = "flagada->votaria" if (d is None or flag) else "CONFIANTE->voto so pela serie"
        tot[via] += 1
        if via.startswith("CONFIANTE"):
            tot["confiante: motor==voto"] += (motor == voto)
            if g is not None:
                tot["confiante c/ gold"] += 1; tot["confiante motor ok"] += (motor == g); tot["confiante voto ok"] += (voto == g)
        print(f"   {e['id'][:38]:38} {via:30} motor={motor:9} band={getattr(d, 'band', '-'):5} voto={voto:9} gold={g or '-':9} "
              f"{'' if g is None else ('motor_ok ' if motor == g else 'MOTOR_ERR ') + ('voto_ok' if voto == g else 'VOTO_ERR')}")
print("TOTAL:", dict(tot))
