# Gerador de Índice Único — Implementation Plan (campanha 1/3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Os 2 write-sites de `.timeline_index.json` (reprocess e rebuild_course) e as sondas produzem índice/taxonomia idênticos; bloco-13 TCC classifica `class` com taxonomia rica; TCC re-flip fecha 5/5 flag-ON.

**Architecture:** Guard anti-falso-exame no caminho de keyword do classifier (pré-requisito); depois montador único de taxonomia rica (`manifest_entries` vivas) consumido por W2 e sondas; serializador fantasma condenado por guard AST (deleção só no cutover); paridade do guard de encolhimento no W2; fix de precedência de pino na régua fase5.

**Tech Stack:** Python stdlib + pytest. Zero dependência nova.

**Spec:** `docs/superpowers/specs/2026-08-06-gerador-indice-unico-design.md` (ler antes).

## Global Constraints

- Repos-tutor READ-ONLY até a Task 7 (única escrita real = TCC re-flip, gated, com backup sha256 de tracked+gitignored antes).
- FAIL de qualquer gate = PARAR + diagnosticar + rollback. NUNCA re-tuning pós-hoc.
- NUNCA ASSUMIR: antes de editar, ler o trecho real; se divergir do plano, parar e registrar.
- Deleção física de legado PROIBIDA neste plano (condição do user; cutover deleta).
- Suite sempre `python -m pytest tests -q` (baseline atual: 1871 passed / 4 skipped / 0 failed).
- 7 probes (`fase0/fase1/fase2-SO/fase2-TCC/fase3/fase4/fase5`) byte-idênticos, EXCETO mudanças intencionais listadas na task que as causa.
- Flags atuais em `%APPDATA%/GPTTutorGenerator/subjects.json`: MF/SO/ES2/IA ON+ON, TCC `{}` — não tocar fora da Task 7.
- Commits: 1 por task, mensagem indicada na task.

---

### Task 1: Guard anti-falso-exame no classifier (C1)

**Files:**
- Modify: `src/builder/timeline/classifier.py:213-222` (loop de keywords)
- Create: `tests/test_classifier_guard_prova_plano.py`

**Interfaces:**
- Consumes: `classify_block`, `_STRONG_EXAM_RE` (`classifier.py:131`), `KIND_KEYWORDS` (`:53-99`), `BlockKind`.
- Produces: comportamento novo — keyword FRACA de ASSESSMENT (`"prova"`, `"avaliacao"`, `"exame"`, `"recuperacao"`, `"substitutiva"`, `"teste"`) só classifica assessment se `_STRONG_EXAM_RE` também casar em `hay_all`; specs regex (`\bp[1-4]\b`, `\bpf\b`) intocadas. Tasks 3/7 dependem disso.

- [x] **Step 1: Baseline PRÉ — rebuild_diff dry-run nos 5 cursos (captura, sem escrita)**

```powershell
python scripts/rebuild_diff.py > "$env:TEMP\rebuild_diff_PRE_task1.txt" 2>&1; Get-Content "$env:TEMP\rebuild_diff_PRE_task1.txt" -Tail 20
```
Guardar o arquivo; ele é a referência do Step 6. (rebuild_diff é `persist=False`, não grava — verificado `scripts/rebuild_diff.py:36-37`.)

- [x] **Step 2: Escrever os testes que falham**

```python
"""Guard anti-falso-exame: 'prova' vindo de rotulo de taxonomia/plano e
demonstracao, nao exame (caso real: TCC bloco-13, 'Prova da Indecidibilidade
do Problema da Parada' -> assessment indevido). Fixture copia contrato real
do bloco (ver institutional.md §Contratos; kind/period/campos conferidos no
.timeline_index.json real do TCC em 2026-08-06)."""
from src.builder.timeline.classifier import classify_block
from src.builder.timeline.kinds import BlockKind


def _bloco13_tcc(primary_topic_label):
    # Espelho do bloco real (TCC .timeline_index.json, bloco-13, conferido em disco):
    # sem source_kind, sem unit apos finalize (o cenario da taxonomia rica poe
    # o label contaminado e o positional pode nao ter setado unit ainda).
    return {
        "id": "bloco-13",
        "kind": "",
        "period_label": "1 dia · 24/04/2026",
        "topic_text": "problema da correspondencia de post",
        "primary_topic_label": primary_topic_label,
        "topics": [],
        "unit_slug": "",
        "auto_unit_slug": "",
        "sessions": [{"label": "problema da correspondencia de post aula", "kind": "class"}],
    }


def test_prova_de_demonstracao_no_label_nao_vira_assessment():
    b = _bloco13_tcc("Prova da Indecidibilidade do Problema da Parada")
    assert classify_block(b) is BlockKind.CLASS


def test_teste_nu_em_conteudo_nao_vira_assessment():
    b = _bloco13_tcc("Teste de mesa de algoritmos")
    assert classify_block(b) is BlockKind.CLASS


def test_exame_real_com_sinal_forte_segue_assessment_via_keyword():
    b = _bloco13_tcc("")
    b["topic_text"] = "prova p1 conteudo unidades 1 e 2"
    b["sessions"] = []
    assert classify_block(b) is BlockKind.ASSESSMENT  # regex \bp[1-4]\b e forte


def test_prova_n_segue_assessment():
    b = _bloco13_tcc("")
    b["topic_text"] = "prova 2 de sistemas"
    b["sessions"] = []
    assert classify_block(b) is BlockKind.ASSESSMENT  # "prova N" casa _STRONG_EXAM_RE
```

- [x] **Step 3: Rodar e confirmar RED no caso-alvo**

Run: `python -m pytest tests/test_classifier_guard_prova_plano.py -v`
Expected: `test_prova_de_demonstracao_no_label_nao_vira_assessment` FAIL (retorna ASSESSMENT hoje — keyword `prova` casa no label); `test_teste_nu...` FAIL; os 2 de sinal forte PASS. Se o RED não for exatamente esse, PARAR e diagnosticar antes de qualquer edit.

- [x] **Step 4: Implementar o guard (edit mínimo no loop :213-222)**

Trocar o corpo do passo 3 do `classify_block` por:

```python
    # 3. Keywords (sobre conteudo + period_label).
    hay_tokens = set(hay_all.split())
    for kind, specs in KIND_KEYWORDS:
        for spec in specs:
            if isinstance(spec, re.Pattern):
                if spec.search(hay_all):
                    return kind
            else:
                if _phrase_match(spec, hay_all, hay_tokens):
                    # Guard anti-falso-exame: "prova"/"teste" nus em texto de
                    # CONTEUDO sao vocabulario de plano de ensino (demonstracao,
                    # teste de mesa) - exame de verdade exige sinal forte
                    # (P1-4/PF/G2/PS/"prova N"), mesmo criterio do caminho de
                    # sessao (_session_exam_or_review).
                    if kind is BlockKind.ASSESSMENT and not _STRONG_EXAM_RE.search(hay_all):
                        continue
                    return kind
```

- [x] **Step 5: GREEN + suite completa**

Run: `python -m pytest tests/test_classifier_guard_prova_plano.py -v` → 4 PASS.
Run: `python -m pytest tests -q` → esperado 1875 passed / 4 skipped (1871+4). Qualquer FAIL = analisar; se for teste legado que assume "prova" nu ⇒ ASSESSMENT vindo de conteúdo, é exatamente a mudança intencional: registrar o teste, avaliar se o caso era falso-exame (corrigir o teste com nota) ou exame real (então o guard quebrou algo — PARAR).

- [x] **Step 6: Medição PÓS — rebuild_diff 5 cursos e diff contra o PRÉ**

```powershell
python scripts/rebuild_diff.py > "$env:TEMP\rebuild_diff_POS_task1.txt" 2>&1
git diff --no-index "$env:TEMP\rebuild_diff_PRE_task1.txt" "$env:TEMP\rebuild_diff_POS_task1.txt"
```
Esperado: ZERO diff (taxonomia dos caminhos de sonda ainda é pobre; o guard só muda casos com "prova"/"teste" nus em topic_text/period_label). **Qualquer diff = lista explícita curso/bloco/kind-antes-depois PARA RULING DO USER antes de commitar** (MF/SO/ES2/IA estão flag-ON em produção).

- [x] **Step 7: Probes 7/7 byte-idênticos**

```powershell
foreach ($p in "fase0_prova_motor_MF","fase1_recall_gate_MF","fase2_prova_SO","fase2_prova_TCC","fase3_prova_LLM_MF","fase4_prova_D9","fase5_prova_tier2") { python "scripts/$p.py" 2>&1 | Select-Object -Last 2 }
```
Esperado: mesmos vereditos/números da baseline da sessão (fase0 48/58 conten0 cw1 · fase1 9/10 · fase2-SO 45.2%/0/cw0 · fase2-TCC 5/5+83.3%+cw0+84.2% · fase3 lift+3/0 API · fase4 det 48/58 cw1, voter 51/58 cw0 calls0 · fase5 4/8 cw0). Restaurar `last_seen` do MF se bumpado (`git -C <MF> checkout -- course/.block_identity.json` só se o diff for exclusivamente `last_seen`).

- [x] **Step 8: Commit**

```bash
git add src/builder/timeline/classifier.py tests/test_classifier_guard_prova_plano.py
git commit -m "fix(classifier): keyword fraca de ASSESSMENT exige sinal forte — 'prova' de plano e demonstracao (C1, campanha indice)"
```

---

### Task 2: Precedência de pino na régua fase5 (C5)

**Files:**
- Modify: `scripts/fase5_prova_tier2.py:48-55` (`_effective_display`)

**Interfaces:**
- Consumes: manifest entries (campos `temporal_block_id`, `manual_timeline_block_id`, `computed_block_id`), `ctx.block_by_ref`.
- Produces: probe espelha a leitura de produção `resolve_temporal_block` → fallback manual→computed (`file_map.py:641-648` → `:594-613`). Task 7 usa esta régua no gate do re-flip.

- [x] **Step 1: Baseline — rodar a régua ANTES do fix e guardar**

```powershell
python scripts/fase5_prova_tier2.py > "$env:TEMP\fase5_PRE_pinfix.txt" 2>&1; Get-Content "$env:TEMP\fase5_PRE_pinfix.txt" -Tail 4
```
Esperado hoje: `PASS: acc 4/8 vs piso 4/8 · cw=0`.

- [x] **Step 2: Aplicar o fix (ordem temporal → manual → computed)**

Trocar `_effective_display` por:

```python
def _effective_display(e: dict, ctx) -> str:
    # Espelha a producao (resolve_temporal_block -> resolve_effective_block):
    # temporal vence; sem temporal, PINO MANUAL vence computed. O motor limpa
    # temporal_* em entry pinada (apply.py:73-75) exatamente para o leitor
    # cair no manual - a regua tem que cair igual.
    ref = str(e.get("temporal_block_id") or "").strip()
    if not ref:
        ref = str(e.get("manual_timeline_block_id") or "").strip()
    if not ref:
        ref = str(e.get("computed_block_id") or "").strip()
    if not ref:
        return ""
    block = ctx.block_by_ref(ref)
    return str((block or {}).get("id") or ref)
```

- [x] **Step 3: Re-rodar e comparar**

```powershell
python scripts/fase5_prova_tier2.py > "$env:TEMP\fase5_POS_pinfix.txt" 2>&1
git diff --no-index "$env:TEMP\fase5_PRE_pinfix.txt" "$env:TEMP\fase5_POS_pinfix.txt"
```
Esperado: veredito segue `PASS 4/8 cw=0`. Diff permitido APENAS em linha de entry pinada
(`revisao-p1-gabarito` tem pino trivial no MF) mudando a predição para o bloco do pino — se
mudar, documentar o delta no commit. Diff em entry NÃO-pinada = PARAR (fix errado).

- [x] **Step 4: Suite (probe não tem teste próprio; suite garante que nada importou dele)**

Run: `python -m pytest tests -q` → mesmo número da Task 1.

- [x] **Step 5: Commit**

```bash
git add scripts/fase5_prova_tier2.py
git commit -m "fix(fase5): regua honra pino manual entre temporal e computed (C5, espelha resolve_temporal_block)"
```

---

### Task 3: Montador único de taxonomia rica (C2)

**Files:**
- Create: `src/builder/ops/taxonomy_inputs.py`
- Modify: `src/builder/engine.py` (wire, 2 linhas: import + partial)
- Modify: `scripts/rebuild_timeline.py:66-68`
- Modify: `scripts/rebuild_diff.py:35-37`
- Modify: `scripts/retag_manifest.py` (bloco do `partial`, ~:53-57)
- Create: `tests/test_taxonomy_inputs.py`

**Interfaces:**
- Consumes: `build_file_map_content_taxonomy_from_course` (wired no engine como `_build_file_map_content_taxonomy_from_course`, `engine.py:2274`), `filter_live_manifest_entries` (`src/builder/artifacts/repo.py:207`).
- Produces: `build_rich_content_taxonomy(repo_root, course_meta, subject_profile, *, taxonomy_fn, filter_live_fn) -> dict` em `taxonomy_inputs.py`; wired no engine como `engine._build_rich_content_taxonomy(repo_root, course_meta, subject_profile)`. Tasks seguintes e sondas usam SEMPRE este nome.

- [x] **Step 1: Teste que falha (paridade montador == produção)**

```python
"""Montador unico de taxonomia rica: sonda == producao por construcao.
Fixture minima com contrato real de manifest (id/category/review_status;
ver institutional.md §Contratos)."""
import json
from pathlib import Path

from src.builder.ops.taxonomy_inputs import build_rich_content_taxonomy


def test_montador_passa_entries_vivas_para_taxonomy_fn(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({
        "course": {"name": "X"},
        "entries": [
            {"id": "a", "category": "material-de-aula", "review_status": "approved"},
            {"id": "b", "category": "material-de-aula", "review_status": "approved"},
        ],
    }), encoding="utf-8")
    seen = {}

    def fake_filter(root_dir, entries):
        seen["filter_args"] = (Path(root_dir), [e["id"] for e in entries])
        return entries[:1]  # simula filtro de vivas

    def fake_taxonomy(course_meta, subject_profile, manifest_entries=None):
        seen["entries_recebidas"] = [e["id"] for e in (manifest_entries or [])]
        return {"units": ["u"], "topics": []}

    out = build_rich_content_taxonomy(
        tmp_path, {"name": "X", "_repo_root": tmp_path}, None,
        taxonomy_fn=fake_taxonomy, filter_live_fn=fake_filter,
    )
    assert out == {"units": ["u"], "topics": []}
    assert seen["filter_args"][1] == ["a", "b"]      # leu o manifest real
    assert seen["entries_recebidas"] == ["a"]        # passou as VIVAS filtradas


def test_montador_sem_manifest_devolve_taxonomia_sem_entries(tmp_path):
    def fake_taxonomy(course_meta, subject_profile, manifest_entries=None):
        return {"units": [], "topics": [], "got": manifest_entries}
    out = build_rich_content_taxonomy(
        tmp_path, {}, None,
        taxonomy_fn=fake_taxonomy, filter_live_fn=lambda r, e: e,
    )
    assert out["got"] == []
```

- [x] **Step 2: RED**

Run: `python -m pytest tests/test_taxonomy_inputs.py -v` → FAIL (módulo não existe).

- [x] **Step 3: Implementar `src/builder/ops/taxonomy_inputs.py`**

```python
"""Montador UNICO de insumos de taxonomia (campanha gerador-indice-unico, C2).

Producao (pedagogical_regeneration.py:394-402) monta taxonomia com as entries
VIVAS do manifest; sondas e rebuild passavam content_taxonomy=None e caiam no
fallback pobre (index.py:1363, manifest_entries=None) - causa-raiz do flip de
kind do TCC bloco-13. Todo caminho fora da regeneracao monta a taxonomia POR
AQUI para que sonda == producao por construcao.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional


def build_rich_content_taxonomy(
    repo_root,
    course_meta: dict,
    subject_profile,
    *,
    taxonomy_fn: Callable[..., dict],
    filter_live_fn: Callable[..., list],
) -> dict:
    manifest_path = Path(repo_root) / "manifest.json"
    entries: list = []
    if manifest_path.is_file():
        try:
            entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("entries", []) or []
        except (json.JSONDecodeError, OSError):
            entries = []
    live = filter_live_fn(repo_root, entries)
    return taxonomy_fn(course_meta, subject_profile, live)
```

- [x] **Step 4: GREEN**

Run: `python -m pytest tests/test_taxonomy_inputs.py -v` → 2 PASS.

- [x] **Step 5: Wire no engine (façade — lógica fica no ops/)**

Em `src/builder/engine.py`, junto dos outros imports de ops (ler a vizinhança real antes; padrão do arquivo):

```python
from src.builder.ops.taxonomy_inputs import build_rich_content_taxonomy as _ops_build_rich_content_taxonomy
```

e, perto de `engine.py:2274` (onde vivem os aliases wired):

```python
def _build_rich_content_taxonomy(repo_root, course_meta, subject_profile):
    return _ops_build_rich_content_taxonomy(
        repo_root, course_meta, subject_profile,
        taxonomy_fn=_build_file_map_content_taxonomy_from_course,
        filter_live_fn=_filter_live_manifest_entries,
    )
```

VERIFICAR (nunca assumir) o nome wired real do filtro no engine: `grep -n "filter_live_manifest_entries" src/builder/engine.py`. Se o engine não o expõe, importar direto de `src/builder/artifacts/repo.py:207`.

- [x] **Step 6: Consumir nos 3 callers (cada um: ler o trecho real, editar, conferir)**

`scripts/rebuild_timeline.py:66-68` — trocar `content_taxonomy=None` por:

```python
        rich_taxonomy = engine._build_rich_content_taxonomy(repo_root, runtime_course_meta, subject_profile)
        ctx = engine._build_file_map_timeline_context_from_course(
            runtime_course_meta, subject_profile, content_taxonomy=rich_taxonomy, persist=WRITE
        )
```

`scripts/rebuild_diff.py:35-37` — idem:

```python
    rich_taxonomy = engine._build_rich_content_taxonomy(repo, {**cm, "_repo_root": repo}, sp)
    ctx = engine._build_file_map_timeline_context_from_course(
        {**cm, "_repo_root": repo}, sp, content_taxonomy=rich_taxonomy, persist=False
    )
```

`scripts/retag_manifest.py` (~:53-57) — o `partial` de contexto ganha a taxonomia rica:

```python
        build_file_map_timeline_context_from_course_fn=partial(
            _build_file_map_timeline_context_from_course, persist=False,
            content_taxonomy=_engine._build_rich_content_taxonomy(repo_root, {"_repo_root": repo_root}, subject_profile),
        ),
```

(Conferir os imports reais do retag antes — ele importa símbolos com underscore do engine; seguir o padrão do arquivo.)

- [x] **Step 7: Efeito medido — rebuild_diff agora com taxonomia rica, 5 cursos**

```powershell
python scripts/rebuild_diff.py > "$env:TEMP\rebuild_diff_POS_task3.txt" 2>&1; Get-Content "$env:TEMP\rebuild_diff_POS_task3.txt" -Tail 30
```
Esperado: TCC bloco-13 `class` (guard da Task 1 segurando a taxonomia rica); MUDANÇAS de
unit/topic label são ESPERADAS nos 5 (taxonomia rica melhora aliases — é o efeito pretendido).
Toda mudança de `kind` = lista curso/bloco/antes/depois; qualquer kind mudando fora do padrão
"falso-exame corrigido" = PARAR para ruling. Verificação A/B da causa-raiz (reproduz o
experimento do agente): com o guard, taxonomia rica NÃO flipa o bloco-13.

- [x] **Step 8: Suite + probes**

`python -m pytest tests -q` (mesma contagem) + os 7 probes byte-idênticos (probes não usam os 3 scripts alterados; qualquer mudança = investigar antes de seguir).

- [x] **Step 9: Commit**

```bash
git add src/builder/ops/taxonomy_inputs.py src/builder/engine.py scripts/rebuild_timeline.py scripts/rebuild_diff.py scripts/retag_manifest.py tests/test_taxonomy_inputs.py
git commit -m "feat(taxonomy): montador unico de taxonomia rica — W2 e sondas usam o insumo da producao (C2, mata dual-source de indice)"
```

---

### Task 4: Cobertura do serializador de produção + condenação do fantasma (C3)

**Files:**
- Create: `tests/test_persist_enriched_serializer.py`
- Modify: `docs/reports/pendencias.md` (item na lista de deleção do cutover)

**Interfaces:**
- Consumes: `persist_enriched_timeline_index` (`src/builder/core/core_utils.py:14-37`), `_serialize_timeline_index` (`src/builder/timeline/index.py:813-866`, fantasma).
- Produces: cobertura de teste do serializador que a PRODUÇÃO usa (hoje só o fantasma tem testes — inversão comprovada pela varredura) + guard AST impedindo caller novo de produção.

- [x] **Step 1: Testes (RED parcial — guard deve passar, cobertura é nova)**

```python
"""Serializador de PRODUCAO (persist_enriched_timeline_index) ganha cobertura
propria; o fantasma (_serialize_timeline_index, v4, filtra admin) fica
CONDENADO por guard ate a delecao no cutover. Contratos conferidos em
core_utils.py:14-37 e index.py:813-866 (2026-08-06)."""
import ast
from pathlib import Path

from src.builder.core.core_utils import persist_enriched_timeline_index


def test_producao_preserva_blocos_admin_e_versao_3():
    idx = {"version": 4, "blocks": [
        {"id": "bloco-01", "kind": "class", "rows": [1], "unit_slug": "u1"},
        {"id": "bloco-02", "kind": "assessment", "rows": [2], "unit_slug": ""},
        {"id": "bloco-03", "kind": "holiday", "rows": [3], "unit_slug": ""},
    ]}
    out = persist_enriched_timeline_index(idx)
    assert out["version"] == 3  # hardcode documentado (core_utils.py:35); mudanca so com varredura de leitores
    assert [b["id"] for b in out["blocks"]] == ["bloco-01", "bloco-02", "bloco-03"]  # admin NAO filtrado
    assert all("rows" not in b for b in out["blocks"])  # rows removidas
    assert out["blocks"][0]["unit_slug"] == "u1"        # kind/unit passthrough (sem reclassificar)


def test_fantasma_condenado_sem_caller_de_producao():
    """_serialize_timeline_index morre no cutover; ate la, nenhum caller novo em src/."""
    offenders = []
    for py in Path("src").rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Name) and n.id == "_serialize_timeline_index" for n in ast.walk(tree)):
            offenders.append(py.as_posix())
    allowed = {"src/builder/timeline/index.py", "src/builder/engine.py"}  # def + re-export historico
    assert set(offenders) <= allowed, f"caller novo do serializador condenado: {offenders}"
```

- [x] **Step 2: Rodar — cobertura PASS direto, guard PASS direto (estado atual já cumpre)**

Run: `python -m pytest tests/test_persist_enriched_serializer.py -v` → 2 PASS. Se o teste de
produção FALHAR, o contrato real difere do documentado — PARAR, ler `core_utils.py` de novo e
corrigir O TESTE com nota (não o serializador).

- [x] **Step 3: Registrar no tracker a entrada de cutover**

Em `docs/reports/pendencias.md`, adicionar ao item do mapa de deleção do cutover (lista de
símbolos condenados): `_serialize_timeline_index` (index.py:813-866) + testes legados dele
(tests/test_core.py:2939,2953,5248-5271; test_fileentry_roundtrip.py:155,181;
test_file_map_unit_mapping.py:1097) morrem JUNTOS no cutover; guard de condenação em
`tests/test_persist_enriched_serializer.py`.

- [x] **Step 4: Suite + commit**

```bash
python -m pytest tests -q
git add tests/test_persist_enriched_serializer.py docs/reports/pendencias.md
git commit -m "test(serializer): cobertura do serializador de producao + guard de condenacao do fantasma (C3; delecao fica pro cutover)"
```

---

### Task 5: Guard de encolhimento no W2 (C4)

**Files:**
- Modify: `scripts/rebuild_timeline.py` (antes do write, ~:94-101)
- Create: `tests/test_rebuild_course_guard.py`

**Interfaces:**
- Consumes: `_guard_units_not_silently_lost(root_dir, course_name, parsed_unit_count, new_index)` (`src/builder/ops/pedagogical_regeneration.py:275`) e `UnitsShrinkError`; call-site de referência W1: `pedagogical_regeneration.py:415-420` (LER antes e espelhar os argumentos exatos, inclusive como `parsed_unit_count` é computado do teaching_plan).
- Produces: `rebuild_course --write` aborta sem escrever quando o índice novo encolhe unidades.

- [x] **Step 1: Ler o call-site W1 real (`pedagogical_regeneration.py:405-425`) e copiar o padrão de argumentos**

Registrar no report da task o trecho lido. Se a assinatura divergir do plano, PARAR e ajustar.

- [x] **Step 2: Teste que falha (tmp repo + monkeypatch do build)**

```python
"""W2 (rebuild_course --write) ganha o mesmo guard de encolhimento do W1."""
import json
import pytest
from pathlib import Path

import scripts.rebuild_timeline as rt
from src.builder.ops.pedagogical_regeneration import UnitsShrinkError


class _Profile:
    teaching_plan = "**UNIDADE 1** A\n**UNIDADE 2** B\n**UNIDADE 3** C"
    syllabus = ""
    def __init__(self, root): self.repo_root = str(root)


def test_rebuild_write_aborta_em_encolhimento(tmp_path, monkeypatch):
    (tmp_path / "course").mkdir()
    (tmp_path / "manifest.json").write_text(json.dumps({"course": {"name": "X"}}), encoding="utf-8")
    # indice ANTIGO em disco: 3 unidades
    (tmp_path / "course" / ".timeline_index.json").write_text(json.dumps({
        "version": 3, "blocks": [
            {"id": "bloco-01", "kind": "class", "unit_slug": "u1"},
            {"id": "bloco-02", "kind": "class", "unit_slug": "u2"},
            {"id": "bloco-03", "kind": "class", "unit_slug": "u3"},
        ]}), encoding="utf-8")
    # build devolve indice ENCOLHIDO (1 unidade)
    shrunk = {"timeline_index": {"version": 3, "blocks": [
        {"id": "bloco-01", "kind": "class", "unit_slug": "u1"}]}}
    monkeypatch.setattr(rt.engine, "_build_file_map_timeline_context_from_course",
                        lambda *a, **k: shrunk)
    monkeypatch.setattr(rt, "WRITE", True, raising=False)
    before = (tmp_path / "course" / ".timeline_index.json").read_text(encoding="utf-8")
    ok = rt.rebuild_course("X", _Profile(tmp_path))
    after = (tmp_path / "course" / ".timeline_index.json").read_text(encoding="utf-8")
    assert after == before, "indice foi sobrescrito apesar do encolhimento"
    assert ok is False
```

(Se `rebuild_course` usar `WRITE` como global de módulo de outro nome/forma — LER `scripts/rebuild_timeline.py:31` antes — ajustar o monkeypatch para o mecanismo real.)

- [x] **Step 3: RED**

Run: `python -m pytest tests/test_rebuild_course_guard.py -v` → FAIL (hoje escreve o encolhido).

- [x] **Step 4: Implementar no `rebuild_course` (antes do write)**

Espelhando o call-site W1 lido no Step 1 (ajustar nomes ao trecho real):

```python
        if WRITE:
            from src.builder.ops.pedagogical_regeneration import (
                _guard_units_not_silently_lost, UnitsShrinkError,
            )
            try:
                parsed_units = engine._parse_units_from_teaching_plan(
                    getattr(subject_profile, "teaching_plan", "") or "")
                _guard_units_not_silently_lost(
                    repo_root, name, len(parsed_units), serialized)
            except UnitsShrinkError as exc:
                print(f"[FAIL] {name}: {exc} — indice NAO gravado")
                return False
```

- [x] **Step 5: GREEN + suite + commit**

```bash
python -m pytest tests/test_rebuild_course_guard.py tests -q
git add scripts/rebuild_timeline.py tests/test_rebuild_course_guard.py
git commit -m "fix(rebuild): guard UnitsShrinkError tambem no W2 — paridade de protecao com o reprocess (C4)"
```

---

### Task 6: Régua completa + registro R2-R12 no tracker

**Files:**
- Modify: `docs/reports/pendencias.md`

**Interfaces:**
- Consumes: resultados das Tasks 1-5.
- Produces: aceite §6.1-6.5 do spec fechado e documentado; tracker com a família R registrada.

- [x] **Step 1: Régua integral**

```powershell
python -m pytest tests -q
python scripts/rebuild_diff.py 2>&1 | Select-Object -Last 30
foreach ($c in "MF","SO","TCC","IA","ES2") { python scripts/audit_gold_freshness.py --course $c 2>&1 | Select-String "hard" }
```
Esperado: suite verde (contagem das tasks); rebuild_diff SEM mudança de kind pendente de ruling; audit hard=0 nos 5.

- [x] **Step 2: Registrar no tracker (CODE — bugs pré-existentes / seção própria "família dual-source")**

Adicionar itens com evidência file:line da varredura de 2026-08-06: R2 (render FILE_MAP
persist=True escreve ledger/manifest/curation — `navigation.py:525-529`+`teaching_timeline.py:93-95`),
R3 (bootstrap×regenerate mesmos .md insumos diferentes — `bootstrap_ops` vs
`pedagogical_regeneration`), R7 (4 loaders de índice com fallbacks distintos), R9
(`scan_existing_block_refs` lê nível errado do manifest — guard cego, `index.py:1401` +
`block_identity.py:269-272`), R11 (dashboard escreve manifest não-atômico,
`timeline_dashboard.py:248-251`), R12 (join de data truncado vs cru — `disambiguator.py:68` vs
`llm_vote.py:227-229`; candidato ao subprojeto SO), R4/R5/R6 (cutover — anexar à lista de
deleção). Marcar o que a campanha 1/3 já fechou: R10 (C2) + R8 (C5) + R1 (C3, condenado).

- [x] **Step 3: Commit**

```bash
git add docs/reports/pendencias.md
git commit -m "docs(tracker): familia dual-source R2-R12 registrada com evidencia; R1/R8/R10 fechados pela campanha 1/3"
```

---

### Task 7: TCC re-flip (aceite final — 5/5 flag-ON)

**Files:**
- Nenhum arquivo do projeto; escreve no repo-tutor `C:\Users\Humberto\Documents\GitHub\TCC-Tutor` e em `subjects.json`. ÚNICA task com escrita em repo-tutor.

**Interfaces:**
- Consumes: Tasks 1-6 verdes; cache `TCC-Tutor/material_curation.json` (16 votos, untracked); rito registrado em `docs/reports/2026-08-06-tcc-reflip-fail-report.md` (a tentativa 3 é o template do rito e do rollback).
- Produces: TCC flag-ON commitado OU FAIL honesto com rollback sha256 e diagnóstico.

- [x] **Step 1: Backup completo (tracked + gitignored, com verificação)**

```bash
TCC=/c/Users/Humberto/Documents/GitHub/TCC-Tutor
BK=/tmp/tcc-reflip4-backup; mkdir -p "$BK/course"
cp "$TCC/manifest.json" "$TCC/material_curation.json" "$BK/"
ls -a "$TCC/course/" | grep '^\.' | grep -v '^\.\{1,2\}$' > /tmp/tcc_hidden.txt
while read f; do cp "$TCC/course/$f" "$BK/course/$f" && echo "OK $f"; done < /tmp/tcc_hidden.txt
```
TODO arquivo listado deve ecoar OK (a lição da tentativa 3: glob silencioso = rede furada).

- [x] **Step 2: Baseline fase2-TCC + audit (pré-flip)**

```bash
python scripts/fase2_prova_TCC.py > /tmp/fase2_TCC_pre4.txt 2>&1; tail -3 /tmp/fase2_TCC_pre4.txt
python scripts/audit_gold_freshness.py --course TCC 2>&1 | grep hard
```
Esperado: PASS 5/5+83.3%+cw0+84.2%; hard=0. Diferente = PARAR (estado mudou desde o plano).

- [x] **Step 3: Flip via SubjectStore + round-trip 5 cursos**

```bash
python - <<'EOF'
import sys; sys.path.insert(0, '.')
from src.models.core import SubjectStore
st = SubjectStore()
p = st.get('Teoria da Computabilidade e Complexidade')
p.feature_flags = {'use_anchor_engine': True, 'use_llm_voter': True}
st.save()
st2 = SubjectStore()
for n in ['Metodos-Formais','Inteligencia Artificial','Teoria da Computabilidade e Complexidade','Sistemas Operacionais','Engenharia de Software II']:
    print(n, '->', st2.get(n).feature_flags)
EOF
```

- [x] **Step 4: Reprocess (T18, sem --flags) + gates estruturais**

```bash
python scripts/reprocess_assignments.py "C:/Users/Humberto/Documents/GitHub/TCC-Tutor" 2>&1 | tail -3
```
Gates (mesmo script da tentativa 3, `gate_tcc_reflip.py` do scratchpad — recriar se a sessão
morreu, o report da tentativa 3 documenta cada gate): (a) pinos 2/2 (`plano-de-ensino`,
`3d-matching`) intactos e sem temporal; (b) funil `auto_tags bloco:` ZERO drift vs backup;
computed 0 diffs; (c) temporal ~19/27, zero out-of-scope; (d) votos 16→16, 0 chaves novas.

- [x] **Step 5: CRITÉRIO DECISIVO — o que derrubou a tentativa 3**

```bash
python scripts/fase2_prova_TCC.py > /tmp/fase2_TCC_pos4.txt 2>&1
diff /tmp/fase2_TCC_pre4.txt /tmp/fase2_TCC_pos4.txt && echo BYTE-IDENTICO
python scripts/audit_gold_freshness.py --course TCC 2>&1 | grep hard
python - <<'EOF'
import json, io
idx = json.load(io.open(r"C:\Users\Humberto\Documents\GitHub\TCC-Tutor\course\.timeline_index.json", encoding="utf-8"))
b13 = [b for b in idx["blocks"] if b["id"] == "bloco-13"][0]
print("bloco-13 kind:", b13["kind"])
assert b13["kind"] == "class", "GUARD FALHOU EM PRODUCAO"
units = sorted({b.get("unit_slug") for b in idx["blocks"] if b.get("unit_slug")})
print("units:", len(units))
EOF
```
Esperado: fase2 byte-idêntica PASS · audit hard=0 · **bloco-13 kind=class no índice do
reprocess** (a prova final da campanha) · units 4. QUALQUER falha = rollback do Step 7 do
report da tentativa 3 (checkout tracked + restore sidecars do backup + sha256 + flags `{}` +
fase2 re-rodada byte-idêntica) e FAIL honesto registrado.

- [x] **Step 6: Commit no TCC-Tutor + tracker + Concluído**

```bash
git -C "C:/Users/Humberto/Documents/GitHub/TCC-Tutor" add -A
git -C "C:/Users/Humberto/Documents/GitHub/TCC-Tutor" commit -m "rollout flag-ON: use_anchor_engine + use_llm_voter (indice unificado, bloco-13 class, gates a-d + fase2 byte-identica PASS)"
```
No projeto: entrada Concluído no `pendencias.md` (campanha 1/3 fechada, 5/5 flag-ON, números) +
mover spec/plano para `Feitos/` (`git mv`) SE gate 100% verde (regra AGENTS.md) + commit
`docs(campanha-1/3): fechamento — 5/5 flag-ON, indice unificado`.

---

## Self-review (feito na escrita)

1. Cobertura do spec: C1→Task1, C5→Task2, C2→Task3, C3→Task4, C4→Task5, aceite §6.1-6.5→Tasks 1-6, §6.6→Task7, §6.7→Tasks 4/6/7. Sem lacuna.
2. Placeholders: nenhum "TBD"; os pontos "LER antes" são verificação obrigatória do protocolo (nunca assumir), cada um com fallback definido (parar/ajustar/registrar).
3. Consistência de nomes: `build_rich_content_taxonomy` / `engine._build_rich_content_taxonomy` usados idênticos nas Tasks 3, 5(não usa) e 7(não usa); `_effective_display` só Task 2; `UnitsShrinkError` Tasks 5/7 conforme `pedagogical_regeneration.py:275`.

---

### Task 8: Guard exam-vocab na assinatura de janela do P4 (C6)

**Files:**
- Modify: `src/builder/routing/motor/window_provider.py` (~:110-122, `_block_topic_stems`)
- Test: `tests/test_motor_window_provider.py` (adicionar à `TestProviderTopic`)

**Interfaces:**
- Consumes: `block_topic_tokens`/`block_session_tokens` (`disambiguator.py:56-71`), `_STRONG_EXAM_RE` (`src/builder/timeline/classifier.py:131` — importar; passa o import-guard do motor), fixture `_ctx` existente (`tests/test_motor_window_provider.py:179-192`).
- Produces: na união da assinatura (`window_provider.py:119`), tokens exam-vocab fracos (`"prova"`, `"teste"` — mesmo par do ruling C1) vindos de `block_topic_tokens` só entram se o BLOCO tiver sinal forte de exame (`_STRONG_EXAM_RE` sobre o texto de sessões — labels + lessons_index, o mesmo texto de `block_session_tokens`); a metade `block_session_tokens` NUNCA é filtrada (é dela que vêm os 8 membros legítimos do caso real).

- [x] **Step 1: Teste RED** — na `TestProviderTopic`: card `"Semana 10 - Revisão para P1 e Prova P1"`; bloco kind=class, `primary_topic_label="Prova da Indecidibilidade do Problema da Parada"`, `topic_text="problema da correspondencia de post"`, session label `"problema da correspondencia de post aula"` (sem sinal forte) → bloco NÃO pode entrar na janela. Segundo teste (controle positivo): bloco com session label `"prova p1 prova"` E `primary_topic_label` com "Prova" acadêmica → CONTINUA na janela (sinal forte presente). Rodar: o 1º FALHA hoje (bloco entra), o 2º passa.
- [x] **Step 2: Implementar o guard** em `_block_topic_stems` (linha ~119): separar `topic_toks = block_topic_tokens(b)`; se `not _STRONG_EXAM_RE.search(texto_de_sessoes_do_bloco)`, remover de `topic_toks` os tokens `{"prova", "teste"}`; `sig = topic_toks | block_session_tokens(b, ctx)`. Comentário citando C1 + diagnóstico 2026-08-06. Invalidar/respeitar o cache `ctx._stems_cache` como está.
- [x] **Step 3: GREEN** nos 2 testes novos + `tests/test_motor_window_provider.py` inteiro + `tests/test_motor_golden_mf.py` + `tests/test_motor_higiene_batch.py` verdes.
- [x] **Step 4: Régua** — `python scripts/fase2_prova_TCC.py` byte-idêntica ao baseline (estado em disco atual é no-op para o guard — MEDIDO no diagnóstico); suite 1880/4/1 (1879+1 novo… são 2 novos: 1881/4/1); 7 probes vereditos PASS inalterados.
- [x] **Step 5: Commit** — `fix(motor): P4 nao casa exam-vocab vindo de rotulo de taxonomia sem sinal forte no bloco (C6, 3a camada da colisao prova/demonstracao)`

### Task 9: TCC re-flip tentativa 5 (aceite final)

Repetir o rito COMPLETO da Task 7 (mesmo brief `task-7-brief.md`, mesmos gates, mesmo protocolo de backup/rollback), com o critério decisivo AMPLIADO: fase2-TCC byte-idêntica ao pré-flip **incluindo a linha da janela do card "Semana 10" SEM bloco-13**; bloco-13 kind=class; units=4; votos 16→16; audit hard=0. Verde = commit no TCC-Tutor + fechamento (entrada Concluído no tracker, spec/plano → `Feitos/`, ledger). Vermelho = rollback + BLOCKED (sem 6ª tentativa automática).
