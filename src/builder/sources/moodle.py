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
        for sf in files:
            folder = dest / sf.section
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / sf.filename
            if skip_existing and target.exists():
                skipped += 1
                continue
            with urllib.request.urlopen(self._download_url(sf.fileurl), timeout=120) as r:
                target.write_bytes(r.read())
            downloaded += 1
        return {"total": len(files), "downloaded": downloaded, "skipped": skipped}


def import_moodle_courses(selected_courses, base_folder, store, client) -> dict:
    """Upsert de SubjectProfile + download do stash por curso selecionado.

    store: objeto com .names()/.get(name)/.add(profile).
    client: objeto com .download_course(courseid, dest).
    """
    from src.models.core import SubjectProfile
    base = Path(base_folder)
    created = updated = downloaded_files = 0
    for course in selected_courses or []:
        info = parse_moodle_course(course)
        cid = info["moodle_course_id"]
        existing_name = None
        for n in store.names():
            sp = store.get(n)
            if sp and getattr(sp, "moodle_course_id", "") == cid and cid:
                existing_name = n
                break
        stash = str(base / info["slug"])
        if existing_name:
            sp = store.get(existing_name)
            sp.stash_folder = stash
            sp.moodle_course_id = cid
            if not sp.professor:
                sp.professor = info["professor"]
            store.add(sp)
            updated += 1
        else:
            sp = SubjectProfile(
                name=info["name"], slug=info["slug"], professor=info["professor"],
                semester=info["semester"], moodle_course_id=cid, stash_folder=stash,
            )
            store.add(sp)
            created += 1
        summary = client.download_course(cid, stash)
        downloaded_files += int(summary.get("downloaded", 0))
    return {"created": created, "updated": updated, "downloaded_files": downloaded_files}


_DEFAULT_MOODLE_URL = "https://moodle.pucrs.br"


def default_token_path() -> Path:
    return Path(__file__).resolve().parents[3] / "moddle" / ".env"


def load_moodle_token(dotenv_path=None):
    path = Path(dotenv_path) if dotenv_path else default_token_path()
    url, token = _DEFAULT_MOODLE_URL, ""
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k == "MOODLE_URL" and v:
                url = v
            elif k == "MOODLE_TOKEN":
                token = v
    return url, token


def save_moodle_token(token: str, url: str = "", dotenv_path=None) -> None:
    path = Path(dotenv_path) if dotenv_path else default_token_path()
    existing_url, _ = load_moodle_token(dotenv_path=path)
    final_url = url or existing_url or _DEFAULT_MOODLE_URL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"MOODLE_URL={final_url}\nMOODLE_TOKEN={token}\n", encoding="utf-8")
