"""Ollama HTTP client for local Vision model (Qwen3-VL)."""

import base64
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError


logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3-vl:235b-cloud"
FALLBACK_MODEL = "qwen3-vl:8b"

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

LATEX_EXTRACT_PROMPT = (
    "Extraia TODO o conteúdo textual e matemático desta imagem de página escaneada.\n"
    "Regras:\n"
    "- Transcreva o texto em português exatamente como aparece.\n"
    "- Converta fórmulas e expressões matemáticas para LaTeX inline ($...$) ou display ($$...$$).\n"
    "- Preserve a estrutura: títulos, listas, enumerações, parágrafos.\n"
    "- Tabelas devem ser transcritas em formato markdown.\n"
    "- Diagramas devem ser descritos textualmente com notação formal.\n"
    "- NÃO adicione comentários ou explicações — apenas a transcrição fiel.\n"
    "- Responda SOMENTE com o conteúdo extraído, nada mais."
)


def _clean_thinking_artifacts(text: str) -> str:
    """Remove Qwen3-VL thinking/reasoning artifacts from response text.

    When the model ignores think=False and /no_think, its internal reasoning
    (in English) leaks into the output. This function extracts only the final
    Portuguese description, discarding the reasoning chain.
    """
    if not text:
        return text

    # Pattern: thinking in English followed by actual content in Portuguese.
    # Look for a clear transition point where the model switches to the answer.
    # Common patterns: starts writing structured Portuguese after reasoning.

    # 1) If text contains <think>...</think> tags, strip them
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # 2) Detect English reasoning preamble — if text starts with common
    #    thinking phrases, find where Portuguese content begins.
    thinking_starters = (
        "Okay,", "OK,", "Let me", "I need to", "I should", "First,",
        "So,", "Now,", "Wait", "Hmm", "Alright", "The user",
        "Looking at", "I'll ", "Let's",
    )
    if any(text.startswith(s) for s in thinking_starters):
        # Try to find where structured Portuguese output begins.
        # Look for markdown headers, "O diagrama", "A imagem", "Esta", etc.
        pt_patterns = [
            r"\n#{1,3}\s+\*?\*?[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÚÇ]",  # markdown header with PT char
            r"\nO diagrama",
            r"\nA (?:imagem|tabela|fórmula|estrutura|hierarquia)",
            r"\nEsta (?:imagem|tabela|figura)",
            r"\nEste (?:diagrama|código)",
            r"\n---\n",  # markdown separator before answer
        ]
        best_pos = len(text)
        for pat in pt_patterns:
            m = re.search(pat, text)
            if m and m.start() < best_pos:
                best_pos = m.start()

        if best_pos < len(text):
            text = text[best_pos:].strip().lstrip("-").strip()

    return text


def get_vision_setup_status(base_url: str, configured_model: str) -> Dict[str, object]:
    """Collect Ollama vision setup details for UI diagnostics."""
    status: Dict[str, object] = {
        "base_url": base_url.rstrip("/"),
        "configured_model": configured_model,
        "ollama_running": False,
        "available_models": [],
        "model_found": False,
        "exact_model_found": False,
        "fallback_found": False,
        "cloud_model": configured_model.endswith("-cloud"),
        "cloud_ready": False,
        "local_family_ready": False,
    }

    try:
        resp = urlopen(f"{status['base_url']}/api/tags", timeout=3)
        data = json.loads(resp.read())
        available_models: List[str] = [m.get("name", "") for m in data.get("models", [])]
        status["ollama_running"] = True
        status["available_models"] = available_models
        configured_base = configured_model.split(":")[0]
        fallback_base = FALLBACK_MODEL.split(":")[0]
        status["exact_model_found"] = configured_model in available_models
        status["model_found"] = any(configured_base in name for name in available_models)
        status["fallback_found"] = any(fallback_base in name for name in available_models)
        status["cloud_ready"] = bool(status["exact_model_found"]) if status["cloud_model"] else False
        status["local_family_ready"] = bool(status["model_found"]) and not bool(status["exact_model_found"])
    except Exception:
        pass

    return status


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _encode_image(self, image_path: Path) -> Tuple[str, float]:
        """Read and base64-encode an image from disk for Ollama chat payloads."""
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
        if not image_path.is_file():
            raise RuntimeError(f"Caminho de imagem inválido: {image_path}")

        img_bytes = image_path.read_bytes()
        if not img_bytes:
            raise RuntimeError(f"Imagem vazia: {image_path}")

        image_b64 = base64.b64encode(img_bytes).decode("utf-8")
        img_size_kb = len(img_bytes) / 1024
        return image_b64, img_size_kb

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

        if self.model.endswith("-cloud"):
            return False, (
                f"Modelo cloud não encontrado no Ollama: {self.model}\n"
                "Para usar modelos cloud:\n"
                "1. rode 'ollama signin'\n"
                f"2. rode 'ollama pull {self.model}'\n"
                f"3. opcionalmente mantenha um fallback local com 'ollama pull {FALLBACK_MODEL}'"
            )

        return False, (
            f"Nenhum modelo Vision encontrado no Ollama.\n"
            f"Rode: ollama pull {DEFAULT_MODEL}\n"
            f"Ou: ollama pull {FALLBACK_MODEL}"
        )

    def _send_vision_request(self, image_path: Path, prompt: str, label: str) -> str:
        """Send a prompt + image to the Vision model via /api/chat.

        Returns the cleaned response text.
        """
        import time

        image_b64, img_size_kb = self._encode_image(image_path)
        logger.info(
            "[Ollama] Preparando request: %s (%.0f KB, %s)",
            image_path.name, img_size_kb, label,
        )

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de visão acadêmica. "
                        "Analise a imagem enviada e responda apenas com o resultado final em português, "
                        "sem expor raciocínio interno."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                },
            ],
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 4000,
                "think": False,
            },
        }).encode("utf-8")

        payload_mb = len(payload) / (1024 * 1024)
        logger.info(
            "[Ollama] Enviando para %s/api/chat (payload: %.1f MB, modelo: %s)...",
            self.base_url, payload_mb, self.model,
        )

        req = Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        t0 = time.time()
        resp = urlopen(req, timeout=600)
        raw = resp.read()
        elapsed = time.time() - t0
        logger.info("[Ollama] Resposta recebida em %.1fs (%d bytes)", elapsed, len(raw))

        result = json.loads(raw)
        msg = result.get("message", {})
        response_text = msg.get("content", "").strip()

        # Some Ollama/model combinations place the text outside message.content.
        if not response_text:
            response_text = result.get("response", "").strip()

        if not response_text:
            thinking_text = msg.get("thinking", "").strip() or result.get("thinking", "").strip()
            if thinking_text:
                logger.info("[Ollama] Campo final vazio; limpando artefatos de 'thinking'")
                response_text = thinking_text
            else:
                logger.warning(
                    "[Ollama] Resposta vazia! Chaves message: %s, chaves top: %s",
                    list(msg.keys()), list(result.keys()),
                )
                raise RuntimeError(
                    "Ollama retornou uma resposta vazia para a imagem. "
                    "Verifique se o modelo configurado realmente suporta visão."
                )

        # Clean any thinking/reasoning artifacts that leaked into the text
        cleaned = _clean_thinking_artifacts(response_text)
        if len(cleaned) < len(response_text):
            logger.info(
                "[Ollama] Thinking artifacts removidos: %d → %d chars",
                len(response_text), len(cleaned),
            )
            response_text = cleaned

        tokens = result.get("eval_count", "?")
        logger.info("[Ollama] %s: %d chars, ~%s tokens", label, len(response_text), tokens)
        return response_text

    def describe_image(self, image_path: Path, image_type: str, page_context: str) -> str:
        """Send an image to the Vision model and return the text description.

        Args:
            image_path: Path to the image file.
            image_type: One of the IMAGE_TYPE_PROMPTS keys.
            page_context: Markdown text from the same page as the image.
        """
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
        """Extract text + math content from a scanned page image as LaTeX/Markdown.

        Args:
            image_path: Path to the scanned page image.
            page_context: Optional context from adjacent pages.
        """
        prompt = LATEX_EXTRACT_PROMPT
        if page_context:
            prompt += (
                "\n\nContexto de páginas adjacentes (para referência):\n"
                "---\n"
                f"{page_context[:2000]}\n"
                "---"
            )
        return self._send_vision_request(image_path, prompt, "Extração LaTeX")
