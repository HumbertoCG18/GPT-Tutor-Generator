"""Factory and local backends for image-vision inference."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

from src.builder.ollama_client import (
    IMAGE_TYPE_PROMPTS,
    LATEX_EXTRACT_PROMPT,
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    _clean_thinking_artifacts,
    OllamaClient,
)

logger = logging.getLogger(__name__)

DEFAULT_BACKEND = "ollama"
DEFAULT_TRANSFORMERS_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"


def resolve_transformers_model(model: str) -> str:
    """Return a usable Hugging Face model id for the transformers backend."""
    if model and "/" in model:
        return model
    return DEFAULT_TRANSFORMERS_MODEL


class TransformersVisionClient:
    """Local Hugging Face backend for multimodal image-text generation."""

    def __init__(
        self,
        model: str,
        device_map: str = "auto",
        attn_implementation: Optional[str] = None,
        max_new_tokens: int = 1024,
    ):
        self.model = model
        self.device_map = device_map
        self.attn_implementation = attn_implementation
        self.max_new_tokens = max_new_tokens
        self._processor = None
        self._model = None

    def check_availability(self) -> Tuple[bool, str]:
        resolved_model = resolve_transformers_model(self.model)

        try:
            import transformers  # noqa: F401
        except Exception as exc:
            return False, (
                "O backend transformers não está disponível.\n"
                f"Import falhou: {exc}\n"
                "Instale dependências como transformers, torch e accelerate."
            )

        if resolved_model != self.model:
            return True, (
                f"Backend transformers configurado ({resolved_model}). "
                f"O valor '{self.model}' foi substituído automaticamente por um model id válido."
            )

        return True, f"Backend transformers configurado ({resolved_model})."

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._processor is not None:
            return

        from transformers import AutoModelForImageTextToText, AutoProcessor
        self.model = resolve_transformers_model(self.model)

        kwargs = {
            "device_map": self.device_map,
            "torch_dtype": "auto",
        }
        if self.attn_implementation:
            kwargs["attn_implementation"] = self.attn_implementation

        logger.info("[Vision/transformers] Carregando modelo %s...", self.model)
        self._model = AutoModelForImageTextToText.from_pretrained(self.model, **kwargs)
        self._processor = AutoProcessor.from_pretrained(self.model)
        logger.info("[Vision/transformers] Modelo carregado: %s", self.model)

    def _send_vision_request(self, image_path: Path, prompt: str, label: str) -> str:
        self._ensure_loaded()

        from PIL import Image as PILImage

        pil_image = PILImage.open(image_path).convert("RGB")
        messages = [
            {
                "role": "system",
                "content": "Responda apenas com o resultado final em português, sem expor raciocínio interno.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt},
                ],
            },
        ]

        inputs = self._processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self._model.device)

        logger.info("[Vision/transformers] Gerando saída para %s com %s", label, self.model)
        generated_ids = self._model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
        )
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self._processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        response_text = output_text[0].strip() if output_text else ""
        response_text = _clean_thinking_artifacts(response_text)
        if not response_text:
            raise RuntimeError(
                "O modelo transformers não retornou texto para a imagem. "
                "Revise o model id configurado e a compatibilidade multimodal."
            )

        logger.info("[Vision/transformers] %s: %d chars", label, len(response_text))
        return response_text

    def describe_image(self, image_path: Path, image_type: str, page_context: str) -> str:
        base_prompt = IMAGE_TYPE_PROMPTS.get(image_type, IMAGE_TYPE_PROMPTS["genérico"])
        prompt = (
            f"{base_prompt}\n\n"
            "Contexto da página onde esta imagem aparece:\n"
            "---\n"
            f"{page_context[:2000]}\n"
            "---\n"
            "Use este contexto para enriquecer e corrigir sua descrição. "
            "Informações como nomes de variáveis, ordem de enumeração, "
            "rótulos e definições presentes no texto devem ser refletidas "
            "fielmente na descrição da imagem."
        )
        return self._send_vision_request(image_path, prompt, f"Descrição ({image_type})")

    def extract_to_latex(self, image_path: Path, page_context: str = "") -> str:
        prompt = LATEX_EXTRACT_PROMPT
        if page_context:
            prompt += (
                "\n\nContexto de páginas adjacentes (para referência):\n"
                "---\n"
                f"{page_context[:2000]}\n"
                "---"
            )
        return self._send_vision_request(image_path, prompt, "Extração LaTeX")


def get_vision_client(config=None):
    """Create the configured vision client."""
    backend = config.get("vision_backend", DEFAULT_BACKEND) if config else DEFAULT_BACKEND
    model = config.get("vision_model", DEFAULT_MODEL) if config else DEFAULT_MODEL

    if backend == "transformers":
        return TransformersVisionClient(model=resolve_transformers_model(model))

    quant = config.get("vision_model_quantization", "default") if config else "default"
    base_url = config.get("ollama_base_url", OLLAMA_BASE_URL) if config else OLLAMA_BASE_URL
    if quant != "default":
        model = f"{model}:{quant}" if ":" not in model else model.split(":")[0] + f":{quant}"
    return OllamaClient(base_url=base_url, model=model)
