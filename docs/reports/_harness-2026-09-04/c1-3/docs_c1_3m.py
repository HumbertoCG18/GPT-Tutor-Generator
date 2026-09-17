"""Registro (06/09): fila de revisao medida contra os golds (rendimento por camada e gatilho; contrafactual de politicas).
Pergunta do user: "queria ver se dava para diminuir os arquivos para revisao, eles estao bem altos e eu nao entendi o que isso significa"."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = """## FILA DE REVISAO (`revisar`/100 = 57,5) — RENDIMENTO MEDIDO CONTRA OS GOLDS (06/09, sessao 6; pergunta do user "da para diminuir?")
**O que e:** campo derivado `revisar` (`routing/revisar.py`, decisao B 02/09) = lista que o tutor mostra para conferir. Tres camadas: **duvida** (o
motor se acusou: sem bloco, bloco flagado, conflito unidade x bloco, subunidade empate/ambigua) · **mudou** (uma sync moveu decisao confiante) ·
**llm** (bloco decidido por voto de LLM, "confira"). Metrica = (duvida + llm + mudou) por 100 materiais. Hoje: 200/348 = 57,5 (duvida 108, llm 79, mudou 13).
**Rendimento (produto, 8 tutores x golds de bloco 234 / unidade 191 / subunidade 233; `c1-3/fila_rendimento.py`, 0 chamadas):** 41 materiais
errados em algum eixo (bloco 1, unidade 0, subunidade 40). Camada **duvida** 108 na fila, 79 com gold, 27 errados (34%) · **mudou** 13, 3 errados ·
**llm** 79 na fila, 71 com gold, **2 errados (3%)** — os blocos decididos por LLM acertam 75/76 no gold; os 2 sao erros de subunidade por acaso ·
**ok** (fora da fila) 148, 125 com gold, 9 errados (7%; todos subunidade confiante sem sinal: MF invariantes/terminacao/tiposindutivos/exemplos/AFP,
CG domina/exercicios-teoricos/pagina-instanciamento/aula-gravada).
**Por gatilho da duvida:** conflito 53 na fila, 13 errados (unidade 0! bloco 1, sub 12 por coincidencia) 31% · flag:janela-1 21 -> 5 (26%) · sub-empate
20 -> 9 (**69%**, o melhor) · sub-ambigua 17 -> 2 (14%) · flag:llm-funil 16 -> 3 (60%) · due-straddle 1 -> 0.
**Contrafactual (tamanho da fila x erros pegos, dos 41):** P0 atual 200 (57,5) pega 32 · **P1 sem a camada llm 121 (34,8) pega 30** · P2 P1 sem
'conflito' 85 (24,4) pega 23 · P1 + gatilho novo sub-vazia 134 (38,5) pega 31 · P1 + sub-vazia + sub-fraca(score<1) 150 (43,1) pega 32 · P2 + vazia +
fraca 129 (37,1) pega 31. Por curso sob P1: CG 76 -> 59, MF 58 -> 15, ES2 66 -> 34.
**Leitura:** a fila e 40% cerimonia: a camada llm (79) existe para "conferir o voto", mas o voto acerta 75/76. Cortar a camada llm da metrica tira 79
itens e perde 2 erros. 'conflito' e o maior gatilho da duvida e tem rendimento ZERO no eixo que ele vigia (unidade 191/191): os 13 que pega sao erros
de subunidade dos mesmos materiais. O que sobra fora da fila (9) e erro confiante de subunidade = vocabulario, sem sinal para gatilho.
**Proposta (decisao do user; muda metrica de produto):** P1 = camada llm vira "ok" na metrica e na fila (conservar o campo `temporal_block_method`
para a UI mostrar "decidido por LLM" como informacao, nao como pendencia). Opcional: gatilho `sub-vazia` (+13 itens, +1 erro). Nao tocar 'conflito'
ate a subunidade do CG melhorar (ele e hoje o unico que pega 7 dos erros de sub do CG sem gold).

"""
edit(T, "## GOLDS CG E MF APROVADOS — REGUA DE SUBUNIDADE PASSA A 233", SEC + "## GOLDS CG E MF APROVADOS — REGUA DE SUBUNIDADE PASSA A 233")

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). Corrigir a extracao dos zips (2).",
        "- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). **Fila de revisao: cortar a camada `llm` da metrica (57,5 -> 34,8; perde 2 de 41 erros;\n"
        "  tracker §FILA DE REVISAO)** — decisao do user, muda metrica de produto (decisao B 02/09). Corrigir a extracao dos zips (2).")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `fila_rendimento.py`: fila `revisar` x golds no produto — camada llm 79 itens / 2 erros (voto de bloco 75/76); conflito 0 erros de unidade; contrafactual P0 200 -> P1 121 (perde 2 de 41).\n", encoding="utf-8")
print("docs ok")
