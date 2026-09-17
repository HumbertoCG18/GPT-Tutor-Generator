"""Verifica fontes/estrutura antes de pontuar a reconstrução com captura Moodle."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("meta_driver", HERE / "metadados_blocos_15-09.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def temporal(root):
    return [{k: b.get(k) for k in ("id", "period_start", "period_end", "source_rows")}
            | {"sessions": [(s.get("date"), s.get("label"), s.get("kind")) for s in b.get("sessions", [])]}
            for b in d.read(root / "course/.timeline_index.json")["blocks"]]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cursos", default=",".join(d.audit.COURSES))
    p.add_argument("--saida", required=True)
    args = p.parse_args()
    out = HERE / args.saida
    assert out.parent == HERE and not out.exists()
    results, total = {}, collections.Counter()
    for course in args.cursos.split(","):
        name, raw_arm = d.audit.COURSES[course]
        raw = d.ROOT / ".frzero" / raw_arm / name
        new = d.ROOT / ".frzero/pacote_fontes_15-09" / name
        build = d.read(new / "_build_result_15-09.json")
        assert build["completed"] and not build["calls"] and not build["failed_entries"], build
        inputs, previous = d.read(new / "_inputs_15-09.json"), d.read(raw / "_inputs_15-09.json")
        assert inputs["profile_input"] == previous["profile_input"], (course, "perfil mudou")
        assert {e["path"]: e["sha256"] for e in inputs["inputs"]} == {
            e["path"]: e["sha256"] for e in previous["inputs"]}, (course, "fontes mudaram")
        capture = d.read(new / "_capture_inputs_15-09.json")
        assert sha(capture["source"]) == capture["sha256"] == sha(new / "raw/moodle/contents.json")
        assert all(sha(e["path"]) == e["sha256"] for e in inputs["inputs"] + inputs["metadata_sources"])
        assert temporal(raw) == temporal(new), (course, "estrutura temporal divergiu; nao pontuar")
        raw_entries = {e["id"]: e for e in d.read(raw / "manifest.json")["entries"]}
        entries = d.read(new / "manifest.json")["entries"]
        assert not any(e.get(k) for e in entries for k in ("manual_timeline_block_id", "manual_unit_slug", "manual_subunit_slug"))
        by_source = d.compare.indexed(entries)
        assert set(by_source) == {d.compare.source(e) for e in raw_entries.values()}, (course, "entries mudaram")
        assert all(len(v) == 1 for v in by_source.values()), (course, "origens ambiguas")
        text_changes = []
        content_changes = []
        for old in raw_entries.values():
            fresh = by_source[d.compare.source(old)][0]
            before_text = d.compare._entry_markdown_text_for_file_map(raw, old)
            after_text = d.compare._entry_markdown_text_for_file_map(new, fresh)
            if before_text != after_text:
                text_changes.append({"id": old["id"], "before_chars": len(before_text), "after_chars": len(after_text)})
                normalized_before = before_text.replace(raw.relative_to(d.ROOT).as_posix(), "<repo>")
                normalized_after = after_text.replace(new.relative_to(d.ROOT).as_posix(), "<repo>")
                if normalized_before != normalized_after:
                    content_changes.append(old["id"])
        rows = list(csv.DictReader((HERE / f"herancas_{course}_15-09.csv").open(encoding="utf-8-sig")))
        mapping = {e["entry_id"]: e["new_id"] for e in d.read(HERE / f"herancas_{course}_15-09.json")["entries"]}
        gold = d.compare.mede.golds(course)
        counts, flips = collections.Counter(), []
        for row in rows:
            raw_entry = raw_entries.get(mapping[row["entry_id"]])
            entry = by_source[d.compare.source(raw_entry)][0] if raw_entry else None
            pred = d.compare.predictions(new, entry) if entry else ("", "", "")
            counts["common" if entry else "absent"] += 1
            changes = {}
            for axis, truth, value in zip(d.compare.AXES, gold, (pred[0], pred[1], pred[2], pred[2]), strict=True):
                if row[axis] == "":
                    continue
                target = truth[row["entry_id"]]
                before = int(row[axis])
                after = int(entry is not None and (value == target if axis == "bloco" else value in target))
                counts[axis + "_n"] += 1
                counts[axis + "_before"] += before
                counts[axis + "_after"] += after
                counts[axis + "_gains"] += after > before
                counts[axis + "_losses"] += after < before
                if entry:
                    counts[axis + "_common_n"] += 1
                if before != after:
                    changes[axis] = [before, after]
            if changes:
                flips.append({"entry_id": row["entry_id"], "changes": changes, "prediction": pred})
        results[course] = {"counts": dict(counts), "flips": flips, "source_hashes_checked": len(inputs["inputs"]),
                           "capture": capture, "entries": len(entries), "temporal_identical": True,
                           "text_changes": text_changes, "content_changes_after_repo_path_normalization": content_changes}
        total.update(counts)
        print(course, json.dumps(dict(counts)))
    out.write_text(json.dumps({"courses": results, "total": dict(total)}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
