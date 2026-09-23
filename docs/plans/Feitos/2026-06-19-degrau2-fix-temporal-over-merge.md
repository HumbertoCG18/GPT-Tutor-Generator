# Degrau 2 — Fix temporal do over-merge de blocos temáticos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Impedir que `_rows_belong_to_same_thematic_block` cole sessões num bloco que ultrapassa um span temporal grande — quebrando os blocos over-merged (ex.: IA bloco-05 de 29 dias) sem fragmentar blocos legítimos de até ~2 semanas.

**Architecture:** Adicionar uma guarda temporal a `_rows_belong_to_same_thematic_block` (`src/builder/timeline/index.py`): antes da lógica de overlap de tokens, se o span do bloco-em-formação (`current_rows[0].date_dt` → `current_row.date_dt`) exceder `MAX_THEMATIC_BLOCK_SPAN_DAYS = 21`, NÃO fundir (retorna `False`, inicia novo bloco). A guarda só aplica quando ambas as datas existem; sem data, comportamento atual preservado. Conservador por design: 21 dias deixa todos os blocos do MF (≤14d, curso ancorado no gold) intactos — então MF rebuild_diff = 0 e golden 5/5 trivial — e só quebra os outliers extremos. O agrupamento principiado por slug igual fica para o degrau 3.

**Tech Stack:** Python 3.13, pytest. Módulo: `src/builder/timeline/index.py`. Gate: `scripts/build_golden_metodos_formais.py`, `scripts/eval_assignments.py`, `scripts/rebuild_diff.py`.

## Global Constraints

- **Guarda só aplica com ambas as datas presentes** — se `current_rows[0].date_dt` ou `current_row.date_dt` for `None`/falsy, NÃO aplicar a guarda (preserva o comportamento atual byte-a-byte para linhas sem data).
- **Constante nomeada** `MAX_THEMATIC_BLOCK_SPAN_DAYS = 21` (sem número mágico inline).
- **Interino, atrás do eval-gate** — esta mudança altera fronteiras de bloco → pode mover `computed_block_id` de entries em blocos >21d. É a correção pretendida. MF (gold) NÃO pode regredir: golden 5/5 e MF rebuild_diff = 0 são condição de aceite. Drift em IA/SO/ES2/TCC restrito a blocos que excediam 21 dias.
- **`date_dt` é `datetime`** (`_parse_timeline_date_value` retorna `datetime` ou `None`; `(a - b).days` é válido).
- **Não substituir** `_rows_belong_to_same_thematic_block` por agrupamento-por-slug — isso é o degrau 3. Aqui só adiciona a guarda temporal.
- **Não tocar** a assinatura da função nem o call-site (`index.py:2046`).

---

### Task 1: Guarda de span temporal em `_rows_belong_to_same_thematic_block`

**Files:**
- Modify: `src/builder/timeline/index.py` (adicionar constante `MAX_THEMATIC_BLOCK_SPAN_DAYS` antes da função em :658; inserir a guarda entre :672 e :674)
- Test: `tests/test_thematic_block_temporal_guard.py` (criar)

**Interfaces:**
- Consumes: `_rows_belong_to_same_thematic_block(previous_row, current_row, current_rows=None) -> bool` (assinatura inalterada). Cada `row` é um dict com `content: str`, `kind: str`, `date_text: str`, `date_dt: datetime | None`. `_parse_timeline_date_value` (`index.py:210`) produz `date_dt`.
- Produces: a mesma função, agora retornando `False` quando o span do bloco-em-formação excede `MAX_THEMATIC_BLOCK_SPAN_DAYS`, antes de avaliar overlap de tokens.

Contexto atual (verbatim, `index.py:658-700`) — a guarda entra logo após o check de review/assessment (linha 672) e antes de `block_tokens = set()` (linha 674):
```python
def _rows_belong_to_same_thematic_block(
    previous_row: Dict[str, object],
    current_row: Dict[str, object],
    current_rows: Optional[List[Dict[str, object]]] = None,
) -> bool:
    if _row_is_standalone_kind(current_row) or _row_is_standalone_kind(previous_row):
        return False

    previous_text = str(previous_row.get("content", ""))
    current_text = str(current_row.get("content", ""))
    if not previous_text or not current_text:
        return False

    if _timeline_row_is_review_or_assessment(current_text):
        return False

    block_tokens = set()
    for row in current_rows or [previous_row]:
        block_tokens.update(_timeline_specific_tokens(str(row.get("content", ""))))
    ...
```

- [ ] **Step 1: Escrever os testes que falham**

Crie `tests/test_thematic_block_temporal_guard.py`:

```python
from datetime import datetime

from src.builder.timeline.index import (
    _rows_belong_to_same_thematic_block,
    MAX_THEMATIC_BLOCK_SPAN_DAYS,
)


def _row(content: str, date_iso: str):
    return {
        "content": content,
        "kind": "class",
        "date_text": date_iso,
        "date_dt": datetime.strptime(date_iso, "%Y-%m-%d") if date_iso else None,
    }


def test_same_theme_close_dates_merges():
    # mesmo tema, datas próximas (2 dias) → funde como antes
    r0 = _row("logica de hoare parte um", "2026-04-27")
    r1 = _row("logica de hoare parte dois", "2026-04-29")
    assert _rows_belong_to_same_thematic_block(r0, r1, current_rows=[r0]) is True


def test_same_theme_span_over_cap_does_not_merge():
    # mesmo tema, mas span do bloco > cap → NÃO funde (quebra o over-merge)
    r0 = _row("logica de hoare parte um", "2026-04-27")
    r_far = _row("logica de hoare revisitada", "2026-06-08")  # 42 dias depois
    assert (r_far["date_dt"] - r0["date_dt"]).days > MAX_THEMATIC_BLOCK_SPAN_DAYS
    assert _rows_belong_to_same_thematic_block(r0, r_far, current_rows=[r0]) is False


def test_span_measured_from_block_start_not_previous_row():
    # span é medido do INÍCIO do bloco (current_rows[0]) até a linha atual
    r0 = _row("logica de hoare um", "2026-04-27")
    r1 = _row("logica de hoare dois", "2026-05-04")   # 7 dias do início
    r2 = _row("logica de hoare tres", "2026-06-08")   # 42 dias do início → corta
    assert _rows_belong_to_same_thematic_block(r0, r2, current_rows=[r0, r1]) is False


def test_missing_date_skips_temporal_guard():
    # sem date_dt nos dois lados → guarda não aplica; funde por overlap como antes
    r0 = {"content": "logica de hoare parte um", "kind": "class", "date_text": "", "date_dt": None}
    r1 = {"content": "logica de hoare parte dois", "kind": "class", "date_text": "", "date_dt": None}
    assert _rows_belong_to_same_thematic_block(r0, r1, current_rows=[r0]) is True
```

- [ ] **Step 2: Rodar os testes para ver falhar**

Run: `python -m pytest tests/test_thematic_block_temporal_guard.py -v`
Expected: `test_same_theme_span_over_cap_does_not_merge` e `test_span_measured_from_block_start_not_previous_row` FALHAM (hoje fundem por overlap ≥2 tokens, sem guarda temporal); `test_same_theme_close_dates_merges` e `test_missing_date_skips_temporal_guard` PASSAM (controles). Pode também falhar no import de `MAX_THEMATIC_BLOCK_SPAN_DAYS` (ainda não existe) — nesse caso TODOS falham no import, o que conta como RED.

- [ ] **Step 3: Adicionar a constante**

Em `src/builder/timeline/index.py`, imediatamente ANTES da definição de `_rows_belong_to_same_thematic_block` (linha 658), adicione:

```python
# Cap de span temporal (interino, degrau 2): blocos temáticos não fundem
# através de um intervalo maior que isto, mesmo com overlap de tokens —
# quebra os blocos over-merged (ex.: IA 29 dias). Conservador (21d): mantém
# blocos legítimos de até ~2 semanas. Substituído pelo agrupamento por slug
# igual no degrau 3.
MAX_THEMATIC_BLOCK_SPAN_DAYS = 21
```

- [ ] **Step 4: Inserir a guarda temporal**

Em `_rows_belong_to_same_thematic_block`, logo após o bloco
```python
    if _timeline_row_is_review_or_assessment(current_text):
        return False
```
e ANTES de `    block_tokens = set()`, insira:

```python
    block_start_dt = (current_rows[0].get("date_dt") if current_rows else previous_row.get("date_dt"))
    current_dt = current_row.get("date_dt")
    if block_start_dt and current_dt:
        if (current_dt - block_start_dt).days > MAX_THEMATIC_BLOCK_SPAN_DAYS:
            return False
```

- [ ] **Step 5: Rodar os testes para ver passar**

Run: `python -m pytest tests/test_thematic_block_temporal_guard.py -v`
Expected: PASS nos 4 casos.

- [ ] **Step 6: Rodar a suíte de timeline para não-regressão**

Run: `python -m pytest tests/test_timeline_kinds.py tests/test_timeline_index_kind.py tests/test_timeline_signals.py tests/test_ddmm_timeline_boost.py -v`
Expected: PASS — a guarda só corta merges de span >21d; os fixtures dessas suítes usam linhas próximas/sem data e não disparam o corte.

- [ ] **Step 7: Commit**

```bash
git add src/builder/timeline/index.py tests/test_thematic_block_temporal_guard.py
git commit -m "fix(timeline): cap de span temporal no agrupamento tematico (quebra over-merge)"
```

---

### Task 2: Eval-gate — golden 5/5 + rebuild_diff (verificação, sem código novo)

**Files:**
- Nenhum arquivo de produção alterado. Esta task é o GATE de aceite do degrau 2.

**Interfaces:**
- Consumes: o estado pós-Task 1 (guarda temporal ativa). Scripts de gate já existentes: `scripts/build_golden_metodos_formais.py`, `scripts/eval_assignments.py`, `scripts/rebuild_diff.py`.
- Produces: confirmação de que (a) o golden do MF continua 5/5, (b) o drift de `computed_block_id` está confinado a blocos que excediam 21 dias (MF = 0 drift).

- [ ] **Step 1: Rodar o golden do MF**

Run (na raiz do repo): `python scripts/build_golden_metodos_formais.py` seguido de `python scripts/eval_assignments.py`
(Se algum script exigir argumentos, rode-o com `--help` e use os mesmos argumentos das fases anteriores — o gate é o mesmo "golden 5/5" registrado no ledger `.git/sdd/progress.md`.)
Expected: **5/5** (cw 0). Se regredir → STOP, reporte BLOCKED com a saída; o threshold de 21d precisa revisão (não prosseguir).

- [ ] **Step 2: Rodar o rebuild_diff por curso**

Run: `python scripts/rebuild_diff.py`
(Mesma invocação das fases S0/S0b registradas no ledger.)
Expected: **MF = 0** (todos os blocos do MF têm ≤14 dias < 21 → fronteiras inalteradas → `computed_block_id` inalterado). Drift em IA/SO/ES2/TCC é aceitável SE restrito a entries cujos blocos excediam 21 dias (a quebra pretendida). Anote o drift observado por curso.

- [ ] **Step 3: Registrar o resultado do gate no relatório**

Anexe ao final de `.git/sdd/task-2-report.md` (degrau 2): o número do golden (esperado 5/5), o `rebuild_diff` por curso (esperado MF=0), e a confirmação de que o drift fora do MF se concentra em blocos >21d. Sem commit (verificação).
Se MF ≠ 0 ou golden < 5/5 → STOP, reporte BLOCKED (o threshold ou a guarda precisam revisão).

---

## Self-Review

**1. Spec coverage (Spec A seção 2 — fix do over-merge):**
- "adicionar um teto temporal ... à condição de `_rows_belong_to_same_thematic_block` (index.py:699-700)" → Task 1 (guarda de span antes do overlap). ✅
- "`date_dt` já está disponível na call-site" → confirmado: `index.py:297` popula `date_dt`; o call-site `index.py:2046` passa `current_rows` (têm `date_dt`). ✅
- "Resolve a granularidade desigual (IA bloco-05 de 29 dias) sem depender de slug canônico" → cap de 21d quebra o bloco de 29d; não usa slug. ✅
- "atrás do eval-gate / gold já existente" → Task 2 (golden 5/5 + rebuild_diff, MF=0). ✅
- "Substituir por agrupamento puro-por-slug fica como refinamento posterior" → explicitamente fora de escopo (degrau 3); Global Constraints proíbe substituir a função. ✅

**2. Placeholder scan:** Task 1 tem código real e testes verbatim. Task 2 nomeia os scripts reais do gate; o único ponto sem CLI exato (args dos scripts de golden) é mitigado por instrução de usar `--help` + a mesma invocação registrada no ledger — não é um "TODO", é delegação a uma ferramenta existente cujo uso está documentado no projeto. ✅

**3. Type consistency:** `MAX_THEMATIC_BLOCK_SPAN_DAYS: int` definido na Task 1 e importado no teste; `date_dt: datetime`, `(current_dt - block_start_dt).days: int`. Assinatura de `_rows_belong_to_same_thematic_block` inalterada. ✅

**Nota de risco (tunável):** 21 dias é conservador por escolha — fixa o caso nomeado (IA 29d) e deixa o MF (gold) intocado. Se o `rebuild_diff` mostrar que blocos legítimos de IA/SO/ES2/TCC quebraram demais, o threshold é o único knob a ajustar (atrás do mesmo gate). O fix definitivo (thematic por slug) é o degrau 3.
