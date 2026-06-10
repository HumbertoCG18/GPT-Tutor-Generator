from __future__ import annotations

import json
import logging
import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional

from src.builder.timeline.classifier import classify_block
from src.builder.timeline.curation import apply_block_curation, set_block_override
from src.builder.timeline.kinds import KIND_DISPLAY, BlockKind
from src.builder.timeline.status import derive_block_status
from src.models.core import SubjectProfile
from src.ui.theme import apply_theme_to_toplevel

logger = logging.getLogger(__name__)

# status derivado -> chave da paleta do tema (cor do badge).
_STATUS_COLOR = {
    "ok": "success",
    "needs_topic": "warning",
    "needs_unit": "error",
    "needs_files": "error",
    "needs_review": "warning",
    "non_applicable": "muted",
}

# rotulo PT-BR curto por status (tooltip/badge).
_STATUS_LABEL = {
    "ok": "OK",
    "needs_topic": "sem tópico",
    "needs_unit": "sem unidade",
    "needs_files": "sem material",
    "needs_review": "revisar",
    "non_applicable": "—",
}


def _kind_display(kind_value: str) -> dict:
    """Lookup seguro em KIND_DISPLAY a partir do valor string do kind."""
    try:
        return KIND_DISPLAY[BlockKind(kind_value)]
    except (ValueError, KeyError):
        return {"icon": "❓", "label": str(kind_value or "—"), "color": "yellow"}

_DATE_PREFIX_RE = re.compile(r"^(\d{1,2})\.(\d{2})\s+")

_ID_NUM_RE = re.compile(r"(\d+)$")


def timeline_sort_key(block: dict, column: str) -> tuple:
    """Chave de ordenacao por coluna para as linhas-pai (blocos) na Treeview.

    Valores ausentes vao para o fim de forma estavel (primeiro elemento 0/1).

    Mapeamento de campos reais (schema v4):
      - "#"       -> sufixo numerico do campo `id` (ex: "bloco-10" -> 10)
      - "Data"    -> `period_start` (ISO YYYY-MM-DD, ordena lexicalmente)
      - "Tipo"    -> `kind`
      - "Unidade" -> `unit_slug`
      - "Arq."    -> `_file_count` (injetado pela view antes de ordenar)
    """
    if column == "Data":
        raw = str(block.get("period_start") or "").strip()
        return (1, "") if not raw else (0, raw)
    if column == "#":
        block_id = str(block.get("id") or "")
        m = _ID_NUM_RE.search(block_id)
        return (1, 0) if not m else (0, int(m.group(1)))
    if column == "Arq.":
        count = block.get("_file_count")
        return (1, 0) if count is None else (0, int(count))
    if column == "Tipo":
        val = str(block.get("kind") or "").strip()
        return (1, "") if not val else (0, val)
    if column == "Unidade":
        val = str(block.get("unit_slug") or "").strip()
        return (1, "") if not val else (0, val)
    return (0, str(block.get("id") or ""))


def load_timeline_data(
    manifest_path: Path,
    timeline_index_path: Path,
) -> tuple[list[dict], dict[str, list[dict]], list[dict]]:
    """Returns (blocks, entries_by_block_id, unmapped_entries)."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    timeline = json.loads(timeline_index_path.read_text(encoding="utf-8"))

    blocks: list[dict] = list(timeline.get("blocks") or [])
    entries: list[dict] = list(manifest.get("entries") or [])

    # Merge dos overrides manuais (curation) pra refletir reclassificacao antes
    # do reprocesso. kind e re-derivado live via classify_block; topic manual
    # promove o label diretamente.
    apply_block_curation(blocks, timeline_index_path.parent)
    for block in blocks:
        manual_topic = str(block.get("manual_topic_label") or "").strip()
        if manual_topic:
            block["primary_topic_label"] = manual_topic
        manual_unit = str(block.get("block_manual_unit_slug") or "").strip()
        if manual_unit:
            block["unit_slug"] = manual_unit

    block_ids = {b["id"] for b in blocks if b.get("id")}
    entries_by_block_id: dict[str, list[dict]] = {b["id"]: [] for b in blocks if b.get("id")}
    unmapped: list[dict] = []

    # FONTE ÚNICA da precedência manual>auto (spec Fase 4): a mesma função que
    # cronograma_health usa, eliminando o leitor divergente que vivia aqui.
    from src.builder.routing.file_map import resolve_effective_block

    for entry in entries:
        assigned_id = resolve_effective_block(entry, blocks).block_id
        if assigned_id and assigned_id in block_ids:
            entries_by_block_id[assigned_id].append(entry)
        else:
            unmapped.append(entry)

    return blocks, entries_by_block_id, unmapped


def save_block_assignment(
    manifest_path: Path,
    entry_id: str,
    block_id: Optional[str],
) -> None:
    """Persiste manual_timeline_block_id no manifest. block_id=None remove o campo."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in data.get("entries") or []:
        if entry.get("id") == entry_id:
            if block_id:
                entry["manual_timeline_block_id"] = block_id
            else:
                entry.pop("manual_timeline_block_id", None)
            break
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_block_kind_override(
    course_dir: Path,
    block_id: str,
    kind_value: Optional[str],
) -> None:
    """Persiste reclassificação manual de kind em curation.
    kind_value vazio/None remove o override (volta pro classifier automático)."""
    set_block_override(course_dir, block_id, "manual_kind_override", kind_value or None)


def save_block_unit_override(
    course_dir: Path,
    block_id: str,
    unit_slug: Optional[str],
) -> None:
    """Persiste atribuição manual de unidade em curation.
    unit_slug vazio/None remove o override (volta pro matcher automático)."""
    set_block_override(course_dir, block_id, "manual_unit_slug", unit_slug or None)


def save_block_scope_override(
    course_dir: Path,
    block_id: str,
    unit_slugs: Optional[list],
) -> None:
    """Persiste o override manual de escopo de prova/revisão.
    Lista vazia/None remove o override (volta ao escopo derivado por data)."""
    set_block_override(
        course_dir, block_id, "manual_scope_unit_slugs", list(unit_slugs or []) or None
    )


def block_kind(block: dict) -> str:
    """kind efetivo do bloco (honra manual_kind_override via classifier)."""
    return classify_block(block).value


def _block_scope_slugs(block: dict) -> list[str]:
    """Escopo efetivo de um bloco de prova/revisão para exibição.

    Override manual (`block_manual_scope_slugs`) vence; senão usa o escopo
    derivado por data (`scope_unit_slugs`) gravado no último build.
    """
    manual = block.get("block_manual_scope_slugs")
    if manual:
        return [str(s).strip() for s in manual if str(s).strip()]
    derived = block.get("scope_unit_slugs") or []
    return [str(s).strip() for s in derived if str(s).strip()]


class ScopeEditDialog(tk.Toplevel):
    """Dialogo modal: marca/desmarca unidades no escopo de uma prova/revisão.

    Lista vazia ao salvar remove o override (volta ao escopo derivado por data).
    """

    def __init__(
        self,
        parent: tk.Widget,
        unit_slugs: list[str],
        current_scope: list[str],
        on_save: Callable[[list[str]], None],
    ):
        super().__init__(parent)
        self.title("Escopo manual")
        self._on_save = on_save
        self._vars: dict[str, tk.IntVar] = {}

        p = apply_theme_to_toplevel(self, parent)
        self.configure(bg=p["bg"])
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)

        tk.Label(
            self,
            text="Unidades cobertas por este bloco:",
            bg=p["bg"],
            fg=p["fg"],
            font=("", 10, "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 6))

        if not unit_slugs:
            tk.Label(
                self,
                text="Nenhuma unidade disponível.\nSalvar remove o override (volta ao escopo por data).",
                bg=p["bg"],
                fg=p["muted"],
                font=("", 9),
                justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 8))
        else:
            current = set(current_scope or [])
            body = tk.Frame(self, bg=p["bg"])
            body.pack(fill="both", expand=True, padx=12)
            for slug in unit_slugs:
                var = tk.IntVar(value=1 if slug in current else 0)
                self._vars[slug] = var
                tk.Checkbutton(
                    body,
                    text=slug,
                    variable=var,
                    bg=p["bg"],
                    fg=p["fg"],
                    selectcolor=p["input_bg"],
                    activebackground=p["bg"],
                    activeforeground=p["accent"],
                    anchor="w",
                    font=("", 9),
                    bd=0,
                    highlightthickness=0,
                ).pack(fill="x", anchor="w")

        btns = tk.Frame(self, bg=p["bg"])
        btns.pack(fill="x", padx=12, pady=12)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right", padx=(4, 0))
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="right")

        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()
        self.focus_set()

    def _ok(self) -> None:
        selected = [slug for slug, var in self._vars.items() if var.get()]
        try:
            self._on_save(selected)
        finally:
            self.destroy()


class TimelineDashboardView(tk.Frame):
    """Embeddable timeline dashboard como tabela ttk.Treeview editável.

    Pass a callable that returns the active subject.
    """

    # colunas extra (alem da arvore #0)
    _COLUMNS = ("incluir", "seq", "tipo", "unidade", "escopo", "arq")
    # mapeamento coluna-treeview -> coluna de ordenacao (timeline_sort_key)
    _SORT_COLUMN = {
        "#0": "Data",
        "seq": "#",
        "tipo": "Tipo",
        "unidade": "Unidade",
        "arq": "Arq.",
    }

    def __init__(
        self,
        parent: tk.Widget,
        get_subject_fn: Callable[[], Optional[SubjectProfile]],
        enqueue_reprocess_fn: Callable[[], None],
    ):
        super().__init__(parent)
        self._get_subject_fn = get_subject_fn
        self._enqueue_reprocess_fn = enqueue_reprocess_fn
        self._subject: Optional[SubjectProfile] = None
        self._repo_root: Optional[Path] = None
        self._dirty = False

        # estado de ordenacao: (coluna_sort, ascending)
        self._sort_state: tuple[str, bool] = ("Data", True)
        # iid (treeview) -> block_id
        self._iid_to_block: dict[str, str] = {}
        # iid (treeview, linha filha) -> entry_id
        self._iid_to_entry: dict[str, str] = {}
        # editor inline ativo (combobox sobreposta)
        self._editor: Optional[ttk.Combobox] = None

        p = apply_theme_to_toplevel(self, parent)
        self._p = p
        self.configure(bg=p["bg"])

        self._build_toolbar(p)
        self._build_filter_holder(p)
        self._build_table(p)
        self._build_unmapped_table(p)
        self.refresh()

    def refresh(self) -> None:
        """Re-read active subject and reload UI. Safe to call after subject change."""
        self._subject = self._get_subject_fn()
        self._repo_root = (
            Path(self._subject.repo_root)
            if self._subject and getattr(self._subject, "repo_root", "")
            else None
        )
        self._dirty = False
        if hasattr(self, "_btn_reprocess"):
            self._btn_reprocess.pack_forget()
        self._reload()

    # ------------------------------------------------------------------ toolbar

    def _build_toolbar(self, p: dict) -> None:
        bar = tk.Frame(self, bg=p["header_bg"], pady=4)
        bar.pack(fill="x", side="top")

        self._repo_label_var = tk.StringVar(value="Repositório: —")
        tk.Label(
            bar,
            textvariable=self._repo_label_var,
            bg=p["header_bg"],
            fg=p["muted"],
            font=("", 10),
        ).pack(side="left", padx=10)

        self._btn_reprocess = ttk.Button(
            bar,
            text="🔄 Reprocessar",
            command=self._on_reprocess,
        )
        self._btn_reprocess.pack(side="right", padx=6)
        self._btn_reprocess.pack_forget()  # oculto até primeira atribuição

        ttk.Button(bar, text="↺ Recarregar", command=self.refresh).pack(side="right", padx=4)

    # ---------------------------------------------------------------- filter bar

    def _build_filter_holder(self, p: dict) -> None:
        # container persistente; o conteudo (checkboxes) e reconstruido em _render
        self._filter_bar = tk.Frame(self, bg=p["frame_bg"])
        self._filter_bar.pack(fill="x", side="top")

    # ---------------------------------------------------------------- main table

    def _build_table(self, p: dict) -> None:
        container = tk.Frame(self, bg=p["bg"])
        container.pack(fill="both", expand=True)
        self._table_container = container

        tree = ttk.Treeview(
            container,
            columns=self._COLUMNS,
            show="tree headings",
        )
        self._tree = tree

        headings = {
            "#0": "Data · Bloco/tópico",
            "incluir": "✓",
            "seq": "#",
            "tipo": "Tipo",
            "unidade": "Unidade",
            "escopo": "Escopo",
            "arq": "Arq.",
        }
        for col, text in headings.items():
            sort_col = self._SORT_COLUMN.get(col)
            if sort_col:
                tree.heading(col, text=text, command=lambda c=sort_col: self._sort_by(c))
            else:
                tree.heading(col, text=text)

        tree.column("#0", width=340, minwidth=180, anchor="w", stretch=True)
        tree.column("incluir", width=36, minwidth=30, anchor="center", stretch=False)
        tree.column("seq", width=44, minwidth=36, anchor="e", stretch=False)
        tree.column("tipo", width=110, minwidth=80, anchor="w", stretch=False)
        tree.column("unidade", width=180, minwidth=100, anchor="w", stretch=False)
        tree.column("escopo", width=200, minwidth=100, anchor="w", stretch=True)
        tree.column("arq", width=48, minwidth=40, anchor="e", stretch=False)

        # striping de linhas
        tree.tag_configure("odd", background=p.get("treeview_odd", p["bg"]))
        tree.tag_configure("even", background=p.get("treeview_even", p["frame_bg"]))
        tree.tag_configure("child", foreground=p["muted"])

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        tree.bind("<Double-1>", self._on_tree_double_click)

    def _build_unmapped_table(self, p: dict) -> None:
        holder = tk.Frame(self, bg=p["frame_bg"])
        holder.pack(fill="x", side="bottom")
        self._unmapped_holder = holder

        self._unmapped_label_var = tk.StringVar(value="")
        self._unmapped_label = tk.Label(
            holder,
            textvariable=self._unmapped_label_var,
            bg=p["frame_bg"],
            fg=p["warning"],
            font=("", 10, "bold"),
            anchor="w",
        )

        ucontainer = tk.Frame(holder, bg=p["bg"])
        self._unmapped_container = ucontainer

        utree = ttk.Treeview(
            ucontainer,
            columns=("acao",),
            show="tree headings",
            height=5,
        )
        self._unmapped_tree = utree
        utree.heading("#0", text="Arquivo sem bloco")
        utree.heading("acao", text="Atribuir a bloco (duplo clique)")
        utree.column("#0", width=420, minwidth=200, anchor="w", stretch=True)
        utree.column("acao", width=300, minwidth=150, anchor="w", stretch=True)

        uscroll = ttk.Scrollbar(ucontainer, orient="vertical", command=utree.yview)
        utree.configure(yscrollcommand=uscroll.set)
        uscroll.pack(side="right", fill="y")
        utree.pack(side="left", fill="both", expand=True)

        utree.bind("<Double-1>", self._on_unmapped_double_click)

    # ----------------------------------------------------------------- load/reload

    def _reload(self) -> None:
        self._cancel_editor()
        self._repo_label_var.set(f"Repositório: {self._repo_root or '—'}")

        if not self._repo_root:
            self._show_error("Selecione uma matéria com repositório gerado.")
            return

        manifest_path = self._repo_root / "manifest.json"
        timeline_path = self._repo_root / "course" / ".timeline_index.json"

        if not manifest_path.exists():
            self._show_error("Build não encontrado — gere o repositório primeiro.")
            return
        if not timeline_path.exists():
            self._show_error("Nenhum cronograma detectado — o SYLLABUS foi carregado?")
            return

        try:
            blocks, entries_by_block_id, unmapped = load_timeline_data(
                manifest_path, timeline_path
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.exception("Erro ao ler artefatos do TimelineDashboard")
            self._show_error("Erro ao ler artefatos — veja o log.")
            return

        self._blocks = blocks
        self._entries_by_block_id = entries_by_block_id
        self._unmapped = unmapped
        self._manifest_path = manifest_path
        self._course_dir = timeline_path.parent
        self._kind_filter = {block_kind(b) for b in blocks}
        # unidades disponíveis pra atribuição manual (as que algum bloco já tem)
        self._unit_slugs = sorted({
            str(b.get("unit_slug") or "").strip()
            for b in blocks
            if str(b.get("unit_slug") or "").strip()
        })
        # injeta contagem de arquivos por bloco (usada por sort/coluna Arq.)
        for block in blocks:
            bid = str(block.get("id") or "")
            block["_file_count"] = len(entries_by_block_id.get(bid, []))

        self._clear_error()
        self._render()

    # ------------------------------------------------------------------ render

    def _render(self) -> None:
        """Reconstrói filtro + repopula tabelas a partir do cache (sem ler disco)."""
        self._build_filter_bar()
        self._populate()
        self._populate_unmapped()

    def _show_error(self, msg: str) -> None:
        self._clear_error()
        if hasattr(self, "_tree"):
            self._table_container.pack_forget()
        if hasattr(self, "_unmapped_holder"):
            self._unmapped_holder.pack_forget()
        for child in self._filter_bar.winfo_children():
            child.destroy()
        self._error_label = tk.Label(
            self,
            text=msg,
            bg=self._p["bg"],
            fg=self._p["warning"],
            font=("", 11),
            wraplength=600,
        )
        self._error_label.pack(expand=True, pady=60)

    def _clear_error(self) -> None:
        lbl = getattr(self, "_error_label", None)
        if lbl is not None and lbl.winfo_exists():
            lbl.destroy()
        self._error_label = None
        # garante que tabela + rodapé voltem a aparecer apos um estado de erro.
        # _unmapped_holder fica acima da tabela na ordem de pack (side=bottom),
        # entao re-empacotamos primeiro o rodapé e depois a tabela.
        if hasattr(self, "_unmapped_holder") and not self._unmapped_holder.winfo_ismapped():
            self._unmapped_holder.pack(fill="x", side="bottom")
        if hasattr(self, "_table_container") and not self._table_container.winfo_ismapped():
            self._table_container.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ reprocess

    def _on_reprocess(self) -> None:
        self._enqueue_reprocess_fn()
        self._btn_reprocess.pack_forget()
        self._dirty = False

    def _reveal_reprocess_btn(self) -> None:
        if not self._dirty:
            self._dirty = True
            self._btn_reprocess.pack(side="right", padx=6)

    # ------------------------------------------------------------------ filtros por kind

    def _build_filter_bar(self) -> None:
        p = self._p
        for child in self._filter_bar.winfo_children():
            child.destroy()

        present = sorted({block_kind(b) for b in (self._blocks or [])})
        if len(present) <= 1:
            return  # nada pra filtrar

        tk.Label(
            self._filter_bar, text="Filtrar:", bg=p["frame_bg"], fg=p["muted"], font=("", 9)
        ).pack(side="left", padx=(8, 4), pady=4)

        def _make_toggle(kind_value: str, var: tk.IntVar):
            def _toggle():
                if var.get():
                    self._kind_filter.add(kind_value)
                else:
                    self._kind_filter.discard(kind_value)
                self._populate()
            return _toggle

        for kind_value in present:
            disp = _kind_display(kind_value)
            var = tk.IntVar(value=1 if kind_value in self._kind_filter else 0)
            cb = tk.Checkbutton(
                self._filter_bar,
                text=f"{disp['icon']} {disp['label']}",
                variable=var,
                command=_make_toggle(kind_value, var),
                bg=p["frame_bg"],
                fg=p["fg"],
                selectcolor=p["input_bg"],
                activebackground=p["frame_bg"],
                activeforeground=p["accent"],
                font=("", 8),
                bd=0,
                highlightthickness=0,
            )
            cb.pack(side="left", padx=2, pady=2)

    # ------------------------------------------------------------------ populate

    def _sorted_blocks(self) -> list[dict]:
        col, ascending = self._sort_state
        blocks = list(self._blocks or [])
        blocks.sort(key=lambda b: timeline_sort_key(b, col), reverse=not ascending)
        return blocks

    def _populate(self) -> None:
        """Repopula a tabela principal respeitando filtro de kind e ordenação."""
        self._cancel_editor()
        tree = self._tree
        tree.delete(*tree.get_children(""))
        self._iid_to_block.clear()
        self._iid_to_entry.clear()

        visible = self._kind_filter
        row_i = 0
        shown = 0
        for block in self._sorted_blocks():
            kind = block_kind(block)
            if kind not in visible:
                continue
            shown += 1
            block_id = str(block.get("id") or "")
            disp = _kind_display(kind)
            period = str(block.get("period_start") or block.get("period_label") or "")
            topic = str(block.get("primary_topic_label") or "")
            title_bits = [b for b in (period, topic) if b]
            tree_text = f"{disp['icon']} " + " · ".join(title_bits) if title_bits else f"{disp['icon']} {block_id}"

            seq = ""
            m = _ID_NUM_RE.search(block_id)
            if m:
                seq = m.group(1)

            unit_slug = str(block.get("unit_slug") or "")
            unit_manual = bool(str(block.get("block_manual_unit_slug") or "").strip())
            unit_cell = (("✎ " if unit_manual else "") + unit_slug) if unit_slug else ""

            if kind in ("assessment", "review"):
                scope = _block_scope_slugs(block)
                escopo_cell = ", ".join(scope) if scope else "(definir)"
            else:
                escopo_cell = "—"

            tipo_manual = bool(str(block.get("manual_kind_override") or "").strip())
            tipo_cell = ("✎ " if tipo_manual else "") + disp["label"]

            tag = "odd" if row_i % 2 else "even"
            iid = tree.insert(
                "",
                "end",
                text=tree_text,
                values=("", seq, tipo_cell, unit_cell, escopo_cell, str(block.get("_file_count", 0))),
                tags=(tag,),
                open=False,
            )
            self._iid_to_block[iid] = block_id
            row_i += 1

            for entry in self._entries_by_block_id.get(block_id, []):
                child_iid = self._insert_entry_child(iid, entry)
                self._iid_to_entry[child_iid] = str(entry.get("id") or "")

        if shown == 0:
            placeholder = tree.insert("", "end", text="Nenhum bloco no filtro atual.", values=("",) * len(self._COLUMNS))
            # nao mapeia: linha informativa apenas

    def _insert_entry_child(self, parent_iid: str, entry: dict) -> str:
        title = str(entry.get("title") or entry.get("source_path") or "—")
        file_type = str(entry.get("file_type") or "")
        icon = "🔗" if file_type in {"url", "github-repo"} else "📄"
        confidence = float(entry.get("unit_match_confidence") or 0.0)
        from src.builder.routing.file_map import resolve_effective_block
        is_manual = resolve_effective_block(entry, self._blocks).source == "manual"
        mark = " ✎" if is_manual else ""
        tree = self._tree
        return tree.insert(
            parent_iid,
            "end",
            text=f"   {icon} {title}{mark}",
            values=("", "", "", "", "", f"conf {confidence:.2f}"),
            tags=("child",),
        )

    def _populate_unmapped(self) -> None:
        utree = self._unmapped_tree
        utree.delete(*utree.get_children(""))
        unmapped = self._unmapped or []
        n = len(unmapped)

        if n == 0:
            self._unmapped_label.pack_forget()
            self._unmapped_container.pack_forget()
            return

        self._unmapped_label_var.set(f"⚠ Sem bloco atribuído — {n} arquivo(s)")
        self._unmapped_label.pack(fill="x", padx=10, pady=(6, 2))
        self._unmapped_container.pack(fill="x", padx=4, pady=(0, 6))

        self._unmapped_iid_to_entry: dict[str, str] = {}
        for entry in unmapped:
            entry_id = str(entry.get("id") or "")
            title = str(entry.get("title") or entry.get("source_path") or "—")
            file_type = str(entry.get("file_type") or "")
            icon = "🔗" if file_type in {"url", "github-repo"} else "📄"
            iid = utree.insert(
                "",
                "end",
                text=f"{icon} {title}",
                values=("duplo clique p/ atribuir",),
            )
            self._unmapped_iid_to_entry[iid] = entry_id

    # ------------------------------------------------------------------ sort

    def _sort_by(self, column: str) -> None:
        cur_col, ascending = self._sort_state
        if cur_col == column:
            ascending = not ascending
        else:
            ascending = True
        self._sort_state = (column, ascending)
        self._populate()

    # ------------------------------------------------------------------ inline edit

    def _cancel_editor(self) -> None:
        ed = getattr(self, "_editor", None)
        if ed is not None:
            try:
                ed.destroy()
            except Exception:
                pass
        self._editor = None

    def _on_tree_double_click(self, event) -> None:
        tree = self._tree
        iid = tree.identify_row(event.y)
        col = tree.identify_column(event.x)  # ex "#3"
        if not iid or iid not in self._iid_to_block:
            return  # so linhas-pai (blocos) sao editaveis
        block_id = self._iid_to_block[iid]
        block = self._block_by_id(block_id)
        if block is None:
            return

        col_name = self._col_name(col)
        if col_name == "tipo":
            self._edit_tipo(iid, col, block_id)
        elif col_name == "unidade":
            self._edit_unidade(iid, col, block_id)
        elif col_name == "escopo":
            self._edit_escopo(block_id, block)

    def _col_name(self, col_id: str) -> str:
        # col_id no formato "#0" (arvore) ou "#N" (1-based em _COLUMNS)
        if col_id == "#0":
            return "#0"
        try:
            idx = int(col_id.replace("#", "")) - 1
        except ValueError:
            return ""
        if 0 <= idx < len(self._COLUMNS):
            return self._COLUMNS[idx]
        return ""

    def _block_by_id(self, block_id: str) -> Optional[dict]:
        for b in self._blocks or []:
            if str(b.get("id") or "") == block_id:
                return b
        return None

    def _overlay_combo(self, iid: str, col_id: str, labels: list[str], current: str) -> ttk.Combobox:
        self._cancel_editor()
        tree = self._tree
        bbox = tree.bbox(iid, col_id)
        if not bbox:
            return None  # celula fora da viewport
        x, y, w, h = bbox
        var = tk.StringVar(value=current)
        combo = ttk.Combobox(tree, textvariable=var, values=labels, state="readonly")
        combo.place(x=x, y=y, width=w, height=h)
        combo.focus_set()
        self._editor = combo
        return combo

    def _edit_tipo(self, iid: str, col_id: str, block_id: str) -> None:
        labels = ["⟳ auto"] + [
            f"{KIND_DISPLAY[k]['icon']} {KIND_DISPLAY[k]['label']}" for k in BlockKind
        ]
        values = [""] + [k.value for k in BlockKind]
        combo = self._overlay_combo(iid, col_id, labels, labels[0])
        if combo is None:
            return

        def on_select(_e=None):
            sel = combo.get()
            i = labels.index(sel) if sel in labels else 0
            new_kind = values[i] if i < len(values) else ""
            self._cancel_editor()
            try:
                save_block_kind_override(self._course_dir, block_id, new_kind or None)
                self._reveal_reprocess_btn()
                self._reload()
            except Exception:
                logger.exception("Erro ao salvar reclassificação do bloco %s", block_id)

        combo.bind("<<ComboboxSelected>>", on_select)
        combo.bind("<FocusOut>", lambda _e: self._cancel_editor())
        combo.bind("<Escape>", lambda _e: self._cancel_editor())

    def _edit_unidade(self, iid: str, col_id: str, block_id: str) -> None:
        slugs = list(self._unit_slugs or [])
        labels = ["⟳ auto"] + slugs
        values = [""] + slugs
        combo = self._overlay_combo(iid, col_id, labels, labels[0])
        if combo is None:
            return

        def on_select(_e=None):
            sel = combo.get()
            i = labels.index(sel) if sel in labels else 0
            chosen = values[i] if i < len(values) else ""
            self._cancel_editor()
            try:
                save_block_unit_override(self._course_dir, block_id, chosen or None)
                self._reveal_reprocess_btn()
                self._reload()
            except Exception:
                logger.exception("Erro ao salvar unidade do bloco %s", block_id)

        combo.bind("<<ComboboxSelected>>", on_select)
        combo.bind("<FocusOut>", lambda _e: self._cancel_editor())
        combo.bind("<Escape>", lambda _e: self._cancel_editor())

    def _edit_escopo(self, block_id: str, block: dict) -> None:
        if block_kind(block) not in ("assessment", "review"):
            return  # escopo read-only para outros tipos
        current = _block_scope_slugs(block)

        def on_save(selected: list[str]) -> None:
            try:
                save_block_scope_override(self._course_dir, block_id, selected)
                self._reveal_reprocess_btn()
                self._reload()
            except Exception:
                logger.exception("Erro ao salvar escopo do bloco %s", block_id)

        ScopeEditDialog(self, list(self._unit_slugs or []), current, on_save)

    # ------------------------------------------------------------------ unmapped reassign

    def _on_unmapped_double_click(self, event) -> None:
        utree = self._unmapped_tree
        iid = utree.identify_row(event.y)
        mapping = getattr(self, "_unmapped_iid_to_entry", {})
        if not iid or iid not in mapping:
            return
        entry_id = mapping[iid]
        self._open_block_picker(entry_id)

    def _open_block_picker(self, entry_id: str) -> None:
        """Toplevel simples: escolhe o bloco de destino para um arquivo sem bloco."""
        p = self._p
        labels = [self._block_label(b) for b in (self._blocks or []) if b.get("id")]
        values = [b["id"] for b in (self._blocks or []) if b.get("id")]
        if not values:
            messagebox.showinfo("Atribuir bloco", "Nenhum bloco disponível.", parent=self)
            return

        dlg = tk.Toplevel(self)
        dlg.title("Atribuir a bloco")
        apply_theme_to_toplevel(dlg, self)
        dlg.configure(bg=p["bg"])
        dlg.transient(self.winfo_toplevel())
        dlg.resizable(False, False)

        tk.Label(
            dlg, text="Atribuir o arquivo ao bloco:", bg=p["bg"], fg=p["fg"], font=("", 10, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))

        var = tk.StringVar(value=labels[0])
        combo = ttk.Combobox(dlg, textvariable=var, values=labels, state="readonly", width=44)
        combo.pack(fill="x", padx=12)

        btns = tk.Frame(dlg, bg=p["bg"])
        btns.pack(fill="x", padx=12, pady=12)

        def _ok():
            sel = var.get()
            idx = labels.index(sel) if sel in labels else 0
            new_block_id = values[idx] if 0 <= idx < len(values) else None
            dlg.destroy()
            if not new_block_id:
                return
            try:
                save_block_assignment(self._manifest_path, entry_id, new_block_id)
                self._reveal_reprocess_btn()
                self._reload()
            except Exception:
                logger.exception("Erro ao salvar atribuição de bloco para entry %s", entry_id)

        ttk.Button(btns, text="OK", command=_ok).pack(side="right", padx=(4, 0))
        ttk.Button(btns, text="Cancelar", command=dlg.destroy).pack(side="right")
        dlg.bind("<Escape>", lambda _e: dlg.destroy())
        dlg.grab_set()
        combo.focus_set()

    def _block_label(self, block: dict) -> str:
        icon = _kind_display(block_kind(block))["icon"]
        period = str(block.get("period_label") or block.get("period_start") or block.get("id") or "")
        topic = str(block.get("primary_topic_label") or "")
        base = f"{period} — {topic}" if topic else period
        return f"{icon} {base}"
