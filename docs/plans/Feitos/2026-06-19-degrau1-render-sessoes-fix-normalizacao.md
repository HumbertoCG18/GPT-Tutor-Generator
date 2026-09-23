# Degrau 1 — Render dia-a-dia (sessões) + Fix de normalização da chave de card — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar cada sessão de aula sob seu bloco no `CRONOGRAMA_DETALHADO.md` (de-opacar blocos over-merged) e corrigir o bug de match case/acento da chave de join do card — duas mudanças cirúrgicas, decoupled, sem schema novo nem mudança no modelo de atribuição.

**Architecture:** Duas entregas independentes. (1) `cronograma_detalhado_md` (`src/builder/artifacts/repo.py`) ganha uma subseção "Sessões" por bloco, lendo o array `blocks[].sessions[]` que JÁ existe no `.timeline_index.json` v3 — sem tocar a atribuição nem a listagem de código existente (não-regressivo). (2) `lookup_card_blocks`/`lookup_card_assign_due` (`src/builder/timeline/card_block.py`) passam a casar a chave do card por forma normalizada (`norm_ascii_lower`: NFKD + sem acento + lowercase), resolvendo divergência de caixa/acento entre `source_section` e a chave do `.card_block_map.json`.

**Tech Stack:** Python 3.13, pytest. Módulos: `src/builder/artifacts/repo.py`, `src/builder/timeline/card_block.py`, `src/utils/helpers.py` (já tem `norm_ascii_lower`).

## Global Constraints

- **Sem arquivo/campo novo paralelo** — reusar `.card_block_map.json` e o `blocks[].sessions[]` existente. (Novos arquivos de TESTE e novas FUNÇÕES helper em arquivos existentes são permitidos; novos artefatos/JSON/campos persistidos NÃO.)
- **Sem mudança de schema** — o render só LÊ `sessions[]`; não escreve nada novo no `.timeline_index.json`.
- **Render NÃO toca atribuição** — a Task 2 não pode alterar `resolve_effective_block`, `computed_block_id`, nem a listagem de código por bloco já existente. Só adiciona a subseção de sessões.
- **Fix de normalização é localizado** — só no ponto de leitura (`lookup_card_blocks`/`lookup_card_assign_due`). NÃO normalizar/mutar as chaves do mapa na escrita nem no load (as chaves continuam legíveis para a UI).
- **`session.date` é string ISO `YYYY-MM-DD`** (origem `_extract_block_sessions`, `src/builder/timeline/index.py:617-625`). Pode ser `""` (sessão async/sem data) — degradar sem quebrar.
- **Sessão tem só** `{id, date, kind, label, signals}` — NÃO tem `topic_slug`/`unit_slug`/`materials`. O render do degrau 1 NÃO mostra material por dia (isso é o degrau 3); só data + dia-semana + label + marcador de prova.
- Testes existentes que NÃO podem regredir: `tests/test_code_index_uses_computed_block.py::test_cronograma_groups_primary_by_computed_block` e `tests/test_core.py::TestCronogramaDetalhado::test_no_todo_comment_leaks` (ambos dependem da listagem de código por bloco, que deve permanecer intacta).

---

### Task 1: Fix de normalização da chave de join do card

**Files:**
- Modify: `src/builder/timeline/card_block.py` (`lookup_card_blocks` em :130-134; `lookup_card_assign_due` em :137-142; adicionar helper `_normalized_card_map`)
- Test: `tests/test_card_block.py` (adicionar casos no fim do arquivo)

**Interfaces:**
- Consumes: `norm_ascii_lower(text: str) -> str` (já importado em `card_block.py:15`, de `src/utils/helpers.py:441`). Faz NFKD + remove acentos + lower + strip.
- Produces: `lookup_card_blocks(card_name, card_map, unit_index, blocks) -> List[str]` e `lookup_card_assign_due(card_name, card_map) -> str` com match de chave insensível a caixa/acento. Assinaturas inalteradas.

Contexto atual (verbatim, `card_block.py:130-142`):
```python
def lookup_card_blocks(card_name, card_map, unit_index, blocks) -> List[str]:
    entry = (card_map or {}).get(str(card_name or ""))
    if entry and "block_ids" in entry:
        return [str(b) for b in (entry.get("block_ids") or [])]
    return list(resolve_card_to_block(card_name, unit_index, blocks).block_ids)


def lookup_card_assign_due(card_name, card_map) -> str:
    """Deadline ISO de entrega do card no card map ("" quando ausente).

    Gravado em import_moodle_courses via extract_assign_deadlines (S5)."""
    entry = (card_map or {}).get(str(card_name or "")) or {}
    return str(entry.get("assign_due") or "")
```

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao fim de `tests/test_card_block.py` (o arquivo já importa `lookup_card_blocks`, `lookup_card_assign_due` e define `UNITS`/`BLOCKS` no topo):

```python
def test_lookup_blocks_matches_card_key_case_accent_insensitive():
    # chave do mapa com caixa/acento "originais"; source_section divergente ainda casa
    card_map = {
        "Especificações Indutivas e Recursivas": {"block_ids": ["bloco-04"], "source": "manual"}
    }
    assert lookup_card_blocks(
        "especificacoes indutivas e recursivas", card_map, UNITS, BLOCKS
    ) == ["bloco-04"]
    assert lookup_card_blocks(
        "ESPECIFICAÇÕES INDUTIVAS E RECURSIVAS", card_map, UNITS, BLOCKS
    ) == ["bloco-04"]


def test_lookup_assign_due_case_accent_insensitive():
    card_map = {"Verificação de Programas": {"assign_due": "2026-06-10", "source": "labels"}}
    assert lookup_card_assign_due("verificacao de programas", card_map) == "2026-06-10"


def test_lookup_blocks_exact_key_still_matches():
    # não regride o match exato
    card_map = {"Meu Card": {"block_ids": ["bloco-07"], "source": "manual"}}
    assert lookup_card_blocks("Meu Card", card_map, UNITS, BLOCKS) == ["bloco-07"]
```

- [ ] **Step 2: Rodar o teste para ver falhar**

Run: `python -m pytest tests/test_card_block.py::test_lookup_blocks_matches_card_key_case_accent_insensitive tests/test_card_block.py::test_lookup_assign_due_case_accent_insensitive -v`
Expected: FAIL — o match atual é exato (`.get(str(card_name))`), então a chave com caixa/acento divergente retorna `None` → `lookup_card_blocks` cai no `resolve_card_to_block` (que não tem "Especificações..." nos UNITS de teste e retorna `[]`); `lookup_card_assign_due` retorna `""`.

- [ ] **Step 3: Implementar o fix mínimo**

Em `src/builder/timeline/card_block.py`, adicione o helper logo antes de `lookup_card_blocks` (após a função `load_card_block_map`, ~linha 128):

```python
def _normalized_card_map(card_map) -> Dict[str, dict]:
    """Índice do card_map por chave normalizada (NFKD + sem acento + lower).

    Resolve divergência de caixa/acento entre o source_section da entry e a
    chave (nome de pasta) do .card_block_map.json — relevante para cards
    M365/legados com acentuação inconsistente. Em colisão, o último vence.
    """
    out: Dict[str, dict] = {}
    for key, value in (card_map or {}).items():
        out[norm_ascii_lower(str(key))] = value
    return out
```

Substitua `lookup_card_blocks` e `lookup_card_assign_due` por:

```python
def lookup_card_blocks(card_name, card_map, unit_index, blocks) -> List[str]:
    entry = _normalized_card_map(card_map).get(norm_ascii_lower(str(card_name or "")))
    if entry and "block_ids" in entry:
        return [str(b) for b in (entry.get("block_ids") or [])]
    return list(resolve_card_to_block(card_name, unit_index, blocks).block_ids)


def lookup_card_assign_due(card_name, card_map) -> str:
    """Deadline ISO de entrega do card no card map ("" quando ausente).

    Gravado em import_moodle_courses via extract_assign_deadlines (S5)."""
    entry = _normalized_card_map(card_map).get(norm_ascii_lower(str(card_name or ""))) or {}
    return str(entry.get("assign_due") or "")
```

- [ ] **Step 4: Rodar os testes para ver passar (e não regredir)**

Run: `python -m pytest tests/test_card_block.py -v`
Expected: PASS em todos — os 3 novos casos e os pré-existentes (incl. `test_card_map_roundtrip`, `test_lookup_prefers_manual_map_over_auto`).

- [ ] **Step 5: Verificar consumidores a jusante**

Run: `python -m pytest tests/test_card_block_assignment.py tests/test_manual_timeline_block_resolution.py -v`
Expected: PASS — `_card_scoped_block` (`content_taxonomy.py:879`) chama `lookup_card_blocks` e não muda de assinatura; a normalização só amplia o conjunto de matches (nunca reduz), então atribuições que já casavam por chave exata continuam casando.

- [ ] **Step 6: Commit**

```bash
git add src/builder/timeline/card_block.py tests/test_card_block.py
git commit -m "fix(card): casar chave de join do card por forma normalizada (caixa/acento)"
```

---

### Task 2: Subseção "Sessões" por bloco no cronograma detalhado

**Files:**
- Modify: `src/builder/artifacts/repo.py` (`cronograma_detalhado_md` em :889-972; adicionar helpers `_PT_WEEKDAYS`/`_session_date_label` antes da função)
- Test: `tests/test_cronograma_sessoes.py` (criar)

**Interfaces:**
- Consumes: `timeline_blocks: list[dict]`, onde cada bloco tem `blocks[].sessions[]` com itens `{id, date, kind, label, signals}` (`date` ISO `YYYY-MM-DD` ou `""`). O bloco também tem `id`, `period_label`, `primary_topic_label`, `topics`, `unit_slug` (já usados).
- Produces: `cronograma_detalhado_md(course_meta, entries, code_curation, timeline_blocks, subject_profile=None) -> str` — assinatura inalterada; a saída ganha, dentro de cada bloco, uma subseção `### Sessões` antes da seção de códigos.

Contexto atual (o trecho do loop a alterar, `repo.py:927-943`):
```python
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
```

- [ ] **Step 1: Escrever o teste que falha**

Crie `tests/test_cronograma_sessoes.py`:

```python
from src.builder.artifacts import repo


def _blocks_with_sessions():
    return [
        {
            "id": "bloco-04",
            "period_label": "Semana 11/03",
            "primary_topic_label": "Especificações Indutivas",
            "topics": ["conjuntos indutivos"],
            "unit_slug": "unidade-01",
            "sessions": [
                {"id": "s1", "date": "2026-03-11", "kind": "class",
                 "label": "conjuntos indutivos e equacoes recursivas", "signals": []},
                {"id": "s2", "date": "2026-03-18", "kind": "class",
                 "label": "estudo de caso listas", "signals": []},
            ],
        },
        {
            "id": "bloco-09",
            "period_label": "Semana 22/04",
            "primary_topic_label": "",
            "topics": [],
            "unit_slug": "unidade-01",
            "sessions": [
                {"id": "s3", "date": "2026-04-22", "kind": "assessment",
                 "label": "prova p1", "signals": []},
            ],
        },
    ]


def test_render_lists_sessions_by_date_with_weekday():
    md = repo.cronograma_detalhado_md({"course_name": "MF"}, [], {}, _blocks_with_sessions())
    assert "### Sessões" in md
    assert "qua 11/03" in md          # 2026-03-11 é quarta
    assert "estudo de caso listas" in md
    assert "qua 18/03" in md


def test_render_marks_assessment_session():
    md = repo.cronograma_detalhado_md({"course_name": "MF"}, [], {}, _blocks_with_sessions())
    assert "⏱" in md
    assert "prova p1" in md


def test_render_block_without_sessions_omits_section():
    blocks = [{"id": "b1", "period_label": "Aula 1", "topics": [], "sessions": []}]
    md = repo.cronograma_detalhado_md({"course_name": "ED"}, [], {}, blocks)
    assert "### Sessões" not in md


def test_render_session_with_empty_date_does_not_crash():
    blocks = [{
        "id": "b1", "period_label": "Aula 1", "topics": [],
        "sessions": [{"id": "s", "date": "", "kind": "async", "label": "atividade ead", "signals": []}],
    }]
    md = repo.cronograma_detalhado_md({"course_name": "ED"}, [], {}, blocks)
    assert "atividade ead" in md
```

- [ ] **Step 2: Rodar o teste para ver falhar**

Run: `python -m pytest tests/test_cronograma_sessoes.py -v`
Expected: FAIL — o render atual não emite `### Sessões` (nem lê `sessions[]`), então `"### Sessões" in md` é `False`.

- [ ] **Step 3: Implementar os helpers de data**

Em `src/builder/artifacts/repo.py`, adicione antes da função `cronograma_detalhado_md` (~linha 888):

```python
_PT_WEEKDAYS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def _session_date_label(date_iso: str) -> str:
    """'qua 11/03' a partir de 'YYYY-MM-DD'; retorna a string crua se inválida/vazia."""
    from datetime import date as _date
    try:
        d = _date.fromisoformat(str(date_iso))
    except (ValueError, TypeError):
        return str(date_iso or "")
    return f"{_PT_WEEKDAYS[d.weekday()]} {d.day:02d}/{d.month:02d}"
```

- [ ] **Step 4: Inserir a subseção de sessões no loop**

Em `cronograma_detalhado_md`, logo após o bloco que termina em `lines.append("")` (a linha após `**Tópicos cobertos**`, ~linha 943) e ANTES do comentário `# Materiais (code-only por enquanto)`, insira:

```python
        sessions = blk.get("sessions") or []
        if sessions:
            lines += ["### Sessões", ""]
            for s in sessions:
                date_label = _session_date_label(str(s.get("date") or ""))
                slabel = str(s.get("label") or "")
                mark = " ⏱" if str(s.get("kind") or "class") == "assessment" else ""
                line = f"- **{date_label}**{mark}" if date_label else f"- **(sem data)**{mark}"
                if slabel:
                    line += f" — {slabel}"
                lines.append(line)
            lines.append("")
```

- [ ] **Step 5: Rodar os testes para ver passar**

Run: `python -m pytest tests/test_cronograma_sessoes.py -v`
Expected: PASS nos 4 casos.

- [ ] **Step 6: Verificar não-regressão dos testes que usam o render**

Run: `python -m pytest tests/test_code_index_uses_computed_block.py tests/test_core.py::TestCronogramaDetalhado -v`
Expected: PASS — a listagem de código por bloco e os headers `## Semana ...` permanecem intactos; a subseção `### Sessões` só aparece quando o bloco tem `sessions[]` (os blocos desses testes não têm, então a saída deles não muda).

- [ ] **Step 7: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_cronograma_sessoes.py
git commit -m "feat(cronograma): listar sessoes por data (dia-semana) sob cada bloco"
```

---

## Self-Review

**1. Spec coverage (Spec A seção 6 — fatia imediata):**
- "lê o `sessions[]` que já existe ... lista por data" → Task 2 (subseção Sessões lendo `blk["sessions"]`). ✅
- "datas + rótulo do dia ... SEM materiais por dia" → Task 2 mostra `date_label` + `label`, sem material. ✅
- "Não toca atribuição nem schema" → Task 2 não altera `resolve_effective_block` nem escreve no índice; só lê. ✅
- "Junto, no mesmo degrau: fix do bug de normalização ... `norm_ascii_lower` nos dois lados do join exato" → Task 1 (normaliza em `lookup_card_blocks`/`lookup_card_assign_due`). ✅
  - Nota: a spec cita também `content_taxonomy.py:890` (`_card_scoped_block`). Coberto indiretamente: `_card_scoped_block` só faz `.strip()` e delega a `lookup_card_blocks`, que agora normaliza — então o fix no ponto de leitura cobre esse caminho sem editar `content_taxonomy.py`. ✅
- "agrupado por semana ISO" → **escopo reduzido nesta entrega**: o degrau 1 lista as sessões por DATA dentro de cada bloco (de-opaca os blocos over-merged, que é o ganho central). O reagrupamento cross-bloco por semana ISO + materiais por dia faz parte do render completo do degrau 3 (quando os materiais migram para o grão-sessão). Justificativa: manter degrau 1 não-regressivo (preserva a listagem de código por bloco e os 2 testes existentes) e verdadeiramente "sem tocar atribuição".

**2. Placeholder scan:** nenhum "TBD/TODO"; todo step de código tem o código real; comandos e saídas esperadas explícitos. ✅

**3. Type consistency:** `_session_date_label(str) -> str` usado só na Task 2; `_normalized_card_map(card_map) -> Dict[str, dict]` usado nas duas funções da Task 1; assinaturas públicas (`lookup_card_blocks`, `lookup_card_assign_due`, `cronograma_detalhado_md`) inalteradas. `norm_ascii_lower` já importado. ✅

**Nota de aceitação do degrau (fora do ciclo unitário):** a Task 1 amplia matches de card → pode mudar `computed_block_id` de entries que antes caíam no scorer. Isso é o fix pretendido e roda **atrás do eval-gate/gold/rebuild_diff** do A1-A7. Após implementar, revisar o `rebuild_diff` por curso antes de qualquer cutover (não bloqueia os testes unitários acima).
