import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.helpers import get_app_data_dir, slugify


@dataclass
class FileEntry:
    source_path: str
    file_type: str  # pdf or image or url
    category: str
    title: str
    tags: str = ""
    notes: str = ""
    professor_signal: str = ""
    relevant_for_exam: bool = True
    include_in_bundle: bool = True

    # V3 fields
    processing_mode: str = "auto"
    document_profile: str = "auto"
    preferred_backend: str = "auto"
    formula_priority: bool = False
    preserve_pdf_images_in_markdown: bool = True
    force_ocr: bool = False
    export_page_previews: bool = True
    extract_images: bool = True
    extract_tables: bool = True
    page_range: str = ""
    ocr_language: str = "por,eng"

    def id(self) -> str:
        if self.file_type == "url":
            return slugify(self.title)
        return slugify(Path(self.source_path).stem)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "FileEntry":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class DocumentProfileReport:
    page_count: int = 0
    text_chars: int = 0
    images_count: int = 0
    table_candidates: int = 0
    text_density: float = 0.0
    suspected_scan: bool = False
    suggested_profile: str = "general"
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
    default_ocr_lang: str = "por,eng"
    repo_root: str = ""
    queue: List[FileEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, any]:
        d = asdict(self)
        # Ensure queue is serialized correctly
        d["queue"] = [e.to_dict() for e in self.queue]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, any]) -> "SubjectProfile":
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
    semester: str = ""           # "3º semestre"
    institution: str = "PUCRS"
    personality: str = ""        # Como o GPT deve ajudar (texto livre)

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "StudentProfile":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in valid})


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
        except Exception:
            pass

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
        except Exception:
            pass

    def save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self.profile.to_dict(), f, indent=2, ensure_ascii=False)
