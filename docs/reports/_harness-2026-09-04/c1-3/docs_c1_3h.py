"""Registro: pergunta 'funciona numa materia nova?' — evidencia (holdout CG) + 2 bugs de dado que uma materia nova traz (paginas do Moodle
capturadas como login; colisao de nomes entre zips)."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
edit(T, "**BUG (medido): zips do MF extraidos SEM subpasta -> colisao de nomes.**",
        "**MATERIA NOVA (pergunta do user 05/09 tarde) — evidencia e bugs de dado medidos nos 8:** o unico teste de generalizacao e o holdout CG (curso nao\n"
        "usado para afinar): bloco automatico 35/35, mas unidade 22/93 erradas (so vistas ao montar o gold de subunidade) e subunidade ~49/82 no gold proposto.\n"
        "O censo ja sinalizava: CG revisar/100 = 74-76 (maior dos 8; media 58) — um curso novo com revisar/100 alto e o sinal para olhar, sem gold. Dados que\n"
        "uma materia nova traz quebrados: (1) **paginas do Moodle (`mod/page`) capturadas como TELA DE LOGIN**: CG 16/16 (unico tutor com paginas; o tutor so\n"
        "roteia essas 16 pelo titulo); (2) **colisao de nomes de membro ENTRE zips** na extracao plana: CG 168 nomes repetidos em 14 zips (projetos OpenGL\n"
        "com os mesmos arquivos), ES2 38 em 8, MF 10 em 13, SO 3 — o codigo do tutor e o resumo de codigo desses zips estao trocados/incompletos.\n"
        "Tag [CODE] SYNC/C5. Condicoes para o automatico funcionar: SARC com sessoes datadas, Moodle com secoes e labels (FR tem 0 labels), plano\n"
        "parseavel ate o fim (CG para em 7.1.2), Gemini para voter/vocab/resumos (~100-150 chamadas por curso de 90 materiais); professor sem sinal\n"
        "temporal (MF: tudo postado em 18/02) empurra 30/66 para o LLM.\n"
        "**BUG (medido): zips do MF extraidos SEM subpasta -> colisao de nomes.**")

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "- **Zips extraidos sem subpasta colidem nomes** (MF 5 zips x `ex1.dfy`; `.smv` ignorado) · `<id>/<membro>` + `.smv` como codigo · SYNC/C5.",
        "- **Zips extraidos sem subpasta colidem nomes** — nos 8: CG 168 nomes repetidos entre 14 zips, ES2 38, MF 10, SO 3; `.smv` ignorado · `<id>/<membro>` + `.smv` como codigo · SYNC/C5 · codigo e resumo certos por zip.\n"
        "- **Paginas do Moodle (`mod/page`) capturadas como tela de login** (CG 16/16; unico tutor com paginas) · capturar com sessao autenticada no pull · SYNC/C5 · conteudo real para rotear.\n"
        "- **Saude de curso novo sem gold**: revisar/100 (CG 74-76 x media 58) + fracao de blocos preenchidos por posicao + conflitos texto x bloco no CRONOGRAMA_HEALTH · sim, so leitura · C4/C6 · sinal de 'olhar este curso' sem gold.")
print("docs ok")
