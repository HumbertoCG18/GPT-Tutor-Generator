"""Motor congelado em destino novo, com fonte atual e rede bloqueada."""
import argparse
import importlib.util
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", required=True)
    parser.add_argument("--cursos", default="MF,SO,IA,ES2,TCC,CG,FR")
    args = parser.parse_args()
    dest = (ROOT / args.destino).resolve()
    allowed = (ROOT / ".frzero").resolve()
    if dest == allowed or not dest.is_relative_to(allowed):
        parser.error("destino deve estar dentro de .frzero")
    if dest.exists():
        parser.error("destino deve ser novo")
    spec = importlib.util.spec_from_file_location("motor_congelado", Path(__file__).with_name("motor_3eixos_12-09.py"))
    motor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(motor)
    import ablacao_rapida as ab
    original_sync = ab.sync
    ab.sync = partial(ab.sync_fresh, sync_fn=original_sync)
    motor.DEST = dest
    try:
        rc = motor.main(["--config", "regua", "--sem-curadoria-benchmark", "puro", "--cursos", args.cursos])
        if motor.TENTATIVAS:
            raise RuntimeError(f"tentativas de rede: {len(motor.TENTATIVAS)}")
        return rc
    finally:
        ab.sync = original_sync


if __name__ == "__main__":
    raise SystemExit(main())
