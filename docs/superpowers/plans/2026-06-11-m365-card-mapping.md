# M365 Card Mapping via API Moodle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Arquivo baixado do M365 cai no card da seção REAL da API Moodle (basename→seção); chute léxico (`match_card`) morre; filtro é persistido e validado.

**Architecture:** `section_file_index_strict` (moodle.py) produz `{basename→seção}` só para basenames não-ambíguos; `download_subject_m365` (m365.py) consulta esse índice por arquivo resolvido — hit = card real + `source_section`; miss/ambíguo/Moodle-off = pasta literal do OneDrive com `matched=False` e aviso. A UI constrói o índice dos contents que já busca e persiste o `m365_filter` no perfil certo via `find_subject_for_course` (lookup id→slug→nome extraído do upsert existente).

**Tech Stack:** Python 3.13, pytest, tkinter (UI), Microsoft Graph (mockado em teste).

**Spec:** `docs/superpowers/specs/2026-06-11-m365-card-mapping-design.md`

---

### Task 1: `section_file_index_strict` em moodle.py

**Files:**
- Modify: `src/builder/sources/moodle.py` (após `section_file_index`, ~linha 138)
- Test: `tests/test_m365_card_mapping.py` (criar)

- [ ] **Step 1: Escrever testes que falham**

Criar `tests/test_m365_card_mapping.py`:

```python
"""Testes do mapeamento de card M365 pela API Moodle (spec 2026-06-11)."""
from src.builder.sources.moodle import section_file_index_strict

def _contents(*secs):
    """secs: (nome_secao, [filenames]) -> payload core_course_get_contents."""
    return [
        {"name": nome, "modules": [
            {"name": f"mod {f}", "contents": [
                {"type": "file", "filename": f, "fileurl": f"https://x/{f}"}]}
            for f in files]}
        for nome, files in secs
    ]

def test_strict_index_maps_unique_basenames():
    idx, amb = section_file_index_strict(_contents(
        ("Verificação de Programas", ["LogicaDeHoare.pdf", "hoare.zip"]),
        ("Provas por Indução", ["intro.thy"]),
    ))
    assert idx["logicadehoare.pdf"] == "Verificação de Programas"
    assert idx["intro.thy"] == "Provas por Indução"
    assert amb == set()

def test_strict_index_excludes_ambiguous_basenames():
    idx, amb = section_file_index_strict(_contents(
        ("Seção A", ["Respostas.pdf"]),
        ("Seção B", ["Respostas.pdf"]),
    ))
    assert "respostas.pdf" not in idx
    assert amb == {"respostas.pdf"}

def test_strict_index_same_section_twice_is_not_ambiguous():
    idx, amb = section_file_index_strict(_contents(
        ("Seção A", ["x.pdf", "x.pdf"]),
    ))
    assert idx["x.pdf"] == "Seção A"
    assert amb == set()

def test_strict_index_empty_contents():
    idx, amb = section_file_index_strict(None)
    assert idx == {} and amb == set()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_m365_card_mapping.py -q`
Expected: FAIL — `ImportError: cannot import name 'section_file_index_strict'`

- [ ] **Step 3: Implementar em moodle.py (logo após `section_file_index`, ~linha 138)**

```python
def section_file_index_strict(contents) -> tuple:
    """({basename.casefold(): secao} só de basenames únicos, {ambíguos}).

    Basename presente em >1 seção sai do dict — ambíguo é miss e o chamador
    decide o fallback (cf. spec 2026-06-11-m365-card-mapping)."""
    secs: dict = {}
    for sf in iter_section_files(contents):
        secs.setdefault(sf.filename.casefold(), set()).add(sf.section)
    index = {k: next(iter(v)) for k, v in secs.items() if len(v) == 1}
    ambiguous = {k for k, v in secs.items() if len(v) > 1}
    return index, ambiguous
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_m365_card_mapping.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_m365_card_mapping.py
git commit -m "feat(moodle): section_file_index_strict (basename->secao, ambiguos fora)"
```

---

### Task 2: `find_subject_for_course` em moodle.py (extraído do upsert)

**Files:**
- Modify: `src/builder/sources/moodle.py:300-311` (loop de match dentro de `import_moodle_courses`)
- Test: `tests/test_m365_card_mapping.py` (append)

- [ ] **Step 1: Testes que falham**

Append em `tests/test_m365_card_mapping.py`:

```python
from src.builder.sources.moodle import find_subject_for_course

class _FakeProfile:
    def __init__(self, name, slug="", moodle_course_id=""):
        self.name = name; self.slug = slug; self.moodle_course_id = moodle_course_id

class _FakeStore:
    def __init__(self, *profiles):
        self._d = {p.name: p for p in profiles}
    def names(self): return sorted(self._d)
    def get(self, name): return self._d.get(name)

_COURSE = {"id": 92717, "fullname":
           "4646M-04 - Métodos Formais para Computação - Turma 031 - 2026/1 - Prof. Julio Machado"}

def test_find_subject_by_moodle_course_id_wins():
    a = _FakeProfile("Metodos-Formais", slug="metodos_formais", moodle_course_id="92717")
    b = _FakeProfile("Métodos Formais para Computação", slug="metodos-formais-para-computacao")
    assert find_subject_for_course(_FakeStore(a, b), _COURSE) is a

def test_find_subject_by_slug_when_no_id():
    b = _FakeProfile("Outro Nome", slug="metodos-formais-para-computacao")
    assert find_subject_for_course(_FakeStore(b), _COURSE) is b

def test_find_subject_falls_back_to_name():
    c = _FakeProfile("Métodos Formais para Computação")
    assert find_subject_for_course(_FakeStore(c), _COURSE) is c

def test_find_subject_none_when_no_match():
    assert find_subject_for_course(_FakeStore(_FakeProfile("X")), _COURSE) is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_m365_card_mapping.py -q`
Expected: FAIL — ImportError `find_subject_for_course`

- [ ] **Step 3: Implementar e refatorar o upsert**

Em moodle.py, ANTES de `import_moodle_courses`:

```python
def find_subject_for_course(store, course):
    """Acha o SubjectProfile da matéria: moodle_course_id > slug > nome.

    Mesma precedência do upsert de import_moodle_courses; usado também pela UI
    (persistir m365_filter no perfil certo — antes o lookup por nome falhava
    em silêncio quando o nome do store divergia do nome vindo do Moodle)."""
    info = parse_moodle_course(course)
    cid = info["moodle_course_id"]
    match_by_slug = None
    for n in store.names():
        sp = store.get(n)
        if not sp:
            continue
        if cid and getattr(sp, "moodle_course_id", "") == cid:
            return sp
        if not match_by_slug and getattr(sp, "slug", "") and sp.slug == info["slug"]:
            match_by_slug = sp
    return match_by_slug or store.get(info["name"])
```

Em `import_moodle_courses`, substituir as linhas 300-311 (de `# --- upsert` até o
fim do `for n in store.names():` com seus dois `if`) por:

```python
        # --- upsert (id -> slug -> create) ---
        sp = find_subject_for_course(store, course)
        match_by_id = sp if (sp is not None and cid and getattr(sp, "moodle_course_id", "") == cid) else None
        match_by_slug = sp if (sp is not None and match_by_id is None and getattr(sp, "slug", "") == info["slug"]) else None
```

ATENÇÃO: o comportamento original NÃO tem fallback por nome no upsert (cria perfil
novo se id/slug não casam). `find_subject_for_course` tem. Para preservar o upsert:
`match_by_id`/`match_by_slug` derivados acima reproduzem o original — perfil achado
só por NOME cai no `else` (cria) como antes. Os branches `if match_by_id ... elif
match_by_slug ... else` existentes ficam intactos.

- [ ] **Step 4: Rodar testes (novos + suíte moodle)**

Run: `python -m pytest tests/test_m365_card_mapping.py tests/test_moodle*.py -q`
Expected: tudo verde (se `tests/test_moodle*.py` não existir, rodar só o primeiro)

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/moodle.py tests/test_m365_card_mapping.py
git commit -m "feat(moodle): find_subject_for_course (id>slug>nome) reutilizado no upsert"
```

---

### Task 3: Reescrever `download_subject_m365` — índice no lugar do léxico

**Files:**
- Modify: `src/builder/sources/m365.py` (remover `_DEFAULT_ALIASES` :32-38, `_ascii_lower` :65-66, `_norm_tokens` :69-70, `_token_affinity` :73-81, `match_card` :84-98; reescrever `download_subject_m365` :222-281; adicionar `filter_in_path` após `subfolder_for`)
- Modify: `tests/test_m365.py` (remover testes léxicos; reescrever testes de download)
- Test: `tests/test_m365_card_mapping.py` (append)

- [ ] **Step 1: Testes novos que falham**

Append em `tests/test_m365_card_mapping.py`:

```python
from pathlib import Path
from src.builder.sources.m365 import download_subject_m365, filter_in_path

_BASE = "https://brpucrs-my.sharepoint.com/personal/p/Documents/Documentos/metodosformais"

class _FakeM365:
    """Client M365 fake: items de list_shared + bytes por nome."""
    def __init__(self, items, blobs):
        self._items, self._blobs = items, blobs
    def list_shared(self, top=200): return self._items
    def resolve(self, iid):
        it = next(i for i in self._items if i["id"] == iid)
        return {"name": it["title"], "id": iid, "parentReference": {"driveId": "D"}}
    def download(self, item): return self._blobs[item["name"]]

def _item(iid, title, sub=""):
    url = f"{_BASE}/{sub}/{title}" if sub else f"{_BASE}/{title}"
    return {"id": iid, "title": title, "type": "Pdf", "web_url": url}

def test_index_hit_beats_onedrive_folder(tmp_path):
    """O caso real do bug: pasta OneDrive 'logica' mas seção API = Verificação."""
    client = _FakeM365([_item("1", "LogicaDeHoare.pdf", "logica")],
                       {"LogicaDeHoare.pdf": b"%PDF-1.7 ok"})
    idx = {"logicadehoare.pdf": "Verificação de Programas"}
    rep = download_subject_m365(client, "metodosformais", idx, tmp_path)
    assert (tmp_path / "Verificação de Programas" / "LogicaDeHoare.pdf").exists()
    assert not (tmp_path / "logica").exists()
    assert rep["mapping"] == [("LogicaDeHoare.pdf", "Verificação de Programas", "moodle_api")]
    assert rep["name_to_section"]["logicadehoare.pdf"] == "Verificação de Programas"

def test_index_miss_falls_back_to_literal_folder(tmp_path):
    client = _FakeM365([_item("1", "extra.pdf", "dafny")], {"extra.pdf": b"%PDF-1.7 ok"})
    rep = download_subject_m365(client, "metodosformais", {"outro.pdf": "X"}, tmp_path)
    assert (tmp_path / "dafny" / "extra.pdf").exists()
    assert rep["mapping"] == [("extra.pdf", "dafny", "fallback_pasta")]
    assert rep["name_to_section"] == {}          # chute NUNCA vira source_section

def test_empty_index_means_all_fallback_with_warning(tmp_path):
    client = _FakeM365([_item("1", "a.pdf", "dafny")], {"a.pdf": b"%PDF-1.7 ok"})
    rep = download_subject_m365(client, "metodosformais", {}, tmp_path)
    assert (tmp_path / "dafny" / "a.pdf").exists()
    assert rep["name_to_section"] == {}
    assert any("Moodle" in w for w in rep["warnings"])

def test_zero_items_aborts_with_warning(tmp_path):
    client = _FakeM365([], {})
    rep = download_subject_m365(client, "naoexiste", {}, tmp_path)
    assert rep["total"] == 0 and rep["downloaded"] == 0
    assert any("filtro" in w for w in rep["warnings"])

def test_filter_not_in_path_majority_warns(tmp_path):
    items = [_item("1", "a.pdf", "dafny"),
             {"id": "2", "title": "b.pdf", "type": "Pdf",
              "web_url": "https://x/y/metodosformais.pdf"}]   # filtro só no NOME
    client = _FakeM365(items, {"a.pdf": b"%PDF-1.7 ok", "b.pdf": b"%PDF-1.7 ok"})
    rep = download_subject_m365(client, "metodosformais", {}, tmp_path)
    # 1 de 2 com filtro fora do caminho de pastas: 50% não dispara (>50% dispara)
    assert not any("caminho" in w for w in rep["warnings"])

def test_filter_in_path():
    assert filter_in_path(f"{_BASE}/dafny/a.pdf", "metodosformais") is True
    assert filter_in_path("https://x/y/z.pdf", "metodosformais") is False

def test_lexical_matching_is_dead():
    import src.builder.sources.m365 as m
    for nome in ("match_card", "_token_affinity", "_norm_tokens", "_DEFAULT_ALIASES"):
        assert not hasattr(m, nome), f"{nome} deveria ter sido removido"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_m365_card_mapping.py -q`
Expected: FAIL — ImportError `filter_in_path` (e teste de limpeza falha enquanto match_card existir)

- [ ] **Step 3: Implementar em m365.py**

(a) Remover os blocos: `_DEFAULT_ALIASES` (linhas 32-38), `_ascii_lower`,
`_norm_tokens`, `_token_affinity`, `match_card` (linhas 65-98). O import
`unicodedata` (linha 14) e `re` (linha 12) ficam SÓ se ainda usados — conferir
com grep após a remoção e limpar imports órfãos.

(b) Adicionar após `subfolder_for` (~linha 56):

```python
def filter_in_path(web_url: str, m365_filter: str) -> bool:
    """True se o filtro casa algum segmento do CAMINHO (não só o nome do arquivo)."""
    fl = (m365_filter or "").lower()
    segs = parse_onedrive_path(web_url)
    return any(fl and fl in s.lower() for s in segs[:-1]) if segs else False
```

(c) Substituir `download_subject_m365` (linhas 222-281) por:

```python
def download_subject_m365(client, m365_filter, section_index, dest,
                          skip_existing: bool = True, progress_cb=None) -> dict:
    """Baixa os arquivos M365 da matéria pros cards das seções REAIS do Moodle.

    section_index: {basename.casefold(): secao} de section_file_index_strict —
    a ÚNICA fonte de card. Miss/ambíguo/índice vazio => subpasta literal do
    OneDrive (ou _geral) com matched=False; NUNCA match léxico (a spec
    2026-06-11 matou o match_card: pasta-tópico do professor não é card).

    Retorna {total, downloaded, failed, mapping: [(basename, card, origem)],
             name_to_section (só origem moodle_api), warnings: [str]}.
    """
    dest = Path(dest)
    index = {str(k).casefold(): v for k, v in (section_index or {}).items()}
    items = select_for_subject(client.list_shared(), m365_filter)
    total = len(items)
    warnings: list = []
    if not items:
        warnings.append(
            "filtro não casou nenhum item compartilhado — confira a grafia "
            "(o filtro é substring da URL do OneDrive, sem espaços/acentos)")
        log.warning(warnings[-1])
        return {"total": 0, "downloaded": 0, "failed": [], "mapping": [],
                "name_to_section": {}, "warnings": warnings}
    misses = sum(1 for it in items if not filter_in_path(it.get("web_url", ""), m365_filter))
    if misses * 2 > total:
        warnings.append(
            f"filtro não aparece no caminho de pastas de {misses}/{total} arquivos — "
            "layout pode cair todo em _geral")
    if not index:
        warnings.append(
            "API Moodle indisponível ou sem arquivos no curso — nenhum card "
            "atribuído pela API; arquivos ficam nas pastas literais do OneDrive")
    log.info("filtro '%s': %d item(ns) -> %s", m365_filter, total, dest)
    downloaded, failed = 0, []
    mapping: list = []
    name_to_section: dict = {}
    seen: set = set()
    for idx, it in enumerate(items):
        try:
            res = client.resolve(it["id"])
            raw_name = res.get("name") or it.get("title") or "arquivo"
            name = sanitize_folder_name(raw_name)
            data = client.download(res)
        except Exception:
            log.exception("falha ao baixar item %r", it.get("title") or it.get("id"))
            failed.append(it.get("title") or it.get("id"))
            continue
        if not looks_like_expected(name, data):
            log.warning("magic-byte inválido, pulando: %s (%d bytes)", name, len(data))
            failed.append(name)
            continue
        section = index.get(name.casefold(), "")
        if section:
            card, origem = section, "moodle_api"
        else:
            card, origem = subfolder_for(it.get("web_url", ""), m365_filter), "fallback_pasta"
        card = sanitize_folder_name(card) or _ROOT_CARD
        if progress_cb:
            progress_cb(idx + 1, total, name, card)
        folder = dest / card
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / name
        if target in seen:                       # colisão intra-execução
            stem, suf = target.stem, target.suffix
            i = 2
            while (folder / f"{stem} ({i}){suf}") in seen:
                i += 1
            target = folder / f"{stem} ({i}){suf}"
        seen.add(target)
        mapping.append((target.name, card, origem))
        if origem == "moodle_api":
            name_to_section[target.name.casefold()] = section
        if skip_existing and target.exists():
            log.info("já existe, pulando: %s/%s", card, target.name)
            continue
        target.write_bytes(data)
        downloaded += 1
        log.info("baixado: %s/%s (%d bytes)", card, target.name, len(data))
    log.info("concluído: %d baixados, %d falhas, %d aviso(s)",
             downloaded, len(failed), len(warnings))
    return {"total": total, "downloaded": downloaded, "failed": failed,
            "mapping": mapping, "name_to_section": name_to_section,
            "warnings": warnings}
```

Nota: a decisão do card mudou de ANTES do download (por URL) para DEPOIS do
resolve (precisa do basename pro índice). `progress_cb` mantém assinatura
`(done, total, name, card)`.

(d) Atualizar `tests/test_m365.py`:
- REMOVER: `test_match_card_matches_by_normalized_tokens`,
  `test_match_card_falls_back_to_new_card_when_no_match`,
  `test_match_card_uses_aliases_extra_tokens`,
  `test_download_subject_m365_default_aliases_fold_tools` e o
  `from src.builder.sources.m365 import match_card` (linha 30) +
  `_SECTIONS` (linhas 32-33).
- `test_download_subject_m365_merges_cards_and_validates`: trocar
  `sections = [...]` + chamada por índice:

```python
    section_index = {"hoare.pdf": "Verificação de Programas",
                     "hoare.zip": "Verificação de Programas"}
    rep = download_subject_m365(FakeClient(), "metodosformais", section_index, tmp_path)
```

  As asserções existentes continuam válidas (Hoare.pdf e hoare.zip caem em
  "Verificação de Programas" — agora via índice; `ruim.pdf` segue em failed;
  `name_to_section["hoare.pdf"]` segue "Verificação de Programas").
- `test_download_subject_m365_no_collision_loss`: trocar `[]` (3º arg) por
  `{"main.pdf": "Provas por Indução"}` e ajustar asserts de caminho:

```python
    rep = download_subject_m365(FakeClient(), "metodosformais",
                                {"main.pdf": "Provas por Indução"}, tmp_path)
    assert rep["downloaded"] == 2
    assert (tmp_path / "Provas por Indução" / "main.pdf").exists()
    assert (tmp_path / "Provas por Indução" / "main (2).pdf").exists()
    assert "main.pdf" in rep["name_to_section"]
    assert "main (2).pdf" in rep["name_to_section"]
```

- `test_download_subject_m365_sanitizes_invalid_card_and_filename`: trocar
  `sections = ["Lógica: Programas/Hoare"]` por
  `section_index = {"logica hoare.pdf": "Lógica: Programas/Hoare"}` — ATENÇÃO:
  o resolve devolve `"Logica: Hoare.pdf"` que sanitiza para outro nome; o
  índice deve casar o nome SANITIZADO. Conferir o output real de
  `sanitize_folder_name("Logica: Hoare.pdf")` ao implementar e usar essa chave
  casefolded no índice do teste. A asserção de ausência de `:` no caminho fica.

- [ ] **Step 4: Rodar tudo do módulo**

Run: `python -m pytest tests/test_m365.py tests/test_m365_card_mapping.py -q`
Expected: tudo verde; `grep -r "match_card" src/` vazio

- [ ] **Step 5: Commit**

```bash
git add src/builder/sources/m365.py tests/test_m365.py tests/test_m365_card_mapping.py
git commit -m "feat(m365): card via section_index da API Moodle; match_card lexico removido"
```

---

### Task 4: UI — índice, persistência do filtro, resumo com avisos

**Files:**
- Modify: `src/ui/dialogs.py:1947-1978` (bloco `elif m365_client:` do `worker()`)

Sem teste automatizado (diálogo tkinter; padrão do arquivo). Validação manual na Task 5.

- [ ] **Step 1: Reescrever o bloco**

Substituir as linhas 1948-1978 (do `try:` interno até a atribuição de
`m365_tail` no final do bloco `elif m365_client:`) por:

```python
                try:
                    from src.builder.sources import m365
                    from src.builder.sources.moodle import (
                        parse_moodle_course, section_file_index_strict, find_subject_for_course,
                    )
                    self._busy("Listando arquivos do OneDrive...")
                    cid0 = str(selected[0].get("id") or "")
                    try:
                        contents0 = self._client.get_course_contents(cid0) or []
                    except Exception:
                        logging.getLogger("m365").exception("contents Moodle indisponível p/ índice M365")
                        contents0 = []
                    section_index, _ambiguous = section_file_index_strict(contents0)
                    info0 = parse_moodle_course(selected[0])
                    mdest = Path(self._base) / info0["slug"]

                    def _pcb(done, total, name, card):
                        self._progress_to(done, total, f"M365 {done}/{total}: {name} → {card}")

                    mrep = m365.download_subject_m365(
                        m365_client, m365_filter, section_index, mdest, progress_cb=_pcb)
                    sp0 = find_subject_for_course(store, selected[0])
                    if sp0 and getattr(sp0, "m365_filter", "") != m365_filter:
                        sp0.m365_filter = m365_filter
                        store.add(sp0)
                    filtro_txt = "" if sp0 else "\nAVISO: perfil da matéria não encontrado — filtro M365 não salvo."
                    repo_root = getattr(sp0, "repo_root", "") if sp0 else ""
                    backf = m365.apply_source_section(repo_root, mrep["name_to_section"]) if repo_root else 0
                    api_n = sum(1 for _b, _c, o in mrep["mapping"] if o == "moodle_api")
                    fallback = [b for b, _c, o in mrep["mapping"] if o == "fallback_pasta"]
                    fb_txt = (f"\nFallback — sem seção na API ({len(fallback)}): "
                              f"{', '.join(fallback[:8])}{' …' if len(fallback) > 8 else ''}"
                              if fallback else "")
                    warn_txt = "".join(f"\nAVISO: {w}" for w in (mrep.get("warnings") or []))
                    multi = ("  (M365 aplicado só à 1ª matéria — o filtro é por matéria; "
                             "reimporte cada uma separadamente)" if len(selected) > 1 else "")
                    m365_tail = (f"\n\nM365 [{info0['name']}] — baixados: {mrep['downloaded']}  "
                                 f"falhas: {len(mrep['failed'])}  cards pela API: {api_n}  "
                                 f"source_section: {backf}{multi}{fb_txt}{warn_txt}{filtro_txt}")
                except Exception as exc:
                    import logging
                    logging.getLogger("m365").exception("Falha no import M365")
                    m365_tail = f"\n\nM365 indisponível: {str(exc)[:160]}\n(detalhes/traceback no terminal)"
```

ATENÇÃO: o bloco original define `sections` num loop sobre TODOS os cursos
selecionados (linhas 1952-1957) — esse loop morre. `import logging` no topo do
`except` já existe no original; dentro do `try` usar `logging` requer o import
no escopo — adicionar `import logging` no início do `worker()` (linha ~1901,
junto de `store = SubjectStore()`) e remover os `import logging` locais dos
`except` do worker.

- [ ] **Step 2: Sanidade de import**

Run: `python -c "import src.ui.dialogs"`
Expected: sem erro

- [ ] **Step 3: Commit**

```bash
git add src/ui/dialogs.py
git commit -m "feat(ui): import M365 usa section_index real, persiste filtro por id/slug, resumo com avisos"
```

---

### Task 5: Suíte completa + verificação final

- [ ] **Step 1: Suíte inteira**

Run: `python -m pytest -q`
Expected: tudo verde (baseline pré-mudança: 1218 passed; agora 1218 − 4 removidos + 15 novos ≈ 1229)

- [ ] **Step 2: Limpeza confirmada**

Run: `python -X utf8 -c "import src.builder.sources.m365 as m; assert not hasattr(m, 'match_card'); print('lexico morto')"`
Run (grep): confirmar `match_card` sem hits em `src/`
Expected: "lexico morto"; grep vazio

- [ ] **Step 3: Smoke manual (opcional, requer tokens)**

Abrir o app → Importar Moodle com M365 ligado e filtro `metodos` → conferir no
resumo: "cards pela API: N" > 0 e fallback listado. Sem token M365 válido, pular.

- [ ] **Step 4: Commit final (se sobrou ajuste)**

```bash
git add -A
git commit -m "test(m365): suite verde pos-reescrita do mapeamento de card"
```

---

## Self-review (feito na escrita)

- Spec §1 (assinatura nova + remoções) → Task 3. §2 (índice estrito) → Task 1.
  §3 (`apply_source_section` só verdade) → Task 3 (name_to_section filtrado na
  origem; função intocada). §4 (persistência filtro) → Tasks 2+4. §5 (validação
  filtro) → Task 3 (warnings). §6 (Moodle off) → Tasks 3+4 (contents0=[] →
  índice vazio → warning). §7 (UI resumo) → Task 4. Testes da spec 1-8 →
  Tasks 1 e 3 (o nº 7 "0 itens aborta" e "maioria _geral" estão em Task 3).
- Tipos consistentes: `section_index: dict[str,str]`; `mapping: list[tuple[str,str,str]]`;
  retorno com `warnings` novo em todos os pontos de uso (UI lê com `.get`).
- Sem placeholders; código completo em cada step.
