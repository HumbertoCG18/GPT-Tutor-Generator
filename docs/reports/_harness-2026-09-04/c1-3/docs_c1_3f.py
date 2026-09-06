"""Registro: pergunta do user 'unificar alavancas?' — 3 medicoes (conflito texto x bloco; higiene por sessao/titulo; radical como fallback)."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:70], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
edit(T, "**BUG (medido): zips do MF extraidos SEM subpasta -> colisao de nomes.**",
        "**UNIFICAR ALAVANCAS? (pergunta do user 05/09 tarde: 'uma acerta, a outra remede e erra') — medido:** (1) Unidade, conflito texto x bloco\n"
        "(`unit_block_conflict`, gold de 191): motor puro 33 conflitos -> bloco certo 27, texto certo 3 (SO sockets x2 bibliografia, IA visao-geral), nenhum 3;\n"
        "produto 25 -> bloco 25, texto 0. Gate 'texto vence quando bloco conf <= 0,4': +1 (IA) -1 (MF) = saldo 0. A decisao de 21/08 ('bloco decide, texto vira\n"
        "registro de conflito') segue certa: 9:1. (2) Higiene de aliases por label de SESSAO/titulo de material: IA tem 5 aliases 'Aula NN - ...' (aspirador\n"
        "do topico de busca), mas os aliases = titulo sao UTEIS (MF 8: 'Conjuntos Indutivos', 'Inducao Estrutural...'; IA 'MLP', 'arvores de decisao'; ES2\n"
        "'Kubernetes', 'DEVOPS') -> nao generalizar. (3) **Radical (6 chars) SO como fallback no mapa bloco->unidade** (tokens exatos decidem; bloco sem\n"
        "ancora exata possivel, aff < 2, ganha ancora por radical com >= 2, margem >= 1, radical exclusivo de UMA unidade): nos 8, **1 bloco muda (CG\n"
        "bloco-15 Modelagem -> u07, = pino), 0 colateral**, pinos 12 -> 13 (sem contar o pino novo do CG), unidade 183 = 183/191. E a unica unificacao que\n"
        "sobrevive: cobre sem pino o caso que hoje o pino cobre. Candidato (caixa): ~15 linhas em `assign_units_positional`, ganho atual 0 (pino ja\n"
        "resolve), valor = proximo curso sem pino. `c1-3/simula_radical_fallback.py`.\n"
        "**BUG (medido): zips do MF extraidos SEM subpasta -> colisao de nomes.**")

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "- **Prompt do voter sem o `moodle_label`**",
        "- **Radical (6 chars) so como fallback no mapa bloco->unidade** (tokens exatos decidem; sem ancora exata, ancora por radical exclusivo) · 1 bloco muda\n"
        "  nos 8 (CG bloco-15 = pino), 0 colateral, unidade 183 = 183 · ~15 linhas em `assign_units_positional` · ganho hoje 0 (pino), valor = proximo curso sem pino · C4/C5.\n"
        "- **Prompt do voter sem o `moodle_label`**")
edit(H, "relaxada 179; higiene sozinha neutra). Solucao = higiene generica",
        "relaxada 179; higiene sozinha neutra; radical so como fallback: +1 bloco, 0 colateral, unica unificacao que sobrevive, caixa). Solucao = higiene generica")
print("docs ok")
