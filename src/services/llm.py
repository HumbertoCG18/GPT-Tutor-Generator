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

from src.utils.helpers import DEFAULT_CATEGORIES

logger = logging.getLogger(__name__)

_VALID_CATEGORIES = set(DEFAULT_CATEGORIES)

class LLMCategorizer:
    def __init__(self, provider: str, openai_key: str, gemini_key: str):
        self.provider = provider.lower().strip()
        self.openai_key = openai_key.strip()
        self.gemini_key = gemini_key.strip()

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
        - unit: slug da unidade (ex: "unidade-1"), ou "".
        - exam_ref: para gabaritos/listas, referência ao item correspondente
          (ex: "Prova 1 - Unidade 2"), ou "".
        """
        if not self.is_configured():
            logger.warning("LLMCategorizer não está configurado.")
            return {"category": "outros", "unit": "", "exam_ref": ""}

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

        prompt = f"""Você é um assistente de curadoria acadêmica.
Analise o trecho inicial do PDF e classifique-o.

# Disciplina: {course_name}
{category_hint}
## Plano de Ensino:
{teaching_plan[:3000]}

## Cronograma:
{syllabus[:1000]}
{other_ctx}
# Tarefa
Retorne APENAS um objeto JSON com exatamente três campos:
- "category": tipo do arquivo. Escolha UM dentre:
  material-de-aula, provas, listas, gabaritos, fotos-de-prova,
  referencias, bibliografia, cronograma, outros
- "unit": unidade do cronograma. Use slug (ex: "unidade-1"). Se não souber, use "".{exam_ref_instruction}

REGRAS:
- Retorne APENAS o JSON cru, sem markdown, sem crases, sem explicações.
- Exemplo: {{"category": "listas", "unit": "unidade-2", "exam_ref": "Lista 3 - Unidade 2"}}
- Em caso de dúvida no tipo, use "material-de-aula". Na unidade, use "".

# Trecho do PDF:
\"\"\"
{pdf_preview_text[:2500]}
\"\"\"
"""
        try:
            if self.provider == "openai":
                raw = self._call_openai(prompt, max_tokens=150)
            elif self.provider == "gemini":
                raw = self._call_gemini(prompt, max_output_tokens=150)
            else:
                return {"category": "outros", "unit": "", "exam_ref": ""}
            return self._parse_llm_json(raw)
        except Exception as e:
            logger.error(f"Erro ao chamar LLM ({self.provider}): {e}")
            return {"category": "outros", "unit": "", "exam_ref": ""}

    def _parse_llm_json(self, raw: str) -> dict:
        """Extrai JSON da resposta, tolerante a markdown e whitespace."""
        raw = raw.strip()
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        try:
            data = json.loads(raw)
            category = data.get("category", "outros").strip().lower()
            unit = data.get("unit", "").strip().lower()
            exam_ref = data.get("exam_ref", "").strip()
            if category not in _VALID_CATEGORIES:
                category = "outros"
            return {"category": category, "unit": unit, "exam_ref": exam_ref}
        except Exception:
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
        return response.choices[0].message.content.strip()

    def _call_gemini(self, prompt: str, max_output_tokens: int = 50) -> str:
        if not genai:
            logger.error("Pacote 'google-genai' não está instalado.")
            return ""

        client = genai.Client(api_key=self.gemini_key)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=max_output_tokens,
                system_instruction="Você é uma ferramenta estrita de categorização acadêmica. Responda apenas com JSON puro."
            )
        )
        return response.text.strip()
