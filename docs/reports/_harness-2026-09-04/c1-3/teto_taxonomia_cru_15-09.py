"""Testa o clamp do glossario na rota que constroi a taxonomia de CG (0 LLM)."""
import importlib.util
import json
import subprocess
import sys
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MOTOR = ROOT / "docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py"


def _sem_teto_do_glossario(text: str, *, max_chars: int, label: str) -> str:
    assert label == "course/GLOSSARY.md"
    return (text or "").strip()


def main() -> None:
    sys.path.insert(0, str(ROOT))
    import src.builder.engine as engine
    from src.builder.facade.glossary import build_glossary_aliases

    glossary = build_glossary_aliases(
        repo_artifacts_module=engine._repo_artifacts,
        course_meta_clamp_navigation_artifact=_sem_teto_do_glossario,
        collapse_ws=engine._collapse_ws,
        strip_frontmatter_block=engine._strip_frontmatter_block,
        parse_units_from_teaching_plan=engine._parse_units_from_teaching_plan,
        topic_text=engine._topic_text,
    )["glossary_md"]
    engine.glossary_md = glossary
    engine._build_file_map_content_taxonomy_from_course = partial(
        engine._file_map_build_file_map_content_taxonomy_from_course,
        parse_units_from_teaching_plan=engine._parse_units_from_teaching_plan,
        topic_text=engine._topic_text,
        glossary_md_fn=glossary,
        collect_strong_heading_candidates=engine._collect_strong_heading_candidates,
        resolve_semantic_profile_fn=engine.resolve_semantic_profile,
        build_content_taxonomy_fn=engine._build_content_taxonomy,
    )

    spec = importlib.util.spec_from_file_location("motor_3eixos_raiz", MOTOR)
    motor = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(motor)

    real_run = subprocess.run

    def sem_medidor(command, *args, **kwargs):
        if any(str(part).endswith("mede_3eixos_12-09.py") for part in command):
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return real_run(command, *args, **kwargs)

    subprocess.run = sem_medidor
    try:
        assert motor.main([
            "--config", "regua",
            "--sem-curadoria-benchmark", "puro",
            "--cursos", "CG",
        ]) == 0
    finally:
        subprocess.run = real_run

    root = motor.DEST / motor.NOMES["CG"] / "course"
    glossary_text = (root / "GLOSSARY.md").read_text(encoding="utf-8")
    taxonomy = json.loads((root / ".content_taxonomy.json").read_text(encoding="utf-8"))
    topics = [t for u in taxonomy.get("units", []) for t in u.get("topics", [])]
    zero = sum(not (t.get("aliases") or []) for t in topics)
    print(f"GLOSSARY chars={len(glossary_text)} truncado={'TRUNCADO' in glossary_text.upper()}")
    print(f"aliases cobertos={len(topics) - zero}/{len(topics)} vazios={zero}")
    print(f"TENTATIVAS DE REDE BLOQUEADAS: {len(motor.TENTATIVAS)}")
    assert "TRUNCADO" not in glossary_text.upper()
    assert zero == 0
    assert not motor.TENTATIVAS


if __name__ == "__main__":
    main()
