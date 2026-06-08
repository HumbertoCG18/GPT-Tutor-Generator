"""Cliente da Moodle Web Services API (mobile app token) — fonte primária de cards.

Seção do Moodle = card do gabarito. Baixa <dest>/<seção>/<arquivo> direto do
ambiente do professor. O stash manual segue como fallback.

Acesso é à conta do PRÓPRIO aluno (token escopado mobile); perm de aluno.
Só stdlib.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.utils.helpers import slugify

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

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
    }


def sanitize_folder_name(name: str) -> str:
    name = _INVALID.sub(" ", str(name or ""))
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "sem-secao"


@dataclass(frozen=True)
class SectionFile:
    section: str
    filename: str
    fileurl: str


def iter_section_files(contents) -> List[SectionFile]:
    out: List[SectionFile] = []
    for sec in contents or []:
        section = sanitize_folder_name(str(sec.get("name") or ""))
        for mod in sec.get("modules", []) or []:
            for f in mod.get("contents", []) or []:
                if f.get("type") == "file" and f.get("filename") and f.get("fileurl"):
                    out.append(SectionFile(section, str(f["filename"]), str(f["fileurl"])))
    return out


def section_file_index(contents) -> dict:
    """{casefold(filename): section} a partir de core_course_get_contents (metadados)."""
    idx = {}
    for sf in iter_section_files(contents):
        idx.setdefault(sf.filename.casefold(), sf.section)
    return idx


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
        for sf in files:
            folder = dest / sf.section
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / sf.filename
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
        by_section.setdefault(sf.section, []).append(sf.filename)
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
    failed: list = []
    for course in selected_courses or []:
        info = parse_moodle_course(course)
        cid = info["moodle_course_id"]
        stash = str(base / info["slug"])
        # --- upsert (id -> slug -> create) ---
        match_by_id = None
        match_by_slug = None
        for n in store.names():
            sp = store.get(n)
            if not sp:
                continue
            if cid and getattr(sp, "moodle_course_id", "") == cid:
                match_by_id = sp
                break
            if not match_by_slug and getattr(sp, "slug", "") and sp.slug == info["slug"]:
                match_by_slug = sp
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
        repo = getattr(sp, "repo_root", "") or ""
        if repo and (Path(repo) / "manifest.json").is_file():
            mpath = Path(repo) / "manifest.json"
            manifest = _json.loads(mpath.read_text(encoding="utf-8"))
            entries = manifest.get("entries", [])
            assignments, _u, _a = backfill_source_section_from_api(entries, contents)
            if assignments:
                for e in entries:
                    eid = str(e.get("id") or "") or Path(str(e.get("source_path") or "")).name
                    if eid in assignments:
                        e["source_section"] = assignments[eid]
                        backfilled += 1
                mpath.with_suffix(".json.apibak").write_text(
                    mpath.read_text(encoding="utf-8"), encoding="utf-8"
                )
                mpath.write_text(_json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        if download:
            dl = client.download_course(cid, stash)
            downloaded += int(dl.get("downloaded", 0))
            failed += list(dl.get("failed", []))
    return {
        "created": created, "updated": updated, "linked": linked,
        "folders": folders, "expected_files": expected_files,
        "backfilled": backfilled, "downloaded": downloaded, "failed": failed,
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


def load_moodle_private_token(dotenv_path=None) -> str:
    return _moodle_env("MOODLE_PRIVATE_TOKEN", dotenv_path)


def save_moodle_token(token: str, url: str = "", dotenv_path=None) -> None:
    path = Path(dotenv_path) if dotenv_path else default_token_path()
    existing_url, _ = load_moodle_token(dotenv_path=path)
    final_url = url or existing_url or _DEFAULT_MOODLE_URL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"MOODLE_URL={final_url}\nMOODLE_TOKEN={token}\n", encoding="utf-8")
