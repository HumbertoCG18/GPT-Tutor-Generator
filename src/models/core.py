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
    manual_subunit_slug: str = ""
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

    # Sinais de match persistidos no manifest.json (gravados por
    # resolve_unit_block_tags). Declarados aqui para o round-trip from_dict ->
    # to_dict parar de descarta-los silenciosamente.
    unit_match_confidence: float = 0.0
    unit_match_reasons: List[str] = field(default_factory=list)
    subunit_match_confidence: float = 0.0
    subunit_match_reasons: List[str] = field(default_factory=list)

    # Atribuicao first-class (Fase 1). Resolve "tudo e parse de tag": o slug/id
    # resolvido vive direto no entry, e auto_tags[unit:|bloco:] sao espelho
    # destes campos (escritos por resolve_unit_block_tags).
    computed_unit_slug: str = ""
    # Melhor candidato de subunidade (best-effort, pode estar abaixo do gate de
    # tag). Declarado aqui para sobreviver ao round-trip from_dict -> to_dict
    # (antes era descartado, deixando subunit_match_confidence orfa). A tag
    # subunit: (gated) continua sendo a atribuicao; este campo e a sugestao.
    computed_subunit_slug: str = ""
    computed_block_id: str = ""
    computed_block_confidence: float = 0.0
    # Faixa ("alta"/"media"/"baixa") derivada de computed_block_confidence via
    # thresholds.confidence_band; "" quando nao ha bloco atribuido.
    computed_block_band: str = ""
    # Justificativa do Gemini (code summarizer) para a escolha de bloco.
    # Copiada de code_curation.json (summary.match_rationale) na regeneração
    # pedagógica; "" para entries sem summary (não-código).
    computed_block_rationale: str = ""
    # Método e confiança do match code->bloco, do code summarizer (Gemini +
    # matcher local). Copiados de code_curation.json (summary.block_match_method
    # / block_match_confidence) na regeneração pedagógica; default vazio/0.0 para
    # entries sem summary (não-código). Distinto de computed_block_confidence
    # (acima), que é a confiança do routing determinístico.
    computed_block_method: str = ""
    computed_block_match_confidence: float = 0.0
    # Bloco TEMPORAL (cronograma) resolvido pela camada de âncora, ADITIVO e
    # disjunto de computed_block_id (KB). Escrito SÓ com flag use_anchor_placement
    # e method anchor/manual; "" (omitido do to_dict) quando scorer ou flag OFF
    # -> resolve_temporal_block cai no fallback resolve_effective_block. NUNCA
    # alimenta file->card/unit (não re-conflaciona temporal vs KB).
    temporal_block_id: str = ""
    temporal_block_method: str = ""
    # Card/seção de origem do arquivo (= subpasta imediata no stash). Sinal
    # autoritativo para a atribuição file->bloco (gabarito-cards). "" quando o
    # arquivo nao veio de um card (cai no caminho lexical, sem regressao).
    source_section: str = ""
    # Label do recurso no Moodle (= mod.get("name") do core_course_get_contents,
    # ex. "Exemplos (Lógica de Floyd-Hoare)"). Capturado no import (backfill da API)
    # ANTES do redirect SharePoint que deixa só o filename. Identidade LIMPA do
    # material — pesa como conceito no resolver. NUNCA sobrescreve title. ""=ausente.
    moodle_label: str = ""
    # Data de upload/postagem (ISO YYYY-MM-DD) do timemodified Moodle/M365.
    # Capturada no import (S0). NAO consumida pela atribuicao (consumo = A2).
    # ""=ausente (HTML sem timestamp, ou fonte sem data).
    posting_date: str = ""
    posting_date_created: str = ""   # ISO do timecreated (diagnostico do probe)
    # Conflito unidade×bloco detectado no auto (F1): a unidade forte (>=0.65)
    # venceu um bloco que apontava OUTRA unidade (block_confidence < unit_conf).
    # {} quando não há conflito. Sinal de revisão exibido no editor; o build
    # mantém a unidade forte. Distinto da herança silenciosa (que não é conflito).
    unit_block_conflict: dict = field(default_factory=dict)
    # Override do id (bug B5): setado pelo import quando o id computado do
    # source_path colide com entry de OUTRO source_path. Quando não-vazio,
    # id() retorna este valor — assim assets/raw/manifest usam o id final
    # consistente desde o início do processamento. Persistido no manifest
    # (to_dict omite quando vazio; from_dict restaura), então releituras
    # mantêm o id deduplicado em vez de recomputar do source_path.
    id_override: str = ""

    def id(self) -> str:
        if self.id_override:
            return self.id_override
        if self.file_type == "url":
            import hashlib
            base = slugify(self.title) or "url"
            url_hash = hashlib.md5(self.source_path.encode()).hexdigest()[:6]
            return f"{base}-{url_hash}"
        return slugify(Path(self.source_path).stem)

    def to_dict(self) -> Dict:
        from dataclasses import fields as _fields, MISSING
        full = asdict(self)
        out: Dict = {}
        for f in _fields(self):
            val = full[f.name]
            if f.default is not MISSING:
                default = f.default
            elif f.default_factory is not MISSING:  # type: ignore[misc]
                default = f.default_factory()       # type: ignore[misc]
            else:
                out[f.name] = val  # required: sempre presente
                continue
            if val != default:
                out[f.name] = val
        return out

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
    image_curation: Optional[dict] = None


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
    default_backend: str = "auto"          # backend de extração padrão da matéria
    default_datalab_mode: str = "accurate"  # modo da API Datalab (fast/balanced/accurate)
    processing_profile: str = ""   # nome do preset ProcessingProfile (referência)
    repo_root: str = ""
    stash_folder: str = ""        # pasta com os arquivos-fonte (PDFs/cards) da materia
    moodle_course_id: str = ""   # liga a matéria ao curso Moodle (re-sync, upsert)
    m365_filter: str = ""        # substring do path OneDrive p/ filtrar insights (M365)
    turma: str = ""              # turma(s) do curso Moodle (ex.: "031"); registro, nao scoped (S0)
    schedule_url: str = ""       # URL do SARC Export.aspx (GUID/ano/sem da turma); registro (S0)
    github_url: str = ""           # URL base do repo no GitHub
    preferred_llm: str = "claude"  # Plataforma principal: "claude", "gpt", "gemini"
    # Flags de feature por matéria (durável). Ausente/{} → todas False. Injetadas
    # nas builder.options por _build_options_from_config. Liga capacidades wired
    # atrás de flag (ex.: use_anchor_placement) sem schema novo por flag.
    feature_flags: Dict[str, bool] = field(default_factory=dict)
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
class ProcessingProfile:
    """Preset reutilizável de processamento (referenciado por nome pela matéria)."""
    name: str = ""
    processing_mode: str = "auto"
    preferred_backend: str = "auto"
    datalab_mode: str = "accurate"
    document_profile: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProcessingProfile":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (d or {}).items() if k in valid})


@dataclass
class StudentProfile:
    """Perfil do aluno — exportado nos repositórios gerados."""
    full_name: str = ""
    nickname: str = ""           # Como o GPT chama o aluno
    personality: str = ""        # Como o GPT deve ajudar (texto livre)
    moodle_base_folder: str = ""  # pasta-base dos stashes baixados do Moodle

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
