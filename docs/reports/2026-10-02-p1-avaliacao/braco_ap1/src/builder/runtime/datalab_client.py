from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import requests


DEFAULT_DATALAB_BASE_URL = "https://www.datalab.to"

# O submit faz upload do PDF e o servidor pode segurar a conexao enquanto
# ingere o arquivo; precisa de read timeout bem maior que o poll de status.
DEFAULT_SUBMIT_TIMEOUT = 180
DEFAULT_POLL_TIMEOUT = 60
DEFAULT_CONNECT_TIMEOUT = 15

# Excecoes transientes de rede que valem retry (submit) / continuar (poll).
_TRANSIENT_ERRORS = (
    requests.exceptions.ReadTimeout,
    requests.exceptions.ConnectTimeout,
    requests.exceptions.ConnectionError,
)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def get_datalab_submit_timeout() -> int:
    return _env_int("DATALAB_SUBMIT_TIMEOUT", DEFAULT_SUBMIT_TIMEOUT)


def get_datalab_poll_timeout() -> int:
    return _env_int("DATALAB_REQUEST_TIMEOUT", DEFAULT_POLL_TIMEOUT)


@dataclass
class DatalabConvertResult:
    request_id: str
    request_check_url: str
    markdown: str
    images: Dict[str, str]
    metadata: Dict[str, object]
    page_count: int
    parse_quality_score: Optional[float]
    cost_breakdown: Dict[str, object]
    raw_response: Dict[str, object]


def get_datalab_api_key() -> str:
    return str(os.environ.get("DATALAB_API_KEY", "") or "").strip()


def get_datalab_base_url() -> str:
    return str(os.environ.get("DATALAB_BASE_URL", DEFAULT_DATALAB_BASE_URL) or DEFAULT_DATALAB_BASE_URL).rstrip("/")


def has_datalab_api_key() -> bool:
    return bool(get_datalab_api_key())


def convert_document_to_markdown(
    source_path: Path,
    *,
    output_format: str = "markdown",
    mode: str = "accurate",
    page_range: Optional[str] = None,
    max_pages: Optional[int] = None,
    disable_image_captions: bool = True,
    disable_image_extraction: bool = True,
    paginate: bool = False,
    token_efficient_markdown: bool = False,
    skip_cache: bool = False,
    additional_config: Optional[Dict[str, object]] = None,
    request_timeout: Optional[int] = None,
    submit_timeout: Optional[int] = None,
    poll_interval: float = 2.0,
    max_wait_seconds: int = 1800,
    max_retries: int = 2,
) -> DatalabConvertResult:
    api_key = get_datalab_api_key()
    if not api_key:
        raise RuntimeError("DATALAB_API_KEY não está configurada no ambiente/.env.")

    base_url = get_datalab_base_url()
    headers = {"X-API-Key": api_key}
    submit_url = f"{base_url}/api/v1/convert"

    data = {
        "output_format": output_format,
        "mode": mode,
        "disable_image_captions": json.dumps(bool(disable_image_captions)).lower(),
        "disable_image_extraction": json.dumps(bool(disable_image_extraction)).lower(),
        "paginate": json.dumps(bool(paginate)).lower(),
        "token_efficient_markdown": json.dumps(bool(token_efficient_markdown)).lower(),
        "skip_cache": json.dumps(bool(skip_cache)).lower(),
    }
    if page_range:
        data["page_range"] = page_range
    if max_pages is not None:
        data["max_pages"] = str(max_pages)
    if additional_config:
        data["additional_config"] = json.dumps(additional_config, ensure_ascii=False)

    submit_to = submit_timeout if submit_timeout is not None else get_datalab_submit_timeout()
    poll_to = request_timeout if request_timeout is not None else get_datalab_poll_timeout()
    connect_to = DEFAULT_CONNECT_TIMEOUT

    # Submit (upload): read timeout generoso + retry em falha transiente. O
    # handle do arquivo e reaberto a cada tentativa (o stream e consumido).
    submit_payload: Dict[str, object] = {}
    last_exc: Optional[BaseException] = None
    for attempt in range(max_retries + 1):
        try:
            with source_path.open("rb") as fh:
                response = requests.post(
                    submit_url,
                    headers=headers,
                    files={"file": (source_path.name, fh, "application/pdf")},
                    data=data,
                    timeout=(connect_to, submit_to),
                )
            response.raise_for_status()
            submit_payload = response.json()
            break
        except _TRANSIENT_ERRORS as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise
            time.sleep(poll_interval * (attempt + 1))
    if not submit_payload:
        raise RuntimeError(f"Datalab submit falhou sem payload: {last_exc}")

    request_id = str(submit_payload.get("request_id") or "").strip()
    check_url = str(submit_payload.get("request_check_url") or "").strip()
    if not request_id or not check_url:
        raise RuntimeError(f"Resposta inválida do Datalab ao submeter arquivo: {submit_payload}")

    deadline = time.monotonic() + max_wait_seconds
    last_payload: Dict[str, object] = {}

    while True:
        try:
            poll_response = requests.get(check_url, headers=headers, timeout=(connect_to, poll_to))
            poll_response.raise_for_status()
            last_payload = poll_response.json()
        except _TRANSIENT_ERRORS:
            # Timeout transiente no poll nao deve abortar o job: tenta de novo
            # ate o deadline geral (max_wait_seconds).
            if time.monotonic() >= deadline:
                raise
            time.sleep(poll_interval)
            continue
        status = str(last_payload.get("status") or "").strip().lower()

        if status == "complete":
            break
        if status == "failed":
            raise RuntimeError(str(last_payload.get("error") or "Datalab retornou status=failed."))
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Datalab não concluiu o processamento em {max_wait_seconds}s. "
                f"Último status: {json.dumps(last_payload, ensure_ascii=False)[:400]}"
            )
        time.sleep(poll_interval)

    return DatalabConvertResult(
        request_id=request_id,
        request_check_url=check_url,
        markdown=str(last_payload.get("markdown") or ""),
        images=dict(last_payload.get("images") or {}),
        metadata=dict(last_payload.get("metadata") or {}),
        page_count=int(last_payload.get("page_count") or 0),
        parse_quality_score=(
            float(last_payload["parse_quality_score"])
            if last_payload.get("parse_quality_score") is not None
            else None
        ),
        cost_breakdown=dict(last_payload.get("cost_breakdown") or {}),
        raw_response=last_payload,
    )
