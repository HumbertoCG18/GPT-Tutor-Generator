"""Cliente da Moodle Web Services API (mobile app token) — fonte primária de cards.

Seção do Moodle = card do gabarito. Baixa <dest>/<seção>/<arquivo> direto do
ambiente do professor. O stash manual segue como fallback.

Acesso é à conta do PRÓPRIO aluno (token escopado mobile); perm de aluno.
Só stdlib.
"""
from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.utils.helpers import slugify, write_json_manifest

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

logger = logging.getLogger(__name__)

import re as _re

_COURSE_PROF_RE = _re.compile(r"\bProf\.?\s*(.+)$", _re.IGNORECASE)
_COURSE_SEM_RE = _re.compile(r"\b(20\d{2}/[12])\b")


def parse_moodle_course(course: dict) -> dict:
    """Extrai campos de SubjectProfile do fullname Moodle.

    Padrão: "CODE - Nome - Turma NNN - YYYY/S - Prof. Fulano". Robusto a faltas.
    """
    full = str(course.get("fullname") or "").strip()
    cid = str(course.get("id") or "")
    professor = ""
    m = _COURSE_PROF_RE.search(full)
    if m:
        professor = m.group(1).strip()
    semester = ""
    m = _COURSE_SEM_RE.search(full)
    if m:
        semester = m.group(1)
    turma = ""
    m_t = _re.search(r"Turmas?\s+(\d{3}\b(?:\s*-\s*\d{3}\b)*)", full, _re.IGNORECASE)
    if m_t:
        turma = _re.sub(r"\s+", " ", m_t.group(1)).strip()
    # corta o tail estrutural (Turma/semestre/Prof) e remove o código inicial.
    m_turma = _re.search(r"\s*-\s*Turma\b", full, _re.IGNORECASE)
    head = full[:m_turma.start()] if m_turma else full
    hp = head.split(" - ", 1)
    name = hp[1].strip() if len(hp) >= 2 else head.strip()
    return {
        "moodle_course_id": cid,
        "name": name,
        "professor": professor,
        "semester": semester,
        "slug": slugify(name) if name else (slugify(str(course.get("shortname") or "")) or cid),
        "shortname": str(course.get("shortname") or ""),
        "turma": turma,
    }


def sanitize_folder_name(name: str) -> str:
    name = _INVALID.sub(" ", str(name or ""))
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "sem-secao"


# Assinatura (magic bytes) por extensão. Defesa em profundidade: mesmo que o
# servidor minta o content-type, um corpo que não casa com a extensão (ex.: JSON
# de "token inválido" salvo como .pdf) é rejeitado em vez de gravar corrompido.
_FILE_SIGNATURES = {
    ".pdf": (b"%PDF",),
    ".zip": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
    ".docx": (b"PK\x03\x04",), ".pptx": (b"PK\x03\x04",), ".xlsx": (b"PK\x03\x04",),
    ".odt": (b"PK\x03\x04",), ".odp": (b"PK\x03\x04",), ".ods": (b"PK\x03\x04",),
    ".doc": (b"\xd0\xcf\x11\xe0",), ".ppt": (b"\xd0\xcf\x11\xe0",), ".xls": (b"\xd0\xcf\x11\xe0",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",), ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".rtf": (b"{\\rtf",),
    ".gz": (b"\x1f\x8b",), ".rar": (b"Rar!",), ".7z": (b"7z\xbc\xaf\x27\x1c"),
}


def looks_like_expected(filename: str, data: bytes) -> bool:
    """True se os primeiros bytes casam com a extensão (ou extensão desconhecida).

    Extensão sem assinatura conhecida -> True (não dá pra validar; confia no
    guard de content-type). Conhecida e divergente -> False (não grava)."""
    ext = Path(filename).suffix.lower()
    sigs = _FILE_SIGNATURES.get(ext)
    if not sigs:
        return True
    return any(data.startswith(s) for s in sigs)


@dataclass(frozen=True)
class SectionFile:
    section: str
    filename: str          # nome ORIGINAL do conteúdo Moodle (ex.: "main.pdf") — usado no backfill
    fileurl: str
    savename: str = ""     # nome p/ disco, derivado do título do módulo (resolve colisão de "main.pdf")
    label: str = ""        # mod.get("name") — label do recurso no Moodle (alavanca 1)
    timemodified: int = 0  # epoch do upload/modificacao no Moodle (posting_date) — S0, nao consumido
    timecreated: int = 0   # epoch de criacao do blob no Moodle

    @property
    def disk_name(self) -> str:
        return self.savename or self.filename


def _savename_from_module(modname: str, original: str, n_in_module: int) -> str:
    """Nome de disco a partir do título do módulo, preservando a extensão.

    Módulo com 1 arquivo -> '<título>.<ext>'. Com vários -> '<título> - <original>'
    (evita colisão interna). Título vazio -> nome original."""
    base = sanitize_folder_name(modname) if str(modname or "").strip() else ""
    if not base:
        return original
    ext = Path(original).suffix
    return f"{base}{ext}" if n_in_module == 1 else f"{base} - {original}"


def iter_section_files(contents) -> List[SectionFile]:
    out: List[SectionFile] = []
    for sec in contents or []:
        section = sanitize_folder_name(str(sec.get("name") or ""))
        for mod in sec.get("modules", []) or []:
            file_contents = [f for f in (mod.get("contents", []) or [])
                             if f.get("type") == "file" and f.get("filename") and f.get("fileurl")]
            for f in file_contents:
                original = str(f["filename"])
                savename = _savename_from_module(mod.get("name"), original, len(file_contents))
                out.append(SectionFile(section, original, str(f["fileurl"]), savename,
                                       label=str(mod.get("name") or ""),
                                       timemodified=int(f.get("timemodified") or 0),
                                       timecreated=int(f.get("timecreated") or 0)))
    return out


def backfill_moodle_label_from_api(manifest_entries, contents):
    """Casa entries -> label do recurso Moodle (mod.name) por basename, mesma
    mecânica do source_section. Retorna {id->moodle_label}. Basename em >1 módulo
    (colisão de filename) -> pulado (igual ao ambiguous do source_section)."""
    from collections import Counter
    counts = Counter()
    label_by_name = {}
    for sf in iter_section_files(contents):
        key = sf.filename.casefold()
        counts[key] += 1
        if sf.label:
            label_by_name.setdefault(key, sf.label)
    out = {}
    for e in manifest_entries or []:
        eid = str(e.get("id") or "")
        base = Path(str(e.get("source_path") or "")).name.casefold()
        if base in label_by_name and counts[base] == 1:
            out[eid or base] = label_by_name[base]
    return out


def posting_date_iso(ts) -> str:
    """Converte epoch -> "YYYY-MM-DD" UTC. Inválido/<=0 -> ""."""
    from datetime import datetime, timezone
    try:
        n = int(ts)
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    return datetime.fromtimestamp(n, tz=timezone.utc).strftime("%Y-%m-%d")


def backfill_posting_date_from_api(manifest_entries, contents):
    """Casa entries -> {timemodified, timecreated} por basename UNICO (igual ao
    source_section). Basename em >1 modulo -> pulado (ambiguo)."""
    from collections import Counter
    counts = Counter()
    ts_by_name = {}
    for sf in iter_section_files(contents):
        key = sf.filename.casefold()
        counts[key] += 1
        if (sf.timemodified or sf.timecreated):
            ts_by_name.setdefault(key, {"timemodified": sf.timemodified,
                                        "timecreated": sf.timecreated})
    out = {}
    for e in manifest_entries or []:
        eid = str(e.get("id") or "")
        base = Path(str(e.get("source_path") or "")).name.casefold()
        if base in ts_by_name and counts[base] == 1:
            out[eid or base] = ts_by_name[base]
    return out


def section_file_index(contents) -> dict:
    """{casefold(filename): section} a partir de core_course_get_contents (metadados)."""
    idx = {}
    for sf in iter_section_files(contents):
        idx.setdefault(sf.filename.casefold(), sf.section)
    return idx


def section_file_index_strict(contents) -> tuple:
    """({basename.casefold(): secao} só de basenames únicos, {ambíguos}).

    Basename presente em >1 seção sai do dict — ambíguo é miss e o chamador
    decide o fallback (cf. spec 2026-06-11-m365-card-mapping)."""
    secs: dict = {}
    for sf in iter_section_files(contents):
        secs.setdefault(sf.filename.casefold(), set()).add(sf.section)
    index = {k: next(iter(v)) for k, v in secs.items() if len(v) == 1}
    ambiguous = {k for k, v in secs.items() if len(v) > 1}
    return index, ambiguous


def backfill_source_section_from_api(manifest_entries, contents):
    """Casa entries do manifest com as seções da API por basename (case-insensitive).

    Retorna (assignments {id->section}, unmatched [ids], ambiguous [ids]).
    Basename presente em >1 seção -> ambiguous.
    """
    from collections import Counter
    counts = Counter()
    sec_by_name = {}
    for sf in iter_section_files(contents):
        key = sf.filename.casefold()
        counts[key] += 1
        sec_by_name.setdefault(key, sf.section)
    assignments, unmatched, ambiguous = {}, [], []
    for e in manifest_entries or []:
        eid = str(e.get("id") or "")
        base = Path(str(e.get("source_path") or "")).name.casefold()
        if base not in sec_by_name:
            unmatched.append(eid or base)
            continue
        if counts[base] > 1:
            ambiguous.append(eid or base)
            continue
        assignments[eid or base] = sec_by_name[base]
    return assignments, unmatched, ambiguous


class MoodleClient:
    def __init__(self, base_url: str, token: str):
        self.base = str(base_url).rstrip("/")
        self._token = token

    def _call(self, wsfunction: str, **params):
        url = self.base + "/webservice/rest/server.php"
        data = {"wstoken": self._token, "wsfunction": wsfunction,
                "moodlewsrestformat": "json", **{k: str(v) for k, v in params.items()}}
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode("utf-8"), method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8"))
        if isinstance(payload, dict) and payload.get("exception"):
            raise RuntimeError(f"Moodle [{payload.get('errorcode')}]: {payload.get('message')}")
        return payload

    def site_info(self):
        return self._call("core_webservice_get_site_info")

    def get_users_courses(self, userid):
        return self._call("core_enrol_get_users_courses", userid=userid)

    def get_course_contents(self, courseid):
        return self._call("core_course_get_contents", courseid=courseid)

    def _download_url(self, fileurl: str) -> str:
        parts = urllib.parse.urlparse(fileurl)
        q = dict(urllib.parse.parse_qsl(parts.query))
        q["token"] = self._token
        return urllib.parse.urlunparse(parts._replace(query=urllib.parse.urlencode(q)))

    @staticmethod
    def login(base_url: str, username: str, password: str) -> str:
        """Troca matrícula+senha pelo wstoken (mobile). Senha só transita aqui."""
        url = str(base_url).rstrip("/") + "/login/token.php?service=moodle_mobile_app"
        body = urllib.parse.urlencode({"username": username, "password": password}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8"))
        if not isinstance(payload, dict) or not payload.get("token"):
            # NÃO repassar payload["error"] bruto — pode conter eco de credencial.
            raise RuntimeError("Falha no login Moodle (verifique matrícula/senha ou se o serviço mobile está habilitado).")
        return str(payload["token"])

    def download_course(self, courseid, dest, skip_existing: bool = True) -> dict:
        dest = Path(dest)
        files = iter_section_files(self.get_course_contents(courseid))
        downloaded = skipped = 0
        failed = []
        seen: set = set()   # targets gravados nesta execução — evita perda silenciosa por colisão
        for sf in files:
            folder = dest / sf.section
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / sf.disk_name
            # Colisão dentro desta execução (dois módulos -> mesmo nome): desambigua.
            if target in seen:
                stem, suf = target.stem, target.suffix
                i = 2
                while (folder / f"{stem} ({i}){suf}") in seen:
                    i += 1
                target = folder / f"{stem} ({i}){suf}"
            seen.add(target)
            if skip_existing and target.exists():
                skipped += 1
                continue
            try:
                with urllib.request.urlopen(self._download_url(sf.fileurl), timeout=120) as r:
                    ctype = (r.headers.get("content-type") or "").lower()
                    data = r.read()
                # Moodle erros e redirects M365 vêm como JSON/HTML — não são o arquivo.
                if ctype.startswith("text/html") or ctype.startswith("application/json"):
                    failed.append(sf.filename)
                    continue
                # Defesa em profundidade: content-type pode mentir. Valida magic bytes.
                if not looks_like_expected(sf.filename, data):
                    failed.append(sf.filename)
                    continue
                target.write_bytes(data)
                downloaded += 1
            except Exception:
                failed.append(sf.filename)
        return {"total": len(files), "downloaded": downloaded, "skipped": skipped, "failed": failed}


def latest_semester(courses) -> str:
    """Retorna o semestre mais recente encontrado nos cursos (ex: '2026/1')."""
    sems = [parse_moodle_course(c)["semester"] for c in (courses or [])]
    sems = [s for s in sems if s]
    return max(sems) if sems else ""


def filter_courses_by_semester(courses, semester) -> list:
    """Filtra cursos pelo semestre informado. Se semester vazio, retorna todos."""
    if not semester:
        return list(courses or [])
    return [c for c in (courses or []) if parse_moodle_course(c)["semester"] == semester]


def build_card_structure(stash_dir, contents) -> dict:
    """Cria <stash_dir>/<seção>/ + _ARQUIVOS_DO_CARD.txt (lista esperada). Sem bytes."""
    stash_dir = Path(stash_dir)
    by_section: dict = {}
    for sf in iter_section_files(contents):
        by_section.setdefault(sf.section, []).append(sf.disk_name)
    folders = 0
    expected = 0
    for section, names in by_section.items():
        folder = stash_dir / section
        folder.mkdir(parents=True, exist_ok=True)
        folders += 1
        expected += len(names)
        listing = "Arquivos esperados neste card (baixe do Moodle e coloque aqui):\n\n" + "\n".join(names) + "\n"
        (folder / "_ARQUIVOS_DO_CARD.txt").write_text(listing, encoding="utf-8")
    return {"folders": folders, "expected_files": expected}


def find_subject_for_course(store, course):
    """Acha o SubjectProfile da matéria: moodle_course_id > slug > nome.

    Mesma precedência do upsert de import_moodle_courses; usado também pela UI
    (persistir m365_filter no perfil certo — antes o lookup por nome falhava
    em silêncio quando o nome do store divergia do nome vindo do Moodle)."""
    info = parse_moodle_course(course)
    cid = info["moodle_course_id"]
    match_by_slug = None
    for n in store.names():
        sp = store.get(n)
        if not sp:
            continue
        if cid and getattr(sp, "moodle_course_id", "") == cid:
            return sp
        if not match_by_slug and getattr(sp, "slug", "") and sp.slug == info["slug"]:
            match_by_slug = sp
    return match_by_slug or store.get(info["name"])


def backfill_repo_signals_additive(repo_root, contents, info, write: bool = True) -> dict:
    """Backfill que NAO muda atribuicao: moodle_label (fill-if-empty), posting_date,
    .lessons_index.json, e meta turma/schedule_url. Grava in-place se write."""
    import json as _json
    repo = Path(repo_root)
    mpath = repo / "manifest.json"
    if not mpath.is_file():
        return {"labels": 0, "posting": 0, "lessons": 0}
    manifest = _json.loads(mpath.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    labels = backfill_moodle_label_from_api(entries, contents)
    posting = backfill_posting_date_from_api(entries, contents)
    n_lab = n_post = 0
    for e in entries:
        eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
        if labels.get(eid) and not str(e.get("moodle_label") or "").strip():
            e["moodle_label"] = labels[eid]
            n_lab += 1
        if eid in posting:
            e["posting_date"] = posting_date_iso(posting[eid]["timemodified"])
            e["posting_date_created"] = posting_date_iso(posting[eid]["timecreated"])
            n_post += 1
    if info.get("turma"):
        manifest["turma"] = info["turma"]
    if info.get("schedule_url"):
        manifest["schedule_url"] = info["schedule_url"]
    if write:
        write_json_manifest(mpath, manifest)
    n_lessons = 0
    try:
        from src.builder.sources.moodle_labels import build_lesson_topic_index
        year = int((info.get("semester") or "0/0").split("/")[0] or 0)
        lessons_index = build_lesson_topic_index(contents, year)
        if lessons_index.get("by_date") and write:
            (repo / "course" / ".lessons_index.json").write_text(
                _json.dumps(lessons_index, ensure_ascii=False, indent=1), encoding="utf-8")
            n_lessons = len(lessons_index["by_date"])
    except Exception:
        logger.warning("lessons_index falhou para %s", info.get("name"), exc_info=True)
    return {"labels": n_lab, "posting": n_post, "lessons": n_lessons}


def backfill_repo_signals_consumed(repo_root, contents, info, write: bool = True) -> dict:
    """Backfill que MUDA atribuicao: source_section (overwrite) + card_block_map/assign_due.
    Usado pelo import normal e pelo S0b (eval-gated). Grava in-place se write."""
    import json as _json
    repo = Path(repo_root)
    mpath = repo / "manifest.json"
    if not mpath.is_file():
        return {"sections": 0, "card_labels": 0}
    manifest = _json.loads(mpath.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    assignments, _u, _a = backfill_source_section_from_api(entries, contents)
    n_sec = 0
    for e in entries:
        eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
        if eid in assignments:
            e["source_section"] = assignments[eid]
            n_sec += 1
    if write:
        write_json_manifest(mpath, manifest)
    n_card = 0
    try:
        from src.builder.sources.moodle_labels import (
            parse_card_dates, derive_card_block_map, merge_card_block_map,
            extract_assign_deadlines,
        )
        ti_path = repo / "course" / ".timeline_index.json"
        map_path = repo / "course" / ".card_block_map.json"
        if ti_path.is_file():
            blocks = (_json.loads(ti_path.read_text(encoding="utf-8")) or {}).get("blocks") or []
            year = int((info.get("semester") or "0/0").split("/")[0] or 0)
            derived = derive_card_block_map(parse_card_dates(contents, year), blocks)
            for _card, _due in extract_assign_deadlines(contents, year).items():
                if _card in derived:
                    derived[_card]["assign_due"] = _due
                else:
                    derived[_card] = {"block_ids": [], "source": "labels", "assign_due": _due}
            existing = _json.loads(map_path.read_text(encoding="utf-8")) if map_path.is_file() else {}
            merged = merge_card_block_map(existing, derived)
            if merged != existing and write:
                map_path.write_text(_json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
            n_card = sum(1 for _ in derived.values())
    except Exception:
        logger.warning("card_block_map via labels falhou para %s", info.get("name"), exc_info=True)
    return {"sections": n_sec, "card_labels": n_card}


def import_moodle_courses(selected_courses, base_folder, store, client, download: bool = False) -> dict:
    """Upsert de SubjectProfile + estrutura de cards + backfill do manifest.

    store: objeto com .names()/.get(name)/.add(profile).
    client: objeto com .get_course_contents(courseid) e .download_course(courseid, dest).
    download: se True, baixa os bytes via client.download_course (default False).
    """
    import json as _json
    from src.models.core import SubjectProfile
    base = Path(base_folder)
    created = updated = linked = 0
    folders = expected_files = backfilled = downloaded = 0
    card_map_labels = card_map_manual = 0
    failed: list = []
    for course in selected_courses or []:
        info = parse_moodle_course(course)
        cid = info["moodle_course_id"]
        stash = str(base / info["slug"])
        # --- upsert (id -> slug -> create) ---
        sp = find_subject_for_course(store, course)
        match_by_id = sp if (sp is not None and cid and getattr(sp, "moodle_course_id", "") == cid) else None
        match_by_slug = sp if (sp is not None and match_by_id is None and getattr(sp, "slug", "") == info["slug"]) else None
        if match_by_id is not None:
            sp = match_by_id
            sp.stash_folder = stash
            if not sp.professor:
                sp.professor = info["professor"]
            store.add(sp)
            updated += 1
        elif match_by_slug is not None:
            sp = match_by_slug
            sp.moodle_course_id = cid
            sp.stash_folder = stash                # NÃO toca repo_root (preserva)
            if not sp.professor:
                sp.professor = info["professor"]
            store.add(sp)
            linked += 1
        else:
            sp = SubjectProfile(
                name=info["name"], slug=info["slug"], professor=info["professor"],
                semester=info["semester"], moodle_course_id=cid, stash_folder=stash,
            )
            store.add(sp)
            created += 1
        # --- metadados: estrutura de cards + backfill ---
        contents = client.get_course_contents(cid)
        st = build_card_structure(base / info["slug"], contents)
        folders += st["folders"]
        expected_files += st["expected_files"]
        sp.turma = info.get("turma", "") or getattr(sp, "turma", "")
        repo = getattr(sp, "repo_root", "") or ""
        if repo and (Path(repo) / "manifest.json").is_file():
            info_repo = {**info, "turma": sp.turma, "schedule_url": getattr(sp, "schedule_url", "")}
            add = backfill_repo_signals_additive(repo, contents, info_repo, write=True)
            con = backfill_repo_signals_consumed(repo, contents, info_repo, write=True)
            backfilled += con["sections"]
            card_map_labels += con["card_labels"]
        if download:
            dl = client.download_course(cid, stash)
            downloaded += int(dl.get("downloaded", 0))
            failed += list(dl.get("failed", []))
    return {
        "created": created, "updated": updated, "linked": linked,
        "folders": folders, "expected_files": expected_files,
        "backfilled": backfilled, "downloaded": downloaded, "failed": failed,
        "card_map_labels": card_map_labels, "card_map_manual": card_map_manual,
    }


_DEFAULT_MOODLE_URL = "https://moodle.pucrs.br"


def default_token_path() -> Path:
    return Path(__file__).resolve().parents[3] / "moddle" / ".env"


def _read_dotenv(path) -> dict:
    out = {}
    p = Path(path)
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _moodle_env(key, dotenv_path=None):
    """Precedência: os.environ (carregado do .env raiz por helpers no import) >
    moddle/.env. Consolida com os demais segredos do projeto.

    Quando `dotenv_path` é passado EXPLICITAMENTE (testes), lê só esse arquivo —
    os.environ não interfere."""
    if dotenv_path is not None:
        return _read_dotenv(dotenv_path).get(key, "").strip()
    import os
    val = (os.environ.get(key) or "").strip()
    if val:
        return val
    return _read_dotenv(default_token_path()).get(key, "").strip()


def load_moodle_token(dotenv_path=None):
    url = _moodle_env("MOODLE_URL", dotenv_path) or _DEFAULT_MOODLE_URL
    token = _moodle_env("MOODLE_TOKEN", dotenv_path)
    return url, token


def save_moodle_token(token: str, url: str = "", dotenv_path=None) -> None:
    path = Path(dotenv_path) if dotenv_path else default_token_path()
    existing_url, _ = load_moodle_token(dotenv_path=path)
    final_url = url or existing_url or _DEFAULT_MOODLE_URL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"MOODLE_URL={final_url}\nMOODLE_TOKEN={token}\n", encoding="utf-8")
