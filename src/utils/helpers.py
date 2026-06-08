import json
import logging
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from urllib.parse import urlparse
import sys
import os

import requests

logger = logging.getLogger(__name__)


def _load_project_env_file() -> None:
    """Load simple KEY=VALUE pairs from the repository .env without overriding OS env."""
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    if not env_path.exists():
        return

    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value
    except Exception:
        logger.debug("Falha ao carregar .env local do projeto.", exc_info=True)


_load_project_env_file()

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

def _resolve_cli_from_project_venv(command_name: str) -> Optional[str]:
    """Resolve a CLI preferring the repository-local virtualenv over PATH."""
    project_root = Path(__file__).resolve().parents[2]
    candidate_dirs = []

    if os.name == "nt":
        candidate_dirs.extend(
            [
                project_root / ".venv" / "Scripts",
                project_root / "venv" / "Scripts",
            ]
        )
        candidate_names = [f"{command_name}.exe", f"{command_name}.bat", command_name]
    else:
        candidate_dirs.extend(
            [
                project_root / ".venv" / "bin",
                project_root / "venv" / "bin",
            ]
        )
        candidate_names = [command_name]

    for candidate_dir in candidate_dirs:
        for candidate_name in candidate_names:
            candidate_path = candidate_dir / candidate_name
            if candidate_path.is_file():
                return str(candidate_path)

    return shutil.which(command_name)


DOCLING_CLI = shutil.which("docling")
MARKER_CLI = _resolve_cli_from_project_venv("marker_single")


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
    ".css", ".scss", ".ipynb", ".thy", ".dfy",
}

LANG_MAP: Dict[str, str] = {
    "py": "python", "js": "javascript", "ts": "typescript",
    "jsx": "jsx", "tsx": "tsx", "java": "java", "c": "c",
    "cpp": "cpp", "h": "c", "hpp": "cpp", "cs": "csharp",
    "go": "go", "rs": "rust", "rb": "ruby", "php": "php",
    "swift": "swift", "kt": "kotlin", "scala": "scala",
    "r": "r", "sh": "bash", "bat": "batch", "ps1": "powershell",
    "sql": "sql", "html": "html", "css": "css", "scss": "scss",
    "ipynb": "json", "thy": "isabelle", "dfy": "dafny",
}

CODE_CATEGORIES       = ("codigo-professor", "codigo-aluno")
ASSIGNMENT_CATEGORIES = ("trabalhos",)
WHITEBOARD_CATEGORIES = ("quadro-branco",)
STUDENT_BRANCHES      = {"main", "master", "minha-solucao", "aluno", "student"}

DEFAULT_OCR_LANGUAGE = "por,eng"

PROCESSING_MODES = ["auto", "quick", "high_fidelity", "manual_assisted"]
DOCUMENT_PROFILES = ["auto", "math_heavy", "diagram_heavy", "scanned"]
LEGACY_DOCUMENT_PROFILE_ALIASES = {
    "": "auto",
    "auto": "auto",
    "general": "auto",
    "math_light": "math_heavy",
    "math_heavy": "math_heavy",
    "layout_heavy": "diagram_heavy",
    "diagram_heavy": "diagram_heavy",
    "exam_pdf": "diagram_heavy",
    "scanned": "scanned",
}
PREFERRED_BACKENDS = ["auto", "pymupdf4llm", "pymupdf", "datalab", "docling", "docling_python", "marker"]
OCR_LANGS = ["por", "eng", "por,eng", "eng,por"]


def normalize_document_profile(profile: str | None) -> str:
    normalized = str(profile or "").strip().lower()
    return LEGACY_DOCUMENT_PROFILE_ALIASES.get(normalized, "auto")

# Utilities

def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or "untitled"

def collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()

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

def _is_aspnet_schedule(soup) -> bool:
    if soup.find(id="dgAulas"):
        return True
    import re as _re
    if soup.find("span", id=_re.compile(r"_lblData$")):
        return True
    return False


def _aspnet_row_cell(row, suffix: str) -> str:
    import re as _re
    span = row.find("span", id=_re.compile(rf"_lbl{suffix}$"))
    if not span:
        return ""
    return " ".join(span.get_text(" ", strip=True).split())


_ASPNET_COLOR_KIND_MAP = {
    "red": ("suspension", True),
    "#ff0000": ("suspension", True),
    "lightgrey": ("g2", True),
    "#d3d3d3": ("g2", True),
    "#ffa500": ("assessment", False),
    "orange": ("assessment", False),
    "#ff8c00": ("ps", True),
    "darkorange": ("ps", True),
    "#8b0000": ("event", True),
    "darkred": ("event", True),
    "#ffff00": ("deliverable", False),
    "yellow": ("deliverable", False),
}


def _aspnet_row_kind(row) -> tuple[str, bool]:
    """Return (kind, ignored) derived from row background-color. Default: ('class', False)."""
    style = (row.get("style") or "").lower().replace(" ", "")
    import re as _re
    match = _re.search(r"background-color:([^;]+)", style)
    if not match:
        return ("class", False)
    color = match.group(1).strip().rstrip(";")
    return _ASPNET_COLOR_KIND_MAP.get(color, ("class", False))


ATIVIDADE_KIND_MAP = {
    "prova": "assessment",
    "avaliacao": "assessment",
    "exame": "assessment",
    "teste": "assessment",
    "trabalho": "deliverable",
    "entrega": "deliverable",
    "feriado": "holiday",
    "revisao": "review",
}


def norm_ascii_lower(text: str) -> str:
    """NFKD + remove acentos + lower + strip. Para casar Atividade do SARC."""
    import unicodedata as _ud
    text = _ud.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not _ud.combining(ch))
    return text.lower().strip()


def _aspnet_row_canonical_kind(row) -> tuple[str, bool]:
    """Tipo canonico (valor de BlockKind) da linha SARC.

    Precedencia:
    1. Cor de EXCLUSAO (suspensao/ps/g2/evento) vence tudo: e a marcacao
       explicita do professor que a coluna Atividade nao expressa.
    2. Coluna Atividade (mapa de keywords) — sinal primario do tipo positivo.
    3. Atividade explicita nao-mapeada (ex.: "Aula") -> class, ignora cor.
    4. Atividade vazia -> cai para a cor positiva (assessment/deliverable).
    Retorna (kind, ignored).
    """
    color_kind, ignored = _aspnet_row_kind(row)
    if ignored:
        return (color_kind, True)
    atividade = norm_ascii_lower(_aspnet_row_cell(row, "Atividade"))
    for needle, kind in ATIVIDADE_KIND_MAP.items():
        if needle in atividade:
            return (kind, False)
    if atividade:
        return ("class", False)
    if color_kind != "class":
        return (color_kind, ignored)
    return ("class", False)


def _parse_aspnet_schedule(soup) -> str:
    table = soup.find(id="dgAulas") or soup.find("table")
    if not table:
        return "Erro: Tabela de cronograma ASP.NET nao encontrada."
    lines = ["## Cronograma de Aulas", ""]
    for row in table.find_all("tr"):
        data = _aspnet_row_cell(row, "Data")
        descricao = _aspnet_row_cell(row, "Descricao")
        if not data or not descricao:
            continue
        dia = _aspnet_row_cell(row, "Dia")
        atividade = _aspnet_row_cell(row, "Atividade") or "Aula"
        recursos = _aspnet_row_cell(row, "Recursos")
        kind, ignored = _aspnet_row_canonical_kind(row)

        parts = [f"- ({data})"]
        if dia:
            parts.append(dia)
        parts.append(f"— {descricao} [{atividade}]")
        if recursos:
            parts.append(f"@{recursos}")
        if kind != "class":
            parts.append(f"{{kind={kind}}}")
        if ignored:
            parts.append("⊘")
        lines.append(" ".join(parts))
    return "\n".join(lines) + "\n"


SARC_HOST = "sarc.pucrs.br"


def is_sarc_url(url: Optional[str]) -> bool:
    """Return True if `url` points to the SARC host (sarc.pucrs.br).

    Pure/testable domain check (UI responsibility, not the fetcher's).
    Accepts http/https and any subpath/query; compares the hostname
    exactly and case-insensitively (ignoring port) so suffix spoofs like
    `sarc.pucrs.br.evil.com` are rejected.
    """
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except (ValueError, AttributeError):
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return host == SARC_HOST


def decide_schedule_source(url: Optional[str], pasted_html: Optional[str]) -> dict:
    """Decide where the cronograma HTML comes from, given the dialog fields.

    Pure/testable: no network, no UI. Given the (possibly empty) SARC URL and
    the pasted HTML, returns a small dict describing the next action so the UI
    only has to obey it:
      {"action": "fetch", "url": <str>}      → fetch this URL on a thread
      {"action": "parse", "html": <str>}     → parse this HTML directly
      {"action": "cancel"}                   → both empty; nothing to do
      {"action": "error", "message": <str>}  → invalid URL; show message
    URL (when present) takes precedence over pasted HTML.
    """
    url = (url or "").strip()
    pasted_html = (pasted_html or "").strip()
    if url:
        if not is_sarc_url(url):
            return {
                "action": "error",
                "message": "URL inválida. Use uma URL do SARC (sarc.pucrs.br).",
            }
        return {"action": "fetch", "url": url}
    if pasted_html:
        return {"action": "parse", "html": pasted_html}
    return {"action": "cancel"}


def fetch_schedule_html(url: str) -> str:
    """GET `url` and return the raw HTML body.

    Single purpose: fetch only. Domain validation (see `is_sarc_url`) and
    parsing happen elsewhere. Raises on network/HTTP failure so the UI can
    translate it into a friendly message.

    Timeout uses the (connect, read) tuple pattern reused from
    datalab_client (timeout=(connect_to, ...)).
    """
    response = requests.get(url, timeout=(10, 30))
    response.raise_for_status()
    return response.text


def parse_html_schedule(html_content: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "Erro: A biblioteca 'beautifulsoup4' não está instalada.\nUse no terminal: pip install beautifulsoup4"

    soup = BeautifulSoup(html_content, "html.parser")

    if _is_aspnet_schedule(soup):
        return _parse_aspnet_schedule(soup)

    table = soup.find("table")
    if not table:
        return "Erro: Nenhuma tabela (<table>) encontrada no HTML fornecido."

    rows = table.find_all("tr")
    if not rows:
        return "Erro: A tabela não possui linhas (<tr>)."

    output = []

    header_cells = rows[0].find_all(["th", "td"])
    headers = [c.get_text(" ", strip=True) for c in header_cells]
    if not headers:
        return "Erro: Tabela sem colunas reconhecíveis."

    output.append("| " + " | ".join(headers) + " |")
    output.append("|" + "|".join(["---"] * len(headers)) + "|")

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
    ext = Path(name).suffix.lower()
    if ext in CODE_EXTENSIONS:
        return "codigo-professor"

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
