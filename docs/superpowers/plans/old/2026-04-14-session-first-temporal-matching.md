# Session-First Temporal Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Melhorar a precisão da atribuição de unidade e bloco temporal usando sessões internas do cronograma antes do bloco agregado, sem exigir input manual novo por entry, e reaplicar esse cálculo nos repositórios já processados.

**Architecture:** O cronograma deixa de ser apenas uma sequência de blocos agregados e passa a expor também `sessions` normalizadas por bloco quando houver datas internas, labels de aula ou atividades assíncronas. O matcher de período da entry passa a pontuar primeiro contra sessões, depois contra blocos, usando sinais temporais extraídos automaticamente do cronograma, do HTML importado, do markdown da entry, do título e do nome do arquivo; o rollout em repositórios já existentes acontece pelo caminho de `refresh_repo` e `_regenerate_pedagogical_files(...)`, sem rebuild completo do conteúdo bruto.

**Tech Stack:** Python 3.11, JSON interno (`course/.timeline_index.json`), markdown parsing leve, regex, pathlib, tkinter workflow já existente, pytest.

---

## Scope Boundary

Este plano cobre:

- enriquecer `course/.timeline_index.json` com `sessions`
- extrair sinais temporais automaticamente das entries
- mudar o matcher para `session-first`, `block-second`
- manter fallback completo para disciplinas sem datas internas
- reaplicar a nova lógica nos repositórios já processados via reprocessamento estrutural

Este plano não cobre:

- novo formulário obrigatório para datas
- edição manual de sessão no diálogo de entrada
- integração com Moodle por API
- reprocessamento OCR/PDF completo de todos os arquivos antigos

---

## File Structure

### Arquivos a criar

- `src/builder/timeline_signals.py`
  Módulo puro de extração de sinais temporais. Responsável por detectar datas únicas, ranges, labels de sessão, atividades assíncronas e texto temporal útil a partir de strings, markdown e nomes de arquivo.

- `tests/test_timeline_signals.py`
  Testes unitários do extrator de sinais temporais.

### Arquivos a modificar

- `src/builder/timeline_index.py`
  Enriquecer o runtime model do cronograma com `sessions`, preservar blocos existentes e serializar o novo formato sem quebrar consumidores legados.

- `src/builder/engine.py`
  Fazer `_build_file_map_timeline_context_from_course(...)` consumir o novo índice, trocar a seleção de período para usar sessão antes de bloco e garantir que `_regenerate_pedagogical_files(...)` continue sendo o ponto único de reaplicação estrutural.

- `src/ui/dialogs.py`
  Ajustar apenas a leitura do status temporal no backlog para exibir informações mais precisas quando houver `sessions`, sem colocar a lógica principal aqui.

- `tests/test_file_map_unit_mapping.py`
  Cobrir o novo matcher temporal com cronograma detalhado por sessão, HTML com datas e fallback para cadeiras sem detalhamento.

- `tests/test_core.py`
  Cobrir a regeneração estrutural, compatibilidade do `timeline_index`, backlog e reprocessamento.

### Arquivos existentes que permanecem ponto de rollout

- `src/ui/app.py`
  Já possui `refresh_repo` e `_reprocess_repo`; não deve receber o algoritmo principal, só continuar disparando a regeneração estrutural.

- `src/models/task_queue.py`
  Já modela `refresh_repo`; não precisa de novo tipo de task para esta rodada.

---

## Runtime Contract

O `course/.timeline_index.json` passa a aceitar:

```json
{
  "version": 2,
  "blocks": [
    {
      "id": "bloco-08",
      "period_label": "30/03/2026 a 03/04/2026",
      "period_start": "2026-03-30",
      "period_end": "2026-04-03",
      "unit_slug": "unidade-02-verificacao-de-programas",
      "topics": ["especificacoes recursivas provas por inducao"],
      "aliases": ["recursivas", "inducao"],
      "topic_text": "especificacoes recursivas provas por inducao leituras recomendadas",
      "sessions": [
        {
          "id": "bloco-08-sessao-2026-03-30",
          "date": "2026-03-30",
          "kind": "class",
          "label": "Especificações recursivas e provas por indução",
          "signals": ["especificacoes recursivas", "provas por inducao"]
        },
        {
          "id": "bloco-08-sessao-async-01",
          "date": "",
          "kind": "async",
          "label": "Complementar os estudos com as leituras recomendadas",
          "signals": ["atividade assincrona", "leituras recomendadas"]
        },
        {
          "id": "bloco-08-sessao-2026-04-01",
          "date": "2026-04-01",
          "kind": "class",
          "label": "Especificações recursivas e provas por indução",
          "signals": ["especificacoes recursivas", "provas por inducao"]
        }
      ]
    }
  ]
}
```

Regras:

- `version` sobe para `2`
- `blocks` continua existindo
- `sessions` é opcional por bloco
- disciplinas sem detalhamento interno continuam válidas com `sessions=[]`
- consumidores antigos que só leem `blocks` não quebram

---

## Matching Contract

A escolha temporal da entry deve seguir esta ordem:

1. `manual_timeline_block_id`
2. sessão explícita compatível
3. bloco compatível
4. unidade + bloco por fallback
5. sem período, se tudo for ambíguo

Sinais que entram no score:

- datas explícitas detectadas no texto da entry
- range explícito detectado na entry
- tokens da sessão
- tokens do bloco
- unidade inferida
- headings do markdown
- lead text
- título
- nome do arquivo
- categoria da entry

Sem input manual novo:

- o sistema tenta extrair tudo automaticamente
- override manual continua opcional e restrito ao que já existe

---

## Rollout Contract For Existing Repositories

O rollout nos repositórios já processados deve ocorrer por regeneração estrutural, não por rebuild bruto:

- carregar `manifest.json`
- regenerar `course/.timeline_index.json`
- regenerar `course/FILE_MAP.md`
- atualizar backlog/status

Isso deve acontecer por:

- botão manual `Reprocessar Repositório`
- task persistente `refresh_repo`
- qualquer fluxo que já chame `_regenerate_pedagogical_files(...)`

Não deve ser necessário:

- reextrair OCR
- reprocessar imagens
- refazer markdown base/advanced

---

## Task 1: Criar extratores temporais puros e independentes da UI

**Files:**
- Create: `src/builder/timeline_signals.py`
- Test: `tests/test_timeline_signals.py`

- [ ] **Step 1: Escrever o teste de extração de datas internas de sessão**

```python
from src.builder.timeline_signals import extract_timeline_session_signals


def test_extract_timeline_session_signals_reads_inline_class_dates():
    text = """
    Semana 30/03/2026 a 03/04/2026:
    (30/03/2026): Especificações recursivas e provas por indução;
    (atividade assíncrona): Complementar os estudos com as leituras recomendadas.
    (01/04/2026): Especificações recursivas e provas por indução;
    """.strip()

    sessions = extract_timeline_session_signals(text)

    assert [item["kind"] for item in sessions] == ["class", "async", "class"]
    assert sessions[0]["date"] == "2026-03-30"
    assert sessions[1]["date"] == ""
    assert "leituras recomendadas" in sessions[1]["signals"]
    assert sessions[2]["date"] == "2026-04-01"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_timeline_signals.py::test_extract_timeline_session_signals_reads_inline_class_dates -v`

Expected: FAIL porque o módulo `timeline_signals.py` ainda não existe.

- [ ] **Step 3: Escrever o teste de extração de range semanal**

```python
from src.builder.timeline_signals import extract_date_range_signal


def test_extract_date_range_signal_reads_week_range():
    signal = extract_date_range_signal("Semana 30/03/2026 a 03/04/2026")

    assert signal == {
        "start": "2026-03-30",
        "end": "2026-04-03",
        "label": "30/03/2026 a 03/04/2026",
    }
```

- [ ] **Step 4: Implementar o módulo mínimo**

Criar `src/builder/timeline_signals.py` com:

```python
from __future__ import annotations

import re
import unicodedata
from datetime import datetime


def _normalize_match_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\\s]", " ", text)
    return re.sub(r"\\s+", " ", text).strip()


def _parse_date(raw: str) -> str:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""
```

- [ ] **Step 5: Implementar os extratores públicos**

Expor:

```python
def extract_date_range_signal(text: str) -> dict[str, str]:
    ...


def extract_timeline_session_signals(text: str) -> list[dict[str, object]]:
    ...
```

Regras mínimas:

- reconhecer `Semana dd/mm/yyyy a dd/mm/yyyy`
- reconhecer linhas como `(30/03/2026): Texto`
- reconhecer linhas como `(atividade assíncrona): Texto`
- normalizar `signals` com tokens/phrases úteis

- [ ] **Step 6: Rodar a suíte da task**

Run: `pytest tests/test_timeline_signals.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/builder/timeline_signals.py tests/test_timeline_signals.py
git commit -m "feat: add automatic temporal signal extraction"
```

---

## Task 2: Enriquecer o `timeline_index` com sessões internas

**Files:**
- Modify: `src/builder/timeline_index.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de serialização de sessões**

```python
from datetime import datetime

from src.builder.engine import _build_timeline_index


def test_build_timeline_index_serializes_sessions_inside_block():
    candidate_rows = [
        {
            "index": 1,
            "date_dt": datetime(2026, 3, 30),
            "date_text": "30/03/2026 a 03/04/2026",
            "content": "Semana 30/03/2026 a 03/04/2026: (30/03/2026): Especificações recursivas e provas por indução; (atividade assíncrona): Complementar os estudos com as leituras recomendadas. (01/04/2026): Especificações recursivas e provas por indução;",
        }
    ]

    index = _build_timeline_index(candidate_rows, unit_index=[], content_taxonomy={"version": 1, "course_slug": "teste", "units": []})
    block = index["blocks"][0]

    assert block["sessions"]
    assert [item["kind"] for item in block["sessions"]] == ["class", "async", "class"]
    assert block["sessions"][0]["date"] == "2026-03-30"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_build_timeline_index_serializes_sessions_inside_block -v`

Expected: FAIL porque o índice atual não gera `sessions`.

- [ ] **Step 3: Importar os extratores em `timeline_index.py`**

Adicionar:

```python
from src.builder.timeline_signals import extract_date_range_signal, extract_timeline_session_signals
```

- [ ] **Step 4: Implementar helper local de sessões por bloco**

Adicionar em `src/builder/timeline_index.py`:

```python
def _extract_block_sessions(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    sessions: List[Dict[str, object]] = []
    for row in rows or []:
        text = str(row.get("content", "") or "")
        sessions.extend(extract_timeline_session_signals(text))
    deduped: List[Dict[str, object]] = []
    seen = set()
    for idx, item in enumerate(sessions, start=1):
        key = (str(item.get("date", "")), str(item.get("kind", "")), str(item.get("label", "")))
        if key in seen:
            continue
        deduped.append({
            "id": f"sessao-{idx:02d}",
            **item,
        })
        seen.add(key)
    return deduped
```

- [ ] **Step 5: Persistir `sessions` em cada bloco**

Ao montar cada bloco em `_build_timeline_index(...)`, incluir:

```python
sessions = _extract_block_sessions(current_rows)
runtime_block = {
    ...,
    "sessions": sessions,
}
```

E subir a versão do índice:

```python
return {"version": 2, "blocks": runtime_blocks}
```

- [ ] **Step 6: Rodar a suíte da task**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/builder/timeline_index.py tests/test_file_map_unit_mapping.py
git commit -m "feat: enrich timeline index with session-level schedule data"
```

---

## Task 3: Extrair sinais temporais das entries e usar sessão antes de bloco

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `src/builder/timeline_signals.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste do match por sessão textual**

```python
from pathlib import Path

from src.builder.engine import file_map_md
from src.models.core import SubjectProfile


def test_file_map_md_prefers_session_with_matching_vocab_inside_week_block(tmp_path: Path):
    repo = tmp_path / "repo"
    md_dir = repo / "exercises" / "lists"
    md_dir.mkdir(parents=True)
    (md_dir / "lista-recursao.md").write_text(
        "# Lista Recursão\n\n## Especificações recursivas\n\n## Provas por indução\n",
        encoding="utf-8",
    )

    subject_profile = SubjectProfile(
        teaching_plan="### Unidade 2 - Verificacao de Programas\n- Especificações recursivas\n- Provas por indução",
        syllabus=\"\"\"
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 30/03/2026 a 03/04/2026 | Semana 30/03/2026 a 03/04/2026: (30/03/2026): Especificações recursivas e provas por indução; (atividade assíncrona): Complementar os estudos com as leituras recomendadas. (01/04/2026): Especificações recursivas e provas por indução; |
| 2 | 06/04/2026 a 10/04/2026 | Tipos algébricos e listas |
\"\"\".strip(),
    )

    entries = [
        {
            "title": "Lista Recursão",
            "category": "listas",
            "tags": "",
            "base_markdown": "exercises/lists/lista-recursao.md",
            "raw_target": "raw/pdfs/listas/lista-recursao.pdf",
        }
    ]

    result = file_map_md({"course_name": "Teste", "_repo_root": repo}, entries, subject_profile)

    assert "30/03/2026 a 03/04/2026" in result
    assert "06/04/2026 a 10/04/2026" not in result
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_file_map_md_prefers_session_with_matching_vocab_inside_week_block -v`

Expected: FAIL no matcher atual ou passar apenas por coincidência fraca; o objetivo é fixar o comportamento deliberadamente.

- [ ] **Step 3: Criar um coletor de sinais temporais da entry**

Em `src/builder/timeline_signals.py`, expor:

```python
def collect_entry_temporal_signals(
    *,
    title: str,
    file_name: str,
    markdown_text: str,
    category: str,
) -> dict[str, object]:
    return {
        "single_dates": ...,
        "date_ranges": ...,
        "temporal_text": ...,
        "temporal_tokens": ...,
        "category": category,
    }
```

- [ ] **Step 4: Integrar o novo coletor ao scorer temporal**

Em `src/builder/engine.py`, ajustar a seleção de período para usar:

```python
entry_temporal = collect_entry_temporal_signals(
    title=str(entry.get("title", "") or ""),
    file_name=Path(str(entry.get("raw_target") or entry.get("source_path") or "")).name,
    markdown_text=markdown_text,
    category=str(entry.get("category", "") or ""),
)
```

E adicionar scorer:

```python
def _score_entry_against_timeline_session(entry_temporal: dict, session: dict, preferred_unit_slug: str = "") -> float:
    ...
```

Regras mínimas:

- mesma data explícita: `+4.0`
- range que contém a data da sessão: `+2.0`
- overlap lexical forte com `session["signals"]`: `+2.5`
- categoria `listas` com `kind == "async"` ganha pouco, não alto
- sessão da unidade preferida ganha bônus pequeno

- [ ] **Step 5: Fazer `session-first`, `block-second`**

Na lógica que escolhe período/bloco, usar:

```python
best_session = ...
if best_session_score >= 3.0:
    return best_session_parent_block
best_block = ...
return best_block_or_empty
```

Sem remover o caminho antigo de bloco; ele vira fallback.

- [ ] **Step 6: Rodar a suíte da task**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/builder/engine.py src/builder/timeline_signals.py tests/test_file_map_unit_mapping.py
git commit -m "feat: prefer schedule sessions over aggregate blocks for period matching"
```

---

## Task 4: Cobrir casos sem datas internas e HTML com datas em `<a>`

**Files:**
- Modify: `src/builder/timeline_signals.py`
- Test: `tests/test_timeline_signals.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de fallback para disciplina sem sessões**

```python
from src.builder.timeline_signals import extract_timeline_session_signals


def test_extract_timeline_session_signals_returns_empty_for_plain_week_block():
    text = "Lógica de Hoare e verificação parcial de programas"

    assert extract_timeline_session_signals(text) == []
```

- [ ] **Step 2: Escrever o teste para texto vindo de HTML com data no link**

```python
from src.builder.timeline_signals import extract_timeline_session_signals


def test_extract_timeline_session_signals_reads_date_even_when_text_came_from_anchor():
    text = "Aula 30/03/2026 Especificações recursivas e provas por indução"

    sessions = extract_timeline_session_signals(text)

    assert sessions[0]["date"] == "2026-03-30"
    assert "especificacoes recursivas" in sessions[0]["signals"]
```

- [ ] **Step 3: Rodar os testes para garantir que falham onde faltarem regras**

Run: `pytest tests/test_timeline_signals.py -q`

Expected: FAIL em pelo menos um padrão novo antes do ajuste.

- [ ] **Step 4: Expandir os padrões de extração**

Adicionar suporte em `extract_timeline_session_signals(...)` para:

- `Aula 30/03/2026 ...`
- `30/03/2026 - ...`
- `30/03/2026: ...`
- texto linearizado vindo de HTML já limpo

E manter:

```python
if not sessions:
    return []
```

para que cadeiras sem detalhamento continuem no fallback de bloco.

- [ ] **Step 5: Rodar a suíte da task**

Run: `pytest tests/test_timeline_signals.py tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/timeline_signals.py tests/test_timeline_signals.py tests/test_file_map_unit_mapping.py
git commit -m "test: cover session extraction from plain text and html-derived schedule text"
```

---

## Task 5: Ajustar o backlog para ler o índice novo sem mover a lógica principal para a UI

**Files:**
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Escrever o teste de backlog usando bloco com sessões**

```python
import json


def test_resolves_backlog_timeline_status_from_timeline_index_with_sessions(tmp_path):
    from src.ui.dialogs import _resolve_backlog_timeline_status

    repo = tmp_path / "repo"
    course = repo / "course"
    course.mkdir(parents=True)
    (course / "FILE_MAP.md").write_text(
        '''# FILE_MAP

| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Seções | Unidade | Confiança | Período |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Lista Recursão | listas | praticar | alta | `exercises/lists/lista-recursao.md` | Recursão | unidade-02 | Alta | 30/03/2026 a 03/04/2026 |
''',
        encoding="utf-8",
    )
    (course / ".timeline_index.json").write_text(
        json.dumps(
            {
                "version": 2,
                "blocks": [
                    {
                        "id": "bloco-08",
                        "period_label": "30/03/2026 a 03/04/2026",
                        "unit_slug": "unidade-02",
                        "topics": ["especificacoes recursivas provas por inducao"],
                        "aliases": ["recursao", "inducao"],
                        "sessions": [
                            {
                                "id": "sessao-01",
                                "date": "2026-03-30",
                                "kind": "class",
                                "label": "Especificações recursivas e provas por indução",
                                "signals": ["especificacoes recursivas", "provas por inducao"],
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    status = _resolve_backlog_timeline_status({"title": "Lista Recursão", "category": "listas"}, repo)

    assert status["block"] == "bloco-08"
    assert "inducao" in status["aliases"]
```

- [ ] **Step 2: Rodar o teste para garantir que falha se houver dependência implícita do formato antigo**

Run: `pytest tests/test_core.py::test_resolves_backlog_timeline_status_from_timeline_index_with_sessions -v`

Expected: FAIL se a UI não tolerar o novo índice ou ignorar o bloco corretamente.

- [ ] **Step 3: Ajustar a leitura do backlog sem duplicar o matcher**

Em `src/ui/dialogs.py`, manter `_resolve_backlog_timeline_status(...)` como consumidor do JSON serializado, apenas aceitando:

```python
sessions = list(block.get("sessions") or [])
```

e, quando existirem sessões, complementar `note` ou `topics` sem recalcular a escolha do bloco ali.

- [ ] **Step 4: Rodar a suíte da task**

Run: `pytest tests/test_core.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py tests/test_core.py
git commit -m "refactor: keep backlog compatible with session-aware timeline index"
```

---

## Task 6: Garantir rollout automático para repositórios já processados

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Escrever o teste de regeneração estrutural com índice versão 2**

```python
import json
from pathlib import Path

from src.builder.engine import RepoBuilder
from src.models.core import SubjectProfile


def test_regenerate_pedagogical_files_rewrites_timeline_index_with_sessions(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest = {
        "entries": [
            {
                "title": "Lista Recursão",
                "category": "listas",
                "base_markdown": "exercises/lists/lista-recursao.md",
                "raw_target": "raw/pdfs/listas/lista-recursao.pdf",
            }
        ]
    }
    (repo / "exercises" / "lists").mkdir(parents=True)
    (repo / "exercises" / "lists" / "lista-recursao.md").write_text(
        "# Lista Recursão\n\n## Especificações recursivas\n",
        encoding="utf-8",
    )

    subject = SubjectProfile(
        name="Teste",
        slug="teste",
        repo_root=str(repo),
        teaching_plan="### Unidade 2 - Verificacao de Programas\n- Especificações recursivas",
        syllabus=\"\"\"
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 30/03/2026 a 03/04/2026 | Semana 30/03/2026 a 03/04/2026: (30/03/2026): Especificações recursivas e provas por indução; |
\"\"\".strip(),
    )

    builder = RepoBuilder(repo, {"course_name": "Teste", "_repo_root": repo}, None, subject)
    builder._regenerate_pedagogical_files(manifest)

    timeline_path = repo / "course" / ".timeline_index.json"
    payload = json.loads(timeline_path.read_text(encoding="utf-8"))

    assert payload["version"] == 2
    assert payload["blocks"][0]["sessions"][0]["date"] == "2026-03-30"
```

- [ ] **Step 2: Rodar o teste para garantir que falha antes do ajuste final**

Run: `pytest tests/test_core.py::test_regenerate_pedagogical_files_rewrites_timeline_index_with_sessions -v`

Expected: FAIL porque a regeneração ainda escreve a versão antiga do índice.

- [ ] **Step 3: Garantir que `_regenerate_pedagogical_files(...)` continue sendo o cutover único**

Em `src/builder/engine.py`, manter:

```python
timeline_context = _build_file_map_timeline_context_from_course(...)
_write_internal_timeline_index(self.root_dir, timeline_context.get("timeline_index", _empty_timeline_index()))
write_text(self.root_dir / "course" / "FILE_MAP.md", file_map_md(...))
```

Sem criar caminho paralelo. O rollout dos repositórios existentes acontece ao disparar:

```python
refresh_repo
```

ou:

```python
_reprocess_repo()
```

- [ ] **Step 4: Acrescentar um teste do fluxo `refresh_repo` não exigir rebuild bruto**

```python
def test_refresh_repo_reapplies_structural_timeline_matching_without_raw_rebuild(monkeypatch):
    from src.ui.app import App

    called = []

    def _fake_refresh(*args, **kwargs):
        called.append("refresh")

    monkeypatch.setattr(App, "_reprocess_repo", _fake_refresh)

    assert callable(_fake_refresh)
```

Implementação esperada desta etapa: se esse teste ficar artificial para o nível atual da suíte, substituí-lo por um teste de integração sobre `RepoBuilder._regenerate_pedagogical_files(...)` e o task `refresh_repo` já serializado em `RepoTask`. O importante é fixar que o rollout usa o caminho estrutural existente, não um novo fluxo manual.

- [ ] **Step 5: Rodar a suíte da task**

Run: `pytest tests/test_core.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: reapply session-aware timeline matching on repository refresh"
```

---

## Task 7: Regressão final da rodada

**Files:**
- Test: `tests/test_timeline_signals.py`
- Test: `tests/test_file_map_unit_mapping.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Rodar os testes focados de sinais e timeline**

Run: `pytest tests/test_timeline_signals.py tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 2: Rodar regressão do core**

Run: `pytest tests/test_core.py -q`

Expected: PASS

- [ ] **Step 3: Rodar regressão curta do dashboard/backlog**

Run: `pytest tests/test_repo_dashboard.py -q`

Expected: PASS

- [ ] **Step 4: Commit final**

```bash
git add tests/test_timeline_signals.py tests/test_file_map_unit_mapping.py tests/test_core.py
git commit -m "test: cover session-first temporal matching rollout"
```

---

## Migration Notes

- Não criar novo diálogo obrigatório de data para `FileEntry`.
- Não pedir input manual na entrada de arquivos nesta rodada.
- Overrides manuais já existentes continuam válidos:
  - `manual_unit_slug`
  - `manual_timeline_block_id`
- Se no futuro surgir necessidade real de override por sessão, isso deve ser um plano separado, só depois de medir quantos casos permanecem ambíguos.

## Self-Review

Cobertura do pedido:

- melhorar precisão da atribuição temporal: Tasks 1, 2 e 3
- manter modular para disciplinas diferentes: Tasks 1 e 4
- suportar cronograma com datas internas, texto livre e HTML linearizado: Task 4
- não depender de input manual novo: contrato e migration notes
- reaplicar em repositórios já criados/processados: Task 6

Verificação de consistência:

- o plano mantém o cutover em `_regenerate_pedagogical_files(...)`
- `timeline_signals.py` concentra a extração temporal, evitando espalhar regex na UI
- `timeline_index.py` enriquece o artefato estrutural sem quebrar o formato base de `blocks`

