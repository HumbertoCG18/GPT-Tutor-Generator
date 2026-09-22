"""Captura aliases da 2a passada do SO, sem alterar src/."""
import collections
import copy
import csv
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

from src.builder.routing import file_map as LOCAL_FM  # noqa: E402
from src.builder.routing import resolver_apply as LOCAL_RA  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402


TARGETS = {
    "laminas-sockets-material-alternativo-em-pt",
    "exemplo-threads-em-c-exemplo1",
    "exemplo-threads-em-c-exemplo2",
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alias_map(taxonomy):
    return {
        (str(unit.get("slug") or ""), str(topic.get("slug") or "")): set(topic.get("aliases") or [])
        for unit in taxonomy.get("units", []) or []
        for topic in unit.get("topics", []) or []
    }


def match_dict(match):
    return {
        "topic_slug": str(getattr(match, "topic_slug", "") or ""),
        "confidence": float(getattr(match, "confidence", 0.0)),
        "ambiguous": bool(getattr(match, "ambiguous", False)),
        "reasons": list(getattr(match, "reasons", ()) or ()),
    }


def capture_propagation(replay, root, overrides=None):
    capture = {"aliases": {}, "origins": {}, "target_ablations": {}}
    original_prop = replay.RA.propagar_vocabulario_por_headings

    def traced_prop(passe1, taxonomy, auto_fn, *, conf_min, min_entries, df_max):
        before = alias_map(taxonomy)
        toks_by_entry = {}
        df = collections.Counter()
        for entry, texto, _unit_slug, _match in passe1:
            toks = LOCAL_RA._tokens_headings(
                LOCAL_RA.collect_entry_unit_signals(entry, texto), MOTOR_GENERIC_STEMS
            )
            toks_by_entry[id(entry)] = toks
            df.update(toks)
        units = {str(u.get("slug") or ""): u for u in taxonomy.get("units", []) or []}
        vocab_unit = {}
        for slug, unit in units.items():
            parts = [str(unit.get("title") or "")] + [
                f"{topic.get('label', '')} {' '.join(topic.get('aliases') or [])}"
                for topic in unit.get("topics", []) or []
            ]
            vocab_unit[slug] = {
                token for token in LOCAL_RA.normalize_match_text(" ".join(parts)).split() if len(token) >= 4
            }
        owners = collections.defaultdict(lambda: collections.defaultdict(set))
        source_rows = collections.defaultdict(list)
        for entry, _texto, unit_slug, match in passe1:
            if not match or not match.topic_slug or match.ambiguous or match.confidence < conf_min:
                continue
            for token in toks_by_entry[id(entry)] - vocab_unit.get(unit_slug, set()):
                if df[token] > df_max * len(passe1):
                    continue
                owners[unit_slug][token].add(match.topic_slug)
                source_rows[(unit_slug, str(match.topic_slug), token)].append({
                    "manifest_id": str(entry.get("id") or ""),
                    "confidence": float(match.confidence),
                })

        def traced_auto(entry, injected_taxonomy, texto, *, winning_unit_slug):
            after = alias_map(injected_taxonomy)
            additions = {key: values - before.get(key, set()) for key, values in after.items()}
            for key, values in additions.items():
                if values:
                    capture["aliases"]["|".join(key)] = sorted(values)
                    for token in values:
                        origin_key = (key[0], key[1], token)
                        capture["origins"]["|".join(origin_key)] = source_rows.get(origin_key, [])
            result = auto_fn(entry, injected_taxonomy, texto, winning_unit_slug=winning_unit_slug)
            eid = str(entry.get("id") or "")
            if eid in TARGETS:
                winner_key = (winning_unit_slug, str(getattr(result, "topic_slug", "") or ""))
                trials = []
                for token in sorted(additions.get(winner_key, set())):
                    ablated = copy.deepcopy(injected_taxonomy)
                    for unit in ablated.get("units", []) or []:
                        if str(unit.get("slug") or "") != winner_key[0]:
                            continue
                        for topic in unit.get("topics", []) or []:
                            if str(topic.get("slug") or "") == winner_key[1]:
                                topic["aliases"] = [x for x in topic.get("aliases", []) if x != token]
                    trial = auto_fn(entry, ablated, texto, winning_unit_slug=winning_unit_slug)
                    trials.append({"removed_alias": token, "result": match_dict(trial)})
                capture["target_ablations"][eid] = {
                    "winning_unit_slug": winning_unit_slug,
                    "full": match_dict(result),
                    "single_alias_removals": trials,
                }
            return result

        return original_prop(
            passe1, taxonomy, traced_auto,
            conf_min=conf_min, min_entries=min_entries, df_max=df_max,
        )

    replay.RA.propagar_vocabulario_por_headings = traced_prop
    try:
        if overrides is None:
            saved, entries, raw = replay.replay(root)
        else:
            saved, entries, raw = replay_with_patch(replay, root, overrides)
    finally:
        replay.RA.propagar_vocabulario_por_headings = original_prop
    return saved, entries, raw, capture


def replay_with_patch(replay, root, overrides):
    original_auto = replay.auto_unit
    original_reconcile = replay.FM.reconcile_unit_with_block
    current, hit = {}, set()

    def traced_auto(entry, *args, **kwargs):
        match = original_auto(entry, *args, **kwargs)
        current.update(id=str(entry["id"]), slug=str(match.slug or ""), ambiguous=bool(match.ambiguous))
        return match

    def section_wins(**kwargs):
        base = original_reconcile(**kwargs)
        eid = current.pop("id", None)
        target = overrides.get(eid)
        if target is None:
            return base
        assert current.pop("slug") == target["raw_slug"] == target["after"]
        assert current.pop("ambiguous") is False
        assert base[0] == target["before"] and base[0] != target["after"]
        hit.add(eid)
        block_id, block_unit = kwargs["computed_block_id"], kwargs["block_unit_slug"]
        conflict = ({"unit": target["after"], "block_unit": block_unit, "block_id": block_id}
                    if block_id and block_unit and block_unit != target["after"] else {})
        return target["after"], [f"secao-vence-bloco={block_id}"], conflict

    replay.auto_unit = traced_auto
    replay.FM.reconcile_unit_with_block = section_wins
    try:
        result = replay.replay(root)
    finally:
        replay.auto_unit = original_auto
        replay.FM.reconcile_unit_with_block = original_reconcile
    assert hit == set(overrides)
    return result


def main():
    out = HERE / "diag_propagacao_token_SO_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    replay_path = EVIDENCE / "replay_unidade_21-09.py"
    rule_path = EVIDENCE / "regra_secao_unidade_21-09.json"
    replay = load("wj_replay", replay_path)
    compare = load("wj_compare", EVIDENCE / "compara_herancas_15-09.py")
    assert replay.FM is LOCAL_FM and replay.RA is LOCAL_RA

    overrides = {
        str(d["id"]): {"before": d["before"], "after": d["section_match"]["slug"], "raw_slug": d["raw"]["slug"]}
        for d in read(rule_path)["decisions"] if d["curso"] == "SO" and d["changed"]["R-sem-misto"]
    }
    assert len(overrides) == 6
    root = DATA / ".frzero/pacote_fontes_15-09" / compare.mede.NOMES["SO"]
    saved, baseline, raw, before_capture = capture_propagation(replay, root)
    _, patched, patched_raw, after_capture = capture_propagation(replay, root, overrides)
    assert raw == patched_raw
    assert all(saved[eid].get("computed_unit_slug") == baseline[eid].get("computed_unit_slug") for eid in saved)

    _gb, _gu, gold_accepted, gold_primary = compare.mede.golds("SO")
    rows = list(csv.DictReader((EVIDENCE / "herancas_SO_15-09.csv").open(encoding="utf-8-sig")))
    ruled_ids = {row["entry_id"] for row in rows}
    collateral = []
    for eid in sorted(TARGETS):
        old, new = baseline[eid], patched[eid]
        collateral.append({
            "manifest_id": eid,
            "unit": str(old.get("computed_unit_slug") or ""),
            "before_subunit": str(old.get("computed_subunit_slug") or ""),
            "after_subunit": str(new.get("computed_subunit_slug") or ""),
            "before_reasons": old.get("subunit_match_reasons") or [],
            "after_reasons": new.get("subunit_match_reasons") or [],
            "baseline_alias_ablation": before_capture["target_ablations"].get(eid),
            "patched_alias_ablation": after_capture["target_ablations"].get(eid),
            "gold": {
                "in_ruler": eid in ruled_ids,
                "primary": list(gold_primary.get(eid, ())),
                "accepted": list(gold_accepted.get(eid, ())),
            },
        })

    report = {
        "head": "ce02a8f47285c30c16f12b131bdf86c46dcba64e",
        "course": "SO",
        "runs": {"without_patch": before_capture, "with_patch": after_capture},
        "alias_diff": {
            "removed_by_patch": {
                key: sorted(set(values) - set(after_capture["aliases"].get(key, [])))
                for key, values in before_capture["aliases"].items()
                if set(values) - set(after_capture["aliases"].get(key, []))
            },
            "added_by_patch": {
                key: sorted(set(values) - set(before_capture["aliases"].get(key, [])))
                for key, values in after_capture["aliases"].items()
                if set(values) - set(before_capture["aliases"].get(key, []))
            },
        },
        "patched_unit_ids": sorted(overrides),
        "collateral_entries": collateral,
        "input_hashes": {str(path): sha256(path) for path in (replay_path, rule_path, root / "manifest.json")},
        "instrumentation": "wrapper em memoria de resolver_apply.propagar_vocabulario_por_headings; aliases observados na taxonomia copiada entregue ao scorer; ablacao individual em memoria",
        "source": "src/builder/routing/resolver_apply.py:262-346",
        "limitations": [
            "Somente SO; uma execucao sem patch e uma com as 6 decisoes juntas.",
            "Blocos congelados; sem rede, LLM, build, escrita em src/ ou proposta de correcao.",
        ],
    }
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"alias_diff": report["alias_diff"], "collateral_entries": collateral}, ensure_ascii=False, indent=2))
    print("SHA256", sha256(out))


if __name__ == "__main__":
    main()
