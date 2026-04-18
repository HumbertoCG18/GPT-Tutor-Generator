# Card Evidence Temporal Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar `card evidence` como fonte auxiliar de sinais temporais e temáticos para melhorar a atribuição de sessão/bloco/unidade, sem substituir o modelo principal baseado em `timeline_block` e `timeline_session`.

**Architecture:** O sistema continua usando `bloco + sessão` como estrutura pedagógica principal. `Card evidence` entra como metadado opcional extraído do cronograma/HTML/cards importados, persistido no `course/.timeline_index.json` e consumido apenas como reforço no score de matching e como rastreabilidade leve na UI, sem virar prompt caro para o tutor nem dependência obrigatória do Moodle.

**Tech Stack:** Python 3.11, regex, JSON interno (`course/.timeline_index.json`), parsing de texto/HTML já existente, pytest, Tkinter backlog já existente.

---

## Scope Boundary

Este plano cobre:

- extrair evidências de card a partir de texto/HTML já importados
- anexar `card_evidence` a sessões e blocos do `timeline_index`
- usar o título do card como reforço semântico de tópico principal
- usar o card como reforço de sessão/bloco no matcher
- manter rollout via regeneração estrutural em repositórios já processados

Este plano não cobre:

- integração direta com API do Moodle
- criar um novo banco ou artefato separado só para cards
- mostrar cards completos ao tutor
- criar formulário manual obrigatório de card por entry

---

## File Structure

### Arquivos a criar

- `src/builder/card_evidence.py`
  Extratores puros de evidência de card. Responsável por identificar títulos de card, labels de sessão associados e datas presentes em texto linearizado ou HTML já transformado em texto.

- `tests/test_card_evidence.py`
  Testes unitários dos extratores de card evidence.

### Arquivos a modificar

- `src/builder/timeline_signals.py`
  Integrar a leitura de `card evidence` como sinais temporais e temáticos auxiliares de baixo custo.

- `src/builder/timeline_index.py`
  Persistir `card_evidence` em blocos e sessões relevantes no `course/.timeline_index.json`.

- `src/builder/engine.py`
  Ajustar o scorer temporal para considerar `card evidence` como reforço, nunca como substituto de sessão/bloco.

- `src/ui/dialogs.py`
  Opcionalmente mostrar preview curto de card no backlog/manual timeline options quando isso aumentar clareza sem poluir a UI.

- `tests/test_file_map_unit_mapping.py`
  Cobrir o ganho de precisão quando o título do card coincide com o tópico principal da unidade.

- `tests/test_core.py`
  Cobrir serialização estrutural, compatibilidade do backlog e reaplicação em repositórios já existentes.

---

## Runtime Contract

O `course/.timeline_index.json` passa a aceitar enriquecimento assim:

```json
{
  "version": 3,
  "blocks": [
    {
      "id": "bloco-09",
      "period_label": "06/04/2026 a 10/04/2026",
      "topics": ["provas por inducao"],
      "sessions": [
        {
          "id": "bloco-09-sessao-2026-04-08",
          "date": "2026-04-08",
          "kind": "class",
          "label": "Provas por indução",
          "signals": ["provas por inducao"],
          "card_evidence": [
            {
              "title": "Provas por indução",
              "normalized_title": "provas por inducao",
              "date": "",
              "source_kind": "moodle-card-title"
            }
          ]
        }
      ],
      "card_evidence": [
        {
          "title": "Especificações Indutivas e Recursivas",
          "normalized_title": "especificacoes indutivas e recursivas",
          "date": "",
          "source_kind": "moodle-card-title"
        }
      ]
    }
  ]
}
```

Regras:

- `card_evidence` é opcional em bloco e em sessão
- `title` é preservado
- `normalized_title` é usado no scorer
- `source_kind` documenta a origem textual, não a plataforma em si
- a mudança é aditiva; blocos sem card continuam válidos

---

## Matching Contract

`Card evidence` deve reforçar o score apenas nestes casos:

- o título do card coincide fortemente com um tópico/subtópico da unidade
- o título do card coincide fortemente com a label da sessão
- o título do card reforça um bloco quando o cronograma textual está fraco

`Card evidence` não deve:

- vencer uma sessão com data explícita conflitante
- reatribuir sozinho uma entry quando o resto dos sinais for fraco
- substituir `manual_timeline_block_id`

Ordem de decisão continua:

1. override manual
2. sessão explícita
3. bloco
4. reforço por `card evidence`
5. fallback por unidade

Observação:

- o card pode melhorar o score de 2, 3 e 4
- ele não vira um “nível” acima da sessão

---

## UX / Token Contract

`Card evidence` deve ficar barato:

- persistido no JSON interno
- consumido pelo builder e pela UI de backlog/dashboard
- não exposto por padrão ao tutor

No máximo, a UI mostra:

- preview curto do título do card
- nunca o HTML bruto do card
- nunca listas longas de cards na instrução do projeto

---

## Task 1: Criar extratores puros de card evidence

**Files:**
- Create: `src/builder/card_evidence.py`
- Test: `tests/test_card_evidence.py`

- [ ] **Step 1: Escrever o teste de extração de título de card como tópico principal**

```python
from src.builder.card_evidence import extract_card_evidence


def test_extract_card_evidence_reads_card_title_as_topic_signal():
    text = "Card: Especificações Indutivas e Recursivas"

    items = extract_card_evidence(text)

    assert len(items) == 1
    assert items[0]["title"] == "Especificações Indutivas e Recursivas"
    assert items[0]["normalized_title"] == "especificacoes indutivas e recursivas"
    assert items[0]["source_kind"] == "card-title"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_card_evidence.py::test_extract_card_evidence_reads_card_title_as_topic_signal -v`

Expected: FAIL porque o módulo ainda não existe.

- [ ] **Step 3: Escrever o teste para texto linearizado vindo de HTML/Moodle**

```python
from src.builder.card_evidence import extract_card_evidence


def test_extract_card_evidence_reads_linearized_moodle_like_title():
    text = "Tópico: Provas por indução"

    items = extract_card_evidence(text)

    assert len(items) == 1
    assert items[0]["normalized_title"] == "provas por inducao"
```

- [ ] **Step 4: Implementar o módulo mínimo**

Criar `src/builder/card_evidence.py` com:

```python
from __future__ import annotations

import re
import unicodedata


def _normalize_match_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\\s]", " ", text)
    return re.sub(r"\\s+", " ", text).strip()
```

- [ ] **Step 5: Implementar o extrator público**

Expor:

```python
def extract_card_evidence(text: str) -> list[dict[str, str]]:
    ...
```

Padrões mínimos:

- `Card: <título>`
- `Tópico: <título>`
- `Semana ...: <título>` somente quando o resto do texto se parecer com heading/card e não com sessão detalhada

- [ ] **Step 6: Rodar a suíte da task**

Run: `pytest tests/test_card_evidence.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/builder/card_evidence.py tests/test_card_evidence.py
git commit -m "feat: add card evidence extraction helpers"
```

---

## Task 2: Anexar card evidence a blocos e sessões no timeline index

**Files:**
- Modify: `src/builder/timeline_index.py`
- Modify: `src/builder/timeline_signals.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de bloco com card evidence**

```python
from datetime import datetime

from src.builder.engine import _build_timeline_index


def test_build_timeline_index_attaches_card_evidence_to_block():
    candidate_rows = [
        {
            "index": 1,
            "date_dt": datetime(2026, 4, 6),
            "date_text": "06/04/2026",
            "content": "Card: Especificações Indutivas e Recursivas",
        }
    ]

    index = _build_timeline_index(candidate_rows, unit_index=[], content_taxonomy={"version": 1, "course_slug": "teste", "units": []})
    block = index["blocks"][0]

    assert block["card_evidence"]
    assert block["card_evidence"][0]["normalized_title"] == "especificacoes indutivas e recursivas"
```

- [ ] **Step 2: Rodar o teste para verificar que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_build_timeline_index_attaches_card_evidence_to_block -v`

Expected: FAIL porque o índice ainda não serializa `card_evidence`.

- [ ] **Step 3: Integrar o extrator no timeline index**

Em `src/builder/timeline_index.py`, importar:

```python
from src.builder.card_evidence import extract_card_evidence
```

Adicionar helpers:

```python
def _extract_block_card_evidence(rows: List[Dict[str, object]]) -> List[Dict[str, str]]:
    ...


def _attach_card_evidence_to_sessions(
    sessions: List[Dict[str, object]],
    card_items: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    ...
```

- [ ] **Step 4: Persistir a informação no runtime block**

Ao montar `runtime_block`, incluir:

```python
card_evidence = _extract_block_card_evidence(rows)
sessions = _attach_card_evidence_to_sessions(
    _extract_block_sessions(rows, f"bloco-{position:02d}"),
    card_evidence,
)
```

E salvar:

```python
"card_evidence": card_evidence,
"sessions": sessions,
```

- [ ] **Step 5: Subir a versão estrutural do índice**

Ao serializar:

```python
return {"version": 3, "blocks": runtime_blocks}
```

- [ ] **Step 6: Rodar a suíte da task**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/builder/timeline_index.py src/builder/timeline_signals.py tests/test_file_map_unit_mapping.py
git commit -m "feat: attach card evidence to timeline blocks and sessions"
```

---

## Task 3: Usar card evidence como reforço no matcher temporal

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste de reforço por card title**

```python
def test_select_probable_period_for_entry_uses_card_title_as_auxiliary_signal():
    unit = {
        "slug": "unidade-01-metodos-formais",
        "title": "Unidade 1 — Métodos Formais",
    }
    blocks = [
        {
            "id": "bloco-01",
            "period_label": "06/04/2026 a 10/04/2026",
            "unit_slug": "unidade-01-metodos-formais",
            "unit_confidence": 0.9,
            "topics": [],
            "aliases": [],
            "topic_text": "",
            "rows": [{"index": 1, "date_text": "06/04/2026", "content": "Aula"}],
            "sessions": [],
            "card_evidence": [
                {
                    "title": "Provas por indução",
                    "normalized_title": "provas por inducao",
                    "date": "",
                    "source_kind": "card-title",
                }
            ],
        }
    ]
    entry = {
        "title": "Lista Provas por Indução",
        "category": "listas",
        "tags": "",
        "raw_target": "raw/pdfs/listas/lista-inducao.pdf",
    }

    period, confidence, ambiguous, reasons = _select_probable_period_for_entry(
        entry=entry,
        unit=unit,
        candidate_rows=blocks,
        markdown_text="# Provas por indução",
    )

    assert period == "06/04/2026 a 10/04/2026"
    assert confidence > 0
    assert any(reason == "card-evidence" for reason in reasons)
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_file_map_unit_mapping.py::test_select_probable_period_for_entry_uses_card_title_as_auxiliary_signal -v`

Expected: FAIL porque o scorer ainda ignora `card_evidence`.

- [ ] **Step 3: Implementar scorer auxiliar**

Em `src/builder/engine.py`, adicionar:

```python
def _score_entry_against_card_evidence(signals: dict, card_items: List[Dict[str, str]]) -> float:
    ...
```

Regras:

- coincidência forte entre `title/headings/tags` da entry e `normalized_title` do card: bônus moderado
- bônus máximo pequeno, para não ultrapassar sessão explícita

- [ ] **Step 4: Integrar o bônus ao score de bloco e sessão**

Aplicar no scorer:

```python
card_score = _score_entry_against_card_evidence(...)
score += min(card_score, 1.5)
```

E registrar motivo:

```python
reasons.append("card-evidence")
```

Somente quando o bônus realmente influenciar.

- [ ] **Step 5: Rodar a suíte da task**

Run: `pytest tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: use card evidence as auxiliary temporal signal"
```

---

## Task 4: Expor preview leve de card evidence na UI estrutural

**Files:**
- Modify: `src/ui/dialogs.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Escrever o teste de preview no backlog/manual timeline options**

```python
import json


def test_load_timeline_block_options_falls_back_to_card_evidence_preview(tmp_path):
    from src.ui.dialogs import _load_timeline_block_options

    repo = tmp_path / "repo"
    course = repo / "course"
    course.mkdir(parents=True)
    (course / ".timeline_index.json").write_text(
        json.dumps(
            {
                "version": 3,
                "blocks": [
                    {
                        "id": "bloco-01",
                        "period_label": "06/04/2026 a 10/04/2026",
                        "topics": [],
                        "aliases": [],
                        "unit_slug": "unidade-01",
                        "card_evidence": [
                            {
                                "title": "Provas por indução",
                                "normalized_title": "provas por inducao",
                                "date": "",
                                "source_kind": "card-title",
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    options = _load_timeline_block_options(repo)

    assert "Provas por indução" in options[0][0]
```

- [ ] **Step 2: Rodar o teste para verificar que falha**

Run: `pytest tests/test_core.py::test_load_timeline_block_options_falls_back_to_card_evidence_preview -v`

Expected: FAIL porque a UI ainda não conhece `card_evidence`.

- [ ] **Step 3: Implementar preview leve**

Em `src/ui/dialogs.py`, criar helper:

```python
def _timeline_block_card_preview(block: Dict[str, object], limit: int = 2) -> List[str]:
    ...
```

Usar só quando:

- `topics` estiver vazio
- `session_preview` também não ajudar o suficiente

- [ ] **Step 4: Rodar a suíte da task**

Run: `pytest tests/test_core.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py tests/test_core.py
git commit -m "feat: expose lightweight card evidence preview in timeline ui"
```

---

## Task 5: Garantir rollout estrutural em repositórios já processados

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Escrever o teste de regeneração com `card_evidence`**

```python
import json
from pathlib import Path

from src.builder.engine import RepoBuilder
from src.models.core import SubjectProfile


def test_regenerate_pedagogical_files_persists_card_evidence_in_timeline_index(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest = {"entries": []}

    subject = SubjectProfile(
        name="Teste",
        slug="teste",
        repo_root=str(repo),
        teaching_plan="### Unidade 1 - Métodos Formais\n- Provas por indução",
        syllabus=\"\"\"
| Semana | Data | Conteúdo |
|---|---|---|
| 1 | 06/04/2026 a 10/04/2026 | Card: Provas por indução |
\"\"\".strip(),
    )

    builder = RepoBuilder(repo, {"course_name": "Teste", "_repo_root": repo}, [], {}, student_profile=None, subject_profile=subject)
    builder._regenerate_pedagogical_files(manifest)

    payload = json.loads((repo / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
    assert payload["version"] == 3
    assert payload["blocks"][0]["card_evidence"][0]["normalized_title"] == "provas por inducao"
```

- [ ] **Step 2: Rodar o teste para garantir que falha**

Run: `pytest tests/test_core.py::test_regenerate_pedagogical_files_persists_card_evidence_in_timeline_index -v`

Expected: FAIL porque o rollout ainda não grava esse enriquecimento.

- [ ] **Step 3: Confirmar o cutover único**

Não criar novo fluxo. Garantir que:

```python
builder.incremental_build()
```

e:

```python
builder._regenerate_pedagogical_files(manifest)
```

continuem sendo o caminho para reaplicar `card_evidence` em repositórios já existentes.

- [ ] **Step 4: Rodar a suíte da task**

Run: `pytest tests/test_core.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: persist card evidence on structural repository refresh"
```

---

## Task 6: Regressão final

**Files:**
- Test: `tests/test_card_evidence.py`
- Test: `tests/test_timeline_signals.py`
- Test: `tests/test_file_map_unit_mapping.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Rodar os testes focados de evidência e matching**

Run: `pytest tests/test_card_evidence.py tests/test_timeline_signals.py tests/test_file_map_unit_mapping.py -q`

Expected: PASS

- [ ] **Step 2: Rodar regressão do core**

Run: `pytest tests/test_core.py -q`

Expected: PASS

- [ ] **Step 3: Commit final**

```bash
git add tests/test_card_evidence.py tests/test_timeline_signals.py tests/test_file_map_unit_mapping.py tests/test_core.py
git commit -m "test: cover card evidence temporal matching"
```

---

## Design Notes

- `Card evidence` é auxiliar; não é a verdade central do cronograma.
- O título do card costuma ser um ótimo proxy de tópico principal, então ele merece bônus semântico.
- O sistema deve continuar funcionando quando não houver card algum.
- `FILE_MAP.md` e instruções do tutor continuam enxutos.

## Self-Review

Cobertura do pedido:

- plano específico para `card evidence`: coberto
- uso do nome do card como tópico principal da unidade: Tasks 1 e 3
- modularidade para disciplinas diferentes: Tasks 1, 2 e design notes
- preocupação com custo de tokens: UX / Token Contract
- reaplicação em repositórios já processados: Task 5

Checagem de consistência:

- `card evidence` não substitui `sessão`
- o rollout continua via regeneração estrutural
- a UI só usa preview leve, não HTML bruto

