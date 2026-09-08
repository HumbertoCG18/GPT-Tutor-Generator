"""HIPOTESE H1: no cronograma do professor, uma AVALIACAO e fronteira de unidade — o bloco de prova fecha a unidade que
vinha antes, e o que vem depois e a proxima. Testada nos 8 tutores contra a timeline JA construida (0 chamadas, 0 rede).

Para cada curso imprime a sequencia de blocos (data, kind, unidade) e conta:
  - trocas de unidade que acontecem NUMA fronteira de avaliacao (a favor de H1)
  - trocas de unidade no meio de blocos de aula (contra H1)
  - avaliacoes que NAO sao fronteira (a unidade continua igual dos dois lados) (contra H1)
Uso: mede_prova_fronteira.py
"""
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
TODOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
         "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
AVAL = {"assessment", "makeup"}
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

favor = contra = aval_neutra = 0
for sig, repo in TODOS.items():
    p = GH / repo / "course/.timeline_index.json"
    if not p.exists():
        print(f"{sig}: sem timeline")
        continue
    blocks = sorted(json.loads(p.read_text(encoding="utf-8")).get("blocks") or [],
                    key=lambda b: str(b.get("period_start") or ""))
    print(f"\n=== {sig} ===")
    for b in blocks:
        u = str(b.get("unit_slug") or "")
        lab = (b.get("sessions") or [{}])[0].get("label") or ""
        print(f"  {str(b.get('id'))[:9]:9} {str(b.get('period_start'))[:10]} {str(b.get('kind'))[:10]:10} "
              f"u={(u[8:20] if u else '-'):12} conf={str(b.get('unit_confidence'))[:4]:4} {str(lab)[:44]}")
    # sequencia so de blocos COM unidade, marcando onde ha avaliacao entre eles
    seq = [(i, b) for i, b in enumerate(blocks)]
    ult_u, ult_i = "", -1
    for i, b in seq:
        u = str(b.get("unit_slug") or "")
        if not u:
            continue
        if ult_u and u != ult_u:
            entre = [x for j, x in seq if ult_i < j < i and str(x.get("kind") or "") in AVAL]
            if entre:
                favor += 1
                print(f"     ^ troca {ult_u[8:18]} -> {u[8:18]} COM avaliacao entre ({[str(x.get('id')) for x in entre]})")
            else:
                contra += 1
                print(f"     ^ troca {ult_u[8:18]} -> {u[8:18]} SEM avaliacao entre")
        ult_u, ult_i = u, i
    for i, b in seq:
        if str(b.get("kind") or "") not in AVAL:
            continue
        antes = next((str(x.get("unit_slug") or "") for j, x in reversed(seq) if j < i and x.get("unit_slug")), "")
        depois = next((str(x.get("unit_slug") or "") for j, x in seq if j > i and x.get("unit_slug")), "")
        if antes and depois and antes == depois:
            aval_neutra += 1
            print(f"     ! avaliacao {b.get('id')} NAO e fronteira (mesma unidade {antes[8:18]} dos dois lados)")

print(f"\n{'=' * 70}\nH1 — a avaliacao e fronteira de unidade")
print(f"  trocas de unidade COM avaliacao entre : {favor:3}  (a favor)")
print(f"  trocas de unidade SEM avaliacao entre : {contra:3}  (contra)")
print(f"  avaliacoes que nao separam unidades   : {aval_neutra:3}  (contra)")
