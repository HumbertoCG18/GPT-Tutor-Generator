# moodle_label por instancename automático + matching robusto — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o `moodle_label` (instancename) e o `posting_date` colarem automaticamente no backfill, robusto à colisão de filename (`main.pdf`/`slides.pdf`), e padronizar datas `DD/MM` com zero-padding.

**Architecture:** Mudança cirúrgica em `src/builder/sources/moodle.py`: (1) um normalizador de data em `sanitize_folder_name` que zero-padda `DD/MM[/YYYY]` só quando o separador é `/`; (2) um índice de `SectionFile` chaveado por savename E filename (unicidade por-key) que os dois backfills aditivos consomem, casando o entry pelo savename sanitizado primeiro. Tudo aditivo — não muda atribuição. O re-sync por fonte é runbook manual pós-merge.

**Tech Stack:** Python 3.11, pytest, stdlib (`re`, `pathlib`, `collections`).

## Global Constraints

- Nova lógica NÃO vai pra `engine.py` (facade). Fica em `src/builder/sources/moodle.py`.
- `google-genai` não envolvido aqui. Sem imports no topo de módulo além dos já presentes.
- Mudança é ADITIVA: `moodle_label`/`posting_date` não entram na atribuição. Eval-gate = `rebuild_diff` idêntico ao baseline (drift pré-existente ES2 7 / IA 20 / SO 13 / MF 1 / TCC 0).
- Comandos rodam de `C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator`. Console Windows: prefixar com `PYTHONIOENCODING=utf-8` quando imprimir UTF-8.
- Casar SEMPRE pelo savename sanitizado, NUNCA pelo instancename cru (que tem `/`).
- Commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## File Structure

- `src/builder/sources/moodle.py` (modify) — `sanitize_folder_name` (date-pad), novo helper `_normalize_date_seps`, novo índice `_section_file_value_index` + `_match_entry_basename`, reescrita de `backfill_moodle_label_from_api` e `backfill_posting_date_from_api`.
- `tests/test_moodle.py` (modify) — testes de `sanitize_folder_name` (date-pad).
- `tests/test_moodle_labels.py` (modify) — testes de matching por savename (colisão `main.pdf`) + fallback por filename, para label e posting_date.

---

### Task 1: Normalização de data com zero-padding em `sanitize_folder_name`

**Files:**
- Modify: `src/builder/sources/moodle.py` (função `sanitize_folder_name`, ~linha 67; adicionar helper `_normalize_date_seps` logo acima)
- Test: `tests/test_moodle.py`

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `sanitize_folder_name(name: str) -> str` com comportamento de data atualizado (zero-pad em `/`-datas). `_normalize_date_seps(name: str) -> str` (helper privado).

- [ ] **Step 1: Ler a função atual antes de editar**

Run: lê `src/builder/sources/moodle.py` linhas 22 e 67-71 (constante `_INVALID` e `sanitize_folder_name`). Confirmar o texto EXATO da primeira linha de `sanitize_folder_name` (a conversão de data atual) para substituí-la sem erro de match.

- [ ] **Step 2: Escrever os testes que falham**

Em `tests/test_moodle.py`, adicionar (importar `sanitize_folder_name` do módulo se ainda não importado):

```python
import pytest
from src.builder.sources.moodle import sanitize_folder_name


@pytest.mark.parametrize("raw, expected", [
    ("20/04 a 24/4", "20.04 a 24.04"),   # zero-pad do mês de 1 dígito
    ("24/4", "24.04"),
    ("06/12/2026", "06.12.2026"),         # data completa, ano preservado
    ("18/06", "18.06"),                    # ja 2-digito: no-op (preserva atual)
    ("1/2", "01.02"),
    ("12/2025", "12.2025"),                # mes/ano: cai no passe generico, sem pad
    ("versao 1.2", "versao 1.2"),          # separador '.' (versao) intacto
    ("2.10.1", "2.10.1"),                  # versao 3-partes intacta
    ("Seção A/B", "Seção A B"),            # '/' nao-data vira espaco (atual)
])
def test_sanitize_folder_name_date_padding(raw, expected):
    assert sanitize_folder_name(raw) == expected
```

- [ ] **Step 3: Rodar o teste e confirmar que falha**

Run: `python -m pytest tests/test_moodle.py -k date_padding -v`
Expected: FAIL nos casos `24/4`→`24.04`, `1/2`→`01.02` (hoje dão `24.4`/`1.2`).

- [ ] **Step 4: Implementar o normalizador de data e religar em `sanitize_folder_name`**

Adicionar acima de `sanitize_folder_name` (após a constante `_INVALID`):

```python
# Datas DD/MM[/YYYY] com separador '/' (convenção de data) -> forma pontilhada
# com dia/mês zero-padded a 2 dígitos. Só age sobre '/', então versão/numeração
# com '.' (ex.: "2.10.1") e "12/2025" (mês/ano, 2º termo 4 dígitos) ficam fora.
_DATE_SLASH_RE = re.compile(r'(?<!\d)(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?!\d)')


def _normalize_date_seps(name: str) -> str:
    def _repl(m):
        head = f"{int(m.group(1)):02d}.{int(m.group(2)):02d}"
        return f"{head}.{m.group(3)}" if m.group(3) else head
    name = _DATE_SLASH_RE.sub(_repl, name)
    # passe genérico: '/' restante entre dígitos (ex.: "12/2025") -> '.', sem pad
    return re.sub(r'(?<=\d)/(?=\d)', '.', name)
```

Trocar a primeira linha de `sanitize_folder_name` (a conversão de data atual) por:

```python
def sanitize_folder_name(name: str) -> str:
    name = _normalize_date_seps(str(name or ""))
    name = _INVALID.sub(" ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "sem-secao"
```

- [ ] **Step 5: Rodar os testes do date-padding e confirmar PASS**

Run: `python -m pytest tests/test_moodle.py -k date_padding -v`
Expected: PASS em todos os casos.

- [ ] **Step 6: Rodar o arquivo inteiro de teste do moodle (regressão local)**

Run: `python -m pytest tests/test_moodle.py tests/test_moodle_labels.py -q`
Expected: PASS. Se algum teste antigo assertava a forma sem-pad (ex.: `"24.4"`), corrigir o esperado para a forma canônica `"24.04"` (o antigo era malformado).

- [ ] **Step 7: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle.py
git commit -m "fix(moodle): zero-pad DD/MM dates in sanitize_folder_name

Datas com separador '/' normalizam para DD.MM[.YYYY] zero-padded; versao
('.') e mes/ano ('12/2025') preservados. Corrige '24/4'->'24.4'.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Matching robusto por savename nos backfills aditivos

**Files:**
- Modify: `src/builder/sources/moodle.py` (`backfill_moodle_label_from_api` ~147-165, `backfill_posting_date_from_api` ~180-198; adicionar helpers `_section_file_value_index` + `_match_entry_basename` acima delas)
- Test: `tests/test_moodle_labels.py`

**Interfaces:**
- Consumes: `iter_section_files(contents) -> List[SectionFile]` (existente; `SectionFile` tem `.filename`, `.disk_name`, `.label`, `.timemodified`, `.timecreated`). `sanitize_folder_name` (Task 1).
- Produces: `backfill_moodle_label_from_api(manifest_entries, contents) -> dict[str,str]` e `backfill_posting_date_from_api(manifest_entries, contents) -> dict[str,dict]` com matching por savename+filename. Helpers `_section_file_value_index(contents, value_fn) -> tuple[dict, Counter]` e `_match_entry_basename(entry, val_by_key, counts) -> value|None`.

- [ ] **Step 1: Escrever os testes que falham**

Em `tests/test_moodle_labels.py`, adicionar:

```python
from src.builder.sources.moodle import (
    backfill_moodle_label_from_api,
    backfill_posting_date_from_api,
)


def _contents_colliding():
    # Dois módulos na mesma seção, ambos 'main.pdf' (colisão), instancenames
    # distintos -> savename desambigua ("Aula 01 - Intro.pdf"/"Aula 02 - Conjuntos.pdf").
    return [{
        "name": "Semana 1",
        "modules": [
            {"name": "Aula 01 - Intro",
             "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u1",
                           "timemodified": 1700000000, "timecreated": 1699999999}]},
            {"name": "Aula 02 - Conjuntos",
             "contents": [{"type": "file", "filename": "main.pdf", "fileurl": "u2",
                           "timemodified": 1700100000, "timecreated": 1700099999}]},
        ],
    }]


def test_label_matches_by_savename_despite_filename_collision():
    contents = _contents_colliding()
    entries = [
        {"id": "e1", "source_path": "/x/Aula 01 - Intro.pdf"},
        {"id": "e2", "source_path": "/x/Aula 02 - Conjuntos.pdf"},
    ]
    labels = backfill_moodle_label_from_api(entries, contents)
    assert labels["e1"] == "Aula 01 - Intro"
    assert labels["e2"] == "Aula 02 - Conjuntos"


def test_posting_date_matches_by_savename_despite_filename_collision():
    contents = _contents_colliding()
    entries = [
        {"id": "e1", "source_path": "/x/Aula 01 - Intro.pdf"},
        {"id": "e2", "source_path": "/x/Aula 02 - Conjuntos.pdf"},
    ]
    posting = backfill_posting_date_from_api(entries, contents)
    assert posting["e1"]["timemodified"] == 1700000000
    assert posting["e2"]["timemodified"] == 1700100000


def test_label_fallback_matches_by_original_filename():
    # Curso M365: o arquivo no repo mantém o nome ORIGINAL (nao o savename).
    contents = [{
        "name": "U1",
        "modules": [
            {"name": "Lógica de Hoare",
             "contents": [{"type": "file", "filename": "hoare.zip", "fileurl": "u",
                           "timemodified": 111, "timecreated": 110}]},
        ],
    }]
    entries = [{"id": "m1", "source_path": "/y/hoare.zip"}]
    labels = backfill_moodle_label_from_api(entries, contents)
    assert labels["m1"] == "Lógica de Hoare"


def test_label_skips_when_both_keys_collide():
    # Sem instancename -> savename = filename = "slides.pdf"; dois módulos colidem
    # nas DUAS keys -> ambíguo -> pulado (segurança preservada).
    contents = [{
        "name": "S",
        "modules": [
            {"name": "", "contents": [{"type": "file", "filename": "slides.pdf", "fileurl": "a"}]},
            {"name": "", "contents": [{"type": "file", "filename": "slides.pdf", "fileurl": "b"}]},
        ],
    }]
    entries = [{"id": "z", "source_path": "/q/slides.pdf"}]
    assert backfill_moodle_label_from_api(entries, contents) == {}
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `python -m pytest tests/test_moodle_labels.py -k "savename or fallback or both_keys" -v`
Expected: FAIL nos dois testes de colisão (`labels=={}`/`posting=={}` hoje, pois `main.pdf` colide e é pulado). `fallback` e `both_keys` podem já passar.

- [ ] **Step 3: Implementar os helpers de índice + match**

Adicionar em `src/builder/sources/moodle.py` ACIMA de `backfill_moodle_label_from_api`:

```python
def _section_file_value_index(contents, value_fn):
    """Indexa SectionFiles por savename (disk_name) E filename original,
    casefolded. value_fn(sf) -> valor ou None. Conta ocorrências por key;
    val_by_key guarda o valor da 1ª ocorrência (quando value_fn != None).
    O chamador só aceita match em key com count == 1 (não-ambígua)."""
    from collections import Counter
    counts = Counter()
    val_by_key = {}
    for sf in iter_section_files(contents):
        v = value_fn(sf)
        for key in {sf.disk_name.casefold(), sf.filename.casefold()}:
            counts[key] += 1
            if v is not None:
                val_by_key.setdefault(key, v)
    return val_by_key, counts


def _match_entry_basename(entry, val_by_key, counts):
    """Casa o basename do source_path do entry contra o índice; só retorna
    valor se a key existir, tiver valor e for única (count == 1)."""
    base = Path(str(entry.get("source_path") or "")).name.casefold()
    if base in val_by_key and counts[base] == 1:
        return val_by_key[base]
    return None
```

- [ ] **Step 4: Reescrever os dois backfills usando os helpers**

Substituir `backfill_moodle_label_from_api` por:

```python
def backfill_moodle_label_from_api(manifest_entries, contents):
    """Casa entries -> label do recurso Moodle (mod.name) por savename
    (instancename) com fallback no filename original. Retorna {id->moodle_label}.
    Keys ambíguas (count>1 nas duas formas) são puladas."""
    val_by_key, counts = _section_file_value_index(
        contents, lambda sf: sf.label or None)
    out = {}
    for e in manifest_entries or []:
        v = _match_entry_basename(e, val_by_key, counts)
        if v is not None:
            eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
            out[eid] = v
    return out
```

Substituir `backfill_posting_date_from_api` por:

```python
def backfill_posting_date_from_api(manifest_entries, contents):
    """Casa entries -> {timemodified, timecreated} por savename com fallback no
    filename. Keys ambíguas puladas."""
    def _ts(sf):
        if sf.timemodified or sf.timecreated:
            return {"timemodified": sf.timemodified, "timecreated": sf.timecreated}
        return None
    val_by_key, counts = _section_file_value_index(contents, _ts)
    out = {}
    for e in manifest_entries or []:
        v = _match_entry_basename(e, val_by_key, counts)
        if v is not None:
            eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
            out[eid] = v
    return out
```

- [ ] **Step 5: Rodar os novos testes e confirmar PASS**

Run: `python -m pytest tests/test_moodle_labels.py -k "savename or fallback or both_keys" -v`
Expected: PASS nos quatro.

- [ ] **Step 6: Rodar a suíte do moodle inteira (regressão)**

Run: `python -m pytest tests/test_moodle.py tests/test_moodle_labels.py tests/test_fileentry_roundtrip.py -q`
Expected: PASS. Os testes antigos de backfill (que usavam basename único) continuam casando pela key filename.

- [ ] **Step 7: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_moodle_labels.py
git commit -m "fix(moodle): match backfill por savename (instancename), resolve colisao main.pdf

backfill_moodle_label/posting_date indexam por disk_name (savename sanitizado)
+ fallback filename, unicidade por-key. TCC (todo recurso main.pdf) passa a
colar o label. Aditivo, nao muda atribuicao.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Eval-gate (suíte completa + golden + rebuild_diff idêntico)

**Files:**
- Nenhum (verificação). Sem código novo.

**Interfaces:**
- Consumes: o estado pós-Task 2.
- Produces: confirmação de que a mudança é aditiva (atribuição inalterada).

- [ ] **Step 1: Capturar o baseline do rebuild_diff ANTES (referência)**

Run: `python scripts/rebuild_diff.py`
Expected: drift pré-existente ES2 7 / IA 20 / SO 13 / MF 1 / TCC 0 (anotar a saída exata).

> Nota: como o código mudou mas NENHUM repo foi re-sincronizado ainda, este passo só confirma que a mudança de código por si não altera o `rebuild_diff` (ele lê manifests/timeline existentes; label/posting não entram na atribuição).

- [ ] **Step 2: Rodar o golden de atribuição**

Run: `python scripts/eval_assignments.py`
Expected: 5/5, confiante-errado 0 (inalterado).

- [ ] **Step 3: Rodar a suíte completa**

Run: `python -m pytest tests -q`
Expected: verde (baseline 1483 + os novos testes das Tasks 1-2; sem regressões).

- [ ] **Step 4: Confirmar rebuild_diff idêntico ao Step 1**

Run: `python scripts/rebuild_diff.py`
Expected: saída IDÊNTICA à do Step 1. Se divergir, a mudança não foi aditiva — investigar (provável: date-padding alterou um nome usado na rota de card) ANTES de prosseguir.

---

### Task 4: Runbook de re-sync por fonte (MANUAL, pós-merge, requer usuário)

**Files:**
- Nenhum código. Operação sobre os repos reais em `C:\Users\Humberto\Documents\GitHub\*-Tutor`.

> Esta task NÃO é TDD. É um runbook a executar com o usuário DEPOIS do merge das Tasks 1-3, repo por repo, revisando o `rebuild_diff` antes de aceitar cada um. NÃO auto-commitar os repos gerados.

- [ ] **Step 1: Re-sync dos cursos Moodle (TCC, IA, SO)**

Para cada um, rodar o import com download (salva em `<seção>/<instancename>` + backfill aditivo cola label/posting). Confirmar caminho exato do entrypoint de import com o usuário (`import_moodle_courses(download=True)` via app ou script equivalente). IA deve puxar os ~50 arquivos faltantes; conferir `failed` no retorno (redirects M365/HTML caem ali).

- [ ] **Step 2: Backfill aditivo nos cursos M365 (MF, ES2)**

Rodar o backfill aditivo contra o conteúdo do Moodle (sem re-download) para capturar `posting_date` (+ label onde o filename casa). Comando: `python -m scripts.migrate_signals --write` no repo (já additive, com `.apibak`), confirmando que usa `backfill_repo_signals_additive`.

- [ ] **Step 3: Verificar cobertura pós-sync**

Conferir no `manifest.json` de cada repo que `moodle_label`/`posting_date` subiram (especialmente TCC: alvo 24/24; IA: completo). Rodar `python -m scripts.moodle_probe --course <id>` (read-only) para comparar seções/arquivos Moodle × repo.

- [ ] **Step 4: Eval-gate por repo + regenerar gold**

Para cada repo re-sincronizado: `python scripts/rebuild_diff.py` (revisar deltas — re-import pode mudar cards; aceitar só se compreensível), golden 5/5, e regenerar `python -m scripts.gold_by_card "<repo>" "docs/reports/gold_templates/gold_by_card_<curso>.csv"` (agora com label/seção limpos). Rotulagem do gold e baseline cross-curso = pendência do usuário (destrava o eval-gate do A1).

---

## Self-Review

**1. Spec coverage:**
- Fix A (matching por savename) → Task 2. ✓
- Fix 1b (date zero-padding só em `/`) → Task 1. ✓
- Re-sync por fonte (Moodle TCC/IA/SO; M365 MF/ES2) → Task 4. ✓
- Testes (colisão main.pdf, fallback filename, date-pad) → Tasks 1-2. ✓
- Eval-gate (rebuild_diff idêntico, golden 5/5, suíte) → Task 3. ✓
- Não-objetivo (source_section matching fora) → respeitado (Tasks só tocam label/posting aditivos + sanitize). ✓

**2. Placeholder scan:** sem TBD/TODO; todo step de código tem o código. Task 4 é runbook operacional declarado como manual (não TDD), com comandos concretos — não é placeholder.

**3. Type consistency:** `_section_file_value_index(contents, value_fn) -> (val_by_key, counts)` e `_match_entry_basename(entry, val_by_key, counts) -> value|None` usados consistentemente nos dois backfills. `SectionFile.disk_name`/`.filename`/`.label`/`.timemodified`/`.timecreated` batem com a definição em `moodle.py:104-115`. `sanitize_folder_name`/`_normalize_date_seps` consistentes entre Tasks 1 e 2.
