"""Passo 3 (C1 item 3): para cada leitor de `title` SOZINHO no motor, quantas entries dos 8 mudam de saida com title := label."""
import sys, json, copy
from pathlib import Path
GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator"); GH = GEN.parent
sys.path.insert(0, str(GEN)); sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.routing.motor import window_provider as wp, anchor_engine as ae, due_window as dw, disambiguator as dis
from src.builder.routing import file_map as fm, concept_resolver as cr
from src.builder.text.normalize import normalize_match_text
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "LR": "Laboratorio-de-Redes-Tutor",
        "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}
def label(e):
    ml = e.get("moodle_label"); return (ml.get("text", "") if isinstance(ml, dict) else str(ml or "")).strip()
def ordinal(e):
    o = wp.extract_lecture_ordinal(normalize_match_text(str(e.get("title") or "")))
    return o if o is not None else wp.extract_lecture_ordinal(normalize_match_text(str(e.get("raw_target") or "")))
READERS = {
    "window_provider:226 ordinal": ordinal,
    "anchor_engine:125 _exam_number": ae._exam_number,
    "anchor_engine:142 is_exam_prep": ae.is_exam_prep_material,
    "due_window:92/97 _stems(title+id)": lambda e: dw._stems(f"{e.get('title') or ''} {e.get('id') or ''}"),
    "concept_resolver:385 extract_dates(title)": lambda e: tuple(cr.extract_dates(str(e.get("title") or ""), default_year=2026, dm_two_digit_only=True)),
    "file_map:230 _REVISAO_RE(title+id)": lambda e: bool(fm._REVISAO_RE.search(f"{e.get('title') or ''} {e.get('id') or ''}")),
    "file_map:446 explicit_unit_number": fm.explicit_unit_number,
    "file_map:1092 split_camel_case(title) tokens": lambda e: dis._toks(fm.split_camel_case(str(e.get("title") or ""))),
    "disambiguator:70 entry_tokens (title+label, conjunto)": lambda e: dis.entry_tokens(e),
}
tot = {k: 0 for k in READERS}; ex = {k: [] for k in READERS}; n_rw = 0; n_all = 0
for sig, repo in REPO.items():
    m = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))
    for e in m["entries"]:
        n_all += 1
        ml = label(e)
        if not ml or ml == str(e.get("title") or ""):
            continue
        n_rw += 1
        e2 = copy.deepcopy(e); e2["title"] = ml
        for k, f in READERS.items():
            a, b = f(e), f(e2)
            if a != b:
                tot[k] += 1
                if len(ex[k]) < 4: ex[k].append(f"{sig}:{e['id'][:28]} {a!r}->{b!r}"[:110])
print(f"entries reescritas (label existe e != title): {n_rw}/{n_all}")
for k in READERS:
    print(f"  {k:52} muda em {tot[k]:3}  {' | '.join(ex[k])}")
