import json
import os
import re
from typing import Optional, List
import logging

try:
    import openai
except ImportError:
    openai = None

try:
    from google import genai
except ImportError:
    genai = None

from src.utils.helpers import DEFAULT_CATEGORIES, slugify

logger = logging.getLogger(__name__)

_VALID_CATEGORIES = set(DEFAULT_CATEGORIES)

class LLMCategorizer:
    def __init__(self, provider: str, openai_key: str, gemini_key: str):
        self.provider = (provider or "").lower().strip()
        self.openai_key = (openai_key or "").strip()
        self.gemini_key = (gemini_key or "").strip()

    def is_configured(self) -> bool:
        if self.provider == "openai" and self.openai_key:
            return True
        if self.provider == "gemini" and self.gemini_key:
            return True
        return False

    def classify_pdf(
        self,
        course_name: str,
        syllabus: str,
        teaching_plan: str,
        pdf_preview_text: str,
        known_category: str = "",
        other_file_titles: Optional[List[str]] = None,
    ) -> dict:
        """
        Retorna {"category": str, "unit": str, "exam_ref": str}.
        - category: um dos valores de DEFAULT_CATEGORIES.
        - unit: slug da unidade (ex: "unidade-01-metodos-formais"), ou "".
        - exam_ref: para gabaritos/listas, referência ao item correspondente
          (ex: "Prova 1 - Unidade 2"), ou "".
        """
        if not self.is_configured():
            logger.warning("LLMCategorizer não está configurado.")
            return {"category": "outros", "unit": "", "exam_ref": ""}

        # Build structured unit map from teaching plan (if available)
        structured_plan = ""
        valid_slugs: List[str] = []
        try:
            from src.builder.engine import _parse_units_from_teaching_plan, _format_units_for_prompt
            units = _parse_units_from_teaching_plan(teaching_plan) if teaching_plan else []
            if units:
                structured_plan = _format_units_for_prompt(units)
                valid_slugs = [slugify(title) for title, _ in units]
        except Exception as e:
            logger.debug("Could not parse teaching plan for structured prompt: %s", e)

        other_ctx = ""
        if other_file_titles:
            titles_list = "\n".join(f"- {t}" for t in other_file_titles[:30])
            other_ctx = f"\n## Outros arquivos já na fila (para referência cruzada):\n{titles_list}\n"

        category_hint = ""
        if known_category and known_category not in ("", "outros", "pdf"):
            category_hint = f'\nCATEGORIA JÁ IDENTIFICADA: "{known_category}" — confirme ou corrija.'

        exam_ref_instruction = ""
        if known_category in ("gabaritos", "listas", "provas"):
            exam_ref_instruction = (
                '\n- "exam_ref": se este arquivo é um gabarito ou lista, indique a qual prova/'
                'lista/unidade ele se refere (ex: "Prova 1 Unidade 2", "Lista 3"). '
                'Use os títulos dos outros arquivos na fila para cruzar. Se não souber, use "".'
            )
        else:
            exam_ref_instruction = '\n- "exam_ref": deixe "".'

        # Use structured plan if available, fallback to raw text
        if structured_plan:
            plan_section = f"## Estrutura do curso (unidades e tópicos):\n{structured_plan}"
        else:
            plan_section = f"## Plano de Ensino:\n{teaching_plan[:3000]}"

        # Build slug instruction
        if valid_slugs:
            slugs_list = ", ".join(f'"{s}"' for s in valid_slugs)
            unit_instruction = (
                f'- "unit": slug da unidade. Use EXATAMENTE um dos seguintes: {slugs_list}. '
                f'Se não souber, use "".'
            )
        else:
            unit_instruction = '- "unit": slug da unidade (ex: "unidade-1"). Se não souber, use "".'

        prompt = f"""Você é um assistente de curadoria acadêmica.
Analise o trecho inicial do PDF e classifique-o.

# Disciplina: {course_name}
{category_hint}
{plan_section}

## Cronograma:
{syllabus[:1000]}
{other_ctx}
# Tarefa
Retorne APENAS um objeto JSON com exatamente três campos:
- "category": tipo do arquivo. Escolha UM dentre:
  material-de-aula, provas, listas, gabaritos, fotos-de-prova,
  referencias, bibliografia, cronograma, outros
{unit_instruction}{exam_ref_instruction}

REGRAS:
- Retorne APENAS o JSON cru, sem markdown, sem crases, sem explicações.
- Exemplo: {{"category": "listas", "unit": "unidade-02-verificacao-de-programas", "exam_ref": "Lista 3 - Unidade 2"}}
- Em caso de dúvida no tipo, use "material-de-aula". Na unidade, use "".

# Trecho do PDF:
\"\"\"
{pdf_preview_text[:2500]}
\"\"\"
"""
        try:
            if self.provider == "openai":
                raw = self._call_openai(prompt, max_tokens=256)
            elif self.provider == "gemini":
                raw = self._call_gemini(prompt, max_output_tokens=1024)
            else:
                return {"category": "outros", "unit": "", "exam_ref": ""}
            return self._parse_llm_json(raw)
        except Exception as e:
            logger.error(f"Erro ao chamar LLM ({self.provider}): {e}")
            return {"category": "outros", "unit": "", "exam_ref": ""}

    def _parse_llm_json(self, raw: str) -> dict:
        """Extrai JSON da resposta, tolerante a markdown, thinking e whitespace."""
        logger.debug("LLM raw response: %s", raw[:500])
        cleaned = raw.strip()
        # Remove blocos de código markdown
        cleaned = re.sub(r"```(?:json)?", "", cleaned).strip()
        # Tenta extrair o primeiro objeto JSON { ... } da resposta
        match = re.search(r'\{[^{}]*\}', cleaned)
        if match:
            cleaned = match.group(0)
        try:
            data = json.loads(cleaned)
            category = data.get("category", "outros").strip().lower()
            unit = data.get("unit", "").strip().lower()
            exam_ref = data.get("exam_ref", "").strip()
            if category not in _VALID_CATEGORIES:
                category = "outros"
            logger.info("LLM parsed: category=%s, unit=%s, exam_ref=%s", category, unit, exam_ref)
            return {"category": category, "unit": unit, "exam_ref": exam_ref}
        except Exception as e:
            logger.error("Falha ao parsear JSON do LLM: %s | raw: %s", e, raw[:300])
            return {"category": "outros", "unit": "", "exam_ref": ""}

    def categorize_pdf(self, course_name: str, syllabus: str, teaching_plan: str, pdf_preview_text: str) -> str:
        """Alias legado — retorna só o category."""
        return self.classify_pdf(course_name, syllabus, teaching_plan, pdf_preview_text)["category"]

    def _call_openai(self, prompt: str, max_tokens: int = 50) -> str:
        if not openai:
            logger.error("Pacote 'openai' não está instalado.")
            return ""

        client = openai.OpenAI(api_key=self.openai_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é uma ferramenta estrita de categorização acadêmica. Responda apenas com JSON puro."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=max_tokens
        )
        return (response.choices[0].message.content or "").strip()

    def _call_gemini(self, prompt: str, max_output_tokens: int = 50) -> str:
        if not genai:
            logger.error("Pacote 'google-genai' não está instalado.")
            return ""

        client = genai.Client(api_key=self.gemini_key)
        config_kwargs = dict(
            temperature=0.0,
            max_output_tokens=max_output_tokens,
            system_instruction="Você é uma ferramenta estrita de categorização acadêmica. Responda apenas com JSON puro.",
        )
        # Desabilita thinking no 2.5-flash para respostas diretas
        if hasattr(genai.types, "ThinkingConfig"):
            config_kwargs["thinking_config"] = genai.types.ThinkingConfig(thinking_budget=0)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(**config_kwargs),
        )
        return (response.text or "").strip()
