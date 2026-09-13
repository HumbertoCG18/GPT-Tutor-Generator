"""SELETOR DE TOPICOS CARENTES, sem usar o gold (12/09 noite).

O problema: devolver vocabulario a 10 topicos leva o cru de 147 para 201 aceito — mas aqueles 10 foram escolhidos
OLHANDO O GOLD. Num curso novo nao ha gold. Precisa-se de uma regra que, vendo so o plano e os materiais, aponte os
topicos que vao ficar orfaos de vocabulario.

CORRECAO QUE O ASTRA DEIXOU antes de bater o limite de uso: **"score > 0" NAO prova suporte lexical**. O scorer da
`+0.04` incondicional a todo topico do tipo `subtopic` (`timeline/index.py:1935`), entao um topico pode aparecer no
top-2 com score positivo e ZERO casamento de texto. O criterio tem que exigir **contribuicao lexical real**.

CRITERIO DESTE SELETOR (nenhum usa gold):
  suporte lexical de um topico = existe pelo menos um material da unidade dele em que o scorer registra
    `exact_hits > 0` (casou uma FRASE do rotulo/alias) ou `overlap >= 1` (casou um TOKEN especifico)
  CARENTE-FORTE  = 0 materiais dao suporte lexical  -> o professor nunca escreve o nome desse topico
  CARENTE-FRACO  = suporte lexical so por TOKEN, nunca por frase
  desempate      = quantos materiais a unidade tem (o dano potencial)

Sai a comparacao com os seletores antigos e com os 10 topicos-alvo (que vieram do gold — usados SO para avaliar).
0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/seletor_topicos_carentes_12-09.py
"""
import collections
import csv
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402
import src.builder.timeline.index as ti  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]


def sem_llm(sig):
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    vet = set()
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        vet = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in vet]
    return change


def suporte_lexical(signals, topic):
    """(exact_hits, overlap) do scorer, sem o bonus estrutural. Reimplementa a parte lexical de
    `_score_entry_against_taxonomy_topic` — o que decide e SE casou texto, nao o total."""
    frases = [str(topic.get("topic_label") or topic.get("label") or "")] + [str(a) for a in (topic.get("aliases") or [])]
    exact = 0
    for campo in ("markdown_headings_text", "title_text", "markdown_lead_text", "manual_tags_text",
                  "markdown_text", "raw_text", "auto_tags_text", "legacy_tags_text"):
        txt = signals.get(campo) or ""
        if not txt:
            continue
        for f in frases:
            if f and ti._matches_normalized_phrase(txt, f):
                exact += 1
    toks = set()
    for f in frases:
        toks |= {t for t in ti._normalize_match_text(f).split() if len(t) >= 4}
    gen = set(topic.get("generic_tokens") or [])
    toks -= gen
    sig_toks = set()
    for campo in ("markdown_headings_text", "title_text", "markdown_lead_text", "markdown_text", "raw_text"):
        sig_toks |= ti._signal_token_set(signals.get(campo) or "")
    return exact, len(toks & sig_toks)


# 1) suporte lexical de cada topico, sobre os materiais da unidade dele
dados = {}
for sig in CURSOS:
    r = rp.evaluate(sig, "com", new=False, taxmod=sem_llm(sig), escopo="produto")
    entries, textos, tax = r[6], r[5], r[7]
    from src.builder.extraction.entry_signals import collect_entry_unit_signals as colsig
    por_unidade = collections.defaultdict(list)
    for t in ti._iter_content_taxonomy_topics(tax) or []:
        por_unidade[str(t.get("unit_slug") or "")].append(t)
    mats_por_unidade = collections.Counter()
    sup = collections.defaultdict(lambda: {"frase": 0, "token": 0, "materiais": 0, "unidade": ""})
    for e in entries:
        eid = e["id"]
        if eid not in textos:
            continue
        un = str(e.get("computed_unit_slug") or "")
        mats_por_unidade[un] += 1
        s = colsig(e, textos[eid])
        for t in por_unidade.get(un, []):
            k = (sig, t["topic_slug"])
            sup[k]["unidade"] = un
            ex, ov = suporte_lexical(s, t)
            if ex:
                sup[k]["frase"] += 1
            if ov:
                sup[k]["token"] += 1
    for k, v in sup.items():
        v["mats_unidade"] = mats_por_unidade.get(v["unidade"], 0)
    dados.update(sup)

# 2) os 10 topicos-alvo (vieram do gold — usados SO para avaliar o seletor)
er = list(csv.DictReader((HERE / "erros_subunidade_motor_12-09.csv").open(encoding="utf-8-sig")))
alvo = [k for k, _ in collections.Counter((r["curso"], r["gold"]) for r in er if r["gold"]).most_common(10)]

forte = [k for k, v in dados.items() if v["frase"] == 0 and v["token"] == 0]
fraco = [k for k, v in dados.items() if v["frase"] == 0 and v["token"] > 0]
print(f"TOPICOS na taxonomia crua dos 7 cursos: {len(dados)}")
print(f"  CARENTE-FORTE (nenhum material da unidade da suporte lexical): {len(forte)} = {len(forte)/len(dados):.0%}")
print(f"  CARENTE-FRACO (suporte so por TOKEN, nunca por frase):        {len(fraco)} = {len(fraco)/len(dados):.0%}")
print()
print("AVALIACAO contra os 10 pares (curso, topico) que concentram 68% dos erros:")
print(f"{'#':>3} {'curso':5} {'topico':52} {'frase':>6} {'token':>6} {'mats un':>8}  pego por")
for i, (sig, slug) in enumerate(alvo, 1):
    v = dados.get((sig, slug))
    if v is None:
        print(f"{i:>3} {sig:5} {slug:52} {'(topico fora da taxonomia crua)':>22}")
        continue
    tags = []
    if (sig, slug) in forte:
        tags.append("FORTE")
    if (sig, slug) in fraco:
        tags.append("fraco")
    print(f"{i:>3} {sig:5} {slug:52} {v['frase']:>6} {v['token']:>6} {v['mats_unidade']:>8}  {' '.join(tags) or '-'}")
peg_f = sum(1 for k in alvo if k in forte)
peg_ff = sum(1 for k in alvo if k in forte or k in fraco)
print()
print(f"  CARENTE-FORTE pega {peg_f} dos 10 alvos, marcando {len(forte)} topicos ({len(forte)/len(dados):.0%} do total)")
print(f"  FORTE+FRACO   pega {peg_ff} dos 10 alvos, marcando {len(forte)+len(fraco)} topicos "
      f"({(len(forte)+len(fraco))/len(dados):.0%} do total)")
print()
print("COMPARACAO com os seletores que ja falharam (medidos em 12/09):")
print("  'topico sem alias textual no cru'  marcava 144 de 217 (66%) e pegava 5 dos 10")
print("  'topico que nunca vence no cru'    marcava 137 de 217 (63%) e pegava 6 dos 10")
print()
print("TOP-K por dano potencial (CARENTE-FORTE, ordenado por materiais na unidade):")
rank = sorted(forte, key=lambda k: -dados[k]["mats_unidade"])
for i, (sig, slug) in enumerate(rank[:20], 1):
    v = dados[(sig, slug)]
    print(f"  {i:>2}. {sig:4} {slug:52} unidade com {v['mats_unidade']:>3} materiais"
          f"{'   <== ALVO' if (sig, slug) in alvo else ''}")

out = HERE / "seletor_topicos_carentes_12-09.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["curso", "topico", "unidade", "materiais_na_unidade", "suporte_por_frase", "suporte_por_token",
                "carente_forte", "carente_fraco", "e_alvo_do_gold"])
    for (sig, slug), v in sorted(dados.items()):
        w.writerow([sig, slug, v["unidade"], v["mats_unidade"], v["frase"], v["token"],
                    int((sig, slug) in forte), int((sig, slug) in fraco), int((sig, slug) in alvo)])
print()
print(f"CSV: {out}")
