# Verificação local de exposição, v2: resumo (29/09/2026)

Substitui, para leitura, `../../validacao_externa_etapa3_29-09/exposicao/resumo_exposicao.md` (preservado). **Nenhum
nível foi alterado**; a leitura de cada trecho é do investigador, não um veredito. O script não lê níveis nem
resultados de classificação.

- **Fontes:** `git grep -z -n -I -P -i --no-color` e `git log --grep` no commit `bf46d51f`, sem cor e sem aspas em
  caminho. As raízes e exclusões são as da triagem. Também entram os nomes das 11 pastas de `~/Desktop/Moodle`.
- **Busca e INDETERMINADO:** nenhuma ampliação do D9. Fonte ausente, saída não interpretada ou linha sem match no regex
  Python dariam INDETERMINADO. Nesta execução, 21/21 ficaram `ok`.
- **Mudanças da v2:** registra **todos** os matches de cada linha, com intervalo, vizinhança e motivo de omissão
  específico. "Resultado do motor" agora é só artefato de dados/log, e por isso os trechos omitidos caíram de 18 para
  5. A categoria continua sendo do arquivo e não prova uso.
- **Dados:** `exposicao_local_v2.json` fica só local, porque tem o texto excedente do catálogo. A cópia divulgável é
  `exposicao_local_v2_divulgacao.json`.

## Sem nenhuma ocorrência (11): igual à v1

Catálogo: 80922, 81476, 82667, 88738, 89100, 89447, 90231, 90572. Locais de 29/09: CALC1, FP, MC.

## Com ocorrência (10)

| candidato | arquivos | matches | o que os trechos mostram |
|---|---:|---:|---|
| 73425 | 1 | 2 | id dentro de sha256 |
| 94492 | 1 | 3 | id dentro de sha256 |
| 82154 Lógica para Computação | 2 | 4 | título de livro na bibliografia de MF |
| 84490 | 1 | 1 | código num fixture do parser de nomes (agora categoria `teste_ou_fixture`) |
| 93730 | 2 | 2 | código e nome como fixture do parser ("Profs. Y") |
| 95864 | 1 | 1 | código numa grade de horários arquivada |
| IC | 4 | 8 | prefixo de "Introdução a Computação Gráfica 3D…" (tópico de CG) |
| MD | 3 | 6 | títulos de livro (bibliografia de MF); frase de outro curso |
| MSA | 2 | 26 | categoria "Métodos Analíticos" em texto de IA (vários matches por linha); caminho da pasta do projeto do aluno |
| 89045 Engenharia de Software I | 127 | 221 | ver abaixo |

## Engenharia de Software I (correção da afirmação da v1)

A v1 guardava só o primeiro match de cada linha. Por isso a afirmação "nenhuma ocorrência do id ou do código" excedia
a evidência: um match próprio de ES I, mais adiante na mesma linha, não teria sido registrado (E3-EXP-09).

Com todos os matches registrados:

- 221 matches no total, todos do padrão de nome;
- 219 são seguidos de `I` e 2 de `i`, ou seja, são prefixo de "Engenharia de Software II";
- o id `89045` e o código `98801-04` não aparecem em nenhum match.

**O que isso permite dizer:** nas fontes pesquisadas (um commit e nomes de pastas), nenhuma menção própria a ES I foi
encontrada.

**O que isso não prova:** equivalência com ES2 nem independência do desenvolvimento. A exclusão por correspondência
parcial continua até decisão própria.

## Limites

- A categoria é do arquivo: um título de livro dentro de dados de MF cai em "dados".
- Trechos omitidos (5, todos de ES I, artefatos de resultado do motor) não permitem ver a natureza da menção. A
  vizinhança de 3 caracteres mostra o sufixo (`I`).
- A busca olha um único commit. Outras branches, worktrees, stashes, memória e conversas não foram pesquisadas (D9
  aberto).
- Reclassificar qualquer N1, ou reincluir ES I, exige decisão explícita, sabendo destas contagens.
