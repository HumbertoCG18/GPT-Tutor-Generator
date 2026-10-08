# Referências como Contexto Base do Tutor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao tutor contexto base real de cada referência (repo GitHub / doc / URL) — buscar conteúdo leve (README via API, texto de página via extrator existente), resumir com Gemini, mapear a unidade/tópico, e surfacear na `BIBLIOGRAPHY.md` — em vez do título+URL morto de hoje.

**Architecture:** Quatro funções puras novas em `src/builder/core/reference_content.py` (aquisição) e `reference_topic.py` (mapeamento), reusando o extrator HTML `text/url_markdown.py` e os helpers de normalização de `core/code_summarization.py`. O resumo reusa a camada Gemini (`client.summarize_bundle`) com um schema `ReferenceSummary`. Uma função batch espelha `summarize_all_code_entries` (cache por content-hash em `references_curation.json`). O surfacing estende `bibliography_md`. Lazy: sem `gemini_api_key`, pula o resumo mas ainda mapeia e surfacea.

**Tech Stack:** Python 3, pytest, `requests` (já dep), `beautifulsoup4` (já dep), pydantic (já dep via `code_summarization`).

---

## Spec

`docs/superpowers/specs/2026-06-04-referencias-contexto-tutor-design.md`. Leia para contexto; este plano implementa-o tarefa-a-tarefa.

## Fatos verificados (confie — não re-investigue)

- `normalize_match_text` vive em `src/builder/text/normalize.py`. Em `code_summarization.py` há `_normalize(text)`, `_stem(token)`, `_expand_concept_tokens(concept_norm) -> set[str]` — reuse-os no matcher de unidade.
- Matcher a espelhar: `code_summarization.assign_code_to_block(concepts, timeline_blocks, *, primary_threshold=0.4, secondary_threshold=0.25, margin_threshold=0.15) -> dict` (linhas 164-242). Faz overlap de `_expand_concept_tokens(concept)` contra um "bag" de tokens do alvo; `score = overlap / len(concept_token_sets)`; aplica thresholds + margem. Retorna `{"primary","secondaries","confidence","method","top_candidate","top_score"}`.
- Resumo Gemini: `client.summarize_bundle(bundle_text=..., schema=PydanticModel, system_instruction=...) -> model`. Cliente lazy criado a partir de `gemini_api_key` (cf. `runtime/gemini_client.py`); sem chave o caller passa `client=None`. Padrão: `summarize_code_entry(builder, entry_data, client)` retorna `None` se `client` é None OU bundle vazio.
- Batch + cache a espelhar: `summarize_all_code_entries(builder, client, progress_cb)` — lê manifest, `load_code_curation(builder.root_dir)`, pula entry se `content_hash` bate e `summary` existe e `matcher_version == MATCHER_VERSION`. `write_code_curation(repo_dir, data)` grava `course/code_curation.json`.
- Extrator HTML: `text/url_markdown.html_to_structured_markdown(html, url, title, *, collapse_ws, truncate_markdown_blocks) -> str` (já filtra nav/header/footer/aside/script). `truncate_markdown_blocks(blocks, max_chars=15000)`. `collapse_ws` vem de `utils/helpers` (há um colapsador de espaços no projeto; use `lambda s: " ".join(s.split())` se preferir local).
- Índice de unidade: `file_map.build_file_map_unit_index_from_course(course_meta, subject_profile) -> list[dict]`. Cada unit dict tem: `slug`, `normalized_title`, `topic_phrases: list[str]`, `topic_tokens: list[str]`, `distinctive_tokens: list[str]`, `token_weights: dict`.
- `requests` disponível (`helpers.py:466` usa `requests.get`). `fetch_url_title(url, timeout)` e `fetch_schedule_html(url)` existem em `helpers.py` como referência de fetch.
- Referência = `FileEntry` com `category ∈ {referencias, bibliografia}`, `source_path` = URL externa. GUARDRAIL: o repo-destino do tutor é `SubjectProfile.github_url`/`repo_root` — NUNCA passe isso ao fetch; o pipeline é gated por `category`.
- `FileEntry.to_dict()` usa `dataclasses.asdict` (obs 391) — campos novos auto-serializam.

## File Structure

- Create `src/builder/core/reference_content.py` — `parse_github_repo`, `fetch_github_readme`, `fetch_reference_text`.
- Create `src/builder/core/reference_topic.py` — `assign_concepts_to_unit`.
- Create `src/builder/core/reference_summary.py` — `ReferenceSummary` (pydantic), `summarize_reference`, `summarize_all_reference_entries` (batch+cache), `load/write_reference_curation`.
- Modify `src/models/core.py` — campos `ref_summary`, `ref_concepts`, `computed_ref_unit`, `computed_ref_topics` em `FileEntry`.
- Modify `src/builder/artifacts/repo.py` — `bibliography_md` renderiza resumo + relevância + preenche mapa de tópico.
- Modify build orchestration — chama `summarize_all_reference_entries` (mesmo ponto que chama `summarize_all_code_entries`).
- Create `tests/test_reference_content.py`, `tests/test_reference_topic.py`, `tests/test_reference_summary.py`, `tests/test_reference_bibliography.py`.

---

## Task 1: `parse_github_repo`

**Files:**
- Create: `src/builder/core/reference_content.py`
- Test: `tests/test_reference_content.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_reference_content.py`:

```python
from src.builder.core.reference_content import parse_github_repo


def test_parses_plain_repo_url():
    assert parse_github_repo("https://github.com/Netflix/eureka") == ("Netflix", "eureka")


def test_parses_with_git_suffix():
    assert parse_github_repo("https://github.com/OpenFeign/feign.git") == ("OpenFeign", "feign")


def test_parses_with_extra_path():
    assert parse_github_repo("https://github.com/spring-projects/spring-security-samples/tree/main/servlet") == ("spring-projects", "spring-security-samples")


def test_parses_without_scheme():
    assert parse_github_repo("github.com/aws/aws-encryption-sdk") == ("aws", "aws-encryption-sdk")


def test_non_github_returns_none():
    assert parse_github_repo("https://docs.python.org/3/library/asyncio.html") is None


def test_garbage_returns_none():
    assert parse_github_repo("") is None
    assert parse_github_repo("https://github.com/onlyowner") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_reference_content.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.builder.core.reference_content'`

- [ ] **Step 3: Implement `parse_github_repo`**

Create `src/builder/core/reference_content.py`:

```python
"""Aquisição leve de conteúdo de referência (sem clone).

GitHub -> README via API (resolve branch default sozinho). Doc/URL -> texto de
página via o extrator HTML existente. Funções com I/O de rede isolado; erros de
rede degradam para "" (nunca levantam para o caller do build).
"""
from __future__ import annotations

import re
from typing import Optional

_GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+)", re.I)


def parse_github_repo(url: str) -> Optional[tuple[str, str]]:
    """(owner, repo) de uma URL GitHub, ou None. Remove sufixo .git e path extra."""
    if not url:
        return None
    m = _GITHUB_RE.search(url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo:
        return None
    return owner, repo
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_content.py -v`
Expected: all 6 PASS. Note `test_garbage_returns_none`: `github.com/onlyowner` has no second path segment so the regex `/([^/\s]+)/([^/\s#?]+)` requires two segments → no match → None.

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/reference_content.py tests/test_reference_content.py
git commit -m "feat(reference): parse_github_repo extracts owner/repo from URL"
```

---

## Task 2: `fetch_github_readme`

**Files:**
- Modify: `src/builder/core/reference_content.py`
- Test: `tests/test_reference_content.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_reference_content.py`:

```python
from unittest.mock import patch, MagicMock
from src.builder.core.reference_content import fetch_github_readme


def _resp(status, text=""):
    r = MagicMock()
    r.status_code = status
    r.text = text
    return r


def test_fetch_readme_returns_body_on_200():
    with patch("src.builder.core.reference_content.requests.get", return_value=_resp(200, "# Eureka\nservice registry")) as g:
        out = fetch_github_readme("Netflix", "eureka")
    assert "service registry" in out
    # usa o endpoint readme da API
    assert "api.github.com/repos/Netflix/eureka/readme" in g.call_args[0][0]


def test_fetch_readme_empty_on_404():
    with patch("src.builder.core.reference_content.requests.get", return_value=_resp(404)):
        assert fetch_github_readme("x", "y") == ""


def test_fetch_readme_empty_on_exception():
    with patch("src.builder.core.reference_content.requests.get", side_effect=Exception("network")):
        assert fetch_github_readme("x", "y") == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_reference_content.py -k readme -v`
Expected: FAIL with `ImportError: cannot import name 'fetch_github_readme'`

- [ ] **Step 3: Implement `fetch_github_readme`**

Add to the top imports of `src/builder/core/reference_content.py`:

```python
import requests
```

Append:

```python
def fetch_github_readme(owner: str, repo: str, *, timeout: float = 10.0) -> str:
    """README do branch DEFAULT via API do GitHub (Accept raw). "" em erro/404.

    A API resolve o branch default sozinha — contorna o bug de branch hardcoded
    do clone. Anônima (sem token): 60 req/h por IP; o cache do batch protege.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    try:
        resp = requests.get(
            url,
            headers={"Accept": "application/vnd.github.raw", "User-Agent": "gpt-tutor-generator"},
            timeout=timeout,
        )
    except Exception:
        return ""
    if resp.status_code != 200:
        return ""
    return resp.text or ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_content.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/reference_content.py tests/test_reference_content.py
git commit -m "feat(reference): fetch_github_readme via GitHub API (default branch)"
```

---

## Task 3: `fetch_reference_text` (dispatch GitHub vs doc/URL)

**Files:**
- Modify: `src/builder/core/reference_content.py`
- Test: `tests/test_reference_content.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_reference_content.py`:

```python
from src.builder.core.reference_content import fetch_reference_text


def test_github_entry_uses_readme():
    entry = {"file_type": "github-repo", "source_path": "https://github.com/Netflix/eureka"}
    with patch("src.builder.core.reference_content.fetch_github_readme", return_value="readme body"):
        assert fetch_reference_text(entry) == "readme body"


def test_doc_url_uses_html_extractor():
    entry = {"file_type": "link", "source_path": "https://docs.example.com/guide"}
    html = "<html><body><nav>menu</nav><main><h1>Guia</h1><p>conteudo util</p></main><footer>rodape</footer></body></html>"
    with patch("src.builder.core.reference_content.requests.get", return_value=_resp(200, html)):
        out = fetch_reference_text(entry)
    assert "conteudo util" in out
    assert "menu" not in out and "rodape" not in out


def test_empty_source_returns_empty():
    assert fetch_reference_text({"file_type": "link", "source_path": ""}) == ""


def test_truncates_to_max_chars():
    entry = {"file_type": "github-repo", "source_path": "https://github.com/a/b"}
    with patch("src.builder.core.reference_content.fetch_github_readme", return_value="x" * 50000):
        out = fetch_reference_text(entry, max_chars=1000)
    assert len(out) <= 1000
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_reference_content.py -k reference_text -v`
Expected: FAIL with `ImportError: cannot import name 'fetch_reference_text'`

- [ ] **Step 3: Implement `fetch_reference_text`**

Append to `src/builder/core/reference_content.py`:

```python
def _collapse_ws(s: str) -> str:
    return " ".join((s or "").split())


def _fetch_doc_text(url: str, *, timeout: float = 10.0) -> str:
    """Texto do corpo de uma página (doc/artigo) via o extrator HTML existente."""
    try:
        resp = requests.get(url, headers={"User-Agent": "gpt-tutor-generator"}, timeout=timeout)
    except Exception:
        return ""
    if resp.status_code != 200 or not resp.text:
        return ""
    from src.builder.text.url_markdown import html_to_structured_markdown, truncate_markdown_blocks
    try:
        return html_to_structured_markdown(
            resp.text, url, "",
            collapse_ws=_collapse_ws,
            truncate_markdown_blocks=truncate_markdown_blocks,
        )
    except Exception:
        return ""


def fetch_reference_text(entry: dict, *, max_chars: int = 16000) -> str:
    """Conteúdo leve de uma referência. GitHub -> README; doc/URL -> texto de
    página. "" se sem fonte ou em qualquer falha. Trunca em max_chars."""
    source = str(entry.get("source_path") or "").strip()
    if not source:
        return ""
    gh = parse_github_repo(source) if (
        str(entry.get("file_type") or "") == "github-repo" or "github.com" in source
    ) else None
    if gh:
        text = fetch_github_readme(*gh)
    else:
        text = _fetch_doc_text(source)
    text = text or ""
    return text[:max_chars]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_content.py -v`
Expected: all PASS. If `html_to_structured_markdown` signature differs (e.g. needs a different `collapse_ws`), adapt the call — the test asserts only that body text survives and nav/footer are stripped.

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/reference_content.py tests/test_reference_content.py
git commit -m "feat(reference): fetch_reference_text dispatches github/doc, truncates"
```

---

## Task 4: `assign_concepts_to_unit`

**Files:**
- Create: `src/builder/core/reference_topic.py`
- Test: `tests/test_reference_topic.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_reference_topic.py`:

```python
from src.builder.core.reference_topic import assign_concepts_to_unit


def _units():
    return [
        {"slug": "unidade-01-seguranca", "normalized_title": "seguranca de aplicacoes",
         "topic_phrases": ["autenticacao", "autorizacao", "spring security"],
         "topic_tokens": ["autenticacao", "autorizacao", "seguranca"], "distinctive_tokens": ["oauth"]},
        {"slug": "unidade-02-microservicos", "normalized_title": "microservicos",
         "topic_phrases": ["service discovery", "api gateway"],
         "topic_tokens": ["microservico", "discovery", "gateway"], "distinctive_tokens": ["eureka"]},
    ]


def test_maps_concepts_to_matching_unit():
    out = assign_concepts_to_unit(["service discovery", "eureka registry"], "", _units())
    assert out["unit_slug"] == "unidade-02-microservicos"
    assert out["confidence"] > 0.0


def test_no_match_returns_empty_slug():
    out = assign_concepts_to_unit(["fotossintese", "mitocondria"], "", _units())
    assert out["unit_slug"] == ""


def test_falls_back_to_text_when_no_concepts():
    out = assign_concepts_to_unit([], "tutorial de spring security e autenticacao", _units())
    assert out["unit_slug"] == "unidade-01-seguranca"


def test_empty_everything_returns_empty():
    out = assign_concepts_to_unit([], "", _units())
    assert out["unit_slug"] == ""
    assert out["topics"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_reference_topic.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `assign_concepts_to_unit`**

Create `src/builder/core/reference_topic.py`:

```python
"""Mapa de relevância de uma referência -> unidade/tópico (NÃO bloco).

Espelha code_summarization.assign_code_to_block, mas o alvo é a unidade: faz
overlap dos tokens de concept (ou, sem concepts, do texto) contra o "bag" de
tokens de cada unidade do índice. Determinístico, sem rede, sem Gemini.
"""
from __future__ import annotations

from typing import List

from src.builder.core.code_summarization import _normalize, _stem, _expand_concept_tokens


def _unit_bag(unit: dict) -> set[str]:
    bag: set[str] = set()
    fields: List[str] = []
    fields.append(unit.get("normalized_title", "") or "")
    fields.extend(unit.get("topic_phrases", []) or [])
    fields.extend(unit.get("topic_tokens", []) or [])
    fields.extend(unit.get("distinctive_tokens", []) or [])
    for f in fields:
        for tok in _normalize(f).split():
            if len(tok) >= 4:
                bag.add(tok)
                bag.add(_stem(tok))
    bag.discard("")
    return bag


def assign_concepts_to_unit(
    concepts: List[str],
    fallback_text: str,
    units: List[dict],
    *,
    primary_threshold: float = 0.34,
    margin_threshold: float = 0.10,
) -> dict:
    """Retorna {"unit_slug": str, "topics": list[str], "confidence": float}.

    Usa `concepts` (do Gemini); sem concepts cai para tokens de `fallback_text`.
    Vazio quando nada casa acima do threshold.
    """
    terms = [c for c in (concepts or []) if c]
    if not terms and fallback_text:
        terms = [t for t in fallback_text.split() if len(t) >= 4]
    terms_norm = [_normalize(t) for t in terms]
    terms_norm = [t for t in terms_norm if t]
    if not terms_norm or not units:
        return {"unit_slug": "", "topics": [], "confidence": 0.0}

    term_token_sets = [_expand_concept_tokens(t) for t in terms_norm]

    scores: list[tuple[str, float, list]] = []
    for unit in units:
        bag = _unit_bag(unit)
        if not bag:
            scores.append((unit.get("slug", ""), 0.0, unit.get("topic_phrases", []) or []))
            continue
        overlap = sum(1 for toks in term_token_sets if toks & bag)
        scores.append((unit.get("slug", ""), overlap / len(term_token_sets), unit.get("topic_phrases", []) or []))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_slug, top_score, top_topics = scores[0]
    second = scores[1][1] if len(scores) > 1 else 0.0
    if top_score >= primary_threshold and (top_score - second) >= margin_threshold:
        return {"unit_slug": top_slug, "topics": list(top_topics)[:3], "confidence": round(top_score, 3)}
    return {"unit_slug": "", "topics": [], "confidence": round(top_score, 3)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_topic.py -v`
Expected: all PASS. If thresholds make a valid case miss, the test fixtures use strong overlaps (eureka/discovery, spring security/autenticacao) that clear 0.34 — do NOT loosen thresholds to pass; verify the bag-building first.

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/reference_topic.py tests/test_reference_topic.py
git commit -m "feat(reference): assign_concepts_to_unit maps reference to unit/topic"
```

---

## Task 5: `ReferenceSummary` + `summarize_reference` (Gemini, lazy)

**Files:**
- Create: `src/builder/core/reference_summary.py`
- Test: `tests/test_reference_summary.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_reference_summary.py`:

```python
from unittest.mock import MagicMock
from src.builder.core.reference_summary import summarize_reference, ReferenceSummary


def test_returns_none_without_client():
    assert summarize_reference("algum texto", None) is None


def test_returns_none_on_empty_text():
    assert summarize_reference("   ", MagicMock()) is None


def test_returns_dict_with_summary_and_concepts():
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(
        inferred_title="Spring Security", summary="Framework de autenticacao.",
        concepts=["autenticacao", "oauth"],
    )
    out = summarize_reference("readme do spring security", client)
    assert out["summary"] == "Framework de autenticacao."
    assert out["concepts"] == ["autenticacao", "oauth"]


def test_returns_none_on_client_exception():
    client = MagicMock()
    client.summarize_bundle.side_effect = Exception("api down")
    assert summarize_reference("texto", client) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_reference_summary.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement model + `summarize_reference`**

Create `src/builder/core/reference_summary.py`:

```python
"""Resumo de referência via Gemini (lazy) + batch com cache por content-hash.

Espelha core/code_summarization, mas o alvo é UMA referência bibliográfica
(repo/doc), não um bundle de código, e o resultado dá contexto base ao tutor.
"""
from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReferenceSummary(BaseModel):
    inferred_title: str = Field(..., description="Título descritivo da referência")
    summary: str = Field(..., description="3-5 linhas: o que a referência cobre e como ajuda o aluno")
    concepts: list[str] = Field(..., description="3-8 termos técnicos do domínio cobertos")


REFERENCE_SYSTEM_INSTRUCTION = """Você resume referências bibliográficas (repos
GitHub, documentações, artigos) de uma disciplina universitária para um tutor LLM.

A saída dá ao tutor CONTEXTO BASE: o que a referência ensina/demonstra e quais
conceitos ela cobre, para o tutor aprofundar explicações.

Regras:
- inferred_title: descritivo, não repita a URL.
- summary: 3-5 frases. O que a referência cobre, que problema resolve, como
  serve de apoio ao estudo. Não invente o que não está no texto.
- concepts: 3-8 termos técnicos do domínio.
- Português brasileiro. Saída APENAS JSON válido conforme schema."""


def summarize_reference(text: str, client) -> Optional[dict]:
    """{summary, concepts, inferred_title} via Gemini, ou None (sem client, texto
    vazio, ou falha). Lazy: nunca quebra o build."""
    if client is None or not (text or "").strip():
        return None
    try:
        result: ReferenceSummary = client.summarize_bundle(
            bundle_text=text,
            schema=ReferenceSummary,
            system_instruction=REFERENCE_SYSTEM_INSTRUCTION,
        )
        return result.model_dump()
    except Exception as exc:
        logger.error("[ReferenceSummary] falha: %s", exc)
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_summary.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/reference_summary.py tests/test_reference_summary.py
git commit -m "feat(reference): ReferenceSummary model + summarize_reference (lazy Gemini)"
```

---

## Task 6: FileEntry storage fields + batch with cache

**Files:**
- Modify: `src/models/core.py` (FileEntry dataclass)
- Modify: `src/builder/core/reference_summary.py`
- Test: `tests/test_reference_summary.py`

- [ ] **Step 1: Add storage fields to FileEntry**

In `src/models/core.py`, find the `FileEntry` dataclass and add these fields alongside the other optional defaulted fields (match the existing field style — default values so old manifests still load):

```python
    ref_summary: str = ""
    ref_concepts: List[str] = field(default_factory=list)
    computed_ref_unit: str = ""
    computed_ref_topics: List[str] = field(default_factory=list)
```

Verify `field` and `List` are already imported in `core.py` (they are — other fields use them).

- [ ] **Step 2: Write the failing test for the batch processor**

Append to `tests/test_reference_summary.py`:

```python
from src.builder.core.reference_summary import process_reference_entry


def test_process_reference_entry_fills_fields():
    entry = {"id": "r1", "category": "referencias", "file_type": "github-repo",
             "source_path": "https://github.com/a/b", "auto_tags": []}
    units = [{"slug": "unidade-01", "normalized_title": "seguranca",
              "topic_phrases": ["autenticacao"], "topic_tokens": ["autenticacao"], "distinctive_tokens": ["oauth"]}]
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(
        inferred_title="t", summary="resumo base", concepts=["autenticacao", "oauth"])
    import src.builder.core.reference_summary as rs
    rs_fetch = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "readme de autenticacao oauth"
        out = process_reference_entry(entry, units, client)
    finally:
        rs.fetch_reference_text = rs_fetch
    assert out["ref_summary"] == "resumo base"
    assert out["computed_ref_unit"] == "unidade-01"
    assert "oauth" in out["ref_concepts"]


def test_process_degrades_without_client():
    entry = {"id": "r1", "category": "referencias", "file_type": "github-repo",
             "source_path": "https://github.com/a/b"}
    units = [{"slug": "unidade-01", "normalized_title": "seguranca",
              "topic_phrases": ["autenticacao"], "topic_tokens": ["autenticacao"], "distinctive_tokens": ["oauth"]}]
    import src.builder.core.reference_summary as rs
    rs_fetch = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "texto sobre autenticacao oauth"
        out = process_reference_entry(entry, units, None)  # sem Gemini
    finally:
        rs.fetch_reference_text = rs_fetch
    assert out["ref_summary"] == ""                 # sem resumo
    assert out["computed_ref_unit"] == "unidade-01" # mas mapeia por texto
```

- [ ] **Step 3: Implement `process_reference_entry`**

Add imports at the top of `src/builder/core/reference_summary.py`:

```python
from src.builder.core.reference_content import fetch_reference_text
from src.builder.core.reference_topic import assign_concepts_to_unit
```

Append:

```python
def process_reference_entry(entry: dict, units: list, client) -> dict:
    """Enriquece UMA entry de referência: busca texto, resume (lazy), mapeia
    unidade/tópico. Retorna um dict de campos a mesclar na entry.

    Sem client -> sem resumo, mas ainda mapeia por texto fetchado (determinístico).
    """
    text = fetch_reference_text(entry)
    summary_dict = summarize_reference(text, client)  # None sem client/texto
    concepts = (summary_dict or {}).get("concepts", []) or []
    fallback = " ".join([str(entry.get("title", "") or ""), text])
    topic = assign_concepts_to_unit(concepts, fallback, units)
    return {
        "ref_summary": (summary_dict or {}).get("summary", "") or "",
        "ref_concepts": concepts,
        "computed_ref_unit": topic["unit_slug"],
        "computed_ref_topics": topic["topics"],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_summary.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py src/builder/core/reference_summary.py tests/test_reference_summary.py
git commit -m "feat(reference): FileEntry ref fields + process_reference_entry (lazy)"
```

---

## Task 7: Surface in `bibliography_md`

**Files:**
- Modify: `src/builder/artifacts/repo.py` (`bibliography_md`, ~654-734)
- Test: `tests/test_reference_bibliography.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_reference_bibliography.py`:

```python
from types import SimpleNamespace
from src.builder.artifacts.repo import bibliography_md


def _entry(**kw):
    base = dict(title="GitHub - a/b", source_path="https://github.com/a/b", tags="",
                notes="", professor_signal="", include_in_bundle=True,
                ref_summary="", computed_ref_unit="", computed_ref_topics=[])
    base.update(kw)
    return SimpleNamespace(**base)


def _bib(entries):
    return bibliography_md(
        {"course_name": "Eng Soft"}, entries=entries, subject_profile=None,
        parse_bibliography_from_teaching_plan_fn=lambda t: {},
        clamp_navigation_artifact=lambda s, **k: s,
    )


def test_renders_summary_when_present():
    md = _bib([_entry(ref_summary="Framework de autenticacao.", computed_ref_unit="unidade-01-seguranca",
                      computed_ref_topics=["autenticacao"])])
    assert "Framework de autenticacao." in md
    assert "unidade-01-seguranca" in md


def test_no_summary_line_when_absent():
    md = _bib([_entry()])
    assert "**Resumo:**" not in md
    assert "https://github.com/a/b" in md  # ainda surfacea URL


def test_relevance_map_lists_mapped_reference():
    md = _bib([_entry(title="Spring Sec", computed_ref_unit="unidade-01-seguranca",
                      computed_ref_topics=["autenticacao"])])
    # a tabela de relevância deixa de ser placeholder "[a preencher]"
    assert "[a preencher]" not in md
    assert "Spring Sec" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reference_bibliography.py -v`
Expected: FAIL — `test_renders_summary_when_present` (no summary rendered) and `test_relevance_map_lists_mapped_reference` (placeholder still present).

- [ ] **Step 3: Render summary + relevance per entry**

In `src/builder/artifacts/repo.py`, in `bibliography_md`, inside the `for entry in entries:` loop (after the existing `- **URL:**` / tags / notes lines, before the `- **Incluir no bundle:**` line at ~707), add:

```python
            ref_summary = getattr(entry, "ref_summary", "") or ""
            if ref_summary:
                lines.append(f"- **Resumo:** {ref_summary}")
            ref_unit = getattr(entry, "computed_ref_unit", "") or ""
            ref_topics = getattr(entry, "computed_ref_topics", []) or []
            if ref_unit or ref_topics:
                rel = ref_unit + (f" / {', '.join(ref_topics)}" if ref_topics else "")
                lines.append(f"- **Relevante para:** {rel}")
```

- [ ] **Step 4: Fill the relevance map from mapped entries**

In `bibliography_md`, replace the hardcoded relevance-map block (currently `repo.py:719-727`, the lines from `"## Mapa de relevância por tópico"` through the `"| [a preencher] | | | |"` row) with:

```python
    mapped = [e for e in entries if (getattr(e, "computed_ref_unit", "") or getattr(e, "computed_ref_topics", []))]
    lines += ["## Mapa de relevância por tópico", ""]
    if mapped:
        lines += ["| Tópico/Unidade | Referência | Acessível | Incidência em prova |", "|---|---|---|---|"]
        for e in mapped:
            unit = getattr(e, "computed_ref_unit", "") or ""
            topics = ", ".join(getattr(e, "computed_ref_topics", []) or [])
            alvo = " / ".join([p for p in (unit, topics) if p]) or "—"
            lines.append(f"| {alvo} | {e.title} | sim | — |")
        lines.append("")
    else:
        lines += ["<!-- Preencha após organizar as referências -->", "",
                  "| Tópico | Referência principal | Acessível | Incidência em prova |",
                  "|---|---|---|---|", "| [a preencher] | | | |", ""]
```

Note: `entries` here may be the same list rendered above; this block runs once after the per-entry loop. Keep the existing `clamp_navigation_artifact(...)` return at the end.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_bibliography.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_reference_bibliography.py
git commit -m "feat(reference): bibliography_md renders summary + relevance map"
```

---

## Task 8: Wire reference processing into the build (batch + cache)

**Files:**
- Modify: `src/builder/core/reference_summary.py` (add `load/write_reference_curation`, `summarize_all_reference_entries`)
- Modify: build orchestration (the call site that invokes `summarize_all_code_entries`)
- Test: `tests/test_reference_summary.py`

- [ ] **Step 1: Locate the call site**

Run: `python -m pytest -q` first to confirm green baseline, then find where code summarization is invoked during build:

Run: `rg -n "summarize_all_code_entries" src`
Read that call site (the build/regeneration orchestrator). It builds/loads `client` from `gemini_api_key` and calls `summarize_all_code_entries(builder, client)`. The reference batch slots in the SAME place, guarded the SAME way (lazy: client may be None — but reference batch still runs for the topic mapping; only the summary is skipped).

- [ ] **Step 2: Implement curation cache + batch (mirror code curation)**

Append to `src/builder/core/reference_summary.py`:

```python
import json
import hashlib
from pathlib import Path

REFERENCE_MATCHER_VERSION = 1
_REFERENCE_CATEGORIES = {"referencias", "bibliografia"}


def load_reference_curation(repo_dir: Path) -> dict:
    p = Path(repo_dir) / "course" / "references_curation.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {"entries": {}}
    return {"entries": {}}


def write_reference_curation(repo_dir: Path, data: dict) -> None:
    p = Path(repo_dir) / "course" / "references_curation.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def _ref_hash(entry: dict, text: str) -> str:
    key = (str(entry.get("source_path") or "") + "\n" + (text or "")).encode("utf-8", "replace")
    return hashlib.sha1(key).hexdigest()


def summarize_all_reference_entries(builder, units: list, client, progress_cb=None) -> dict:
    """Processa todas as entries de referência do manifest, com cache por hash.
    Grava computed_ref_* / ref_summary nas entries do manifest e em
    references_curation.json. Sem client -> mapeia por texto, sem resumo."""
    manifest_path = builder.root_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    curation = load_reference_curation(builder.root_dir)
    cache = curation.setdefault("entries", {})

    refs = [e for e in manifest.get("entries", [])
            if str(e.get("category") or "").lower() in _REFERENCE_CATEGORIES]
    for idx, entry in enumerate(refs):
        eid = entry.get("id")
        if not eid:
            continue
        text = fetch_reference_text(entry)
        h = _ref_hash(entry, text)
        existing = cache.get(eid, {})
        if (existing.get("content_hash") == h
                and existing.get("matcher_version") == REFERENCE_MATCHER_VERSION
                and (existing.get("ref_summary") or client is None)):
            fields = existing
        else:
            summary_dict = summarize_reference(text, client)
            concepts = (summary_dict or {}).get("concepts", []) or []
            fallback = " ".join([str(entry.get("title", "") or ""), text])
            topic = assign_concepts_to_unit(concepts, fallback, units)
            fields = {
                "ref_summary": (summary_dict or {}).get("summary", "") or "",
                "ref_concepts": concepts,
                "computed_ref_unit": topic["unit_slug"],
                "computed_ref_topics": topic["topics"],
                "content_hash": h,
                "matcher_version": REFERENCE_MATCHER_VERSION,
            }
            cache[eid] = fields
        for e in manifest["entries"]:
            if e.get("id") == eid:
                e.update({k: fields[k] for k in
                          ("ref_summary", "ref_concepts", "computed_ref_unit", "computed_ref_topics")})
        if progress_cb:
            progress_cb(idx, len(refs), entry.get("title", ""), "ok")

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_reference_curation(builder.root_dir, curation)
    return curation
```

- [ ] **Step 3: Write the cache test**

Append to `tests/test_reference_summary.py`:

```python
def test_batch_caches_by_hash(tmp_path):
    import json as _json
    from src.builder.core import reference_summary as rs
    root = tmp_path
    (root / "course").mkdir()
    (root / "manifest.json").write_text(_json.dumps({"entries": [
        {"id": "r1", "category": "referencias", "file_type": "github-repo",
         "source_path": "https://github.com/a/b"}]}), encoding="utf-8")
    builder = SimpleNamespace_ = type("B", (), {"root_dir": root})()
    units = [{"slug": "u1", "normalized_title": "x", "topic_phrases": [], "topic_tokens": [], "distinctive_tokens": []}]
    client = MagicMock()
    client.summarize_bundle.return_value = ReferenceSummary(inferred_title="t", summary="s", concepts=["c"])
    orig = rs.fetch_reference_text
    try:
        rs.fetch_reference_text = lambda e, **k: "texto fixo"
        rs.summarize_all_reference_entries(builder, units, client)
        rs.summarize_all_reference_entries(builder, units, client)  # 2a vez: cache
    finally:
        rs.fetch_reference_text = orig
    assert client.summarize_bundle.call_count == 1  # resumiu só 1x
```

Add `from types import SimpleNamespace` at the top of the test file if not present.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_reference_summary.py -v`
Expected: all PASS including the cache test (summarize called once across two runs).

- [ ] **Step 5: Wire into the build call site**

At the call site found in Step 1 (next to `summarize_all_code_entries(builder, client)`), add a sibling call. You need the `units` index there — build it via the same helper the regeneration already uses (`build_file_map_unit_index_from_course(course_meta, subject_profile)`; in the facade it is exposed as `_build_file_map_unit_index_from_course`). Concretely, after the code-summarization call:

```python
    from src.builder.core.reference_summary import summarize_all_reference_entries
    units = _build_file_map_unit_index_from_course(course_meta, subject_profile)
    summarize_all_reference_entries(builder, units, client)
```

Use the SAME `client` (None when no `gemini_api_key`) and the same `course_meta`/`subject_profile` already in scope at that call site. If the unit-index helper has a different local name there, use the name in scope (it is the function that builds the unit index from course meta).

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest tests -q`
Expected: zero NEW failures (was 814 + new reference tests; all green).

- [ ] **Step 7: Commit**

```bash
git add src/builder/core/reference_summary.py tests/test_reference_summary.py <build-orchestrator-file>
git commit -m "feat(reference): batch summarize+map references into build with hash cache"
```

---

## Self-Review

**Spec coverage:**
- Aquisição README (GitHub, sem clone) → Task 2. ✓
- Aquisição doc/URL via `url_markdown` → Task 3. ✓
- Resumo Gemini lazy → Task 5. ✓
- Mapa concept→unidade/tópico (não bloco) → Task 4. ✓
- Cache `references_curation.json` por hash → Task 8. ✓
- Surfacing resumo + mapa de relevância na BIBLIOGRAPHY.md → Task 7. ✓
- Storage fields auto-serializados → Task 6. ✓
- Degradado (sem Gemini → mapeia por texto; sem rede → título+URL) → Tasks 3, 6, 8. ✓
- Guardrail (só category referencias/bibliografia; nunca github_url do perfil) → Tasks 3 (gated por source_path da entry) + 8 (filtro por category). ✓

**Placeholder scan:** Sem TBD/"handle errors". Task 8 Step 1 e Step 5 referenciam o call site exato a localizar via `rg` — é um mirror preciso de `summarize_all_code_entries`, com o código a inserir mostrado. Único ponto runtime-dependente (nome local do helper de unit-index no call site) tem instrução explícita.

**Type consistency:**
- `parse_github_repo -> Optional[tuple[str,str]]` (T1) usado em T3. ✓
- `fetch_github_readme(owner, repo)` (T2) chamado em T3 via `fetch_github_readme(*gh)`. ✓
- `fetch_reference_text(entry, *, max_chars)` (T3) usado em T6/T8. ✓
- `assign_concepts_to_unit(concepts, fallback_text, units) -> {"unit_slug","topics","confidence"}` (T4) consumido em T6/T8. ✓
- `summarize_reference(text, client) -> Optional[dict]` com `{summary,concepts,inferred_title}` (T5) usado em T6/T8. ✓
- `process_reference_entry(entry, units, client) -> {ref_summary, ref_concepts, computed_ref_unit, computed_ref_topics}` (T6) — mesmos nomes dos campos FileEntry (T6 Step1) e do render (T7). ✓
- Campos `ref_summary`/`computed_ref_unit`/`computed_ref_topics` consistentes entre T6, T7, T8. ✓

## Follow-ups (NÃO neste plano — ver BACKLOG.md)

1. Harness de referências (gold repo→unidade esperada) medindo acerto de tema.
2. Conserto do clone completo (branch default + long-path) — só p/ análise de código.
3. Token GitHub (rate limit) p/ lote grande.
4. Approach C: injeção das referências no contexto de unidade/tópico que o tutor carrega.
