"""PLACAR CONSOLIDADO da sessao de 12/09 — o que sobrou depois das correcoes e das refutacoes.

Nao mede nada: junta os numeros que sobreviveram, aponta a fonte de cada um, e mostra lado a lado o que foi PUBLICADO
durante o dia e o que ficou DEPOIS da correcao. Serve para a proxima sessao nao reusar numero morto.

Uso: python -B docs/reports/_harness-2026-09-04/c1-3/placar_consolidado_12-09.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
L = "-" * 104

print("=" * 104)
print("PLACAR CONSOLIDADO — 12/09, depois de 4 rodadas de correcao e 9 refutacoes adversariais")
print("=" * 104)
print()
print("1) OS 3 EIXOS COM O MOTOR COMPLETO (acuracia TOTAL: todo material no denominador; abster nao tira ninguem)")
print("   fonte: c1-3/motor_3eixos_v2_12-09.log + motor_3eixos_produto_12-09.log · 0 tentativas de rede nas 4")
print(L)
print(f"   {'eixo':22} {'NU':>10} {'CRU':>10} {'+VOCAB':>10} {'PRODUTO':>10}   {'meta 90%':>10}")
for eixo, n, nu, cru, voc, pro in [
        ("bloco", 237, "93,2%", "93,7%", "93,2%", "99,2%"),
        ("unidade", 284, "85,9%", "89,1%", "89,8%", "92,6%"),
        ("subunidade (aceito)", 251, "49,8%", "58,2%", "87,6%", "89,2%"),
        ("subunidade (primario)", 251, "33,9%", "41,0%", "73,3%", "74,1%")]:
    meta = "OK no cru" if float(cru.replace("%", "").replace(",", ".")) >= 90 else \
           f"faltam {90 - float(cru.replace('%','').replace(',','.')):.1f} pp"
    print(f"   {eixo:22} {nu:>10} {cru:>10} {voc:>10} {pro:>10}   {meta:>10}")
print(f"   {'cobertura':22} {'54,2%':>10} {'56,2%':>10} {'58,2%':>10} {'76,9%':>10}")
print()
print("   NU = sem curadoria manual e sem vocab LLM · CRU = curadoria humana, sem vocab (o regime da regua)")
print("   +VOCAB = com o vocabulario do LLM, voter ainda off · PRODUTO = voter ligado (reproduz o produto em disco)")
print()
print("2) A META 90/90/90 EM MATERIAIS (o que falta, no regime CRU)")
print(L)
for eixo, n, tem, meta in [("bloco", 237, 222, 214), ("unidade", 284, 253, 256), ("subunidade", 251, 146, 226)]:
    falta = meta - tem
    st = "JA BATE" if falta <= 0 else f"faltam {falta} materiais"
    print(f"   {eixo:14} tem {tem:>3}/{n:<4} · 90% exige {meta:>3} · {st}")
print()
print("3) O QUE CADA CAMADA COMPRA (pontos de acuracia total)")
print(L)
print(f"   {'camada':34} {'bloco':>8} {'unidade':>9} {'subunidade':>12}")
for c, b, u, s in [("curadoria humana (NU -> CRU)", "+0,4", "+3,2", "+8,4"),
                   ("vocabulario do LLM (CRU -> VOCAB)", "-0,4", "+0,7", "+29,4"),
                   ("voter do LLM (VOCAB -> PRODUTO)", "+5,9", "+2,8", "+1,6")]:
    print(f"   {c:34} {b:>8} {u:>9} {s:>12}")
print()
print("4) NUMEROS QUE MUDARAM HOJE — nao reusar a coluna da esquerda")
print(L)
print(f"   {'numero':46} {'publicado':>16} {'depois da correcao':>20}")
for nome, antes, depois in [
        ("divergencias replay x produto", "2", "0 (eram 10)"),
        ("regua do cru, subunidade aceito (replay)", "139/251", "147/251"),
        ("erros de aceito no cru", "112", "104 (replay) / 105 (motor)"),
        ("erros CONFIANTES no cru", "82", "77"),
        ("teto das fontes do professor (primario, 227)", "61% e depois 64%", "44%"),
        ("SARC no IA (alcance)", "87%", "5%"),
        ("ganho do seletor com 5 topicos", "+31 (5 topicos)", "+31, mas 2 topicos de 1 curso"),
        ("2a passada: higiene de token de midia", "divida a pagar", "REFUTADA (-2 cru, -3 produto)")]:
    print(f"   {nome:46} {antes:>16} {depois:>20}")
print()
print("5) FRENTES FECHADAS POR NEGATIVO MEDIDO (nao reabrir sem dado novo)")
print(L)
for f in ["SARC posicional (perde nos dois regimes; sobrevive a 2 testes de robustez)",
          "piso global de winner_score e a margem 1o-2o (Spearman 0,948: e o mesmo piso, 5a refutacao)",
          "razao s2/s1, cobertura de tokens, riqueza de alias, 'sem competicao' (nao separam)",
          "limpar token de midia da doacao por headings (custa -2 no cru e -3 no produto)",
          "numerar artificialmente o plano do IA (o professor realmente nao numera)",
          "Datalab como alavanca de atribuicao (3 predicoes mudam de 31, saldo zero)"]:
    print(f"   x {f}")
print()
print("6) O QUE CONTINUA SEM MEDICAO")
print(L)
for f in ["custo por curso da compilacao de vocabulario (tokens, retries, tempo humano)",
          "validacao fora da amostra: o LR nao tem gold de subunidade",
          "o prompt v1 do compilador — a unica peca calibrada no gold que sobra",
          "a meta POR CURSO (MF 89,4% no bloco, SO 73,0% na unidade)",
          "os 25 erros de subunidade que o produto tambem erra"]:
    print(f"   ? {f}")
print()
print("=" * 104)
print("EM UMA LINHA: no motor cru o BLOCO ja bate a meta (93,7%), a UNIDADE fica a 3 materiais (89,1%) e a")
print("SUBUNIDADE precisa de 80 materiais (58,2% contra 90%) — e o unico mecanismo que move a subunidade e")
print("vocabulario, que hoje so sabemos produzir com uma passada de LLM por curso.")
print("=" * 104)
