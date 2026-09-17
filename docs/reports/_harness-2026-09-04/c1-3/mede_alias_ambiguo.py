"""H2: ALIAS que serve a DOIS topicos nao discrimina — e hoje entra no motor sem nenhuma verificacao, e chega a decidir
um BLOCO com confianca 1,0. Levantamento nos 8 tutores (0 chamadas, 0 rede).

Contexto (ES2, achado de 07/09): `.glossary_curation.json` — arquivo marcado "Proposto-claude a partir de subunit_gt_ES2;
revisar a mao" — poe `service discovery`, `name server`, `service registry`, `API gateway`, `gateway` sob 2.7 ("integração
e IMPLANTAÇÃO"), e `microsserviço de câmbio` sob 1.5 E 2.7 ao mesmo tempo.

Mede:
  A) aliases identicos em 2+ topicos, por curso (dentro da mesma unidade e entre unidades)
  B) quantos materiais e blocos hoje sao decididos por um alias ambiguo
Uso: mede_alias_ambiguo.py
"""
import collections
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
TODOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
         "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402

print("A) ALIASES QUE SERVEM A 2+ TOPICOS")
print(f"{'':4} {'topicos':>8} {'aliases':>8} {'ambiguos':>9} {'entre unidades':>15}")
TOT = collections.Counter()
DET = {}
for sig, repo in TODOS.items():
    p = GH / repo / "course/.content_taxonomy.json"
    if not p.exists():
        print(f"{sig:4} sem taxonomia")
        continue
    tax = json.loads(p.read_text(encoding="utf-8"))
    units = tax.get("units")
    it = list(units.values()) if isinstance(units, dict) else list(units or [])
    dono = collections.defaultdict(list)
    ntop = 0
    for u in it:
        for t in (u.get("topics") or []):
            ntop += 1
            for a in (t.get("aliases") or []):
                n = N(a)
                if n:
                    dono[n].append((str(u.get("slug") or ""), str(t.get("slug") or ""), a))
    amb = {a: v for a, v in dono.items() if len({x[1] for x in v}) > 1}
    entre = {a: v for a, v in amb.items() if len({x[0] for x in v}) > 1}
    DET[sig] = (amb, entre)
    TOT["topicos"] += ntop
    TOT["aliases"] += len(dono)
    TOT["ambiguos"] += len(amb)
    TOT["entre"] += len(entre)
    print(f"{sig:4} {ntop:8} {len(dono):8} {len(amb):9} {len(entre):15}")
print(f"{'TOT':4} {TOT['topicos']:8} {TOT['aliases']:8} {TOT['ambiguos']:9} {TOT['entre']:15}")

print("\nOS AMBIGUOS ENTRE UNIDADES (os que podem mover a unidade de um material):")
for sig, (amb, entre) in DET.items():
    for a, v in sorted(entre.items()):
        alvos = " | ".join(f"{u[8:20]}/{t[:26]}" for u, t, _ in v)
        print(f"  {sig:4} {v[0][2][:34]:34} -> {alvos}")

print("\nB) DECISOES DE HOJE QUE DEPENDEM DE UM ALIAS AMBIGUO")
for sig, repo in TODOS.items():
    if sig not in DET:
        continue
    amb, _ = DET[sig]
    if not amb:
        continue
    root = GH / repo
    tl = root / "course/.timeline_index.json"
    nb = 0
    if tl.exists():
        for b in json.loads(tl.read_text(encoding="utf-8")).get("blocks") or []:
            txt = N(str(b.get("topic_text") or ""))
            prim = str(b.get("primary_topic_slug") or "")
            if not prim or not txt:
                continue
            for a, v in amb.items():
                if a in txt and prim in {t for _, t, _ in v}:
                    nb += 1
                    print(f"  {sig:4} BLOCO {str(b.get('id')):9} topic_text={str(b.get('topic_text'))[:40]!r} "
                          f"-> {prim[:40]} (conf {b.get('primary_topic_confidence')}) por alias ambiguo {v[0][2]!r}")
                    break
    if not nb:
        print(f"  {sig:4} nenhum bloco decidido por alias ambiguo")
