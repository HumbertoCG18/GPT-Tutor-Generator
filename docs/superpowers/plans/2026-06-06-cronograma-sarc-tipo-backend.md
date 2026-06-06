# Cronograma SARC: tipo autoritativo → kind do bloco (Backend) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Usar o tipo autoritativo do cronograma SARC (coluna *Atividade* primário, cor da linha confirmando) para classificar blocos do timeline, fazendo dias de prova virarem `assessment` de forma confiável e **não** receberem unidade.

**Architecture:** O tipo SARC vira `{kind=<canônico>}` no parse HTML, é validado e agregado num hint `block["source_kind"]`, que `classify_block` honra com prioridade logo abaixo do override manual. Texto/sessão seguem como fallback. Um `finalize_block` limpa `unit_slug` de blocos cujo kind final não é `class` (preservando override manual de unidade).

**Tech Stack:** Python 3.11/3.13, pytest, BeautifulSoup (parsing SARC ASP.NET).

**Spec:** `docs/superpowers/specs/2026-06-06-cronograma-sarc-tipo-e-tab-design.md` (Parte A).

---

## File Structure

- `src/utils/helpers.py` — parsing SARC. Recebe `ATIVIDADE_KIND_MAP`, `_norm_ascii_lower`, `_aspnet_row_canonical_kind`; `_ASPNET_COLOR_KIND_MAP` canonicalizado; `_parse_aspnet_schedule` passa a emitir `{kind=<canônico>}`.
- `src/builder/timeline/index.py` — montagem do índice. Recebe import de `BlockKind`, `_VALID_KIND_VALUES`, validação do token em `_build_timeline_candidate_rows`, `_SOURCE_KIND_PRIORITY` + `_aggregate_source_kind`, escrita de `source_kind` no bloco e no serializer, e `finalize_block` substituindo `ensure_block_kind` nos call sites.
- `src/builder/timeline/classifier.py` — `classify_block` honra `block["source_kind"]`.
- `schemas/timeline_index.v4.json` — declara `source_kind` (opcional) no bloco.
- `tests/test_sarc_kind_flow.py` — **novo**: testes do fluxo SARC→kind (helpers, candidate, aggregate, finalize).
- `tests/test_timeline_kinds.py` — testes de `classify_block` honrando `source_kind`.

---

## Task 1: Atividade + cor → kind canônico (helpers)

**Files:**
- Modify: `src/utils/helpers.py` (`_ASPNET_COLOR_KIND_MAP` ~361-374; após `_aspnet_row_kind` ~385; `_parse_aspnet_schedule` ~401)
- Test: `tests/test_sarc_kind_flow.py` (novo)

- [ ] **Step 1: Write the failing test**

Criar `tests/test_sarc_kind_flow.py`:

```python
"""SARC type (Atividade column + row color) -> canonical BlockKind flow."""

from src.utils.helpers import parse_html_schedule


def _sarc_html(atividade: str, descricao: str = "Conteudo", style: str = "") -> str:
    tr_style = f' style="{style}"' if style else ""
    return f"""
    <html><body><table id="dgAulas">
      <tr{tr_style}>
        <td><span id="dgAulas_ctl02_lblData">03/07/2026</span></td>
        <td><span id="dgAulas_ctl02_lblDia">Qui</span></td>
        <td><span id="dgAulas_ctl02_lblDescricao">{descricao}</span></td>
        <td><span id="dgAulas_ctl02_lblAtividade">{atividade}</span></td>
        <td><span id="dgAulas_ctl02_lblRecursos"></span></td>
      </tr>
    </table></body></html>
    """


def test_atividade_prova_emits_assessment():
    md = parse_html_schedule(_sarc_html("Prova"))
    assert "{kind=assessment}" in md


def test_atividade_avaliacao_accented_emits_assessment():
    md = parse_html_schedule(_sarc_html("Avaliação"))
    assert "{kind=assessment}" in md


def test_atividade_trabalho_emits_deliverable():
    md = parse_html_schedule(_sarc_html("Trabalho"))
    assert "{kind=deliverable}" in md


def test_atividade_aula_with_orange_row_stays_class():
    # Atividade explicita vence a cor: Aula + laranja -> class (sem marcador).
    md = parse_html_schedule(_sarc_html("Aula", style="background-color:#ffa500"))
    assert "{kind=" not in md


def test_empty_atividade_with_orange_row_falls_back_to_assessment():
    md = parse_html_schedule(_sarc_html("", style="background-color:#ffa500"))
    assert "{kind=assessment}" in md


def test_orange_row_no_longer_emits_legacy_exam_token():
    md = parse_html_schedule(_sarc_html("", style="background-color:#ffa500"))
    assert "{kind=exam}" not in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sarc_kind_flow.py -v`
Expected: FAIL — `test_atividade_prova_emits_assessment` etc. (Atividade não dirige kind hoje; cor laranja emite `{kind=exam}`).

- [ ] **Step 3: Write minimal implementation**

Em `src/utils/helpers.py`, trocar as entradas **não-ignoradas** de `_ASPNET_COLOR_KIND_MAP` para nomes canônicos do enum (manter as ignoradas):

```python
_ASPNET_COLOR_KIND_MAP = {
    "red": ("suspension", True),
    "#ff0000": ("suspension", True),
    "lightgrey": ("g2", True),
    "#d3d3d3": ("g2", True),
    "#ffa500": ("assessment", False),
    "orange": ("assessment", False),
    "#ff8c00": ("ps", True),
    "darkorange": ("ps", True),
    "#8b0000": ("event", True),
    "darkred": ("event", True),
    "#ffff00": ("deliverable", False),
    "yellow": ("deliverable", False),
}
```

Logo após `_aspnet_row_kind` (~linha 385), adicionar:

```python
ATIVIDADE_KIND_MAP = {
    "prova": "assessment",
    "avaliacao": "assessment",
    "exame": "assessment",
    "teste": "assessment",
    "trabalho": "deliverable",
    "entrega": "deliverable",
    "feriado": "holiday",
    "revisao": "review",
}


def _norm_ascii_lower(text: str) -> str:
    """NFKD + remove acentos + lower + strip. Para casar Atividade do SARC."""
    import unicodedata as _ud
    text = _ud.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not _ud.combining(ch))
    return text.lower().strip()


def _aspnet_row_canonical_kind(row) -> tuple[str, bool]:
    """Tipo canonico (valor de BlockKind) da linha SARC.

    Atividade primario (coluna explicita do professor); cor confirma apenas
    quando a Atividade nao decide. Retorna (kind, ignored).
    """
    atividade = _norm_ascii_lower(_aspnet_row_cell(row, "Atividade"))
    for needle, kind in ATIVIDADE_KIND_MAP.items():
        if needle in atividade:
            return (kind, False)
    color_kind, ignored = _aspnet_row_kind(row)
    if color_kind != "class":
        return (color_kind, ignored)
    return ("class", False)
```

Em `_parse_aspnet_schedule`, trocar a derivação de kind (linha ~401) de
`kind, ignored = _aspnet_row_kind(row)` para:

```python
        kind, ignored = _aspnet_row_canonical_kind(row)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sarc_kind_flow.py -v`
Expected: PASS (6 testes). Run também `python -m pytest tests/test_sarc_import.py -q` — PASS (regressão do parser).

- [ ] **Step 5: Commit**

```bash
git add src/utils/helpers.py tests/test_sarc_kind_flow.py
git commit -m "feat(sarc): derive canonical BlockKind from Atividade column + row color"
```

---

## Task 2: Validar o token {kind=} contra BlockKind (candidate rows)

**Files:**
- Modify: `src/builder/timeline/index.py` (import ~13; `_IGNORED_KINDS` ~412; `_build_timeline_candidate_rows` ~415-437)
- Test: `tests/test_sarc_kind_flow.py`

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/test_sarc_kind_flow.py`:

```python
from src.builder.timeline.index import _build_timeline_candidate_rows


def test_candidate_row_keeps_valid_kind():
    rows = [{"content": "Prova final {kind=assessment}", "date": "03/07/2026"}]
    out = _build_timeline_candidate_rows(rows)
    assert out[0]["kind"] == "assessment"
    assert out[0]["ignored"] is False


def test_candidate_row_invalid_kind_becomes_class():
    rows = [{"content": "Algo {kind=foobar}", "date": "03/07/2026"}]
    out = _build_timeline_candidate_rows(rows)
    assert out[0]["kind"] == "class"


def test_candidate_row_ignored_token_preserved():
    rows = [{"content": "Greve {kind=suspension}", "date": "03/07/2026"}]
    out = _build_timeline_candidate_rows(rows)
    assert out[0]["kind"] == "suspension"
    assert out[0]["ignored"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sarc_kind_flow.py -k candidate_row -v`
Expected: FAIL em `test_candidate_row_invalid_kind_becomes_class` (hoje `kind="foobar"` é aceito cru).

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/timeline/index.py`, adicionar o import (após a linha 13):

```python
from src.builder.timeline.kinds import BlockKind
```

Logo após `_IGNORED_KINDS = {...}` (~linha 412), adicionar:

```python
_VALID_KIND_VALUES = {k.value for k in BlockKind}
```

Em `_build_timeline_candidate_rows`, no bloco que extrai o kind (linhas ~422-425), trocar:

```python
        match = _KIND_TOKEN_RE.search(content)
        if match:
            raw = match.group(1).strip().lower() or "class"
            # token deve ser um BlockKind valido OU um token ignorado conhecido;
            # qualquer outra coisa cai em class (defensivo).
            kind = raw if (raw in _VALID_KIND_VALUES or raw in _IGNORED_KINDS) else "class"
            content = _collapse_ws(_KIND_TOKEN_RE.sub("", content))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sarc_kind_flow.py -k candidate_row -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_sarc_kind_flow.py
git commit -m "feat(timeline): validate {kind=} token against BlockKind in candidate rows"
```

---

## Task 3: Agregar `source_kind` no bloco + serializar + schema

**Files:**
- Modify: `src/builder/timeline/index.py` (após `_VALID_KIND_VALUES`; assembly ~2105; serializer ~1066)
- Modify: `schemas/timeline_index.v4.json` (propriedades do bloco ~117)
- Test: `tests/test_sarc_kind_flow.py`

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/test_sarc_kind_flow.py`:

```python
from src.builder.timeline.index import _aggregate_source_kind


def test_aggregate_source_kind_picks_strongest():
    rows = [{"kind": "class"}, {"kind": "review"}, {"kind": "assessment"}]
    assert _aggregate_source_kind(rows) == "assessment"


def test_aggregate_source_kind_none_when_all_class():
    rows = [{"kind": "class"}, {"kind": "class"}]
    assert _aggregate_source_kind(rows) == ""


def test_aggregate_source_kind_single_non_class():
    rows = [{"kind": "class"}, {"kind": "deliverable"}]
    assert _aggregate_source_kind(rows) == "deliverable"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sarc_kind_flow.py -k aggregate -v`
Expected: FAIL — `ImportError: cannot import name '_aggregate_source_kind'`.

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/timeline/index.py`, após `_VALID_KIND_VALUES`, adicionar:

```python
# Prioridade ao agregar kinds das linhas num hint de bloco (mais forte vence).
# class/overview/unknown nunca viram hint (sao o fallback de texto).
_SOURCE_KIND_PRIORITY = [
    "assessment", "deliverable", "review", "holiday", "makeup",
    "suspended", "academic_event", "results", "workshop",
    "office_hours", "planning", "reserved",
]


def _aggregate_source_kind(rows) -> str:
    """Maior-prioridade kind nao-class entre as linhas do bloco; '' se nenhum."""
    present = {str(r.get("kind", "")) for r in (rows or [])}
    for kind in _SOURCE_KIND_PRIORITY:
        if kind in present:
            return kind
    return ""
```

No loop de montagem, logo após criar `runtime_block` (após a linha 2105, antes da atribuição de `sessions`), adicionar:

```python
        source_kind = _aggregate_source_kind(rows)
        if source_kind:
            runtime_block["source_kind"] = source_kind
```

No serializer `_serialize_timeline_index`, junto dos campos opcionais (após o bloco `block_manual_unit_slug`, ~linha 1078), adicionar:

```python
        source_kind = block.get("source_kind")
        if source_kind:
            payload["source_kind"] = source_kind
```

Em `schemas/timeline_index.v4.json`, nas propriedades do bloco (junto de `manual_kind_override`, ~linha 118), adicionar a linha:

```json
        "source_kind": { "$ref": "#/definitions/BlockKind" },
```

(Garantir vírgula correta no JSON; campo opcional — não entra em `required`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sarc_kind_flow.py -k aggregate -v`
Expected: PASS (3 testes).
Run: `python -m pytest tests/test_timeline_schema.py -q`
Expected: PASS (schema continua válido; `additionalProperties: true` + campo declarado).

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py schemas/timeline_index.v4.json tests/test_sarc_kind_flow.py
git commit -m "feat(timeline): aggregate SARC type into block source_kind hint"
```

---

## Task 4: `classify_block` honra `source_kind`

**Files:**
- Modify: `src/builder/timeline/classifier.py` (`classify_block` ~128-141)
- Test: `tests/test_timeline_kinds.py` (lista `CLASSIFIER_CASES` ~51 e novos testes)

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/test_timeline_kinds.py` (após `test_invalid_override_falls_back`, ~linha 106):

```python
def test_source_kind_wins_over_text_and_unit():
    block = {"source_kind": "assessment", "topic_text": "Lógica",
             "unit_slug": "u1"}
    assert classify_block(block) == BlockKind.ASSESSMENT


def test_manual_override_wins_over_source_kind():
    block = {"source_kind": "assessment", "manual_kind_override": "holiday"}
    assert classify_block(block) == BlockKind.HOLIDAY


def test_invalid_source_kind_falls_back_to_text():
    block = {"source_kind": "garbage", "topic_text": "Feriado de Carnaval"}
    assert classify_block(block) == BlockKind.HOLIDAY
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_timeline_kinds.py -k source_kind -v`
Expected: FAIL em `test_source_kind_wins_over_text_and_unit` (hoje `unit_slug` faz virar CLASS).

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/timeline/classifier.py`, dentro de `classify_block`, logo após o bloco de `manual_kind_override` (após a linha 135, antes de `hay_content = ...`), inserir:

```python
    # Hint autoritativo do SARC (Atividade/cor). Vence texto/sessao/unidade,
    # perde so para o override manual acima.
    source = block.get("source_kind")
    if isinstance(source, str) and source:
        try:
            return BlockKind(source)
        except ValueError:
            pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_timeline_kinds.py -q`
Expected: PASS (todos, incluindo os 3 novos).

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/classifier.py tests/test_timeline_kinds.py
git commit -m "feat(timeline): classify_block honors authoritative source_kind hint"
```

---

## Task 5: `finalize_block` — limpar unidade em não-aula

**Files:**
- Modify: `src/builder/timeline/index.py` (após `ensure_block_kind` ~29; serializer ~1045; assembly ~2153-2154)
- Test: `tests/test_sarc_kind_flow.py`

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/test_sarc_kind_flow.py`:

```python
from src.builder.timeline.index import finalize_block


def test_finalize_strips_unit_for_assessment():
    block = {"source_kind": "assessment", "unit_slug": "u1",
             "unit_confidence": 0.9}
    finalize_block(block)
    assert block["kind"] == "assessment"
    assert block["unit_slug"] == ""
    assert block["unit_confidence"] == 0.0


def test_finalize_keeps_unit_for_class():
    block = {"topic_text": "Lógica de predicados", "unit_slug": "u1",
             "unit_confidence": 0.8}
    finalize_block(block)
    assert block["kind"] == "class"
    assert block["unit_slug"] == "u1"


def test_finalize_preserves_manual_unit_on_non_class():
    block = {"source_kind": "assessment", "unit_slug": "u1",
             "unit_confidence": 0.9, "block_manual_unit_slug": "u1"}
    finalize_block(block)
    assert block["kind"] == "assessment"
    assert block["unit_slug"] == "u1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sarc_kind_flow.py -k finalize -v`
Expected: FAIL — `ImportError: cannot import name 'finalize_block'`.

- [ ] **Step 3: Write minimal implementation**

Em `src/builder/timeline/index.py`, logo após `ensure_block_kind` (após a linha 29), adicionar:

```python
def finalize_block(block: dict) -> dict:
    """Garante `kind` e limpa unidade de blocos nao-aula.

    Provas/feriados/revisoes/etc nao tem unidade pedagogica. Override manual de
    unidade (`block_manual_unit_slug`) sempre preservado. Idempotente.
    """
    if not isinstance(block, dict):
        return block
    ensure_block_kind(block)
    if block.get("kind") != BlockKind.CLASS.value and not block.get("block_manual_unit_slug"):
        block["unit_slug"] = ""
        block["unit_confidence"] = 0.0
    return block
```

No serializer `_serialize_timeline_index`, após o `continue` de administrativo (após a linha 1046), adicionar como primeira linha do corpo do loop:

```python
        finalize_block(block)
```

No loop final de montagem (linhas 2153-2154), trocar:

```python
    for block in runtime_blocks:
        finalize_block(block)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sarc_kind_flow.py -k finalize -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_sarc_kind_flow.py
git commit -m "feat(timeline): finalize_block strips unit from non-class blocks"
```

---

## Task 6: Verificação fim-a-fim + regressão de corpus

**Files:**
- Test: nenhum arquivo novo (verificação)

- [ ] **Step 1: Rodar a suíte completa**

Run: `python -m pytest -q`
Expected: PASS (todos verdes; nenhuma regressão). Anotar o total.

- [ ] **Step 2: Verificar o delta dos cursos reais**

Run (PowerShell/bash):

```bash
python -c "
import json, os
from src.builder.timeline.classifier import classify_block
base = r'C:\Users\Humberto\Documents\GitHub'
for c in ['Engenharia-Software-2-Tutor','Inteligencia-Artifical-Tutor','Metodos-Formais-Tutor','Sistemas-Operacionais-Tutor','TCC-Tutor']:
    p = os.path.join(base, c, 'course', '.timeline_index.json')
    if not os.path.exists(p): continue
    for b in json.load(open(p, encoding='utf-8')).get('blocks', []):
        old = b.get('kind'); new = classify_block(b).value
        if old != new:
            print(c[:6], b['id'], old, '->', new, '| unit=', bool(b.get('unit_slug')))
"
```

Expected: apenas mudanças `class/reserved -> assessment/review` em blocos `unit=False` (os 5 já conhecidos: IA bloco-09, Métodos bloco-07/16, TCC bloco-16/24). **Nenhuma** regressão de aula/feriado/correção. Stored data não tem `source_kind`, então o fallback de sessão é quem age aqui — confirma compatibilidade com índices não regenerados.

- [ ] **Step 3: Verificar serialização (strip de unidade)**

Run:

```bash
python -c "
import json, os
from src.builder.timeline.index import _serialize_timeline_index
base = r'C:\Users\Humberto\Documents\GitHub'
p = os.path.join(base, 'TCC-Tutor', 'course', '.timeline_index.json')
idx = json.load(open(p, encoding='utf-8'))
out = _serialize_timeline_index(idx)
bad = [b['id'] for b in out['blocks'] if b['kind'] != 'class' and b['unit_slug'] and not b.get('block_manual_unit_slug')]
print('nao-aula com unidade (deve ser []):', bad)
"
```

Expected: `[]` (nenhum bloco não-aula com unidade após serialização).

- [ ] **Step 4: Commit (se algo foi ajustado)**

Se os passos 1-3 não exigirem mudança, não há commit. Caso contrário, corrigir e:

```bash
git add -A
git commit -m "test(timeline): verify SARC kind flow end-to-end, no corpus regressions"
```

---

## Notas de execução

- O hook de git (`code-review-graph.exe`) imprime um `UnicodeEncodeError` cosmético (cp1252) ao commitar; o commit **passa** mesmo assim. Ignorar.
- Trailer de co-autoria nos commits: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- A Parte B (UI: tabela + legenda) é um plano separado, escrito depois deste.
