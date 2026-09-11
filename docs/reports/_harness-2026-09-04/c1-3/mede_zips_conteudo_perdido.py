"""Decisao 5, 0 chamadas: quantos membros de zip mostram conteudo de OUTRO zip.
process_zip grava raw/code/<sub>/<id-do-membro>.<ext> so pelo nome-base, entao o ultimo zip vence.
Compara o original em staging/zip-extract/<zip>/<membro> com o sobrevivente em raw/. Uso: python mede_zips_conteudo_perdido.py"""
import hashlib, json
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
T = {"CG": "Computacao-Grafica-Tutor", "ES2": "Engenharia-Software-2-Tutor", "MF": "Metodos-Formais-Tutor",
     "IA": "Inteligencia-Artifical-Tutor", "FR": "Fundamentos-de-Redes-Tutor", "SO": "Sistemas-Operacionais-Tutor"}
def h(p): return hashlib.sha1(p.read_bytes()).hexdigest()
print(f"{'curso':4} {'zips':>5} {'membros':>7} {'md distintos':>12} {'sobrescritos':>12} {'conteudo perdido':>16} {'zips com perda':>14}")
tot = [0] * 6
for sig, nome in T.items():
    root = REPO.parent / nome
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    zips = membros = perdido = 0; mds = set(); zips_perda = set()
    for e in man:
        if e.get("file_type") != "zip": continue
        zips += 1
        for f in e.get("extracted_files") or []:
            membros += 1; mds.add(f.get("base_markdown"))
            title = str(f.get("title", "")).replace("\\", "/")
            stg = root / "staging" / "zip-extract" / e["id"] / title
            bm = Path(str(f.get("base_markdown") or ""))
            raw = root / "raw" / "code" / bm.parent.name / (bm.stem + Path(title).suffix.lower())
            if stg.is_file() and raw.is_file() and h(stg) != h(raw):
                perdido += 1; zips_perda.add(e["id"])
    row = [zips, membros, len(mds), membros - len(mds), perdido, len(zips_perda)]
    tot = [a + b for a, b in zip(tot, row)]
    print(f"{sig:4} {row[0]:5} {row[1]:7} {row[2]:12} {row[3]:12} {row[4]:16} {row[5]:14}")
print(f"{'tot':4} {tot[0]:5} {tot[1]:7} {tot[2]:12} {tot[3]:12} {tot[4]:16} {tot[5]:14}")
assert tot[4] > 0, "se deu 0, ou a colisao foi corrigida ou o staging sumiu — conferir antes de acreditar"
