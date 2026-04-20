from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Dict

from src.utils.helpers import ensure_dir, safe_rel, write_text

logger = logging.getLogger(__name__)


def remove_entry_consolidated_images(root_dir: Path, entry_id: str) -> int:
    """Remove consolidated content/images assets that belong to one entry."""
    if not entry_id:
        return 0

    removed_count = 0
    images_dir = root_dir / "content" / "images"
    if not images_dir.exists():
        return 0

    entry_prefix = entry_id.lower()
    for img_path in images_dir.iterdir():
        if not img_path.is_file():
            continue
        lower_name = img_path.name.lower()
        if not (
            lower_name == entry_prefix
            or lower_name.startswith(entry_prefix + "-")
            or lower_name.startswith(entry_prefix + "_")
        ):
            continue
        try:
            img_path.unlink()
            removed_count += 1
        except Exception as e:
            logger.warning("Could not remove consolidated image %s: %s", img_path, e)

    scanned_dir = images_dir / "scanned" / entry_id
    if scanned_dir.exists():
        try:
            shutil.rmtree(scanned_dir)
            removed_count += 1
        except Exception as e:
            logger.warning("Could not remove scanned image dir %s: %s", scanned_dir, e)

    return removed_count


def process_url(
    builder,
    entry,
    *,
    html_to_structured_markdown_fn,
    manual_url_review_template_fn,
) -> Dict[str, object]:
    item: Dict[str, object] = {
        "document_report": None,
        "pipeline_decision": None,
        "base_markdown": None,
        "advanced_markdown": None,
        "advanced_backend": None,
        "base_backend": "url_fetcher",
        "manual_review": None,
    }
    url_dest = builder.root_dir / "staging" / "markdown-auto" / "url_fetcher"
    ensure_dir(url_dest)
    md_file = url_dest / f"{entry.id()}.md"
    url = entry.source_path
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            charset = response.info().get_content_charset("utf-8")
            html = response.read().decode(charset, errors="replace")
        try:
            markdown_content = html_to_structured_markdown_fn(html, url, entry.title)
        except ImportError:
            markdown_content = (
                f"# {entry.title}\n\n"
                f"- URL: [{url}]({url})\n\n"
                "> BeautifulSoup nao instalado. Conteudo HTML nao foi convertido para Markdown estruturado.\n"
            )
        builder.logs.append({"entry": entry.id(), "step": "url_fetch", "status": "ok"})
    except Exception as e:
        logger.warning("Failed to fetch content from URL %s: %s", url, e)
        markdown_content = (
            f"# {entry.title}\n\n"
            f"- URL: [{url}]({url})\n\n"
            f"> Nao foi possivel carregar o conteudo: {e}\n"
        )
        builder.logs.append(
            {
                "entry": entry.id(),
                "step": "url_fetch",
                "status": "error",
                "error": str(e),
            }
        )
    write_text(md_file, markdown_content)
    item["base_markdown"] = safe_rel(md_file, builder.root_dir)
    manual = builder.root_dir / "manual-review" / "web" / f"{entry.id()}.md"
    write_text(manual, manual_url_review_template_fn(entry, item))
    item["manual_review"] = safe_rel(manual, builder.root_dir)
    return item
