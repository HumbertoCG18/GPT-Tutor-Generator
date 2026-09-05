"""Registro da propagacao de vocabulario por headings (sem LLM) — +5/-0 no gold de subunidade, mas sem gold nos 4 outros
cursos: nao entra no motor; vira decisao do user (gold de subunidade CG/MF, C5). Idempotente por assert."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:70], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
edit(T, "(camada humana, ou re-compilacao por LLM quando liberado). Fora disso, o que sobra e voto (LLM) ou pino (camada humana), por desenho.",
        "(camada humana, ou re-compilacao por LLM quando liberado).\n"
        "**PROPAGACAO DE VOCABULARIO POR HEADINGS (sem LLM, 05/09 tarde; `c1-3/simula_propaga_headings*.py`, em memoria pela rota real):** tokens\n"
        "EXCLUSIVOS dos headings/titulo dos materiais que o motor ja atribuiu com confianca a um subtopico viram aliases desse subtopico (2 passadas;\n"
        "token em > 25% dos materiais do curso = generico; 2a passada so onde a 1a nao decidiu com confianca). **Gold (93): 82 -> 87/93, +5 -0**\n"
        "(IA perceptron x3 + mlp-xor via `rede`/`nearest`/`neighbors`; SO `exemplo3`) no ponto (conf >= 0,7; token em >= 2 confiantes; df <= 25%);\n"
        "curada 93/93 intacta. Grade df 0,25 (8 pontos): (0,5;2) +5/-3 · (0,5;3) +3/0 · (0,6;2) +5/-3 · **(0,7;2) +5/0** · (0,7;3) +4/0 · (0,8;2) +5/-1 ·\n"
        "(0,9;2) 0/0 · (0,9;3) 0/0; sem o teto de df, (0,9;2) dava -20 (poucos confiantes = exclusividade vazia). **MAS nos 4 cursos SEM gold de\n"
        "subunidade (weak-only, `simula_propaga_semgold_weak.log`): MF 6 mudancas, CG 9, FR 0, LR 0 — varias visivelmente erradas** (CG\n"
        "`transformacoesgeometricas` -> recorte, `aula-gravada` da Morfologia -> a-matematica-das-projecoes, `slab` geometria-comp -> operacoes-com-\n"
        "vetores; MF `hoare` logica-de-hoare -> verificacao-de-programas). Sem rescore dos confiantes o CG ainda perdia 8 decisoes confiantes (19 mudancas).\n"
        "**Nao entra no motor: saldo nos 8 desconhecido sem gold.** Caminho sem LLM = humano: gold de subunidade do CG (e MF) proposto-claude para\n"
        "aprovacao do user (formato de 25/08), depois remedir nos 8 (C5, \"gold proprio ou ruling\"); ou pino/glossario manual para os 4 do IA (curadoria).\n"
        "Fora disso, o que sobra e voto (LLM) ou pino (camada humana), por desenho.")

H = GEN / "docs/reports/2026-09-05-handoff-fila-campanhas.md"
edit(H, "- **FILE_MAP titulo = label perde o stem**",
        "- **Propagacao de vocabulario por headings para a subunidade (sem LLM):** +5/-0 no gold (82 -> 87/93), curada intacta, mas MF 6 e CG 9 mudancas\n"
        "  sem gold com varias erradas a olho (tracker §OS 32 ERROS) · sim, ~40 linhas em `apply_unit_subunit_fields` (2a passada) · **C5: so depois de gold de\n"
        "  subunidade do CG/MF proposto-claude + aprovado pelo user** · +4 IA +1 SO no puro; risco medido no CG sem gold.\n"
        "- **FILE_MAP titulo = label perde o stem**")
edit(H, "- **Desligar `gemini_auto_summarize` na UI enquanto o Gemini estiver bloqueado** (incidente de 60 chamadas em 05/09 tarde; sem isso qualquer\n"
        "  reprocess que mude hash de codigo chama a API). O tripwire cobre so as medicoes com o shim.\n",
        "- ~~Desligar `gemini_auto_summarize` na UI~~ **FEITO 05/09 tarde pelo user** (`~/.gpt_tutor_config.json`: False, verificado). Religar so quando liberar o Gemini.\n"
        "- **Gold de subunidade do CG (93) e MF (66) proposto-claude para sua aprovacao** (C5): destrava a propagacao de vocabulario (+5 no gold atual)\n"
        "  e da regua a 4 cursos que hoje so listam flips. Custo: revisao humana; 0 LLM.\n")

D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### Propagacao de vocabulario por headings (sem LLM) fica na caixa: +5 no gold de subunidade, mas sem gold nos outros 4 cursos nao entra

**Date:** 2026-09-05
**Status:** Active
**Decision:** A 2a passada de subunidade (tokens exclusivos dos headings dos confiantes viram aliases; teto de df 25%; so onde a 1a passada nao decidiu) NAO entra no motor agora, apesar de 82 -> 87/93 no gold e curada intacta. Entra so depois de gold de subunidade do CG e do MF (proposto-claude, aprovado pelo user) e saldo medido nos 8.
**Reasoning:** No gold o ganho e real e estavel em conf >= 0,7 (min 2-3 entries), mas nos cursos sem gold a mesma regra muda MF 6 e CG 9 subunidades, varias visivelmente erradas (self-training amplifica o boilerplate de headings do OpenGL); sem o teto de df, (0,9;2) dava -20. "Saldo medido nos 8" e lei; 4 cursos sem regua nao contam como saldo.
**Consequences:** Caixa do handoff + decisao aberta do user (gold CG/MF, C5). Ate la, subunidade do motor puro = 82/93 por vocabulario. `gemini_auto_summarize` desligado na UI pelo user em 05/09 tarde.
"""
assert "Propagacao de vocabulario por headings (sem LLM) fica na caixa" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + """
- `simula_propaga_headings.py <snapshot> conf min_entries df_max [orig]` / `_weak.py` (2a passada so nos nao-confiantes) / `_semgold.py` (MF, CG, FR,
  LR: lista o que mudaria): propagacao de vocabulario por headings — gold 82 -> 87/93 (+5/-0) em (0,7; 2; 0,25) weak-only, curada 93/93;
  grades em `simula_propaga_grid*.log`; sem gold MF 6 / CG 9 mudancas (`simula_propaga_semgold_weak.log`). Nao entra sem gold CG/MF.
""", encoding="utf-8")
print("docs ok")
