"""Registro: REGUA AUTOMATICA (motor + voter cacheado, sem pino, sem glossario manual) vira a oficial; gold so mede; pinos sao andaime."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = """## REGUA AUTOMATICA (05/09 tarde, sessao 6; decisao do user: "gold so mede; nao criar curadoria por curso") — MEDIDA, VIRA A OFICIAL
**Definicao:** motor + voter com CACHE de votos, SEM pinos (bloco/unidade/sub), SEM glossario manual, COM vocab compilado por LLM; copias `.ablacao`;
tripwire (cache miss = voto pulado e contado; 0 pulados nesta rodada; 0 chamadas). Ferramenta: `_harness-2026-09-04/c1-3/motor_auto.py {puro5|holdout}`.
| regua | motor puro | **AUTOMATICA** | curada (produto) |
|---|---|---|---|
| bloco (199) | 186 conf-err 1 | **192 = 96,5%, conf-err 0** | 198 |
| unidade (191) | 183 | **185 = 96,9%** | 191 |
| cobertura (57) | 53 | 53 | 55 |
| subunidade (93) | 82 | **82 = 88%** | (sem regua curada; IA 39/39 com glossario manual) |
| holdout CG (35) | 31 | **35 = 100%** | 35 |
**Leitura:** o pipeline automatico ja passa de 95% em bloco, unidade e no curso nao usado para afinar; o que falta para a curada e o territorio dos
pinos (MF 6 de bloco: arvores/listas e cia.; SO 3 + IA 3 de unidade) — o voter resolve os flagados de bloco (holdout 31 -> 35) mas NAO existe voto de
UNIDADE para bloco sem evidencia lexical. **Onde esta abaixo de 95%: subunidade (88%) = vocabulario** (o plano nomeia categorias, o material nomeia
algoritmos; o vocab compilado por LLM nao emitiu 'perceptron'/'rede neural'/'MLP' para o IA; o glossario manual foi o remendo humano).
**Regras genericas x pinos do CG (medido nos 8, `c1-3/simula_radical_fallback.py` + combo em memoria):** bloco-06 (u04) ja nao precisa de pino
(a higiene resolveu; base = u04) · bloco-15 (u07) e coberto por RADICAL SO COMO FALLBACK (1 bloco muda nos 8, 0 colateral, unidade 183 = 183) ·
bloco-08 (morfologia -> u03) NAO tem sinal lexical generico possivel: o plano nao menciona morfologia e o unico token que casa e 'matematica' no
label do topico u06 'A matematica das projecoes'; higiene por titulo/secao no mapa, heranca por afinidade zero (Z0) e exclusividade relaxada (XR)
nao o alcancam (0 efeito nos 8). Caminho generico para esse residuo = LLM decidindo a UNIDADE de bloco sem evidencia lexical (1 chamada por bloco
assim; CG tem 1) — precisa de Gemini. Ate la o pino do bloco-08 e andaime, nao arquitetura.

"""
edit(T, "## CURADORIA DE UNIDADE DO CG + HIGIENE DO VOCAB", SEC + "## CURADORIA DE UNIDADE DO CG + HIGIENE DO VOCAB")
edit(T, "last_updated: 2026-09-05 tarde (sessao 6; C0 FECHADA 11/11; C1 itens 1-3 FEITOS — o 3 por medicao, REFUTADO; gold pelo oraculo;",
        "last_updated: 2026-09-05 tarde (sessao 6; REGUA AUTOMATICA = oficial: bloco 192/199, unidade 185/191, holdout CG 35/35, sub 82/93; C1 itens 1-3 FEITOS; gold pelo oraculo;")

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "## COMECE POR (proxima sessao) — tres decisoes do user antes de qualquer codigo",
        """## REGUA OFICIAL A PARTIR DE AGORA: a AUTOMATICA (user, 05/09 tarde: "gold so mede; nao criar curadoria por curso")
Motor + voter com cache, sem pino, sem glossario manual, com vocab LLM (`_harness-2026-09-04/c1-3/motor_auto.py`): **bloco 192/199 = 96,5% conf-err 0 ·
unidade 185/191 = 96,9% · cobertura 53/57 · subunidade 82/93 = 88% · holdout CG 35/35**. Motor puro (sem voter) segue como regua de diagnostico; curada
(com pinos) e o produto de hoje, nao a meta. Pinos e glossario manual sao ANDAIME: cada um deve ter regra generica ou voto de LLM que o substitua,
medido nos 8 — ou fica registrado como residuo humano com nome. Golds novos so para MEDIR (CG/MF subunidade: aprovar uma vez, nunca curar por curso).
**Abaixo de 95% so a subunidade (vocabulario). Caminhos genericos:** vocab compilado melhor (LLM; hoje nao emite 'perceptron'/'MLP' para o IA) ·
propagacao por headings (+5/-0 no gold, valida com o gold CG/MF) · voto de LLM para unidade de bloco sem evidencia lexical (CG bloco-08; 1 chamada por bloco assim).

## COMECE POR (proxima sessao) — tres decisoes do user antes de qualquer codigo""")
edit(H, "Golds propostos (NAO na regua): `subunit_gt_CG.csv` 82 pontuaveis · `subunit_gt_MF.csv` 58.",
        "Golds propostos (NAO na regua): `subunit_gt_CG.csv` 82 pontuaveis · `subunit_gt_MF.csv` 58. **Regua automatica: bloco 192/199 · unidade 185/191 · sub 82/93 · holdout 35/35.**")
edit(H, "- **Radical (6 chars) so como fallback no mapa bloco->unidade**",
        "- **Voto de LLM para a UNIDADE de bloco sem evidencia lexical** (CG bloco-08 morfologia: plano nao menciona; unico caso nos 8) · 1 chamada por bloco assim · substitui o pino do bloco-08 · precisa de Gemini.\n"
        "- **Radical (6 chars) so como fallback no mapa bloco->unidade**")

D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### Regua oficial e a AUTOMATICA (motor + voter cacheado, sem pino, sem glossario manual); gold so mede; curadoria por curso e andaime

**Date:** 2026-09-05
**Status:** Active
**Decision:** A meta de precisao e medida no pipeline automatico, nao no motor puro (diagnostico) nem na curada (produto de hoje). Golds existem para medir; nao se cria curadoria por curso como caminho para a precisao. Pino e glossario manual sao andaime: cada um precisa de regra generica ou voto de LLM que o substitua, medido nos 8, ou fica registrado como residuo humano com nome.
**Reasoning:** Medido em 05/09 tarde (`motor_auto.py`, 0 chamadas, 0 votos pulados): bloco 192/199 (96,5%, conf-err 0), unidade 185/191 (96,9%), holdout CG 35/35, subunidade 82/93 (88%). O automatico ja passa de 95% onde o aluno pergunta quando e em que unidade; abaixo de 95% so a subunidade, cujo bloqueio e vocabulario (o plano nomeia categorias, o material nomeia algoritmos). Dos 3 pinos do CG: bloco-06 ja nao precisa (higiene), bloco-15 e coberto por radical-fallback (generico, 0 colateral), bloco-08 nao tem sinal lexical possivel (plano nao menciona morfologia) — residuo para voto de LLM de unidade.
**Consequences:** Handoff 2026-09-05b registra a regua automatica como oficial; motor puro e curada continuam medidos como diagnostico e produto. Proximos genericos: radical-fallback (caixa), voto de LLM de unidade para bloco sem evidencia (Gemini), vocab compilado que emita nomes de algoritmos, propagacao por headings validada com o gold CG/MF.
"""
assert "Regua oficial e a AUTOMATICA" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `motor_auto.py {puro5|holdout}` -> `auto_*.log`: REGUA AUTOMATICA (motor + voter cacheado, sem pino, sem glossario manual): bloco 192/199, unidade 185/191, sub 82/93, holdout CG 35/35; 0 chamadas.\n", encoding="utf-8")
print("docs ok")
