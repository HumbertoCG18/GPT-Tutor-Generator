"""Credenciais locais fora da árvore do repositório, protegidas pelo sistema operacional (#80; incidente de 24/09).

Nunca grava em texto puro. No Windows, o valor é protegido com DPAPI (escopo do usuário, via ctypes, sem dependência
nova). Fora do Windows não há armazenamento protegido disponível: a gravação falha com `ProtectedStorageUnavailable`,
e cabe ao chamador oferecer um modo explícito sem persistência. Mensagens de erro nunca incluem o valor.
"""
from __future__ import annotations

import ctypes
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional

ENV_CREDENTIALS_DIR = "GPT_TUTOR_CREDENTIALS_DIR"
REPO_ROOT = Path(__file__).resolve().parents[2]
_ENTROPY = b"GPTTutorGenerator/credential-store/v1"
_CRYPTPROTECT_UI_FORBIDDEN = 0x01
_NOME_RE = re.compile(r"[a-z0-9_]+")


class CredentialStoreError(RuntimeError):
    """Falha ao guardar ou ler credencial. A mensagem nunca contém o valor."""


class ProtectedStorageUnavailable(CredentialStoreError):
    """Não há armazenamento protegido pelo sistema operacional neste ambiente."""


def default_credentials_dir() -> Path:
    """Diretório por usuário, independente do diretório corrente."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "GPTTutorGenerator" / "credentials"
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "gpt_tutor_generator" / "credentials"


def is_inside_repo(path: Path, repo_root: Path = REPO_ROOT) -> bool:
    """True se `path`, depois de resolver `..` e links simbólicos, estiver na árvore do repositório."""
    alvo, raiz = Path(path).resolve(), Path(repo_root).resolve()
    return alvo == raiz or raiz in alvo.parents


def credentials_dir(repo_root: Path = REPO_ROOT) -> Path:
    """Diretório efetivo, já resolvido: `GPT_TUTOR_CREDENTIALS_DIR` (absoluto) ou o padrão; nunca no repositório."""
    bruto = os.environ.get(ENV_CREDENTIALS_DIR, "").strip()
    destino = Path(bruto).expanduser() if bruto else default_credentials_dir()
    if not destino.is_absolute():
        raise CredentialStoreError(f"{ENV_CREDENTIALS_DIR} precisa ser um caminho absoluto")
    if is_inside_repo(destino, repo_root):
        raise CredentialStoreError("diretório de credenciais dentro da árvore do repositório: recusado")
    return destino.resolve()


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _blob(buf) -> "_Blob":
    return _Blob(len(buf) - 1, ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))


def _dpapi(data: bytes, protect: bool, crypt32=None, kernel32=None) -> bytes:
    """CryptProtectData/CryptUnprotectData do Windows. `crypt32`/`kernel32` injetáveis para teste."""
    if crypt32 is None:
        if sys.platform != "win32":
            raise ProtectedStorageUnavailable("armazenamento protegido (DPAPI) indisponível fora do Windows")
        crypt32, kernel32 = ctypes.WinDLL("crypt32"), ctypes.WinDLL("kernel32")
    dados, entropia = ctypes.create_string_buffer(data, len(data) + 1), ctypes.create_string_buffer(_ENTROPY)
    entrada, extra, saida = _blob(dados), _blob(entropia), _Blob()
    funcao = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    ok = funcao(ctypes.pointer(entrada), None, ctypes.pointer(extra), None, None,
                _CRYPTPROTECT_UI_FORBIDDEN, ctypes.pointer(saida))
    if not ok:
        raise CredentialStoreError(f"DPAPI {'proteger' if protect else 'abrir'} falhou (código {kernel32.GetLastError()})")
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        kernel32.LocalFree(saida.pbData)


def _arquivo(nome: str, repo_root: Path = REPO_ROOT) -> Path:
    if not _NOME_RE.fullmatch(nome):
        raise ValueError("nome de credencial inválido")
    return credentials_dir(repo_root) / f"{nome}.dpapi"


def ensure_available(repo_root: Path = REPO_ROOT) -> Path:
    """Falha antes de qualquer login se o destino ou a proteção do SO não estiverem disponíveis."""
    destino = credentials_dir(repo_root)
    _dpapi(b"verificacao", True)
    return destino


def save_secret(nome: str, valor: str, repo_root: Path = REPO_ROOT) -> Path:
    """Protege antes de tocar o disco; se a proteção falhar, nada é gravado. Escrita atômica."""
    alvo = _arquivo(nome, repo_root)
    protegido = _dpapi(valor.encode("utf-8"), True)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    # ponytail: rechecar estreita a janela de troca por link; fechá-la exigiria fds de diretório (ausentes no Windows).
    if alvo.parent.resolve() != alvo.parent:
        raise CredentialStoreError("diretório de credenciais mudou durante a gravação: recusado")
    fd, tmp =tempfile.mkstemp(dir=str(alvo.parent), prefix=".tmp-", suffix=".dpapi")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(protegido)
        os.replace(tmp, alvo)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return alvo


def load_secret(nome: str, repo_root: Path = REPO_ROOT) -> Optional[str]:
    """Valor salvo, ou None se não houver. Falha de leitura/proteção vira `CredentialStoreError`."""
    alvo = _arquivo(nome, repo_root)
    if not alvo.is_file():
        return None
    try:
        return _dpapi(alvo.read_bytes(), False).decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # `from None`: UnicodeDecodeError carrega os bytes lidos; a cadeia não pode chegar a logs.
        raise CredentialStoreError(f"credencial ilegível ({type(exc).__name__})") from None
