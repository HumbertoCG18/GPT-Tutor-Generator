"""Audita captura e granularidade em dados reais; não escreve nos repositórios."""
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import socket

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("meta_driver", HERE / "metadados_blocos_15-09.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
socket.socket.connect = d.blocked
socket.create_connection = d.blocked

from src.builder.sources.moodle import backfill_moodle_structure_from_api, backfill_moodle_label_from_api
from src.builder.sources.moodle_labels import parse_card_dates, derive_card_block_map, build_lesson_topic_index
from src.builder.routing.motor.context import build_motor_context
from src.builder.routing.motor.card_stream import card_windows
from src.builder.routing.motor.window_provider import provider_labels
from src.builder.routing.file_map import unit_of_block_or_neighbor


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    out = HERE / "cadeia_metadados_verificada_15-09.json"
    assert not out.exists()
    results = {}
    for course, (name, raw_arm) in d.audit.COURSES.items():
        old_root = d.ROOT / ".frzero/implementacao_taxonomia_15-09" / name
        raw_root = d.ROOT / ".frzero" / raw_arm / name
        capture = old_root / "raw/moodle/contents.json"
        contents = d.read(capture)
        old = d.read(old_root / "manifest.json")["entries"]
        raw = d.read(raw_root / "manifest.json")["entries"]
        by_old = d.compare.indexed(old)
        by_raw = d.compare.indexed(raw)
        blocks = d.read(raw_root / "course/.timeline_index.json")["blocks"]
        year = int(blocks[0]["period_start"][:4])
        structure = backfill_moodle_structure_from_api(raw, contents, year)
        labels = backfill_moodle_label_from_api(raw, contents)
        enriched = copy.deepcopy(raw)
        for e in enriched:
            if not e.get("moodle_label") and labels.get(e["id"]):
                e["moodle_label"] = labels[e["id"]]
        enriched_structure = backfill_moodle_structure_from_api(enriched, contents, year)
        counts = collections.Counter()
        differences = []
        gold = d.compare.mede.golds(course)
        curricular = []
        for e in raw:
            matches = by_old.get(d.compare.source(e), [])
            if len(matches) != 1 or len(by_raw[d.compare.source(e)]) != 1:
                continue
            prior = matches[0]
            eid = e["id"]
            expected = {f: prior.get(f) for f in d.FIELDS["ordem"]}
            counts["common_entries"] += 1
            for tag, found in (("raw", structure), ("with_labels", enriched_structure)):
                counts[f"{tag}_matched"] += eid in found
                if eid in found:
                    same = found[eid] == expected
                    counts[f"{tag}_exact_historical"] += same
                    if not same:
                        differences.append({"id": eid, "stage": tag, "parsed": found[eid], "historical": expected})
            if prior["id"] in gold[0] and gold[1].get(prior["id"]):
                true_block = gold[0][prior["id"]]
                temporal_unit, neighbor = unit_of_block_or_neighbor(true_block, blocks)
                if temporal_unit:
                    counts["gold_block_and_unit_with_block_unit"] += 1
                    compatible = temporal_unit in gold[1][prior["id"]]
                    counts["gold_block_unit_compatible"] += compatible
                    if not compatible:
                        curricular.append({"id": prior["id"], "gold_block": true_block,
                            "derived_block_unit": temporal_unit, "neighbor": neighbor,
                            "gold_units": sorted(gold[1][prior["id"]])})
        parsed = parse_card_dates(contents, year)
        cards = derive_card_block_map(parsed, blocks)
        card_path = old_root / "course/.card_block_map.json"
        historical_cards = d.read(card_path) if card_path.is_file() else {}
        date_check = {k: {"same_dates_format": (v.get("dates", []), v.get("format", "")) ==
                        (cards.get(k, {}).get("dates", []), cards.get(k, {}).get("format", "")),
                         "rederived": k in cards}
                      for k, v in historical_cards.items() if v.get("source") == "labels" and v.get("dates")}
        controls = {}
        for arm in ("ordem", "datas_cards"):
            root = d.ROOT / ".frzero" / f"metadados_{arm}_integral_15-09" / name
            if not root.is_dir():
                continue
            manifest = d.read(root / "manifest.json")
            ctx = build_motor_context(root, manifest["course"]["course_name"])
            windows = card_windows(manifest["entries"], ctx) if arm == "ordem" else {}
            count = collections.defaultdict(collections.Counter)
            for e in manifest["entries"]:
                match = by_old.get(d.compare.source(e), [])
                if len(match) != 1 or match[0]["id"] not in gold[0]:
                    continue
                raw_matches = by_raw.get(d.compare.source(e), [])
                if len(raw_matches) != 1:
                    continue
                truth = gold[0][match[0]["id"]]
                before = d.compare.predictions(raw_root, raw_matches[0])[0] == truth
                after = d.compare.predictions(root, e)[0] == truth
                status = {(True, True): "kept_correct", (False, True): "gain",
                          (True, False): "loss", (False, False): "kept_wrong"}[before, after]
                win = windows.get(e["id"], []) if arm == "ordem" else provider_labels(e, ctx)
                win = [str((ctx.block_by_ref(ref) or {}).get("id") or ref) for ref in win]
                count[status]["entries"] += 1
                count[status]["signal_window"] += bool(win)
                count[status]["gold_in_signal_window"] += truth in win
            controls[arm] = {k: dict(v) for k, v in count.items()}
        results[course] = {"capture": str(capture), "capture_sha256": digest(capture),
            "same_as_product_capture": digest(capture) == digest(d.ROOT.parent / name / "raw/moodle/contents.json"),
            "raw_reconstruction_has_capture": (raw_root / "raw/moodle/contents.json").is_file(),
            "sections": len(contents), "modules": sum(len(s.get("modules", [])) for s in contents),
            "counts": dict(counts), "structure_differences": differences,
            "historical_dates_check": date_check,
            "derived_lessons": len(build_lesson_topic_index(contents, year)["by_date"]),
            "curricular_disagreements": curricular, "controls": controls}
        print(course, json.dumps({"counts": dict(counts), "capture_in_raw": results[course]["raw_reconstruction_has_capture"],
              "dates_exact": sum(v["same_dates_format"] for v in date_check.values()), "dates_n": len(date_check),
              "curricular_disagreements": len(curricular)}))
    from src.builder.timeline.unit_matcher import assign_units_positional, assign_units_by_work_milestones
    from src.builder.routing.file_map import reconcile_unit_with_block
    es2 = d.ROOT / ".frzero/cru_fontes_15-09/Engenharia-Software-2-Tutor"
    blocks = d.read(es2 / "course/.timeline_index.json")["blocks"]
    units = d.read(es2 / "course/.content_taxonomy.json")["units"]
    candidates = [b for b in blocks if not b.get("source_kind")]
    assert not assign_units_by_work_milestones(blocks, candidates, units)
    positional = assign_units_positional(candidates, units)
    probe = [{"block": b["id"], "stored": [b["unit_slug"], b["unit_confidence"]], "replayed": list(p)}
             for b, p in zip(candidates, positional, strict=True) if b["id"] in ("bloco-08", "bloco-09")]
    assert len(probe) == 2 and all(p["stored"] == p["replayed"] for p in probe)
    # Contract probe, not a claim that a real entry had confidence .99.
    confidence_probe = [reconcile_unit_with_block(computed_unit_slug=units[0]["slug"], unit_confidence=.99,
        computed_block_id="bloco-09", block_confidence=c, block_unit_slug=units[1]["slug"],
        block_is_manual=False, has_manual_unit=False) for c in (0, .4, 1)]
    assert confidence_probe[0] == confidence_probe[1] == confidence_probe[2]
    assert not d.CALLS
    out.write_text(json.dumps({"courses": results, "calls": d.CALLS, "es2_positional_probe": probe,
        "contract_confidence_probe": confidence_probe}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
