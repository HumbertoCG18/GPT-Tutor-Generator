"""W-I: diagnostica os aliases temporarios da 2a passada apenas no curso CG."""
import collections
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
EVIDENCE = DATA / "docs/reports/_harness-2026-09-04/c1-3"
sys.path.insert(0, str(ROOT))

from src.builder.extraction.entry_signals import collect_entry_unit_signals, normalize_match_text  # noqa: E402
from src.builder.routing import resolver_apply as RA  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402

TARGET = "pagina-com-videos-sobre-sintese-de-imagens-realisticas-a6d9ea"
COMPETITORS = {"modelos-de-reflexao-ambiente-difusa-especular", "mapeamento-de-textura"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aliases(taxonomy):
    return {
        (str(unit.get("slug") or ""), str(topic.get("slug") or "")): set(topic.get("aliases") or [])
        for unit in taxonomy.get("units", []) or []
        for topic in unit.get("topics", []) or []
    }


def scores(replay, entry, text, taxonomy, unit_slug):
    signals = collect_entry_unit_signals(entry, text)
    return {
        topic["topic_slug"]: replay._score_entry_against_taxonomy_topic(signals, topic)
        for topic in replay._iter_content_taxonomy_topics(taxonomy)
        if topic.get("unit_slug") == unit_slug
    }


def match_dict(match, conf_min):
    slug = str(getattr(match, "topic_slug", "") or "") if match else ""
    confidence = float(getattr(match, "confidence", 0.0)) if match else 0.0
    ambiguous = bool(getattr(match, "ambiguous", True)) if match else True
    return {
        "topic_slug": slug,
        "confidence": confidence,
        "ambiguous": ambiguous,
        "reasons": list(getattr(match, "reasons", []) or []) if match else [],
        "indecision": {
            "empty": not slug,
            "ambiguous": ambiguous,
            "below_conf_min": confidence < conf_min,
            "conf_min": conf_min,
        },
    }


def run(replay, effect, root, overrides):
    captured = {}
    original = replay.RA.propagar_vocabulario_por_headings

    def instrument(passe1, taxonomy, auto_sub, *, conf_min, min_entries, df_max):
        assert not captured, "propagacao chamada mais de uma vez"
        base_aliases = aliases(taxonomy)
        target_row = next(row for row in passe1 if str(row[0].get("id")) == TARGET)
        target_entry, target_text, target_unit, target_match = target_row
        captured.update({
            "parameters": {"conf_min": conf_min, "min_entries": min_entries, "df_max": df_max,
                           "passe1_entries": len(passe1)},
            "target": {
                "unit_slug": target_unit,
                "pass1": match_dict(target_match, conf_min),
                "scores_pass1": scores(replay, target_entry, target_text, taxonomy, target_unit),
            },
        })
        augmented = {}

        def traced_auto(entry, tax, text, **kwargs):
            if not augmented:
                augmented.update({
                    key: sorted(values - base_aliases.get(key, set()))
                    for key, values in aliases(tax).items()
                    if values - base_aliases.get(key, set())
                })
            result = auto_sub(entry, tax, text, **kwargs)
            if str(entry.get("id")) == TARGET:
                unit_slug = str(kwargs.get("winning_unit_slug") or "")
                captured["target"]["scores_pass2"] = scores(replay, entry, text, tax, unit_slug)
                captured["target"]["pass2"] = match_dict(result, conf_min)
            return result

        changed = original(passe1, taxonomy, traced_auto, conf_min=conf_min,
                           min_entries=min_entries, df_max=df_max)
        captured["changed_entries"] = changed
        captured["learned_aliases"] = [
            {"unit_slug": key[0], "topic_slug": key[1], "aliases": values}
            for key, values in sorted(augmented.items())
        ]

        toks_by_entry = {}
        df = collections.Counter()
        for entry, text, _unit_slug, _match in passe1:
            toks = RA._tokens_headings(collect_entry_unit_signals(entry, text), MOTOR_GENERIC_STEMS)
            toks_by_entry[id(entry)] = toks
            df.update(toks)
        metadata = []
        for (unit_slug, topic_slug), values in sorted(augmented.items()):
            for token in values:
                donors = []
                owners = set()
                for entry, _text, candidate_unit, match in passe1:
                    if (candidate_unit == unit_slug and match and match.topic_slug and not match.ambiguous
                            and match.confidence >= conf_min and token in toks_by_entry[id(entry)]):
                        owners.add(str(match.topic_slug))
                        if str(match.topic_slug) == topic_slug:
                            donors.append(str(entry.get("id")))
                metadata.append({
                    "unit_slug": unit_slug,
                    "topic_slug": topic_slug,
                    "alias": token,
                    "generic_stem": token in MOTOR_GENERIC_STEMS,
                    "document_frequency": df[token],
                    "df_rate": df[token] / len(passe1),
                    "df_limit_count": df_max * len(passe1),
                    "confident_owners_in_unit": sorted(owners),
                    "donor_count": len(donors),
                    "donor_entries": sorted(donors),
                })
        captured["alias_evidence"] = metadata
        return changed

    replay.RA.propagar_vocabulario_por_headings = instrument
    try:
        if overrides:
            _saved, entries, _raw = effect.replay_with_patch(replay, root, overrides)
        else:
            _saved, entries, _raw = replay.replay(root)
    finally:
        replay.RA.propagar_vocabulario_por_headings = original
    target = entries[TARGET]
    captured["target"]["final"] = {
        "unit_slug": str(target.get("computed_unit_slug") or ""),
        "subunit_slug": str(target.get("computed_subunit_slug") or ""),
        "confidence": float(target.get("subunit_match_confidence") or 0.0),
        "reasons": list(target.get("subunit_match_reasons") or []),
    }
    for key in ("scores_pass1", "scores_pass2"):
        captured["target"][key] = {
            slug: captured["target"].get(key, {}).get(slug, 0.0) for slug in sorted(COMPETITORS)
        }
    return captured


def main():
    out = HERE / "diag_propagacao_token_CG_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    replay_path = EVIDENCE / "replay_unidade_21-09.py"
    effect_path = EVIDENCE / "regra_secao_efeito_subunidade_21-09.py"
    rule_path = EVIDENCE / "regra_secao_unidade_21-09.json"
    replay = load("wi_replay", replay_path)
    effect = load("wi_effect", effect_path)
    compare = load("wi_compare", EVIDENCE / "compara_herancas_15-09.py")
    assert replay.RA is RA and effect.LOCAL_RA is RA

    decisions = json.loads(rule_path.read_text(encoding="utf-8"))["decisions"]
    overrides = {
        str(item["id"]): {"before": item["before"], "after": item["section_match"]["slug"],
                          "raw_slug": item["raw"]["slug"]}
        for item in decisions if item["curso"] == "CG" and item["changed"]["R-sem-misto"]
    }
    assert set(overrides) == {"maptextures", "pagina-com-videos-sobre-mapeamento-de-texturas-07bbe3"}
    root = DATA / ".frzero/pacote_fontes_15-09" / compare.mede.NOMES["CG"]
    runs = {"without_patch": run(replay, effect, root, {}),
            "with_patch": run(replay, effect, root, overrides)}

    alias_sets = {
        label: {(row["unit_slug"], row["topic_slug"]): set(row["aliases"])
                for row in data["learned_aliases"]}
        for label, data in runs.items()
    }
    keys = sorted(set(alias_sets["without_patch"]) | set(alias_sets["with_patch"]))
    diff = [{
        "unit_slug": key[0], "topic_slug": key[1],
        "added_with_patch": sorted(alias_sets["with_patch"].get(key, set()) - alias_sets["without_patch"].get(key, set())),
        "removed_with_patch": sorted(alias_sets["without_patch"].get(key, set()) - alias_sets["with_patch"].get(key, set())),
    } for key in keys if alias_sets["without_patch"].get(key, set()) != alias_sets["with_patch"].get(key, set())]

    report = {
        "head": "ce02a8f47285c30c16f12b131bdf86c46dcba64e",
        "course": "CG",
        "runs": runs,
        "learned_alias_diff": diff,
        "source_locations": {
            "safeguards": "src/builder/routing/resolver_apply.py:264-272",
            "alias_selection": "src/builder/routing/resolver_apply.py:289-313",
            "real_call": "src/builder/routing/resolver_apply.py:574-576",
            "indecision_gate": "src/builder/routing/resolver_apply.py:318-335",
            "scoring": "src/builder/routing/file_map.py:172-257",
        },
        "input_hashes": {str(path): sha256(path) for path in (replay_path, effect_path, rule_path, root / "manifest.json")},
        "limitations": ["Somente CG; duas entradas patchadas juntas; patch e instrumentacao em memoria; sem gold, rede, LLM, build ou escrita em src/."],
    }
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"learned_alias_diff": diff,
                      "target_without_patch": runs["without_patch"]["target"],
                      "target_with_patch": runs["with_patch"]["target"]}, ensure_ascii=False, indent=2))
    print("SHA256", sha256(out))


if __name__ == "__main__":
    main()
