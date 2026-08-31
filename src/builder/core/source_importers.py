from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict

from src.builder.artifacts import repo as _repo_artifacts
from src.builder.core.code_summarization import (
    _get_or_load_code_curation,
    _resolve_block_info,
)
from src.builder.core.markdown_utils import compact_notebook_markdown
from src.models.core import FileEntry
from src.utils.helpers import (
    CODE_CATEGORIES,
    CODE_EXTENSIONS,
    LANG_MAP,
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

    curation = _get_or_load_code_curation(builder)
    entry_data = curation.get("entries", {}).get(entry.id(), {})
    entry_summary = entry_data.get("summary") or {}

    if entry_summary:
        title = entry_summary.get("inferred_title") or entry.title
        body = f"# {title}\n\n"
        body += f"> **Arquivo original:** `{entry.title}`\n"

        # Linkagem timeline
        primary_block_id = entry_summary.get("primary_block_id", "")
        if primary_block_id:
            block_info = _resolve_block_info(builder, primary_block_id)
            if block_info:
                body += f"> **Aula:** {block_info['period_label']} — {block_info['primary_topic_label']}\n"

        secondary = entry_summary.get("secondary_block_ids") or []
        if secondary:
            labels = []
            for bid in secondary:
                bi = _resolve_block_info(builder, bid)
                if bi:
                    labels.append(f"{bi['period_label']} ({bi['primary_topic_label']})")
            if labels:
                body += f"> **Também relevante para:** {'; '.join(labels)}\n"

        body += f"> **Linguagem:** {entry_summary.get('language', lang)}"
        if entry.tags:
            body += f"  |  **Unidade:** {entry.tags}"
        body += f"  |  **Papel:** {entry_summary.get('pedagogical_role', '?')}\n"

        concepts = entry_summary.get("concepts") or []
        if concepts:
            body += f"> **Conceitos:** {', '.join(concepts)}\n"

        body += f"\n**Resumo:** {entry_summary.get('summary', '')}\n\n---\n\n"
    else:
        # Fallback (header atual original)
        body = f"# {entry.title}\n\n"
        body += f"> **Linguagem:** {lang}"
        if entry.tags:
            body += f"  |  **Unidade:** {entry.tags}"
        if entry.notes:
            body += f"\n> {entry.notes}"
        body += "\n\n"

    if ext == "ipynb":
        body += body_content.rstrip() + "\n"
    else:
        body += f"```{lang}\n{body_content}\n```\n"

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


def _detect_default_branch(url: str, *, timeout: int = 30) -> str:
    """Branch default de um repo remoto via `git ls-remote --symref HEAD`.

    Contorna o bug de assumir `main`: repos com default `master`/outro
    quebravam o clone (`Remote branch main not found`). "main" como fallback
    seguro se git ausente, rede falha, ou saída inesperada.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--symref", url, "HEAD"],
            check=False, capture_output=True, text=True, timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return "main"
    if proc.returncode != 0:
        return "main"
    for line in (proc.stdout or "").splitlines():
        # "ref: refs/heads/<name>\tHEAD"
        if line.startswith("ref:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].startswith("refs/heads/"):
                return parts[1][len("refs/heads/"):]
    return "main"


def process_github_repo(builder, entry: FileEntry) -> Dict[str, object]:
    item: Dict[str, object] = {
        "extracted_files": [],
        "base_markdown": None,
        "clone_error": None,
    }
    url = entry.source_path
    # Texto da pagina do repo (README server-rendered) e a UNICA rota de texto
    # de um github-repo: o clone importa so codigo e nunca preenche
    # base_markdown, deixando o scorer de unidade/cobertura com 0 chars
    # (eth2/aws-encryption-sdk no MF). Mesmo mecanismo de file_type=url.
    url_item = builder._process_url(entry)
    for key in ("base_markdown", "base_backend", "manual_review"):
        item[key] = url_item.get(key)
    # Clone e SO para entries de CODIGO: para bibliografia/materiais o valor e
    # o texto da pagina — clonar importava o repo INTEIRO como codigo e a
    # heuristica de branch (main/master em STUDENT_BRANCHES) sobrescrevia a
    # categoria da entry para codigo-aluno (higiene 2026-08-31; eth2/aws no MF
    # ficaram com pin de branch errado DE PROPOSITO ate este fix).
    if entry.category not in CODE_CATEGORIES:
        builder.logs.append({"entry": entry.id(), "step": "github_clone", "status": "skip",
                             "reason": f"categoria '{entry.category}' nao e de codigo"})
        return item
    # tags pinam o branch explicitamente; vazio -> detecta o default do remoto.
    branch = entry.tags.strip() or _detect_default_branch(url)
    slug = entry.id()
    clone_dir = builder.root_dir / "raw" / "repos" / slug / branch
    if clone_dir.exists():
        shutil.rmtree(clone_dir)
    ensure_dir(clone_dir.parent)

    # core.longpaths=true evita "Filename too long" no checkout em Windows.
    cmd = ["git", "-c", "core.longpaths=true", "clone", "--depth", "1",
           "--branch", branch, "--single-branch", url, str(clone_dir)]
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

    # Branch default nao diz nada sobre aluno x professor — a categoria da
    # ENTRY (escolhida no import) manda; sub-entries herdam.
    category = entry.category
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
    builder.logs.append({"entry": slug, "step": "github_clone", "status": "ok", "file_count": len(processed)})
    return item
