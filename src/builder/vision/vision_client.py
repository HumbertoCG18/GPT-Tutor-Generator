"""Factory for the configured image-vision client."""

from __future__ import annotations

from src.builder.vision.ollama_client import (
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    OllamaClient,
)

DEFAULT_BACKEND = "ollama"


def get_vision_client(config=None):
    """Create the configured vision client.

    The current architecture is Ollama-only. ``vision_backend`` is kept in the
    config for backward compatibility with older saved settings.
    """
    model = config.get("vision_model", DEFAULT_MODEL) if config else DEFAULT_MODEL

    quant = config.get("vision_model_quantization", "default") if config else "default"
    base_url = config.get("ollama_base_url", OLLAMA_BASE_URL) if config else OLLAMA_BASE_URL
    if quant != "default":
        model = f"{model}:{quant}" if ":" not in model else model.split(":")[0] + f":{quant}"
    return OllamaClient(base_url=base_url, model=model)
