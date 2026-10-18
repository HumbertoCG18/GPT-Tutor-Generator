"""Token do Moodle com renovacao automatica (2026-08-31, pedido do user).

O token do webservice expira; ficar renovando a mao em moddle/.env quebrava o pull
("invalidtoken" ate no site_info). O endpoint publico `login/token.php` da PUCRS
aceita usuario/senha (verificado: usuario falso -> "invalidlogin", nao bloqueio de
SSO), entao com MOODLE_USER e MOODLE_PASS no moddle/.env o token se renova sozinho:

    from scripts.moodle_token import ensure_moodle_token
    url, tok = ensure_moodle_token()   # valido, renovado se preciso, regravado no .env

Sem credenciais no .env, comporta-se como antes (usa o token que estiver la).
O .env e local e gitignored (`/moddle/*`); token e senha NUNCA sao impressos.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / "moddle" / ".env"


def _read_env(path: Path = ENV_PATH) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _write_token(token: str, path: Path = ENV_PATH) -> None:
    """Regrava so a linha MOODLE_TOKEN, preservando o resto do arquivo."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == "MOODLE_TOKEN":
            lines[i] = f"MOODLE_TOKEN={token}"
            break
    else:
        lines.append(f"MOODLE_TOKEN={token}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _call(url: str, endpoint: str, params: dict) -> dict:
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}/{endpoint}?{q}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def token_valido(url: str, token: str) -> bool:
    if not token:
        return False
    payload = _call(url, "webservice/rest/server.php",
                    {"wstoken": token, "wsfunction": "core_webservice_get_site_info", "moodlewsrestformat": "json"})
    return not (isinstance(payload, dict) and payload.get("errorcode"))


def renovar_token(url: str, user: str, password: str) -> str:
    """login/token.php -> token novo; RuntimeError com o errorcode se falhar (sem ecoar senha)."""
    payload = _call(url, "login/token.php",
                    {"username": user, "password": password, "service": "moodle_mobile_app"})
    if payload.get("token"):
        return str(payload["token"])
    raise RuntimeError(f"token.php falhou: {payload.get('errorcode') or 'sem token na resposta'}")


def ensure_moodle_token(env_path: Path = ENV_PATH) -> tuple[str, str]:
    """(url, token) valido. Renova via credenciais do .env quando o atual expirou."""
    env = _read_env(env_path)
    url = env.get("MOODLE_URL", "").strip().rstrip("/")
    tok = env.get("MOODLE_TOKEN", "").strip()
    if not url:
        raise RuntimeError("MOODLE_URL ausente no moddle/.env")
    if token_valido(url, tok):
        return url, tok
    user, password = env.get("MOODLE_USER", "").strip(), env.get("MOODLE_PASS", "").strip()
    if not (user and password):
        raise RuntimeError("token invalido/expirado e sem MOODLE_USER/MOODLE_PASS no moddle/.env para renovar")
    tok = renovar_token(url, user, password)
    _write_token(tok, env_path)
    print("[moodle] token renovado e regravado em moddle/.env")
    return url, tok
