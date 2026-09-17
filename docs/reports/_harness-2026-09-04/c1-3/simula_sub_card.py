"""Simulacao em memoria (05/09 tarde, sem reprocess): subunidade de codigo de apoio herdada do CARD.
Variante A: card cujo NOME casa um topico da unidade (>= 50% dos tokens do label/alias).
Variante B: subunidade do(s) material(is) NAO-codigo do MESMO card (irmao principal, maioria).
Resultado nos 4 golds (SO/IA/ES2/TCC, 40 entries codigo-professor): A = 0 '+', 23 '-' (IA: cards "Semana N - ML Aprendizado
Supervisionado" casam `introducao-ao-aprendizado-de-maquina`); B = 0 '+', 2 '-' (IA analise-exploratoria herda dos k-NN).
O SO fork/exec x4 (gold `chamadas-de-sistema` pela regra humana "apoio rotula pelo card") nao muda em nenhuma: o card nao nomeia
o topico e os irmaos tambem estao em `estudo-de-casos`. Uso: python simula_sub_card.py {A|B}"""
import collections
import csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.text.normalize import normalize_match_text  # noqa: E402

REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
VARIANTE = (sys.argv[1] if len(sys.argv) > 1 else "B").upper()


def toks(t):
    return {x for x in normalize_match_text(str(t or "")).split() if len(x) >= 4}


def pred_por_nome_do_card(r, e, units):
    unit = units.get(r["unit_slug"]) or {}
    ct = toks(r["card"])
    hits = []
    for tp in unit.get("topics", []):
        names = [tp.get("label", "")] + list(tp.get("aliases") or [])
        best = max((len(ct & toks(n)) / max(1, len(toks(n))) for n in names if toks(n)), default=0)
        if best >= 0.5:
            hits.append((best, tp.get("slug")))
    hits.sort(reverse=True)
    if len(hits) == 1 or (len(hits) > 1 and hits[0][0] > hits[1][0]):
        return hits[0][1], f"card~{hits[0][1]}"
    return None, "sem-card-match"


def pred_por_irmao_principal(e, by_card):
    card = str(e.get("source_section") or "")
    irmaos = [x for x in by_card[card] if x.get("category") != "codigo-professor" and x.get("file_type") != "code"
              and x.get("computed_unit_slug") == e.get("computed_unit_slug") and x.get("computed_subunit_slug")]
    votos = collections.Counter(x["computed_subunit_slug"] for x in irmaos)
    if votos and (len(votos) == 1 or votos.most_common(2)[0][1] > votos.most_common(2)[1][1]):
        return votos.most_common(1)[0][0], f"irmaos={dict(votos)}"
    return None, f"sem-irmao({dict(votos)})"


tot = collections.Counter()
for sig, repo in REPO.items():
    ents = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    man = {e["id"]: e for e in ents}
    by_card = collections.defaultdict(list)
    for e in ents:
        by_card[str(e.get("source_section") or "")].append(e)
    tax = json.loads((GH / repo / "course" / ".content_taxonomy.json").read_text(encoding="utf-8"))
    units = {u.get("slug"): u for u in tax.get("units", [])}
    with (GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("scorable") == "yes"]
    for r in rows:
        e = man.get(r["entry_id"], {})
        if e.get("category") != "codigo-professor":
            continue
        pred_now = str(e.get("computed_subunit_slug") or "")
        pred_new, how = (pred_por_nome_do_card(r, e, units) if VARIANTE == "A" else pred_por_irmao_principal(e, by_card))
        if pred_new is None:
            pred_new = pred_now
            tot["sem-sinal"] += 1
        alvo = {r["gold_subunit"]} | set(filter(None, (r.get("gold_subunits_extra") or "").split(";")))
        a, b = pred_now in alvo, pred_new in alvo
        v = "+" if (b and not a) else "-" if (a and not b) else "="
        tot[v] += 1
        tot[f"{sig}{v}"] += 1
        if v != "=" or pred_new != pred_now:
            print(f"  {v} {sig:3} {r['entry_id'][:40]:40} card={r['card'][:30]!r:32} agora={pred_now[:26] or '-':26} "
                  f"regra={pred_new[:26] or '-':26} gold={r['gold_subunit'][:24]:24} {how[:60]}")
print(f"variante {VARIANTE} — codigo-professor nos 4 golds:", dict(tot))
