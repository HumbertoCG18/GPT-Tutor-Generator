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
    APP_NAME, DOCLING_CLI, HAS_PDFPLUMBER, HAS_PYMUPDF,
    HAS_PYMUPDF4LLM, IMAGE_CATEGORIES, MARKER_CLI
)
from src.utils.helpers import (
    ensure_dir, file_size_mb, json_str, pages_to_marker_range,
    parse_page_range, safe_rel, slugify, write_text
)

import pymupdf
import pymupdf4llm
import pdfplumber

logger = logging.getLogger(__name__)

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

        # Carrega manifest existente
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        existing_sources = {e.get("source_path") for e in manifest.get("entries", [])}

        # Filtra apenas novos entries
        new_entries = [e for e in self.entries if e.source_path not in existing_sources]
        if not new_entries:
            logger.info("No new entries to process.")
            return

        logger.info("Processing %d new entries (skipping %d existing).",
                     len(new_entries), len(self.entries) - len(new_entries))

        # Garante que a estrutura existe
        self._create_structure()

        # Processa apenas os novos
        for entry in new_entries:
            logger.info("Processing new entry: %s (%s)", entry.title, entry.file_type)
            item_result = self._process_entry(entry)
            manifest["entries"].append(item_result)

        # Atualiza timestamp e logs
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        manifest.setdefault("logs", []).extend(self.logs)

        # Reescreve tudo que depende do manifest
        write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        self._write_source_registry(manifest)
        self._write_bundle_seed(manifest)
        self._write_build_report(manifest)
        logger.info("Incremental build completed. %d new entries added.", len(new_entries))


# ---------------------------------------------------------------------------
# Free functions (templates, prompts)
# ---------------------------------------------------------------------------

def generate_system_prompt(course_meta: dict, student_profile=None, subject_profile=None) -> str:
    """Gera as instruções completas do GPT Tutor, incluindo política de handoff."""
    course_name = course_meta.get("course_name", "Curso")
    professor = course_meta.get("professor", "")
    institution = course_meta.get("institution", "PUCRS")
    semester = course_meta.get("semester", "")
    slug = course_meta.get("course_slug", "")

    student_section = ""
    if student_profile:
        nick = student_profile.nickname or student_profile.full_name or "Aluno"
        student_section = f"""
## Sobre o Aluno
- Chame o aluno de **{nick}**.
- Semestre atual: {student_profile.semester}
- Instituição: {student_profile.institution}

### Estilo preferido
{student_profile.personality or 'Nenhuma preferência definida.'}
"""

    subject_section = ""
    if subject_profile:
        subject_section = f"""
## Detalhes da Matéria
- Horário: {subject_profile.schedule}
- Modo padrão: {subject_profile.default_mode}
"""
        if subject_profile.syllabus:
            subject_section += f"\n### Cronograma\n{subject_profile.syllabus}\n"
        if getattr(subject_profile, "teaching_plan", ""):
            subject_section += f"\n### Plano de Ensino (Ementa, Objetivos)\n{subject_profile.teaching_plan}\n"

    return f"""# Instruções do GPT Tutor — {course_name}

Você é um tutor acadêmico especializado na disciplina **{course_name}**,
ministrada pelo professor **{professor}** na **{institution}**, semestre **{semester}**.

## Seu Papel
- Ajude o aluno a entender os conceitos da disciplina.
- Use os materiais do repositório (pasta `content/`, `exercises/`, `exams/`) como fonte de verdade.
- Quando referenciar conteúdo, cite o arquivo de origem.
- Priorize materiais marcados como "relevante para prova".
- Adapte suas explicações ao estilo preferido do aluno.

## Fontes de Conhecimento
O repositório **{slug}** contém:
- `content/`: material curado de aulas
- `exercises/`: listas de exercícios
- `exams/`: provas anteriores e gabaritos
- `build/gpt-knowledge/bundle.seed.json`: índice de todo o material disponível
{student_section}{subject_section}
## Política de Continuidade — CURRENT_STATE e Handoff

### REGRA FUNDAMENTAL
Este chat é **temporário**. O repositório no GitHub é **permanente**.
Tudo que for decidido aqui deve ser salvo no repositório.

### Dois Mecanismos de Preservação

#### 1. CURRENT_STATE.md — Fonte de Verdade Operacional
É um **arquivo do repositório**. Representa o estado vivo e oficial do projeto.
Registra:
- Estado atual do projeto
- Decisões vigentes
- Próximos passos e pendências abertas
- Versão atual da arquitetura
- Arquivos e histórico de mudanças

**Quando gerar/atualizar:** quando o aluno pedir, ou quando decisões importantes
forem tomadas que precisam ser registradas. Salvar como `CURRENT_STATE.md` na
raiz do repositório e dar push no GitHub.

Modelo sugerido:
```markdown
# Estado Atual — {course_name}

## Dados da Disciplina
- Nome: {course_name}
- Professor: {professor}
- Semestre: {semester}
- Instituição: {institution}

## Decisões Vigentes
<!-- Listar decisões técnicas e arquiteturais já fechadas -->

## Arquivos Relevantes
<!-- Tabela com arquivos do repositório e status -->

## Pendências Abertas
<!-- Coisas que ainda precisam ser feitas -->

## Próximos Passos
<!-- O que fazer em seguida -->
```

#### 2. Handoff — Pacote de Transferência entre Chats
É uma **mensagem de passagem de contexto**, mais curta e situacional.
Serve para abrir um novo chat sem perder o fio da conversa atual.

**Quando gerar:**
- **Proativamente**, quando o chat começar a ficar longo e lento.
- Quando o aluno pedir.

O handoff deve conter:
- **Contexto:** o que estava sendo discutido nesta sessão
- **Decisões tomadas:** o que foi decidido e fechado
- **Arquivos criados/modificados:** lista de mudanças feitas
- **Próximos passos:** exatamente o que falta fazer
- **Prompt de continuação:** texto colável para iniciar o próximo chat

O handoff **evita** que a próxima conversa:
- Volte ao zero
- Repita decisões já fechadas
- Perca contexto importante
- Gere inconsistência

### Ao receber um CURRENT_STATE.md ou Handoff de outra sessão:
1. Leia o conteúdo fornecido.
2. **Assuma o estado descrito como verdade.**
3. **Não repita trabalho já feito.**
4. Continue de onde parou.

### O que deve estar no repositório (não só no chat):
- Arquitetura e schemas (JSON/YAML)
- Decisões técnicas
- Roadmap e pendências
- Templates e políticas do tutor
- CURRENT_STATE.md atualizado

### Fluxo Ideal
```
Chat GPT conversa e implementa
→ Salva decisões no GitHub
→ Quando decisões importantes são tomadas, atualiza CURRENT_STATE.md
→ Quando o chat crescer demais e ficar lento, gera um handoff
→ Novo chat recebe handoff + CURRENT_STATE.md
→ Continua sem perder progresso
```
"""



def root_readme(course_meta: dict) -> str:
    return f"""# {course_meta.get('course_name', 'Curso')}

Repositório gerado pelo **Academic Tutor Repo Builder V3**.

## Estrutura
- `raw/`: materiais originais
- `staging/`: extração automática
- `manual-review/`: revisão guiada
- `content/`, `exercises/`, `exams/`: conhecimento curado
- `build/gpt-knowledge/`: bundle inicial para GPT
- `CURRENT_STATE.md`: memória operacional (handoff entre chats)

## Fluxo recomendado
1. Adicionar PDFs e imagens
2. Rodar extração automática
3. Revisar `manual-review/`
4. Promover conteúdo curado para `content/`, `exercises/` e `exams/`
5. Atualizar `build/gpt-knowledge/`
6. Manter `CURRENT_STATE.md` atualizado

## Backends em camadas
- Base: PyMuPDF4LLM / PyMuPDF
- Avançado: Docling / Marker
- Revisão humana obrigatória para materiais críticos de prova
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

