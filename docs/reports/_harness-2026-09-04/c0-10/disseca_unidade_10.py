"""C0 item 10 (read-only): os erros de UNIDADE do motor puro +vocab (copias .ablacao), dissecados.
Verdade = unidade do bloco do gold (eval_entry_unit._load_truth, mesma regua do eval_eixos). Por erro: unidade gravada x verdade x
unidade do TEXTO (unit_block_conflict.unit) x unidade do bloco previsto; bloco previsto x gold; flag/metodo; razao gravada; e o que a
CURADA (original) gravou (pino manual? metodo?). Baldes: (a) bloco errado e unidade seguiu o bloco; (b) bloco certo e unidade errada;
(c) bloco flagado/sem bloco e a reconciliacao impos a unidade do bloco sobre o texto."""
import json
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402

REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
COPY = GEN / ".ablacao"
baldes = Counter(); linhas = []
for sig, name in REPOS.items():
    copy, orig = COPY / name, GH / name
    truth = _load_truth(sig)
    ents = {e["id"]: e for e in json.loads((copy / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    ents_o = {e["id"]: e for e in json.loads((orig / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tl = json.loads((copy / "course/.timeline_index.json").read_text(encoding="utf-8")); blocks = tl if isinstance(tl, list) else tl.get("blocks", [])
    unit_of = {}
    for b in blocks:
        for k in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
            unit_of[k] = str(b.get("unit_slug") or "")
    labels = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    gold_block = {}
    for row in (labels if isinstance(labels, list) else labels.values()):
        if isinstance(row, dict):
            gold_block[str(row.get("id") or "")] = str(row.get("true_block_id") or "")
    if not gold_block and isinstance(labels, dict):
        gold_block = {k: (v if isinstance(v, str) else str(v.get("true_block_id", ""))) for k, v in labels.items()}
    preds = load_predictions(copy); preds_o = load_predictions(orig)
    n = ok = 0
    for eid, want in truth.items():
        e = ents.get(eid)
        if not e or not _is_material(e):
            continue
        n += 1
        got = str(e.get("computed_unit_slug") or "")
        if got == want:
            ok += 1; continue
        conf = e.get("unit_block_conflict") or {}
        text_unit = str(conf.get("unit") or "") if isinstance(conf, dict) else ""
        pred = preds.get(eid, {}).get("block_id", ""); g = gold_block.get(eid, "")
        block_unit = unit_of.get(pred, "")
        flag = bool(e.get("temporal_block_flag")); meth = str(e.get("temporal_block_method") or "-")
        reasons = [r for r in (e.get("unit_match_reasons") or []) if "reconcil" in str(r) or "winner" in str(r) or "topic" in str(r)]
        bloco_ok = (pred == g) if g else None
        if bloco_ok is False and got == block_unit:
            b = "a) bloco errado, unidade seguiu o bloco"
        elif bloco_ok and got != want:
            b = "b) bloco certo, unidade errada"
        elif (flag or not pred) and got == block_unit and text_unit and text_unit != got:
            b = "c) bloco flagado/sem, reconciliacao impos o bloco sobre o texto"
        else:
            b = "d) outro"
        baldes[b] += 1
        eo = ents_o.get(eid, {})
        cur = f"curada: unit={str(eo.get('computed_unit_slug') or '')[:28]} manual={'sim' if eo.get('manual_unit_slug') else 'nao'} bloco={preds_o.get(eid, {}).get('block_id', '')} met={eo.get('temporal_block_method')}"
        texto_ok = "texto=VERDADE" if text_unit == want else ("texto=errado" if text_unit else "texto=?")
        linhas.append(f"{sig} {eid[:40]:40} {b[:3]} | gravada={got[:26]:26} verdade={want[:26]:26} {texto_ok:14} | bloco {pred or '-':8}->{g or '?':8} {'ok ' if bloco_ok else 'ERR'} flag={'S' if flag else 'n'} {meth:10} | {cur} | {reasons[:2]}")
    print(f"== {sig}: unidade {ok}/{n}")
print()
for l in linhas: print("  " + l)
print("\nBALDES:", dict(baldes))
print("texto acertaria a verdade em:", sum(1 for l in linhas if "texto=VERDADE" in l), "de", len(linhas))
