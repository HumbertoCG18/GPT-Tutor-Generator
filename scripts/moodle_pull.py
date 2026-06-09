"""Baixa um curso do Moodle organizado por seção (= card) numa pasta destino.

Lê MOODLE_URL/MOODLE_TOKEN de moddle/.env (ou ambiente). Não imprime o token.

Uso:
    python -m scripts.moodle_pull --course <id> <dest>
    python -m scripts.moodle_pull --course <id> <dest> --dry-run
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.builder.sources.moodle import MoodleClient, iter_section_files


def _load_env() -> dict:
    env = {}
    dotenv = Path(__file__).resolve().parent.parent / "moddle" / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    import os
    env.setdefault("MOODLE_URL", os.environ.get("MOODLE_URL", "https://moodle.pucrs.br"))
    if os.environ.get("MOODLE_TOKEN"):
        env["MOODLE_TOKEN"] = os.environ["MOODLE_TOKEN"]
    return env


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dry = "--dry-run" in argv
    course_id = ""
    if "--course" in argv:
        i = argv.index("--course")
        if i + 1 < len(argv):
            course_id = argv[i + 1]
    pos = [a for a in argv if not a.startswith("-") and a != course_id]
    if not course_id or not pos:
        print("uso: python -m scripts.moodle_pull --course <id> <dest> [--dry-run]")
        return 2
    dest = Path(pos[0])
    env = _load_env()
    token = env.get("MOODLE_TOKEN", "")
    if not token or token == "cole_o_wstoken_aqui":
        print("Faltando MOODLE_TOKEN em moddle/.env.")
        return 2
    client = MoodleClient(env["MOODLE_URL"], token)
    if dry:
        files = iter_section_files(client.get_course_contents(course_id))
        print(f"[dry-run] {len(files)} arquivos em {len({f.section for f in files})} seções -> {dest}")
        for f in files:
            print(f"  {f.section}/{f.disk_name}")
        return 0
    summary = client.download_course(course_id, dest)
    print(f"OK -> {dest}")
    print(f"  total={summary['total']}  baixados={summary['downloaded']}  pulados(existiam)={summary['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
