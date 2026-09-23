# Correções de atribuição — D1 (fonte única do bloco de código) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar `computed_block_id` (funil) a fonte única do bloco de código em todos os artefatos, retirando o `primary_block_id` (Gemini) como decisor — mas com um consenso **band-gated** que mantém o Gemini como desempate só onde o funil é honestamente fraco (sem card E band baixa), preservando o sinal autoritativo de card.

**Architecture:** Decisão D1=A (ver spec `docs/superpowers/specs/2026-06-16-correcoes-atribuicao-wave-1-2-design.md`). O funil já calcula `computed_block_id` para toda entry, incluindo código, usando manual > card/`source_section` (autoritativo) > review_rule > scorer léxico. O Gemini decide só por concepts (ignora card) e hoje governa CODE_INDEX/CRONOGRAMA/CODE_HEALTH via `primary_block_id`. Este plano: (1) adiciona um consenso band-gated em `attach_block_summary_fields` que adota o bloco do Gemini SOMENTE para código sem card e com band baixa; (2) reaponta os 3 artefatos para `resolve_effective_block`/`computed_block_id`; (3) entrega um script de censo para o eval-gate no repo real.

**Tech Stack:** Python 3, pytest. Comando de teste: `python -m pytest tests -q`.

**Escopo:** D1 (= P0.3 do spec). Pré-requisito: P0 já mergeado (subunit fonte-única + dedup), suíte verde em 1340. Fora de escopo: `source_importers.py:75` (linha "Aula:" do `.md` curado de código) — roda no IMPORT, antes do funil, então não tem `computed_block_id`; tratado como follow-up junto com a regeneração da `.md` curada (escalada 3b). Secondaries (`secondary_block_ids`) do Gemini ficam como "Também relevante" (suplementar), inalterados.

**Constraint (toda task):** suíte verde após cada task. Tasks que mudam o agrupamento de artefatos são eval-gated pelo **censo de código→bloco no repo real** (Task 6) + golden de bloco fixture (`scripts/eval_assignments.py`, hoje 100%, confiante-errado 0).

**Regra de consenso (núcleo do D1), derivação de `computed_block_id` para CÓDIGO:**
```
1. manual                                  (sempre — já no funil)
2. card / source_section                   (autoritativo — já no funil)
3. review_rule                             (já no funil)
4. funil scorer  SE band != "baixa"        (funil forte — já no funil)
5. SENÃO Gemini primary (se existir)       <-- ADICIONADO em attach (Task 2)
6. SENÃO funil best-effort (band baixa)    (mantém)
```
Regras 1-4/6 já existem no funil. Task 2 adiciona apenas a regra 5 (o desempate band-gated) em `attach_block_summary_fields`.

---

## File Structure

- `src/builder/ops/pedagogical_regeneration.py` — **Modify**: em `attach_block_summary_fields` (linhas 120-158), após o overlay de method/confidence, adicionar o consenso band-gated para código. Import de `confidence_band`.
- `src/builder/artifacts/repo.py` — **Modify**: 3 sites de leitura de bloco de código passam a usar `resolve_effective_block`/`computed_block_id`:
  - CODE_INDEX (linhas ~835-841)
  - `cronograma_detalhado_md` (linhas ~906-915)
  - `code_health_md` (linhas ~992-997)
  Import de `resolve_effective_block`.
- `scripts/eval_code_block_census.py` — **Create**: censo código→bloco (Gemini-antigo × computed-novo) sobre um repo gerado real, para o eval-gate.
- `tests/test_attach_block_consensus.py` — **Create**: testa a regra band-gated em `attach_block_summary_fields`.
- `tests/test_code_index_uses_computed_block.py` — **Create**: testa que os 3 artefatos agrupam por `computed_block_id`, não por `primary_block_id`.

---

## Task 1: Verificar timing (o funil vê concepts?) — read-only + teste-documento

**Objetivo:** confirmar que `attach_block_summary_fields` roda DEPOIS de `resolve_unit_block_tags` e ANTES da renderização dos artefatos, e documentar se a `.md` curada que o funil lê contém concepts Gemini (define se a escalada 3b é necessária).

**Files:**
- Test: `tests/test_pedagogical_regeneration_order.py` (criar — guard de ordem)

- [ ] **Step 1: Ler e confirmar a ordem**

Ler `src/builder/ops/pedagogical_regeneration.py` função `regenerate_pedagogical_files`. Confirmar a sequência (hoje linhas 327 → 336): `resolve_unit_block_tags_fn(...)` precede `attach_block_summary_fields(...)`, e ambos precedem a renderização de CODE_INDEX/CRONOGRAMA/CODE_HEALTH. Anotar os números de linha atuais no relatório.

- [ ] **Step 2: Escrever guard de ordem (teste-documento)**

Criar `tests/test_pedagogical_regeneration_order.py` que lê o source do módulo e afirma a ordem textual das chamadas (guard barato contra reordenação acidental que quebraria o consenso):

```python
import inspect
from src.builder.ops import pedagogical_regeneration as pr


def test_resolve_unit_block_tags_runs_before_attach_block_summary():
    src = inspect.getsource(pr.regenerate_pedagogical_files)
    i_resolve = src.find("resolve_unit_block_tags_fn(")
    i_attach = src.find("attach_block_summary_fields(")
    assert i_resolve != -1 and i_attach != -1
    assert i_resolve < i_attach, "funil deve rodar antes do attach (consenso D1 depende disso)"
```

- [ ] **Step 3: Rodar**

Run: `python -m pytest tests/test_pedagogical_regeneration_order.py -q`
Expected: PASS.

- [ ] **Step 4: Documentar o fato dos concepts**

Por inspeção: `source_importers.py` escreve a `.md` curada no IMPORT (`_process_entry`), com concepts SÓ se o summary Gemini já existia naquele momento. Numa importação fresca, o summary ainda não existe → a `.md` tem o header fallback (código cru, sem concepts). Logo o funil normalmente NÃO vê concepts no primeiro build. **Conclusão a registrar:** o consenso band-gated (Task 2) é necessário; a escalada 3b (regenerar a `.md` curada com concepts no tempo da regeneração) fica como follow-up gated no censo (Task 6). Sem mudança de código neste step.

- [ ] **Step 5: Commit**

```bash
git add tests/test_pedagogical_regeneration_order.py
git commit -m "test(d1): guard de ordem funil->attach + nota de timing dos concepts" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Consenso band-gated em `attach_block_summary_fields`

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py` (`attach_block_summary_fields`, ~120-158; import de `confidence_band`)
- Test: `tests/test_attach_block_consensus.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_attach_block_consensus.py`:

```python
from src.builder.ops.pedagogical_regeneration import attach_block_summary_fields


def _curation(primary, method="llm_only", conf=0.6):
    return {"entries": {"c1": {"summary": {
        "primary_block_id": primary,
        "block_match_method": method,
        "block_match_confidence": conf,
    }}}}


def _code_entry(**over):
    e = {
        "id": "c1",
        "file_type": "zip",
        "category": "codigo-professor",
        "computed_block_id": "bloco-05",
        "computed_block_band": "baixa",
        "source_section": "",
    }
    e.update(over)
    return e


def test_weak_noncard_code_adopts_gemini_block():
    # sem card + band baixa + gemini primary -> adota o Gemini
    [out] = attach_block_summary_fields([_code_entry()], _curation("bloco-12"))
    assert out["computed_block_id"] == "bloco-12"
    assert out["computed_block_method"] in ("llm_only", "consensus")
    assert out["computed_block_band"] != "baixa"  # band reflete a conf do Gemini (0.6)


def test_carded_code_keeps_funnel_block():
    # com card -> NUNCA sobrescreve (card é autoritativo)
    [out] = attach_block_summary_fields(
        [_code_entry(source_section="aula-05", computed_block_id="bloco-05")],
        _curation("bloco-12"),
    )
    assert out["computed_block_id"] == "bloco-05"


def test_strong_funnel_code_keeps_funnel_block():
    # band alta -> funil forte vence, Gemini não desempata
    [out] = attach_block_summary_fields(
        [_code_entry(computed_block_band="alta", computed_block_id="bloco-05")],
        _curation("bloco-12"),
    )
    assert out["computed_block_id"] == "bloco-05"


def test_non_code_entry_untouched_by_consensus():
    e = {"id": "c1", "file_type": "pdf", "category": "material",
         "computed_block_id": "bloco-05", "computed_block_band": "baixa", "source_section": ""}
    [out] = attach_block_summary_fields([e], _curation("bloco-12"))
    assert out["computed_block_id"] == "bloco-05"


def test_no_gemini_primary_keeps_funnel_block():
    [out] = attach_block_summary_fields([_code_entry()], _curation(""))
    assert out["computed_block_id"] == "bloco-05"
```

- [ ] **Step 2: Rodar pra confirmar que falha**

Run: `python -m pytest tests/test_attach_block_consensus.py -q`
Expected: FAIL em `test_weak_noncard_code_adopts_gemini_block` (hoje attach não adota o Gemini; computed_block_id segue "bloco-05").

- [ ] **Step 3: Implementar o consenso band-gated**

Em `src/builder/ops/pedagogical_regeneration.py`: garantir o import de `confidence_band` no topo (vem de `src.builder.routing.thresholds`; confirmar o caminho exato lendo outros imports do módulo — se já houver `from src.builder.routing.thresholds import ...`, adicionar `confidence_band` à lista). Dentro do laço `for e in entries:` de `attach_block_summary_fields`, APÓS o bloco que trata `block_match_confidence` (após a linha ~156, antes do `return entries`), adicionar:

```python
        # D1: consenso band-gated para CÓDIGO. computed_block_id é a fonte única
        # do bloco. O funil decide (card-aware); o Gemini só desempata onde o
        # funil é honestamente fraco — SEM card E band "baixa". Card e funil-forte
        # nunca são sobrescritos (preserva o gabarito autoritativo, erro 0/22).
        if str(e.get("file_type") or "") in ("code", "zip"):
            gemini_primary = str(summary.get("primary_block_id") or "")
            if (
                gemini_primary
                and not str(e.get("source_section") or "").strip()
                and str(e.get("computed_block_band") or "") == "baixa"
            ):
                e["computed_block_id"] = gemini_primary
                e["computed_block_method"] = method or "llm_only"
                _gem_conf = summary.get("block_match_confidence")
                if _gem_conf is not None:
                    try:
                        e["computed_block_confidence"] = float(_gem_conf)
                        e["computed_block_band"] = confidence_band(float(_gem_conf))
                    except (TypeError, ValueError):
                        pass
```

Notas: `summary` e `method` já estão definidos no laço (linhas 126 e 134). `method` é `block_match_method` (consensus/llm_only/auto_concept); usar `method or "llm_only"` cobre o caso de summary sem method explícito.

- [ ] **Step 4: Rodar pra confirmar que passa**

Run: `python -m pytest tests/test_attach_block_consensus.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Suíte inteira**

Run: `python -m pytest tests -q`
Expected: verde (sem regressão).

- [ ] **Step 6: Commit**

```bash
git add src/builder/ops/pedagogical_regeneration.py tests/test_attach_block_consensus.py
git commit -m "feat(d1): consenso band-gated - codigo sem card + band baixa adota bloco do Gemini" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Reapontar CODE_INDEX / CRONOGRAMA / CODE_HEALTH para `computed_block_id`

**Files:**
- Modify: `src/builder/artifacts/repo.py` (3 sites + import)
- Test: `tests/test_code_index_uses_computed_block.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Ler primeiro `src/builder/artifacts/repo.py` para confirmar os nomes/assinaturas das 3 funções: a que renderiza CODE_INDEX (perto da linha 790-885), `cronograma_detalhado_md` (888) e `code_health_md` (973). Criar `tests/test_code_index_uses_computed_block.py`. O teste constrói entries de código cujo `computed_block_id` DIFERE do `primary_block_id` do Gemini na curation, e afirma que o agrupamento usa o `computed_block_id`:

```python
from src.models.core import FileEntry
from src.builder.artifacts import repo


def _blocks():
    return [
        {"id": "bloco-05", "period_label": "Semana 5", "primary_topic_label": "Hoare", "topics": [], "unit_slug": "u1"},
        {"id": "bloco-12", "period_label": "Semana 12", "primary_topic_label": "Dafny", "topics": [], "unit_slug": "u2"},
    ]


def _code_entry():
    # computed_block_id = bloco-05 (funil); Gemini diria bloco-12
    return FileEntry.from_dict({
        "id": "c1", "title": "Hoare demo", "file_type": "zip",
        "category": "codigo-professor", "source_path": "code/hoare.zip",
        "computed_block_id": "bloco-05",
    })


def _curation():
    return {"entries": {"c1": {"summary": {
        "primary_block_id": "bloco-12",
        "secondary_block_ids": [],
        "concepts": ["Hoare"], "inferred_title": "Hoare demo",
        "language": "dafny", "pedagogical_role": "exemplo",
    }}}}


def test_code_index_groups_by_computed_block(tmp_path):
    md = repo.code_index_md(  # confirmar nome real ao ler repo.py
        {"course_name": "MF"}, [_code_entry()], _curation(), _blocks(),
    )
    assert "Semana 5" in md            # agrupado sob o bloco do funil
    assert "Semana 12" not in md       # NÃO sob o bloco do Gemini


def test_cronograma_groups_primary_by_computed_block():
    md = repo.cronograma_detalhado_md(
        {"course_name": "MF"}, [_code_entry()], _curation(), _blocks(),
    )
    # a entry aparece como código primário sob Semana 5, não Semana 12
    bloco5 = md.split("Semana 12")[0]
    assert "Hoare demo" in bloco5


def test_code_health_counts_computed_block():
    md = repo.code_health_md(
        {"course_name": "MF"}, [_code_entry()], _curation(), _blocks(),
    )
    # 1 código, todos com bloco (via computed) -> sem órfãos
    assert "1" in md  # cobertura; ajustar à string real de cobertura ao ler repo.py
```

NOTA ao implementer: ajustar os nomes de função (`code_index_md`) e as asserções de string (headers/cobertura) à saída REAL após ler `repo.py`. As asserções-chave (agrupa sob bloco-05, não bloco-12) são o contrato; o resto é forma.

- [ ] **Step 2: Rodar pra confirmar que falha**

Run: `python -m pytest tests/test_code_index_uses_computed_block.py -q`
Expected: FAIL — hoje os 3 leem `summary.primary_block_id` ("bloco-12"), então agrupam sob Semana 12.

- [ ] **Step 3: Implementar — reapontar os 3 sites**

Adicionar no topo de `repo.py` (verificar que não cria import circular; se criar, importar localmente dentro de cada função):
```python
from src.builder.routing.file_map import resolve_effective_block
```

**CODE_INDEX** (linhas ~835-841): trocar
```python
    for e in code_only:
        summary = (curation_entries.get(e.id()) or {}).get("summary") or {}
        primary = summary.get("primary_block_id", "")
        if primary and primary in blocks_by_id:
            by_block.setdefault(primary, []).append((e, summary))
        else:
            orphans.append((e, summary))
```
por
```python
    for e in code_only:
        summary = (curation_entries.get(e.id()) or {}).get("summary") or {}
        primary = resolve_effective_block(e.to_dict(), timeline_blocks).id
        if primary and primary in blocks_by_id:
            by_block.setdefault(primary, []).append((e, summary))
        else:
            orphans.append((e, summary))
```

**CRONOGRAMA** (`cronograma_detalhado_md`, ~911-915): trocar
```python
        s = (curation_entries.get(e.id()) or {}).get("summary") or {}
        if s.get("primary_block_id"):
            primary_idx.setdefault(s["primary_block_id"], []).append((e, s))
        for sb in (s.get("secondary_block_ids") or []):
            secondary_idx.setdefault(sb, []).append((e, s))
```
por
```python
        s = (curation_entries.get(e.id()) or {}).get("summary") or {}
        primary = resolve_effective_block(e.to_dict(), timeline_blocks).id
        if primary:
            primary_idx.setdefault(primary, []).append((e, s))
        for sb in (s.get("secondary_block_ids") or []):
            secondary_idx.setdefault(sb, []).append((e, s))
```
(secondaries do Gemini ficam — "Também relevante".)

**CODE_HEALTH** (`code_health_md`, ~992-997): trocar
```python
    for e in code_entries:
        s = (curation_entries.get(e.id()) or {}).get("summary") or {}
        if s.get("primary_block_id"):
            with_block += 1
        elif s:  # tem summary mas sem block
            orphans_list.append((e, s))
```
por
```python
    for e in code_entries:
        s = (curation_entries.get(e.id()) or {}).get("summary") or {}
        if resolve_effective_block(e.to_dict(), timeline_blocks).id:
            with_block += 1
        elif s:  # tem summary mas sem block
            orphans_list.append((e, s))
```

- [ ] **Step 4: Rodar pra confirmar que passa**

Run: `python -m pytest tests/test_code_index_uses_computed_block.py -q`
Expected: PASS.

- [ ] **Step 5: Suíte inteira**

Run: `python -m pytest tests -q`
Expected: verde. Se algum teste existente de CODE_INDEX/CRONOGRAMA/CODE_HEALTH afirmava agrupamento por `primary_block_id`, atualizar para `computed_block_id` (é a correção pretendida) e reportar quais.

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_code_index_uses_computed_block.py
git commit -m "feat(d1): CODE_INDEX/CRONOGRAMA/CODE_HEALTH leem computed_block_id (fonte unica) - Gemini vira voto" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Script de censo código→bloco (eval-gate do repo real)

**Files:**
- Create: `scripts/eval_code_block_census.py`

- [ ] **Step 1: Escrever o script**

Criar `scripts/eval_code_block_census.py` — lê um repo gerado e tabula Gemini-antigo × computed-novo por entry de código, com flags de regressão. Read-only sobre o repo.

```python
"""Censo código->bloco: compara primary_block_id (Gemini) x computed_block_id
(funil + consenso band-gated) num repo gerado real. Eval-gate do D1.

Uso: python scripts/eval_code_block_census.py <caminho-do-repo-gerado>
Lê manifest.json + course/code_curation.json. Não escreve nada.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

CODE_TYPES = {"code", "zip"}


def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python scripts/eval_code_block_census.py <repo-gerado>")
        return 2
    repo = Path(sys.argv[1])
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    cur_path = repo / "course" / "code_curation.json"
    curation = json.loads(cur_path.read_text(encoding="utf-8")) if cur_path.exists() else {"entries": {}}
    cur_entries = curation.get("entries", {})

    rows = []
    for e in manifest.get("entries", []):
        if str(e.get("file_type") or "") not in CODE_TYPES:
            continue
        eid = str(e.get("id") or "")
        summary = (cur_entries.get(eid) or {}).get("summary") or {}
        gemini = str(summary.get("primary_block_id") or "")
        computed = str(e.get("computed_block_id") or "")
        carded = bool(str(e.get("source_section") or "").strip())
        band = str(e.get("computed_block_band") or "")
        rows.append({
            "id": eid, "carded": carded, "band": band,
            "gemini": gemini, "computed": computed,
            "changed": gemini != computed,
        })

    print(f"=== Censo codigo->bloco ({len(rows)} entries) ===")
    print(f"{'id':28} {'card':5} {'band':6} {'gemini':10} {'computed':10} {'mudou'}")
    for r in rows:
        print(f"{r['id'][:28]:28} {str(r['carded']):5} {r['band']:6} "
              f"{r['gemini'][:10]:10} {r['computed'][:10]:10} {'SIM' if r['changed'] else ''}")

    changed = [r for r in rows if r["changed"]]
    carded_changed = [r for r in changed if r["carded"]]
    midband_changed = [r for r in changed if not r["carded"] and r["band"] != "baixa"]
    weak_changed = [r for r in changed if not r["carded"] and r["band"] == "baixa"]

    print()
    print(f"Mudaram (gemini != computed): {len(changed)}/{len(rows)}")
    print(f"  - carded (esperado: funil/card vence, conferir se melhora): {len(carded_changed)}")
    print(f"  - faixa do meio (sem card, band!=baixa — REVISAR no ground truth): {len(midband_changed)}")
    print(f"  - fraca (sem card, band baixa — deveria ter adotado Gemini=computed; se mudou aqui, revisar consenso): {len(weak_changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Sanity-check do script (sintaxe + roda sem repo)**

Run: `python scripts/eval_code_block_census.py`
Expected: imprime a linha de uso e sai com código 2 (sem traceback).

- [ ] **Step 3: Commit**

```bash
git add scripts/eval_code_block_census.py
git commit -m "tool(d1): censo codigo->bloco (Gemini x computed) p/ eval-gate no repo real" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Eval-gate da fase D1 (antes de considerar D1 fechado)

- [ ] **Golden de bloco fixture:** `python scripts/eval_assignments.py` → 100% / confiante-errado 0 mantido (D1 não toca o scorer; só leitura + consenso de código).
- [ ] **Censo no repo real (user-side):** `python scripts/eval_code_block_census.py <Metodos-Formais-Tutor>` (após reprocesso/retag). Critérios:
  - **carded**: mudanças são melhorias (passam a bater o bloco do card) — 0 regressão.
  - **faixa do meio** (sem card, band != baixa): inspecionar cada `mudou=SIM` contra o ground truth — nenhum vira confiante-errado.
  - **fraca** (sem card, band baixa): `computed` deve == `gemini` (o consenso adotou). Se divergir, revisar a Task 2.
- [ ] **Escalada 3b (só se a faixa do meio regredir):** estender `code_curation_signal_text` para o scorer de BLOCO de código (hoje só alimenta o subunit) e/ou regenerar a `.md` curada com concepts no tempo da regeneração (também conserta o follow-up de `source_importers.py:75`). Vira plano próprio, gated neste censo.

---

## Self-Review

**Spec coverage:** D1=A do spec — fonte única `computed_block_id` (Task 3), Gemini vira voto band-gated (Task 2), secondaries mantidos, eval-gate (Task 4 + seção). Timing verificado (Task 1). ✓

**Placeholder scan:** sem TBD/TODO. Tasks 3 deixam explícito ao implementer ajustar nomes de função/strings de saída APÓS ler `repo.py` (o contrato — agrupar por computed, não por gemini — está fixo no teste); isso é instrução de verificação, não placeholder de lógica. ✓

**Type consistency:** `resolve_effective_block(entry_dict, blocks).id` usado igual nos 3 sites; recebe `e.to_dict()` (FileEntry) + `timeline_blocks` (param presente nas 3 funções). `confidence_band(float)` em attach. `summary`/`method` reusados do laço existente em attach. ✓

**Risco residual tratado:** consenso band-gated (Task 2) garante mudança ≥ hoje por construção (card e funil-forte nunca sobrescritos; fraca-sem-card cai no Gemini = comportamento atual); o censo (Task 4) prova a faixa do meio; escalada 3b gated. ✓
