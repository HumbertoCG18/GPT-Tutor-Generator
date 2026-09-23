# FASE 1 — Gate D4 com Medição de Recall — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Medir o RECALL do gate D4 (fração dos erros reais do motor que ganham FLAG) na régua externa MF e no gold embutido, calibrar o gate com dois levers novos (desconto nome-do-curso + token discriminante) e documentar quanto do resíduo confiante-errado sobra para o TIER 3 same-theme — fechando o número da FASE 1 do spec (`docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` §6/§7).

**Architecture:** Tudo dentro do pacote isolado `src/builder/routing/motor/` (+ 1 módulo puro novo `metrics.py`) e de 1 script READ-ONLY novo em `scripts/`. Nenhuma integração ao pipeline (isso é FASE 4); nenhum artefato de repo-tutor é mutado. O gate D4 hoje é proxy (`rel_margin >= MARGIN_TAU` com `s2>0` e cap de band); a FASE 1 o evolui para o D4 do spec ("best supera runner-up por ≥1 token **discriminante**") e remove a poluição do nome-do-curso das assinaturas de bloco.

**Tech Stack:** Python 3 (stdlib only nos módulos novos), pytest, CSV gold externo `docs/reports/ground_truth_MF.csv`, fixture embutida `tests/fixtures/eval/metodos_formais_golden.json`.

## Global Constraints

- Respostas/documentos em PT-BR; código e commits em estilo normal do repo.
- Todo script novo em `scripts/` começa com o shim UTF-8 (console Windows cp1252):
  `if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")` (+ stderr) — igual a `scripts/fase0_prova_motor_MF.py:22-24`.
- Scripts/probes de CC são READ-ONLY nos repos-tutor (`~/Documents/GitHub/Metodos-Formais-Tutor` etc.). Mutação do vivo = ação do USER na GUI.
- Lógica nova SÓ em `src/builder/routing/motor/` (e `scripts/`); NUNCA `engine.py`.
- PROIBIDO importar `block_token_weights`, `score_entry_against_timeline_block`, `select_probable_period_for_entry` no pacote do motor (guard AST `tests/test_motor_import_guard.py` — inclui star-import e acesso module-qualified). Whitelist: `concept_resolver` puro, `card_block`, `thresholds`, `entry_signals`, `text/*`.
- ANCHOR-ONLY: o motor NÃO escreve nada em manifest/artefato nesta fase; retorna `AnchorDecision` ou `None` (funil).
- MARCO 0/1 NÃO se re-rodam (provas cacheadas).
- Piso HARD externo (escopo-disamb MF, par-colapsado): **≥ 59.7%**. FASE 0 entregou **62.1%** — queda abaixo de 62.1% precisa de justificativa medida no report; abaixo de 59.7% = FAIL.
- Gold embutido (CI, `tests/test_motor_golden_mf.py`): contenção 100% e confiante-errado 0 permanecem invioláveis.
- Referência de recall a bater (spec §7): proxy MARCO 1 pegou **15/26 ≈ 57.7%** dos erros. O recall do motor calibrado deve superar isso.
- Docstrings multi-parágrafo do plano governam sobre `.mex/AGENTS.md` (decisão do user na FASE 0, vale para o ciclo).
- Suite inteira verde ao final de cada task (`python -m pytest -q`); baseline atual: 1689 passed / 4 skipped.

**Definição operacional (usada em todo o plano):**
- *Erro ancorado* = motor retorna decisão (não-funil) e `pred != true`.
- *Confiante-errado* = erro ancorado com `band == "alta"`.
- *Recall do gate* = `erros_flagados / erros_ancorados` (fração dos erros reais que ganham `flag=True`); com 0 erros ancorados, recall = 1.0 por convenção.
- Métricas de gate contadas POR CASO (como o probe FASE 0 conta confiante-errado); acurácia segue par-colapsada (`pair_key`).
- Decisões `method="janela-1"` são reportadas em linha separada: erro ali é erro de JANELA (curadoria de card map), não do gate — o gate não roda em janela unitária.

---

### Task 1: Métricas de gate puras (`metrics.py`)

**Files:**
- Create: `src/builder/routing/motor/metrics.py`
- Test: `tests/test_motor_metrics.py`

**Interfaces:**
- Consumes: nada do motor (módulo puro, stdlib only).
- Produces: `gate_report(outcomes: list[dict]) -> dict` — consumido pela Task 2 (harness) e Task 5 (calibração). Cada outcome: `{"correct": bool, "band": str, "flag": bool, "method": str}` (só decisões ANCORADAS entram; funil fica fora). Retorno: dict com chaves `total`, `erros`, `erros_flagados`, `confiante_errado`, `recall_gate` (float), `flagged_total`, `flagged_certos`, `janela1_erros`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motor_metrics.py
from src.builder.routing.motor.metrics import gate_report


def _o(correct, band, flag, method="disamb"):
    return {"correct": correct, "band": band, "flag": flag, "method": method}


def test_recall_basico_erros_flagados_sobre_erros():
    outcomes = [
        _o(True, "alta", False),          # acerto confiante — não conta como erro
        _o(False, "media", True),         # erro flagado (gate pegou)
        _o(False, "alta", False),         # confiante-errado (gate NÃO pegou)
        _o(False, "baixa", True),         # erro flagado
    ]
    r = gate_report(outcomes)
    assert r["total"] == 4
    assert r["erros"] == 3
    assert r["erros_flagados"] == 2
    assert r["confiante_errado"] == 1
    assert abs(r["recall_gate"] - 2 / 3) < 1e-9


def test_recall_sem_erros_e_1():
    r = gate_report([_o(True, "alta", False), _o(True, "media", True)])
    assert r["erros"] == 0
    assert r["recall_gate"] == 1.0


def test_flagged_certos_mede_falso_alarme():
    # flag em decisão CERTA = custo de fila humana/TIER 3, não recall
    r = gate_report([_o(True, "media", True), _o(False, "media", True)])
    assert r["flagged_total"] == 2
    assert r["flagged_certos"] == 1


def test_janela1_erro_reportado_separado():
    # erro em janela-1 é erro de JANELA (curadoria), não do gate; entra em
    # erros/confiante_errado (é confiante-errado REAL) mas ganha contador próprio
    r = gate_report([_o(False, "alta", False, method="janela-1")])
    assert r["erros"] == 1
    assert r["confiante_errado"] == 1
    assert r["janela1_erros"] == 1


def test_lista_vazia_nao_divide_por_zero():
    r = gate_report([])
    assert r["total"] == 0
    assert r["recall_gate"] == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.routing.motor.metrics'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/builder/routing/motor/metrics.py
"""Métricas do gate D4 (FASE 1): recall do gate sobre decisões ANCORADAS.

Puro (stdlib): consumido pelo harness externo (scripts/fase1_recall_gate_MF.py)
e reutilizável pelo Dashboard na FASE 4. Funil (None) NÃO entra aqui — recall
do gate mede só o que o motor ancorou.
"""
from __future__ import annotations

from typing import Dict, List


def gate_report(outcomes: List[dict]) -> Dict[str, object]:
    """Agrega outcomes ancorados em métricas do gate D4.

    outcome: {"correct": bool, "band": str, "flag": bool, "method": str}.
    recall_gate = erros_flagados / erros (1.0 quando não há erros — gate sem
    erro para pegar não é gate ruim).
    """
    total = len(outcomes)
    erros = [o for o in outcomes if not o.get("correct")]
    erros_flagados = [o for o in erros if o.get("flag")]
    confiante_errado = [o for o in erros if str(o.get("band")) == "alta"]
    flagged = [o for o in outcomes if o.get("flag")]
    janela1_erros = [o for o in erros if str(o.get("method")) == "janela-1"]
    return {
        "total": total,
        "erros": len(erros),
        "erros_flagados": len(erros_flagados),
        "confiante_errado": len(confiante_errado),
        "recall_gate": (len(erros_flagados) / len(erros)) if erros else 1.0,
        "flagged_total": len(flagged),
        "flagged_certos": len([o for o in flagged if o.get("correct")]),
        "janela1_erros": len(janela1_erros),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_motor_metrics.py -v`
Expected: 5 passed

- [ ] **Step 5: Verificar guard de imports e suite do motor**

Run: `python -m pytest tests/test_motor_import_guard.py tests/test_motor_metrics.py -q`
Expected: tudo verde (metrics.py é stdlib-only, guard não acusa).

- [ ] **Step 6: Commit**

```bash
git add src/builder/routing/motor/metrics.py tests/test_motor_metrics.py
git commit -m "feat(motor): metricas puras do gate D4 (recall/flag) para FASE 1"
```

---

### Task 2: Harness externo de recall (`scripts/fase1_recall_gate_MF.py`)

**Files:**
- Create: `scripts/fase1_recall_gate_MF.py`
- Reference (não modificar): `scripts/fase0_prova_motor_MF.py` (loader/colapso reutilizados por cópia — scripts são standalone por convenção do repo)

**Interfaces:**
- Consumes: `gate_report` (Task 1); `MotorContext`, `AnchorEngine`, `is_out_of_disamb_scope` do motor (já commitados na FASE 0).
- Produces: script CLI READ-ONLY com veredito por exit code. Constante `PISO_RECALL_REFERENCIA = 0.577` (proxy MARCO 1 15/26 — referência ruim a bater). A Task 5 substituirá por baseline própria medida.

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""FASE 1 — recall do gate D4 do MOTOR real vs ground_truth_MF.csv (READ-ONLY).

Mede a métrica-número da FASE 1 (spec §6/§7): fração dos erros reais que o
gate FLAGA (recall), além de confiante-errado e falso-alarme do flag. Régua:
mesmo escopo-disamb par-colapsado do probe FASE 0; métricas de gate POR CASO.
Referência ruim a bater: proxy MARCO 1 = 15/26 (57.7%).
NÃO muta manifest/artefato. Uso:
  python scripts/fase1_recall_gate_MF.py [--repo PATH] [--gold CSV]
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.contracts import MotorContext          # noqa: E402
from src.builder.routing.motor.metrics import gate_report              # noqa: E402
from src.builder.routing.motor.anchor_engine import (                  # noqa: E402
    AnchorEngine, is_out_of_disamb_scope,
)

DEFAULT_REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
DEFAULT_GOLD = Path(__file__).resolve().parents[1] / "docs" / "reports" / "ground_truth_MF.csv"
PISO_ACURACIA = 59.7          # HARD (MARCO 0 Config A'); FASE 0 entregou 62.1
PISO_RECALL_REFERENCIA = 0.577  # proxy MARCO 1 (15/26) — referência ruim a bater
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


def build_context(repo: Path, course_name: str) -> MotorContext:
    tl = _load(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(repo, "course/.card_block_map.json")
    lessons = (_load(repo, "course/.lessons_index.json") or {}).get("by_date", {})
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index=lessons,
        course_name=course_name,
    )


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
    course_name = str((man.get("course") or {}).get("course_name") or "")
    byid = {}
    for e in man.get("entries") or []:
        byid.setdefault(str(e.get("id")), e)

    ctx = build_context(repo, course_name)
    eng = AnchorEngine()

    rows = [r for r in csv.DictReader(open(gold_path, encoding="utf-8"))
            if str(r.get("scorable")) == "yes"]
    scope = [r for r in rows
             if byid.get(r["id"]) and not is_out_of_disamb_scope(byid[r["id"]])]

    results: dict = {}
    outcomes: list = []
    detalhe_erros: list = []
    for r in scope:
        rid, true = r["id"], r["true_block_id"]
        e = byid[rid]
        d = eng.resolve(e, ctx, markdown=_md_text(repo, e))
        if d is None:
            pred = r["computed_block_id"] or ""     # funil = piso (D9)
            results[rid] = (pred == true)
            continue
        pred = display_of(ctx, d.block_ref)
        correct = (pred == true)
        results[rid] = correct
        outcomes.append({"correct": correct, "band": d.band,
                         "flag": d.flag, "method": d.method})
        if not correct:
            detalhe_erros.append((rid, pred, true, d.band, d.flag,
                                  d.method, d.provider,
                                  str(r.get("discriminante") or "")))

    ok, tot = collapse(results, scope)
    pct = ok / tot * 100 if tot else 0.0
    rep = gate_report(outcomes)

    print("=" * 70)
    print(f"FASE 1 — recall do gate D4  repo={repo.name}  course={course_name!r}")
    print(f"  acurácia escopo-disamb: {ok}/{tot} = {pct:.1f}% (par-colapsada; piso HARD {PISO_ACURACIA}%)")
    print(f"  decisões ancoradas (por caso): {rep['total']}")
    print(f"  erros ancorados: {rep['erros']}  | flagados: {rep['erros_flagados']}"
          f"  | confiante-errado: {rep['confiante_errado']}"
          f"  | erros janela-1: {rep['janela1_erros']}")
    print(f"  RECALL DO GATE: {rep['recall_gate']:.3f} "
          f"(referência ruim a bater: {PISO_RECALL_REFERENCIA} = proxy 15/26 MARCO 1)")
    print(f"  fila do flag: {rep['flagged_total']} flagados, "
          f"{rep['flagged_certos']} certos (falso-alarme)")
    print("  erros ancorados (id, pred, true, band, flag, method, provider, discriminante):")
    for x in detalhe_erros:
        print(f"    {x}")
    print("=" * 70)

    ok_acc = pct + 1e-9 >= PISO_ACURACIA
    ok_recall = rep["recall_gate"] > PISO_RECALL_REFERENCIA
    verdict = ok_acc and ok_recall
    print(f"VEREDITO FASE 1 (parcial, pré-calibração): {'PASS' if verdict else 'FAIL'} "
          f"(acc={ok_acc} recall={ok_recall})")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

**NOTA de dependência:** o script passa `course_name=` a `MotorContext.from_artifacts`. Esse kwarg SÓ EXISTE após a Task 3. Nesta task, escreva o script SEM o kwarg (linha `course_name=course_name,` omitida e `build_context(repo)` sem o parâmetro) — a Task 3 o adiciona. O código acima é a forma FINAL (pós-Task 3), mostrada completa para o implementer da Task 3 saber o alvo.

- [ ] **Step 2: Rodar o harness e capturar a BASELINE atual (pré-levers)**

Run: `python scripts/fase1_recall_gate_MF.py`
Expected: imprime o report. Números esperados com o motor da FASE 0 (validar contra o probe fase0): confiante-errado = 7; acurácia = 62.1%. O recall exato é a PRIMEIRA MEDIÇÃO da FASE 1 — registre o número impresso no report da task (ele é deliverable, não chute). Exit code pode ser 0 ou 1 dependendo do recall medido — ambos aceitáveis nesta task (é instrumento; o gate vira HARD na Task 5).

- [ ] **Step 3: Sanidade cruzada com o probe FASE 0**

Run: `python scripts/fase0_prova_motor_MF.py`
Expected: `VEREDITO FASE 0: PASS` inalterado (62.1%, conten 2, conf 7) — o harness novo não mudou código de produção.

- [ ] **Step 4: Commit**

```bash
git add scripts/fase1_recall_gate_MF.py
git commit -m "feat(motor): harness READ-ONLY de recall do gate D4 vs ground_truth_MF"
```

---

### Task 3: Desconto do nome-do-curso nas assinaturas de bloco

**Files:**
- Modify: `src/builder/routing/motor/contracts.py` (campo `course_name` no `MotorContext`)
- Modify: `src/builder/routing/motor/disambiguator.py` (`_block_signature` desconta tokens do nome do curso)
- Modify: `tests/test_motor_disambiguator.py` (+2 testes)
- Modify: `tests/test_motor_golden_mf.py` (passa `data["subject"]` como `course_name`)
- Modify: `scripts/fase0_prova_motor_MF.py` e `scripts/fase1_recall_gate_MF.py` (passam `man["course"]["course_name"]`)

**Interfaces:**
- Consumes: `MotorContext.from_artifacts(blocks=, card_block_map=, lessons_index=)` (FASE 0).
- Produces: `MotorContext.from_artifacts(..., course_name: str = "")` e campo `MotorContext.course_name: str` — usados pela Task 2 (forma final do harness) e Task 5. Default `""` = comportamento FASE 0 inalterado (backward-compatível com todo call-site existente).

**Contexto do problema (tracker, dívida FASE 1):** `topic_text` do bloco-02 do MF = `"introducao metodos formais"`. Os tokens `metodos`/`formais` são o NOME DA DISCIPLINA — boilerplate que aparece em materiais de qualquer bloco e faz o bloco-02 vencer sem evidência real (2 dos 7 confiante-errado externos). Fix GENÉRICO (sem hardcode de cadeira): descontar das ASSINATURAS DE BLOCO os tokens do nome do curso corrente (`manifest["course"]["course_name"]`; no gold embutido, `data["subject"]`). Só o lado do bloco é filtrado — o material pode citar o nome à vontade, sem assinatura não há match.

- [ ] **Step 1: Write the failing tests**

Adicionar a `tests/test_motor_disambiguator.py` (usar os mesmos helpers/estilo dos 6 testes existentes; `_ctx`/`_block` do arquivo, se existirem, senão construir inline como abaixo):

```python
def test_nome_do_curso_nao_pontua_assinatura():
    # bloco-A só tem tokens do nome do curso; bloco-B tem token real do material.
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01",
         "topic_text": "introducao metodos formais", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "logica predicados", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(
        blocks=blocks, card_block_map={}, lessons_index={},
        course_name="Metodos-Formais",
    )
    entry = {"title": "exercicios metodos formais logica"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    # sem o desconto, bloco-A ganharia por "metodos"+"formais" (2 tokens vs 1)
    assert d.block_ref == "bloco-B"


def test_course_name_default_vazio_preserva_fase0():
    # sem course_name, comportamento FASE 0: nome do curso pontua normalmente
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01",
         "topic_text": "introducao metodos formais", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "logica predicados", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    entry = {"title": "exercicios metodos formais"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    assert d.block_ref == "bloco-A"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_motor_disambiguator.py -v -k "nome_do_curso or default_vazio"`
Expected: `test_nome_do_curso_nao_pontua_assinatura` FAIL (`TypeError: from_artifacts() got an unexpected keyword argument 'course_name'`); o segundo pode passar (é caracterização do default).

- [ ] **Step 3: Implement — contracts.py**

Em `MotorContext` (`contracts.py:31`), adicionar o campo e o kwarg (docstring de linha única na mudança; shape do dataclass permanece):

```python
@dataclass
class MotorContext:
    """Contexto READ-ONLY de um curso: blocos + card_block_map + lessons_index.

    blocks ficam ORDENADOS por period_start; _by_ref indexa id E block_uuid.
    course_name = nome da disciplina (manifest course.course_name / gold
    subject); tokens dele são BOILERPLATE local e saem das assinaturas de
    bloco no disambiguator ("" = sem desconto, comportamento FASE 0).
    """
    blocks: List[dict]
    card_block_map: Dict[str, dict]
    lessons_index: Dict[str, str]  # {date_iso: topico} (by_date do .lessons_index.json)
    course_name: str = ""
    _by_ref: Dict[str, dict] = field(default_factory=dict, repr=False)

    @classmethod
    def from_artifacts(
        cls,
        *,
        blocks: List[dict],
        card_block_map: Dict[str, dict],
        lessons_index: Dict[str, str],
        course_name: str = "",
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
            course_name=str(course_name or ""),
            _by_ref=by_ref,
        )
```

- [ ] **Step 4: Implement — disambiguator.py**

Em `_block_signature` (`disambiguator.py:80`):

```python
def _block_signature(block: dict, ctx: MotorContext) -> dict:
    """{token: peso} do bloco: session-label (1ª classe) sobrepõe topic (grosso).

    Tokens do NOME DO CURSO (ctx.course_name) saem da assinatura: são
    boilerplate local (2 confiante-errado externos na FASE 0 vinham do
    topic "introducao metodos formais" do bloco-02 — dívida do tracker)."""
    drop = _toks(ctx.course_name)
    sig: dict = {}
    for t in block_topic_tokens(block) - drop:
        sig[t] = W_TOPIC
    for t in block_session_tokens(block, ctx) - drop:
        sig[t] = W_SESSION_LABEL  # 1ª classe: substitui o peso grosso se colidir
    return sig
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_motor_disambiguator.py tests/test_motor_contracts.py -v`
Expected: todos verdes (os 2 novos + 6 antigos + contracts).

- [ ] **Step 6: Wire no gold embutido**

Em `tests/test_motor_golden_mf.py`, `_load_ctx_and_cases`:

```python
    ctx = MotorContext.from_artifacts(
        blocks=data["timeline"]["blocks"],  # gold embute blocos em timeline.blocks (mesmo shape de test_resolver_fusion.py)
        card_block_map=data["card_block_map"],
        lessons_index={},  # gold não embute lessons_index; session-label vem de sessions[].label
        course_name=str(data.get("subject") or ""),
    )
```

Run: `python -m pytest tests/test_motor_golden_mf.py -v`
Expected: 4 passed — contenção 100% e confiante-errado 0 MANTIDOS com o desconto ligado. Se `test_confiante_errado_zero` ou `test_contencao_100_pct_quando_ancora` falharem, PARE e reporte ao controller com os casos exatos (o desconto mudou escolhas no embutido — decisão de calibração, não força bruta).

- [ ] **Step 7: Wire nos dois scripts**

Em `scripts/fase0_prova_motor_MF.py`: `build_context` ganha parâmetro e o `main` extrai o nome —

```python
def build_context(repo: Path, course_name: str = "") -> MotorContext:
    tl = _load(repo, "course/.timeline_index.json")
    blocks = tl if isinstance(tl, list) else (tl.get("blocks") or [])
    cbm = _load(repo, "course/.card_block_map.json")
    lessons = (_load(repo, "course/.lessons_index.json") or {}).get("by_date", {})
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=cbm, lessons_index=lessons,
        course_name=course_name,
    )
```

e no `main`, logo após carregar `man`:

```python
    course_name = str((man.get("course") or {}).get("course_name") or "")
```

trocando `ctx = build_context(repo)` por `ctx = build_context(repo, course_name)`.

Em `scripts/fase1_recall_gate_MF.py`: aplicar a forma FINAL mostrada na Task 2 (kwarg `course_name=` no `from_artifacts` + extração do manifest).

- [ ] **Step 8: Medir o efeito na régua externa**

Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected (hipótese a validar): confiante-errado cai 7 → ~5 (os 2 casos de poluição saem); acurácia NÃO cai abaixo de 62.1% (o desconto pode até subir o número — os 2 casos passam a acertar ou flagar). Registre os números reais impressos no report da task. FAIL do fase0 (qualquer métrica acima do baseline consciente) = PARE e reporte.

**NÃO ajuste `BASELINE_CONFIANTE_ERRADO` ainda** — os baselines do probe fase0 são renegociados UMA vez na Task 5, com todos os levers medidos.

- [ ] **Step 9: Suite completa**

Run: `python -m pytest -q`
Expected: tudo verde (1691+ passed / 4 skipped).

- [ ] **Step 10: Commit**

```bash
git add src/builder/routing/motor/contracts.py src/builder/routing/motor/disambiguator.py tests/test_motor_disambiguator.py tests/test_motor_golden_mf.py scripts/fase0_prova_motor_MF.py scripts/fase1_recall_gate_MF.py
git commit -m "feat(motor): desconto de tokens do nome-do-curso nas assinaturas de bloco"
```

---

### Task 4: Gate D4 por token discriminante

**Files:**
- Modify: `src/builder/routing/motor/disambiguator.py` (função `disambiguate`)
- Modify: `tests/test_motor_disambiguator.py` (+2 testes)

**Interfaces:**
- Consumes: `_block_signature`, `_score`, `MARGIN_TAU`, `entry_tokens` (existentes).
- Produces: mesma assinatura pública `disambiguate(entry, window, ctx, markdown="") -> AnchorDecision` — sem mudança de contrato; só o predicado `confident` fica mais exigente.

**Contexto (spec §3 Contrato 2, D4):** "confiante = best supera runner-up por **≥1 token discriminante**". Hoje o gate é só proporcional (`rel_margin`): um bloco pode vencer o runner-up com os MESMOS tokens casados, apenas por peso maior (session vs topic) ou IDF — e sair band "alta" sem nenhuma evidência exclusiva. A FASE 1 implementa o D4 literal: `confident` exige que o material tenha ≥1 token casando com a assinatura do best que NÃO casa com a do runner-up.

- [ ] **Step 1: Write the failing tests**

Adicionar a `tests/test_motor_disambiguator.py`:

```python
def test_vitoria_so_por_peso_sem_token_exclusivo_flagra():
    # os DOIS blocos casam exatamente os mesmos tokens do material ("inducao",
    # "estrutural"); o best vence só por peso (session-label 1.0 vs topic 0.6)
    # + len-norm (assinatura do runner é maior). Margem calculada: s1=0.980,
    # s2=0.416, rel_margin=0.576 >= MARGIN_TAU(0.45) e s2>0 => o gate ATUAL
    # dá "alta" sem nenhum token exclusivo — exatamente o furo do D4 proxy.
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01", "topic_text": "",
         "sessions": [{"date": "2026-03-02", "label": "inducao estrutural"}]},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "inducao estrutural conjuntos recursao", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    entry = {"title": "lista inducao estrutural"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    assert d.block_ref == "bloco-A"      # seleção não muda (peso decide)
    assert d.flag is True                 # mas SEM token exclusivo => nunca confiante
    assert d.band != "alta"


def test_token_exclusivo_permite_confianca():
    # best casa "hoare" (exclusivo) + "verificacao"; runner casa só "verificacao"
    blocks = [
        {"id": "bloco-A", "period_start": "2026-03-01",
         "topic_text": "verificacao logica hoare", "sessions": []},
        {"id": "bloco-B", "period_start": "2026-03-08",
         "topic_text": "verificacao modelos", "sessions": []},
    ]
    ctx = MotorContext.from_artifacts(blocks=blocks, card_block_map={}, lessons_index={})
    entry = {"title": "deducao hoare verificacao"}
    d = disambiguate(entry, ["bloco-A", "bloco-B"], ctx)
    assert d.block_ref == "bloco-A"
    assert d.flag is False
    assert d.band == "alta"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_motor_disambiguator.py -v -k "peso_sem_token or token_exclusivo"`
Expected: `test_vitoria_so_por_peso_sem_token_exclusivo_flagra` FAIL na asserção `d.flag is True` (hoje rel_margin alto + s2>0 dá confiança). ATENÇÃO: se falhar ANTES disso (ex.: rel_margin < MARGIN_TAU e o teste passa vacuamente), ajuste os tokens do fixture até o cenário forçar o gate atual a dar "alta" — o teste TEM que ficar vermelho pela razão certa antes do fix.

- [ ] **Step 3: Implement**

Em `disambiguate` (`disambiguator.py:98`), após computar `scores` e `order`:

```python
    order = sorted(range(len(blocks)), key=lambda i: scores[i], reverse=True)
    i1 = order[0]
    s1 = scores[i1]
    s2 = scores[order[1]] if len(order) > 1 else 0.0
    rel_margin = (s1 - s2) / max(s1, _EPS)
    # D4 literal (spec §3): confiança exige COMPETIÇÃO real (s2>0) E >=1 token
    # DISCRIMINANTE — token do material que casa a assinatura do best e NÃO a
    # do runner-up. Vitória só-por-peso/IDF (mesmos tokens) nunca é confiante.
    hits_best = mat & set(sigs[i1])
    hits_runner = mat & set(sigs[order[1]]) if len(order) > 1 else set()
    discriminante = hits_best - hits_runner
    confident = s1 > 0 and s2 > 0 and rel_margin >= MARGIN_TAU and bool(discriminante)
```

(o restante da função — `ref`, band com cap "media", retorno — permanece byte-idêntico ao da FASE 0.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_motor_disambiguator.py -v`
Expected: 10 passed (6 FASE 0 + 2 Task 3 + 2 novos). Se algum teste FASE 0 quebrar, o fixture dele dependia de confiança sem token exclusivo — reporte ao controller antes de alterar QUALQUER teste existente.

- [ ] **Step 5: Gold embutido + régua externa**

Run: `python -m pytest tests/test_motor_golden_mf.py -v && python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: embutido 4 passed (confiante-errado continua 0 — gate mais exigente não cria confiante-errado novo, só pode reduzir "alta"). Externo: registre acurácia / confiante-errado / recall impressos. Hipóteses a validar: recall SOBE (erros antes confiantes agora flagados) e acurácia par-colapsada NÃO muda (a seleção de bloco é intocada — só band/flag mudam). Se a acurácia mudar, algo está errado no diff: a seleção não pode ter sido tocada.

- [ ] **Step 6: Suite completa**

Run: `python -m pytest -q`
Expected: tudo verde.

- [ ] **Step 7: Commit**

```bash
git add src/builder/routing/motor/disambiguator.py tests/test_motor_disambiguator.py
git commit -m "feat(motor): gate D4 exige token discriminante best vs runner-up"
```

---

### Task 5: Calibração de grade com recall + baselines renegociados + veredito FASE 1

**Files:**
- Modify: `src/builder/routing/motor/disambiguator.py` (constantes `MARGIN_TAU`/`W_SESSION_LABEL`/`W_TOPIC`, SÓ se a grade achar ponto melhor)
- Modify: `scripts/fase0_prova_motor_MF.py` (`BASELINE_CONFIANTE_ERRADO`, `BASELINE_CONTENCAO_FORA` — renegociação única com números medidos)
- Modify: `scripts/fase1_recall_gate_MF.py` (adiciona `BASELINE_RECALL` HARD = valor alcançado, anti-regressão; veredito final da fase)

**Interfaces:**
- Consumes: harness Task 2, levers Tasks 3-4.
- Produces: constantes finais calibradas + vereditos HARD nos dois scripts. Números finais da FASE 1 para o report do controller.

**Procedimento de calibração (determinístico, espelha a Task 7 da FASE 0):**

- [ ] **Step 1: Varredura de grade (ad-hoc, NÃO commitada)**

Rodar via `python -c` (ou script temporário no scratchpad) a grade
`MARGIN_TAU ∈ {0.25, 0.35, 0.45, 0.55}` × `W_TOPIC ∈ {0.4, 0.6, 0.8}` × `W_SESSION_LABEL ∈ {0.8, 1.0, 1.5}`,
monkey-patchando as constantes do módulo e reexecutando a lógica do harness (import das funções do script ou duplicação inline). Para CADA ponto, registrar: acurácia par-colapsada, confiante-errado, recall do gate, flagged_total, e o resultado dos 4 testes do gold embutido (`python -m pytest tests/test_motor_golden_mf.py -q` no ponto candidato final, não em todos).

**Critério de escolha (ordem lexicográfica):**
1. Gold embutido 100% verde (eliminatório).
2. Acurácia par-colapsada ≥ 62.1% (não regredir a FASE 0; piso HARD 59.7% é o mínimo absoluto — entre 59.7 e 62.1 SÓ com justificativa medida e aprovação do controller).
3. Menor `confiante_errado` (meta do spec: 0 — "nenhum erro confiante escapa nos golds").
4. Maior `recall_gate`.
5. Menor `flagged_total` (desempate: fila humana menor).

- [ ] **Step 2: Aplicar o ponto vencedor (se ≠ atual)**

Se a grade achar ponto estritamente melhor, editar as 3 constantes em `disambiguator.py` com comentário de 1 linha (`# Calibração FASE 1 (grade com recall, 2026-07-XX): ...`). Se o ponto atual (0.45/1.0/0.6) já for o vencedor, NÃO editar — registrar no report que a calibração confirmou a FASE 0.

Run: `python -m pytest -q`
Expected: suite inteira verde.

- [ ] **Step 3: Renegociar baselines do probe FASE 0 (única vez, com números finais)**

Em `scripts/fase0_prova_motor_MF.py`, atualizar com os números MEDIDOS finais:

```python
# Baselines renegociados na FASE 1 (calibração com recall, 2026-07-XX):
# confiante-errado <N_FINAL> (era 7 na FASE 0: -2 poluição nome-do-curso via
# desconto course_name, -M via gate discriminante); contenção-fora segue 2
# (lacuna do card_block_map real — pendência USER bloco-09, não é do gate).
BASELINE_CONFIANTE_ERRADO = <N_FINAL>
BASELINE_CONTENCAO_FORA = 2
```

(`<N_FINAL>` = o número real medido — o implementer substitui pelo valor; deixar `7` se nada melhorou é FAIL da fase, volte ao controller.)

- [ ] **Step 4: Veredito HARD da FASE 1 no harness**

Em `scripts/fase1_recall_gate_MF.py`, adicionar baseline anti-regressão com o valor alcançado e promover o veredito:

```python
BASELINE_RECALL = <RECALL_FINAL>   # medido na calibração FASE 1 — regressão abaixo = FAIL
```

e no veredito:

```python
    ok_recall = rep["recall_gate"] + 1e-9 >= BASELINE_RECALL and rep["recall_gate"] > PISO_RECALL_REFERENCIA
    verdict = ok_acc and ok_recall
    print(f"VEREDITO FASE 1: {'PASS' if verdict else 'FAIL'} (acc={ok_acc} recall={ok_recall})")
```

Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: `VEREDITO FASE 0: PASS` e `VEREDITO FASE 1: PASS`, ambos exit 0.

- [ ] **Step 5: Registrar a decisão TIER 3 (insumo do go/no-go da fase 3)**

No report da task, tabela final: composição do resíduo — (a) confiante-errado restante (se >0: ids + por quê o gate não pega — ex. gold `discriminante=yes` same-theme), (b) flagged errados (candidatos a conversão TIER 3/LLM), (c) flagged certos (falso-alarme = custo de fila), (d) erros janela-1 (curadoria USER). Essa tabela é o insumo direto da decisão do user sobre a FASE 3 (sign-off condicional §9 do spec).

- [ ] **Step 6: Commit**

```bash
git add src/builder/routing/motor/disambiguator.py scripts/fase0_prova_motor_MF.py scripts/fase1_recall_gate_MF.py
git commit -m "feat(motor): calibracao FASE 1 com recall medido + baselines renegociados"
```

---

### Task 6: Protocols de `contracts.py` alinhados às assinaturas reais (dívida FASE 0)

**Files:**
- Modify: `src/builder/routing/motor/contracts.py` (Protocols `Disambiguator` e `AnchorEngine`)
- Modify: `tests/test_motor_contracts.py` (asserções de conformidade)

**Interfaces:**
- Consumes: assinaturas reais — `disambiguate(entry, window, ctx, markdown="")` e `AnchorEngine.resolve(entry, ctx, markdown="")`.
- Produces: `Disambiguator.__call__(..., markdown: str = "")`; Protocol renomeado `AnchorEngineProtocol` (mata o shadowing com a classe concreta `anchor_engine.AnchorEngine`). Nenhum comportamento muda.

- [ ] **Step 1: Verificar importadores do Protocol antigo**

Run: `grep -rn "from src.builder.routing.motor.contracts import" src/ tests/ scripts/ | grep -i "AnchorEngine"`
Expected: nenhum importador do PROTOCOL `AnchorEngine` fora de `tests/test_motor_contracts.py` (a classe concreta vem de `anchor_engine.py`). Se aparecer importador inesperado, liste no report e atualize-o na mesma task.

- [ ] **Step 2: Write the failing test**

Em `tests/test_motor_contracts.py`, adicionar:

```python
import inspect

from src.builder.routing.motor.contracts import AnchorEngineProtocol, Disambiguator
from src.builder.routing.motor.disambiguator import disambiguate
from src.builder.routing.motor.anchor_engine import AnchorEngine as ConcreteEngine


def test_protocols_batem_com_assinaturas_reais():
    # Disambiguator: (entry, window, ctx, markdown="")
    params = list(inspect.signature(disambiguate).parameters)
    assert params == ["entry", "window", "ctx", "markdown"]
    proto_params = list(inspect.signature(Disambiguator.__call__).parameters)
    assert proto_params[1:] == ["entry", "window", "ctx", "markdown"]
    # AnchorEngineProtocol.resolve: (entry, ctx, markdown="")
    proto_resolve = list(inspect.signature(AnchorEngineProtocol.resolve).parameters)
    real_resolve = list(inspect.signature(ConcreteEngine.resolve).parameters)
    assert proto_resolve == real_resolve == ["self", "entry", "ctx", "markdown"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_contracts.py -v`
Expected: FAIL — `ImportError: cannot import name 'AnchorEngineProtocol'`.

- [ ] **Step 4: Implement**

Em `contracts.py`, substituir os dois Protocols:

```python
class Disambiguator(Protocol):
    """Escolhe DENTRO da janela (só roda se |window| > 1)."""
    def __call__(self, entry: dict, window: List[str], ctx: MotorContext,
                 markdown: str = "") -> AnchorDecision: ...


class AnchorEngineProtocol(Protocol):
    """Orquestra tiers; None = sem âncora -> funil.

    Nome com sufixo Protocol: a implementação concreta anchor_engine.AnchorEngine
    tinha shadowing com este Protocol na FASE 0 (dívida do tracker)."""
    def resolve(self, entry: dict, ctx: MotorContext,
                markdown: str = "") -> Optional[AnchorDecision]: ...
```

(o Protocol `AnchorEngine` DEIXA de existir em contracts.py — sem alias de compatibilidade; o Step 1 provou que não há importador.)

- [ ] **Step 5: Run tests + suite**

Run: `python -m pytest tests/test_motor_contracts.py -v && python -m pytest -q`
Expected: tudo verde.

- [ ] **Step 6: Commit**

```bash
git add src/builder/routing/motor/contracts.py tests/test_motor_contracts.py
git commit -m "fix(motor): Protocols alinhados as assinaturas reais (markdown; fim do shadowing AnchorEngine)"
```

---

### Task 7: Unificar lookup normalizado do card map (`card_block.normalized_card_map`)

**Files:**
- Modify: `src/builder/timeline/card_block.py` (promove `_normalized_card_map` → público `normalized_card_map`)
- Modify: `src/builder/routing/motor/window_provider.py` (`_card_entry` consome o helper único)
- Modify: `tests/test_motor_window_provider.py` (teste de equivalência)

**Interfaces:**
- Consumes: `card_block._normalized_card_map(card_map) -> Dict[str, dict]` (card_block.py:159, privado hoje).
- Produces: `card_block.normalized_card_map(card_map) -> Dict[str, dict]` (público, mesma semântica: NFKD+lower+sem-acento, colisão → último vence). `window_provider._card_entry` mantém contrato `-> dict` com guard de malformado (`{}` se valor não-dict).

**Contexto (dívida FASE 0):** `window_provider._card_entry` reconstrói o índice normalizado inline — mesma lógica de `card_block._normalized_card_map`. Dois pontos de manutenção para a MESMA regra de chave = drift futuro. `card_block` está na whitelist do guard de imports do motor.

- [ ] **Step 1: Write the failing test**

Em `tests/test_motor_window_provider.py`, adicionar:

```python
from src.builder.timeline.card_block import normalized_card_map


def test_card_entry_usa_normalizacao_unica_do_card_block():
    # a MESMA chave com acento/caixa divergente resolve nos dois caminhos
    cbm = {"Verificação de Programas": {"source": "labels", "block_ids": ["bloco-10"]}}
    ctx = MotorContext.from_artifacts(blocks=[], card_block_map=cbm, lessons_index={})
    entry = {"source_section": "verificacao de programas"}
    win, provider = resolve_window(entry, ctx)
    assert win == ["bloco-10"] and provider == "labels"
    # e o índice público de card_block dá a mesma visão normalizada
    assert "verificacao de programas" in normalized_card_map(cbm)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_motor_window_provider.py -v`
Expected: FAIL — `ImportError: cannot import name 'normalized_card_map'`.

- [ ] **Step 3: Implement — card_block.py**

Renomear `_normalized_card_map` para `normalized_card_map` (docstring intacta) e atualizar os DOIS call-sites internos (`lookup_card_blocks:173` e `lookup_card_assign_due:193`). Sem alias privado.

Run: `grep -rn "_normalized_card_map" src/ tests/ scripts/`
Expected: zero ocorrências após o rename (se aparecer caller externo, atualizá-lo na mesma task).

- [ ] **Step 4: Implement — window_provider.py**

```python
from src.builder.timeline.card_block import normalized_card_map


def _card_entry(entry: dict, ctx: MotorContext) -> dict:
    """Entrada do card_block_map para a source_section da entry (match sem
    acento/caixa via card_block.normalized_card_map — helper ÚNICO; em
    colisão, o último vence)."""
    key = norm_ascii_lower(str(entry.get("source_section") or ""))
    if not key:
        return {}
    # Card malformado (não-dict) degrada para janela vazia, não crashes.
    info = normalized_card_map(ctx.card_block_map).get(key)
    return info if isinstance(info, dict) else {}
```

- [ ] **Step 5: Run tests + guard + suite**

Run: `python -m pytest tests/test_motor_window_provider.py tests/test_motor_import_guard.py -v && python -m pytest -q`
Expected: tudo verde — `card_block` está na whitelist do guard; os 6 testes FASE 0 do window_provider (incl. degradação de malformado) continuam passando.

- [ ] **Step 6: Sanidade externa final**

Run: `python scripts/fase0_prova_motor_MF.py && python scripts/fase1_recall_gate_MF.py`
Expected: ambos PASS com os MESMOS números da Task 5 (refactor byte-idêntico de comportamento).

- [ ] **Step 7: Commit**

```bash
git add src/builder/timeline/card_block.py src/builder/routing/motor/window_provider.py tests/test_motor_window_provider.py
git commit -m "refactor(motor): lookup normalizado unico via card_block.normalized_card_map"
```

---

## Fechamento da fase (controller, fora das tasks)

1. Report `docs/reports/2026-07-XX-fase1-recall-report.md`: recall final vs referência 15/26, confiante-errado final vs 7, tabela do resíduo (Step 5 da Task 5), decisão TIER 3 recomendada.
2. Tracker `docs/reports/pendencias.md`: entrada de fechamento FASE 1 + baixa das dívidas resolvidas (poluição nome-do-curso, Protocols, unificação lookup) + o que resta (hardening MotorContext adiado; 5 casos `discriminante=yes` → resultado da calibração; pendência USER bloco-09 inalterada).
3. `.mex/ROUTER.md`: bullet do estado atualizado.
4. `graphify update .` após mudanças de código.
5. AskUserQuestion: go/no-go da FASE 3 (LLM) com o recall medido em mãos — condição do sign-off §9 do spec.

## Fora do escopo desta fase

- Hardening geral de `MotorContext` (validação de shape de blocks) — dívida segue no tracker; nenhum crash conhecido a motivar agora (YAGNI).
- Providers P3/P4 (FASE 2), TIER 0/1/2 no engine, janela-de-prazo, LLM (FASE 3), integração (FASE 4).
- Curadoria do `card_block_map` do repo MF (bloco-09) — ação do USER na GUI; as 2 contenções-fora NÃO são resolvíveis por código.
