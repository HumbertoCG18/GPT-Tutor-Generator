"""Build inicial de um curso por CLI — o MESMO caminho da UI (perfil -> stash -> RepoBuilder.build).

    python scripts/build_course.py --name "Computação Gráfica" --repo <repo-dir> --stash <stash-dir> \\
        --syllabus-url "https://sarc.pucrs.br/Default/Export.aspx?id=...&ano=2026&sem=2" \\
        --teaching-plan-pdf <PlanoDeEnsino.pdf> \\
        [--professor ...] [--schedule "Ter/Qui 17:30 - 19:00"] [--semester 2026/2] [--moodle-course 95106] \\
        [--flags use_anchor_engine,use_llm_voter] [--dry-run]

O que faz, na ordem da UI (ui/app.py: Gerenciador de Materias -> Importar do stash -> Gerar):
  1. cria/atualiza o SubjectProfile no subjects.json (nome, professor, horario, syllabus = tabela SARC,
     teaching_plan = plano em markdown via pymupdf4llm, repo_root, stash_folder, moodle_course_id, defaults de
     extracao e feature_flags — sem `use_anchor_engine`/`use_llm_voter` o motor nem roda);
  2. scan_stash_cards + build_stash_entries com os defaults do perfil (pasta = card, como no export do Moodle);
  3. RepoBuilder(course_meta, entries, options=_build_options_from_config(AppConfig), subject_profile).build().
  Zero curadoria: nenhum pino, card manual, sidecar ou boundary_dates e criado. E o holdout.

--syllabus-url: o export HTML publico do SARC (F12, 2026-08-30) -> tabela markdown direto; imprime a TURMA do
cabecalho para conferencia (o link postado no Moodle pode ser de OUTRA turma — Lab SO 330 vs 310).
--syllabus-pdf: fallback quando o cronograma so existe em PDF (caso CG) -> tabela markdown por geometria:
fronteiras de coluna = celulas do find_tables, faixa vertical = cada data. Medido na CG: 38/38.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SARC_COLS = ["#", "Dia", "Data", "Hora", "Descrição", "Atividade", "Recursos"]


def sarc_html_to_table(html: str) -> tuple[str, str]:
    """Export HTML do SARC -> (tabela markdown SARC, turma do cabecalho). Linha = <tr> com data DD/MM/AAAA."""
    import html as _html
    import re as _re
    turma = ""
    m = _re.search(r"\((\d{3})\)", _re.sub(r"<[^>]+>", " ", html[:4000]))
    if m:
        turma = m.group(1)
    rows = []
    for r in _re.findall(r"<tr[^>]*>(.*?)</tr>", html, _re.S | _re.I):
        cells = [" ".join(_html.unescape(_re.sub(r"<[^>]+>", " ", c)).split())
                 for c in _re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, _re.S | _re.I)]
        if len(cells) >= 7 and _re.fullmatch(r"\d{2}/\d{2}/\d{4}", cells[2]):
            rows.append(cells[:7])
    if not rows:
        raise SystemExit("nenhuma linha com data no export HTML do SARC")
    out = ("| " + " | ".join(SARC_COLS) + " |\n| " + " | ".join("---" for _ in SARC_COLS) + " |\n"
           + "\n".join("| " + " | ".join(c.replace("|", "/") for c in r) + " |" for r in rows) + "\n")
    return out, turma


def sarc_pdf_to_table(pdf_path: Path) -> str:
    """Export do SARC (PDF) -> tabela markdown SARC (mesmo formato do SubjectProfile.syllabus dos outros cursos)."""
    import fitz  # pymupdf
    rows: list[list[str]] = []
    for page in fitz.open(str(pdf_path)):
        tabs = page.find_tables().tables
        if not tabs:
            continue
        t = tabs[0]
        first = [c for c in t.rows[0].cells if c]
        xb = sorted(set([c[0] for c in first] + [c[2] for c in first]))
        ncol = len(xb) - 1
        words = [w for w in page.get_text("words") if t.bbox[0] - 2 <= w[0] <= t.bbox[2] + 2 and t.bbox[1] <= w[1] <= t.bbox[3]]
        header_y = max((w[3] for w in words if w[4] in SARC_COLS), default=t.bbox[1])
        dates = sorted((w for w in words if re.fullmatch(r"\d{2}/\d{2}/\d{4}", w[4]) and w[1] > header_y), key=lambda w: w[1])
        ys = [(w[1] + w[3]) / 2 for w in dates]
        if not ys:
            continue
        yb = [(ys[i] + ys[i + 1]) / 2 for i in range(len(ys) - 1)]

        def col(x: float) -> int:
            for i in range(ncol):
                if x < xb[i + 1]:
                    return i
            return ncol - 1

        def band(y: float) -> int:
            for i, b in enumerate(yb):
                if y < b:
                    return i
            return len(ys) - 1

        cells = [[[] for _ in range(ncol)] for _ in ys]
        for w in sorted(words, key=lambda w: (round(w[1]), w[0])):
            if w[1] <= header_y:
                continue
            cells[band((w[1] + w[3]) / 2)][col((w[0] + w[2]) / 2)].append(w[4])
        rows.extend([" ".join(c) for c in r] for r in cells)
    if not rows:
        raise SystemExit(f"nenhuma tabela/data encontrada em {pdf_path}")
    cols = SARC_COLS[: len(rows[0])]
    return ("| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"
            + "\n".join("| " + " | ".join(r) + " |" for r in rows) + "\n")


def teaching_plan_md(pdf_path: Path) -> str:
    from src.utils.pdf_markdown import pdf_to_markdown  # mesmo conversor do botao "Extrair PDF" da UI
    return pdf_to_markdown(pdf_path)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name")
    ap.add_argument("--repo")
    ap.add_argument("--stash")
    ap.add_argument("--syllabus-pdf")
    ap.add_argument("--syllabus-url", help="URL do export HTML do SARC (Export.aspx...); PDF vira fallback")
    ap.add_argument("--syllabus-md", help="tabela SARC ja em markdown (alternativa ao PDF)")
    ap.add_argument("--teaching-plan-pdf")
    ap.add_argument("--teaching-plan-md", help="plano ja em markdown (alternativa ao PDF)")
    ap.add_argument("--args-json", help="JSON UTF-8 com os mesmos parametros (evita acentos corrompidos por Start-Process/cmd)")
    ap.add_argument("--professor", default="")
    ap.add_argument("--schedule", default="")
    ap.add_argument("--semester", default="")
    ap.add_argument("--moodle-course", default="")
    ap.add_argument("--mode", default="high_fidelity")
    ap.add_argument("--backend", default="datalab")
    ap.add_argument("--datalab-mode", default="balanced")
    ap.add_argument("--ocr-language", default="")
    ap.add_argument("--flags", default="use_anchor_engine,use_llm_voter")
    ap.add_argument("--dry-run", action="store_true", help="grava o perfil e lista as entries; NAO roda o build")
    args = ap.parse_args(argv)
    if args.args_json:
        import json
        for k, v in json.loads(Path(args.args_json).read_text(encoding="utf-8")).items():
            setattr(args, k.replace("-", "_"), v)

    from src.builder.core.stash_import import build_stash_entries, scan_stash_cards
    from src.builder.engine import RepoBuilder
    from src.models.core import SubjectProfile, SubjectStore
    from src.ui.app import _build_options_from_config
    from src.ui.theme import AppConfig
    from src.utils.helpers import DEFAULT_OCR_LANGUAGE, ensure_builtin_profiles, slugify

    if not (args.name and args.repo and args.stash):
        print("faltam --name/--repo/--stash (ou --args-json)"); return 2
    repo = Path(args.repo).resolve()
    stash = Path(args.stash).resolve()
    if not stash.is_dir():
        print(f"stash nao existe: {stash}")
        return 2
    store = SubjectStore()
    sp = store.get(args.name) or SubjectProfile(name=args.name)
    sp.slug = sp.slug or slugify(args.name)
    sp.professor = args.professor or sp.professor
    sp.schedule = args.schedule or sp.schedule
    sp.semester = args.semester or sp.semester
    sp.moodle_course_id = args.moodle_course or sp.moodle_course_id
    sp.repo_root = str(repo).replace("\\", "/")
    sp.stash_folder = str(stash)
    sp.default_mode, sp.default_backend, sp.default_datalab_mode = args.mode, args.backend, args.datalab_mode
    sp.default_ocr_lang = args.ocr_language or sp.default_ocr_lang or DEFAULT_OCR_LANGUAGE
    sp.feature_flags = {f.strip(): True for f in args.flags.split(",") if f.strip()}
    if args.syllabus_md:
        sp.syllabus = Path(args.syllabus_md).read_text(encoding="utf-8")
    elif args.syllabus_url:
        import urllib.request
        with urllib.request.urlopen(args.syllabus_url, timeout=60) as r:
            html = r.read().decode("utf-8", errors="replace")
        sp.syllabus, turma = sarc_html_to_table(html)
        print(f"[sarc] turma do export: ({turma or '?'}) — confira que e a SUA turma (Lab SO tinha 330 postado na 310)")
    elif args.syllabus_pdf:
        sp.syllabus = sarc_pdf_to_table(Path(args.syllabus_pdf))
    if args.teaching_plan_md:
        sp.teaching_plan = Path(args.teaching_plan_md).read_text(encoding="utf-8")
    elif args.teaching_plan_pdf:
        sp.teaching_plan = teaching_plan_md(Path(args.teaching_plan_pdf))
    store.add(sp)
    n_rows = max(0, len(sp.syllabus.splitlines()) - 2)
    print(f"[perfil] '{sp.name}' salvo em {store._path}: syllabus {n_rows} linhas, plano {len(sp.teaching_plan)} chars, flags {sp.feature_flags}")

    scan = scan_stash_cards(stash)
    entries = build_stash_entries(scan, existing_source_paths=set(), defaults={
        "processing_mode": sp.default_mode, "ocr_language": sp.default_ocr_lang, "preferred_backend": sp.default_backend,
        "datalab_mode": sp.default_datalab_mode, "document_profile": "",
    })
    cards = {}
    for e in entries:
        cards[e.source_section] = cards.get(e.source_section, 0) + 1
    print(f"[stash] {len(entries)} entries em {len(cards)} cards; {len(scan.skipped)} ignorado(s) por extensao: {[Path(s).name for s in scan.skipped][:6]}")
    for card, n in cards.items():
        print(f"    {n:3}  {card}")

    config = AppConfig()
    ensure_builtin_profiles(config)
    options = _build_options_from_config(sp.default_mode, sp.default_ocr_lang, config, subject=sp)
    meta = {"course_name": sp.name, "course_slug": sp.slug, "semester": sp.semester, "professor": sp.professor, "institution": sp.institution or "PUCRS"}
    print(f"[options] {', '.join(f'{k}={v}' for k, v in options.items() if k in ('default_processing_mode', 'image_description_source', 'skip_base_backends', 'use_anchor_engine', 'use_llm_voter'))}")
    if args.dry_run:
        print("[dry-run] build NAO executado.")
        return 0
    repo.mkdir(parents=True, exist_ok=True)
    builder = RepoBuilder(root_dir=repo, course_meta=meta, entries=entries, options=options, subject_profile=sp,
                          progress_callback=lambda i, n, title: print(f"  ({i + 1}/{n}) {title[:70]}", flush=True))
    builder.build()
    failed = list(getattr(builder, "failed_entries", []) or [])
    print(f"[build] concluido em {repo}: {len(entries) - len(failed)} ok, {len(failed)} falha(s)")
    for f in failed[:10]:
        print("   !!", str(f)[:160])
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
