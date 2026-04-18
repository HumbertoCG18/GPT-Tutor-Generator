# FILE_MAP Unit Auto-Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preencher automaticamente as colunas `Unidade` e `Período` do `course/FILE_MAP.md` no build e no reprocessamento, usando heurística modular baseada em `COURSE_MAP`, `SYLLABUS`, títulos, categorias, headings e sinais do markdown, reduzindo a dependência do tutor web para esse mapeamento.

**Architecture:** O sistema deixa de delegar o mapeamento de unidades quase todo para a LLM e passa a gerar esse dado no backend. A abordagem será um matcher modular em camadas: primeiro extrai um índice estruturado de unidades do `COURSE_MAP`/plano de ensino; depois coleta pistas baratas dos próprios entries e markdowns; por fim, calcula score por unidade e grava o slug técnico vencedor no `FILE_MAP.md`, marcando ambiguidades quando necessário. A ligação com o cronograma continua vindo do `SYLLABUS.md`, mas o `FILE_MAP.md` passa a exibir um `Período provável` derivado do subtópico/bloco do cronograma mais compatível dentro da unidade, sem duplicar a tabela inteira do cronograma e sem herdar automaticamente o período completo da unidade quando a evidência for fina.

**Tech Stack:** Python 3.11, pathlib, json, regex, dataclasses, pytest.

---

## Estrutura de Arquivos

### Novos arquivos

- `tests/test_file_map_unit_mapping.py`
  Testes unitários do matcher de unidades, heurísticas de score, sinais temporais e geração final do `FILE_MAP.md`.

### Arquivos a modificar

- `src/builder/engine.py`
  Adicionar extração estruturada de unidades para o `FILE_MAP`, coleta de evidência por entry, score modular de correspondência e escrita da coluna `Unidade`.

- `src/utils/helpers.py`
  Se necessário, consolidar helper técnico de slug de unidade sem acento para reuso consistente entre `COURSE_MAP`, `FILE_MAP` e outros artefatos.

- `README.md`
  Atualizar a descrição da arquitetura para deixar explícito que o `FILE_MAP.md` já sai com `Unidade` preenchida automaticamente no build/reprocessamento.

- `src/ui/dialogs.py`
  Atualizar a Central de Ajuda para explicar que o mapeamento de unidades agora é automático e que a LLM revisa apenas casos ambíguos.

---

### Task 1: Cobrir o comportamento esperado do novo mapeamento de unidades

**Files:**
- Create: `tests/test_file_map_unit_mapping.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Escrever o teste de mapeamento por tópicos da unidade**

```python
from src.builder.engine import _auto_map_entry_unit


def test_auto_map_entry_unit_matches_exercise_to_recursive_definitions():
    units = [
        {
            "title": "Unidade 01 — Métodos Formais",
            "slug": "unidade-01-metodos-formais",
            "topics": [
                "1.2.2. Especificação de Conjuntos Indutivos",
                "1.2.3. Especificação de Funções Recursivas",
            ],
        },
        {
            "title": "Unidade 02 — Verificação de Programas",
            "slug": "unidade-02-verificacao-de-programas",
            "topics": [
                "2.1. Lógica de Hoare",
                "2.1.1. Pré e Pós Condições",
            ],
        },
    ]
    entry = {
        "title": "Exerciciosformalizacaoalgoritmosrecursao",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/exerciciosformalizacaoalgoritmosrecursao.pdf",
    }

    result = _auto_map_entry_unit(entry, units, markdown_text="")

    assert result.slug == "unidade-01-metodos-formais"
    assert result.confidence >= 0.5
```

- [ ] **Step 2: Escrever o teste de mapeamento por heading/markdown em vez de só nome do arquivo**

```python
from src.builder.engine import _auto_map_entry_unit


def test_auto_map_entry_unit_uses_markdown_headings_as_signal():
    units = [
        {
            "title": "Unidade 02 — Verificação de Programas",
            "slug": "unidade-02-verificacao-de-programas",
            "topics": [
                "2.1. Lógica de Hoare",
                "2.1.2. Correção Parcial e Total",
            ],
        },
        {
            "title": "Unidade 03 — Verificação de Modelos",
            "slug": "unidade-03-verificacao-de-modelos",
            "topics": [
                "3.1. Máquinas de Estado",
                "3.2. Lógicas Temporais",
            ],
        },
    ]
    entry = {
        "title": "Exerciciosespecificacao",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
    }
    markdown = "# Exercícios\n\n## Lógica de Hoare\n\n### Pré e Pós Condições\n"

    result = _auto_map_entry_unit(entry, units, markdown_text=markdown)

    assert result.slug == "unidade-02-verificacao-de-programas"
```

- [ ] **Step 3: Escrever o teste de caso ambíguo**

```python
from src.builder.engine import _auto_map_entry_unit


def test_auto_map_entry_unit_marks_ambiguous_when_scores_tie():
    units = [
        {
            "title": "Unidade 01 — Métodos Formais",
            "slug": "unidade-01-metodos-formais",
            "topics": ["Lógica", "Sistemas Formais"],
        },
        {
            "title": "Unidade 02 — Verificação de Programas",
            "slug": "unidade-02-verificacao-de-programas",
            "topics": ["Lógica", "Programas"],
        },
    ]
    entry = {
        "title": "Revisao",
        "category": "material-de-aula",
        "tags": "",
        "raw_target": "raw/pdfs/material-de-aula/revisao.pdf",
    }

    result = _auto_map_entry_unit(entry, units, markdown_text="Revisão geral de lógica.")

    assert result.slug in {
        "unidade-01-metodos-formais",
        "unidade-02-verificacao-de-programas",
    }
    assert result.confidence < 0.5
    assert result.ambiguous is True
```

- [ ] **Step 4: Rodar os testes para garantir que falham**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: FAIL com `ImportError`/funções ausentes.

- [ ] **Step 5: Implementar o modelo mínimo de resultado do matcher**

```python
from dataclasses import dataclass, field
from typing import List


@dataclass
class UnitMatchResult:
    slug: str
    confidence: float
    ambiguous: bool = False
    reasons: List[str] = field(default_factory=list)
```

- [ ] **Step 6: Rodar o teste para garantir que ainda falha no comportamento**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: FAIL por score/lógica ainda não implementados.

- [ ] **Step 7: Commit**

```bash
git add tests/test_file_map_unit_mapping.py src/builder/engine.py
git commit -m "test: cover automatic file map unit matching behavior"
```

### Task 2: Extrair um índice técnico de unidades estável para reuso no FILE_MAP

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de índice de unidades sem acento**

```python
from src.builder.engine import _build_file_map_unit_index


def test_build_file_map_unit_index_normalizes_unit_slugs():
    units = [
        {
            "title": "Unidade 02 — Verificação de Programas",
            "topics": ["2.1. Lógica de Hoare"],
        }
    ]

    index = _build_file_map_unit_index(units)

    assert index[0]["slug"] == "unidade-02-verificacao-de-programas"
    assert "logica de hoare" in index[0]["topic_tokens"]
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_build_file_map_unit_index_normalizes_unit_slugs -q`

Expected: FAIL com função ausente.

- [ ] **Step 3: Implementar a indexação técnica das unidades**

```python
import unicodedata
import re


def _normalize_match_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _build_file_map_unit_index(units: list) -> list:
    indexed = []
    for unit in units or []:
        title = unit.get("title", "")
        slug = slugify(title.replace("—", "-"))
        topics = unit.get("topics", []) or []
        indexed.append({
            "title": title,
            "slug": slug,
            "normalized_title": _normalize_match_text(title),
            "topics": topics,
            "topic_tokens": [_normalize_match_text(topic) for topic in topics],
        })
    return indexed
```

- [ ] **Step 4: Rodar o teste para garantir que passa**

Run: `pytest tests/test_file_map_unit_mapping.py::test_build_file_map_unit_index_normalizes_unit_slugs -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: add normalized unit index for file map auto-mapping"
```

### Task 3: Implementar coleta modular de sinais por entry

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de coleta de sinais do entry**

```python
from src.builder.engine import _collect_entry_unit_signals


def test_collect_entry_unit_signals_uses_title_category_tags_and_markdown():
    entry = {
        "title": "Exerciciosespecificacao",
        "category": "listas",
        "tags": "dafny",
        "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
    }
    markdown = "# Exercícios\n\n## Lógica de Hoare\n\nPré e Pós Condições."

    signals = _collect_entry_unit_signals(entry, markdown)

    assert "exerciciosespecificacao" in signals["title_text"]
    assert "listas" in signals["category_text"]
    assert "dafny" in signals["tags_text"]
    assert "logica de hoare" in signals["markdown_text"]
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_collect_entry_unit_signals_uses_title_category_tags_and_markdown -q`

Expected: FAIL com função ausente.

- [ ] **Step 3: Implementar a coleta dos sinais**

```python
def _collect_entry_unit_signals(entry: dict, markdown_text: str) -> dict:
    return {
        "title_text": _normalize_match_text(entry.get("title", "")),
        "category_text": _normalize_match_text(entry.get("category", "")),
        "tags_text": _normalize_match_text(entry.get("tags", "")),
        "raw_text": _normalize_match_text(entry.get("raw_target", "")),
        "markdown_text": _normalize_match_text(markdown_text),
    }
```

- [ ] **Step 4: Rodar o teste para garantir que passa**

Run: `pytest tests/test_file_map_unit_mapping.py::test_collect_entry_unit_signals_uses_title_category_tags_and_markdown -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: collect modular signals for file map unit inference"
```

### Task 4: Implementar score de correspondência por unidade sem hardcode de nomes

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de score favorecendo tópicos internos**

```python
from src.builder.engine import _score_entry_against_unit


def test_score_entry_against_unit_prefers_topic_overlap():
    unit = {
        "title": "Unidade 02 — Verificação de Programas",
        "slug": "unidade-02-verificacao-de-programas",
        "normalized_title": "unidade 02 verificacao de programas",
        "topics": ["2.1. Lógica de Hoare", "2.1.1. Pré e Pós Condições"],
        "topic_tokens": ["2 1 logica de hoare", "2 1 1 pre e pos condicoes"],
    }
    signals = {
        "title_text": "exercicios especificacao",
        "category_text": "listas",
        "tags_text": "",
        "raw_text": "raw pdfs listas exercicios especificacao pdf",
        "markdown_text": "logica de hoare pre e pos condicoes",
    }

    score = _score_entry_against_unit(signals, unit)

    assert score > 0
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_score_entry_against_unit_prefers_topic_overlap -q`

Expected: FAIL com função ausente.

- [ ] **Step 3: Implementar score modular**

```python
def _score_entry_against_unit(signals: dict, unit: dict) -> float:
    score = 0.0
    title_text = signals["title_text"]
    markdown_text = signals["markdown_text"]

    if unit["normalized_title"] and unit["normalized_title"] in markdown_text:
        score += 2.0

    for topic_text in unit.get("topic_tokens", []):
        if not topic_text:
            continue
        if topic_text in markdown_text:
            score += 3.0
        elif any(token in markdown_text for token in topic_text.split() if len(token) >= 5):
            score += 1.0
        if any(token in title_text for token in topic_text.split() if len(token) >= 6):
            score += 0.5

    if signals["category_text"] in {"listas", "gabaritos"}:
        score += 0.2
    return score
```

- [ ] **Step 4: Implementar `_auto_map_entry_unit(...)`**

```python
def _auto_map_entry_unit(entry: dict, units: list, markdown_text: str) -> UnitMatchResult:
    indexed_units = _build_file_map_unit_index(units)
    signals = _collect_entry_unit_signals(entry, markdown_text)
    scored = [
        (unit, _score_entry_against_unit(signals, unit))
        for unit in indexed_units
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    if not scored:
        return UnitMatchResult(slug="", confidence=0.0, ambiguous=True, reasons=["sem-unidades"])
    winner, winner_score = scored[0]
    runner_up_score = scored[1][1] if len(scored) > 1 else 0.0
    confidence = min(1.0, winner_score / 5.0)
    ambiguous = abs(winner_score - runner_up_score) < 0.75
    return UnitMatchResult(
        slug=winner["slug"],
        confidence=confidence,
        ambiguous=ambiguous,
        reasons=[f"score={winner_score:.2f}"],
    )
```

- [ ] **Step 5: Rodar a suíte do matcher**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: add modular unit scoring for file map entries"
```

### Task 5: Integrar o auto-mapeamento na geração do FILE_MAP

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de `FILE_MAP` já preenchido**

```python
from src.builder.engine import _low_token_file_map_md


def test_low_token_file_map_md_fills_unit_column_from_auto_mapping():
    course_meta = {"course_name": "Métodos Formais"}
    manifest_entries = [
        {
            "id": "exerciciosespecificacao",
            "title": "Exerciciosespecificacao",
            "category": "listas",
            "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
            "base_markdown": "exercises/lists/exerciciosespecificacao.md",
            "_markdown_text_for_tests": "# Exercícios\n\n## Lógica de Hoare\n",
        }
    ]
    course_meta["_unit_index_for_tests"] = [
        {
            "title": "Unidade 02 — Verificação de Programas",
            "topics": ["2.1. Lógica de Hoare"],
        }
    ]

    md = _low_token_file_map_md(course_meta, manifest_entries)

    assert "unidade-02-verificacao-de-programas" in md
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_low_token_file_map_md_fills_unit_column_from_auto_mapping -q`

Expected: FAIL porque a coluna `Unidade` ainda sai vazia.

- [ ] **Step 3: Implementar leitura de markdown e preenchimento da unidade**

```python
def _entry_markdown_text_for_unit_mapping(root_dir: Optional[Path], entry: dict) -> str:
    if "_markdown_text_for_tests" in entry:
        return entry["_markdown_text_for_tests"]
    if not root_dir:
        return ""
    md_rel = (
        entry.get("approved_markdown")
        or entry.get("curated_markdown")
        or entry.get("base_markdown")
        or entry.get("advanced_markdown")
        or ""
    )
    if not md_rel:
        return ""
    md_path = root_dir / md_rel
    if not md_path.exists():
        return ""
    return md_path.read_text(encoding="utf-8", errors="replace")
```

- [ ] **Step 4: Integrar no `file_map_md` / `_low_token_file_map_md`**

```python
unit_index = course_meta.get("_unit_index_for_tests") or _build_file_map_unit_index(
    _parse_units_from_teaching_plan(getattr(subject_profile, "teaching_plan", ""))
)
markdown_text = _entry_markdown_text_for_unit_mapping(course_meta.get("_repo_root"), entry)
match = _auto_map_entry_unit(entry, unit_index, markdown_text)
unit = match.slug if match.slug else ""
```

- [ ] **Step 5: Rodar o teste para garantir que passa**

Run: `pytest tests/test_file_map_unit_mapping.py::test_low_token_file_map_md_fills_unit_column_from_auto_mapping -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: auto-fill file map unit column during build"
```

### Task 6: Usar a timeline do cronograma como sinal auxiliar sem hardcode

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de apoio temporal**

```python
from src.builder.engine import _score_entry_against_unit


def test_score_entry_against_unit_uses_timeline_terms_as_support():
    unit = {
        "title": "Unidade 01 — Métodos Formais",
        "slug": "unidade-01-metodos-formais",
        "normalized_title": "unidade 01 metodos formais",
        "topics": ["Definições indutivas", "Funções recursivas"],
        "topic_tokens": ["definicoes indutivas", "funcoes recursivas"],
    }
    signals = {
        "title_text": "exercicios formalizacao algoritmos recursao",
        "category_text": "listas",
        "tags_text": "",
        "raw_text": "",
        "markdown_text": "definicoes indutivas e recursivas sobre listas e arvores",
    }

    score = _score_entry_against_unit(signals, unit)

    assert score >= 2.0
```

- [ ] **Step 2: Rodar o teste para garantir que passa só depois do ajuste**

Run: `pytest tests/test_file_map_unit_mapping.py::test_score_entry_against_unit_uses_timeline_terms_as_support -q`

Expected: FAIL ou score insuficiente.

- [ ] **Step 3: Ajustar o score para token distintivo**

```python
def _distinctive_tokens(unit: dict) -> set[str]:
    tokens = set()
    for text in [unit.get("normalized_title", "")] + list(unit.get("topic_tokens", [])):
        for token in text.split():
            if len(token) >= 5 and not token.isdigit():
                tokens.add(token)
    return tokens
```

- [ ] **Step 4: Incorporar os tokens distintivos no score**

```python
distinctive = _distinctive_tokens(unit)
for token in distinctive:
    if token in markdown_text:
        score += 0.35
    if token in title_text:
        score += 0.2
```

- [ ] **Step 5: Rodar a suíte do arquivo**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: use temporal-topic signals to stabilize file map unit mapping"
```

### Task 7: Marcar ambiguidades sem quebrar o fluxo low-token

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de anotação compacta de ambiguidade**

```python
from src.builder.engine import _format_file_map_unit_cell


def test_format_file_map_unit_cell_marks_ambiguous_result():
    text = _format_file_map_unit_cell(
        slug="unidade-01-metodos-formais",
        confidence=0.32,
        ambiguous=True,
    )

    assert "unidade-01-metodos-formais" in text
    assert "ambíguo" in text
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_format_file_map_unit_cell_marks_ambiguous_result -q`

Expected: FAIL com função ausente.

- [ ] **Step 3: Implementar a formatação compacta**

```python
def _format_file_map_unit_cell(slug: str, confidence: float, ambiguous: bool) -> str:
    if not slug:
        return ""
    if ambiguous:
        return f"{slug} _(ambíguo)_"
    if confidence < 0.45:
        return f"{slug} _(baixa confiança)_"
    return slug
```

- [ ] **Step 4: Integrar a formatação na coluna `Unidade`**

```python
unit_cell = _format_file_map_unit_cell(
    match.slug,
    match.confidence,
    match.ambiguous,
)
```

- [ ] **Step 5: Rodar o teste para garantir que passa**

Run: `pytest tests/test_file_map_unit_mapping.py::test_format_file_map_unit_cell_marks_ambiguous_result -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: mark ambiguous automatic unit mappings compactly"
```

### Task 8: Atualizar documentação e ajuda para o novo comportamento

**Files:**
- Modify: `README.md`
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Atualizar README**

```md
## Mapeamento automático de unidades

O `course/FILE_MAP.md` agora é gerado com a coluna `Unidade` preenchida automaticamente
durante o build e no `Reprocessar Repositório`.

O mapeamento usa:
- título e categoria do arquivo
- markdown processado da entry
- tópicos do `COURSE_MAP.md`
- sinais do `SYLLABUS.md`

Casos ambíguos são marcados no próprio `FILE_MAP.md` para revisão posterior.
```

- [ ] **Step 2: Atualizar a Central de Ajuda**

```python
("FILE_MAP automático", """O FILE_MAP agora sai com a coluna Unidade preenchida automaticamente.

O app cruza:
  • tópicos do COURSE_MAP
  • timeline do SYLLABUS
  • nome/categoria do arquivo
  • headings e conteúdo do markdown da própria entry

Casos ambíguos são marcados no FILE_MAP para revisão leve, em vez de depender de
uma sessão inicial longa com a LLM.""")
```

- [ ] **Step 3: Rodar uma suíte curta de regressão**

Run: `pytest tests/test_file_map_unit_mapping.py tests/test_core.py -q`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add README.md src/ui/dialogs.py tests/test_file_map_unit_mapping.py tests/test_core.py
git commit -m "docs: explain automatic file map unit mapping"
```

### Task 9: Validar reprocessamento em um repositório real e fechar a arquitetura

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de reprocessamento aplicando unidade**

```python
from pathlib import Path
import json

from src.builder.engine import RepoBuilder


def test_regenerate_pedagogical_files_rewrites_file_map_with_units(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "content" / "curated").mkdir(parents=True)
    md = repo / "content" / "curated" / "exerciciosespecificacao.md"
    md.write_text("# Exercícios\n\n## Lógica de Hoare\n", encoding="utf-8")

    manifest = {
        "generated_at": "2026-04-01T00:00:00",
        "entries": [
            {
                "id": "exerciciosespecificacao",
                "title": "Exerciciosespecificacao",
                "category": "listas",
                "base_markdown": "content/curated/exerciciosespecificacao.md",
                "raw_target": "raw/pdfs/listas/exerciciosespecificacao.pdf",
            }
        ],
    }

    builder = RepoBuilder.__new__(RepoBuilder)
    builder.root_dir = repo
    builder.course_meta = {"course_name": "Métodos Formais"}
    builder.subject_profile = None
    builder.student_profile = None

    builder._regenerate_pedagogical_files(manifest)

    file_map = (repo / "course" / "FILE_MAP.md").read_text(encoding="utf-8")
    assert "Unidade" in file_map
```

- [ ] **Step 2: Rodar o teste para garantir integração**

Run: `pytest tests/test_file_map_unit_mapping.py::test_regenerate_pedagogical_files_rewrites_file_map_with_units -q`

Expected: PASS

- [ ] **Step 3: Fazer uma revisão rápida de consistência**

Checklist:
- `COURSE_MAP.md` e `FILE_MAP.md` usam slugs técnicos sem acento
- a coluna `Unidade` não nasce mais vazia por padrão
- casos sem evidência suficiente aparecem como ambíguos ou baixa confiança
- o tutor web não precisa mais mapear toda a disciplina do zero

- [ ] **Step 4: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: auto-map file map units during build and reprocess"
```
