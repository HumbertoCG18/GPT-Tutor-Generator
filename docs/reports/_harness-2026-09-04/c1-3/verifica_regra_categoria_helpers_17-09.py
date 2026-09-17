"""Replay de auto_detect_category (helpers.py) sobre os 338 inputs de 15/09; sem build, sem rede.

Exige: exatamente 3 mudancas vs a categoria importada em 15/09, todas nos alvos MF
(ProvasIndutivas_EspecificacoesRecursivas{,_Arvores,_Listas}.pdf, provas -> material-de-aula).
Reproduz a entrada do stash_import.py:104 (moodle_label + nome, frases_do_plano do perfil).
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _topic_text  # noqa: E402
from src.utils.helpers import auto_detect_category  # noqa: E402

EXPECTED = {
    ("Metodos-Formais-Tutor", "ProvasIndutivas_EspecificaçõesRecursivas.pdf"),
    ("Metodos-Formais-Tutor", "ProvasIndutivas_EspecificaçõesRecursivas_Arvores.pdf"),
    ("Metodos-Formais-Tutor", "ProvasIndutivas_EspecificaçõesRecursivas_Listas.pdf"),
}


def phrases_of(profile_input):
    out = []
    for title, topics in _parse_units_from_teaching_plan(profile_input["teaching_plan"]):
        out.append(title.lower())
        out.extend(_topic_text(t).lower() for t in topics)
    return [p for p in out if len(p) >= 6]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="verificacao_regra_categoria_helpers_17-09.json")
    out = HERE / parser.parse_args().saida
    assert out.parent == HERE and not out.exists(), "preservar resultado existente"
    report, changes, total = {}, [], 0
    for root in sorted((ROOT / ".frzero/pacote_fontes_15-09").iterdir()):
        inputs = json.loads((root / "_inputs_15-09.json").read_text(encoding="utf-8"))
        phrases = phrases_of(inputs["profile_input"])
        course_changes = []
        for item in inputs["inputs"]:
            total += 1
            name = f"{item['moodle_label']} {Path(item['path']).name}".strip()
            now = ("codigo-professor" if item["file_type"] == "zip" else
                   auto_detect_category(name, is_image=item["file_type"] == "image", frases_do_plano=phrases))
            if now != item["category"]:
                course_changes.append({"file": Path(item["path"]).name, "input": name,
                                       "before": item["category"], "after": now})
        report[root.name] = {"inputs": len(inputs["inputs"]), "changes": course_changes}
        changes.extend((root.name, c["file"]) for c in course_changes)
        print(root.name, len(inputs["inputs"]), "mudancas", len(course_changes))
    assert total == 338, total
    assert set(changes) == EXPECTED and len(changes) == 3, changes
    assert all(c["before"] == "provas" and c["after"] == "material-de-aula"
               for c in report["Metodos-Formais-Tutor"]["changes"])
    out.write_text(json.dumps({"courses": report, "total_inputs": total, "changes": len(changes),
                               "scope": "replay de classificacao; sem build, sem rede (so helpers e teaching_plan importados)"},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL", total, "mudancas", len(changes), "OK")


if __name__ == "__main__":
    main()
