# Janela-de-prazo TIER 2 (provider due-window) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provider due-window no motor: due-date por-assignment (Moodle) → bloco cuja janela contém o due; 8 rows TIER-2 do gold MF saem de 1/8 para 4/8 sem tocar o funil.

**Architecture:** Produtor burro (extração emite `assign_dues` por módulo, sem colapsar, no card map — aditivo) + motor esperto (`due_window.py`: escopo por categoria, matching por stem, containment/straddle). Probe `fase5_prova_tier2.py` crava baseline 1/8 ANTES de qualquer código de produção.

**Tech Stack:** Python 3.13, pytest, stdlib only (re/datetime/csv/json). Zero dependência nova, zero rede no motor.

**Spec:** `docs/superpowers/specs/2026-07-22-janela-de-prazo-tier2-design.md`

## Global Constraints

- Lógica nova SÓ em `src/builder/routing/motor/` + `src/builder/sources/moodle_labels.py` (produtor) + `scripts/`. NUNCA `engine.py` (guard AST `test_motor_import_guard` ativo).
- Flag-OFF byte-idêntico: nada muda sem `use_anchor_engine`.
- READ-ONLY nos repos-tutor: probes copiam manifest em memória/tmp, nunca gravam.
- Gold (`ground_truth_MF.csv`) intocado. Pré-gate `python scripts/audit_gold_freshness.py` (exit 0) antes de QUALQUER medição.
- Pisos em FRAÇÃO EXATA: baseline `1/8`, alvo `4/8`, confident-wrong `0` (precedente F1 — nunca float arredondado).
- Régua existente (6 probes fase0/1/2-SO/2-TCC/3/4) com números IDÊNTICOS ao fim de cada task.
- Scripts novos com shim UTF-8 (`sys.stdout.reconfigure(encoding="utf-8", errors="replace")`).
- Medição FAIL = resultado honesto; proibido re-tuning de piso (spec-mãe §12 regra 4).
- Commits nesta branch (`feat/motor-atribuicao`); mensagens estilo `feat(motor)`/`test(motor)`/`docs(f5)`.

---

### Task 1: Probe `fase5_prova_tier2.py` — baseline 1/8 ANTES de código

**Files:**
- Create: `scripts/fase5_prova_tier2.py`

**Interfaces:**
- Consumes: `apply_anchor_engine(entries, repo_dir, course_name, enabled, voter, markdown_fn)` (motor/apply.py), `build_motor_context(repo, course_name)` (motor/context.py), `is_out_of_disamb_scope(entry)` (motor/anchor_engine.py), `true_of(ctx, row)`/`_md_text` (scripts/fase0_prova_motor_MF.py).
- Produces: probe CLI `python scripts/fase5_prova_tier2.py [--repo PATH] [--gold CSV]`; exit 0 = PASS. Task 4 re-roda este probe sem modificá-lo.

- [ ] **Step 1: Escrever o probe**

```python
#!/usr/bin/env python3
"""FASE 5 — prova TIER-2 (janela-de-prazo): 8 rows out-of-scope do gold MF.

Universo DECLARADO: rows scorable==yes com is_out_of_disamb_scope(entry)==True
(8 rows: t1/t2/t1-thy/revisao-p1-gabarito/plano/eth2/aws/archive). Campo medido =
atribuicao EFETIVA pos-motor flag-ON: temporal_block_id se existir, senao
computed_block_id (ambos resolvidos a display via ctx.block_by_ref).

Modos (auto-detectados):
  baseline-only  nenhum card do card map tem assign_dues -> exige acc == BASELINE (1/8)
  target         algum card tem assign_dues             -> exige acc >= TARGET (4/8) e cw == 0

PRE-GATE: rode scripts/audit_gold_freshness.py antes de medir.
"""
from __future__ import annotations

import argparse
import copy
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.builder.routing.motor.apply import apply_anchor_engine        # noqa: E402
from src.builder.routing.motor.context import build_motor_context      # noqa: E402
from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope  # noqa: E402
from fase0_prova_motor_MF import _md_text, true_of                     # noqa: E402

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = ROOT / "docs" / "reports" / "ground_truth_MF.csv"
BASELINE = (1, 8)   # fracao exata: funil hoje (so revisao-p1-gabarito)
TARGET = (4, 8)     # fracao exata: + t1, t2, t1-thy via due-window


def _load_manifest_entries(repo: Path) -> list:
    import json
    m = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    return m.get("files") or m.get("entries") or []


def _effective_display(e: dict, ctx) -> str:
    ref = str(e.get("temporal_block_id") or "").strip()
    if not ref:
        ref = str(e.get("computed_block_id") or "").strip()
    if not ref:
        return ""
    block = ctx.block_by_ref(ref)
    return str((block or {}).get("id") or ref)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    args = ap.parse_args()

    ctx = build_motor_context(args.repo, "Metodos Formais")
    if not ctx.blocks:
        print("FAIL: contexto sem blocos"); return 1
    entries = copy.deepcopy(_load_manifest_entries(args.repo))
    apply_anchor_engine(entries, args.repo, "Metodos Formais",
                        enabled=True, voter=None, markdown_fn=lambda e: _md_text(args.repo, e))

    rows = [r for r in csv.DictReader(open(args.gold, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    byid = {str(e.get("id")): e for e in entries}
    universe, ok, cw = [], 0, 0
    for r in rows:
        e = byid.get(r["id"])
        if e is None or not is_out_of_disamb_scope(e):
            continue
        universe.append(r["id"])
        pred = _effective_display(e, ctx)
        truth = true_of(ctx, r)
        hit = (pred == truth)
        ok += int(hit)
        if (str(e.get("temporal_block_band") or "") == "alta"
                and not e.get("temporal_block_flag") and not hit):
            cw += 1
        print(f"  {r['id']:38s} pred={pred or '-':10s} true={truth:10s} {'OK' if hit else 'X'}")

    n = len(universe)
    has_dues = any((v or {}).get("assign_dues")
                   for v in (ctx.card_block_map or {}).values() if isinstance(v, dict))
    mode = "target" if has_dues else "baseline-only"
    print(f"\nuniverso={n} rows out-of-scope · modo={mode} · acc={ok}/{n} · confident-wrong={cw}")

    if n != BASELINE[1]:
        print(f"FAIL: universo {n} != {BASELINE[1]} declarado (gold mudou? re-declarar)"); return 1
    if mode == "baseline-only":
        want = BASELINE[0]
        verdict = (ok == want)
        print("assign_dues AUSENTE -> baseline-only (nao conta como PASS do alvo)")
        print(f"{'PASS' if verdict else 'FAIL'}: acc {ok}/{n} vs baseline exigido {want}/{n}")
        return 0 if verdict else 1
    verdict = (ok >= TARGET[0]) and (cw == 0)
    print(f"{'PASS' if verdict else 'FAIL'}: acc {ok}/{n} vs piso {TARGET[0]}/{TARGET[1]} · cw={cw} (exigido 0)")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Pré-gate + rodar baseline**

Run: `python scripts/audit_gold_freshness.py` — Expected: exit 0 (warnings ZERO_OVERLAP = informativos).
Run: `python scripts/fase5_prova_tier2.py`
Expected: `universo=8 · modo=baseline-only · acc=1/8` → `PASS`. Se acc != 1/8: PARAR — baseline declarado no spec está errado, reportar ao controller antes de seguir (proibido ajustar o número pra passar).

- [ ] **Step 3: Regressão rápida da régua existente**

Run: `python scripts/fase4_prova_D9.py`
Expected: PASS com os mesmos números de sempre (det 48/58 cw1 · voter all-cache 51/58 cw0 · 0 chamadas API). O probe novo é read-only — qualquer delta aqui é bug do probe.

- [ ] **Step 4: Commit**

```bash
git add scripts/fase5_prova_tier2.py
git commit -m "test(f5): probe fase5_prova_tier2 - baseline 1/8 nas rows TIER-2 do gold MF cravado antes de codigo"
```

---

### Task 2: Produtor — `extract_assign_deadlines_detailed` + `assign_dues` no card map

**Files:**
- Modify: `src/builder/sources/moodle_labels.py` (após `extract_assign_deadlines`, ~linha 230)
- Modify: `src/builder/sources/moodle.py:513-517` (`backfill_repo_signals_consumed`)
- Test: `tests/test_moodle_assign_dues.py` (novo)

**Interfaces:**
- Consumes: `sanitize_folder_name`, `_DEADLINE_NAME`, `_iso` (já existem em moodle_labels.py).
- Produces: `extract_assign_deadlines_detailed(contents, year: int = 0) -> dict` retornando `{secao_sanitizada: [{"name": str, "due": iso_str, "source": "structured"|"named"}]}`; card map entries ganham chave `assign_dues` (lista) — Task 3 lê exatamente este shape.

- [ ] **Step 1: Teste falhando da extração**

```python
"""Testes do produtor assign_dues (janela-de-prazo TIER 2, spec 2026-07-22)."""
import json

from src.builder.sources.moodle_labels import extract_assign_deadlines_detailed
from src.builder.sources.moodle import backfill_repo_signals_consumed


def _contents_tde():
    return [
        {"name": "TDE Trabalho Discente Efetivo", "modules": [
            {"modname": "resource", "name": "t1_2026_1.pdf"},
            {"modname": "assign", "name": "Entrega T1",
             "dates": [{"dataid": "duedate", "timestamp": 1781146800}]},   # 2026-06-10 local
            {"modname": "assign", "name": "Entrega T2 (29/06)", "dates": []},
        ]},
        {"name": "Materiais", "modules": [
            {"modname": "resource", "name": "aula01.pdf"},
        ]},
    ]


def test_detailed_um_item_por_modulo_sem_colapsar():
    out = extract_assign_deadlines_detailed(_contents_tde(), year=2026)
    dues = out["TDE Trabalho Discente Efetivo"]
    assert len(dues) == 2
    by_name = {d["name"]: d for d in dues}
    assert by_name["Entrega T1"]["source"] == "structured"
    assert by_name["Entrega T1"]["due"] == "2026-06-10"
    assert by_name["Entrega T2 (29/06)"] == {
        "name": "Entrega T2 (29/06)", "due": "2026-06-29", "source": "named"}


def test_detailed_secao_sem_fonte_fica_fora():
    out = extract_assign_deadlines_detailed(_contents_tde(), year=2026)
    assert "Materiais" not in out


def test_detailed_named_exige_entrega_no_nome():
    contents = [{"name": "X", "modules": [
        {"modname": "forum", "name": "Avisos (10/06)"}]}]
    assert extract_assign_deadlines_detailed(contents, year=2026) == {}


def test_backfill_grava_assign_dues_aditivo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    (repo / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": []}), encoding="utf-8")
    stats = backfill_repo_signals_consumed(
        repo, _contents_tde(), {"name": "MF", "semester": "2026/1"}, write=True)
    card_map = json.loads(
        (repo / "course" / ".card_block_map.json").read_text(encoding="utf-8"))
    entry = card_map["TDE Trabalho Discente Efetivo"]
    assert entry.get("assign_due")                       # legado intacto
    assert len(entry["assign_dues"]) == 2                # novo, sem colapso
    assert stats["card_labels"] >= 1
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_moodle_assign_dues.py -q`
Expected: FAIL — `ImportError: cannot import name 'extract_assign_deadlines_detailed'`.

- [ ] **Step 3: Implementar a extração (moodle_labels.py, logo após `extract_assign_deadlines`)**

```python
def extract_assign_deadlines_detailed(contents, year: int = 0) -> dict:
    """{secao_sanitizada: [{name, due, source}]} — UM item por módulo, sem colapsar.

    Mesma cascata POR MÓDULO da versão colapsada: (1) assign com
    dates[dataid=duedate] -> source="structured"; (2) assign/forum com "entrega"
    no nome e data `(DD/MM[/AAAA])` -> source="named". Módulo sem fonte fica
    fora; seção sem itens fica fora (nunca inventa). Consumidor: motor/due_window.
    """
    from datetime import datetime
    out: dict = {}
    for sec in contents or []:
        name = sanitize_folder_name(str(sec.get("name") or ""))
        if not name:
            continue
        items: list = []
        for mod in sec.get("modules", []) or []:
            modname = str(mod.get("modname") or "")
            mod_name = str(mod.get("name") or "")
            due = source = ""
            if modname == "assign":
                for d in mod.get("dates") or []:
                    if str(d.get("dataid") or "") == "duedate" and d.get("timestamp"):
                        try:
                            due = datetime.fromtimestamp(int(d["timestamp"])).date().isoformat()
                            source = "structured"
                        except (ValueError, OSError, OverflowError):
                            due = ""
                        break
            if (not due and modname in ("assign", "forum")
                    and "entrega" in mod_name.lower()):
                m = _DEADLINE_NAME.search(mod_name)
                if m:
                    due = _iso(m.group(1), year)
                    source = "named"
            if due:
                items.append({"name": mod_name, "due": due, "source": source})
        if items:
            out[name] = items
    return out
```

- [ ] **Step 4: Wiring no backfill (moodle.py, dentro do bloco do card map, após o loop de `extract_assign_deadlines`)**

O trecho atual (moodle.py:513-517):

```python
            for _card, _due in extract_assign_deadlines(contents, year).items():
                if _card in derived:
                    derived[_card]["assign_due"] = _due
                else:
                    derived[_card] = {"block_ids": [], "source": "labels", "assign_due": _due}
```

ganha logo abaixo (import junto do bloco `from src.builder.sources.moodle_labels import (...)` na linha 503, adicionando `extract_assign_deadlines_detailed`):

```python
            for _card, _lst in extract_assign_deadlines_detailed(contents, year).items():
                if _card in derived:
                    derived[_card]["assign_dues"] = _lst
                else:
                    derived[_card] = {"block_ids": [], "source": "labels", "assign_dues": _lst}
```

Nota de comportamento (documentada, sem código): `merge_card_block_map` nunca sobrescreve entry `source=="manual"` — card manual não ganha `assign_dues`; manual vence por design (D1 da spec-mãe).

- [ ] **Step 5: Rodar testes**

Run: `python -m pytest tests/test_moodle_assign_dues.py -q`
Expected: 4 passed. Nota: o teste do timestamp usa 1781146800; se o fuso da máquina deslocar o dia, ajustar o timestamp do FIXTURE (nunca a implementação) para meio-dia local: `datetime(2026, 6, 10, 12).timestamp()`.

- [ ] **Step 6: Regressão do produtor + suite**

Run: `python -m pytest tests/ -q -k "moodle or labels or card_block"`
Expected: tudo verde (a colapsada continua intocada; consumidores legados idem).

- [ ] **Step 7: Commit**

```bash
git add src/builder/sources/moodle_labels.py src/builder/sources/moodle.py tests/test_moodle_assign_dues.py
git commit -m "feat(motor-producer): extract_assign_deadlines_detailed + assign_dues aditivo no card map (um due por modulo assign, sem colapso)"
```

---

### Task 3: Motor — `due_window.py` (tier2_due_scope, matching, containment/straddle)

**Files:**
- Create: `src/builder/routing/motor/due_window.py`
- Test: `tests/test_motor_due_window.py` (novo)

**Interfaces:**
- Consumes: `AnchorDecision`, `MotorContext` (motor/contracts.py); `norm_ascii_lower` (src/utils/helpers).
- Produces: `tier2_due_scope(entry: dict) -> bool` e `resolve_due_window(entry: dict, ctx: MotorContext) -> Optional[AnchorDecision]` — Task 4 pluga exatamente estas duas no apply.py. Decision: `provider="due-window"`, `method` ∈ {"due-contain","due-straddle"}, `band` ∈ {"alta","media"}, `block_ref` no grão DISPLAY (`block["id"]`), `window=[display_id]`.

- [ ] **Step 1: Testes falhando**

```python
"""Provider due-window (TIER 2 janela-de-prazo, spec 2026-07-22).

Fixtures sintéticas espelham o caso real MF: blocos 15 (2026-06-01..10) e
16 (2026-06-15..29); card TDE com dues por módulo.
"""
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.due_window import tier2_due_scope, resolve_due_window


def _ctx(card_map=None):
    blocks = [
        {"id": "bloco-07", "block_uuid": "u07", "period_start": "2026-04-15", "period_end": "2026-04-15"},
        {"id": "bloco-08", "block_uuid": "u08", "period_start": "2026-04-20", "period_end": "2026-04-20"},
        {"id": "bloco-15", "block_uuid": "u15", "period_start": "2026-06-01", "period_end": "2026-06-10"},
        {"id": "bloco-16", "block_uuid": "u16", "period_start": "2026-06-15", "period_end": "2026-06-29"},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=card_map or {}, lessons_index={})


TDE = {"TDE Trabalho Discente Efetivo": {"block_ids": [], "source": "labels", "assign_dues": [
    {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"},
    {"name": "Entrega T2", "due": "2026-06-29", "source": "structured"},
]}}


def _t(eid, cat="trabalhos", sec="TDE Trabalho Discente Efetivo", title=None):
    return {"id": eid, "title": title or eid.replace("-", " "),
            "category": cat, "source_section": sec}


def test_scope_categorias():
    assert tier2_due_scope(_t("t1-2026-1"))
    assert tier2_due_scope(_t("x", cat="provas", sec="Revisao"))
    assert tier2_due_scope(_t("t1-thy", cat="codigo-professor"))
    assert not tier2_due_scope(_t("x", cat="codigo-professor", sec="Aulas"))
    assert not tier2_due_scope(_t("x", cat="bibliografia", sec=""))
    assert not tier2_due_scope(_t("x", cat="pdfs", sec="Materiais"))


def test_containment_stem_match_band_alta():
    d = resolve_due_window(_t("t1-2026-1"), _ctx(TDE))
    assert d.block_ref == "bloco-15" and d.band == "alta" and not d.flag
    assert d.provider == "due-window" and d.method == "due-contain"
    d2 = resolve_due_window(_t("t2-2026-1"), _ctx(TDE))
    assert d2.block_ref == "bloco-16"


def test_companion_codigo_no_tde_casa_pelo_stem():
    d = resolve_due_window(
        _t("t1-2026-1-thy", cat="codigo-professor", title="T1 2026 1"), _ctx(TDE))
    assert d.block_ref == "bloco-15"


def test_sem_due_casado_retorna_none():
    assert resolve_due_window(_t("revisao-p1-gabarito", cat="provas",
                                 sec="Exercicios de Revisao"), _ctx(TDE)) is None
    assert resolve_due_window(_t("t3-2026-1"), _ctx(TDE)) is None  # stem sem modulo


def test_secao_um_due_so_casa_sem_stem():
    cm = {"Trabalho Final": {"assign_dues": [
        {"name": "Entrega", "due": "2026-06-20", "source": "structured"}]}}
    d = resolve_due_window(_t("trabalho-final", sec="Trabalho Final"), _ctx(cm))
    assert d.block_ref == "bloco-16" and d.band == "alta"


def test_straddle_gap_bloco_anterior_media_flag():
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-04-17", "source": "structured"}]}}
    d = resolve_due_window(_t("t1-x", sec="TDE"), _ctx(cm))
    assert d.block_ref == "bloco-07" and d.band == "media" and d.flag
    assert d.method == "due-straddle"


def test_due_antes_do_primeiro_bloco_none():
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-03-01", "source": "structured"}]}}
    assert resolve_due_window(_t("t1-x", sec="TDE"), _ctx(cm)) is None


def test_named_source_band_media():
    cm = {"TDE": {"assign_dues": [
        {"name": "Entrega T1 (10/06)", "due": "2026-06-10", "source": "named"}]}}
    d = resolve_due_window(_t("t1-x", sec="TDE"), _ctx(cm))
    assert d.block_ref == "bloco-15" and d.band == "media" and not d.flag


def test_lookup_de_card_fold_caso_acento():
    cm = {"Exercícios de Revisão": {"assign_dues": [
        {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"}]}}
    d = resolve_due_window(_t("t1-x", sec="exercicios de revisao"), _ctx(cm))
    assert d is not None and d.block_ref == "bloco-15"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_due_window.py -q`
Expected: FAIL — `ModuleNotFoundError: ... due_window`.

- [ ] **Step 3: Implementar `due_window.py`**

```python
"""TIER 2 janela-de-prazo: due-date por-assignment -> bloco da entrega.

Spec: docs/superpowers/specs/2026-07-22-janela-de-prazo-tier2-design.md.
Semântica (D-A/D-B): bloco cujo [period_start, period_end] CONTÉM o due;
straddle -> bloco anterior mais próximo, band media + FLAG. Nunca chuta:
sem due casado -> None -> funil. NUNCA disambiguator, NUNCA voto LLM.
"""
from __future__ import annotations

import re
from typing import Optional

from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.utils.helpers import norm_ascii_lower

_TDE_PREFIX = "TDE"
_STEM_RE = re.compile(r"\bt(\d+)\b")
_CONF_ALTA, _CONF_MEDIA = 0.95, 0.75


def tier2_due_scope(entry: dict) -> bool:
    """Categorias que TENTAM o provider (gated em casar due; senão funil)."""
    cat = str(entry.get("category") or "").strip().lower()
    if cat in ("trabalhos", "provas"):
        return True
    sec = str(entry.get("source_section") or "").strip()
    return cat.startswith("codigo") and sec.startswith(_TDE_PREFIX)


def _card_entry(entry: dict, ctx: MotorContext) -> Optional[dict]:
    sec = str(entry.get("source_section") or "").strip()
    if not sec:
        return None
    cm = ctx.card_block_map or {}
    hit = cm.get(sec)
    if isinstance(hit, dict):
        return hit
    want = norm_ascii_lower(sec)
    for k, v in cm.items():
        if isinstance(v, dict) and norm_ascii_lower(str(k)) == want:
            return v
    return None


def _stems(text: str) -> set:
    return set(_STEM_RE.findall(norm_ascii_lower(text)))


def _match_due(entry: dict, ctx: MotorContext) -> Optional[dict]:
    """UM {name, due, source} de assign_dues, ou None (0-match/empate)."""
    card = _card_entry(entry, ctx)
    dues = [d for d in ((card or {}).get("assign_dues") or [])
            if isinstance(d, dict) and str(d.get("due") or "")]
    if not dues:
        return None
    if len(dues) == 1:
        return dues[0]
    mine = _stems(f"{entry.get('title') or ''} {entry.get('id') or ''}")
    if not mine:
        return None
    hits = [d for d in dues if _stems(str(d.get("name") or "")) & mine]
    return hits[0] if len(hits) == 1 else None


def resolve_due_window(entry: dict, ctx: MotorContext) -> Optional[AnchorDecision]:
    m = _match_due(entry, ctx)
    if not m:
        return None
    due = str(m.get("due") or "")
    contain = prev = None
    for b in ctx.blocks:  # ordenados por period_start (contrato do MotorContext)
        start = str(b.get("period_start") or "")
        end = str(b.get("period_end") or "") or start
        if not start:
            continue
        if start <= due <= end:
            contain = b
            break
        if end < due:
            prev = b  # último bloco inteiramente antes do due
    if contain is not None:
        band = "alta" if str(m.get("source") or "") == "structured" else "media"
        return AnchorDecision(
            block_ref=str(contain.get("id") or ""), conf=_CONF_ALTA if band == "alta" else _CONF_MEDIA,
            band=band, flag=False, provider="due-window", method="due-contain",
            window=[str(contain.get("id") or "")])
    if prev is None:
        return None  # due antes do primeiro bloco: sem âncora honesta -> funil
    return AnchorDecision(
        block_ref=str(prev.get("id") or ""), conf=_CONF_MEDIA, band="media",
        flag=True, provider="due-window", method="due-straddle",
        window=[str(prev.get("id") or "")])
```

- [ ] **Step 4: Rodar testes**

Run: `python -m pytest tests/test_motor_due_window.py -q`
Expected: 9 passed.

- [ ] **Step 5: Guard AST + suite motor**

Run: `python -m pytest tests/ -q -k motor`
Expected: verde (import guard não reclama — due_window importa só contracts/helpers).

- [ ] **Step 6: Commit**

```bash
git add src/builder/routing/motor/due_window.py tests/test_motor_due_window.py
git commit -m "feat(motor): provider due-window - tier2_due_scope + matching stem + containment/straddle (nunca chuta, nunca disambiguator)"
```

---

### Task 4: Wiring no apply + régua completa

**Files:**
- Modify: `src/builder/routing/motor/apply.py:67-75` (cascata) e docstring do módulo
- Modify: `tests/test_motor_apply.py` (adicionar 3 testes)

**Interfaces:**
- Consumes: `tier2_due_scope`, `resolve_due_window` (Task 3); `_valid_manual_pin`, `_clear_temporal`, `_write_temporal`, `is_out_of_disamb_scope` (já em apply.py).
- Produces: cascata final `pino > tier2_due_scope(provider) > is_out_of_disamb_scope > dup-cache > engine`. Sem dup-cache pra TIER-2 (decisão por-entry, determinística e barata; lição do review F4 I1 — escopo é atributo da ENTRY).

- [ ] **Step 1: Testes falhando (adicionar em tests/test_motor_apply.py, seguindo os fixtures existentes do arquivo)**

```python
def test_tier2_due_window_escreve_temporal(tmp_repo_factory):
    """Entry trabalhos com due casado ganha temporal_* do provider due-window."""
    repo = tmp_repo_factory(
        blocks=[{"id": "bloco-15", "block_uuid": "u15",
                 "period_start": "2026-06-01", "period_end": "2026-06-10"}],
        card_map={"TDE Trabalho Discente Efetivo": {"assign_dues": [
            {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"}]}},
        entries=[{"id": "t1-2026-1", "title": "t1 2026 1", "category": "trabalhos",
                  "source_section": "TDE Trabalho Discente Efetivo"}])
    out = apply_anchor_engine(repo.entries, repo.dir, "MF", enabled=True, voter=None)
    e = out[0]
    assert e["temporal_block_id"] == "u15"
    assert e["temporal_block_band"] == "alta"
    assert e["temporal_block_provider"] == "due-window"


def test_tier2_sem_due_limpa_temporal_e_vai_pro_funil(tmp_repo_factory):
    repo = tmp_repo_factory(
        blocks=[{"id": "bloco-15", "block_uuid": "u15",
                 "period_start": "2026-06-01", "period_end": "2026-06-10"}],
        card_map={},
        entries=[{"id": "revisao-p1-gabarito", "title": "revisao p1 gabarito",
                  "category": "provas", "source_section": "Exercicios de Revisao",
                  "temporal_block_id": "stale"}])
    out = apply_anchor_engine(repo.entries, repo.dir, "MF", enabled=True, voter=None)
    assert not out[0].get("temporal_block_id")  # limpo, funil responde


def test_pino_manual_vence_due_window(tmp_repo_factory):
    repo = tmp_repo_factory(
        blocks=[{"id": "bloco-15", "block_uuid": "u15",
                 "period_start": "2026-06-01", "period_end": "2026-06-10"}],
        card_map={"TDE Trabalho Discente Efetivo": {"assign_dues": [
            {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"}]}},
        entries=[{"id": "t1-2026-1", "title": "t1 2026 1", "category": "trabalhos",
                  "source_section": "TDE Trabalho Discente Efetivo",
                  "manual_timeline_block_id": "u15"}])
    out = apply_anchor_engine(repo.entries, repo.dir, "MF", enabled=True, voter=None)
    assert not out[0].get("temporal_block_id")  # pino: motor respeita e limpa temporal
```

Nota ao implementador: `tests/test_motor_apply.py` já tem fixture/factory própria pra montar repo tmp (blocks + card map + manifest) — REUSAR o helper existente do arquivo; se a assinatura diferir de `tmp_repo_factory`, adaptar os 3 testes ao helper real mantendo os asserts.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_apply.py -q -k "tier2 or pino_manual_vence"`
Expected: FAIL (provider não plugado).

- [ ] **Step 3: Wiring na cascata (apply.py)**

Import no topo (junto dos imports do motor):

```python
from src.builder.routing.motor.due_window import resolve_due_window, tier2_due_scope
```

No loop de entries, ENTRE o pino e o `is_out_of_disamb_scope` (o skip I1 continua valendo pro resto):

```python
        if _valid_manual_pin(entry, ctx):
            _clear_temporal(entry)
            continue
        if tier2_due_scope(entry):
            # TIER 2 janela-de-prazo (spec 2026-07-22): decisão por-entry, sem
            # dup-cache — escopo é atributo da ENTRY (lição review F4 I1).
            decision = resolve_due_window(entry, ctx)
            if decision is None:
                _clear_temporal(entry)
                continue
            _write_temporal(entry, decision, ctx)
            continue
        if is_out_of_disamb_scope(entry):
```

`_OUT_CATEGORIES`/`is_out_of_disamb_scope` NÃO mudam (universo dos probes fase0-4 depende deles).

- [ ] **Step 4: Rodar os testes novos + suite motor**

Run: `python -m pytest tests/test_motor_apply.py tests/test_motor_due_window.py -q`
Expected: verde.

- [ ] **Step 5: Régua COMPLETA (7 probes) + suite inteira**

Run (pré-gate): `python scripts/audit_gold_freshness.py` — exit 0.
Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py && python scripts/fase2_prova_SO.py && python scripts/fase2_prova_TCC.py && python scripts/fase3_prova_llm.py && python scripts/fase4_prova_D9.py && python scripts/fase5_prova_tier2.py`
Expected: 6 probes com números IDÊNTICOS aos baselines (fase0 82.8%/0/1 · fase1 9/10 · fase2-SO 45.2%/0/0 · fase2-TCC 5/5+83.3%/0 · fase3 lift +3/0 API · fase4 48/58 cw1 + 51/58 cw0) e fase5 `modo=baseline-only · acc=1/8 · PASS` (repo MF real ainda sem assign_dues — o alvo 4/8 só mede pós-sync, ação user no rollout).
Run: `python -m pytest tests/ -q`
Expected: 1787+ passed / 4 skipped / 0 failed (novos testes somam ao total; ZERO failed).

- [ ] **Step 6: Commit**

```bash
git add src/builder/routing/motor/apply.py tests/test_motor_apply.py
git commit -m "feat(motor): pluga due-window na cascata do apply (pino > due-window > fora-de-escopo; sem dup-cache no TIER-2)"
```

---

## Pós-plano (fora do escopo destas tasks — rollout F5, ação user)

1. Sync Moodle do MF na GUI (popula `assign_dues` real) → re-rodar `fase5_prova_tier2.py` → modo `target`, piso 4/8 · cw 0. FAIL = resultado honesto, contingência = pino manual/card-window (spec §6).
2. Badges do dashboard já mostram `provider` — `due-window` aparece de graça (band autoritativa do motor, F4 item 7).
3. Atualizar pendencias.md + handoff com o número medido.
