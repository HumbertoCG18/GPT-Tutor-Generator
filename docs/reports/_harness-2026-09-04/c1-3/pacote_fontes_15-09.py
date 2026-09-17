"""Reconstrução original com captura Moodle bruta; sem decisões transplantadas."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cru_driver", HERE / "cru_fontes_15-09.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def main():
    import argparse
    import socket
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curso", choices=base.COURSES, required=True)
    args = parser.parse_args()
    socket.socket.connect = base.blocked
    socket.create_connection = base.blocked
    from src.builder import engine
    from src.builder.sources.moodle import backfill_repo_signals_additive, backfill_repo_signals_consumed
    original = engine.RepoBuilder
    name = base.COURSES[args.curso]
    capture = base.ROOT / ".frzero/implementacao_taxonomia_15-09" / name / "raw/moodle/contents.json"
    expected = json.loads((HERE / "cadeia_metadados_verificada_15-09.json").read_text(encoding="utf-8"))
    expected_hash = expected["courses"][args.curso]["capture_sha256"]
    assert base.digest(capture) == expected_hash, "captura mudou depois do diagnostico"
    contents = json.loads(capture.read_text(encoding="utf-8"))

    class WithCapture(original):
        def build(self):
            target = self.root_dir / "raw/moodle/contents.json"
            if target.exists():
                assert base.digest(target) == expected_hash
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(capture, target)
            super().build()
            timeline = json.loads((self.root_dir / "course/.timeline_index.json").read_text(encoding="utf-8"))
            year = timeline["blocks"][0]["period_start"][:4]
            info = {"semester": f"{year}/1"}
            additive = backfill_repo_signals_additive(self.root_dir, contents, info)
            consumed = backfill_repo_signals_consumed(self.root_dir, contents, info)
            rebuilt = original(root_dir=self.root_dir, course_meta=self.course_meta, entries=[],
                options={**self.options, "use_llm_voter": False, "compile_vocabulary": False},
                subject_profile=self.subject_profile)
            rebuilt.incremental_build()
            assert base.digest(capture) == expected_hash == base.digest(target)
            (self.root_dir / "_capture_inputs_15-09.json").write_text(json.dumps({
                "source": str(capture), "sha256": expected_hash,
                "additive": additive, "consumed": consumed,
                "policy": "payload bruto; sem campos ou mapas historicos",
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{args.curso}] capture backfills: {additive} {consumed}", flush=True)

    engine.RepoBuilder = WithCapture
    sys.argv = [str(HERE / "cru_fontes_15-09.py"), "--curso", args.curso,
                "--destino", ".frzero/pacote_fontes_15-09", "--sem-descricao-html"]
    try:
        return base.main()
    finally:
        engine.RepoBuilder = original


if __name__ == "__main__":
    raise SystemExit(main())
