"""Registro: propagacao de vocabulario por headings no motor (4a239d9) + reprocess registrado dos 8 + gates. Arg1 = linha da regua automatica nos 5."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
AUTO5 = sys.argv[1] if len(sys.argv) > 1 else "AUTO5_PLACEHOLDER"


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = f"""## SUBUNIDADE SEM LLM — PROPAGACAO DE VOCABULARIO POR HEADINGS NO MOTOR (05/09 noite, sessao 6, FEITO; gerador `4a239d9`)
**Pedido do user:** arrumar as subunidades de maneira automatica, sem LLM. **Raiz:** o plano nomeia categorias e o material nomeia algoritmos; o vocab
compilado por LLM nao emitiu 'perceptron'/'rede neural'/'MLP' para o IA e o remendo era o glossario MANUAL (curadoria).
**Regra (`resolver_apply.propagar_vocabulario_por_headings`, 2a passada):** token EXCLUSIVO dos headings/titulo dos materiais que a 1a passada atribuiu
com confianca (>= 0,7) a um subtopico vira alias desse subtopico; so materiais vazios/ambiguos/fracos sao repontuados; decisao confiante nunca e
sobreposta. Salvaguardas medidas, cada uma: sem stems genericos do motor ('exemplo'/'respostas' viravam alias: CG `slab` e MF `respostas` caiam) · df
<= 25% dos materiais ('sumario'/'aula' do TCC) · >= 2 confiantes · exclusivo de UM subtopico · so nos nao-confiantes (o CG perdia 8 confiantes sem isso).
Limiares em `thresholds.T` (SUBUNIT_PROPAG_CONF 0,7 · MIN_ENTRIES 2 · DF_MAX 0,25; grade de 8 pontos em `c1-3/simula_propaga_grid_df025.log`).
Teste `tests/test_subunit_propagacao.py` (2). Suite 2328. Reason gravada: `propagado-headings`.
**Medido antes de entrar (`c1-3/simula_propaga_headings_6golds.py`, 6 golds = 233, CG/MF propostos):** 182 -> 187, **+5 -0**, 4 mudancas erro->erro;
FR/LR 0 mudancas. Alias = label de sessao do SARC (`simula_alias_sessao_sub.py`): 0 efeito nos 93.
**Gates (tripwire, 0 chamadas):** motor puro +vocab bloco 186/199 · unidade 183/191 · cobertura 53/57 · **sub 82 -> 87/93 (83 primario)** · automatica {AUTO5}
· holdout CG puro 31/35 · automatico 35/35 · CG sub automatico 49/82 (1 propagado) · curada bloco 198/199 · 191/191 · 55/57 · produto x 6 golds de
subunidade 193/233 com extras (igual; primario 162) · sentinela 0 · censo revisar/100 57,5 (sub-empate 24 -> 20, sub-ambigua 19 -> 17) · determinismo 8/8, 0 arquivos.
**Reprocess registrado dos 8 (`c1-3/reprocess_8_propagacao.py`, tripwire de produto; NAO commita quando so `updated_at` muda — caixa aplicada):**
MF `7a8707a` (sub mudou 4: t1-thy, hoare, invariantes, terminacao -> verificacao-de-programas; os zips com resumo colidido) · IA `0075334` (2: lista-de-
exercicios-i, p2-202401 -> busca-adversaria) · ES2 `4c8011b` (6, todos dentro dos extras do gold) · TCC `621c292` (1: aula-16 -> prova-da-indecidibilidade) ·
SO/LR/FR/CG so `updated_at`, sem commit. Bloco 0 · unidade 0 · flagadas iguais · propagados 26 nos 8.
**O que sobra na subunidade do motor puro (6/93):** SO fork/exec x4 (gold pela regra humana 'apoio rotula pelo card', que o IA contradiz: sem regra
generica), ES2 `devops`/`kubernetes` (quase-empate). No IA o automatico agora iguala o glossario manual (39/39) — o remendo humano deixou de ser necessario.

"""
edit(T, "## CG UNIDADE SEM LLM E SEM PINO — RADICAL-FALLBACK", SEC + "## CG UNIDADE SEM LLM E SEM PINO — RADICAL-FALLBACK")
edit(T, "CG unidade automatica 6/93 erradas; radical-fallback no motor;",
        "CG unidade automatica 6/93 erradas; radical-fallback no motor; propagacao por headings no motor: sub puro 82 -> 87/93;")

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "Gerador `feat/motor-atribuicao` @ `ff21cab` (codigo: higiene do glossario `e0c433c` + radical-fallback `ff21cab`) + docs da sessao 6.",
        "Gerador `feat/motor-atribuicao` @ `4a239d9` (codigo: higiene `e0c433c` + radical-fallback `ff21cab` + propagacao por headings `4a239d9`) + docs da sessao 6.")
edit(H, "· `ff21cab` (feat radical-fallback + teste). Suite 2326.", "· `ff21cab` (feat radical-fallback + teste) · `4a239d9` (feat propagacao por headings + teste). Suite 2328.")
edit(H, "Tutores: MF `afb83cb` · SO `0921948` · IA `d7d81ed` · ES2 `ba7d2c8` · TCC `13ced08` · LR `d139547` · FR `fd7814f` · **CG `0d2020a`** (4 reprocess",
        "Tutores: **MF `7a8707a` · SO `0921948` · IA `0075334` · ES2 `4c8011b` · TCC `621c292`** · LR `d139547` · FR `fd7814f` · **CG `0d2020a`** (reprocess da propagacao:\nMF/IA/ES2/TCC commitados, SO/LR/FR/CG so `updated_at` e nao commitados; CG: 4 reprocess")
edit(H, "**Regua automatica (v2): bloco 193/199 · unidade 185/191 · sub 82/93 · holdout 35/35 · CG unidade 6/93 erradas sem pino.**",
        f"**Regua automatica (v2, pos-propagacao): {AUTO5} · holdout 35/35 · CG unidade 6/93 erradas sem pino.**")
edit(H, "**Abaixo de 95% so a subunidade (vocabulario). Caminhos genericos:** vocab compilado melhor (LLM; hoje nao emite 'perceptron'/'MLP' para o IA) ·\npropagacao por headings (+5/-0 no gold, valida com o gold CG/MF) · voto de LLM para unidade de bloco sem evidencia lexical (CG bloco-08; 1 chamada por bloco assim).",
        "**Subunidade: propagacao por headings ENTROU no motor (`4a239d9`): motor puro 82 -> 87/93; o IA automatico iguala o glossario manual (39/39).**\nResto sem LLM: SO fork/exec x4 (regra humana do gold contradiz o IA) e ES2 quase-empates x2. Caminhos com LLM: vocab compilado melhor · voto de LLM para\nunidade de bloco sem evidencia lexical (CG bloco-08; 1 chamada por bloco assim).")
edit(H, "- **Propagacao de vocabulario por headings para a subunidade (sem LLM)** · +5/-0 no gold de 93 (conf >= 0,7, token em >= 2 confiantes, df <= 25%, so nos\n  nao-confiantes), curada intacta; MF 6 / CG 9 mudancas sem gold com erros a olho · sim, ~40 linhas em `apply_unit_subunit_fields` · **depois do gold CG/MF aprovado**.\n",
        "")
edit(H, "   ligar `subunit_gt_{CG,MF}.csv` em `scripts/motor_puro.py` (`SUBUNIT_GOLD`) e REMEDIR a propagacao de vocabulario por headings nos 8\n   (`c1-3/simula_propaga_headings*.py`: +5/-0 no gold de 93, mas MF 6 / CG 9 mudancas sem gold — o gold novo e o que decide).",
        "   ligar `subunit_gt_{CG,MF}.csv` em `scripts/motor_puro.py` (`SUBUNIT_GOLD`): a propagacao ja entrou (medida +5/-0 nos 6 golds com os propostos);\n   o gold aprovado passa a ser regua permanente de CG/MF.")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Subunidade: propagacao de vocabulario por headings entra no motor como 2a passada (so onde a 1a nao decidiu); glossario manual deixa de ser necessario no IA

**Date:** 2026-09-05
**Status:** Active
**Decision:** `apply_unit_subunit_fields` ganha uma 2a passada: tokens exclusivos dos headings/titulo dos materiais confiantes (>= 0,7) de um subtopico viram aliases dele e so os materiais vazios/ambiguos/fracos sao repontuados (`4a239d9`, limiares em `thresholds.T`). Decisao confiante nunca e sobreposta. Reason gravada `propagado-headings`.
**Reasoning:** Pedido do user: subunidade automatica sem LLM, gold so mede. Medido em memoria pela rota real nos 6 golds (233): +5 -0 (IA perceptron x3 + mlp-xor, SO exemplo3), FR/LR 0 mudancas; grade de 8 pontos estavel em conf 0,7; cada salvaguarda tem a perda que evita medida (stems genericos, df 25%, minimo 2 confiantes, exclusividade, so nao-confiantes). Gates: motor puro sub 82 -> 87/93 com bloco/unidade iguais; automatica {AUTO5}; holdout 35/35; curada igual; produto x 6 golds 193/233 igual; determinismo 8/8.
**Consequences:** Reprocess registrado dos 8 (MF/IA/ES2/TCC commitados; 4 tutores so `updated_at`, sem commit). Residuo da subunidade no puro: SO fork/exec x4 (regra humana do gold que o IA contradiz) e ES2 quase-empates x2.
"""
assert "propagacao de vocabulario por headings entra no motor" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `simula_propaga_headings_6golds.py` (6 golds, filtro de stems genericos) · `simula_alias_sessao_sub.py` (0 efeito) · `reprocess_8_propagacao.py` (registrado, tripwire; pula commit so `updated_at`). Logs `b_prop_*.log`, `auto_prop_*.log`, `determinismo_prop.log`, `reprocess_8_propagacao.log`.\n", encoding="utf-8")
print("docs ok")
