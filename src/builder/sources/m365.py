"""Cliente Microsoft Graph (OneDrive/SharePoint) — fonte secundária de cards.

Arquivos que o professor hospeda no OneDrive dele não aparecem na API do Moodle.
Descoberta via /me/insights/shared (o que a página /shared do OneDrive mostra),
download via /me/insights/shared/{id}/resource. Auth device-code (client público
"Microsoft Graph Command Line Tools"); só leitura. Token em moddle/.m365_token.json.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse
from pathlib import Path

import requests

from src.builder.sources.moodle import (
    looks_like_expected, sanitize_folder_name, default_token_path,
)

log = logging.getLogger("m365")

_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # Microsoft Graph Command Line Tools
_AUTHORITY = "https://login.microsoftonline.com/organizations/oauth2/v2.0"
_SCOPE = "Files.Read.All Sites.Read.All offline_access"
_GRAPH = "https://graph.microsoft.com/v1.0"
_ROOT_CARD = "_geral"


def parse_onedrive_path(web_url: str) -> list:
    p = urllib.parse.urlparse(str(web_url or ""))
    return [seg for seg in urllib.parse.unquote(p.path).split("/") if seg]


def subfolder_for(web_url: str, m365_filter: str, default: str = _ROOT_CARD) -> str:
    segs = parse_onedrive_path(web_url)
    fl = (m365_filter or "").lower()
    idx = next((i for i, s in enumerate(segs) if fl and fl in s.lower()), None)
    if idx is None:
        return default
    after = segs[idx + 1:]
    if len(after) <= 1:                       # só o nome do arquivo -> raiz do curso
        return default
    return sanitize_folder_name(after[0])


def filter_in_path(web_url: str, m365_filter: str) -> bool:
    """True se o filtro casa algum segmento do CAMINHO (não só o nome do arquivo)."""
    fl = (m365_filter or "").lower()
    segs = parse_onedrive_path(web_url)
    return any(fl and fl in s.lower() for s in segs[:-1]) if segs else False


def select_for_subject(items, m365_filter: str) -> list:
    fl = (m365_filter or "").lower()
    if not fl:
        return []
    return [it for it in items if fl in str(it.get("web_url", "")).lower()]


class M365Client:
    def __init__(self, access_token: str):
        self._token = access_token

    def _get(self, path: str) -> dict:
        r = requests.get(f"{_GRAPH}{path}",
                         headers={"Authorization": f"Bearer {self._token}"}, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"Graph {r.status_code}: {r.text[:200]}")
        return r.json()

    def list_shared(self, top: int = 200) -> list:
        out, url = [], f"{_GRAPH}/me/insights/shared?$top={top}"
        while url:
            r = requests.get(url, headers={"Authorization": f"Bearer {self._token}"}, timeout=60)
            if r.status_code >= 400:
                raise RuntimeError(f"Graph {r.status_code}: {r.text[:200]}")
            data = r.json()
            for it in data.get("value", []):
                rv = it.get("resourceVisualization") or {}
                rr = it.get("resourceReference") or {}
                out.append({"id": it.get("id"), "title": rv.get("title"),
                            "type": rv.get("type"), "web_url": rr.get("webUrl", "")})
            url = data.get("@odata.nextLink")
        log.info("insights/shared: %d itens", len(out))
        return out

    def resolve(self, insight_id: str) -> dict:
        return self._get(f"/me/insights/shared/{urllib.parse.quote(insight_id, safe='')}/resource")

    def download(self, item: dict) -> bytes:
        dl = item.get("@microsoft.graph.downloadUrl")
        if dl:
            r = requests.get(dl, timeout=180)
            r.raise_for_status()
            return r.content
        pref = item["parentReference"]
        r = requests.get(f"{_GRAPH}/drives/{pref['driveId']}/items/{item['id']}/content",
                         headers={"Authorization": f"Bearer {self._token}"}, timeout=180)
        r.raise_for_status()
        return r.content


def _token_path() -> Path:
    return default_token_path().parent / ".m365_token.json"


def _save_token(tok: dict) -> None:
    rt = tok.get("refresh_token")
    if not rt:
        return
    p = _token_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"refresh_token": rt}), encoding="utf-8")


def load_cached_token():
    """Access token via refresh token salvo, ou None se ausente/expirado."""
    p = _token_path()
    if not p.is_file():
        return None
    try:
        rt = (json.loads(p.read_text(encoding="utf-8")) or {}).get("refresh_token")
    except (ValueError, OSError):
        return None
    if not rt:
        return None
    j = requests.post(f"{_AUTHORITY}/token", timeout=30, data={
        "grant_type": "refresh_token", "client_id": _CLIENT_ID,
        "refresh_token": rt, "scope": _SCOPE}).json()
    if "access_token" in j:
        _save_token(j)
        return j["access_token"]
    return None


def device_login(prompt_callback=None) -> str:
    """Device-code flow. prompt_callback({verification_uri, user_code}) p/ a UI."""
    r = requests.post(f"{_AUTHORITY}/devicecode", timeout=30,
                      data={"client_id": _CLIENT_ID, "scope": _SCOPE})
    r.raise_for_status()
    d = r.json()
    info = {"verification_uri": d["verification_uri"], "user_code": d["user_code"]}
    log.info("device-code: abra %s e digite %s", info["verification_uri"], info["user_code"])
    if prompt_callback:
        prompt_callback(info)
    else:
        print(f"Abra {info['verification_uri']} e digite {info['user_code']}")
    interval = int(d.get("interval", 5))
    deadline = time.time() + int(d.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(interval)
        j = requests.post(f"{_AUTHORITY}/token", timeout=30, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": _CLIENT_ID, "device_code": d["device_code"]}).json()
        if "access_token" in j:
            _save_token(j)
            log.info("autenticado com sucesso")
            return j["access_token"]
        err = j.get("error")
        if err == "slow_down":
            interval += 5
            continue
        if err == "authorization_pending":
            continue
        log.error("device-code falhou: %s — %s", err, j.get("error_description", "")[:200])
        raise RuntimeError(f"device-code falhou: {err}")
    raise RuntimeError("Tempo de login M365 esgotado.")


def get_client(prompt_callback=None) -> "M365Client":
    """Cliente pronto: usa refresh token salvo ou faz device-login."""
    tok = load_cached_token()
    if tok:
        log.info("usando refresh token salvo")
    else:
        log.info("sem token salvo — iniciando device-login")
        tok = device_login(prompt_callback)
    return M365Client(tok)


def download_subject_m365(client, m365_filter, section_index, dest,
                          skip_existing: bool = True, progress_cb=None) -> dict:
    """Baixa os arquivos M365 da matéria pros cards das seções REAIS do Moodle.

    section_index: {basename.casefold(): secao} de section_file_index_strict
    (chaves são re-sanitizadas aqui — nomes Moodle crus e nomes M365 sanitizados casam) —
    a ÚNICA fonte de card. Miss/ambíguo/índice vazio => subpasta literal do
    OneDrive (ou _geral) com matched=False; NUNCA match léxico (a spec
    2026-06-11 matou o match_card: pasta-tópico do professor não é card).

    Retorna {total, downloaded, failed, mapping: [(basename, card, origem)],
             name_to_section (só origem moodle_api), warnings: [str]}.
    """
    dest = Path(dest)
    index = {sanitize_folder_name(str(k)).casefold(): v
             for k, v in (section_index or {}).items()}
    items = select_for_subject(client.list_shared(), m365_filter)
    total = len(items)
    warnings: list = []
    if not items:
        warnings.append(
            "filtro não casou nenhum item compartilhado — confira a grafia "
            "(o filtro é substring da URL do OneDrive, sem espaços/acentos)")
        log.warning(warnings[-1])
        return {"total": 0, "downloaded": 0, "failed": [], "mapping": [],
                "name_to_section": {}, "warnings": warnings}
    misses = sum(1 for it in items if not filter_in_path(it.get("web_url", ""), m365_filter))
    if misses * 2 > total:
        warnings.append(
            f"filtro não aparece no caminho de pastas de {misses}/{total} arquivos — "
            "layout pode cair todo em _geral")
    if not index:
        warnings.append(
            "API Moodle indisponível ou sem arquivos no curso — nenhum card "
            "atribuído pela API; arquivos ficam nas pastas literais do OneDrive")
    log.info("filtro '%s': %d item(ns) -> %s", m365_filter, total, dest)
    downloaded, failed = 0, []
    mapping: list = []
    name_to_section: dict = {}
    seen: set = set()
    for idx, it in enumerate(items):
        try:
            res = client.resolve(it["id"])
            raw_name = res.get("name") or it.get("title") or "arquivo"
            name = sanitize_folder_name(raw_name)
            data = client.download(res)
        except Exception:
            log.exception("falha ao baixar item %r", it.get("title") or it.get("id"))
            failed.append(it.get("title") or it.get("id"))
            continue
        if not looks_like_expected(name, data):
            log.warning("magic-byte inválido, pulando: %s (%d bytes)", name, len(data))
            failed.append(name)
            continue
        section = index.get(name.casefold(), "")
        if section:
            card, origem = section, "moodle_api"
        else:
            card, origem = subfolder_for(it.get("web_url", ""), m365_filter), "fallback_pasta"
        card = sanitize_folder_name(card) or _ROOT_CARD
        if progress_cb:
            progress_cb(idx + 1, total, name, card)
        folder = dest / card
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / name
        if target in seen:                       # colisão intra-execução
            stem, suf = target.stem, target.suffix
            i = 2
            while (folder / f"{stem} ({i}){suf}") in seen:
                i += 1
            target = folder / f"{stem} ({i}){suf}"
        seen.add(target)
        mapping.append((target.name, card, origem))
        if origem == "moodle_api":
            name_to_section[target.name.casefold()] = section
        if skip_existing and target.exists():
            log.info("já existe, pulando: %s/%s", card, target.name)
            continue
        target.write_bytes(data)
        downloaded += 1
        log.info("baixado: %s/%s (%d bytes)", card, target.name, len(data))
    log.info("concluído: %d baixados, %d falhas, %d aviso(s)",
             downloaded, len(failed), len(warnings))
    return {"total": total, "downloaded": downloaded, "failed": failed,
            "mapping": mapping, "name_to_section": name_to_section,
            "warnings": warnings}


def apply_source_section(repo_root: str, name_to_section: dict) -> int:
    """Preenche source_section no manifest casando por basename (case-insensitive).

    name_to_section: {basename.casefold(): card}. Retorna nº de entries atualizadas.
    Faz backup .apibak e escreve atômico. No-op se não houver manifest."""
    if not repo_root:
        return 0
    mpath = Path(repo_root) / "manifest.json"
    if not mpath.is_file():
        return 0
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    updated = 0
    for e in entries:
        base = Path(str(e.get("source_path") or "")).name.casefold()
        sec = name_to_section.get(base)
        if sec and e.get("source_section") != sec:
            e["source_section"] = sec
            updated += 1
    if updated:
        mpath.with_suffix(".json.apibak").write_text(
            mpath.read_text(encoding="utf-8"), encoding="utf-8")
        tmp = mpath.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(mpath)
    return updated
