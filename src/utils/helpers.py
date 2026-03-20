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


def _configure_tessdata() -> Optional[str]:
    """Detecta a instalação do Tesseract e configura TESSDATA_PREFIX se necessário.
    Retorna o caminho do tessdata encontrado, ou None."""
    # Se já está configurado e o diretório existe, não mexe
    existing = os.environ.get("TESSDATA_PREFIX", "")
    if existing and Path(existing).is_dir():
        return existing

    candidates: List[Path] = []

    # 1. Derivar do executável tesseract no PATH
    tess_bin = shutil.which("tesseract")
    if tess_bin:
        bin_dir = Path(tess_bin).parent
        candidates += [
            bin_dir / "tessdata",
            bin_dir.parent / "tessdata",
            bin_dir.parent / "share" / "tessdata",
        ]

    # 2. Caminhos padrão no Windows
    if sys.platform == "win32":
        for prog in [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
            Path(r"C:\Tesseract-OCR"),
        ]:
            candidates += [prog / "Tesseract-OCR" / "tessdata", prog / "tessdata"]

    # 3. Caminhos padrão no Linux/macOS
    candidates += [
        Path("/usr/share/tesseract-ocr/4.00/tessdata"),
        Path("/usr/share/tesseract-ocr/tessdata"),
        Path("/usr/local/share/tessdata"),
        Path("/opt/homebrew/share/tessdata"),
    ]

    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob("*.traineddata")):
            os.environ["TESSDATA_PREFIX"] = str(candidate)
            logger.info("TESSDATA_PREFIX configurado automaticamente: %s", candidate)
            return str(candidate)

    logger.warning("tessdata não encontrado; OCR por Tesseract pode não funcionar.")
    return None


TESSDATA_PATH = _configure_tessdata()

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
    "trabalhos",
    "codigo-professor",
    "codigo-aluno",
    "quadro-branco",
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
    "trabalhos": "📋 Trabalhos e projetos (enunciados, requisitos)",
    "codigo-professor": "💻 Código do professor (exemplos, base de código)",
    "codigo-aluno": "🧑‍💻 Meu código (para revisão e feedback)",
    "quadro-branco": "🖊 Quadro branco (foto de aula ou explicação)",
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

IMAGE_CATEGORIES = {"fotos-de-prova", "provas", "material-de-aula", "quadro-branco", "outros"}

EXAM_CATEGORIES = ("provas", "fotos-de-prova")
EXERCISE_CATEGORIES = ("listas", "gabaritos")

CODE_EXTENSIONS: set = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h",
    ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt",
    ".scala", ".r", ".m", ".sh", ".bat", ".ps1", ".sql", ".html",
    ".css", ".scss", ".ipynb",
}

LANG_MAP: Dict[str, str] = {
    "py": "python", "js": "javascript", "ts": "typescript",
    "jsx": "jsx", "tsx": "tsx", "java": "java", "c": "c",
    "cpp": "cpp", "h": "c", "hpp": "cpp", "cs": "csharp",
    "go": "go", "rs": "rust", "rb": "ruby", "php": "php",
    "swift": "swift", "kt": "kotlin", "scala": "scala",
    "r": "r", "sh": "bash", "bat": "batch", "ps1": "powershell",
    "sql": "sql", "html": "html", "css": "css", "scss": "scss",
    "ipynb": "json",
}

CODE_CATEGORIES       = ("codigo-professor", "codigo-aluno")
ASSIGNMENT_CATEGORIES = ("trabalhos",)
WHITEBOARD_CATEGORIES = ("quadro-branco",)
STUDENT_BRANCHES      = {"main", "master", "minha-solucao", "aluno", "student"}

DEFAULT_OCR_LANGUAGE = "por,eng"

PROCESSING_MODES = ["auto", "quick", "high_fidelity", "manual_assisted"]
DOCUMENT_PROFILES = ["auto", "general", "math_light", "math_heavy", "layout_heavy", "scanned", "exam_pdf"]
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
        base_dir = Path(os.getenv("APPDATA") or str(Path.home())) / "GPTTutorGenerator"
    else:
        base_dir = Path.home() / ".config" / "gpt_tutor_generator"
    ensure_dir(base_dir)
    return base_dir
def auto_detect_category(name: str, is_image: bool = False) -> str:
    """Detecta a categoria provável baseada no nome do arquivo."""
    if is_image:
        return "fotos-de-prova"
    
    import re as _re
    name = name.lower()
    # Use word-boundary regex for short codes to avoid false positives (e.g. "cap1" matching "p1")
    _wb = lambda pattern: bool(_re.search(r'(?:^|[\W_])' + pattern + r'(?:$|[\W_])', name))
    if any(k in name for k in ["prova", "exame"]) or _wb("test") or _wb("p1") or _wb("p2") or _wb("p3") or _wb("av1") or _wb("av2"):
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

    if any(k in name for k in ["trabalho", "projeto", "assignment",
                                "enunciado", "spec", "requisito"]):
        return "trabalhos"

    ext = Path(name).suffix.lower()
    if ext in CODE_EXTENSIONS:
        return "codigo-professor"

    return "outros"

def auto_detect_title(path_or_name: str) -> str:
    """Gera um título amigável a partir do nome do arquivo."""
    name = Path(path_or_name).stem
    # Limpa caracteres comuns de separação
    name = name.replace("-", " ").replace("_", " ").replace(".", " ")
    # Remove espaços duplos
    name = " ".join(name.split())
    return name.title()


def fetch_url_title(url: str, timeout: float = 5.0) -> str:
    """Busca o <title> de uma URL. Retorna '' em caso de erro.

    Funciona com YouTube, sites genéricos, etc.
    Usa apenas stdlib (urllib) para evitar dependências extras.
    """
    import urllib.request
    import html as html_mod

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            # Lê só os primeiros 64KB para não baixar a página inteira
            raw = resp.read(65536)
            charset = resp.headers.get_content_charset() or "utf-8"
            text = raw.decode(charset, errors="replace")
        # Extrai <title>...</title>
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if m:
            title = m.group(1).strip()
            title = html_mod.unescape(title)
            # YouTube: remove " - YouTube" do final
            title = re.sub(r"\s*[-–—]\s*YouTube\s*$", "", title)
            return title
    except Exception:
        pass
    return ""
