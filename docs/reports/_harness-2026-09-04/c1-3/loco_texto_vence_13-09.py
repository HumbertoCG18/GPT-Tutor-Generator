"""LEAVE-ONE-COURSE-OUT da regra "texto vence quando o bloco veio de metodo fraco" (13/09, Gate 1 do eixo unidade).

A regra tem UM parametro: o conjunto de metodos de bloco considerados fracos. Eu escolhi {janela-1, due-contain,
due-straddle} OLHANDO a distribuicao nos 6 cursos — e o saldo agregado (+7 no cru, +5 no produto) esconde que tres
cursos ganham e tres perdem. O LOCO testa se a ESCOLHA do conjunto generaliza:

    para cada curso c:
        escolhe os metodos com saldo > 0 usando SO os outros 5 cursos
        aplica essa escolha no curso c e mede o saldo LA (fora da amostra)

Publica: o conjunto escolhido em cada fold (estabilidade), o saldo DENTRO e FORA, e o agregado fora da amostra — que e
o numero honesto. Compara com o conjunto fixo que eu tinha escolhido e com "texto vence sempre".

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/loco_texto_vence_13-09.py
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
FIXO = {"janela-1", "due-contain", "due-straddle"}


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
            casos.append(dict(sig=sig, eid=eid, metodo=str(e.get("temporal_block_method") or "(vazio)"),
                              gan=int(texto in gu[eid] and bloco not in gu[eid]),
                              per=int(bloco in gu[eid] and texto not in gu[eid])))
    return casos


def saldo(casos, metodos):
    sel = [c for c in casos if c["metodo"] in metodos]
    return sum(c["gan"] for c in sel) - sum(c["per"] for c in sel), len(sel)


def escolhe(casos):
    """Os metodos com saldo > 0 nos cursos dados. E a unica decisao 'treinada' da regra."""
    por = collections.defaultdict(lambda: [0, 0])
    for c in casos:
        por[c["metodo"]][0] += c["gan"]
        por[c["metodo"]][1] += c["per"]
    return {m for m, (g, p) in por.items() if g - p > 0}


for rotulo, raiz in (("CRU", COPIA), ("PRODUTO", ORIG)):
    casos = levanta(raiz)
    print(f"================ {rotulo} — {len(casos)} conflitos ================")
    tot_dentro = tot_fora = 0
    print(f"  {'fold (curso de fora)':22} {'conjunto escolhido nos outros 5':44} {'DENTRO':>8} {'FORA':>7}")
    for c_out in NOMES:
        treino = [c for c in casos if c["sig"] != c_out]
        teste = [c for c in casos if c["sig"] == c_out]
        M = escolhe(treino)
        s_in, _ = saldo(treino, M)
        s_out, n_out = saldo(teste, M)
        tot_dentro += s_in
        tot_fora += s_out
        nome = ", ".join(sorted(M)) if M else "(vazio: nenhum metodo com saldo > 0)"
        print(f"  {c_out:22} {nome[:44]:44} {s_in:>+8} {s_out:>+7}")
    print(f"  {'AGREGADO':22} {'':44} {tot_dentro:>+8} {tot_fora:>+7}   <- FORA e o numero honesto")
    print()
    fx, nfx = saldo(casos, FIXO)
    todos = {c["metodo"] for c in casos}
    sp, nsp = saldo(casos, todos)
    print(f"  para comparar, na amostra inteira:")
    print(f"    conjunto FIXO que eu escolhi {sorted(FIXO)}: saldo {fx:+d} (dispara em {nfx})")
    print(f"    texto vence SEMPRE: saldo {sp:+d} (dispara em {nsp})")
    print()
    print("  estabilidade do conjunto entre os folds:")
    freq = collections.Counter()
    for c_out in NOMES:
        for m in escolhe([c for c in casos if c["sig"] != c_out]):
            freq[m] += 1
    for m, k in freq.most_common():
        print(f"    {m:20} escolhido em {k} dos {len(NOMES)} folds")
    print()
