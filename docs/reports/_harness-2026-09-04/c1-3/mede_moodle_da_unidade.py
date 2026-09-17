"""A afirmacao do user (08/09): "o Moodle ja da a unidade (nome do card / label), o SARC diz quando". Medida, nao chutada.

Para cada material COM gold de unidade (190 em 5 cursos), testa se cada fonte NOMEIA a unidade correta, pelo criterio
deterministico que o motor ja usa para unidade explicita (`window_provider.unit_named_by_section`): tokens especificos
da fonte contidos nos do titulo da unidade, ou vice-versa, sem genericos.

  SECAO        `source_section` (o card/secao do Moodle onde o arquivo esta)
  LABEL        `moodle_label` / `moodle_week_label`
  SECAO+LABEL  qualquer um dos dois
  BLOCO        o que o motor usa HOJE: a unidade do bloco temporal (que vem do SARC pelo DP posicional)

Tambem mede o efeito colateral da restricao ja existente (`file_map.py:184`, a busca de subunidade so ve os topicos da
unidade atribuida): quantos erros de SUBUNIDADE de hoje sao causados por a unidade estar errada.
0 chamadas. Uso: mede_moodle_da_unidade.py
"""
import collections
import csv as _csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
COM_UNIT = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
            "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor"}
TODOS = dict(COM_UNIT, CG="Computacao-Grafica-Tutor")
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from src.builder import engine as eng  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.patterns import SECTION_NUM_PREFIX_RE  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS, UNIT_TITLE_GENERIC  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402


def toks(texto: str) -> set:
    return {t for t in N(SECTION_NUM_PREFIX_RE.sub("", str(texto or ""))).split()
            if len(t) >= 4 and t not in UNIT_TITLE_GENERIC and not any(t.startswith(g) for g in MOTOR_GENERIC_STEMS)}


def nomeia_unidade(texto: str, unidades: dict) -> str:
    """unit_slug que o texto nomeia, se for exatamente UM (mesmo criterio de unit_named_by_section)."""
    ft = toks(texto)
    if not ft:
        return ""
    hits = [u for u, ut in unidades.items() if ut and (ft <= ut or ut <= ft)]
    return hits[0] if len(hits) == 1 else ""


T = collections.Counter()
print("A FONTE NOMEIA A UNIDADE CORRETA? (materiais com gold de unidade)")
print(f"{'':5} {'n':>4} {'SECAO':>12} {'LABEL':>12} {'SECAO+LABEL':>13} {'BLOCO (hoje)':>14}")
for sig, repo in COM_UNIT.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    unidades = {}
    for t in eng._iter_content_taxonomy_topics(tax):
        unidades.setdefault(t["unit_slug"], toks(str(t.get("unit_title") or "")))
    gu = _load_truth(sig)
    c = collections.Counter()
    for eid, ouro in gu.items():
        e = man.get(eid)
        if not e:
            continue
        c["n"] += 1
        sec = nomeia_unidade(str(e.get("source_section") or ""), unidades)
        lab = nomeia_unidade(f"{moodle_label_text(e) or ''} {e.get('moodle_week_label') or ''}", unidades)
        c["sec_tenta"] += bool(sec)
        c["sec"] += sec == ouro
        c["lab_tenta"] += bool(lab)
        c["lab"] += lab == ouro
        amb = sec or lab
        c["amb_tenta"] += bool(amb)
        c["amb"] += amb == ouro
        c["bloco"] += str(e.get("computed_unit_slug") or "") == ouro
    T.update(c)
    print(f"{sig:5} {c['n']:4} {c['sec']:5}/{c['sec_tenta']:<3} {100 * c['sec'] / c['n']:3.0f}% "
          f"{c['lab']:5}/{c['lab_tenta']:<3} {100 * c['lab'] / c['n']:3.0f}% "
          f"{c['amb']:5}/{c['amb_tenta']:<3} {100 * c['amb'] / c['n']:3.0f}% {c['bloco']:8} {100 * c['bloco'] / c['n']:3.0f}%")
print(f"{'TOT':5} {T['n']:4} {T['sec']:5}/{T['sec_tenta']:<3} {100 * T['sec'] / T['n']:3.0f}% "
      f"{T['lab']:5}/{T['lab_tenta']:<3} {100 * T['lab'] / T['n']:3.0f}% "
      f"{T['amb']:5}/{T['amb_tenta']:<3} {100 * T['amb'] / T['n']:3.0f}% {T['bloco']:8} {100 * T['bloco'] / T['n']:3.0f}%")
print("  (x/y = acertos / vezes que a fonte arriscou um palpite; % = sobre TODOS os materiais)")

print("\nEFEITO COLATERAL DA RESTRICAO (file_map.py:184): erro de subunidade com o gold FORA da unidade atribuida")
tot = collections.Counter()
for sig, repo in TODOS.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    dono = {t["topic_slug"]: t["unit_slug"] for t in eng._iter_content_taxonomy_topics(tax)}
    c = collections.Counter()
    for r in _csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] != "yes" or not r["gold_subunit"]:
            continue
        e = man.get(r["entry_id"])
        if not e:
            continue
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        c["n"] += 1
        if str(e.get("computed_subunit_slug") or "") in alvo:
            continue
        c["erro"] += 1
        u = str(e.get("computed_unit_slug") or "")
        if dono.get(r["gold_subunit"]) and dono[r["gold_subunit"]] != u:
            c["fora"] += 1
    tot.update(c)
    print(f"  {sig:4} erros={c['erro']:3}  destes, gold fora da unidade atribuida: {c['fora']:2}")
print(f"  {'TOT':4} erros={tot['erro']:3}  destes, gold fora da unidade atribuida: {tot['fora']:2} "
      f"({100 * tot['fora'] / max(1, tot['erro']):.0f}% dos erros de subunidade sao, na verdade, erro de UNIDADE)")
