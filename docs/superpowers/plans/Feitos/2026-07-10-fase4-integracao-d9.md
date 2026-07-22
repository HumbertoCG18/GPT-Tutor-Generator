# FASE 4 — Integração D9 (AnchorEngine no reprocess) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AnchorEngine substitui `apply_anchor_placement` no call-site do reprocess, atrás de feature-flag por-curso, com funil intacto: flag-OFF ⇒ saída byte-idêntica; flag-ON ⇒ sem-regressão 5/5 no gold (pair_key), `computed_*` inalterado, só `temporal_*`.

**Architecture:** O motor (`src/builder/routing/motor/`) ganha um producer `apply.py` (escreve `temporal_*` ANCHOR-ONLY, honra pino manual, propaga TIER 0 por md5) e um loader único `context.py` (memoizações `_global_df`/`_modal_years`/`normalized_card_map`; probes migram pra cá). O call-site `pedagogical_regeneration.py:379` ganha um ramo novo gated em `use_anchor_engine` (flag por-curso via `SubjectProfile.feature_flags`, injeção genérica já existente em `_build_options_from_config`, app.py:99-103); o ramo legado `use_anchor_placement` fica intacto até o cutover FASE 5. TIER 3 (voter) é opt-in separado (`use_llm_voter`), com cache sidecar no repo-tutor, thread-safety e observabilidade.

**Tech Stack:** Python 3, pytest, google-genai (lazy), tkinter (Dashboard).

## Global Constraints (não-negociáveis, valem para TODAS as tasks)

- Tudo que CC roda sozinho é READ-ONLY nos repos-tutor; escrever temporal/sidecar = reprocess = ação do user na GUI.
- Lógica nova SÓ em `src/builder/routing/motor/` (e `scripts/`); NUNCA `engine.py`.
- ANCHOR-ONLY: escreve só `temporal_*`; NUNCA toca `computed_block_id` nem `manual_timeline_block_id`.
- NÃO commitar sem autorização explícita da sessão (re-perguntar; não transfere entre sessões).
- Guard AST: proibido importar `block_token_weights`, `score_entry_against_timeline_block`, `select_probable_period_for_entry` no pacote do motor.
- LLM = `google-genai` lazy dentro de método; PROIBIDO `google.generativeai`/`genai.GenerativeModel`. Modelo pinado explícito (não-alias) como default.
- PRÉ-GATE: `scripts/audit_gold_freshness.py` antes de QUALQUER medição contra golds (falso-alarme conhecido: SO `lista2` ADMIN_TRUE).
- Regressão = 5 probes em conjunto (`fase0 && fase1 && fase2_SO && fase2_TCC && fase3`) + suite (`python -m pytest tests -q`). Baseline da sessão 10/07: 5/5 PASS + 1743 passed/4 skipped/0 failed.
- Autoconfiança do LLM NUNCA lida por gate. Voto não se re-roda por capricho (spec §12 regra 4).
- UTF-8 shim em script novo (`sys.stdout.reconfigure(encoding="utf-8", errors="replace")`); PT-BR nos docs.
- Âncoras re-verificadas 10/07: call-site gate `pedagogical_regeneration.py:379` (spec dizia 381, drift -2); `apply_anchor_placement:344`, `AnchorResult:77`, `resolve_placement:258` (anchor_placement.py); `SubjectProfile.feature_flags` `src/models/core.py:244`; `resolve_temporal_block` `file_map.py:617`; `DEFAULT_MODEL` `gemini_client.py:11`; combo/fallback `dialogs.py:441`/`:430`; `_global_df` `disambiguator.py:119`; `_modal_years` `window_provider.py:48`; `_top_candidate_blocks` `cronograma_health.py:114`; `_entry_label` `timeline_dashboard.py:304`.

## Decisões para o PLANO-REVIEW (user decide antes da execução)

**D-A (item 1 do handoff, [DECISION]) — D4 × janela-1 degenerada.**
Decisão D4-flagada (ou membro de série) com |janela|==1 entra no voto com UM candidato: o LLM confirma e desflaga sem informação nova.
- **Opção A (RECOMENDADA):** excluir |janela|==1 do escopo do voto (gate `len(window) > 1` no hook do voter). Determinístico, zero prompt-engineering, o FLAG honesto sobrevive pra fila humana.
- Opção B: opção "nenhum destes" no prompt (mantém janela-1 no escopo; voto "nenhum" mantém FLAG). Mais recall teórico, mas re-abre calibração de prompt (spec §12 regra 4 desaconselha).
- Task 3 implementa a Opção A; se B for escolhida, a task é re-escrita antes da execução.

**D-B — nome da flag da integração.**
Spec §7 diz "AnchorEngine SUBSTITUI apply_anchor_placement". IA já roda `use_anchor_placement=true` com a semântica LEGADA (33 temporal, 2 movers validados).
- **Recomendação:** flag NOVA `use_anchor_engine` com precedência sobre a legada no call-site (`if use_anchor_engine: motor; elif use_anchor_placement: legado`). Substituição efetiva ocorre por-curso quando o user liga a flag nova; caminho legado morre no cutover FASE 5. Evita mudar o IA silenciosamente antes do rollout gold-gated.
- Alternativa: trocar a implementação sob a MESMA flag `use_anchor_placement` (IA muda no próximo reprocess, sem gate por-curso novo).

**D-C (item 8 do handoff) — decisão `cronograma_health`.**
`_top_candidate_blocks` (cronograma_health.py:114-171) reusa o scorer S2 condenado (`score_entry_against_timeline_block`), pré-requisito nomeado da deleção FASE 5.
- **Recomendação:** entry com `temporal_block_window` serializada (motor flag-ON) usa a JANELA como lista de candidatos no health (sem re-scoring); sem o campo, cai no caminho legado S2. Na FASE 5, o caminho legado morre junto com o S2. Badges band/flag/provider do Dashboard (Task 8) cobrem a triagem.
- Alternativa: portar o scoring do disambiguator pro health (mais custo, valor marginal sobre a janela ordenada).

---

### Task 1: Pré-flight modelo morto (item 0 — PRIMEIRO, antes de qualquer chamada Gemini)

**Files:**
- Modify: `src/builder/runtime/gemini_client.py:11`
- Modify: `src/ui/dialogs.py:430` e `:441`
- Test: `tests/test_gemini_default_model.py` (novo)

**Interfaces:**
- Consumes: `DEFAULT_MODEL` (gemini_client.py:11, hoje `"gemini-2.5-flash"`, MORTO no endpoint generateContent; metadados ainda respondem).
- Produces: `DEFAULT_MODEL = "gemini-3.5-flash"` (stable atual, PINADO não-alias — inventário live 09/07: `gemini-3.5-flash` e alias `gemini-flash-latest` resolvem; lição 404: alias mascara mudança, então o DEFAULT é o pinado).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gemini_default_model.py
"""Guard do pré-flight FASE 4 (item 0): modelo default vivo e zero refs ao morto."""
from pathlib import Path


def test_default_model_is_pinned_live():
    from src.builder.runtime.gemini_client import DEFAULT_MODEL
    assert DEFAULT_MODEL == "gemini-3.5-flash"


def test_no_dead_gemini_25_reference_in_src():
    root = Path(__file__).resolve().parents[1] / "src"
    hits = sorted(
        str(p) for p in root.rglob("*.py")
        if "gemini-2.5" in p.read_text(encoding="utf-8")
    )
    assert hits == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_gemini_default_model.py -v`
Expected: FAIL — `assert 'gemini-2.5-flash' == 'gemini-3.5-flash'` e hits com `gemini_client.py` + `dialogs.py`.

- [ ] **Step 3: Write minimal implementation**

`src/builder/runtime/gemini_client.py:11`:
```python
DEFAULT_MODEL = "gemini-3.5-flash"
```

`src/ui/dialogs.py:430`:
```python
        self._var_gemini_model = tk.StringVar(value=self.config.get("gemini_model", "gemini-3.5-flash"))
```

`src/ui/dialogs.py:441` (combo — os dois valores vivos confirmados na API em 09/07; alias documentado como segunda opção consciente):
```python
                     values=["gemini-3.5-flash", "gemini-flash-latest"],
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_gemini_default_model.py tests/test_motor_llm_vote.py -v`
Expected: PASS (llm_vote não referencia modelo por string; guard confirma zero `gemini-2.5` em `src/`).

- [ ] **Step 5: Regressão rápida**

Run: `python -m pytest tests -q`
Expected: 1745 passed (1743 + 2 novos) / 4 skipped / 0 failed.

- [ ] **Step 6: Commit (SÓ com autorização de commit da sessão)**

```bash
git add tests/test_gemini_default_model.py src/builder/runtime/gemini_client.py src/ui/dialogs.py
git commit -m "fix(gemini): pre-flight FASE 4 — DEFAULT_MODEL e UI migram do gemini-2.5-flash aposentado (404) para gemini-3.5-flash pinado"
```

---

### Task 2: `motor/context.py` — loader único + memoizações (item 5)

**Files:**
- Create: `src/builder/routing/motor/context.py`
- Modify: `src/builder/routing/motor/contracts.py` (3 slots de cache no `MotorContext`)
- Modify: `src/builder/routing/motor/disambiguator.py:119` (`_global_df` usa cache)
- Modify: `src/builder/routing/motor/window_provider.py:48` (`_modal_years` usa cache) e `_card_entry` (usa cache do mapa normalizado)
- Modify: `scripts/fase0_prova_motor_MF.py` (loader `build_context` vira re-export)
- Test: `tests/test_motor_context.py` (novo)

**Interfaces:**
- Consumes: `MotorContext.from_artifacts` (contracts.py:46); `card_block.normalized_card_map(card_map) -> Dict[str, dict]` (card_block.py:159, whitelist do guard AST).
- Produces: `context.load_repo_artifact(repo: Path, rel: str) -> dict|list`; `context.build_motor_context(repo: Path, course_name: str = "") -> MotorContext`. Slots novos no `MotorContext`: `_global_df_cache: Optional[dict]`, `_modal_years_cache: Optional[list]`, `_ncm_cache: Optional[dict]` (todos `field(default=None, repr=False, compare=False)`). Tasks 6 e 11 consomem `build_motor_context`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_context.py
"""FASE 4 item 5: loader único do motor + memoização por-contexto."""
import json

from src.builder.routing.motor.context import build_motor_context, load_repo_artifact


def _write(repo, rel, data):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")


def _fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "course/.timeline_index.json", {"blocks": [
        {"id": "bloco-01", "block_uuid": "u-1", "period_start": "2026-03-01",
         "sessions": [{"date": "2026-03-02", "label": "Aula 1"}]},
        {"id": "bloco-02", "block_uuid": "u-2", "period_start": "2026-03-08",
         "sessions": [{"date": "2026-03-09", "label": "Aula 2"}]},
    ]})
    _write(repo, "course/.card_block_map.json", {"card x": {"blocks": ["bloco-01"]}})
    _write(repo, "course/.lessons_index.json", {"by_date": {"2026-03-02": "inducao"}})
    return repo


def test_build_motor_context_loads_artifacts(tmp_path):
    ctx = build_motor_context(_fixture_repo(tmp_path), "Curso X")
    assert [b["id"] for b in ctx.blocks] == ["bloco-01", "bloco-02"]
    assert ctx.lessons_index == {"2026-03-02": "inducao"}
    assert ctx.course_name == "Curso X"
    assert ctx.block_by_ref("u-2")["id"] == "bloco-02"


def test_load_repo_artifact_missing_or_corrupt(tmp_path):
    assert load_repo_artifact(tmp_path, "nao/existe.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{quebrado", encoding="utf-8")
    assert load_repo_artifact(tmp_path, "bad.json") == {}


def test_global_df_memoized_per_context(tmp_path):
    from src.builder.routing.motor.disambiguator import _global_df
    ctx = build_motor_context(_fixture_repo(tmp_path))
    first = _global_df(ctx)
    assert _global_df(ctx) is first          # mesma instância = cache hit
    ctx2 = build_motor_context(_fixture_repo(tmp_path))
    assert _global_df(ctx2) is not first     # contexto novo = cache próprio


def test_modal_years_memoized_per_context(tmp_path):
    from src.builder.routing.motor.window_provider import _modal_years
    ctx = build_motor_context(_fixture_repo(tmp_path))
    first = _modal_years(ctx)
    assert _modal_years(ctx) is first
    assert "2026" in first
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_context.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.routing.motor.context'`.

- [ ] **Step 3: Write minimal implementation**

`src/builder/routing/motor/context.py` (novo):
```python
"""Loader único do motor (FASE 4 item 5): artefatos por-curso + memoizações.

Fonte única do que os probes fase0-3 duplicavam (build_context). READ-ONLY:
lê os 3 artefatos gerados do repo-tutor, nunca escreve.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.builder.routing.motor.contracts import MotorContext


def load_repo_artifact(repo: Path, rel: str):
    p = Path(repo) / rel
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_motor_context(repo: Path, course_name: str = "") -> MotorContext:
    tl = load_repo_artifact(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = load_repo_artifact(repo, "course/.card_block_map.json")
    lessons = (load_repo_artifact(repo, "course/.lessons_index.json") or {}).get("by_date", {})
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index=lessons,
        course_name=course_name,
    )
```

`contracts.py` — adicionar 3 slots ao dataclass `MotorContext` (depois de `_by_ref`, contracts.py:43):
```python
    _global_df_cache: Optional[dict] = field(default=None, repr=False, compare=False)
    _modal_years_cache: Optional[list] = field(default=None, repr=False, compare=False)
    _ncm_cache: Optional[dict] = field(default=None, repr=False, compare=False)
```
(Sem lógica no contracts — só shape, coerente com a docstring do módulo.)

`disambiguator.py:119` — envolver o corpo EXISTENTE de `_global_df` com o cache (duas linhas; corpo intacto):
```python
def _global_df(ctx: MotorContext) -> dict:
    """df de cada token sobre as assinaturas de TODOS os blocos do curso."""
    if ctx._global_df_cache is not None:
        return ctx._global_df_cache
    df: dict = {}
    # ... (corpo atual inalterado, linhas 122-124) ...
    ctx._global_df_cache = df
    return df
```

`window_provider.py:48` — mesmo padrão em `_modal_years` (guard no topo, atribuição antes do return). Em `_card_entry`, substituir a reconstrução do mapa normalizado por:
```python
    if ctx._ncm_cache is None:
        ctx._ncm_cache = normalized_card_map(ctx.card_block_map)
    entry = ctx._ncm_cache.get(...)  # mesma chave de lookup atual
```
(Verificar o call-site exato com `grep -n "normalized_card_map" src/builder/routing/motor/window_provider.py` — a chave de lookup NÃO muda.)

`scripts/fase0_prova_motor_MF.py` — `build_context` vira re-export (probes fase1/2/3 importam de fase0, então UM ponto muda):
```python
from src.builder.routing.motor.context import build_motor_context as build_context  # loader migrado (F4 item 5)
```
Remover o corpo antigo de `build_context` e o helper `_load` se ficar órfão (verificar com grep).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_context.py tests/test_motor_contracts.py tests/test_motor_anchor_engine.py tests/test_motor_golden_mf.py -v`
Expected: PASS (gold embutido byte-idêntico: memoização não muda resultado, só evita recomputo).

- [ ] **Step 5: Regressão dos probes (byte-idêntico)**

Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py && python scripts/fase2_prova_SO.py && python scripts/fase2_prova_TCC.py && python scripts/fase3_prova_LLM_MF.py`
Expected: 5/5 PASS com números idênticos ao baseline (MF 82.8/conf-errado 1/recall 0.900; SO 45.2/0/0; TCC 5/5/83.3/0; fase3 lift +3, 0 chamadas API — all-cache).

- [ ] **Step 6: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/builder/routing/motor/context.py src/builder/routing/motor/contracts.py src/builder/routing/motor/disambiguator.py src/builder/routing/motor/window_provider.py scripts/fase0_prova_motor_MF.py tests/test_motor_context.py
git commit -m "feat(motor): context.py — loader único + memoizações _global_df/_modal_years/normalized_card_map (F4 item 5)"
```

---

### Task 3: Gate D4 × janela-1 no escopo do voto (item 1 — Opção A da decisão D-A)

**Files:**
- Modify: `src/builder/routing/motor/anchor_engine.py:56-57`
- Test: `tests/test_motor_anchor_engine.py` (estende; usa o `_FakeVoter` existente em :90)

**Interfaces:**
- Consumes: `AnchorEngine.resolve` (anchor_engine.py:46); `_FakeVoter` do teste existente.
- Produces: hook do voter só dispara com `len(window) > 1`. Contrato inalterado para os demais casos.

- [ ] **Step 1: Write the failing test**

Adicionar em `tests/test_motor_anchor_engine.py` (reusar `_ctx`/helpers do arquivo; se o fixture atual não tiver caso janela-1, montar card map com card apontando pra UM bloco):

```python
def test_janela_1_nao_entra_no_voto_mesmo_em_serie():
    """D4×janela-1 (decisão D-A, 10/07): voto com 1 candidato desflaga sem
    informação nova. |janela|==1 fica FORA do escopo do voter; a decisão
    determinística (e o FLAG, se houver) sobrevive pra fila humana."""
    ctx = _ctx_janela_unica()          # card 'aula unica' -> ['bloco-01']
    entry = {"id": "e1", "title": "Aula 3", "source_section": "aula unica",
             "category": "materiais"}
    voter = _FakeVoter("bloco-01")
    eng = AnchorEngine(voter=voter, series_ids={"e1"})
    d = eng.resolve(entry, ctx)
    assert d is not None and d.block_ref
    assert voter.calls == 0            # janela-1: voter NUNCA chamado
    assert d.provider != "llm" and d.method != "llm"
```

(Se `_FakeVoter` não tiver contador `calls`, adicionar `self.calls = 0` no `__init__` e `self.calls += 1` no `vote` do fake — mudança só no teste.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_anchor_engine.py -v -k janela_1_nao_entra`
Expected: FAIL — `assert voter.calls == 0` (hoje o voter é chamado se flag/série, mesmo com janela-1).

- [ ] **Step 3: Write minimal implementation**

`anchor_engine.py:56` — uma condição a mais no hook:
```python
        if self._voter is not None and len(window) > 1 and (
                decision.flag or str(entry.get("id") or "") in self._series_ids):
```
E na docstring da classe, adicionar a linha: `Janela-1 NUNCA vota (D4×janela-1, decisão 10/07): 1 candidato = voto sem informação.`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_anchor_engine.py -v`
Expected: PASS (novo + existentes).

- [ ] **Step 5: Medição honesta — fase3 all-cache**

Run: `python scripts/fase3_prova_LLM_MF.py`
Expected: PASS lift >= +3, 0 chamadas API. Se o lift MUDAR (havia janela-1 no escopo do voto do MF), REPORTAR o número novo ao user SEM iterar (spec §12 regra 4): FAIL de medição = resultado honesto = decisão do user.

- [ ] **Step 6: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/builder/routing/motor/anchor_engine.py tests/test_motor_anchor_engine.py
git commit -m "fix(motor): D4xjanela-1 — |janela|==1 fora do escopo do voto TIER 3 (F4 item 1, opção A)"
```

---

### Task 4: LlmVoter — concorrência do cache + observabilidade (itens 3-parcial e 4)

**Files:**
- Modify: `src/builder/routing/motor/llm_vote.py` (classe `LlmVoter:173`)
- Test: `tests/test_motor_llm_vote.py` (estende; usa `_entry`/`_ctx`/`FakeClient` existentes)

**Interfaces:**
- Consumes: `load_material_curation:61`, `save_material_curation:73`, `content_key:45` (mesmo arquivo).
- Produces: `LlmVoter` thread-safe com contadores novos `no_key`, `cache_hits` e métodos `round_summary() -> dict` e `prune(live_keys: set) -> int`. Persistência vira merge-on-save (lost-update morre). Task 7 consome `round_summary`; Task 5 consome `prune`.

- [ ] **Step 1: Write the failing tests**

Adicionar em `tests/test_motor_llm_vote.py`:

```python
def test_persist_merges_disk_state(tmp_path):
    """Duas instâncias no MESMO cache: a segunda não apaga o voto da primeira
    (last-writer-wins morto; review final F3)."""
    cache = tmp_path / "material_curation.json"
    e1, e2 = _entry("a"), _entry("b")
    ctx = _ctx()
    va = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient("bloco-01"))
    vb = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient("bloco-01"))
    va.vote(e1, ["bloco-01"], ctx)          # persiste voto de e1
    vb.vote(e2, ["bloco-01"], ctx)          # vb carregou ANTES do save de va
    final = json.loads(cache.read_text(encoding="utf-8"))["votes"]
    assert len(final) == 2                   # merge, não overwrite


def test_error_is_logged_not_swallowed(caplog):
    """Item 4: exceção da API vira WARNING com id da entry e tipo do erro
    (o 404 da F3 só foi visto reproduzindo por fora)."""
    class Boom:
        model = "x"
        def summarize_bundle(self, *a, **k):
            raise RuntimeError("404 model retired")
    v = LlmVoter({}, cache_path=Path("nao-usado.json"), repo_dir=Path("."), client=Boom())
    with caplog.at_level("WARNING"):
        got = v.vote(_entry("a"), ["bloco-01"], _ctx())
    assert got is None and v.errors == 1
    assert any("RuntimeError" in r.message and "404" in r.message for r in caplog.records)


def test_no_key_counter_and_round_summary(tmp_path):
    v = LlmVoter({}, cache_path=tmp_path / "c.json", repo_dir=tmp_path, client=None)
    v._client_loaded = True                  # simula get_gemini_client -> None
    assert v.vote(_entry("a"), ["bloco-01"], _ctx()) is None
    s = v.round_summary()
    assert s["no_key"] == 1 and s["calls"] == 0
    assert set(s) == {"calls", "errors", "skipped_cap", "no_key", "cache_hits"}


def test_prune_removes_orphan_keys(tmp_path):
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps({"version": 1, "votes": {
        "viva": {"block_id": "bloco-01"}, "orfa": {"block_id": "bloco-02"}}}),
        encoding="utf-8")
    v = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient("bloco-01"))
    assert v.prune({"viva"}) == 1
    assert set(json.loads(cache.read_text(encoding="utf-8"))["votes"]) == {"viva"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_motor_llm_vote.py -v -k "persist_merges or error_is_logged or no_key or prune"`
Expected: FAIL — merge (1 voto no disco), caplog vazio, `AttributeError: round_summary`, `AttributeError: prune`.

- [ ] **Step 3: Write minimal implementation**

Em `llm_vote.py`, topo do arquivo: `import logging`, `import threading`; `logger = logging.getLogger(__name__)`.

`LlmVoter.__init__` ganha:
```python
        self._lock = threading.Lock()
        self.no_key = 0
        self.cache_hits = 0
```

Método novo `_persist` (merge-on-save) + `prune` + `round_summary`:
```python
    def _persist(self) -> None:
        disk = load_material_curation(self._cache_path)
        merged = dict(disk.get("votes") or {})
        merged.update(self._data["votes"])
        self._data["votes"] = merged
        save_material_curation(self._cache_path, self._data)

    def prune(self, live_keys: set) -> int:
        """Remove votos cuja identidade de conteúdo sumiu do manifest (item 2).

        Merge-on-save como _persist: poda computada sobre a visão disco∪memória,
        senão o save cru apagaria voto concorrente de outra instância.
        [CORRIGIDO no review da Task 4 — snippet original salvava cru]"""
        with self._lock:
            disk = load_material_curation(self._cache_path)
            merged = dict(disk.get("votes") or {})
            merged.update(self._data["votes"])
            stale = [k for k in merged if k not in live_keys]
            for k in stale:
                merged.pop(k, None)
            self._data["votes"] = merged
            if stale:
                save_material_curation(self._cache_path, self._data)
        return len(stale)

    def round_summary(self) -> dict:
        return {"calls": self.calls, "errors": self.errors,
                "skipped_cap": self.skipped_cap, "no_key": self.no_key,
                "cache_hits": self.cache_hits}
```

No `vote()` (corpo atual :204-233), mudanças cirúrgicas:
1. Envolver do lookup `cached = ...` até o `save` com `with self._lock:` (o `match_window_ref` final fica fora do lock).
2. `if cached is None:` ... ramo `client is None` vira:
```python
            if client is None:
                self.no_key += 1
                logger.info("TIER 3: sem gemini_api_key; voto pulado p/ %s", entry.get("id"))
                return None
```
3. Ramo `except Exception as exc:` vira:
```python
            except Exception as exc:  # noqa: BLE001 — voto falhou: FLAG fica, sem cache
                self.errors += 1
                logger.warning("TIER 3: voto falhou p/ %s (%s: %s)",
                               entry.get("id"), type(exc).__name__, exc)
                return None
```
4. `else`-side do cache hit: `self.cache_hits += 1` quando `cached` já existia.
5. Trocar `save_material_curation(self._cache_path, self._data)` por `self._persist()`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_motor_llm_vote.py -v`
Expected: PASS (novos + existentes; erro continua NÃO cacheado, voto fora da janela continua cacheado).

- [ ] **Step 5: fase3 all-cache (contrato intacto)**

Run: `python scripts/fase3_prova_LLM_MF.py`
Expected: PASS lift >= +3, 0 chamadas API.

- [ ] **Step 6: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/builder/routing/motor/llm_vote.py tests/test_motor_llm_vote.py
git commit -m "feat(motor): LlmVoter thread-safe (merge-on-save) + observabilidade (log de erro, no_key, round_summary, prune) — F4 itens 3/4"
```

---

### Task 5: Sidecar `material_curation.json` no repo-tutor (item 2)

**Files:**
- Modify: `src/builder/routing/motor/llm_vote.py` (constante de path + docstring)
- Test: `tests/test_motor_llm_vote.py` (estende)

**Interfaces:**
- Consumes: convenção do `code_curation.json` (sidecar na RAIZ do repo gerado: `repo_dir / "code_curation.json"`, ver codes_panel.py:110 e navigation.py:591).
- Produces: `material_curation_path(repo_dir: Path) -> Path` = `repo_dir / "material_curation.json"`. Task 7 usa este path no wiring do reprocess. Cache dos PROBES continua em `docs/reports/material_curation_MF.json` (separado, probe passa `cache_path` explícito — nada muda nos scripts).

- [ ] **Step 1: Write the failing test**

```python
def test_material_curation_path_segue_convencao_code_curation(tmp_path):
    from src.builder.routing.motor.llm_vote import material_curation_path
    assert material_curation_path(tmp_path) == tmp_path / "material_curation.json"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_llm_vote.py -v -k material_curation_path`
Expected: FAIL — `ImportError: cannot import name 'material_curation_path'`.

- [ ] **Step 3: Write minimal implementation**

Em `llm_vote.py`, após `save_material_curation`:
```python
def material_curation_path(repo_dir: Path) -> Path:
    """Sidecar de votos no repo-tutor (spec §12 item 10): raiz, como code_curation.json.

    Escrito SÓ pelo reprocess (ação do user na GUI). Probes usam cache próprio
    em docs/reports/ — nunca este path.
    """
    return Path(repo_dir) / "material_curation.json"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_llm_vote.py -v`
Expected: PASS.

- [ ] **Step 5: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/builder/routing/motor/llm_vote.py tests/test_motor_llm_vote.py
git commit -m "feat(motor): material_curation_path — sidecar de votos na raiz do repo-tutor (F4 item 2)"
```

---

### Task 6: `motor/apply.py` — producer D9 ANCHOR-ONLY (núcleo)

**Files:**
- Create: `src/builder/routing/motor/apply.py`
- Test: `tests/test_motor_apply.py` (novo)

**Interfaces:**
- Consumes: `AnchorEngine` (anchor_engine.py:32), `build_motor_context` (Task 2), `content_key`/`detect_same_theme_series` (llm_vote.py:45/:101), `MotorContext.block_by_ref` (contracts.py:68).
- Produces: `apply_anchor_engine(entries: list, repo_dir, course_name: str, *, enabled: bool = True, voter=None, markdown_fn=None) -> list` e a constante `TEMPORAL_KEYS`. Escreve por entry: `temporal_block_id` (uuid quando existe), `temporal_block_method`, `temporal_block_band`, `temporal_block_flag`, `temporal_block_provider`, `temporal_block_window` (refs display, consumida pela Task 9). Tasks 7 e 11 consomem.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_motor_apply.py
"""FASE 4 D9: producer do motor — ANCHOR-ONLY, pino manual intocável, TIER 0."""
import copy
import json

from src.builder.routing.motor.apply import TEMPORAL_KEYS, apply_anchor_engine


def _repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".timeline_index.json").write_text(json.dumps({"blocks": [
        {"id": "bloco-01", "block_uuid": "u-1", "period_start": "2026-03-01",
         "sessions": [{"date": "2026-03-02", "label": "inducao estrutural"}]},
        {"id": "bloco-02", "block_uuid": "u-2", "period_start": "2026-03-08",
         "sessions": [{"date": "2026-03-09", "label": "logica de hoare"}]},
    ]}), encoding="utf-8")
    (repo / "course" / ".card_block_map.json").write_text(json.dumps(
        {"card a": {"blocks": ["bloco-01", "bloco-02"]}}), encoding="utf-8")
    (repo / "course" / ".lessons_index.json").write_text(json.dumps(
        {"by_date": {}}), encoding="utf-8")
    return repo


def _entries():
    return [
        {"id": "e1", "title": "inducao estrutural slides", "category": "materiais",
         "source_section": "card a", "computed_block_id": "u-1"},
        {"id": "pin", "title": "qualquer", "category": "materiais",
         "source_section": "card a", "computed_block_id": "u-1",
         "manual_timeline_block_id": "u-2",
         "temporal_block_id": "stale", "temporal_block_method": "anchor"},
        {"id": "fora", "title": "plano de ensino", "category": "bibliografia",
         "computed_block_id": "u-1"},
    ]


def test_flag_off_e_byte_identico(tmp_path):
    entries = _entries()
    before = copy.deepcopy(entries)
    out = apply_anchor_engine(entries, _repo(tmp_path), "MF", enabled=False)
    assert out == before


def test_pino_manual_nunca_recebe_temporal_e_stale_sai(tmp_path):
    entries = _entries()
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    pin = next(e for e in entries if e["id"] == "pin")
    assert pin["manual_timeline_block_id"] == "u-2"       # verdade humana intacta
    assert all(k not in pin for k in TEMPORAL_KEYS)        # temporal stale removido


def test_anchor_only_computed_intocado_e_temporal_escrito(tmp_path):
    entries = _entries()
    before = copy.deepcopy(entries)
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    for e, b in zip(entries, before):
        assert e.get("computed_block_id") == b.get("computed_block_id")
    e1 = next(e for e in entries if e["id"] == "e1")
    assert e1.get("temporal_block_id") in {"u-1", "u-2"}   # uuid, não display
    assert e1.get("temporal_block_window") == ["bloco-01", "bloco-02"]
    assert "temporal_block_band" in e1 and "temporal_block_provider" in e1


def test_fora_do_motor_nao_ganha_temporal(tmp_path):
    entries = _entries()
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    fora = next(e for e in entries if e["id"] == "fora")
    assert all(k not in fora for k in TEMPORAL_KEYS)       # bibliografia -> funil


def test_tier0_gemeos_md5_mesma_decisao(tmp_path):
    repo = _repo(tmp_path)
    twin = repo / "twin.pdf"
    twin.write_bytes(b"conteudo identico")
    entries = [
        {"id": "g1", "title": "inducao 1", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
        {"id": "g2", "title": "inducao 2", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
    ]
    apply_anchor_engine(entries, repo, "MF")
    assert entries[0].get("temporal_block_id") == entries[1].get("temporal_block_id")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_motor_apply.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.routing.motor.apply'`.

- [ ] **Step 3: Write minimal implementation**

`src/builder/routing/motor/apply.py` (novo):
```python
"""Producer D9 (FASE 4): AnchorEngine -> temporal_* nas entries, in place.

Substitui apply_anchor_placement no call-site quando use_anchor_engine=ON
(caminho legado intacto até o cutover FASE 5). Invariantes:
- ANCHOR-ONLY: nunca toca computed_* nem manual_timeline_block_id.
- Pino manual válido = verdade humana: motor NÃO escreve e REMOVE temporal
  stale (leitor resolve_temporal_block cai no fallback manual>computed).
- TIER 0: grupo md5 (content_key) recebe UMA decisão (dup-divergence = 0).
- Sem âncora (None) = funil-piso: temporal_* removido se existia.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from src.builder.routing.motor.anchor_engine import AnchorEngine
from src.builder.routing.motor.context import build_motor_context
from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor.llm_vote import content_key, detect_same_theme_series

TEMPORAL_KEYS = (
    "temporal_block_id", "temporal_block_method", "temporal_block_band",
    "temporal_block_flag", "temporal_block_provider", "temporal_block_window",
)


def _valid_manual_pin(entry: dict, ctx: MotorContext) -> bool:
    pin = str(entry.get("manual_timeline_block_id") or "").strip()
    return bool(pin) and ctx.block_by_ref(pin) is not None


def _clear_temporal(entry: dict) -> None:
    for key in TEMPORAL_KEYS:
        entry.pop(key, None)


def _write_temporal(entry: dict, decision: AnchorDecision, ctx: MotorContext) -> None:
    block = ctx.block_by_ref(decision.block_ref) or {}
    entry["temporal_block_id"] = str(block.get("block_uuid") or decision.block_ref)
    entry["temporal_block_method"] = decision.method
    entry["temporal_block_band"] = decision.band
    entry["temporal_block_flag"] = bool(decision.flag)
    entry["temporal_block_provider"] = decision.provider
    entry["temporal_block_window"] = [str(r) for r in (decision.window or [])]


def apply_anchor_engine(
    entries: list,
    repo_dir,
    course_name: str,
    *,
    enabled: bool = True,
    voter=None,
    markdown_fn: Optional[Callable[[dict], str]] = None,
) -> list:
    if not enabled:
        return entries
    repo = Path(repo_dir)
    ctx = build_motor_context(repo, course_name)
    if not ctx.blocks:
        return entries
    series = detect_same_theme_series(entries)
    engine = AnchorEngine(voter=voter, series_ids=series)
    md_of = markdown_fn or (lambda e: "")
    decided: dict = {}
    for entry in entries:
        if _valid_manual_pin(entry, ctx):
            _clear_temporal(entry)
            continue
        key = content_key(entry, repo)
        if key in decided:
            decision = decided[key]
        else:
            decision = engine.resolve(entry, ctx, markdown=str(md_of(entry) or ""))
            decided[key] = decision
        if decision is None:
            _clear_temporal(entry)
            continue
        _write_temporal(entry, decision, ctx)
    return entries
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_motor_apply.py tests/test_motor_anchor_engine.py -v`
Expected: PASS. Nota: `test_temporal_block_wire.py` e `test_anchor_placement.py` devem seguir verdes (caminho legado intocado): `python -m pytest tests/test_temporal_block_wire.py tests/test_anchor_placement.py -q`.

- [ ] **Step 5: Guard AST do motor**

Run: `python -m pytest tests -q -k "import_guard or motor"`
Expected: PASS (apply.py não importa símbolo condenado).

- [ ] **Step 6: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/builder/routing/motor/apply.py tests/test_motor_apply.py
git commit -m "feat(motor): apply.py — producer D9 ANCHOR-ONLY (pino manual intocável, TIER 0 por md5, temporal_* serializado com band/flag/provider/window)"
```

---

### Task 7: Call-site — flags `use_anchor_engine` + `use_llm_voter` no reprocess (núcleo + item 3)

> **[CORRIGIDO no review da Task 7]** O bloco do call-site abaixo foi entregue extraído num
> helper `_run_anchor_engine_layer(builder, live_manifest_entries)` com try/except Exception
> (log WARNING "camada temporal pulada") — falha de I/O do voter/prune NÃO derruba a
> regeneração (precedente Approach C do mesmo arquivo). O branch `if use_anchor_engine`
> chama só o helper; o elif legado permanece byte-idêntico.

**Files:**
- Modify: `src/builder/ops/pedagogical_regeneration.py` (:376-384 e helper novo perto de `_resolve_gemini_client:20`)
- Test: `tests/test_motor_apply.py` (estende — testes do wiring)

**Interfaces:**
- Consumes: `apply_anchor_engine`/`TEMPORAL_KEYS` (Task 6), `LlmVoter`+`material_curation_path`+`content_key` (Tasks 4/5), `_entry_markdown_text_for_file_map` (navigation.py:83, já usado em `run_material_residual:66`), `builder.options` (flags injetadas por `_build_options_from_config`, app.py:99-103 — injeção genérica, NENHUMA mudança na UI é necessária), `builder.root_dir`, `builder.course_meta`.
- Produces: ramo motor no call-site com precedência `use_anchor_engine` > `use_anchor_placement` (legado); helper `_build_motor_voter(builder) -> LlmVoter|None` (opt-in `use_llm_voter`, cap=20, sidecar do repo, prune de órfãos, log do `round_summary`). O reprocess roda na task queue (background) — o voter NÃO roda na UI thread, mesmo padrão avisado em `run_material_residual`.

- [ ] **Step 1: Write the failing tests**

Adicionar em `tests/test_motor_apply.py`:

```python
def test_build_motor_voter_off_por_default(tmp_path):
    from src.builder.ops.pedagogical_regeneration import _build_motor_voter

    class _B:
        options = {}
        root_dir = tmp_path
    assert _build_motor_voter(_B()) is None


def test_build_motor_voter_on_sem_chave_degrada_none(tmp_path, monkeypatch):
    from src.builder.ops import pedagogical_regeneration as pr

    class _B:
        options = {"use_llm_voter": True}
        root_dir = tmp_path
    monkeypatch.setattr(pr.Path, "home", lambda: tmp_path)  # sem config -> sem chave
    assert pr._build_motor_voter(_B()) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_motor_apply.py -v -k build_motor_voter`
Expected: FAIL — `ImportError: cannot import name '_build_motor_voter'`.

- [ ] **Step 3: Write minimal implementation**

Em `pedagogical_regeneration.py`, garantir `from pathlib import Path` no topo (verificar imports atuais) e adicionar após `_resolve_gemini_client` (:41):

```python
def _build_motor_voter(builder):
    """Voter TIER 3 do motor. OPT-IN por flag de curso `use_llm_voter`.

    None em qualquer falha/ausência: voter=None => AnchorEngine byte-idêntico
    às FASES 0-2 (determinístico). Cache = sidecar do repo-tutor; o reprocess
    roda na task queue (background), nunca na UI thread. Cap=20 (orçamento D8).
    """
    options = getattr(builder, "options", {}) or {}
    if not bool(options.get("use_llm_voter", False)):
        return None
    try:
        import json as _json
        from src.builder.routing.motor.llm_vote import LlmVoter, material_curation_path

        cfg_path = Path.home() / ".gpt_tutor_config.json"
        config = _json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
        if not isinstance(config, dict) or not str(config.get("gemini_api_key") or "").strip():
            return None
        return LlmVoter(
            config,
            cache_path=material_curation_path(builder.root_dir),
            repo_dir=builder.root_dir,
            cap=20,
        )
    except Exception:
        return None
```

Substituir o bloco do gate (:376-384) por:

```python
    # Camada de placement por âncora (TEMPORAL-only, aditiva). Escreve
    # temporal_* sem tocar computed_block_id (KB). Precedência: motor D9
    # (use_anchor_engine, FASE 4) > legado (use_anchor_placement, morre no
    # cutover FASE 5). Imports function-local sob o gate (padrão existente).
    if bool(builder.options.get("use_anchor_engine", False)):
        from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
        from src.builder.routing.motor.apply import apply_anchor_engine
        from src.builder.routing.motor.llm_vote import content_key

        voter = _build_motor_voter(builder)
        if voter is not None:
            live_keys = {content_key(e, builder.root_dir) for e in live_manifest_entries}
            pruned = voter.prune(live_keys)
            if pruned:
                logger.info("motor/voter: %d voto(s) órfão(s) removido(s) do sidecar", pruned)
        live_manifest_entries = apply_anchor_engine(
            live_manifest_entries,
            builder.root_dir,
            str((builder.course_meta or {}).get("course_name") or ""),
            enabled=True,
            voter=voter,
            markdown_fn=lambda e: _entry_markdown_text_for_file_map(builder.root_dir, e) or "",
        )
        if voter is not None:
            logger.info("motor/voter round_summary: %s", voter.round_summary())
    elif bool(builder.options.get("use_anchor_placement", False)):
        from src.builder.routing.anchor_placement import apply_anchor_placement
        live_manifest_entries = apply_anchor_placement(
            live_manifest_entries,
            enriched_timeline_index.get("blocks") or [],
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_motor_apply.py -v`
Expected: PASS.

- [ ] **Step 5: Regressão da suite (flags ausentes = caminho intocado)**

Run: `python -m pytest tests -q`
Expected: 0 failed. Com AMBAS as flags ausentes o diff de comportamento é zero (byte-idêntico estrutural: ramo novo não executa).

- [ ] **Step 6: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/builder/ops/pedagogical_regeneration.py tests/test_motor_apply.py
git commit -m "feat(motor): call-site D9 — use_anchor_engine substitui apply_anchor_placement por-curso; voter opt-in use_llm_voter com sidecar+prune+summary (F4)"
```

---

### Task 8: Badges band/flag/provider no Timeline Dashboard (item 7)

**Files:**
- Modify: `src/ui/timeline_dashboard.py` (`_entry_label:304`)
- Test: `tests/test_timeline_dashboard_badges.py` (novo)

**Interfaces:**
- Consumes: campos serializados pela Task 6 (`temporal_block_band`, `temporal_block_flag`, `temporal_block_provider`).
- Produces: `motor_badge(entry: dict) -> str` e `_entry_label` com badge anexado. REGRA (review F3): o consumidor lê `band` como autoritativo, NUNCA `conf`/`computed_block_band` (decisão votada mantém conf determinístico residual).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_timeline_dashboard_badges.py
"""Item 7 F4: badge do motor na linha do material — band autoritativa, não conf."""
from src.ui.timeline_dashboard import _entry_label, motor_badge


def test_motor_badge_band_flag_provider():
    e = {"temporal_block_band": "media", "temporal_block_flag": True,
         "temporal_block_provider": "llm"}
    assert motor_badge(e) == "[media ⚑ llm]"


def test_motor_badge_sem_flag():
    e = {"temporal_block_band": "alta", "temporal_block_provider": "labels"}
    assert motor_badge(e) == "[alta labels]"


def test_motor_badge_vazio_sem_motor():
    assert motor_badge({}) == ""
    assert motor_badge({"computed_block_band": "alta"}) == ""  # conf/computed NÃO vaza


def test_entry_label_anexa_badge():
    e = {"title": "inducao.pdf", "temporal_block_band": "media",
         "temporal_block_provider": "llm"}
    label = _entry_label(e)
    assert "inducao.pdf" in label and "[media llm]" in label
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_timeline_dashboard_badges.py -v`
Expected: FAIL — `ImportError: cannot import name 'motor_badge'`.

- [ ] **Step 3: Write minimal implementation**

Em `timeline_dashboard.py`, antes de `_entry_label:304`:
```python
def motor_badge(entry: dict) -> str:
    """Badge do motor (F4 item 7): band/flag/provider serializados pelo D9.

    band é o sinal AUTORITATIVO de confiança do temporal (review F3): decisão
    votada carrega conf determinístico residual — conf/computed_* NUNCA entram
    aqui. Vazio quando a entry não passou pelo motor.
    """
    band = str(entry.get("temporal_block_band") or "").strip()
    if not band:
        return ""
    parts = [band]
    if entry.get("temporal_block_flag"):
        parts.append("⚑")
    provider = str(entry.get("temporal_block_provider") or "").strip()
    if provider:
        parts.append(provider)
    return "[" + " ".join(parts) + "]"
```

Em `_entry_label:304`, anexar o badge ao label existente (preservar o corpo atual; só a linha de retorno muda):
```python
    badge = motor_badge(entry)
    return f"{label} {badge}" if badge else label
```
(onde `label` é a expressão hoje retornada — renomear a expressão de retorno atual para a variável `label` sem alterá-la.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_timeline_dashboard_badges.py -v && python -m pytest tests -q -k dashboard`
Expected: PASS (novo + existentes do dashboard).

- [ ] **Step 5: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/ui/timeline_dashboard.py tests/test_timeline_dashboard_badges.py
git commit -m "feat(dashboard): badge band/flag/provider do motor nas linhas de material — band autoritativa (F4 item 7)"
```

---

### Task 9: `cronograma_health` lê a janela do motor (item 8 — decisão D-C)

**Files:**
- Modify: `src/builder/artifacts/cronograma_health.py` (novo helper + gate no chamador de `_top_candidate_blocks:114`)
- Test: `tests/test_cronograma_health_window.py` (novo)

**Interfaces:**
- Consumes: `temporal_block_window` (Task 6); `_top_candidate_blocks:114` (legado S2, fica como fallback flag-OFF até a FASE 5).
- Produces: `_candidate_refs(entry: dict, blocks: list) -> list[tuple[str, Optional[float]]]` — janela do motor quando presente (score `None`), senão S2 legado. Isto fecha o pré-requisito da deleção S2 no cutover F5: cursos flag-ON não tocam o scorer condenado.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cronograma_health_window.py
"""Item 8 F4 (decisão D-C): health usa a janela serializada do motor;
S2 legado só quando a entry não passou pelo motor."""
from src.builder.artifacts.cronograma_health import _candidate_refs


def test_janela_do_motor_substitui_scoring_s2():
    entry = {"temporal_block_window": ["bloco-03", "bloco-04"]}
    refs = _candidate_refs(entry, blocks=[])
    assert refs == [("bloco-03", None), ("bloco-04", None)]


def test_sem_janela_cai_no_caminho_legado():
    # blocks=[] faz o caminho legado degradar para [] (comportamento atual
    # documentado de _top_candidate_blocks) — o que importa é NÃO explodir
    # e NÃO inventar candidatos.
    assert _candidate_refs({}, blocks=[]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cronograma_health_window.py -v`
Expected: FAIL — `ImportError: cannot import name '_candidate_refs'`.

- [ ] **Step 3: Write minimal implementation**

Em `cronograma_health.py`, após `_top_candidate_blocks` (:171):
```python
def _candidate_refs(entry: dict, blocks: list) -> list:
    """Candidatos p/ material flagado. Janela do motor (F4) quando serializada:
    lista ordenada sem re-scoring — o S2 condenado (cutover F5) só roda p/
    entries que não passaram pelo motor (flag OFF)."""
    window = [str(r) for r in (entry.get("temporal_block_window") or []) if str(r)]
    if window:
        return [(ref, None) for ref in window]
    return _top_candidate_blocks(entry, blocks)
```
No(s) call-site(s) de `_top_candidate_blocks` dentro deste arquivo (localizar com `grep -n "_top_candidate_blocks(" src/builder/artifacts/cronograma_health.py`), trocar a chamada por `_candidate_refs(entry, blocks)` e, no render, formatar score `None` como `—` (sem número inventado).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cronograma_health_window.py -v && python -m pytest tests -q -k health`
Expected: PASS.

- [ ] **Step 5: Commit (SÓ com autorização de commit da sessão)**

```bash
git add src/builder/artifacts/cronograma_health.py tests/test_cronograma_health_window.py
git commit -m "feat(health): candidatos via janela do motor; S2 legado vira fallback flag-OFF (F4 item 8, pré-requisito do cutover F5)"
```

---

### Task 10: Gold → `block_uuid` (item 6 — decisão user 08/07)

**Files:**
- Create: `scripts/migrate_gold_uuid.py`
- Modify: `scripts/fase0_prova_motor_MF.py` (helper `true_of`), `scripts/fase1_recall_gate_MF.py`, `scripts/fase2_prova_SO.py`, `scripts/fase2_prova_TCC.py`, `scripts/fase3_prova_LLM_MF.py` (trocar leituras diretas de `r["true_block_id"]` por `true_of(ctx, r)`)
- Data: `docs/reports/ground_truth_{MF,IA,SO,TCC,ES2}.csv` (coluna nova `true_block_uuid`)

**Interfaces:**
- Consumes: `ctx.block_by_ref` (contracts.py:68); repos: MF=`Metodos-Formais-Tutor`, IA=`Inteligencia-Artifical-Tutor` (typo real do repo, crosscheck_IA.py:134), SO=`Sistemas-Operacionais-Tutor`, TCC=`TCC-Tutor` (defaults dos scripts); ES2 SEM default conhecido — passar `--es2 PATH` ou o curso é PULADO com aviso.
- Produces: CSVs com coluna extra `true_block_uuid` (rótulo display preservado; nada removido); `true_of(ctx, row) -> str` em fase0 (re-exportado pros demais probes): uuid-first com fallback display. O gold vira robusto a drift posicional pós-reprocess; `audit_gold_freshness.py` CONTINUA pré-gate até os 5 CSVs migrados e verificados.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Migra os gold CSVs para block_uuid (decisão user 08/07): adiciona coluna
true_block_uuid resolvendo o display true_block_id no ledger do repo-tutor.

READ-ONLY nos repos-tutor; escreve SÓ nos CSVs de docs/reports/ deste repo.
Display fica (humano lê); uuid vira a referência estável (drift posicional
pós-reprocess não invalida mais o gold).

Uso: python scripts/migrate_gold_uuid.py [--es2 PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.builder.routing.motor.context import build_motor_context  # noqa: E402

GH = Path.home() / "Documents" / "GitHub"
REPOS = {
    "MF": GH / "Metodos-Formais-Tutor",
    "IA": GH / "Inteligencia-Artifical-Tutor",
    "SO": GH / "Sistemas-Operacionais-Tutor",
    "TCC": GH / "TCC-Tutor",
    "ES2": None,  # sem default conhecido: --es2 obrigatório p/ migrar ES2
}


def migrate(course: str, repo: Path, dry: bool) -> tuple:
    gold = ROOT / "docs" / "reports" / f"ground_truth_{course}.csv"
    if not gold.is_file():
        return (0, 0, f"sem CSV: {gold.name}")
    ctx = build_motor_context(repo)
    if not ctx.blocks:
        return (0, 0, f"repo sem timeline: {repo}")
    with open(gold, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if "true_block_uuid" not in fields:
        fields.append("true_block_uuid")
    ok = miss = 0
    for r in rows:
        display = str(r.get("true_block_id") or "").strip()
        b = ctx.block_by_ref(display) if display else None
        if b is not None and b.get("block_uuid"):
            r["true_block_uuid"] = str(b["block_uuid"])
            ok += 1
        else:
            r.setdefault("true_block_uuid", "")
            if display:
                miss += 1
    if not dry:
        with open(gold, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    return (ok, miss, "ok" if not dry else "dry-run")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--es2", default=None, help="path do repo ES2-Tutor")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.es2:
        REPOS["ES2"] = Path(args.es2)
    failures = 0
    for course, repo in REPOS.items():
        if repo is None or not Path(repo).is_dir():
            print(f"  {course}: PULADO (repo ausente — passe --es2/clone)")
            continue
        ok, miss, status = migrate(course, Path(repo), args.dry_run)
        print(f"  {course}: {ok} uuid resolvidos, {miss} sem match [{status}]")
        if miss:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Dry-run**

Run: `python scripts/migrate_gold_uuid.py --dry-run`
Expected: contagens por curso; `miss > 0` em qualquer curso = investigar ANTES de escrever (display que não resolve = drift; rodar `python scripts/audit_gold_freshness.py` — gold = verdade humana, re-rotulagem só com sign-off do user).

- [ ] **Step 3: Migrar de verdade + helper nos probes**

Run: `python scripts/migrate_gold_uuid.py` (com `--es2` se o path existir).

Em `scripts/fase0_prova_motor_MF.py`, adicionar:
```python
def true_of(ctx, row) -> str:
    """Verdade do gold em DISPLAY: uuid-first (estável a drift posicional),
    fallback true_block_id legado enquanto a coluna não existe."""
    uid = str(row.get("true_block_uuid") or "").strip()
    if uid:
        b = ctx.block_by_ref(uid)
        if b is not None:
            return str(b.get("id") or uid)
    return str(row.get("true_block_id") or "").strip()
```
Nos 5 probes, trocar CADA comparação/leitura `r["true_block_id"]` (localizar com `grep -n "true_block_id" scripts/fase*.py`) por `true_of(ctx, r)` (import de fase0, padrão já usado pelos probes 1-3).

- [ ] **Step 4: Regressão dos 5 probes**

Run: `python scripts/audit_gold_freshness.py && python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py && python scripts/fase2_prova_SO.py && python scripts/fase2_prova_TCC.py && python scripts/fase3_prova_LLM_MF.py`
Expected: pré-gate limpo (falso-alarme SO `lista2` conhecido) e 5/5 PASS com números IDÊNTICOS ao baseline (uuid resolve pro mesmo display de hoje; qualquer divergência = drift real que o uuid acabou de expor — reportar, não mascarar).

- [ ] **Step 5: Commit (SÓ com autorização de commit da sessão)**

```bash
git add scripts/migrate_gold_uuid.py scripts/fase0_prova_motor_MF.py scripts/fase1_recall_gate_MF.py scripts/fase2_prova_SO.py scripts/fase2_prova_TCC.py scripts/fase3_prova_LLM_MF.py docs/reports/ground_truth_*.csv
git commit -m "feat(gold): migração block_uuid nos 5 CSVs + true_of uuid-first nos probes (F4 item 6, decisão 08/07)"
```

---

### Task 11: Régua da FASE 4 — `scripts/fase4_prova_D9.py` + regressão total

**Files:**
- Create: `scripts/fase4_prova_D9.py`
- Test: a régua É o teste (veredito HARD composto, padrão fase0-3)

**Interfaces:**
- Consumes: `apply_anchor_engine`/`TEMPORAL_KEYS` (Task 6), `build_motor_context` (Task 2), `LlmVoter` (Task 4), `true_of`/`collapse`/`display_of`/`_md_text` (fase0), gold MF, cache `docs/reports/material_curation_MF.json` (cópia p/ temp — o original é READ-ONLY do probe F3).
- Produces: veredito HARD do número da FASE 4: **flag-OFF byte-idêntico; flag-ON `computed_*` inalterado, só `temporal_*`; pino manual intocado; dup-divergence 0; gold pair-colapsado sem regressão (det ≥ 82.8%, conf-errado ≤ 1; com voter cacheado ≥ 87.9%, conf-errado 0)**.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""FASE 4 — prova D9: apply_anchor_engine vs manifest MF (READ-ONLY no repo).

Número do aceite (spec §7 FASE 4): flag-OFF ⇒ byte-idêntico; flag-ON ⇒
computed_* inalterado, só temporal_*; pino manual nunca sobrescrito;
dup-divergence 0; gold MF pair-colapsado sem regressão:
  det (voter=None):        acc >= 82.8% e confiante-errado <= 1  (baseline F0)
  voter all-cache (cap=0): acc >= 87.9% e confiante-errado == 0  (baseline F3)

PRE-GATE: rode scripts/audit_gold_freshness.py antes de medir.
Uso: python scripts/fase4_prova_D9.py [--repo PATH] [--gold CSV]
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.builder.routing.motor.apply import TEMPORAL_KEYS, apply_anchor_engine   # noqa: E402
from src.builder.routing.motor.context import build_motor_context               # noqa: E402
from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope      # noqa: E402
from src.builder.routing.motor.llm_vote import LlmVoter                         # noqa: E402
from fase0_prova_motor_MF import _md_text, collapse, display_of, true_of        # noqa: E402

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = ROOT / "docs" / "reports" / "ground_truth_MF.csv"
CACHE_F3 = ROOT / "docs" / "reports" / "material_curation_MF.json"
ACC_DET_MIN, CW_DET_MAX = 48 / 58, 1   # fração exata baseline F0 (precedente F1: evita FAIL espúrio de float)
ACC_LLM_MIN, CW_LLM_MAX = 51 / 58, 0   # fração exata baseline F3


def _gold_check(entries, ctx, gold_path, repo) -> tuple:
    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    byid = {str(e.get("id")): e for e in entries}
    res, cw = {}, 0
    for r in rows:
        e = byid.get(r["id"])
        if e is None:
            continue
        if is_out_of_disamb_scope(e):
            # universo dos pisos 82.8/87.9 = escopo-disamb de fase0/fase3 (58 rows);
            # TIER-2 (trabalhos/provas/TDE) fica no funil por design — dívida F5.
            continue
        temporal = str(e.get("temporal_block_id") or "").strip()
        block = ctx.block_by_ref(temporal) if temporal else None
        pred = str((block or {}).get("id") or temporal) if temporal else ""
        if not pred:
            # sem temporal: funil-piso responde (computed via display)
            comp = ctx.block_by_ref(str(e.get("computed_block_id") or ""))
            pred = str((comp or {}).get("id") or e.get("computed_block_id") or "")
        truth = true_of(ctx, r)
        res[r["id"]] = (pred == truth)
        if (e.get("temporal_block_band") == "alta"
                and not e.get("temporal_block_flag") and pred != truth):
            cw += 1
    ok, tot = collapse(res, rows)
    return ok, tot, cw


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
    course_name = str((man.get("course") or {}).get("course_name") or "")
    entries0 = man.get("entries") or []
    ctx = build_motor_context(repo, course_name)
    md_fn = lambda e: _md_text(repo, e)  # noqa: E731

    # 1) flag-OFF byte-idêntico
    off = copy.deepcopy(entries0)
    apply_anchor_engine(off, repo, course_name, enabled=False)
    p_off = off == entries0
    print(f"flag-OFF byte-idêntico: {p_off}")

    # 2) flag-ON determinístico (voter=None)
    on = copy.deepcopy(entries0)
    apply_anchor_engine(on, repo, course_name, markdown_fn=md_fn)
    p_computed = all(
        {k: v for k, v in a.items() if not k.startswith("temporal_")}
        == {k: v for k, v in b.items() if not k.startswith("temporal_")}
        for a, b in zip(on, copy.deepcopy(entries0))
    )
    pins = [e for e in on if str(e.get("manual_timeline_block_id") or "").strip()
            and ctx.block_by_ref(str(e.get("manual_timeline_block_id")))]
    p_pins = all(all(k not in e for k in TEMPORAL_KEYS) for e in pins)
    from src.builder.routing.motor.llm_vote import content_key
    groups: dict = {}
    for e in on:
        groups.setdefault(content_key(e, repo), set()).add(
            str(e.get("temporal_block_id") or ""))
    p_dup = all(len(v) == 1 for v in groups.values())
    ok_d, tot_d, cw_d = _gold_check(on, ctx, gold_path, repo)
    acc_d = 100.0 * ok_d / tot_d if tot_d else 0.0
    p_det = (ok_d / tot_d if tot_d else 0.0) >= ACC_DET_MIN and cw_d <= CW_DET_MAX
    print(f"flag-ON det: computed intacto={p_computed} pinos intactos={p_pins} "
          f"({len(pins)} pinos) dup-div0={p_dup}")
    print(f"  gold pair-colapsado: {ok_d}/{tot_d} = {acc_d:.1f}% "
          f"(piso {100 * ACC_DET_MIN:.1f}) conf-errado={cw_d} (max {CW_DET_MAX})")

    # 3) flag-ON com voter ALL-CACHE (cap=0: zero chamadas API; cache copiado)
    p_llm = True
    if CACHE_F3.is_file():
        with tempfile.TemporaryDirectory() as td:
            tmp_cache = Path(td) / "material_curation.json"
            shutil.copy(CACHE_F3, tmp_cache)
            voter = LlmVoter({}, cache_path=tmp_cache, repo_dir=repo, cap=0)
            lv = copy.deepcopy(entries0)
            apply_anchor_engine(lv, repo, course_name, voter=voter, markdown_fn=md_fn)
            ok_l, tot_l, cw_l = _gold_check(lv, ctx, gold_path, repo)
        acc_l = 100.0 * ok_l / tot_l if tot_l else 0.0
        p_llm = (ok_l / tot_l if tot_l else 0.0) >= ACC_LLM_MIN and cw_l <= CW_LLM_MAX
        print(f"flag-ON voter all-cache: {ok_l}/{tot_l} = {acc_l:.1f}% "
              f"(piso {100 * ACC_LLM_MIN:.1f}) conf-errado={cw_l} (max {CW_LLM_MAX}) "
              f"chamadas API={voter.calls} (esperado 0)")
    else:
        print(f"AVISO: cache F3 ausente ({CACHE_F3.name}); passo voter pulado")

    ok = p_off and p_computed and p_pins and p_dup and p_det and p_llm
    print("=" * 70)
    print(f"VEREDITO FASE 4: {'PASS' if ok else 'FAIL'} "
          f"(off={p_off} computed={p_computed} pinos={p_pins} dup={p_dup} "
          f"det={p_det} voter={p_llm})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Pré-gate + rodar a prova**

Run: `python scripts/audit_gold_freshness.py && python scripts/fase4_prova_D9.py`
Expected: `VEREDITO FASE 4: PASS`. FAIL = resultado honesto → reportar ao user com os números (spec §12 regra 4; NÃO iterar calibração por conta própria).

- [ ] **Step 3: Regressão COMPLETA (régua de 6 probes agora) + suite**

Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py && python scripts/fase2_prova_SO.py && python scripts/fase2_prova_TCC.py && python scripts/fase3_prova_LLM_MF.py && python scripts/fase4_prova_D9.py && python -m pytest tests -q`
Expected: 6/6 PASS + suite 0 failed.

- [ ] **Step 4: Pós-verde — housekeeping obrigatório**

1. `docs/reports/pendencias.md`: fechar itens F4 (0-8 do handoff), registrar dívidas novas descobertas com tag [USER|CODE|DECISION].
2. `.mex/ROUTER.md` "Current Project State": entrada FASE 4 (motor integrado atrás de `use_anchor_engine`; voter `use_llm_voter`; régua agora 6 probes).
3. `docs/Overview-Sistema.html`: refletir integração D9 (attribution tabs).
4. `graphify update .`
5. Plano 100% verde → `git mv` deste arquivo para `docs/superpowers/plans/Feitos/` (com autorização de commit).
6. Reprocess REAL nos repos-tutor (escrever temporal/sidecar de verdade) = AÇÃO DO USER na GUI, curso a curso (rollout = FASE 5); ligar `use_anchor_engine`/`use_llm_voter` em `SubjectProfile.feature_flags` também é ação do user.

- [ ] **Step 5: Commit (SÓ com autorização de commit da sessão)**

```bash
git add scripts/fase4_prova_D9.py docs/reports/pendencias.md .mex/ROUTER.md docs/Overview-Sistema.html
git commit -m "feat(motor): FASE 4 — régua fase4_prova_D9 (flag-OFF byte-idêntico, flag-ON sem-regressão, pinos/dup/computed intactos) + housekeeping"
```

---

## Fora de escopo (registrado, NÃO fazer nesta fase)

- Janela-de-prazo TIER 2 (`assign_due` p/ trabalhos/provas/TDE): hoje essas categorias saem do motor via `_OUT_CATEGORIES` (funil, comportamento atual preservado). A janela-de-prazo real (T1/T2 MF → blocos 15/16) é dívida NOMEADA pro tracker; entra no rollout F5 com medição própria.
- Dívidas menores defer-F4 do review F3 (parent dir em `save_material_curation`; fold caso/acento em `source_section`; `match_window_ref` strip/casefold; truncamento do dry-run; stopwords PT no P4): ficam no ledger `.superpowers/sdd/progress.md`, não bloqueiam.
- Merge da branch: decisão do user (pendente desde F0; review whole-branch F3 = Ready to merge Yes).
- Fila humana MF (7 pinos, handoff §5): ação do user na GUI, opcional.

## Self-Review (executado na escrita, 10/07)

**1. Spec coverage:** item 0→Task 1; item 1→Task 3 (D-A); item 2→Tasks 5+7 (path+prune+wiring); item 3→Tasks 4+7 (lock/merge + opt-in flag; background = task queue, mesmo padrão `run_material_residual`); item 4→Task 4 (log+no_key+summary); item 5→Task 2; item 6→Task 10; item 7→Task 8; item 8→Task 9 (D-C); número da fase (flag-OFF/ON)→Tasks 6+11. TIER 0/pino manual (invariantes §4/§6 do spec que a integração OBRIGA a honrar: temporal vence manual no leitor `resolve_temporal_block:617`, então o producer TEM que proteger o pino)→Task 6. Janela-de-prazo explicitamente fora (seção acima). ✅
**2. Placeholder scan:** zero TBD/TODO; os dois pontos "verificar com grep" (call-site exato de `normalized_card_map` no `_card_entry`, call-sites de `_top_candidate_blocks`) são passos de VERIFICAÇÃO com comando dado, não lacunas de design. ✅
**3. Type consistency:** `apply_anchor_engine(entries, repo_dir, course_name, *, enabled, voter, markdown_fn)` idêntica nas Tasks 6/7/11; `TEMPORAL_KEYS` tupla de 6 strings nas Tasks 6/7/9/11; `round_summary()` chaves {calls,errors,skipped_cap,no_key,cache_hits} nas Tasks 4/7; `material_curation_path(repo_dir)->Path` nas Tasks 5/7; `true_of(ctx,row)->str` nas Tasks 10/11; `motor_badge(entry)->str` só Task 8; `_candidate_refs(entry,blocks)->list[tuple]` só Task 9. ✅
