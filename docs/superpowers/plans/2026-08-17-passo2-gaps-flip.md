# Passo 2 da campanha 3 — C1 pinos + gaps 1.2/1.3 (destrava o flip) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar as três pré-condições do flip do `use_concept_resolver`: C1 (motor honra pinos manuais em uuid), gap 1.3 (resync da tag `bloco:` no attach) e gap 1.2 (verificação de que os campos de unidade descrevem o bloco pós-motor).

**Architecture:** Três fixes cirúrgicos, sem mudança estrutural: `_manual_block_id` passa a casar uuid E display (Tier 1 do motor); `attach_block_summary_fields` resincroniza a tag `bloco:` quando troca `computed_block_id` (caminho D1 código); teste de integração prova a cadeia `apply_concept_resolver → apply_unit_subunit_fields` coerente. Tudo coberto por teste antes do fix (TDD).

**Tech Stack:** Python 3, pytest. Sem dependências novas.

**Spec:** review final F4 (achados C1/I2, ledger 2026-08-14) + `docs/reports/2026-08-14-auditoria-enxame.md` §1 (1.2/1.3) + `docs/reports/2026-08-14-handoff-campanha3-cutover.md` (passo 2). Itens C1/M4-M8 registrados em `docs/reports/pendencias.md` (Concluído F4 + itens [CODE] da review final).

## Global Constraints

- Flag `use_concept_resolver` OFF em produção: `attach_block_summary_fields` RODA flag-OFF (caminho legado vivo) — o fix 1.3 muda produção flag-OFF; é correção de drift REAL já documentado (auditoria 1.3), então sentinelas PODEM mudar SÓ se algum curso tiver o drift nos casos-chave — diff de sentinela deve ser revisado e explicado, nunca aceito às cegas.
- O fix C1 (`_manual_block_id`) só roda sob flag ON (Tier 1 do motor) — zero efeito flag-OFF.
- Tag `bloco:` é DISPLAY (`bloco-NN`), nunca uuid (`file_map.py:506` parseia `bloco-(\d+)`).
- `engine.py` façade; imports de submódulos focados.
- Não tocar: `resolve_unit_block_tags`, símbolos condenados, `docs/reports/gold_templates/gold_units_rotular.xlsx` (sujo pré-sessão, ruling pendente).
- Gates do passo: suite verde + sentinelas (diff zero OU explicado caso-a-caso pelo fix 1.3) + régua MF ≥ 50/57.
- Comandos: `python -m pytest tests -q` · `python scripts/eval_ground_truth.py ..\Metodos-Formais-Tutor tests\fixtures\eval\ground_truth_MF.csv`.

---

### Task 1: C1 — `_manual_block_id` aceita uuid e display; pino sobrevive ao apply

**Files:**
- Modify: `src/builder/routing/concept_resolver.py:250-255` (`_manual_block_id`) e `:272-284` (lookup do winner no Tier 1)
- Test: `tests/test_concept_resolver.py` (acrescentar) e `tests/test_resolver_apply_units.py` (acrescentar)

**Interfaces:**
- Produces: `_manual_block_id` devolve o id CANÔNICO do bloco pinado (uuid quando existe, senão display), `""` quando não resolve. `Assignment.block_id` do Tier 1 = canônico.
- Consumes: `resolve_material_assignment` (assinatura inalterada); `apply_concept_resolver` (inalterado — `resolve_block_ref` já faz passthrough de uuid).

- [x] **Step 1: Testes que falham** — em `tests/test_concept_resolver.py` (seguir os imports/fixtures do próprio arquivo):

```python
def test_pino_manual_em_uuid_vence_tier1():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
        {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
    ]
    entry = {"id": "e1", "manual_timeline_block_id": "u-2"}
    a = resolve_material_assignment(entry, blocks, [], signals={})
    assert a["block_id"] == "u-2"
    assert a["method"] == "manual"
    assert a["confidence"] == 1.0
    assert a["unit_slug"] == "u2"

def test_pino_manual_em_display_segue_valendo():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
        {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
    ]
    entry = {"id": "e1", "manual_timeline_block_id": "bloco-02"}
    a = resolve_material_assignment(entry, blocks, [], signals={})
    assert a["block_id"] == "u-2"          # canonico = uuid do bloco casado
    assert a["method"] == "manual"
    assert a["unit_slug"] == "u2"
```

E em `tests/test_resolver_apply_units.py` (sobrevivência fim-a-fim pelo apply, helpers `_entry`/`BLOCKS` existentes):

```python
def test_apply_concept_resolver_honra_pino_uuid():
    from src.builder.routing.resolver_apply import apply_concept_resolver
    e = {"id": "e1", "file_type": "pdf", "computed_block_id": "u-1",
         "manual_timeline_block_id": "u-2", "auto_tags": ["bloco:bloco-01"]}
    out = apply_concept_resolver([e], list(BLOCKS), [], {}, None)
    assert out[0]["computed_block_id"] == "u-2"          # pino vence o scorer
    assert out[0]["computed_block_method"] == "manual"
    assert out[0]["computed_block_confidence"] == 1.0
    assert "bloco:bloco-02" in out[0]["auto_tags"]       # espelho display resync
```

- [x] **Step 2: Rodar e ver falhar** — `python -m pytest tests/test_concept_resolver.py tests/test_resolver_apply_units.py -q`. Esperado: os 3 novos FAIL (pino uuid devolve Assignment do scorer, não manual).

- [x] **Step 3: Implementar.** Substituir `_manual_block_id` (concept_resolver.py:250-255):

```python
def _manual_block_id(entry: dict, blocks: List[dict]) -> str:
    """Pino manual em uuid OU display (bloco-NN legado); devolve o id CANONICO
    (uuid quando o bloco tem) ou ''. Pinos migraram pra uuid na Fase 1
    (file_map.py:498-513); casar so display matava o Tier 1 em producao
    (review final F4, achado C1)."""
    raw = str(entry.get("manual_timeline_block_id") or "").strip()
    if not raw:
        return ""
    for b in blocks or []:
        if raw in (str(b.get("id", "")).strip(), str(b.get("block_uuid", "")).strip()):
            return str(b.get("block_uuid") or b.get("id") or "")
    return ""
```

E no Tier 1 (`resolve_material_assignment`, :272-284), o lookup do winner casa uuid OU display:

```python
    manual = _manual_block_id(entry, blocks)
    if manual:
        winner = next(
            (b for b in blocks
             if manual in (str(b.get("block_uuid") or ""), str(b.get("id") or ""))),
            None,
        )
```

(resto do branch inalterado — `block_id=manual` já é canônico.)

- [x] **Step 4: Rodar e ver passar** — mesmos arquivos; TODOS verdes (novos + antigos; os antigos de pino display não podem quebrar).

- [x] **Step 5: Commit** — `fix(routing): Tier 1 casa pino manual em uuid e display (C1, review final F4)` nos 3 arquivos.

---

### Task 2: gap 1.3 — resync da tag `bloco:` no attach + teste de invariante

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py:242-250` (dentro do swap D1)
- Test: `tests/test_attach_block_consensus.py` (acrescentar — hoje não asserta `auto_tags`, gap apontado pela auditoria)

**Interfaces:**
- Consumes: `attach_block_summary_fields(entries, code_curation, blocks)` — assinatura inalterada; `blocks` já chega no call-site (pedagogical_regeneration.py:517).
- Produces: invariante `computed_block_id` ↔ tag `bloco:<display>` preservado quando o D1 troca o bloco.

- [x] **Step 1: Teste que falha** — em `tests/test_attach_block_consensus.py`, seguindo as fixtures do próprio arquivo (entry código, band baixa, sem source_section, curation com `primary_block_id`):

```python
def test_swap_d1_resincroniza_tag_bloco():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u-1"},
        {"id": "bloco-02", "block_uuid": "u-2"},
    ]
    e = {"id": "e1", "file_type": "code", "computed_block_id": "u-1",
         "computed_block_band": "baixa", "auto_tags": ["bloco:bloco-01", "outra:tag"]}
    curation = {"entries": {"e1": {"summary": {
        "primary_block_id": "u-2", "block_match_method": "llm_only",
        "block_match_confidence": 0.9}}}}
    out = attach_block_summary_fields([e], curation, blocks=blocks)
    assert out[0]["computed_block_id"] == "u-2"
    assert "bloco:bloco-02" in out[0]["auto_tags"]      # resync (era o drift 1.3)
    assert "bloco:bloco-01" not in out[0]["auto_tags"]
    assert "outra:tag" in out[0]["auto_tags"]
```

- [x] **Step 2: Rodar e ver falhar** — `python -m pytest tests/test_attach_block_consensus.py -q`. Esperado: FAIL na tag (swap acontece, tag fica velha).

- [x] **Step 3: Implementar** — dentro do `if` do swap (após a linha 250, mesmo nível de `e["computed_block_id"] = gemini_primary`):

```python
                # Resync do espelho: sem isto a tag bloco: segue descrevendo o
                # bloco antigo (drift 1.3, auditoria 2026-08-14). Tag e DISPLAY.
                _display = next(
                    (str(b.get("id") or "") for b in blocks
                     if str(b.get("block_uuid") or "") == gemini_primary),
                    gemini_primary,
                )
                _tags = [t for t in (e.get("auto_tags") or []) if not str(t).startswith("bloco:")]
                if _display:
                    _tags.append(f"bloco:{_display}")
                e["auto_tags"] = _tags
```

- [x] **Step 4: Rodar e ver passar** — arquivo inteiro verde.

- [x] **Step 5: Commit** — `fix(ops): attach resincroniza tag bloco: no swap D1 (gap 1.3)`.

---

### Task 3: gap 1.2 — teste de integração da cadeia motor e fechamento

**Files:**
- Test: `tests/test_resolver_apply_units.py` (acrescentar 1 teste de integração)

**Interfaces:**
- Consumes: `apply_concept_resolver` + `apply_unit_subunit_fields` (Tasks F4), pino uuid da Task 1.

- [x] **Step 1: Teste que falha só se a cadeia regredir** (característica — deve PASSAR já na primeira execução se F4+Task 1 estão corretos; se falhar, é bug real a investigar antes de prosseguir):

```python
def test_cadeia_motor_unit_descreve_bloco_pos_apply():
    # 1.2 (auditoria): unit fields nao podem descrever o bloco ANTIGO.
    # Pino move e1 de u-1 pra u-2; a unidade final deve ser a de u-2.
    from src.builder.routing.resolver_apply import apply_concept_resolver
    e = {"id": "e1", "file_type": "pdf", "computed_block_id": "u-1",
         "manual_timeline_block_id": "u-2", "auto_tags": ["unit:u1", "bloco:bloco-01"]}
    entries = apply_concept_resolver([e], list(BLOCKS), [], {}, None)
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields(entries, BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_block_id"] == "u-2"
    assert out[0]["computed_unit_slug"] == "u2"          # unidade do bloco NOVO (pino manual)
    assert "unidade_do_bloco_manual" in out[0]["unit_match_reasons"]
    assert out[0]["unit_block_conflict"] == {}
    assert "unit:u2" in out[0]["auto_tags"] and "unit:u1" not in out[0]["auto_tags"]
```

- [x] **Step 2: Rodar** — `python -m pytest tests/test_resolver_apply_units.py -q`. Se FAIL: investigar como bug (systematic-debugging), não ajustar o assert.

- [x] **Step 3: Commit** — `test(routing): cadeia motor — unit descreve bloco pos-apply (fecha gap 1.2)`.

---

### Task 4: gates do passo

- [x] **Step 1:** `python -m pytest tests -q` — baseline 1946/1/0 + novos.
- [x] **Step 2:** `python -m pytest tests/test_caracterizacao_blocos_atual.py -q` — diff zero esperado; se houver diff, correlacionar caso-a-caso com o fix 1.3 (cursos com drift real de tag) e reportar SEM re-versionar snapshot (decisão de re-baseline é do controlador).
- [x] **Step 3:** `python scripts/eval_ground_truth.py ..\Metodos-Formais-Tutor tests\fixtures\eval\ground_truth_MF.csv` — ≥ 50/57.
- [x] **Step 4:** Reportar os 3 números. Tracker/fechamento dos itens fica com o controlador.

## Notas de escopo

- Régua de sobrevivência de pinos POR CURSO (condição do GO) roda na medição do FLIP (passo 3), não aqui — aqui nasce o teste unitário que a garante no código.
- M4-M8 (dívidas menores da review final) ficam registradas no tracker; oportunista M6/M4 NÃO entram neste passo (diff mínimo primeiro).

## Self-review (feita na escrita)

- C1: casa uuid+display nos DOIS pontos (helper + winner lookup); canônico consistente com o caminho não-manual (`:427`). Teste fim-a-fim cobre espelho display.
- 1.3: fix dentro do `if` do swap (só quando trocou), display resolvido via blocks, prefixos preservados. Invariante testado com os 3 asserts de tag.
- 1.2: teste de integração usa pino (determinístico, sem depender de scoring) — cobre exatamente a frase do achado ("campos descrevem o bloco antigo").
- Sem placeholders; código completo em todo step.
