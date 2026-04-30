from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional

from src.builder.artifacts.student_state import (
    apply_manual_import_to_student_state,
    build_course_unit_topic_index,
    course_topics_for_unit,
    parse_student_state_manual_import,
    save_manual_import_battery,
    validate_manual_import_selection,
    VALID_MANUAL_IMPORT_STATUSES,
)
from src.utils.helpers import APP_NAME


class StudentStateCurator(tk.Toplevel):
    def __init__(
        self,
        parent,
        *,
        repo_dir: Path,
        subject_profile,
        theme_mgr,
        on_saved: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.repo_dir = Path(repo_dir)
        self.subject_profile = subject_profile
        self.theme_mgr = theme_mgr
        self._on_saved = on_saved
        self.course_index = build_course_unit_topic_index(subject_profile)
        self._theme_name = parent.config_obj.get("theme") if hasattr(parent, "config_obj") else "dark"

        self.title("Student State")
        self.geometry("1100x820")
        self.minsize(920, 660)

        self._import_var = tk.StringVar(value="Cole o markdown do tutor e clique em Importar.")
        self._validation_var = tk.StringVar(value="")
        self._target_var = tk.StringVar(value="Destino: —")
        self._unit_var = tk.StringVar(value="")
        self._topic_var = tk.StringVar(value="")
        self._status_var = tk.StringVar(value="em_progresso")
        self._date_var = tk.StringVar(value="")
        self._time_var = tk.StringVar(value="")
        self._next_topic_var = tk.StringVar(value="")
        self._topic_display_to_slug: dict[str, str] = {}
        self._topic_slug_to_display: dict[str, str] = {}

        self.theme_mgr.apply(self, self._theme_name)
        self._build_ui()
        self._populate_units()
        self.grab_set()

    def _build_ui(self) -> None:
        p = self.theme_mgr.palette(self._theme_name)

        header = tk.Frame(self, bg=p["header_bg"], padx=16, pady=10)
        header.pack(fill="x")
        tk.Label(
            header,
            text="🧠 Student State",
            bg=p["header_bg"],
            fg=p["header_fg"],
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")
        ttk.Button(header, text="Importar", command=self._import_markdown).pack(side="right", padx=(8, 0))
        ttk.Button(header, text="Salvar", command=self._save).pack(side="right")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=10)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(3, weight=1)

        ttk.Label(body, text="Importação do tutor", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(body, text="Sessão normalizada", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.import_text = tk.Text(
            body,
            wrap="word",
            height=16,
            bg=p["input_bg"],
            fg=p["fg"],
            insertbackground=p["fg"],
            selectbackground=p["select_bg"],
            selectforeground=p["select_fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=p["border"],
            font=("Consolas", 10),
        )
        self.import_text.grid(row=1, column=0, sticky="nsew", pady=(4, 8))

        self.editor = tk.Text(
            body,
            wrap="word",
            height=16,
            bg=p["input_bg"],
            fg=p["fg"],
            insertbackground=p["fg"],
            selectbackground=p["select_bg"],
            selectforeground=p["select_fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=p["border"],
            font=("Consolas", 10),
        )
        self.editor.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(4, 8))

        meta = ttk.LabelFrame(body, text="Metadados")
        meta.grid(row=2, column=0, columnspan=2, sticky="ew")
        for col in range(4):
            meta.grid_columnconfigure(col, weight=1)

        ttk.Label(meta, text="Unidade").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        self.unit_combo = ttk.Combobox(meta, textvariable=self._unit_var, state="readonly")
        self.unit_combo.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        self.unit_combo.bind("<<ComboboxSelected>>", self._on_unit_changed)

        ttk.Label(meta, text="Tópico").grid(row=0, column=1, sticky="w", padx=8, pady=(8, 2))
        self.topic_combo = ttk.Combobox(meta, textvariable=self._topic_var, state="readonly")
        self.topic_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=(0, 8))
        self.topic_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_target_preview())

        ttk.Label(meta, text="Status").grid(row=0, column=2, sticky="w", padx=8, pady=(8, 2))
        self.status_combo = ttk.Combobox(
            meta,
            textvariable=self._status_var,
            state="readonly",
            values=tuple(sorted(VALID_MANUAL_IMPORT_STATUSES)),
        )
        self.status_combo.grid(row=1, column=2, sticky="ew", padx=8, pady=(0, 8))

        ttk.Label(meta, text="Próximo tópico").grid(row=0, column=3, sticky="w", padx=8, pady=(8, 2))
        ttk.Entry(meta, textvariable=self._next_topic_var).grid(row=1, column=3, sticky="ew", padx=8, pady=(0, 8))

        ttk.Label(meta, text="Data").grid(row=2, column=0, sticky="w", padx=8, pady=(2, 2))
        ttk.Entry(meta, textvariable=self._date_var).grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))
        ttk.Label(meta, text="Hora").grid(row=2, column=1, sticky="w", padx=8, pady=(2, 2))
        ttk.Entry(meta, textvariable=self._time_var).grid(row=3, column=1, sticky="ew", padx=8, pady=(0, 8))

        ttk.Label(body, textvariable=self._import_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 2))
        ttk.Label(body, textvariable=self._validation_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 2))
        ttk.Label(body, textvariable=self._target_var, font=("Segoe UI", 9, "bold")).grid(
            row=6, column=0, columnspan=2, sticky="w"
        )

    def _populate_units(self) -> None:
        values = [item["unit_slug"] for item in self.course_index]
        self.unit_combo["values"] = values
        if values:
            self._unit_var.set(values[0])
            self._populate_topics(values[0])

    def _populate_topics(self, unit_slug: str) -> None:
        self._topic_display_to_slug = {}
        self._topic_slug_to_display = {}
        unit = next((item for item in self.course_index if item.get("unit_slug") == unit_slug), None)
        topic_values: list[str] = []
        for topic in list(unit.get("topics", [])) if unit else []:
            slug = str(topic.get("topic_slug") or "").strip()
            display = str(topic.get("topic_label") or topic.get("topic_title") or slug).strip()
            if not slug or not display:
                continue
            self._topic_display_to_slug[display] = slug
            self._topic_slug_to_display[slug] = display
            topic_values.append(display)
        self.topic_combo["values"] = topic_values
        if topic_values:
            current_slug = self._selected_topic_slug()
            self._topic_var.set(self._topic_slug_to_display.get(current_slug, topic_values[0]))
        else:
            self._topic_var.set("")
        self._refresh_target_preview()

    def _on_unit_changed(self, _event=None) -> None:
        self._populate_topics(self._unit_var.get().strip())

    def _refresh_target_preview(self) -> None:
        unit_slug = self._unit_var.get().strip()
        topic_slug = self._selected_topic_slug()
        if unit_slug and topic_slug:
            self._target_var.set(f"Destino: student/batteries/{unit_slug}/{topic_slug}.md")
        else:
            self._target_var.set("Destino: —")

    def _import_markdown(self) -> None:
        raw = self.import_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning(APP_NAME, "Cole um markdown do tutor antes de importar.")
            return

        payload = parse_student_state_manual_import(raw)
        self._unit_var.set(payload["unit_slug"])
        self._populate_topics(payload["unit_slug"])
        if payload["topic_slug"]:
            self._topic_var.set(
                self._topic_slug_to_display.get(payload["topic_slug"], payload["topic_slug"])
            )
        if payload["status"]:
            self._status_var.set(payload["status"])
        self._date_var.set(payload["date"])
        self._time_var.set(payload["time"])
        self._next_topic_var.set(payload["next_topic"])
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", payload["body"])
        self._import_var.set("Importação concluída. Revise a unidade, o tópico e o conteúdo antes de salvar.")
        self._update_validation_summary()

    def _update_validation_summary(self) -> list[str]:
        errors = validate_manual_import_selection(
            unit_slug=self._unit_var.get().strip(),
            topic_slug=self._selected_topic_slug(),
            course_index=self.course_index,
        )
        if not self.course_index:
            self._validation_var.set("Nenhuma unidade/tópico disponível. Revise o plano de ensino da matéria.")
            return ["course_index"]
        if not errors:
            self._validation_var.set("Mapeamento válido contra a estrutura atual do curso.")
        elif errors == ["unit_slug"]:
            self._validation_var.set("Unidade inválida para o curso atual. Corrija manualmente no dropdown.")
        else:
            self._validation_var.set("Tópico inválido para a unidade selecionada. Corrija manualmente no dropdown.")
        return errors

    def _selected_topic_title(self) -> str:
        unit_slug = self._unit_var.get().strip()
        topic_slug = self._selected_topic_slug()
        for item in self.course_index:
            if item.get("unit_slug") != unit_slug:
                continue
            for topic in item.get("topics", []):
                if topic.get("topic_slug") == topic_slug:
                    return str(topic.get("topic_title") or "").strip()
        return topic_slug.replace("-", " ").title()

    def _selected_unit_title(self) -> str:
        unit_slug = self._unit_var.get().strip()
        for item in self.course_index:
            if item.get("unit_slug") == unit_slug:
                return str(item.get("unit_title") or "").strip()
        return unit_slug

    def _selected_topic_slug(self) -> str:
        raw = self._topic_var.get().strip()
        return self._topic_display_to_slug.get(raw, raw)

    def _save(self) -> None:
        errors = self._update_validation_summary()
        if errors:
            messagebox.showerror(APP_NAME, "Corrija unidade/tópico antes de salvar.")
            return

        state_path = self.repo_dir / "student" / "STUDENT_STATE.md"
        if not state_path.exists():
            messagebox.showerror(APP_NAME, f"STUDENT_STATE.md não encontrado em:\n{state_path}")
            return

        if not self._date_var.get().strip():
            self._date_var.set(datetime.now().strftime("%d-%m-%y"))
        if not self._time_var.get().strip():
            self._time_var.set(datetime.now().strftime("%H-%M"))

        payload = {
            "unit_slug": self._unit_var.get().strip(),
            "unit_title": self._selected_unit_title(),
            "topic_slug": self._selected_topic_slug(),
            "topic_title": self._selected_topic_title(),
            "status": self._status_var.get().strip() or "em_progresso",
            "date": self._date_var.get().strip(),
            "time": self._time_var.get().strip(),
            "next_topic": self._next_topic_var.get().strip(),
            "body": self.editor.get("1.0", tk.END).strip(),
        }

        battery_path = save_manual_import_battery(self.repo_dir, payload)
        battery_rel = battery_path.relative_to(self.repo_dir).as_posix()
        apply_manual_import_to_student_state(
            self.repo_dir,
            payload=payload,
            battery_rel_path=battery_rel,
            course_map_topics=course_topics_for_unit(self.course_index, payload["unit_slug"]),
        )
        if self._on_saved is not None:
            self._on_saved(f"Student State atualizado: {battery_rel}")
        messagebox.showinfo(
            APP_NAME,
            "Student State salvo com sucesso.\n\n"
            f"Bateria: {battery_rel}\n"
            "STUDENT_STATE.md atualizado.",
        )
        self.destroy()
