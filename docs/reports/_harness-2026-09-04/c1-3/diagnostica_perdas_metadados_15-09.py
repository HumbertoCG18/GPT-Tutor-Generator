"""Replay read-only das perdas, usando manifests e artefatos reais de 15/09."""
import collections
import copy
from dataclasses import asdict
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

from src.builder.routing.motor import anchor_engine, card_stream, disambiguator as dis
from src.builder.routing.motor.apply import apply_anchor_engine, TEMPORAL_KEYS
from src.builder.routing.motor.context import build_motor_context
from src.builder.routing.motor.card_stream import card_windows, _week_blocks
from src.builder.routing.motor.window_provider import resolve_window, _card_entry
from src.builder.routing.file_map import unit_of_block_or_neighbor
from src.builder.routing.motor.due_window import tier2_due_scope


def main():
    out = HERE / "diagnostico_perdas_metadados_verificado_15-09.json"
    assert not out.exists(), "preservar resultado existente"
    cases = []
    for filename in ("placar_metadados_7cursos_15-09.json", "placar_datas_cards_piloto_15-09.json"):
        cases += [f for f in d.read(HERE / filename)["flips"]
                  if any(v == [1, 0] for v in f["flips"].values())]
    runs, report = {}, []
    for case in cases:
        course, arm, eid = case["course"], case["arm"], case["entry_id"]
        name, raw = d.audit.COURSES[course]
        mapping = {e["entry_id"]: e["new_id"] for e in d.read(HERE / f"herancas_{course}_15-09.json")["entries"]}
        new_id = mapping[eid]
        row = {**case, "gold_block": d.compare.mede.golds(course)[0].get(eid),
               "gold_units": sorted(d.compare.mede.golds(course)[1].get(eid, []))}
        for label, parent in (("before", raw), ("after", f"metadados_{arm}_integral_15-09")):
            root = d.ROOT / ".frzero" / parent / name
            if root not in runs:
                manifest = d.read(root / "manifest.json")
                entries = manifest["entries"]
                texts = {e["id"]: d.compare._entry_markdown_text_for_file_map(root, e) for e in entries}
                traces = collections.defaultdict(list)
                original = anchor_engine.disambiguate

                def traced(entry, window, ctx, markdown="", provider="", original=original, traces=traces):
                    answer = original(entry, window, ctx, markdown, provider)
                    traces[entry["id"]].append(asdict(answer) | {"provider": provider})
                    return answer

                anchor_engine.disambiguate = traced
                try:
                    replay = apply_anchor_engine(copy.deepcopy(entries), root, manifest["course"]["course_name"],
                                                 voter=None, markdown_fn=lambda e, texts=texts: texts[e["id"]])
                finally:
                    anchor_engine.disambiguate = original
                mismatches = [e["id"] for e, r in zip(entries, replay, strict=True)
                              if any(e.get(k) != r.get(k) for k in TEMPORAL_KEYS)]
                assert not mismatches, (str(root), "replay divergiu", mismatches)
                ctx = build_motor_context(root, manifest["course"]["course_name"])
                alignments = {}
                original_align = card_stream._align

                def traced_align(mats, weeks, context, original_align=original_align, alignments=alignments):
                    answer = original_align(mats, weeks, context)
                    signatures = [dis._toks(t + " " + " ".join(" ".join(sorted(dis._block_signature(
                        context.block_by_ref(b) or {}, context))) for b in bl)) for bl, t in weeks]
                    group = [{"id": mid, "name": name, "scores": [len(dis._toks(name) & sig) - .001 * j
                              for j, sig in enumerate(signatures)], "selected": answer[mid]} for mid, name in mats]
                    for mid, _ in mats:
                        alignments[mid] = group
                    return answer

                card_stream._align = traced_align
                try:
                    ctx._card_windows_cache = card_windows(entries, ctx)
                finally:
                    card_stream._align = original_align
                runs[root] = (entries, ctx, texts, traces, alignments)
            entries, ctx, texts, traces, alignments = runs[root]
            entry = next(e for e in entries if e["id"] == new_id)
            block, unit, sub = d.compare.predictions(root, entry)
            relevant = {block, row["gold_block"]}
            for trace in traces[new_id]:
                relevant.update(trace["window"])
                resolved = [ctx.block_by_ref(ref) for ref in trace["window"]]
                resolved = [b for b in resolved if b]
                sigs = [dis._block_signature(b, ctx) for b in resolved]
                df = collections.Counter(t for sig in sigs for t in sig)
                tokens = dis.entry_tokens(entry, texts[new_id])
                trace["lexical_scores"] = [{"block": b["id"], "hits": sorted(tokens & set(sig)),
                    "score": dis._score(tokens, sig, len(sigs), df)} for b, sig in zip(resolved, sigs, strict=True)]
            relevant = {str((ctx.block_by_ref(ref) or {}).get("id") or ref) for ref in relevant}
            details = {k: entry.get(k) for k in ("id", "title", "category", "source_section", "moodle_label",
                       "moodle_section_index", "moodle_module_index", "moodle_week_label",
                       "computed_unit_slug", "unit_match_reasons", "unit_match_confidence", "unit_block_conflict")}
            details.update(root=str(root), prediction=[block, unit, sub], traces=traces[new_id],
                           initial_window=resolve_window(entry, ctx),
                           card_window=ctx._card_windows_cache.get(new_id, []),
                           card_dates=_card_entry(entry, ctx),
                           alignment=alignments.get(new_id),
                           effective_block_unit=unit_of_block_or_neighbor(block, ctx.blocks),
                           weeks=[{"text": t, "blocks": _week_blocks(t, ctx)}
                                  for t in str(entry.get("moodle_week_label") or "").split(" || ") if t],
                           blocks=[{k: b.get(k) for k in ("id", "kind", "unit_slug", "primary_topic_label",
                                   "period_start", "period_end", "sessions")} for b in ctx.blocks if b["id"] in relevant])
            if label == "after":
                alt_ctx = build_motor_context(root, ctx.course_name)
                if arm == "ordem":
                    alt_ctx._card_windows_cache = {}
                else:
                    alt_ctx.card_block_map = {}
                    alt_ctx._ncm_cache = None
                alt = anchor_engine.AnchorEngine(voter=None).resolve_unscoped(
                    entry, alt_ctx, texts[new_id], lexical=not tier2_due_scope(entry))
                details["remove_signal_decision"] = asdict(alt) if alt else None
                assert alt and alt.block_ref == row["before"]["prediction"][0], (eid, arm, alt)
            row[label] = details
        report.append(row)
    assert not d.CALLS
    result = {"cases": report, "replay_roots": len(runs),
              "replay_entries": sum(len(r[0]) for r in runs.values()), "calls": d.CALLS}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}))
    for row in report:
        print(row["course"], row["arm"], row["entry_id"], row["before"]["prediction"], "->",
              row["after"]["prediction"], "gold", row["gold_block"], row["gold_units"])


if __name__ == "__main__":
    main()
