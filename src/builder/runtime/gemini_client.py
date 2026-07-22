"""Gemini API client for code summarization."""
from __future__ import annotations
import logging
import os
import time
from typing import Optional, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.5-flash"

# Modelos aposentados pela API (404 em generateContent). Config persistido
# antigo pode ainda apontar pra eles: resolve em runtime pro default vivo.
RETIRED_MODELS = frozenset({"gemini-2.5-flash", "gemini-2.5-pro"})


def _resolve_gemini_key(config) -> str:
    """Chave Gemini com precedência config (UI) > GEMINI_API_KEY do .env/ambiente.

    `.env` é carregado em os.environ no import (helpers._load_project_env_file),
    espelhando o princípio do DATALAB sem quebrar o campo da UI.
    """
    key = ""
    if config is not None:
        key = (config.get("gemini_api_key", "") or "").strip()
    if not key:
        key = (os.environ.get("GEMINI_API_KEY", "") or "").strip()
    return key


def has_gemini_api_key(config) -> bool:
    return bool(_resolve_gemini_key(config))


class GeminiClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai não instalado. Rode: pip install google-genai"
            ) from exc
        self._client = genai.Client(api_key=self.api_key)

    def summarize_bundle(
        self,
        bundle_text: str,
        schema: Type[BaseModel],
        system_instruction: str,
        max_retries: int = 5,
    ) -> BaseModel:
        self._ensure_client()
        from google.genai import types
        from google.genai import errors as genai_errors

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
        )

        delay = 1.0
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                resp = self._client.models.generate_content(
                    model=self.model,
                    contents=bundle_text,
                    config=config,
                )
                if resp.parsed is None:
                    raise RuntimeError("Gemini retornou parsed=None")
                return resp.parsed
            except genai_errors.ClientError as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    last_exc = e
                    logger.warning("[Gemini] 429 attempt %d/%d, sleeping %.1fs",
                                   attempt + 1, max_retries, delay)
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
                    continue
                raise
            except genai_errors.ServerError as e:
                last_exc = e
                logger.warning("[Gemini] 5xx attempt %d/%d, sleeping %.1fs",
                               attempt + 1, max_retries, delay)
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
        raise RuntimeError(f"Gemini falhou após {max_retries} tentativas") from last_exc


def get_gemini_client(config) -> Optional[GeminiClient]:
    key = _resolve_gemini_key(config)
    if not key:
        return None
    model = config.get("gemini_model", DEFAULT_MODEL) if config is not None else DEFAULT_MODEL
    if model in RETIRED_MODELS:
        # review F4 T1a: remap silencioso de modelo aposentado -> log p/ auditoria
        # (config persistido antigo apontando pra um modelo morto some sem rastro).
        logger.info("gemini_model %r aposentado; usando default %r", model, DEFAULT_MODEL)
        model = DEFAULT_MODEL
    return GeminiClient(api_key=key, model=model)
