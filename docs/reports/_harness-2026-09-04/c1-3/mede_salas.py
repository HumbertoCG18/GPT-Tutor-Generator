"""Medicao (read-only, 0 Gemini): SALAS DE ENTREGA nos 8 cursos, pela API do Moodle (mod_assign_get_assignments) x SARC dos tutores.
Funda as propostas C1-C5 (06/09): (C3) duracao abertura->vencimento separa atividade de aula x trabalho; (C5) vencimento x sessao do SARC;
(C1) quantos vencimentos caem em bloco de prova; (C4) anexos/enunciado das salas que o tutor nao tem. Nunca imprime o token.
Uso: mede_salas.py  -> log em stdout + salas_api.json (gitignored)"""
import datetime as d
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
C13 = GEN / "docs/reports/_harness-2026-09-04/c1-3"
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from scripts.moodle_token import ensure_moodle_token
    URL, TOK = ensure_moodle_token()
except Exception:
    from scripts.migrate_signals import load_moodle_token
    URL, TOK = load_moodle_token()
from src.builder.sources.moodle import MoodleClient  # noqa: E402

REPO = {"MF": ("Metodos-Formais-Tutor", "metodos formais"), "SO": ("Sistemas-Operacionais-Tutor", "sistemas operacionais"),
        "IA": ("Inteligencia-Artifical-Tutor", "inteligencia artificial"), "ES2": ("Engenharia-Software-2-Tutor", "engenharia de software ii"),
        "TCC": ("TCC-Tutor", "computabilidade"), "LR": ("Laboratorio-de-Redes-Tutor", "laboratorio de redes"),
        "CG": ("Computacao-Grafica-Tutor", "computacao grafica"), "FR": ("Fundamentos-de-Redes-Tutor", "fundamentos de redes")}


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()).strip()


def fdt(ts):
    return d.datetime.fromtimestamp(ts).strftime("%d/%m %H:%M") if ts else "-"


def classe(o, due):
    if not due:
        return "sem-vencimento"
    if not o:
        return "so-vencimento"
    h = (due - o) / 3600
    return "atividade-de-aula" if h <= 26 else ("curta" if h < 7 * 24 else "trabalho")


c = MoodleClient(URL, TOK)
uid = c.site_info().get("userid")
cursos = c.get_users_courses(uid)
escolha = {}
for sig, (repo, kw) in REPO.items():
    cands = [x for x in cursos if kw in norm(x.get("fullname")) and ("laboratorio" in kw or "laboratorio" not in norm(x.get("fullname")))]
    if cands:
        escolha[sig] = max(cands, key=lambda x: x.get("startdate") or 0)
print("cursos:", {s: f"{x['id']} {x['fullname'][:34]}" for s, x in escolha.items()})
params = {f"courseids[{i}]": x["id"] for i, x in enumerate(escolha.values())}
res = c._call("mod_assign_get_assignments", **params)
by_course = {course["id"]: course for course in res.get("courses", [])}
warn = Counter(w.get("message") for w in (res.get("warnings") or []))
print("warnings da API:", dict(warn))

OUT = {}
TOT = Counter()
for sig, (repo, _) in REPO.items():
    if sig not in escolha:
        print(f"\n== {sig}: curso nao encontrado na conta")
        continue
    course = by_course.get(escolha[sig]["id"], {})
    root = GH / repo
    ti = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]
    blocks = sorted(ti, key=lambda b: str(b.get("period_start") or ""))
    contents = json.loads((root / "raw/moodle/contents.json").read_text(encoding="utf-8")) if (root / "raw/moodle/contents.json").exists() else []
    sec_of = {m.get("id"): s.get("name") for s in contents for m in (s.get("modules") or [])}
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    stems = {norm(Path(str(e.get("source_path") or "")).stem): e for e in man}
    cbm = json.loads((root / "course/.card_block_map.json").read_text(encoding="utf-8")) if (root / "course/.card_block_map.json").exists() else {}
    file_dues = {norm(Path(f).stem): v for card in cbm.values() if isinstance(card, dict) for f, v in (card.get("file_dues") or {}).items()}

    def bloco_de(ts):
        if not ts:
            return None
        day = d.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        for b in blocks:
            if str(b.get("period_start") or "") <= day <= str(b.get("period_end") or ""):
                return b
        prev = [b for b in blocks if str(b.get("period_start") or "") <= day]
        return prev[-1] if prev else None

    rows = []
    print(f"\n== {sig} ({repo}): {len(course.get('assignments', []))} salas · arquivos com vencimento no card_block_map: {len(file_dues)}")
    for a in sorted(course.get("assignments", []), key=lambda a: a.get("duedate") or 0):
        o, due, cut = a.get("allowsubmissionsfromdate") or 0, a.get("duedate") or 0, a.get("cutoffdate") or 0
        cl = classe(o, due)
        b = bloco_de(due)
        blabel = " | ".join(str(s.get("label"))[:30] for s in (b.get("sessions") or [])[:2]) if b else ""
        sarc_ok = bool(re.search(r"entrega|apresenta|trabalho|\bt[1-3]\b|tp[1-3]|prova", norm(blabel)))
        att = [f.get("filename") for f in (a.get("introattachments") or [])]
        att_no_tutor = [f for f in att if norm(Path(f).stem) not in stems]
        sec = sec_of.get(a.get("cmid"))
        row = {"nome": a.get("name"), "secao": sec, "cmid": a.get("cmid"), "abertura": fdt(o), "vencimento": fdt(due), "fechamento": fdt(cut),
               "classe": cl, "intro_chars": len(a.get("intro") or ""), "anexos": att, "anexos_fora_do_tutor": att_no_tutor,
               "bloco": b.get("id") if b else None, "bloco_kind": b.get("kind") if b else None, "bloco_label": blabel, "sarc_nomeia_entrega": sarc_ok,
               "fileurls": [f.get("fileurl") for f in (a.get("introattachments") or [])]}
        rows.append(row)
        TOT[f"classe {cl}"] += 1; TOT["salas"] += 1; TOT["anexos"] += len(att); TOT["anexos fora do tutor"] += len(att_no_tutor)
        if b:
            TOT[f"vencimento em bloco {b.get('kind')}"] += 1
            if cl == "trabalho":
                TOT["trabalho: SARC nomeia entrega/prova"] += sarc_ok
        print(f"   {str(a.get('name'))[:34]:34} sec={str(sec)[:16]!r:18} abre={fdt(o):11} vence={fdt(due):11} fecha={fdt(cut):5} {cl:17} "
              f"bloco={b.get('id') if b else '-':8} {str(b.get('kind') if b else '-'):11} sarc={'sim' if sarc_ok else 'nao'} '{blabel[:34]}' anexos={att[:2]}{' (FORA do tutor)' if att_no_tutor else ''} intro={len(a.get('intro') or '')}")
    # materiais que o motor ja liga a um vencimento (D-G): categoria e bloco do vencimento
    cats = Counter()
    for stem, v in file_dues.items():
        e = stems.get(stem)
        cats[str(e.get("category")) if e else "(sem entry)"] += 1
    print(f"   arquivos com vencimento (card_block_map): categorias {dict(cats)}")
    OUT[sig] = rows
print("\n[TOTAL]", dict(TOT))
(C13 / "salas_api.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("salas_api.json gravado (gitignored)")
