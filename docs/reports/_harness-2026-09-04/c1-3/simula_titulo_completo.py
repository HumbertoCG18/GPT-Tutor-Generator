"""O NOME do material como sinal de subunidade, com o vocabulario COMPLETO (rotulo + aliases), aplicado por cima do
estado gravado nos 6 golds (0 chamadas).

Hoje `resolver_apply._subtopico_nomeado_no_titulo` so consulta as PARTES de rotulo (`_partes_de_rotulo`), que passam por
filtros duros (parte nao pode nomear mais nada no curso, df <= teto). Se o titulo traz o ROTULO INTEIRO do subtopico certo
("pagina com videos sobre Curvas Parametricas"), a regra nao dispara.

Variantes (titulo = entry.title + label do Moodle):
  T1  titulo nomeia exatamente UM subtopico Y da unidade e NAO nomeia o vencedor -> Y
  T1c T1 so quando a decisao NAO e confiante (score < 10, faixa onde a precisao cai de 92% para ~67%)
  T1v T1 so quando o vencedor atual NAO esta nomeado no titulo E o titulo nomeia Y por frase de >= 2 tokens especificos
  T0  so mede o TETO: em quantos erros o titulo nomeia o gold
Uso: simula_titulo_completo.py
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

SCORE_RE = re.compile(r"(?:winner_)?score=([0-9.]+)")


def frase_no(texto_norm: str, frase: str) -> bool:
    n = N(frase or "")
    return bool(n) and re.search(r"(^|\s)" + re.escape(n) + r"(\s|$)", texto_norm) is not None


def especificos(frase: str, generic: set) -> set:
    return {t for t in N(frase).split() if len(t) >= 4 and t not in generic
            and not any(t.startswith(g) for g in MOTOR_GENERIC_STEMS)}


CASOS = []
for sig, repo in REPOS.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    por_unidade = collections.defaultdict(list)
    for t in eng._iter_content_taxonomy_topics(tax):
        por_unidade[t["unit_slug"]].append(t)
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    for r in rows:
        e = man.get(r["entry_id"])
        if not e:
            continue
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        pred = str(e.get("computed_subunit_slug") or "")
        unit = str(e.get("computed_unit_slug") or "")
        raz = " ".join(str(x) for x in (e.get("subunit_match_reasons") or []))
        m = SCORE_RE.search(raz)
        score = float(m.group(1)) if m else 0.0
        tit = N(f"{e.get('title') or ''} {moodle_label_text(e) or ''}")
        # quem o titulo nomeia, na unidade
        nomeados, nomeados2 = [], []
        for t in por_unidade.get(unit, []):
            gen = set(t.get("generic_tokens") or [])
            frases = [t.get("topic_label") or ""] + list(t.get("aliases") or [])
            hit = [f for f in frases if f and frase_no(tit, f)]
            if hit:
                nomeados.append(t["topic_slug"])
                if any(len(especificos(f, gen)) >= 2 for f in hit):
                    nomeados2.append(t["topic_slug"])
        CASOS.append(dict(sig=sig, id=r["entry_id"], alvo=alvo, pred=pred, score=score, unit=unit, tit=tit,
                          nomeados=nomeados, nomeados2=nomeados2))

base = sum(1 for c in CASOS if c["pred"] in c["alvo"])
erros = [c for c in CASOS if c["pred"] not in c["alvo"]]
print(f"base {base}/{len(CASOS)} · erros {len(erros)}\n")

print("T0 TETO — o titulo nomeia o gold, em quantos erros?")
teto = [c for c in erros if any(g and g in c["nomeados"] for g in c["alvo"])]
print(f"   titulo nomeia o gold em {len(teto)}/{len(erros)} erros: " + ", ".join(f"{c['sig']}/{c['id'][:26]}" for c in teto))
sozinho = [c for c in teto if c["pred"] not in c["nomeados"]]
print(f"   destes, o titulo NAO nomeia o vencedor atual: {len(sozinho)}\n")


def aplica(c, modo):
    pred, nom = c["pred"], (c["nomeados2"] if modo == "T1v" else c["nomeados"])
    cand = [y for y in nom if y != pred]
    if len(set(cand)) != 1 or pred in c["nomeados"]:
        return pred
    if modo == "T1c" and c["score"] >= 10:
        return pred
    return cand[0]


print(f"{'modo':5} {'certos':>7} {'delta':>6} {'ganha':>6} {'perde':>6} {'muda':>6}")
for modo in ["T1", "T1c", "T1v"]:
    ok = ganha = perde = muda = 0
    det = []
    for c in CASOS:
        novo = aplica(c, modo)
        if novo != c["pred"]:
            muda += 1
            g = novo in c["alvo"] and c["pred"] not in c["alvo"]
            p = c["pred"] in c["alvo"] and novo not in c["alvo"]
            ganha += g
            perde += p
            det.append((("+" if g else "-" if p else "~"), c["sig"], c["id"][:34], c["pred"][-24:], novo[-24:], list(c["alvo"])[0][-24:]))
        ok += novo in c["alvo"]
    print(f"{modo:5} {ok:7} {ok - base:+6} {ganha:6} {perde:6} {muda:6}")
    for d in sorted(det):
        print(f"   {d[0]} {d[1]:4} {d[2]:34} {d[3]:24} -> {d[4]:24} gold={d[5]}")
