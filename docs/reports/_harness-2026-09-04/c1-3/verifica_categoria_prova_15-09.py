"""Teste offline de categoria com entradas reais; não regrava os tutores."""
import collections
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unicodedata

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("diagnosis", HERE / "diagnostica_perdas_metadados_15-09.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _topic_text
from src.utils.helpers import auto_detect_category


def candidate(name, original):
    normalized = "".join(c for c in unicodedata.normalize("NFD", name.lower())
                         if not unicodedata.combining(c))
    explicit_exam = re.search(r"(?:^|[\W_])(?:p[123]|av[12]|exame|test|avaliacao|prova[\W_]*[123])(?:$|[\W_])", normalized)
    mathematical = re.search(r"provas?[\W_]*(?:indutiv\w*|por[\W_]+induc\w*)", normalized)
    return "material-de-aula" if original == "provas" and mathematical and not explicit_exam else original


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(items, root, course_name, texts):
    return d.apply_anchor_engine(copy.deepcopy(items), root, course_name, voter=None,
                                 markdown_fn=lambda entry: texts[entry["id"]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="verificacao_categoria_prova_verificada_15-09.json")
    out = HERE / parser.parse_args().saida
    assert out.parent == HERE
    assert not out.exists(), "preservar resultado existente"
    report, total, protected = {}, collections.Counter(), {}
    for course, (name, _) in d.d.audit.COURSES.items():
        root = d.d.ROOT / ".frzero/pacote_fontes_15-09" / name
        manifest_path = root / "manifest.json"
        manifest = d.d.read(manifest_path)
        entries = manifest["entries"]
        inputs = d.d.read(root / "_inputs_15-09.json")
        source_inputs = {str(Path(item["path"]).resolve()).casefold(): item for item in inputs["inputs"]}
        phrases = []
        for title, topics in _parse_units_from_teaching_plan(inputs["profile_input"]["teaching_plan"]):
            phrases.append(title.lower())
            phrases.extend(_topic_text(t).lower() for t in topics)
        phrases = [phrase for phrase in phrases if len(phrase) >= 6]
        watched = [manifest_path, *root.joinpath("course").glob("*.json")]
        protected.update({str(path): digest(path) for path in watched})
        texts = {e["id"]: d.d.compare._entry_markdown_text_for_file_map(root, e) for e in entries}
        control = replay(entries, root, manifest["course"]["course_name"], texts)
        assert all(e.get(k) == r.get(k) for e, r in zip(entries, control, strict=True)
                   for k in d.TEMPORAL_KEYS), (course, "controle divergiu")
        modified = copy.deepcopy(entries)
        changes, exam_controls, probes = [], [], []
        for e in modified:
            source = source_inputs[d.d.compare.source(e)]
            input_name = f"{source['moodle_label']} {Path(source['path']).name}".strip()
            original = ("codigo-professor" if source["file_type"] == "zip" else
                        auto_detect_category(input_name, is_image=source["file_type"] == "image", frases_do_plano=phrases))
            assert original == source["category"], (course, e["id"], "import divergiu")
            proposed = candidate(input_name, original)
            if proposed != original:
                assert e["category"] == original
                changes.append({"id": e["id"], "input": input_name, "before": original, "after": proposed})
                e["category"] = proposed
                # Perturbações explícitas de nomes reais; não são novos documentos reais.
                for prefix in ("P1 - ", "Prova 1 - "):
                    probe = prefix + input_name
                    detected = auto_detect_category(probe, frases_do_plano=phrases)
                    assert candidate(probe, detected) == "provas"
                    probes.append({"synthetic_name": probe, "category": "provas"})
            elif e.get("category") in ("provas", "fotos-de-prova"):
                exam_controls.append({"id": e["id"], "category": e["category"],
                                      "source_sha256": digest(Path(source["path"]))})
        result = replay(modified, root, manifest["course"]["course_name"], texts)
        changed_ids = {row["id"] for row in changes}
        untouched = [e["id"] for e, r in zip(entries, result, strict=True) if e["id"] not in changed_ids
                     and any(e.get(k) != r.get(k) for k in d.TEMPORAL_KEYS)]
        assert not untouched, (course, "efeito colateral", untouched)
        by_id, after_id = {e["id"]: e for e in entries}, {e["id"]: e for e in result}
        mapping = {e["entry_id"]: e["new_id"] for e in d.d.read(HERE / f"herancas_{course}_15-09.json")["entries"]}
        counts = collections.Counter()
        flips = []
        for old_id, truth in d.d.compare.mede.golds(course)[0].items():
            current_id = mapping[old_id]
            before = d.d.compare.predictions(root, by_id[current_id])[0] if current_id in by_id else ""
            after = d.d.compare.predictions(root, after_id[current_id])[0] if current_id in after_id else ""
            b, a = before == truth, after == truth
            counts.update(n=1, before=int(b), after=int(a), gains=int(a and not b), losses=int(b and not a))
            if b != a:
                flips.append({"id": old_id, "before": before, "after": after, "gold": truth})
        report[course] = {"entries": len(entries), "category_changes": changes, "protected_exam_entries": exam_controls,
                          "synthetic_exam_guards": probes, "block_counts": dict(counts), "block_flips": flips}
        total.update(counts)
        print(course, len(entries), "category_changes", len(changes), dict(counts))
    assert (total["n"], total["before"]) == (237, 210), total
    assert all(digest(Path(path)) == value for path, value in protected.items())
    assert not d.d.CALLS
    out.write_text(json.dumps({"courses": report, "total": dict(total), "calls": dict(d.d.CALLS),
                               "protected_hashes": protected, "scope": "categorias e replay temporal; demais eixos nao reavaliados"},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL", dict(total))


if __name__ == "__main__":
    main()
