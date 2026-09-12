# F5b — Matching Posicional + Delivery-Window Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o provider due-window (TIER 2) atingir 4/8 no gold MF corrigido, casando entry→due por POSIÇÃO na seção Moodle (D-G) e ancorando no último bloco DE CONTEÚDO (D-H/D-I), sem quebrar nada da régua flag-OFF.

**Architecture:** Produtor ganha `extract_file_dues` (posicional: resource herda o due do PRÓXIMO módulo-com-due da seção; keys por filename original E savename, casefolded, ambíguas descartadas) gravado aditivamente no card map como `file_dues`. Motor: `_match_due` tenta `file_dues` por basename do entry ANTES do stem matching (que vira fallback); `resolve_due_window` ganha UM filtro — só blocos com `topics` não-vazio ancoram (containment → band pela fonte; senão último bloco de conteúdo anterior → media+FLAG, branch straddle existente).

**Tech Stack:** Python stdlib puro (re, datetime, collections.Counter, pathlib). pytest. Sem dependência nova.

**Spec:** `docs/superpowers/specs/2026-08-03-janela-de-prazo-f5b-adendo.md` (base: `2026-07-22-janela-de-prazo-tier2-design.md`).

## Global Constraints

- Flag-OFF byte-idêntico: nenhuma mudança de atribuição com `use_anchor_engine` off; probes fase0/1/2/3/4 byte-idênticos.
- `tier2_due_scope` INTOCADO (true-set ⊂ `is_out_of_disamb_scope` é invariante testado).
- `merge_card_block_map`: card `source=="manual"` NUNCA é sobrescrito — `file_dues` segue a mesma regra por construção (nada a mudar no merge).
- D-E intacto: sem due casado → `None` → funil. Provider NUNCA chuta, NUNCA vota LLM.
- Piso da medição: acc ≥ 4/8 E cw == 0 no `scripts/fase5_prova_tier2.py`. FAIL = resultado honesto; PROIBIDO re-tuning para passar régua.
- Medição só com `scripts/audit_gold_freshness.py --course MF` retornando hard=0.
- TDD por task; fixture pode ser ajustada por timezone (precedente F5), implementação NUNCA.
- Legado `extract_assign_deadlines` (colapsada) INTOCADO.

## File Structure

- `src/builder/sources/moodle_labels.py` — ganha `_module_due` (helper extraído da cascata per-módulo já existente em `extract_assign_deadlines_detailed`) e `extract_file_dues` (posicional). Import top-level de `_savename_from_module` (direção labels→moodle já existe: `sanitize_folder_name`).
- `src/builder/sources/moodle.py` — `backfill_repo_signals_consumed` ganha loop `file_dues` espelhando o de `assign_dues`.
- `src/builder/routing/motor/due_window.py` — `_match_due` posicional-first; `resolve_due_window` com filtro bloco-de-conteúdo.
- `tests/test_moodle_assign_dues.py`, `tests/test_motor_due_window.py`, `tests/test_motor_apply.py` — novos testes + fixtures ganham `topics`.

---

### Task 1: Produtor posicional — `extract_file_dues` + wiring no backfill

**Files:**
- Modify: `src/builder/sources/moodle_labels.py` (após `extract_assign_deadlines_detailed`, ~L270)
- Modify: `src/builder/sources/moodle.py` (`backfill_repo_signals_consumed`, ~L502-522)
- Test: `tests/test_moodle_assign_dues.py`

**Interfaces:**
- Consumes: `_savename_from_module(modname, original, n_in_module)` de `src/builder/sources/moodle.py` (já existe); `_DEADLINE_NAME`, `_iso`, `sanitize_folder_name` (já importados/definidos em moodle_labels).
- Produces: `extract_file_dues(contents, year: int = 0) -> dict` retornando `{secao_sanitizada: {key_casefold: {"due": "YYYY-MM-DD", "source": "structured"|"named"}}}`; card map ganha chave `file_dues` por seção (Task 2 consome via `card.get("file_dues")`).

- [ ] **Step 1: Escrever os testes que falham**

Adicionar ao FIM de `tests/test_moodle_assign_dues.py`:

```python
def _contents_posicional():
    """Espelha a seção TDE real do MF: 2 grupos label→resources→assign;
    savenames colidem ('Definição.pdf' 2x), originais são únicos."""
    return [
        {"name": "TDE Trabalho Discente Efetivo", "modules": [
            {"modname": "label", "name": "Trabalho 1 (06/05/2026):"},
            {"modname": "resource", "name": "Definição",
             "contents": [{"type": "file", "filename": "t1_2026_1.pdf", "fileurl": "u"}]},
            {"modname": "resource", "name": "Arquivo .thy",
             "contents": [{"type": "file", "filename": "T1_2026_1.thy", "fileurl": "u"}]},
            {"modname": "assign", "name": "Sala de entrega",
             "dates": [{"dataid": "duedate", "timestamp": 1778122740}]},   # 2026-05-06 local
            {"modname": "label", "name": "Trabalho 2:"},
            {"modname": "resource", "name": "Definição",
             "contents": [{"type": "file", "filename": "t2_2026_1.pdf", "fileurl": "u"}]},
            {"modname": "assign", "name": "Sala de entrega",
             "dates": [{"dataid": "duedate", "timestamp": 1783393140}]},   # 2026-07-06 local
            {"modname": "resource", "name": "Gabarito",
             "contents": [{"type": "file", "filename": "gab.pdf", "fileurl": "u"}]},
        ]},
    ]


def test_file_dues_posicional_resource_herda_proximo_assign():
    from src.builder.sources.moodle_labels import extract_file_dues
    fd = extract_file_dues(_contents_posicional(), year=2026)["TDE Trabalho Discente Efetivo"]
    assert fd["t1_2026_1.pdf"] == {"due": "2026-05-06", "source": "structured"}
    assert fd["t1_2026_1.thy"] == {"due": "2026-05-06", "source": "structured"}
    assert fd["t2_2026_1.pdf"] == {"due": "2026-07-06", "source": "structured"}


def test_file_dues_savename_ambiguo_descartado_originais_ficam():
    from src.builder.sources.moodle_labels import extract_file_dues
    fd = extract_file_dues(_contents_posicional(), year=2026)["TDE Trabalho Discente Efetivo"]
    # savename 'Definição.pdf' aparece nos 2 grupos -> key ambígua NUNCA casa
    assert "definição.pdf" not in fd
    assert "t1_2026_1.pdf" in fd and "t2_2026_1.pdf" in fd


def test_file_dues_arquivo_apos_ultimo_due_fica_fora():
    from src.builder.sources.moodle_labels import extract_file_dues
    fd = extract_file_dues(_contents_posicional(), year=2026)["TDE Trabalho Discente Efetivo"]
    assert "gab.pdf" not in fd


def test_file_dues_secao_sem_modulo_com_due_fica_fora():
    from src.builder.sources.moodle_labels import extract_file_dues
    contents = [{"name": "Materiais", "modules": [
        {"modname": "resource", "name": "Aula",
         "contents": [{"type": "file", "filename": "aula01.pdf", "fileurl": "u"}]},
    ]}]
    assert extract_file_dues(contents, year=2026) == {}


def test_backfill_grava_file_dues_aditivo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    (repo / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": []}), encoding="utf-8")
    backfill_repo_signals_consumed(
        repo, _contents_posicional(), {"name": "MF", "semester": "2026/1"}, write=True)
    card_map = json.loads(
        (repo / "course" / ".card_block_map.json").read_text(encoding="utf-8"))
    entry = card_map["TDE Trabalho Discente Efetivo"]
    assert entry["file_dues"]["t1_2026_1.pdf"]["due"] == "2026-05-06"
    assert entry["assign_dues"]                          # aditivo: não substitui
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_moodle_assign_dues.py -v`
Expected: 5 novos FAIL com `ImportError: cannot import name 'extract_file_dues'`; 4 antigos PASS.

- [ ] **Step 3: Implementar — helper `_module_due` + refactor do detailed + `extract_file_dues`**

Em `src/builder/sources/moodle_labels.py`, trocar o import top-level existente:

```python
from src.builder.sources.moodle import sanitize_folder_name
```

por:

```python
from src.builder.sources.moodle import _savename_from_module, sanitize_folder_name
```

Adicionar ANTES de `extract_assign_deadlines_detailed`:

```python
def _module_due(mod, year: int = 0) -> tuple:
    """Cascata POR MÓDULO: (1) assign com dates[dataid=duedate] -> "structured";
    (2) assign/forum com "entrega" no nome e data `(DD/MM[/AAAA])` -> "named".
    Sem fonte -> ("", "")."""
    from datetime import datetime
    modname = str(mod.get("modname") or "")
    mod_name = str(mod.get("name") or "")
    if modname == "assign":
        for d in mod.get("dates") or []:
            if str(d.get("dataid") or "") == "duedate" and d.get("timestamp"):
                try:
                    return (datetime.fromtimestamp(
                        int(d["timestamp"])).date().isoformat(), "structured")
                except (ValueError, OSError, OverflowError):
                    pass
                break
    if modname in ("assign", "forum") and "entrega" in mod_name.lower():
        m = _DEADLINE_NAME.search(mod_name)
        if m:
            due = _iso(m.group(1), year)
            if due:
                return due, "named"
    return "", ""
```

Reescrever o CORPO do loop de `extract_assign_deadlines_detailed` usando o helper
(comportamento idêntico — os 4 testes existentes provam):

```python
def extract_assign_deadlines_detailed(contents, year: int = 0) -> dict:
    """{secao_sanitizada: [{name, due, source}]} — UM item por módulo, sem colapsar.

    Cascata por módulo em _module_due. Módulo sem fonte fica fora; seção sem
    itens fica fora (nunca inventa). Consumidor: motor/due_window (fallback stem).
    """
    out: dict = {}
    for sec in contents or []:
        name = sanitize_folder_name(str(sec.get("name") or ""))
        if not name:
            continue
        items: list = []
        for mod in sec.get("modules", []) or []:
            due, source = _module_due(mod, year)
            if due:
                items.append({"name": str(mod.get("name") or ""), "due": due,
                              "source": source})
        if items:
            out[name] = items
    return out
```

Adicionar APÓS `extract_assign_deadlines_detailed`:

```python
def extract_file_dues(contents, year: int = 0) -> dict:
    """{secao_sanitizada: {key_casefold: {"due", "source"}}} — posicional (D-G).

    Cada arquivo herda o due do PRÓXIMO módulo-com-due da MESMA seção (grupo
    `label → resources → assign`). Keys: filename original E savename de disco,
    casefolded (mesma convenção do backfill de seções); key com 2+ ocorrências
    na seção é DESCARTADA (nunca chuta). Arquivo sem módulo-com-due depois
    fica fora. Consumidor: motor/due_window (matching posicional)."""
    from collections import Counter
    out: dict = {}
    for sec in contents or []:
        secname = sanitize_folder_name(str(sec.get("name") or ""))
        if not secname:
            continue
        counts: Counter = Counter()
        fdues: dict = {}
        pending: list = []
        for mod in sec.get("modules", []) or []:
            files = [f for f in (mod.get("contents", []) or [])
                     if f.get("type") == "file" and f.get("filename")]
            for f in files:
                original = str(f["filename"])
                save = _savename_from_module(mod.get("name"), original, len(files))
                keys = {original.casefold(), save.casefold()}
                for k in keys:
                    counts[k] += 1
                pending.append(keys)
            due, source = _module_due(mod, year)
            if due:
                for keys in pending:
                    for k in keys:
                        fdues.setdefault(k, {"due": due, "source": source})
                pending = []
        fdues = {k: v for k, v in fdues.items() if counts[k] == 1}
        if fdues:
            out[secname] = fdues
    return out
```

Em `src/builder/sources/moodle.py`, no `backfill_repo_signals_consumed`:
(a) adicionar `extract_file_dues` ao import lazy existente (~L503-506);
(b) adicionar APÓS o loop de `assign_dues` (~L518-522), espelhando-o:

```python
            for _card, _fd in extract_file_dues(contents, year).items():
                if _card in derived:
                    derived[_card]["file_dues"] = _fd
                else:
                    derived[_card] = {"block_ids": [], "source": "labels",
                                      "file_dues": _fd}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_moodle_assign_dues.py tests/test_moodle_labels.py tests/test_moodle.py -v`
Expected: tudo PASS (novos 5 + antigos; refactor do detailed provado pelos 4 existentes). Se algum novo teste falhar SÓ por data deslocada (timezone da máquina), ajustar o timestamp da FIXTURE (precedente F5) — nunca a implementação.

- [ ] **Step 5: Suite completa + commit**

Run: `python -m pytest -q`
Expected: verde (~1811 passed / 4 skipped), saída limpa.

```bash
git add src/builder/sources/moodle_labels.py src/builder/sources/moodle.py tests/test_moodle_assign_dues.py
git commit -m "feat(produtor): extract_file_dues posicional (resource herda o proximo assign da secao) + wiring aditivo no card map (F5b D-G)"
```

---

### Task 2: Motor — matching posicional-first + filtro bloco-de-conteúdo

**Files:**
- Modify: `src/builder/routing/motor/due_window.py`
- Test: `tests/test_motor_due_window.py`
- Test: `tests/test_motor_apply.py` (SÓ fixtures: blocos ganham `topics`)

**Interfaces:**
- Consumes: `card["file_dues"]` no shape da Task 1; `entry["source_path"]` (basename casefolded = mesma chave do produtor); `b["topics"]` dos blocos do `.timeline_index.json` (lista; vazia = bloco administrativo, ex.: dia de prova/devolução).
- Produces: `resolve_due_window(entry, ctx) -> Optional[AnchorDecision]` com semântica D-H/D-I — assinatura, provider ("due-window") e methods ("due-contain"/"due-straddle") INALTERADOS (apply.py não muda).

- [ ] **Step 1: Atualizar fixtures existentes (topics) e escrever os testes novos que falham**

Em `tests/test_motor_due_window.py`:

(a) No helper `_ctx`, dar `"topics": ["t"]` a TODOS os 4 blocos existentes (são blocos de aula nas fixtures; sem isso o filtro D-H os descartaria):

```python
def _ctx(card_map=None):
    blocks = [
        {"id": "bloco-07", "block_uuid": "u07", "period_start": "2026-04-15", "period_end": "2026-04-15", "topics": ["t"]},
        {"id": "bloco-08", "block_uuid": "u08", "period_start": "2026-04-20", "period_end": "2026-04-20", "topics": ["t"]},
        {"id": "bloco-15", "block_uuid": "u15", "period_start": "2026-06-01", "period_end": "2026-06-10", "topics": ["t"]},
        {"id": "bloco-16", "block_uuid": "u16", "period_start": "2026-06-15", "period_end": "2026-06-29", "topics": ["t"]},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=card_map or {}, lessons_index={})
```

(b) No helper `_t`, aceitar `source_path`:

```python
def _t(eid, cat="trabalhos", sec="TDE Trabalho Discente Efetivo", title=None, source_path=""):
    e = {"id": eid, "title": title or eid.replace("-", " "),
         "category": cat, "source_section": sec}
    if source_path:
        e["source_path"] = source_path
    return e
```

(c) Adicionar ao fim do arquivo (espelham o caso real MF pós-correção do gold):

```python
TDE_POSICIONAL = {"TDE Trabalho Discente Efetivo": {
    "block_ids": [], "source": "labels",
    "file_dues": {
        "t1_2026_1.pdf": {"due": "2026-05-06", "source": "structured"},
        "t1_2026_1.thy": {"due": "2026-05-06", "source": "structured"},
        "t2_2026_1.pdf": {"due": "2026-07-06", "source": "structured"},
    },
    # dues SEM stem no nome (realidade MF): fallback stem nunca casa aqui
    "assign_dues": [
        {"name": "Sala de entrega", "due": "2026-05-06", "source": "structured"},
        {"name": "Sala de entrega", "due": "2026-07-06", "source": "structured"},
    ],
}}


def _ctx_mf_real(card_map):
    """Blocos do caso real: 11 (conteúdo, dia-único 06/05), 16 (conteúdo),
    17/18 (administrativos, topics vazio — prova/devolução)."""
    blocks = [
        {"id": "bloco-11", "block_uuid": "u11", "period_start": "2026-05-06", "period_end": "2026-05-06", "topics": ["invariantes"]},
        {"id": "bloco-16", "block_uuid": "u16", "period_start": "2026-06-15", "period_end": "2026-06-29", "topics": ["modelos"]},
        {"id": "bloco-17", "block_uuid": "u17", "period_start": "2026-07-01", "period_end": "2026-07-01", "topics": []},
        {"id": "bloco-18", "block_uuid": "u18", "period_start": "2026-07-06", "period_end": "2026-07-06", "topics": []},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map=card_map, lessons_index={})


def test_posicional_casa_por_filename_e_ancora_containment_alta():
    d = resolve_due_window(
        _t("t1-2026-1", source_path="files/t1_2026_1.pdf"),
        _ctx_mf_real(TDE_POSICIONAL))
    assert d.block_ref == "bloco-11" and d.band == "alta" and not d.flag
    assert d.method == "due-contain"


def test_posicional_companion_thy_casa_igual():
    d = resolve_due_window(
        _t("t1-2026-1-thy", cat="codigo-professor", source_path="files/T1_2026_1.thy"),
        _ctx_mf_real(TDE_POSICIONAL))
    assert d.block_ref == "bloco-11"


def test_due_em_bloco_sem_topicos_cai_no_ultimo_bloco_de_conteudo():
    # due 2026-07-06 CONTIDO no bloco-18 (admin) -> pula 18/17 -> bloco-16, media+FLAG
    d = resolve_due_window(
        _t("t2-2026-1", source_path="files/t2_2026_1.pdf"),
        _ctx_mf_real(TDE_POSICIONAL))
    assert d.block_ref == "bloco-16" and d.band == "media" and d.flag
    assert d.method == "due-straddle"


def test_sem_file_dues_sem_stem_vai_pro_funil():
    # realidade MF pré-Task1: só assign_dues sem stem -> None (nunca chuta)
    so_assign = {"TDE Trabalho Discente Efetivo": {
        "block_ids": [], "source": "labels",
        "assign_dues": TDE_POSICIONAL["TDE Trabalho Discente Efetivo"]["assign_dues"]}}
    assert resolve_due_window(
        _t("t1-2026-1", source_path="files/t1_2026_1.pdf"),
        _ctx_mf_real(so_assign)) is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_motor_due_window.py -v`
Expected: `test_posicional_*` e `test_due_em_bloco_sem_topicos*` FAIL (matching posicional não existe; bloco-18 admin ainda ancora containment); `test_sem_file_dues_sem_stem_vai_pro_funil` já PASS (guard atual); 12 antigos PASS.

- [ ] **Step 3: Implementar em `src/builder/routing/motor/due_window.py`**

(a) Imports — adicionar `Path`:

```python
from pathlib import Path
```

(b) Docstring do módulo — atualizar a linha de semântica:

```python
"""TIER 2 janela-de-prazo: due-date por-assignment -> bloco da entrega.

Spec: 2026-07-22-janela-de-prazo-tier2-design.md + adendo F5b 2026-08-03.
Matching: posicional (file_dues por filename, D-G) com fallback stem (D-C).
Janela (D-H/D-I): só bloco DE CONTEÚDO (topics não-vazio) ancora — containment
-> band pela fonte; senão último bloco de conteúdo anterior -> media+FLAG.
Nunca chuta: sem due casado -> None -> funil. NUNCA disambiguator, NUNCA voto LLM.
"""
```

(c) `_match_due` — posicional primeiro, stem fallback (corpo do fallback é o código ATUAL, inalterado):

```python
def _match_due(entry: dict, ctx: MotorContext) -> Optional[dict]:
    """UM {name, due, source}: posicional (file_dues, D-G) > stem (D-C) > None."""
    card = _card_entry(entry, ctx)
    if card is None:
        return None
    base = Path(str(entry.get("source_path") or "")).name.casefold()
    hit = (card.get("file_dues") or {}).get(base) if base else None
    if isinstance(hit, dict) and str(hit.get("due") or ""):
        return {"name": base, "due": str(hit.get("due")),
                "source": str(hit.get("source") or "")}
    dues = [d for d in (card.get("assign_dues") or [])
            if isinstance(d, dict) and str(d.get("due") or "")]
    if not dues:
        return None
    if len(dues) == 1:
        mine = _stems(f"{entry.get('title') or ''} {entry.get('id') or ''}")
        theirs = _stems(str(dues[0].get("name") or ""))
        if mine and theirs and not (mine & theirs):
            return None  # stem-conflito: extracao parcial nao pode virar chute
        return dues[0]
    mine = _stems(f"{entry.get('title') or ''} {entry.get('id') or ''}")
    if not mine:
        return None
    hits = [d for d in dues if _stems(str(d.get("name") or "")) & mine]
    return hits[0] if len(hits) == 1 else None
```

(Nota: `_card_entry` retornando dict vazio nunca acontece — retorna `None` ou dict do card; o acesso `card.get` é seguro.)

(d) `resolve_due_window` — UMA linha nova no loop (filtro D-H); resto intacto:

```python
    for b in ctx.blocks:  # ordenados por period_start (contrato do MotorContext)
        if not (b.get("topics") or []):
            continue  # D-H: só bloco DE CONTEÚDO ancora entrega (admin/prova fora)
        start = str(b.get("period_start") or "")
        ...
```

- [ ] **Step 4: Rodar due_window + apply e consertar fixtures do apply**

Run: `python -m pytest tests/test_motor_due_window.py tests/test_motor_apply.py -v`
Expected: due_window 16/16 PASS. Se testes tier2 do `test_motor_apply.py` falharem porque os blocos das fixtures não têm `topics` (filtro D-H os descarta), adicionar `"topics": ["t"]` aos blocos DAS FIXTURES desses testes — mudança de fixture, nunca de implementação. Re-rodar até PASS.

- [ ] **Step 5: Suite completa + commit**

Run: `python -m pytest -q`
Expected: verde, saída limpa.

```bash
git add src/builder/routing/motor/due_window.py tests/test_motor_due_window.py tests/test_motor_apply.py
git commit -m "feat(motor): matching posicional file_dues + ancora so em bloco de conteudo (F5b D-G/D-H/D-I; stem vira fallback)"
```

---

### Task 3: Re-sync headless + medição target + régua completa

**Files:**
- Create: `<scratchpad>/resync_mf_f5b.py` (one-off, fora do repo)
- Modify: `docs/reports/pendencias.md` (registro do resultado)

**Interfaces:**
- Consumes: Task 1 no repo (o re-sync grava `file_dues` real no card map do MF via `backfill_repo_signals_consumed`); Task 2 no motor.
- Produces: medição target registrada; nenhum código novo.

- [ ] **Step 1: Pre-gate frescor**

Run: `python scripts/audit_gold_freshness.py --course MF`
Expected: `hard=0` (suspeitas soft ZERO_OVERLAP em PDFs de trabalho são esperadas). hard>0 → PARAR e reportar.

- [ ] **Step 2: Re-sync headless do MF (grava file_dues real)**

Escrever `<scratchpad>/resync_mf_f5b.py`:

```python
import sys
from pathlib import Path
ROOT = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(ROOT))
from src.builder.sources.moodle import (
    MoodleClient, load_moodle_token, parse_moodle_course,
    backfill_repo_signals_consumed,
)
REPO = Path.home() / "Documents" / "GitHub" / "Metodos-Formais-Tutor"
url, tok = load_moodle_token()
client = MoodleClient(url, tok)
courses = client.get_users_courses(client.site_info().get("userid"))
mf = next(c for c in courses if "formais" in str(c.get("fullname") or "").casefold())
info = parse_moodle_course(mf)
contents = client.get_course_contents(mf["id"])
print(backfill_repo_signals_consumed(REPO, contents, info, write=True))
```

Run: `python <scratchpad>/resync_mf_f5b.py`
Expected: `{'sections': 63, 'card_labels': >=7}`. Verificar `file_dues` gravado:

Run: `python -c "import json, pathlib; m = json.loads((pathlib.Path.home() / 'Documents/GitHub/Metodos-Formais-Tutor/course/.card_block_map.json').read_text(encoding='utf-8')); print(json.dumps(m['TDE Trabalho Discente Efetivo'].get('file_dues'), ensure_ascii=False))"`
Expected: keys `t1_2026_1.pdf`/`t1_2026_1.thy` com due `2026-05-06` e `t2_2026_1.pdf` com `2026-07-06`.

- [ ] **Step 3: Medição target**

Run: `python scripts/fase5_prova_tier2.py`
Expected: `modo=target · acc>=4/8 · confident-wrong=0 → PASS` com t1→bloco-11, t1-thy→bloco-11, t2→bloco-16, revisao-p1-gabarito→bloco-07. FAIL → registrar honesto em pendencias e PARAR (proibido re-tuning); NÃO reverter Tasks 1-2.

- [ ] **Step 4: Régua flag-OFF byte-idêntica**

Run (cada um deve manter o resultado da última medição registrada — fase0 82.8%/conten 0/cw 1 · fase1 9/10 · fase2-SO 45.2%/0/0 · fase2-TCC 5/5+83.3%/0 · fase3 lift sem API nova · fase4 det 48/58 cw1):

```bash
python scripts/fase0_prova_motor_MF.py
python scripts/fase1_recall_gate_MF.py
python scripts/fase2_prova_SO.py
python scripts/fase2_prova_TCC.py
python scripts/fase3_prova_LLM_MF.py
python scripts/fase4_prova_D9.py
```

Expected: todos PASS/byte-idênticos. Qualquer drift → PARAR e reportar (não "consertar" probe).

- [ ] **Step 5: Suite + registro + commit**

Run: `python -m pytest -q`
Expected: verde.

Adicionar bullet em `docs/reports/pendencias.md` (seção 2026-08-03, após a entrada da correção do gold): resultado da medição (acc real, cw, modo), confirmação da régua, head dos commits F5b.

```bash
git add docs/reports/pendencias.md
git commit -m "docs(f5b): medicao target pos-F5b registrada (acc X/8, cw=0, regua byte-identica)"
```

---

## Self-Review (executado na escrita)

- **Spec coverage:** D-F (semântica) = premissa das Tasks 2-3; D-G = Task 1 (produtor) + Task 2 (_match_due); D-H/D-I = Task 2 (filtro + branches contain/straddle existentes); §3 verificação = Task 3 Step 3; §4 re-sync = Task 3 Step 2. Sem gap.
- **Placeholders:** nenhum TBD; todo código completo.
- **Type consistency:** `extract_file_dues` → `{sec: {key: {"due","source"}}}` consumido idêntico em `_match_due` (Task 2) e assertado nos testes (Tasks 1-3); methods/bands inalterados → apply.py e probe intocados.
