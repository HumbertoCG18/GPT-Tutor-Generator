"""Painel de manutenção — limpeza retroativa de resíduos no repositório."""
from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional


class MaintenancePanel(tk.Frame):
    """Detecta e remove resíduos deixados por remoções anteriores.

    Surfaces:
      - code_curation.json (entries órfãs)
      - image_curation.json embarcado no manifest (imagens removidas)
      - sidecars derivativos (regerados do manifest atual)
    """

    def __init__(
        self,
        parent,
        *,
        get_repo_dir_fn: Callable[[], Optional[Path]],
        make_builder_fn: Callable[[], object],
    ):
        super().__init__(parent)
        self._get_repo_dir = get_repo_dir_fn
        self._make_builder = make_builder_fn
        self._busy = False
        self._build_ui()

    # ---------------------------------------------------------- UI
    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Label(
            header,
            text="🧹 Manutenção do repositório",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text=(
                "Remove resíduos de entries deletadas antes da correção de "
                "lifecycle e regenera sidecars derivativos (taxonomy, "
                "timeline, MDs). Não reprocessa entries — custo zero."
            ),
            foreground="gray",
            wraplength=720,
            justify="left",
        ).pack(anchor="w", pady=(2, 8))

        # ── Cards de status
        cards = ttk.Frame(self)
        cards.pack(fill="x", padx=12, pady=4)

        self._var_subject = tk.StringVar(value="—")
        self._var_code_orphans = tk.StringVar(value="—")
        self._var_sidecar_age = tk.StringVar(value="—")

        for i, (label, var) in enumerate([
            ("Matéria atual:", self._var_subject),
            ("Órfãos em code_curation.json:", self._var_code_orphans),
            ("Sidecars derivativos:", self._var_sidecar_age),
        ]):
            row = ttk.Frame(cards)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=32).pack(side="left")
            ttk.Label(row, textvariable=var, font=("Segoe UI", 10, "bold")).pack(side="left")

        # ── Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Button(
            toolbar, text="🔍 Detectar resíduos", command=self.refresh
        ).pack(side="left", padx=2)
        ttk.Button(
            toolbar, text="🧹 Executar limpeza", command=self._on_sweep
        ).pack(side="left", padx=2)

        # ── Log
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, padx=12, pady=12)
        self._log = tk.Text(log_frame, wrap="word", height=12, font=("Consolas", 9))
        self._log.pack(fill="both", expand=True, padx=4, pady=4)
        self._log.configure(state="disabled")

    # ---------------------------------------------------------- helpers
    def _log_line(self, msg: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self) -> None:
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _detect_orphans(self, repo_dir: Path) -> tuple[int, list[str]]:
        """Read-only: conta órfãos em code_curation contra manifest."""
        cur_path = repo_dir / "code_curation.json"
        mf_path = repo_dir / "manifest.json"
        if not cur_path.exists() or not mf_path.exists():
            return (0, [])
        try:
            cur = json.loads(cur_path.read_text(encoding="utf-8"))
            mf = json.loads(mf_path.read_text(encoding="utf-8"))
        except Exception:
            return (0, [])
        valid = {e.get("id") for e in mf.get("entries", []) if e.get("id")}
        orphans = [eid for eid in (cur.get("entries") or {}) if eid not in valid]
        return (len(orphans), orphans)

    def _sidecar_files(self, repo_dir: Path) -> list[Path]:
        return [
            repo_dir / "course" / ".assessment_context.json",
            repo_dir / "course" / ".content_taxonomy.json",
            repo_dir / "course" / ".semantic_profile.generated.json",
            repo_dir / "course" / ".tag_catalog.json",
            repo_dir / "course" / ".timeline_index.json",
        ]

    # ---------------------------------------------------------- refresh
    def refresh(self) -> None:
        repo_dir = self._get_repo_dir() if self._get_repo_dir else None
        if not repo_dir:
            self._var_subject.set("(sem matéria selecionada)")
            self._var_code_orphans.set("—")
            self._var_sidecar_age.set("—")
            return
        repo_dir = Path(repo_dir)
        self._var_subject.set(repo_dir.name)

        n, ids = self._detect_orphans(repo_dir)
        if n == 0:
            self._var_code_orphans.set("nenhum")
        else:
            self._var_code_orphans.set(f"{n} órfão(s): {', '.join(ids[:5])}{'...' if n > 5 else ''}")

        present = [p.name for p in self._sidecar_files(repo_dir) if p.exists()]
        self._var_sidecar_age.set(f"{len(present)}/5 presentes (serão regerados)")

    # ---------------------------------------------------------- sweep
    def _on_sweep(self) -> None:
        if self._busy:
            return
        repo_dir = self._get_repo_dir() if self._get_repo_dir else None
        if not repo_dir:
            messagebox.showwarning("Manutenção", "Selecione uma matéria primeiro.")
            return

        if not messagebox.askyesno(
            "Confirmar limpeza",
            "Vai purgar entries órfãs de code_curation/image_curation e "
            "regenerar sidecars derivativos.\n\n"
            "Não reprocessa entries (zero custo Gemini/extractor).\n\n"
            "Continuar?",
        ):
            return

        self._busy = True
        self._clear_log()
        self._log_line(f"[start] repo={Path(repo_dir).name}")

        def _worker():
            try:
                builder = self._make_builder()
                if builder is None:
                    self.after(0, lambda: self._log_line("[erro] builder indisponível"))
                    return
                report = builder.sweep_orphans()
                self.after(0, lambda r=report: self._render_report(r))
            except Exception as exc:
                self.after(0, lambda e=exc: self._log_line(f"[erro] {e}"))
            finally:
                def _done():
                    self._busy = False
                    self.refresh()
                self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def _render_report(self, report: dict) -> None:
        self._log_line(f"code_curation purgadas: {report.get('code_curation_removed', 0)}")
        self._log_line(f"image_curation purgadas: {report.get('image_curation_removed', 0)}")
        self._log_line(f"sidecars regerados: {report.get('regenerated', False)}")
        errs = report.get("errors") or []
        if errs:
            self._log_line("erros:")
            for e in errs:
                self._log_line(f"  - {e}")
        else:
            self._log_line("[ok] limpeza concluída sem erros.")
