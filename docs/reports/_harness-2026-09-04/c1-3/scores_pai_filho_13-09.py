"""PAI x FILHO: os scores dos 8 erros contra CONTROLES CORRETOS (13/09, proximo passo do astra na §36).

A contagem da §36 e estrutural: 8 de 109 erros sao o motor escolhendo o ancestral do gold. Ela nao diz POR QUE o pai
venceu. Antes de qualquer regra, o astra pediu: *"inspecionar scores pai/filho nesses casos e controles corretos"*.

Para cada material com gold nao vazio cujo topico do gold tem ANCESTRAL ou DESCENDENTE na mesma unidade (6 cursos; o IA
nao tem `code` e fica fora), separa quatro grupos pelo resultado do braco C (cru honesto):

  E-pai    erro: o motor escolheu um ANCESTRAL do gold          (os 8 da §36)
  E-filho  erro: o motor escolheu um DESCENDENTE do gold        (os 5 da §36)
  C-filho  controle: o gold tem ancestral e o motor ACERTOU
  C-pai    controle: o gold tem descendente e o motor ACERTOU

E mede, com as funcoes REAIS do motor (`_score_entry_against_taxonomy_topic`, `_matches_normalized_phrase`):
  - score do gold e do parente rival na 1a passada (texto = markdown + resumo deterministico de codigo, como o resolver)
  - se o ROTULO do filho casa como frase em algum campo (exact hit)
  - se ha token DISTINTIVO do filho no texto: token do filho que o pai nao tem  [APROXIMACAO: reconstroi o conjunto de
    tokens do scorer (>= 4 chars ou short_vocab, sem genericos); nao reproduz o descarte de fusao do slug]

Referencia de acerto: `erros_subunidade_cru_honesto_13-09.csv` (erros de ACEITO do braco C). A copia pode estar noutro
braco com o mesmo agregado (hoje `sempropag`): o score da 1a passada nao muda com ele; material cuja resposta final difere
do braco C e marcado `indeterminado`.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/scores_pai_filho_13-09.py
"""
import collections
import csv
import json
import statistics
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
COPIA = GEN / ".motor3eixos"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import src.utils.helpers  # noqa: F401,E402  (.env)
from src.builder import engine as eng  # noqa: E402
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.extraction.entry_signals import collect_entry_unit_signals  # noqa: E402
import src.builder.timeline.index as ti  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
CAMPOS = [("markdown_headings_text", True), ("title_text", True), ("markdown_lead_text", False),
          ("manual_tags_text", True), ("markdown_text", False), ("auto_tags_text", True),
          ("legacy_tags_text", False), ("raw_text", True)]
N = ti._normalize_match_text
GENERICOS_PADRAO = set(getattr(ti, "UNIT_GENERIC_TOKENS", set()) or set())


def tokens_do_topico(t):
    gen = set(t.get("generic_tokens") or []) or GENERICOS_PADRAO
    curto = set(t.get("short_vocab") or [])
    textos = [str(t.get("topic_label") or "")] + [str(a) for a in (t.get("aliases") or [])] + \
             [str(t.get("topic_slug") or "").replace("-", " ")]
    return {x for s in textos for x in N(s).split() if (len(x) >= 4 or x in curto) and x not in gen}


def tokens_do_sinal(sig, curto):
    return {x for campo, forte in CAMPOS for x in str(sig.get(campo, "")).split() if len(x) >= 4 or (forte and x in curto)}


def frase_do_rotulo_casa(sig, t):
    rot = str(t.get("topic_label") or "")
    return any(ti._matches_normalized_phrase(str(sig.get(campo, "")), rot) for campo, _ in CAMPOS)


def ancestral(a, b):
    return bool(a) and bool(b) and b.startswith(a + ".")


def main():
    marc = (COPIA / "_CONFIG_ATUAL.txt").read_text(encoding="utf-8").splitlines()[0] if (COPIA / "_CONFIG_ATUAL.txt").exists() else "?"
    print(f"copia em: {marc}")
    erros_c = {(r["curso"], r["entry_id"]): r for r in
               csv.DictReader((HERE / "erros_subunidade_cru_honesto_13-09.csv").open(encoding="utf-8-sig", newline=""))}
    linhas = []
    for sig, nome in NOMES.items():
        root = COPIA / nome
        bruta = json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
        code = {(str(u.get("slug") or ""), str(tp.get("slug") or "")): str(tp.get("code") or "")
                for u in bruta["units"] for tp in (u.get("topics") or [])}
        tax = load_internal_content_taxonomy(root)
        idx = ti._iter_content_taxonomy_topics(tax)
        por_unidade = collections.defaultdict(list)
        for t in idx:
            por_unidade[str(t.get("unit_slug") or "")].append(t)
        cc = (json.loads((root / "code_curation.json").read_text(encoding="utf-8")).get("entries") or {}) \
            if (root / "code_curation.json").exists() else {}
        gold = {}
        for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
            if r["scorable"] == "yes" and r["gold_subunit"]:
                gold[r["entry_id"]] = (r["gold_subunit"], {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";"))))
        for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]:
            if e["id"] not in gold:
                continue
            g_slug, aceitos = gold[e["id"]]
            unidade = str(e.get("computed_unit_slug") or "")
            tops = por_unidade.get(unidade) or []
            t_gold = next((t for t in tops if str(t.get("topic_slug") or "") == g_slug), None)
            if not t_gold:
                continue  # gold fora da unidade atribuida: nao e pai x filho
            c_gold = code.get((unidade, g_slug), "")
            if not c_gold:
                continue
            anc = [t for t in tops if ancestral(code.get((unidade, str(t.get("topic_slug") or "")), ""), c_gold)]
            desc = [t for t in tops if ancestral(c_gold, code.get((unidade, str(t.get("topic_slug") or "")), ""))]
            if not anc and not desc:
                continue

            erro_c = erros_c.get((sig, e["id"]))
            pred_c = erro_c["cru"] if erro_c else None
            pred_agora = str(e.get("computed_subunit_slug") or "")
            if erro_c:
                pred = pred_c
            elif pred_agora in aceitos:
                pred = pred_agora
            else:
                pred = None  # certo no braco C, errado na copia atual: resposta do C desconhecida
            anc_slugs = {str(t.get("topic_slug") or "") for t in anc}
            desc_slugs = {str(t.get("topic_slug") or "") for t in desc}
            if pred is None:
                grupo, rival = "indeterminado", (anc or desc)[0]
            elif erro_c and pred in anc_slugs:
                grupo, rival = "E-pai", next(t for t in anc if str(t.get("topic_slug")) == pred)
            elif erro_c and pred in desc_slugs:
                grupo, rival = "E-filho", next(t for t in desc if str(t.get("topic_slug")) == pred)
            elif not erro_c and anc:
                grupo, rival = "C-filho", max(anc, key=lambda t: len(code.get((unidade, str(t.get("topic_slug"))), "")))
            elif not erro_c and desc:
                grupo, rival = "C-pai", desc[0]
            else:
                continue  # erro com parentesco na unidade, mas o motor escolheu outro topico: nao e disputa pai x filho

            md = _entry_markdown_text_for_file_map(root, e) or ""
            resumo = code_curation_signal_text(cc.get(e["id"]) or {}) if e["id"] in cc else ""
            texto = f"{md}\n\n{resumo}" if (md and resumo) else (md or resumo)
            s = collect_entry_unit_signals(e, texto)
            sc_gold = ti._score_entry_against_taxonomy_topic(s, t_gold)
            sc_rival = ti._score_entry_against_taxonomy_topic(s, rival)
            filho, pai = (t_gold, rival) if grupo in ("E-pai", "C-filho") or (grupo == "indeterminado" and anc) else (rival, t_gold)
            curto = set(filho.get("short_vocab") or [])
            distintivos = sorted((tokens_do_topico(filho) - tokens_do_topico(pai)) & tokens_do_sinal(s, curto))
            linhas.append(dict(
                curso=sig, entry_id=e["id"], grupo=grupo, gold=g_slug, code_gold=c_gold,
                rival=str(rival.get("topic_slug") or ""), code_rival=code.get((unidade, str(rival.get("topic_slug") or "")), ""),
                score_gold=round(sc_gold, 3), score_rival=round(sc_rival, 3),
                frase_filho_casa=int(frase_do_rotulo_casa(s, filho)), frase_pai_casa=int(frase_do_rotulo_casa(s, pai)),
                n_distintivos_filho=len(distintivos), distintivos_filho=";".join(distintivos),
                chars_texto=len(texto), razoes=";".join(str(x) for x in (e.get("subunit_match_reasons") or []))))

    out = HERE / "scores_pai_filho_13-09.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    print(f"\n{len(linhas)} materiais em disputa pai x filho (6 cursos; IA fora por nao ter code)\n")
    print(f"{'grupo':14} {'n':>3} {'score gold (med)':>17} {'score rival (med)':>18} {'frase do filho casa':>20} "
          f"{'filho tem token distintivo':>27}")
    for g in ("E-pai", "C-filho", "E-filho", "C-pai", "indeterminado"):
        rs = [l for l in linhas if l["grupo"] == g]
        if not rs:
            continue
        med = lambda k: statistics.median([l[k] for l in rs])
        print(f"{g:14} {len(rs):>3} {med('score_gold'):>17.3f} {med('score_rival'):>18.3f} "
              f"{sum(l['frase_filho_casa'] for l in rs):>12} de {len(rs):<5} {sum(1 for l in rs if l['n_distintivos_filho']):>19} de {len(rs)}")
    por_curso = collections.Counter((l["curso"], l["grupo"]) for l in linhas)
    print("\npor curso:", {f"{c}:{g}": n for (c, g), n in sorted(por_curso.items())})

    print("\nOS ERROS, material a material:")
    for l in linhas:
        if l["grupo"].startswith("E-"):
            print(f"  [{l['grupo']}] {l['curso']:4} {l['entry_id'][:32]:34} gold {l['code_gold']:8} {l['score_gold']:>6.3f} x "
                  f"rival {l['code_rival']:8} {l['score_rival']:>6.3f} · frase filho {l['frase_filho_casa']} · "
                  f"distintivos do filho no texto: {l['distintivos_filho'] or '(nenhum)'}")
    print("\nOS CONTROLES C-filho (o filho venceu o pai e acertou):")
    for l in linhas:
        if l["grupo"] == "C-filho":
            print(f"  {l['curso']:4} {l['entry_id'][:32]:34} gold {l['code_gold']:8} {l['score_gold']:>6.3f} x pai {l['code_rival']:8} "
                  f"{l['score_rival']:>6.3f} · frase filho {l['frase_filho_casa']} · distintivos: {l['distintivos_filho'] or '(nenhum)'}")
    print(f"\nDetalhe em {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
