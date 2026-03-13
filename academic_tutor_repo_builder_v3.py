#!/usr/bin/env python3
"""
Academic Tutor Repo Builder V3

What this version adds:
- Layered backend architecture for PDF extraction.
- Automatic backend selection by document profile.
- Support for processing modes: auto, quick, high_fidelity, manual_assisted.
- Advanced backend integration for formulas/layout using Docling and Marker CLIs.
- Asset pipeline for images, tables and page previews.
- Guided manual review files to preserve integrity.
- Generates backend architecture / policy files inside the repository.

The app is intentionally resilient:
- It runs even if optional dependencies are missing.
- It records what was available in the environment.
- It keeps raw files and auto outputs separated from curated knowledge.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

# Optional dependencies
try:
    import pymupdf  # PyMuPDF
    HAS_PYMUPDF = True
except Exception:
    pymupdf = None
    HAS_PYMUPDF = False

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except Exception:
    pymupdf4llm = None
    HAS_PYMUPDF4LLM = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except Exception:
    pdfplumber = None
    HAS_PDFPLUMBER = False

DOCILING_CLI = shutil.which("docling")
MARKER_CLI = shutil.which("marker_single")

APP_NAME = "Academic Tutor Repo Builder V3"

DEFAULT_CATEGORIES = [
    "course-material",
    "exams",
    "exercise-lists",
    "rubrics",
    "schedule",
    "references",
    "photos-of-exams",
    "answer-keys",
    "other",
]

IMAGE_CATEGORIES = {"photos-of-exams", "exams", "course-material", "other"}

PROCESSING_MODES = ["auto", "quick", "high_fidelity", "manual_assisted"]
DOCUMENT_PROFILES = ["auto", "general", "math_heavy", "layout_heavy", "scanned", "exam_pdf"]
PREFERRED_BACKENDS = ["auto", "pymupdf4llm", "pymupdf", "docling", "marker"]
OCR_LANGS = ["por", "eng", "por,eng", "eng,por"]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or "untitled"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def parse_page_range(page_range: str) -> Optional[List[int]]:
    """Parse zero-based and one-based page specifications.

    Accepted examples:
    - ""
    - "1-3"
    - "0,2,4-6"
    - "2, 5-7"

    Returned pages are zero-based, sorted, unique.
    When the spec contains only positive integers >= 1 and no zero, it is treated
    as one-based for user convenience.
    """
    value = (page_range or "").strip()
    if not value:
        return None

    tokens = [t.strip() for t in value.split(",") if t.strip()]
    if not tokens:
        return None

    raw_pages: List[int] = []
    saw_zero = False
    saw_positive = False

    for token in tokens:
        if "-" in token:
            start_str, end_str = [p.strip() for p in token.split("-", 1)]
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError(f"Faixa de páginas inválida: {token}")
            start = int(start_str)
            end = int(end_str)
            if start > end:
                start, end = end, start
            raw_pages.extend(list(range(start, end + 1)))
            if start == 0 or end == 0:
                saw_zero = True
            if end >= 1:
                saw_positive = True
        else:
            if not token.isdigit():
                raise ValueError(f"Página inválida: {token}")
            num = int(token)
            raw_pages.append(num)
            if num == 0:
                saw_zero = True
            if num >= 1:
                saw_positive = True

    pages = sorted(set(raw_pages))
    if not saw_zero and saw_positive:
        pages = [p - 1 for p in pages]

    pages = [p for p in pages if p >= 0]
    return pages or None


def pages_to_marker_range(pages: Optional[Sequence[int]]) -> Optional[str]:
    if not pages:
        return None
    pages = sorted(set(int(p) for p in pages if p >= 0))
    if not pages:
        return None
    ranges: List[str] = []
    start = prev = pages[0]
    for p in pages[1:]:
        if p == prev + 1:
            prev = p
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = p
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def file_size_mb(path: Path) -> float:
    try:
        return round(path.stat().st_size / (1024 * 1024), 2)
    except Exception:
        return 0.0


def safe_rel(path: Optional[Path], root: Path) -> Optional[str]:
    if not path:
        return None
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def json_str(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class FileEntry:
    source_path: str
    file_type: str  # pdf or image
    category: str
    title: str
    tags: str = ""
    notes: str = ""
    professor_signal: str = ""
    relevant_for_exam: bool = True
    include_in_bundle: bool = True

    # V3 fields
    processing_mode: str = "auto"
    document_profile: str = "auto"
    preferred_backend: str = "auto"
    formula_priority: bool = False
    preserve_pdf_images_in_markdown: bool = True
    force_ocr: bool = False
    export_page_previews: bool = True
    extract_images: bool = True
    extract_tables: bool = True
    page_range: str = ""
    ocr_language: str = "por,eng"

    def id(self) -> str:
        return slugify(Path(self.source_path).stem)


@dataclass
class DocumentProfileReport:
    page_count: int = 0
    text_chars: int = 0
    images_count: int = 0
    table_candidates: int = 0
    text_density: float = 0.0
    suspected_scan: bool = False
    suggested_profile: str = "general"
    notes: List[str] = field(default_factory=list)


@dataclass
class BackendRunResult:
    name: str
    layer: str
    status: str
    markdown_path: Optional[str] = None
    asset_dir: Optional[str] = None
    metadata_path: Optional[str] = None
    command: Optional[List[str]] = None
    notes: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class PipelineDecision:
    entry_id: str
    processing_mode: str
    effective_profile: str
    base_backend: Optional[str]
    advanced_backend: Optional[str]
    reasons: List[str] = field(default_factory=list)


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
        return bool(DOCILING_CLI)

    def run(self, ctx: BackendContext) -> BackendRunResult:
        out_dir = ctx.root_dir / "staging" / "markdown-auto" / "docling" / ctx.entry_id
        ensure_dir(out_dir)

        cmd = [
            DOCILING_CLI,
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
    def __init__(self, root_dir: Path, course_meta: Dict[str, str], entries: List[FileEntry], options: Dict[str, object]):
        self.root_dir = root_dir
        self.course_meta = course_meta
        self.entries = entries
        self.options = options
        self.logs: List[Dict[str, object]] = []
        self.selector = BackendSelector()

    def build(self) -> None:
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
                "docling_cli": bool(DOCILING_CLI),
                "marker_cli": bool(MARKER_CLI),
            },
            "entries": [],
        }

        for entry in self.entries:
            item_result = self._process_entry(entry)
            manifest["entries"].append(item_result)

        manifest["logs"] = self.logs
        write_text(self.root_dir / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)

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
            "raw/pdfs/course-material",
            "raw/pdfs/exams",
            "raw/pdfs/exercise-lists",
            "raw/pdfs/rubrics",
            "raw/pdfs/schedule",
            "raw/pdfs/references",
            "raw/pdfs/photos-of-exams",
            "raw/pdfs/answer-keys",
            "raw/pdfs/other",
            "raw/images/photos-of-exams",
            "raw/images/exams",
            "raw/images/course-material",
            "raw/images/other",
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
            "build/gpt-knowledge",
        ]
        for d in dirs:
            ensure_dir(self.root_dir / d)

    def _write_root_files(self) -> None:
        course_slug = self.course_meta["course_slug"]
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
curado e reutilizável para um GPT Tutor acadêmico.
""",
        )

        write_text(self.root_dir / "system" / "PDF_CURATION_GUIDE.md", pdf_curation_guide())
        write_text(self.root_dir / "system" / "BACKEND_ARCHITECTURE.md", backend_architecture_md())
        write_text(self.root_dir / "system" / "BACKEND_POLICY.yaml", backend_policy_yaml(self.options))
        write_text(self.root_dir / "README.md", root_readme(self.course_meta))
        write_text(self.root_dir / ".gitignore", "__pycache__/\n*.pyc\n.DS_Store\nThumbs.db\n")

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
                    f"    raw_target: {json_str(item['raw_target'])}",
                    f"    processing_mode: {item.get('processing_mode', 'auto')}",
                    f"    effective_profile: {item.get('effective_profile', 'general')}",
                    f"    include_in_bundle: {str(item['include_in_bundle']).lower()}",
                    f"    professor_signal: {json_str(item['professor_signal'])}",
                ]
            )
        write_text(self.root_dir / "course" / "SOURCE_REGISTRY.yaml", "\n".join(lines) + "\n")

    def _write_bundle_seed(self, manifest: Dict[str, object]) -> None:
        selected = [e for e in manifest["entries"] if e["include_in_bundle"]]
        seed = {
            "generated_at": manifest["generated_at"],
            "course_slug": self.course_meta["course_slug"],
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
        write_text(self.root_dir / "build" / "gpt-knowledge" / "bundle.seed.json", json.dumps(seed, indent=2, ensure_ascii=False))

    def _write_build_report(self, manifest: Dict[str, object]) -> None:
        report = [
            "# BUILD_REPORT",
            "",
            f"- generated_at: {manifest['generated_at']}",
            f"- pymupdf: {HAS_PYMUPDF}",
            f"- pymupdf4llm: {HAS_PYMUPDF4LLM}",
            f"- pdfplumber: {HAS_PDFPLUMBER}",
            f"- docling_cli: {bool(DOCILING_CLI)}",
            f"- marker_cli: {bool(MARKER_CLI)}",
            "",
            "## Regras práticas",
            "- PDFs simples: camada base costuma bastar.",
            "- PDFs com fórmulas, scans, layout complexo ou provas: camada avançada + revisão manual.",
            "- Imagens, tabelas e previews são preservados como artefatos auxiliares.",
            "- O conhecimento final do tutor deve sair de `manual-review/` e depois ser promovido para `content/`, `exercises/` e `exams/`.",
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
        safe_name = f"{entry.id()}{src.suffix.lower()}"

        if entry.file_type == "pdf":
            raw_target = self.root_dir / "raw" / "pdfs" / entry.category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_pdf(entry, raw_target))
        else:
            image_category = entry.category if entry.category in IMAGE_CATEGORIES else "other"
            raw_target = self.root_dir / "raw" / "images" / image_category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_image(entry, raw_target))

        return item

    def _process_pdf(self, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
        item: Dict[str, object] = {
            "document_report": None,
            "pipeline_decision": None,
            "base_markdown": None,
            "advanced_markdown": None,
            "advanced_backend": None,
            "base_backend": None,
            "images_dir": None,
            "tables_dir": None,
            "page_previews_dir": None,
            "table_detection_dir": None,
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
                item.setdefault("backend_errors", []).append({decision.advanced_backend: result.error})

        if HAS_PYMUPDF and entry.extract_images:
            try:
                images_dir = self.root_dir / "staging" / "assets" / "images" / entry.id()
                count = self._extract_pdf_images(raw_target, images_dir, pages=parse_page_range(entry.page_range))
                item["images_dir"] = safe_rel(images_dir, self.root_dir)
                self.logs.append({"entry": entry.id(), "step": "extract_images", "status": "ok", "count": count})
            except Exception as e:
                self.logs.append({"entry": entry.id(), "step": "extract_images", "status": "error", "error": str(e)})

        if HAS_PYMUPDF and entry.export_page_previews:
            try:
                previews_dir = self.root_dir / "staging" / "assets" / "page-previews" / entry.id()
                count = self._export_page_previews(raw_target, previews_dir, pages=parse_page_range(entry.page_range))
                item["page_previews_dir"] = safe_rel(previews_dir, self.root_dir)
                self.logs.append({"entry": entry.id(), "step": "page_previews", "status": "ok", "count": count})
            except Exception as e:
                self.logs.append({"entry": entry.id(), "step": "page_previews", "status": "error", "error": str(e)})

        if entry.extract_tables:
            if HAS_PDFPLUMBER:
                try:
                    tables_dir = self.root_dir / "staging" / "assets" / "tables" / entry.id()
                    count = self._extract_tables_pdfplumber(raw_target, tables_dir, pages=parse_page_range(entry.page_range))
                    item["tables_dir"] = safe_rel(tables_dir, self.root_dir)
                    self.logs.append({"entry": entry.id(), "step": "extract_tables_pdfplumber", "status": "ok", "count": count})
                except Exception as e:
                    self.logs.append({"entry": entry.id(), "step": "extract_tables_pdfplumber", "status": "error", "error": str(e)})
            if HAS_PYMUPDF:
                try:
                    det_dir = self.root_dir / "staging" / "assets" / "table-detections" / entry.id()
                    count = self._detect_tables_pymupdf(raw_target, det_dir, pages=parse_page_range(entry.page_range))
                    item["table_detection_dir"] = safe_rel(det_dir, self.root_dir)
                    self.logs.append({"entry": entry.id(), "step": "detect_tables_pymupdf", "status": "ok", "count": count})
                except Exception as e:
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
        elif entry.category == "exams" or "prova" in name_hint or "questão" in name_hint or "questao" in name_hint:
            report.suggested_profile = "exam_pdf"
            report.notes.append("Detectado como material de prova/exame.")
        elif entry.formula_priority or re.search(r"\b(latex|equa[cç][aã]o|equation|f[oó]rmula|teorema|prova formal|indu[cç][aã]o)\b", name_hint):
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
            "entry": entry_id,
            "step": result.name,
            "layer": result.layer,
            "status": result.status,
            "markdown_path": result.markdown_path,
            "asset_dir": result.asset_dir,
            "metadata_path": result.metadata_path,
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
                    serializable.append({
                        "table_index": idx,
                        "bbox": list(bbox) if bbox else None,
                        "rows": rows,
                    })
                meta_path = out_dir / f"page-{page_num + 1:03d}.json"
                write_text(meta_path, json.dumps(serializable, indent=2, ensure_ascii=False))
                count += len(serializable)
            except Exception:
                continue
        return count


# ---------------------------------------------------------------------------
# Manual review templates and text blocks
# ---------------------------------------------------------------------------

def wrap_frontmatter(meta: Dict[str, object], body: str) -> str:
    header = ["---"]
    for k, v in meta.items():
        header.append(f"{k}: {json_str(v)}")
    header.append("---")
    header.append("")
    return "\n".join(header) + body.strip() + "\n"


def rows_to_markdown_table(rows: List[List[str]]) -> str:
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
images_dir: {json_str(item.get('images_dir'))}
tables_dir: {json_str(item.get('tables_dir'))}
table_detection_dir: {json_str(item.get('table_detection_dir'))}
page_previews_dir: {json_str(item.get('page_previews_dir'))}
---

# Revisão Manual — {entry.title}

## Objetivo
Corrigir a extração automática, preservar integridade do conteúdo e registrar
pistas sobre o estilo do professor.

## Perfil detectado
- Perfil efetivo: `{item.get('effective_profile')}`
- Páginas: `{report.get('page_count')}`
- Caracteres de texto: `{report.get('text_chars')}`
- Imagens detectadas: `{report.get('images_count')}`
- Tabelas candidatas: `{report.get('table_candidates')}`
- Suspeita de scan: `{report.get('suspected_scan')}`
- Notas do perfil: `{'; '.join(report.get('notes', []))}`

## Decisão de pipeline
- Modo: `{decision.get('processing_mode')}`
- Backend base: `{decision.get('base_backend')}`
- Backend avançado: `{decision.get('advanced_backend')}`
- Razões: `{'; '.join(decision.get('reasons', []))}`

## Checklist
- [ ] Conferir títulos e subtítulos
- [ ] Corrigir ordem de leitura
- [ ] Revisar fórmulas e converter para LaTeX quando necessário
- [ ] Revisar tabelas exportadas
- [ ] Verificar imagens/figuras importantes
- [ ] Marcar quais partes entram no bundle do GPT
- [ ] Registrar pistas sobre padrão de prova do professor

## Metadados rápidos
- Categoria: `{entry.category}`
- Tags: `{entry.tags}`
- Relevante para prova: `{entry.relevant_for_exam}`
- Prioridade em fórmulas: `{entry.formula_priority}`
- Sinal do professor: `{entry.professor_signal}`

## Arquivos gerados
- Markdown base: `{item.get('base_markdown')}`
- Markdown avançado: `{item.get('advanced_markdown')}`
- Imagens: `{item.get('images_dir')}`
- Tabelas: `{item.get('tables_dir')}`
- Detecção de tabelas: `{item.get('table_detection_dir')}`
- Previews: `{item.get('page_previews_dir')}`

## Estratégia de curadoria sugerida
1. Escolher a melhor saída entre base e avançada.
2. Corrigir cabeçalhos, listas e leitura em colunas.
3. Reconstruir fórmulas importantes em LaTeX.
4. Reconstruir tabelas críticas em Markdown.
5. Anotar padrões do professor e dificuldade.
6. Promover o conteúdo curado para a pasta final correta.

## Markdown corrigido
<!-- Cole aqui a versão corrigida do conteúdo -->

## Fórmulas / LaTeX
<!-- Cole aqui blocos em LaTeX importantes -->

## Tabelas corrigidas
<!-- Refaça aqui as tabelas que ficaram ruins -->

## Figuras e imagens relevantes
<!-- Liste as imagens que precisam ser mantidas no banco de conhecimento -->

## Padrões do professor
### Estrutura recorrente
<!-- Ex.: mistura teoria + aplicação, pede demonstrações, gosta de pegadinhas conceituais -->

### Assuntos recorrentes
<!-- Ex.: indução estrutural, prova por contraposição, tabelas-verdade, interpretação de enunciado -->

### Tipo de cobrança
<!-- Ex.: definição formal, resolver exercício, justificar passo, comparar conceitos -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `content/concepts/`
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

## Objetivo
Transcrever com fidelidade uma foto/imagem importante para o tutor acadêmico.

## Metadados rápidos
- Tags: `{entry.tags}`
- Relevante para prova: `{entry.relevant_for_exam}`
- Sinal do professor: `{entry.professor_signal}`

## Transcrição fiel
<!-- Escreva o texto da imagem aqui -->

## Estrutura da questão
<!-- Explique como a questão foi montada -->

## Gabarito ou resposta correta
<!-- Preencha se souber -->

## Pistas sobre o professor
<!-- Ex.: formato preferido, nível de detalhe, tipo de raciocínio cobrado -->

## Destino curado sugerido
- [ ] `exams/past-exams/`
- [ ] `content/curated/`
- [ ] `content/concepts/`
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
- Manual assisted: qualquer material que influencie a lógica de prova, rubrica ou estilo do professor.

## Critérios de revisão obrigatória
- títulos e subtítulos
- fórmulas e LaTeX
- tabelas
- figuras/imagens importantes
- enunciados de prova
- pistas sobre o estilo do professor

## Artefatos gerados
- `raw/`: arquivo original
- `staging/`: extração automática
- `manual-review/`: revisão humana guiada
- `content/` e `exams/`: conhecimento curado
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
```

## Camada base
Responsável por gerar uma primeira saída rápida e barata.

### Backends
- `pymupdf4llm`: Markdown rápido e bom para PDFs digitais simples.
- `pymupdf`: fallback bruto quando o PyMuPDF4LLM não estiver disponível.

## Camada avançada
Responsável por documentos difíceis.

### Backends
- `docling`: OCR, fórmulas, tabelas e imagens referenciadas.
- `marker`: saída avançada para equações, inline math, tabelas e imagens.

## Camada de artefatos
- imagens embutidas do PDF
- previews de páginas
- tabelas em CSV/Markdown
- detecção adicional de tabelas

## Camada manual assisted
Todo material relevante para prova passa por revisão guiada.
O objetivo é preservar:
- integridade factual
- fórmulas em LaTeX
- tabelas corretas
- padrão de cobrança do professor

## Modos de processamento
- `quick`: velocidade máxima, normalmente só camada base.
- `high_fidelity`: camada base + avançada sempre que possível.
- `manual_assisted`: base + artefatos + revisão humana forte.
- `auto`: decide pelo perfil do documento.

## Perfis de documento
- `general`
- `math_heavy`
- `layout_heavy`
- `scanned`
- `exam_pdf`

## Regra de ouro
O tutor não deve consumir o PDF bruto como fonte final.
A fonte final deve ser o Markdown curado derivado da revisão manual.
"""


def backend_policy_yaml(options: Dict[str, object]) -> str:
    return f"""version: 3
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
    O conhecimento final deve sair de manual-review/ e depois ser promovido.
"""


def root_readme(course_meta: Dict[str, str]) -> str:
    return f"""# {course_meta['course_name']}

Repositório gerado pelo **{APP_NAME}**.

## Estrutura
- `raw/`: materiais originais
- `staging/`: extração automática
- `manual-review/`: revisão guiada
- `content/`, `exercises/`, `exams/`: conhecimento curado
- `build/gpt-knowledge/`: bundle inicial para GPT

## Fluxo recomendado
1. Adicionar PDFs e imagens
2. Rodar extração automática
3. Revisar `manual-review/`
4. Promover conteúdo curado para `content/`, `exercises/` e `exams/`
5. Atualizar `build/gpt-knowledge/`

## Backends em camadas
- Base: PyMuPDF4LLM / PyMuPDF
- Avançado: Docling / Marker
- Revisão humana obrigatória para materiais críticos de prova
"""


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class FileEntryDialog(simpledialog.Dialog):
    def __init__(self, parent, path: str, initial: Optional[FileEntry] = None, default_mode: str = "auto", default_ocr_language: str = "por,eng"):
        self.path = path
        self.initial = initial
        self.default_mode = default_mode
        self.default_ocr_language = default_ocr_language
        self.result_entry: Optional[FileEntry] = None
        super().__init__(parent, title="Editar item")

    def body(self, master):
        src = Path(self.path)
        self.file_type = "pdf" if src.suffix.lower() == ".pdf" else "image"

        ttk.Label(master, text=f"Arquivo: {src.name}").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        self.var_title = tk.StringVar(value=self.initial.title if self.initial else src.stem)
        self.var_category = tk.StringVar(value=self.initial.category if self.initial else ("exams" if self.file_type == "pdf" else "photos-of-exams"))
        self.var_tags = tk.StringVar(value=self.initial.tags if self.initial else "")
        self.var_notes = tk.StringVar(value=self.initial.notes if self.initial else "")
        self.var_prof = tk.StringVar(value=self.initial.professor_signal if self.initial else "")
        self.var_bundle = tk.BooleanVar(value=self.initial.include_in_bundle if self.initial else True)
        self.var_exam = tk.BooleanVar(value=self.initial.relevant_for_exam if self.initial else True)

        self.var_mode = tk.StringVar(value=self.initial.processing_mode if self.initial else self.default_mode)
        self.var_profile = tk.StringVar(value=self.initial.document_profile if self.initial else "auto")
        self.var_backend = tk.StringVar(value=self.initial.preferred_backend if self.initial else "auto")
        self.var_formula = tk.BooleanVar(value=self.initial.formula_priority if self.initial else False)
        self.var_keep_images = tk.BooleanVar(value=self.initial.preserve_pdf_images_in_markdown if self.initial else True)
        self.var_force_ocr = tk.BooleanVar(value=self.initial.force_ocr if self.initial else False)
        self.var_previews = tk.BooleanVar(value=self.initial.export_page_previews if self.initial else True)
        self.var_imgs = tk.BooleanVar(value=self.initial.extract_images if self.initial else True)
        self.var_tables = tk.BooleanVar(value=self.initial.extract_tables if self.initial else True)
        self.var_page_range = tk.StringVar(value=self.initial.page_range if self.initial else "")
        self.var_ocr_lang = tk.StringVar(value=self.initial.ocr_language if self.initial else self.default_ocr_language)

        row = 1
        ttk.Label(master, text="Título").grid(row=row, column=0, sticky="w")
        ttk.Entry(master, textvariable=self.var_title, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        ttk.Label(master, text="Categoria").grid(row=row, column=0, sticky="w")
        ttk.Combobox(master, textvariable=self.var_category, values=DEFAULT_CATEGORIES, state="readonly", width=22).grid(row=row, column=1, sticky="ew")
        ttk.Label(master, text="Modo").grid(row=row, column=2, sticky="w")
        ttk.Combobox(master, textvariable=self.var_mode, values=PROCESSING_MODES, state="readonly", width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        ttk.Label(master, text="Perfil").grid(row=row, column=0, sticky="w")
        ttk.Combobox(master, textvariable=self.var_profile, values=DOCUMENT_PROFILES, state="readonly", width=22).grid(row=row, column=1, sticky="ew")
        ttk.Label(master, text="Backend preferido").grid(row=row, column=2, sticky="w")
        ttk.Combobox(master, textvariable=self.var_backend, values=PREFERRED_BACKENDS, state="readonly", width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        ttk.Label(master, text="Tags").grid(row=row, column=0, sticky="w")
        ttk.Entry(master, textvariable=self.var_tags, width=26).grid(row=row, column=1, sticky="ew")
        ttk.Label(master, text="OCR lang").grid(row=row, column=2, sticky="w")
        ttk.Combobox(master, textvariable=self.var_ocr_lang, values=OCR_LANGS, width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        ttk.Label(master, text="Notas").grid(row=row, column=0, sticky="w")
        ttk.Entry(master, textvariable=self.var_notes, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        ttk.Label(master, text="Pista do professor").grid(row=row, column=0, sticky="w")
        ttk.Entry(master, textvariable=self.var_prof, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        ttk.Checkbutton(master, text="Relevante para prova", variable=self.var_exam).grid(row=row, column=0, sticky="w")
        ttk.Checkbutton(master, text="Incluir no bundle inicial", variable=self.var_bundle).grid(row=row, column=1, sticky="w")
        ttk.Checkbutton(master, text="Prioridade em fórmulas", variable=self.var_formula).grid(row=row, column=2, sticky="w")
        row += 1

        if self.file_type == "pdf":
            ttk.Checkbutton(master, text="Preservar imagens do PDF no Markdown base", variable=self.var_keep_images).grid(row=row, column=0, columnspan=2, sticky="w")
            ttk.Checkbutton(master, text="Forçar OCR", variable=self.var_force_ocr).grid(row=row, column=2, sticky="w")
            row += 1

            ttk.Checkbutton(master, text="Exportar previews das páginas", variable=self.var_previews).grid(row=row, column=0, sticky="w")
            ttk.Checkbutton(master, text="Extrair imagens do PDF", variable=self.var_imgs).grid(row=row, column=1, sticky="w")
            ttk.Checkbutton(master, text="Extrair tabelas", variable=self.var_tables).grid(row=row, column=2, sticky="w")
            row += 1

            ttk.Label(master, text="Page range").grid(row=row, column=0, sticky="w")
            ttk.Entry(master, textvariable=self.var_page_range, width=18).grid(row=row, column=1, sticky="w")
            ttk.Label(master, text='Ex.: "1-4" ou "0,2,5-7"').grid(row=row, column=2, columnspan=2, sticky="w")
            row += 1

        master.columnconfigure(1, weight=1)
        master.columnconfigure(3, weight=1)
        return master

    def apply(self):
        self.result_entry = FileEntry(
            source_path=self.path,
            file_type=self.file_type,
            category=self.var_category.get(),
            title=self.var_title.get().strip() or Path(self.path).stem,
            tags=self.var_tags.get().strip(),
            notes=self.var_notes.get().strip(),
            professor_signal=self.var_prof.get().strip(),
            relevant_for_exam=self.var_exam.get(),
            include_in_bundle=self.var_bundle.get(),
            processing_mode=self.var_mode.get(),
            document_profile=self.var_profile.get(),
            preferred_backend=self.var_backend.get(),
            formula_priority=self.var_formula.get() if self.file_type == "pdf" else False,
            preserve_pdf_images_in_markdown=self.var_keep_images.get() if self.file_type == "pdf" else False,
            force_ocr=self.var_force_ocr.get() if self.file_type == "pdf" else False,
            export_page_previews=self.var_previews.get() if self.file_type == "pdf" else False,
            extract_images=self.var_imgs.get() if self.file_type == "pdf" else False,
            extract_tables=self.var_tables.get() if self.file_type == "pdf" else False,
            page_range=self.var_page_range.get().strip() if self.file_type == "pdf" else "",
            ocr_language=self.var_ocr_lang.get().strip() or self.default_ocr_language,
        )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1320x820")
        self.entries: List[FileEntry] = []
        self._build_ui()

    def _build_ui(self):
        self.var_repo_root = tk.StringVar()
        self.var_course_name = tk.StringVar()
        self.var_course_slug = tk.StringVar()
        self.var_semester = tk.StringVar()
        self.var_professor = tk.StringVar()
        self.var_institution = tk.StringVar(value="PUCRS")
        self.var_default_mode = tk.StringVar(value="auto")
        self.var_default_ocr_language = tk.StringVar(value="por,eng")

        top = ttk.Frame(self, padding=12)
        top.pack(fill="both", expand=True)

        course = ttk.LabelFrame(top, text="Dados da disciplina", padding=10)
        course.pack(fill="x", pady=(0, 8))

        ttk.Label(course, text="Nome da disciplina").grid(row=0, column=0, sticky="w")
        ttk.Entry(course, textvariable=self.var_course_name, width=34).grid(row=0, column=1, sticky="ew", padx=(8, 12))
        ttk.Label(course, text="Slug").grid(row=0, column=2, sticky="w")
        ttk.Entry(course, textvariable=self.var_course_slug, width=20).grid(row=0, column=3, sticky="ew", padx=(8, 12))
        ttk.Label(course, text="Semestre").grid(row=1, column=0, sticky="w")
        ttk.Entry(course, textvariable=self.var_semester, width=18).grid(row=1, column=1, sticky="w", padx=(8, 12))
        ttk.Label(course, text="Professor").grid(row=1, column=2, sticky="w")
        ttk.Entry(course, textvariable=self.var_professor, width=24).grid(row=1, column=3, sticky="ew", padx=(8, 12))
        ttk.Label(course, text="Instituição").grid(row=2, column=0, sticky="w")
        ttk.Entry(course, textvariable=self.var_institution, width=18).grid(row=2, column=1, sticky="w", padx=(8, 12))

        ttk.Label(course, text="Pasta do repositório").grid(row=3, column=0, sticky="w")
        ttk.Entry(course, textvariable=self.var_repo_root).grid(row=3, column=1, columnspan=2, sticky="ew", padx=(8, 12))
        ttk.Button(course, text="Escolher pasta", command=self.pick_repo_root).grid(row=3, column=3, sticky="ew")

        ttk.Label(course, text="Modo padrão").grid(row=4, column=0, sticky="w")
        ttk.Combobox(course, textvariable=self.var_default_mode, values=PROCESSING_MODES, state="readonly", width=18).grid(row=4, column=1, sticky="w", padx=(8, 12))
        ttk.Label(course, text="OCR padrão").grid(row=4, column=2, sticky="w")
        ttk.Combobox(course, textvariable=self.var_default_ocr_language, values=OCR_LANGS, width=20).grid(row=4, column=3, sticky="ew", padx=(8, 12))

        course.columnconfigure(1, weight=1)
        course.columnconfigure(3, weight=1)

        toolbar = ttk.Frame(top)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Adicionar PDFs", command=self.add_pdfs).pack(side="left")
        ttk.Button(toolbar, text="Adicionar imagens/fotos", command=self.add_images).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Editar selecionado", command=self.edit_selected).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Duplicar selecionado", command=self.duplicate_selected).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Remover selecionado", command=self.remove_selected).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Criar repositório", command=self.build_repo).pack(side="right")

        table_frame = ttk.LabelFrame(top, text="Arquivos importados", padding=8)
        table_frame.pack(fill="both", expand=True)

        columns = ("type", "category", "mode", "profile", "backend", "title", "source")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=22)
        self.tree.heading("type", text="Tipo")
        self.tree.heading("category", text="Categoria")
        self.tree.heading("mode", text="Modo")
        self.tree.heading("profile", text="Perfil")
        self.tree.heading("backend", text="Preferência")
        self.tree.heading("title", text="Título")
        self.tree.heading("source", text="Arquivo")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("category", width=130, anchor="center")
        self.tree.column("mode", width=110, anchor="center")
        self.tree.column("profile", width=110, anchor="center")
        self.tree.column("backend", width=110, anchor="center")
        self.tree.column("title", width=310)
        self.tree.column("source", width=360)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")

        help_box = ttk.LabelFrame(top, text="Ambiente detectado", padding=10)
        help_box.pack(fill="x", pady=(8, 0))
        env_text = (
            f"PyMuPDF: {HAS_PYMUPDF} | "
            f"PyMuPDF4LLM: {HAS_PYMUPDF4LLM} | "
            f"pdfplumber: {HAS_PDFPLUMBER} | "
            f"docling: {bool(DOCILING_CLI)} | "
            f"marker_single: {bool(MARKER_CLI)}"
        )
        ttk.Label(help_box, text=env_text).pack(anchor="w")
        ttk.Label(
            help_box,
            text="Dica: use high_fidelity ou manual_assisted para provas, PDFs matemáticos e scans.",
            wraplength=1220,
        ).pack(anchor="w", pady=(4, 0))

    def pick_repo_root(self):
        path = filedialog.askdirectory(title="Escolha a pasta onde o repositório será criado")
        if path:
            self.var_repo_root.set(path)

    def _entry_dialog(self, path: str, initial: Optional[FileEntry] = None) -> Optional[FileEntry]:
        dialog = FileEntryDialog(self, path, initial=initial, default_mode=self.var_default_mode.get(), default_ocr_language=self.var_default_ocr_language.get())
        return dialog.result_entry

    def add_pdfs(self):
        paths = filedialog.askopenfilenames(title="Selecione PDFs", filetypes=[("PDF files", "*.pdf")])
        for path in paths:
            entry = self._entry_dialog(path)
            if entry:
                self.entries.append(entry)
        self.refresh_tree()

    def add_images(self):
        paths = filedialog.askopenfilenames(
            title="Selecione imagens/fotos",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff")],
        )
        for path in paths:
            entry = self._entry_dialog(path)
            if entry:
                self.entries.append(entry)
        self.refresh_tree()

    def selected_index(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(selected[0])

    def edit_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para editar.")
            return
        entry = self.entries[idx]
        updated = self._entry_dialog(entry.source_path, initial=entry)
        if updated:
            self.entries[idx] = updated
            self.refresh_tree()

    def duplicate_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para duplicar.")
            return
        entry = self.entries[idx]
        copied = FileEntry(**asdict(entry))
        copied.title = f"{entry.title} (cópia)"
        self.entries.insert(idx + 1, copied)
        self.refresh_tree()

    def remove_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para remover.")
            return
        del self.entries[idx]
        self.refresh_tree()

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, entry in enumerate(self.entries):
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    entry.file_type,
                    entry.category,
                    entry.processing_mode,
                    entry.document_profile,
                    entry.preferred_backend,
                    entry.title,
                    Path(entry.source_path).name,
                ),
            )

    def _course_meta(self) -> Optional[Dict[str, str]]:
        course_name = self.var_course_name.get().strip()
        repo_root = self.var_repo_root.get().strip()
        if not course_name or not repo_root:
            messagebox.showerror(APP_NAME, "Preencha ao menos o nome da disciplina e a pasta do repositório.")
            return None
        course_slug = self.var_course_slug.get().strip() or slugify(course_name)
        return {
            "course_name": course_name,
            "course_slug": course_slug,
            "semester": self.var_semester.get().strip(),
            "professor": self.var_professor.get().strip(),
            "institution": self.var_institution.get().strip() or "PUCRS",
        }

    def build_repo(self):
        meta = self._course_meta()
        if meta is None:
            return
        if not self.entries:
            if not messagebox.askyesno(APP_NAME, "Nenhum arquivo foi adicionado. Criar apenas a estrutura do repositório?"):
                return

        root_base = Path(self.var_repo_root.get().strip())
        repo_dir = root_base / meta["course_slug"]

        try:
            builder = RepoBuilder(
                root_dir=repo_dir,
                course_meta=meta,
                entries=self.entries,
                options={
                    "default_processing_mode": self.var_default_mode.get(),
                    "default_ocr_language": self.var_default_ocr_language.get(),
                },
            )
            builder.build()
        except Exception:
            traceback_str = traceback.format_exc()
            messagebox.showerror(APP_NAME, f"Erro ao criar repositório:\n\n{traceback_str}")
            return

        messagebox.showinfo(
            APP_NAME,
            f"Repositório criado com sucesso em:\n{repo_dir}\n\n"
            f"Próximo passo recomendado:\n"
            f"1. revisar manual-review/\n"
            f"2. escolher a melhor saída entre base e avançada\n"
            f"3. promover conteúdo curado\n"
            f"4. subir no GitHub"
        )


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
