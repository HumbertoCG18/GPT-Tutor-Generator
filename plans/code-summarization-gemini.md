# Plano: Code Summarization via Gemini + Timeline Integration

**Objetivo**: enriquecer entendimento dos códigos no tutor gerando resumos semânticos via Gemini API + vincular cada código ao bloco do cronograma (timeline) usando concept matching. Persistir em `code_curation.json`. Render consumido por surfaces existentes (CODE_INDEX, header MD) + novo `CRONOGRAMA_DETALHADO.md` (estrutura code-only agora, expansível depois).

**Não-objetivos** (registrados em `plans/material-agnostic-refactor.md`):
- Material-agnostic aggregation (PDFs/imagens/exercícios por bloco) — fica pra plano futuro
- Curator UI completo (só mini-painel ~150 linhas)
- Modificar DeepTutor
- MinerU

**Anti-regressão**: sem `gemini_api_key` configurada → comportamento idêntico ao atual. Lazy import. CRONOGRAMA_DETALHADO só gera se há blocks no `.timeline_index.json`.

---

## Phase 0 — Documentation Discovery (CONCLUÍDA)

### Gemini SDK

| Item | Valor |
|------|-------|
| Pacote | `google-genai` (NÃO `google-generativeai`) |
| Import | `from google import genai` |
| Cliente | `genai.Client(api_key=...)` |
| Modelo | `gemini-2.5-flash` |
| Pricing | $0.30 in / $2.50 out por 1M tokens |
| Errors | `google.genai.errors.APIError` (ClientError/ServerError) |

### Padrão `image_curation` (template)

| Componente | File:line |
|------------|-----------|
| Schema curation no manifest entry | `src/ui/image_curator.py:1620-1635` |
| Hash SHA1 | `src/ui/image_curator.py:114-142` |
| Prune stale | `src/builder/core/image_resolution.py:181-253` |
| Engine import + método | `src/builder/engine.py:178-183` |
| Callsite build | `src/builder/ops/build_workflow.py:113` |
| Botão batch + worker | `src/ui/image_curator.py:313, 1476-1616` |
| Settings dialog | `src/ui/dialogs.py:305-362` |
| AppConfig storage | `src/ui/theme.py:84-132` |
| Vision call | `src/builder/vision/ollama_client.py:294` |

### Timeline data model (existente — IMPORTANTE)

| Componente | File:line | Função |
|------------|-----------|--------|
| `FileEntry.manual_timeline_block_id` | `src/models/core.py:49` | Já existe, aplica a códigos |
| `SubjectProfile.syllabus` | `src/models/core.py:142` | Cronograma como markdown (não estruturado) |
| Block dataclass (dict) | `src/builder/timeline/index.py:1880-1910` | id, period_start/end, period_label, unit_slug, primary_topic_label, topic_text, topics, aliases, sessions |
| Block ID format | `src/builder/timeline/index.py:1880` | `bloco-01`, `bloco-02` |
| Block ↔ Unit link | `src/builder/timeline/index.py:1913-1920` | via `unit_slug`, threshold 0.51 |
| Serialização | `src/builder/timeline/index.py:984-1009` | `.timeline_index.json` v3 |
| Auto-tag `bloco:bloco-NN` | em `auto_tags` de entries | Existente |
| Loader UI | `src/ui/timeline_dashboard.py:35-45` | `load_timeline_data` |
| ASPNET parser | `src/utils/helpers.py:414-424` | `parse_html_schedule` |
| Unit extraction | `src/builder/extraction/teaching_plan.py:30-119` | regex em PDF plano |

### UI insertion points

| Ponto | File:line |
|-------|-----------|
| Tabs notebook | `src/ui/app.py:546` (após Cronograma) |
| Settings vision section end | `src/ui/dialogs.py:363` |
| AppConfig defaults | `src/ui/theme.py` DEFAULTS dict |

### Anti-patterns

```bash
grep -rn "google.generativeai" src/    # 0 matches
grep -rn "genai.GenerativeModel" src/  # 0 matches (API antiga)
```

NÃO usar `response_format={...}` wrapper. Usar `response_mime_type="application/json"` + `response_schema=PydanticModel`.

---

## Phase 1 — Backbone (Gemini client + summarization engine + settings + block matcher)

### 1.1 Settings

**A) `src/ui/theme.py` DEFAULTS** — adicionar:

```python
"gemini_api_key": "",
"gemini_model": "gemini-2.5-flash",
```

**B) `src/ui/dialogs.py:363`** — inserir após vision fields:

```python
ttk.Separator(tab_proc, orient="horizontal").grid(
    row=sep_row + 9, column=0, columnspan=2, sticky="ew", pady=(12, 8))
ttk.Label(tab_proc, text="Gemini — Resumos de Código",
          style="Accent.TLabel").grid(
    row=sep_row + 10, column=0, columnspan=2, sticky="w", pady=(0, 8))

self._var_gemini_api_key = tk.StringVar(value=self.config.get("gemini_api_key", ""))
self._var_gemini_model = tk.StringVar(value=self.config.get("gemini_model", "gemini-2.5-flash"))

ttk.Label(tab_proc, text="Chave da API do Gemini").grid(
    row=sep_row + 11, column=0, sticky="w", pady=6, padx=(0, 16))
ttk.Entry(tab_proc, textvariable=self._var_gemini_api_key, width=28, show="*").grid(
    row=sep_row + 11, column=1, sticky="ew")

ttk.Label(tab_proc, text="Modelo Gemini").grid(
    row=sep_row + 12, column=0, sticky="w", pady=6, padx=(0, 16))
ttk.Combobox(tab_proc, textvariable=self._var_gemini_model,
             values=["gemini-2.5-flash", "gemini-2.5-pro"],
             state="readonly", width=25).grid(
    row=sep_row + 12, column=1, sticky="ew")
```

**C) `_save()`** — persist após linha 399:

```python
self.config.set("gemini_api_key", self._var_gemini_api_key.get().strip())
self.config.set("gemini_model", self._var_gemini_model.get())
```

### 1.2 Cliente Gemini (NOVO)

**Arquivo**: `src/builder/runtime/gemini_client.py` (~140 linhas)

```python
"""Gemini API client for code summarization."""
from __future__ import annotations
import logging
import time
from typing import Optional, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"


def has_gemini_api_key(config) -> bool:
    if config is None:
        return False
    key = (config.get("gemini_api_key", "") or "").strip()
    return bool(key)


class GeminiClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai não instalado. Rode: pip install google-genai"
            ) from exc
        self._client = genai.Client(api_key=self.api_key)

    def summarize_bundle(
        self,
        bundle_text: str,
        schema: Type[BaseModel],
        system_instruction: str,
        max_retries: int = 5,
    ) -> BaseModel:
        self._ensure_client()
        from google.genai import types
        from google.genai import errors as genai_errors

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
        )

        delay = 1.0
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                resp = self._client.models.generate_content(
                    model=self.model,
                    contents=bundle_text,
                    config=config,
                )
                if resp.parsed is None:
                    raise RuntimeError("Gemini retornou parsed=None")
                return resp.parsed
            except genai_errors.ClientError as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    last_exc = e
                    logger.warning("[Gemini] 429 attempt %d/%d, sleeping %.1fs",
                                   attempt + 1, max_retries, delay)
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
                    continue
                raise
            except genai_errors.ServerError as e:
                last_exc = e
                logger.warning("[Gemini] 5xx attempt %d/%d, sleeping %.1fs",
                               attempt + 1, max_retries, delay)
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
        raise RuntimeError(f"Gemini falhou após {max_retries} tentativas") from last_exc


def get_gemini_client(config) -> Optional[GeminiClient]:
    if not has_gemini_api_key(config):
        return None
    key = config.get("gemini_api_key", "").strip()
    model = config.get("gemini_model", DEFAULT_MODEL)
    return GeminiClient(api_key=key, model=model)
```

### 1.3 Summarization engine + block matcher (NOVO)

**Arquivo**: `src/builder/core/code_summarization.py` (~300 linhas)

#### Schema Pydantic

```python
from pydantic import BaseModel, Field
from typing import Literal

PedagogicalRole = Literal[
    "exemplo_demonstrativo",
    "exercicio_resolvido",
    "template_aluno",
    "solucao_referencia",
    "utilitario",
    "outro",
]

class CodeFileSummary(BaseModel):
    name: str
    role: str

class CodeSummary(BaseModel):
    inferred_title: str = Field(..., description="Título descritivo do conteúdo")
    language: str
    pedagogical_role: PedagogicalRole
    concepts: list[str] = Field(..., description="3-8 termos técnicos do domínio")
    summary: str = Field(..., description="2-3 linhas: o que faz, por que importa")
    files: list[CodeFileSummary] = Field(default_factory=list)
```

#### System instruction

```python
SYSTEM_INSTRUCTION = """Você analisa bundles de código acadêmico (Python, Jupyter,
Dafny, Java etc) e produz resumos estruturados em JSON.

Contexto: usuário é estudante; bundles vêm de matérias universitárias.

Sua saída alimenta um tutor LLM. Tutor precisa entender:
- O que código DEMONSTRA conceitualmente
- Qual papel pedagógico cumpre
- Que conceitos vincular ao glossário/unidades

Regras:
- inferred_title: descritivo e específico. NUNCA repita filename
  (ex: "Verificação de pré/pós-condições com Dafny", NÃO "introducao.dfy")
- concepts: 3-8 termos técnicos. Use terminologia do domínio
  (ex: "tripla de Hoare", "invariante de laço", "ghost predicate")
- summary: 2-3 frases. Foque no QUE ensina, não na sintaxe
- files: liste cada arquivo do bundle com role curto
- Responda em português brasileiro
- Saída APENAS JSON válido conforme schema"""
```

#### Bundle builder

```python
def _build_bundle_text(builder, entry_data: dict) -> str:
    parts = []
    parts.append(f"# Entry: {entry_data.get('title', '<sem título>')}")
    parts.append(f"Unidade: {entry_data.get('tags', '?')}")
    parts.append(f"Categoria: {entry_data.get('category', '?')}")
    parts.append("")

    base_md = entry_data.get("base_markdown")
    if base_md:
        path = builder.root_dir / base_md
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))

    for ef in entry_data.get("extracted_files") or []:
        ef_md = ef.get("base_markdown")
        if ef_md:
            path = builder.root_dir / ef_md
            if path.exists():
                parts.append(f"\n\n## Arquivo: {ef.get('title', '<sem nome>')}\n")
                parts.append(path.read_text(encoding="utf-8", errors="replace"))

    text = "\n".join(parts)
    if len(text) > 200_000:
        text = text[:200_000] + "\n\n[...truncado em 200k chars...]"
    return text


def compute_entry_hash(entry_data: dict, builder) -> str:
    import hashlib
    bundle = _build_bundle_text(builder, entry_data)
    return hashlib.sha1(bundle.encode("utf-8", errors="replace")).hexdigest()
```

#### Block matcher (concept-based, sem chamada extra Gemini)

```python
import re
import unicodedata

def _normalize(text: str) -> str:
    """Remove acentos, lowercase, strip. Para matching robusto."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def assign_code_to_block(
    concepts: list[str],
    timeline_blocks: list[dict],
    *,
    primary_threshold: float = 0.4,
    secondary_threshold: float = 0.25,
    margin_threshold: float = 0.15,
) -> tuple[str, list[str], float, str]:
    """Concept-match código → block.

    Compara concepts do Gemini contra block.topics + primary_topic_label +
    aliases + topic_text. Retorna (primary_id, secondary_ids, confidence, method).

    method ∈ {"auto_concept", "orphan"}.
    """
    if not concepts or not timeline_blocks:
        return ("", [], 0.0, "orphan")

    concepts_norm = {_normalize(c) for c in concepts if c}
    concepts_norm.discard("")
    if not concepts_norm:
        return ("", [], 0.0, "orphan")

    scores: list[tuple[str, float]] = []
    for blk in timeline_blocks:
        bag: set[str] = set()
        for t in blk.get("topics") or []:
            bag.add(_normalize(t))
        bag.add(_normalize(blk.get("primary_topic_label", "")))
        for a in blk.get("aliases") or []:
            bag.add(_normalize(a))
        for token in (blk.get("topic_text") or "").split():
            n = _normalize(token)
            if len(n) >= 4:
                bag.add(n)
        bag.discard("")
        if not bag:
            scores.append((blk["id"], 0.0))
            continue

        # Score = overlap parcial (substring match) / N concepts
        overlap = 0
        for c in concepts_norm:
            for b in bag:
                if c == b or (len(c) >= 5 and c in b) or (len(b) >= 5 and b in c):
                    overlap += 1
                    break
        score = overlap / len(concepts_norm)
        scores.append((blk["id"], score))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_id, top_score = scores[0]
    second_score = scores[1][1] if len(scores) > 1 else 0.0
    margin = top_score - second_score

    if top_score >= primary_threshold and margin >= margin_threshold:
        secondaries = [
            bid for bid, s in scores[1:]
            if s >= secondary_threshold and s >= top_score * 0.6
        ]
        return (top_id, secondaries[:2], top_score, "auto_concept")

    return ("", [], top_score, "orphan")
```

**Thresholds calibrados conservadoramente**: 0.4 primary é generoso, mas margin de 0.15 garante que ambiguidade vira órfão. Calibrar com dados reais depois.

#### Curation IO

```python
import json
from datetime import datetime
from pathlib import Path

def load_code_curation(repo_dir: Path) -> dict:
    path = repo_dir / "code_curation.json"
    if not path.exists():
        return {"version": 1, "entries": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "entries": {}}


def write_code_curation(repo_dir: Path, data: dict) -> None:
    path = repo_dir / "code_curation.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

#### Top-level summarize functions

```python
def _load_timeline_blocks(builder) -> list[dict]:
    path = builder.root_dir / ".timeline_index.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("blocks", []) or []
    except Exception:
        return []


def summarize_code_entry(builder, entry_data: dict, client) -> Optional[dict]:
    bundle_text = _build_bundle_text(builder, entry_data)
    if not bundle_text.strip():
        return None
    try:
        result: CodeSummary = client.summarize_bundle(
            bundle_text=bundle_text,
            schema=CodeSummary,
            system_instruction=SYSTEM_INSTRUCTION,
        )
        summary_dict = result.model_dump()
        # Block matching pós-summary
        blocks = _load_timeline_blocks(builder)
        primary, secondaries, conf, method = assign_code_to_block(
            summary_dict["concepts"], blocks
        )
        summary_dict["primary_block_id"] = primary
        summary_dict["secondary_block_ids"] = secondaries
        summary_dict["block_match_confidence"] = round(conf, 3)
        summary_dict["block_match_method"] = method
        return summary_dict
    except Exception as exc:
        logger.error("[CodeSummary] Falha em %s: %s",
                     entry_data.get("id"), exc)
        return None


def summarize_all_code_entries(builder, client, progress_cb=None) -> dict:
    """Summarize ALL code entries, cache by hash. Returns updated curation dict."""
    manifest_path = builder.root_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    curation = load_code_curation(builder.root_dir)
    entries_map = curation.setdefault("entries", {})

    code_entries = _collect_code_entries(manifest)
    total = len(code_entries)
    for idx, entry_data in enumerate(code_entries):
        eid = entry_data.get("id")
        if not eid:
            continue
        new_hash = compute_entry_hash(entry_data, builder)
        existing = entries_map.get(eid, {})
        if existing.get("content_hash") == new_hash and existing.get("summary"):
            if progress_cb:
                progress_cb(idx, total, entry_data.get("title", ""), "cached")
            continue

        if progress_cb:
            progress_cb(idx, total, entry_data.get("title", ""), "calling_api")

        summary = summarize_code_entry(builder, entry_data, client)
        if summary is None:
            continue
        entries_map[eid] = {
            "content_hash": new_hash,
            "model": client.model,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": summary,
        }
        write_code_curation(builder.root_dir, curation)

    if progress_cb:
        progress_cb(total, total, "", "done")
    return curation


def _collect_code_entries(manifest: dict) -> list[dict]:
    """Top-level code entries + flattened ZIP children."""
    result = []
    for e in manifest.get("entries", []):
        if e.get("file_type") == "code":
            result.append(e)
        elif e.get("file_type") == "zip":
            for ef in e.get("extracted_files") or []:
                # ZIP children são entries virtuais; tratamos ZIP como bundle único
                pass
            # Trata ZIP como entry único (bundle holístico)
            result.append(e)
    return result
```

#### Prune

```python
def prune_stale_code_curation(builder) -> int:
    curation_path = builder.root_dir / "code_curation.json"
    if not curation_path.exists():
        return 0
    manifest_path = builder.root_dir / "manifest.json"
    if not manifest_path.exists():
        return 0

    try:
        curation = json.loads(curation_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return 0

    valid_ids = {e.get("id") for e in manifest.get("entries", []) if e.get("id")}
    entries_map = curation.get("entries", {})
    stale = [eid for eid in entries_map if eid not in valid_ids]
    for eid in stale:
        entries_map.pop(eid, None)

    if stale:
        curation_path.write_text(
            json.dumps(curation, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("[CodeCuration] Pruned %d stale entries", len(stale))
    return len(stale)
```

### 1.4 Engine wiring

**`src/builder/engine.py:178-183`** — import:

```python
from src.builder.core.code_summarization import (
    prune_stale_code_curation as _core_code_summarization_prune_stale,
    load_code_curation as _core_code_summarization_load,
    summarize_all_code_entries as _core_code_summarization_summarize_all,
)
```

Métodos em `RepoBuilder`:

```python
def _prune_stale_code_curation(self) -> int:
    return _core_code_summarization_prune_stale(self)

def _load_code_curation(self) -> dict:
    return _core_code_summarization_load(self.root_dir)

def _summarize_code_entries(self, client, progress_cb=None) -> dict:
    return _core_code_summarization_summarize_all(self, client, progress_cb)
```

### 1.5 Verification checklist (Phase 1)

- [ ] `pip install google-genai` instalado em venv
- [ ] `from src.builder.runtime.gemini_client import GeminiClient` importa OK
- [ ] `has_gemini_api_key({})` → False
- [ ] `has_gemini_api_key({"gemini_api_key": "x"})` → True
- [ ] Settings dialog mostra novos campos (key masked com `*`)
- [ ] Salvar persiste em `~/.gpt_tutor_config.json`
- [ ] `prune_stale_code_curation` em repo sem JSON retorna 0
- [ ] `assign_code_to_block(["ghosts", "autocontrato"], blocks_fake)` retorna primary correto pra block que tem topics=["ghosts", "predicado fantasma"]
- [ ] `assign_code_to_block(["tema-aleatorio-xyz"], blocks)` retorna ("", [], <baixo>, "orphan")
- [ ] App abre sem key configurada (lazy import não dispara)
- [ ] Anti-pattern: `grep -rn "google.generativeai" src/` → 0

---

## Phase 2 — Build Pipeline Integration (prune apenas)

### 2.1 Build workflow

**`src/builder/ops/build_workflow.py:113`** — após image prune:

```python
removed = builder._prune_stale_image_curation()
if removed:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

removed_code = builder._prune_stale_code_curation()
if removed_code:
    logger.info("Pruned %d stale code_curation entries", removed_code)

builder._resolve_content_images()
```

### 2.2 Incremental build

`src/builder/ops/incremental_build.py` — mesma adição após image prune.

### 2.3 Verification

- [ ] Build sem `code_curation.json` não quebra
- [ ] Build com curation órfã limpa entries stale
- [ ] Log mostra contador

---

## Phase 3 — Render rico (CODE_INDEX, header MD, CRONOGRAMA_DETALHADO)

### 3.1 Header MD por entry

**`src/builder/core/source_importers.py:61`** — substituir construção body:

```python
curation = _get_or_load_code_curation(builder)  # cacheia em builder._code_curation
entry_data = curation.get("entries", {}).get(entry.id(), {})
entry_summary = entry_data.get("summary") or {}

if entry_summary:
    title = entry_summary.get("inferred_title") or entry.title
    body = f"# {title}\n\n"
    body += f"> **Arquivo original:** `{entry.title}`\n"

    # Linkagem timeline
    primary_block_id = entry_summary.get("primary_block_id", "")
    if primary_block_id:
        block_info = _resolve_block_info(builder, primary_block_id)
        if block_info:
            body += f"> **Aula:** {block_info['period_label']} — {block_info['primary_topic_label']}\n"

    secondary = entry_summary.get("secondary_block_ids") or []
    if secondary:
        labels = []
        for bid in secondary:
            bi = _resolve_block_info(builder, bid)
            if bi:
                labels.append(f"{bi['period_label']} ({bi['primary_topic_label']})")
        if labels:
            body += f"> **Também relevante para:** {'; '.join(labels)}\n"

    body += f"> **Linguagem:** {entry_summary.get('language', lang)}"
    if entry.tags:
        body += f"  |  **Unidade:** {entry.tags}"
    body += f"  |  **Papel:** {entry_summary.get('pedagogical_role', '?')}\n"

    concepts = entry_summary.get("concepts") or []
    if concepts:
        body += f"> **Conceitos:** {', '.join(concepts)}\n"

    body += f"\n**Resumo:** {entry_summary.get('summary', '')}\n\n---\n\n"
else:
    # Fallback (header atual original)
    body = f"# {entry.title}\n\n"
    body += f"> **Linguagem:** {lang}"
    if entry.tags:
        body += f"  |  **Unidade:** {entry.tags}"
    if entry.notes:
        body += f"\n> {entry.notes}"
    body += "\n\n"

if ext == "ipynb":
    body += body_content.rstrip() + "\n"
else:
    body += f"```{lang}\n{body_content}\n```\n"
```

Helper `_resolve_block_info` em `code_summarization.py` ou local — carrega `.timeline_index.json` e retorna `{period_label, primary_topic_label}`.

### 3.2 CODE_INDEX agrupado por aula

**`src/builder/artifacts/repo.py:807-855`** — reescrever `code_index_md`:

```python
def code_index_md(
    course_meta: dict,
    entries=None,
    subject_profile=None,
    *,
    code_curation: Optional[dict] = None,
    timeline_blocks: Optional[list[dict]] = None,
    code_review_profile_fn: Callable[[Optional[dict], object], dict],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    curation_entries = (code_curation or {}).get("entries", {})
    blocks_by_id = {b["id"]: b for b in (timeline_blocks or [])}

    # Agrupar code entries por primary_block_id
    by_block: dict[str, list] = {}
    orphans: list = []
    for e in entries:
        if e.file_type not in ("code", "zip"):
            continue
        if e.category not in ("codigo-professor", "codigo-aluno", "codigo-trabalho-aluno"):
            continue
        summary = (curation_entries.get(e.id()) or {}).get("summary") or {}
        primary = summary.get("primary_block_id", "")
        if primary and primary in blocks_by_id:
            by_block.setdefault(primary, []).append((e, summary))
        else:
            orphans.append((e, summary))

    profile = code_review_profile_fn(course_meta, subject_profile)
    lines = [f"# CODE_INDEX — {course_name}", "",
             profile["code_index_intro"],
             profile["code_index_review_line"], ""]

    # Render por bloco (em ordem cronológica)
    for bid in sorted(blocks_by_id.keys()):
        entries_in = by_block.get(bid, [])
        if not entries_in:
            continue
        blk = blocks_by_id[bid]
        period = blk.get("period_label", bid)
        topic = blk.get("primary_topic_label", "")
        header = f"## {period} — {topic}" if topic else f"## {period}"
        lines += [header, ""]
        lines += ["| Título | Linguagem | Categoria | Conceitos | Papel | Arquivo |",
                  "|---|---|---|---|---|---|"]
        for e, s in entries_in:
            title = s.get("inferred_title") or e.title
            lang = s.get("language", "")
            cat_short = {"codigo-professor": "prof",
                         "codigo-aluno": "aluno",
                         "codigo-trabalho-aluno": "trabalho"}.get(e.category, e.category)
            concepts = ", ".join((s.get("concepts") or [])[:4])
            role = s.get("pedagogical_role", "")
            fname = Path(e.source_path).name
            lines.append(f"| {title} | {lang} | {cat_short} | {concepts} | {role} | `{fname}` |")
        lines.append("")

    # Órfãos
    if orphans:
        lines += ["## ⚠ Sem aula atribuída (requer atribuição manual)", ""]
        lines += ["| Título | Linguagem | Conceitos | Arquivo |",
                  "|---|---|---|---|"]
        for e, s in orphans:
            title = s.get("inferred_title") or e.title
            lang = s.get("language", "")
            concepts = ", ".join((s.get("concepts") or [])[:4])
            fname = Path(e.source_path).name
            lines.append(f"| {title} | {lang} | {concepts} | `{fname}` |")
        lines.append("")

    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=14000, label="course/CODE_INDEX.md")
```

**Callsites** — procurar quem chama `code_index_md`, passar `code_curation` e `timeline_blocks=builder._load_timeline_blocks()` (helper a adicionar no engine, leitura simples de `.timeline_index.json`).

### 3.3 CRONOGRAMA_DETALHADO.md (NOVO — estrutura code-only, expansível)

**`src/builder/artifacts/repo.py`** — adicionar função:

```python
def cronograma_detalhado_md(
    course_meta: dict,
    entries: list,
    code_curation: dict,
    timeline_blocks: list[dict],
    subject_profile=None,
) -> str:
    """Render bloco-por-bloco com tópicos + códigos vinculados.

    Estrutura code-only nesta iteração. Seções placeholder ("Materiais",
    "Exercícios") ficam comentadas/vazias até material-agnostic refactor.
    """
    course_name = course_meta.get("course_name", "Curso")
    curation_entries = (code_curation or {}).get("entries", {})

    # Index: code entries primários e secundários por block
    primary_idx: dict[str, list] = {}
    secondary_idx: dict[str, list] = {}
    for e in entries:
        if e.file_type not in ("code", "zip"):
            continue
        if e.category not in ("codigo-professor", "codigo-aluno", "codigo-trabalho-aluno"):
            continue
        s = (curation_entries.get(e.id()) or {}).get("summary") or {}
        if s.get("primary_block_id"):
            primary_idx.setdefault(s["primary_block_id"], []).append((e, s))
        for sb in (s.get("secondary_block_ids") or []):
            secondary_idx.setdefault(sb, []).append((e, s))

    lines = [
        f"# CRONOGRAMA DETALHADO — {course_name}",
        "",
        "> Visão aula-por-aula com tópicos cobertos e materiais vinculados.",
        "> **Nesta versão**: apenas códigos. Expansão futura: PDFs, exercícios, imagens.",
        "",
    ]

    for blk in timeline_blocks:
        bid = blk["id"]
        period = blk.get("period_label", bid)
        topic = blk.get("primary_topic_label", "")
        topics = blk.get("topics") or []
        unit_slug = blk.get("unit_slug", "")

        header = f"## {period}"
        if topic:
            header += f" — {topic}"
        lines += [header, ""]

        if unit_slug:
            lines.append(f"**Unidade**: {unit_slug}")
        if topics:
            lines.append(f"**Tópicos cobertos**: {', '.join(topics)}")
        lines.append("")

        # Materiais (code-only por enquanto)
        primaries = primary_idx.get(bid, [])
        secondaries = secondary_idx.get(bid, [])

        if primaries or secondaries:
            lines += ["### Códigos desta aula", ""]
            for e, s in primaries:
                title = s.get("inferred_title") or e.title
                fname = Path(e.source_path).name
                concepts = ", ".join((s.get("concepts") or [])[:4])
                role = s.get("pedagogical_role", "")
                lines.append(f"- **{title}** (`{fname}`)")
                if concepts:
                    lines.append(f"  - Conceitos: {concepts}")
                if role:
                    lines.append(f"  - Papel: {role}")
            if secondaries:
                lines += ["", "**Também relevante** (outras aulas como contexto):", ""]
                for e, s in secondaries:
                    title = s.get("inferred_title") or e.title
                    fname = Path(e.source_path).name
                    lines.append(f"- {title} (`{fname}`)")
        else:
            lines.append("_Sem códigos vinculados a esta aula._")

        lines += ["", "<!-- TODO (material-agnostic refactor): PDFs, exercícios, imagens -->", "", "---", ""]

    return "\n".join(lines)
```

**Wire**: chamada após CODE_INDEX gen (em `pedagogical_regeneration.py` ou `bootstrap_ops.py`). Só gera se `timeline_blocks` não-vazio.

### 3.4 FILE_MAP

**`src/builder/routing/file_map.py`** — quando renderiza entry de código, usar `inferred_title` do curation se disponível. Mudança ~5 linhas.

### 3.5 Verification (Phase 3)

- [ ] Build sem curation: MDs e CODE_INDEX idênticos ao atual (diff vazio)
- [ ] Build com curation manual em 1 entry: MD mostra título + aula + conceitos
- [ ] CODE_INDEX agrupado por aula com data + tópico
- [ ] Entries órfãos vão pra seção "⚠ Sem aula atribuída"
- [ ] CRONOGRAMA_DETALHADO.md gerado se há blocks
- [ ] CRONOGRAMA_DETALHADO mostra códigos primários + secundários
- [ ] Block sem códigos mostra "_Sem códigos vinculados_"

---

## Phase 4 — UI Mini-painel "💻 Códigos"

### 4.1 `src/ui/codes_panel.py` (NOVO, ~250 linhas)

```python
class CodesPanel(tk.Frame):
    """Mini-painel pra gerar/editar code summaries + atribuir aula."""

    def __init__(self, parent, *, get_subject_fn, get_config_fn, get_repo_dir_fn):
        super().__init__(parent)
        self._get_subject = get_subject_fn
        self._get_config = get_config_fn
        self._get_repo_dir = get_repo_dir_fn
        self._busy = False
        self._build_ui()

    def _build_ui(self):
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=8)
        ttk.Button(toolbar, text="🔄 Recarregar", command=self.refresh).pack(side="left", padx=2)
        ttk.Button(toolbar, text="✨ Gerar resumos (Gemini)",
                   command=self._on_generate_all).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📝 Editar selecionado",
                   command=self._on_edit_selected).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🎯 Atribuir aula",
                   command=self._on_assign_block).pack(side="left", padx=2)

        # Treeview
        cols = ("status", "titulo", "linguagem", "aula", "conceitos")
        self._tree = ttk.Treeview(self, columns=cols, show="tree headings")
        self._tree.heading("#0", text="ID")
        for c, label in zip(cols, ("Status", "Título", "Linguagem", "Aula", "Conceitos")):
            self._tree.heading(c, text=label)
        self._tree.column("status", width=80)
        self._tree.column("titulo", width=300)
        self._tree.column("linguagem", width=80)
        self._tree.column("aula", width=200)
        self._tree.column("conceitos", width=300)
        self._tree.pack(fill="both", expand=True, padx=8)

        # Status bar
        self._status = tk.StringVar(value="Sem matéria selecionada.")
        ttk.Label(self, textvariable=self._status).pack(fill="x", padx=8, pady=4)

    def refresh(self):
        """Re-read manifest + curation, redraw."""
        for item in self._tree.get_children():
            self._tree.delete(item)

        repo_dir = self._get_repo_dir()
        if not repo_dir:
            self._status.set("Sem matéria selecionada.")
            return

        manifest_path = Path(repo_dir) / "manifest.json"
        if not manifest_path.exists():
            self._status.set("Manifest não encontrado.")
            return

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        curation = json.loads((Path(repo_dir) / "code_curation.json").read_text(encoding="utf-8")) \
            if (Path(repo_dir) / "code_curation.json").exists() \
            else {"entries": {}}
        timeline_path = Path(repo_dir) / ".timeline_index.json"
        blocks_by_id = {}
        if timeline_path.exists():
            blocks_data = json.loads(timeline_path.read_text(encoding="utf-8"))
            blocks_by_id = {b["id"]: b for b in blocks_data.get("blocks", [])}

        total = 0
        with_summary = 0
        for e in manifest.get("entries", []):
            if e.get("file_type") not in ("code", "zip"):
                continue
            total += 1
            eid = e.get("id", "")
            entry_curation = curation.get("entries", {}).get(eid, {})
            summary = entry_curation.get("summary") or {}
            has_summary = bool(summary)
            if has_summary:
                with_summary += 1

            status_icon = "✅" if has_summary else "⏳"
            title = summary.get("inferred_title") or e.get("title", "")
            lang = summary.get("language") or ""
            block_id = summary.get("primary_block_id", "")
            if block_id and block_id in blocks_by_id:
                block_label = blocks_by_id[block_id].get("period_label", block_id)
            elif has_summary:
                block_label = "⚠ órfão"
            else:
                block_label = ""
            concepts = ", ".join((summary.get("concepts") or [])[:3])

            self._tree.insert("", "end", iid=eid,
                              text=eid[:8],
                              values=(status_icon, title, lang, block_label, concepts))

        self._status.set(f"{with_summary}/{total} resumidos.")

    def _on_generate_all(self):
        if self._busy:
            return
        config = self._get_config()
        from src.builder.runtime.gemini_client import get_gemini_client, has_gemini_api_key
        if not has_gemini_api_key(config):
            messagebox.showwarning("Gemini", "Configure a chave da API em Settings.")
            return
        client = get_gemini_client(config)

        repo_dir = self._get_repo_dir()
        if not repo_dir:
            return

        # Spawn worker thread (espelha image_curator pattern)
        self._busy = True
        self._status.set("Iniciando...")

        def _worker():
            try:
                from src.builder.core.code_summarization import summarize_all_code_entries
                # Construir um builder leve OU passar repo_dir direto — depende do API
                # Para isto, criar wrapper que recebe repo_dir e simula builder.root_dir
                from src.builder.engine import RepoBuilder  # ou helper

                def _progress(idx, total, title, status):
                    self.after(0, lambda: self._status.set(
                        f"[{idx}/{total}] {status}: {title}"
                    ))

                builder = self._make_lightweight_builder(repo_dir)
                summarize_all_code_entries(builder, client, _progress)
                self.after(0, self.refresh)
                self.after(0, lambda: messagebox.showinfo(
                    "Códigos", "Resumos gerados/atualizados."
                ))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Erro", str(exc)))
            finally:
                self._busy = False

        threading.Thread(target=_worker, daemon=True).start()

    def _on_edit_selected(self):
        # Dialog modal com textareas para inferred_title, language, concepts (csv),
        # summary, pedagogical_role dropdown. Salva no code_curation.json e refresh.
        ...

    def _on_assign_block(self):
        # Dialog com Combobox de blocks (period_label + topic) + secundários (multiselect).
        # Salva primary_block_id + secondary_block_ids no curation.
        ...

    def _make_lightweight_builder(self, repo_dir):
        # Helper minimal — RepoBuilder pode ser pesado demais. Criar wrapper só com
        # .root_dir e métodos necessários, OU usar RepoBuilder existente se factory permitir.
        ...
```

### 4.2 Wire em `src/ui/app.py:546`

```python
# Após Cronograma tab, antes do bind:
tab_codes = ttk.Frame(self.notebook)
self._codes_tab = tab_codes
self.notebook.add(tab_codes, text="  💻 Códigos  ")
self._codes_panel = CodesPanel(
    tab_codes,
    get_subject_fn=lambda: self._resolve_subject_profile(),
    get_config_fn=lambda: self.config,
    get_repo_dir_fn=lambda: self._repo_dir(),
)
self._codes_panel.pack(fill="both", expand=True)
```

`_on_notebook_tab_changed` — adicionar:

```python
if current is getattr(self, "_codes_tab", None):
    self._codes_panel.refresh()
```

Import:

```python
from src.ui.codes_panel import CodesPanel
```

### 4.3 Verification (Phase 4)

- [ ] Tab "💻 Códigos" aparece entre Cronograma e Log
- [ ] Sem matéria: status mostra "Sem matéria selecionada"
- [ ] Com matéria: tree lista code entries (file_type=code OR zip)
- [ ] Coluna Aula mostra `period_label` quando atribuído
- [ ] Coluna Aula mostra "⚠ órfão" quando summary existe mas sem block
- [ ] Sem Gemini key: warning ao clicar "Gerar resumos"
- [ ] Worker thread não trava UI
- [ ] Cache hit: rodar 2× → 2ª vez log marca "cached" sem chamada API
- [ ] Edit dialog salva e refresca tree
- [ ] Assign block dialog mostra todos blocks da matéria

---

## Phase 5 — CODE_HEALTH.md

### 5.1 Gerador

**`src/builder/artifacts/repo.py`** — adicionar:

```python
def code_health_md(
    course_meta: dict,
    entries: list,
    code_curation: dict,
    timeline_blocks: list[dict],
    glossary_terms: Optional[set[str]] = None,
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    curation_entries = (code_curation or {}).get("entries", {})
    code_entries = [e for e in entries if e.file_type in ("code", "zip")
                    and e.category and e.category.startswith("codigo")]

    total = len(code_entries)
    with_summary = sum(1 for e in code_entries if e.id() in curation_entries)
    pct = (with_summary / total * 100) if total else 0

    # Cobertura timeline
    with_block = 0
    orphans_list = []
    for e in code_entries:
        s = (curation_entries.get(e.id()) or {}).get("summary") or {}
        if s.get("primary_block_id"):
            with_block += 1
        elif s:  # tem summary mas sem block
            orphans_list.append((e, s))

    # Cobertura por unidade
    by_unit: dict[str, int] = {}
    for e in code_entries:
        key = e.tags or "(sem unidade)"
        by_unit[key] = by_unit.get(key, 0) + 1

    # Conceitos
    all_concepts: set[str] = set()
    for eid in curation_entries:
        all_concepts.update(
            (curation_entries[eid].get("summary") or {}).get("concepts") or []
        )

    lines = [
        f"# CODE_HEALTH — {course_name}",
        "",
        "> Relatório auto-gerado da saúde da base de código.",
        "",
        "## Cobertura de resumos",
        f"- Códigos totais: **{total}**",
        f"- Com resumo Gemini: **{with_summary} / {total} ({pct:.0f}%)**",
        f"- Sem resumo: **{total - with_summary}**",
        "",
        "## Cobertura timeline",
        f"- Vinculados a aula: **{with_block} / {with_summary}**",
        f"- Órfãos (resumo sem aula): **{len(orphans_list)}**",
    ]
    if orphans_list:
        lines += ["", "### Órfãos (requer atribuição manual)"]
        for e, s in orphans_list[:30]:
            title = s.get("inferred_title") or e.title
            lines.append(f"- `{Path(e.source_path).name}` — {title}")

    lines += ["", "## Cobertura por unidade"]
    for unit, n in sorted(by_unit.items()):
        lines.append(f"- {unit}: {n} código(s)")

    if glossary_terms is not None:
        intersect = all_concepts & glossary_terms
        orphan_concepts = sorted(all_concepts - glossary_terms)
        lines += ["", "## Conceitos vs Glossário",
                  f"- Conceitos extraídos: **{len(all_concepts)}**",
                  f"- Match com glossário: **{len(intersect)}**"]
        if orphan_concepts:
            lines.append(f"- ⚠ Órfãos (no resumo mas não no glossário): {len(orphan_concepts)}")
            lines += [f"  - {c}" for c in orphan_concepts[:20]]

    return "\n".join(lines)
```

### 5.2 Wire

`pedagogical_regeneration.py` ou `bootstrap_ops.py` — após CODE_INDEX:

```python
from src.builder.artifacts.repo import code_health_md

write_text(
    builder.root_dir / "course" / "CODE_HEALTH.md",
    code_health_md(
        builder.course_meta,
        active_entries,
        code_curation=builder._load_code_curation(),
        timeline_blocks=builder._load_timeline_blocks(),
        glossary_terms=builder._load_glossary_terms() if hasattr(builder, "_load_glossary_terms") else None,
    ),
)
```

### 5.3 Verification

- [ ] Build gera `course/CODE_HEALTH.md`
- [ ] Repo sem código: arquivo mostra "0 / 0"
- [ ] Repo com 5 códigos, 3 resumidos, 2 com block: mostra "3/5 (60%)" + "2/3 com aula"
- [ ] Órfãos listados com link arquivo

---

## Phase 6 — Verificação final

### 6.1 Smoke tests

| Cenário | Esperado |
|---------|----------|
| Build sem `gemini_api_key` | Pipeline idêntico ao atual; CODE_HEALTH mostra "0/0 resumidos" |
| Build com key + sem clicar Gerar | `code_curation.json` ausente; CODE_HEALTH "0% cobertura" |
| Clicar Gerar em matéria com 5 códigos + timeline rica | API calls; curation populado; CODE_INDEX agrupa por aula; CRONOGRAMA_DETALHADO mostra códigos por bloco |
| Reprocessar sem mudanças | Cache hit; 0 API calls |
| Deletar 1 entry e reprocessar | Prune remove do `code_curation.json` |
| Modificar 1 entry e reprocessar | Hash diferente; só esse entry chama API |
| Códigos cujos conceitos não casam com nenhum block | Órfãos listados em CODE_HEALTH + CODE_INDEX seção "⚠" |
| Atribuir block manual via UI | Curation atualizado com `block_match_method="manual"`; CODE_INDEX e CRONOGRAMA_DETALHADO refletem |

### 6.2 Anti-pattern grep

```bash
grep -rn "google.generativeai" src/
grep -rn "genai.GenerativeModel" src/
grep -rn "GEMINI_API_KEY" src/ --include="*.py"
```

Tudo deve retornar 0 matches (exceto comentários/docs).

### 6.3 Custo

- 1 matéria 20 códigos → ~$0.028
- Cache hit em reprocess → $0
- Build sem key → 0 overhead

### 6.4 Docs

- `README.md` — nova seção "Resumos de código (opcional, via Gemini)" + "Vinculação código ↔ aula"
- `requirements.txt` — `google-genai` como **opcional** (extras_require ou nota)
- `.mex/AGENTS.md` — registrar nova dependência

---

## Resumo executivo

| Fase | Arquivos novos | Arquivos editados | Linhas | Risco |
|------|---------------|-------------------|--------|-------|
| 1 | `gemini_client.py`, `code_summarization.py` | `theme.py`, `dialogs.py`, `engine.py` | ~500 | Baixo |
| 2 | — | `build_workflow.py`, `incremental_build.py` | ~10 | Baixo |
| 3 | — | `source_importers.py`, `repo.py` (×3), `file_map.py` | ~250 | Médio |
| 4 | `codes_panel.py` | `app.py` | ~280 | Médio |
| 5 | — | `repo.py`, `bootstrap_ops.py` | ~120 | Baixo |
| 6 | — | `README.md`, `requirements.txt` | ~50 | Trivial |

**Total**: 3 arquivos novos, ~10 editados, ~1200 linhas.

**Execução**: cada fase commit isolado. Reverter qualquer fase = `git revert` simples.

**Follow-up registrado**: `plans/material-agnostic-refactor.md` pra expansão pra PDFs/imagens/exercícios depois de code estável.

---

## Phase 7 — Atualização de arquivos de instrução + MEX

**Objetivo**: refletir o sistema de code summarization nos arquivos de instrução para agentes (CLAUDE/GEMINI/AGENTS) e na scaffold MEX (ROUTER, context, patterns) para que futuras sessões saibam que (a) `google-genai` é dependência opcional com import lazy, (b) `code_curation.json` existe, (c) os artifacts CODE_HEALTH.md e CRONOGRAMA_DETALHADO.md fazem parte do repo gerado, (d) há padrão reutilizável para batch jobs com Gemini.

**Não-objetivo**: reescrever os arquivos. Edições cirúrgicas só. Não tocar em pastas `student/`, `exercises/`, `system/` da documentação.

### 7.1 `.mex/AGENTS.md`

Inserir na seção "Non-Negotiables" (após a linha sobre `mcp__code-review-graph`):

```text
- Gemini integration uses `google-genai` (NOT `google-generativeai`). Imports via `from google import genai` and must stay lazy inside method bodies — never at module top level. Anti-patterns to grep: `google.generativeai`, `genai.GenerativeModel`.
- `code_curation.json` is a generated artifact (not source). Treat it like manifest cache: prune stale entries before reads, write atomically.
```

Bump `last_updated` no front-matter.

### 7.2 `.mex/ROUTER.md` — Current Project State

Adicionar em "Working":

```text
- Code summarization via Gemini API (`gemini-2.5-flash`): bundle each code entry, persist summary + concept-based timeline block assignment in `course/code_curation.json`. Lazy: without `gemini_api_key` in config the pipeline is a no-op.
- Generated artifacts add `course/CODE_HEALTH.md` (coverage report) and `course/CRONOGRAMA_DETALHADO.md` (block-by-block render).
```

Bump `last_updated`.

### 7.3 `.mex/context/architecture.md`

**Components table** — adicionar linha:

```text
| Code Summarization (Gemini) | Lazy `google-genai` client + concept-based timeline block matcher. Backbone in `src/builder/core/code_summarization.py` and `src/builder/runtime/gemini_client.py`. |
```

**Integrations table** — adicionar:

```text
| Google Gemini (`gemini-2.5-flash`) | Optional. Generates structured JSON summaries of code bundles consumed by CODE_INDEX, header MD, CRONOGRAMA_DETALHADO, and CODE_HEALTH. |
```

Bump `last_updated`.

### 7.4 `.mex/context/stack.md`

**Runtime Technologies** — adicionar linha:

```text
| `google-genai` | Optional runtime dependency for the code-summarization pipeline. SDK used: `from google import genai` (NOT `google.generativeai`). |
```

Nota: marcar como **opcional** — pipeline degrada graciosamente sem ela.

Bump `last_updated`.

### 7.5 `.mex/context/decisions.md`

Append nova decisão (acima das anteriores, formato igual):

```text
### Code Summarization Uses Gemini at Build Time (Optional Layer)

**Date:** 2026-06-02
**Status:** Active
**Decision:** Code entries can be summarized at build time through `google-genai`'s structured-output mode (`response_schema=CodeSummary`) with a content-hash cache in `course/code_curation.json`. Timeline block assignment is done locally via concept overlap, not via a second LLM call.
**Reasoning:** Code bundles benefit from semantic enrichment (inferred title, role, concepts) for richer downstream artifacts (CODE_INDEX, CRONOGRAMA_DETALHADO, CODE_HEALTH) and tutor grounding. Structured output prevents JSON parsing failures; the local matcher keeps the per-build cost bounded to one LLM call per changed entry. Without an API key the entire layer is bypassed via lazy import.
**Consequences:** Build pipeline must keep the no-key path identical to current behavior. New artifacts must be tolerant of empty `code_curation.json`. Future material types (PDF, exercises) follow the same hash-cache + local-link pattern.
```

Bump `last_updated`.

### 7.6 `.mex/context/repo-output.md`

**Critical Generated Files** — adicionar dentro do bloco code-fence:

```text
course/CRONOGRAMA_DETALHADO.md               # block-by-block render with linked code; only when timeline blocks exist
course/CODE_HEALTH.md                        # auto-generated coverage report for code summaries + block linkage
course/code_curation.json                    # content-hash cache for Gemini summaries; safe to delete
```

**Source Modules That Generate These Files** — adicionar:

```text
| `src/builder/core/code_summarization.py` | Generates Gemini summaries, assigns timeline blocks via concept overlap, prunes stale curation. |
| `src/builder/runtime/gemini_client.py` | Lazy Gemini API client with exponential backoff on 429/5xx. |
```

Atualizar "What Does Not Exist": substituir "No LLM API calls happen at build time" por:

```text
- LLM API calls at build time are confined to the optional code-summarization layer (Gemini). With no API key configured, the build remains fully local.
```

Bump `last_updated`.

### 7.7 `.mex/patterns/INDEX.md`

Adicionar linha na tabela:

```text
| [gemini-code-summarization.md](gemini-code-summarization.md) | Adding a Gemini-backed batch job with hash cache (follow this for future material types: PDFs, exercises) |
```

Bump `last_updated`.

### 7.8 `.mex/patterns/gemini-code-summarization.md` (NOVO, ~150 linhas)

Estrutura:

```markdown
---
name: gemini-code-summarization
description: Pattern for adding a Gemini-backed batch summarization layer with content-hash cache and lazy import
triggers:
  - gemini
  - summarization
  - batch llm
  - structured output
edges:
  - target: ../context/decisions.md
    condition: when revisiting why Gemini is optional
  - target: ../context/architecture.md
    condition: when wiring a new summarization layer
last_updated: 2026-06-02
---

# Gemini Batch Summarization Pattern

Use when adding a build-time Gemini layer that enriches a class of entries (code, PDFs, exercises) with structured summaries, cached by content hash, with lazy degradation when no API key is configured.

## Reference implementation

| Piece | File |
|---|---|
| Lazy client + retry | `src/builder/runtime/gemini_client.py` |
| Engine (schemas, hash, bundle, prune) | `src/builder/core/code_summarization.py` |
| Settings UI | `src/ui/dialogs.py` (Gemini section) |
| Engine wiring | `src/builder/engine.py` (`_load_code_curation`, `_summarize_code_entries`, `_prune_stale_code_curation`) |
| Build pipeline prune call | `src/builder/ops/build_workflow.py` + `incremental_build.py` |
| Renderers consuming curation | `src/builder/core/source_importers.py`, `src/builder/artifacts/repo.py` (CODE_INDEX, CRONOGRAMA_DETALHADO, CODE_HEALTH) |

## Steps for a new entry class (e.g. PDFs)

1. Define a `BaseModel` schema + `SYSTEM_INSTRUCTION` mirroring `CodeSummary`. Concepts list MUST be 3-8 normalized strings — the local block matcher depends on it.
2. Write a `_build_bundle_text(builder, entry_data)` that flattens base + extracted children into <200k chars (clip + marker if larger).
3. Reuse `compute_entry_hash` semantics: hash the bundle text, not the entry dict.
4. Persist in `<class>_curation.json` with shape `{version, entries: {id: {content_hash, model, generated_at, summary}}}`. Atomic write only.
5. Add a `prune_stale_<class>_curation(builder)` that removes ids not in `manifest.json`. Call it from `build_workflow.py` and `incremental_build.py` after manifest reload.
6. Block matching: reuse `assign_code_to_block` if concepts shape is identical; otherwise duplicate the matcher with the same thresholds (`primary=0.4`, `secondary=0.25`, `margin=0.15`) and calibrate later.
7. Lazy import: never `import google.genai` at module top. Always inside method bodies. Anti-pattern grep: `google.generativeai`, `genai.GenerativeModel`.

## Anti-patterns

- Module-level `from google import genai` — breaks no-key flow.
- `response_format={...}` wrapper — Gemini SDK uses `response_mime_type` + `response_schema`.
- Re-hashing entry dicts instead of the bundle text (cache becomes stale on cosmetic edits).
- LLM call inside `assign_*_to_block`: matcher must stay local.
- Logging the API key. Treat as secret.

## Verification

Mirror plan §1.5: anti-pattern grep, `py_compile`, smoke `has_gemini_api_key({})/({key})`, matcher smoke with synthetic blocks.
```

### 7.9 Outros arquivos raiz

- **`README.md`** — já tratado em Phase 6.4 (seção Gemini). Phase 7 não duplica.
- **`CLAUDE.md`** (raiz) — só ponteiro pra `.mex/AGENTS.md`. Sem mudanças.
- **`AGENTS.md`** (raiz) — só MCP graph. Sem mudanças.
- **`GEMINI.md`** (raiz) — contém dump de memory antigo (`<claude-mem-context>`). Sem mudanças nesta fase; substituição é outra task.
- **`ROADMAP.md`** — verificar se há item "code summarization"; se sim, marcar concluído ou mover para "Done". Edit mínimo. Se ausente, no-op.

### 7.10 Verification (Phase 7)

- [ ] `grep -rn "google.generativeai" .mex/` → 0 (só menção válida é dentro de blocos anti-pattern em prosa)
- [ ] `last_updated` bumped em todos os arquivos editados (`.mex/AGENTS.md`, `ROUTER.md`, todos `context/*.md` tocados, `patterns/INDEX.md`)
- [ ] Pattern novo `gemini-code-summarization.md` referenciado em `INDEX.md`
- [ ] `decisions.md` decisão nova fica acima das antigas (append-only log com mais recente no topo da lista cronológica)
- [ ] `repo-output.md` lista os 3 arquivos novos (`CRONOGRAMA_DETALHADO.md`, `CODE_HEALTH.md`, `code_curation.json`)
- [ ] Nenhum trecho de código fonte mudou nesta fase — `git diff src/` vazio
- [ ] `ROADMAP.md` revisto (se tinha item code-summarization, marcado)

### 7.11 Resumo Phase 7

| Arquivo | Operação | Linhas estimadas |
|---|---|---:|
| `.mex/AGENTS.md` | edit (2 bullets) | ~5 |
| `.mex/ROUTER.md` | edit (2 bullets) | ~5 |
| `.mex/context/architecture.md` | edit (2 rows) | ~5 |
| `.mex/context/stack.md` | edit (1 row) | ~3 |
| `.mex/context/decisions.md` | append (1 decision) | ~12 |
| `.mex/context/repo-output.md` | edit (3 inserts) | ~10 |
| `.mex/patterns/INDEX.md` | edit (1 row) | ~2 |
| `.mex/patterns/gemini-code-summarization.md` | NEW | ~150 |
| `ROADMAP.md` | edit conditional | ~3 |

**Total**: 1 arquivo novo, ~8 editados, ~200 linhas. Risco: trivial (doc-only).

**Execução**: pode rodar antes ou depois de Phase 6 — só depende das fases 1-5 já terem definido nomes finais dos artefatos. Como Fase 1 commit já existe, segue executável a qualquer momento. Recomendado executar **depois de Fase 5** para que decisão + repo-output reflitam render real, não promessa.
