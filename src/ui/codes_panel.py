"""Mini-painel UI para gerar/editar code summaries + atribuir aula (block)."""
from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional


def _code_row_label(summary: dict, entry: dict, eid: str) -> str:
    """Rótulo da linha na aba códigos: título do Gemini > título da entry > id.
    Evita o eid[:8] que colide visualmente (ex.: exemplos.thy e exemplos.zip → ambos 'exemplos')."""
    return str((summary or {}).get("inferred_title") or (entry or {}).get("title") or eid or "")


PEDAGOGICAL_ROLES = [
    "exemplo_demonstrativo",
    "exercicio_resolvido",
    "template_aluno",
    "solucao_referencia",
    "utilitario",
    "outro",
]


class _LiteBuilder:
    """Builder leve — `summarize_all_code_entries` só usa `.root_dir`."""

    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)


class CodesPanel(tk.Frame):
    """Mini-painel pra gerar/editar code summaries + atribuir aula."""

    def __init__(
        self,
        parent,
        *,
        get_subject_fn: Callable,
        get_config_fn: Callable,
        get_repo_dir_fn: Callable,
    ):
        super().__init__(parent)
        self._get_subject = get_subject_fn
        self._get_config = get_config_fn
        self._get_repo_dir = get_repo_dir_fn
        self._busy = False
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=8)
        ttk.Button(toolbar, text="🔄 Recarregar", command=self.refresh).pack(side="left", padx=2)
        ttk.Button(
            toolbar,
            text="✨ Gerar resumos (Gemini)",
            command=self._on_generate_all,
        ).pack(side="left", padx=2)
        ttk.Button(
            toolbar,
            text="📝 Editar selecionado",
            command=self._on_edit_selected,
        ).pack(side="left", padx=2)
        ttk.Button(
            toolbar,
            text="🎯 Atribuir aula",
            command=self._on_assign_block,
        ).pack(side="left", padx=2)

        cols = ("status", "titulo", "linguagem", "aula", "conceitos")
        self._tree = ttk.Treeview(self, columns=cols, show="tree headings")
        self._tree.heading("#0", text="ID")
        for c, label in zip(cols, ("Status", "Título", "Linguagem", "Aula", "Conceitos")):
            self._tree.heading(c, text=label)
        self._tree.column("status", width=80)
        self._tree.column("titulo", width=300)
        self._tree.column("linguagem", width=80)
        self._tree.column("aula", width=200)
        self._tree.column("conceitos", width=300)
        self._tree.pack(fill="both", expand=True, padx=8)

        self._status = tk.StringVar(value="Sem matéria selecionada.")
        ttk.Label(self, textvariable=self._status).pack(fill="x", padx=8, pady=4)

    # -------------------------------------------------------------- helpers
    def _repo_dir(self) -> Optional[Path]:
        repo_dir = self._get_repo_dir()
        if not repo_dir:
            return None
        return Path(repo_dir)

    def _load_curation(self, repo_dir: Path) -> dict:
        path = repo_dir / "code_curation.json"
        if not path.exists():
            return {"version": 1, "entries": {}}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"version": 1, "entries": {}}

    def _write_curation(self, repo_dir: Path, data: dict) -> None:
        path = repo_dir / "code_curation.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    def _load_blocks(self, repo_dir: Path) -> list[dict]:
        for rel in ("course/.timeline_index.json", ".timeline_index.json"):
            path = repo_dir / rel
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("blocks", []) or []
            except Exception:
                return []
        return []

    # -------------------------------------------------------------- refresh
    def refresh(self):
        """Re-read manifest + curation, redraw."""
        for item in self._tree.get_children():
            self._tree.delete(item)

        repo_dir = self._repo_dir()
        if not repo_dir:
            self._status.set("Sem matéria selecionada.")
            return

        manifest_path = repo_dir / "manifest.json"
        if not manifest_path.exists():
            self._status.set("Manifest não encontrado.")
            return

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._status.set(f"Erro lendo manifest: {exc}")
            return

        curation = self._load_curation(repo_dir)
        blocks = self._load_blocks(repo_dir)
        blocks_by_id = {b["id"]: b for b in blocks if b.get("id")}

        total = 0
        with_summary = 0
        for e in manifest.get("entries", []):
            if e.get("file_type") not in ("code", "zip"):
                continue
            total += 1
            eid = e.get("id", "")
            entry_curation = curation.get("entries", {}).get(eid, {})
            summary = entry_curation.get("summary") or {}
            has_summary = bool(summary)
            if has_summary:
                with_summary += 1

            status_icon = "✅" if has_summary else "⏳"
            title = summary.get("inferred_title") or e.get("title", "")
            lang = summary.get("language") or ""
            block_id = summary.get("primary_block_id", "")
            if block_id and block_id in blocks_by_id:
                block_label = blocks_by_id[block_id].get("period_label", block_id)
            elif has_summary:
                block_label = "⚠ órfão"
            else:
                block_label = ""
            concepts = ", ".join((summary.get("concepts") or [])[:3])

            self._tree.insert(
                "",
                "end",
                iid=eid,
                text=_code_row_label(summary, e, eid),
                values=(status_icon, title, lang, block_label, concepts),
            )

        self._status.set(f"{with_summary}/{total} resumidos.")

    # ---------------------------------------------------------- generate
    def _on_generate_all(self):
        if self._busy:
            return
        config = self._get_config()
        try:
            from src.builder.runtime.gemini_client import (
                get_gemini_client,
                has_gemini_api_key,
            )
        except Exception as exc:
            messagebox.showerror("Gemini", f"Cliente indisponível: {exc}")
            return

        if not has_gemini_api_key(config):
            messagebox.showwarning("Gemini", "Configure a chave da API em Settings.")
            return

        repo_dir = self._repo_dir()
        if not repo_dir:
            messagebox.showwarning("Códigos", "Selecione uma matéria primeiro.")
            return

        manifest_path = repo_dir / "manifest.json"
        if not manifest_path.exists():
            messagebox.showwarning("Códigos", "Manifest não encontrado.")
            return

        try:
            client = get_gemini_client(config)
        except Exception as exc:
            messagebox.showerror("Gemini", f"Falha inicializando cliente: {exc}")
            return

        self._busy = True
        self._status.set("Iniciando...")

        def _worker():
            try:
                from src.builder.core.code_summarization import (
                    summarize_all_code_entries,
                )

                def _progress(idx, total, title, status):
                    msg = f"[{idx}/{total}] {status}: {title}"
                    self.after(0, lambda m=msg: self._status.set(m))

                builder = self._make_lightweight_builder(repo_dir)
                summarize_all_code_entries(builder, client, _progress)
                self.after(0, self.refresh)
                self.after(
                    0,
                    lambda: messagebox.showinfo("Códigos", "Resumos gerados/atualizados."),
                )
            except Exception as exc:
                err = str(exc)
                self.after(0, lambda e=err: messagebox.showerror("Erro", e))
            finally:
                self._busy = False

        threading.Thread(target=_worker, daemon=True).start()

    # ---------------------------------------------------------------- edit
    def _on_edit_selected(self):
        selection = self._tree.selection()
        if not selection:
            messagebox.showwarning("Editar", "Selecione um item primeiro.")
            return
        eid = selection[0]

        repo_dir = self._repo_dir()
        if not repo_dir:
            return

        curation = self._load_curation(repo_dir)
        entry = curation.setdefault("entries", {}).setdefault(eid, {})
        summary = dict(entry.get("summary") or {})

        dlg = tk.Toplevel(self)
        dlg.title(f"Editar resumo — {eid[:8]}")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(True, True)

        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Título inferido:").grid(row=0, column=0, sticky="w", pady=2)
        var_title = tk.StringVar(value=summary.get("inferred_title", ""))
        ent_title = ttk.Entry(frm, textvariable=var_title, width=60)
        ent_title.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(frm, text="Linguagem:").grid(row=1, column=0, sticky="w", pady=2)
        var_lang = tk.StringVar(value=summary.get("language", ""))
        ttk.Entry(frm, textvariable=var_lang, width=30).grid(row=1, column=1, sticky="w", pady=2)

        ttk.Label(frm, text="Papel pedagógico:").grid(row=2, column=0, sticky="w", pady=2)
        var_role = tk.StringVar(value=summary.get("pedagogical_role", "outro"))
        cb_role = ttk.Combobox(
            frm,
            textvariable=var_role,
            values=PEDAGOGICAL_ROLES,
            state="readonly",
            width=30,
        )
        cb_role.grid(row=2, column=1, sticky="w", pady=2)

        ttk.Label(frm, text="Conceitos (CSV):").grid(row=3, column=0, sticky="w", pady=2)
        concepts_csv = ", ".join(summary.get("concepts") or [])
        var_concepts = tk.StringVar(value=concepts_csv)
        ttk.Entry(frm, textvariable=var_concepts, width=60).grid(row=3, column=1, sticky="ew", pady=2)

        ttk.Label(frm, text="Resumo:").grid(row=4, column=0, sticky="nw", pady=2)
        txt_summary = tk.Text(frm, width=60, height=4, wrap="word")
        txt_summary.grid(row=4, column=1, sticky="ew", pady=2)
        txt_summary.insert("1.0", summary.get("summary", ""))

        frm.columnconfigure(1, weight=1)

        btns = ttk.Frame(dlg, padding=(10, 0, 10, 10))
        btns.pack(fill="x")

        def _on_save():
            # Re-load to avoid clobbering concurrent edits
            cur = self._load_curation(repo_dir)
            ent = cur.setdefault("entries", {}).setdefault(eid, {})
            existing_summary = dict(ent.get("summary") or {})

            new_concepts = [
                c.strip() for c in var_concepts.get().split(",") if c.strip()
            ]
            existing_summary["inferred_title"] = var_title.get().strip()
            existing_summary["language"] = var_lang.get().strip()
            existing_summary["pedagogical_role"] = var_role.get().strip() or "outro"
            existing_summary["concepts"] = new_concepts
            existing_summary["summary"] = txt_summary.get("1.0", "end").strip()
            existing_summary["block_match_method"] = "manual"
            # preserve content_hash & other fields by not touching them above
            ent["summary"] = existing_summary
            try:
                self._write_curation(repo_dir, cur)
            except Exception as exc:
                messagebox.showerror("Erro", f"Falha gravando curation: {exc}", parent=dlg)
                return
            dlg.destroy()
            self.refresh()

        ttk.Button(btns, text="Salvar", command=_on_save).pack(side="right", padx=4)
        ttk.Button(btns, text="Cancelar", command=dlg.destroy).pack(side="right", padx=4)

        ent_title.focus_set()
        dlg.wait_window()

    # ------------------------------------------------------------ assign
    def _on_assign_block(self):
        selection = self._tree.selection()
        if not selection:
            messagebox.showwarning("Atribuir aula", "Selecione um item primeiro.")
            return
        eid = selection[0]

        repo_dir = self._repo_dir()
        if not repo_dir:
            return

        blocks = self._load_blocks(repo_dir)
        if not blocks:
            messagebox.showwarning("Atribuir aula", "Nenhum block encontrado (.timeline_index.json).")
            return

        curation = self._load_curation(repo_dir)
        entry = curation.setdefault("entries", {}).setdefault(eid, {})
        summary = dict(entry.get("summary") or {})

        ORPHAN = "(nenhum / órfão)"

        def _block_label(b: dict) -> str:
            period = b.get("period_label", "?")
            topic = b.get("primary_topic_label", "")
            return f"{period} — {topic}" if topic else period

        labels = [_block_label(b) for b in blocks]
        label_to_id = {lbl: b["id"] for lbl, b in zip(labels, blocks)}
        id_to_label = {b["id"]: lbl for lbl, b in zip(labels, blocks)}

        current_primary = summary.get("primary_block_id", "")
        current_secondaries = list(summary.get("secondary_block_ids") or [])

        dlg = tk.Toplevel(self)
        dlg.title(f"Atribuir aula — {eid[:8]}")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        frm = ttk.Frame(dlg, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Aula primária:").grid(row=0, column=0, sticky="w", pady=2)
        primary_values = [ORPHAN] + labels
        var_primary = tk.StringVar(
            value=id_to_label.get(current_primary, ORPHAN)
        )
        cb_primary = ttk.Combobox(
            frm,
            textvariable=var_primary,
            values=primary_values,
            state="readonly",
            width=60,
        )
        cb_primary.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(frm, text="Aulas secundárias\n(Ctrl+clique p/ múltiplos):").grid(
            row=1, column=0, sticky="nw", pady=2
        )
        lb_frame = ttk.Frame(frm)
        lb_frame.grid(row=1, column=1, sticky="nsew", pady=2)
        lb = tk.Listbox(lb_frame, selectmode="extended", height=10, width=60, exportselection=False)
        sb = ttk.Scrollbar(lb_frame, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(1, weight=1)

        def _refill_secondary_list(*_args):
            primary_label = var_primary.get()
            lb.delete(0, "end")
            secondary_labels = [lbl for lbl in labels if lbl != primary_label]
            for lbl in secondary_labels:
                lb.insert("end", lbl)
            # pre-select current secondaries
            for i, lbl in enumerate(secondary_labels):
                bid = label_to_id.get(lbl)
                if bid in current_secondaries:
                    lb.selection_set(i)

        cb_primary.bind("<<ComboboxSelected>>", _refill_secondary_list)
        _refill_secondary_list()

        btns = ttk.Frame(dlg, padding=(10, 0, 10, 10))
        btns.pack(fill="x")

        def _on_save():
            cur = self._load_curation(repo_dir)
            ent = cur.setdefault("entries", {}).setdefault(eid, {})
            existing_summary = dict(ent.get("summary") or {})

            primary_label = var_primary.get()
            if primary_label == ORPHAN:
                existing_summary["primary_block_id"] = ""
            else:
                existing_summary["primary_block_id"] = label_to_id.get(primary_label, "")

            primary_label_now = var_primary.get()
            secondary_labels_now = [lbl for lbl in labels if lbl != primary_label_now]
            selected_indices = lb.curselection()
            secondary_ids = []
            for idx in selected_indices:
                lbl = secondary_labels_now[idx]
                bid = label_to_id.get(lbl)
                if bid and bid != existing_summary.get("primary_block_id"):
                    secondary_ids.append(bid)
            existing_summary["secondary_block_ids"] = secondary_ids
            existing_summary["block_match_method"] = "manual"

            ent["summary"] = existing_summary
            try:
                self._write_curation(repo_dir, cur)
            except Exception as exc:
                messagebox.showerror("Erro", f"Falha gravando curation: {exc}", parent=dlg)
                return
            dlg.destroy()
            self.refresh()

        ttk.Button(btns, text="Salvar", command=_on_save).pack(side="right", padx=4)
        ttk.Button(btns, text="Cancelar", command=dlg.destroy).pack(side="right", padx=4)

        dlg.wait_window()

    # ---------------------------------------------------------- builder
    def _make_lightweight_builder(self, repo_dir):
        """`summarize_all_code_entries` só lê `builder.root_dir`."""
        return _LiteBuilder(repo_dir)
