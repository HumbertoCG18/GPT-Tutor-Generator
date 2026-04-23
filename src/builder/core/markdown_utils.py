from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def strip_frontmatter_block(text: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n?", "", text or "", flags=re.DOTALL)


def rewrite_markdown_asset_paths(markdown: str, source_dir: Path, target_dir: Path) -> str:
    """Rewrite relative markdown asset links from one directory base to another."""
    pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def _replace(match):
        alt = match.group(1)
        raw_path = match.group(2)
        if re.match(r"^[a-z]+://", raw_path, re.IGNORECASE):
            return match.group(0)
        if raw_path.startswith("/"):
            return match.group(0)
        source_path = (source_dir / raw_path).resolve()
        try:
            rel = os.path.relpath(source_path, target_dir)
        except Exception:
            rel = raw_path
        return f"![{alt}]({str(rel).replace(os.sep, '/')})"

    return pattern.sub(_replace, markdown)


def strip_markdown_image_refs(markdown: str) -> str:
    if not markdown:
        return markdown
    stripped = re.sub(r"(?m)^[ \t]*!\[[^\]]*\]\([^)]+\)[ \t]*\n?", "", markdown)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    normalized = stripped.strip()
    return normalized + ("\n" if normalized else "")


def merge_numeric_dicts(items: List[Dict[str, object]]) -> Dict[str, object]:
    merged: Dict[str, object] = {}
    for item in items:
        for key, value in (item or {}).items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                merged[key] = float(merged.get(key, 0) or 0) + value
    return merged


def compact_notebook_markdown(
    raw_text: str,
    max_cells: int = 24,
    max_output_chars: int = 6000,
) -> Tuple[str, str]:
    try:
        notebook = json.loads(raw_text)
    except Exception:
        return "json", raw_text

    cells = notebook.get("cells") or []
    rendered: List[str] = []
    output_budget = 0

    for idx, cell in enumerate(cells[:max_cells], start=1):
        cell_type = (cell.get("cell_type") or "").strip().lower()
        source = "".join(cell.get("source") or []).strip()
        if not source and cell_type != "code":
            continue

        if cell_type == "markdown":
            rendered.append(f"## Célula {idx} — Markdown\n\n{source}")
            continue

        if cell_type == "code":
            rendered.append(f"## Célula {idx} — Código\n\n```python\n{source}\n```")
            outputs = cell.get("outputs") or []
            output_lines: List[str] = []
            for output in outputs[:3]:
                text = "".join(output.get("text") or output.get("data", {}).get("text/plain", []) or []).strip()
                if not text:
                    continue
                remaining = max_output_chars - output_budget
                if remaining <= 0:
                    break
                text = text[:remaining].rstrip()
                output_budget += len(text)
                output_lines.append(text)
            if output_lines:
                rendered.append("**Saída:**\n\n```text\n" + "\n\n".join(output_lines) + "\n```")

    if len(cells) > max_cells:
        rendered.append(f"> Notebook truncado: exibindo {max_cells} de {len(cells)} células.")

    return "jupyter", "\n\n".join(block for block in rendered if block).strip() or raw_text


def generated_repo_gitignore_text() -> str:
    return "\n".join([
        "# === Não essencial para o Tutor ===",
        "# Cache de build (assets, markdowns intermediários)",
        "staging/",
        "# Fontes originais (tutor lê os markdowns convertidos)",
        "raw/",
        "# Artefatos de build",
        "build/",
        "# Backups de consolidação e migração",
        "build/consolidation-backup/",
        "build/migration-v1-backup/",
        "# Workspace de revisão manual",
        "manual-review/",
        "# Scripts utilitários locais",
        "scripts/",
        "# Índices internos derivados do app (regeneráveis)",
        "course/.content_taxonomy.json",
        "course/.timeline_index.json",
        "course/.assessment_context.json",
        "course/.tag_catalog.json",
        "course/.semantic_profile.generated.json",
        "# Assets de imagem usados localmente pelo app (o tutor consome as descrições injetadas)",
        "content/images/",
        "# Exportações operacionais de prompt (copiadas para a plataforma, não lidas pelo tutor)",
        "setup/",
        "",
        "# === Sistema ===",
        "__pycache__/",
        "*.pyc",
        ".DS_Store",
        "# Exportação local para DeepTutor (não commitada)",
        ".deeptutor/",
    ])
