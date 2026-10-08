# Matcher posicional bloco→unidade (Plano 2 de C) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o caminho frágil de atribuição bloco→unidade (scorer-keyword/voto sobre tópico ambíguo) por um matcher posicional: afinidade token-overlap (bloco × título+tópicos+aliases da unidade) + preenchimento monotônico ancorado sobre unidades ordenadas, aplicado só a blocos-aula. Mantém o caminho antigo como fallback estreito.

**Architecture:** Módulo novo `src/builder/timeline/unit_matcher.py` (puro, testável). `_build_timeline_index` passa a: resolver tópico por bloco (display), classificar kind, e DEPOIS rodar o matcher posicional sobre os blocos-aula em ordem cronológica. Override manual e `finalize_block` (zera unidade de não-aula) permanecem.

**Tech Stack:** Python 3.11/3.13, pytest.

**Spec:** `docs/superpowers/specs/2026-06-06-precisao-bloco-unidade-design.md` (Parte 2 + bônus guard + Parte 3 guard).

---

## File Structure

- `src/builder/timeline/unit_matcher.py` — **novo**: `score_block_unit_affinity`, `assign_units_positional`, helpers de token, constantes de limiar.
- `src/builder/timeline/index.py` — `_build_timeline_index`: remove atribuição de unidade per-bloco; após o loop, roda o matcher posicional sobre blocos-aula; fallback estreito.
- `src/builder/timeline/conflicts.py` — bônus: `auto_suggested_unit` reflete a sugestão do posicional (campo persistido `auto_unit_slug`).
- `scripts/rebuild_diff.py` — **novo**: rebuild-diff dry-run dos 5 cursos (guard).
- `tests/test_unit_matcher.py` — **novo**: testes do matcher.

---

## Task 1: Afinidade `score_block_unit_affinity`

**Files:**
- Create: `src/builder/timeline/unit_matcher.py`
- Test: `tests/test_unit_matcher.py` (novo)

- [ ] **Step 1: Write the failing test**

Criar `tests/test_unit_matcher.py`:

```python
"""Matcher posicional bloco->unidade: afinidade token-overlap + anchor-fill."""

from src.builder.timeline.unit_matcher import score_block_unit_affinity


def _unit(slug, title, *topic_labels):
    return {"slug": slug, "title": title,
            "topics": [{"label": t, "aliases": []} for t in topic_labels]}


def _block(*session_labels, topic_text=""):
    return {"sessions": [{"label": s} for s in session_labels], "topic_text": topic_text}


U_REC = _unit("unidade-01-conjuntos", "Conjuntos Enumeraveis e Funcoes Recursivas",
              "Conjuntos Enumeraveis", "Funcoes Recursivas Primitivas")
U_TUR = _unit("unidade-02-turing", "Turing e Computabilidade",
              "Maquinas de Turing", "Conjectura de Church-Turing")


def test_affinity_matches_recursivas_to_unit01_not_turing():
    b = _block("funcoes recursivas primitivas", topic_text="funcoes recursivas")
    assert score_block_unit_affinity(b, U_REC) > score_block_unit_affinity(b, U_TUR)


def test_affinity_matches_turing_block_to_turing_unit():
    b = _block("maquinas de turing")
    assert score_block_unit_affinity(b, U_TUR) > score_block_unit_affinity(b, U_REC)


def test_affinity_zero_when_no_overlap():
    b = _block("feriado nacional")
    assert score_block_unit_affinity(b, U_REC) == 0.0


def test_affinity_ignores_stopwords_and_short_tokens():
    # "de", "e" (stopwords) e tokens <3 nao contam
    b = _block("a de e")
    assert score_block_unit_affinity(b, U_REC) == 0.0
```

- [ ] **Step 2: Run to confirm FAIL**

Run: `python -m pytest tests/test_unit_matcher.py -v`
Expected: `ModuleNotFoundError: ...unit_matcher`.

- [ ] **Step 3: Implement** `src/builder/timeline/unit_matcher.py`

```python
"""Matcher posicional bloco->unidade.

Afinidade = overlap de tokens entre o conteudo do bloco (labels de sessao +
topic_text) e a unidade (titulo + labels/aliases dos topicos), com stopwords PT
e tokens curtos filtrados. Mais forte/especifico que o scorer-keyword antigo, que
casava contra o NOME da unidade (confundia "computavel"~"computabilidade").

`assign_units_positional` alinha blocos-aula (ordem cronologica) a unidades
(ordem do plano) por anchor-fill monotonico: ancoras (vencedor com margem)
progridem nao-decrescente; ancora fraca fora de ordem e rebaixada; blocos sem
sinal herdam a unidade da ancora anterior.
"""

from __future__ import annotations

import re
from typing import List, Mapping, Sequence, Tuple

from src.utils.helpers import norm_ascii_lower

# Stopwords PT + tokens genericos que nao discriminam unidade/topico.
_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "para", "com",
    "em", "no", "na", "nos", "nas", "ao", "aos", "um", "uma", "sobre", "que",
    "introducao", "aula", "parte", "modulo",
}
_UNIT_GENERIC = {"unidade", "aprendizagem", "visao", "geral"}

ANCHOR_MIN_MARGIN = 1.0   # margem minima (winner - runnerup) p/ virar ancora
STRONG_MARGIN = 3.0       # margem p/ ancora forte quebrar a ordem (fora de ordem)


def _tokens(text: str) -> set:
    """Tokens alfabeticos >=3 chars, sem acento/stopword."""
    norm = norm_ascii_lower(text or "")
    return {t for t in re.findall(r"[a-z]+", norm) if len(t) >= 3 and t not in _STOPWORDS}


def _block_tokens(block: Mapping) -> set:
    parts = [str(s.get("label", "")) for s in (block.get("sessions") or []) if isinstance(s, Mapping)]
    parts.append(str(block.get("topic_text", "") or ""))
    return _tokens(" ".join(parts))


def _unit_tokens(unit: Mapping) -> set:
    parts = [str(unit.get("title", "") or "")]
    for t in unit.get("topics", []) or []:
        if isinstance(t, Mapping):
            parts.append(str(t.get("label", "") or ""))
            parts.extend(str(a) for a in (t.get("aliases") or []))
    return _tokens(" ".join(parts)) - _UNIT_GENERIC


def score_block_unit_affinity(block: Mapping, unit: Mapping) -> float:
    """Overlap de tokens entre bloco e unidade (0.0 se nenhum)."""
    return float(len(_block_tokens(block) & _unit_tokens(unit)))


def assign_units_positional(
    class_blocks: Sequence[Mapping], units: Sequence[Mapping]
) -> List[Tuple[str, float]]:
    """(unit_slug, confidence) por bloco-aula, em ordem. [] se inaplicavel.

    Inaplicavel: <2 unidades, sem blocos, ou nenhuma ancora (sinaliza fallback).
    """
    if len(units) < 2 or not class_blocks:
        return []
    uslugs = [str(u.get("slug", "") or "") for u in units]
    utoks = [_unit_tokens(u) for u in units]

    # matriz de afinidade + deteccao de ancora por bloco
    aff_rows: List[List[float]] = []
    anchors: List[Tuple[int, int, float]] = []  # (block_idx, unit_idx, margin)
    for i, b in enumerate(class_blocks):
        bt = _block_tokens(b)
        aff = [float(len(bt & ut)) for ut in utoks]
        aff_rows.append(aff)
        order = sorted(range(len(units)), key=lambda j: aff[j], reverse=True)
        win = order[0]
        ws = aff[win]
        rs = aff[order[1]] if len(order) > 1 else 0.0
        if ws > 0 and (ws - rs) >= ANCHOR_MIN_MARGIN:
            anchors.append((i, win, ws - rs))

    if not anchors:
        return []

    # passada monotonica: mantem nao-decrescente; ancora fraca fora de ordem cai
    kept: List[Tuple[int, int]] = []
    strong: set = set()
    cur = -1
    for (i, u, m) in anchors:
        if u >= cur:
            kept.append((i, u)); cur = u
            if m >= STRONG_MARGIN:
                strong.add(i)
        elif m >= STRONG_MARGIN:
            kept.append((i, u)); cur = u; strong.add(i)
        # senao: rebaixa (ignora)
    if not kept:
        return []

    anchor_idx = {i for (i, _) in kept}
    assign: List[int] = [-1] * len(class_blocks)
    for (i, u) in kept:
        assign[i] = u
    # preenchimento: herda a unidade da ancora anterior; antes da 1a ancora usa a 1a
    cur_u = kept[0][1]
    for i in range(len(class_blocks)):
        if assign[i] >= 0:
            cur_u = assign[i]
        else:
            assign[i] = cur_u

    out: List[Tuple[str, float]] = []
    for i in range(len(class_blocks)):
        if i in strong:
            conf = 0.8
        elif i in anchor_idx:
            conf = 0.6
        else:
            conf = 0.4
        out.append((uslugs[assign[i]], conf))
    return out
```

- [ ] **Step 4: Run to confirm PASS**

Run: `python -m pytest tests/test_unit_matcher.py -k affinity -v` (4 pass)

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/unit_matcher.py tests/test_unit_matcher.py
git commit -m "feat(timeline): token-overlap block-unit affinity scorer"
```

---

## Task 2: Anchor-fill monotônico `assign_units_positional`

**Files:**
- Modify: `src/builder/timeline/unit_matcher.py` (já criado na Task 1 — a função já está; aqui só os testes)
- Test: `tests/test_unit_matcher.py` (APPEND)

> Nota: a Task 1 já implementou `assign_units_positional` no módulo. Esta task valida o comportamento de alinhamento com testes dedicados (RED→GREEN sobre a lógica já presente; se algum falhar, corrigir a função na Task 1's file).

- [ ] **Step 1: Append tests**

```python
from src.builder.timeline.unit_matcher import assign_units_positional

UNITS3 = [
    _unit("u1", "Alfa", "alfa primeiro tema", "alfa segundo tema"),
    _unit("u2", "Beta", "beta terceiro tema", "beta quarto tema"),
    _unit("u3", "Gama", "gama quinto tema", "gama sexto tema"),
]


def test_positional_strong_anchors_in_order():
    blocks = [_block("alfa primeiro"), _block("beta terceiro"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert [s for s, _ in out] == ["u1", "u2", "u3"]


def test_positional_fills_no_signal_block_between_anchors():
    # meio sem sinal -> herda a unidade da ancora anterior (u1)
    blocks = [_block("alfa primeiro"), _block("xyz sem sinal"), _block("alfa segundo")]
    out = assign_units_positional(blocks, UNITS3)
    assert [s for s, _ in out] == ["u1", "u1", "u1"]


def test_positional_weak_out_of_order_anchor_demoted():
    # bloco 2 tem leve sinal de u1 mas vem depois de u2 -> rebaixado, segue u2
    blocks = [_block("beta terceiro tema"), _block("alfa"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[0][0] == "u2" and out[2][0] == "u3"
    assert out[1][0] in ("u2",)  # nao recua pra u1 (ancora fraca rebaixada)


def test_positional_empty_when_no_anchor():
    blocks = [_block("xyz"), _block("qwe")]
    assert assign_units_positional(blocks, UNITS3) == []


def test_positional_empty_when_single_unit():
    assert assign_units_positional([_block("alfa")], [UNITS3[0]]) == []
```

- [ ] **Step 2: Run** `python -m pytest tests/test_unit_matcher.py -k positional -v`
Expected: PASS (se algum falhar, ajustar `assign_units_positional`).

- [ ] **Step 3..5: corrigir se necessário + commit**

```bash
git add src/builder/timeline/unit_matcher.py tests/test_unit_matcher.py
git commit -m "test(timeline): anchor-fill monotonic alignment cases"
```

---

## Task 3: Wire posicional no `_build_timeline_index` + fallback estreito

**Files:**
- Modify: `src/builder/timeline/index.py` (import topo; loop ~2197-2210 remove unit per-bloco; bloco novo após o loop ~2211-2224)
- Test: `tests/test_unit_matcher.py` (APPEND — integração)

- [ ] **Step 1: Write the failing test (integração via build)**

```python
import json
from pathlib import Path


def test_real_metodos_recursivas_or_hoare_units_sane(tmp_path=None):
    # Integra via engine no curso real Metodos (skip se ausente). Verifica que
    # blocos com sinal forte caem na unidade certa pelo posicional.
    import os
    from src.models.core import SubjectStore
    import src.builder.engine as engine
    base = os.environ.get("TUTOR_COURSES_DIR", r"C:\Users\Humberto\Documents\GitHub")
    repo = Path(base) / "Metodos-Formais-Tutor"
    if not repo.exists():
        import pytest
        pytest.skip("corpus indisponivel")
    sp = SubjectStore().get("Metodos-Formais")
    cm = json.loads((repo / "manifest.json").read_text(encoding="utf-8")).get("course", {})
    ctx = engine._build_file_map_timeline_context_from_course({**cm, "_repo_root": repo}, sp, content_taxonomy=None)
    blocks = ctx["timeline_index"]["blocks"]
    by_label = {(b.get("primary_topic_label") or "").lower(): b for b in blocks}
    hoare = next((b for k, b in by_label.items() if "hoare" in k), None)
    if hoare:
        assert "verificacao-de-programas" in (hoare.get("unit_slug") or "")
```

(Teste tolerante: só afirma o caso forte "Hoare→verificação-de-programas" quando presente; o rebuild-diff da Task 6 cobre o resto.)

- [ ] **Step 2: Run** — provavelmente FAIL antes do wiring (Hoare hoje cai em unidade errada via caminho frágil).

- [ ] **Step 3: Implement wiring** em `src/builder/timeline/index.py`

(a) Import no topo (perto dos outros imports de timeline):
```python
from src.builder.timeline.unit_matcher import assign_units_positional
```

(b) No loop de montagem, **remover** o bloco de atribuição de unidade per-bloco (linhas ~2197-2210, do `topic_unit_slug = ""` até `runtime_block["unit_confidence"] = unit_confidence`). Manter a resolução de tópico/label acima (não mexer). O bloco fica sem unidade no loop.

(c) **Após** o loop (antes do bloco de soft-continuation ~2213), inserir:
```python
    # Kind precisa estar resolvido antes de separar blocos-aula.
    for block in runtime_blocks:
        ensure_block_kind(block)

    units_ordered = list((content_taxonomy or {}).get("units", []) or [])
    class_blocks = [b for b in runtime_blocks if b.get("kind") == BlockKind.CLASS.value]
    positional = assign_units_positional(class_blocks, units_ordered)
    if positional:
        for b, (slug, conf) in zip(class_blocks, positional):
            b["unit_slug"] = slug
            b["unit_confidence"] = conf
            b["auto_unit_slug"] = slug  # sugestao auto (pre-override) p/ guard
    else:
        # Fallback estreito: caminho antigo por bloco-aula (curso sem unidades
        # ordenadas / sem ancora). Override manual e finalize_block ainda agem.
        # NAO reconstroi TopicMatchResult: o topic-derive confiante praticamente
        # nunca dispara (ver investigacao); _assign -> _vote basta.
        for b in class_blocks:
            us, uc = _assign_timeline_block_to_unit(b, unit_index)
            if not us:
                us, uc = _vote_unit_from_topic_candidates(b, unit_index)
            b["unit_slug"] = us
            b["unit_confidence"] = uc
            if us:
                b["auto_unit_slug"] = us
```

(d) Manter o bloco de soft-continuation (~2213-2221) e `finalize_block` (~2223-2224)
inalterados. (Soft-continuation só preenche blocos-aula sem unidade — ainda útil
para os que o posicional não cobriu; revisar via rebuild-diff se virou redundante.)

(e) Garantir `BlockKind` importado em index.py (já está, da task anterior).

- [ ] **Step 4: Run** integração + suíte:
`python -m pytest tests/test_unit_matcher.py -q`
`python -m pytest -q` (suíte completa verde — anotar total)

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline/index.py tests/test_unit_matcher.py
git commit -m "feat(timeline): positional unit matcher as primary, narrow fallback"
```

---

## Task 4: Persistir `auto_unit_slug` (serializer + schema)

**Files:**
- Modify: `src/builder/timeline/index.py` (`_serialize_timeline_index`)
- Modify: `schemas/timeline_index.v4.json`
- Test: `tests/test_unit_matcher.py` (APPEND)

- [ ] **Step 1: Test**

```python
def test_serializer_keeps_auto_unit_slug():
    from src.builder.timeline.index import _serialize_timeline_index
    blk = {"id": "b", "kind": "class", "unit_slug": "u1", "auto_unit_slug": "u1",
           "period_start": "2026-03-01", "period_end": "2026-03-01"}
    out = _serialize_timeline_index({"version": 4, "blocks": [blk]})
    assert out["blocks"][0].get("auto_unit_slug") == "u1"
```

- [ ] **Step 2: Run** → FAIL (campo não serializado).

- [ ] **Step 3: Implement**
Em `_serialize_timeline_index`, junto dos campos opcionais (perto de `source_kind`):
```python
        auto_unit_slug = block.get("auto_unit_slug")
        if auto_unit_slug:
            payload["auto_unit_slug"] = auto_unit_slug
```
Em `schemas/timeline_index.v4.json`, nas propriedades do bloco (perto de `source_kind`):
```json
        "auto_unit_slug": { "type": "string" },
```
(opcional; `additionalProperties: true` já aceita.)

- [ ] **Step 4: Run** `python -m pytest tests/test_unit_matcher.py tests/test_timeline_schema.py -q` (pass)

- [ ] **Step 5: Commit**
```bash
git add src/builder/timeline/index.py schemas/timeline_index.v4.json tests/test_unit_matcher.py
git commit -m "feat(timeline): persist auto_unit_slug (positional suggestion) for guard"
```

---

## Task 5: Bônus — `auto_suggested_unit` reflete o posicional

**Files:**
- Modify: `src/builder/timeline/conflicts.py` (`auto_suggested_unit`)
- Test: `tests/test_curation_conflicts.py` (APPEND)

- [ ] **Step 1: Test**

```python
def test_auto_suggested_unit_prefers_auto_unit_slug():
    from src.builder.timeline.conflicts import auto_suggested_unit
    block = {"auto_unit_slug": "unidade-01-conjuntos", "unit_confidence": 0.8,
             "topic_ambiguous": True, "primary_topic_confidence": 0.2,
             "topic_candidates": [{"unit_slug": "unidade-02-turing"}]}
    slug, conf = auto_suggested_unit(block)
    assert slug == "unidade-01-conjuntos"
```

- [ ] **Step 2: Run** → FAIL (hoje usa topic_candidates[0]).

- [ ] **Step 3: Implement**
Em `auto_suggested_unit`, no início (antes da lógica de topic_candidates):
```python
    auto = str(block.get("auto_unit_slug") or "").strip()
    if auto:
        conf = float(block.get("unit_confidence") or 0.0)
        return (auto, conf)
```
(Mantém o resto como fallback p/ blocos sem `auto_unit_slug`.)

- [ ] **Step 4: Run** `python -m pytest tests/test_curation_conflicts.py -q` (pass — incluindo os antigos)

- [ ] **Step 5: Commit**
```bash
git add src/builder/timeline/conflicts.py tests/test_curation_conflicts.py
git commit -m "feat(timeline): conflict guard uses positional auto_unit_slug suggestion"
```

---

## Task 6: Script rebuild-diff (guard de regressão)

**Files:**
- Create: `scripts/rebuild_diff.py`

- [ ] **Step 1: Implement** `scripts/rebuild_diff.py`

```python
"""Rebuild-diff dry-run dos cursos reais: compara unit_slug/kind por bloco
(indice gravado x rebuild com o codigo atual). NAO grava. Guard de regressao
do matcher posicional.

Uso: python scripts/rebuild_diff.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.core import SubjectStore  # noqa: E402
import src.builder.engine as engine  # noqa: E402
from src.builder.timeline.index import _serialize_timeline_index  # noqa: E402

BASE = Path(os.environ.get("TUTOR_COURSES_DIR", r"C:\Users\Humberto\Documents\GitHub"))


def diff_course(name: str, sp) -> None:
    repo = Path(getattr(sp, "repo_root", "") or "")
    idx_path = repo / "course" / ".timeline_index.json"
    if not idx_path.exists():
        print(f"[skip] {name}: sem indice ({idx_path})")
        return
    old = {b.get("id"): b for b in json.loads(idx_path.read_text(encoding="utf-8")).get("blocks", [])}
    cm = json.loads((repo / "manifest.json").read_text(encoding="utf-8")).get("course", {}) if (repo / "manifest.json").exists() else {}
    ctx = engine._build_file_map_timeline_context_from_course({**cm, "_repo_root": repo}, sp, content_taxonomy=None)
    new = _serialize_timeline_index(ctx.get("timeline_index") or {"version": 4, "blocks": []})
    print(f"=== {name} ({len(new['blocks'])} blocos) ===")
    changed = 0
    for b in new["blocks"]:
        ob = old.get(b["id"], {})
        du = (ob.get("unit_slug", ""), b.get("unit_slug", ""))
        dk = (ob.get("kind", ""), b.get("kind", ""))
        if du[0] != du[1] or dk[0] != dk[1]:
            changed += 1
            print(f"  {b['id']:9} unit {du[0][:20] or '-'} -> {du[1][:20] or '-'} | kind {dk[0] or '-'} -> {dk[1] or '-'} | {(b.get('primary_topic_label') or '')[:30]}")
    print(f"  ({changed} blocos mudaram)\n")


def main() -> int:
    store = SubjectStore()
    for name in store.names():
        sp = store.get(name)
        if sp is not None:
            diff_course(name, sp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Rodar e revisar (NÃO grava nada)**

Run: `python scripts/rebuild_diff.py`
Revisar a saída: deltas coerentes? Provas viram assessment sem unidade? Blocos-aula
com unidade plausível na progressão (early→U1, etc.)? Casos óbvios como
recursivas→U1 e Hoare→verificação-de-programas resolvidos? **Não há critério
automático** — é revisão humana (controller resume + julga). Registrar achados.

- [ ] **Step 3: Commit do script**

```bash
git add scripts/rebuild_diff.py
git commit -m "tooling(timeline): rebuild-diff dry-run guard for unit/kind deltas"
```

---

## Task 7: Verificação final

- [ ] **Step 1:** `python -m pytest -q` — suíte completa verde (anotar total).
- [ ] **Step 2:** Rodar `python scripts/rebuild_diff.py` e colar o resumo dos deltas no relatório final pro usuário revisar antes de qualquer regravação de índices.
- [ ] **Step 3:** Sanidade: recursivas→unidade-01 e Hoare→verificação-de-programas no rebuild (via rebuild_diff ou one-liner).

---

## Notas de execução

- **NÃO** regravar os `.timeline_index.json` dos cursos reais neste plano — só
  dry-run/diff. A regravação (reprocess) é decisão do usuário após revisar os deltas.
- Limiares `ANCHOR_MIN_MARGIN=1.0` / `STRONG_MARGIN=3.0` são ponto de partida;
  se o rebuild-diff mostrar sobre/sub-segmentação, ajustar (reportar antes de mudar).
- Hook `code-review-graph.exe` imprime `UnicodeEncodeError` cosmético (cp1252); o
  commit **passa**. Ignorar.
- Trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- `norm_ascii_lower` é público em `src/utils/helpers.py` (promovido no Plano 1).
- A separação em `unit_matcher.py` evita inchar mais o `index.py` (já grande).
