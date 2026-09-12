"""Replay de subunidade em memoria, sem LLM: os 3 regimes (sem resumos, determ v2, com
resumos) nos 5 cursos com gold, mais os experimentos que o Codex astra rodou em 11/09.

Extraido do rollout ~/.codex/sessions/2026/09/11/rollout-*-01a08ea5-*.jsonl (o astra montou
isto em memoria e morreu com a sessao). Cada evaluate() leva ~1 s; a tabela inteira, ~15 s.

Estado que o replay assume (medido em 11/09, 01:0x):
- .ablacao/<tutor>/ e a copia com VOCAB ANTIGO da medicao "com resumos, vocab antigo";
  load(new=True) injeta o vocab novo a partir de ../<tutor>/course/.glossary_curation.llm.json
  (MF nao tem .llm.json; ES2 teve 3 entradas de unidade trocadas no run com vocab novo).
- docs/reports/subunit_gt_<sig>.csv e o gold; scorable=yes.
- Regua igual aos logs codigo_{sem,determ2,com}_puro_b.log: (com-extras, primario).

Uso:  python -B docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py [experimentos]
"""
import ast
import copy
import csv
import functools
import json
import os
import re
import socket
import sys
from collections import Counter  # noqa: F401  (usado por _sintetico do shim)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"


def _denied(*a, **k):
    raise RuntimeError("network blocked")


socket.socket.connect = _denied
socket.create_connection = _denied

from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd  # noqa: E402
from src.builder.artifacts.repo import _glossary_curation_key, _normalize_secao  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text as signaltext  # noqa: E402
from src.builder.extraction.content_taxonomy import (  # noqa: E402
    _glossary_aliases_for_topic, _parse_glossary_terms, load_internal_content_taxonomy)
from src.builder.extraction.entry_signals import collect_entry_unit_signals as signals  # noqa: E402
from src.builder.routing.file_map import auto_map_entry_subtopic  # noqa: E402
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
import src.builder.timeline.index as ti  # noqa: E402
from src.builder.timeline.index import (  # noqa: E402
    TopicMatchResult, _iter_content_taxonomy_topics as topics,
    _score_entry_against_taxonomy_topic as score)

# Cache nos normalizadores: sem isto cada evaluate() leva minutos, nao segundos.
ti._normalize_match_text = functools.lru_cache(maxsize=100000)(ti._normalize_match_text)
ti._signal_token_set = functools.lru_cache(maxsize=100000)(ti._signal_token_set)
ti._matches_normalized_phrase = functools.lru_cache(maxsize=100000)(ti._matches_normalized_phrase)

# _bundle_md/_sintetico do shim, sem importar o shim: o import dele monkeypatcha
# ablacao_rapida e reprocess_assignments.
_SHIM = Path("docs/reports/_harness-2026-09-04/c1-3/shim_codigo.py")
_KEEP = {"_CAMEL", "_COMMENT", "_WORD", "_STOP", "_FRONT", "_FENCE", "_HEAD", "_CELULA"}
_nodes = [n for n in ast.parse(_SHIM.read_text(encoding="utf-8")).body
          if (isinstance(n, ast.FunctionDef) and n.name in ("_bundle_md", "_sintetico"))
          or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in _KEEP for t in n.targets))]
exec(compile(ast.Module(body=_nodes, type_ignores=[]), str(_SHIM), "exec"))

sub = functools.partial(auto_map_entry_subtopic, collect_entry_unit_signals=signals,
                        iter_content_taxonomy_topics=topics,
                        score_entry_against_taxonomy_topic=score,
                        topic_match_result_factory=TopicMatchResult)

NAMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor",
         "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor"}
CATEGORIAS = {"material-de-aula", "codigo-professor", "listas", "gabaritos", "slides", "apostila",
              "provas", "trabalhos", "exercicios", "bibliografia", "referencias", "quadro-branco"}
# Categorias sem eixo temporal, `content_taxonomy._NO_TIMELINE_CATEGORIES` (o produto as processa mesmo sem bloco).
NO_TIMELINE = {"cronograma", "bibliografia", "referencias", "references"}


def _no_escopo(e, escopo):
    """Quem entra na passada do replay.

    `replay` (default): o filtro historico, preservado para os asserts contra os logs de 11/09.
    `produto`: o MESMO predicado do produto (`resolver_apply.apply_unit_subunit_fields`, linhas 421-436):
    `_is_material` e (bloco OU bloco temporal OU categoria sem eixo temporal). Medido em 12/09: com o filtro
    historico o replay processa 68 das 93 entradas do CG, e as 25 puladas ficam com o `computed_subunit_slug`
    QUE VEIO DO MANIFEST DO PRODUTO -- 22 delas estao no gold, e o regime cru marcava 16 aceito/14 primario
    herdados de uma decisao tomada COM o vocabulario LLM. Alem do vazamento, as puladas nao entram no `df` nem
    nos `owners` da 2a passada, o que fazia a propagacao divergir do produto."""
    if escopo != "produto":
        return e.get("category") in CATEGORIAS or bool(e.get("computed_block_id"))
    if str(e.get("file_type") or "") != "pdf" and not e.get("category"):
        return False
    if str(e.get("computed_block_id") or "").strip() or str(e.get("temporal_block_id") or "").strip():
        return True
    return str(e.get("category") or "").strip().lower() in NO_TIMELINE


def load(sig, new=True):
    """(root, entries, tax, code_curation, gold) do curso; new=True injeta o vocab novo."""
    root = Path(".ablacao") / NAMES[sig]
    orig = Path("..") / NAMES[sig]
    entries = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    tax = load_internal_content_taxonomy(root)
    if new and sig != "MF":
        vocab = json.loads((orig / "course/.glossary_curation.llm.json").read_text(encoding="utf-8"))
        terms = _parse_glossary_terms((root / "course/GLOSSARY.md").read_text(encoding="utf-8"))
        secs = {_normalize_secao(e.get("source_section", "")) for e in entries if e.get("source_section")}
        cv = {_glossary_curation_key(k): v["synonyms"] for k, v in vocab.items() if not k.startswith("_")}
        for term in terms:
            term["synonyms"] = list(term.get("synonyms", [])) + [
                v for v in cv.get(_glossary_curation_key(term["term"]), []) if _normalize_secao(v) not in secs]
        for u in tax["units"]:
            for t in u["topics"]:
                t["aliases"] = list(dict.fromkeys(
                    t.get("aliases", []) + _glossary_aliases_for_topic(t["label"], u["title"], terms)))
    if new and sig == "ES2":
        # A copia .ablacao e vocab antigo; estas 3 entradas mudaram de unidade no run com
        # vocab novo (logs pareados). Fixar a unidade e' o que faz o replay bater com o log.
        u = next(u["slug"] for u in tax["units"] if "devops" in u["slug"])
        for e in entries:
            if e["id"] in ("microsservicos4", "roteiro4-circuitbreaker", "roteiro4"):
                e["computed_unit_slug"] = u
    cc_path = orig / "code_curation.json"
    cc = json.loads(cc_path.read_text(encoding="utf-8"))["entries"] if cc_path.exists() else {}
    gold = {r["entry_id"]: r for r in csv.DictReader(
        Path(f"docs/reports/subunit_gt_{sig}.csv").open(encoding="utf-8-sig")) if r["scorable"] == "yes"}
    return root, entries, tax, cc, gold


def evaluate(sig, mode, new=True, taxmod=None, synth=None, escopo="replay"):
    """mode: 'sem' | 'determ' | 'com'; escopo: 'replay' (historico) | 'produto' (ver `_no_escopo`). Devolve
    (com_extras, primario, ok_por_id, pred_por_id, match_1a_passada, texto_por_id, entries, tax, processados)."""
    root, entries, tax, cc, gold = load(sig, new)
    if taxmod:
        taxmod(tax)
    passes, first, texts = [], {}, {}
    for e in entries:
        if not _no_escopo(e, escopo):
            continue
        md = getmd(root, e)
        if mode == "com":
            rec = cc.get(e["id"], {})
        elif mode == "determ" and (e.get("category") == "codigo-professor" or e.get("file_type") in ("code", "zip")):
            rec = (synth or _sintetico)(e, root)  # noqa: F821  (do shim)
        else:
            rec = {}
        extra = signaltext(rec)
        text = md + "\n\n" + extra if md and extra else md or extra
        unit = e.get("computed_unit_slug", "")
        match = sub(e, tax, text, winning_unit_slug=unit)
        e["computed_subunit_slug"] = match.topic_slug
        e["subunit_match_reasons"] = match.reasons
        e["subunit_match_confidence"] = match.confidence
        passes.append((e, text, unit, match))
        first[e["id"]] = match
        texts[e["id"]] = text
    propagar_vocabulario_por_headings(passes, tax, sub, conf_min=T.SUBUNIT_PROPAG_CONF,
                                      min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=T.SUBUNIT_PROPAG_DF_MAX)
    pred = {e["id"]: e.get("computed_subunit_slug", "") for e in entries}
    ok = {}
    for k, r in gold.items():
        aceitos = ({r["gold_subunit"]} | set(filter(None, r.get("gold_subunits_extra", "").split(";")))
                   if r["gold_subunit"] else {""})
        ok[k] = pred.get(k) in aceitos
    prim = sum(pred.get(k) == r["gold_subunit"] for k, r in gold.items())
    processados = {e["id"] for e, _, _, _ in passes}
    return sum(ok.values()), prim, ok, pred, first, texts, entries, tax, processados


def tabela(new=True):
    """Imprime curso x regime (com-extras/gold) e devolve {sig: {mode: (extras, prim)}}."""
    res = {}
    for sig in NAMES:
        res[sig] = {}
        for mode in ("sem", "determ", "com"):
            r = evaluate(sig, mode, new)
            res[sig][mode] = (r[0], r[1], len(r[2]))
    print(f"{'curso':6} {'sem':>9} {'determ':>9} {'com':>9}")
    for sig, ms in res.items():
        print(f"{sig:6} " + " ".join(f"{ms[m][0]:>5}/{ms[m][2]:<3}" for m in ("sem", "determ", "com")))
    tot = {m: (sum(ms[m][0] for ms in res.values()), sum(ms[m][2] for ms in res.values())) for m in ("sem", "determ", "com")}
    print(f"{'total':6} " + " ".join(f"{tot[m][0]:>5}/{tot[m][1]:<3}" for m in ("sem", "determ", "com")))
    return res


# ---- experimentos do astra (nenhum aplicado ao produto) ---------------------------------

def no_study(tax):
    """REMOVE_STUDY_ALIASES: em 'estudo-de-casos' fica so alias que comeca com digito."""
    for u in tax["units"]:
        for t in u["topics"]:
            if t["slug"] == "estudo-de-casos":
                t["aliases"] = [a for a in t["aliases"] if re.match(r"^\d", a)]


def remove_added(sig="SO"):
    """SO_ONLY_NEW_STUDY: 'estudo-de-casos' volta aos aliases do vocab antigo."""
    base = load(sig, False)[2]
    old = {(u["slug"], t["slug"]): t["aliases"] for u in base["units"] for t in u["topics"]}

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                if t["slug"] == "estudo-de-casos":
                    t["aliases"] = old[(u["slug"], t["slug"])]
    return change


def ownmd(e, root):
    """SKIP_DUPLICATE_MD: sem resumo sintetico quando o leitor ja entrega .md."""
    return {} if getmd(root, e) else _sintetico(e, root)  # noqa: F821


def restored(sig):
    """RESTORE_REJECTED: devolve a taxonomia os termos vetados 'Rede Perceptron', 'MLP', 'Kubernetes'."""
    vocab = json.loads((Path("..") / NAMES[sig] / "course/.glossary_curation.llm.json").read_text(encoding="utf-8"))

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                key = f"{t.get('code', '')} {t['label']}".strip()
                for alias in vocab["_raw"].get(key, []):
                    if alias in ("Rede Perceptron", "MLP", "Kubernetes"):
                        t["aliases"].append(alias)
    return change


def identifiers(sig):
    """IDENTIFIER_ALIASES: alias do vocabulario presente em identificador CamelCase do codigo bruto."""
    tax = load(sig)[2]
    als = {a for u in tax["units"] for t in u["topics"] for a in t.get("aliases", []) if len(a) >= 4}

    def synth(e, root):
        r = _sintetico(e, root)  # noqa: F821
        raw = " ".join(md for _, md in _bundle_md(e, root))  # noqa: F821
        words = set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", raw))
        hits = [a for a in als if re.search(r"[A-Za-z]", a) and any(
            re.search(r"(?<![a-z])" + re.escape(a.replace(" ", "")) + r"(?=[A-Z_0-9]|$)", w) for w in words)]
        r["summary"]["concepts"] += sorted(hits)
        return r
    return synth


def preserve(sig):
    """PRESERVE_PHRASES: identifiers() + frase literal do vocabulario presente no codigo bruto."""
    f = identifiers(sig)
    als = {a for t in topics(load(sig)[2]) for a in t.get("aliases", []) if len(a) >= 4}

    def synth(e, root):
        r = f(e, root)
        raw = " ".join(md for _, md in _bundle_md(e, root))  # noqa: F821
        r["summary"]["concepts"] += sorted(a for a in als if ti._matches_normalized_phrase(raw, a))
        return r
    return synth


def result(label, sig, **kwargs):
    """Baseline determ vs determ com taxmod=/synth=; imprime ganho e perda por material."""
    b = evaluate(sig, "determ")
    r = evaluate(sig, "determ", **kwargs)
    print(label, sig, b[:2], "->", r[:2],
          "gain", [k for k in b[2] if not b[2][k] and r[2][k]],
          "loss", [k for k in b[2] if b[2][k] and not r[2][k]], flush=True)
    return b[:2], r[:2]


def experimentos():
    """Os que o astra reportou; valores obtidos em 11/09 entre parenteses."""
    result("REMOVE_STUDY_ALIASES", "SO", taxmod=no_study)          # (8,7) -> (15,14)
    result("RESTORE_REJECTED", "IA", taxmod=restored("IA"))         # (36,36) -> (37,37)
    result("RESTORE_REJECTED", "ES2", taxmod=restored("ES2"))       # (20,18) -> (21,19)
    for sig in NAMES:
        result("SKIP_DUPLICATE_MD", sig, synth=ownmd)
    for sig in ("ES2", "MF", "IA", "SO"):
        result("IDENTIFIER_ALIASES", sig, synth=identifiers(sig))   # ES2 (20,18) -> (22,20)
    for sig in ("ES2", "MF", "IA", "SO"):
        result("PRESERVE_PHRASES", sig, synth=preserve(sig))        # ES2 (20,18) -> (24,22), perde roteiro3-gateway
    for mode in ("sem", "determ", "com"):
        a = evaluate("SO", mode)
        b = evaluate("SO", mode, taxmod=remove_added("SO"))
        print("SO_ONLY_NEW_STUDY", mode, a[:2], b[:2], flush=True)  # (8,7) (15,14) nos tres


if __name__ == "__main__":
    import time
    t0 = time.time()
    res = tabela()
    print(f"tempo: {time.time() - t0:.0f}s")
    # Por curso, o que o astra reproduziu contra os logs codigo_{sem,determ2,com}_puro_b.log
    # (totais 122/124/128 de 151). TCC: replay da 11, log deu 10; divergencia conhecida, sem assert.
    esperado = {"sem": {"MF": 52, "SO": 8, "IA": 36, "ES2": 16},
                "determ": {"MF": 50, "SO": 8, "IA": 36, "ES2": 20},
                "com": {"MF": 51, "SO": 8, "IA": 38, "ES2": 21}}
    log_total = {"sem": 122, "determ": 124, "com": 128}
    for mode, cursos in esperado.items():
        for sig, n in cursos.items():
            assert res[sig][mode][0] == n, f"{sig} {mode}: replay {res[sig][mode][0]} != log {n}"
        assert sum(cursos.values()) + 10 == log_total[mode], mode
    print("TCC:", {m: res["TCC"][m][0] for m in ("sem", "determ", "com")}, "(log: 10; replay diverge, conhecido)")
    print("ok: MF/SO/IA/ES2 batem com os logs nos 3 regimes")
    if "experimentos" in sys.argv:
        experimentos()
