from __future__ import annotations
import csv
import json
import logging
import re
import shutil
import subprocess
import sys
import tkinter as tk
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.models.core import (
    BackendRunResult, DocumentProfileReport, FileEntry,
    PipelineDecision, StudentProfile, SubjectProfile
)
from src.utils.helpers import (
    APP_NAME, DOCLING_CLI, EXAM_CATEGORIES, EXERCISE_CATEGORIES,
    HAS_PDFPLUMBER, HAS_PYMUPDF, HAS_PYMUPDF4LLM, IMAGE_CATEGORIES, MARKER_CLI,
    ensure_dir, file_size_mb, json_str, pages_to_marker_range,
    parse_page_range, safe_rel, slugify, write_text,
)

import pymupdf
import pymupdf4llm
import pdfplumber

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend architecture
# ---------------------------------------------------------------------------

class BackendContext:
    def __init__(self, root_dir: Path, raw_target: Path, entry: FileEntry, report: DocumentProfileReport):
        self.root_dir = root_dir
        self.raw_target = raw_target
        self.entry = entry
        self.report = report
        self.entry_id = entry.id()
        self.pages = parse_page_range(entry.page_range)

    def page_label(self) -> str:
        return self.entry.page_range.strip() or "all"


class ExtractionBackend:
    name = "base"
    layer = "base"

    def available(self) -> bool:
        return False

    def run(self, ctx: BackendContext) -> BackendRunResult:
        raise NotImplementedError


class PyMuPDF4LLMBackend(ExtractionBackend):
    name = "pymupdf4llm"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF4LLM

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf4llm"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        kwargs = {
            "pages": ctx.pages,
            "write_images": bool(ctx.entry.preserve_pdf_images_in_markdown),
            "image_path": str((ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id).resolve()),
            "force_ocr": bool(ctx.entry.force_ocr),
            "ocr_language": ctx.entry.ocr_language.replace(",", "+"),
            "page_separators": True,
        }
        if not ctx.entry.preserve_pdf_images_in_markdown:
            kwargs["write_images"] = False
            kwargs.pop("image_path", None)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        md = pymupdf4llm.to_markdown(str(ctx.raw_target), **kwargs)
        if isinstance(md, list):
            body = "\n\n".join(chunk.get("text", "") for chunk in md)
        else:
            body = md

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            asset_dir=safe_rel(ctx.root_dir / "staging" / "assets" / "inline-images" / ctx.entry_id, ctx.root_dir) if ctx.entry.preserve_pdf_images_in_markdown else None,
            notes=["Markdown gerado com PyMuPDF4LLM."],
        )


class PyMuPDFBackend(ExtractionBackend):
    name = "pymupdf"
    layer = "base"

    def available(self) -> bool:
        return HAS_PYMUPDF

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "pymupdf"
        ensure_dir(out_dir)
        out_path = out_dir / f"{ctx.entry_id}.md"

        doc = pymupdf.open(str(ctx.raw_target))
        target_pages = ctx.pages or list(range(doc.page_count))
        pieces = [f"# {ctx.entry.title}", ""]
        for i in target_pages:
            if i < 0 or i >= doc.page_count:
                continue
            page = doc[i]
            pieces.append(f"## Página {i + 1}")
            pieces.append("")
            text = page.get_text("text")
            text = re.sub(r"[ \t]+\n", "\n", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            pieces.append(text.strip())
            pieces.append("")
        body = "\n".join(pieces).strip() + "\n"

        write_text(out_path, wrap_frontmatter({
            "entry_id": ctx.entry_id,
            "title": ctx.entry.title,
            "backend": self.name,
            "source_pdf": safe_rel(ctx.raw_target, ctx.root_dir),
            "page_range": ctx.entry.page_range,
        }, body))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(out_path, ctx.root_dir),
            notes=["Markdown bruto gerado com PyMuPDF."],
        )


class DoclingCLIBackend(ExtractionBackend):
    name = "docling"
    layer = "advanced"

    def available(self) -> bool:
        return bool(DOCLING_CLI)

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "docling" / ctx.entry_id
        ensure_dir(out_dir)

        cmd = [
            DOCLING_CLI,
            str(ctx.raw_target),
            "--to", "md",
            "--output", str(out_dir),
            "--image-export-mode", "referenced",
            "--tables",
            "--ocr",
            "--ocr-lang", ctx.entry.ocr_language,
            "--table-mode", "accurate",
        ]

        if ctx.entry.force_ocr or ctx.report.suspected_scan:
            cmd.append("--force-ocr")
        if ctx.entry.formula_priority or ctx.report.suggested_profile in {"math_heavy", "exam_pdf"}:
            cmd.append("--enrich-formula")
        if ctx.report.suggested_profile in {"layout_heavy", "exam_pdf"}:
            cmd.append("--enrich-picture-classes")
        if ctx.report.suggested_profile == "layout_heavy":
            cmd.extend(["--image-export-mode", "referenced"])

        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                command=cmd,
                error=(proc.stderr or proc.stdout or "Docling CLI falhou")[-4000:],
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        metadata_path = out_dir / "docling-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Docling CLI."],
        )


class MarkerCLIBackend(ExtractionBackend):
    name = "marker"
    layer = "advanced"

    def available(self) -> bool:
        return bool(MARKER_CLI)

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "marker" / ctx.entry_id
        ensure_dir(out_dir)

        cmd = [
            MARKER_CLI,
            str(ctx.raw_target),
            "--output_format", "markdown",
            "--output_dir", str(out_dir),
        ]

        marker_range = pages_to_marker_range(ctx.pages)
        if marker_range:
            cmd.extend(["--page_range", marker_range])
        if ctx.entry.force_ocr or ctx.entry.formula_priority or ctx.report.suspected_scan:
            cmd.append("--force_ocr")

        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return BackendRunResult(
                name=self.name,
                layer=self.layer,
                status="error",
                command=cmd,
                error=(proc.stderr or proc.stdout or "Marker CLI falhou")[-4000:],
            )

        produced_md = sorted(out_dir.glob("**/*.md"))
        md_path = produced_md[0] if produced_md else None
        metadata_path = out_dir / "marker-run.json"
        write_text(metadata_path, json.dumps({
            "command": cmd,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-2000:],
        }, indent=2, ensure_ascii=False))

        return BackendRunResult(
            name=self.name,
            layer=self.layer,
            status="ok",
            markdown_path=safe_rel(md_path, ctx.root_dir),
            asset_dir=safe_rel(out_dir, ctx.root_dir),
            metadata_path=safe_rel(metadata_path, ctx.root_dir),
            command=cmd,
            notes=["Saída avançada gerada com Marker CLI."],
        )


# ---------------------------------------------------------------------------
# Selection / profiling
# ---------------------------------------------------------------------------

class BackendSelector:
    def __init__(self):
        self.backends: Dict[str, ExtractionBackend] = {
            "pymupdf4llm": PyMuPDF4LLMBackend(),
            "pymupdf": PyMuPDFBackend(),
            "docling": DoclingCLIBackend(),
            "marker": MarkerCLIBackend(),
        }

    def available_backends(self) -> Dict[str, bool]:
        return {name: backend.available() for name, backend in self.backends.items()}

    def decide(self, entry: FileEntry, report: DocumentProfileReport) -> PipelineDecision:
        mode = entry.processing_mode or "auto"
        effective_profile = entry.document_profile if entry.document_profile != "auto" else report.suggested_profile
        reasons: List[str] = []

        available = self.available_backends()

        def pick_first(names: Iterable[str]) -> Optional[str]:
            for name in names:
                if available.get(name):
                    return name
            return None

        base_backend: Optional[str] = None
        advanced_backend: Optional[str] = None

        if entry.preferred_backend != "auto" and available.get(entry.preferred_backend):
            preferred = entry.preferred_backend
            if preferred in {"docling", "marker"}:
                advanced_backend = preferred
                base_backend = pick_first(["pymupdf4llm", "pymupdf"])
                reasons.append(f"Backend preferido manualmente: {preferred}.")
            else:
                base_backend = preferred
                reasons.append(f"Backend base preferido manualmente: {preferred}.")

        if mode == "quick":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            reasons.append("Modo quick prioriza velocidade e baixo custo.")

        elif mode == "manual_assisted":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "layout_heavy", "scanned", "exam_pdf"}:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
            reasons.append("Modo manual_assisted gera base automática e exige revisão humana guiada.")

        elif mode == "high_fidelity":
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile == "math_heavy":
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                reasons.append("Documento math_heavy pede backend avançado para fórmulas.")
            elif effective_profile in {"layout_heavy", "scanned", "exam_pdf"}:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                reasons.append("Documento com layout/scan/exam pede backend avançado.")
            else:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                if advanced_backend:
                    reasons.append("Modo high_fidelity tenta saída avançada além da base.")

        else:  # auto
            base_backend = base_backend or pick_first(["pymupdf4llm", "pymupdf"])
            if effective_profile in {"math_heavy", "layout_heavy", "scanned", "exam_pdf"}:
                advanced_backend = advanced_backend or pick_first(["docling", "marker"])
                reasons.append(f"Modo auto detectou perfil {effective_profile} e ativou camada avançada.")
            else:
                reasons.append("Modo auto detectou documento geral; saída base é suficiente.")

        if entry.formula_priority and not advanced_backend:
            advanced_backend = pick_first(["docling", "marker"])
            if advanced_backend:
                reasons.append("formula_priority ativou backend avançado.")

        if not base_backend and advanced_backend:
            reasons.append("Sem backend base disponível; usando apenas backend avançado.")

        return PipelineDecision(
            entry_id=entry.id(),
            processing_mode=mode,
            effective_profile=effective_profile,
            base_backend=base_backend,
            advanced_backend=advanced_backend,
            reasons=reasons,
        )


# ---------------------------------------------------------------------------
# Repo builder
# ---------------------------------------------------------------------------

class RepoBuilder:
    def __init__(self, root_dir: Path, course_meta: Dict[str, str], entries: List[FileEntry],
                 options: Dict[str, object], *,
                 student_profile: Optional[StudentProfile] = None,
                 subject_profile: Optional[SubjectProfile] = None):
        self.root_dir = root_dir
        self.course_meta = course_meta
        self.entries = entries
        self.options = options
        self.student_profile = student_profile
        self.subject_profile = subject_profile
        self.logs: List[Dict[str, object]] = []
        self.selector = BackendSelector()

    def build(self) -> None:
        logger.info("Building repository at %s", self.root_dir)
        self._create_structure()
        self._write_root_files()

        manifest = {
            "app": APP_NAME,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "course": self.course_meta,
            "options": self.options,
            "environment": {
                "python": sys.version.split()[0],
                "pymupdf": HAS_PYMUPDF,
                "pymupdf4llm": HAS_PYMUPDF4LLM,
                "pdfplumber": HAS_PDFPLUMBER,
                "docling_cli": bool(DOCLING_CLI),
                "marker_cli": bool(MARKER_CLI),
            },
            "entries": [],
        }

        for entry in self.entries:
            logger.info("Processing entry: %s (%s)", entry.title, entry.file_type)
            item_result = self._process_entry(entry)
            manifest["entries"].append(item_result)

        manifest["logs"] = self.logs
        write_text(self.root_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)
        logger.info("Repository built successfully at %s", self.root_dir)

    def _create_structure(self) -> None:
        dirs = [
            "system",
            "course",
            "content/units",
            "content/concepts",
            "content/summaries",
            "content/references",
            "content/curated",
            "exercises/lists",
            "exercises/solved",
            "exercises/index",
            "exams/past-exams",
            "exams/answer-keys",
            "exams/exam-index",
            "student",
            "scripts",
            "raw/pdfs/material-de-aula",
            "raw/pdfs/provas",
            "raw/pdfs/listas",
            "raw/pdfs/gabaritos",
            "raw/pdfs/cronograma",
            "raw/pdfs/referencias",
            "raw/pdfs/bibliografia",
            "raw/pdfs/fotos-de-prova",
            "raw/pdfs/outros",
            "raw/images/fotos-de-prova",
            "raw/images/provas",
            "raw/images/material-de-aula",
            "raw/images/outros",
            "staging/markdown-auto/pymupdf4llm",
            "staging/markdown-auto/pymupdf",
            "staging/markdown-auto/docling",
            "staging/markdown-auto/marker",
            "staging/assets/images",
            "staging/assets/inline-images",
            "staging/assets/page-previews",
            "staging/assets/tables",
            "staging/assets/table-detections",
            "manual-review/pdfs",
            "manual-review/images",
            "build/claude-knowledge",
        ]
        for d in dirs:
            ensure_dir(self.root_dir / d)

    def _write_root_files(self) -> None:
        course_slug = self.course_meta["course_slug"]

        # ── COURSE_IDENTITY ──────────────────────────────────────────
        write_text(
            self.root_dir / "course" / "COURSE_IDENTITY.md",
            f"""---
course_slug: {course_slug}
course_name: {self.course_meta['course_name']}
semester: {self.course_meta['semester']}
professor: {self.course_meta['professor']}
institution: {self.course_meta['institution']}
created_at: {datetime.now().isoformat(timespec='seconds')}
---

# COURSE_IDENTITY

## Disciplina
- Nome: {self.course_meta['course_name']}
- Slug: {course_slug}
- Semestre: {self.course_meta['semester']}
- Professor: {self.course_meta['professor']}
- Instituição: {self.course_meta['institution']}

## Objetivo
Este repositório organiza o conhecimento da disciplina em formato rastreável,
curado e reutilizável para um tutor acadêmico baseado no Claude.
""",
        )

        # ── System files ─────────────────────────────────────────────
        write_text(self.root_dir / "system" / "PDF_CURATION_GUIDE.md", pdf_curation_guide())
        write_text(self.root_dir / "system" / "BACKEND_ARCHITECTURE.md", backend_architecture_md())
        write_text(self.root_dir / "system" / "BACKEND_POLICY.yaml", backend_policy_yaml(self.options))
        write_text(self.root_dir / "system" / "TUTOR_POLICY.md", tutor_policy_md())
        write_text(self.root_dir / "system" / "PEDAGOGY.md", pedagogy_md())
        write_text(self.root_dir / "system" / "MODES.md", modes_md())
        write_text(self.root_dir / "system" / "OUTPUT_TEMPLATES.md", output_templates_md())

        # ── Course files ─────────────────────────────────────────────
        write_text(self.root_dir / "course" / "COURSE_MAP.md",
                   course_map_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "course" / "GLOSSARY.md",
                   glossary_md(self.course_meta, self.subject_profile))

        # ── Student files ─────────────────────────────────────────────
        write_text(self.root_dir / "student" / "STUDENT_STATE.md",
                   student_state_md(self.course_meta, self.student_profile))
        write_text(self.root_dir / "student" / "PROGRESS_SCHEMA.md", progress_schema_md())

        # ── Student profile ───────────────────────────────────────────
        if self.student_profile:
            write_text(self.root_dir / "student" / "STUDENT_PROFILE.md",
                       student_profile_md(self.student_profile))

        # ── Syllabus ──────────────────────────────────────────────────
        if self.subject_profile and self.subject_profile.syllabus:
            write_text(self.root_dir / "course" / "SYLLABUS.md",
                       syllabus_md(self.subject_profile))

        # ── Bibliography ──────────────────────────────────────────────
        bib_entries = [e for e in self.entries if e.category == "bibliografia"]
        write_text(self.root_dir / "content" / "BIBLIOGRAPHY.md",
                   bibliography_md(self.course_meta, bib_entries, self.subject_profile))

        # ── Exam & Exercise indexes ───────────────────────────────────
        exam_entries = [e for e in self.entries if e.category in EXAM_CATEGORIES]
        if exam_entries:
            write_text(self.root_dir / "exams" / "EXAM_INDEX.md",
                       exam_index_md(self.course_meta, exam_entries))

        exercise_entries = [e for e in self.entries if e.category in EXERCISE_CATEGORIES]
        if exercise_entries:
            write_text(self.root_dir / "exercises" / "EXERCISE_INDEX.md",
                       exercise_index_md(self.course_meta, exercise_entries))

        # ── Root files ────────────────────────────────────────────────
        write_text(self.root_dir / "README.md", root_readme(self.course_meta))
        write_text(self.root_dir / ".gitignore", "__pycache__/\n*.pyc\n.DS_Store\nThumbs.db\n")

        # ── Claude Project instructions (replaces INSTRUCOES_DO_GPT.txt)
        instructions = generate_claude_project_instructions(
            self.course_meta, self.student_profile, self.subject_profile
        )
        write_text(self.root_dir / "INSTRUCOES_CLAUDE_PROJETO.md", instructions)

    def _write_source_registry(self, manifest: Dict[str, object]) -> None:
        lines = [
            f"generated_at: {manifest['generated_at']}",
            "sources:",
        ]
        for item in manifest["entries"]:
            lines.extend(
                [
                    f"  - id: {item['id']}",
                    f"    title: {json_str(item['title'])}",
                    f"    category: {item['category']}",
                    f"    file_type: {item['file_type']}",
                    f"    source_path: {json_str(item['source_path'])}",
                    f"    raw_target: {json_str(item.get('raw_target'))}",
                    f"    processing_mode: {item.get('processing_mode', 'auto')}",
                    f"    effective_profile: {item.get('effective_profile', 'general')}",
                    f"    include_in_bundle: {str(item.get('include_in_bundle', True)).lower()}",
                    f"    professor_signal: {json_str(item.get('professor_signal', ''))}",
                ]
            )
        write_text(self.root_dir / "course" / "SOURCE_REGISTRY.yaml", "\n".join(lines) + "\n")

    def _write_bundle_seed(self, manifest: Dict[str, object]) -> None:
        selected = [e for e in manifest["entries"] if e.get("include_in_bundle")]
        seed = {
            "generated_at": manifest["generated_at"],
            "course_slug": self.course_meta["course_slug"],
            "target_platform": "claude-projects",
            "bundle_candidates": [
                {
                    "id": e["id"],
                    "title": e["title"],
                    "category": e["category"],
                    "preferred_manual_review": e.get("manual_review"),
                    "base_markdown": e.get("base_markdown"),
                    "advanced_markdown": e.get("advanced_markdown"),
                    "effective_profile": e.get("effective_profile"),
                }
                for e in selected
            ],
        }
        write_text(
            self.root_dir / "build" / "claude-knowledge" / "bundle.seed.json",
            json.dumps(seed, indent=2, ensure_ascii=False)
        )

    def _write_build_report(self, manifest: Dict[str, object]) -> None:
        report = [
            "# BUILD_REPORT",
            "",
            f"- generated_at: {manifest['generated_at']}",
            f"- target_platform: Claude Projects",
            f"- pymupdf: {HAS_PYMUPDF}",
            f"- pymupdf4llm: {HAS_PYMUPDF4LLM}",
            f"- pdfplumber: {HAS_PDFPLUMBER}",
            f"- docling_cli: {bool(DOCLING_CLI)}",
            f"- marker_cli: {bool(MARKER_CLI)}",
            "",
            "## Como usar com Claude Projects",
            "1. Crie um Projeto no Claude.ai para esta disciplina",
            "2. Cole o conteúdo de `INSTRUCOES_CLAUDE_PROJETO.md` no system prompt do Projeto",
            "3. Conecte este repositório GitHub ao Projeto (Settings → GitHub)",
            "4. Ou faça upload manual dos arquivos de `build/claude-knowledge/`",
            "",
            "## Regras práticas de curadoria",
            "- PDFs simples: camada base costuma bastar.",
            "- PDFs com fórmulas, scans, layout complexo ou provas: camada avançada + revisão manual.",
            "- O conhecimento final do tutor deve sair de `manual-review/` e depois ser promovido.",
            "- Atualizar `student/STUDENT_STATE.md` após cada sessão de estudo.",
        ]
        write_text(self.root_dir / "BUILD_REPORT.md", "\n".join(report) + "\n")

    def _process_entry(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "id": entry.id(),
            "title": entry.title,
            "category": entry.category,
            "file_type": entry.file_type,
            "source_path": entry.source_path,
            "tags": entry.tags,
            "notes": entry.notes,
            "professor_signal": entry.professor_signal,
            "include_in_bundle": entry.include_in_bundle,
            "relevant_for_exam": entry.relevant_for_exam,
            "processing_mode": entry.processing_mode,
            "document_profile": entry.document_profile,
            "preferred_backend": entry.preferred_backend,
        }

        src = Path(entry.source_path)
        if entry.file_type != "url" and not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")

        if entry.file_type == "url":
            item.update(self._process_url(entry))
            return item

        safe_name = f"{entry.id()}{src.suffix.lower()}"

        if entry.file_type == "pdf":
            raw_target = self.root_dir / "raw" / "pdfs" / entry.category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_pdf(entry, raw_target))
        else:
            image_category = entry.category if entry.category in IMAGE_CATEGORIES else "outros"
            raw_target = self.root_dir / "raw" / "images" / image_category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_image(entry, raw_target))

        return item

    def _process_url(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "document_report": None, "pipeline_decision": None,
            "base_markdown": None, "advanced_markdown": None,
            "advanced_backend": None, "base_backend": "url_fetcher",
            "manual_review": None,
        }
        url_dest = self.root_dir / "staging" / "markdown-auto" / "url_fetcher"
        ensure_dir(url_dest)
        md_file = url_dest / f"{entry.id()}.md"
        url = entry.source_path
        markdown_content = f"# {entry.title}\n\n**Link:** [{url}]({url})\n\n"
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                content_type = response.info().get_content_charset('utf-8')
                html = response.read().decode(content_type, errors='replace')
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator='\n', strip=True)
                markdown_content += "## Conteúdo Extraído\n\n```text\n"
                markdown_content += text[:15000]
                if len(text) > 15000:
                    markdown_content += "\n... (conteúdo truncado)\n"
                markdown_content += "\n```\n"
            except ImportError:
                markdown_content += "> BeautifulSoup não instalado. Conteúdo de texto não foi processado.\n"
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "ok"})
        except Exception as e:
            logger.warning(f"Failed to fetch content from URL {url}: {e}")
            markdown_content += f"> Não foi possível carregar o conteúdo: {e}\n"
            self.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "error", "error": str(e)})
        write_text(md_file, markdown_content)
        item["base_markdown"] = safe_rel(md_file, self.root_dir)
        manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
        write_text(manual, manual_pdf_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        return item

    def _process_pdf(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        item: Dict[str, object] = {
            "document_report": None, "pipeline_decision": None,
            "base_markdown": None, "advanced_markdown": None,
            "advanced_backend": None, "base_backend": None,
            "images_dir": None, "tables_dir": None,
            "page_previews_dir": None, "table_detection_dir": None,
            "manual_review": None,
        }
        report = self._profile_pdf(raw_target, entry)
        decision = self.selector.decide(entry, report)
        item["document_report"] = asdict(report)
        item["pipeline_decision"] = asdict(decision)
        item["effective_profile"] = decision.effective_profile
        item["base_backend"] = decision.base_backend
        item["advanced_backend"] = decision.advanced_backend
        ctx = BackendContext(self.root_dir, raw_target, entry, report)
        if decision.base_backend:
            backend = self.selector.backends[decision.base_backend]
            result = backend.run(ctx)
            self._log_backend_result(entry.id(), result)
            if result.status == "ok":
                item["base_markdown"] = result.markdown_path
            else:
                logger.warning("Base backend %s failed for %s: %s", decision.base_backend, entry.id(), result.error)
                item.setdefault("backend_errors", []).append({decision.base_backend: result.error})
        if decision.advanced_backend:
            backend = self.selector.backends[decision.advanced_backend]
            result = backend.run(ctx)
            self._log_backend_result(entry.id(), result)
            if result.status == "ok":
                item["advanced_markdown"] = result.markdown_path
                item["advanced_asset_dir"] = result.asset_dir
                item["advanced_metadata_path"] = result.metadata_path
            else:
                logger.warning("Advanced backend %s failed for %s: %s", decision.advanced_backend, entry.id(), result.error)
                item.setdefault("backend_errors", []).append({decision.advanced_backend: result.error})
        if HAS_PYMUPDF and entry.extract_images:
            try:
                images_dir = self.root_dir / "staging" / "assets" / "images" / entry.id()
                count = self._extract_pdf_images(raw_target, images_dir, pages=parse_page_range(entry.page_range))
                item["images_dir"] = safe_rel(images_dir, self.root_dir)
                self.logs.append({"entry": entry.id(), "step": "extract_images", "status": "ok", "count": count})
            except Exception as e:
                logger.error("Image extraction failed for %s: %s", entry.id(), e)
                self.logs.append({"entry": entry.id(), "step": "extract_images", "status": "error", "error": str(e)})
        if HAS_PYMUPDF and entry.export_page_previews:
            try:
                previews_dir = self.root_dir / "staging" / "assets" / "page-previews" / entry.id()
                count = self._export_page_previews(raw_target, previews_dir, pages=parse_page_range(entry.page_range))
                item["page_previews_dir"] = safe_rel(previews_dir, self.root_dir)
                self.logs.append({"entry": entry.id(), "step": "page_previews", "status": "ok", "count": count})
            except Exception as e:
                logger.error("Page preview export failed for %s: %s", entry.id(), e)
                self.logs.append({"entry": entry.id(), "step": "page_previews", "status": "error", "error": str(e)})
        if entry.extract_tables:
            if HAS_PDFPLUMBER:
                try:
                    tables_dir = self.root_dir / "staging" / "assets" / "tables" / entry.id()
                    count = self._extract_tables_pdfplumber(raw_target, tables_dir, pages=parse_page_range(entry.page_range))
                    item["tables_dir"] = safe_rel(tables_dir, self.root_dir)
                    self.logs.append({"entry": entry.id(), "step": "extract_tables_pdfplumber", "status": "ok", "count": count})
                except Exception as e:
                    logger.error("Table extraction (pdfplumber) failed for %s: %s", entry.id(), e)
                    self.logs.append({"entry": entry.id(), "step": "extract_tables_pdfplumber", "status": "error", "error": str(e)})
            if HAS_PYMUPDF:
                try:
                    det_dir = self.root_dir / "staging" / "assets" / "table-detections" / entry.id()
                    count = self._detect_tables_pymupdf(raw_target, det_dir, pages=parse_page_range(entry.page_range))
                    item["table_detection_dir"] = safe_rel(det_dir, self.root_dir)
                    self.logs.append({"entry": entry.id(), "step": "detect_tables_pymupdf", "status": "ok", "count": count})
                except Exception as e:
                    logger.error("Table detection (pymupdf) failed for %s: %s", entry.id(), e)
                    self.logs.append({"entry": entry.id(), "step": "detect_tables_pymupdf", "status": "error", "error": str(e)})
        manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
        write_text(manual, manual_pdf_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        return item

    def _process_image(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        item: Dict[str, object] = {"manual_review": None}
        manual = self.root_dir / "manual-review" / "images" / f"{entry.id()}.md"
        write_text(manual, manual_image_review_template(entry, raw_target, self.root_dir))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        self.logs.append({"entry": entry.id(), "step": "image_import", "status": "ok"})
        return item

    def _profile_pdf(self, pdf_path: Path, entry: FileEntry) -> DocumentProfileReport:
        report = DocumentProfileReport()
        if not HAS_PYMUPDF:
            report.suggested_profile = entry.document_profile if entry.document_profile != "auto" else "general"
            report.notes.append("PyMuPDF não disponível; perfil automático limitado.")
            return report
        doc = pymupdf.open(str(pdf_path))
        pages = parse_page_range(entry.page_range) or list(range(doc.page_count))
        pages = [p for p in pages if 0 <= p < doc.page_count]
        report.page_count = len(pages)
        total_text = 0
        total_images = 0
        table_candidates = 0
        low_text_pages = 0
        for page_num in pages:
            page = doc[page_num]
            text = page.get_text("text") or ""
            total_text += len(text.strip())
            images = page.get_images(full=True) or []
            total_images += len(images)
            try:
                tables = page.find_tables()
                table_candidates += len(getattr(tables, "tables", []) or [])
            except Exception:
                pass
            if len(text.strip()) < 60 and len(images) > 0:
                low_text_pages += 1
        report.text_chars = total_text
        report.images_count = total_images
        report.table_candidates = table_candidates
        report.text_density = round(total_text / max(report.page_count, 1), 2)
        report.suspected_scan = (low_text_pages / max(report.page_count, 1)) >= 0.5 and total_images > 0
        if entry.document_profile != "auto":
            report.suggested_profile = entry.document_profile
            report.notes.append("Perfil definido manualmente pelo usuário.")
            return report
        name_hint = f"{entry.title} {entry.tags} {entry.notes}".lower()
        if report.suspected_scan:
            report.suggested_profile = "scanned"
            report.notes.append("Muitas páginas com pouco texto e imagens presentes: provável scan.")
        elif entry.category == "provas" or "prova" in name_hint or "questão" in name_hint or "questao" in name_hint:
            report.suggested_profile = "exam_pdf"
            report.notes.append("Detectado como material de prova/exame.")
        elif entry.formula_priority or re.search(r"\b(latex|equação|equation|fórmula|teorema|prova formal|indução)\b", name_hint):
            report.suggested_profile = "math_heavy"
            report.notes.append("Sinais de conteúdo matemático/formal.")
        elif report.table_candidates >= 2 or report.images_count >= max(3, report.page_count):
            report.suggested_profile = "layout_heavy"
            report.notes.append("Layout com tabelas/imagens relevantes.")
        else:
            report.suggested_profile = "general"
            report.notes.append("Documento geral detectado.")
        return report

    def _log_backend_result(self, entry_id: str, result: BackendRunResult) -> None:
        payload = {
            "entry": entry_id, "step": result.name, "layer": result.layer,
            "status": result.status, "markdown_path": result.markdown_path,
            "asset_dir": result.asset_dir, "metadata_path": result.metadata_path,
            "notes": result.notes,
        }
        if result.command:
            payload["command"] = result.command
        if result.error:
            payload["error"] = result.error
        self.logs.append(payload)

    def _extract_pdf_images(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        doc = pymupdf.open(str(pdf_path))
        target_pages = pages or list(range(doc.page_count))
        count = 0
        for page_num in target_pages:
            if not (0 <= page_num < doc.page_count):
                continue
            page = doc[page_num]
            for img_idx, img in enumerate(page.get_images(full=True), start=1):
                xref = img[0]
                image = doc.extract_image(xref)
                ext = image.get("ext", "png")
                data = image["image"]
                fname = out_dir / f"page-{page_num + 1:03d}-img-{img_idx:02d}.{ext}"
                fname.write_bytes(data)
                count += 1
        return count

    def _export_page_previews(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        doc = pymupdf.open(str(pdf_path))
        target_pages = pages or list(range(doc.page_count))
        count = 0
        for page_num in target_pages:
            if not (0 <= page_num < doc.page_count):
                continue
            page = doc[page_num]
            pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
            out = out_dir / f"page-{page_num + 1:03d}.png"
            pix.save(str(out))
            count += 1
        return count

    def _extract_tables_pdfplumber(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        count = 0
        with pdfplumber.open(str(pdf_path)) as pdf:
            selected = pages or list(range(len(pdf.pages)))
            for page_num in selected:
                if not (0 <= page_num < len(pdf.pages)):
                    continue
                page = pdf.pages[page_num]
                tables = page.extract_tables() or []
                for table_idx, table in enumerate(tables, start=1):
                    normalized = [
                        [("" if cell is None else str(cell).strip()) for cell in row]
                        for row in table if row and any(cell not in (None, "", " ") for cell in row)
                    ]
                    if not normalized:
                        continue
                    csv_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.csv"
                    ensure_dir(csv_path.parent)
                    with csv_path.open("w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerows(normalized)
                    md_path = out_dir / f"page-{page_num + 1:03d}-table-{table_idx:02d}.md"
                    write_text(md_path, rows_to_markdown_table(normalized))
                    count += 1
        return count

    def _detect_tables_pymupdf(self, pdf_path: Path, out_dir: Path, pages: Optional[List[int]] = None) -> int:
        ensure_dir(out_dir)
        doc = pymupdf.open(str(pdf_path))
        selected = pages or list(range(doc.page_count))
        count = 0
        for page_num in selected:
            if not (0 <= page_num < doc.page_count):
                continue
            page = doc[page_num]
            try:
                tables = page.find_tables()
                found = getattr(tables, "tables", []) or []
                if not found:
                    continue
                serializable = []
                for idx, tbl in enumerate(found, start=1):
                    bbox = getattr(tbl, "bbox", None)
                    rows = []
                    try:
                        extracted = tbl.extract() or []
                        rows = [["" if cell is None else str(cell) for cell in row] for row in extracted]
                    except Exception:
                        pass
                    serializable.append({"table_index": idx, "bbox": list(bbox) if bbox else None, "rows": rows})
                meta_path = out_dir / f"page-{page_num + 1:03d}.json"
                write_text(meta_path, json.dumps(serializable, indent=2, ensure_ascii=False))
                count += len(serializable)
            except Exception:
                continue
        return count

    def incremental_build(self) -> None:
        """Adiciona novos arquivos a um repositório existente sem recriar do zero."""
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.info("No existing manifest found, falling back to full build.")
            self.build()
            return

        logger.info("Incremental build at %s", self.root_dir)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
        new_entries = [e for e in self.entries if e.source_path not in existing_sources]
        if not new_entries:
            logger.info("No new entries to process.")
            return

        logger.info("Processing %d new entries (skipping %d existing).",
                     len(new_entries), len(self.entries) - len(new_entries))

        self._create_structure()

        for entry in new_entries:
            logger.info("Processing new entry: %s (%s)", entry.title, entry.file_type)
            item_result = self._process_entry(entry)
            manifest["entries"].append(item_result)

        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).extend(self.logs)

        # Atualiza bibliography com novos entries
        bib_entries = [e for e in self.entries if e.category == "bibliografia"]
        if bib_entries or getattr(self.subject_profile, "teaching_plan", ""):
            write_text(self.root_dir / "content" / "BIBLIOGRAPHY.md",
                       bibliography_md(self.course_meta, bib_entries, self.subject_profile))

        # Atualiza exam & exercise indexes
        all_entries = [FileEntry.from_dict(e) for e in manifest.get("entries", [])]
        exam_entries = [e for e in all_entries if e.category in EXAM_CATEGORIES]
        if exam_entries:
            write_text(self.root_dir / "exams" / "EXAM_INDEX.md",
                       exam_index_md(self.course_meta, exam_entries))
        exercise_entries = [e for e in all_entries if e.category in EXERCISE_CATEGORIES]
        if exercise_entries:
            write_text(self.root_dir / "exercises" / "EXERCISE_INDEX.md",
                       exercise_index_md(self.course_meta, exercise_entries))

        # Regenera arquivos que dependem do perfil da matéria/aluno
        instructions = generate_claude_project_instructions(
            self.course_meta, self.student_profile, self.subject_profile
        )
        write_text(self.root_dir / "INSTRUCOES_CLAUDE_PROJETO.md", instructions)

        write_text(self.root_dir / "course" / "COURSE_MAP.md",
                   course_map_md(self.course_meta, self.subject_profile))
        write_text(self.root_dir / "course" / "GLOSSARY.md",
                   glossary_md(self.course_meta, self.subject_profile))

        if self.subject_profile and self.subject_profile.syllabus:
            write_text(self.root_dir / "course" / "SYLLABUS.md",
                       syllabus_md(self.subject_profile))

        if self.student_profile:
            write_text(self.root_dir / "student" / "STUDENT_PROFILE.md",
                       student_profile_md(self.student_profile))

        # Atualiza student state timestamp
        state_path = self.root_dir / "student" / "STUDENT_STATE.md"
        if state_path.exists():
            content = state_path.read_text(encoding="utf-8")
            content = re.sub(
                r"last_updated:.*",
                f"last_updated: {datetime.now().strftime('%Y-%m-%d')}",
                content
            )
            state_path.write_text(content, encoding="utf-8")

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)
        logger.info("Incremental build completed. %d new entries added.", len(new_entries))

    def process_single(self, entry: "FileEntry") -> None:
        """
        Processa um único FileEntry e adiciona ao repositório existente.
        Chamado pelo botão '⚡ Processar' da UI para processar item a item.
        Se o repositório ainda não existir, cria a estrutura primeiro.
        """
        manifest_path = self.root_dir / "manifest.json"

        # Garante estrutura mínima existente
        self._create_structure()

        # Carrega ou inicializa manifest
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        else:
            # Primeiro item — cria manifest + arquivos raiz
            self._write_root_files()
            manifest = {
                "app": APP_NAME,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "course": self.course_meta,
                "options": self.options,
                "environment": {
                    "python": sys.version.split()[0],
                    "pymupdf": HAS_PYMUPDF,
                    "pymupdf4llm": HAS_PYMUPDF4LLM,
                    "pdfplumber": HAS_PDFPLUMBER,
                    "docling_cli": bool(DOCLING_CLI),
                    "marker_cli": bool(MARKER_CLI),
                },
                "entries": [],
                "logs": [],
            }

        # Verifica duplicata por source_path
        existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}
        if entry.source_path in existing_sources:
            logger.info("Entry already processed, skipping: %s", entry.source_path)
            return

        logger.info("Processing single entry: %s (%s)", entry.title, entry.file_type)
        item_result = self._process_entry(entry)
        manifest["entries"].append(item_result)
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).extend(self.logs)
        self.logs = []  # reset para próxima chamada

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)
        logger.info("Single entry processed: %s", entry.id())

    def unprocess(self, entry_id: str) -> bool:
        """
        Remove todos os arquivos gerados para um entry_id e o retira do manifest.
        Chamado pelo botão '🗑 Limpar Processamento' da UI.
        Retorna True se removeu com sucesso, False caso contrário.
        """
        manifest_path = self.root_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("No manifest found at %s", manifest_path)
            return False

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        target = next((e for e in manifest["entries"] if e.get("id") == entry_id), None)
        if not target:
            logger.warning("Entry not found in manifest: %s", entry_id)
            return False

        paths_to_remove: List[str] = []
        for key in ["raw_target", "base_markdown", "advanced_markdown", "manual_review",
                    "images_dir", "tables_dir", "page_previews_dir", "table_detection_dir",
                    "advanced_asset_dir"]:
            val = target.get(key)
            if val:
                paths_to_remove.append(val)

        removed_count = 0
        for rel_path in paths_to_remove:
            full = self.root_dir / rel_path
            try:
                if full.is_dir():
                    shutil.rmtree(full)
                    removed_count += 1
                elif full.is_file():
                    full.unlink()
                    removed_count += 1
            except Exception as e:
                logger.warning("Could not remove %s: %s", full, e)

        manifest["entries"] = [e for e in manifest["entries"] if e.get("id") != entry_id]
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")

        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        logger.info("Unprocessed entry %s (%d files removed)", entry_id, removed_count)
        return True


# ---------------------------------------------------------------------------
# Free functions — Claude Project instructions (replaces generate_system_prompt)
# ---------------------------------------------------------------------------

def generate_claude_project_instructions(
    course_meta: dict,
    student_profile=None,
    subject_profile=None
) -> str:
    """
    Gera o system prompt no formato ideal para Claude Projects.
    Resultado: INSTRUCOES_CLAUDE_PROJETO.md
    Cole este conteúdo no campo 'Instructions' do Projeto no Claude.ai.
    """
    course_name = course_meta.get("course_name", "Curso")
    professor = course_meta.get("professor", "")
    institution = course_meta.get("institution", "")
    semester = course_meta.get("semester", "")

    nick = "Aluno"
    personality_block = ""
    if student_profile and student_profile.full_name:
        nick = student_profile.nickname or student_profile.full_name
        if student_profile.personality:
            personality_block = f"\n**Estilo de aprendizado do aluno:** {student_profile.personality}\n"

    schedule_block = ""
    if subject_profile and subject_profile.schedule:
        schedule_block = f"\n**Horário:** {subject_profile.schedule}"

    return f"""# Instruções do Tutor — {course_name}

## Identidade

Você é o tutor acadêmico da disciplina **{course_name}**, ministrada pelo professor **{professor}** na **{institution}**, semestre **{semester}**.

Chame o aluno de **{nick}**.{personality_block}{schedule_block}

## Arquivos de referência deste Projeto

Antes de responder, consulte os arquivos relevantes abaixo. Eles são sua fonte de verdade — não invente conteúdo que não esteja neles.

| Arquivo | Quando consultar |
|---|---|
| `system/TUTOR_POLICY.md` | Sempre — regras de comportamento |
| `system/PEDAGOGY.md` | Ao explicar qualquer conceito |
| `system/MODES.md` | Para identificar o modo da sessão |
| `system/OUTPUT_TEMPLATES.md` | Para formatar respostas |
| `course/COURSE_IDENTITY.md` | Dados gerais da disciplina |
| `course/COURSE_MAP.md` | Ordem dos tópicos e dependências |
| `course/SYLLABUS.md` | Cronograma e datas |
| `course/GLOSSARY.md` | Terminologia da disciplina |
| `student/STUDENT_STATE.md` | Estado atual do aluno — SEMPRE consulte |
| `student/STUDENT_PROFILE.md` | Perfil e estilo do aluno |
| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |
| `content/` | Material de aula curado |
| `exercises/` | Listas de exercícios |
| `exams/` | Provas anteriores e gabaritos |

## Modos de operação

Identifique o modo da sessão pela frase do aluno e ajuste seu comportamento:

- **`study`** — "quero entender X", "explica Y" → ensinar do zero
- **`assignment`** — "tenho uma lista", "exercício X" → guiar sem entregar tudo
- **`exam_prep`** — "prova semana que vem", "revisão" → foco em incidência e padrões; provas são cumulativas com peso maior no conteúdo mais recente
- **`class_companion`** — "estou na aula", "o prof falou X" → resumir e contextualizar

Se o modo não for claro, pergunte: *"Você quer entender o conceito, resolver um exercício ou revisar para prova?"*

## Lógica de escopo das provas

As provas são **cumulativas com peso progressivo**. Sempre que entrar em modo `exam_prep`, identifique qual prova está próxima via `course/SYLLABUS.md` e aplique esta lógica:

| Prova | Escopo total | Foco principal | Foco secundário |
|---|---|---|---|
| P1 | Início → P1 | Todo o conteúdo (100%) | — |
| P2 | Início → P2 | Conteúdo entre P1 e P2 (~70%) | Conteúdo pré-P1 (~30%) |
| P3 | Início → P3 | Conteúdo entre P2 e P3 (~70%) | P1→P2 (~20%), pré-P1 (~10%) |

**Regra:** comece sempre pelos tópicos do período mais recente. Sinalize claramente o que é foco principal vs secundário antes de iniciar a revisão.

## Regras fundamentais

1. **Nunca invente** conteúdo não presente nos arquivos do Projeto
2. **Sempre cite** o arquivo de origem ao referenciar conteúdo
3. **Consulte `STUDENT_STATE.md`** antes de responder — não repita o que já foi explicado
4. **Não entregue** a resposta de exercícios de imediato — guie o raciocínio
5. **Ao final de cada sessão**, sugira atualizar `student/STUDENT_STATE.md`

## Atualização de estado

Ao final de cada sessão de estudo, gere um bloco para atualizar `student/STUDENT_STATE.md`:

```
## Atualização sugerida para STUDENT_STATE.md
- Tópico estudado: [tópico]
- Status: [compreendido / em progresso / com dúvidas]
- Dúvidas pendentes: [lista]
- Próximo passo sugerido: [próximo tópico]
```

O aluno faz o commit no GitHub. Na próxima sessão, o estado estará atualizado automaticamente.
"""


# Mantém compatibilidade com código legado que chame generate_system_prompt
def generate_system_prompt(course_meta, student_profile=None, subject_profile=None) -> str:
    return generate_claude_project_instructions(course_meta, student_profile, subject_profile)


# ---------------------------------------------------------------------------
# Free functions — Pedagogical file generators
# ---------------------------------------------------------------------------

def tutor_policy_md() -> str:
    return """# TUTOR_POLICY

## Propósito
Define as regras de comportamento do tutor acadêmico.
Este arquivo é lido pelo Claude antes de responder qualquer pergunta.

## Regras de comportamento

### O que o tutor SEMPRE faz
- Consulta `STUDENT_STATE.md` antes de explicar qualquer tópico
- Cita o arquivo de origem ao usar conteúdo curado
- Adapta a profundidade da explicação ao nível atual do aluno
- Conecta cada conceito novo ao que o aluno já estudou
- Sinaliza quando um tópico tem alta incidência em provas

### O que o tutor NUNCA faz
- Inventa conteúdo não presente nos arquivos do Projeto
- Entrega a resposta de exercícios sem guiar o raciocínio
- Avança para tópico novo sem confirmar entendimento do atual
- Repete explicação idêntica se o aluno já entendeu
- Ignora o progresso registrado em `STUDENT_STATE.md`

### Ao receber uma pergunta ambígua
Identifique o modo antes de responder:
> "Você quer entender o conceito, resolver um exercício ou revisar para prova?"

### Ao detectar erro conceitual do aluno
1. Não corrija abruptamente
2. Faça uma pergunta que revele a inconsistência
3. Guie o aluno ao raciocínio correto
4. Confirme a compreensão antes de continuar

### Qualidade das respostas
- Use LaTeX para fórmulas: `$f(x)$` inline, `$$...$$` em bloco
- Use code blocks para código
- Prefira exemplos concretos antes de definições formais
- Máximo de 3 conceitos novos por resposta
"""


def pedagogy_md() -> str:
    return """# PEDAGOGY

## Estrutura padrão de explicação

Para cada conceito novo, siga esta sequência:

1. **Contexto** — Por que este conceito existe? Que problema resolve?
2. **Definição** — O que é, em termos precisos
3. **Intuição** — Como pensar sobre isso sem formalismo
4. **Exemplo mínimo** — O caso mais simples possível
5. **Aplicação** — Como aparece na disciplina / em computação
6. **Erros comuns** — O que os alunos costumam confundir
7. **Exercício guiado** — Uma pergunta para o aluno aplicar
8. **Resumo** — Uma frase que captura a essência

## Adaptação de profundidade

| Situação | Ajuste |
|---|---|
| Aluno nunca viu o tópico | Comece pelo contexto e intuição |
| Aluno tem dúvida pontual | Vá direto ao ponto de dúvida |
| Aluno preparando prova | Foque em erros comuns e formatos de questão |
| Aluno resolvendo exercício | Guie sem revelar resposta |

## Princípios pedagógicos

- **Concretude antes da abstração** — Exemplo antes de definição
- **Andaime** — Construa sobre o que o aluno já sabe
- **Verificação ativa** — Pergunte antes de continuar
- **Espaçamento** — Reforce tópicos anteriores ao introduzir novos
- **Erros como dados** — Erros do aluno revelam onde focar

## Quando usar provas anteriores

Ao explicar um tópico, verifique `exams/EXAM_INDEX.md`:
- Se o tópico tem alta incidência → mencione o padrão de cobrança
- Se há questão representativa → use como exercício guiado
- Se há erro recorrente registrado → alerte proativamente

## Lógica de escopo das provas

As provas seguem um modelo cumulativo com foco progressivo:

```
P1: cobre TODO o conteúdo do início até a P1
        → foco: 100% no conteúdo pré-P1

P2: cobre TODO o conteúdo do início até a P2
        → foco primário:   conteúdo entre P1 e P2  (~70%)
        → foco secundário: conteúdo pré-P1          (~30%)

P3: cobre TODO o conteúdo do início até a P3
        → foco primário:   conteúdo entre P2 e P3  (~70%)
        → foco secundário: conteúdo entre P1 e P2  (~20%)
        → foco terciário:  conteúdo pré-P1          (~10%)
```

**Regra prática para o tutor:**

Ao entrar no modo `exam_prep`, identifique qual prova está próxima consultando
`course/SYLLABUS.md`. Então:

1. Liste todos os tópicos no escopo daquela prova
2. Priorize os tópicos do período mais recente (entre a última prova e esta)
3. Reserve tempo menor para revisar tópicos de provas anteriores
4. Use provas antigas do mesmo tipo para calibrar o peso de cada assunto

**Exemplo de resposta em exam_prep:**

> "Para a P2, vou focar primeiro em [tópicos pós-P1] porque esse é o
> conteúdo novo desta prova. Depois revisamos [tópicos pré-P1] que
> costumam aparecer com menos peso mas ainda caem."
"""


def modes_md() -> str:
    return """# MODES

## Modos de operação do tutor

O tutor opera em quatro modos. Cada modo tem objetivo, postura e formato de resposta diferentes.

---

## study — Aprendizado de conceito novo

**Ativado por:** "quero entender X", "o que é Y", "explica Z"

**Objetivo:** construir compreensão sólida do zero

**Postura:**
- Siga a estrutura completa de PEDAGOGY.md
- Não assuma conhecimento prévio
- Verifique compreensão antes de avançar

**Formato de resposta:**
- Contexto → Intuição → Definição → Exemplo → Exercício

---

## assignment — Resolução de exercício

**Ativado por:** "tenho uma lista", "não entendi essa questão", "como resolver X"

**Objetivo:** desenvolver habilidade de resolução sem dependência

**Postura:**
- NUNCA entregue a resposta diretamente
- Identifique onde o aluno está travado
- Faça perguntas que revelem o próximo passo
- Consulte `exercises/EXERCISE_INDEX.md` para localizar o exercício no mapa da disciplina
- Entregue a resolução completa só depois que o aluno chegou lá

**Formato de resposta:**
- Diagnóstico → Pergunta socrática → Dica mínima → Confirmação

---

## exam_prep — Preparação para prova

**Ativado por:** "tenho prova", "revisão", "o que cai", "resumo para prova"

**Objetivo:** maximizar performance na avaliação

**Primeira ação obrigatória:** identificar qual prova está próxima via `course/SYLLABUS.md`

**Lógica de escopo (regra fundamental):**

As provas são cumulativas mas com peso progressivo:

- **P1** → cobre tudo do início até a P1. Foco total no conteúdo pré-P1.
- **P2** → cobre tudo até a P2. Foco principal no conteúdo entre P1 e P2 (~70%). Conteúdo da P1 ainda cai, mas com menos peso (~30%).
- **P3** → cobre tudo até a P3. Foco principal no conteúdo entre P2 e P3 (~70%). Conteúdo entre P1-P2 cai menos (~20%). Conteúdo pré-P1 cai pouco (~10%).

**Postura:**
- Comece sempre pelos tópicos do período mais recente
- Sinalize explicitamente quais tópicos são "foco principal" vs "foco secundário"
- Consulte `exams/EXAM_INDEX.md` para identificar tópicos com alta incidência e padrões recorrentes
- Use questões de provas anteriores para calibrar o nível de cobrança
- Sinalize armadilhas e erros recorrentes de cada tópico

**Formato de resposta:**
- Identificar a prova → Mapear escopo completo → Priorizar por período → Questão representativa → Armadilha → Checklist

---

## class_companion — Acompanhamento de aula

**Ativado por:** "estou na aula", "o professor falou X", "não entendi o que ele disse"

**Objetivo:** apoio em tempo real durante ou logo após a aula

**Postura:**
- Respostas curtas e diretas
- Contextualize o que o professor disse com o material curado
- Não entre em detalhes desnecessários — o aluno está ocupado
- Sugira registrar dúvidas para explorar depois

**Formato de resposta:**
- Resposta em até 3 parágrafos → Conexão com material → Sugestão de follow-up
"""


def output_templates_md() -> str:
    return """# OUTPUT_TEMPLATES

## Templates de resposta por modo

### study — Conceito novo

```
## [Nome do conceito]

**Por que existe:** [contexto em 1-2 frases]

**Intuição:** [analogia ou imagem mental]

**Definição formal:**
[definição precisa, com LaTeX se necessário]

**Exemplo mínimo:**
[exemplo mais simples possível]

**Como aparece na disciplina:**
[conexão com o conteúdo do curso]

**Cuidado com:**
[erro mais comum]

**Agora você:** [pergunta para o aluno aplicar o conceito]

*Fonte: [arquivo de origem]*
```

---

### assignment — Guia de exercício

```
## Analisando a questão

[Identifica o que está sendo pedido]

**O que você já tentou?** [pergunta ao aluno]

*Se o aluno tentou algo:*
> Você está no caminho certo / Tem um ponto a revisar em [etapa X]

**Dica mínima:** [menor hint possível que desbloqueie o raciocínio]

[Aguarda o aluno tentar antes de revelar mais]
```

---

### exam_prep — Revisão para prova

```
## Revisão para [P1 / P2 / P3] — [Disciplina]

**Escopo desta prova:** [todo o conteúdo até esta prova]

### 🎯 Foco principal — conteúdo do período recente
*Estes tópicos têm maior peso nesta prova*

- [Tópico A] | Incidência: Alta | Formato: [dissertativa/cálculo/múltipla]
- [Tópico B] | Incidência: Alta
- [Tópico C] | Incidência: Média

### 📌 Foco secundário — conteúdo de provas anteriores
*Ainda cai, mas com menos peso*

- [Tópico X] — revisão rápida suficiente
- [Tópico Y] — revisar definição e um exemplo

### Questão representativa
[questão de prova anterior ou similar ao estilo do professor]

### Armadilha mais comum
[o que os alunos erram com frequência]

### Checklist de prontidão
Foco principal:
- [ ] Sei definir [Tópico A]
- [ ] Sei calcular / aplicar [Tópico A]
- [ ] Identifiquei em questão de prova anterior

Foco secundário:
- [ ] Consigo lembrar a definição de [Tópico X]
- [ ] Consigo resolver um exemplo básico de [Tópico X]
```

---

### class_companion — Suporte durante aula

```
**[Conceito mencionado]**

[Explicação em 2-3 frases diretas]

*Isso está em: [arquivo relevante]*

Para explorar melhor depois: [sugestão rápida]
```
"""


_TEACHING_PLAN_SECTION_STOP = re.compile(
    r'^(?:PROCEDIMENTOS|AVALIA[ÇC][AÃ]O|BIBLIOGRAFIA|METODOLOGIA)',
    re.IGNORECASE,
)

def _parse_units_from_teaching_plan(text: str):
    """
    Extrai (título_da_unidade, [tópicos]) do texto livre do plano de ensino.

    Suporta dois formatos:
      Formato PUCRS:  "N°. DA UNIDADE: N" seguido de "CONTEÚDO: Título"
                      Tópicos numerados como "1.1.", "1.2.1." etc.
      Formato genérico: "Unidade N – Título" / "UNIDADE N: Título"
                        Tópicos com marcadores (-, •, *) ou numerados (1.1)

    Para quando encontra seções pós-conteúdo (PROCEDIMENTOS, AVALIAÇÃO, BIBLIOGRAFIA).
    Retorna lista de (str, List[str]).
    """
    units: list = []
    current_title: Optional[str] = None
    current_unit_num: Optional[str] = None
    current_topics: list = []

    pucrs_unit_re = re.compile(r'N[°º]?\.\s*DA\s+UNIDADE\s*:\s*(\d+)', re.IGNORECASE)
    pucrs_content_re = re.compile(r'CONTE[ÚU]DO\s*:\s*(.+)', re.IGNORECASE)
    generic_unit_re = re.compile(r'^#{0,4}\s*unidade\s+[\divxlc]+[\s\-–:—]+(.+)', re.IGNORECASE)
    numbered_topic_re = re.compile(r'^(\d+\.\d+(?:\.\d+)*)\.\s+(.+)')
    bullet_topic_re = re.compile(r'^[-•*]\s+(.+)')

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if _TEACHING_PLAN_SECTION_STOP.match(line):
            break

        # PUCRS: "N°. DA UNIDADE: N"
        m = pucrs_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_unit_num = m.group(1)
            current_title = None
            current_topics = []
            continue

        # PUCRS: "CONTEÚDO: Título" — título da unidade atual
        if current_unit_num is not None and current_title is None:
            m = pucrs_content_re.match(line)
            if m:
                current_title = f"Unidade {current_unit_num} — {m.group(1).strip()}"
                continue

        # Genérico: "Unidade N – Título" ou "### Unidade N – Título"
        m = generic_unit_re.match(line)
        if m:
            if current_title is not None:
                units.append((current_title, current_topics))
            current_title = line.lstrip("#").strip()
            current_unit_num = None
            current_topics = []
            continue

        # Tópicos numerados (1.1., 1.2.1.) ou com marcador (-, •)
        if current_title is not None:
            m = numbered_topic_re.match(line)
            if m:
                current_topics.append(m.group(2).strip())
                continue
            m = bullet_topic_re.match(line)
            if m:
                current_topics.append(m.group(1).strip())

    if current_title is not None:
        units.append((current_title, current_topics))

    return units


def _parse_bibliography_from_teaching_plan(text: str) -> dict:
    """
    Extrai referências bibliográficas do texto do plano de ensino.
    Detecta seção BIBLIOGRAFIA com sub-seções BÁSICA e COMPLEMENTAR.
    Retorna {"basica": [str, ...], "complementar": [str, ...]}.
    """
    result: dict = {"basica": [], "complementar": []}

    bib_match = re.search(r'^BIBLIOGRAFIA', text, re.MULTILINE | re.IGNORECASE)
    if not bib_match:
        return result

    bib_text = text[bib_match.start():]
    current_section: Optional[str] = None
    current_ref: Optional[str] = None
    ref_start_re = re.compile(r'^\d+\.\s+(.+)')

    def _flush():
        if current_ref and current_section:
            result[current_section].append(current_ref.strip())

    for raw in bib_text.splitlines():
        line = raw.strip()

        if re.match(r'^B[ÁA]SICA\s*:', line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "basica"
            continue

        if re.match(r'^COMPLEMENTAR\s*:', line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "complementar"
            continue

        if not current_section:
            continue

        if not line:
            _flush()
            current_ref = None
            continue

        m = ref_start_re.match(line)
        if m:
            _flush()
            current_ref = m.group(1).strip()
        elif current_ref is not None:
            current_ref += " " + line

    _flush()
    return result


def syllabus_md(subject_profile) -> str:
    """Gera o conteúdo de course/SYLLABUS.md a partir do SubjectProfile."""
    subj = subject_profile
    return f"""---
course: {subj.name}
professor: {subj.professor}
schedule: {subj.schedule}
---

# Cronograma — {subj.name}

**Horário:** {subj.schedule}

{subj.syllabus}
"""


def student_profile_md(student_profile) -> str:
    """Gera o conteúdo de student/STUDENT_PROFILE.md a partir do StudentProfile."""
    sp = student_profile
    return f"""---
nickname: {sp.nickname or sp.full_name}
semester: {sp.semester}
institution: {sp.institution}
---

# Perfil do Aluno

- **Nome:** {sp.full_name}
- **Apelido:** {sp.nickname or sp.full_name}
- **Semestre:** {sp.semester}
- **Instituição:** {sp.institution}

## Estilo de aprendizado preferido

{sp.personality}
"""


def course_map_md(course_meta: dict, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")

    lines = [
        f"# COURSE_MAP — {course_name}",
        "",
        "> **Como usar:** Este arquivo define a ordem pedagógica dos tópicos.",
        "> O tutor consulta este mapa para saber o que o aluno já deveria ter visto",
        "> e o que ainda não foi apresentado formalmente.",
    ]

    if subject_profile and subject_profile.syllabus:
        lines.append("> Cronograma completo disponível em `course/SYLLABUS.md`")
    lines.append("")

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    units = _parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []

    lines.append("## Estrutura do curso")
    lines.append("")

    if units:
        for unit_title, topics in units:
            lines.append(f"### {unit_title}")
            if topics:
                for t in topics:
                    lines.append(f"- [ ] {t}")
            else:
                lines.append("- [ ] [tópicos a preencher]")
            lines.append("")
    else:
        lines += [
            "<!--",
            "INSTRUÇÃO PARA O MANTENEDOR:",
            "Preencha os tópicos abaixo em ordem pedagógica.",
            "Use indentação para indicar subtópicos.",
            "Marque dependências com '→ requer: [tópico]'",
            "-->",
            "",
            "### Unidade 1 — [Nome da unidade]",
            "- [ ] Tópico 1.1",
            "- [ ] Tópico 1.2",
            "",
            "### Unidade 2 — [Nome da unidade]",
            "- [ ] Tópico 2.1 → requer: Tópico 1.2",
            "- [ ] Tópico 2.2",
            "",
        ]

    lines += [
        "## Tópicos de alta incidência em prova",
        "",
        "<!-- Preencha com base nas provas anteriores em exams/ -->",
        "",
        "| Tópico | Unidade | Incidência |",
        "|---|---|---|",
        "| [a preencher] | | |",
        "",
        "## Notas do professor",
        "",
        "<!-- Padrões observados no estilo de cobrança do professor -->",
        "- [a preencher após análise das provas anteriores]",
    ]

    return "\n".join(lines)


def glossary_md(course_meta: dict, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")

    lines = [
        f"# GLOSSARY — {course_name}",
        "",
        "> **Como usar:** Terminologia oficial da disciplina.",
        "> O tutor consulta este arquivo para usar os mesmos termos que o professor.",
        "> Inconsistência terminológica é fonte de confusão em provas.",
        "",
        "## Formato de entrada",
        "",
        "```",
        "## [Termo]",
        "**Definição:** [definição precisa usada nesta disciplina]",
        "**Sinônimos aceitos:** [outros nomes para o mesmo conceito]",
        "**Não confundir com:** [termo similar mas diferente]",
        "**Aparece em:** [unidades / tópicos onde é usado]",
        "```",
        "",
        "---",
        "",
        "## Termos",
        "",
    ]

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    units = _parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []

    # Collect all leaf topics as candidate terms
    candidates = []
    for _unit_title, topics in units:
        candidates.extend(topics)

    if candidates:
        lines.append("<!-- Termos extraídos automaticamente do plano de ensino. Preencha as definições. -->")
        lines.append("")
        for term in candidates:
            lines += [
                f"## {term}",
                "**Definição:** [a preencher]",
                "**Sinônimos aceitos:** —",
                "**Não confundir com:** —",
                f"**Aparece em:** [unidade a identificar]",
                "",
            ]
    else:
        lines.append("<!-- Preencha conforme o conteúdo da disciplina for sendo curado -->")
        lines.append("")

    return "\n".join(lines)


def student_state_md(course_meta: dict, student_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    nick = "Aluno"
    if student_profile and student_profile.full_name:
        nick = student_profile.nickname or student_profile.full_name

    today = datetime.now().strftime("%Y-%m-%d")

    return f"""---
course: {course_name}
student: {nick}
last_updated: {today}
---

# STUDENT_STATE — {nick}

> **Como usar:** Este arquivo é a memória do tutor sobre o progresso do aluno.
> Atualize após cada sessão de estudo. Faça commit no GitHub.
> O tutor lê este arquivo SEMPRE antes de responder.

## Posição atual no curso

- **Último tópico estudado:** [a preencher]
- **Unidade atual:** [a preencher]
- **Status geral:** Início do semestre

## Tópicos concluídos

<!-- Marque com ✅ quando o aluno demonstrar compreensão sólida -->

| Tópico | Status | Data |
|---|---|---|
| [a preencher] | | |

## Dúvidas pendentes

<!-- Registre dúvidas que ficaram em aberto para retomar -->

- [ ] [a preencher]

## Erros recorrentes

<!-- Padrões de erro observados — ajuda o tutor a antecipar problemas -->

| Tópico | Erro observado | Frequência |
|---|---|---|
| [a preencher] | | |

## Próximos passos sugeridos

1. [a preencher após primeira sessão]

## Histórico de sessões

| Data | Modo | Tópicos | Observações |
|---|---|---|---|
| {today} | — | Início | Repositório criado |
"""


def progress_schema_md() -> str:
    return """# PROGRESS_SCHEMA

## Schema do estado do aluno

Define a estrutura esperada de `STUDENT_STATE.md`.
Use este arquivo como referência ao atualizar o estado manualmente
ou ao pedir ao Claude para gerar uma atualização.

## Campos obrigatórios

```yaml
---
course: string          # Nome da disciplina
student: string         # Nome/apelido do aluno
last_updated: YYYY-MM-DD
---
```

## Status válidos para tópicos

| Status | Significado |
|---|---|
| `não iniciado` | Ainda não foi estudado |
| `em progresso` | Estudado mas não consolidado |
| `com dúvidas` | Estudado com pontos em aberto |
| `concluído` | Compreensão sólida demonstrada |
| `revisão` | Concluído mas precisa reforçar para prova |

## Ciclo de atualização recomendado

```
Sessão de estudo
    → Claude sugere bloco de atualização
    → Aluno revisa e ajusta
    → Aluno faz commit no GitHub
    → Na próxima sessão: Claude lê o estado atualizado
```

## Template de atualização (gerado pelo Claude ao final da sessão)

```markdown
## Atualização sugerida — [DATA]

**Tópico estudado:** [nome]
**Status:** [status válido acima]
**Dúvidas identificadas:** [lista ou "nenhuma"]
**Erros observados:** [lista ou "nenhum"]
**Próximo passo:** [próximo tópico sugerido]
```
"""


def bibliography_md(course_meta: dict, entries: List[FileEntry] = None, subject_profile=None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# BIBLIOGRAPHY — {course_name}",
        "",
        "> **Como usar:** Links e referências da disciplina.",
        "> O tutor consulta este arquivo quando o aluno pede fontes",
        "> ou quando uma explicação pode ser aprofundada com leitura adicional.",
        "",
    ]

    # Referências extraídas do plano de ensino
    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    parsed = _parse_bibliography_from_teaching_plan(teaching_plan) if teaching_plan else {}
    basica = parsed.get("basica", [])
    complementar = parsed.get("complementar", [])

    if basica or complementar:
        lines.append("## Bibliografia do plano de ensino")
        lines.append("")
        if basica:
            lines.append("### Básica")
            lines.append("")
            for ref in basica:
                lines.append(f"- {ref}")
            lines.append("")
        if complementar:
            lines.append("### Complementar")
            lines.append("")
            for ref in complementar:
                lines.append(f"- {ref}")
            lines.append("")

    # Referências importadas manualmente via app (categoria "bibliografia")
    if entries:
        lines.append("## Referências importadas")
        lines.append("")
        for entry in entries:
            lines.append(f"### {entry.title}")
            lines.append(f"- **URL:** {entry.source_path}")
            if entry.tags:
                lines.append(f"- **Tags:** {entry.tags}")
            if entry.notes:
                lines.append(f"- **Nota:** {entry.notes}")
            if entry.professor_signal:
                lines.append(f"- **Indicação do professor:** {entry.professor_signal}")
            lines.append(f"- **Incluir no bundle:** {'sim' if entry.include_in_bundle else 'não'}")
            lines.append("")

    if not basica and not complementar and not entries:
        lines += [
            "## Referências",
            "",
            "<!-- Adicione referências aqui, importe links pelo app,",
            "     ou preencha o Plano de Ensino no Gerenciador de Matérias. -->",
            "",
        ]

    lines += [
        "## Mapa de relevância por tópico",
        "",
        "<!-- Preencha após organizar as referências -->",
        "",
        "| Tópico | Referência principal | Acessível | Incidência em prova |",
        "|---|---|---|---|",
        "| [a preencher] | | | |",
        "",
    ]

    return "\n".join(lines)


def exam_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# EXAM_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice de provas anteriores por tópico.",
        "> O tutor consulta este arquivo no modo `exam_prep` para identificar",
        "> quais tópicos têm maior incidência e quais padrões de questão se repetem.",
        "",
        "## Provas disponíveis",
        "",
    ]

    lines.append("| Arquivo | Tipo | Prova | Observação | Padrão do professor |")
    lines.append("|---|---|---|---|---|")
    for entry in entries:
        tipo = "foto" if entry.category == "fotos-de-prova" else "original"
        lines.append(
            f"| {Path(entry.source_path).name} | {tipo} | {entry.title} "
            f"| {entry.notes or ''} | {entry.professor_signal or ''} |"
        )

    lines += [
        "",
        "## Incidência de tópicos por prova",
        "",
        "> Preencha após revisar cada prova. O tutor usa esta tabela no modo `exam_prep`.",
        "",
        "| Tópico | P1 | P2 | P3 | Total | Peso estimado |",
        "|---|---|---|---|---|---|",
        "| [a preencher] | | | | | |",
        "",
        "## Padrões de questão observados",
        "",
        "<!-- Liste padrões recorrentes: tipos de enunciado, estrutura, pegadinhas comuns -->",
        "",
    ]

    return "\n".join(lines)


def exercise_index_md(course_meta: dict, entries: List[FileEntry] = None) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# EXERCISE_INDEX — {course_name}",
        "",
        "> **Como usar:** Mapa de listas de exercícios por tópico.",
        "> O tutor consulta este arquivo no modo `assignment` para contextualizar",
        "> exercícios e no modo `exam_prep` para indicar prática por tema.",
        "",
        "## Listas disponíveis",
        "",
    ]

    if entries:
        lines.append("| Arquivo | Título | Categoria | Observação |")
        lines.append("|---|---|---|---|")
        for entry in entries:
            lines.append(
                f"| {Path(entry.source_path).name} | {entry.title} "
                f"| {entry.category} | {entry.notes or ''} |"
            )
    else:
        lines.append("| Arquivo | Título | Categoria | Observação |")
        lines.append("|---|---|---|---|")
        lines.append("| [a preencher] | | | |")

    lines += [
        "",
        "## Mapeamento de exercícios por tópico",
        "",
        "> Preencha após organizar as listas. O tutor usa esta tabela para sugerir exercícios relevantes.",
        "",
        "| Tópico | Lista | Exercícios | Dificuldade | Notas |",
        "|---|---|---|---|---|",
        "| [a preencher] | | | | |",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Free functions — existing templates (unchanged)
# ---------------------------------------------------------------------------

def root_readme(course_meta: dict) -> str:
    return f"""# {course_meta.get('course_name', 'Curso')}

Repositório gerado pelo **Academic Tutor Repo Builder V3**.
Plataforma alvo: **Claude Projects** (claude.ai)

## Como usar com Claude

1. Crie um **Projeto** no Claude.ai com o nome desta disciplina
2. Cole o conteúdo de `INSTRUCOES_CLAUDE_PROJETO.md` no campo **Instructions** do Projeto
3. Conecte este repositório GitHub ao Projeto (aba Settings → GitHub)
4. Inicie uma conversa — o Claude lerá os arquivos automaticamente

## Estrutura
- `system/` — política do tutor, pedagogia, modos, templates
- `course/` — identidade, mapa, cronograma, glossário, bibliografia
- `student/` — estado atual, perfil, schema de progresso
- `content/` — material de aula curado
- `exercises/` — listas de exercícios
- `exams/` — provas anteriores e gabaritos
- `raw/` — materiais originais (PDFs, imagens)
- `staging/` — extração automática (para revisão)
- `manual-review/` — revisão humana guiada
- `build/claude-knowledge/` — bundle para upload manual se necessário

## Arquivos-chave para o tutor

| Arquivo | Função |
|---|---|
| `INSTRUCOES_CLAUDE_PROJETO.md` | System prompt do Projeto |
| `student/STUDENT_STATE.md` | Estado atual do aluno — atualizar após cada sessão |
| `course/COURSE_MAP.md` | Preencher com os tópicos em ordem |
| `course/GLOSSARY.md` | Preencher com terminologia da disciplina |
| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |

## Fluxo recomendado

1. Rodar extração automática no app
2. Revisar `manual-review/`
3. Promover conteúdo curado para `content/`, `exercises/`, `exams/`
4. Preencher `COURSE_MAP.md` e `GLOSSARY.md`
5. Conectar ao Projeto no Claude.ai
6. Após cada sessão de estudo: atualizar `student/STUDENT_STATE.md` e fazer push
"""


def wrap_frontmatter(meta: dict, body: str) -> str:
    header = ["---"]
    for k, v in meta.items():
        header.append(f"{k}: {json_str(v)}")
    header.append("---")
    header.append("")
    return "\n".join(header) + body.strip() + "\n"


def rows_to_markdown_table(rows: list) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    fixed = [r + [""] * (width - len(r)) for r in rows]
    header = fixed[0]
    sep = ["---"] * width
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in fixed[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def manual_pdf_review_template(entry: FileEntry, item: Dict[str, object]) -> str:
    report = item.get("document_report") or {}
    decision = item.get("pipeline_decision") or {}
    return f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_pdf_review
category: {entry.category}
source_pdf: {json_str(item.get('raw_target'))}
processing_mode: {json_str(entry.processing_mode)}
document_profile: {json_str(entry.document_profile)}
effective_profile: {json_str(item.get('effective_profile'))}
base_backend: {json_str(item.get('base_backend'))}
advanced_backend: {json_str(item.get('advanced_backend'))}
base_markdown: {json_str(item.get('base_markdown'))}
advanced_markdown: {json_str(item.get('advanced_markdown'))}
---

# Revisão Manual — {entry.title}

## Perfil detectado
- Perfil efetivo: `{item.get('effective_profile')}`
- Páginas: `{report.get('page_count')}`
- Texto: `{report.get('text_chars')}` chars
- Imagens: `{report.get('images_count')}`
- Tabelas: `{report.get('table_candidates')}`
- Scan: `{report.get('suspected_scan')}`

## Pipeline
- Modo: `{decision.get('processing_mode')}`
- Base: `{decision.get('base_backend')}`
- Avançado: `{decision.get('advanced_backend')}`

## Checklist
- [ ] Conferir títulos e subtítulos
- [ ] Corrigir ordem de leitura
- [ ] Revisar fórmulas e converter para LaTeX
- [ ] Revisar tabelas exportadas
- [ ] Verificar imagens/figuras importantes
- [ ] Registrar pistas sobre o professor

## Markdown corrigido
<!-- Cole aqui a versão corrigida -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `exercises/lists/`
- [ ] `exams/past-exams/`
"""


def manual_image_review_template(entry: FileEntry, raw_target: Path, root_dir: Path) -> str:
    image_path = safe_rel(raw_target, root_dir)
    return f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_image_review
category: {entry.category}
source_image: {json_str(image_path)}
---

# Revisão Manual — Imagem

## Metadados
- Tags: `{entry.tags}`
- Relevante para prova: `{entry.relevant_for_exam}`
- Sinal do professor: `{entry.professor_signal}`

## Transcrição fiel
<!-- Escreva o texto da imagem aqui -->

## Destino curado sugerido
- [ ] `exams/past-exams/`
- [ ] `content/curated/`
"""


def pdf_curation_guide() -> str:
    return """# PDF_CURATION_GUIDE

## Regra central
PDF bruto não é conhecimento final.
Ele é insumo para:
1. extração automática
2. revisão manual
3. curadoria por função pedagógica

## Quando usar cada camada
- Base: PDFs simples, texto corrido, listas e cronogramas.
- Avançada: fórmulas, tabelas difíceis, layout complexo, scans, provas.
- Manual assisted: qualquer material que influencie a lógica de prova.

## Artefatos gerados
- `raw/`: arquivo original
- `staging/`: extração automática
- `manual-review/`: revisão humana guiada
- `content/` e `exams/`: conhecimento curado

## Destino final no Claude Project
Todo arquivo curado deve estar em formato Markdown limpo
para ser lido eficientemente pelo Claude via integração GitHub.
"""


def backend_architecture_md() -> str:
    return """# BACKEND_ARCHITECTURE

## Visão geral
A V3 usa arquitetura de backends em camadas.

```text
PDF bruto
 -> camada base
 -> camada avançada (quando necessário)
 -> extração de artefatos
 -> revisão manual guiada
 -> conteúdo curado
 -> Claude Project (via GitHub sync)
```

## Camada base
- `pymupdf4llm`: Markdown rápido para PDFs digitais.
- `pymupdf`: fallback bruto.

## Camada avançada
- `docling`: OCR, fórmulas, tabelas e imagens referenciadas.
- `marker`: equações, inline math, tabelas e imagens.

## Modos de processamento
- `quick`: só camada base.
- `high_fidelity`: base + avançada.
- `manual_assisted`: base + artefatos + revisão humana.
- `auto`: decide pelo perfil do documento.

## Regra de ouro
O tutor não deve consumir o PDF bruto como fonte final.
A fonte final deve ser o Markdown curado derivado da revisão manual,
sincronizado com o Claude Project via GitHub.
"""


def backend_policy_yaml(options: Dict[str, object]) -> str:
    return f"""version: 3
target_platform: claude-projects
policy:
  default_processing_mode: {options.get('default_processing_mode', 'auto')}
  default_ocr_language: {json_str(options.get('default_ocr_language', 'por,eng'))}
  require_manual_review_for:
    - math_heavy
    - scanned
    - exam_pdf
    - layout_heavy
  base_layer_priority:
    - pymupdf4llm
    - pymupdf
  advanced_layer_priority:
    - docling
    - marker
  asset_pipeline:
    extract_images: true
    export_page_previews: true
    extract_tables: true
  promotion_rule: |
    Nenhum arquivo de staging é conhecimento final.
    O conhecimento final deve sair de manual-review/ e depois ser promovido
    para content/, exercises/ ou exams/, e então sincronizado com o Claude Project.
"""