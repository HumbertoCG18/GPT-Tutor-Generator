"""Renovacao automatica do token do Moodle (moddle/.env local, gitignored)."""
import pytest

import scripts.moodle_token as MT


def _env(tmp_path, text):
    env = tmp_path / ".env"
    env.write_text(text, encoding="utf-8")
    return env


def test_write_token_preserva_o_resto(tmp_path):
    env = _env(tmp_path, "MOODLE_URL=https://m.x\nMOODLE_TOKEN=velho\nMOODLE_USER=u\n")
    MT._write_token("novo123", env)
    linhas = env.read_text(encoding="utf-8").splitlines()
    assert "MOODLE_TOKEN=novo123" in linhas
    assert "MOODLE_URL=https://m.x" in linhas and "MOODLE_USER=u" in linhas


def test_ensure_renova_quando_invalido(tmp_path, monkeypatch):
    env = _env(tmp_path, "MOODLE_URL=https://m.x\nMOODLE_TOKEN=expirado\nMOODLE_USER=u\nMOODLE_PASS=p\n")
    respostas = {"webservice/rest/server.php": {"errorcode": "invalidtoken"},
                 "login/token.php": {"token": "fresquinho"}}
    monkeypatch.setattr(MT, "_call", lambda url, ep, params: respostas[ep])
    url, tok = MT.ensure_moodle_token(env)
    assert (url, tok) == ("https://m.x", "fresquinho")
    assert "MOODLE_TOKEN=fresquinho" in env.read_text(encoding="utf-8")


def test_ensure_sem_credenciais_avisa(tmp_path, monkeypatch):
    env = _env(tmp_path, "MOODLE_URL=https://m.x\nMOODLE_TOKEN=expirado\n")
    monkeypatch.setattr(MT, "_call", lambda url, ep, params: {"errorcode": "invalidtoken"})
    with pytest.raises(RuntimeError, match="MOODLE_USER"):
        MT.ensure_moodle_token(env)


def test_ensure_token_valido_nao_mexe(tmp_path, monkeypatch):
    env = _env(tmp_path, "MOODLE_URL=https://m.x\nMOODLE_TOKEN=ok\n")
    monkeypatch.setattr(MT, "_call", lambda url, ep, params: {"sitename": "x"})
    assert MT.ensure_moodle_token(env) == ("https://m.x", "ok")
