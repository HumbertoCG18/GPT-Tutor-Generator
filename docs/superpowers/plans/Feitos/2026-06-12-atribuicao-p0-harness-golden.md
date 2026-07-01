# P0 Atribuição — Harness B3 + Golden Set Real — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harness de medição funcionando com o índice persistido real (B3 corrigido) + golden set do Metodos-Formais versionado com ground truth ancorado no gabarito da seção real.

**Architecture:** (1) `_is_prebuilt_block` em file_map.py alarga a detecção de bloco pré-construído (aceita `rows` legado E `id`+`source_rows`/`sessions` persistido). (2) Gerador offline cruza manifest real + seção física do stash + `card_block_map` → `metodos_formais_golden.json` (1-bloco = auto; 2+/sem = null pra decisão humana, preservada em re-runs). (3) `eval_assignments.py` consome o golden real: card map vai pra um tempdir como `course/.card_block_map.json` via `course_meta={"_repo_root": td}` (é como produção carrega, content_taxonomy.py:989-995), placar com pendentes.

**Tech Stack:** Python 3.13, pytest. Sem rede/Gemini — determinístico.

**Spec:** `docs/superpowers/specs/2026-06-12-atribuicao-p0-harness-golden-design.md`

**Fatos do código que o engenheiro precisa saber:**
- `select_probable_period_for_entry` está em `src/builder/routing/file_map.py:1087`; a detecção bugada é `if candidate_rows and "rows" in candidate_rows[0]:` (linha ~1108).
- O shape persistido de bloco (gerado por `_serialize_timeline_index`, `src/builder/timeline/index.py:902-921`) tem `id`, `period_start/end/label`, `kind`, `unit_slug`, `unit_confidence`, `primary_topic_*`, `topic_text`, `topics`, `aliases`, `card_evidence`, `sessions`, `source_rows` — e NÃO tem `rows`. Linha crua de cronograma não tem `id`+`source_rows`/`sessions`.
- Blocos administrativos já são excluídos na serialização (index.py:893) — o `.timeline_index.json` só tem blocos úteis.
- O gabarito seção→blocos é carregado em `resolve_unit_block_tags` (content_taxonomy.py:989-995) de `<repo_root>/course/.card_block_map.json`, onde `repo_root = course_meta.get("_repo_root")`. Formato: `{"<Seção>": {"block_ids": ["bloco-04"], "source": "manual"}}`.
- `_card_scoped_block` (content_taxonomy.py:845) usa `entry["source_section"]` pra consultar o gabarito; vazio → `("", 0.0)` silencioso.
- `scripts/eval_assignments.py` já roda (fixture sintética 5/5); `predict_block` monta a entry via `_entry_from_case` (sem `source_section` hoje) e injeta stubs em `resolve_unit_block_tags`.
- Pre-commit hook imprime `UnicodeEncodeError` cp1252 — inofensivo, commit passa (confirmar com `git log -1 --oneline`).
- Branch de trabalho: `feat/reconciliar-unit-bloco` (já correta).

---

### Task 1: Fix B3 — `_is_prebuilt_block` em file_map.py

**Files:**
- Modify: `src/builder/routing/file_map.py` (helper antes de `select_probable_period_for_entry:1087`; uso na linha ~1108)
- Test: `tests/test_eval_b3_persisted_index.py` (criar)

- [ ] **Step 1: Escrever testes que falham**

Criar `tests/test_eval_b3_persisted_index.py`:

```python
"""Regressão do bug B3: índice persistido (sem 'rows') degenerava pra 1º bloco.

Prova viva: blocos no shape de _serialize_timeline_index (id + sessions +
source_rows) devem ser reconhecidos como pré-construídos, não reconstruídos.
"""
import importlib.util
from pathlib import Path

from src.builder.routing.file_map import _is_prebuilt_block

_SPEC = importlib.util.spec_from_file_location(
    "eval_assignments",
    Path(__file__).resolve().parents[1] / "scripts" / "eval_assignments.py",
)
eval_assignments = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(eval_assignments)


def _pblock(bid, topic, start, end, unit="unidade-01-metodos-formais"):
    """Bloco no shape PERSISTIDO (cf. _serialize_timeline_index, index.py:902)."""
    return {
        "id": bid, "period_start": start, "period_end": end,
        "period_label": f"{start}..{end}", "kind": "class",
        "unit_slug": unit, "unit_confidence": 0.8,
        "primary_topic_slug": topic.replace(" ", "-"),
        "primary_topic_label": topic, "primary_topic_confidence": 0.8,
        "topic_ambiguous": False, "topic_candidates": [],
        "topic_text": topic, "topics": [topic],
        "aliases": [], "card_evidence": [],
        "sessions": [{"label": topic, "date": start}],
        "source_rows": [{"date": start, "description": topic}],
    }


def test_is_prebuilt_block_accepts_legacy_rows_shape():
    assert _is_prebuilt_block({"rows": [], "id": "b1"}) is True


def test_is_prebuilt_block_accepts_persisted_shape():
    assert _is_prebuilt_block(_pblock("bloco-01", "logica", "2026-03-02", "2026-03-02")) is True


def test_is_prebuilt_block_rejects_raw_cronograma_row():
    assert _is_prebuilt_block({"date": "2026-03-02", "description": "aula 1"}) is False
    assert _is_prebuilt_block({"id": "x"}) is False
    assert _is_prebuilt_block("nao-dict") is False


def test_persisted_index_does_not_degenerate_to_first_block():
    """ANTES do fix: blocos persistidos eram tratados como linhas cruas e a
    predição colapsava pro 1º bloco. DEPOIS: o scorer ranqueia os blocos reais."""
    blocks = [
        _pblock("bloco-01", "logica predicados sintaxe semantica", "2026-03-09", "2026-03-09"),
        _pblock("bloco-02", "inducao estrutural arvores listas", "2026-03-30", "2026-04-01"),
    ]
    case = {
        "id": "provas-arvores",
        "title": "ProvasIndutivas Arvores",
        "category": "material-de-aula",
        "raw_target": "raw/pdfs/ProvasIndutivas_Arvores.pdf",
        "tags": "inducao arvores",
        "markdown": "inducao estrutural sobre arvores e listas provas indutivas",
        "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                       "ambiguous": False},
        "expected_block_id": "bloco-02",
    }
    predicted, _band = eval_assignments.predict_block(case, blocks)
    assert predicted == "bloco-02"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_eval_b3_persisted_index.py -q`
Expected: FAIL — `ImportError: cannot import name '_is_prebuilt_block'`

- [ ] **Step 3: Implementar o helper e o uso**

Em `src/builder/routing/file_map.py`, logo ANTES de `def select_probable_period_for_entry(` (linha ~1087):

```python
def _is_prebuilt_block(item) -> bool:
    """Bloco já construído (não linha crua de cronograma).

    Legado: shape com 'rows'. Persistido (_serialize_timeline_index /
    .timeline_index.json): 'id' + 'source_rows'/'sessions'. Aceitar ambos
    conserta o bug B3 — o índice persistido era tratado como linha crua e a
    predição degenerava (cf. re-análise 2026-06-11)."""
    if not isinstance(item, dict):
        return False
    if "rows" in item:
        return True
    return "id" in item and ("source_rows" in item or "sessions" in item)
```

E dentro de `select_probable_period_for_entry`, trocar (linha ~1108):

```python
    if candidate_rows and "rows" in candidate_rows[0]:
```

por:

```python
    if candidate_rows and _is_prebuilt_block(candidate_rows[0]):
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_eval_b3_persisted_index.py -q`
Expected: 4 passed

Se `test_persisted_index_does_not_degenerate_to_first_block` falhar com o fix no
lugar (predição ainda errada), NÃO afrouxe o assert: aumente o sinal do caso
(tags/markdown mais alinhados ao topic do bloco-02) — o objetivo é um caso
inequívoco. Reporte se precisar disso.

- [ ] **Step 5: Suíte de regressão do módulo**

Run: `python -m pytest tests/ -q -k "file_map or eval or timeline"`
Expected: tudo verde (o caminho `rows` legado continua aceito)

Run também: `python scripts/eval_assignments.py`
Expected: `Acuracia de bloco: 5/5 (100.0%)` (fixture sintética intacta)

- [ ] **Step 6: Commit**

```bash
git add src/builder/routing/file_map.py tests/test_eval_b3_persisted_index.py
git commit -m "fix(routing): aceita bloco persistido em select_probable_period (bug B3)"
```

---

### Task 2: Gerador do golden set

**Files:**
- Create: `scripts/build_golden_metodos_formais.py`
- Test: `tests/test_golden_generator.py` (criar)

- [ ] **Step 1: Testes que falham**

Criar `tests/test_golden_generator.py`:

```python
"""Testes do gerador do golden set (funções puras; sem disco real)."""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "build_golden",
    Path(__file__).resolve().parents[1] / "scripts" / "build_golden_metodos_formais.py",
)
build_golden = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(build_golden)

_CARD_MAP = {
    "Secao Um Bloco": {"block_ids": ["bloco-04"], "source": "manual"},
    "Secao Dois Blocos": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
}
_SEC_INDEX = {"a.pdf": "Secao Um Bloco", "b.pdf": "Secao Dois Blocos",
              "d.pdf": "Secao Sem Gabarito"}


def _entry(eid, base, **kw):
    e = {"id": eid, "title": eid, "category": "material-de-aula",
         "source_path": f"C:/x/{base}", "computed_unit_slug": "u1",
         "unit_match_confidence": 0.7}
    e.update(kw)
    return e


def test_secao_um_bloco_vira_expected_automatico():
    case = build_golden.case_for_entry(_entry("e1", "a.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_block_id"] == "bloco-04"
    assert case["expected_origin"] == "gabarito_1bloco"


def test_secao_dois_blocos_vira_null_com_candidatos():
    case = build_golden.case_for_entry(_entry("e2", "b.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_block_id"] is None
    assert case["expected_origin"] == "precisa_decisao"
    assert case["candidates"] == ["bloco-05", "bloco-06"]


def test_sem_secao_fisica_vira_excluido():
    case = build_golden.case_for_entry(_entry("e3", "naoexiste.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_origin"] == "excluido"


def test_secao_sem_gabarito():
    case = build_golden.case_for_entry(_entry("e4", "d.pdf"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_block_id"] is None
    assert case["expected_origin"] == "sem_gabarito"


def test_bloco_manual_vira_excluido():
    case = build_golden.case_for_entry(
        _entry("e5", "a.pdf", manual_timeline_block_id="bloco-09"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_origin"] == "excluido"


def test_categoria_fora_da_timeline_vira_excluido():
    case = build_golden.case_for_entry(
        _entry("e6", "a.pdf", category="bibliografia"), _SEC_INDEX, _CARD_MAP)
    assert case["expected_origin"] == "excluido"


def test_merge_preserva_decisao_humana():
    old = [{"id": "e2", "expected_block_id": "bloco-06",
            "expected_origin": "precisa_decisao", "note": "aula de listas"}]
    new = [build_golden.case_for_entry(_entry("e2", "b.pdf"), _SEC_INDEX, _CARD_MAP)]
    build_golden.merge_manual_decisions(old, new)
    assert new[0]["expected_block_id"] == "bloco-06"


def test_merge_nao_inventa_decisao():
    new = [build_golden.case_for_entry(_entry("e2", "b.pdf"), _SEC_INDEX, _CARD_MAP)]
    build_golden.merge_manual_decisions([], new)
    assert new[0]["expected_block_id"] is None


def test_stash_section_index_exclui_basename_ambiguo(tmp_path):
    (tmp_path / "Sec A").mkdir(); (tmp_path / "Sec B").mkdir()
    (tmp_path / "Sec A" / "x.pdf").write_bytes(b"a")
    (tmp_path / "Sec B" / "x.pdf").write_bytes(b"b")
    (tmp_path / "Sec A" / "unico.pdf").write_bytes(b"c")
    idx = build_golden.stash_section_index(tmp_path)
    assert "x.pdf" not in idx
    assert idx["unico.pdf"] == "Sec A"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_golden_generator.py -q`
Expected: FAIL — arquivo `scripts/build_golden_metodos_formais.py` não existe

- [ ] **Step 3: Implementar o gerador**

Criar `scripts/build_golden_metodos_formais.py`:

```python
"""Gera o golden set real do Metodos-Formais (P0 da reforma da atribuicao).

Cruza o manifest real com a secao FISICA de cada arquivo no stash e o gabarito
card_block_map. Ground truth ancorado no cronograma: secao com 1 bloco no
gabarito vira expected automatico; 2+ ou sem gabarito fica null para decisao
humana (preservada em re-runs via merge_manual_decisions).

Utilitario de dados (caminhos da maquina do Humberto como constantes) — nao e
codigo de producao. Spec: docs/superpowers/specs/2026-06-12-atribuicao-p0-*.md

Uso:
    python scripts/build_golden_metodos_formais.py            # grava a fixture
    python scripts/build_golden_metodos_formais.py --dry-run  # so imprime
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_TUTOR = Path("C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor")
STASH = Path("C:/Users/Humberto/Desktop/Moodle/metodos-formais-para-computacao")
OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "eval" / "metodos_formais_golden.json"

_EXCLUDED_CATEGORIES = {"bibliografia", "referencias", "references", "cronograma"}
_MARKDOWN_CHARS = 1500


def stash_section_index(stash_dir: Path) -> dict:
    """{basename.casefold(): secao fisica} so para basenames de secao unica."""
    secs: dict = defaultdict(set)
    for f in stash_dir.rglob("*"):
        if f.is_file() and f.name != "_ARQUIVOS_DO_CARD.txt":
            secs[f.name.casefold()].add(f.relative_to(stash_dir).parts[0])
    return {k: next(iter(v)) for k, v in secs.items() if len(v) == 1}


def case_for_entry(entry: dict, sec_index: dict, card_map: dict) -> dict:
    """Um caso do golden a partir de uma entry do manifest real."""
    base = Path(str(entry.get("source_path") or "")).name.casefold()
    section = sec_index.get(base, "")
    case = {
        "id": str(entry.get("id") or ""),
        "title": str(entry.get("title") or ""),
        "category": str(entry.get("category") or ""),
        "source_section_real": section,
        "unit_guess": {
            "slug": str(entry.get("computed_unit_slug") or ""),
            "confidence": float(entry.get("unit_match_confidence") or 0.0),
            "ambiguous": False,
        },
        "markdown": "",
        "expected_block_id": None,
        "expected_origin": "",
        "candidates": [],
        "note": "",
    }
    if entry.get("manual_timeline_block_id"):
        case["expected_origin"] = "excluido"
        case["note"] = "bloco manual — nao mede o scorer"
        return case
    category = case["category"].strip().lower()
    if category in _EXCLUDED_CATEGORIES:
        case["expected_origin"] = "excluido"
        case["note"] = f"categoria fora da timeline: {category}"
        return case
    if not section:
        case["expected_origin"] = "excluido"
        case["note"] = "sem secao fisica derivavel (fora do stash ou basename ambiguo)"
        return case
    block_ids = list((card_map.get(section) or {}).get("block_ids") or [])
    if len(block_ids) == 1:
        case["expected_block_id"] = block_ids[0]
        case["expected_origin"] = "gabarito_1bloco"
    elif len(block_ids) >= 2:
        case["expected_origin"] = "precisa_decisao"
        case["candidates"] = block_ids
    else:
        case["expected_origin"] = "sem_gabarito"
    return case


def attach_markdown(case: dict, entry: dict, repo: Path) -> None:
    """Primeiros _MARKDOWN_CHARS do markdown base da entry (sinal pro scorer)."""
    rel = str(entry.get("base_markdown") or "")
    if not rel:
        return
    p = repo / rel
    if p.is_file():
        try:
            case["markdown"] = p.read_text(encoding="utf-8", errors="replace")[:_MARKDOWN_CHARS]
        except OSError:
            pass


def merge_manual_decisions(old_cases: list, new_cases: list) -> None:
    """Preserva expected_block_id preenchido a mao em re-runs (muta new_cases)."""
    decided = {
        str(c.get("id")): c
        for c in old_cases or []
        if c.get("expected_block_id")
        and c.get("expected_origin") in ("precisa_decisao", "sem_gabarito")
    }
    for case in new_cases:
        old = decided.get(str(case.get("id")))
        if old and case.get("expected_origin") in ("precisa_decisao", "sem_gabarito"):
            case["expected_block_id"] = old["expected_block_id"]
            case["note"] = str(old.get("note") or "decisao humana preservada")


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dry = "--dry-run" in argv
    manifest = json.loads((REPO_TUTOR / "manifest.json").read_text(encoding="utf-8"))
    ti = json.loads((REPO_TUTOR / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
    card_map = json.loads((REPO_TUTOR / "course" / ".card_block_map.json").read_text(encoding="utf-8"))
    sec_index = stash_section_index(STASH)

    cases = []
    for entry in manifest.get("entries") or []:
        case = case_for_entry(entry, sec_index, card_map)
        if case["expected_origin"] != "excluido":
            attach_markdown(case, entry, REPO_TUTOR)
        cases.append(case)
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8"))
        merge_manual_decisions(old.get("cases") or [], cases)

    gold = {
        "subject": "Metodos-Formais",
        "generated_from": {
            "manifest": str(REPO_TUTOR / "manifest.json"),
            "timeline_index": str(REPO_TUTOR / "course" / ".timeline_index.json"),
            "card_block_map": str(REPO_TUTOR / "course" / ".card_block_map.json"),
        },
        "card_block_map": card_map,
        "timeline": {"blocks": ti.get("blocks") or []},
        "cases": cases,
    }
    pend = [c for c in cases
            if c["expected_origin"] in ("precisa_decisao", "sem_gabarito")
            and not c["expected_block_id"]]
    excl = sum(1 for c in cases if c["expected_origin"] == "excluido")
    print(f"casos: {len(cases)}  pendentes (decisao humana): {len(pend)}  excluidos: {excl}")
    for c in pend:
        cands = f"  candidatos: {', '.join(c['candidates'])}" if c["candidates"] else ""
        print(f"  - {c['id']:40} secao={c['source_section_real']}{cands}")
    if not dry:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(gold, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"gravado: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_golden_generator.py -q`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/build_golden_metodos_formais.py tests/test_golden_generator.py
git commit -m "feat(eval): gerador do golden set real (gabarito 1-bloco auto, resto decisao humana)"
```

---

### Task 3: Harness consome o golden real

**Files:**
- Modify: `scripts/eval_assignments.py`
- Test: `tests/test_eval_golden_real.py` (criar)

- [ ] **Step 1: Testes que falham**

Criar `tests/test_eval_golden_real.py`:

```python
"""Harness com golden real: gabarito dispara com seção; null = pendente, não erro."""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "eval_assignments",
    Path(__file__).resolve().parents[1] / "scripts" / "eval_assignments.py",
)
eval_assignments = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(eval_assignments)


def _pblock(bid, topic, start, end, unit="unidade-01-metodos-formais"):
    return {
        "id": bid, "period_start": start, "period_end": end,
        "period_label": f"{start}..{end}", "kind": "class",
        "unit_slug": unit, "unit_confidence": 0.8,
        "primary_topic_slug": topic.replace(" ", "-"),
        "primary_topic_label": topic, "primary_topic_confidence": 0.8,
        "topic_ambiguous": False, "topic_candidates": [],
        "topic_text": topic, "topics": [topic],
        "aliases": [], "card_evidence": [],
        "sessions": [{"label": topic, "date": start}],
        "source_rows": [{"date": start, "description": topic}],
    }


def _gold():
    return {
        "card_block_map": {
            "Secao X": {"block_ids": ["bloco-02"], "source": "manual"},
        },
        "timeline": {"blocks": [
            _pblock("bloco-01", "logica predicados", "2026-03-09", "2026-03-09"),
            _pblock("bloco-02", "inducao arvores", "2026-03-30", "2026-04-01"),
        ]},
        "cases": [
            {"id": "hit-gabarito", "title": "Inducao", "category": "material-de-aula",
             "source_section_real": "Secao X",
             "unit_guess": {"slug": "unidade-01-metodos-formais", "confidence": 0.6,
                            "ambiguous": False},
             "markdown": "inducao estrutural",
             "expected_block_id": "bloco-02", "expected_origin": "gabarito_1bloco",
             "candidates": [], "note": ""},
            {"id": "pendente-1", "title": "Outro", "category": "material-de-aula",
             "source_section_real": "Secao Y",
             "unit_guess": {"slug": "", "confidence": 0.0, "ambiguous": True},
             "markdown": "",
             "expected_block_id": None, "expected_origin": "precisa_decisao",
             "candidates": ["bloco-01", "bloco-02"], "note": ""},
            {"id": "fora-1", "title": "Plano", "category": "cronograma",
             "source_section_real": "",
             "unit_guess": {"slug": "", "confidence": 0.0, "ambiguous": True},
             "markdown": "",
             "expected_block_id": None, "expected_origin": "excluido",
             "candidates": [], "note": "categoria fora da timeline"},
        ],
    }


def test_gabarito_dispara_com_secao_e_pendente_nao_conta_erro():
    report = eval_assignments.evaluate(_gold())
    assert report["correct"] == 1            # hit-gabarito acerta via card map
    assert report["total"] == 1              # só casos com expected não-null contam
    assert report["pending"] == 1            # null = pendente
    assert report["excluded"] == 1
    assert report["wrong"] == 0


def test_breakdown_com_e_sem_secao():
    gold = _gold()
    report = eval_assignments.evaluate(gold)
    assert report["with_section"]["total"] == 1
    assert report["with_section"]["correct"] == 1
    assert report["without_section"]["total"] == 0


def test_fixture_sintetica_antiga_continua_funcionando():
    import json
    gold_path = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "eval" / "assignments_gold.json"
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    report = eval_assignments.evaluate(gold)
    assert report["total"] == 5 and report["correct"] == 5
    assert report["pending"] == 0 and report["excluded"] == 0
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_eval_golden_real.py -q`
Expected: FAIL — `predict_block` não aceita `course_meta` / `evaluate` sem `pending`

- [ ] **Step 3: Implementar em scripts/eval_assignments.py**

(a) `_entry_from_case` ganha `source_section` (campo novo no dict retornado):

```python
def _entry_from_case(case: dict) -> dict:
    return {
        "id": str(case.get("id", "")),
        "title": str(case.get("title", "")),
        "category": str(case.get("category", "material-de-aula")),
        "file_type": "pdf",
        "source_path": str(case.get("raw_target", "")),
        "raw_target": str(case.get("raw_target", "")),
        "source_section": str(case.get("source_section_real", "")),
        "tags": str(case.get("tags", "")),
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
        "manual_subunit_slug": "",
    }
```

(b) `predict_block` ganha `course_meta` (3º parâmetro, default None) e repassa:

```python
def predict_block(case: dict, blocks: list, course_meta: dict | None = None) -> tuple[str, str]:
    """Retorna (computed_block_id, computed_block_band) do scorer real."""
    guess = case.get("unit_guess") or {}
    unit_stub = _stub_unit_match(
        guess.get("slug", ""),
        guess.get("confidence", 0.0),
        guess.get("ambiguous", True),
    )
    markdown = str(case.get("markdown", ""))

    out = resolve_unit_block_tags(
        [_entry_from_case(case)],
        course_meta=dict(course_meta or {}),
        ...resto idêntico ao atual...
```

(só a linha `course_meta={}` muda para `course_meta=dict(course_meta or {})`; o
resto dos kwargs fica como está).

(c) `evaluate` ganha card map via tempdir (é como produção carrega o gabarito,
content_taxonomy.py:989-995), pendentes e breakdown com/sem seção. Substituir a
função inteira por:

```python
def evaluate(gold: dict) -> dict:
    import tempfile

    blocks = gold["timeline"]["blocks"]
    cases = gold["cases"]
    card_map = gold.get("card_block_map") or {}

    case_rows = []
    pending_rows = []
    confusion: dict = {}
    bands = {
        "alta": {"correct": 0, "wrong": 0},
        "media": {"correct": 0, "wrong": 0},
        "baixa": {"correct": 0, "wrong": 0},
        "": {"correct": 0, "wrong": 0},  # orfao (sem band)
    }
    correct = 0
    orphans = 0
    pending = 0
    excluded = 0
    with_section = {"total": 0, "correct": 0}
    without_section = {"total": 0, "correct": 0}

    with tempfile.TemporaryDirectory() as td:
        course_meta: dict = {}
        if card_map:
            course_dir = Path(td) / "course"
            course_dir.mkdir(parents=True)
            (course_dir / ".card_block_map.json").write_text(
                json.dumps(card_map, ensure_ascii=False), encoding="utf-8")
            course_meta = {"_repo_root": td}

        for case in cases:
            origin = str(case.get("expected_origin") or "")
            if origin == "excluido":
                excluded += 1
                continue
            predicted, band = predict_block(case, blocks, course_meta)
            raw_expected = case.get("expected_block_id", "")
            if raw_expected is None:
                # null explícito = ground truth pendente de decisão humana.
                # ("" continua sendo o legado "espera órfão" da fixture sintética.)
                pending += 1
                pending_rows.append({
                    "id": str(case.get("id", "")), "origin": origin,
                    "predicted": predicted, "band": band,
                    "candidates": list(case.get("candidates") or []),
                })
                continue
            expected = str(raw_expected)
            is_correct = predicted == expected
            if is_correct:
                correct += 1
            if predicted == "":
                orphans += 1
            seg = with_section if str(case.get("source_section_real") or "") else without_section
            seg["total"] += 1
            seg["correct"] += int(is_correct)
            bands.setdefault(band, {"correct": 0, "wrong": 0})
            bands[band]["correct" if is_correct else "wrong"] += 1
            key = f"{expected}->{predicted or '(orfao)'}"
            confusion[key] = confusion.get(key, 0) + 1
            case_rows.append({
                "id": str(case.get("id", "")),
                "expected": expected,
                "predicted": predicted,
                "band": band,
                "correct": is_correct,
                "note": str(case.get("note", "")),
            })

    total = len(case_rows)
    return {
        "total": total,
        "correct": correct,
        "wrong": total - correct,
        "orphans": orphans,
        "pending": pending,
        "excluded": excluded,
        "block_accuracy": (correct / total) if total else 0.0,
        "with_section": with_section,
        "without_section": without_section,
        # confiante e ERRADO = pior falha (band alta mas bloco errado)
        "confident_wrong": bands["alta"]["wrong"],
        "bands": bands,
        "confusion": confusion,
        "cases": case_rows,
        "pending_cases": pending_rows,
    }
```

(d) `format_report` ganha as linhas novas. Depois da linha "Confiante e ERRADO",
inserir:

```python
    ws, wos = report["with_section"], report["without_section"]
    lines.append(
        f"Com secao real: {ws['correct']}/{ws['total']}   "
        f"Sem secao: {wos['correct']}/{wos['total']}   "
        f"Pendentes (decisao humana): {report['pending']}   "
        f"Excluidos: {report['excluded']}"
    )
```

E antes do "Baseline registrado", listar pendentes se houver:

```python
    if report["pending_cases"]:
        lines.append("")
        lines.append("Pendentes (expected_block_id null — preencher no golden):")
        for p in report["pending_cases"]:
            cands = f"  candidatos: {', '.join(p['candidates'])}" if p["candidates"] else ""
            lines.append(f"  - {p['id']:<40} previu={p['predicted'] or '(orfao)'} band={p['band'] or '-'}{cands}")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_eval_golden_real.py tests/test_eval_b3_persisted_index.py -q`
Expected: 7 passed

Run: `python scripts/eval_assignments.py`
Expected: `Acuracia de bloco: 5/5 (100.0%)` — retrocompat intacta

- [ ] **Step 5: Commit**

```bash
git add scripts/eval_assignments.py tests/test_eval_golden_real.py
git commit -m "feat(eval): harness consome golden real (card map, pendentes, breakdown secao)"
```

---

### Task 4: Gerar a fixture real e registrar o placar

Pré-requisito de máquina: o repo `Metodos-Formais-Tutor` e o stash do Desktop
existem nos caminhos das constantes do gerador (é a máquina do Humberto).

- [ ] **Step 1: Gerar**

Run: `python scripts/build_golden_metodos_formais.py`
Expected: imprime `casos: 56  pendentes (decisao humana): N  excluidos: M` +
lista de pendentes, e grava `tests/fixtures/eval/metodos_formais_golden.json`.
Esperado da re-análise: ~22 casos `gabarito_1bloco`-ish, ~18 `sem_gabarito`
(seção "Verificação de Programas" sem entrada no card map), alguns
`precisa_decisao` e excluídos (manuais, bibliografia, fora do stash). Os números
exatos podem variar (o usuário moveu arquivos no stash) — registrar o que sair.

- [ ] **Step 2: Rodar o harness no golden real**

Run: `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json`
Expected (critérios de aceite da spec):
- roda sem erro, imprime placar com pendentes/excluídos
- casos `gabarito_1bloco` com seção real majoritariamente CORRETOS (gabarito dispara)
- pendentes listados com predição informativa (Hoare/Dafny aparecem aqui — seção
  "Verificação de Programas" sem gabarito; o erro do scorer fica VISÍVEL na coluna
  `previu=`, é o sintoma que P1-P4 consertam)
- baseline: a fixture real não tem campo `baseline` → "Baseline registrado: 0.0%"
  e exit 0 — ok neste P0

Copiar o placar impresso para o commit message do Step 3 (registro histórico).

- [ ] **Step 3: Commitar a fixture com o placar**

```bash
git add tests/fixtures/eval/metodos_formais_golden.json
git commit -m "feat(eval): golden set real Metodos-Formais (placar inicial no corpo)" -m "<colar aqui o placar impresso no Step 2>"
```

---

### Task 5: Suíte completa + verificação final

- [ ] **Step 1: Suíte inteira**

Run: `python -m pytest -q`
Expected: tudo verde (1231 + 16 novos ≈ 1247)

- [ ] **Step 2: Verificação de aceite da spec**

Run: `python scripts/eval_assignments.py` → 5/5 (sintética intacta)
Run: `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json` → placar real sem crash
Run: `python -m pytest tests/test_eval_b3_persisted_index.py -q` → B3 provado

- [ ] **Step 3: Commit final (se sobrou ajuste)**

```bash
git add -A
git commit -m "test(eval): P0 fechado - harness real + golden versionado"
```

---

## Self-review (feito na escrita)

- Spec Componente 1 (fix B3 aceitar ambos + teste regressão) → Task 1.
  Componente 2 (gerador, regras 1-bloco/2+/sem/excluído, merge preserva humano,
  teste) → Task 2. Componente 3 (harness: source_section na entry, card map via
  `_repo_root`, placar com pendentes/breakdown, retrocompat, teste) → Task 3.
  Critérios de aceite do harness 1-5 → Tasks 3 (testes) e 4 (run real) e 5 (suíte).
- Semântica null vs "": null = pendente (golden real); "" = legado espera-órfão
  (fixture sintética) — explícito no código e comentário (Task 3c).
- Tipos consistentes: `_pblock` idêntico nos 2 arquivos de teste (duplicado de
  propósito — arquivos de teste independentes, sem helper compartilhado novo);
  `predict_block(case, blocks, course_meta=None)` usado igual nas Tasks 1 e 3;
  campos do caso (`source_section_real`, `expected_origin`, `candidates`) iguais
  no gerador (Task 2) e no harness (Task 3).
- Sem placeholders; código completo em cada step; comandos com expected.
