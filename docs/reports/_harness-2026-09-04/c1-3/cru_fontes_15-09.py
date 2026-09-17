"""Reconstrói pelo import de stash da UI, sem herdar manifest ou derivados do tutor."""
import argparse
import collections
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
COURSES = {
    "MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor",
    "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
    "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
    "FR": "Fundamentos-de-Redes-Tutor",
}
CALLS = collections.Counter()


def blocked(*args, **kwargs):
    CALLS["network"] += 1
    raise RuntimeError("REDE BLOQUEADA: cru desde as fontes")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curso", choices=COURSES, required=True)
    parser.add_argument("--destino", required=True)
    parser.add_argument("--inventario", action="store_true")
    parser.add_argument("--sem-descricao-html", action="store_true")
    args = parser.parse_args()
    parent = (ROOT / args.destino).resolve()
    allowed = (ROOT / ".frzero").resolve()
    if parent == allowed or not parent.is_relative_to(allowed):
        parser.error("destino precisa estar sob .frzero")
    dest = parent / COURSES[args.curso]
    if dest.exists():
        parser.error("destino do curso ja existe")

    socket.socket.connect = blocked
    socket.create_connection = blocked
    from src.builder.runtime import gemini_client, datalab_client
    gemini_client.get_gemini_client = lambda config=None: None
    gemini_client.GeminiClient.__init__ = blocked
    datalab_client.convert_document_to_markdown = blocked
    from src.builder import engine
    from src.builder.core.stash_import import scan_stash_cards, build_stash_entries
    from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _topic_text
    from src.models.core import SubjectStore
    from src.ui.app import _build_options_from_config
    from src.ui.theme import AppConfig

    engine.convert_document_to_markdown = blocked
    if args.sem_descricao_html:
        from src.builder.core import html_material
        html_material.HTML_IMAGE_DATALAB_CAP = 0
    store = SubjectStore()
    profiles = [store.get(n) for n in store.names()]
    profile = copy.deepcopy(next(p for p in profiles if Path(p.repo_root).name == COURSES[args.curso]))
    stash = Path(profile.stash_folder).resolve()
    if not stash.is_dir():
        raise FileNotFoundError(stash)
    phrases = []
    for title, topics in _parse_units_from_teaching_plan(profile.teaching_plan):
        phrases.append(title.lower())
        phrases.extend(_topic_text(t).lower() for t in topics)
    scan = scan_stash_cards(stash, frases_do_plano=[p for p in phrases if len(p) >= 6])
    # quick + backend base são escolhas locais da UI; impedem fallback para APIs/modelos.
    entries = build_stash_entries(scan, existing_source_paths=set(), defaults={
        "processing_mode": "quick", "ocr_language": profile.default_ocr_lang,
        "preferred_backend": "pymupdf4llm", "document_profile": "auto",
    })
    inputs = [{"path": item.source_path, "sha256": digest(Path(item.source_path)),
               "card": item.card_name, "moodle_label": item.moodle_label,
               "file_type": item.file_type, "category": item.category} for item in scan.items]
    moodle = stash.parent / "raw/moodle/contents.json"
    names = stash / ".moodle_nomes.json"
    metadata_sources = [p for p in (moodle, names) if p.is_file()]
    record = {
        "course": args.curso, "stash": str(stash), "inputs": inputs,
        "skipped": scan.skipped,
        "metadata_sources": [{"path": str(p), "sha256": digest(p)} for p in metadata_sources],
        "profile_input": {key: getattr(profile, key) for key in (
            "name", "slug", "professor", "institution", "semester", "syllabus", "teaching_plan")},
        "policy": "stash + perfil salvo + Moodle bruto; sem queue/curadoria/derivados do produto",
        "html_image_cap": 0 if args.sem_descricao_html else "default",
    }
    print(f"[{args.curso}] inventario={len(entries)} tipos={dict(collections.Counter(e.file_type for e in entries))} metadata={[p.name for p in metadata_sources]}", flush=True)
    if args.inventario:
        print(json.dumps(record, ensure_ascii=False))
        return 0
    dest.mkdir(parents=True, exist_ok=False)
    (dest / "_inputs_15-09.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    if moodle.is_file():
        target = dest / "raw/moodle/contents.json"
        target.parent.mkdir(parents=True)
        shutil.copy2(moodle, target)
    profile.queue = []
    profile.repo_root = str(dest)
    profile.feature_flags = {**(profile.feature_flags or {}), "use_llm_voter": False,
                             "compile_vocabulary": False}
    options = _build_options_from_config("quick", profile.default_ocr_lang, AppConfig(), subject=profile)
    options.update({"marker_use_llm": False, "image_description_source": "none",
                    "skip_base_backends": False, "profile_backends": {},
                    "prevent_sleep_during_build": False})
    meta = {"course_name": profile.name, "course_slug": profile.slug, "semester": profile.semester,
            "professor": profile.professor, "institution": profile.institution}
    start = time.time()
    builder = engine.RepoBuilder(
        root_dir=dest, course_meta=meta, entries=entries, options=options, subject_profile=profile,
        progress_callback=lambda i, n, title: print(f"[{args.curso}] {i}/{n} {title[:65]}", flush=True),
    )
    completed = False
    try:
        builder.build()
        completed = True
    finally:
        summary = {"seconds": round(time.time() - start, 2), "calls": dict(CALLS),
                   "failed_entries": builder.failed_entries, "completed": completed}
        (dest / "_build_result_15-09.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{args.curso}] resultado={summary}", flush=True)
    if CALLS:
        raise RuntimeError(f"tentativas de rede: {dict(CALLS)}")
    # Detecta alterações de fonte durante o build; jamais restaura/sobrescreve a origem.
    assert all(digest(Path(item["path"])) == item["sha256"] for item in inputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
