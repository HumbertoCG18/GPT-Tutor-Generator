"""TEXTO x BLOCO na unidade, contra a regua CURRICULAR (13/09; decisao do user: "o motor deveria seguir o plano").

A precedencia atual esta em `src/builder/routing/file_map.py:802-807` e o comentario dela diz por que:

    "2026-08-21: a verdade de unidade e, por construcao, a unidade do bloco (ground_truth |><| gold_units).
     Medido nos 5 cursos (188 entries): scorer de texto 130, unidade do bloco temporal 162 ... O bloco decide;
     o texto discordante vira registro de conflito para auditoria, nunca decisao."

**Aquela medicao e circular por admissao propria**: a regua ERA a unidade do bloco. Em 12/09 a regua virou CURRICULAR
(`material_gt_<sig>.csv` adjudicado pelo usuario sobrepoe o gold por bloco). Entao a comparacao tem que ser refeita.

Como medir sem rodar o motor: quando o bloco vence um texto discordante, o motor GRAVA o que o texto queria em
`entry["unit_block_conflict"] = {"unit": <texto>, "block_unit": <bloco>, "block_id": ...}`. Basta comparar os dois
contra a regua curricular.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/texto_x_bloco_curricular_13-09.py
"""
import collections
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
ORIG = GEN.parent
COPIA = GEN / ".motor3eixos"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import carrega_regua_unidade  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}


def mede(raiz, rotulo):
    tot = collections.Counter()
    casos = []
    for sig, nm in NOMES.items():
        p = raiz / nm / "manifest.json"
        if not p.exists():
            continue
        gu = carrega_regua_unidade(sig)
        for e in json.loads(p.read_text(encoding="utf-8"))["entries"]:
            eid = e["id"]
            if eid not in gu:
                continue
            tot["n"] += 1
            cf = e.get("unit_block_conflict") or {}
            if not cf:
                continue
            texto = str(cf.get("unit") or "")
            bloco = str(cf.get("block_unit") or "")
            if not texto or not bloco or texto == bloco:
                continue
            tot["conflitos"] += 1
            aceitas = gu[eid]
            t_ok, b_ok = texto in aceitas, bloco in aceitas
            if t_ok and not b_ok:
                tot["TEXTO certo"] += 1
                casos.append((sig, eid, "TEXTO", texto, bloco))
            elif b_ok and not t_ok:
                tot["BLOCO certo"] += 1
                casos.append((sig, eid, "BLOCO", texto, bloco))
            elif t_ok and b_ok:
                tot["ambos certos"] += 1
            else:
                tot["ambos errados"] += 1
                casos.append((sig, eid, "ambos errados", texto, bloco))
    print(f"=== {rotulo} ===")
    for k in ("n", "conflitos", "TEXTO certo", "BLOCO certo", "ambos certos", "ambos errados"):
        print(f"  {k:16} {tot[k]:>4}")
    t, b = tot["TEXTO certo"], tot["BLOCO certo"]
    print(f"  --> trocar a precedencia (texto vence): {t - b:+d} materiais (ganha {t}, perde {b})")
    print()
    return tot, casos


print("A comparacao que a precedencia atual cita foi feita contra uma regua construida DO BLOCO.")
print("Aqui ela e refeita contra a regua CURRICULAR (material_gt adjudicado pelo usuario em 12/09).")
print()
tc, cc = mede(COPIA, "REGIME CRU (copia .motor3eixos)")
tp, cp = mede(ORIG, "PRODUTO")

print("CASOS NO PRODUTO em que o TEXTO estava certo e o bloco venceu (o que a mudanca corrigiria):")
for sig, eid, quem, texto, bloco in cp:
    if quem == "TEXTO":
        print(f"  {sig:4} {eid:44}")
        print(f"        texto queria : {texto}")
        print(f"        bloco impos  : {bloco}")
print()
print("CASOS NO PRODUTO em que o BLOCO estava certo (o que a mudanca QUEBRARIA):")
for sig, eid, quem, texto, bloco in cp:
    if quem == "BLOCO":
        print(f"  {sig:4} {eid:44}")
        print(f"        texto queria : {texto}  <-- passaria a valer, e esta ERRADO")
        print(f"        bloco impos  : {bloco}")
