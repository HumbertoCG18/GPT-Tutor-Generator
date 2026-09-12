"""C3 (provas, listas, trabalhos) x C5 (dividas de dados): qual campanha tem mais massa e mais erro? 0 chamadas.

O user (08/09) aceitou promover a C5 "se fundamentado com dados reais". A recomendacao anterior media o alvo da C5 e
NAO media o da C3 — este script mede os dois na mesma base, nos 8 tutores.

C3 = categorias provas, listas, trabalhos, gabaritos.
C5 = dividas de dados medidas: material sem texto, texto minusculo, texto so de links, zips com nomes colidindo,
     extensao ignorada, e materiais sem gold de unidade (a divida de regua).
Uso: compara_c3_c5.py
"""
import collections
import csv as _csv
import json
import re
import sys
import zipfile
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
TODOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
         "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
C3_CATS = {"provas", "listas", "trabalhos", "gabaritos"}
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder import engine as eng  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

LINK = re.compile(r"\]\((https?://[^)\s]+)\)")


def golds(sig):
    p = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
    gb = load_labels_csv(p) if p.exists() else {}
    gu = _load_truth(sig) if sig in UNI else {}
    p = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    gs = {}
    if p.exists():
        for r in _csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
            if r["scorable"] == "yes":
                gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
    return gb, gu, gs


CAT = collections.defaultdict(lambda: collections.Counter())
DIV = collections.Counter()
DET_ZIP = collections.Counter()
for sig, repo in TODOS.items():
    root = GH / repo
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    ti = {}
    for b in json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]
        ti[b["id"]] = b["id"]
    gb, gu, gs = golds(sig)
    nomes_zip = collections.Counter()
    for e in man:
        if not _is_material(e):
            continue
        cat = str(e.get("category") or "?").strip().lower()
        grupo = "C3: provas/listas/trabalhos" if cat in C3_CATS else "resto"
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        c = CAT[grupo]
        c["n"] += 1
        c[f"cat:{cat}"] += 1
        err = []
        eid = e["id"]
        if eid in gb:
            c["nb"] += 1
            ok = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "") == gb[eid]
            c["ob"] += ok
            err += [] if ok else ["b"]
        if eid in gu:
            c["nu"] += 1
            ok = str(e.get("computed_unit_slug") or "") == gu[eid]
            c["ou"] += ok
            err += [] if ok else ["u"]
        if eid in gs:
            c["ns"] += 1
            ok = str(e.get("computed_subunit_slug") or "") in gs[eid]
            c["os"] += ok
            err += [] if ok else ["s"]
        if eid in gb or eid in gu or eid in gs:
            c["cg"] += 1
            c["errado"] += bool(err)
        c["fila"] += revisar_de(e) in ("duvida", "mudou")
        # --- dividas de dados (C5)
        if not md.strip():
            DIV["sem texto nenhum"] += 1
        elif len(md) < 200:
            DIV["texto < 200 chars"] += 1
        links = LINK.findall(md)
        if links and len(LINK.sub(" ", md)) < 0.55 * max(1, len(md)):
            DIV["texto quase so links"] += 1
        arq = str(e.get("source_path") or e.get("path") or e.get("filename") or "")
        if arq.lower().endswith(".zip") and Path(arq).exists():
            try:
                with zipfile.ZipFile(arq) as z:
                    for nome in z.namelist():
                        base = Path(nome).name
                        if base:
                            nomes_zip[base] += 1
            except Exception:
                pass
    col = sum(v - 1 for v in nomes_zip.values() if v > 1)
    if col:
        DET_ZIP[sig] = col
        DIV["nomes de membro colidindo entre zips"] += col
    if sig not in UNI:
        DIV[f"materiais sem gold de unidade ({sig})"] += len([e for e in man if _is_material(e)])

print("A) MASSA E ERRO POR GRUPO (8 tutores)")
print(f"{'grupo':32} {'materiais':>10} {'com gold':>9} {'errados':>8} {'% erro':>7} {'fila':>6}")
for g in ("C3: provas/listas/trabalhos", "resto"):
    c = CAT[g]
    print(f"{g:32} {c['n']:10} {c['cg']:9} {c['errado']:8} {100 * c['errado'] / max(1, c['cg']):6.0f}% {c['fila']:6}")
print()
for g in ("C3: provas/listas/trabalhos", "resto"):
    c = CAT[g]
    cats = {k[4:]: v for k, v in c.items() if k.startswith("cat:")}
    print(f"  {g}: {dict(sorted(cats.items(), key=lambda x: -x[1]))}")
    print(f"     bloco {c['ob']}/{c['nb']} · unidade {c['ou']}/{c['nu']} · subunidade {c['os']}/{c['ns']}")

print("\nB) DIVIDAS DE DADOS MEDIDAS (alvo da C5)")
for k, v in DIV.most_common():
    print(f"   {k:44} {v:5}")
print(f"   colisao de nome por curso: {dict(DET_ZIP)}")

print("\nC) LEITURA")
c3, resto = CAT["C3: provas/listas/trabalhos"], CAT["resto"]
print(f"   C3 cobre {c3['n']} de {c3['n'] + resto['n']} materiais ({100 * c3['n'] / (c3['n'] + resto['n']):.0f}%) e "
      f"carrega {c3['errado']} dos {c3['errado'] + resto['errado']} erros "
      f"({100 * c3['errado'] / max(1, c3['errado'] + resto['errado']):.0f}%).")
