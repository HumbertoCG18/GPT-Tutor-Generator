"""Ollama HTTP client for local Vision model (Qwen3-VL)."""

import base64
import json
import logging
from pathlib import Path
from typing import Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3-vl"
FALLBACK_MODEL = "qwen2.5vl:7b"

IMAGE_TYPE_PROMPTS = {
    "diagrama": (
        "Descreva a estrutura deste diagrama academicamente. "
        "Identifique nós, relações, hierarquia e regras representadas. "
        "Use notação formal quando possível. Responda em português."
    ),
    "tabela": (
        "Transcreva esta tabela fielmente em formato markdown. "
        "Preserve cabeçalhos, valores e alinhamento. Responda em português."
    ),
    "fórmula": (
        "Transcreva esta fórmula ou expressão matemática em LaTeX. "
        "Se houver contexto visual como setas ou anotações, descreva-o. "
        "Responda em português."
    ),
    "código": (
        "Transcreva este código exatamente como aparece na imagem. "
        "Identifique a linguagem de programação se possível. Responda em português."
    ),
    "genérico": (
        "Descreva o conteúdo desta imagem de forma detalhada e academicamente útil. "
        "Responda em português."
    ),
}


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def check_availability(self) -> Tuple[bool, str]:
        """Check if Ollama is running and a vision model is available.
        Tries DEFAULT_MODEL first, falls back to FALLBACK_MODEL.
        Returns (available, message).
        """
        try:
            resp = urlopen(f"{self.base_url}/api/tags")
            data = json.loads(resp.read())
        except (URLError, ConnectionError, OSError):
            return False, (
                f"Ollama não está rodando em {self.base_url}.\n"
                "Instale em https://ollama.com e rode 'ollama serve'."
            )

        model_names = [m.get("name", "") for m in data.get("models", [])]

        # Try primary model
        base = self.model.split(":")[0]
        if any(base in name for name in model_names):
            return True, f"Ollama disponível ({self.model})."

        # Try fallback
        fallback_base = FALLBACK_MODEL.split(":")[0]
        if any(fallback_base in name for name in model_names):
            logger.info("Modelo primário '%s' não encontrado, usando fallback '%s'.", self.model, FALLBACK_MODEL)
            self.model = FALLBACK_MODEL
            return True, f"Ollama disponível (fallback: {FALLBACK_MODEL})."

        return False, (
            f"Nenhum modelo Vision encontrado no Ollama.\n"
            f"Rode: ollama pull {DEFAULT_MODEL}\n"
            f"Ou: ollama pull {FALLBACK_MODEL}"
        )

    def describe_image(self, image_path: Path, image_type: str, page_context: str) -> str:
        """Send an image to the Vision model and return the text description.

        Args:
            image_path: Path to the image file.
            image_type: One of the IMAGE_TYPE_PROMPTS keys.
            page_context: Markdown text from the same page as the image.
                          Required — provides surrounding context for faithful descriptions.
        """
        prompt = IMAGE_TYPE_PROMPTS.get(image_type, IMAGE_TYPE_PROMPTS["genérico"])
        prompt += (
            "\n\nContexto da página onde esta imagem aparece:\n"
            "---\n"
            f"{page_context[:2000]}\n"
            "---\n"
            "Use este contexto para enriquecer e corrigir sua descrição. "
            "Informações como nomes de variáveis, ordem de enumeração, "
            "rótulos e definições presentes no texto devem ser refletidas "
            "fielmente na descrição da imagem."
        )
        import time

        img_bytes = image_path.read_bytes()
        img_size_kb = len(img_bytes) / 1024
        image_b64 = base64.b64encode(img_bytes).decode("utf-8")
        logger.info(
            "[Ollama] Preparando request: %s (%.0f KB, tipo: %s, contexto: %d chars)",
            image_path.name, img_size_kb, image_type, len(page_context),
        )

        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "keep_alive": "10m",
        }).encode("utf-8")

        payload_mb = len(payload) / (1024 * 1024)
        logger.info(
            "[Ollama] Enviando para %s/api/generate (payload: %.1f MB, modelo: %s)...",
            self.base_url, payload_mb, self.model,
        )

        req = Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        t0 = time.time()
        resp = urlopen(req, timeout=300)
        raw = resp.read()
        elapsed = time.time() - t0
        logger.info("[Ollama] Resposta recebida em %.1fs (%d bytes)", elapsed, len(raw))

        result = json.loads(raw)
        response_text = result.get("response", "").strip()
        tokens = result.get("eval_count", "?")
        logger.info("[Ollama] Descrição: %d chars, ~%s tokens", len(response_text), tokens)
        return response_text
