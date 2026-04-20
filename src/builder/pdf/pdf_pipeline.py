from __future__ import annotations

import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from src.utils.helpers import parse_page_range, safe_rel, write_text

logger = logging.getLogger(__name__)


def log_backend_result(logs: list, entry_id: str, result) -> None:
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
    logs.append(payload)


def process_pdf(builder, entry, raw_target: Path, *, backend_context_factory, manual_pdf_review_template_fn, detect_latex_corruption_fn, hybridize_marker_markdown_with_base_fn) -> Dict[str, object]:
    item: Dict[str, object] = {
        "document_report": None,
        "pipeline_decision": None,
        "base_markdown": None,
        "advanced_markdown": None,
        "advanced_backend": None,
        "base_backend": None,
        "images_dir": None,
        "tables_dir": None,
        "table_detection_dir": None,
        "manual_review": None,
        "raw_target": safe_rel(raw_target, builder.root_dir),
    }
    t0 = time.time()

    logger.info(
        "  [1/6] Profiling PDF: %s (%d págs, %.1f MB)",
        entry.title,
        builder._quick_page_count(raw_target),
        raw_target.stat().st_size / 1048576,
    )
    report = builder._profile_pdf(raw_target, entry)
    decision = builder.selector.decide(entry, report)
    logger.info(
        "  [1/6] Profile=%s, Paginas=%d, Texto=%d chars, Imagens=%d, Scan=%s",
        decision.effective_profile,
        report.page_count,
        report.text_chars,
        report.images_count,
        report.suspected_scan,
    )

    item["document_report"] = asdict(report)
    item["pipeline_decision"] = asdict(decision)
    item["effective_profile"] = decision.effective_profile
    item["base_backend"] = decision.base_backend
    item["advanced_backend"] = decision.advanced_backend

    stall_timeout = int(builder.options.get("stall_timeout", 300))
    ctx = backend_context_factory(
        builder.root_dir,
        raw_target,
        entry,
        report,
        cancel_check=builder._check_cancel,
        stall_timeout=stall_timeout,
        marker_chunking_mode=str(builder.options.get("marker_chunking_mode", "fallback")),
        marker_use_llm=bool(builder.options.get("marker_use_llm", False)),
        marker_llm_model=str(builder.options.get("marker_llm_model", "") or ""),
        marker_torch_device=str(builder.options.get("marker_torch_device", "auto") or "auto"),
        ollama_base_url=str(builder.options.get("ollama_base_url", "") or ""),
        vision_model=str(builder.options.get("vision_model", "") or ""),
    )

    builder._check_cancel()

    if decision.effective_profile == "scanned":
        logger.info("  [2/6] Perfil scanned detectado → convertendo páginas em imagens.")
        try:
            scanned_result = builder._render_scanned_pdf_as_images(entry, raw_target)
            item.update(scanned_result)
            builder.logs.append(
                {
                    "entry": entry.id(),
                    "step": "scanned_pages",
                    "status": "ok",
                    "rendered_pages_dir": scanned_result.get("rendered_pages_dir"),
                }
            )
        except Exception as exc:
            logger.error("  [2/6] Falha ao tratar scanned como imagens: %s", exc)
            builder.logs.append(
                {
                    "entry": entry.id(),
                    "step": "scanned_pages",
                    "status": "error",
                    "error": str(exc),
                }
            )
            raise

        manual = builder.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
        write_text(manual, manual_pdf_review_template_fn(entry, item))
        item["manual_review"] = safe_rel(manual, builder.root_dir)

        logger.info("  ✓ PDF scanned concluído como páginas-imagem: %s", entry.title)
        return item

    if decision.base_backend:
        logger.info("  [2/6] Backend base: %s → iniciando...", decision.base_backend)
        t1 = time.time()
        backend = builder.selector.backends[decision.base_backend]
        result = backend.run(ctx)
        logger.info(
            "  [2/6] Backend base: %s → %s (%.1fs)",
            decision.base_backend,
            result.status,
            time.time() - t1,
        )
        log_backend_result(builder.logs, entry.id(), result)

        if result.status == "ok":
            item["base_markdown"] = result.markdown_path
            builder._apply_math_normalization(result.markdown_path)
        else:
            logger.warning("  Base backend %s failed: %s", decision.base_backend, result.error)
            item.setdefault("backend_errors", []).append({decision.base_backend: result.error})
    else:
        logger.info("  [2/6] Backend base: nenhum selecionado")

    builder._check_cancel()

    if decision.advanced_backend:
        logger.info("  [3/6] Backend avançado: %s → iniciando...", decision.advanced_backend)
        t1 = time.time()
        backend = builder.selector.backends[decision.advanced_backend]
        result = backend.run(ctx)
        logger.info(
            "  [3/6] Backend avançado: %s → %s (%.1fs)",
            decision.advanced_backend,
            result.status,
            time.time() - t1,
        )
        log_backend_result(builder.logs, entry.id(), result)

        if result.status == "ok":
            item["advanced_backend"] = result.name
            item["advanced_markdown"] = result.markdown_path
            item["advanced_asset_dir"] = result.asset_dir
            item["advanced_metadata_path"] = result.metadata_path
            builder._apply_math_normalization(result.markdown_path)
            if result.images_dir and not item.get("images_dir"):
                item["images_dir"] = result.images_dir
            if (
                result.name == "marker"
                and not ctx.marker_use_llm
                and item.get("base_markdown")
                and item.get("advanced_markdown")
                and not ctx.report.suspected_scan
            ):
                try:
                    base_path = builder.root_dir / str(item["base_markdown"])
                    advanced_path = builder.root_dir / str(item["advanced_markdown"])
                    if base_path.exists() and advanced_path.exists():
                        fused_text, fusion_stats = hybridize_marker_markdown_with_base_fn(
                            base_path.read_text(encoding="utf-8", errors="replace"),
                            advanced_path.read_text(encoding="utf-8", errors="replace"),
                        )
                        if fusion_stats["replacements"] > 0:
                            hybrid_dir = builder.root_dir / "staging" / "markdown-auto" / "marker-hybrid"
                            from src.utils.helpers import ensure_dir

                            ensure_dir(hybrid_dir)
                            hybrid_path = hybrid_dir / f"{entry.id()}.md"
                            write_text(hybrid_path, fused_text)
                            item["advanced_markdown_raw"] = item["advanced_markdown"]
                            item["advanced_markdown"] = safe_rel(hybrid_path, builder.root_dir)
                            item["advanced_hybrid"] = {
                                "source": "marker+base-text-rescue",
                                "replacements": fusion_stats["replacements"],
                                "candidate_matches": fusion_stats["candidate_matches"],
                            }
                            logger.info(
                                "  [3/6] Marker híbrido aplicado: %d linhas recuperadas do markdown base.",
                                fusion_stats["replacements"],
                            )
                except Exception as exc:
                    logger.warning("  [3/6] Falha ao aplicar híbrido Marker+base: %s", exc)
        else:
            logger.warning("  Advanced backend %s failed: %s", decision.advanced_backend, result.error)
            item.setdefault("backend_errors", []).append({decision.advanced_backend: result.error})
    else:
        logger.info("  [3/6] Backend avançado: nenhum selecionado")

    builder._check_cancel()

    if builder.HAS_PYMUPDF and entry.extract_images:
        logger.info("  [4/6] Extraindo imagens...")
        try:
            images_dir = builder.root_dir / "staging" / "assets" / "images" / entry.id()
            image_policy = builder._pdf_image_extraction_policy(ctx)
            count = builder._extract_pdf_images(raw_target, images_dir, pages=parse_page_range(entry.page_range), ctx=ctx)
            item["images_dir"] = safe_rel(images_dir, builder.root_dir)
            item["image_extraction"] = {
                "source": "pymupdf-pdf-images",
                "mode": image_policy["mode"],
                "count": count,
            }
            logger.info("  [4/6] %d imagens extraídas", count)
            builder.logs.append({"entry": entry.id(), "step": "extract_images", "status": "ok", "count": count})
        except Exception as exc:
            logger.error("  [4/6] Falha na extração de imagens: %s", exc)
            builder.logs.append(
                {"entry": entry.id(), "step": "extract_images", "status": "error", "error": str(exc)}
            )
    else:
        logger.info("  [4/6] Extração de imagens: pulado")

    builder._check_cancel()

    if entry.extract_tables:
        logger.info("  [6/6] Extraindo tabelas...")

        if builder.HAS_PDFPLUMBER:
            try:
                tables_dir = builder.root_dir / "staging" / "assets" / "tables" / entry.id()
                count = builder._extract_tables_pdfplumber(raw_target, tables_dir, pages=parse_page_range(entry.page_range))
                item["tables_dir"] = safe_rel(tables_dir, builder.root_dir)
                logger.info("  [6/6] pdfplumber: %d tabelas extraídas", count)
                builder.logs.append(
                    {
                        "entry": entry.id(),
                        "step": "extract_tables_pdfplumber",
                        "status": "ok",
                        "count": count,
                    }
                )
            except Exception as exc:
                logger.error("  [6/6] pdfplumber falhou: %s", exc)
                builder.logs.append(
                    {
                        "entry": entry.id(),
                        "step": "extract_tables_pdfplumber",
                        "status": "error",
                        "error": str(exc),
                    }
                )

        if builder.HAS_PYMUPDF:
            try:
                det_dir = builder.root_dir / "staging" / "assets" / "table-detections" / entry.id()
                count = builder._detect_tables_pymupdf(raw_target, det_dir, pages=parse_page_range(entry.page_range))
                item["table_detection_dir"] = safe_rel(det_dir, builder.root_dir)
                logger.info("  [6/6] pymupdf: %d detecções de tabela", count)
                builder.logs.append(
                    {
                        "entry": entry.id(),
                        "step": "detect_tables_pymupdf",
                        "status": "ok",
                        "count": count,
                    }
                )
            except Exception as exc:
                logger.error("  [6/6] pymupdf table detection falhou: %s", exc)
                builder.logs.append(
                    {
                        "entry": entry.id(),
                        "step": "detect_tables_pymupdf",
                        "status": "error",
                        "error": str(exc),
                    }
                )
    else:
        logger.info("  [6/6] Tabelas: pulado")

    active_markdown_rel = str(item.get("advanced_markdown") or item.get("base_markdown") or "").strip()
    latex_check = {"corrupted": False, "score": 0, "signals": []}
    if active_markdown_rel:
        try:
            active_markdown_path = builder.root_dir / active_markdown_rel
            if active_markdown_path.exists():
                latex_check = detect_latex_corruption_fn(
                    active_markdown_path.read_text(encoding="utf-8", errors="replace")
                )
        except Exception as exc:
            logger.warning("  [latex-check] Falha ao analisar %s: %s", active_markdown_rel, exc)

    item["latex_corruption"] = {
        "detected": bool(latex_check.get("corrupted")),
        "score": int(latex_check.get("score", 0) or 0),
        "signals": list(latex_check.get("signals") or []),
        "markdown_path": active_markdown_rel or None,
    }
    if item["latex_corruption"]["detected"]:
        logger.warning(
            "  [latex-check] LaTeX possivelmente corrompido em %s (score: %s/100).",
            entry.title,
            item["latex_corruption"]["score"],
        )
        builder.logs.append(
            {
                "entry": entry.id(),
                "step": "latex_check",
                "status": "warning",
                "message": (
                    f"LaTeX possivelmente corrompido "
                    f"(score: {item['latex_corruption']['score']}/100) — "
                    f"sinais: {'; '.join(item['latex_corruption']['signals'])}"
                ),
            }
        )

    logger.info("  ✓ PDF concluído em %.1fs: %s", time.time() - t0, entry.title)

    manual = builder.root_dir / "manual-review" / "pdfs" / f"{entry.id()}.md"
    write_text(manual, manual_pdf_review_template_fn(entry, item))
    item["manual_review"] = safe_rel(manual, builder.root_dir)
    return item
