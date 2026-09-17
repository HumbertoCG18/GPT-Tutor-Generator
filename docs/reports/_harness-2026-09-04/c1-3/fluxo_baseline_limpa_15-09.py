"""Roda a baseline crua numa copia nova sob .frzero (0 chamadas de LLM)."""
import importlib.util
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MOTOR = ROOT / "docs/reports/_harness-2026-09-04/c1-3/motor_3eixos_12-09.py"
DEST = Path(os.environ["FLUXO_DEST"]).resolve()


def main() -> int:
    assert DEST.is_relative_to((ROOT / ".frzero").resolve())
    assert not DEST.exists(), f"destino experimental deve nascer vazio: {DEST}"
    spec = importlib.util.spec_from_file_location("motor_baseline_limpa", MOTOR)
    motor = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(motor)
    motor.DEST = DEST
    return motor.main(["--config", "regua", "--sem-curadoria-benchmark", "puro"])


if __name__ == "__main__":
    raise SystemExit(main())
