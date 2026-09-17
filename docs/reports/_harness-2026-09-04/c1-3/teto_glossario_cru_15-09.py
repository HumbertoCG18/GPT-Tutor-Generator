"""Mede o teto do GLOSSARY.md no cru, somente em CG (0 chamadas de rede/LLM)."""
import importlib.util
import subprocess
import sys
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

    aliases = build_glossary_aliases(
        repo_artifacts_module=engine._repo_artifacts,
        course_meta_clamp_navigation_artifact=_sem_teto_do_glossario,
        collapse_ws=engine._collapse_ws,
        strip_frontmatter_block=engine._strip_frontmatter_block,
        parse_units_from_teaching_plan=engine._parse_units_from_teaching_plan,
        topic_text=engine._topic_text,
    )
    engine.glossary_md = aliases["glossary_md"]

    spec = importlib.util.spec_from_file_location("motor_3eixos", MOTOR)
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
        assert motor.main(["--config", "regua", "--sem-curadoria-benchmark", "puro", "--cursos", "CG"]) == 0
    finally:
        subprocess.run = real_run

    import reprocess_assignments as ra

    ra.reprocess(motor.DEST / motor.NOMES["CG"], [])
    print(f"reprocess extra CG · TENTATIVAS DE REDE BLOQUEADAS: {len(motor.TENTATIVAS)}")


if __name__ == "__main__":
    main()
