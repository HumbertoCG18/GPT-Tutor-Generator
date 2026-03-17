import json
import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence
import sys
import os

logger = logging.getLogger(__name__)

# Environment / Optional Dependencies
try:
    import pymupdf
    HAS_PYMUPDF = True
except Exception:
    pymupdf = None
    HAS_PYMUPDF = False
    logger.info("pymupdf not available; PyMuPDF backend disabled.")

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except Exception:
    pymupdf4llm = None
    HAS_PYMUPDF4LLM = False
    logger.info("pymupdf4llm not available; PyMuPDF4LLM backend disabled.")

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except Exception:
    pdfplumber = None
    HAS_PDFPLUMBER = False
    logger.info("pdfplumber not available; table extraction via pdfplumber disabled.")

DOCLING_CLI = shutil.which("docling")
MARKER_CLI = shutil.which("marker_single")

APP_NAME = "Academic Tutor Repo Builder V3"

DEFAULT_CATEGORIES = [
    "material-de-aula",
    "provas",
    "listas",
    "gabaritos",
    "fotos-de-prova",
    "referencias",
    "bibliografia",
    "cronograma",
    "outros",
]

CATEGORY_LABELS: Dict[str, str] = {
    "material-de-aula": "📘 Material de aula (slides, notas, apostilas)",
    "provas": "📝 Provas anteriores",
    "listas": "📋 Listas de exercícios",
    "gabaritos": "✅ Gabaritos e resoluções",
    "fotos-de-prova": "📷 Fotos de provas/cadernos",
    "referencias": "📚 Referências e documentos",
    "bibliografia": "🔗 Bibliografia (livros, artigos, links)",
    "cronograma": "📅 Cronograma da disciplina",
    "outros": "📦 Outros materiais",
}

_LEGACY_CATEGORY_MAP: Dict[str, str] = {
    "course-material": "material-de-aula",
    "exams": "provas",
    "exercise-lists": "listas",
    "rubrics": "gabaritos",
    "schedule": "cronograma",
    "references": "referencias",
    "photos-of-exams": "fotos-de-prova",
    "answer-keys": "gabaritos",
    "other": "outros",
}

IMAGE_CATEGORIES = {"fotos-de-prova", "provas", "material-de-aula", "outros"}

EXAM_CATEGORIES = ("provas", "fotos-de-prova")
EXERCISE_CATEGORIES = ("listas", "gabaritos")

DEFAULT_OCR_LANGUAGE = "por,eng"

PROCESSING_MODES = ["auto", "quick", "high_fidelity", "manual_assisted"]
DOCUMENT_PROFILES = ["auto", "general", "math_heavy", "layout_heavy", "scanned", "exam_pdf"]
PREFERRED_BACKENDS = ["auto", "pymupdf4llm", "pymupdf", "docling", "marker"]
OCR_LANGS = ["por", "eng", "por,eng", "eng,por"]

# Utilities

def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or "untitled"

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")

def parse_page_range(page_range: str) -> Optional[List[int]]:
    value = (page_range or "").strip()
    if not value:
        return None

    tokens = [t.strip() for t in value.split(",") if t.strip()]
    if not tokens:
        return None

    raw_pages: List[int] = []
    saw_zero = False
    saw_positive = False

    for token in tokens:
        if "-" in token:
            start_str, end_str = [p.strip() for p in token.split("-", 1)]
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError(f"Faixa de páginas inválida: {token}")
            start = int(start_str)
            end = int(end_str)
            if start > end:
                start, end = end, start
            raw_pages.extend(list(range(start, end + 1)))
            if start == 0 or end == 0:
                saw_zero = True
            if end >= 1:
                saw_positive = True
        else:
            if not token.isdigit():
                raise ValueError(f"Página inválida: {token}")
            num = int(token)
            raw_pages.append(num)
            if num == 0:
                saw_zero = True
            if num >= 1:
                saw_positive = True

    pages = sorted(set(raw_pages))
    if not saw_zero and saw_positive:
        pages = [p - 1 for p in pages]

    pages = [p for p in pages if p >= 0]
    return pages or None

def pages_to_marker_range(pages: Optional[Sequence[int]]) -> Optional[str]:
    if not pages:
        return None
    pages = sorted(set(int(p) for p in pages if p >= 0))
    if not pages:
        return None
    ranges: List[str] = []
    start = prev = pages[0]
    for p in pages[1:]:
        if p == prev + 1:
            prev = p
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = p
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)

def file_size_mb(path: Path) -> float:
    try:
        return round(path.stat().st_size / (1024 * 1024), 2)
    except Exception:
        return 0.0

def safe_rel(path: Optional[Path], root: Path) -> Optional[str]:
    if not path:
        return None
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def json_str(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)

def parse_html_schedule(html_content: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "Erro: A biblioteca 'beautifulsoup4' não está instalada.\nUse no terminal: pip install beautifulsoup4"

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    if not table:
        return "Erro: Nenhuma tabela (<table>) encontrada no HTML fornecido."

    rows = table.find_all("tr")
    if not rows:
        return "Erro: A tabela não possui linhas (<tr>)."

    output = []
    
    # Headers
    header_cells = rows[0].find_all(["th", "td"])
    headers = [c.get_text(" ", strip=True) for c in header_cells]
    if not headers:
        return "Erro: Tabela sem colunas reconhecíveis."
        
    output.append("| " + " | ".join(headers) + " |")
    output.append("|" + "|".join(["---"] * len(headers)) + "|")

    # Body
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        row_data = []
        for cell in cells:
            text = " ".join(cell.get_text(" ", strip=True).replace("\n", " ").replace("\r", " ").split())
            row_data.append(text)
            
        if any(row_data):
            output.append("| " + " | ".join(row_data) + " |")

    return "\n".join(output) + "\n"

def get_app_data_dir() -> Path:
    """Retorna o diretório base para configurações do aplicativo."""
    if sys.platform == "win32":
        base_dir = Path(os.getenv("APPDATA")) / "GPTTutorGenerator"
    else:
        base_dir = Path.home() / ".config" / "gpt_tutor_generator"
    ensure_dir(base_dir)
    return base_dir
def auto_detect_category(name: str, is_image: bool = False) -> str:
    """Detecta a categoria provável baseada no nome do arquivo."""
    if is_image:
        return "fotos-de-prova"
    
    name = name.lower()
    if any(k in name for k in ["prova", "exame", "test", "p1", "p2", "p3", "av1", "av2"]):
        return "provas"
    if any(k in name for k in ["lista", "exerc", "quest", "trab", "exer"]):
        return "listas"
    if any(k in name for k in ["gabarito", "resol", "soluc", "key", "espelho"]):
        return "gabaritos"
    if any(k in name for k in ["cronograma", "plano", "agenda", "schedule", "ementa"]):
        return "cronograma"
    if any(k in name for k in ["slide", "aula", "apresenta", "unidade", "modulo", "cap"]):
        return "material-de-aula"
    if any(k in name for k in ["livro", "referencia", "biblio", "artigo", "paper"]):
        return "bibliografia"
    
    return "outros"

def auto_detect_title(path_or_name: str) -> str:
    """Gera um título amigável a partir do nome do arquivo."""
    name = Path(path_or_name).stem
    # Limpa caracteres comuns de separação
    name = name.replace("-", " ").replace("_", " ").replace(".", " ")
    # Remove espaços duplos
    name = " ".join(name.split())
    return name.title()
