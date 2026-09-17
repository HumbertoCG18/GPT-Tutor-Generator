"""Reproduz as três abstenções novas de MF sem regravar o tutor."""
import copy
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("diagnosis", HERE / "diagnostica_perdas_metadados_15-09.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def main():
    out = HERE / "replay_abstencoes_pacote_raiz_15-09.json"
    assert not out.exists()
    report = {}
    for arm in ("cru_fontes_serial_15-09", "pacote_fontes_15-09"):
        root = d.d.ROOT / ".frzero" / arm / "Metodos-Formais-Tutor"
        manifest = d.d.read(root / "manifest.json")
        entries = manifest["entries"]
        inputs = d.d.read(root / "_inputs_15-09.json")
        from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _topic_text
        from src.utils.helpers import auto_detect_category
        phrases = []
        for title, topics in _parse_units_from_teaching_plan(inputs["profile_input"]["teaching_plan"]):
            phrases.append(title.lower())
            phrases.extend(_topic_text(t).lower() for t in topics)
        phrases = [phrase for phrase in phrases if len(phrase) >= 6]
        texts = {e["id"]: d.d.compare._entry_markdown_text_for_file_map(root, e) for e in entries}
        course = manifest["course"]["course_name"]
        replay = d.apply_anchor_engine(copy.deepcopy(entries), root, course, voter=None,
                                      markdown_fn=lambda e, texts=texts: texts[e["id"]])
        assert all(e.get(k) == r.get(k) for e, r in zip(entries, replay, strict=True)
                   for k in d.TEMPORAL_KEYS), arm
        cases = []
        for entry in entries:
            if not entry["id"].startswith("provasindutivas-especificacoesrecursivas"):
                continue
            ctx = d.build_motor_context(root, course)
            ctx._card_windows_cache = d.card_windows(entries, ctx)
            lexical = not d.tier2_due_scope(entry)
            engine = d.anchor_engine.AnchorEngine(voter=None)
            decision = engine.resolve_unscoped(entry, ctx, texts[entry["id"]], lexical=lexical)
            row = {"id": entry["id"], "category": entry.get("category"), "lexical": lexical,
                   "window": d.resolve_window(entry, ctx),
                   "decision": asdict(decision) if decision else None}
            source = next(item for item in inputs["inputs"] if item["path"] == entry["source_path"])
            name = f"{source['moodle_label']} {Path(source['path']).name}".strip()
            category = auto_detect_category(name, is_image=False, frases_do_plano=phrases)
            assert category == source["category"] == entry["category"]
            row["category_replay"] = {"input": name, "result": category}
            row["window_block_ids"] = [(ctx.block_by_ref(ref) or {}).get("id", ref)
                                       for ref in row["window"][0]]
            hypothetical = engine.resolve_unscoped(entry, ctx, texts[entry["id"]], lexical=True)
            row["lexical_enabled_probe"] = asdict(hypothetical) if hypothetical else None
            ctx = d.build_motor_context(root, course)
            ctx.card_block_map = {}
            ctx._ncm_cache = None
            ctx._card_windows_cache = d.card_windows(entries, ctx)
            alternative = engine.resolve_unscoped(entry, ctx, texts[entry["id"]], lexical=lexical)
            row["without_card_dates_window"] = d.resolve_window(entry, ctx)
            row["without_card_dates_decision"] = asdict(alternative) if alternative else None
            cases.append(row)
        assert len(cases) == 3
        report[arm] = {"replay_entries": len(entries), "cases": cases}
    assert not d.d.CALLS
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
