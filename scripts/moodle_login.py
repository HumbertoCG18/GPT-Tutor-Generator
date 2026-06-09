"""Debug: cunha o wstoken a partir de matrícula/senha e grava em moddle/.env.

Senha NÃO é persistida. Lida via getpass (não ecoa, não fica no histórico).

Uso:
    python -m scripts.moodle_login            # pergunta usuário/senha
    python -m scripts.moodle_login --user MAT # pergunta só a senha
"""
from __future__ import annotations

import getpass
import sys

from src.builder.sources.moodle import MoodleClient, save_moodle_token, load_moodle_token


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    url, _ = load_moodle_token()
    user = ""
    if "--user" in argv:
        i = argv.index("--user")
        if i + 1 < len(argv):
            user = argv[i + 1]
    if not user:
        user = input("Matrícula: ").strip()
    password = getpass.getpass("Senha (não será salva): ")
    try:
        token = MoodleClient.login(url, user, password)
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1
    save_moodle_token(token, url=url)
    print("Token salvo em moddle/.env (senha descartada).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
