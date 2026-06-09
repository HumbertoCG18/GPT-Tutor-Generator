# Integração Moodle (onboarding + stash por API) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans. Steps usam checkbox (`- [ ]`).

**Goal:** Aluno conecta a conta Moodle (matrícula+senha → token), escolhe cursos, e o app cria as matérias + baixa os stashes organizados por seção (= card). Senha nunca persiste; só o token (gitignored).

**Architecture:** Backend puro/testável primeiro (`login`+token store, `parse_moodle_course`, `import_moodle_courses` com store/client injetados), depois CLI de debug, e por fim a casca UI (seção "Conta Moodle" no perfil do aluno + diálogo de seleção de cursos). API é fonte primária; o "Importar do stash" e o matching lexical seguem de fallback.

**Tech Stack:** Python 3.11/3.13, pytest, stdlib urllib, Tkinter (só na casca).

**Fonte:** `docs/superpowers/specs/2026-06-07-moodle-integracao-design.md`. Cliente base já existe (`src/builder/sources/moodle.py`: `MoodleClient`, `iter_section_files`, `download_course`, `sanitize_folder_name`).

---

## Contexto técnico verificado

- `src/builder/sources/moodle.py`: `MoodleClient(base_url, token)` com `_call`, `site_info`, `get_users_courses(userid)`, `get_course_contents(courseid)`, `_download_url`, `download_course(courseid, dest, skip_existing=True)`. Falta `login`.
- `src/models/core.py`: `SubjectProfile` (dataclass, `to_dict` omite defaults, `from_dict` filtra por nomes válidos; já tem `stash_folder`). `StudentProfile` (`full_name`, `nickname`, `personality`; `to_dict`=asdict, `from_dict` filtra). `SubjectStore` (`get`, `add(p)` salva, `names`, `save`). `StudentStore` (`.profile`, `.save()`). `slugify` em `src/utils/helpers.py`.
- `src/ui/dialogs.py:1399` `StudentProfileDialog(parent, student_store, theme_mgr)`: `_build_ui` monta `self._vars` (StringVars) + `_save` reconstrói `StudentProfile`. Aberto por `src/ui/app.py:1344`.
- `moddle/.env` é gitignored (`.gitignore`: `/moddle/*` + `!moddle/.env.example`). CLI `scripts/moodle_pull.py` já tem `_load_env` lendo `moddle/.env`.

---

## File Structure

- `src/builder/sources/moodle.py` — `+login` (staticmethod), `+default_token_path`, `+load_moodle_token`, `+save_moodle_token`, `+parse_moodle_course`, `+import_moodle_courses`.
- `src/models/core.py` — `SubjectProfile.moodle_course_id`, `StudentProfile.moodle_base_folder`.
- `scripts/moodle_login.py` (NOVO) — debug: cunha token de user/pass e grava no `.env`.
- `src/ui/dialogs.py` — seção "Conta Moodle" no `StudentProfileDialog` + `MoodleCourseSelectDialog` (NOVO, casca).
- Testes: `tests/test_moodle.py` (estende), `tests/test_core.py` (campos novos).

---

## Task 1: `MoodleClient.login` + token store

**Files:**
- Modify: `src/builder/sources/moodle.py`
- Test: `tests/test_moodle.py`

- [ ] **Step 1: Testes que falham**

Adicionar a `tests/test_moodle.py`:

```python
def test_save_load_token_roundtrip_preserves_url(tmp_path):
    from src.builder.sources.moodle import save_moodle_token, load_moodle_token
    env = tmp_path / ".env"
    env.write_text("MOODLE_URL=https://moodle.pucrs.br\nMOODLE_TOKEN=old\n", encoding="utf-8")
    save_moodle_token("newtok", dotenv_path=env)
    url, tok = load_moodle_token(dotenv_path=env)
    assert tok == "newtok"
    assert url == "https://moodle.pucrs.br"


def test_save_token_creates_file_when_missing(tmp_path):
    from src.builder.sources.moodle import save_moodle_token, load_moodle_token
    env = tmp_path / "sub" / ".env"
    save_moodle_token("t1", dotenv_path=env)
    url, tok = load_moodle_token(dotenv_path=env)
    assert tok == "t1"
    assert url == "https://moodle.pucrs.br"   # default


def test_login_posts_credentials_and_returns_token(monkeypatch):
    from src.builder.sources import moodle
    captured = {}
    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"token":"abc123"}'
    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return _Resp()
    monkeypatch.setattr(moodle.urllib.request, "urlopen", fake_urlopen)
    tok = moodle.MoodleClient.login("https://moodle.pucrs.br", "matricula", "senha")
    assert tok == "abc123"
    assert "login/token.php" in captured["url"]
    assert b"matricula" in captured["data"]


def test_login_raises_on_error(monkeypatch):
    from src.builder.sources import moodle
    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"error":"Invalid login"}'
    monkeypatch.setattr(moodle.urllib.request, "urlopen", lambda req, timeout=0: _Resp())
    import pytest
    with pytest.raises(RuntimeError):
        moodle.MoodleClient.login("https://moodle.pucrs.br", "x", "y")
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_moodle.py -k "token or login" -v`
Expected: FAIL — `cannot import name 'save_moodle_token'` / `AttributeError: login`.

- [ ] **Step 3: Implementar (em `src/builder/sources/moodle.py`)**

Adicionar o `login` como staticmethod dentro de `MoodleClient`:

```python
    @staticmethod
    def login(base_url: str, username: str, password: str) -> str:
        """Troca matrícula+senha pelo wstoken (mobile). Senha só transita aqui."""
        url = str(base_url).rstrip("/") + "/login/token.php?service=moodle_mobile_app"
        body = urllib.parse.urlencode({"username": username, "password": password}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8"))
        if not isinstance(payload, dict) or not payload.get("token"):
            msg = payload.get("error") if isinstance(payload, dict) else "resposta inválida"
            raise RuntimeError(f"Falha no login Moodle: {msg}")
        return str(payload["token"])
```

E, ao fim do módulo, os helpers de token store:

```python
_DEFAULT_MOODLE_URL = "https://moodle.pucrs.br"


def default_token_path() -> Path:
    return Path(__file__).resolve().parents[3] / "moddle" / ".env"


def load_moodle_token(dotenv_path=None):
    path = Path(dotenv_path) if dotenv_path else default_token_path()
    url, token = _DEFAULT_MOODLE_URL, ""
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k == "MOODLE_URL" and v:
                url = v
            elif k == "MOODLE_TOKEN":
                token = v
    return url, token


def save_moodle_token(token: str, url: str = "", dotenv_path=None) -> None:
    path = Path(dotenv_path) if dotenv_path else default_token_path()
    existing_url, _ = load_moodle_token(dotenv_path=path)
    final_url = url or existing_url or _DEFAULT_MOODLE_URL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"MOODLE_URL={final_url}\nMOODLE_TOKEN={token}\n", encoding="utf-8")
```

- [ ] **Step 4: Ver passar**

Run: `python -m pytest tests/test_moodle.py -v`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle.py
git commit -m "feat(moodle): login (mint token) + token store helpers"
```

---

## Task 2: Campos de modelo + `parse_moodle_course`

**Files:**
- Modify: `src/models/core.py` (`SubjectProfile`, `StudentProfile`)
- Modify: `src/builder/sources/moodle.py` (`parse_moodle_course`)
- Test: `tests/test_core.py`, `tests/test_moodle.py`

- [ ] **Step 1: Testes que falham**

Em `tests/test_core.py` (fim):

```python
def test_subject_profile_moodle_course_id_roundtrip():
    from src.models.core import SubjectProfile
    p = SubjectProfile(name="Métodos", moodle_course_id="92717")
    assert p.to_dict()["moodle_course_id"] == "92717"
    assert SubjectProfile.from_dict(p.to_dict()).moodle_course_id == "92717"


def test_student_profile_moodle_base_folder_roundtrip():
    from src.models.core import StudentProfile
    s = StudentProfile(full_name="X", moodle_base_folder="C:/Moodle")
    assert StudentProfile.from_dict(s.to_dict()).moodle_base_folder == "C:/Moodle"
```

Em `tests/test_moodle.py`:

```python
def test_parse_moodle_course_full_pattern():
    from src.builder.sources.moodle import parse_moodle_course
    c = {"id": 92717, "shortname": "4646M-04031261",
         "fullname": "4646M-04 - Métodos Formais para Computação - Turma 031 - 2026/1 - Prof. Julio Henrique A P Machado"}
    r = parse_moodle_course(c)
    assert r["moodle_course_id"] == "92717"
    assert r["name"] == "Métodos Formais para Computação"
    assert r["professor"] == "Julio Henrique A P Machado"
    assert r["semester"] == "2026/1"
    assert r["slug"]  # não vazio


def test_parse_moodle_course_degraded_no_prof():
    from src.builder.sources.moodle import parse_moodle_course
    r = parse_moodle_course({"id": 1, "fullname": "Curso de Ciência da Computação"})
    assert r["moodle_course_id"] == "1"
    assert r["name"] == "Curso de Ciência da Computação"
    assert r["professor"] == ""
    assert r["semester"] == ""
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_core.py -k moodle tests/test_moodle.py -k parse -v`
Expected: FAIL (campo/inexistente).

- [ ] **Step 3: Implementar campos**

Em `src/models/core.py`, no `SubjectProfile`, adicionar após `stash_folder`:

```python
    moodle_course_id: str = ""   # liga a matéria ao curso Moodle (re-sync, upsert)
```

No `StudentProfile`, adicionar após `personality`:

```python
    moodle_base_folder: str = ""  # pasta-base dos stashes baixados do Moodle
```

- [ ] **Step 4: Implementar `parse_moodle_course` (em `moodle.py`)**

Adicionar `from src.utils.helpers import slugify` no topo e:

```python
import re as _re

_COURSE_PROF_RE = _re.compile(r"\bProf\.?\s*(.+)$", _re.IGNORECASE)
_COURSE_SEM_RE = _re.compile(r"\b(20\d{2}/[12])\b")
_COURSE_TURMA_RE = _re.compile(r"\bTurma\b.*$", _re.IGNORECASE)


def parse_moodle_course(course: dict) -> dict:
    """Extrai campos de SubjectProfile do fullname Moodle.

    Padrão: "CODE - Nome - Turma NNN - YYYY/S - Prof. Fulano". Robusto a faltas.
    """
    full = str(course.get("fullname") or "").strip()
    cid = str(course.get("id") or "")
    professor = ""
    m = _COURSE_PROF_RE.search(full)
    if m:
        professor = m.group(1).strip()
    semester = ""
    m = _COURSE_SEM_RE.search(full)
    if m:
        semester = m.group(1)
    # Nome = segundo segmento entre " - " quando há padrão CODE - Nome - ...;
    # senão o fullname inteiro.
    name = full
    parts = [p.strip() for p in full.split(" - ")]
    if len(parts) >= 2:
        name = parts[1]
    return {
        "moodle_course_id": cid,
        "name": name,
        "professor": professor,
        "semester": semester,
        "slug": slugify(name) if name else (slugify(str(course.get("shortname") or "")) or cid),
        "shortname": str(course.get("shortname") or ""),
    }
```

- [ ] **Step 5: Ver passar**

Run: `python -m pytest tests/test_core.py -k moodle tests/test_moodle.py -v`
Expected: PASS.

- [ ] **Step 6: Suíte**

Run: `python -m pytest -q` → verde.

- [ ] **Step 7: Commit**

```bash
git add src/models/core.py src/builder/sources/moodle.py tests/test_core.py tests/test_moodle.py
git commit -m "feat(moodle): SubjectProfile.moodle_course_id, StudentProfile base folder, parse_moodle_course"
```

---

## Task 3: `import_moodle_courses` (upsert + download, injetável)

**Files:**
- Modify: `src/builder/sources/moodle.py`
- Test: `tests/test_moodle.py`

**Contrato:** dado `selected_courses` (lista de dicts Moodle), `base_folder`, um `store` (com `.get`, `.names`, `.add`) e um `client` (com `.download_course`), faz por curso: parse → upsert `SubjectProfile` (sem duplicar — casa por `moodle_course_id`, senão cria) com `stash_folder=<base>/<slug>` → `client.download_course(id, stash)`. Retorna sumário.

- [ ] **Step 1: Teste que falha**

Em `tests/test_moodle.py`:

```python
def test_import_moodle_courses_upserts_and_downloads(tmp_path):
    from src.builder.sources.moodle import import_moodle_courses
    from src.models.core import SubjectProfile

    class FakeStore:
        def __init__(self): self.data = {}
        def names(self): return list(self.data.keys())
        def get(self, n): return self.data.get(n)
        def add(self, p): self.data[p.name] = p

    class FakeClient:
        def __init__(self): self.calls = []
        def download_course(self, cid, dest, skip_existing=True):
            self.calls.append((str(cid), str(dest)))
            return {"total": 3, "downloaded": 3, "skipped": 0}

    store, client = FakeStore(), FakeClient()
    courses = [{"id": 92717, "fullname": "X - Métodos Formais - Turma 031 - 2026/1 - Prof. Julio"}]
    base = tmp_path / "Moodle"

    rep = import_moodle_courses(courses, base, store, client)
    assert len(store.names()) == 1
    sp = store.data["Métodos Formais"]
    assert sp.moodle_course_id == "92717"
    assert sp.stash_folder == str(base / sp.slug)
    assert client.calls == [("92717", str(base / sp.slug))]
    assert rep["created"] == 1 and rep["downloaded_files"] == 3

    # idempotência: re-importar o mesmo curso não duplica (atualiza)
    rep2 = import_moodle_courses(courses, base, store, client)
    assert len(store.names()) == 1
    assert rep2["updated"] == 1 and rep2["created"] == 0
```

- [ ] **Step 2: Ver falhar**

Run: `python -m pytest tests/test_moodle.py -k import_moodle -v`
Expected: FAIL — `cannot import name 'import_moodle_courses'`.

- [ ] **Step 3: Implementar (em `moodle.py`)**

```python
def import_moodle_courses(selected_courses, base_folder, store, client) -> dict:
    """Upsert de SubjectProfile + download do stash por curso selecionado.

    store: objeto com .names()/.get(name)/.add(profile).
    client: objeto com .download_course(courseid, dest).
    """
    from src.models.core import SubjectProfile
    base = Path(base_folder)
    created = updated = downloaded_files = 0
    for course in selected_courses or []:
        info = parse_moodle_course(course)
        cid = info["moodle_course_id"]
        # acha existente pelo moodle_course_id
        existing_name = None
        for n in store.names():
            sp = store.get(n)
            if sp and getattr(sp, "moodle_course_id", "") == cid and cid:
                existing_name = n
                break
        stash = str(base / info["slug"])
        if existing_name:
            sp = store.get(existing_name)
            sp.stash_folder = stash
            sp.moodle_course_id = cid
            if not sp.professor:
                sp.professor = info["professor"]
            store.add(sp)
            updated += 1
        else:
            sp = SubjectProfile(
                name=info["name"], slug=info["slug"], professor=info["professor"],
                semester=info["semester"], moodle_course_id=cid, stash_folder=stash,
            )
            store.add(sp)
            created += 1
        summary = client.download_course(cid, stash)
        downloaded_files += int(summary.get("downloaded", 0))
    return {"created": created, "updated": updated, "downloaded_files": downloaded_files}
```

- [ ] **Step 4: Ver passar**

Run: `python -m pytest tests/test_moodle.py -v` → todos verdes.

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle.py
git commit -m "feat(moodle): import_moodle_courses upsert + download orchestration"
```

---

## Task 4: Debug CLI `moodle_login.py`

**Files:**
- Create: `scripts/moodle_login.py`

**Nota:** ferramenta de debug isolada (cunha token de user/pass e grava no `.env`). Sem teste unitário (interativo); valida por execução manual local.

- [ ] **Step 1: Implementar `scripts/moodle_login.py`**

```python
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
```

- [ ] **Step 2: Smoke (sintaxe, sem login real)**

Run: `python -c "import scripts.moodle_login"`
Expected: sem erro.

- [ ] **Step 3: Commit**

```bash
git add scripts/moodle_login.py
git commit -m "feat(moodle): debug CLI to mint+store token from credentials"
```

---

## Task 5: UI — seção "Conta Moodle" + diálogo de seleção

**Files:**
- Modify: `src/ui/dialogs.py` (`StudentProfileDialog`: seção Moodle + `_save`; novo `MoodleCourseSelectDialog`)

**Nota:** casca Tk (não unit-testada; lógica nos puros das Tasks 1-3). O reviewer confere que a casca delega aos puros e roda o download off-thread (mesmo padrão do unprocess que evita travar a UI). Senha em `show="*"`, nunca persistida.

- [ ] **Step 1: Seção "Conta Moodle" no `StudentProfileDialog._build_ui`**

Antes do botão "Salvar Perfil" (linha ~1472), adicionar uma `LabelFrame`:

```python
        moodle_frame = ttk.LabelFrame(self, text="  🎓  Conta Moodle (PUCRS)", padding=14)
        moodle_frame.pack(fill="x", padx=14, pady=(0, 8))

        from src.builder.sources.moodle import load_moodle_token
        _url, _tok = load_moodle_token()
        status = "conectado (token salvo)" if _tok else "não conectado"
        ttk.Label(moodle_frame, text=f"Status: {status}", style="Muted.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(moodle_frame, text="Matrícula").grid(row=1, column=0, sticky="w", pady=4)
        self._moodle_user = tk.StringVar()
        ttk.Entry(moodle_frame, textvariable=self._moodle_user, width=30).grid(row=1, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(moodle_frame, text="Senha").grid(row=2, column=0, sticky="w", pady=4)
        self._moodle_pass = tk.StringVar()
        ttk.Entry(moodle_frame, textvariable=self._moodle_pass, width=30, show="*").grid(row=2, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(moodle_frame, text="Pasta-base dos stashes").grid(row=3, column=0, sticky="w", pady=4)
        self._moodle_base = tk.StringVar(value=getattr(self._store.profile, "moodle_base_folder", ""))
        base_row = ttk.Frame(moodle_frame)
        base_row.grid(row=3, column=1, sticky="ew", padx=(8, 0))
        ttk.Entry(base_row, textvariable=self._moodle_base).pack(side="left", fill="x", expand=True)
        ttk.Button(base_row, text="📁", width=3, command=self._pick_moodle_base).pack(side="left", padx=(4, 0))

        ttk.Button(moodle_frame, text="🔗  Conectar e escolher cursos", command=self._moodle_connect).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        moodle_frame.columnconfigure(1, weight=1)
        ttk.Label(moodle_frame, text="A senha não é salva — só o token (revogável).",
                  style="Muted.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 0))
```

- [ ] **Step 2: Handlers no `StudentProfileDialog`**

```python
    def _pick_moodle_base(self):
        d = filedialog.askdirectory(title="Pasta-base dos stashes do Moodle")
        if d:
            self._moodle_base.set(d)

    def _moodle_connect(self):
        from src.builder.sources.moodle import MoodleClient, save_moodle_token, load_moodle_token
        user = self._moodle_user.get().strip()
        password = self._moodle_pass.get()
        base = self._moodle_base.get().strip()
        if not base:
            messagebox.showwarning("Moodle", "Escolha a pasta-base dos stashes primeiro.")
            return
        url, token = load_moodle_token()
        try:
            if user and password:
                token = MoodleClient.login(url, user, password)
                save_moodle_token(token, url=url)
            if not token:
                messagebox.showwarning("Moodle", "Informe matrícula e senha para conectar.")
                return
            self._moodle_pass.set("")  # limpa a senha da memória da UI
            client = MoodleClient(url, token)
            info = client.site_info()
            courses = client.get_users_courses(info.get("userid"))
        except Exception as exc:
            messagebox.showerror("Moodle", f"Falha ao conectar: {exc}")
            return
        # salva a pasta-base no perfil
        self._store.profile.moodle_base_folder = base
        self._store.save()
        MoodleCourseSelectDialog(self, courses, base, client, self._p)
```

- [ ] **Step 3: `_save` persiste a pasta-base**

No `_save`, antes de reconstruir `StudentProfile`, preservar o campo novo:

```python
    def _save(self):
        sp = StudentProfile(
            full_name=self._vars["full_name"].get().strip(),
            nickname=self._vars["nickname"].get().strip(),
            personality=self._personality_text.get("1.0", "end-1c").strip(),
            moodle_base_folder=getattr(self, "_moodle_base", tk.StringVar()).get().strip(),
        )
        self._store.profile = sp
        self._store.save()
        messagebox.showinfo("Perfil", "Perfil salvo com sucesso!")
        self.destroy()
```

- [ ] **Step 4: `MoodleCourseSelectDialog` (novo, em `dialogs.py`)**

```python
class MoodleCourseSelectDialog(tk.Toplevel):
    """Lista cursos Moodle com checkbox; importa os marcados (upsert + download)."""

    def __init__(self, parent, courses, base_folder, client, palette):
        super().__init__(parent)
        self.title("🎓  Escolher cursos do Moodle")
        self.geometry("680x520")
        self.transient(parent)
        self.grab_set()
        self._courses = list(courses or [])
        self._base = base_folder
        self._client = client
        self._vars = []
        self._build_ui()

    def _build_ui(self):
        from src.builder.sources.moodle import parse_moodle_course
        ttk.Label(self, text="Marque os cursos que viram matéria:", padding=10).pack(anchor="w")
        canvas = tk.Canvas(self, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scroll.pack(side="right", fill="y")
        for course in self._courses:
            info = parse_moodle_course(course)
            var = tk.BooleanVar(value=False)
            self._vars.append((var, course))
            label = f"{info['name']}   ·   {info['professor'] or '—'}   ·   {info['semester'] or '—'}"
            ttk.Checkbutton(inner, text=label, variable=var).pack(anchor="w", pady=2)
        ttk.Button(self, text="📥  Importar marcados", command=self._import).pack(fill="x", padx=10, pady=10)

    def _import(self):
        import threading
        from src.builder.sources.moodle import import_moodle_courses
        from src.models.core import SubjectStore
        selected = [c for v, c in self._vars if v.get()]
        if not selected:
            messagebox.showinfo("Moodle", "Marque ao menos um curso.")
            return

        def worker():
            store = SubjectStore()
            try:
                rep = import_moodle_courses(selected, self._base, store, self._client)
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Moodle", f"Falha no import: {exc}"))
                return
            self.after(0, lambda: messagebox.showinfo(
                "Moodle",
                f"Criadas: {rep['created']}  Atualizadas: {rep['updated']}  "
                f"Arquivos baixados: {rep['downloaded_files']}"))
            self.after(0, self.destroy)

        threading.Thread(target=worker, daemon=True).start()
```

- [ ] **Step 5: Smoke + suíte**

Run: `python -c "import src.ui.dialogs"` (sem erro)
Run: `python -m pytest -q` (verde)

- [ ] **Step 6: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(ui): Moodle account section + course selection import dialog"
```

---

## Validação manual (após as 5 tasks — não é task)

1. Perfil do Aluno → seção Conta Moodle → escolhe pasta-base → matrícula+senha → Conectar.
2. Diálogo lista os cursos → marca Métodos → Importar.
3. Confere: matéria criada no Gerenciador de Matérias com `stash_folder` setado; stash em `<base>/<slug>/<card>/arquivos`.
4. Seleciona a matéria → "Importar do stash" → processa → retag → eval.

## Notas de execução

- Hook `code-review-graph.exe` imprime `UnicodeEncodeError` cosmético; commit passa.
- Trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- NUNCA logar/printar o token. Senha só em memória, limpa após uso.
- NÃO commitar `moddle/.env`.
