# M365/OneDrive Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import a professor's OneDrive-hosted course files (invisible to the Moodle WS API) into the subject's card folders, discovered via Microsoft Graph Insights and authenticated with device-code OAuth.

**Architecture:** New `src/builder/sources/m365.py` module: device-code OAuth (public Graph CLI client, token cached in `moddle/.m365_token.json`), discovery via `/me/insights/shared?$top=200` filtered by a per-subject path substring, download via `/me/insights/shared/{id}/resource`. OneDrive subfolders merge into Moodle cards by token similarity (fallback: new card). Wired into the existing Moodle import dialog.

**Tech Stack:** Python 3.8+, `requests` (existing dep), Microsoft Graph v1.0, tkinter. Reuses `looks_like_expected` and `sanitize_folder_name` from `moodle.py`.

---

## File Structure

- **Create** `src/builder/sources/m365.py` — Graph client + pure helpers + orchestration.
- **Create** `tests/test_m365.py` — unit tests (requests mocked).
- **Modify** `src/models/core.py` — add `SubjectProfile.m365_filter`.
- **Modify** `src/ui/dialogs.py` — checkbox + filter field + device-code dialog + report in the Moodle import flow.
- **Modify** `.gitignore` — ignore `moddle/.m365_token.json`.

Validated against the PUCRS tenant by `scripts/m365_probe.py` (committed spike).

---

## Task 1: SubjectProfile.m365_filter + gitignore

**Files:**
- Modify: `src/models/core.py:188` (after the `queue` field of `SubjectProfile`)
- Modify: `.gitignore`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_subject_profile_m365_filter_roundtrip():
    from src.models.core import SubjectProfile
    sp = SubjectProfile(name="Métodos Formais", slug="metodos-formais", m365_filter="metodosformais")
    d = sp.to_dict()
    assert d["m365_filter"] == "metodosformais"
    sp2 = SubjectProfile.from_dict(d)
    assert sp2.m365_filter == "metodosformais"

def test_subject_profile_m365_filter_defaults_empty_for_old_profiles():
    from src.models.core import SubjectProfile
    sp = SubjectProfile.from_dict({"name": "x", "slug": "x"})   # sem o campo
    assert sp.m365_filter == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_core.py::test_subject_profile_m365_filter_roundtrip -q`
Expected: FAIL (`TypeError: unexpected keyword argument 'm365_filter'`)

- [ ] **Step 3: Add the field**

In `src/models/core.py`, in `class SubjectProfile`, add after `moodle_course_id` (line 185):

```python
    m365_filter: str = ""        # substring do path OneDrive p/ filtrar insights (M365)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_core.py -q -k m365`
Expected: 2 passed

- [ ] **Step 5: Add gitignore entry**

Append to `.gitignore`:

```
moddle/.m365_token.json
```

- [ ] **Step 6: Commit**

```bash
git add src/models/core.py tests/test_core.py .gitignore
git commit -m "feat(m365): SubjectProfile.m365_filter + gitignore token cache"
```

---

## Task 2: Pure path helpers

**Files:**
- Create: `src/builder/sources/m365.py`
- Test: `tests/test_m365.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_m365.py`:

```python
from src.builder.sources.m365 import (
    parse_onedrive_path, subfolder_for, select_for_subject,
)

_BASE = "https://brpucrs-my.sharepoint.com/personal/10070245_pucrs_br/Documents/Documentos"

def test_parse_onedrive_path_segments():
    segs = parse_onedrive_path(f"{_BASE}/metodosformais/dafny/hoare.zip")
    assert segs[-3:] == ["metodosformais", "dafny", "hoare.zip"]

def test_subfolder_for_uses_immediate_subfolder():
    assert subfolder_for(f"{_BASE}/metodosformais/dafny/hoare.zip", "metodosformais") == "dafny"
    assert subfolder_for(f"{_BASE}/metodosformais/logica_programas/Hoare.pdf", "metodosformais") == "logica_programas"

def test_subfolder_for_root_file_is_default():
    assert subfolder_for(f"{_BASE}/metodosformais/plano.pdf", "metodosformais") == "_geral"

def test_select_for_subject_filters_by_substring():
    items = [
        {"web_url": f"{_BASE}/metodosformais/dafny/a.pdf"},
        {"web_url": f"{_BASE}/engenhariadesoftware2/b.pdf"},
        {"web_url": "https://outlook.office.com/owa/?x=AttachmentId"},
    ]
    out = select_for_subject(items, "metodosformais")
    assert len(out) == 1 and "dafny" in out[0]["web_url"]

def test_select_for_subject_empty_filter_returns_nothing():
    assert select_for_subject([{"web_url": "x"}], "") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_m365.py -q`
Expected: FAIL (`ModuleNotFoundError: src.builder.sources.m365`)

- [ ] **Step 3: Create the module with the helpers**

Create `src/builder/sources/m365.py`:

```python
"""Cliente Microsoft Graph (OneDrive/SharePoint) — fonte secundária de cards.

Arquivos que o professor hospeda no OneDrive dele não aparecem na API do Moodle.
Descoberta via /me/insights/shared (o que a página /shared do OneDrive mostra),
download via /me/insights/shared/{id}/resource. Auth device-code (client público
"Microsoft Graph Command Line Tools"); só leitura. Token em moddle/.m365_token.json.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.parse
from pathlib import Path

import requests

from src.builder.sources.moodle import (
    looks_like_expected, sanitize_folder_name, default_token_path,
)

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


def select_for_subject(items, m365_filter: str) -> list:
    fl = (m365_filter or "").lower()
    if not fl:
        return []
    return [it for it in items if fl in str(it.get("web_url", "")).lower()]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_m365.py -q`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/m365.py tests/test_m365.py
git commit -m "feat(m365): path helpers (parse/subfolder/select)"
```

---

## Task 3: Card matcher (merge by token similarity)

**Files:**
- Modify: `src/builder/sources/m365.py`
- Test: `tests/test_m365.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_m365.py`:

```python
from src.builder.sources.m365 import match_card

_SECTIONS = ["Introdução a Métodos Formais", "Provas por Indução",
             "Verificação de Programas", "Plano de Ensino"]

def test_match_card_matches_by_normalized_tokens():
    assert match_card("introducao", _SECTIONS) == ("Introdução a Métodos Formais", True)
    assert match_card("correcao_provasinducao", _SECTIONS)[1] is True
    assert match_card("logica_programas", _SECTIONS) == ("Verificação de Programas", True)

def test_match_card_falls_back_to_new_card_when_no_match():
    card, matched = match_card("dafny", _SECTIONS)
    assert matched is False and card == "dafny"
```

Note: `correcao_provasinducao` → tokens {correcao, provasinducao}? Tokenization splits on `_ - . / space` only, so `provasinducao` stays one token and would NOT match {provas, por, inducao}. To make the real PUCRS folders match, the test expects a match — so the implementation must also split camel/joined forms is NOT feasible; instead lower the bar: match if ANY shared token OR substring containment between tokens. The implementation below handles `provasinducao` by substring containment against section tokens (`provas`, `inducao` are substrings of `provasinducao`).

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_m365.py -q -k match_card`
Expected: FAIL (`ImportError: cannot import name 'match_card'`)

- [ ] **Step 3: Implement match_card**

Append to `src/builder/sources/m365.py`:

```python
def _norm_tokens(s: str) -> set:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii").lower()
    return {t for t in re.split(r"[\s_\-./]+", s) if len(t) > 2}


def _token_affinity(a: set, b: set) -> float:
    """Sobreposição tolerante: conta tokens iguais OU um contido no outro."""
    if not a or not b:
        return 0.0
    hits = 0
    for ta in a:
        if any(ta == tb or ta in tb or tb in ta for tb in b):
            hits += 1
    return hits / min(len(a), len(b))


def match_card(subfolder: str, moodle_sections, threshold: float = 0.34):
    sf = _norm_tokens(subfolder)
    best, best_score = None, 0.0
    for sec in moodle_sections or []:
        score = _token_affinity(sf, _norm_tokens(sec))
        if score > best_score:
            best, best_score = sec, score
    if best and best_score >= threshold:
        return best, True
    return sanitize_folder_name(subfolder), False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_m365.py -q -k match_card`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/m365.py tests/test_m365.py
git commit -m "feat(m365): merge subfolder into Moodle card by token affinity"
```

---

## Task 4: Graph client (list_shared paginated, resolve, download)

**Files:**
- Modify: `src/builder/sources/m365.py`
- Test: `tests/test_m365.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_m365.py`:

```python
from src.builder.sources import m365 as m365mod

class _Resp:
    def __init__(self, status=200, payload=None, content=b""):
        self.status_code = status; self._p = payload or {}; self.content = content; self.text = str(payload)
    def json(self): return self._p
    def raise_for_status(self):
        if self.status_code >= 400: raise RuntimeError(f"http {self.status_code}")

def test_list_shared_follows_pagination(monkeypatch):
    pages = {
        "https://graph.microsoft.com/v1.0/me/insights/shared?$top=200": _Resp(payload={
            "value": [{"id": "1", "resourceVisualization": {"title": "a.pdf", "type": "Pdf"},
                       "resourceReference": {"webUrl": "u/a"}}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/insights/shared?$skip=1"}),
        "https://graph.microsoft.com/v1.0/me/insights/shared?$skip=1": _Resp(payload={
            "value": [{"id": "2", "resourceVisualization": {"title": "b.pdf", "type": "Pdf"},
                       "resourceReference": {"webUrl": "u/b"}}]}),
    }
    monkeypatch.setattr(m365mod.requests, "get", lambda url, headers=None, timeout=0: pages[url])
    c = m365mod.M365Client("tok")
    items = c.list_shared(top=200)
    assert [it["id"] for it in items] == ["1", "2"]
    assert items[0]["title"] == "a.pdf" and items[0]["web_url"] == "u/a"

def test_resolve_and_download_via_downloadurl(monkeypatch):
    calls = {}
    def fake_get(url, headers=None, timeout=0):
        if "/resource" in url:
            return _Resp(payload={"name": "x.pdf", "id": "I", "file": {},
                                  "@microsoft.graph.downloadUrl": "https://dl/x"})
        if url == "https://dl/x":
            calls["dl"] = True
            return _Resp(content=b"%PDF-1.7 ok")
        raise AssertionError(url)
    monkeypatch.setattr(m365mod.requests, "get", fake_get)
    c = m365mod.M365Client("tok")
    res = c.resolve("INS")
    data = c.download(res)
    assert res["name"] == "x.pdf" and data[:4] == b"%PDF" and calls["dl"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_m365.py -q -k "list_shared or resolve"`
Expected: FAIL (`AttributeError: module ... has no attribute 'M365Client'`)

- [ ] **Step 3: Implement M365Client**

Append to `src/builder/sources/m365.py`:

```python
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
        return out

    def resolve(self, insight_id: str) -> dict:
        return self._get(f"/me/insights/shared/{urllib.parse.quote(insight_id, safe='')}/resource")

    def download(self, item: dict) -> bytes:
        dl = item.get("@microsoft.graph.downloadUrl")
        if dl:
            return requests.get(dl, timeout=180).content
        pref = item["parentReference"]
        r = requests.get(f"{_GRAPH}/drives/{pref['driveId']}/items/{item['id']}/content",
                         headers={"Authorization": f"Bearer {self._token}"}, timeout=180)
        r.raise_for_status()
        return r.content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_m365.py -q -k "list_shared or resolve"`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/m365.py tests/test_m365.py
git commit -m "feat(m365): Graph client list_shared(paginated)/resolve/download"
```

---

## Task 5: Token cache + device-code login

**Files:**
- Modify: `src/builder/sources/m365.py`
- Test: `tests/test_m365.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_m365.py`:

```python
def test_device_login_polls_until_token(monkeypatch, tmp_path):
    monkeypatch.setattr(m365mod, "_token_path", lambda: tmp_path / ".m365_token.json")
    monkeypatch.setattr(m365mod.time, "sleep", lambda s: None)
    seq = [
        _Resp(payload={"verification_uri": "https://aka.ms/dev", "user_code": "ABC",
                       "device_code": "DC", "interval": 1, "expires_in": 900}),
    ]
    posts = [
        _Resp(payload={"error": "authorization_pending"}),
        _Resp(payload={"access_token": "AT", "refresh_token": "RT"}),
    ]
    monkeypatch.setattr(m365mod.requests, "post",
                        lambda url, data=None, timeout=0: seq.pop(0) if "devicecode" in url else posts.pop(0))
    shown = {}
    tok = m365mod.device_login(prompt_callback=lambda m: shown.update(m))
    assert tok == "AT"
    assert shown["user_code"] == "ABC"
    saved = (tmp_path / ".m365_token.json").read_text(encoding="utf-8")
    assert "RT" in saved

def test_load_cached_token_refreshes(monkeypatch, tmp_path):
    p = tmp_path / ".m365_token.json"
    p.write_text('{"refresh_token": "RT"}', encoding="utf-8")
    monkeypatch.setattr(m365mod, "_token_path", lambda: p)
    monkeypatch.setattr(m365mod.requests, "post",
                        lambda url, data=None, timeout=0: _Resp(payload={"access_token": "NEW", "refresh_token": "RT2"}))
    assert m365mod.load_cached_token() == "NEW"
    assert "RT2" in p.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_m365.py -q -k "device_login or cached_token"`
Expected: FAIL (`AttributeError: ... 'device_login'`)

- [ ] **Step 3: Implement token cache + device login**

Append to `src/builder/sources/m365.py`:

```python
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
    rt = (json.loads(p.read_text(encoding="utf-8")) or {}).get("refresh_token")
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
            return j["access_token"]
        err = j.get("error")
        if err == "slow_down":
            interval += 5
            continue
        if err == "authorization_pending":
            continue
        raise RuntimeError(f"device-code falhou: {err}")
    raise RuntimeError("Tempo de login M365 esgotado.")


def get_client(prompt_callback=None) -> "M365Client":
    """Cliente pronto: usa refresh token salvo ou faz device-login."""
    tok = load_cached_token()
    if not tok:
        tok = device_login(prompt_callback)
    return M365Client(tok)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_m365.py -q -k "device_login or cached_token"`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/m365.py tests/test_m365.py
git commit -m "feat(m365): device-code login + refresh token cache"
```

---

## Task 6: source_section manifest writer

**Files:**
- Modify: `src/builder/sources/m365.py`
- Test: `tests/test_m365.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_m365.py`:

```python
import json as _json

def test_apply_source_section_writes_manifest(tmp_path):
    from src.builder.sources.m365 import apply_source_section
    repo = tmp_path / "repo"; repo.mkdir()
    (repo / "manifest.json").write_text(_json.dumps({"entries": [
        {"id": "1", "source_path": "C:/x/Hoare.pdf"},
        {"id": "2", "source_path": "C:/x/outro.pdf"},
    ]}), encoding="utf-8")
    n = apply_source_section(str(repo), {"hoare.pdf": "Verificação de Programas"})
    assert n == 1
    m = _json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in m["entries"]}
    assert by_id["1"]["source_section"] == "Verificação de Programas"
    assert "source_section" not in by_id["2"]
    assert (repo / "manifest.json.apibak").is_file()

def test_apply_source_section_noop_without_manifest(tmp_path):
    from src.builder.sources.m365 import apply_source_section
    assert apply_source_section(str(tmp_path / "nada"), {"a.pdf": "X"}) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_m365.py -q -k apply_source_section`
Expected: FAIL (`ImportError: cannot import name 'apply_source_section'`)

- [ ] **Step 3: Implement apply_source_section**

Append to `src/builder/sources/m365.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_m365.py -q -k apply_source_section`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/m365.py tests/test_m365.py
git commit -m "feat(m365): backfill source_section into manifest"
```

---

## Task 7: download_subject_m365 orchestration

**Files:**
- Modify: `src/builder/sources/m365.py`
- Test: `tests/test_m365.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_m365.py`:

```python
def test_download_subject_m365_merges_cards_and_validates(tmp_path):
    from src.builder.sources.m365 import download_subject_m365
    base = "https://brpucrs-my.sharepoint.com/personal/p/Documents/Documentos/metodosformais"

    class FakeClient:
        def list_shared(self, top=200):
            return [
                {"id": "1", "title": "Hoare.pdf", "type": "Pdf", "web_url": f"{base}/logica_programas/Hoare.pdf"},
                {"id": "2", "title": "hoare.zip", "type": "Archive", "web_url": f"{base}/dafny/hoare.zip"},
                {"id": "3", "title": "ruim.pdf", "type": "Pdf", "web_url": f"{base}/dafny/ruim.pdf"},
                {"id": "9", "title": "outro.pdf", "type": "Pdf", "web_url": "https://x/engsoft/outro.pdf"},
            ]
        def resolve(self, iid):
            return {"name": {"1": "Hoare.pdf", "2": "hoare.zip", "3": "ruim.pdf"}[iid],
                    "id": iid, "parentReference": {"driveId": "D"}}
        def download(self, item):
            return {"Hoare.pdf": b"%PDF-1.7 ok", "hoare.zip": b"PK\x03\x04zip",
                    "ruim.pdf": b'{"error":"x"}'}[item["name"]]

    sections = ["Verificação de Programas", "Provas por Indução"]
    rep = download_subject_m365(FakeClient(), "metodosformais", sections, tmp_path)

    assert rep["downloaded"] == 2
    assert "ruim.pdf" in rep["failed"]                          # magic byte errado
    # logica_programas casa com "Verificação de Programas" (token 'programas')
    assert (tmp_path / "Verificação de Programas" / "Hoare.pdf").exists()
    # dafny não casa -> card novo
    assert (tmp_path / "dafny" / "hoare.zip").exists()
    # item de outro curso ignorado pelo filtro
    assert not any("outro" in str(p) for p in tmp_path.rglob("*"))
    assert rep["name_to_section"]["hoare.pdf"] == "Verificação de Programas"

def test_download_subject_m365_no_collision_loss(tmp_path):
    from src.builder.sources.m365 import download_subject_m365
    base = "https://x/Documents/Documentos/metodosformais/dafny"

    class FakeClient:
        def list_shared(self, top=200):
            return [{"id": "1", "title": "main.pdf", "type": "Pdf", "web_url": f"{base}/main.pdf"},
                    {"id": "2", "title": "main.pdf", "type": "Pdf", "web_url": f"{base}/sub/main.pdf"}]
        def resolve(self, iid):
            return {"name": "main.pdf", "id": iid, "parentReference": {"driveId": "D"}}
        def download(self, item):
            return b"%PDF-1.7 x"
    rep = download_subject_m365(FakeClient(), "metodosformais", [], tmp_path)
    assert rep["downloaded"] == 2                              # nenhum perdido
    assert (tmp_path / "dafny" / "main.pdf").exists()
    assert (tmp_path / "dafny" / "main (2).pdf").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_m365.py -q -k download_subject`
Expected: FAIL (`ImportError: cannot import name 'download_subject_m365'`)

- [ ] **Step 3: Implement download_subject_m365**

Append to `src/builder/sources/m365.py`:

```python
def download_subject_m365(client, m365_filter, moodle_sections, dest,
                          skip_existing: bool = True) -> dict:
    """Baixa os arquivos M365 da matéria pros cards (merge com seções Moodle).

    Retorna {total, downloaded, failed, mapping:[(subfolder,card,matched)], name_to_section}.
    """
    dest = Path(dest)
    items = select_for_subject(client.list_shared(), m365_filter)
    downloaded, failed = 0, []
    name_to_section: dict = {}
    card_cache: dict = {}      # subfolder -> (card, matched)
    seen: set = set()
    for it in items:
        sub = subfolder_for(it["web_url"], m365_filter)
        if sub not in card_cache:
            card_cache[sub] = match_card(sub, moodle_sections)
        card = card_cache[sub][0]
        try:
            res = client.resolve(it["id"])
            name = res.get("name") or it.get("title") or "arquivo"
            data = client.download(res)
        except Exception:
            failed.append(it.get("title") or it.get("id"))
            continue
        if not looks_like_expected(name, data):
            failed.append(name)
            continue
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
        name_to_section[name.casefold()] = card
        if skip_existing and target.exists():
            continue
        target.write_bytes(data)
        downloaded += 1
    return {"total": len(items), "downloaded": downloaded, "failed": failed,
            "mapping": [(s, c, m) for s, (c, m) in card_cache.items()],
            "name_to_section": name_to_section}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_m365.py -q`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/m365.py tests/test_m365.py
git commit -m "feat(m365): download_subject_m365 orchestration (merge + validate + collision)"
```

---

## Task 8: Wire into the Moodle import dialog

**Files:**
- Modify: `src/ui/dialogs.py` — the `MoodleImport` dialog (`__init__` area near `src/ui/dialogs.py:1608`, and `_import` near `:1637`)

This task is UI (tkinter) — verified manually, no automated test. Code must be exact.

- [ ] **Step 1: Add the M365 controls next to the download checkbox**

In `src/ui/dialogs.py`, find (added by the Moodle bugfix):

```python
        self._download_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self, text="Baixar arquivos PDF (desmarque para só montar a estrutura dos cards)",
            variable=self._download_var,
        ).pack(anchor="w", padx=10, pady=(6, 0))
```

Add immediately after it:

```python
        self._m365_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self, text="Incluir material do OneDrive (M365) por matéria",
            variable=self._m365_var,
        ).pack(anchor="w", padx=10, pady=(2, 0))
        m365row = ttk.Frame(self); m365row.pack(fill="x", padx=10)
        ttk.Label(m365row, text="Filtro M365 (trecho do caminho, ex.: metodosformais):").pack(side="left")
        self._m365_filter_var = tk.StringVar(value="")
        ttk.Entry(m365row, textvariable=self._m365_filter_var).pack(side="left", fill="x", expand=True)
```

- [ ] **Step 2: Add a device-code prompt helper to the dialog class**

Add this method to the `MoodleImport` class (anywhere among its methods):

```python
    def _m365_prompt(self, info):
        # Chamado da thread worker; agenda o dialog na main thread.
        def show():
            messagebox.showinfo(
                "Login M365",
                f"Abra:\n{info['verification_uri']}\n\nDigite o código:\n{info['user_code']}\n\n"
                "Autentique com a conta PUCRS. O import continua após o login.")
        self._post(show)
```

- [ ] **Step 3: Call the M365 import inside the worker**

In `_import`, find the end of `worker()` where `base_msg`/`tail` are built and `showinfo` is posted. Replace the final `self._post(lambda: messagebox.showinfo("Moodle", base_msg + tail))` block with M365-aware logic:

```python
            m365_tail = ""
            if self._m365_var.get():
                flt = self._m365_filter_var.get().strip()
                if not flt:
                    m365_tail = "\n\nM365: filtro vazio — pulado."
                else:
                    try:
                        from src.builder.sources import m365
                        client = m365.get_client(prompt_callback=self._m365_prompt)
                        # seções Moodle do(s) curso(s) selecionado(s), p/ o merge de cards
                        sections = []
                        for course in selected:
                            cid = str(course.get("id") or "")
                            for sec in (self._client.get_course_contents(cid) or []):
                                if sec.get("name"):
                                    sections.append(sec["name"])
                        # baixa pro stash da 1ª matéria importada (base/slug)
                        from src.builder.sources.moodle import parse_moodle_course
                        info0 = parse_moodle_course(selected[0])
                        mdest = Path(self._base) / info0["slug"]
                        mrep = m365.download_subject_m365(client, flt, sections, mdest)
                        # source_section backfill no repo da matéria (decisão: preencher)
                        sp0 = store.get(info0["name"]) if hasattr(store, "get") else None
                        repo_root = getattr(sp0, "repo_root", "") if sp0 else ""
                        backf = m365.apply_source_section(repo_root, mrep["name_to_section"]) if repo_root else 0
                        mapped = "; ".join(f"{s}->{c}{'' if m else ' (novo)'}"
                                           for s, c, m in mrep["mapping"])
                        m365_tail = (f"\n\nM365 — baixados: {mrep['downloaded']}  "
                                     f"falhas: {len(mrep['failed'])}  source_section: {backf}\n"
                                     f"Cards: {mapped}")
                    except Exception as exc:
                        m365_tail = f"\n\nM365 indisponível: {str(exc)[:160]}"
            self._post(lambda: messagebox.showinfo("Moodle", base_msg + tail + m365_tail))
```

- [ ] **Step 4: Ensure `Path` is imported in dialogs.py**

Run: `python -c "import ast,re; src=open('src/ui/dialogs.py',encoding='utf-8').read(); print('Path import OK' if re.search(r'from pathlib import.*Path', src) else 'MISSING')"`
Expected: `Path import OK` (it is already imported; if MISSING, add `from pathlib import Path` near the top imports).

- [ ] **Step 5: Syntax check + smoke import**

Run: `python -c "import ast; ast.parse(open('src/ui/dialogs.py',encoding='utf-8').read()); print('dialogs OK')"`
Expected: `dialogs OK`

- [ ] **Step 6: Manual verification (document the result)**

Launch `python app.py`, open Moodle import, check "Incluir material do OneDrive (M365)", type `metodosformais`, import the Métodos Formais course. Expected: device-code dialog appears; after login, files land under `<base>/<slug>/<card>/` with logica_programas merged into "Verificação de Programas" and dafny as a new card; final dialog reports M365 downloaded count + card mapping.

- [ ] **Step 7: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(m365): wire OneDrive import into the Moodle import dialog"
```

---

## Task 9: Full suite + docs

- [ ] **Step 1: Run the whole suite**

Run: `python -m pytest -q`
Expected: all passed (previous baseline 1041 + new m365/core tests).

- [ ] **Step 2: Update the spec status**

In `docs/superpowers/specs/2026-06-08-m365-onedrive-import-design.md`, change `status:` to `implementado`.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-06-08-m365-onedrive-import-design.md
git commit -m "docs(m365): mark spec implemented"
```

---

## Self-Review (completed by plan author)

**Spec coverage:**
- m365.py module → Tasks 2-7. OAuth/token → Task 5. Insights discovery + pagination → Task 4. Download → Task 4. Magic-byte reuse → Task 7. Merge matcher → Task 3. source_section → Task 6. SubjectProfile.m365_filter → Task 1. UI integrated → Task 8. gitignore/security → Task 1/5. zip-as-is → no extraction step (by omission, correct).
- Card default `_geral` → Task 2 (`_ROOT_CARD`). Filter substring → Task 2. skip_existing → Task 7. Mapping report → Task 8.

**Placeholder scan:** none — every code step has complete code.

**Type consistency:** `M365Client(access_token)`, `.list_shared(top)`, `.resolve(id)`, `.download(item)`, `get_client(prompt_callback)`, `device_login(prompt_callback)`, `load_cached_token()`, `_token_path()`, `download_subject_m365(client, m365_filter, moodle_sections, dest, skip_existing)`, `apply_source_section(repo_root, name_to_section)`, `match_card(subfolder, sections, threshold)`, `subfolder_for(web_url, m365_filter, default)`, `select_for_subject(items, m365_filter)` — names consistent across tasks and the UI call site.

**Task 6/8 link:** `apply_source_section` (Task 6) IS called from the UI worker in Task 8 Step 3 (`store.get(info0["name"]).repo_root` → backfill `mrep["name_to_section"]`), satisfying the "fill source_section" decision. No-op when the subject has no repo yet.
