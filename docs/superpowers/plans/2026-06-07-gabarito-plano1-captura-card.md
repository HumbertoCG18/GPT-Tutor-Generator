# Gabarito Plano 1 — Captura do card (source_section + import do stash) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capturar o card de origem de cada arquivo: novo campo `FileEntry.source_section` + import ciente de pasta-card que lê `<stash>/<card>/<arquivos>` e atribui `source_section = <card>`.

**Architecture:** Scanner puro (`scan_stash_cards`) percorre a árvore do stash e classifica cada arquivo (card, file_type, categoria). Builder puro (`build_stash_entries`) transforma o resultado em `FileEntry`s idempotentes (dedup por `source_path`). A UI (`import_from_stash`) é uma casca fina sobre os dois — toda a lógica testável vive nos módulos puros. Sem regressão: arquivos soltos na raiz do stash viram `source_section=""` e seguem o caminho lexical atual.

**Tech Stack:** Python 3.11/3.13, pytest, dataclasses, Tkinter (só na casca da UI).

**Fonte:** `docs/superpowers/specs/2026-06-07-gabarito-cards-pasta-design.md` (componentes 1 e 2).

---

## File Structure

- `src/models/core.py` — adiciona campo `FileEntry.source_section: str = ""` (round-trip via `to_dict`/`from_dict` já genéricos).
- `src/builder/core/stash_import.py` (NOVO) — módulo puro: `StashItem`, `StashScanResult`, `scan_stash_cards(stash_root)`, `build_stash_entries(scan, existing_source_paths, defaults)`. Sem dependência de Tkinter.
- `src/ui/app.py` — `_stash_dir_from_active_subject()` + `import_from_stash()` + botão "📥 Importar do stash". Casca fina.
- `tests/test_core.py` — round-trip de `source_section`.
- `tests/test_stash_import.py` (NOVO) — scanner sobre árvore-fixture + builder (idempotência, categoria, file_type, card).

---

## Task 1: Campo `FileEntry.source_section`

**Files:**
- Modify: `src/models/core.py:86` (após `computed_block_band`)
- Test: `tests/test_core.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao fim de `tests/test_core.py`:

```python
def test_file_entry_source_section_roundtrip():
    from src.models.core import FileEntry
    e = FileEntry(
        source_path="/x/Verificacao de Programas/hoare.zip",
        file_type="zip",
        category="codigo-professor",
        title="hoare",
        source_section="Verificacao de Programas",
    )
    d = e.to_dict()
    assert d["source_section"] == "Verificacao de Programas"
    back = FileEntry.from_dict(d)
    assert back.source_section == "Verificacao de Programas"


def test_file_entry_source_section_defaults_empty():
    from src.models.core import FileEntry
    e = FileEntry(source_path="/x/a.pdf", file_type="pdf", category="material-de-aula", title="a")
    # default vazio nao deve poluir o dict serializado
    assert "source_section" not in e.to_dict()
    assert FileEntry.from_dict(e.to_dict()).source_section == ""
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python -m pytest tests/test_core.py::test_file_entry_source_section_roundtrip tests/test_core.py::test_file_entry_source_section_defaults_empty -v`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'source_section'`

- [ ] **Step 3: Adicionar o campo**

Em `src/models/core.py`, logo após a linha `computed_block_band: str = ""` (linha 86):

```python
    # Card/seção de origem do arquivo (= subpasta imediata no stash). Sinal
    # autoritativo para a atribuição file->bloco (gabarito-cards). "" quando o
    # arquivo nao veio de um card (cai no caminho lexical, sem regressao).
    source_section: str = ""
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python -m pytest tests/test_core.py::test_file_entry_source_section_roundtrip tests/test_core.py::test_file_entry_source_section_defaults_empty -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Rodar a suíte de core completa**

Run: `python -m pytest tests/test_core.py -q`
Expected: tudo verde (contagem antiga + 2)

- [ ] **Step 6: Commit**

```bash
git add src/models/core.py tests/test_core.py
git commit -m "feat(model): add FileEntry.source_section (card origin)"
```

---

## Task 2: Scanner puro do stash (`scan_stash_cards`)

**Files:**
- Create: `src/builder/core/stash_import.py`
- Test: `tests/test_stash_import.py`

**Contrato:** percorre `stash_root` recursivamente. Para cada arquivo, `card_name` = nome do primeiro componente abaixo de `stash_root` quando o arquivo está numa subpasta; `""` quando está direto na raiz. Classifica `file_type` por extensão; extensões desconhecidas vão para `skipped` (não viram entry). `category` via `auto_detect_category` (reuso — já mapeia código/provas/listas/gabaritos/etc).

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_stash_import.py`:

```python
from pathlib import Path
from src.builder.core.stash_import import scan_stash_cards, StashItem


def _make_tree(root: Path):
    (root / "Verificacao de Programas").mkdir(parents=True)
    (root / "Verificacao de Programas" / "hoare.pdf").write_text("x", encoding="utf-8")
    (root / "Verificacao de Programas" / "hoare.zip").write_bytes(b"PK\x03\x04")
    (root / "Introducao").mkdir()
    (root / "Introducao" / "slides.pdf").write_text("x", encoding="utf-8")
    (root / "Introducao" / "foto.png").write_bytes(b"\x89PNG")
    (root / "solto.pdf").write_text("x", encoding="utf-8")
    (root / "leiame.txt").write_text("x", encoding="utf-8")  # ext desconhecida


def test_scan_groups_files_by_immediate_card(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}

    assert by_name["hoare.pdf"].card_name == "Verificacao de Programas"
    assert by_name["hoare.pdf"].file_type == "pdf"
    assert by_name["hoare.zip"].card_name == "Verificacao de Programas"
    assert by_name["hoare.zip"].file_type == "zip"
    assert by_name["slides.pdf"].card_name == "Introducao"
    assert by_name["foto.png"].file_type == "image"
    assert by_name["foto.png"].category == "fotos-de-prova"


def test_scan_root_level_file_has_empty_card(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    by_name = {Path(i.source_path).name: i for i in res.items}
    assert by_name["solto.pdf"].card_name == ""


def test_scan_skips_unknown_extensions(tmp_path):
    _make_tree(tmp_path)
    res = scan_stash_cards(tmp_path)
    names = {Path(i.source_path).name for i in res.items}
    assert "leiame.txt" not in names
    assert any(Path(p).name == "leiame.txt" for p in res.skipped)


def test_scan_missing_root_returns_empty(tmp_path):
    res = scan_stash_cards(tmp_path / "nao-existe")
    assert res.items == []
    assert res.skipped == []
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_stash_import.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.builder.core.stash_import'`

- [ ] **Step 3: Implementar o scanner**

Criar `src/builder/core/stash_import.py`:

```python
"""Import ciente de pasta-card a partir do stash da matéria.

Convenção: ``<stash>/<card>/<arquivos>``. A subpasta imediata é o card
(seção do Moodle feita pelo professor) — sinal autoritativo para a
atribuição file->bloco. Arquivos soltos na raiz do stash ficam sem card
(``card_name=""``) e seguem o caminho lexical atual.

Módulo PURO: sem Tkinter, sem I/O além de varrer o filesystem.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from src.utils.helpers import CODE_EXTENSIONS, auto_detect_category

# Extensões de imagem suportadas pela importação (espelha os filtros da UI).
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".gif"}


@dataclass
class StashItem:
    source_path: str
    card_name: str
    file_type: str   # "pdf" | "image" | "zip" | "code"
    category: str


@dataclass
class StashScanResult:
    items: List[StashItem] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)  # paths de ext. desconhecida


def _classify_file_type(ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext == ".zip":
        return "zip"
    if ext in CODE_EXTENSIONS:
        return "code"
    return ""  # desconhecido -> skip


def _card_for(path: Path, root: Path) -> str:
    """Nome do primeiro componente abaixo de root; "" se o arquivo está na raiz."""
    rel_parts = path.relative_to(root).parts
    return rel_parts[0] if len(rel_parts) > 1 else ""


def scan_stash_cards(stash_root) -> StashScanResult:
    root = Path(stash_root)
    result = StashScanResult()
    if not root.is_dir():
        return result
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        ftype = _classify_file_type(path.suffix)
        if not ftype:
            result.skipped.append(str(path))
            continue
        # .zip = código do professor por convenção (fica dentro do card);
        # demais tipos usam a heurística de nome existente.
        if ftype == "zip":
            category = "codigo-professor"
        else:
            category = auto_detect_category(path.name, is_image=(ftype == "image"))
        result.items.append(StashItem(
            source_path=str(path),
            card_name=_card_for(path, root),
            file_type=ftype,
            category=category,
        ))
    return result
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_stash_import.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/stash_import.py tests/test_stash_import.py
git commit -m "feat(stash): pure card-aware stash scanner"
```

---

## Task 3: Builder puro de entries (`build_stash_entries`, idempotente)

**Files:**
- Modify: `src/builder/core/stash_import.py`
- Test: `tests/test_stash_import.py`

**Contrato:** transforma `StashScanResult` em `FileEntry`s. Pula itens cujo `source_path` já existe (idempotência por path absoluto). Carimba `source_section = card_name`, `category`, `file_type`, `title = stem`. Aplica defaults de processamento passados pelo chamador (modo/ocr) — sem acoplar à UI.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tests/test_stash_import.py`:

```python
from src.builder.core.stash_import import build_stash_entries
from src.models.core import FileEntry


def test_build_entries_stamps_source_section_and_category(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    entries = build_stash_entries(scan, existing_source_paths=set(),
                                  defaults={"processing_mode": "auto", "ocr_language": "por"})
    by_name = {Path(e.source_path).name: e for e in entries}
    assert by_name["hoare.zip"].source_section == "Verificacao de Programas"
    assert by_name["hoare.zip"].category == "codigo-professor"
    assert by_name["hoare.zip"].file_type == "zip"
    assert by_name["hoare.zip"].title == "hoare"
    assert by_name["hoare.zip"].processing_mode == "auto"
    assert by_name["hoare.zip"].ocr_language == "por"
    assert all(isinstance(e, FileEntry) for e in entries)


def test_build_entries_is_idempotent_by_source_path(tmp_path):
    _make_tree(tmp_path)
    scan = scan_stash_cards(tmp_path)
    already = {i.source_path for i in scan.items if Path(i.source_path).name == "hoare.pdf"}
    entries = build_stash_entries(scan, existing_source_paths=already, defaults={})
    names = {Path(e.source_path).name for e in entries}
    assert "hoare.pdf" not in names      # já existia -> pulado
    assert "hoare.zip" in names          # novo -> incluído
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_stash_import.py::test_build_entries_stamps_source_section_and_category tests/test_stash_import.py::test_build_entries_is_idempotent_by_source_path -v`
Expected: FAIL — `ImportError: cannot import name 'build_stash_entries'`

- [ ] **Step 3: Implementar o builder**

Adicionar ao fim de `src/builder/core/stash_import.py` (e incluir o import no topo):

```python
from src.models.core import FileEntry


def build_stash_entries(scan: StashScanResult, existing_source_paths, defaults=None) -> List[FileEntry]:
    """Converte itens varridos em FileEntry, pulando paths já presentes."""
    existing = set(existing_source_paths or set())
    defaults = defaults or {}
    entries: List[FileEntry] = []
    for item in scan.items:
        if item.source_path in existing:
            continue
        entries.append(FileEntry(
            source_path=item.source_path,
            file_type=item.file_type,
            category=item.category,
            title=Path(item.source_path).stem,
            source_section=item.card_name,
            processing_mode=defaults.get("processing_mode", "auto"),
            ocr_language=defaults.get("ocr_language", "por"),
        ))
    return entries
```

Nota: mover o `from src.models.core import FileEntry` para o bloco de imports no topo do arquivo (logo abaixo do import de helpers) para manter o estilo.

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_stash_import.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add src/builder/core/stash_import.py tests/test_stash_import.py
git commit -m "feat(stash): build idempotent FileEntries from card scan"
```

---

## Task 4: Casca da UI — ação "Importar do stash"

**Files:**
- Modify: `src/ui/app.py:1574` (após `add_images`, antes de `add_url`) e `src/ui/app.py:349` (wiring do botão)

**Nota:** UI Tkinter não é coberta por teste unitário neste projeto; toda a lógica testável já vive em `stash_import`. Esta task é só a casca (ler stash da matéria ativa, chamar os puros, anexar, salvar fila). O reviewer confere que a casca delega aos puros e não duplica lógica.

- [ ] **Step 1: Adicionar helper + método na classe da app**

Em `src/ui/app.py`, inserir após o fim de `add_images` (linha ~1574):

```python
    def _stash_dir_from_active_subject(self) -> Optional[Path]:
        name = self._var_active_subject.get()
        if not name or name == "(nenhuma)":
            return None
        sp = self.subject_store.get(name)
        if not sp or not getattr(sp, "stash_folder", ""):
            return None
        p = Path(sp.stash_folder)
        return p if p.is_dir() else None

    def import_from_stash(self):
        from src.builder.core.stash_import import scan_stash_cards, build_stash_entries
        stash = self._stash_dir_from_active_subject()
        if stash is None:
            messagebox.showinfo(
                APP_NAME,
                "Defina a 'Pasta de arquivos (stash)' da matéria ativa no "
                "Gerenciador de Matérias (e selecione a matéria no topo)."
            )
            return
        scan = scan_stash_cards(stash)
        if not scan.items:
            messagebox.showinfo(APP_NAME, f"Nenhum arquivo importável em:\n{stash}")
            return
        existing = {e.source_path for e in self.entries}
        new_entries = build_stash_entries(
            scan, existing_source_paths=existing,
            defaults={
                "processing_mode": self.var_default_mode.get(),
                "ocr_language": self.var_default_ocr_language.get(),
            },
        )
        if not new_entries:
            messagebox.showinfo(APP_NAME, "Todos os arquivos do stash já estão na lista.")
            return
        self.entries.extend(new_entries)
        self.refresh_tree()
        self._save_current_queue()
        skipped_note = f" ({len(scan.skipped)} ignorado(s) por extensão)" if scan.skipped else ""
        self._set_status(f"{len(new_entries)} arquivo(s) importado(s) do stash{skipped_note}. {len(self.entries)} na lista.")
```

- [ ] **Step 2: Wire do botão**

Em `src/ui/app.py:349` (bloco `import_actions`, junto dos outros botões de import), adicionar:

```python
        ttk.Button(import_actions, text="📥 Importar do stash", command=self.import_from_stash).grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
```

(Ajustar `row`/`column` para uma célula livre do grid `import_actions` se a indicada estiver ocupada — manter o padrão dos botões vizinhos.)

- [ ] **Step 3: Smoke import do módulo da app**

Run: `python -c "import src.ui.app"`
Expected: sem erro (import resolve; sintaxe ok)

- [ ] **Step 4: Suíte completa**

Run: `python -m pytest -q`
Expected: tudo verde (sem regressão)

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py
git commit -m "feat(ui): 'Importar do stash' action (card-aware import)"
```

---

## Notas de execução

- Hook `code-review-graph.exe` imprime `UnicodeEncodeError` cosmético no commit; o commit passa — ignorar.
- Trailer obrigatório: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Não reprocessar repositórios reais como efeito colateral.
- Plano 2 (uso + medição: `resolve_card_to_block`, `.card_block_map.json`, telinha de confirmação, atribuição determinística, medição vs baseline 62,5%/11-confident-wrong) é esforço separado, após este.
