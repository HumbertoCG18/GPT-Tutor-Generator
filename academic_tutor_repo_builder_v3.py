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
import logging
import os
import re
import shutil
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

# Optional dependencies
try:
    import pymupdf  # PyMuPDF
    HAS_PYMUPDF = True
except Exception:
    pymupdf = None
    HAS_PYMUPDF = False
    logger.info("pymupdf not available; PyMuPDF backend disabled.")

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except Exception:
    pymupdf4llm = None
    HAS_PYMUPDF4LLM = False
    logger.info("pymupdf4llm not available; PyMuPDF4LLM backend disabled.")

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except Exception:
    pdfplumber = None
    HAS_PDFPLUMBER = False
    logger.info("pdfplumber not available; table extraction via pdfplumber disabled.")

DOCLING_CLI = shutil.which("docling")
MARKER_CLI = shutil.which("marker_single")

APP_NAME = "Academic Tutor Repo Builder V3"

DEFAULT_CATEGORIES = [
    "material-de-aula",
    "provas",
    "listas",
    "gabaritos",
    "fotos-de-prova",
    "referencias",
    "bibliografia",
    "cronograma",
    "outros",
]

CATEGORY_LABELS: Dict[str, str] = {
    "material-de-aula": "📘 Material de aula (slides, notas, apostilas)",
    "provas": "📝 Provas anteriores",
    "listas": "📋 Listas de exercícios",
    "gabaritos": "✅ Gabaritos e resoluções",
    "fotos-de-prova": "📷 Fotos de provas/cadernos",
    "referencias": "📚 Referências e documentos",
    "bibliografia": "🔗 Bibliografia (livros, artigos, links)",
    "cronograma": "📅 Cronograma da disciplina",
    "outros": "📦 Outros materiais",
}

# Legacy category mapping for backwards compatibility
_LEGACY_CATEGORY_MAP: Dict[str, str] = {
    "course-material": "material-de-aula",
    "exams": "provas",
    "exercise-lists": "listas",
    "rubrics": "gabaritos",
    "schedule": "cronograma",
    "references": "referencias",
    "photos-of-exams": "fotos-de-prova",
    "answer-keys": "gabaritos",
    "other": "outros",
}

IMAGE_CATEGORIES = {"fotos-de-prova", "provas", "material-de-aula", "outros"}

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
# Subject & Student Profiles
# ---------------------------------------------------------------------------

@dataclass
class SubjectProfile:
    """Perfil salvo de uma matéria — preenche automaticamente os campos da disciplina."""
    name: str = ""
    slug: str = ""
    professor: str = ""
    institution: str = "PUCRS"
    semester: str = ""
    schedule: str = ""           # "Seg/Qua 10:15-11:55"
    syllabus: str = ""           # Cronograma multilinea
    default_mode: str = "auto"
    default_ocr_lang: str = "por,eng"
    repo_root: str = ""

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "SubjectProfile":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class StudentProfile:
    """Perfil do aluno — exportado nos repositórios gerados."""
    full_name: str = ""
    nickname: str = ""           # Como o GPT chama o aluno
    semester: str = ""           # "3º semestre"
    institution: str = "PUCRS"
    personality: str = ""        # Como o GPT deve ajudar (texto livre)

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "StudentProfile":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})


class SubjectStore:
    """Persistência de perfis de matérias em JSON."""
    _path = Path.home() / ".gpt_tutor_subjects.json"

    def __init__(self):
        self._subjects: List[SubjectProfile] = []
        self.load()

    def load(self):
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                self._subjects = [SubjectProfile.from_dict(d) for d in raw]
            except Exception:
                self._subjects = []

    def save(self):
        data = [s.to_dict() for s in self._subjects]
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")

    def all(self) -> List[SubjectProfile]:
        return list(self._subjects)

    def names(self) -> List[str]:
        return [s.name for s in self._subjects]

    def get(self, name: str) -> Optional[SubjectProfile]:
        for s in self._subjects:
            if s.name == name:
                return s
        return None

    def add(self, sp: SubjectProfile):
        # Replace if exists
        self._subjects = [s for s in self._subjects if s.name != sp.name]
        self._subjects.append(sp)
        self.save()

    def delete(self, name: str):
        self._subjects = [s for s in self._subjects if s.name != name]
        self.save()


class StudentStore:
    """Persistência do perfil do aluno em JSON."""
    _path = Path.home() / ".gpt_tutor_student.json"

    def __init__(self):
        self._profile = StudentProfile()
        self.load()

    def load(self):
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text("utf-8"))
                self._profile = StudentProfile.from_dict(raw)
            except Exception:
                self._profile = StudentProfile()

    def save(self):
        self._path.write_text(
            json.dumps(self._profile.to_dict(), indent=2, ensure_ascii=False), "utf-8"
        )

    @property
    def profile(self) -> StudentProfile:
        return self._profile

    @profile.setter
    def profile(self, p: StudentProfile):
        self._profile = p
        self.save()


# ---------------------------------------------------------------------------
# Auto-detection Utilities
# ---------------------------------------------------------------------------

import re as _re  # keep near usage

_CATEGORY_PATTERNS: List[Tuple[str, List[str]]] = [
    ("provas",          ["prova", "p1", "p2", "p3", "ap1", "ap2", "ap3", "exam", "midterm", "final"]),
    ("listas",          ["lista", "exercicio", "exercícios", "exercise", "ex-", "atividade"]),
    ("gabaritos",       ["gabarito", "resolucao", "resolução", "resposta", "answer", "solucao", "solução"]),
    ("material-de-aula",["slide", "aula", "notas", "cap", "capitulo", "capítulo", "apostila", "resumo"]),
    ("fotos-de-prova",  ["foto", "photo", "img_", "scan"]),
    ("cronograma",      ["cronograma", "calendario", "calendário", "schedule", "plano-de-ensino"]),
    ("referencias",     ["referencia", "referência", "reference", "livro", "book"]),
    ("bibliografia",    ["biblio", "artigo", "paper", "article"]),
]


def auto_detect_category(filename: str, is_image: bool = False) -> str:
    """Detecta a categoria provável a partir do nome do arquivo."""
    name_lower = filename.lower().replace("_", "-").replace(" ", "-")
    for cat, patterns in _CATEGORY_PATTERNS:
        for p in patterns:
            if p in name_lower:
                return cat
    if is_image:
        return "fotos-de-prova"
    return "outros"


def auto_detect_title(filepath: str) -> str:
    """Gera título legível a partir do nome do arquivo."""
    stem = Path(filepath).stem
    # Remove common prefixes like timestamps
    cleaned = _re.sub(r"^\d{4}[-_]\d{2}[-_]\d{2}[-_]?", "", stem)
    # Replace separators with spaces
    cleaned = cleaned.replace("_", " ").replace("-", " ")
    # Collapse whitespace and title-case
    cleaned = " ".join(cleaned.split())
    if cleaned:
        return cleaned.title()
    return stem.title()


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
            "student",
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
        
        # System Prompt Generation
        sprompt = generate_system_prompt(self.course_meta, self.student_profile, self.subject_profile)
        write_text(self.root_dir / "INSTRUCOES_DO_GPT.txt", sprompt)

        # Student profile
        if self.student_profile:
            sp = self.student_profile
            write_text(
                self.root_dir / "student" / "STUDENT_PROFILE.md",
                f"""---
nickname: {sp.nickname or sp.full_name}
semester: {sp.semester}
institution: {sp.institution}
---

# Perfil do Aluno

- **Nome:** {sp.full_name}
- **Apelido:** {sp.nickname or sp.full_name}
- **Semestre:** {sp.semester}
- **Instituição:** {sp.institution}

## Personalidade do Tutor

{sp.personality}
""",
            )

        # Syllabus (cronograma)
        if self.subject_profile and self.subject_profile.syllabus:
            subj = self.subject_profile
            write_text(
                self.root_dir / "course" / "SYLLABUS.md",
                f"""---
course: {subj.name}
professor: {subj.professor}
schedule: {subj.schedule}
---

# Cronograma — {subj.name}

**Horário:** {subj.schedule}

{subj.syllabus}
""",
            )

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
            f"- docling_cli: {bool(DOCLING_CLI)}",
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
        if entry.file_type != "url" and not src.exists():
            raise FileNotFoundError(f"Source file not found: {src}")
            
        if entry.file_type == "url":
            safe_name = f"{entry.id()}.url"
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
            image_category = entry.category if entry.category in IMAGE_CATEGORIES else "other"
            raw_target = self.root_dir / "raw" / "images" / image_category / safe_name
            ensure_dir(raw_target.parent)
            shutil.copy2(src, raw_target)
            item["raw_target"] = safe_rel(raw_target, self.root_dir)
            item.update(self._process_image(entry, raw_target))

        return item

    def _process_url(self, entry: FileEntry) -> Dict[str, object]:
        item: Dict[str, object] = {
            "document_report": None,
            "pipeline_decision": None,
            "base_markdown": None,
            "advanced_markdown": None,
            "advanced_backend": None,
            "base_backend": "url_fetcher",
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
                markdown_content += text[:15000] # Limite para não explodir arquivos
                
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
        
        # Cria review manual
        manual = self.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
        write_text(manual, manual_pdf_review_template(entry, item))
        item["manual_review"] = safe_rel(manual, self.root_dir)
        
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
# GUI — Utilities: Tooltip, ThemeManager, AppConfig
# ---------------------------------------------------------------------------

CONFIG_PATH = Path.home() / ".gpt_tutor_config.json"

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#1e1e2e",
        "frame_bg": "#181825",
        "input_bg": "#313244",
        "fg": "#cdd6f4",
        "muted": "#6c7086",
        "accent": "#89b4fa",
        "accent2": "#cba6f7",
        "select_bg": "#45475a",
        "select_fg": "#cdd6f4",
        "button_bg": "#313244",
        "button_active": "#45475a",
        "border": "#45475a",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "header_bg": "#11111b",
        "header_fg": "#89b4fa",
        "tooltip_bg": "#313244",
        "tooltip_fg": "#cdd6f4",
        "treeview_odd": "#1e1e2e",
        "treeview_even": "#24273a",
    },
    "light": {
        "bg": "#eff1f5",
        "frame_bg": "#e6e9ef",
        "input_bg": "#ffffff",
        "fg": "#4c4f69",
        "muted": "#8c8fa1",
        "accent": "#1e66f5",
        "accent2": "#8839ef",
        "select_bg": "#c9cbff",
        "select_fg": "#4c4f69",
        "button_bg": "#dce0e8",
        "button_active": "#bcc0cc",
        "border": "#bcc0cc",
        "success": "#40a02b",
        "warning": "#df8e1d",
        "error": "#d20f39",
        "header_bg": "#dce0e8",
        "header_fg": "#1e66f5",
        "tooltip_bg": "#feffe0",
        "tooltip_fg": "#4c4f69",
        "treeview_odd": "#eff1f5",
        "treeview_even": "#e6e9ef",
    },
    "solarized": {
        "bg": "#002b36",
        "frame_bg": "#073642",
        "input_bg": "#073642",
        "fg": "#839496",
        "muted": "#586e75",
        "accent": "#268bd2",
        "accent2": "#6c71c4",
        "select_bg": "#073642",
        "select_fg": "#93a1a1",
        "button_bg": "#073642",
        "button_active": "#0d4a5a",
        "border": "#586e75",
        "success": "#859900",
        "warning": "#b58900",
        "error": "#dc322f",
        "header_bg": "#00212b",
        "header_fg": "#268bd2",
        "tooltip_bg": "#073642",
        "tooltip_fg": "#93a1a1",
        "treeview_odd": "#002b36",
        "treeview_even": "#073642",
    },
}


class AppConfig:
    """Manages persistent app configuration via ~/.gpt_tutor_config.json."""

    DEFAULTS: Dict[str, object] = {
        "theme": "dark",
        "default_mode": "auto",
        "default_ocr_language": "por,eng",
        "default_profile": "auto",
        "default_backend": "auto",
        "font_size": 10,
    }

    def __init__(self):
        self.data: Dict[str, object] = dict(self.DEFAULTS)
        self._load()

    def _load(self) -> None:
        try:
            if CONFIG_PATH.exists():
                stored = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                self.data.update({k: v for k, v in stored.items() if k in self.DEFAULTS})
        except Exception:
            pass

    def save(self) -> None:
        try:
            CONFIG_PATH.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def get(self, key: str, default=None):
        return self.data.get(key, default if default is not None else self.DEFAULTS.get(key))

    def set(self, key: str, value) -> None:
        self.data[key] = value


class ThemeManager:
    """Applies a colour palette to all ttk/tk widgets via ttk.Style."""

    def __init__(self):
        self._current: str = "dark"

    @property
    def current(self) -> str:
        return self._current

    def palette(self, name: str) -> Dict[str, str]:
        return THEMES.get(name, THEMES["dark"])

    def apply_titlebar_color(self, window: tk.Widget) -> None:
        try:
            import platform
            if platform.system() != "Windows":
                return
            import ctypes
            
            window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            is_dark = self._current == "dark"
            
            value = ctypes.c_int(2 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), 4)
            value_win10 = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value_win10), 4)
        except Exception:
            pass

    def apply(self, root: tk.Tk, name: str) -> None:
        p = self.palette(name)
        self._current = name
        style = ttk.Style(root)

        # Use a clean base theme
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Root background
        root.configure(bg=p["bg"])
        
        # Apply dark mode titlebar on Windows
        def _on_map(event):
            if isinstance(event.widget, (tk.Tk, tk.Toplevel)):
                self.apply_titlebar_color(event.widget)
        root.bind_all("<Map>", _on_map, add="+")


        # Fix Standard Tk Widgets (Text, Listbox, etc.) white backgrounds
        root.option_add("*Text.background", p["input_bg"])
        root.option_add("*Text.foreground", p["fg"])
        root.option_add("*Listbox.background", p["input_bg"])
        root.option_add("*Listbox.foreground", p["fg"])
        root.option_add("*Listbox.selectBackground", p["select_bg"])
        root.option_add("*Listbox.selectForeground", p["select_fg"])

        font_body = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 10, "bold")
        font_small = ("Segoe UI", 9)

        # TFrame / TLabelFrame
        style.configure("TFrame", background=p["bg"])
        style.configure("TLabelframe", background=p["frame_bg"], bordercolor=p["border"], relief="flat")
        style.configure("TLabelframe.Label", background=p["frame_bg"], foreground=p["accent"], font=font_bold)

        # TLabel
        style.configure("TLabel", background=p["bg"], foreground=p["fg"], font=font_body)
        style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"], font=font_small)
        style.configure("Header.TLabel", background=p["header_bg"], foreground=p["header_fg"], font=font_bold)
        style.configure("Accent.TLabel", background=p["bg"], foreground=p["accent"], font=font_bold)

        # TEntry
        style.configure("TEntry", fieldbackground=p["input_bg"], foreground=p["fg"],
                         insertcolor=p["fg"], bordercolor=p["border"], font=font_body)
        style.map("TEntry", bordercolor=[("focus", p["accent"])])

        # TCombobox
        style.configure("TCombobox", fieldbackground=p["input_bg"], foreground=p["fg"],
                         background=p["button_bg"], selectbackground=p["select_bg"],
                         selectforeground=p["select_fg"], bordercolor=p["border"], font=font_body)
        style.map("TCombobox", fieldbackground=[("readonly", p["input_bg"])],
                  selectbackground=[("readonly", p["select_bg"])],
                  foreground=[("readonly", p["fg"])])
        root.option_add("*TCombobox*Listbox.background", p["input_bg"])
        root.option_add("*TCombobox*Listbox.foreground", p["fg"])
        root.option_add("*TCombobox*Listbox.selectBackground", p["select_bg"])
        root.option_add("*TCombobox*Listbox.selectForeground", p["select_fg"])

        # TButton
        style.configure("TButton", background=p["button_bg"], foreground=p["fg"],
                         bordercolor=p["border"], font=font_body, padding=(8, 4))
        style.map("TButton",
                  background=[("active", p["button_active"]), ("pressed", p["accent"])],
                  foreground=[("pressed", p["bg"])])
        style.configure("Accent.TButton", background=p["accent"], foreground=p["bg"],
                         bordercolor=p["accent"], font=font_bold, padding=(10, 5))
        style.map("Accent.TButton",
                  background=[("active", p["accent2"]), ("pressed", p["accent2"])])

        # TCheckbutton
        style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"], font=font_body)
        style.map("TCheckbutton", background=[("active", p["bg"])],
                  foreground=[("active", p["accent"])])

        # TRadiobutton
        style.configure("TRadiobutton", background=p["bg"], foreground=p["fg"], font=font_body)
        style.map("TRadiobutton", background=[("active", p["bg"])],
                  foreground=[("active", p["accent"])])

        # TNotebook
        style.configure("TNotebook", background=p["bg"], bordercolor=p["border"])
        style.configure("TNotebook.Tab", background=p["button_bg"], foreground=p["muted"],
                         font=font_body, padding=(12, 5))
        style.map("TNotebook.Tab",
                  background=[("selected", p["frame_bg"])],
                  foreground=[("selected", p["accent"])])

        # Treeview
        style.configure("Treeview", background=p["treeview_odd"], foreground=p["fg"],
                         fieldbackground=p["treeview_odd"], bordercolor=p["border"],
                         rowheight=26, font=font_body)
        style.configure("Treeview.Heading", background=p["header_bg"], foreground=p["header_fg"],
                         font=font_bold, relief="flat")
        style.map("Treeview",
                  background=[("selected", p["select_bg"])],
                  foreground=[("selected", p["select_fg"])])
        style.map("Treeview.Heading", background=[("active", p["button_active"])])

        # Scrollbar
        style.configure("TScrollbar", background=p["button_bg"], troughcolor=p["bg"],
                         bordercolor=p["bg"], arrowcolor=p["muted"])

        # Separator
        style.configure("TSeparator", background=p["border"])

        # Progressbar
        style.configure("TProgressbar", background=p["accent"], troughcolor=p["bg"])

        # Status bar style
        style.configure("Status.TLabel", background=p["header_bg"], foreground=p["muted"],
                         font=font_small, padding=(6, 3))


class Tooltip:
    """Shows a descriptive tooltip balloon after the mouse hovers for `delay` ms."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 600):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._job = None
        self._tip: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event=None):
        self._cancel()
        self._job = self.widget.after(self.delay, self._show)

    def _on_leave(self, _event=None):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self._job:
            self.widget.after_cancel(self._job)
            self._job = None

    def _show(self):
        if self._tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        # Try to get theme colours from the root
        try:
            root = self.widget.winfo_toplevel()
            theme_name = getattr(root, "_theme_name", "dark")
            p = THEMES.get(theme_name, THEMES["dark"])
            bg, fg = p["tooltip_bg"], p["tooltip_fg"]
            border = p["border"]
        except Exception:
            bg, fg, border = "#313244", "#cdd6f4", "#45475a"

        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        self._tip.attributes("-topmost", True)

        frame = tk.Frame(self._tip, background=border, bd=0)
        frame.pack()
        inner = tk.Frame(frame, background=bg, bd=0, padx=10, pady=6)
        inner.pack(padx=1, pady=1)
        tk.Label(
            inner,
            text=self.text,
            background=bg,
            foreground=fg,
            font=("Segoe UI", 9),
            wraplength=320,
            justify="left",
        ).pack()

    def _hide(self):
        if self._tip:
            self._tip.destroy()
            self._tip = None


def add_tooltip(widget: tk.Widget, text: str, delay: int = 600) -> Tooltip:
    """Convenience function to attach a Tooltip to any widget."""
    return Tooltip(widget, text, delay)


# ---------------------------------------------------------------------------
# GUI — Settings Dialog
# ---------------------------------------------------------------------------

class SettingsDialog(tk.Toplevel):
    """Modal settings window with Appearance and Processing tabs."""

    def __init__(self, parent: tk.Tk, config: AppConfig, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.theme_mgr = theme_mgr
        self.title("Configurações")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._saved = False
        self._build()
        self.update_idletasks()
        # Centre over parent
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w)//2}+{py + (ph - h)//2}")

    def _build(self):
        p = self.theme_mgr.palette(self.theme_mgr.current)
        self.configure(bg=p["bg"])

        # Header
        hdr = tk.Frame(self, bg=p["header_bg"], pady=12, padx=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  Configurações", bg=p["header_bg"], fg=p["header_fg"],
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(hdr, text="Personalize o comportamento e aparência do app.",
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9)).pack(anchor="w")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Appearance tab ──────────────────────────────────────────────
        tab_app = ttk.Frame(nb, padding=16)
        nb.add(tab_app, text="  🎨  Aparência  ")

        ttk.Label(tab_app, text="Tema da interface", style="Accent.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self._var_theme = tk.StringVar(value=self.config.get("theme"))
        theme_desc = {
            "dark": "Escuro (Catppuccin Mocha)",
            "light": "Claro (Catppuccin Latte)",
            "solarized": "Solarized Dark",
        }
        for i, (key, label) in enumerate(theme_desc.items()):
            row_f = ttk.Frame(tab_app)
            row_f.grid(row=i + 1, column=0, columnspan=3, sticky="ew", pady=2)
            rb = ttk.Radiobutton(row_f, text=label, variable=self._var_theme,
                                  value=key, command=self._preview_theme)
            rb.pack(side="left")
            # Colour swatch
            sw_p = THEMES[key]
            swatch = tk.Canvas(row_f, width=80, height=18, bg=sw_p["bg"],
                                highlightthickness=1, highlightbackground=sw_p["border"])
            swatch.pack(side="left", padx=(8, 0))
            swatch.create_rectangle(1, 1, 26, 17, fill=sw_p["accent"], outline="")
            swatch.create_rectangle(27, 1, 52, 17, fill=sw_p["accent2"], outline="")
            swatch.create_rectangle(53, 1, 79, 17, fill=sw_p["input_bg"], outline="")

        # ── Processing tab ──────────────────────────────────────────────
        tab_proc = ttk.Frame(nb, padding=16)
        nb.add(tab_proc, text="  ⚙  Processamento  ")

        self._var_mode = tk.StringVar(value=self.config.get("default_mode"))
        self._var_ocr = tk.StringVar(value=self.config.get("default_ocr_language"))
        self._var_profile = tk.StringVar(value=self.config.get("default_profile"))
        self._var_backend = tk.StringVar(value=self.config.get("default_backend"))

        fields = [
            ("Modo de processamento padrão", self._var_mode, PROCESSING_MODES),
            ("Idioma OCR padrão", self._var_ocr, OCR_LANGS),
            ("Perfil de documento padrão", self._var_profile, DOCUMENT_PROFILES),
            ("Backend preferido padrão", self._var_backend, PREFERRED_BACKENDS),
        ]
        for r, (label, var, vals) in enumerate(fields):
            ttk.Label(tab_proc, text=label).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 16))
            ttk.Combobox(tab_proc, textvariable=var, values=vals, state="readonly",
                          width=22).grid(row=r, column=1, sticky="ew")
        tab_proc.columnconfigure(1, weight=1)

        # ── Buttons ─────────────────────────────────────────────────────
        btn_frame = ttk.Frame(self, padding=(16, 0, 16, 16))
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="Salvar", style="Accent.TButton",
                   command=self._save).pack(side="right")

    def _preview_theme(self):
        self.theme_mgr.apply(self.parent, self._var_theme.get())
        self.parent._theme_name = self._var_theme.get()  # type: ignore[attr-defined]
        # Rebuild self visuals too
        self.destroy()
        SettingsDialog(self.parent, self.config, self.theme_mgr)

    def _save(self):
        self.config.set("theme", self._var_theme.get())
        self.config.set("default_mode", self._var_mode.get())
        self.config.set("default_ocr_language", self._var_ocr.get())
        self.config.set("default_profile", self._var_profile.get())
        self.config.set("default_backend", self._var_backend.get())
        self.config.save()
        self.theme_mgr.apply(self.parent, self._var_theme.get())
        self.parent._theme_name = self._var_theme.get()  # type: ignore[attr-defined]
        self._saved = True
        self.destroy()

    def _cancel(self):
        # Revert preview if user just browsed themes
        self.theme_mgr.apply(self.parent, self.config.get("theme"))
        self.parent._theme_name = self.config.get("theme")  # type: ignore[attr-defined]
        self.destroy()


# ---------------------------------------------------------------------------
# GUI — Help Window
# ---------------------------------------------------------------------------

HELP_SECTIONS: List[Tuple[str, str]] = [
    ("Visão Geral", """O Academic Tutor Repo Builder converte PDFs e imagens acadêmicas em repositórios estruturados de conhecimento, prontos para uso com GPTs tutores.

Fluxo recomendado:
  1. Preencha os dados da disciplina.
  2. Adicione PDFs e imagens com os botões da barra de ferramentas.
  3. Configure cada arquivo (categoria, modo, perfil, etc.).
  4. Clique em "Criar repositório".
  5. Revise a pasta manual-review/ gerada.
  6. Promova o conteúdo curado para content/, exercises/, exams/.
"""),
    ("Dados da Disciplina", """NOME DA DISCIPLINA
  Nome completo como aparece no sistema acadêmico. Obrigatório.
  Exemplo: "Cálculo I", "Estruturas de Dados"

SLUG
  Identificador curto usado para nomear pastas e arquivos. Gerado automaticamente a partir do nome se vazio.
  Use letras minúsculas, números e hífens.
  Exemplo: "calculo-i", "estruturas-de-dados"

SEMESTRE
  Período letivo. Não há validação de formato; use o que fizer sentido.
  Exemplos: "2024/1", "2025-2", "1º sem 2025"

PROFESSOR
  Nome do professor principal da disciplina. Usado para contextualizar o tutor.

INSTITUIÇÃO
  Nome da instituição (padrão: PUCRS). Armazenado nos metadados.

PASTA DO REPOSITÓRIO
  Pasta onde o repositório será criado. Dentro dela, uma subpasta com o slug será gerada.
  Clicar em "Escolher pasta" abre o seletor de diretórios.
"""),
    ("Modos de Processamento", """Os modos controlam QUANTO processamento cada arquivo recebe.

auto
  Detecta automaticamente o tipo de documento e escolhe o melhor pipeline.
  Use quando não tiver certeza. É o padrão.

quick
  Só a camada base (pymupdf4llm ou pymupdf). Rápido e leve.
  Use para materiais simples: cronogramas, ementas, textos corridos.

high_fidelity
  Camada base + camada avançada (docling ou marker) quando disponível.
  Use para PDFs com fórmulas, tabelas complexas ou layout diferenciado.

manual_assisted
  Igual ao high_fidelity + geração de arquivo de revisão manual guiada.
  Use para provas, gabaritos, materiais críticos onde a precisão é essencial.
  Exige que você revise o conteúdo gerado antes de publicar.
"""),
    ("Perfis de Documento", """Os perfis descrevem o TIPO de conteúdo do documento e guiam a escolha de backend.

auto
  O sistema analisa o PDF (texto, imagens, tabelas, densidade) e decide.
  Recomendado por padrão.

general
  Documento de texto comum. Slides simples, ementas, cronogramas.

math_heavy
  Material com fórmulas matemáticas, notação LaTeX, teoremas.
  Ativa backends com suporte a fórmulas (docling --enrich-formula).

layout_heavy
  Documento com layout complexo: múltiplas colunas, figuras, tabelas elaboradas.
  Ativa processamento de imagens e layout referenciado.

scanned
  PDF gerado a partir de scanner ou foto, sem texto digital.
  Ativa OCR obrigatório em todos os backends.

exam_pdf
  Prova ou lista de exercícios. Combina necessidades de layout e fórmulas.
  Ativa camada avançada e revisão manual.
"""),
    ("Backends de Extração", """Os backends são os motores que extraem texto e conteúdo dos PDFs.

CAMADA BASE (rápida)
  pymupdf4llm — Markdown de alta qualidade para PDFs digitais. Recomendado.
  pymupdf    — Fallback bruto quando pymupdf4llm não está disponível.

CAMADA AVANÇADA (para documentos difíceis)
  docling    — OCR, fórmulas, tabelas e imagens referenciadas (CLI externo).
  marker     — Excelente para equações inline, tabelas e imagens (CLI externo).

BACKEND PREFERIDO
  Define qual backend usar por padrão para este arquivo, sobrepondo a seleção automática.
  Deixe "auto" para que o sistema escolha com base no perfil e modo.

  Se escolher docling ou marker como preferido, o sistema ainda executa a
  camada base (pymupdf4llm) como complemento.
"""),
    ("Opções por Arquivo", """TÍTULO
  Nome legível do documento. Usado nos metadados e no índice do repositório.

CATEGORIA
  Classifica o arquivo dentro da estrutura do repositório.
  course-material  → Slides, notas de aula, apostilas
  exams            → Provas anteriores em PDF
  exercise-lists   → Listas de exercícios
  rubrics          → Gabaritos e critérios de correção
  schedule         → Cronograma da disciplina
  references       → Livros, artigos, documentos de referência
  photos-of-exams  → Fotos de provas manuscritas
  answer-keys      → Gabaritos separados
  other            → Qualquer outro material

TAGS
  Palavras-chave separadas por vírgula para facilitar busca futura.
  Exemplo: "gabarito, integração, 2024-1"

NOTAS
  Observação livre sobre o arquivo. Não afeta o processamento.

PISTA DO PROFESSOR
  Registre padrões observados: tipo de cobrança, notação preferida, dificuldade recorrente.
  Exemplo: "cobra demonstração formal; mistura indução e recursão"

RELEVANTE PARA PROVA
  Marca o material como importante para preparação de provas. Afeta priorização no bundle.

INCLUIR NO BUNDLE INICIAL
  Se marcado, o arquivo entra no bundle.seed.json para alimentar o GPT tutor.

PRIORIDADE EM FÓRMULAS
  Força ativação do backend avançado mesmo em modo auto ou quick.
  Use quando o documento tem muitas equações críticas.
"""),
    ("Opções de PDF", """PRESERVAR IMAGENS NO MARKDOWN BASE
  Se marcado, o pymupdf4llm salva as imagens do PDF como arquivos externos
  referenciados no Markdown. Útil para manter figuras após a extração.

FORÇAR OCR
  Ignora o texto digital do PDF e passa tudo pelo OCR.
  Use para PDFs com texto não selecionável ou codificação incorreta.

EXPORTAR PREVIEWS DAS PÁGINAS
  Gera imagens PNG de cada página (resolução 1.5x) em staging/assets/page-previews/.
  Consome mais espaço mas facilita a revisão visual do conteúdo.

EXTRAIR IMAGENS DO PDF
  Extrai todas as imagens embutidas no PDF para staging/assets/images/.
  Requer PyMuPDF instalado.

EXTRAIR TABELAS
  Detecta e exporta tabelas como CSV e Markdown em staging/assets/tables/.
  Requer pdfplumber e/ou PyMuPDF instalados.

PAGE RANGE (Intervalo de páginas)
  Limita o processamento a páginas específicas.
  Formato: "1-5" (páginas 1 a 5), "1,3,7" (páginas 1, 3 e 7), "2, 5-8" (misto).
  Deixe em branco para processar todas as páginas.
  Tratamento: se o intervalo não contiver zero, é interpretado como base-1.

OCR LANGUAGE
  Idiomas para o mecanismo OCR. Separados por vírgula.
  por,eng → Português + Inglês (padrão recomendado)
  por     → Somente Português
  eng     → Somente Inglês
"""),
    ("Atalhos e Dicas", """ATALHOS
  F1          → Abre esta janela de ajuda
  Double-click → Edita o item selecionado na tabela
  Delete      → Remove o item selecionado (via botão na toolbar)

DICAS GERAIS
  • Duplique um item bem configurado para processar arquivos similares rapidamente.
  • O slug da disciplina define o nome da pasta raiz do repositório.
  • O arquivo manifest.json gerado contém o histórico completo de todas as decisões de pipeline.
  • Se um backend avançado falhar, o sistema registra o erro no manifest mas continua.
  • O arquivo BUILD_REPORT.md na raiz do repositório resume o que foi gerado.

AMBIENTE DETECTADO
  Se PyMuPDF, PyMuPDF4LLM ou pdfplumber aparecem como False na barra inferior,
  instale-os com: pip install pymupdf pymupdf4llm pdfplumber

  Para backends avançados (docling, marker): instale separadamente e certifique-se
  que os executáveis 'docling' e 'marker_single' estão no PATH do sistema.
"""),
]


class HelpWindow(tk.Toplevel):
    """F1-style help window with navigation panel and searchable content."""

    def __init__(self, parent: tk.Tk, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.title("Ajuda — Academic Tutor Repo Builder")
        self.geometry("900x620")
        self.minsize(700, 480)
        self.transient(parent)
        p = self.theme_mgr.palette(self.theme_mgr.current)
        self.configure(bg=p["bg"])
        self._build(p)

    def _build(self, p: Dict[str, str]):
        font_body = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 10, "bold")

        # Header
        hdr = tk.Frame(self, bg=p["header_bg"], pady=10, padx=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="?  Central de Ajuda", bg=p["header_bg"], fg=p["header_fg"],
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        # Search bar
        search_frame = tk.Frame(hdr, bg=p["header_bg"])
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", bg=p["header_bg"], fg=p["muted"],
                 font=("Segoe UI", 10)).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                                 bg=p["input_bg"], fg=p["fg"], insertbackground=p["fg"],
                                 relief="flat", font=font_body, width=22)
        search_entry.pack(side="left", padx=(4, 0), ipady=3)

        body = tk.Frame(self, bg=p["bg"])
        body.pack(fill="both", expand=True)

        # Left navigation pane
        nav_frame = tk.Frame(body, bg=p["frame_bg"], width=200)
        nav_frame.pack(side="left", fill="y")
        nav_frame.pack_propagate(False)

        tk.Label(nav_frame, text="Seções", bg=p["frame_bg"], fg=p["accent"],
                 font=font_bold, padx=12, pady=8).pack(anchor="w")

        self._nav_buttons: List[tk.Button] = []
        for i, (title, _) in enumerate(HELP_SECTIONS):
            btn = tk.Button(
                nav_frame, text=title, anchor="w", padx=12, pady=6,
                bg=p["frame_bg"] if i != 0 else p["select_bg"],
                fg=p["fg"] if i != 0 else p["accent"],
                activebackground=p["select_bg"], activeforeground=p["accent"],
                relief="flat", bd=0, font=font_body, cursor="hand2",
                command=lambda idx=i: self._show_section(idx),
            )
            btn.pack(fill="x")
            self._nav_buttons.append(btn)

        # Divider
        tk.Frame(body, bg=p["border"], width=1).pack(side="left", fill="y")

        # Content area
        content_frame = tk.Frame(body, bg=p["bg"])
        content_frame.pack(side="left", fill="both", expand=True)

        self._text = tk.Text(
            content_frame, wrap="word", state="disabled",
            bg=p["bg"], fg=p["fg"], font=font_body,
            relief="flat", padx=24, pady=16,
            spacing1=2, spacing3=4,
            selectbackground=p["select_bg"], selectforeground=p["select_fg"],
            cursor="arrow",
        )
        self._text.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(content_frame, orient="vertical", command=self._text.yview)
        sb.pack(side="right", fill="y")
        self._text.configure(yscrollcommand=sb.set)

        # Configure text tags
        self._text.tag_configure("h1", font=("Segoe UI", 14, "bold"),
                                  foreground=p["accent"], spacing1=4, spacing3=8)
        self._text.tag_configure("h2", font=("Segoe UI", 11, "bold"),
                                  foreground=p["accent2"], spacing1=10, spacing3=4)
        self._text.tag_configure("body", font=font_body, foreground=p["fg"])
        self._text.tag_configure("code", font=("Consolas", 9),
                                  foreground=p["success"], background=p["frame_bg"])
        self._text.tag_configure("keyword", font=font_bold, foreground=p["warning"])
        self._text.tag_configure("highlight", background=p["warning"],
                                  foreground=p["bg"])

        self._current_section = 0
        self._show_section(0)

    def _show_section(self, idx: int):
        p = self.theme_mgr.palette(self.theme_mgr.current)
        self._current_section = idx

        # Update nav button highlights
        for i, btn in enumerate(self._nav_buttons):
            if i == idx:
                btn.configure(bg=p["select_bg"], fg=p["accent"])
            else:
                btn.configure(bg=p["frame_bg"], fg=p["fg"])

        title, content = HELP_SECTIONS[idx]
        self._render(title, content)

    def _render(self, title: str, content: str, highlight: str = ""):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("end", title + "\n", "h1")
        self._text.insert("end", "─" * 60 + "\n", "body")

        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and stripped == stripped.upper() and len(stripped) > 3 and not stripped.startswith("•"):
                # ALL CAPS lines → subheading
                self._text.insert("end", "\n" + line + "\n", "h2")
            elif stripped.startswith("•"):
                self._text.insert("end", "  " + line.lstrip() + "\n", "body")
            else:
                self._text.insert("end", line + "\n", "body")

        # Highlight search term if provided
        if highlight:
            self._highlight_in_text(highlight)

        self._text.configure(state="disabled")
        self._text.see("1.0")

    def _highlight_in_text(self, term: str):
        content = self._text.get("1.0", "end").lower()
        term_lower = term.lower()
        start = 0
        while True:
            pos = content.find(term_lower, start)
            if pos == -1:
                break
            line = content[:pos].count("\n") + 1
            col = pos - content[:pos].rfind("\n") - 1
            end_col = col + len(term)
            self._text.tag_add("highlight", f"{line}.{col}", f"{line}.{end_col}")
            start = pos + 1

    def _on_search(self, *_args):
        query = self._search_var.get().strip().lower()
        if not query:
            self._show_section(self._current_section)
            return

        # Search across all sections
        results = []
        for title, content in HELP_SECTIONS:
            if query in title.lower() or query in content.lower():
                results.append((title, content))

        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        p = self.theme_mgr.palette(self.theme_mgr.current)

        if not results:
            self._text.insert("end", "Nenhum resultado encontrado para: ", "body")
            self._text.insert("end", f'"{query}"', "keyword")
        else:
            self._text.insert("end", f"Resultados para: ", "body")
            self._text.insert("end", f'"{query}"\n\n', "keyword")
            for title, content in results:
                self._text.insert("end", title + "\n", "h1")
                self._text.insert("end", "─" * 60 + "\n", "body")
                for line in content.split("\n"):
                    self._text.insert("end", line + "\n", "body")
                self._text.insert("end", "\n", "body")
            self._highlight_in_text(query)

        self._text.configure(state="disabled")
        self._text.see("1.0")


# ---------------------------------------------------------------------------
# HTML Schedule Parser
# ---------------------------------------------------------------------------

def parse_html_schedule(html_content: str) -> str:
    """Extrai tabela do cronograma em HTML e converte em Markdown (útil para LLMs e leitura)."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "Erro: A biblioteca 'beautifulsoup4' não está instalada.\nUse no terminal: pip install beautifulsoup4"

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    if not table:
        return "Erro: Nenhuma tabela (<table>) encontrada no HTML fornecido."

    rows = table.find_all("tr")
    if not rows:
        return "Erro: A tabela não possui linhas (<tr>)."

    output = []
    
    # Headers
    header_cells = rows[0].find_all(["th", "td"])
    headers = [c.get_text(" ", strip=True) for c in header_cells]
    if not headers:
        return "Erro: Tabela sem colunas reconhecíveis."
        
    output.append("| " + " | ".join(headers) + " |")
    output.append("|" + "|".join(["---"] * len(headers)) + "|")

    # Body
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        row_data = []
        for cell in cells:
            text = " ".join(cell.get_text(" ", strip=True).replace("\n", " ").replace("\r", " ").split())
            row_data.append(text)
            
        if any(row_data):
            output.append("| " + " | ".join(row_data) + " |")

    return "\n".join(output) + "\n"

class HTMLImportDialog(tk.Toplevel):
    """Diálogo para colar código HTML do cronograma e converter."""
    def __init__(self, parent: "SubjectManagerDialog"):
        super().__init__(parent)
        self.title("📥  Importar Cronograma (HTML)")
        self.geometry("640x480")
        self.transient(parent)
        self.grab_set()
        self.parent = parent
        
        ttk.Label(self, text="Cole o elemento HTML interiro da tabela de cronograma (ex: Portal/Moodle):").pack(padx=10, pady=(10, 5), anchor="w")
        self.text = tk.Text(self, font=("Consolas", 10), wrap="word")
        self.text.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(5, 0))
        btn_import = ttk.Button(btn_frame, text="Importar para Markdown", style="Accent.TButton", command=self._process)
        btn_import.pack(side="right")
        
    def _process(self):
        html_str = self.text.get("1.0", "end").strip()
        if not html_str:
            self.destroy()
            return
        
        res = parse_html_schedule(html_str)
        if res.startswith("Erro:"):
            messagebox.showerror(APP_NAME, res, parent=self)
            return
            
        current = self.parent._syllabus_text.get("1.0", "end").strip()
        if current:
            current += "\n\n"
        self.parent._syllabus_text.delete("1.0", "end")
        self.parent._syllabus_text.insert("end", current + res)
        self.destroy()


# ---------------------------------------------------------------------------
# GUI — Subject Manager Dialog
# ---------------------------------------------------------------------------

class SubjectManagerDialog(tk.Toplevel):
    """Gerenciador de matérias — criar, editar, excluir perfis."""

    def __init__(self, parent, subject_store: SubjectStore, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.title("📚  Gerenciador de Matérias")
        self.geometry("780x560")
        self.transient(parent)
        self.grab_set()
        self._store = subject_store
        self._theme_mgr = theme_mgr
        self._current_name: Optional[str] = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Left panel: subject list ─────────────────────────────────
        left = ttk.Frame(pw, width=220)
        pw.add(left, weight=0)

        ttk.Label(left, text="Matérias salvas", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self._listbox = tk.Listbox(left, width=28, font=("Segoe UI", 10))
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="➕ Nova", command=self._new).pack(side="left")
        ttk.Button(btn_frame, text="✖ Excluir", command=self._delete).pack(side="right")

        # ── Right panel: edit form ───────────────────────────────────
        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        form = ttk.LabelFrame(right, text="  Dados da Matéria", padding=12)
        form.pack(fill="both", expand=True)

        self._vars: Dict[str, tk.StringVar] = {}
        labels = [
            ("name", "Nome da matéria", "Ex: Cálculo I, Estruturas de Dados"),
            ("slug", "Slug", "Auto-gerado se vazio. Ex: calculo-i"),
            ("professor", "Professor", "Nome do professor"),
            ("institution", "Instituição", "Ex: PUCRS"),
            ("semester", "Semestre", "Ex: 2025/1"),
            ("schedule", "Horário", "Ex: Seg/Qua 10:15-11:55"),
            ("default_mode", "Modo padrão", "auto, quick, high_fidelity, manual_assisted"),
            ("default_ocr_lang", "OCR padrão", "por,eng"),
            ("repo_root", "Pasta do repositório", "Pasta base para criar repos"),
        ]

        for i, (key, label, tip) in enumerate(labels):
            lbl = ttk.Label(form, text=label)
            lbl.grid(row=i, column=0, sticky="w", pady=3)
            add_tooltip(lbl, tip)
            var = tk.StringVar()
            self._vars[key] = var
            if key == "default_mode":
                ttk.Combobox(form, textvariable=var, values=PROCESSING_MODES,
                             state="readonly", width=22).grid(row=i, column=1, sticky="ew", padx=(8, 0))
            elif key == "repo_root":
                fr = ttk.Frame(form)
                fr.grid(row=i, column=1, sticky="ew", padx=(8, 0))
                ttk.Entry(fr, textvariable=var).pack(side="left", fill="x", expand=True)
                ttk.Button(fr, text="📁", width=3,
                           command=lambda v=var: v.set(filedialog.askdirectory() or v.get())).pack(side="right", padx=(4, 0))
            else:
                ttk.Entry(form, textvariable=var, width=36).grid(row=i, column=1, sticky="ew", padx=(8, 0))

        form.columnconfigure(1, weight=1)

        # Syllabus (cronograma) — multiline
        row_syl = len(labels)
        
        lbl_syl_frame = ttk.Frame(form)
        lbl_syl_frame.grid(row=row_syl, column=0, sticky="nw", pady=3)
        lbl_syl = ttk.Label(lbl_syl_frame, text="Cronograma")
        lbl_syl.pack(anchor="w")
        btn_html = ttk.Button(lbl_syl_frame, text="📥 De HTML", width=12, command=self._import_html)
        btn_html.pack(anchor="w", pady=(8, 0))
        add_tooltip(btn_html, "Cole o HTML do cronograma (do Portal/Moodle) para converter automaticamente numa tabela Markdown limpa.")

        self._syllabus_text = tk.Text(form, height=6, width=36, font=("Segoe UI", 9), wrap="word")
        self._syllabus_text.grid(row=row_syl, column=1, sticky="nsew", padx=(8, 0), pady=3)
        form.rowconfigure(row_syl, weight=1)

        # Save button
        ttk.Button(right, text="💾  Salvar matéria", style="Accent.TButton",
                   command=self._save).pack(fill="x", pady=(10, 0))

    def _refresh_list(self):
        self._listbox.delete(0, "end")
        for name in self._store.names():
            self._listbox.insert("end", name)

    def _on_select(self, _event=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        name = self._listbox.get(sel[0])
        sp = self._store.get(name)
        if not sp:
            return
        self._current_name = name
        for key, var in self._vars.items():
            var.set(getattr(sp, key, ""))
        self._syllabus_text.delete("1.0", "end")
        self._syllabus_text.insert("1.0", sp.syllabus)

    def _new(self):
        self._current_name = None
        for var in self._vars.values():
            var.set("")
        self._vars["institution"].set("PUCRS")
        self._vars["default_mode"].set("auto")
        self._vars["default_ocr_lang"].set("por,eng")
        self._syllabus_text.delete("1.0", "end")

    def _save(self):
        name = self._vars["name"].get().strip()
        if not name:
            messagebox.showwarning("Matéria", "Preencha o nome da matéria.")
            return
        slug = self._vars["slug"].get().strip() or slugify(name)
        sp = SubjectProfile(
            name=name,
            slug=slug,
            professor=self._vars["professor"].get().strip(),
            institution=self._vars["institution"].get().strip() or "PUCRS",
            semester=self._vars["semester"].get().strip(),
            schedule=self._vars["schedule"].get().strip(),
            syllabus=self._syllabus_text.get("1.0", "end-1c").strip(),
            default_mode=self._vars["default_mode"].get(),
            default_ocr_lang=self._vars["default_ocr_lang"].get().strip() or "por,eng",
            repo_root=self._vars["repo_root"].get().strip(),
        )
        self._store.add(sp)
        self._current_name = name
        self._refresh_list()
        messagebox.showinfo(APP_NAME, f"Matéria '{sp.name}' salva com sucesso!", parent=self)
        
    def _import_html(self):
        HTMLImportDialog(self)

    def _delete(self):
        sel = self._listbox.curselection()
        if not sel:
            messagebox.showinfo("Matéria", "Selecione uma matéria para excluir.")
            return
        name = self._listbox.get(sel[0])
        if messagebox.askyesno("Matéria", f"Excluir '{name}'?"):
            self._store.delete(name)
            self._current_name = None
            self._new()
            self._refresh_list()


# ---------------------------------------------------------------------------
# GUI — Student Profile Dialog
# ---------------------------------------------------------------------------

class StudentProfileDialog(tk.Toplevel):
    """Editor do perfil do aluno."""

    def __init__(self, parent, student_store: StudentStore, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.title("👤  Perfil do Aluno")
        self.geometry("560x520")
        self.transient(parent)
        self.grab_set()
        self._store = student_store
        self._build_ui()

    def _build_ui(self):
        p = self._store.profile
        frm = ttk.LabelFrame(self, text="  Seus dados", padding=14)
        frm.pack(fill="x", padx=14, pady=(14, 8))

        self._vars: Dict[str, tk.StringVar] = {}
        entries = [
            ("full_name", "Nome completo", "Seu nome completo, como aparece no sistema acadêmico."),
            ("nickname", "Como prefere ser chamado", "Nome/apelido que o GPT deve usar ao se referir a você.\nEx: Humberto, Beto, Hu"),
            ("semester", "Semestre atual", "Em qual semestre você está.\nEx: 3º semestre, 5º período"),
            ("institution", "Instituição", "Nome da sua universidade."),
        ]
        for i, (key, label, tip) in enumerate(entries):
            lbl = ttk.Label(frm, text=label)
            lbl.grid(row=i, column=0, sticky="w", pady=4)
            add_tooltip(lbl, tip)
            var = tk.StringVar(value=getattr(p, key, ""))
            self._vars[key] = var
            ttk.Entry(frm, textvariable=var, width=40).grid(row=i, column=1, sticky="ew", padx=(8, 0))
        frm.columnconfigure(1, weight=1)

        # Personality — multiline
        pers_frame = ttk.LabelFrame(self, text="  🧠  Personalidade do Tutor", padding=14)
        pers_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        hint = ttk.Label(pers_frame, text="Como o GPT deve te ajudar? Descreva o estilo que funciona para você:",
                         style="Muted.TLabel")
        hint.pack(anchor="w", pady=(0, 6))
        add_tooltip(hint, "Este texto será exportado nos repositórios e define como o tutor GPT interage com você.\nDica: seja específico sobre estilo de explicação, nível de detalhe, e preferências.")

        self._personality_text = tk.Text(pers_frame, height=10, font=("Segoe UI", 10), wrap="word")
        self._personality_text.pack(fill="both", expand=True)
        if p.personality:
            self._personality_text.insert("1.0", p.personality)
        else:
            # Placeholder text
            placeholder = (
                "Exemplo:\n"
                "• Explique com exemplos práticos e analogias.\n"
                "• Quando eu errar, me mostre o raciocínio passo a passo.\n"
                "• Foque em preparação para provas.\n"
                "• Use português informal.\n"
                "• Quando possível, mostre como resolver de mais de uma forma."
            )
            self._personality_text.insert("1.0", placeholder)
            self._personality_text.config(fg="#888888")
            self._personality_text.bind("<FocusIn>", self._clear_placeholder)

        ttk.Button(self, text="💾  Salvar Perfil", style="Accent.TButton",
                   command=self._save).pack(fill="x", padx=14, pady=(0, 14))

    def _clear_placeholder(self, _event=None):
        if self._personality_text.get("1.0", "2.0").startswith("Exemplo:"):
            self._personality_text.delete("1.0", "end")
            self._personality_text.config(fg="")

    def _save(self):
        sp = StudentProfile(
            full_name=self._vars["full_name"].get().strip(),
            nickname=self._vars["nickname"].get().strip(),
            semester=self._vars["semester"].get().strip(),
            institution=self._vars["institution"].get().strip() or "PUCRS",
            personality=self._personality_text.get("1.0", "end-1c").strip(),
        )
        self._store.profile = sp
        messagebox.showinfo("Perfil", "Perfil salvo com sucesso!")
        self.destroy()


# ---------------------------------------------------------------------------
# GUI — Markdown Preview Window
# ---------------------------------------------------------------------------

class MarkdownPreviewWindow(tk.Toplevel):
    """Visualizador de Markdown processado — mostra conteúdo e verifica LaTeX."""

    def __init__(self, parent, repo_dir: str, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.title("📄  Visualizador de Markdown")
        self.geometry("900x650")
        self.transient(parent)
        self._repo_dir = Path(repo_dir)
        self._theme_mgr = theme_mgr
        self._build_ui()

    def _build_ui(self):
        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Left: file tree ──────────────────────────────────────────
        left = ttk.Frame(pw, width=250)
        pw.add(left, weight=0)
        ttk.Label(left, text="Arquivos Markdown", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        self._file_list = tk.Listbox(left, width=35, font=("Consolas", 9))
        self._file_list.pack(fill="both", expand=True)
        self._file_list.bind("<<ListboxSelect>>", self._load_file)

        # Populate
        self._md_files: List[Path] = []
        if self._repo_dir.exists():
            self._md_files = sorted(self._repo_dir.rglob("*.md"))
        for f in self._md_files:
            rel = f.relative_to(self._repo_dir)
            self._file_list.insert("end", str(rel))

        if not self._md_files:
            self._file_list.insert("end", "(nenhum .md encontrado)")

        # ── Right: content viewer ────────────────────────────────────
        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        # Stats bar
        self._stats_var = tk.StringVar(value="Selecione um arquivo à esquerda.")
        ttk.Label(right, textvariable=self._stats_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 6))

        self._text = tk.Text(right, wrap="word", font=("Consolas", 10), state="disabled")
        scroll = ttk.Scrollbar(right, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scroll.set)
        self._text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Tag configs for syntax
        self._text.tag_configure("heading", font=("Segoe UI", 12, "bold"), foreground="#89b4fa")
        self._text.tag_configure("latex", foreground="#f9e2af", font=("Consolas", 10, "italic"))
        self._text.tag_configure("code", background="#313244", font=("Consolas", 10))
        self._text.tag_configure("table_row", foreground="#a6e3a1")

    def _load_file(self, _event=None):
        sel = self._file_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._md_files):
            return
        fpath = self._md_files[idx]
        try:
            content = fpath.read_text("utf-8", errors="replace")
        except Exception as e:
            content = f"Erro ao ler arquivo: {e}"

        # Stats
        lines = content.split("\n")
        latex_count = content.count("$")
        latex_blocks = content.count("$$")
        img_refs = content.count("![")
        self._stats_var.set(
            f"📊  {len(lines)} linhas  |  "
            f"LaTeX inline: ~{latex_count - latex_blocks*2}  |  "
            f"LaTeX blocos: {latex_blocks}  |  "
            f"Imagens: {img_refs}"
        )

        # Display
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", content)

        # Highlight
        for i, line in enumerate(lines, 1):
            tag = f"{i}.0"
            tag_end = f"{i}.end"
            if line.startswith("#"):
                self._text.tag_add("heading", tag, tag_end)
            elif "$$" in line or line.strip().startswith("\\"):
                self._text.tag_add("latex", tag, tag_end)
            elif "$" in line:
                # Inline LaTeX — highlight dollar regions
                self._text.tag_add("latex", tag, tag_end)
            elif line.startswith("|") and "|" in line[1:]:
                self._text.tag_add("table_row", tag, tag_end)
            elif line.startswith("```"):
                self._text.tag_add("code", tag, tag_end)

        self._text.configure(state="disabled")


# ---------------------------------------------------------------------------
# GUI — FileEntryDialog & App
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

        ttk.Label(master, text=f"Arquivo: {src.name}", style="Accent.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        self.var_title = tk.StringVar(value=self.initial.title if self.initial else auto_detect_title(self.path))
        self.var_category = tk.StringVar(value=self.initial.category if self.initial else auto_detect_category(src.name, self.file_type == "image"))
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

        lbl_title = ttk.Label(master, text="Título")
        lbl_title.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_title, "Nome legível do documento. Aparece nos metadados e no índice do repositório.")
        ttk.Entry(master, textvariable=self.var_title, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        lbl_cat = ttk.Label(master, text="Categoria")
        lbl_cat.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_cat, "Classifica o arquivo na estrutura do repositório.\nexams → provas | course-material → slides/notas | exercise-lists → listas | references → livros/artigos | photos-of-exams → fotos manuscritas")
        ttk.Combobox(master, textvariable=self.var_category, values=DEFAULT_CATEGORIES, state="readonly", width=22).grid(row=row, column=1, sticky="ew")

        lbl_mode = ttk.Label(master, text="Modo")
        lbl_mode.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_mode, "Controla o pipeline de processamento.\nauto → decide pelo perfil do documento\nquick → só backend base (rápido)\nhigh_fidelity → base + avançado\nmanual_assisted → base + avançado + revisão humana guiada")
        ttk.Combobox(master, textvariable=self.var_mode, values=PROCESSING_MODES, state="readonly", width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_profile = ttk.Label(master, text="Perfil")
        lbl_profile.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_profile, "Descreve o tipo de conteúdo do PDF.\nauto → detecta automaticamente\ngeneral → texto simples\nmath_heavy → fórmulas e LaTeX\nlayout_heavy → colunas, figuras, tabelas\nscanned → PDF de scan/foto (ativa OCR)\nexam_pdf → prova/lista de exercícios")
        ttk.Combobox(master, textvariable=self.var_profile, values=DOCUMENT_PROFILES, state="readonly", width=22).grid(row=row, column=1, sticky="ew")

        lbl_backend = ttk.Label(master, text="Backend preferido")
        lbl_backend.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_backend, "Backend de extração preferido.\nauto → seleção automática\npymupdf4llm → rápido e bom para PDFs digitais\npymupdf → fallback básico\ndocling → avançado: OCR, fórmulas, tabelas (CLI externo)\nmarker → avançado: equações e imagens (CLI externo)")
        ttk.Combobox(master, textvariable=self.var_backend, values=PREFERRED_BACKENDS, state="readonly", width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_tags = ttk.Label(master, text="Tags")
        lbl_tags.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_tags, "Palavras-chave separadas por vírgula para facilitar busca futura.\nExemplo: gabarito, integração, 2024-1")
        ttk.Entry(master, textvariable=self.var_tags, width=26).grid(row=row, column=1, sticky="ew")

        lbl_ocr = ttk.Label(master, text="OCR lang")
        lbl_ocr.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_ocr, "Idioma(s) para o OCR.\npor,eng → Português + Inglês (padrão recomendado)\npor → só Português | eng → só Inglês")
        ttk.Combobox(master, textvariable=self.var_ocr_lang, values=OCR_LANGS, width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_notes = ttk.Label(master, text="Notas")
        lbl_notes.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_notes, "Observação livre sobre o arquivo. Não afeta o processamento, apenas fica registrado nos metadados.")
        ttk.Entry(master, textvariable=self.var_notes, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        lbl_prof = ttk.Label(master, text="Pista do professor")
        lbl_prof.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_prof, "Padrões observados no estilo do professor: tipo de cobrança, notação preferida, nível de detalhe.\nExemplo: cobra demonstração formal; mistura indução e recursão")
        ttk.Entry(master, textvariable=self.var_prof, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        cb_exam = ttk.Checkbutton(master, text="Relevante para prova", variable=self.var_exam)
        cb_exam.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(cb_exam, "Marca este material como importante para preparação de provas. Afeta priorização no bundle do GPT tutor.")

        cb_bundle = ttk.Checkbutton(master, text="Incluir no bundle inicial", variable=self.var_bundle)
        cb_bundle.grid(row=row, column=1, sticky="w")
        add_tooltip(cb_bundle, "Se marcado, o arquivo entra no bundle.seed.json para alimentar o GPT tutor como conhecimento base.")

        cb_formula = ttk.Checkbutton(master, text="Prioridade em fórmulas", variable=self.var_formula)
        cb_formula.grid(row=row, column=2, sticky="w")
        add_tooltip(cb_formula, "Força ativação do backend avançado (docling/marker) mesmo em modo auto ou quick.\nUse quando o documento tem muitas equações matemáticas críticas.")
        row += 1

        if self.file_type == "pdf":
            cb_keep = ttk.Checkbutton(master, text="Preservar imagens do PDF no Markdown base", variable=self.var_keep_images)
            cb_keep.grid(row=row, column=0, columnspan=2, sticky="w", pady=4)
            add_tooltip(cb_keep, "Se marcado, o pymupdf4llm extrai as imagens embutidas no PDF e as referencia no Markdown. Útil para manter figuras após a extração.")

            cb_ocr = ttk.Checkbutton(master, text="Forçar OCR", variable=self.var_force_ocr)
            cb_ocr.grid(row=row, column=2, sticky="w")
            add_tooltip(cb_ocr, "Ignora o texto digital do PDF e passa tudo pelo OCR.\nUse para PDFs com texto não selecionável, imagens de texto, ou codificação incorreta.")
            row += 1

            cb_prev = ttk.Checkbutton(master, text="Exportar previews das páginas", variable=self.var_previews)
            cb_prev.grid(row=row, column=0, sticky="w")
            add_tooltip(cb_prev, "Gera imagens PNG de cada página (resolução 1.5x) em staging/assets/page-previews/.\nConsome mais espaço, mas facilita a revisão visual do conteúdo extraído.")

            cb_imgs = ttk.Checkbutton(master, text="Extrair imagens do PDF", variable=self.var_imgs)
            cb_imgs.grid(row=row, column=1, sticky="w")
            add_tooltip(cb_imgs, "Extrai todas as imagens embutidas no PDF para staging/assets/images/.\nRequer PyMuPDF instalado.")

            cb_tbl = ttk.Checkbutton(master, text="Extrair tabelas", variable=self.var_tables)
            cb_tbl.grid(row=row, column=2, sticky="w")
            add_tooltip(cb_tbl, "Detecta e exporta tabelas como CSV e Markdown em staging/assets/tables/.\nRequer pdfplumber e/ou PyMuPDF instalados.")
            row += 1

            lbl_pr = ttk.Label(master, text="Page range")
            lbl_pr.grid(row=row, column=0, sticky="w", pady=4)
            add_tooltip(lbl_pr, 'Limita o processamento a páginas específicas. Deixe vazio para processar todas.\nFormatos aceitos: "1-5" (págs 1 a 5) | "1,3,7" (págs específicas) | "2, 5-8" (misto)\nNota: sem o zero, é interpretado como base-1 (página 1 = primeira página).')
            ttk.Entry(master, textvariable=self.var_page_range, width=18).grid(row=row, column=1, sticky="w")
            ttk.Label(master, text='Ex.: "1-4" ou "0,2,5-7"', style="Muted.TLabel").grid(row=row, column=2, columnspan=2, sticky="w")
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


class URLEntryDialog(tk.Toplevel):
    """Dialog specifically for entering a URL representing a web bibliography/document."""
    def __init__(self, parent, default_category: str = "references"):
        super().__init__(parent)
        self.title("🔗 Importar Link / Bibliografia")
        self.geometry("560x420")
        self.transient(parent)
        self.grab_set()
        
        self.result_entry: Optional[FileEntry] = None
        self.var_url = tk.StringVar()
        self.var_title = tk.StringVar()
        self.var_category = tk.StringVar(value=default_category)
        self.var_tags = tk.StringVar()
        self.var_notes = tk.StringVar()
        self.var_bundle = tk.BooleanVar(value=True)
        
        self._build_ui()
        
    def _build_ui(self):
        form = ttk.Frame(self, padding=14)
        form.pack(fill="both", expand=True)
        
        r = 0
        ttk.Label(form, text="URL do material:").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.var_url, width=40).grid(row=r, column=1, sticky="w", padx=8)
        
        r += 1
        ttk.Label(form, text="Título:").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.var_title, width=40).grid(row=r, column=1, sticky="w", padx=8)
        
        r += 1
        ttk.Label(form, text="Categoria:").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=self.var_category, values=list(CATEGORY_LABELS.keys()), state="readonly", width=38).grid(row=r, column=1, sticky="w", padx=8)
        
        r += 1
        ttk.Label(form, text="Tags (vírgulas):").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.var_tags, width=40).grid(row=r, column=1, sticky="w", padx=8)
        
        r += 1
        ttk.Label(form, text="Notas:").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.var_notes, width=40).grid(row=r, column=1, sticky="w", padx=8)
        
        r += 1
        ttk.Checkbutton(form, text="Incluir no bundle base", variable=self.var_bundle).grid(row=r, column=0, columnspan=2, sticky="w", pady=8)
        
        btn_frame = ttk.Frame(self, padding=(14, 0, 14, 14))
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Salvar Link", style="Accent.TButton", command=self._save).pack(side="right")
        
    def _save(self):
        url = self.var_url.get().strip()
        title = self.var_title.get().strip()
        if not url:
            messagebox.showwarning(APP_NAME, "O URL é obrigatório.", parent=self)
            return
        if not title:
            title = url.split("://")[-1].split("/")[0] # fallback pro domínio
            
        self.result_entry = FileEntry(
            source_path=url,
            file_type="url",
            category=self.var_category.get(),
            title=title,
            tags=self.var_tags.get().strip(),
            notes=self.var_notes.get().strip(),
            include_in_bundle=self.var_bundle.get(),
            document_profile="general",
            processing_mode="auto",
            preferred_backend="url_fetcher"
        )
        self.destroy()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_obj = AppConfig()
        self.theme_mgr = ThemeManager()
        self.subject_store = SubjectStore()
        self.student_store = StudentStore()
        self._theme_name: str = self.config_obj.get("theme")  # type: ignore[assignment]
        self.title(APP_NAME)
        self.geometry("1360x900")
        self.minsize(900, 600)
        self.entries: List[FileEntry] = []
        self._quick_import = tk.BooleanVar(value=False)

        # Apply theme before building UI
        self.theme_mgr.apply(self, self._theme_name)

        self._build_ui()
        self.bind("<F1>", lambda _: self.open_help())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.config_obj.save()
        self.destroy()

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        p = self.theme_mgr.palette(self._theme_name)

        self.var_repo_root = tk.StringVar()
        self.var_course_name = tk.StringVar()
        self.var_course_slug = tk.StringVar()
        self.var_semester = tk.StringVar()
        self.var_professor = tk.StringVar()
        self.var_institution = tk.StringVar(value="PUCRS")
        self.var_default_mode = tk.StringVar(value=self.config_obj.get("default_mode"))
        self.var_default_ocr_language = tk.StringVar(value=self.config_obj.get("default_ocr_language"))

        # ─── Header bar ────────────────────────────────────────────────
        header = tk.Frame(self, bg=p["header_bg"], pady=8, padx=16)
        header.pack(fill="x")
        tk.Label(header, text=f"🎓  {APP_NAME}", bg=p["header_bg"], fg=p["header_fg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(header, text="v3 — Gerador de repositórios para GPT tutores acadêmicos",
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9)).pack(side="left", padx=(12, 0))

        # ─── Main content area ─────────────────────────────────────────
        top = ttk.Frame(self, padding=14)
        top.pack(fill="both", expand=True)

        # ── Subject selector ────────────────────────────────────────────
        subj_frame = ttk.Frame(top)
        subj_frame.pack(fill="x", pady=(0, 8))
        lbl_subj = ttk.Label(subj_frame, text="📚 Matéria ativa:", font=("Segoe UI", 10, "bold"))
        lbl_subj.pack(side="left")
        add_tooltip(lbl_subj, "Selecione uma matéria salva para preencher automaticamente todos os campos da disciplina.\nUse 'Gerenciar' para criar, editar ou excluir perfis de matérias.")
        self._var_active_subject = tk.StringVar(value="(nenhuma)")
        self._subject_combo = ttk.Combobox(subj_frame, textvariable=self._var_active_subject,
                                            values=["(nenhuma)"] + self.subject_store.names(),
                                            state="readonly", width=30)
        self._subject_combo.pack(side="left", padx=(8, 6))
        self._subject_combo.bind("<<ComboboxSelected>>", self._on_subject_selected)
        ttk.Button(subj_frame, text="📝 Gerenciar", command=self.open_subject_manager).pack(side="left")
        ttk.Separator(subj_frame, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(subj_frame, text="👤 Aluno", command=self.open_student_profile).pack(side="left")

        # Quick import toggle
        cb_quick = ttk.Checkbutton(subj_frame, text="⚡ Importação rápida", variable=self._quick_import)
        cb_quick.pack(side="right")
        add_tooltip(cb_quick, "Quando ativo, adicionar arquivos NÃO abre o diálogo de edição.\nUsa auto-detecção de categoria e título + defaults da matéria ativa.\nÚtil para importar muitos arquivos de uma vez.")

        # ── Course data frame ───────────────────────────────────────────
        course = ttk.LabelFrame(top, text="  📋  Dados da Disciplina", padding=12)
        course.pack(fill="x", pady=(0, 10))

        # Row 0: Course name + slug
        lbl_cn = ttk.Label(course, text="Nome da disciplina")
        lbl_cn.grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_course_name, font=("Segoe UI", 10, "bold"), foreground=p["accent"]).grid(row=0, column=1, sticky="w", padx=(8, 16))

        lbl_sl = ttk.Label(course, text="Slug")
        lbl_sl.grid(row=0, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_course_slug, font=("Segoe UI", 10, "bold")).grid(row=0, column=3, sticky="w", padx=(8, 0))

        # Row 1: Semester + professor
        lbl_sem = ttk.Label(course, text="Semestre")
        lbl_sem.grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_semester, font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w", padx=(8, 16))

        lbl_prof = ttk.Label(course, text="Professor")
        lbl_prof.grid(row=1, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_professor, font=("Segoe UI", 10, "bold")).grid(row=1, column=3, sticky="w", padx=(8, 0))

        # Row 2: Institution
        lbl_inst = ttk.Label(course, text="Instituição")
        lbl_inst.grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_institution, font=("Segoe UI", 10, "bold")).grid(row=2, column=1, sticky="w", padx=(8, 16))

        # Row 3: Repo path
        lbl_repo = ttk.Label(course, text="Pasta do repositório")
        lbl_repo.grid(row=3, column=0, sticky="w", pady=4)
        add_tooltip(lbl_repo, "Pasta onde o repositório será criado.\nDentro dela, uma subpasta com o slug da disciplina será gerada automaticamente.")
        ttk.Entry(course, textvariable=self.var_repo_root).grid(row=3, column=1, columnspan=2, sticky="ew", padx=(8, 8))
        ttk.Button(course, text="📁 Escolher", width=12, command=self.pick_repo_root).grid(row=3, column=3, sticky="w")

        # Row 4: Default mode + OCR
        lbl_dm = ttk.Label(course, text="Modo padrão")
        lbl_dm.grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(course, textvariable=self.var_default_mode, font=("Segoe UI", 10, "bold")).grid(row=4, column=1, sticky="w", padx=(8, 16))

        lbl_ocr = ttk.Label(course, text="OCR padrão")
        lbl_ocr.grid(row=4, column=2, sticky="w")
        ttk.Label(course, textvariable=self.var_default_ocr_language, font=("Segoe UI", 10, "bold")).grid(row=4, column=3, sticky="w", padx=(8, 0))

        course.columnconfigure(1, weight=1)
        course.columnconfigure(3, weight=1)

        # ── Toolbar ─────────────────────────────────────────────────────
        toolbar = ttk.Frame(top)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(toolbar, text="➕ PDFs", command=self.add_pdfs).pack(side="left")
        ttk.Button(toolbar, text="🖼 Imagens/Fotos", command=self.add_images).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="🔗 Adicionar Link", command=self.add_url).pack(side="left", padx=(6, 0))
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(toolbar, text="✏ Editar", command=self.edit_selected).pack(side="left")
        ttk.Button(toolbar, text="⧉ Duplicar", command=self.duplicate_selected).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="✖ Remover", command=self.remove_selected).pack(side="left", padx=(6, 0))

        ttk.Button(toolbar, text="⚙ Configurações", command=self.open_settings).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="? Ajuda  F1", command=self.open_help).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="📄 Preview", command=self.open_preview).pack(side="right", padx=(6, 0))
        ttk.Button(toolbar, text="🚀 Criar Repositório", style="Accent.TButton",
                   command=self.build_repo).pack(side="right", padx=(0, 6))

        # ── Table Notebook ──────────────────────────────────────────────────
        self.notebook = ttk.Notebook(top)
        self.notebook.pack(fill="both", expand=True)

        tab_queue = ttk.Frame(self.notebook)
        self.notebook.add(tab_queue, text="  ⏳ Fila a Processar  ")

        columns = ("type", "category", "mode", "profile", "backend", "title", "source")
        self.tree = ttk.Treeview(tab_queue, columns=columns, show="headings", height=14)
        self.tree.heading("type", text="Tipo")
        self.tree.heading("category", text="Categoria")
        self.tree.heading("mode", text="Modo")
        self.tree.heading("profile", text="Perfil")
        self.tree.heading("backend", text="Backend")
        self.tree.heading("title", text="Título")
        self.tree.heading("source", text="Arquivo")
        self.tree.column("type", width=75, anchor="center")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("mode", width=120, anchor="center")
        self.tree.column("profile", width=120, anchor="center")
        self.tree.column("backend", width=120, anchor="center")
        self.tree.column("title", width=330)
        self.tree.column("source", width=360)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

        scroll_q = ttk.Scrollbar(tab_queue, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll_q.set)
        scroll_q.pack(side="right", fill="y")

        tab_backlog = ttk.Frame(self.notebook)
        self.notebook.add(tab_backlog, text="  📁 Backlog (Já Processados)  ")
        
        btn_refresh = ttk.Button(tab_backlog, text="🔄 Atualizar Backlog", command=self._refresh_backlog)
        btn_refresh.pack(anchor="w", pady=(8, 4), padx=8)

        columns_bk = ("category", "layer", "status", "title", "backend", "file")
        self.repo_tree = ttk.Treeview(tab_backlog, columns=columns_bk, show="headings", height=14)
        self.repo_tree.heading("category", text="Categoria")
        self.repo_tree.heading("layer", text="Camada")
        self.repo_tree.heading("status", text="Status")
        self.repo_tree.heading("title", text="Título")
        self.repo_tree.heading("backend", text="Backend")
        self.repo_tree.heading("file", text="Arquivo Original")
        self.repo_tree.column("category", width=140, anchor="center")
        self.repo_tree.column("layer", width=100, anchor="center")
        self.repo_tree.column("status", width=90, anchor="center")
        self.repo_tree.column("title", width=330)
        self.repo_tree.column("backend", width=120, anchor="center")
        self.repo_tree.column("file", width=360)
        self.repo_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))

        scroll_bk = ttk.Scrollbar(tab_backlog, orient="vertical", command=self.repo_tree.yview)
        self.repo_tree.configure(yscroll=scroll_bk.set)
        scroll_bk.pack(side="right", fill="y", pady=(0, 8))

        # ── Status bar ──────────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=p["header_bg"])
        status_bar.pack(fill="x", side="bottom")

        env_parts = []
        env_parts.append(f"PyMuPDF: {'✓' if HAS_PYMUPDF else '✗'}")
        env_parts.append(f"PyMuPDF4LLM: {'✓' if HAS_PYMUPDF4LLM else '✗'}")
        env_parts.append(f"pdfplumber: {'✓' if HAS_PDFPLUMBER else '✗'}")
        env_parts.append(f"docling: {'✓' if DOCLING_CLI else '✗'}")
        env_parts.append(f"marker: {'✓' if MARKER_CLI else '✗'}")
        env_text = "  |  ".join(env_parts)

        self._status_var = tk.StringVar(value="Pronto.")
        tk.Label(status_bar, textvariable=self._status_var,
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9),
                 anchor="w", padx=10, pady=4).pack(side="left")
        tk.Label(status_bar, text=env_text,
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9),
                 anchor="e", padx=10, pady=4).pack(side="right")

    def _set_status(self, msg: str):
        self._status_var.set(msg)
        self.update_idletasks()

    # ── Actions ──────────────────────────────────────────────────────────────

    def pick_repo_root(self):
        path = filedialog.askdirectory(title="Escolha a pasta onde o repositório será criado")
        if path:
            self.var_repo_root.set(path)

    def open_settings(self):
        SettingsDialog(self, self.config_obj, self.theme_mgr)
        # Sync default vars from config after settings close
        self.var_default_mode.set(self.config_obj.get("default_mode"))
        self.var_default_ocr_language.set(self.config_obj.get("default_ocr_language"))
        self._theme_name = self.config_obj.get("theme")

    def open_help(self):
        HelpWindow(self, self.theme_mgr)

    def open_subject_manager(self):
        SubjectManagerDialog(self, self.subject_store, self.theme_mgr)
        # Refresh combo values
        self._subject_combo["values"] = ["(nenhuma)"] + self.subject_store.names()

    def open_student_profile(self):
        StudentProfileDialog(self, self.student_store, self.theme_mgr)

    def open_preview(self):
        repo_root = self.var_repo_root.get().strip()
        slug = self.var_course_slug.get().strip() or slugify(self.var_course_name.get().strip())
        if repo_root and slug:
            repo_dir = str(Path(repo_root) / slug)
        elif repo_root:
            repo_dir = repo_root
        else:
            messagebox.showinfo(APP_NAME, "Preencha a pasta do repositório para visualizar os Markdowns.")
            return
        MarkdownPreviewWindow(self, repo_dir, self.theme_mgr)

    def _on_subject_selected(self, _event=None):
        name = self._var_active_subject.get()
        if name == "(nenhuma)":
            return
        sp = self.subject_store.get(name)
        if not sp:
            return
        self.var_course_name.set(sp.name)
        self.var_course_slug.set(sp.slug)
        self.var_professor.set(sp.professor)
        self.var_institution.set(sp.institution)
        self.var_semester.set(sp.semester)
        self.var_default_mode.set(sp.default_mode)
        self.var_default_ocr_language.set(sp.default_ocr_lang)
        if sp.repo_root:
            self.var_repo_root.set(sp.repo_root)
        self._set_status(f"Matéria carregada: {sp.name}")
        self._refresh_backlog()

    def _refresh_backlog(self):
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
            
        repo_root = self.var_repo_root.get().strip()
        slug = self.var_course_slug.get().strip()
        if not repo_root or not slug:
            return
            
        repo_dir = Path(repo_root) / slug
        manifest_path = repo_dir / "manifest.json"
        
        if not manifest_path.exists():
            return
            
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            files = data.get("files", [])
            for i, f_data in enumerate(files):
                pipeline = f_data.get("pipeline", {})
                layer = pipeline.get("layer_achieved", "unknown")
                status = pipeline.get("status", "unknown")
                backend = pipeline.get("backend_used", "unknown")
                
                self.repo_tree.insert(
                    "",
                    "end",
                    iid=f"backlog_{i}",
                    values=(
                        f_data.get("category", ""),
                        layer,
                        status,
                        f_data.get("title", ""),
                        backend,
                        Path(f_data.get("source_file", "")).name
                    )
                )
        except Exception as e:
            logging.error(f"Erro ao ler backlog: {e}")

    def _entry_dialog(self, path: str, initial: Optional[FileEntry] = None) -> Optional[FileEntry]:
        dialog = FileEntryDialog(
            self, path, initial=initial,
            default_mode=self.var_default_mode.get(),
            default_ocr_language=self.var_default_ocr_language.get(),
        )
        return dialog.result_entry

    def _quick_add_file(self, path: str, is_image: bool = False) -> FileEntry:
        """Cria FileEntry automaticamente sem abrir diálogo."""
        src = Path(path)
        file_type = "image" if is_image else ("pdf" if src.suffix.lower() == ".pdf" else "image")
        return FileEntry(
            source_path=path,
            file_type=file_type,
            category=auto_detect_category(src.name, is_image),
            title=auto_detect_title(path),
            processing_mode=self.var_default_mode.get(),
            document_profile="auto",
            preferred_backend="auto",
            ocr_language=self.var_default_ocr_language.get(),
        )

    def add_pdfs(self):
        paths = filedialog.askopenfilenames(title="Selecione PDFs", filetypes=[("PDF files", "*.pdf")])
        if self._quick_import.get():
            for path in paths:
                self.entries.append(self._quick_add_file(path))
        else:
            for path in paths:
                entry = self._entry_dialog(path)
                if entry:
                    self.entries.append(entry)
        self.refresh_tree()
        self._set_status(f"{len(self.entries)} arquivo(s) na lista.")

    def add_images(self):
        paths = filedialog.askopenfilenames(
            title="Selecione imagens/fotos",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff")],
        )
        if self._quick_import.get():
            for path in paths:
                self.entries.append(self._quick_add_file(path, is_image=True))
        else:
            for path in paths:
                entry = self._entry_dialog(path)
                if entry:
                    self.entries.append(entry)
        self.refresh_tree()
        self._set_status(f"{len(self.entries)} arquivo(s) na lista.")

    def add_url(self):
        dialog = URLEntryDialog(self)
        self.wait_window(dialog)
        if dialog.result_entry:
            self.entries.append(dialog.result_entry)
            self.refresh_tree()
            self._set_status(f"{len(self.entries)} arquivo(s) na lista.")


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
        self._set_status(f"Item duplicado: {copied.title}")

    def remove_selected(self):
        idx = self.selected_index()
        if idx is None:
            messagebox.showinfo(APP_NAME, "Selecione um item para remover.")
            return
        removed = self.entries[idx].title
        del self.entries[idx]
        self.refresh_tree()
        self._set_status(f"Removido: {removed}")

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
        self._set_status(f"Criando repositório em {repo_dir} ...")

        try:
            # Gather student & subject for export
            student_p = self.student_store.profile if self.student_store.profile.full_name else None
            active_subj_name = self._var_active_subject.get()
            active_subj = self.subject_store.get(active_subj_name) if active_subj_name != "(nenhuma)" else None

            builder = RepoBuilder(
                root_dir=repo_dir,
                course_meta=meta,
                entries=self.entries,
                options={
                    "default_processing_mode": self.var_default_mode.get(),
                    "default_ocr_language": self.var_default_ocr_language.get(),
                },
                student_profile=student_p,
                subject_profile=active_subj,
            )
            builder.build()
        except Exception:
            traceback_str = traceback.format_exc()
            self._set_status("Erro ao criar repositório.")
            messagebox.showerror(APP_NAME, f"Erro ao criar repositório:\n\n{traceback_str}")
            return

        self._set_status(f"✓ Repositório criado em: {repo_dir}")
        messagebox.showinfo(
            APP_NAME,
            f"Repositório criado com sucesso em:\n{repo_dir}\n\n"
            f"Próximo passo recomendado:\n"
            f"1. Revisar manual-review/\n"
            f"2. Escolher a melhor saída entre base e avançada\n"
            f"3. Promover conteúdo curado\n"
            f"4. Subir no GitHub"
        )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

