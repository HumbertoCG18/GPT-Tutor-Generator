"""SARC POSICIONAL: alinhar as AULAS do cronograma aos TOPICOS do plano dentro de cada unidade, por ordem, do mesmo
jeito que `assign_units_positional` ja alinha bloco->unidade. Nao depende de vocabulario (a nomeacao por texto e
circular: medido em 07/09, com a taxonomia limpa o SARC so nomeia o subtopico certo em 21% e no IA em 0%).

Se o alinhamento funciona, ele e o gerador de vocabulario que falta: a aula alinhada ao topico DOA seus tokens como
alias, sem olhar o gold em momento nenhum.

Mede o teto: subunidade predita = topico alinhado ao bloco do material.
  POS   DP monotonico por afinidade de tokens (aula x topico), como o unit_matcher
  ORD   alinhamento proporcional puro (i-esima aula da unidade -> i-esimo topico), sem texto nenhum
Uso: mede_sarc_posicional.py
"""
import collections
import csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.timeline.unit_matcher import _dp_monotonic, _tokens  # noqa: E402

TOT = collections.Counter()
print("SARC POSICIONAL — a aula alinhada ao topico do plano acerta a subunidade?")
print(f"{'':5} {'n':>4} {'POS':>10} {'ORD':>10} {'motor hoje':>12}")
DOACOES = {}
for sig, repo in GOLD.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    units = tax.get("units")
    ulist = list(units.values()) if isinstance(units, dict) else list(units or [])
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = sorted(tl["blocks"], key=lambda b: str(b.get("period_start") or ""))
    curp = root / "course/.glossary_curation.json"
    curados = set()
    if curp.exists():
        for k, v in json.loads(curp.read_text(encoding="utf-8")).items():
            if not k.startswith("_"):
                curados |= {N(s) for s in (v.get("synonyms") or [])}

    def toks_topico(tp):
        # SEM os aliases curados: o gerador nao pode depender do que ele mesmo vai substituir
        parts = [str(tp.get("label") or "")] + [a for a in (tp.get("aliases") or []) if N(a) not in curados]
        return _tokens(" ".join(parts))

    pred_pos, pred_ord, doa = {}, {}, collections.defaultdict(set)
    for u in ulist:
        uslug = str(u.get("slug") or "")
        tops = [t for t in (u.get("topics") or [])]
        bl = [b for b in blocks if b.get("kind") == "class" and str(b.get("unit_slug") or "") == uslug]
        if not tops or not bl:
            continue
        labels = [" ".join(str(s.get("label") or "") for s in (b.get("sessions") or [])) for b in bl]
        tt = [toks_topico(t) for t in tops]
        aff = [[float(len(_tokens(lab) & tt[j])) for j in range(len(tops))] for lab in labels]
        _, assign = _dp_monotonic(aff, len(tops))
        for i, b in enumerate(bl):
            j = assign[i]
            pred_pos[b["id"]] = pred_pos[str(b.get("block_uuid") or "")] = str(tops[j].get("slug") or "")
            k = min(len(tops) - 1, (i * len(tops)) // max(1, len(bl)))
            pred_ord[b["id"]] = pred_ord[str(b.get("block_uuid") or "")] = str(tops[k].get("slug") or "")
            # doacao: tokens da aula que nao estao no topico alinhado
            extra = _tokens(labels[i]) - tt[j]
            if extra:
                doa[(uslug, str(tops[j].get("slug") or ""))] |= extra
    DOACOES[sig] = doa
    c = collections.Counter()
    for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] != "yes" or not r["gold_subunit"]:
            continue
        e = man.get(r["entry_id"])
        if not e:
            continue
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        bid = str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or "")
        c["n"] += 1
        c["pos"] += pred_pos.get(bid, "") in alvo and bool(pred_pos.get(bid))
        c["ord"] += pred_ord.get(bid, "") in alvo and bool(pred_ord.get(bid))
        c["motor"] += str(e.get("computed_subunit_slug") or "") in alvo
    TOT.update(c)
    print(f"{sig:5} {c['n']:4} {c['pos']:4} {100 * c['pos'] / c['n']:4.0f}% {c['ord']:4} {100 * c['ord'] / c['n']:4.0f}% "
          f"{c['motor']:6} {100 * c['motor'] / c['n']:4.0f}%")
print(f"{'TOT':5} {TOT['n']:4} {TOT['pos']:4} {100 * TOT['pos'] / TOT['n']:4.0f}% {TOT['ord']:4} "
      f"{100 * TOT['ord'] / TOT['n']:4.0f}% {TOT['motor']:6} {100 * TOT['motor'] / TOT['n']:4.0f}%")

print("\nVOCABULARIO QUE O ALINHAMENTO DOARIA (amostra por curso):")
for sig, doa in DOACOES.items():
    itens = [(t, sorted(v)[:7]) for (u, t), v in list(doa.items()) if v][:4]
    print(f"  {sig}: " + " · ".join(f"{t[:26]} <- {v}" for t, v in itens))
