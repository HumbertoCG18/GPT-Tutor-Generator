from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from src.ui.theme import apply_theme_to_toplevel
from src.builder.student_state import (
    consolidate_unit,
    UnitNotReadyError,
    parse_battery_frontmatter,
)


class ConsolidateUnitDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, repo_dir: Path, course_topics_by_unit: dict):
        super().__init__(parent)
        self.title("Consolidar unidade")
        self.repo_dir = repo_dir
        self.course_topics_by_unit = course_topics_by_unit
        self.grab_set()
        p = apply_theme_to_toplevel(self, parent)

        frm = tk.Frame(self, bg=p["bg"])
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(frm, text="Unidades elegíveis:", bg=p["bg"], fg=p["fg"]).pack(anchor="w")

        self.tree = ttk.Treeview(
            frm,
            columns=("progress", "action"),
            show="tree headings",
            height=8,
        )
        self.tree.heading("#0", text="Unidade")
        self.tree.heading("progress", text="Progresso")
        self.tree.heading("action", text="Ação")
        self.tree.column("#0", width=200)
        self.tree.column("progress", width=160)
        self.tree.column("action", width=120)
        self.tree.pack(fill="both", expand=True, pady=(4, 8))

        self._populate()

        btn_frm = tk.Frame(frm, bg=p["bg"])
        btn_frm.pack(fill="x")
        ttk.Button(
            btn_frm,
            text="Consolidar selecionada",
            command=self._consolidate_selected,
        ).pack(side="left")
        ttk.Button(
            btn_frm,
            text="Forçar consolidação",
            command=self._force_selected,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(btn_frm, text="Fechar", command=self.destroy).pack(side="right")

    def _populate(self) -> None:
        batteries_root = self.repo_dir / "student" / "batteries"
        for unit_slug, topics in self.course_topics_by_unit.items():
            unit_dir = batteries_root / unit_slug
            if not unit_dir.is_dir():
                continue
            total = len(topics)
            closed = 0
            for slug, _label in topics:
                battery_file = unit_dir / f"{slug}.md"
                if battery_file.exists():
                    fm = parse_battery_frontmatter(
                        battery_file.read_text(encoding="utf-8")
                    )
                    if fm.get("status") == "compreendido":
                        closed += 1
            progress = f"{closed}/{total} compreendidos"
            action = "Consolidar" if closed == total and total > 0 else "Forçar"
            self.tree.insert(
                "",
                "end",
                iid=unit_slug,
                text=unit_slug,
                values=(progress, action),
            )

    def _selected_unit(self) -> str:
        sel = self.tree.selection()
        return sel[0] if sel else ""

    def _consolidate_selected(self) -> None:
        unit = self._selected_unit()
        if not unit:
            return
        self._run(unit, force=False)

    def _force_selected(self) -> None:
        unit = self._selected_unit()
        if not unit:
            return
        if not messagebox.askyesno(
            "Forçar consolidação",
            f"Forçar consolidação da {unit} mesmo com tópicos pendentes?",
        ):
            return
        self._run(unit, force=True)

    def _run(self, unit_slug: str, force: bool) -> None:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        topic_order = [slug for slug, _ in self.course_topics_by_unit.get(unit_slug, [])]
        try:
            result = consolidate_unit(
                root_dir=self.repo_dir,
                unit_slug=unit_slug,
                today=today,
                topic_order=topic_order,
                force=force,
            )
            messagebox.showinfo(
                "Consolidada",
                f"{unit_slug} consolidada.\n"
                f"Summary: {result.summary_path.relative_to(self.repo_dir)}\n"
                f"Backup: {result.backup_path.relative_to(self.repo_dir)}",
            )
            self.destroy()
        except UnitNotReadyError as exc:
            messagebox.showwarning(
                "Unidade não pronta",
                f"Tópicos pendentes em {unit_slug}: {', '.join(exc.pending)}\n"
                "Use 'Forçar consolidação' se realmente quiser consolidar parcial.",
            )
