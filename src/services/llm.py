import os
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

logger = logging.getLogger(__name__)

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

    def categorize_pdf(self, course_name: str, syllabus: str, teaching_plan: str, pdf_preview_text: str) -> str:
        """
        Pede à IA para classificar o texto do PDF dentro de alguma unidade do Plano de Ensino.
        Retorna EXATAMENTE o nome sugerido para a categoria/unidade, ou "pdf" se não conseguir.
        """
        if not self.is_configured():
            logger.warning("LLMCategorizer não está configurado.")
            return "pdf"

        prompt = f"""Você é um assistente de curadoria acadêmica. 
Sua tarefa é classificar um documento PDF em qual Unidade/Tópico de aula ele pertence, baseando-se no PLANO DE ENSINO.

# Dados da Disciplina: {course_name}

## Plano de Ensino:
{teaching_plan}

## Cronograma / Unidades:
{syllabus}

# Tarefa:
Analise o trecho inicial do PDF abaixo. 
Identifique qual é a "Unidade" ou "Tópico" principal mais aderente do cronograma.
SE NÃO FOR POSSÍVEL IDENTIFICAR COM CLAREZA absoluta, retorne exatamente: pdf
SE CONSEGUIR, extraia uma tag curta para categorização. Exemplo: Se o cronograma diz "Unidade 1 - Introdução ao Direito", tente retornar algo no formato "unidade-1".
Mas se as unidades estiverem estruturadas de outra forma, crie uma string de subpasta no formato "kebab-case" (ex: "tema-1-introducao").

# Regras:
- Retorne APENAS a string da categoria (nome da pasta).
- Não retorne NADA ALÉM da palavra, sem ponto, sem crases, sem aspas, sem explicações.
- Tudo minúsculo, substituindo espaços por hífens.
- Em caso de dúvida, retorne: pdf

# Trecho inicial do PDF:
\"\"\"
{pdf_preview_text[:2500]} 
\"\"\"
"""
        try:
            if self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "gemini":
                return self._call_gemini(prompt)
            else:
                return "pdf"
        except Exception as e:
            logger.error(f"Erro ao chamar LLM ({self.provider}): {e}")
            return "pdf"

    def _call_openai(self, prompt: str) -> str:
        if not openai:
            logger.error("Pacote 'openai' não está instalado.")
            return "pdf"
            
        client = openai.OpenAI(api_key=self.openai_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é uma ferramenta estrita de categorização. Só responde a string requisitada em letras minúsculas e hífens."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        cat = response.choices[0].message.content.strip()
        return cat if cat else "pdf"

    def _call_gemini(self, prompt: str) -> str:
        if not genai:
            logger.error("Pacote 'google-genai' não está instalado.")
            return "pdf"
            
        client = genai.Client(api_key=self.gemini_key)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=50,
                system_instruction="Você é uma ferramenta estrita de categorização. Só responde a string requisitada em letras minúsculas e hífens."
            )
        )
        cat = response.text.strip()
        return cat if cat else "pdf"
