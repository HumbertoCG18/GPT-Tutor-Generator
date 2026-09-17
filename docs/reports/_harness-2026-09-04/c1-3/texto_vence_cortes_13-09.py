"""Quando o TEXTO deve vencer o BLOCO na unidade? (13/09, Gate 1 do eixo unidade)

"Texto vence sempre" foi medido e PERDE mesmo contra a regua curricular: -15 no cru, -7 no produto
(`texto_x_bloco_curricular_13-09.log`). O handoff ja apontava o caminho:

    "reabrir so com a regra ESTREITA (secao especifica mapeada ao plano, corroborada pelo material, supera bloco
     misto), Gate 1"

Aqui os cortes sao medidos um a um. Um corte so passa se GANHAR no cru E nao regredir o produto.

  A  sempre                            (o baseline refutado)
  B  bloco MISTO                       o bloco tem materiais de 2+ unidades (o bloco nao discrimina)
  C  bloco de metodo FRACO             herdado do vizinho, ref-generica, meta-generica, disamb
  D  texto CONFIANTE                   unit_match_confidence >= 0.60
  E  B e D                             bloco misto E texto confiante
  F  C e D                             bloco fraco E texto confiante
  G  B ou C, com D                     (bloco misto OU fraco) E texto confiante

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/texto_vence_cortes_13-09.py
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
FRACOS = {"ref-generica", "meta-generica", "disamb", "disamb-curto", "irmao-card", "secao-geral", ""}


def levanta(raiz):
    casos = []
    for sig, nm in NOMES.items():
        p = raiz / nm / "manifest.json"
        if not p.exists():
            continue
        gu = carrega_regua_unidade(sig)
        entries = json.loads(p.read_text(encoding="utf-8"))["entries"]
        # bloco MISTO: quantas unidades distintas o motor atribuiu aos materiais daquele bloco (sem gold)
        por_bloco = collections.defaultdict(set)
        for e in entries:
            b = str(e.get("temporal_block_id") or "")
            u = str(e.get("computed_unit_slug") or "")
            if b and u:
                por_bloco[b].add(u)
        for e in entries:
            eid = e["id"]
            if eid not in gu:
                continue
            cf = e.get("unit_block_conflict") or {}
            texto, bloco = str(cf.get("unit") or ""), str(cf.get("block_unit") or "")
            if not texto or not bloco or texto == bloco:
                continue
            b = str(e.get("temporal_block_id") or "")
            casos.append(dict(
                sig=sig, eid=eid, texto=texto, bloco=bloco, aceitas=gu[eid],
                misto=len(por_bloco.get(b, set())) > 1,
                fraco=str(e.get("temporal_block_method") or "") in FRACOS,
                conf=float(e.get("unit_match_confidence") or 0.0),
                metodo=str(e.get("temporal_block_method") or ""),
            ))
    return casos


CORTES = {
    "A sempre": lambda c: True,
    "B bloco misto": lambda c: c["misto"],
    "C bloco de metodo fraco": lambda c: c["fraco"],
    "D texto confiante (>=0,60)": lambda c: c["conf"] >= 0.60,
    "E misto E confiante": lambda c: c["misto"] and c["conf"] >= 0.60,
    "F fraco E confiante": lambda c: c["fraco"] and c["conf"] >= 0.60,
    "G (misto ou fraco) E conf": lambda c: (c["misto"] or c["fraco"]) and c["conf"] >= 0.60,
}

for rotulo, raiz in (("CRU", COPIA), ("PRODUTO", ORIG)):
    casos = levanta(raiz)
    print(f"=== {rotulo} — {len(casos)} conflitos texto x bloco ===")
    print(f"  {'corte':28} {'dispara':>8} {'GANHA':>7} {'PERDE':>7} {'neutro':>7} {'saldo':>7}")
    for nome, f in CORTES.items():
        sel = [c for c in casos if f(c)]
        g = sum(1 for c in sel if c["texto"] in c["aceitas"] and c["bloco"] not in c["aceitas"])
        p_ = sum(1 for c in sel if c["bloco"] in c["aceitas"] and c["texto"] not in c["aceitas"])
        print(f"  {nome:28} {len(sel):>8} {g:>7} {p_:>7} {len(sel)-g-p_:>7} {g-p_:>+7}")
    print()

print("DISTRIBUICAO dos conflitos do CRU por metodo do bloco (quem ganha em cada um):")
casos = levanta(COPIA)
por_metodo = collections.defaultdict(lambda: [0, 0, 0])
for c in casos:
    k = c["metodo"] or "(sem metodo)"
    if c["texto"] in c["aceitas"] and c["bloco"] not in c["aceitas"]:
        por_metodo[k][0] += 1
    elif c["bloco"] in c["aceitas"] and c["texto"] not in c["aceitas"]:
        por_metodo[k][1] += 1
    else:
        por_metodo[k][2] += 1
print(f"  {'metodo do bloco':22} {'texto certo':>12} {'bloco certo':>12} {'neutro':>8}")
for k, (t, b, n) in sorted(por_metodo.items(), key=lambda x: -(x[1][0] + x[1][1] + x[1][2])):
    print(f"  {k:22} {t:>12} {b:>12} {n:>8}")
