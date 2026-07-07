# FASE 0 — Motor de Atribuição (Contratos + WindowProvider P1/P2 + Disambiguator len-norm) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o esqueleto dos 3 contratos do motor (WindowProvider / Disambiguator / AnchorEngine), implementar WindowProvider P1 (manual) + P2 (labels datados) e o Disambiguator determinístico com len-norm (`sqrt(|assinatura|)`) e `sessions[].label` como sinal de 1ª classe, tudo num pacote isolado `src/builder/routing/motor/` protegido por um guard test de imports — provado READ-ONLY contra o gold MF.

**Architecture:** Pacote novo `src/builder/routing/motor/` com 5 módulos puros (sem I/O de escrita). O motor REUSA as primitivas de scoring já canônicas (`concept_resolver.concept_token_weights`/`concept_vector`, `thresholds.confidence_band`) bounded à janela, mas é PROIBIDO (guard test AST) de importar os símbolos condenados do cutover (`block_token_weights`, `score_entry_against_timeline_block`, `select_probable_period_for_entry`). A cascata de janela (P1/P2) lê `card_block_map`; o Disambiguator só roda quando `|janela| > 1`. Nenhuma escrita em artefato de curso: aceite via testes (gold embutido, CI) + um probe externo READ-ONLY.

**Tech Stack:** Python 3.11, pytest, dataclasses, `typing.Protocol`, `ast` (guard test). Sem dependências novas.

---

## Contexto de fontes (leia antes de começar)

- **Spec fechado:** `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` — contratos (§3), invariantes ANCHOR-ONLY (§4), aceite (§6), fases (§7), mapa de reúso (§8), calibração aberta (§12).
- **Handoff de partida:** `docs/reports/2026-07-03-handoff-plano-fase0.md`.
- **Referência canônica do disambiguator (NÃO re-rodar, é prova cacheada):** `scripts/marco0_prova_deterministica.py` — a Config `A'` (len-norm) é o piso 59.7% que a FASE 0 tem que bater. O algoritmo de scoring desta fase é o `A'` promovido a código de produção reutilizando `concept_resolver`.
- **Régua oficial (par-colapsado):** `docs/reports/ground_truth_MF.csv` (cabeçalho: `id,material,true_block_id,computed_block_id,temporal_block_id,pair_key,provenance,scope,data_real,scorable,discriminante`).
- **Régua DEV self-contained (embute blocks + card_block_map + cases):** `tests/fixtures/eval/metodos_formais_golden.json`.

## Escopo da FASE 0 (o que ENTRA e o que NÃO entra)

ENTRA:
1. Esqueleto dos **3 contratos** (dataclasses + `Protocol`): `WindowProvider`, `Disambiguator`, `AnchorEngine`.
2. **WindowProvider P1 (manual)** + **P2 (labels datado)** via `card_block_map`, em cascata por confiabilidade.
3. **Disambiguator** determinístico: IDF bounded à janela + **len-norm `sqrt(|assinatura|)`** + `sessions[].label` como sinal de 1ª classe (acima de `block.topic_text`) + gate de margem básico (D4 proxy → `band`/`flag`).
4. **AnchorEngine.resolve** fino: roteia D6 (trabalho/prova/TDE) e bibliografia PARA FORA (funil), senão `WindowProvider → Disambiguator`.
5. **Guard test de imports** (AST): pacote do motor nunca importa os 3 condenados.
6. **Aceite READ-ONLY vs gold MF**: escopo-disamb MF ≥ **59.7%** (probe externo); contenção **100%**; confiante-errado (`band=="alta"` e errado) = **0** (gold embutido, CI).

NÃO ENTRA (fases seguintes — não implementar):
- Gate D4 com **medição de recall** → FASE 1.
- Providers **P3 (SO data-no-nome)** e **P4 (TCC tópico)** → FASE 2.
- Escalada **LLM / TIER 3** → FASE 3 (gate go/no-go).
- **TIER 0 dup-grouping**, **TIER 1 pino manual**, janela-de-prazo D6 real (`assign_due`), integração no pipeline / feature-flag → FASE 4.
- Qualquer **escrita** de `temporal_block_id` (isso é reprocess = ação do user na GUI).

## File Structure

Código novo (todo o pacote é READ-ONLY quanto a artefatos de curso; só lê + calcula):

| Arquivo | Responsabilidade |
|---|---|
| `src/builder/routing/motor/__init__.py` | Exports públicos do motor (contratos + funções). |
| `src/builder/routing/motor/contracts.py` | `AnchorDecision` (dataclass), `MotorContext` (dataclass), `WindowProvider`/`Disambiguator`/`AnchorEngine` (`Protocol`). Sem lógica. |
| `src/builder/routing/motor/context.py` | Loader READ-ONLY: `load_context(course_dir)` lê os 4 JSON do curso; `MotorContext.from_artifacts(...)` monta índices. |
| `src/builder/routing/motor/window_provider.py` | `provider_manual` (P1), `provider_labels` (P2), `resolve_window(entry, ctx)` (cascata). |
| `src/builder/routing/motor/disambiguator.py` | `block_signature`, `entry_tokens`, `disambiguate(entry, window, ctx)` (len-norm + session-label + gate). |
| `src/builder/routing/motor/anchor_engine.py` | `AnchorEngine.resolve(entry, ctx)` — roteamento D6/bibliografia + wiring janela→disambiguator. |
| `scripts/fase0_prova_motor_MF.py` | Probe externo READ-ONLY (espelha marco0, mas chama o motor real) → escopo-disamb ≥59.7%. |

Testes (convenção do repo = flat em `tests/`, prefixo `test_motor_`):

| Arquivo | Cobre |
|---|---|
| `tests/test_motor_contracts.py` | Formato de `AnchorDecision`/`MotorContext`; conformidade Protocol. |
| `tests/test_motor_import_guard.py` | Guard AST dos 3 condenados. |
| `tests/test_motor_window_provider.py` | P1/P2 + cascata + invariante janela `[]`. |
| `tests/test_motor_disambiguator.py` | len-norm, session-label>topic, gate, janela=1. |
| `tests/test_motor_anchor_engine.py` | Roteamento D6/bibliografia; wiring. |
| `tests/test_motor_golden_mf.py` | Aceite self-contained: contenção 100%, confiante-errado=0, janela=1. |

## Disciplina (não-negociável — do handoff/spec)

- **NÃO commitar sem pedido explícito.** Commits desta fase só quando o user pedir.
- Lógica nova SÓ em `src/builder/routing/motor/`, **NUNCA** em `src/builder/engine.py` (facade).
- Motor escreve conceitualmente só `temporal_block_id` — mas na FASE 0 **não escreve nada** em curso; retorna `AnchorDecision`.
- PT-BR nos comentários/docstrings; shim UTF-8 em todo script novo (console cp1252 no Windows).
- Cada task = TDD (teste falha → implementação mínima → teste passa → commit). Commits frequentes.

---

## Task 1: Esqueleto dos contratos (`contracts.py`)

**Files:**
- Create: `src/builder/routing/motor/__init__.py`
- Create: `src/builder/routing/motor/contracts.py`
- Test: `tests/test_motor_contracts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_contracts.py
from dataclasses import fields

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext


def test_anchor_decision_fields_and_defaults():
    d = AnchorDecision(block_ref="bloco-05")
    assert d.block_ref == "bloco-05"
    assert d.conf == 0.0
    assert d.band == ""
    assert d.flag is False
    assert d.provider == ""
    assert d.method == ""
    assert d.window == []
    names = {f.name for f in fields(AnchorDecision)}
    assert names == {"block_ref", "conf", "band", "flag", "provider", "method", "window"}


def test_anchor_decision_window_is_not_shared():
    a = AnchorDecision(block_ref="bloco-01")
    b = AnchorDecision(block_ref="bloco-02")
    a.window.append("bloco-01")
    assert b.window == []  # default_factory, não lista compartilhada


def test_motor_context_indexes_blocks_by_ref():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u1", "period_start": "2026-03-04"},
        {"id": "bloco-02", "block_uuid": "u2", "period_start": "2026-03-02"},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    # ordena por period_start
    assert [b["id"] for b in ctx.blocks] == ["bloco-02", "bloco-01"]
    # índice por id E por uuid
    assert ctx.block_by_ref("bloco-01")["block_uuid"] == "u1"
    assert ctx.block_by_ref("u2")["id"] == "bloco-02"
    assert ctx.block_by_ref("inexistente") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_contracts.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.builder.routing.motor'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/builder/routing/motor/__init__.py
"""Motor de atribuição material->bloco (ANCHOR-ONLY, plugável mode-aware).

Pacote ISOLADO: proibido importar os símbolos condenados do cutover
(block_token_weights, score_entry_against_timeline_block,
select_probable_period_for_entry) — ver tests/test_motor_import_guard.py.
Reúso permitido: concept_resolver (scoring PURO), card_block, thresholds,
entry_signals, text/*.
"""
from src.builder.routing.motor.contracts import (
    AnchorDecision,
    MotorContext,
)

__all__ = ["AnchorDecision", "MotorContext"]
```

```python
# src/builder/routing/motor/contracts.py
"""Contratos do motor: tipos de resultado/contexto + Protocols dos 3 tiers.

Sem lógica de negócio — só shape. A implementação vive em window_provider.py,
disambiguator.py, anchor_engine.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol


@dataclass
class AnchorDecision:
    """Decisão do motor para uma entry (grão de bloco DISPLAY, não uuid).

    band ∈ {"alta","media","baixa",""}; flag=True => entra na fila humana / TIER 3.
    provider = qual WindowProvider rendeu a janela ("manual"|"labels"|"").
    method = tier/caminho que decidiu ("janela-1"|"disamb"|"funil"|"d6"|...).
    window = janela DISPLAY considerada (para auditoria/serialização Dashboard).
    """
    block_ref: str
    conf: float = 0.0
    band: str = ""
    flag: bool = False
    provider: str = ""
    method: str = ""
    window: List[str] = field(default_factory=list)


@dataclass
class MotorContext:
    """Contexto READ-ONLY de um curso: blocos + card_block_map + lessons_index.

    blocks ficam ORDENADOS por period_start; _by_ref indexa id E block_uuid.
    """
    blocks: List[dict]
    card_block_map: Dict[str, dict]
    lessons_index: Dict[str, str]  # {date_iso: topico} (by_date do .lessons_index.json)
    _by_ref: Dict[str, dict] = field(default_factory=dict, repr=False)

    @classmethod
    def from_artifacts(
        cls,
        *,
        blocks: List[dict],
        card_block_map: Dict[str, dict],
        lessons_index: Dict[str, str],
    ) -> "MotorContext":
        ordered = sorted(blocks or [], key=lambda b: str(b.get("period_start") or ""))
        by_ref: Dict[str, dict] = {}
        for b in ordered:
            for key in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
                if key:
                    by_ref[key] = b
        return cls(
            blocks=ordered,
            card_block_map=dict(card_block_map or {}),
            lessons_index=dict(lessons_index or {}),
            _by_ref=by_ref,
        )

    def block_by_ref(self, ref: str) -> Optional[dict]:
        return self._by_ref.get(str(ref or ""))


class WindowProvider(Protocol):
    """1º provider que rende janela não-vazia; [] = sem janela (funil-piso)."""
    def __call__(self, entry: dict, ctx: MotorContext) -> List[str]: ...


class Disambiguator(Protocol):
    """Escolhe DENTRO da janela (só roda se |janela| > 1)."""
    def __call__(self, entry: dict, window: List[str], ctx: MotorContext) -> AnchorDecision: ...


class AnchorEngine(Protocol):
    """Orquestra tiers; None = sem âncora -> funil."""
    def resolve(self, entry: dict, ctx: MotorContext) -> Optional[AnchorDecision]: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_contracts.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/motor/__init__.py src/builder/routing/motor/contracts.py tests/test_motor_contracts.py
git commit -m "feat(motor): contratos AnchorDecision/MotorContext + Protocols dos 3 tiers"
```

---

## Task 2: Guard test de imports (trava a fronteira do cutover)

**Files:**
- Test: `tests/test_motor_import_guard.py`

Feito CEDO para a fronteira valer para todo módulo escrito depois. É requisito explícito da FASE 0 (spec §7). Verificação por AST (não por string, para não falsear com nomes em comentários/docstrings).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_import_guard.py
import ast
from pathlib import Path

# Símbolos condenados no cutover da FASE 5 (spec §7, revisão 03/07).
CONDENADOS = frozenset({
    "block_token_weights",
    "score_entry_against_timeline_block",
    "select_probable_period_for_entry",
})

MOTOR_DIR = Path(__file__).resolve().parents[1] / "src" / "builder" / "routing" / "motor"


def _imported_names(tree: ast.AST) -> set:
    """Nomes trazidos para o namespace por import/from-import (last segment)."""
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)              # from x import <name>
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


def test_motor_package_exists():
    assert MOTOR_DIR.is_dir(), f"pacote do motor ausente: {MOTOR_DIR}"


def test_motor_never_imports_condemned_symbols():
    offenders: dict = {}
    for py in sorted(MOTOR_DIR.rglob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        bad = _imported_names(tree) & CONDENADOS
        if bad:
            offenders[py.name] = sorted(bad)
    assert not offenders, (
        f"motor importa condenados do cutover: {offenders}. "
        "Whitelist: concept_resolver puro, card_block, thresholds, entry_signals, text/*."
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_import_guard.py -v`
Expected (com o pacote da Task 1 já existindo): PASS — mas confirme rodando; o teste é o contrato que qualquer import futuro proibido quebra. Para provar que ele PEGA violação, adicione temporariamente em `contracts.py` a linha `from src.builder.routing.file_map import block_token_weights  # noqa` e rode: deve FALHAR com `motor importa condenados: {'contracts.py': ['block_token_weights']}`. **Remova a linha** e rode de novo: PASS.

- [ ] **Step 3: (sem implementação nova — o teste é a implementação)**

Nada a escrever: o guard é o próprio teste. Garanta que a linha temporária do Step 2 foi removida.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_import_guard.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add tests/test_motor_import_guard.py
git commit -m "test(motor): guard AST proibe import dos 3 condenados do cutover"
```

---

## Task 3: WindowProvider P1 (manual) + P2 (labels) + cascata

**Files:**
- Create: `src/builder/routing/motor/window_provider.py`
- Modify: `src/builder/routing/motor/__init__.py` (exportar `resolve_window`)
- Test: `tests/test_motor_window_provider.py`

**Design:** `card_block_map[secao]` traz `{block_ids, source}` com `source ∈ {"manual","labels"}`. P1 só rende janela se `source=="manual"`; P2 só se `source=="labels"`. A cascata tenta P1 antes de P2 e devolve a 1ª janela não-vazia + o nome do provider. A chave da entry é `source_section` (normalizada NFKD+lower+sem-acento, reusando `norm_ascii_lower`, porque cards M365/legados divergem em caixa/acento). Janela `[]` (ou card ausente) = sem janela → funil.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_window_provider.py
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.window_provider import (
    provider_manual,
    provider_labels,
    resolve_window,
)

BLOCKS = [
    {"id": "bloco-01", "period_start": "2026-03-02"},
    {"id": "bloco-02", "period_start": "2026-03-04"},
    {"id": "bloco-05", "period_start": "2026-04-06"},
    {"id": "bloco-06", "period_start": "2026-04-13"},
]

CBM = {
    "Provas por Indução": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
    "Introdução a Métodos Formais": {
        "block_ids": ["bloco-01", "bloco-02"], "source": "labels",
    },
    "Bibliografia-Livros": {"block_ids": [], "source": "manual"},
}


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=CBM, lessons_index={})


def test_p1_manual_returns_window_only_for_manual_source():
    ctx = _ctx()
    assert provider_manual({"source_section": "Provas por Indução"}, ctx) == ["bloco-05", "bloco-06"]
    # labels-source NÃO é P1:
    assert provider_manual({"source_section": "Introdução a Métodos Formais"}, ctx) == []


def test_p2_labels_returns_window_only_for_labels_source():
    ctx = _ctx()
    assert provider_labels({"source_section": "Introdução a Métodos Formais"}, ctx) == ["bloco-01", "bloco-02"]
    assert provider_labels({"source_section": "Provas por Indução"}, ctx) == []


def test_cascade_prefers_manual_then_labels():
    ctx = _ctx()
    win, prov = resolve_window({"source_section": "Provas por Indução"}, ctx)
    assert (win, prov) == (["bloco-05", "bloco-06"], "manual")
    win, prov = resolve_window({"source_section": "Introdução a Métodos Formais"}, ctx)
    assert (win, prov) == (["bloco-01", "bloco-02"], "labels")


def test_empty_or_missing_card_yields_no_window():
    ctx = _ctx()
    assert resolve_window({"source_section": "Bibliografia-Livros"}, ctx) == ([], "")
    assert resolve_window({"source_section": "Card Inexistente"}, ctx) == ([], "")
    assert resolve_window({"source_section": ""}, ctx) == ([], "")


def test_card_lookup_is_accent_and_case_insensitive():
    ctx = _ctx()
    # "provas por inducao" (sem acento, minúsculo) casa "Provas por Indução"
    win, prov = resolve_window({"source_section": "provas por inducao"}, ctx)
    assert (win, prov) == (["bloco-05", "bloco-06"], "manual")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_window_provider.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.builder.routing.motor.window_provider'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/builder/routing/motor/window_provider.py
"""WindowProvider: cascata de providers por CONFIABILIDADE (P1 manual > P2 labels).

FASE 0: só P1/P2 (card_block_map). P3 (data-no-nome) e P4 (tópico) = FASE 2.
Retorna janela como lista de refs DISPLAY (bloco-NN). [] = sem janela = funil.
"""
from __future__ import annotations

from typing import List, Tuple

from src.utils.helpers import norm_ascii_lower

from src.builder.routing.motor.contracts import MotorContext


def _card_entry(entry: dict, ctx: MotorContext) -> dict:
    """Entrada do card_block_map para a source_section da entry (match sem
    acento/caixa; em colisão, o último vence — igual a card_block._normalized)."""
    key = norm_ascii_lower(str(entry.get("source_section") or ""))
    if not key:
        return {}
    normalized = {norm_ascii_lower(str(k)): v for k, v in ctx.card_block_map.items()}
    return normalized.get(key) or {}


def _window_for_source(entry: dict, ctx: MotorContext, source: str) -> List[str]:
    info = _card_entry(entry, ctx)
    if str(info.get("source") or "") != source:
        return []
    return [str(b) for b in (info.get("block_ids") or []) if str(b)]


def provider_manual(entry: dict, ctx: MotorContext) -> List[str]:
    """P1 — card-window MANUAL (verdade humana)."""
    return _window_for_source(entry, ctx, "manual")


def provider_labels(entry: dict, ctx: MotorContext) -> List[str]:
    """P2 — card_block_map LABELS datado (parse_card_dates A-D)."""
    return _window_for_source(entry, ctx, "labels")


# Cascata em ordem de CONFIABILIDADE. Cada par (fn, nome).
_CASCADE = (
    (provider_manual, "manual"),
    (provider_labels, "labels"),
)


def resolve_window(entry: dict, ctx: MotorContext) -> Tuple[List[str], str]:
    """1º provider com janela não-vazia -> (janela, nome_provider). ([], "") = funil."""
    for fn, name in _CASCADE:
        win = fn(entry, ctx)
        if win:
            return win, name
    return [], ""
```

Adicione ao `__init__.py`:

```python
# src/builder/routing/motor/__init__.py  (após o import de contracts)
from src.builder.routing.motor.window_provider import resolve_window

__all__ = ["AnchorDecision", "MotorContext", "resolve_window"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_window_provider.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/motor/window_provider.py src/builder/routing/motor/__init__.py tests/test_motor_window_provider.py
git commit -m "feat(motor): WindowProvider P1 (manual) + P2 (labels) + cascata"
```

---

## Task 4: Assinatura de bloco + tokens da entry (session-label 1ª classe)

**Files:**
- Create: `src/builder/routing/motor/disambiguator.py` (parte 1: helpers de sinal)
- Test: `tests/test_motor_disambiguator.py` (parte 1)

**Design:** Separa a construção de SINAL do scoring (Task 5). A assinatura do bloco é um `set` de tokens vindos de duas origens com pesos distintos: `sessions[].label` (via `ctx.lessons_index[date]` reforçado pelo `label` embutido no bloco) = FINO/1ª classe; `topic_text`+`primary_topic_label` = GROSSO/fallback. Tokenização reusa `normalize_match_text` + filtro `>=3 chars` e stems genéricos (espelha `marco0._toks`/`_GEN` — a prova cacheada), para o número casar com o piso 59.7%. Retornamos os dois conjuntos separados para o scorer poder pesar session-label acima de topic.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_disambiguator.py
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.disambiguator import (
    entry_tokens,
    block_topic_tokens,
    block_session_tokens,
)


def test_entry_tokens_merge_title_label_markdown_and_drop_generics():
    entry = {
        "title": "LogicaDeHoare2",              # camelCase quebrado no fold
        "moodle_label": "Exemplos (Lógica de Floyd-Hoare)",
        "approved_markdown": "",
    }
    toks = entry_tokens(entry, markdown="Introdução ao cálculo de Hoare")
    assert "hoare" in toks
    assert "logica" in toks
    assert "introduc" not in toks and "introducao" not in toks  # stem genérico dropado
    assert all(len(t) >= 3 for t in toks)


def test_block_session_tokens_come_from_lessons_index_by_date():
    block = {
        "id": "bloco-05",
        "topic_text": "provas inducao",
        "primary_topic_label": "Provas por Indução",
        "sessions": [{"date": "2026-04-06", "label": "inducao estrutural aula"}],
    }
    ctx = MotorContext.from_artifacts(
        blocks=[block], card_block_map={},
        lessons_index={"2026-04-06": "inducao estrutural sobre listas"},
    )
    sess = block_session_tokens(block, ctx)
    # vem do lessons_index (roteiro do dia) E do label embutido na sessão
    assert "estrutural" in sess
    assert "listas" in sess
    topic = block_topic_tokens(block)
    assert "provas" in topic and "inducao" in topic
    # session-label e topic são conjuntos SEPARADOS (pesagem distinta no scorer)
    assert "listas" not in topic
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_disambiguator.py -v`
Expected: FAIL com `ImportError: cannot import name 'entry_tokens'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/builder/routing/motor/disambiguator.py
"""Disambiguator: escolhe DENTRO da janela (|janela|>1) por IDF len-norm.

Reúso PURO: concept_resolver.concept_token_weights/concept_vector (bounded à
janela) — mas a tokenização/stems desta fase espelha marco0 (prova cacheada
Config A' = 59.7%) para o número bater. session-label é 1ª classe (peso acima
do topic_text agregado).

PROIBIDO importar block_token_weights/score_entry_against_timeline_block/
select_probable_period_for_entry (guard test).
"""
from __future__ import annotations

import re
from typing import List

from src.builder.text.normalize import normalize_match_text
from src.builder.routing.motor.contracts import MotorContext

# Espelha marco0._GEN: stems (prefixo 8) que NÃO discriminam bloco.
_GENERIC_STEMS = frozenset({
    "introduc", "continua", "exercici", "revisao", "conteudo", "material",
    "aplicac", "apresent", "sobre", "parte", "exemplo", "usando", "aula",
    "para", "resposta", "solucao", "lista",
})


def _toks(text: str) -> set:
    """Tokens normalizados >=3 chars, sem dígitos-puros nem stems genéricos.

    Quebra camelCase ANTES do fold (LogicaDeHoare -> logica de hoare)."""
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(text or ""))
    out: set = set()
    for t in normalize_match_text(text).split():
        if len(t) >= 3 and not t.isdigit() and t[:8] not in _GENERIC_STEMS:
            out.add(t)
    return out


def _moodle_label_text(entry: dict) -> str:
    ml = entry.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else str(ml or "")


def entry_tokens(entry: dict, markdown: str = "") -> set:
    """Sinal LIMPO do material: título + moodle_label + markdown (capado fora)."""
    parts = [str(entry.get("title") or ""), _moodle_label_text(entry), str(markdown or "")]
    return _toks(" ".join(p for p in parts if p))


def block_topic_tokens(block: dict) -> set:
    """Assinatura GROSSA do bloco: topic_text + primary_topic_label."""
    return _toks(
        str(block.get("topic_text") or "") + " " + str(block.get("primary_topic_label") or "")
    )


def block_session_tokens(block: dict, ctx: MotorContext) -> set:
    """Assinatura FINA (1ª classe): sessions[].label + roteiro do dia (lessons_index)."""
    out: set = set()
    for sess in block.get("sessions") or []:
        out |= _toks(str(sess.get("label") or ""))
        topic = ctx.lessons_index.get(str(sess.get("date") or ""))
        if topic:
            out |= _toks(str(topic))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_disambiguator.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/motor/disambiguator.py tests/test_motor_disambiguator.py
git commit -m "feat(motor): sinais do disambiguator (session-label 1a classe + entry tokens)"
```

---

## Task 5: Scoring len-norm + gate de margem → `disambiguate`

**Files:**
- Modify: `src/builder/routing/motor/disambiguator.py` (adiciona `disambiguate` + constantes)
- Modify: `src/builder/routing/motor/__init__.py` (exportar `disambiguate`)
- Test: `tests/test_motor_disambiguator.py` (adiciona casos)

**Design:** IDF LOCAL à janela (`df` = nº de blocos da janela cujo sig contém o token), score = `Σ log(1 + m/df[t])` sobre tokens casados, **normalizado por `sqrt(|sig|)`** (a alavanca +6.5pp do MARCO 0). session-label soma com peso `W_SESSION_LABEL` acima do topic (grosso) `W_TOPIC`. Gate D4 proxy: `band="alta"` se `(s1 - s2)/max(s1,ε) >= MARGIN_TAU` e `s1 > 0`; senão `flag=True` + `band` via `confidence_band`. `|janela|==1` → coloca direto, band alta, sem flag. Valor de `MARGIN_TAU`/`W_*` = **calibração TDD** (spec §12): ajuste para que na régua gold (Task 7) confiante-errado=0 sem derrubar o piso 59.7%; comece com os valores abaixo (herdados do MARCO 0) e só mexa se um teste vermelho exigir.

- [ ] **Step 1: Write the failing test (adicionar ao arquivo existente)**

```python
# tests/test_motor_disambiguator.py  (APÊNDICE — mantenha os testes da Task 4)
import math

from src.builder.routing.motor.disambiguator import disambiguate


def _ctx(blocks, lessons=None):
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map={}, lessons_index=lessons or {}
    )


def test_window_of_one_places_directly_high_band_no_flag():
    blocks = [{"id": "bloco-04", "topic_text": "especificacoes indutivas recursivas"}]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "ConjuntosIndutivos.pdf"}, ["bloco-04"], ctx)
    assert d.block_ref == "bloco-04"
    assert d.band == "alta" and d.flag is False and d.method == "janela-1"


def test_len_norm_beats_verbose_sink_block():
    # bloco-verboso tem assinatura enorme (sink); bloco-alvo é enxuto e casa 'hoare'.
    blocks = [
        {"id": "bloco-10", "topic_text": "hoare"},
        {"id": "bloco-11", "topic_text": (
            "logica proposicional predicados conjuntos relacoes funcoes inducao "
            "recursao provas semantica sintaxe modelos verificacao"
        )},
    ]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "Logica de Hoare"}, ["bloco-10", "bloco-11"], ctx)
    assert d.block_ref == "bloco-10"  # len-norm impede o sumidouro verboso


def test_session_label_outranks_topic_text_on_multiblock():
    # Ambos os blocos têm o MESMO topic grosso; só o session-label discrimina.
    blocks = [
        {"id": "bloco-05", "topic_text": "provas inducao",
         "sessions": [{"date": "2026-04-06", "label": "inducao estrutural listas"}]},
        {"id": "bloco-06", "topic_text": "provas inducao",
         "sessions": [{"date": "2026-04-13", "label": "inducao arvores binarias"}]},
    ]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "Prova por indução em árvores"}, ["bloco-05", "bloco-06"], ctx)
    assert d.block_ref == "bloco-06"  # 'arvores' vem do session-label, não do topic


def test_tie_flags_and_is_not_high_band():
    # Sem token discriminante em nenhum lado -> empate -> flag, band != alta.
    blocks = [
        {"id": "bloco-05", "topic_text": "provas inducao"},
        {"id": "bloco-06", "topic_text": "provas inducao"},
    ]
    ctx = _ctx(blocks)
    d = disambiguate({"title": "material sem sinal"}, ["bloco-05", "bloco-06"], ctx)
    assert d.flag is True
    assert d.band != "alta"
    assert d.block_ref in {"bloco-05", "bloco-06"}
    assert d.window == ["bloco-05", "bloco-06"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_disambiguator.py -v`
Expected: FAIL com `ImportError: cannot import name 'disambiguate'`.

- [ ] **Step 3: Write minimal implementation (adicionar ao disambiguator.py)**

```python
# src/builder/routing/motor/disambiguator.py  (APÊNDICE)
from src.builder.routing.motor.contracts import AnchorDecision
from src.builder.routing.thresholds import confidence_band

# Pesos da fusão (calibração TDD — spec §12). session-label (fino) > topic (grosso).
W_SESSION_LABEL: float = 1.0
W_TOPIC: float = 0.6
# Gate D4 proxy (MARCO 0): margem relativa mínima p/ band "alta". Calibração
# fina COM RECALL = FASE 1; aqui só garante confiante-errado=0 no gold.
MARGIN_TAU: float = 0.25
_EPS: float = 1e-9


def _block_signature(block: dict, ctx: MotorContext) -> dict:
    """{token: peso} do bloco: session-label (1ª classe) sobrepõe topic (grosso)."""
    sig: dict = {}
    for t in block_topic_tokens(block):
        sig[t] = W_TOPIC
    for t in block_session_tokens(block, ctx):
        sig[t] = W_SESSION_LABEL  # 1ª classe: substitui o peso grosso se colidir
    return sig


def _score(mat: set, sig: dict, m: int, df: dict) -> float:
    """IDF local (log(1+m/df)) ponderado pelo peso do token, LEN-NORMalizado."""
    if not sig:
        return 0.0
    import math
    raw = sum(sig[t] * math.log(1.0 + m / df[t]) for t in (mat & set(sig)))
    return raw / math.sqrt(len(sig))


def disambiguate(entry: dict, window: List[str], ctx: MotorContext, markdown: str = "") -> AnchorDecision:
    win = list(window or [])
    blocks = [ctx.block_by_ref(r) for r in win]
    blocks = [b for b in blocks if b is not None]
    if not blocks:
        return AnchorDecision(block_ref="", method="funil", window=win)
    if len(blocks) == 1:
        ref = str(blocks[0].get("id") or blocks[0].get("block_uuid") or win[0])
        return AnchorDecision(block_ref=ref, conf=1.0, band="alta", flag=False,
                              method="janela-1", window=win)

    mat = entry_tokens(entry, markdown)
    sigs = [_block_signature(b, ctx) for b in blocks]
    m = len(blocks)
    df: dict = {}
    for sig in sigs:
        for t in sig:
            df[t] = df.get(t, 0) + 1
    scores = [_score(mat, sig, m, df) for sig in sigs]

    order = sorted(range(len(blocks)), key=lambda i: scores[i], reverse=True)
    i1 = order[0]
    s1 = scores[i1]
    s2 = scores[order[1]] if len(order) > 1 else 0.0
    rel_margin = (s1 - s2) / max(s1, _EPS)
    confident = s1 > 0 and rel_margin >= MARGIN_TAU

    ref = str(blocks[i1].get("id") or blocks[i1].get("block_uuid") or win[i1])
    band = "alta" if confident else confidence_band(rel_margin)
    return AnchorDecision(
        block_ref=ref, conf=float(rel_margin),
        band=band, flag=not confident, method="disamb", window=win,
    )
```

Adicione ao `__init__.py`:

```python
# src/builder/routing/motor/__init__.py
from src.builder.routing.motor.disambiguator import disambiguate

__all__ = ["AnchorDecision", "MotorContext", "resolve_window", "disambiguate"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_disambiguator.py -v`
Expected: PASS (6 passed — 2 da Task 4 + 4 novos).

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/motor/disambiguator.py src/builder/routing/motor/__init__.py tests/test_motor_disambiguator.py
git commit -m "feat(motor): disambiguate len-norm + session-label peso + gate D4 proxy"
```

---

## Task 6: AnchorEngine.resolve (roteamento D6/bibliografia + wiring)

**Files:**
- Create: `src/builder/routing/motor/anchor_engine.py`
- Modify: `src/builder/routing/motor/__init__.py`
- Test: `tests/test_motor_anchor_engine.py`

**Design:** FASE 0 do AnchorEngine é fino: (1) categorias que vão FORA do disambiguator retornam `None` (funil) — bibliografia/references/cronograma **nunca** entram; trabalho/prova/TDE também saem do disambiguator na FASE 0 (a janela-de-prazo real por `assign_due` é FASE 4 — aqui apenas os removemos do escopo, como o MARCO 0 faz). (2) senão: `resolve_window`; janela `[]` → `None`; `|janela|==1` ou `>1` → `disambiguate`. Marca `provider` na decisão. Detecção D6 espelha `marco0.is_d6` (categoria ∈ {trabalhos, provas} ou `source_section` começa com "TDE").

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_anchor_engine.py
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope

BLOCKS = [
    {"id": "bloco-01", "period_start": "2026-03-02", "topic_text": "introducao"},
    {"id": "bloco-02", "period_start": "2026-03-04", "topic_text": "logica predicados"},
    {"id": "bloco-05", "period_start": "2026-04-06", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-06", "label": "inducao estrutural"}]},
    {"id": "bloco-06", "period_start": "2026-04-13", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-13", "label": "inducao arvores"}]},
]
CBM = {
    "Provas por Indução": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
    "Bibliografia-Livros": {"block_ids": [], "source": "manual"},
}


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=CBM, lessons_index={})


def test_bibliografia_routes_out_of_motor():
    assert is_out_of_disamb_scope({"category": "bibliografia"}) is True
    eng = AnchorEngine()
    assert eng.resolve({"category": "bibliografia", "source_section": "Bibliografia-Livros"}, _ctx()) is None


def test_d6_trabalho_prova_tde_out_of_disambiguator():
    assert is_out_of_disamb_scope({"category": "trabalhos"}) is True
    assert is_out_of_disamb_scope({"category": "provas"}) is True
    assert is_out_of_disamb_scope({"source_section": "TDE 3 - entrega"}) is True
    assert is_out_of_disamb_scope({"category": "material"}) is False


def test_no_window_returns_none_funil():
    eng = AnchorEngine()
    assert eng.resolve({"category": "material", "source_section": "Card Sem Janela"}, _ctx()) is None


def test_multiblock_window_runs_disambiguator_and_sets_provider():
    eng = AnchorEngine()
    d = eng.resolve(
        {"category": "material", "source_section": "Provas por Indução",
         "title": "Prova por indução em árvores"},
        _ctx(),
    )
    assert d is not None
    assert d.block_ref == "bloco-06"      # session-label 'arvores' discrimina
    assert d.provider == "manual"
    assert d.method == "disamb"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_anchor_engine.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.builder.routing.motor.anchor_engine'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/builder/routing/motor/anchor_engine.py
"""AnchorEngine (FASE 0): roteia D6/bibliografia p/ fora, senão janela->disambig.

TIER 0 (dup), TIER 1 (pino manual), janela-de-prazo real (assign_due) e TIER 3
(LLM) = fases seguintes. Aqui: escopo-disambiguator + funil honesto (None).
"""
from __future__ import annotations

from typing import Optional

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor.window_provider import resolve_window
from src.builder.routing.motor.disambiguator import disambiguate

# Categorias que NUNCA entram no disambiguator na FASE 0 (spec §3 TIER 2 + marco0).
# bibliografia/references/cronograma = funil direto (0 chamada LLM depois).
# trabalhos/provas = janela-de-prazo (FASE 4); fora do disambiguator já agora.
_OUT_CATEGORIES = frozenset({
    "bibliografia", "references", "referencias", "cronograma", "apoio",
    "trabalhos", "provas",
})
_TDE_PREFIX = "TDE"


def is_out_of_disamb_scope(entry: dict) -> bool:
    cat = str(entry.get("category") or "").strip().lower()
    if cat in _OUT_CATEGORIES:
        return True
    sec = str(entry.get("source_section") or "").strip()
    return sec.startswith(_TDE_PREFIX)


class AnchorEngine:
    """resolve(entry, ctx) -> AnchorDecision | None (None = funil-piso)."""

    def resolve(self, entry: dict, ctx: MotorContext, markdown: str = "") -> Optional[AnchorDecision]:
        if is_out_of_disamb_scope(entry):
            return None
        window, provider = resolve_window(entry, ctx)
        if not window:
            return None  # sem janela -> funil (invariante ANCHOR-ONLY)
        decision = disambiguate(entry, window, ctx, markdown)
        decision.provider = provider
        return decision
```

Adicione ao `__init__.py`:

```python
# src/builder/routing/motor/__init__.py
from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope

__all__ = [
    "AnchorDecision", "MotorContext", "resolve_window", "disambiguate",
    "AnchorEngine", "is_out_of_disamb_scope",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_anchor_engine.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/builder/routing/motor/anchor_engine.py src/builder/routing/motor/__init__.py tests/test_motor_anchor_engine.py
git commit -m "feat(motor): AnchorEngine.resolve (roteia D6/bibliografia + wiring janela->disambig)"
```

---

## Task 7: Aceite self-contained vs gold MF embutido (contenção 100% + confiante-errado 0)

**Files:**
- Create: `tests/test_motor_golden_mf.py`
- Test: o próprio arquivo

**Design:** Carrega `tests/fixtures/eval/metodos_formais_golden.json` (embute `blocks`, `card_block_map`, `cases`). Monta `MotorContext` do fixture. Para cada case COM window (não-excluído, `source_section_real` mapeando a card com `block_ids` não-vazio), roda `AnchorEngine.resolve` e verifica os invariantes de aceite da FASE 0 mensuráveis SEM o repo externo:
1. **Contenção**: quando o motor ancora (decisão não-None), o `expected_block_id` do case está DENTRO da janela considerada (`decision.window`).
2. **Confiante-errado = 0**: nenhum case com `band=="alta"` tem `block_ref != expected_block_id`.
3. **Janela=1**: casos de janela unitária colocam o bloco certo, 0 flag.

O número 59.7% (escopo-disamb par-colapsado) vem do probe externo (Task 8) — o gold embutido garante os invariantes duros em CI sem depender do repo MF.

> **Nota de tensão (registrar no tracker):** o card **"Verificação de Programas"** tem `block_ids: []` no gold embutido → janela vazia → sai como funil aqui. A fixture nomeada "Verificação de Programas (blocos 10-15)" do aceite §6 é exercida no **probe externo** (Task 8), onde o repo real fornece a janela via labels/roteiro. Não falhar a CI por causa dela.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_golden_mf.py
import json
from pathlib import Path

import pytest

from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope
from src.utils.helpers import norm_ascii_lower

GOLD = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "eval" / "metodos_formais_golden.json"


def _load_ctx_and_cases():
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    ctx = MotorContext.from_artifacts(
        blocks=data["blocks"],
        card_block_map=data["card_block_map"],
        lessons_index={},  # gold não embute lessons_index; session-label vem de sessions[].label
    )
    return ctx, data["cases"]


def _has_window(ctx, section) -> bool:
    key = norm_ascii_lower(str(section or ""))
    norm = {norm_ascii_lower(str(k)): v for k, v in ctx.card_block_map.items()}
    info = norm.get(key) or {}
    return bool(info.get("block_ids"))


def _entry_of(case):
    # mapeia o case do gold para o shape que o motor lê
    return {
        "title": case.get("title", ""),
        "category": case.get("category", ""),
        "source_section": case.get("source_section_real", ""),
        "moodle_label": case.get("moodle_label", ""),
        "auto_tags": case.get("auto_tags", []),
    }


def _scored_cases(ctx, cases):
    """Cases mensuráveis: têm expected_block_id, não são excluídos/D6, e têm janela."""
    out = []
    for c in cases:
        if not c.get("expected_block_id"):
            continue
        entry = _entry_of(c)
        if is_out_of_disamb_scope(entry):
            continue
        if not _has_window(ctx, entry["source_section"]):
            continue
        out.append((c, entry))
    return out


def test_gold_has_scorable_windowed_cases():
    ctx, cases = _load_ctx_and_cases()
    assert len(_scored_cases(ctx, cases)) >= 8  # sanidade: há casos de janela pra medir


def test_contencao_100_pct_quando_ancora():
    ctx, cases = _load_ctx_and_cases()
    fora = []
    eng = AnchorEngine()
    for c, entry in _scored_cases(ctx, cases):
        d = eng.resolve(entry, ctx, markdown=c.get("markdown", ""))
        if d is None:
            continue  # funil não viola contenção
        if c["expected_block_id"] not in d.window:
            fora.append((entry["title"], c["expected_block_id"], d.window))
    assert not fora, f"verdade FORA da janela (contenção quebrada): {fora}"


def test_confiante_errado_zero():
    ctx, cases = _load_ctx_and_cases()
    eng = AnchorEngine()
    confiante_errado = []
    for c, entry in _scored_cases(ctx, cases):
        d = eng.resolve(entry, ctx, markdown=c.get("markdown", ""))
        if d is None:
            continue
        if d.band == "alta" and d.block_ref != c["expected_block_id"]:
            confiante_errado.append((entry["title"], d.block_ref, c["expected_block_id"]))
    assert not confiante_errado, f"confiante-e-errado (band alta): {confiante_errado}"


def test_janela_unitaria_coloca_e_nao_flaga():
    ctx, cases = _load_ctx_and_cases()
    eng = AnchorEngine()
    for c, entry in _scored_cases(ctx, cases):
        d = eng.resolve(entry, ctx, markdown=c.get("markdown", ""))
        if d is not None and len(d.window) == 1:
            assert d.flag is False
            assert d.block_ref == c["expected_block_id"], (entry["title"], d.block_ref)
```

- [ ] **Step 2: Run test to verify it fails (então calibrar)**

Run: `python -m pytest tests/test_motor_golden_mf.py -v`
Expected inicial: `test_contencao_*` e `test_janela_unitaria_*` devem PASSAR de imediato (contenção é garantida pelo card_block_map manual). `test_confiante_errado_zero` PODE falhar se algum multi-bloco sair `band=="alta"` e errado — nesse caso **calibre** `MARGIN_TAU`/`W_SESSION_LABEL`/`W_TOPIC` na `disambiguator.py` (Task 5, Step 3) até zerar, SEM derrubar os testes unitários da Task 5. Documente o valor final num comentário citando o gold.

- [ ] **Step 3: (calibração, não código novo)**

Se `test_confiante_errado_zero` falhar: aumente `MARGIN_TAU` (ex.: 0.25 → 0.35) para exigir margem maior antes de `band="alta"`, OU ajuste `W_SESSION_LABEL/W_TOPIC`. Re-rode as Tasks 5 e 7 a cada ajuste. Critério de parada: `test_motor_disambiguator.py` E `test_motor_golden_mf.py` verdes juntos.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_golden_mf.py tests/test_motor_disambiguator.py -v`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add tests/test_motor_golden_mf.py src/builder/routing/motor/disambiguator.py
git commit -m "test(motor): aceite gold MF embutido (contencao 100%, confiante-errado 0) + calibracao"
```

---

## Task 8: Probe externo READ-ONLY vs ground_truth_MF.csv (escopo-disamb ≥59.7%)

**Files:**
- Create: `scripts/fase0_prova_motor_MF.py`
- (Sem teste unitário: depende do repo externo `Metodos-Formais-Tutor`; roda manual, reporta número.)

**Design:** Espelha `scripts/marco0_prova_deterministica.py` (mesma régua, mesmo colapso de par), mas chama o **motor real** (`AnchorEngine`/`disambiguate`) em vez do `Motor` inline. Prova que o código de produção reproduz a Config `A'` (≥59.7% escopo-disamb par-colapsado), contenção 100%, confiante-errado=0. **READ-ONLY**: só lê `manifest.json` + os 4 JSON de `course/` do repo MF; não muta nada. Shim UTF-8 obrigatório (console cp1252). O MARCO 0 NÃO se re-roda — este probe é do MOTOR real, não a prova cacheada.

- [ ] **Step 1: Escrever o probe**

```python
# scripts/fase0_prova_motor_MF.py
#!/usr/bin/env python3
"""FASE 0 — prova READ-ONLY do MOTOR real vs ground_truth_MF.csv.

Reproduz a régua do MARCO 0 (colapso de par, escopo-disamb) chamando o motor de
produção (src/builder/routing/motor). Verifica:
  - escopo-disamb par-colapsado >= 59.7% (piso MARCO 0 Config A')
  - contenção 100% (verdade dentro da janela quando ancora)
  - confiante-e-errado (band alta + errado) = 0
NÃO muta manifest/artefato. Uso:
  python scripts/fase0_prova_motor_MF.py [--repo PATH] [--gold CSV]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# permite rodar de qualquer cwd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.contracts import MotorContext          # noqa: E402
from src.builder.routing.motor.anchor_engine import (                 # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_MF.csv"
PISO = 59.7
MD_CAP = 6000


def _load(repo: Path, rel: str):
    p = repo / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _md_text(repo: Path, e: dict) -> str:
    for k in ("approved_markdown", "curated_markdown", "base_markdown"):
        rel = str(e.get(k) or "")
        p = repo / rel
        if rel and p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:MD_CAP]
            except OSError:
                pass
    return ""


def build_context(repo: Path) -> MotorContext:
    tl = _load(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(repo, "course/.card_block_map.json")
    lessons = (_load(repo, "course/.lessons_index.json") or {}).get("by_date", {})
    return MotorContext.from_artifacts(blocks=blocks, card_block_map=cbm, lessons_index=lessons)


def display_of(ctx: MotorContext, ref: str) -> str:
    b = ctx.block_by_ref(ref)
    return str((b or {}).get("id") or ref)


def collapse(results: dict, rows: list) -> tuple:
    by_pair = defaultdict(list)
    for r in rows:
        if r["id"] in results:
            by_pair[r["pair_key"] or r["id"]].append(results[r["id"]])
    total = len(by_pair)
    ok = sum(int(all(by_pair[k])) for k in by_pair)
    return ok, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--gold", default=str(DEFAULT_GOLD))
    args = ap.parse_args()
    repo, gold_path = Path(args.repo), Path(args.gold)

    if not repo.is_dir():
        print(f"ERRO: repo MF nao encontrado: {repo}", file=sys.stderr)
        return 2

    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    byid = {}
    for e in man.get("entries") or []:
        byid.setdefault(str(e.get("id")), e)

    ctx = build_context(repo)
    eng = AnchorEngine()

    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    scope = [r for r in rows
             if byid.get(r["id"]) and not is_out_of_disamb_scope(byid[r["id"]])]

    results: dict = {}
    contencao_fora = []
    confiante_errado = []
    for r in scope:
        rid, true = r["id"], r["true_block_id"]
        e = byid[rid]
        d = eng.resolve(e, ctx, markdown=_md_text(repo, e))
        if d is None:
            pred = r["computed_block_id"] or ""     # funil = piso (D9)
            results[rid] = (pred == true)
            continue
        pred = display_of(ctx, d.block_ref)
        results[rid] = (pred == true)
        if true and true not in [display_of(ctx, w) for w in d.window]:
            contencao_fora.append((rid, true, d.window))
        if d.band == "alta" and pred != true:
            confiante_errado.append((rid, pred, true))

    ok, tot = collapse(results, scope)
    pct = ok / tot * 100 if tot else 0.0
    print("=" * 70)
    print(f"FASE 0 — motor real  repo={repo.name}  escopo-disamb={tot} (par-colapsado)")
    print(f"  escopo-disamb: {ok}/{tot} = {pct:.1f}%   (piso MARCO 0 A' = {PISO}%)")
    print(f"  contenção fora da janela: {len(contencao_fora)}")
    for x in contencao_fora:
        print(f"    {x}")
    print(f"  confiante-e-errado (band alta): {len(confiante_errado)}")
    for x in confiante_errado:
        print(f"    {x}")
    print("=" * 70)

    ok_number = pct + 1e-9 >= PISO
    ok_conten = not contencao_fora
    ok_conf = not confiante_errado
    verdict = ok_number and ok_conten and ok_conf
    print(f"VEREDITO FASE 0: {'PASS' if verdict else 'FAIL'} "
          f"(num={ok_number} conten={ok_conten} conf={ok_conf})")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Rodar o probe contra o repo MF**

Run: `python scripts/fase0_prova_motor_MF.py`
Expected: imprime `escopo-disamb: NN/MM = XX.X%` com `XX.X >= 59.7`, `contenção fora = 0`, `confiante-e-errado = 0`, e `VEREDITO FASE 0: PASS`.

- [ ] **Step 3: Se FAIL no número (< 59.7%)**

Diagnostique com o marco0 lado a lado (`python scripts/marco0_prova_deterministica.py`): a Config `A'` dele é o alvo. Divergência ⇒ diferença na tokenização/pesos entre `disambiguator._toks`/`_block_signature` e `marco0._toks`/`block_sig`. Ajuste o motor até reproduzir o `A'` (mesma prova, mesmo número). NÃO baixe o piso — o piso é a régua.

- [ ] **Step 4: Rodar suíte inteira do motor**

Run: `python -m pytest tests/test_motor_*.py -v`
Expected: PASS (todos os arquivos test_motor_*).

- [ ] **Step 5: Commit**

```bash
git add scripts/fase0_prova_motor_MF.py
git commit -m "test(motor): probe externo READ-ONLY vs ground_truth_MF (escopo-disamb >=59.7%)"
```

---

## Task 9: Fechar a fase (regressão global + tracker)

**Files:**
- Modify: `docs/reports/pendencias.md` (registrar número da FASE 0 + tensão "Verificação de Programas")

- [ ] **Step 1: Rodar a suíte inteira do repo (não-regressão)**

Run: `python -m pytest -q`
Expected: sem novas falhas. `test_anchor_placement.py` (o anchor velho) permanece intacto — a FASE 0 é ADITIVA, não toca o call-site (isso é FASE 4). Se algo do motor colidir com coleta de testes, isole em `tests/test_motor_*.py`.

- [ ] **Step 2: Registrar o número no tracker**

Edite `docs/reports/pendencias.md`, seção da FASE 0: registre `escopo-disamb MF = XX.X%` (do probe Task 8), `contenção=100%`, `confiante-errado=0`, e a **tensão aberta**: card "Verificação de Programas" com `block_ids: []` no gold embutido → fixture nomeada dos blocos 10-15 fica no probe externo / vira item de calibração da FASE 1 (§12). Aponte também: valores finais de `MARGIN_TAU`/`W_SESSION_LABEL`/`W_TOPIC` calibrados.

- [ ] **Step 3: Commit (só quando o user pedir — disciplina §1)**

```bash
git add docs/reports/pendencias.md
git commit -m "docs(motor): FASE 0 fechada — escopo-disamb XX.X%, contencao 100%, confiante-errado 0"
```

---

## Self-Review (cobertura vs spec)

- **Contratos (spec §3):** `AnchorDecision`/`MotorContext` + 3 `Protocol` — Task 1. AnchorResult final (band/flag/provider serializados no dataclass de produção `anchor_placement.py:77`) fica na **FASE 4** (integração); aqui o dataclass próprio do motor basta para provar READ-ONLY. ✔ (com corte de escopo explícito)
- **WindowProvider P1/P2 (spec §3 Contrato 1, §5):** Task 3. P3/P4 explicitamente FASE 2. ✔
- **Disambiguator len-norm + session-label 1ª classe (spec §3 Contrato 2, §12):** Tasks 4-5. len-norm `sqrt(|sig|)` e `W_SESSION_LABEL>W_TOPIC` são código + teste. ✔
- **Gate D4 (spec §3):** proxy de margem em Task 5; **recall medido = FASE 1** (não implementado aqui, por design). ✔
- **Invariantes ANCHOR-ONLY (spec §4):** motor não escreve nada; janela `[]`→None→funil (Task 6); lógica em `routing/motor/`, nunca `engine.py`. ✔
- **Guard test de imports (spec §7):** Task 2, AST, whitelist documentada. ✔
- **Aceite: escopo-disamb ≥59.7% / contenção 100% / confiante-errado 0 (spec §6/§7):** contenção+confiante-errado em CI (Task 7, gold embutido); número 59.7% no probe externo (Task 8). ✔
- **Régua par-colapsada (spec §2):** probe usa `pair_key` + `scorable==yes` (Task 8). ✔
- **Reúso (spec §8):** `confidence_band` (thresholds), `norm_ascii_lower` (helpers), `normalize_match_text` (text/normalize), estrutura de sinais espelhando `entry_signals`/`concept_resolver`. `concept_token_weights`/`concept_vector` são reúso PERMITIDO — nesta fase a tokenização espelha o MARCO 0 para o número casar; migrar para chamar `concept_token_weights` diretamente é refinamento seguro se a Task 8 exigir (mesma whitelist). ✔

**Tensões surfaçadas (para o user / debate):**
1. **"Verificação de Programas" sem janela no gold embutido** (`block_ids: []`) — a fixture nomeada do §6 (blocos 10-15) NÃO é exercível na CI self-contained; movida para o probe externo. Se o user quiser a fixture na CI, é preciso regenerar o gold com a janela desse card (fora do escopo da FASE 0).
2. **Tokenização duplicada** (motor espelha `marco0._toks`/`_GEN` em vez de chamar `concept_token_weights` de cara) — decisão consciente para garantir paridade com o piso 59.7%; dívida a resolver quando o probe estiver verde (unificar no `concept_resolver`, sem quebrar o guard).
3. **`MARGIN_TAU`/pesos calibrados no gold MF** — risco de overfit a um curso. Mitigação: são só o piso da FASE 0; a FASE 1 remede com RECALL e a FASE 2 traz SO/TCC como contraprova.

---

**Plano completo e salvo em `docs/superpowers/plans/2026-07-03-fase0-motor-atribuicao.md`.**
