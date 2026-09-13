"""O corte que os DADOS apontam: o texto vence quando o bloco veio de `janela-1` (13/09).

Os cortes que eu supus (bloco misto, bloco de "metodo fraco", texto confiante) TODOS perdem
(`texto_vence_cortes_13-09.log`). Mas a distribuicao por metodo do bloco mostra que eu tinha classificado ao contrario:

    metodo do bloco     texto certo   bloco certo
    disamb                        1            19     <- desempate ATIVO: o bloco e forte
    janela-1                     11             6     <- proximidade temporal: o bloco e fraco

Faz sentido mecanico: `janela-1` poe o material no bloco por estar na janela de uma aula — proximidade, nao conteudo;
`disamb` e desempate que usou sinal. Aqui os cortes derivados disso sao medidos.

ATENCAO ao risco: este corte foi derivado OLHANDO a distribuicao dos erros, que vem do gold. Vale como hipotese com
mecanismo plausivel, nao como regra validada — a validacao honesta e fora da amostra.

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/texto_vence_janela_13-09.py
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


def levanta(raiz):
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
            cf = e.get("unit_block_conflict") or {}
            texto, bloco = str(cf.get("unit") or ""), str(cf.get("block_unit") or "")
            if not texto or not bloco or texto == bloco:
                continue
            casos.append(dict(sig=sig, eid=eid, texto=texto, bloco=bloco, aceitas=gu[eid],
                              metodo=str(e.get("temporal_block_method") or ""),
                              conf=float(e.get("unit_match_confidence") or 0.0)))
    return casos


CORTES = {
    "A sempre (refutado)": lambda c: True,
    "H so janela-1": lambda c: c["metodo"] == "janela-1",
    "I janela-1 E confiante": lambda c: c["metodo"] == "janela-1" and c["conf"] >= 0.60,
    "J janela-1 ou due-*": lambda c: c["metodo"] in ("janela-1", "due-contain", "due-straddle"),
    "K tudo MENOS disamb*": lambda c: not c["metodo"].startswith("disamb"),
}
res = {}
for rotulo, raiz in (("CRU", COPIA), ("PRODUTO", ORIG)):
    casos = levanta(raiz)
    print(f"=== {rotulo} — {len(casos)} conflitos ===")
    print(f"  {'corte':26} {'dispara':>8} {'GANHA':>7} {'PERDE':>7} {'saldo':>7}")
    for nome, f in CORTES.items():
        sel = [c for c in casos if f(c)]
        g = sum(1 for c in sel if c["texto"] in c["aceitas"] and c["bloco"] not in c["aceitas"])
        p_ = sum(1 for c in sel if c["bloco"] in c["aceitas"] and c["texto"] not in c["aceitas"])
        res[(rotulo, nome)] = (g, p_)
        print(f"  {nome:26} {len(sel):>8} {g:>7} {p_:>7} {g - p_:>+7}")
    print()

print("TESTE DE APROVACAO (ganha no cru E nao regride o produto):")
for nome in CORTES:
    gc, pc = res[("CRU", nome)]
    gp, pp = res[("PRODUTO", nome)]
    ok = (gc - pc) > 0 and (gp - pp) >= 0
    print(f"  {nome:26} cru {gc - pc:+3d} · produto {gp - pp:+3d}   {'PASSA' if ok else 'nao passa'}")

print()
print("POR CURSO, o corte H (so janela-1), no CRU:")
casos = levanta(COPIA)
por = collections.defaultdict(lambda: [0, 0])
for c in casos:
    if c["metodo"] != "janela-1":
        continue
    if c["texto"] in c["aceitas"] and c["bloco"] not in c["aceitas"]:
        por[c["sig"]][0] += 1
    elif c["bloco"] in c["aceitas"] and c["texto"] not in c["aceitas"]:
        por[c["sig"]][1] += 1
for sig, (g, p_) in sorted(por.items()):
    print(f"  {sig:5} ganha {g:>2} · perde {p_:>2} · saldo {g - p_:+d}")
