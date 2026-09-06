"""Pergunta do user (06/09): "quantos % um vocab e similar a um nome de material" como indice para a subunidade.
Medicao em memoria, sem LLM: Jaccard de tokens (>= 4 letras, normalizados) entre o NOME do material (title + label do Moodle)
e o label do topico (plano puro) ou label + aliases (vocab compilado). Regua: 4 golds aprovados de subunidade (93 pontuaveis).
Comparar com o scorer do motor (mesma ideia, texto inteiro + pesos): 87/93 com vocab, 30/93 sem."""
import csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402

REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}


def toks(s: str) -> set:
    return {t for t in N(s).split() if len(t) >= 4}


rows = []
for sig, repo in REPO.items():
    man = {e["id"]: e for e in json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = json.loads((GH / repo / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
    units = {u["slug"]: u for u in tax["units"]}
    for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] != "yes":
            continue
        e, u = man.get(r["entry_id"]), units.get(r["unit_slug"])
        if not e or not u:
            continue
        ml = e.get("moodle_label")
        ml = ml.get("text") if isinstance(ml, dict) else ml
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        rows.append((sig, r["entry_id"], f"{e.get('title') or ''} {ml or ''}", u, alvo))

for usar_aliases in (False, True):
    print(f"=== Jaccard tokens(nome do material) x tokens({'label + aliases (vocab LLM)' if usar_aliases else 'label do plano, sem LLM'}) ===")
    for th in (0.2, 0.3, 0.5):
        ok = err = vazio = 0
        for sig, eid, nome, u, alvo in rows:
            best = (0.0, "")
            for t in u["topics"]:
                for c in [t["label"]] + (list(t.get("aliases") or []) if usar_aliases else []):
                    a, b = toks(nome), toks(c)
                    s = len(a & b) / max(1, len(a | b))
                    if s > best[0]:
                        best = (s, t["slug"])
            if best[0] >= th:
                ok, err = (ok + 1, err) if best[1] in alvo else (ok, err + 1)
            else:
                vazio += 1
        print(f"   limiar {th}: atribui {ok + err}/{len(rows)} -> certo {ok} errado {err} · sem atribuicao {vazio}")
