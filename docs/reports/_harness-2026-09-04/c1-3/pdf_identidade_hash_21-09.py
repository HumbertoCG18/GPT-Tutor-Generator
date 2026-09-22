"""Medição lateral de identidade por bytes; não executa o motor nem altera a régua."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
PRINCIPAL = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
OUTPUT = HERE / "pdf_identidade_hash_21-09.json"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    assert not OUTPUT.exists(), "Saída existente: não sobrescrever evidência"
    blocked = []

    def deny_network(event, args):
        if event in {"socket.connect", "socket.getaddrinfo"}:
            blocked.append(event)
            raise RuntimeError(f"Operação proibida nesta medição: {event}")

    sys.addaudithook(deny_network)
    rule = HERE / "compara_herancas_15-09.py"
    spec = importlib.util.spec_from_file_location("compare_pdf_hash", rule)
    compare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compare)
    snapshot = HERE / "snapshot_implementacao_taxonomia_15-09.csv"
    with snapshot.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    provenance = {str(p): sha(p) for p in (rule, HERE / "mede_3eixos_12-09.py", snapshot, Path(__file__))}
    courses, unmatched, recovered = {}, [], []
    counts = collections.Counter()
    target = None

    def inventory(root):
        manifest = root / "manifest.json"
        provenance[str(manifest)] = sha(manifest)
        timeline = root / "course/.timeline_index.json"
        if timeline.exists():
            provenance[str(timeline)] = sha(timeline)
        entries = compare.read(manifest)["entries"]
        by_hash = collections.defaultdict(list)
        records = {}
        for entry in entries:
            raw = entry.get("raw_target") or ""
            path = (root / raw).resolve() if raw else None
            if path:
                assert path.is_relative_to(root.resolve()), (root, raw)
            digest = sha(path) if path and path.is_file() else None
            assert entry["id"] not in records, "ID duplicado"
            records[entry["id"]] = {"id": entry["id"], "source_path": entry.get("source_path"),
                                    "file_type": entry.get("file_type"), "raw_target": raw,
                                    "raw_status": "hashed" if digest else "missing_file" if raw else "no_raw_target",
                                    "sha256": digest}
            if digest:
                by_hash[digest].append(entry)
        duplicates = {h: [e["id"] for e in group] for h, group in by_hash.items() if len(group) > 1}
        stats = {"root": str(root), "manifest_entries": len(entries),
                 "hashed_entries": sum(len(g) for g in by_hash.values()),
                 "raw_status_counts": dict(collections.Counter(r["raw_status"] for r in records.values())),
                 "duplicate_hash_groups": len(duplicates),
                 "entries_in_duplicate_groups": sum(len(g) for g in duplicates.values()),
                 "duplicate_excess_entries": sum(len(g) - 1 for g in duplicates.values()),
                 "duplicates": duplicates, "entries": list(records.values())}
        return entries, records, by_hash, stats

    for sig, name in compare.mede.NOMES.items():
        old_root = PRINCIPAL / ".frzero/implementacao_taxonomia_15-09" / name
        package = "pacote_categoria_17-09" if sig in {"MF", "IA"} else "pacote_fontes_15-09"
        new_root = PRINCIPAL / ".frzero" / package / name
        old, old_records, old_hashes, old_stats = inventory(old_root)
        new, new_records, new_hashes, new_stats = inventory(new_root)
        courses[sig] = {"baseline": old_stats, "package": new_stats}
        old_index, new_index = compare.indexed(old), compare.indexed(new)
        old_ids = {e["id"]: e for e in old}
        path_matches = {}
        for entry in old:
            key = compare.source(entry)
            matches = new_index.get(key, [])
            matched = bool(key) and len(matches) == 1 and len(old_index[key]) == 1
            path_matches[entry["id"]] = matches[0] if matched else None
            if matched:
                continue
            digest = old_records[entry["id"]]["sha256"]
            hash_matches = new_hashes.get(digest, []) if digest else []
            unique = bool(digest) and len(old_hashes[digest]) == len(hash_matches) == 1
            detail = {"course": sig, **old_records[entry["id"]],
                      "path_failure": "origem_ambigua" if matches else "entrada_ausente",
                      "hash_candidates": [e["id"] for e in hash_matches], "unique_hash_match": unique}
            unmatched.append(detail)
            if unique:
                recovered.append(detail)
        gold = compare.mede.golds(sig)
        for p in (compare.mede.GEN / "docs/reports" / f"{prefix}_{sig}.csv"
                  for prefix in ("ground_truth", "material_gt", "subunit_gt")):
            if p.exists():
                provenance[str(p)] = sha(p)
        unit_gold = compare.mede.GEN / "tests/fixtures/eval" / f"gold_units_{sig}.csv"
        if unit_gold.exists():
            provenance[str(unit_gold)] = sha(unit_gold)
        for row in (r for r in rows if r["curso"] == sig):
            eid = row["entry_id"]
            matched = path_matches[eid]
            predictions = compare.predictions(new_root, matched) if matched else ("", "", "")
            counts["path_unmatched_snapshot"] += matched is None
            for axis, truth, prediction in zip(("bloco", "unidade"), gold[:2], predictions[:2], strict=True):
                if row[axis] == "":
                    continue
                counts[axis + "_n"] += 1
                counts[axis + "_path_correct"] += int(matched is not None and
                    (prediction == truth[eid] if axis == "bloco" else prediction in truth[eid]))
            if sig == "MF" and eid == "t1-2026-1":
                digest = old_records[eid]["sha256"]
                assert matched is None and len(old_hashes[digest]) == len(new_hashes[digest]) == 1
                counterpart = new_hashes[digest][0]
                block, unit, _ = compare.predictions(new_root, counterpart)
                target = {"course": sig, "baseline": old_records[eid],
                          "package": new_records[counterpart["id"]],
                          "manual_timeline_block_id": counterpart.get("manual_timeline_block_id"),
                          "temporal_block_id": counterpart.get("temporal_block_id"),
                          "prediction": {"bloco": block, "unidade": unit},
                          "gold": {"bloco": gold[0][eid], "unidades_aceitas": sorted(gold[1][eid])},
                          "correct": {"bloco": block == gold[0][eid], "unidade": unit in gold[1][eid]}}
                assert row["bloco"] != "" and row["unidade"] != ""

    assert target is not None
    assert (counts["bloco_path_correct"], counts["bloco_n"],
            counts["unidade_path_correct"], counts["unidade_n"]) == (213, 237, 239, 284), counts
    lateral = {axis: {"correct": counts[axis + "_path_correct"] + int(target["correct"][axis]),
                      "n": counts[axis + "_n"], "delta": int(target["correct"][axis])}
               for axis in ("bloco", "unidade")}
    result = {"task": "W-D", "head_expected": "ce02a8f47285c30c16f12b131bdf86c46dcba64e",
              "method": "SHA-256 dos bytes de raw_target; casamento único nos dois manifests do mesmo curso; gold só na avaliação",
              "package_selection": "MF e IA: pacote_categoria_17-09; demais: pacote_fontes_15-09",
              "target": target, "published_path_score_reproduced": dict(counts),
              "lateral_only_target": lateral, "unmatched_baseline_all_manifest_entries": unmatched,
              "hash_recovered": recovered, "courses": courses, "input_sha256": provenance,
              "blocked_operations": blocked, "builds": 0, "llm_calls": 0,
              "limitations": ["Placar lateral altera apenas o casamento do PDF; publicado preservado, denominadores fixos.",
                              "Hash identifica bytes, não identidade pedagógica; duplicatas tornam o vínculo ambíguo.",
                              "Unicidade limitada aos arquivos raw_target existentes nestes 14 manifests; links sem raw não têm hash.",
                              "Previsões gravadas avaliadas, sem build nem nova execução do motor."]}
    assert not blocked
    with OUTPUT.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"target": target, "path_score": dict(counts), "lateral": lateral,
                      "unmatched": len(unmatched), "recovered": recovered,
                      "duplicates": {sig: {side: {k: stats[k] for k in
                          ("manifest_entries", "hashed_entries", "raw_status_counts", "duplicate_hash_groups", "entries_in_duplicate_groups")}
                          for side, stats in data.items()} for sig, data in courses.items()},
                      "json_sha256": sha(OUTPUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
