"""Registro (06/09): golds de subunidade CG e MF APROVADOS pelo user; regua de subunidade passa a 233; remedicao das 4 reguas
(puro 5 + holdout, automatica 5 + holdout) com tripwire; censo de subunidade sem gold e 'duvida x gold'. Tracker + handoff + decisions + README."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = """## GOLDS CG E MF APROVADOS — REGUA DE SUBUNIDADE PASSA A 233; REMEDIDO (06/09, sessao 6; user: "Eu aprovo o gold de MF e CG")
**Ligacao:** `scripts/ablacao_rapida.score_subunit` (scorer compartilhado) · MF em `scripts/motor_puro.py` (`SUBUNIT_GOLD`) · CG no fim de
`_harness-2026-09-02/holdout_cg.py` (imprime `SUBUNIDADE CG`). Proposta marcada como aprovada (4 rulings como propostos). Suite 2328.
**Remedido (copias, tripwire, 0 chamadas; `c1-3/regua_tripwire.py {puro|holdout}` + `motor_auto.py {puro5|holdout}`, logs `gold6_*.log`):**
| regua | bloco (199) | unidade (191) | cobertura (57) | subunidade 5 cursos (151) | CG bloco (35) | CG subunidade (82) |
|---|---|---|---|---|---|---|
| motor puro + vocab (holdout CG sem vocab por definicao) | 186 conf-err 1 | 183 | 53 | **138 (91,4%) · 118 primario** | 31 | **39 (48%) · 27** |
| automatica v2 | 193 conf-err 0 | 185 | 53 | 138 · 118 | 35 | **49 (60%) · 36** |
| produto | 198 | 191 | 55 | 144 (93 + MF 51) | 35 | 49 · 36 |
**Automatica x 6 golds (233): 187 (80,3%) · primario 154. Produto: 193 (83%) · 162.** Por curso (automatica): SO 11/15 · IA 39/39 · ES2 26/28 ·
TCC 11/11 · MF 51/58 · CG 49/82. **Causa dos 46 erros da automatica:** SO 4 confiantes (fork/exec, regra humana) · ES2 1 ambigua + 1 confiante ·
MF 5 confiantes + 1 fraca + 1 vazia · **CG 11 vazias + 10 confiantes + 9 em que o GOLD E VAZIO e o motor preencheu (OpenGL/transformacoes sem
subtopico) + 2 ambiguas + 1 fraca.** Sem vocab (holdout puro) o CG cai para 39: o vocab vale 10 no CG.
**Numeros sem gold (censo do produto 06/09, `scripts/censo_motor_llm.py` + sinais do scorer):** subunidade vazia 44/348 (CG 17, SO 7, FR 6) ·
empate 20 (CG 10, IA 5) · ambigua 17 · score < 1: 40 (CG 22) · propagadas 25 · subtopicos no plano 229 (CG 59, SO 36, FR 33) = 1,3 material por
subtopico. **Duvida do motor x erro no gold (produto, 233):** 40 errados, 47 com sinal de duvida, 20 errados-e-com-duvida, 20 errados confiantes
(CG 15 de 33), 27 alarmes falsos: o sinal aponta o CURSO (revisar/100 CG 76, FR 59) e filtra revisao; nao mede acerto.
**Relatorio consolidado (artefato, pedido do user "todos os numeros, facil de entender"):** https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de

"""
edit(T, "## NO MAXIMO DUAS CAMADAS LLM — CAMADA 3", SEC + "## NO MAXIMO DUAS CAMADAS LLM — CAMADA 3")
edit(T, "## GOLD DE SUBUNIDADE CG E MF — PROPOSTO-CLAUDE (05/09 tarde, sessao 6; **AGUARDA APROVACAO DO USER**) + BUG: ZIPS DO MF COLIDEM",
        "## GOLD DE SUBUNIDADE CG E MF — PROPOSTO-CLAUDE (05/09 tarde, sessao 6; **APROVADO PELO USER EM 06/09**, ver secao acima) + BUG: ZIPS DO MF COLIDEM")

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "1. **APROVAR os golds de subunidade propostos** (`docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md`, coluna `ok?`): CG 82 pontuaveis",
        "1. ~~APROVAR os golds de subunidade propostos~~ **FEITO 06/09: aprovados pelo user, ligados na regua (MF em `motor_puro.py`, CG em `holdout_cg.py`,\n"
        "   scorer `ablacao_rapida.score_subunit`); automatica x 233 = 187 (80,3%), CG 49/82, MF 51/58; causas no tracker §GOLDS CG E MF APROVADOS.**\n"
        "   (texto original:) (`docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md`, coluna `ok?`): CG 82 pontuaveis")
edit(H, "Golds propostos (NAO na regua): `subunit_gt_CG.csv` 82 pontuaveis · `subunit_gt_MF.csv` 58.",
        "Golds de subunidade APROVADOS 06/09 e na regua: `subunit_gt_CG.csv` 82 pontuaveis · `subunit_gt_MF.csv` 58 (regua = 233; automatica 187 = 80,3%).")
edit(H, "- Aprovar os golds de subunidade CG/MF (COMECE POR 1). Corrigir a extracao dos zips (2).",
        "- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). Corrigir a extracao dos zips (2).")

D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### Golds de subunidade CG e MF aprovados: a regua de subunidade passa a 233 e o numero de referencia vira o da automatica nos 6 (80,3%), nao 87/93

**Date:** 2026-09-06
**Status:** Active
**Decision:** User aprovou os golds propostos (com os 4 rulings). `subunit_gt_MF.csv` entra em `scripts/motor_puro.py` e `subunit_gt_CG.csv` no `holdout_cg.py`, ambos pelo scorer compartilhado `ablacao_rapida.score_subunit`. Remedido com tripwire: automatica x 233 = 187 (80,3%; SO 11/15, IA 39/39, ES2 26/28, TCC 11/11, MF 51/58, CG 49/82); produto 193 (83%); CG puro sem vocab 39/82.
**Reasoning:** Os 87/93 eram in-sample (golds nascidos com a curadoria dos 4 cursos; regras e prompt afinados neles). O CG, unico curso nao usado para afinar, da 60%. Gold so mede: o motor nao o le; sem gold nao ha numero, so os sinais de duvida do motor, que apontam o curso (revisar/100) mas acertam so metade dos erros (20/40) e erram confiantes nos outros 20.
**Consequences:** Alvo da subunidade passa a ser o CG (33 erros: 11 vazias, 10 confiantes, 9 gold-vazio-preenchido, 2 ambiguas, 1 fraca) e o MF (7). Bloco e unidade seguem >= 96,9% na automatica. Um curso 100% novo deve esperar o numero do CG, nao o dos 93.
"""
assert "Golds de subunidade CG e MF aprovados" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `regua_tripwire.py {puro|holdout}` (motor puro --com-vocab / holdout CG com tripwire) + `motor_auto.py` -> `gold6_*.log`: golds CG/MF aprovados 06/09; automatica x 233 = 187 (80,3%), CG 49/82 (puro sem vocab 39), MF 51/58. `docs_c1_3l.py` registra.\n", encoding="utf-8")
print("docs ok")
