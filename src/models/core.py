import json
import logging
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from src.utils.helpers import DEFAULT_OCR_LANGUAGE, get_app_data_dir, normalize_document_profile, slugify


def _normalize_tag_list(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        values = raw
    else:
        values = str(raw).replace(",", ";").split(";")
    cleaned: List[str] = []
    seen = set()
    for value in values:
        tag = str(value).strip()
        if not tag or tag in seen:
            continue
        cleaned.append(tag)
        seen.add(tag)
    return cleaned


def _should_migrate_legacy_tags(file_type: str, raw_tags: str) -> bool:
    text = (raw_tags or "").strip()
    if not text:
        return False
    if file_type in {"code", "github-repo"}:
        return False
    return ":" in text or ";" in text or "," in text


@dataclass
class FileEntry:
    source_path: str
    file_type: str  # pdf or image or url
    category: str
    title: str
    tags: str = ""
    manual_tags: List[str] = field(default_factory=list)
    auto_tags: List[str] = field(default_factory=list)
    manual_unit_slug: str = ""
    manual_timeline_block_id: str = ""
    notes: str = ""
    professor_signal: str = ""
    relevant_for_exam: bool = True
    include_in_bundle: bool = True

    # V3 fields
    processing_mode: str = "auto"
    document_profile: str = "auto"
    preferred_backend: str = "auto"
    datalab_mode: str = "accurate"
    formula_priority: bool = False
    preserve_pdf_images_in_markdown: bool = True
    force_ocr: bool = False
    extract_images: bool = True
    extract_tables: bool = True
    page_range: str = ""
    ocr_language: str = DEFAULT_OCR_LANGUAGE
    enabled: bool = True

    def id(self) -> str:
        if self.file_type == "url":
            import hashlib
            base = slugify(self.title) or "url"
            url_hash = hashlib.md5(self.source_path.encode()).hexdigest()[:6]
            return f"{base}-{url_hash}"
        return slugify(Path(self.source_path).stem)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "FileEntry":
        valid = {f.name for f in fields(cls)}
        payload = {k: v for k, v in d.items() if k in valid}
        manual_tags = _normalize_tag_list(payload.get("manual_tags"))
        auto_tags = _normalize_tag_list(payload.get("auto_tags"))
        legacy_tags = str(payload.get("tags", "") or "").strip()
        file_type = str(payload.get("file_type", "") or "").strip().lower()
        payload["document_profile"] = normalize_document_profile(payload.get("document_profile"))
        if not manual_tags and _should_migrate_legacy_tags(file_type, legacy_tags):
            manual_tags = _normalize_tag_list(legacy_tags)
        payload["manual_tags"] = manual_tags
        payload["auto_tags"] = auto_tags
        return cls(**payload)


@dataclass
class DocumentProfileReport:
    page_count: int = 0
    text_chars: int = 0
    images_count: int = 0
    table_candidates: int = 0
    text_density: float = 0.0
    suspected_scan: bool = False
    suggested_profile: str = "auto"
    notes: List[str] = field(default_factory=list)


@dataclass
class BackendRunResult:
    name: str
    layer: str
    status: str
    markdown_path: Optional[str] = None
    asset_dir: Optional[str] = None
    metadata_path: Optional[str] = None
    command: Optional[List[str]] = None
    notes: List[str] = field(default_factory=list)
    error: Optional[str] = None
    images_dir: Optional[str] = None


@dataclass
class PipelineDecision:
    entry_id: str
    processing_mode: str
    effective_profile: str
    base_backend: Optional[str]
    advanced_backend: Optional[str]
    reasons: List[str] = field(default_factory=list)


@dataclass
class SubjectProfile:
    """Perfil salvo de uma matéria — preenche automaticamente os campos da disciplina."""
    name: str = ""
    slug: str = ""
    professor: str = ""
    institution: str = "PUCRS"
    semester: str = ""
    schedule: str = ""           # "Seg/Qua 10:15-11:55"
    syllabus: str = ""           # Cronograma multilinea
    teaching_plan: str = ""      # Plano de ensino (Ementa, Objetivos, Metodologia)
    default_mode: str = "auto"
    default_ocr_lang: str = DEFAULT_OCR_LANGUAGE
    repo_root: str = ""
    github_url: str = ""           # URL base do repo no GitHub
    preferred_llm: str = "claude"  # Plataforma principal: "claude", "gpt", "gemini"
    queue: List[FileEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Ensure queue is serialized correctly
        d["queue"] = [e.to_dict() for e in self.queue]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SubjectProfile":
        valid = {f.name for f in fields(cls)}
        # Pre-process queue
        queue_raw = d.get("queue", [])
        # Construct with other fields
        filtered = {k: v for k, v in d.items() if k in valid and k != "queue"}
        sp = cls(**filtered)
        sp.queue = [FileEntry.from_dict(item) for item in queue_raw]
        return sp


@dataclass
class StudentProfile:
    """Perfil do aluno — exportado nos repositórios gerados."""
    full_name: str = ""
    nickname: str = ""           # Como o GPT chama o aluno
    personality: str = ""        # Como o GPT deve ajudar (texto livre)

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "StudentProfile":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class PendingOperation:
    """Estado persistido de uma operação pausada/interrompida para retomar depois."""

    operation_type: str = ""          # "build" | "single"
    requested_mode: str = ""          # "full" | "incremental" | "single"
    repo_root: str = ""
    course_meta: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    active_subject: str = ""
    selected_entry_source: str = ""
    shutdown_after_build: bool = False
    entries: List[FileEntry] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["entries"] = [e.to_dict() for e in self.entries]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PendingOperation":
        valid = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in d.items() if k in valid and k != "entries"}
        op = cls(**filtered)
        op.entries = [FileEntry.from_dict(item) for item in d.get("entries", [])]
        return op


class SubjectStore:
    """Persistência de perfis de matérias em JSON."""

    def __init__(self):
        self._path = get_app_data_dir() / "subjects.json"
        self._data: Dict[str, SubjectProfile] = {}
        self.load()

    def load(self):
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                for k, v in raw.items():
                    self._data[k] = SubjectProfile.from_dict(v)
        except Exception as e:
            logger.warning("Failed to load subjects from %s: %s", self._path, e)

    def save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump({k: v.to_dict() for k, v in self._data.items()}, f, indent=2, ensure_ascii=False)

    def get(self, name: str) -> Optional[SubjectProfile]:
        return self._data.get(name)

    def add(self, p: SubjectProfile):
        self._data[p.name] = p
        self.save()

    def delete(self, name: str):
        if name in self._data:
            del self._data[name]
            self.save()

    def names(self) -> List[str]:
        return sorted(list(self._data.keys()))


class StudentStore:
    """Persistência única do perfil do aluno em JSON."""

    def __init__(self):
        self._path = get_app_data_dir() / "student.json"
        self.profile = StudentProfile()
        self.load()

    def load(self):
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                d = json.load(f)
                self.profile = StudentProfile.from_dict(d)
        except Exception as e:
            logger.warning("Failed to load student profile from %s: %s", self._path, e)

    def save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self.profile.to_dict(), f, indent=2, ensure_ascii=False)


class PendingOperationStore:
    """Persistência simples do estado de retomada do app."""

    def __init__(self):
        self._path = get_app_data_dir() / "pending_operation.json"

    def load(self) -> Optional[PendingOperation]:
        if not self._path.exists():
            return None
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return PendingOperation.from_dict(json.load(f))
        except Exception as e:
            logger.warning("Failed to load pending operation from %s: %s", self._path, e)
            return None

    def save(self, op: PendingOperation) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(op.to_dict(), f, indent=2, ensure_ascii=False)

    def clear(self) -> None:
        try:
            if self._path.exists():
                self._path.unlink()
        except Exception as e:
            logger.warning("Failed to clear pending operation %s: %s", self._path, e)
