from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from src.builder.artifacts import repo as _repo_artifacts
from src.builder.markdown_utils import compact_notebook_markdown
from src.models.core import FileEntry
from src.utils.helpers import (
    CODE_EXTENSIONS,
    LANG_MAP,
    STUDENT_BRANCHES,
    ensure_dir,
    json_str,
    safe_rel,
    write_text,
)

logger = logging.getLogger(__name__)


def process_image(builder, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
    item: Dict[str, object] = {"manual_review": None}
    manual = builder.root_dir / "manual-review" / "images" / f"{entry.id()}.md"
    write_text(
        manual,
        _repo_artifacts.manual_image_review_template(
            entry,
            raw_target,
            builder.root_dir,
            safe_rel_fn=safe_rel,
        ),
    )
    item["manual_review"] = safe_rel(manual, builder.root_dir)
    builder.logs.append({"entry": entry.id(), "step": "image_import", "status": "ok"})
    return item


def process_code(builder, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
    item: Dict[str, object] = {"manual_review": None, "base_markdown": None}
    ext = raw_target.suffix.lower().lstrip(".")
    lang = LANG_MAP.get(ext, ext)
    try:
        code_content = raw_target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logger.error("Could not read code file %s: %s", raw_target, exc)
        code_content = f"[Erro ao ler arquivo: {exc}]"

    body_content = code_content
    if ext == "ipynb":
        lang, body_content = compact_notebook_markdown(code_content)

    curated_subdir = "student" if entry.category == "codigo-aluno" else "professor"
    curated_dir = builder.root_dir / "code" / curated_subdir
    ensure_dir(curated_dir)
    curated_path = curated_dir / f"{entry.id()}.md"

    body = f"# {entry.title}\n\n"
    body += f"> **Linguagem:** {lang}"
    if entry.tags:
        body += f"  |  **Unidade:** {entry.tags}"
    if entry.notes:
        body += f"\n> {entry.notes}"
    if ext == "ipynb":
        body += "\n\n" + body_content.rstrip() + "\n"
    else:
        body += f"\n\n```{lang}\n{body_content}\n```\n"

    write_text(
        curated_path,
        _repo_artifacts.wrap_frontmatter(
            {
                "entry_id": entry.id(),
                "title": entry.title,
                "language": lang,
                "category": entry.category,
                "unit": entry.tags,
                "source": safe_rel(raw_target, builder.root_dir),
            },
            body,
            json_str_fn=json_str,
        ),
    )

    item["base_markdown"] = safe_rel(curated_path, builder.root_dir)
    item["language"] = lang

    manual = builder.root_dir / "manual-review" / "code" / f"{entry.id()}.md"
    write_text(
        manual,
        f"""---
id: {entry.id()}
title: {json_str(entry.title)}
type: manual_code_review
category: {entry.category}
language: {lang}
unit: {entry.tags}
---

# Revisão — {entry.title}

## Checklist
- [ ] Código compila/executa sem erros
- [ ] Anotar padrões de estilo do professor
- [ ] Identificar conceitos demonstrados

## Destino
`{safe_rel(curated_path, builder.root_dir)}`
""",
    )
    item["manual_review"] = safe_rel(manual, builder.root_dir)
    builder.logs.append(
        {"entry": entry.id(), "step": "code_import", "status": "ok", "language": lang}
    )
    return item


def _should_skip_code_import_path(base_dir: Path, code_path: Path) -> bool:
    if not code_path.is_file():
        return True
    parts = code_path.relative_to(base_dir).parts
    if any(
        part.startswith(".") or part in {"__pycache__", "node_modules", "dist", "build", ".git"}
        for part in parts
    ):
        return True
    if code_path.suffix.lower() not in CODE_EXTENSIONS:
        return True
    if code_path.stat().st_size > 500_000:
        return True
    return False


def process_zip(builder, entry: FileEntry, raw_target: Path) -> Dict[str, object]:
    import zipfile

    item: Dict[str, object] = {
        "extracted_files": [],
        "base_markdown": None,
        "extraction_error": None,
    }
    extract_dir = builder.root_dir / "staging" / "zip-extract" / entry.id()
    ensure_dir(extract_dir)
    try:
        with zipfile.ZipFile(raw_target, "r") as zf:
            zf.extractall(extract_dir)
    except Exception as exc:
        item["extraction_error"] = str(exc)
        builder.logs.append(
            {"entry": entry.id(), "step": "zip_extract", "status": "error", "error": str(exc)}
        )
        return item

    processed = []
    for code_path in sorted(extract_dir.rglob("*")):
        if _should_skip_code_import_path(extract_dir, code_path):
            continue

        relative_name = str(code_path.relative_to(extract_dir))
        sub_entry = FileEntry(
            source_path=str(code_path),
            file_type="code",
            category=entry.category,
            title=relative_name,
            tags=entry.tags,
            notes=f"Extraído de: {entry.title}",
            professor_signal=entry.professor_signal,
            include_in_bundle=entry.include_in_bundle,
        )
        code_subdir = "student" if entry.category == "codigo-aluno" else "professor"
        safe_name_c = f"{sub_entry.id()}{code_path.suffix.lower()}"
        raw_target_c = builder.root_dir / "raw" / "code" / code_subdir / safe_name_c
        ensure_dir(raw_target_c.parent)
        shutil.copy2(code_path, raw_target_c)

        sub_result = process_code(builder, sub_entry, raw_target_c)
        sub_result["title"] = relative_name
        processed.append(sub_result)

    item["extracted_files"] = processed
    item["file_count"] = len(processed)
    builder.logs.append(
        {"entry": entry.id(), "step": "zip_extract", "status": "ok", "file_count": len(processed)}
    )
    return item


def process_github_repo(builder, entry: FileEntry) -> Dict[str, object]:
    item: Dict[str, object] = {
        "extracted_files": [],
        "base_markdown": None,
        "clone_error": None,
    }
    url = entry.source_path
    branch = entry.tags.strip() or "main"
    slug = entry.id()
    clone_dir = builder.root_dir / "raw" / "repos" / slug / branch
    if clone_dir.exists():
        shutil.rmtree(clone_dir)
    ensure_dir(clone_dir.parent)

    cmd = ["git", "clone", "--depth", "1", "--branch", branch, "--single-branch", url, str(clone_dir)]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        err = "git não encontrado no PATH."
        item["clone_error"] = err
        builder.logs.append({"entry": slug, "step": "github_clone", "status": "error", "error": err})
        return item

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "git clone falhou")[-2000:]
        item["clone_error"] = err
        builder.logs.append({"entry": slug, "step": "github_clone", "status": "error", "error": err})
        return item

    category = "codigo-aluno" if branch.lower() in STUDENT_BRANCHES else "codigo-professor"
    processed = []
    for code_path in sorted(clone_dir.rglob("*")):
        if _should_skip_code_import_path(clone_dir, code_path):
            continue

        relative_name = str(code_path.relative_to(clone_dir))
        sub_entry = FileEntry(
            source_path=str(code_path),
            file_type="code",
            category=category,
            title=relative_name,
            tags=entry.tags,
            notes=f"Branch: {branch} — {url}",
            professor_signal=entry.professor_signal,
            include_in_bundle=entry.include_in_bundle,
        )
        code_subdir = "student" if category == "codigo-aluno" else "professor"
        safe_name_c = f"{sub_entry.id()}{code_path.suffix.lower()}"
        raw_target_c = builder.root_dir / "raw" / "code" / code_subdir / safe_name_c
        ensure_dir(raw_target_c.parent)
        shutil.copy2(code_path, raw_target_c)

        sub_result = process_code(builder, sub_entry, raw_target_c)
        sub_result["title"] = relative_name
        sub_result["branch"] = branch
        processed.append(sub_result)

    item["extracted_files"] = processed
    item["file_count"] = len(processed)
    item["category"] = category
    builder.logs.append({"entry": slug, "step": "github_clone", "status": "ok", "file_count": len(processed)})
    return item
