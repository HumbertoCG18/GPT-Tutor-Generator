"""Pontua o pacote com categoria corrigida contra o pacote de 15/09; publica sempre, aceita so com todos os gates."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("meta_driver", HERE / "metadados_blocos_15-09.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
AXES = d.compare.AXES
EXAM = ("provas", "fotos-de-prova")
TARGETS = {"MF": {"provasindutivas-especificacoesrecursivas", "provasindutivas-especificacoesrecursivas-arvores",
                  "provasindutivas-especificacoesrecursivas-listas"}, "IA": set()}
EXPECTED_REF = json.loads((HERE / "verificacao_pacote_7cursos_15-09.json").read_text(encoding="utf-8"))["courses"]
DERIVED = ("exams/EXAM_INDEX.md", "course/FILE_MAP.md", "course/FILE_MAP_TRACE.md", ".deeptutor/knowledge/EXAM_INDEX.md")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def temporal(root):
    return [{k: b.get(k) for k in ("id", "period_start", "period_end", "source_rows")}
            | {"sessions": [(s.get("date"), s.get("label"), s.get("kind")) for s in b.get("sessions", [])]}
            for b in d.read(root / "course/.timeline_index.json")["blocks"]]


def taxonomy(root):
    return {u["slug"]: sorted(t["slug"] for t in u.get("topics", []))
            for u in d.read(root / "course/.content_taxonomy.json")["units"]}


def normalized(root, text, category=""):
    text = text.replace(root.relative_to(d.ROOT).as_posix(), "<repo>")
    # entry_processing.py:105 move o PDF para raw/pdfs/<categoria>; o front matter cita esse caminho.
    return text.replace(f"raw/pdfs/{category}/", "raw/pdfs/<categoria>/") if category else text


def derived_report(ref, new, rel, target_names, control_names):
    ref_path, new_path = ref / rel, new / rel
    if not ref_path.is_file() or not new_path.is_file():
        return {"present": [ref_path.is_file(), new_path.is_file()]}
    ref_lines = normalized(ref, ref_path.read_text(encoding="utf-8")).splitlines()
    new_lines = normalized(new, new_path.read_text(encoding="utf-8")).splitlines()
    diff = set(ref_lines) ^ set(new_lines)
    broken = [t for t in re.findall(r"\]\(([^)#]+)", new_path.read_text(encoding="utf-8"))
              if not t.startswith(("http://", "https://")) and not (new_path.parent / t.replace("%20", " ")).exists()]
    return {"targets_ref": sum(any(n in l for n in target_names) for l in ref_lines),
            "targets_novo": sum(any(n in l for n in target_names) for l in new_lines),
            "controls_ref": sum(any(n in l for n in control_names) for l in ref_lines),
            "controls_novo": sum(any(n in l for n in control_names) for l in new_lines),
            "diff_lines": len(diff), "diff_lines_mentioning_targets": sum(any(n in l for n in target_names) for l in diff),
            "broken_links_novo": broken}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--referencia", default=".frzero/pacote_fontes_15-09")
    p.add_argument("--novo", default=".frzero/pacote_categoria_17-09")
    p.add_argument("--cursos", default="MF,IA")
    p.add_argument("--hashes", default="hashes_protegidos_antes_17-09.json")
    p.add_argument("--saida", required=True)
    args = p.parse_args()
    out = HERE / args.saida
    assert out.parent == HERE and not out.exists()
    protected = d.read(HERE / args.hashes)
    hash_drift = [path for path, value in protected.items() if sha(path) != value]
    results, total = {}, collections.Counter()
    for course in args.cursos.split(","):
        name, _ = d.audit.COURSES[course]
        ref, new = d.ROOT / args.referencia / name, d.ROOT / args.novo / name
        gates = []
        build = d.read(new / "_build_result_15-09.json")
        if not (build["completed"] and not build["calls"] and not build["failed_entries"]):
            gates.append(f"build: {build}")
        inputs, previous = d.read(new / "_inputs_15-09.json"), d.read(ref / "_inputs_15-09.json")
        gates += [f"_inputs.{key} difere" for key in ("profile_input", "metadata_sources", "html_image_cap", "skipped")
                  if inputs[key] != previous[key]]
        if {e["path"]: e["sha256"] for e in inputs["inputs"]} != {e["path"]: e["sha256"] for e in previous["inputs"]}:
            gates.append("fontes diferem do pacote de 15/09")
        if any(sha(e["path"]) != e["sha256"] for e in inputs["inputs"] + inputs["metadata_sources"]):
            gates.append("fontes mudaram em disco")
        capture = d.read(new / "_capture_inputs_15-09.json")
        if not (sha(capture["source"]) == capture["sha256"] == sha(new / "raw/moodle/contents.json")
                == d.read(ref / "_capture_inputs_15-09.json")["sha256"]):
            gates.append("captura Moodle difere")
        ref_manifest, new_manifest = d.read(ref / "manifest.json"), d.read(new / "manifest.json")
        options_diff = sorted(k for k in set(ref_manifest["options"]) | set(new_manifest["options"])
                              if ref_manifest["options"].get(k) != new_manifest["options"].get(k))
        if options_diff:
            gates.append(f"options do manifest diferem: {options_diff}")
        ref_entries, new_entries = ref_manifest["entries"], new_manifest["entries"]
        if any(e.get(k) for e in new_entries for k in ("manual_timeline_block_id", "manual_unit_slug", "manual_subunit_slug")):
            gates.append("pinos manuais no novo")
        ref_by_source, new_by_source = d.compare.indexed(ref_entries), d.compare.indexed(new_entries)
        if set(ref_by_source) != set(new_by_source):
            gates.append("conjunto de origens difere")
        if any(len(v) != 1 for v in list(ref_by_source.values()) + list(new_by_source.values())):
            gates.append("origens ambiguas")
        pairs = [(old, new_by_source[d.compare.source(old)][0]) for old in ref_entries if d.compare.source(old) in new_by_source]

        category_changes = [{"id": old["id"], "before": old["category"], "after": fresh["category"]}
                            for old, fresh in pairs if old["category"] != fresh["category"]]
        if {c["id"] for c in category_changes} != TARGETS[course]:
            gates.append(f"categorias alteradas {sorted(c['id'] for c in category_changes)} != alvo {sorted(TARGETS[course])}")
        recorded = d.read(new / "_categoria_17-09.json")
        if len(recorded["changes"]) != len(category_changes) or recorded["calls"]:
            gates.append(f"registro do driver: {len(recorded['changes'])} alteracoes, calls={recorded['calls']}")

        controls = []
        for old, fresh in pairs:
            if old["category"] in EXAM and old["id"] not in TARGETS[course]:
                same = old["category"] == fresh["category"] and d.compare.predictions(ref, old) == d.compare.predictions(new, fresh)
                controls.append({"id": old["id"], "category": old["category"], "invariant": same})
                if not same:
                    gates.append(f"controle {old['id']} mudou")

        temporal_identical, taxonomy_identical = temporal(ref) == temporal(new), taxonomy(ref) == taxonomy(new)
        if not temporal_identical:
            gates.append("estrutura temporal divergiu: eixo bloco nao comparavel")
        if not taxonomy_identical:
            gates.append("taxonomia divergiu: eixos unidade/subunidade nao comparaveis")

        text_changes, content_changes, category_path_changes, empty_both = [], [], [], []
        for old, fresh in pairs:
            before = d.compare._entry_markdown_text_for_file_map(ref, old)
            after = d.compare._entry_markdown_text_for_file_map(new, fresh)
            if old["file_type"] != "zip" and not before.strip() and not after.strip():
                empty_both.append(old["id"])
            if before != after:
                text_changes.append({"id": old["id"], "before_chars": len(before), "after_chars": len(after)})
                if normalized(ref, before) != normalized(new, after):
                    if normalized(ref, before, old["category"]) == normalized(new, after, fresh["category"]):
                        category_path_changes.append(old["id"])
                    else:
                        content_changes.append(old["id"])
        if set(category_path_changes) - TARGETS[course]:
            gates.append(f"caminho de categoria mudou fora dos alvos: {sorted(set(category_path_changes) - TARGETS[course])}")
        if empty_both:
            gates.append(f"texto vazio nos dois lados: {empty_both}")
        if content_changes:
            gates.append(f"texto extraido mudou: {content_changes}")

        # Placar: os dois lados recalculados contra o gold; ausentes ficam no denominador.
        rows = list(csv.DictReader((HERE / f"herancas_{course}_15-09.csv").open(encoding="utf-8-sig")))
        mapping = {e["entry_id"]: e["new_id"] for e in d.read(HERE / f"herancas_{course}_15-09.json")["entries"]}
        ref_by_id = {e["id"]: e for e in ref_entries}
        gold = d.compare.mede.golds(course)
        counts, flips, prediction_changes = collections.Counter(), [], []
        for row in rows:
            old = ref_by_id.get(mapping[row["entry_id"]] or "")
            fresh = new_by_source[d.compare.source(old)][0] if old and d.compare.source(old) in new_by_source else None
            pred_ref = d.compare.predictions(ref, old) if old else ("", "", "")
            pred_new = d.compare.predictions(new, fresh) if fresh else ("", "", "")
            counts["common" if old and fresh else "absent"] += 1
            changes = {}
            for axis, truth, vr, vn in zip(AXES, gold, (pred_ref[0], pred_ref[1], pred_ref[2], pred_ref[2]),
                                            (pred_new[0], pred_new[1], pred_new[2], pred_new[2]), strict=True):
                if row[axis] == "":
                    continue
                target = truth[row["entry_id"]]
                before = int(old is not None and (vr == target if axis == "bloco" else vr in target))
                after = int(fresh is not None and (vn == target if axis == "bloco" else vn in target))
                counts[axis + "_n"] += 1
                counts[axis + "_ref"] += before
                counts[axis + "_novo"] += after
                counts[axis + "_gains"] += after > before
                counts[axis + "_losses"] += after < before
                if before != after:
                    changes[axis] = [before, after]
            if changes:
                flips.append({"entry_id": row["entry_id"], "changes": changes, "pred_ref": pred_ref, "pred_novo": pred_new})
            if pred_ref != pred_new:
                prediction_changes.append({"entry_id": row["entry_id"], "ref_id": old["id"] if old else None,
                                           "target": bool(old) and old["id"] in TARGETS[course],
                                           "pred_ref": pred_ref, "pred_novo": pred_new, "scored": changes})
        expected = EXPECTED_REF[course]["counts"]
        ref_mismatch = {axis: [counts[axis + "_ref"], expected[axis + "_after"]] for axis in AXES
                        if counts[axis + "_ref"] != expected[axis + "_after"]}
        if ref_mismatch or counts["absent"] != expected["absent"]:
            gates.append(f"lado de referencia recalculado difere do JSON de 15/09: {ref_mismatch} absent={counts['absent']}")
        losses = {axis: counts[axis + "_losses"] for axis in AXES if counts[axis + "_losses"]}
        if losses:
            gates.append(f"perdas: {losses}")
        if course == "IA" and (prediction_changes or category_changes):
            gates.append("controle IA com flips")

        # EXAM_INDEX cita o nome de origem; FILE_MAP cita o id. Procurar os dois.
        target_names = [Path(old["source_path"]).name for old in ref_entries if old["id"] in TARGETS[course]] + sorted(TARGETS[course])
        control_names = [Path(ref_by_id[c["id"]]["source_path"]).name for c in controls] + [c["id"] for c in controls]
        derived = {rel: derived_report(ref, new, rel, target_names, control_names) for rel in DERIVED}
        exam_index = derived["exams/EXAM_INDEX.md"]
        if "targets_novo" in exam_index and (exam_index["targets_novo"] or exam_index["controls_novo"] != exam_index["controls_ref"]
                                              or exam_index["broken_links_novo"]):
            gates.append(f"exams/EXAM_INDEX.md: {exam_index}")
        raw_moves = {t: [(ref / "raw/pdfs/provas" / f"{t}.pdf").is_file(), (new / "raw/pdfs/material-de-aula" / f"{t}.pdf").is_file()]
                     for t in sorted(TARGETS[course])}
        if not all(all(v) for v in raw_moves.values()):
            gates.append(f"raw/pdfs/<categoria> nao moveu: {raw_moves}")

        results[course] = {
            "accepted": not gates and not hash_drift, "gates_failed": gates, "counts": dict(counts), "flips": flips,
            "prediction_changes": prediction_changes,
            "prediction_changes_outside_targets": [c for c in prediction_changes if not c["target"]],
            "category_changes": category_changes, "controls": controls,
            "temporal_identical": temporal_identical, "taxonomy_identical": taxonomy_identical,
            "text_changes": text_changes, "content_changes_after_repo_path_normalization": content_changes,
            "text_changes_only_category_path": category_path_changes,
            "empty_text_both_sides": empty_both, "options_diff": options_diff, "derived": derived, "raw_pdf_moves": raw_moves,
            "build": build, "entries": [len(ref_entries), len(new_entries)], "source_hashes_checked": len(inputs["inputs"]),
        }
        total.update(counts)
        print(course, "ACEITO" if results[course]["accepted"] else "REPROVADO",
              f"comuns={counts['common']} ausentes={counts['absent']} categorias={len(category_changes)}")
        for axis in AXES:
            print(f"  {axis}: ref={counts[axis + '_ref']}/{counts[axis + '_n']} novo={counts[axis + '_novo']}/{counts[axis + '_n']}"
                  f" ganhos={counts[axis + '_gains']} perdas={counts[axis + '_losses']}")
        print(f"  previsoes alteradas={len(prediction_changes)} (fora dos alvos: {len(results[course]['prediction_changes_outside_targets'])})"
              f" texto_mudou={len(text_changes)} conteudo_mudou={len(content_changes)} EXAM_INDEX={exam_index}")
        for gate in gates:
            print("  GATE:", gate)
    accepted = all(r["accepted"] for r in results.values())
    out.write_text(json.dumps({"accepted": accepted, "protected_hash_drift": hash_drift, "courses": results, "total": dict(total)},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("hash drift:", hash_drift or "nenhum", "| ACEITO" if accepted else "| REPROVADO")
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
