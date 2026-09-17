"""Plano 08/09 item 2.3 (medido em 11/09, 0 chamadas): nos materiais em `conflito` (texto aponta uma unidade, bloco aponta
outra; o bloco vence por desenho), quem acerta contra o gold de unidade? `unit_block_conflict` guarda a unidade do texto
(`{"unit": ...}`), `computed_unit_slug` e a decisao (do bloco). Uso: python mede_conflito_unidade.py"""
import ast
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = Path(__file__).resolve().parent
src = (H / "calibra_fila_como_regua.py").read_text(encoding="utf-8")
mod = ast.parse(src)
keep = [n for n in mod.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign)) or (isinstance(n, ast.FunctionDef) and n.name == "golds")]
ns = {}
exec(compile(ast.Module(body=keep, type_ignores=[]), "calibra", "exec"), ns)

TUTORES = {"CG": "Computacao-Grafica-Tutor", "ES2": "Engenharia-Software-2-Tutor", "FR": "Fundamentos-de-Redes-Tutor",
           "IA": "Inteligencia-Artifical-Tutor", "LR": "Laboratorio-de-Redes-Tutor", "MF": "Metodos-Formais-Tutor",
           "SO": "Sistemas-Operacionais-Tutor", "TCC": "TCC-Tutor"}
total = com_gold = bloco_certo = texto_certo = 0
print(f"{'curso':5} {'material':46} {'bloco decidiu':34} {'texto queria':34} {'gold':34} veredito")
for sig, repo in TUTORES.items():
    man = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    gu = ns["golds"](sig)[1] if sig in ns["UNI"] else {}
    for e in man:
        c = e.get("unit_block_conflict")
        if not c:
            continue
        total += 1
        texto = str((c or {}).get("unit") or "") if isinstance(c, dict) else ""
        dec = str(e.get("computed_unit_slug") or "")
        g = gu.get(e["id"])
        if not g:
            print(f"{sig:5} {e['id'][:46]:46} {dec[:34]:34} {texto[:34]:34} {'(sem gold)':34} -")
            continue
        com_gold += 1
        bloco_certo += dec == g
        texto_certo += texto == g
        print(f"{sig:5} {e['id'][:46]:46} {dec[:34]:34} {texto[:34]:34} {g[:34]:34} {'bloco' if dec == g else ('TEXTO' if texto == g else 'nenhum')}")
print(f"\nconflitos {total} · com gold de unidade {com_gold} · bloco (decisao atual) certo {bloco_certo} · texto certo {texto_certo}")
