"""Registro (06/09, sessao 6): regra 'titulo nomeia outro subtopico vence decisao confiante' (34d8b19) — simulacao, gates,
reprocess registrado. Args: 1 = resumo do reprocess (ex.: 'sub mudou 2 (CG 2), bloco 0, unidade 0; CG HEAD xxxx'), 2 = determinismo,
3 = produto x 6 golds (ex.: '199/233 (85,4%), primario 166'), 4 = fila/100 (ex.: '33,0')."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
REP, DET, PROD, FILA = (sys.argv + ["?", "?", "?", "?"])[1:5]


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = f"""## CG CONFIANTES ERRADOS — TITULO NOMEIA OUTRO SUBTOPICO (06/09, sessao 6, FEITO; gerador `34d8b19`; user: "vamos medir essa alavanca")
**Regra (2a passada, `resolver_apply._subtopico_nomeado_no_titulo`):** decisao CONFIANTE da 1a passada cai quando o titulo + label do Moodle do
material contem uma parte de rotulo (decomposicao) de OUTRO subtopico Y da mesma unidade, Y e unico, e NENHUMA frase (rotulo/aliases) do vencedor
esta no titulo. Reason `titulo-nomeia-subtopico`. Caso: CG "Exercicios de geometria computacional" ia para `entidades-geometricas` (7,74, por
'Vetor/Pontos/Retas' no corpo) com o gold `algoritmos-de-geometria-computacional` em 0,96.
**Simulado (`c1-3/simula_titulo_confiante.py`, rota real: 1a passada + 2a passada REAL + regra por cima; base reproduz o gravado 192/233, 0 divergencias):**
T1 (parte no titulo, vencedor ausente do titulo) **+2 -0** · T1b (T1 e Y > 0 no corpo) +2 -0 · T2 (T1 so com margem pequena, 2o >= 50% do 1o) 0/0
— a margem nao separa (7,74 x 0,96). Entrou T1 (mais simples; T1b exigiria re-pontuar). Os outros 5 confiantes errados do CG NAO tem parte de rotulo
no titulo (exercicios-sobre-curvas x2 "Exercicios sobre curvas" com hermite 4,92 x catmull-rom 4,27 ambos no texto; vis2d x2; basico3d-py) e
seguem: sao escolha entre dois assuntos presentes, sem sinal generico.
**Gates (copias, tripwire, 0 chamadas; `titulo_*.log`):** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 5 cursos 138/151 (117) · holdout CG
puro 31/35 · CG sub puro 45/82 · automatica 193 conf-err 0 · 185 · 53 · 138/151 · holdout 35/35 · **CG sub automatica 54 -> 56/82 (42 primario)** ·
**automatica x 233: 192 -> 194 (83,3%)** · suite 2333 · determinismo {DET} · sentinela 0.
**Reprocess registrado dos 8 (`c1-3/reprocess_8_titulo.py`, tripwire de produto):** {REP}. **Produto x 6 golds: {PROD}.** Fila {FILA} por 100.
**CG, o que resta (26/82):** 9 gold-vazio (5 pelo alias 'OpenGL' do vocab LLM em `conceitos`: Gemini) · 5 paginas de LOGIN (SYNC) · 3 morfologia (unidade a
montante) · 5 confiantes entre dois assuntos presentes · curvasparametricas (empate hermite = b-spline, gold e o pai) · 3 vazias sem alias no texto
(intro, exercicio-com-animacao, aula-gravada). Sem LLM e sem dado novo, o teto do CG na automatica e ~56-58/82.

"""
edit(T, "## CG SUBUNIDADE 60% — DIAGNOSTICO DOS 33 E DECOMPOSICAO DE ROTULOS NO MOTOR", SEC + "## CG SUBUNIDADE 60% — DIAGNOSTICO DOS 33 E DECOMPOSICAO DE ROTULOS NO MOTOR")

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "(`ff3eda7`): automatica x 233 187 -> 192 (82,4%), CG 49 -> 54/82, produto 193 -> 197 (84,5%); tracker §CG SUBUNIDADE 60% e §FILA DE REVISAO — CAMADA LLM CORTADA.**",
        "(`ff3eda7`): automatica x 233 187 -> 192 (82,4%), CG 49 -> 54/82, produto 193 -> 197 (84,5%); tracker §CG SUBUNIDADE 60% e §FILA DE REVISAO — CAMADA LLM CORTADA.\n"
        f"Regra do titulo (`34d8b19`, +2 -0): automatica x 233 194 (83,3%), CG 56/82; produto {PROD}; tracker §CG CONFIANTES ERRADOS. Teto do CG sem LLM/sem dado novo ~56-58/82.**")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Subunidade: titulo que nomeia outro subtopico (parte do rotulo) vence decisao confiante que o titulo nao nomeia

**Date:** 2026-09-06
**Status:** Active
**Decision:** Na 2a passada, decisao confiante da 1a cai quando o titulo + label do Moodle contem uma parte de rotulo de outro subtopico Y da unidade (unico) e nenhuma frase do vencedor esta no titulo (`34d8b19`, reason `titulo-nomeia-subtopico`). Unica excecao ao principio "decisao confiante nunca e sobreposta" — e o professor nomeando o assunto no titulo.
**Reasoning:** Simulado pela rota real nos 6 golds (base reproduz o gravado): +2 -0; variante por margem 0/0 (a margem nao separa 7,74 x 0,96). Gates: bloco/unidade/cobertura iguais; 5 cursos 138 = 138; CG 54 -> 56/82; automatica x 233 194 (83,3%); determinismo {DET}.
**Consequences:** Reprocess registrado: {REP}. Produto x 6 golds {PROD}. Resta no CG (26/82): 9 gold-vazio (alias 'OpenGL' do vocab LLM), 5 login (dado), 3 morfologia (unidade), 5 confiantes entre dois assuntos presentes, 4 vazias/empate sem alias. Teto sem LLM e sem dado novo ~56-58/82.
"""
assert "titulo que nomeia outro subtopico (parte do rotulo) vence decisao confiante" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `simula_titulo_confiante.py` (T1 +2/-0, T1b +2/-0, T2 0/0) · `reprocess_8_titulo.py`. Logs `titulo_*.log`, `reprocess_8_titulo.log`.\n", encoding="utf-8")
print("docs ok")
