"""Alavancas GENERICAS para a subunidade, apontadas pelo diagnostico do CG (`diag_cg_sub.py`), simuladas em memoria pela rota
real (`file_map.auto_map_entry_subtopic` + scorer do engine) nas copias `.ablacao` (regua automatica) contra os 6 golds (233). 0 chamadas.
  base  reproduz o gravado (gate do harness)
  H2    higiene estendida do vocab LLM: sinonimo compilado cuja forma normalizada e SUBFRASE (palavra inteira) de um nome de secao do
        Moodle sai (hoje so sai o IGUAL). CG: 'OpenGL' <- secao 'Biblioteca OpenGL' pendurado em u01/'Conceitos'.
  D     decomposicao de rotulos compostos: partes de 'A e B' / 'A ou B' / 'A: B' / 'A (B)' / 'A / B' viram aliases; e rotulo com cabeca
        generica no curso ('Algoritmos de X', 'Tecnicas de X': cabeca presente em >= 2 rotulos do curso) ganha alias 'X'. So partes
        exclusivas dentro da unidade (nao contidas em irmao) e com token especifico.
  H2+D  as duas.
Uso: simula_cg_sub_levers.py [--lista]"""
import collections
import csv
import functools
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
COPY = GEN / ".ablacao"
LISTA = "--lista" in sys.argv
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.artifacts.repo import _moodle_section_names  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402

REPO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
iter_orig = eng._iter_content_taxonomy_topics
_SEP = re.compile(r"\s+e\s+|\s+ou\s+|:|\(|\)|/|,|\s+-\s+", re.I)
_NUM = re.compile(r"^\d+(\.\d+)*\s+")
_HEAD = re.compile(r"^(\w+)\s+(de|da|do|das|dos|para|em)\s+(.+)$", re.I)
_STOP = {"de", "da", "do", "das", "dos", "e", "ou", "em", "para", "com", "a", "o", "as", "os", "um", "uma"}


def toks(s: str) -> set:
    return {t for t in N(s).split() if len(t) >= 4}


def llm_synonyms(root: Path) -> set:
    p = root / "course/.glossary_curation.llm.json"
    if not p.exists():
        return set()
    g = json.loads(p.read_text(encoding="utf-8"))
    return {N(v) for k, vals in g.items() if not k.startswith("_") and isinstance(vals, dict) for v in (vals.get("synonyms") or []) if N(v)}


def h2_drop(alias_norm: str, secoes: set) -> bool:
    """Subfrase (palavra inteira) de um nome de secao, e nao igual (o igual ja sai na higiene atual)."""
    return any(alias_norm != s and re.search(rf"(^|\s){re.escape(alias_norm)}(\s|$)", s) for s in secoes)


def parts_of(label: str, heads_genericos: set) -> list:
    base = _NUM.sub("", label).strip()
    out = []
    for p in _SEP.split(base):
        p = (p or "").strip(" .;")
        if p and N(p) != N(base) and toks(p):
            out.append(p)
    m = _HEAD.match(base)
    if m and N(m.group(1)) in heads_genericos and toks(m.group(3)):
        out.append(m.group(3).strip())
    return out


def make_iter(variante: str, root: Path):
    syn = llm_synonyms(root) if "H2" in variante else set()
    secoes = _moodle_section_names(root) if "H2" in variante else set()

    def _iter(taxonomy):
        topics = [dict(t) for t in iter_orig(taxonomy)]
        if variante == "base":
            return topics
        removidos, adicionados = [], []
        if "H2" in variante:
            for t in topics:
                keep = []
                for al in t.get("aliases") or []:
                    n = N(al)
                    if n in syn and h2_drop(n, secoes):
                        removidos.append((t["topic_slug"], al))
                        continue
                    keep.append(al)
                t["aliases"] = keep
        if "D" in variante:
            heads = collections.Counter()
            for t in topics:
                m = _HEAD.match(_NUM.sub("", t["topic_label"]).strip())
                if m:
                    heads[N(m.group(1))] += 1
            heads_gen = {h for h, n in heads.items() if n >= 2}
            por_unidade = collections.defaultdict(list)
            for t in topics:
                por_unidade[t["unit_slug"]].append(t)
            for unit_slug, irmaos in por_unidade.items():
                generic = set(irmaos[0].get("generic_tokens") or [])
                for t in irmaos:
                    vocab_irmaos = " | ".join(N(x) for o in irmaos if o is not t for x in [o["topic_label"]] + list(o.get("aliases") or []))
                    novos = []
                    for p in parts_of(t["topic_label"], heads_gen):
                        n = N(p)
                        if not n or n in vocab_irmaos or not (toks(p) - generic - _STOP):
                            continue
                        if n in {N(x) for x in [t["topic_label"]] + list(t.get("aliases") or [])}:
                            continue
                        if n == N(t.get("unit_title") or ""):
                            continue
                        novos.append(p)
                    if novos:
                        t["aliases"] = list(t.get("aliases") or []) + novos
                        adicionados.append((t["topic_slug"], novos))
        if LISTA and not getattr(_iter, "_listado", False):
            _iter._listado = True
            if removidos:
                print(f"     [{variante}] {root.name[:20]} remove: {removidos}")
            if adicionados:
                print(f"     [{variante}] {root.name[:20]} adiciona: {adicionados}")
        return topics
    return _iter


def subtopic_fn(variante, root):
    return functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                             iter_content_taxonomy_topics=make_iter(variante, root),
                             score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                             topic_match_result_factory=TopicMatchResult)


def texto(root: Path, entry: dict, code_cur: dict) -> str:
    md = eng._entry_markdown_text_for_file_map(root, entry)
    rec = (code_cur.get("entries") or {}).get(str(entry.get("id") or "")) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    return (f"{md}\n\n{resumo}" if md else resumo) if resumo else md


VARIANTES = ["base", "H2", "D", "H2+D"]
res = {v: collections.Counter() for v in VARIANTES}
por_curso = {v: collections.Counter() for v in VARIANTES}
for sig, repo in REPO.items():
    root = COPY / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    code_cur = json.loads((root / "code_curation.json").read_text(encoding="utf-8")) if (root / "code_curation.json").exists() else {}
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    fns = {v: subtopic_fn(v, root) for v in VARIANTES}
    for r in rows:
        e = man.get(r["entry_id"])
        if e is None:
            continue
        alvo = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
        t = texto(root, e, code_cur)
        unit = str(e.get("computed_unit_slug") or "")
        preds = {}
        for v in VARIANTES:
            m = fns[v](e, tax, t, winning_unit_slug=unit)
            preds[v] = str(m.topic_slug or "")
        if preds["base"] != str(e.get("computed_subunit_slug") or ""):
            res["base"]["DIVERGE"] += 1
        for v in VARIANTES:
            ok = preds[v] in alvo
            res[v]["ok"] += ok; res[v]["n"] += 1; por_curso[v][sig] += ok
            if v != "base":
                a, b = preds["base"] in alvo, ok
                flip = "+" if (b and not a) else "-" if (a and not b) else ("~" if preds[v] != preds["base"] else "=")
                res[v][flip] += 1
                if flip in "+-" or (LISTA and flip == "~"):
                    print(f"  {v:4} {flip} {sig:3} {r['entry_id'][:40]:40} {preds['base'][-26:] or '-':26} -> {preds[v][-26:] or '-':26} gold={r['gold_subunit'][-24:] or '(vazio)'}")
for v in VARIANTES:
    c = res[v]
    pc = " ".join(f"{s} {por_curso[v][s]}" for s in REPO)
    print(f"{v:4} subunidade {c['ok']}/{c['n']}  " + (f"flips + {c['+']} - {c['-']} ~ {c['~']}  | " if v != "base" else f"diverge={c['DIVERGE']} | ") + pc)
