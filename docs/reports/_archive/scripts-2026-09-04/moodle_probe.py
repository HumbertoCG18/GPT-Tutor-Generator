"""Probe READ-ONLY da Moodle Web Services API (mobile app token).

Confirma o token, lista cursos e — para um curso — imprime as SEÇÕES (= cards)
com nº de arquivos e nomes de exemplo. Não baixa nada, não imprime o token.

Lê MOODLE_URL e MOODLE_TOKEN de moddle/.env (ou do ambiente).

Uso:
    python -m scripts.moodle_probe                 # site info + lista de cursos
    python -m scripts.moodle_probe --course 12345  # seções/arquivos do curso
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def _load_env() -> dict:
    env = {}
    dotenv = Path(__file__).resolve().parent.parent / "moddle" / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    import os
    env.setdefault("MOODLE_URL", os.environ.get("MOODLE_URL", "https://moodle.pucrs.br"))
    if os.environ.get("MOODLE_TOKEN"):
        env["MOODLE_TOKEN"] = os.environ["MOODLE_TOKEN"]
    return env


def _call(base: str, token: str, wsfunction: str, **params) -> object:
    url = base.rstrip("/") + "/webservice/rest/server.php"
    data = {
        "wstoken": token,
        "wsfunction": wsfunction,
        "moodlewsrestformat": "json",
        **{k: str(v) for k, v in params.items()},
    }
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if isinstance(payload, dict) and payload.get("exception"):
        raise RuntimeError(f"Moodle erro [{payload.get('errorcode')}]: {payload.get('message')}")
    return payload


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    env = _load_env()
    base = env.get("MOODLE_URL", "")
    token = env.get("MOODLE_TOKEN", "")
    if not token or token == "cole_o_wstoken_aqui":
        print("Faltando MOODLE_TOKEN. Preencha moddle/.env (veja moddle/.env.example).")
        return 2

    course_id = ""
    if "--course" in argv:
        i = argv.index("--course")
        if i + 1 < len(argv):
            course_id = argv[i + 1]

    # --dump <id>: despeja o JSON cru de core_course_get_contents (diagnóstico
    # M365). Não imprime token. Útil pra ver mod_url/externalurl e redirects.
    if "--dump" in argv:
        i = argv.index("--dump")
        dump_id = argv[i + 1] if i + 1 < len(argv) else course_id
        if not dump_id:
            print("Uso: python -m scripts.moodle_probe --dump <course_id>")
            return 2
        contents = _call(base, token, "core_course_get_contents", courseid=dump_id)
        print(json.dumps(contents, ensure_ascii=False, indent=2))
        return 0

    # 1) Confirma o token (sem imprimi-lo).
    info = _call(base, token, "core_webservice_get_site_info")
    userid = info.get("userid")
    print(f"OK. Usuário: {info.get('fullname')} | site: {info.get('sitename')} | userid={userid}")

    # 2) Lista cursos.
    courses = _call(base, token, "core_enrol_get_users_courses", userid=userid)
    print(f"\nCursos matriculados: {len(courses)}")
    for c in courses:
        print(f"  id={c.get('id'):<8} {c.get('shortname','')}  |  {c.get('fullname','')}")

    if not course_id:
        print("\nRode com --course <id> pra ver as seções (cards) e arquivos.")
        return 0

    # 3) Seções (= cards) + arquivos do curso.
    contents = _call(base, token, "core_course_get_contents", courseid=course_id)
    print(f"\n=== Seções do curso {course_id} (seção = card) ===")
    total_files = 0
    for sec in contents:
        files = []
        for mod in sec.get("modules", []) or []:
            for f in mod.get("contents", []) or []:
                if f.get("type") == "file" and f.get("filename"):
                    files.append(f["filename"])
        total_files += len(files)
        sample = ", ".join(files[:4]) + (" ..." if len(files) > 4 else "")
        print(f"  [{sec.get('name','(sem nome)')}]  {len(files)} arquivo(s)  {sample}")
    print(f"\nTotal de arquivos baixáveis: {total_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
