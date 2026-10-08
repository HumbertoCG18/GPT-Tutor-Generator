"""Credenciais fora do repositório e sem texto puro (#80; incidente de 24/09). Valores sintéticos gerados em runtime."""
import ctypes
import hashlib
import logging
import os
import secrets
import sys

import pytest

from src.builder.sources import m365
from src.utils import credential_store as cs


def _sintetico() -> str:
    return "sint-" + secrets.token_urlsafe(40)


class _FakeCrypt32:
    """Troca CryptProtectData/CryptUnprotectData por XOR reversível; exercita o marshaling do ctypes em qualquer SO."""

    def __init__(self, ok=True):
        self.ok, self.vivos = ok, []

    def _rodar(self, pin, _desc, pent, _res, _prompt, flags, pout):
        assert flags == cs._CRYPTPROTECT_UI_FORBIDDEN
        assert ctypes.string_at(pent.contents.pbData, pent.contents.cbData) == cs._ENTROPY
        if not self.ok:
            return 0
        dados = ctypes.string_at(pin.contents.pbData, pin.contents.cbData)
        saida = bytes(b ^ 0x5A for b in dados)
        buf = ctypes.create_string_buffer(saida, len(saida) + 1)
        self.vivos.append(buf)
        pout.contents.cbData = len(saida)
        pout.contents.pbData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
        return 1

    CryptProtectData = CryptUnprotectData = _rodar


class _FakeKernel32:
    def __init__(self):
        self.liberados = 0

    def GetLastError(self):  # noqa: N802 (nome da API do Windows)
        return 5

    def LocalFree(self, _ptr):  # noqa: N802
        self.liberados += 1


def _dpapi_falso(data, protect, crypt32=None, kernel32=None):
    return bytes(b ^ 0x5A for b in data)


@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.delenv(cs.ENV_CREDENTIALS_DIR, raising=False)
    monkeypatch.delenv(m365.ENV_NO_PERSIST, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(m365, "LEGACY_TOKEN_PATH", tmp_path / "repo-antigo" / "moddle" / ".m365_token.json")
    return tmp_path


# 1. caminho padrão fora do repositório, independente do diretório corrente
def test_caminho_padrao_fora_do_repo_de_qualquer_diretorio(base, monkeypatch):
    vistos = set()
    for cwd in (cs.REPO_ROOT, base, cs.REPO_ROOT / "src"):
        monkeypatch.chdir(cwd)
        d = cs.credentials_dir()
        assert d.is_absolute() and not cs.is_inside_repo(d)
        vistos.add(d)
    assert len(vistos) == 1
    assert str(base.resolve()) in str(next(iter(vistos)))


# 2. caminho configurado dentro do repositório é recusado (também via .., relativo, padrão e link simbólico)
@pytest.mark.parametrize("alvo", ["moddle", "src/../moddle", "."])
def test_caminho_explicito_dentro_do_repo_recusado(base, monkeypatch, alvo):
    monkeypatch.setenv(cs.ENV_CREDENTIALS_DIR, str(cs.REPO_ROOT / alvo))
    with pytest.raises(cs.CredentialStoreError, match="dentro da árvore do repositório"):
        cs.credentials_dir()


def test_caminho_relativo_recusado(base, monkeypatch):
    monkeypatch.setenv(cs.ENV_CREDENTIALS_DIR, "credenciais")
    with pytest.raises(cs.CredentialStoreError, match="absoluto"):
        cs.credentials_dir()


def test_padrao_apontando_para_o_repo_recusado(base, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(cs.REPO_ROOT / "moddle"))
    monkeypatch.setenv("XDG_DATA_HOME", str(cs.REPO_ROOT / "moddle"))
    with pytest.raises(cs.CredentialStoreError, match="dentro da árvore do repositório"):
        cs.credentials_dir()


def test_link_simbolico_para_o_repo_recusado(base, monkeypatch):
    link = base / "atalho"
    try:
        os.symlink(cs.REPO_ROOT, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("criação de link simbólico não permitida neste ambiente")
    monkeypatch.setenv(cs.ENV_CREDENTIALS_DIR, str(link / "moddle"))
    with pytest.raises(cs.CredentialStoreError, match="dentro da árvore do repositório"):
        cs.credentials_dir()


def test_troca_por_link_durante_a_gravacao_recusada(base, monkeypatch):
    cred, outro = base / "cred", base / "outro"
    outro.mkdir()
    monkeypatch.setenv(cs.ENV_CREDENTIALS_DIR, str(cred))

    def protege_e_troca(data, protect, crypt32=None, kernel32=None):
        try:
            os.symlink(outro, cred, target_is_directory=True)  # troca entre a validação e a escrita
        except (OSError, NotImplementedError):
            pytest.skip("criação de link simbólico não permitida neste ambiente")
        return _dpapi_falso(data, protect)

    monkeypatch.setattr(cs, "_dpapi", protege_e_troca)
    with pytest.raises(cs.CredentialStoreError, match="mudou durante a gravação"):
        cs.save_secret("m365_refresh_token", _sintetico())
    assert list(outro.iterdir()) == []


# 3. falha da proteção: nada em texto puro, nada no caminho antigo, falha antes do login
def test_falha_da_protecao_nao_grava_nada(base, monkeypatch):
    def indisponivel(*a, **k):
        raise cs.ProtectedStorageUnavailable("sem DPAPI")

    monkeypatch.setattr(cs, "_dpapi", indisponivel)
    valor = _sintetico()
    with pytest.raises(cs.ProtectedStorageUnavailable):
        cs.save_secret("m365_refresh_token", valor)
    with pytest.raises(cs.ProtectedStorageUnavailable):
        m365._save_token({"refresh_token": valor})
    assert not m365.LEGACY_TOKEN_PATH.exists()
    for p in base.rglob("*"):
        assert not p.is_file() or valor.encode() not in p.read_bytes()


def test_sem_protecao_falha_antes_do_device_login(base, monkeypatch):
    def indisponivel(*a, **k):
        raise cs.ProtectedStorageUnavailable("sem DPAPI")

    def rede_proibida(*a, **k):
        raise AssertionError("não deveria chamar a rede")

    monkeypatch.setattr(cs, "_dpapi", indisponivel)
    monkeypatch.setattr(m365.requests, "post", rede_proibida)
    with pytest.raises(cs.ProtectedStorageUnavailable) as ei:
        m365.get_client(prompt_callback=lambda info: None)
    assert m365.ENV_NO_PERSIST in str(ei.value)[:160]  # src/ui/dialogs.py mostra str(exc)[:160]


def test_destino_no_repo_falha_antes_do_device_login(base, monkeypatch):
    monkeypatch.setenv(cs.ENV_CREDENTIALS_DIR, str(cs.REPO_ROOT / "moddle"))
    monkeypatch.setattr(cs, "_dpapi", _dpapi_falso)
    monkeypatch.setattr(m365.requests, "post", lambda *a, **k: pytest.fail("não deveria chamar a rede"))
    with pytest.raises(cs.CredentialStoreError, match="dentro da árvore do repositório"):
        m365.get_client(prompt_callback=lambda info: None)


# persistência protegida: arquivo sem texto puro, escrita atômica, ida e volta
def test_ida_e_volta_sem_texto_puro(base, monkeypatch):
    monkeypatch.setattr(cs, "_dpapi", _dpapi_falso)
    valor = _sintetico()
    alvo = cs.save_secret("m365_refresh_token", valor)
    assert alvo.suffix == ".dpapi" and not cs.is_inside_repo(alvo)
    assert valor.encode() not in alvo.read_bytes()
    assert cs.load_secret("m365_refresh_token") == valor
    assert [p.name for p in alvo.parent.iterdir()] == [alvo.name]


def test_nome_invalido_recusado(base):
    with pytest.raises(ValueError):
        cs.save_secret("../fora", "x")


def test_marshaling_dpapi_com_bibliotecas_falsas():
    crypt32, kernel32 = _FakeCrypt32(), _FakeKernel32()
    protegido = cs._dpapi(b"abc\x00def", True, crypt32=crypt32, kernel32=kernel32)
    assert protegido == bytes(b ^ 0x5A for b in b"abc\x00def")
    assert cs._dpapi(protegido, False, crypt32=crypt32, kernel32=kernel32) == b"abc\x00def"
    assert kernel32.liberados == 2
    with pytest.raises(cs.CredentialStoreError, match="código 5"):
        cs._dpapi(b"x", True, crypt32=_FakeCrypt32(ok=False), kernel32=kernel32)


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI real só no Windows")
def test_dpapi_real_windows(base, monkeypatch):
    monkeypatch.setenv(cs.ENV_CREDENTIALS_DIR, str(base / "cred"))
    valor = _sintetico()
    alvo = cs.save_secret("teste_dpapi", valor)
    assert valor.encode() not in alvo.read_bytes()
    assert cs.load_secret("teste_dpapi") == valor


@pytest.mark.skipif(sys.platform == "win32", reason="fora do Windows")
def test_fora_do_windows_indisponivel(base):
    with pytest.raises(cs.ProtectedStorageUnavailable):
        cs.ensure_available()


# cache legado: nunca lido, migrado ou apagado; 10. logs sem valores sintéticos
def test_cache_legado_ignorado_e_logs_sem_valores(base, monkeypatch, caplog):
    monkeypatch.setattr(cs, "_dpapi", _dpapi_falso)
    monkeypatch.setattr(m365.time, "sleep", lambda s: None)
    antigo, novo_rt, novo_at = _sintetico(), _sintetico(), _sintetico()
    m365.LEGACY_TOKEN_PATH.parent.mkdir(parents=True)
    m365.LEGACY_TOKEN_PATH.write_text('{"refresh_token": "%s"}' % antigo, encoding="utf-8")
    hash_antes = hashlib.sha256(m365.LEGACY_TOKEN_PATH.read_bytes()).hexdigest()
    enviados = []

    def post(url, data=None, timeout=0):
        enviados.append(dict(data or {}))
        if "devicecode" in url:
            return _Resp({"verification_uri": "https://exemplo.invalid", "user_code": "COD",
                          "device_code": "dc", "interval": 1, "expires_in": 60})
        return _Resp({"access_token": novo_at, "refresh_token": novo_rt})

    monkeypatch.setattr(m365.requests, "post", post)
    with caplog.at_level(logging.DEBUG):
        cliente = m365.get_client(prompt_callback=lambda info: None)
    assert cliente._token == novo_at
    assert hashlib.sha256(m365.LEGACY_TOKEN_PATH.read_bytes()).hexdigest() == hash_antes
    assert all(antigo not in str(d) for d in enviados)
    assert "IGNORADO" in caplog.text
    for v in (antigo, novo_rt, novo_at):
        assert v not in caplog.text
    assert cs.load_secret("m365_refresh_token") == novo_rt


def test_modo_sem_persistencia_nao_grava(base, monkeypatch):
    monkeypatch.setenv(m365.ENV_NO_PERSIST, "1")
    monkeypatch.setattr(m365.time, "sleep", lambda s: None)

    def indisponivel(*a, **k):
        raise cs.ProtectedStorageUnavailable("sem DPAPI")

    monkeypatch.setattr(cs, "_dpapi", indisponivel)
    at = _sintetico()
    monkeypatch.setattr(m365.requests, "post", lambda url, data=None, timeout=0: (
        _Resp({"verification_uri": "https://exemplo.invalid", "user_code": "COD", "device_code": "dc",
               "interval": 1, "expires_in": 60}) if "devicecode" in url
        else _Resp({"access_token": at, "refresh_token": _sintetico()})))
    assert m365.get_client(prompt_callback=lambda info: None)._token == at
    assert not (base / "local").exists() and not (base / "xdg").exists()


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def json(self):
        return self._p

    def raise_for_status(self):
        return None
