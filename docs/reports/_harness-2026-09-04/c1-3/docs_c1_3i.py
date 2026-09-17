"""Registro: radical-fallback no motor (ff21cab) + pinos 06/15 do CG removidos (0d2020a) + regua automatica remedida com vocab e cache do produto.
Placeholders AUTO5_PLACEHOLDER / DET_PLACEHOLDER preenchidos pelo runner."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
AUTO5 = sys.argv[1] if len(sys.argv) > 1 else "AUTO5_PLACEHOLDER"
DET = sys.argv[2] if len(sys.argv) > 2 else "DET_PLACEHOLDER"


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = f"""## CG UNIDADE SEM LLM E SEM PINO — RADICAL-FALLBACK NO MOTOR + 2 PINOS REMOVIDOS (05/09 tarde, sessao 6, FEITO; gerador `ff21cab`, CG `0d2020a`)
**Pedido do user:** o maior numero possivel sem LLM, sem curadoria por curso. **Medido antes (`c1-3/simula_cg_unidade_generico.py`, nos 8):** radical so como
fallback (RF) +1 bloco (CG 15 -> u07), 0 colateral, unidade 183 = 183 · generico por radical entre unidades (SG) 183 -> 172, SO 32 -> 21: REFUTADO · heranca
por afinidade zero (Z0) 0 efeito (o bloco-08 tem afinidade 1 via 'matematica' no label de u06) · alias boilerplate ('OpenGL' em > 25% dos materiais) 0
efeito no mapa · bloco flagado nao impoe unidade: texto certo 3 x bloco certo 4 (puro), 0 x 4 (produto): REFUTADO · gate por confianca do texto
(>= 0,6 a 0,95): saldo -17 a -2 em toda a varredura: REFUTADO (o 'bloco decide' de 21/08 segue certo).
**Codigo (`ff21cab`, `assign_units_positional`):** bloco sem ancora exata possivel (aff < 2) ancora por radical de 6 chars com as mesmas exigencias
(>= 2, margem >= 1, radical exclusivo de UMA unidade), conf 0,6. Teste `test_positional_radical_so_como_fallback_ancora_bloco_sem_token_exato`.
No codigo real muda so o bloco-15 do CG nos 8. Suite 2326.
**Curadoria do CG:** pinos dos blocos 06 e 15 REMOVIDOS (`0d2020a`; a mensagem do commit repete a anterior — e a remocao); fica so o bloco-08
(morfologia -> u03), residuo com nome. Reprocess registrado (tripwire): unidade mudou 0, bloco 0, sub 0, votos 42 = 42, 0 resumo: o produto
ficou identico sem os 2 pinos.
**Gates:** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 82/93 (iguais) · holdout CG puro 31/35 (igual) · curada 198/199 · 191/191 ·
55/57 (igual) · sentinela 0 · censo 58,3/35,9 · determinismo {DET}.
**Regua automatica remedida (`motor_auto.py` v2: COM vocab tambem no holdout e cache de votos DO PRODUTO copiado para a copia — a copia acumulava
votos antigos, CG 2/42 diferentes, e o holdout puro roda SEM vocab por definicao, o que fazia o bloco-02 ficar sem unidade):** 5 cursos {AUTO5} ·
holdout CG 35/35 · **CG unidade automatica: 22/93 -> 6/93 erradas** = morfologia x3 (bloco-08 -> u06; plano nao menciona morfologia) + texturas x3
(`maptextures` e pagina de videos no bloco-06 por colisao 'mapeamento'; `texturas-v3` u01 por conteudo). A primeira medicao (11/93) estava
contaminada pela falta do vocab na copia: corrigida.
**Residuo sem LLM (com nome):** 3 de morfologia (so voto de LLM de unidade ou pino) + 3 de texturas (2 erro de bloco flagado -> voter; 1 conteudo).

"""
edit(T, "## REGUA AUTOMATICA (05/09 tarde, sessao 6;", SEC + "## REGUA AUTOMATICA (05/09 tarde, sessao 6;")
edit(T, "last_updated: 2026-09-05 tarde (sessao 6; REGUA AUTOMATICA = oficial: bloco 192/199, unidade 185/191, holdout CG 35/35, sub 82/93;",
        "last_updated: 2026-09-05 tarde (sessao 6; REGUA AUTOMATICA = oficial: bloco 192/199, unidade 185/191, holdout CG 35/35, sub 82/93; CG unidade automatica 6/93 erradas; radical-fallback no motor;")

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "Gerador `feat/motor-atribuicao` @ `e0c433c` (codigo: higiene do glossario) + docs da sessao 6.",
        "Gerador `feat/motor-atribuicao` @ `ff21cab` (codigo: higiene do glossario `e0c433c` + radical-fallback `ff21cab`) + docs da sessao 6.")
edit(H, "`75b9955` `7a19208` `dc98c15` `ef4628c` `009b627` `d880f1b` `17afd2e` (docs/medicoes) · `e0c433c` (feat higiene + teste). Suite 2325.",
        "`75b9955` `7a19208` `dc98c15` `ef4628c` `009b627` `d880f1b` `17afd2e` (docs/medicoes) · `e0c433c` (feat higiene + teste) · `ff21cab` (feat radical-fallback + teste). Suite 2326.")
edit(H, "**CG `2c5e01e`** (3 reprocess\nregistrados: `c566dc3` pinos de unidade 06/08/15, `ee4c276` sinonimo de morfologia — REVERTIDO em `2c5e01e`; 0 chamadas Gemini; votos 42 = 42).",
        "**CG `0d2020a`** (4 reprocess\nregistrados: `c566dc3` pinos 06/08/15, `ee4c276` sinonimo de morfologia — REVERTIDO em `2c5e01e`, `0d2020a` pinos 06 e 15 REMOVIDOS, fica so o 08; 0 chamadas Gemini; votos 42 = 42).")
edit(H, "**CG unidade: 22/93 erradas -> 1** (`texturas-v3`) + 2 por erro de bloco\n(texturas no bloco-06, flagadas)",
        "**CG unidade: produto 1/93 errada (+2 por erro de bloco); AUTOMATICA (sem pino) 22/93 -> 6/93** (morfologia x3, texturas x3)")
edit(H, "- **Radical (6 chars) so como fallback no mapa bloco->unidade** (tokens exatos decidem; sem ancora exata, ancora por radical exclusivo) · 1 bloco muda\n"
        "  nos 8 (CG bloco-15 = pino), 0 colateral, unidade 183 = 183 · ~15 linhas em `assign_units_positional` · ganho hoje 0 (pino), valor = proximo curso sem pino · C4/C5.\n",
        "")
edit(H, "relaxada 179; higiene sozinha neutra; radical so como fallback: +1 bloco, 0 colateral, unica unificacao que sobrevive, caixa). Solucao = higiene generica (codigo, `e0c433c`) + pinos de unidade nos blocos 06 (u04, nome do SARC), 08 (u03),\n  15 (u07) — o mesmo mecanismo dos outros 7 tutores (13 pinos).",
        "relaxada 179; higiene sozinha neutra). **Entrou no motor: higiene (`e0c433c`) e radical so como fallback (`ff21cab`, +1 bloco, 0 colateral).** Pinos 06 e 15\n  removidos (produto identico); fica so o 08 (morfologia: plano nao menciona, residuo para voto de LLM de unidade). CG automatico: 22 -> 6 unidades erradas.")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Radical so como fallback no mapa bloco->unidade; pinos do CG 06 e 15 removidos (regra generica cobre); bloco-08 e residuo nomeado

**Date:** 2026-09-05
**Status:** Active
**Decision:** `assign_units_positional` ganha ancora por radical de 6 chars SO para bloco sem ancora exata possivel (aff < 2), com as mesmas exigencias da ancora exata (`ff21cab`). Os pinos de unidade dos blocos 06 e 15 do CG saem (a higiene e o radical-fallback os cobrem; produto identico); o pino do bloco-08 fica como residuo com nome ate existir voto de LLM de unidade para bloco sem evidencia lexical.
**Reasoning:** Medido nos 8 antes do codigo: RF muda 1 bloco (CG 15 -> u07 = pino), 0 colateral, unidade 183 = 183/191; radical em tudo, generico por radical entre unidades (183 -> 172), heranca por afinidade zero, alias boilerplate, bloco flagado sem imposicao e gate por confianca do texto (saldo -17 a -2) foram refutados. Regua automatica remedida com vocab e cache do produto: CG unidade 22 -> 6 erradas (morfologia x3, texturas x3), holdout 35/35, 5 cursos {AUTO5}; determinismo {DET}.
**Consequences:** CG `0d2020a` com 1 pino; motor puro/curada/holdout iguais; suite 2326. Caixa: voto de LLM de unidade para bloco sem evidencia (Gemini).
"""
assert "Radical so como fallback no mapa bloco->unidade; pinos do CG" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `simula_cg_unidade_generico.py`: RF/SG/Z0/DF no mapa bloco->unidade nos 8 (so RF sobrevive). `motor_auto.py` v2: vocab tambem no holdout + cache de votos do produto. Logs `b_rf_*.log`, `auto_rf_*.log`, `determinismo_rf.log`.\n", encoding="utf-8")
print("docs ok")
