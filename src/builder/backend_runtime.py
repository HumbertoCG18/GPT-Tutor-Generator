from __future__ import annotations

import importlib
import logging
import os
import subprocess
import sys
import threading as _th
import time as _time
from pathlib import Path
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)

_DOCLING_PYTHON_API_CACHE = None
_MARKER_CAPABILITIES_CACHE = None
MARKER_OLLAMA_SERVICE = "marker.services.ollama.OllamaService"


def build_page_chunks(pages: Optional[List[int]], page_count: int, chunk_size: int = 20) -> List[List[int]]:
    selected = sorted(pages if pages is not None else list(range(page_count)))
    if not selected:
        return []
    return [selected[i:i + chunk_size] for i in range(0, len(selected), chunk_size)]


def build_marker_page_chunks(pages: Optional[List[int]], page_count: int, chunk_size: int = 20) -> List[List[int]]:
    return build_page_chunks(pages, page_count, chunk_size=chunk_size)


def selected_page_count(ctx: "BackendContext") -> int:
    if ctx.pages is not None:
        return len(ctx.pages)
    return max(int(ctx.report.page_count or 0), 0)


def prepare_docling_python_source_pdf(
    ctx: "BackendContext",
    out_dir: Path,
    *,
    has_pymupdf: bool,
    pymupdf_module,
) -> tuple[Path, bool]:
    if not ctx.pages:
        return ctx.raw_target, False
    if not has_pymupdf:
        logger.warning(
            "  [docling_python] page_range solicitado, mas PyMuPDF nao esta disponivel; usando o PDF inteiro."
        )
        return ctx.raw_target, False

    sliced_pdf = out_dir / f"{ctx.entry_id}--selected-pages.pdf"
    src_doc = pymupdf_module.open(str(ctx.raw_target))
    dst_doc = pymupdf_module.open()
    try:
        valid_pages = [page for page in ctx.pages if 0 <= page < src_doc.page_count]
        if not valid_pages:
            logger.warning(
                "  [docling_python] page_range=%s nao gerou paginas validas; usando o PDF inteiro.",
                ctx.entry.page_range or "all",
            )
            return ctx.raw_target, False
        for page in valid_pages:
            dst_doc.insert_pdf(src_doc, from_page=page, to_page=page)
        dst_doc.save(str(sliced_pdf))
    finally:
        dst_doc.close()
        src_doc.close()

    return sliced_pdf, True


def configure_docling_python_standard_gpu(api: dict, pipeline_options) -> dict:
    accelerator_options_cls = api.get("AcceleratorOptions")
    accelerator_device = api.get("AcceleratorDevice")
    rapid_ocr_options_cls = api.get("RapidOcrOptions")
    settings_obj = api.get("settings")

    gpu_config = {
        "enabled": False,
        "device": "auto",
        "ocr_batch_size": None,
        "layout_batch_size": None,
        "table_batch_size": None,
        "page_batch_size": None,
        "ocr_backend": None,
        "previous_page_batch_size": None,
    }

    if accelerator_options_cls and accelerator_device and hasattr(pipeline_options, "accelerator_options"):
        pipeline_options.accelerator_options = accelerator_options_cls(device=accelerator_device.CUDA)
        gpu_config["enabled"] = True
        gpu_config["device"] = str(accelerator_device.CUDA.value)

    if hasattr(pipeline_options, "ocr_batch_size"):
        pipeline_options.ocr_batch_size = 8
        gpu_config["ocr_batch_size"] = 8
    if hasattr(pipeline_options, "layout_batch_size"):
        pipeline_options.layout_batch_size = 8
        gpu_config["layout_batch_size"] = 8
    if hasattr(pipeline_options, "table_batch_size"):
        pipeline_options.table_batch_size = 4
        gpu_config["table_batch_size"] = 4

    if rapid_ocr_options_cls and hasattr(pipeline_options, "ocr_options"):
        pipeline_options.ocr_options = rapid_ocr_options_cls(backend="torch")
        gpu_config["ocr_backend"] = "torch"

    if settings_obj is not None and hasattr(settings_obj, "perf") and hasattr(settings_obj.perf, "page_batch_size"):
        gpu_config["previous_page_batch_size"] = int(settings_obj.perf.page_batch_size)
        settings_obj.perf.page_batch_size = max(int(settings_obj.perf.page_batch_size), 8)
        gpu_config["page_batch_size"] = int(settings_obj.perf.page_batch_size)

    return gpu_config


def marker_chunk_size_for_workload(
    ctx: "BackendContext",
    *,
    effective_document_profile_fn,
    selected_page_count_fn=selected_page_count,
) -> int:
    effective_profile = effective_document_profile_fn(ctx.entry.document_profile, ctx.report.suggested_profile)
    selected_pages = selected_page_count_fn(ctx)
    if effective_profile in {"math_heavy", "diagram_heavy"} and selected_pages >= 80:
        return 10
    return 20


def datalab_chunk_size_for_workload(
    ctx: "BackendContext",
    *,
    effective_document_profile_fn,
    selected_page_count_fn=selected_page_count,
) -> int:
    effective_profile = effective_document_profile_fn(ctx.entry.document_profile, ctx.report.suggested_profile)
    selected_pages = selected_page_count_fn(ctx)
    if effective_profile == "math_heavy":
        return 15 if selected_pages >= 120 else 20
    if effective_profile in {"diagram_heavy", "scanned"}:
        return 20
    return 25


def datalab_should_chunk(
    ctx: "BackendContext",
    *,
    datalab_chunk_size_for_workload_fn,
    selected_page_count_fn=selected_page_count,
) -> bool:
    selected_pages = selected_page_count_fn(ctx)
    if selected_pages < 50:
        return False
    return selected_pages > datalab_chunk_size_for_workload_fn(ctx)


def should_force_ocr_for_marker(ctx: "BackendContext") -> bool:
    return bool(ctx.entry.force_ocr) or bool(ctx.report.suspected_scan)


def marker_should_use_llm(ctx: "BackendContext") -> bool:
    return bool(getattr(ctx, "marker_use_llm", False))


def marker_ollama_model(ctx: "BackendContext") -> str:
    return str(getattr(ctx, "marker_llm_model", "") or "").strip()


def marker_torch_device(ctx: "BackendContext") -> str:
    return str(getattr(ctx, "marker_torch_device", "") or "").strip().lower()


def marker_effective_torch_device(ctx: "BackendContext") -> str:
    configured = marker_torch_device(ctx)
    if configured and configured != "auto":
        return configured
    return "mps" if sys.platform == "darwin" else "cuda"


def marker_model_slug(model: str) -> str:
    return str(model or "").strip().lower()


def marker_model_is_qwen3_vl_8b(model: str) -> bool:
    slug = marker_model_slug(model)
    return slug.startswith("qwen3-vl:8b") or slug == "qwen3-vl:8b"


def marker_model_is_cloud_variant(model: str) -> bool:
    return "cloud" in marker_model_slug(model)


def marker_model_is_probably_vision(model: str) -> bool:
    slug = marker_model_slug(model)
    return any(token in slug for token in ("-vl", "vision", "gemma3", "gemma4"))


def marker_should_redo_inline_math(ctx: "BackendContext") -> bool:
    suggested_profile = str(getattr(ctx.report, "suggested_profile", "") or "").strip().lower()
    return bool(getattr(ctx.entry, "formula_priority", False)) or suggested_profile == "math_heavy"


def marker_progress_hints(line: str, previous_phase: Optional[str]) -> tuple[Optional[str], list[str]]:
    phase = None
    hints: list[str] = []

    if ":" in line:
        phase = line.split(":", 1)[0].strip() or None
    if not phase:
        return previous_phase, hints

    if previous_phase != phase:
        hints.append(f"Fase detectada: {phase}")

    if "0it [00:00" in line.lower():
        hints.append(f"Fase '{phase}' concluída sem itens para processar.")

    return phase, hints


def load_docling_python_api():
    global _DOCLING_PYTHON_API_CACHE

    if _DOCLING_PYTHON_API_CACHE is not None:
        return _DOCLING_PYTHON_API_CACHE

    try:
        document_converter = importlib.import_module("docling.document_converter")
        pipeline_options = importlib.import_module("docling.datamodel.pipeline_options")
        base_models = importlib.import_module("docling.datamodel.base_models")
        accelerator_options = importlib.import_module("docling.datamodel.accelerator_options")
        settings_module = importlib.import_module("docling.datamodel.settings")
        _DOCLING_PYTHON_API_CACHE = {
            "DocumentConverter": document_converter.DocumentConverter,
            "PdfFormatOption": document_converter.PdfFormatOption,
            "PdfPipelineOptions": pipeline_options.PdfPipelineOptions,
            "ThreadedPdfPipelineOptions": getattr(pipeline_options, "ThreadedPdfPipelineOptions", pipeline_options.PdfPipelineOptions),
            "RapidOcrOptions": getattr(pipeline_options, "RapidOcrOptions", None),
            "AcceleratorOptions": accelerator_options.AcceleratorOptions,
            "AcceleratorDevice": accelerator_options.AcceleratorDevice,
            "settings": settings_module.settings,
            "InputFormat": base_models.InputFormat,
        }
    except Exception:
        _DOCLING_PYTHON_API_CACHE = None

    return _DOCLING_PYTHON_API_CACHE


def default_marker_capabilities() -> Dict[str, object]:
    return {
        "page_range_flag": "--page_range",
        "force_ocr_flag": "--force_ocr",
        "use_llm_flag": "--use_llm",
        "llm_service_flag": "--llm_service",
        "ollama_base_url_flag": "--OllamaService_ollama_base_url",
        "ollama_model_flag": "--OllamaService_ollama_model",
        "ollama_timeout_flag": "--OllamaService_timeout",
        "redo_inline_math_flag": "--redo_inline_math",
        "disable_image_extraction_flag": "--disable_image_extraction",
    }


def apply_marker_capabilities_help_text(help_text: str, caps: Dict[str, object]) -> Dict[str, object]:
    help_text = str(help_text or "").lower()

    if "--page-range" in help_text:
        caps["page_range_flag"] = "--page-range"
    elif "--page_range" in help_text:
        caps["page_range_flag"] = "--page_range"
    else:
        caps["page_range_flag"] = None

    if "--force-ocr" in help_text:
        caps["force_ocr_flag"] = "--force-ocr"
    elif "--force_ocr" in help_text:
        caps["force_ocr_flag"] = "--force_ocr"
    else:
        caps["force_ocr_flag"] = None

    for candidate in ("--use-llm", "--use_llm"):
        if candidate in help_text:
            caps["use_llm_flag"] = candidate
            break

    for candidate in ("--llm-service", "--llm_service"):
        if candidate in help_text:
            caps["llm_service_flag"] = candidate
            break

    for candidate in (
        "--OllamaService_ollama_base_url",
        "--ollama-base-url",
        "--ollama_base_url",
        "--ollamaservice-ollama-base-url",
    ):
        if candidate.lower() in help_text:
            caps["ollama_base_url_flag"] = candidate
            break

    for candidate in (
        "--OllamaService_ollama_model",
        "--ollama-model",
        "--ollama_model",
        "--ollamaservice-ollama-model",
    ):
        if candidate.lower() in help_text:
            caps["ollama_model_flag"] = candidate
            break

    for candidate in ("--redo_inline_math", "--redo-inline-math"):
        if candidate in help_text:
            caps["redo_inline_math_flag"] = candidate
            break

    for candidate in (
        "--OllamaService_timeout",
        "--ollamaservice-timeout",
    ):
        if candidate.lower() in help_text:
            caps["ollama_timeout_flag"] = candidate
            break

    for candidate in ("--disable_image_extraction", "--disable-image-extraction"):
        if candidate in help_text:
            caps["disable_image_extraction_flag"] = candidate
            break

    return caps


def detect_marker_capabilities(
    marker_cli: str | None,
    *,
    use_cache: bool = True,
    run_cmd=subprocess.run,
) -> Dict[str, object]:
    global _MARKER_CAPABILITIES_CACHE

    if use_cache and _MARKER_CAPABILITIES_CACHE is not None:
        return dict(_MARKER_CAPABILITIES_CACHE)

    caps = default_marker_capabilities()
    if not marker_cli:
        caps = {k: None for k in caps}
        _MARKER_CAPABILITIES_CACHE = dict(caps)
        return dict(caps)

    try:
        proc = run_cmd(
            [marker_cli, "--help"],
            capture_output=True,
            text=True,
            timeout=45,
        )
        help_text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).lower()
    except Exception as exc:
        logger.warning(
            "  [marker] Não foi possível inspecionar --help: %s. Usando fallback otimista com as flags atuais conhecidas do Marker.",
            exc,
        )
        if use_cache:
            _MARKER_CAPABILITIES_CACHE = dict(caps)
        return dict(caps)

    caps = apply_marker_capabilities_help_text(help_text, caps)

    if use_cache:
        _MARKER_CAPABILITIES_CACHE = dict(caps)
    logger.info("  [marker] Capabilities detectadas: %s", caps)
    return dict(caps)


def advanced_cli_stall_timeout(
    backend_name: str,
    ctx: "BackendContext",
    *,
    effective_document_profile_fn,
    selected_page_count_fn=selected_page_count,
) -> int:
    base_timeout = int(ctx.stall_timeout or 300)
    effective_profile = effective_document_profile_fn(ctx.entry.document_profile, ctx.report.suggested_profile)
    selected_pages = selected_page_count_fn(ctx)
    heavy_profiles = {"math_heavy", "diagram_heavy", "scanned"}

    if backend_name == "marker":
        marker_model = marker_ollama_model(ctx)
        marker_llm_active = marker_should_use_llm(ctx) and bool(marker_model)
        if marker_llm_active and marker_model_is_qwen3_vl_8b(marker_model):
            if effective_profile in heavy_profiles and selected_pages >= 80:
                return max(base_timeout, 3600)
            if effective_profile in heavy_profiles and selected_pages >= 40:
                return max(base_timeout, 2700)
            return max(base_timeout, 1200)
        if marker_llm_active:
            if effective_profile in heavy_profiles and selected_pages >= 80:
                return max(base_timeout, 3600)
            if effective_profile in heavy_profiles and selected_pages >= 40:
                return max(base_timeout, 2700)
            return max(base_timeout, 900)
        if effective_profile in {"math_heavy", "diagram_heavy"} and selected_pages >= 80:
            return max(base_timeout, 2700)
        if effective_profile in {"math_heavy", "diagram_heavy"} and selected_pages >= 40:
            return max(base_timeout, 1800)
        return base_timeout

    if backend_name == "docling":
        if effective_profile in heavy_profiles and (selected_pages >= 80 or ctx.report.images_count >= 200):
            return max(base_timeout, 1800)
        if effective_profile in heavy_profiles and selected_pages >= 40:
            return max(base_timeout, 1200)
        return base_timeout

    return base_timeout


def run_cli_with_timeout(
    cmd: list,
    backend_name: str,
    ctx: "BackendContext",
    *,
    logger_obj,
    marker_effective_torch_device_fn,
    marker_progress_hints_fn,
    marker_should_use_llm_fn,
    marker_ollama_model_fn,
    marker_model_is_qwen3_vl_8b_fn,
    stall_timeout: Optional[int] = None,
):
    """Run an external CLI process with stall timeout and cancel support."""
    stdout_lines: list = []
    stderr_lines: list = []
    last_output_time = _time.monotonic()
    effective_stall_timeout = stall_timeout if stall_timeout is not None else ctx.stall_timeout
    lock = _th.Lock()
    killed_by_cancel = _th.Event()
    killed_by_stall = _th.Event()
    last_marker_phase = {"name": None}
    process_env = None

    if backend_name == "marker":
        process_env = os.environ.copy()
        process_env["TORCH_DEVICE"] = marker_effective_torch_device_fn(ctx)

    def _log_marker_progress_hint(line: str):
        if backend_name != "marker":
            return
        phase, hints = marker_progress_hints_fn(line, last_marker_phase["name"])
        last_marker_phase["name"] = phase
        for hint in hints:
            logger_obj.info("  [marker] %s", hint)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=process_env,
    )
    logger_obj.info("  [%s] PID=%d - aguardando saida...", backend_name, proc.pid)

    def _phase_stall_timeout() -> int:
        phase_stall_timeout = effective_stall_timeout
        if backend_name == "marker" and marker_should_use_llm_fn(ctx) and marker_ollama_model_fn(ctx):
            phase_name = str(last_marker_phase.get("name") or "")
            if phase_name.startswith("LLM processors running"):
                if marker_model_is_qwen3_vl_8b_fn(marker_ollama_model_fn(ctx)):
                    phase_stall_timeout = max(phase_stall_timeout, 1800)
                else:
                    phase_stall_timeout = max(phase_stall_timeout, 1200)
        return phase_stall_timeout

    def _read_stderr():
        nonlocal last_output_time
        for line in proc.stderr:
            line = line.rstrip()
            if line:
                with lock:
                    stderr_lines.append(line)
                    last_output_time = _time.monotonic()
                _log_marker_progress_hint(line)
                logger_obj.info("  [%s stderr] %s", backend_name, line)

    stderr_thread = _th.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    def _watchdog():
        while proc.poll() is None:
            _time.sleep(2)
            if ctx.cancel_check:
                try:
                    ctx.cancel_check()
                except InterruptedError:
                    logger_obj.warning(
                        "  [%s] Cancelado pelo usuario - matando PID %d",
                        backend_name,
                        proc.pid,
                    )
                    killed_by_cancel.set()
                    proc.kill()
                    return
            with lock:
                elapsed = _time.monotonic() - last_output_time
            phase_stall_timeout = _phase_stall_timeout()
            if elapsed > phase_stall_timeout:
                logger_obj.error(
                    "  [%s] Sem output por %ds - matando PID %d (stall timeout)",
                    backend_name,
                    phase_stall_timeout,
                    proc.pid,
                )
                killed_by_stall.set()
                proc.kill()
                return

    watchdog_thread = _th.Thread(target=_watchdog, daemon=True)
    watchdog_thread.start()

    for line in proc.stdout:
        line = line.rstrip()
        if line:
            stdout_lines.append(line)
            with lock:
                last_output_time = _time.monotonic()
            _log_marker_progress_hint(line)
            logger_obj.info("  [%s stdout] %s", backend_name, line)

    proc.wait()
    stderr_thread.join(timeout=5)
    watchdog_thread.join(timeout=2)

    if killed_by_cancel.is_set():
        raise InterruptedError(f"{backend_name} cancelado pelo usuario.")

    if killed_by_stall.is_set():
        last_line = (stderr_lines or stdout_lines or ["(nenhum)"])[-1]
        phase_stall_timeout = _phase_stall_timeout()
        raise TimeoutError(
            f"{backend_name} travou (sem output por {phase_stall_timeout}s). "
            f"Ultimo output:\n{last_line}"
        )

    returncode = proc.returncode
    logger_obj.info("  [%s] Processo finalizado com codigo %d", backend_name, returncode)
    return returncode, stdout_lines, stderr_lines
