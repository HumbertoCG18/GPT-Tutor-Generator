"""Registro (06/09, sessao 6): regra da secao (S1b, 4d649c4) — gates, reprocess registrado, produto, fila. Args: 1 = resumo do reprocess,
2 = determinismo, 3 = produto x 6 golds, 4 = fila/100 (ex.: '33,0 (115/348)')."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
REP, DET, PROD, FILA = (sys.argv + ["?", "?", "?", "?"])[1:5]


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
edit(T, "Candidata a entrar: S1b (ultimo recurso; mesma rota da 2a passada; reason `secao-nomeia-subtopico`).\n",
        "**ENTROU (`4d649c4`, `resolver_apply._secao_nomeia_subtopico` no fim da 2a passada; reason `secao-nomeia-subtopico`; a 2a passada perdeu o\n"
        "retorno antecipado `if not extra` para a regra do titulo e a da secao valerem sempre; teste `test_secao_do_moodle_decide_so_onde_nada_decidiu`).\n"
        f"**Gates (copias, tripwire, 0 chamadas; `secao_*.log`):** motor puro +vocab 186/199 · 183/191 · 53/57 · sub 5 cursos 138/151 (117) · holdout CG puro 31/35 ·\n"
        f"CG sub puro (sem vocab) 45 -> 47/82 · automatica 193 · 185 · 53 · 138/151 · holdout 35/35 · **CG sub automatica 56 -> 58/82 (45 primario)** ·\n"
        f"**automatica x 233: 194 -> 196 (84,1%)** · suite 2334 · determinismo {DET} · sentinela 0. (O +1 do MF `exemplos-zip` da simulacao nao se\n"
        f"reproduziu no motor: o filtro de genericos do motor e o do curso, nao a lista da simulacao.)\n"
        f"**Reprocess registrado dos 8 (`c1-3/reprocess_8_secao.py`):** {REP}. **Produto x 6 golds: {PROD}.** Fila {FILA} por 100.\n")

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "Regra do titulo (`34d8b19`, +2 -0): automatica x 233 194 (83,3%), CG 56/82; produto",
        f"Regra da secao S1b (`4d649c4`, +3 -0 simulado, +2 no motor): automatica x 233 196 (84,1%), CG 58/82; produto {PROD}; gold `intro` corrigido pelo oraculo (origens).\n"
        "Regra do titulo (`34d8b19`, +2 -0): automatica x 233 194 (83,3%), CG 56/82; produto")

D = GEN / ".mex/context/decisions.md"
ENTRY = f"""

---

### Subunidade: secao do Moodle que nomeia exatamente um subtopico decide onde nem a 1a nem a 2a passada decidiram (S1b); Moodle e o oraculo tambem para o gold de subunidade

**Date:** 2026-09-06
**Status:** Active
**Decision:** No fim da 2a passada, material ainda vazio ou empatado recebe o subtopico que a SECAO do Moodle nomeia, se for exatamente um da unidade (`4d649c4`, reason `secao-nomeia-subtopico`). Gold do CG `intro` corrigido pelo oraculo (secao "Origens" -> primario `origens`; conceitos/areas-relacionadas extras).
**Reasoning:** Pedido do user: comparar o gold de subunidade do CG com o Moodle, que e o oraculo. Onde a secao nomeia um subtopico, gold = secao em 27/29; as 2 divergencias sao o `intro` (gold errado) e `exemplozbuffer` (gold mais especifico que a secao). Regra simulada pela rota real nos 6 golds: S1b +3 -0; S1 (sobrepoe a 2a passada) +5 -3; S2 (sobrepoe confiante) +5 -13 — a secao nomeia o pai quando o gold e o filho. Gates: bloco/unidade/cobertura iguais; CG 56 -> 58/82; automatica x 233 194 -> 196; determinismo {DET}.
**Consequences:** Reprocess registrado: {REP}. Produto x 6 golds {PROD}. Fila {FILA}/100. A secao do Moodle e sinal de subunidade so como ultimo recurso; como override e refutada.
"""
assert "secao do Moodle que nomeia exatamente um subtopico decide" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `simula_secao_sub.py` (S1 +5/-3, S1b +3/-0, S2 +5/-13) · `reprocess_8_secao.py`. Logs `secao_*.log`, `reprocess_8_secao.log`, `determinismo_secao.log`.\n", encoding="utf-8")
print("docs ok")
