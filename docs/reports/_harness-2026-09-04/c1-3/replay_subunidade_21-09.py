"""Replay read-only da subunidade (1a + 2a passada reais) sobre os builds existentes, com scorer trocavel.

Sem build, sem rede, sem LLM, sem escrita em src/ nem nos builds (entries em deepcopy). Gold so para avaliar.
A unidade e a GRAVADA no manifest (`computed_unit_slug`): o replay isola o eixo de subunidade.

  base  scorer de subtopico atual (`timeline/index.py:_score_entry_against_taxonomy_topic`)
  h2    base + bonus por token exclusivo entre irmaos da unidade presente em heading (0.8) / titulo (0.55)
  h3    scorer de UNIDADE (`file_map.py:score_entry_against_unit`) sobre os subtopicos irmaos como pseudo-unidades;
        indice CONGELADO na 1a taxonomia — defeito apontado pela pesquisa Astra de 21/09, mantido so para o pareamento
  h3a   h3 com o indice refeito por taxonomia: enxerga os aliases que a 2a passada propaga
  h3ad  h3a + frases de label/alias deduplicadas por forma normalizada
  h3b   pos-hoc: base inteira; h3 so onde 1a e 2a passada nao decidiram (vazio/ambiguo/empate), sem sobrepor decisao

Fidelidade = predicao do replay `base` igual a gravada. Sem fidelidade, ganho/perda de h2/h3 e so indicio.
"""
import argparse
import collections
import copy
import csv
import importlib.util
import json
import sys
from functools import partial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diag = load("diagnostico_subunidade", HERE / "diagnostico_subunidade_17-09.py")
compare, mede = diag.compare, diag.mede
from src.builder import engine as E  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text, load_code_curation  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing import resolver_apply as RA  # noqa: E402
from src.builder.routing.coverage_rules import META_COVERAGE_RULES  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402

AUTO = E._auto_map_entry_subtopic
KW = dict(AUTO.keywords)
SCORE_BASE = KW["score_entry_against_taxonomy_topic"]
ITER_TOPICS = KW["iter_content_taxonomy_topics"]
ALIASES = E._file_map_aliases
BONUS_HEADING, BONUS_TITULO = 0.8, 0.55   # pesos de token por campo do scorer de unidade (file_map.py:378-383)


def _toks(text, generic):
    return {t for t in normalize_match_text(text).split() if len(t) >= 4 and t not in generic}


def score_h2(taxonomy):
    exclusivos = {}
    por_unidade = collections.defaultdict(list)
    for t in ITER_TOPICS(taxonomy):
        por_unidade[str(t.get("unit_slug") or "")].append(t)
    for unit, topics in por_unidade.items():
        toks = {str(t.get("topic_slug")): _toks(" ".join([str(t.get("topic_label") or "")] + [str(a) for a in t.get("aliases") or []]),
                                                set(t.get("generic_tokens") or [])) for t in topics}
        freq = collections.Counter(tok for ts in toks.values() for tok in ts)
        for slug, ts in toks.items():
            exclusivos[(unit, slug)] = {tok for tok in ts if freq[tok] == 1}

    def score(signals, topic):
        s = SCORE_BASE(signals, topic)
        excl = exclusivos.get((str(topic.get("unit_slug") or ""), str(topic.get("topic_slug") or "")), set())
        s += BONUS_HEADING * len(excl & set(signals.get("markdown_headings_text", "").split()))
        s += BONUS_TITULO * len(excl & set(signals.get("title_text", "").split()))
        return s
    return score


def _pseudo_unidades(topics, dedupe):
    pseudo = {}
    por_unidade = collections.defaultdict(list)
    for t in topics:
        por_unidade[str(t.get("unit_slug") or "")].append(t)
    for unit, ts in por_unidade.items():
        specs = []
        for t in ts:
            frases = [str(t.get("topic_label") or "")] + [str(a) for a in t.get("aliases") or []]
            if dedupe:   # label e alias que viram a MESMA frase normalizada contavam 2x em `topic_phrases` (file_map.py:99-109)
                vistos, unicas = set(), []
                for f in frases:
                    n = normalize_match_text(ALIASES["_strip_outline_prefix"](f))
                    if n and n not in vistos:
                        vistos.add(n)
                        unicas.append(f)
                frases = unicas
            specs.append({"title": str(t.get("topic_label") or ""), "topics": frases,
                          "generic_tokens": list(t.get("generic_tokens") or [])})
        for t, indexed in zip(ts, ALIASES["_build_file_map_unit_index"](specs)):
            pseudo[(unit, str(t.get("topic_slug") or ""))] = indexed
    return pseudo


def kw_h3(congelado=False, dedupe=False):
    """Scorer de unidade sobre os subtopicos irmaos. `congelado=True` reproduz o defeito achado pela Astra (21/09): o
    indice nasce da 1a taxonomia vista e ignora os aliases que a 2a passada acrescenta na copia (`resolver_apply.py:308-331`).
    Sem ele, o indice e refeito por objeto de taxonomia (memo com ref forte: sem hazard de reuso de id)."""
    memo, atual = {}, {}

    def iter_topics(taxonomy):
        topics = ITER_TOPICS(taxonomy)
        chave = "unica" if congelado else id(taxonomy)
        if chave not in memo:
            memo[chave] = (taxonomy, _pseudo_unidades(topics, dedupe))
        atual["pseudo"] = memo[chave][1]
        return topics

    def score(signals, topic):
        unit = atual["pseudo"].get((str(topic.get("unit_slug") or ""), str(topic.get("topic_slug") or "")))
        return ALIASES["_score_entry_against_unit"](signals, unit) if unit else 0.0
    return {"iter_content_taxonomy_topics": iter_topics, "score_entry_against_taxonomy_topic": score}


VARIANTES = {   # cada valor devolve os kwargs que trocam em `auto_map_entry_subtopic`
    "base": lambda tax: {},
    "h2": lambda tax: {"score_entry_against_taxonomy_topic": score_h2(tax)},
    "h3": lambda tax: kw_h3(congelado=True),            # como medido em 21/09 02:0x (defeituoso, mantido para o pareamento)
    "h3a": lambda tax: kw_h3(),                          # + aliases da 2a passada
    "h3ad": lambda tax: kw_h3(dedupe=True),              # + aliases + frases deduplicadas
    "h3b": lambda tax: {},
}


def replay(root, variante):
    """Espelha o trecho de subunidade de `apply_unit_subunit_fields` (resolver_apply.py:420-577)."""
    entries = copy.deepcopy(compare.read(root / "manifest.json")["entries"])
    taxonomy = load_internal_content_taxonomy(root)
    curation = load_code_curation(root).get("entries", {}) or {}
    auto = partial(AUTO.func, **{**KW, **VARIANTES[variante](taxonomy)})
    passe1, processadas = [], set()
    for entry in entries:
        if not RA._is_material(entry):
            continue
        if not str(entry.get("computed_block_id") or "").strip() and not str(entry.get("temporal_block_id") or "").strip():
            if RA._collapse_ws_cat(str(entry.get("category") or "")).lower() not in RA._NO_TIMELINE_CATEGORIES:
                continue
        cobertura = entry.get("coverage_units") or []
        if str(entry.get("manual_subunit_slug") or "").strip() or (cobertura and str(cobertura[0].get("rule") or "") in META_COVERAGE_RULES):
            continue   # manual e meta-material nao passam pelo scorer: valor gravado fica
        md = diag._entry_markdown_text_for_file_map(root, entry)
        resumo = code_curation_signal_text(curation.get(str(entry.get("id") or ""), {}) or {})
        texto = (f"{md}\n\n{resumo}" if md else resumo) if resumo else md
        unit = str(entry.get("computed_unit_slug") or "")
        match = auto(entry, taxonomy, texto, winning_unit_slug=unit)
        passe1.append((entry, texto, unit, match))
        processadas.add(str(entry.get("id")))
        entry["computed_subunit_slug"] = str(match.topic_slug or "")
        entry["subunit_match_reasons"] = list(match.reasons)
        entry["subunit_match_confidence"] = float(match.confidence)
    RA.propagar_vocabulario_por_headings(passe1, taxonomy, auto, conf_min=T.SUBUNIT_PROPAG_CONF,
                                         min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=T.SUBUNIT_PROPAG_DF_MAX)
    if variante == "h3b":   # pos-hoc (21/09): h3 so onde 1a e 2a passada NAO decidiram; decisao tomada nunca e sobreposta
        auto_h3 = partial(AUTO.func, **{**KW, **kw_h3()})   # so ve a taxonomia original: a copia com aliases morre dentro de `propagar`
        for entry, texto, unit, _ in passe1:
            reasons = [str(r) for r in entry.get("subunit_match_reasons") or []]
            if entry.get("computed_subunit_slug") and not any(r == "ambiguous" or r.startswith("empate-exato") for r in reasons):
                continue
            m = auto_h3(entry, taxonomy, texto, winning_unit_slug=unit)
            if m.topic_slug and not m.ambiguous:
                entry["computed_subunit_slug"] = str(m.topic_slug)
    return {str(e.get("id")): e for e in entries}, processadas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="replay_subunidade_21-09")
    out = (HERE / parser.parse_args().saida).with_suffix(".json")
    assert out.parent == HERE and not out.exists(), "preservar resultado existente"
    report, detalhe = {}, []
    total = collections.Counter()
    for sig, name in mede.NOMES.items():
        ref_root, root = ROOT / diag.REF / name, ROOT / diag.NEW.get(sig, diag.REF) / name
        gravado = {str(e.get("id")): e for e in compare.read(root / "manifest.json")["entries"]}
        ref_by_id = {e["id"]: e for e in compare.read(ref_root / "manifest.json")["entries"]}
        by_source = compare.indexed(list(gravado.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in compare.read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gold_prim = mede.golds(sig)[3]
        rodadas = {v: replay(root, v) for v in VARIANTES}
        c = collections.Counter()
        base_entries, processadas = rodadas["base"]
        for eid in processadas:
            c["manifest_processadas"] += 1
            c["manifest_fieis"] += str(base_entries[eid].get("computed_subunit_slug") or "") == str(gravado[eid].get("computed_subunit_slug") or "")
        rows = [r for r in csv.DictReader((HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig")) if r["sub_primario"] != ""]
        for row in rows:
            eid = row["entry_id"]
            c["n"] += 1
            old = ref_by_id.get(mapping.get(eid) or "")
            entry = (by_source.get(compare.source(old)) or [None])[0] if old else None
            if entry is None:
                c["ausente"] += 1
                continue
            new_id, prim = str(entry.get("id")), gold_prim[eid]
            rec = str(entry.get("computed_subunit_slug") or "")
            pred = {v: str(rodadas[v][0][new_id].get("computed_subunit_slug") or "") for v in VARIANTES}
            c["gold_fiel"] += pred["base"] == rec
            c["acerto_gravado"] += rec in prim
            for v in VARIANTES:
                c[f"acerto_{v}"] += pred[v] in prim
            for v in (x for x in VARIANTES if x != "base"):
                c[f"{v}_ganho"] += pred[v] in prim and pred["base"] not in prim
                c[f"{v}_perda"] += pred["base"] in prim and pred[v] not in prim
                if not pred["base"] and pred[v]:   # abstencao que vira decisao: acerto ou erro novo (cobertura separada)
                    c[f"{v}_abst_{'acerto' if pred[v] in prim else 'erro'}"] += 1
            if pred["base"] != rec or len(set(pred.values())) > 1:
                detalhe.append({"curso": sig, "entry_id": eid, "gold": sorted(prim), "gravado": rec, **pred,
                                "reasons_gravado": gravado[new_id].get("subunit_match_reasons"),
                                "reasons_base": rodadas["base"][0][new_id].get("subunit_match_reasons")})
        report[sig] = dict(c)
        total.update(c)
        print(f"{sig:4}", dict(c))
    print("TOTAL", dict(total))
    # Fidelidade e pre-condicao: sem reproduzir o gravado, ganho/perda das variantes nao vale como medida.
    assert total["manifest_fieis"] == total["manifest_processadas"], "replay base diverge do manifest gravado"
    assert total["gold_fiel"] == total["n"] - total["ausente"] and total["acerto_base"] == total["acerto_gravado"], "replay base diverge no gold"
    out.write_text(json.dumps({"scope": __doc__, "total": dict(total), "courses": report, "detalhe": detalhe},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado em", out.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
