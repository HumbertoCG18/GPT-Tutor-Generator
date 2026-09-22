"""Mede R-sem-misto dentro da fase real; gold entra somente na avaliacao."""
import collections
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

# Importar o src do worktree antes de carregar os replays nao rastreados do PRINCIPAL.
from src.builder.routing import file_map as LOCAL_FM  # noqa: E402
from src.builder.routing import resolver_apply as LOCAL_RA  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


REPLAY_PATH = EVIDENCE / "replay_unidade_21-09.py"
BASE_PATH = EVIDENCE / "replay_unidade_21-09.json"
RULE_PATH = EVIDENCE / "regra_secao_unidade_21-09.json"
EXPECTED = {
    REPLAY_PATH.name: "a39e95af186466a53c5cf3ebc15164cdb30c2ee4e3ad820f8534c7fa0bfb81bf",
    BASE_PATH.name: "8971a419ca105bb3611a3d53364ab8fe6a523e9fe60f08cdb03db485e62242c8",
    RULE_PATH.name: "2af303fa5ce592c1862afd90837df80d627aa07d40b580bacb2e0328bd7b29ca",
}


def replay_with_patch(replay, root, overrides):
    """Monkeypatch apenas a reconciliacao; scorer e restante da fase sao reais."""
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
        assert not kwargs["block_is_manual"] and not kwargs["has_manual_unit"]
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
    assert hit == set(overrides), ("overrides nao exercidos", sorted(set(overrides) - hit))
    return result


def field_changes(before, after, fields):
    changes = []
    for eid, old in before.items():
        new = after[eid]
        changed = {field: {"before": old.get(field), "after": new.get(field)}
                   for field in fields if old.get(field) != new.get(field)}
        if changed:
            changes.append({"manifest_id": eid, "fields": changed})
    return changes


def main():
    out = HERE / "regra_secao_efeito_subunidade_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    for path in (REPLAY_PATH, BASE_PATH, RULE_PATH):
        assert sha256(path) == EXPECTED[path.name], (path.name, sha256(path))

    replay = load("wf_replay", REPLAY_PATH)
    compare = load("wf_compare", EVIDENCE / "compara_herancas_15-09.py")
    mede = compare.mede
    assert replay.FM is LOCAL_FM and replay.RA is LOCAL_RA
    assert Path(replay.FM.__file__).resolve().is_relative_to(ROOT)

    rule = read(RULE_PATH)
    frozen = collections.defaultdict(dict)
    for decision in rule["decisions"]:
        if decision["changed"]["R-sem-misto"]:
            frozen[decision["curso"]][str(decision["id"])] = {
                "before": decision["before"],
                "after": decision["section_match"]["slug"],
                "raw_slug": decision["raw"]["slug"],
            }
    assert {sig: len(v) for sig, v in frozen.items()} == {"SO": 6, "CG": 2}

    runs, fidelity, input_hashes = {}, collections.Counter(), {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
                       else ".frzero/pacote_fontes_15-09") / name
        manifest = root / "manifest.json"
        input_hashes[str(manifest)] = sha256(manifest)
        saved, baseline, raw = replay.replay(root)
        _, patched, patched_raw = replay_with_patch(replay, root, frozen.get(sig, {}))
        assert raw == patched_raw
        fidelity["manifest_n"] += len(saved)
        fidelity["baseline_fiel"] += sum(
            str(saved[eid].get("computed_unit_slug") or "")
            == str(baseline[eid].get("computed_unit_slug") or "")
            for eid in saved
        )
        runs[sig] = {"root": root, "saved": saved, "baseline": baseline, "patched": patched}
        print(sig, "entries", len(saved), "unit_changes",
              sum(baseline[e]["computed_unit_slug"] != patched[e]["computed_unit_slug"] for e in saved), flush=True)
    assert (fidelity["manifest_n"], fidelity["baseline_fiel"]) == (338, 338)

    totals = {"baseline": collections.Counter(), "patched": collections.Counter()}
    courses = {"baseline": {}, "patched": {}}
    unit_changes, sub_changes = [], []
    changed_manifest_ids = set()
    diagnostic_fields = ("unit_match_reasons", "unit_match_confidence", "unit_block_conflict",
                         "subunit_match_reasons", "subunit_match_confidence")
    diagnostics_outside = []
    eight_subunits = []

    for sig, run in runs.items():
        root, baseline, patched = run["root"], run["baseline"], run["patched"]
        ref = DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
        ref_entries = {str(e["id"]): e for e in read(ref / "manifest.json")["entries"]}
        source_index = compare.indexed(list(run["saved"].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(EVIDENCE / f"herancas_{sig}_15-09.json")["entries"]}
        gb, gu, gs, gsp = mede.golds(sig)
        rows = list(csv.DictReader((EVIDENCE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig")))
        by_manifest = {}
        for row in rows:
            old = ref_entries.get(mapping.get(row["entry_id"]) or "")
            hits = source_index.get(compare.source(old), []) if old else []
            assert len(hits) <= 1, (sig, row["entry_id"], "origem nao unica")
            if hits:
                by_manifest[str(hits[0]["id"])] = row["entry_id"]

        for label, entries in (("baseline", baseline), ("patched", patched)):
            c = collections.Counter()
            for row in rows:
                gold_id = row["entry_id"]
                old = ref_entries.get(mapping.get(gold_id) or "")
                hits = source_index.get(compare.source(old), []) if old else []
                entry = entries[str(hits[0]["id"])] if hits else None
                if row["bloco"] != "":
                    c["bloco_n"] += 1
                    c["bloco"] += bool(entry and compare.predictions(root, entry)[0] == gb[gold_id])
                if row["unidade"] != "":
                    c["unidade_n"] += 1
                    c["unidade"] += bool(entry and compare.predictions(root, entry)[1] in gu[gold_id])
                if row["sub_primario"] != "":
                    c["sub_n"] += 1
                    pred = compare.predictions(root, entry)[2] if entry else None
                    c["sub_primaria"] += bool(entry and pred in gsp[gold_id])
                    c["sub_aceita"] += bool(entry and pred in gs[gold_id])
                    c["sub_ausente"] += entry is None
            courses[label][sig] = dict(c)
            totals[label].update(c)

        for eid, old in baseline.items():
            new = patched[eid]
            before_u, after_u = str(old.get("computed_unit_slug") or ""), str(new.get("computed_unit_slug") or "")
            before_s, after_s = str(old.get("computed_subunit_slug") or ""), str(new.get("computed_subunit_slug") or "")
            gold_id = by_manifest.get(eid)
            if before_u != after_u:
                changed_manifest_ids.add((sig, eid))
                truth = gu.get(gold_id, ()) if gold_id else ()
                unit_changes.append({"curso": sig, "id": gold_id, "manifest_id": eid,
                                     "before": before_u, "after": after_u,
                                     "before_correct": before_u in truth if truth else None,
                                     "after_correct": after_u in truth if truth else None,
                                     "frozen_eight": eid in frozen.get(sig, {})})
            if before_s != after_s:
                prim = gsp.get(gold_id, ()) if gold_id else ()
                accepted = gs.get(gold_id, ()) if gold_id else ()
                sub_changes.append({"curso": sig, "id": gold_id, "manifest_id": eid,
                                    "before": before_s, "after": after_s,
                                    "primary_gain": bool(prim and before_s not in prim and after_s in prim),
                                    "primary_loss": bool(prim and before_s in prim and after_s not in prim),
                                    "accepted_gain": bool(accepted and before_s not in accepted and after_s in accepted),
                                    "accepted_loss": bool(accepted and before_s in accepted and after_s not in accepted),
                                    "unit_changed": before_u != after_u})

        topic_units = collections.defaultdict(set)
        for unit in read(root / "course/.content_taxonomy.json").get("units", []):
            for topic in unit.get("topics", []):
                topic_units[str(topic.get("slug") or topic.get("topic_slug") or "")].add(
                    str(topic.get("unit_slug") or unit.get("slug") or ""))
        for eid, target in frozen.get(sig, {}).items():
            sub = str(baseline[eid].get("computed_subunit_slug") or "")
            eight_subunits.append({"curso": sig, "manifest_id": eid, "subunit": sub,
                                   "topic_units": sorted(topic_units.get(sub, set())),
                                   "belongs_to_old_unit": target["before"] in topic_units.get(sub, set())})

        for change in field_changes(baseline, patched, diagnostic_fields):
            if (sig, change["manifest_id"]) not in changed_manifest_ids:
                diagnostics_outside.append({"curso": sig, **change})

    for label in ("baseline", "patched"):
        t = totals[label]
        assert (t["bloco"], t["bloco_n"], t["unidade_n"], t["sub_n"], t["sub_ausente"]) == (213, 237, 284, 251, 8)
    assert (totals["baseline"]["unidade"], totals["baseline"]["sub_primaria"],
            totals["baseline"]["sub_aceita"]) == (239, 84, 108)
    assert len(unit_changes) >= 8 and sum(x["frozen_eight"] for x in unit_changes) == 8

    sub_deltas = {}
    for metric in ("primary", "accepted"):
        gain_key, loss_key = f"{metric}_gain", f"{metric}_loss"
        sub_deltas[metric] = {
            "gains": [x for x in sub_changes if x[gain_key]],
            "losses": [x for x in sub_changes if x[loss_key]],
        }
    report = {
        "head": "ce02a8f47285c30c16f12b131bdf86c46dcba64e",
        "rule": "R-sem-misto; 8 decisoes congeladas antes do gold e revalidadas contra o scorer bruto durante a fase",
        "patch_point": {
            "product": "src/builder/routing/file_map.py:795-812 (antes da queda final em bloco-vence), chamada em resolver_apply.py:507",
            # Conserto do coordenador (21/09): resolver_apply importa a funcao localmente a cada
            # chamada (resolver_apply.py:394-396), entao o patch vai no atributo de file_map.
            "harness": "monkeypatch em memoria de file_map.reconcile_unit_with_block (import local em resolver_apply.py:394-396); src/ intacto",
            "reason": "secao-vence-bloco=<id>",
        },
        "input_hashes": {**input_hashes, **{str(p): sha256(p) for p in (REPLAY_PATH, BASE_PATH, RULE_PATH)}},
        "fidelity": dict(fidelity),
        "totals": {k: dict(v) for k, v in totals.items()},
        "courses": courses,
        "unit_changes": unit_changes,
        "unit_changes_beyond_frozen_eight": [x for x in unit_changes if not x["frozen_eight"]],
        "subunit_changes": sub_changes,
        "subunit_deltas": sub_deltas,
        "frozen_eight_baseline_subunit_membership": eight_subunits,
        "diagnostic_changes_outside_unit_changes": diagnostics_outside,
        "limitations": [
            "Blocos sao congelados; a fase real reexecutada nao recalcula o motor de bloco.",
            "A lista das 8 decisoes e congelada; o harness nao reimplementa a regua de secao.",
            "Gold e carregado somente depois das duas execucoes e serve apenas para avaliacao.",
            "Ausentes permanecem nos denominadores; 0 rede, LLM, build/rebuild e escrita em src/.",
        ],
    }
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("TOTALS", json.dumps(report["totals"], ensure_ascii=False))
    print("UNIT_CHANGES", len(unit_changes), "BEYOND", len(report["unit_changes_beyond_frozen_eight"]))
    print("SUB_CHANGES", len(sub_changes), "OUTSIDE_DIAGNOSTICS", len(diagnostics_outside))
    print("SHA256", sha256(out))


if __name__ == "__main__":
    main()
