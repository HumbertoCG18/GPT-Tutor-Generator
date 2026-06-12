# Reforma do Funil P1+P2+P3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Card_block_map automático via labels Moodle (P1), confiança de bloco calibrada com teto por método e `computed_block_method` universal (P2), higiene B1/B5/B4 (P3) — medindo no golden após cada fase (meta: 58.7% → ≥75%, confiante-e-errado 6 → ≤2).

**Architecture:** Parser puro de labels (`moodle_labels.py`, cascata A→B→C→D) → `derive_card_block_map` (datas ∩ períodos dos blocos) → persistido no import com merge (manual sobrepõe). Confiança de bloco ganha `relative_margin_confidence` (margem relativa × força absoluta) usada SÓ nos caminhos de bloco; teto por método aplicado no ponto único de decisão em `resolve_unit_block_tags`, que passa a gravar `computed_block_method` pra toda entry.

**Tech Stack:** Python 3.13, pytest. Harness: `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json`.

**Spec:** `docs/superpowers/specs/2026-06-12-atribuicao-p1p2p3-funil-design.md`
**Catálogo de formatos:** `docs/reports/2026-06-12-catalogo-formatos-labels-moodle.md`

**Fatos do código:**
- Decisão de bloco em `resolve_unit_block_tags` (src/builder/extraction/content_taxonomy.py:1055-1124): branches manual (conf 1.0) → `review_list_block_for_entry` (0.95) → `_card_scoped_block` (card map) → scorer (`select_probable_period_for_entry_fn`) → `_best_instructional_block_fallback`. `computed_block_confidence` consolidada na linha ~1135.
- `_card_scoped_block` (content_taxonomy.py:845): 1 bloco no card → `CARD_SINGLE_CONF`; 2+ → scorer restrito (retorna conf do scorer).
- Card map carregado de `<repo_root>/course/.card_block_map.json` (content_taxonomy.py:989-995); formato `{"Seção": {"block_ids": [...], "source": "manual"}}`; `load_card_block_map`/`lookup_card_blocks` em src/builder/timeline/card_block.py.
- `margin_confidence` (src/builder/routing/thresholds.py:6-12) é COMPARTILHADA com unidade/tópico — NÃO alterar; criar função nova só pra bloco.
- Bands: `confidence_band` thresholds.py:41 (BAND_HIGH=0.50, BAND_LOW=0.20).
- Conf de bloco nasce em 2 lugares: dentro de `select_probable_period_for_entry` (file_map.py, retorna p_conf) e `_best_instructional_block_fallback`. Ambos usam `margin_confidence` hoje.
- `import_moodle_courses` (src/builder/sources/moodle.py:283): tem `contents` e `repo_root` (sp.repo_root) na mão; já faz backfill de source_section.
- `_NO_TIMELINE_CATEGORIES` (content_taxonomy.py:961) = {"cronograma","bibliografia","referencias"} — sem "references".
- Import de entries: src/builder/ops/lifecycle_ops.py:58-65 (dedup por source_path; ids podem colidir).
- Branch: feat/reconciliar-unit-bloco. Pre-commit imprime UnicodeEncodeError cp1252 inofensivo.
- MEDIR = rodar o harness no golden real e anotar (geral, com-seção, confiante-errado); regenerar golden quando o card map mudar (`python scripts/build_golden_metodos_formais.py` — merge preserva decisões humanas).

---

### Task 1: Parser formato A (moodle_labels.py)

**Files:**
- Create: `src/builder/sources/moodle_labels.py`
- Test: `tests/test_moodle_labels.py` (criar)

- [ ] **Step 1: Testes que falham** — criar `tests/test_moodle_labels.py`:

```python
"""Parser de labels temporais dos cards Moodle (formatos A-D do catálogo)."""
from src.builder.sources.moodle_labels import parse_card_dates

def _sec(name, labels=(), modname="label"):
    return {"name": name, "modules": [
        {"modname": modname, "name": "", "description": d} for d in labels]}

_A = """<p>Semana 13/04/2026 a 17/04/2026:</p>
<p>(13/04/2026): Provas em Isabelle, exerc&iacute;cios;</p>
<p>(15/04/2026): Exerc&iacute;cios de revis&atilde;o para P1.</p>
<p>(atividade ass&iacute;ncrona): exerc&iacute;cios.</p>"""

def test_formato_a_extrai_aulas_com_data_completa():
    out = parse_card_dates([_sec("Provas por Indução", [_A])], year=2026)
    card = out["Provas por Indução"]
    assert card["format"] == "A"
    assert "2026-04-13" in card["dates"] and "2026-04-15" in card["dates"]
    assert ("2026-04-13", "2026-04-17") in card["weeks"]
    texts = {l["date"]: l["text"] for l in card["lessons"]}
    assert "revis" in texts["2026-04-15"].lower()

def test_formato_a_ignora_linha_assincrona():
    out = parse_card_dates([_sec("X", [_A])], year=2026)
    assert all(l["date"] for l in out["X"]["lessons"])

def test_formato_a_data_avulsa_fora_do_padrao():
    lbl = "<p>Trabalho Final (03/07/2026):</p>"
    out = parse_card_dates([_sec("TDE", [lbl])], year=2026)
    assert "2026-07-03" in out["TDE"]["dates"]

def test_data_invalida_descartada_sem_excecao():
    lbl = "<p>(30/02/2026): aula fantasma;</p><p>(04/03/2026): real.</p>"
    out = parse_card_dates([_sec("X", [lbl])], year=2026)
    assert out["X"]["dates"] == ["2026-03-04"]

def test_secao_sem_labels_fica_fora():
    out = parse_card_dates([_sec("Threads", [])], year=2026)
    assert "Threads" not in out
```

- [ ] **Step 2:** `python -m pytest tests/test_moodle_labels.py -q` → FAIL (módulo não existe)

- [ ] **Step 3: Implementar** `src/builder/sources/moodle_labels.py`:

```python
"""Parser dos labels temporais dos cards Moodle — formatos A-D do catálogo.

Cf. docs/reports/2026-06-12-catalogo-formatos-labels-moodle.md. Funções puras
(recebem o payload de core_course_get_contents); nunca inventam: seção sem
sinal temporal fica FORA do resultado (formato E = degradação honesta).
"""
from __future__ import annotations

import html
import re
from datetime import date

from src.builder.sources.moodle import sanitize_folder_name

_WEEK_FULL = re.compile(r"Semana\s+(\d{1,2}/\d{1,2}/\d{4})\s*a\s*(\d{1,2}/\d{1,2}/\d{4})")
_LESSON_FULL = re.compile(r"\((\d{1,2}/\d{1,2}/\d{4})\)\s*:\s*(.+)")
_LOOSE_FULL = re.compile(r"\((\d{1,2}/\d{1,2}/\d{4})\)")
_ASYNC = re.compile(r"\(atividade\s+ass[ií]ncrona\)", re.IGNORECASE)


def _strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "\n", s or ""))


def _iso(raw: str, year: int | None = None) -> str:
    """DD/MM[/AAAA] -> ISO; '' se inválida (30/02 etc.)."""
    parts = raw.split("/")
    try:
        d, m = int(parts[0]), int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else int(year or 0)
        return date(y, m, d).isoformat()
    except (ValueError, IndexError):
        return ""


def _label_texts(sec: dict) -> list:
    return [_strip_html(m.get("description") or m.get("name") or "")
            for m in sec.get("modules", []) or [] if m.get("modname") == "label"]


def _parse_format_a(texts: list) -> dict | None:
    weeks, lessons, dates = [], [], []
    for txt in texts:
        for line in txt.splitlines():
            line = line.strip()
            if not line or _ASYNC.search(line):
                continue
            w = _WEEK_FULL.search(line)
            if w:
                a, b = _iso(w.group(1)), _iso(w.group(2))
                if a and b:
                    weeks.append((a, b))
                continue
            l = _LESSON_FULL.search(line)
            if l:
                d = _iso(l.group(1))
                if d:
                    lessons.append({"date": d, "text": l.group(2).strip().rstrip(";.")})
                    dates.append(d)
                continue
            for m in _LOOSE_FULL.finditer(line):
                d = _iso(m.group(1))
                if d:
                    dates.append(d)
    if not dates and not weeks:
        return None
    return {"format": "A", "dates": sorted(set(dates)), "weeks": weeks, "lessons": lessons}


def parse_card_dates(contents, year: int) -> dict:
    """{secao_sanitizada: {format, dates[iso], weeks[(ini,fim)], lessons}}.

    Cascata A -> B -> C -> D por seção (Tasks 1-2 implementam A; B-D na Task 2).
    Seção sem sinal -> fora do dict."""
    out: dict = {}
    for sec in contents or []:
        name = sanitize_folder_name(str(sec.get("name") or ""))
        if not name:
            continue
        texts = _label_texts(sec)
        parsed = _parse_format_a(texts)
        if parsed:
            out[name] = parsed
    return out
```

- [ ] **Step 4:** `python -m pytest tests/test_moodle_labels.py -q` → 5 passed
- [ ] **Step 5: Commit** — `git add src/builder/sources/moodle_labels.py tests/test_moodle_labels.py && git commit -m "feat(labels): parser formato A (Semana DD/MM/AAAA + aulas por dia)"`

---

### Task 2: Parsers B, C, D (cascata completa)

**Files:**
- Modify: `src/builder/sources/moodle_labels.py`
- Test: `tests/test_moodle_labels.py` (append)

- [ ] **Step 1: Testes que falham** (append):

```python
def test_formato_b_nome_da_secao_e_roteiro():
    sec = {"name": "Semana 5 -30/03 a 01/04: ML - Aprendizado Supervisionado",
           "modules": [{"modname": "label", "name": "",
                        "description": "<p>Roteiro</p><p>30/03: Rede Perceptron; Exercicios</p><p>01/04: Rede MLP.</p>"}]}
    out = parse_card_dates([sec], year=2026)
    card = out[list(out)[0]]
    assert card["format"] == "B"
    assert "2026-03-30" in card["dates"] and "2026-04-01" in card["dates"]
    assert ("2026-03-30", "2026-04-01") in card["weeks"]

def test_formato_b_tolerante_dia_sem_zero():
    sec = {"name": "Semana 8 - 20/04 a 24/4 - ML", "modules": []}
    out = parse_card_dates([sec], year=2026)
    assert ("2026-04-20", "2026-04-24") in out[list(out)[0]]["weeks"]

def test_formato_c_aula_numerada():
    lbl = "<p>Aula 2 - 05/03</p><p>CONTEÚDO: Contexto da Área</p>"
    sec = {"name": "Fundamentos de IHC/UX",
           "modules": [{"modname": "label", "name": "", "description": lbl}]}
    out = parse_card_dates([sec], year=2026)
    card = out["Fundamentos de IHC_UX"] if "Fundamentos de IHC_UX" in out else out[list(out)[0]]
    assert card["format"] == "C"
    assert "2026-03-05" in card["dates"]

def test_formato_d_semana_ordinal_so_com_ancora():
    sec = {"name": "Semana 7 - Halteproblem und Entscheidungsproblem", "modules": []}
    out = parse_card_dates([sec], year=2026)
    assert list(out) == []          # sem week_anchor -> degrada (fora)
    out2 = parse_card_dates([sec], year=2026, week_anchor="2026-03-02")
    card = out2[list(out2)[0]]
    assert card["format"] == "D"
    # semana 7 = anchor + 6*7 dias: 13/04 a 17/04 (seg-sex)
    assert card["weeks"] == [("2026-04-13", "2026-04-17")]

def test_formato_a_tem_precedencia_sobre_b():
    sec = {"name": "Semana 1 - 02/03 a 06/03 - Intro",
           "modules": [{"modname": "label", "name": "",
                        "description": "<p>(04/03/2026): aula com ano completo.</p>"}]}
    out = parse_card_dates([sec], year=2026)
    assert out[list(out)[0]]["format"] == "A"
```

- [ ] **Step 2:** rodar → FAIL
- [ ] **Step 3: Implementar** — adicionar em moodle_labels.py:

```python
_WEEK_SHORT = re.compile(r"Semana\s*\d+\s*[-–]?\s*(\d{1,2}/\d{1,2})\s*a\s*(\d{1,2}/\d{1,2})")
_LESSON_SHORT = re.compile(r"^(\d{1,2}/\d{1,2})\s*[:\-]\s*(.+)")
_AULA_C = re.compile(r"Aula\s+\d+\s*[-–]\s*(\d{1,2}/\d{1,2})\b")
_WEEK_ORDINAL = re.compile(r"Semana\s+(\d+)\b")


def _parse_format_b(sec_name: str, texts: list, year: int) -> dict | None:
    w = _WEEK_SHORT.search(sec_name)
    if not w:
        return None
    a, b = _iso(w.group(1), year), _iso(w.group(2), year)
    if not (a and b):
        return None
    lessons, dates = [], []
    for txt in texts:
        for line in txt.splitlines():
            m = _LESSON_SHORT.match(line.strip())
            if m:
                d = _iso(m.group(1), year)
                if d:
                    lessons.append({"date": d, "text": m.group(2).strip().rstrip(";.")})
                    dates.append(d)
    return {"format": "B", "dates": sorted(set(dates)) or [a, b],
            "weeks": [(a, b)], "lessons": lessons}


def _parse_format_c(texts: list, year: int) -> dict | None:
    dates, lessons = [], []
    for txt in texts:
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        for i, line in enumerate(lines):
            m = _AULA_C.search(line)
            if m:
                d = _iso(m.group(1), year)
                if d:
                    text = next((x.split(":", 1)[1].strip() for x in lines[i:i + 3]
                                 if x.upper().startswith("CONTE") and ":" in x), "")
                    lessons.append({"date": d, "text": text})
                    dates.append(d)
    if not dates:
        return None
    return {"format": "C", "dates": sorted(set(dates)), "weeks": [], "lessons": lessons}


def _parse_format_d(sec_name: str, week_anchor: str) -> dict | None:
    m = _WEEK_ORDINAL.search(sec_name)
    if not m or not week_anchor:
        return None
    from datetime import timedelta
    try:
        start = date.fromisoformat(week_anchor) + timedelta(weeks=int(m.group(1)) - 1)
    except ValueError:
        return None
    end = start + timedelta(days=4)
    return {"format": "D", "dates": [], "weeks": [(start.isoformat(), end.isoformat())],
            "lessons": []}
```

E `parse_card_dates` vira a cascata (assinatura ganha `week_anchor: str = ""`):

```python
def parse_card_dates(contents, year: int, week_anchor: str = "") -> dict:
    out: dict = {}
    for sec in contents or []:
        raw_name = str(sec.get("name") or "")
        name = sanitize_folder_name(raw_name)
        if not name:
            continue
        texts = _label_texts(sec)
        parsed = (_parse_format_a(texts)
                  or _parse_format_b(raw_name, texts, year)
                  or _parse_format_c(texts, year)
                  or _parse_format_d(raw_name, week_anchor))
        if parsed:
            out[name] = parsed
    return out
```

- [ ] **Step 4:** `python -m pytest tests/test_moodle_labels.py -q` → 10 passed
- [ ] **Step 5: Commit** — `git commit -m "feat(labels): parsers B (IA), C (UX), D (semana ordinal com ancora)"`

---

### Task 3: derive_card_block_map

**Files:**
- Modify: `src/builder/sources/moodle_labels.py`
- Test: `tests/test_moodle_labels.py` (append)

- [ ] **Step 1: Testes que falham** (append):

```python
from src.builder.sources.moodle_labels import derive_card_block_map

def _blk(bid, start, end, admin=False):
    b = {"id": bid, "period_start": start, "period_end": end}
    if admin:
        b["administrative_only"] = True
    return b

_BLOCKS = [_blk("bloco-03", "2026-03-09", "2026-03-09"),
           _blk("bloco-04", "2026-03-11", "2026-03-25"),
           _blk("bloco-08", "2026-04-20", "2026-04-20", admin=True)]

def test_derive_intersecta_datas_de_aula_com_periodos():
    cards = {"Revisão": {"format": "A", "weeks": [],
                         "dates": ["2026-03-09", "2026-03-11"], "lessons": []}}
    out = derive_card_block_map(cards, _BLOCKS)
    assert out["Revisão"]["block_ids"] == ["bloco-03", "bloco-04"]
    assert out["Revisão"]["source"] == "labels"

def test_derive_ignora_bloco_administrativo():
    cards = {"X": {"format": "A", "weeks": [], "dates": ["2026-04-20"], "lessons": []}}
    assert "X" not in derive_card_block_map(cards, _BLOCKS)

def test_derive_usa_weeks_quando_nao_ha_dates():
    cards = {"D": {"format": "D", "weeks": [("2026-03-09", "2026-03-13")],
                   "dates": [], "lessons": []}}
    out = derive_card_block_map(cards, _BLOCKS)
    assert "bloco-03" in out["D"]["block_ids"] and "bloco-04" in out["D"]["block_ids"]

def test_derive_card_sem_match_fica_fora():
    cards = {"X": {"format": "A", "weeks": [], "dates": ["2027-01-01"], "lessons": []}}
    assert derive_card_block_map(cards, _BLOCKS) == {}
```

- [ ] **Step 2:** rodar → FAIL
- [ ] **Step 3: Implementar**:

```python
def derive_card_block_map(card_dates: dict, blocks: list) -> dict:
    """{secao: {block_ids, source:"labels", format, dates}} por interseção de
    datas de AULA (preferidas) ou semanas (formato D) com period_start..end
    dos blocos não-administrativos. Card sem match -> fora (nunca inventa)."""
    instructional = [b for b in blocks or [] if not bool(b.get("administrative_only"))]
    out: dict = {}
    for card, info in (card_dates or {}).items():
        hits = []
        for b in instructional:
            start = str(b.get("period_start") or "")
            end = str(b.get("period_end") or "") or start
            if not start:
                continue
            dates = info.get("dates") or []
            in_dates = any(start <= d <= end for d in dates)
            in_weeks = (not dates) and any(
                ws <= end and we >= start for ws, we in info.get("weeks") or [])
            if in_dates or in_weeks:
                hits.append((start, str(b.get("id") or "")))
        if hits:
            out[card] = {"block_ids": [bid for _s, bid in sorted(hits)],
                         "source": "labels", "format": info.get("format", ""),
                         "dates": list(info.get("dates") or [])}
    return out
```

- [ ] **Step 4:** `python -m pytest tests/test_moodle_labels.py -q` → 14 passed
- [ ] **Step 5: Commit** — `git commit -m "feat(labels): derive_card_block_map (datas de aula x periodos dos blocos)"`

---

### Task 4: Persistência no import com merge (manual sobrepõe)

**Files:**
- Modify: `src/builder/sources/moodle.py` (`import_moodle_courses`, após o backfill ~linha 351)
- Modify: `src/builder/timeline/card_block.py` (helper `save_card_block_map` se não existir — conferir)
- Test: `tests/test_moodle_labels.py` (append)

- [ ] **Step 1: Testes que falham** (append):

```python
import json
from src.builder.sources.moodle_labels import merge_card_block_map

def test_merge_manual_sobrepoe_auto():
    existing = {"Revisão": {"block_ids": ["bloco-02"], "source": "manual"}}
    derived = {"Revisão": {"block_ids": ["bloco-03"], "source": "labels", "format": "A", "dates": []},
               "Novo": {"block_ids": ["bloco-05"], "source": "labels", "format": "A", "dates": []}}
    out = merge_card_block_map(existing, derived)
    assert out["Revisão"]["block_ids"] == ["bloco-02"]      # manual intocado
    assert out["Novo"]["block_ids"] == ["bloco-05"]

def test_merge_labels_antigo_e_atualizado():
    existing = {"X": {"block_ids": ["bloco-01"], "source": "labels"}}
    derived = {"X": {"block_ids": ["bloco-02"], "source": "labels", "format": "A", "dates": []}}
    assert merge_card_block_map(existing, derived)["X"]["block_ids"] == ["bloco-02"]

def test_merge_entrada_manual_sem_derivacao_sobrevive():
    existing = {"So Manual": {"block_ids": ["bloco-07"], "source": "manual"}}
    assert merge_card_block_map(existing, {})["So Manual"]["block_ids"] == ["bloco-07"]
```

- [ ] **Step 2:** rodar → FAIL
- [ ] **Step 3: Implementar** `merge_card_block_map` em moodle_labels.py:

```python
def merge_card_block_map(existing: dict, derived: dict) -> dict:
    """Merge do card map: manual NUNCA é sobrescrito; labels atualiza/adiciona."""
    out = dict(existing or {})
    for card, entry in (derived or {}).items():
        cur = out.get(card)
        if cur and str(cur.get("source") or "") == "manual":
            continue
        out[card] = entry
    return out
```

Em `import_moodle_courses` (moodle.py), após o bloco de backfill (linhas ~340-351),
dentro do mesmo `if repo ...` (precisa do timeline index do repo):

```python
        # --- card_block_map automático via labels (P1) ---
        if repo:
            try:
                from src.builder.sources.moodle_labels import (
                    parse_card_dates, derive_card_block_map, merge_card_block_map,
                )
                ti_path = Path(repo) / "course" / ".timeline_index.json"
                map_path = Path(repo) / "course" / ".card_block_map.json"
                if ti_path.is_file():
                    blocks = (_json.loads(ti_path.read_text(encoding="utf-8")) or {}).get("blocks") or []
                    year = int((info.get("semester") or "0/0").split("/")[0] or 0)
                    derived = derive_card_block_map(parse_card_dates(contents, year), blocks)
                    existing = {}
                    if map_path.is_file():
                        existing = _json.loads(map_path.read_text(encoding="utf-8")) or {}
                    merged = merge_card_block_map(existing, derived)
                    if merged != existing:
                        map_path.write_text(
                            _json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
                    card_map_labels += sum(1 for v in derived.values())
                    card_map_manual += sum(1 for v in merged.values()
                                           if str(v.get("source") or "") == "manual")
            except Exception:
                logger.warning("card_block_map via labels falhou para %s", info["name"], exc_info=True)
```

Inicializar `card_map_labels = card_map_manual = 0` junto dos contadores (linha ~294)
e adicionar ao dict de retorno: `"card_map_labels": card_map_labels,
"card_map_manual": card_map_manual`. Conferir: moodle.py usa `logger`? Se não
existir, usar `logging.getLogger(__name__)` no topo (conferir imports).
A UI (dialogs.py:1926-1928) ganha no `base_msg`:
`f"card map por labels: {rep.get('card_map_labels', 0)} (manuais preservadas: {rep.get('card_map_manual', 0)})\n"`.

- [ ] **Step 4:** `python -m pytest tests/test_moodle_labels.py tests/test_moodle.py tests/test_m365_card_mapping.py -q` → verde
- [ ] **Step 5: Commit** — `git commit -m "feat(labels): card_block_map automatico no import (manual sobrepoe)"`

---

### Task 5: MEDIR P1 — regenerar card map de MF + golden + placar

Operacional (dados da máquina). Sub-steps:

- [ ] **Step 1:** Script one-shot (inline, não versionado — ou `--dry-run` primeiro): chamar a API com o client real, `parse_card_dates(contents, 2026)` + `derive_card_block_map(blocks do .timeline_index.json de MF)` + `merge_card_block_map` com o mapa atual → gravar `Metodos-Formais-Tutor/course/.card_block_map.json`. IMPRIMIR o diff por seção antes de gravar.
  Validar contra o esperado da spec: "Exercícios de Revisão para Provas"→{bloco-07} (manual, preservada), "Verificação de Programas"→{bloco-10..13,15}, "Revisão - Lógica e Especificação"→{bloco-03, bloco-04}.
- [ ] **Step 2:** `python scripts/build_golden_metodos_formais.py` (merge preserva decisões) e `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json`.
- [ ] **Step 3:** Registrar placar na tabela do plano-mestre (linha P1) + commit fixture/docs:
  `git commit -m "feat(p1): card map de MF via labels (placar no corpo)"` com o placar no corpo.
  Aceite: acurácia ≥ 75%; zero regressão nos 27 casos hoje certos (comparar lista de erros antes/depois).

---

### Task 6: Mapear consumidores de confiança/band (P2.4 — investigação)

- [ ] **Step 1:** Grep e leitura: todos os usos de `computed_block_confidence`,
  `computed_block_band`, `confidence_band`, `BAND_HIGH`, `BAND_LOW` em src/ e scripts/.
  Para cada uso: arquivo:linha, o que faz com o valor, quebra se a distribuição mudar?
- [ ] **Step 2:** Registrar a lista como comentário no commit da Task 7 e no relatório
  do ciclo. Sem mudança de código nesta task.

---

### Task 7: relative_margin_confidence (P2.1)

**Files:**
- Modify: `src/builder/routing/thresholds.py`
- Modify: `src/builder/routing/file_map.py` (os 2 pontos que computam conf de BLOCO)
- Test: `tests/test_thresholds_block_confidence.py` (criar)

- [ ] **Step 1: Testes que falham**:

```python
"""relative_margin_confidence: margem relativa x força absoluta (P2.1)."""
from src.builder.routing.thresholds import relative_margin_confidence, T

def test_nao_satura_com_scores_grandes():
    # bug antigo: (8-2) + 8*0.18 = 7.44 -> 1.0. Agora: rel=0.75, strength=1.0
    c = relative_margin_confidence(8.0, 2.0)
    assert c < 1.0 and abs(c - 0.75) < 0.02

def test_winner_fraco_tem_conf_baixa_mesmo_sem_runner():
    c = relative_margin_confidence(0.5, 0.0)
    assert c < 0.75            # rel=1.0 mas strength baixa segura

def test_empate_da_zero():
    assert relative_margin_confidence(3.0, 3.0) == 0.0

def test_winner_zero_ou_negativo():
    assert relative_margin_confidence(0.0, 0.0) == 0.0
    assert relative_margin_confidence(-1.0, 0.0) == 0.0

def test_monotonica_na_margem():
    assert (relative_margin_confidence(4.0, 1.0)
            > relative_margin_confidence(4.0, 3.0))
```

- [ ] **Step 2:** rodar → FAIL
- [ ] **Step 3: Implementar** em thresholds.py (NÃO tocar `margin_confidence`):

```python
# Score "forte" de bloco: matches genuinos do scorer real ficam >=3.x
# (multiplos sinais somados); calibrado no golden v1 (Task 7/Step 5).
STRONG_SCORE: float = 3.0


def relative_margin_confidence(winner: float, runner_up: float) -> float:
    """Confiança de BLOCO: margem RELATIVA escalada pela força absoluta.

    Substitui margin_confidence SÓ nos caminhos de bloco (a aditiva saturava em
    1.0 com scores 4-8 — 46/56 entries conf=1.0, re-análise 2026-06-11).
    margin_confidence original permanece para unidade/tópico."""
    w = float(winner)
    if w <= 0:
        return 0.0
    rel = (w - max(float(runner_up), 0.0)) / w
    strength = min(1.0, w / STRONG_SCORE)
    return max(0.0, min(1.0, rel * (0.55 + 0.45 * strength)))
```

Trocar nos 2 pontos de file_map.py que computam confiança de BLOCO (localizar
os usos de `margin_confidence` em `select_probable_period_for_entry` e
`_best_instructional_block_fallback`/caminho equivalente — grep
`margin_confidence` em file_map.py e identificar quais são de bloco vs unidade;
os de unidade NÃO mudam).

- [ ] **Step 4:** suíte + harness: `python -m pytest -q` e MEDIR no golden.
  A fixture sintética (5/5 com bands) pode mudar de band — se mudar, atualizar
  `tests/fixtures/eval/assignments_gold.json` JUNTO, justificando no commit.
  Calibrar `STRONG_SCORE` se a distribuição ficar degenerada (tudo alta ou tudo baixa):
  alvo = casos hoje CERTOS majoritariamente alta/média; casos errados deixando a alta.
- [ ] **Step 5: Commit** — `git commit -m "feat(p2): relative_margin_confidence nos caminhos de bloco (mata clamp 1.0)"` (lista de consumidores da Task 6 no corpo)

---

### Task 8: Teto por método + computed_block_method universal (P2.2/P2.3)

**Files:**
- Modify: `src/builder/routing/thresholds.py` (constantes de teto)
- Modify: `src/builder/extraction/content_taxonomy.py` (resolve_unit_block_tags:1055-1135)
- Test: `tests/test_block_method_caps.py` (criar)

- [ ] **Step 1: Testes que falham** — usar o harness sintético como rig (mesmo
  padrão de tests/test_eval_golden_real.py, via importlib de eval_assignments):
  construir golds inline com 2 blocos persistidos e card map em que:

```python
"""Teto de confiança por método + computed_block_method universal (P2.2/P2.3)."""
# (mesmo _pblock/_gold rig de tests/test_eval_golden_real.py — duplicação
#  intencional entre arquivos de teste)
# Casos a cobrir (asserts sobre o manifest de saída de resolve_unit_block_tags,
# chamado pelo predict_block — estender o rig para devolver a entry processada
# ou chamar resolve_unit_block_tags direto com os stubs do harness):

def test_method_card_com_teto():
    # entry com source_section cujo card map tem 1 bloco ->
    # computed_block_method == "card", confidence == 0.85 (CARD_SINGLE_CONF)
    ...

def test_method_scorer_only_com_teto():
    # entry SEM section -> method == "scorer_only", confidence <= 0.70
    ...

def test_method_manual():
    # entry com manual_timeline_block_id -> method == "manual", confidence 1.0
    ...

def test_method_card_scorer():
    # card map com 2 blocos (scorer desempata) -> method == "card+scorer",
    # confidence <= 0.80
    ...
```

(O implementer escreve os corpos com o rig real — chamar `resolve_unit_block_tags`
com os mesmos stubs de `scripts/eval_assignments.py:predict_block` e ler
`computed_block_method`/`computed_block_confidence` do dict de saída. Os stubs
estão prontos no script — importar via importlib como nos outros testes.)

- [ ] **Step 2:** rodar → FAIL
- [ ] **Step 3: Implementar.**

(a) thresholds.py:

```python
# Tetos de confiança por método de atribuição de bloco (P2.2):
# "não há como ter certeza só com léxico" — o teto materializa isso.
METHOD_CAPS: dict = {
    "manual": 1.0,
    "review_rule": 0.95,
    "card": 0.85,          # = CARD_SINGLE_CONF (gabarito 1-bloco)
    "card+scorer": 0.80,
    "scorer_only": 0.70,
}
```

(b) content_taxonomy.py — no fluxo 1055-1124, cada branch já é distinto; capturar
o método numa variável `block_method`:
- `manual_block` → `"manual"`
- `_review_bid` → `"review_rule"`
- `_card_bid` com 1 bloco → `"card"`; com 2+ (o fallback do scorer dentro de
  `_card_scoped_block` decidiu) → `"card+scorer"` — `_card_scoped_block` precisa
  RETORNAR também se foi single ou scoped (mudar retorno para
  `(block_id, conf, "card"|"card+scorer")`; atualizar os 2 call sites)
- scorer/fallback → `"scorer_only"`

Na consolidação (~1135):

```python
        computed_block_id = period_block_id
        cap = METHOD_CAPS.get(block_method, 1.0)
        computed_block_confidence = min(float(block_confidence), cap)
        if computed_block_id:
            entry["computed_block_method"] = block_method
```

ATENÇÃO: o caminho de código (pedagogical_regeneration) JÁ grava
`computed_block_method` = consensus/llm_only DEPOIS — verificar ordem (regeneração
roda depois do retag? ler pedagogical_regeneration.py:115-148) e garantir que o
valor de código não é sobrescrito pelo retag nem vice-versa: regra = código
(consensus/llm_only) vence quando existir; documentar no código.

(c) Editor: conferir que o campo "Match do bloco" (dialogs.py, BacklogEntryEditDialog)
exibe `computed_block_method` para entries não-código (deve, se lê o campo) — ajustar
SÓ se estiver filtrando por categoria de código.

- [ ] **Step 4:** suíte + MEDIR no golden (esperado: confiante-e-errado despenca —
  scorer_only nunca passa de 0.70 < BAND_HIGH? NÃO: 0.70 > 0.50 ainda é alta.
  Se confiante-e-errado não cair ≤2, recalibrar BAND_HIGH para 0.75 nesta task,
  com a fixture sintética atualizada jundo e justificativa).
- [ ] **Step 5: Commit** — `git commit -m "feat(p2): teto por metodo + computed_block_method universal"`

---

### Task 9: B1 — references no filtro (P3.1)

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py:961`
- Test: `tests/test_no_timeline_categories.py` (criar)

- [ ] **Step 1: Teste que falha:**

```python
from src.builder.extraction.content_taxonomy import _NO_TIMELINE_CATEGORIES

def test_references_en_esta_no_filtro():
    assert "references" in _NO_TIMELINE_CATEGORIES
    assert {"cronograma", "bibliografia", "referencias"} <= _NO_TIMELINE_CATEGORIES
```

- [ ] **Step 2-4:** adicionar `"references"` ao set (linha 961); rodar; suíte verde.
  Caso real de regressão: entry categoria `references` não pode receber bloco
  (cobrir com um caso no rig da Task 8 se trivial; senão o assert do set basta).
- [ ] **Step 5: Commit** — `git commit -m "fix(taxonomy): references (EN) no _NO_TIMELINE_CATEGORIES (bug B1)"`

---

### Task 10: B5 — dedup de id no import (P3.2)

**Files:**
- Modify: `src/builder/ops/lifecycle_ops.py` (ponto onde a entry nova entra no manifest, ~linha 58)
- Test: `tests/test_import_id_dedup.py` (criar)

- [ ] **Step 1: Teste que falha** (ler lifecycle_ops.py primeiro para usar a API real
  de import — o implementer adapta o rig ao formato do módulo):

```python
def test_ids_duplicados_ganham_sufixo_de_categoria():
    # importar 2 arquivos de mesmo basename (introducao.pdf) em categorias
    # diferentes -> ids "introducao" e "introducao-codigo-professor"
    ...

def test_mesmo_id_mesma_categoria_ganha_contador():
    # 3o arquivo "introducao.pdf" tambem codigo-professor (outra pasta) ->
    # "introducao-codigo-professor-2"
    ...

def test_reimport_do_mesmo_source_path_nao_duplica():
    # mesmo source_path -> comportamento atual (already_exists) intacto
    ...
```

- [ ] **Step 2:** rodar → FAIL
- [ ] **Step 3: Implementar** em lifecycle_ops, antes de inserir a entry:

```python
def _dedup_entry_id(entry_id: str, category: str, existing_ids: set) -> str:
    """Id colidiu com entry de OUTRO source_path: sufixa categoria, depois contador.

    Ids são diretórios de assets (sobrescrita silenciosa, bug B5) — nunca colidir."""
    if entry_id not in existing_ids:
        return entry_id
    cat = slugify(category or "")
    candidate = f"{entry_id}-{cat}" if cat else f"{entry_id}-2"
    i = 2
    while candidate in existing_ids:
        candidate = f"{entry_id}-{cat}-{i}" if cat else f"{entry_id}-{i}"
        i += 1
    return candidate
```

(usar o slugify já importado no módulo; aplicar SÓ quando source_path difere —
o fluxo already_exists/força-reprocesso atual fica intacto). NÃO retroativo.

- [ ] **Step 4:** suíte verde
- [ ] **Step 5: Commit** — `git commit -m "fix(import): dedup de entry id por categoria/contador (bug B5)"`

---

### Task 11: B4 — verificação retag pós-F1 + MEDIR final + placar

Operacional:

- [ ] **Step 1:** `python scripts/retag_manifest.py` no repo real de MF (conferir
  flags do script antes — `--repo`?). Verificar a entry
  `formalizacaoalgoritmos-recursao`: unit reconciliada com o bloco OU
  `unit_block_conflict` presente. Registrar o resultado.
- [ ] **Step 2:** MEDIR final no golden + atualizar tabela do plano-mestre
  (linhas P1, P2, P3) com os números de cada fase.
- [ ] **Step 3:** Decisão P4 pelos números (registrar recomendação no plano-mestre):
  < 85% → listar os erros restantes e mapear quais P4 resolve.
- [ ] **Step 4:** Suíte completa final `python -m pytest -q` + commit:
  `git commit -m "feat(funil): ciclo P1+P2+P3 fechado (placares no plano-mestre)"`

---

## Self-review (na escrita)

- Spec P1.1-P1.4 → Tasks 1-5; P2.1 → Task 7 (com refinamento da função nova,
  spec atualizada); P2.2/P2.3 → Task 8; P2.4 → Task 6; P2.5 → Tasks 7-8 (MEDIR);
  P3.1 → Task 9; P3.2 → Task 10; P3.3/P3.4 → Task 11. Metas e sequência de MEDIR
  preservadas.
- Tasks 8 e 10 têm esqueletos de teste com `...` de propósito: dependem do rig
  real (stubs do harness / API do lifecycle_ops) — o implementer escreve os
  corpos LENDO os módulos citados; os comportamentos esperados estão
  especificados nos comentários de cada teste. Não é placeholder de
  comportamento, é adaptação de mecânica ao rig.
- Tipos consistentes: `parse_card_dates(contents, year, week_anchor="")` igual
  nas Tasks 1-5; `{"block_ids", "source", "format", "dates"}` igual nas Tasks
  3-5; `METHOD_CAPS`/`block_method` strings iguais nas Tasks 8 e spec.
