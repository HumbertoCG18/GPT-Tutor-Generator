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

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


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
            msg = payload.get("error") if isinstance(payload, dict) else "resposta inválida"
            raise RuntimeError(f"Falha no login Moodle: {msg}")
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
