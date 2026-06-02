import json
import re
import glob
import unicodedata
from collections import Counter, defaultdict


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()


paths = glob.glob("C:/Users/Humberto/Documents/GitHub/*-Tutor/course/.timeline_index.json")

ASSESSMENT = {"p1", "p2", "p3", "p4", "pf", "prova", "provas", "avaliacao", "exame", "recuperacao", "substitutiva", "teste"}
REVIEW = {"revisao", "revisoes", "review"}
NON_ACAD = {
    "feriado", "recesso", "suspensao", "suspenso", "suspensa",
    "evento", "semana", "simposio", "congresso", "workshop", "jornada",
    "greve", "paralisacao", "assembleia",
    "devolucao", "devolutiva", "encerramento", "seminario", "seminarios",
    "substituicao", "reposicao",
    "ferias", "carnaval", "natal", "pascoa", "corpus", "tiradentes", "independencia", "finados", "consciencia", "aparecida",
    "planejamento", "reuniao", "conselho",
    "atendimento", "duvidas", "reserva",
    "oficina", "lancamento", "divulgacao",
}

per = {}
for p in paths:
    parts = re.split(r"[\\/]+", p)
    course = parts[-3]
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    blocks = d.get("blocks", [])
    kinds = Counter()
    samples = defaultdict(list)
    for b in blocks:
        tt = norm(b.get("topic_text", ""))
        toks = set(tt.split()) if tt else set()
        unit = bool(b.get("unit_slug"))
        topic = bool(b.get("primary_topic_label"))
        if toks & ASSESSMENT:
            k = "assessment"
        elif toks & REVIEW:
            k = "review"
        elif toks & NON_ACAD:
            k = "non_academic"
        elif not tt and not unit:
            k = "unknown_gap"
        elif unit and topic:
            k = "ok"
        elif unit and not topic:
            k = "missing_topic"
        else:
            k = "missing_unit"
        kinds[k] += 1
        samples[k].append((b.get("id"), b.get("period_label"), tt[:70]))
    per[course] = {"total": len(blocks), "kinds": dict(kinds), "samples": samples}

for c, info in per.items():
    print("===", c, "(", info["total"], "blocos )")
    for k, n in sorted(info["kinds"].items(), key=lambda x: -x[1]):
        print("  %3d  %s" % (n, k))
    for k in ("missing_unit", "missing_topic", "unknown_gap", "non_academic", "assessment", "review"):
        if info["samples"].get(k):
            print("  --", k, "--")
            for bid, lab, tt in info["samples"][k][:8]:
                print("     ", bid, " ", lab, " ", repr(tt))
    print()
