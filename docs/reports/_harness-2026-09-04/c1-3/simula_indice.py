"""MATERIAL-INDICE: quando o corpo e uma LISTA de itens filhos, a soma do corpo elege um filho e o assunto real esta no
cabecalho. Medido nos 6 golds por cima do estado gravado (0 chamadas).

Exemplo real (CG): "Pagina com Videos sobre Curvas Parametricas", secao "7 - Curvas Parametricas", corpo = 12 links de
YouTube (Bezier, Hermite, Casteljau...). O motor grava `hermite` (o filho que somou mais); o gold e o subtopico da pagina.

Gate INDICE (sem gold, sem curso): o corpo nomeia K+ subtopicos distintos da unidade com score >= 1.
Sinal do cabecalho, criterio de tokens especificos (o mesmo de `_secao_nomeia_subtopico`, ja no motor):
  SEC   a secao do Moodle nomeia exatamente um subtopico Y
  TIT   o titulo + label do Moodle + H1 do markdown nomeiam exatamente um Y
Variantes: sinal sozinho (sem gate) x com gate INDICE, e com/sem exigir que o cabecalho NAO nomeie o vencedor.
Uso: simula_indice.py
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
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.resolver_apply import _secao_nomeia_subtopico  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

H1_RE = re.compile(r"^#\s+(.+)$", re.M)


def nomeia_um(texto: str, topicos: list) -> str:
    """Como `_secao_nomeia_subtopico`, mas para um texto qualquer de cabecalho."""
    fake = {"source_section": texto}
    return _secao_nomeia_subtopico(fake, topicos, MOTOR_GENERIC_STEMS)


CASOS = []
for sig, repo in REPOS.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    por_unidade = collections.defaultdict(list)
    for t in eng._iter_content_taxonomy_topics(tax):
        por_unidade[t["unit_slug"]].append(t)
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    for r in rows:
        e = man.get(r["entry_id"])
        if not e:
            continue
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        rec = (code_cur.get("entries") or {}).get(str(e.get("id") or "")) or {}
        resumo = code_curation_signal_text(rec) if rec else ""
        t = f"{md}\n\n{resumo}" if md and resumo else (md or resumo)
        unit = str(e.get("computed_unit_slug") or "")
        tops = por_unidade.get(unit, [])
        sinais = eng._collect_entry_unit_signals(e, t)
        scores = {tp["topic_slug"]: eng._score_entry_against_taxonomy_topic(sinais, tp) for tp in tops}
        h1 = " ".join(H1_RE.findall(md)[:2])
        cab_tit = f"{e.get('title') or ''} {moodle_label_text(e) or ''} {h1}"
        CASOS.append(dict(
            sig=sig, id=r["entry_id"], unit=unit,
            alvo={r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";"))),
            pred=str(e.get("computed_subunit_slug") or ""),
            k=sum(1 for v in scores.values() if v >= 1.0),
            links=len(re.findall(r"\]\(http", md)),
            sec=nomeia_um(str(e.get("source_section") or ""), tops),
            tit=nomeia_um(cab_tit, tops),
            frases={tp["topic_slug"]: [N(x) for x in [tp.get("topic_label") or ""] + list(tp.get("aliases") or []) if N(x)] for tp in tops},
            cab=N(f"{e.get('source_section') or ''} {cab_tit}"),
        ))

base = sum(1 for c in CASOS if c["pred"] in c["alvo"])
print(f"base {base}/{len(CASOS)} · erros {len(CASOS) - base}")
idx = [c for c in CASOS if c["k"] >= 3]
print(f"gate INDICE (k>=3 subtopicos com score>=1): {len(idx)} materiais, {sum(1 for c in idx if c['pred'] not in c['alvo'])} erros dentro\n")

print("TETO: o cabecalho nomeia o gold, nos 38 erros")
for nome, chave in [("secao", "sec"), ("titulo+h1", "tit"), ("qualquer", None)]:
    n = sum(1 for c in CASOS if c["pred"] not in c["alvo"] and
            ((c[chave] in c["alvo"] and c[chave]) if chave else ((c["sec"] in c["alvo"] and c["sec"]) or (c["tit"] in c["alvo"] and c["tit"]))))
    print(f"   {nome:12} alcanca {n}/38")
print()


def aplica(c, fonte, gate, exige_nao_vencedor):
    y = c["sec"] if fonte == "SEC" else c["tit"] if fonte == "TIT" else (c["sec"] or c["tit"])
    if not y or y == c["pred"]:
        return c["pred"]
    if gate and c["k"] < 3:
        return c["pred"]
    if exige_nao_vencedor and any(re.search(r"(^|\s)" + re.escape(f) + r"(\s|$)", c["cab"]) for f in c["frases"].get(c["pred"], [])):
        return c["pred"]
    return y


print(f"{'variante':22} {'certos':>7} {'delta':>6} {'ganha':>6} {'perde':>6} {'muda':>6}")
RES = {}
for fonte in ["SEC", "TIT", "AMBOS"]:
    for gate in [True, False]:
        for env in [True, False]:
            nome = f"{fonte}{'+indice' if gate else ''}{'+nv' if env else ''}"
            ok = ganha = perde = muda = 0
            det = []
            for c in CASOS:
                novo = aplica(c, fonte, gate, env)
                if novo != c["pred"]:
                    muda += 1
                    g = novo in c["alvo"] and c["pred"] not in c["alvo"]
                    p = c["pred"] in c["alvo"] and novo not in c["alvo"]
                    ganha += g
                    perde += p
                    det.append((("+" if g else "-" if p else "~"), c["sig"], c["id"][:32], c["pred"][-22:], novo[-22:], (list(c["alvo"])[0] or "(vazio)")[-22:], c["k"]))
                ok += novo in c["alvo"]
            RES[nome] = (ok, det)
            print(f"{nome:22} {ok:7} {ok - base:+6} {ganha:6} {perde:6} {muda:6}")

melhor = max(RES, key=lambda k: RES[k][0])
print(f"\nmelhor: {melhor} -> {RES[melhor][0]}/{len(CASOS)} ({RES[melhor][0] - base:+d}); flips:")
for d in sorted(RES[melhor][1]):
    print(f"   {d[0]} {d[1]:4} {d[2]:32} {d[3]:22} -> {d[4]:22} gold={d[5]:22} k={d[6]}")
