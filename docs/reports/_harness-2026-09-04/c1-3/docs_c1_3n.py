"""Registro (06/09, sessao 6): (1) fila de revisao sem a camada llm (0673150) + reprocess registrado; (2) diagnostico dos 33 erros de
subunidade do CG; (3) decomposicao de rotulos compostos na 2a passada (ff3eda7) + gates + reprocess registrado; (4) higiene estendida
(H2) refutada. Arg1 = resultado do determinismo (ex.: '8/8, 0 arquivos')."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
DET = sys.argv[1] if len(sys.argv) > 1 else "DET_PLACEHOLDER"


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = f"""## CG SUBUNIDADE 60% — DIAGNOSTICO DOS 33 E DECOMPOSICAO DE ROTULOS NO MOTOR (06/09, sessao 6, FEITO; gerador `ff3eda7`)
**Pedido do user:** "vamos resolver o problema de subunidades de CG; o que mais me preocupa e o 60%". **Diagnostico pela rota real
(`c1-3/diag_cg_sub.py CG`, copia na regua automatica, 0 chamadas) — os 33 erros por familia:** (a) **gold vazio, motor preencheu 9**: OpenGL x5 vao
para u01/`conceitos` porque o vocab LLM pendurou 'OpenGL'/'OpenGL 3D' como sinonimo de "Conceitos" (secao 'Biblioteca OpenGL'); transformacoes/
instanciamento x4 em u04 sem subtopico no plano · (b) **vazia 12** (3 sao paginas do Moodle capturadas como LOGIN, sem texto): bezier x4 (rotulo
"Bezier e Algoritmo de Casteljau" so casa a FRASE inteira; 'bezier' sozinho valia 0,12), curvasparametricas (empate hermite = b-spline 6,44), intro,
exercicio-com-animacao, exercicioduascores, aula-gravada (UNIDADE errada a montante: morfologia u06 x gold u03) · (c) **confiante 9**: morfologia x2
(unidade errada a montante + colisao 'matematica' com "A matematica das projecoes"), geometria computacional x2 (titulo diz "geometria computacional",
rotulo e "Algoritmos de Geometria Computacional": frase nao casa; `entidades-geometricas` ganha por 'Vetor/Pontos/Retas'), exercicios-sobre-curvas
x2 (hermite 4,92 x catmull-rom 4,27, ambos no texto), exercicios-teoricos-vis2d x2, basico3d-py (perspectiva 8,98 x camera 4,46) · (d) ambigua 2,
fraca 1. **Raiz generica:** o plano nomeia por FRASE COMPOSTA e o material nomeia a PARTE.
**Alavancas simuladas (`c1-3/simula_cg_sub_levers.py`, 1a passada em memoria, 6 golds = 233):** H2 = higiene estendida (sinonimo LLM que e SUBFRASE
de nome de secao sai; 'OpenGL' <- 'Biblioteca OpenGL'): **+0 -2 (SO threads perdem 'Processos'): REFUTADA**. D = decomposicao de rotulos
(partes de 'A e B'/'A ou B'/'A: B'/'A (B)'/'A / B' + rotulo com cabeca generica no curso 'Algoritmos de X' -> 'X'): **+9 -1 (CG 49 -> 57)**.
**Codigo (`ff3eda7`):** `timeline.index._label_parts` + `resolver_apply._partes_de_rotulo`, 2a FONTE de aliases da 2a passada
(`propagar_vocabulario_por_headings`), com as salvaguardas da propagacao: teto de df 25% dos materiais, exclusividade no CURSO INTEIRO (parte
contida no rotulo/aliases de outro topico ou no titulo de uma unidade nao entra — sem isso 'saida' de "Dispositivos de entrada e saida" no SO custava
1 cobertura e 'Internet' do rotulo-aspirador do FR derrubava o teste do holdout FR), e so onde a 1a passada nao decidiu. Reason `rotulo-decomposto`.
Primeira versao (na taxonomia, 1a passada, sem df): CG 57 mas cobertura SO 19 -> 18 e teste do FR vermelho — por isso foi para a 2a passada.
Testes `tests/test_label_decomposition.py` (4). Suite 2332.
**Gates (copias, tripwire, 0 chamadas; `decomp2_*.log`):** motor puro +vocab bloco 186/199 conf-err 1 · unidade 183/191 · cobertura 53/57 · sub 5 cursos
138/151 (117 primario, era 118) · holdout CG puro 31/35 · **CG sub puro (sem vocab) 39 -> 45/82** · automatica bloco 193 conf-err 0 · 185 · 53 · 138/151 ·
holdout 35/35 · **CG sub automatica 49 -> 54/82 (40 primario)** · **automatica x 233: 187 -> 192 (82,4%)** · determinismo {DET} · sentinela 0.
**Reprocess registrado dos 8 (`c1-3/reprocess_8_decomp.py`, tripwire de produto):** subunidade mudou 15 (CG 10: bezier x4, basico3d-cpp,
programabasico3d, img, listadeexercicios, resolucao-de-prova, exercicioduascores · IA 3 · MF 1 `intro` · ES2 1 `devops`), bloco 0, unidade 0.
**Produto x 6 golds: 193 -> 197/233 (84,5%; primario 164)**: CG 49 -> 54, **ES2 28 -> 27** (`devops`: era ambiguo em `conceito-de-devops`; a parte
"Integracao continua" do rotulo "Integracao continua (CI)" — que nunca casava como frase por causa do '(CI)' — esta no texto da aula de DevOps; o gold
diz conceito). MF 51, SO 15, IA 39, TCC 11. Curada bloco 198/199 · 191/191 · 55/57 (intacta). HEADs: MF `ed31d99` · IA `74fec68` · ES2 `0fe0f53` ·
CG `929cdc3` (SO/TCC/LR/FR so `updated_at`).
**O que resta no CG (28/82):** 9 gold-vazio (5 pelo alias 'OpenGL' do vocab LLM em `conceitos` — a higiene estendida perde 2 no SO; caminho e recompilar
o vocab com o Gemini ou regra de 'ferramenta' sem subtopico) · 3 morfologia (unidade errada a montante, residuo conhecido) · 5 paginas de LOGIN
(dado, SYNC) · confiantes errados (geometria computacional x2, exercicios-sobre-curvas x2, vis2d x2, basico3d-py): a 2a passada nao toca decisao
confiante por desenho; alavanca candidata = "confiante com margem pequena e parte do rotulo no TITULO" (medir).

## FILA DE REVISAO — CAMADA LLM CORTADA (06/09, sessao 6, FEITO; gerador `0673150`; decisao do user "diminuir os arquivos para revisar")
`routing/revisar.py`: voto de LLM na janela nao e mais pendencia (era 79 dos 200 itens por 2 erros; bloco por voto 75/76 no gold). Teste ajustado
(`test_llm_na_janela_nao_e_pendencia`). **Reprocess registrado dos 8 (`c1-3/reprocess_8_revisar.py`):** revisar mudou 80, fila 200 -> 120, bloco/
unidade/subunidade 0 mudancas; commits MF `00539d2` SO `f513ba0` IA `d67cd58` ES2 `0f92ae5` TCC `082b728` FR `4c64ed6` CG `f920f21` (LR so `updated_at`).
Apos a decomposicao: **fila 115/348 = 33,0 por 100** (duvida 102 + mudou 13; sub-empate 20 -> 12, sub-ambigua 17 -> 15). A UI segue lendo
`temporal_block_method == "llm"` como informacao. 'conflito' (53, 0 erros de unidade) fica ate a subunidade do CG melhorar.

"""
edit(T, "## FILA DE REVISAO (`revisar`/100 = 57,5) — RENDIMENTO MEDIDO CONTRA OS GOLDS", SEC + "## FILA DE REVISAO (`revisar`/100 = 57,5) — RENDIMENTO MEDIDO CONTRA OS GOLDS")

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "**Camada 3 (resumos de codigo) medida (06/09, tracker §NO MAXIMO DUAS CAMADAS):**",
        "**06/09 noite — golds CG/MF aprovados (regua 233) · fila sem a camada llm (57,5 -> 33,0 por 100; `0673150`) · decomposicao de rotulos na 2a passada\n"
        "(`ff3eda7`): automatica x 233 187 -> 192 (82,4%), CG 49 -> 54/82, produto 193 -> 197 (84,5%); tracker §CG SUBUNIDADE 60% e §FILA DE REVISAO — CAMADA LLM CORTADA.**\n"
        "**Camada 3 (resumos de codigo) medida (06/09, tracker §NO MAXIMO DUAS CAMADAS):**")
edit(H, "- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). **Fila de revisao: cortar a camada `llm` da metrica (57,5 -> 34,8; perde 2 de 41 erros;\n  tracker §FILA DE REVISAO)** — decisao do user, muda metrica de produto (decisao B 02/09). Corrigir a extracao dos zips (2).",
        "- ~~Aprovar os golds de subunidade CG/MF~~ (feito 06/09). ~~Fila de revisao: cortar a camada `llm`~~ (feito 06/09, `0673150`). Corrigir a extracao dos zips (2).")
t = H.read_text(encoding="utf-8")
t = t.replace("Tutores: **MF `7a8707a` · SO `0921948` · IA `0075334` · ES2 `4c8011b` · TCC `621c292`** · LR `d139547` · FR `fd7814f` · **CG `0d2020a`**",
              "Tutores (06/09 noite, apos fila + decomposicao): **MF `ed31d99` · SO `f513ba0` · IA `74fec68` · ES2 `0fe0f53` · TCC `082b728` · LR `d139547` · FR `4c64ed6` · CG `929cdc3`** (antes: MF `7a8707a` · SO `0921948` · IA `0075334` · ES2 `4c8011b` · TCC `621c292` · LR `d139547` · FR `fd7814f` · CG `0d2020a`)", 1)
H.write_text(t, encoding="utf-8")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Subunidade: partes do rotulo composto do plano viram aliases na 2a passada (teto de df, exclusividade no curso); fila de revisao sem a camada llm

**Date:** 2026-09-06
**Status:** Active
**Decision:** (1) `resolver_apply._partes_de_rotulo` alimenta a 2a passada (`propagar_vocabulario_por_headings`) com as partes dos rotulos compostos ('Bezier e Algoritmo de Casteljau' -> 'Bezier', 'Algoritmo de Casteljau'; 'Algoritmos de X' -> 'X' quando a cabeca e generica no curso), sob as salvaguardas da propagacao (df <= 25%, exclusividade no curso inteiro incluindo titulos de unidade, nunca sobre decisao confiante). Reason `rotulo-decomposto`. `ff3eda7`. (2) `revisar_de` deixa de classificar voto de LLM na janela como pendencia (`0673150`).
**Reasoning:** Diagnostico dos 33 erros do CG pela rota real: o plano nomeia por frase composta e o material pela parte (bezier x4 valiam 0,12). Simulado na 1a passada: +9 -1 nos 6 golds; na taxonomia (1a passada, sem df) custava 1 cobertura no SO ('saida' = titulo da unidade) e o teste do holdout FR ('Internet'): por isso a rota e a 2a passada com df. Gates: bloco/unidade/cobertura iguais em todas as reguas; CG automatica 49 -> 54/82; automatica x 233 187 -> 192; produto 193 -> 197 (ES2 devops 28 -> 27: parte "Integracao continua" de "Integracao continua (CI)" esta na aula de DevOps; gold diz conceito). Fila: camada llm era 79/200 itens por 2 erros (voto 75/76 no gold): 57,5 -> 33,0 por 100 sem perder bloco/unidade/subunidade. Determinismo {DET}.
**Consequences:** Reprocess registrado dos 8 duas vezes (fila; decomposicao): HEADs MF ed31d99, SO f513ba0, IA 74fec68, ES2 0fe0f53, TCC 082b728, LR d139547, FR 4c64ed6, CG 929cdc3. Residuo do CG (28/82): 9 gold-vazio (alias 'OpenGL' do vocab LLM em `conceitos`), 3 morfologia (unidade a montante), 5 paginas de login (dado), confiantes errados (a 2a passada nao os toca por desenho). Higiene estendida contra nomes de secao REFUTADA (+0 -2).
"""
assert "partes do rotulo composto do plano viram aliases na 2a passada" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `diag_cg_sub.py [CG|MF|...]`: erros de subunidade por causa pela rota real (33 do CG). `simula_cg_sub_levers.py`: H2 higiene estendida (+0/-2, refutada) e D decomposicao de rotulos (+9/-1). `reprocess_8_revisar.py` / `reprocess_8_decomp.py`: reprocess registrados (fila 200 -> 120; sub 15 mudancas). Logs `decomp_*.log` (v1, na taxonomia: cobertura -1), `decomp2_*.log` (v2, 2a passada: gates limpos), `determinismo_decomp.log`.\n", encoding="utf-8")
print("docs ok")
