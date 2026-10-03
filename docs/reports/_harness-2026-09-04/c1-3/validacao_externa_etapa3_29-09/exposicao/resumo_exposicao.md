# Verificação local de exposição: resumo (29/09/2026)

**Nenhum nível foi alterado.** Este resumo descreve as evidências encontradas; a leitura de cada uma (menção incidental
ou uso em desenvolvimento) é minha e **não** é um veredito. N1 continua N1 até decisão explícita. O script não lê
níveis nem resultados de classificação: a lista de candidatos sai só da identidade (`entrada_exposicao.json`).

- Fontes pesquisadas: `git grep -n -I -P -i` e `git log --grep` no commit `bf46d51f` (raízes docs, tests, src, scripts,
  .mex, .workflow; mesmas exclusões de caminho da triagem) + nomes das pastas em `~/Desktop/Moodle` (11, só nomes).
- Não pesquisado (D9): outras branches, worktrees, stashes, memória de sessões, conversas, conteúdo de pastas locais.
- Padrões: os mesmos da triagem de 29/09 (id com borda de dígito, nome escapado, código com 4+ caracteres) e os
  `padrao` dos candidatos locais de 29/09. Nenhuma busca falhou: 21/21 com `status_da_busca = ok`, nenhum INDETERMINADO.
- Trechos de arquivo de resultado do motor, ou com assinatura de saída do motor ou de segredo, foram omitidos; a
  vizinhança de 3 caracteres do termo fica visível mesmo assim.
- Detalhes (arquivo, linha, categoria, termo, vizinhança, trecho): `exposicao_local.json`.

## Sem nenhuma ocorrência (11)

Catálogo: 80922, 81476, 82667, 88738, 89100, 89447, 90231, 90572. Locais de 29/09: CALC1, FP, MC. Nenhum commit,
nenhuma pasta de download anterior.

## Com ocorrência (10)

| candidato | arquivos (categoria) | termo que casou | o que o trecho mostra |
|---|---|---|---|
| 73425 Fundamentos de D. de Software | 1 (dados) | `73425` | o id aparece dentro de um sha256 (vizinhança `d0f`…`",`) |
| 94492 Simulação e Métodos Analíticos | 1 (dados) | `94492` | o id aparece dentro de um sha256 num inventário de skills (`1bc`…`da0`) |
| 82154 Lógica para Computação | 2 (dados: `moodle_contents/MF.json`, `moodle_sections/MF.json`) | `Lógica para computação` | título de livro na bibliografia de MF |
| 84490 Infraestrutura para Gestão de Dados | 1 (código: `tests/test_moodle.py`) | `98H00-04` | o código aparece num fixture do parser de nomes, com outro nome de disciplina |
| 93730 Prática em Pesquisa | 2 (código: `tests/test_moodle.py`; relatório arquivado) | `98702-04` | código e nome completo como fixture do parser de nomes ("Profs. Y") |
| 95864 Língua Inglesa IV | 1 (relatório arquivado) | `125AB-04` | código numa linha de grade de horários |
| IC Introdução à Computação | 4 (log e caches da travessia de CG) | `Introdução a Computação` | prefixo de "Introdução a Computação Gráfica 3D…" (tópico de CG) |
| MD Matemática Discreta | 3 (dados de MF; inventário de relações) | `Matemática Discreta` | títulos de livros na bibliografia de MF; frase de outro curso |
| MSA Métodos Analíticos | 2 (inventário de relações; inventário do workflow) | `Métodos Analíticos`, `MetodosAnaliticos` | categoria em texto de IA; caminho da pasta do projeto do aluno num inventário |
| 89045 Engenharia de Software I | 127 (109 relatório, 7 resultado do motor, 5 código, 4 dados, 2 plano) | `Engenharia de Software I` (221×) | **todas** as 221 ocorrências continuam com `I`/`i`: são "Engenharia de Software II" (ES2). Id `89045` e código `98801-04`: nenhuma ocorrência |

## O que isto permite e o que não permite

- Distingue, por arquivo, menção documental de presença em código/teste/dados/resultado (`sinais.arquivos_por_categoria`),
  mas a categoria é do **arquivo**, não da menção: um título de livro dentro de dados de MF cai em "dados".
- Nenhuma ocorrência acima mostra material da disciplina candidata processado pelo motor; isso é leitura dos trechos,
  não prova de independência (fontes não pesquisadas acima).
- Engenharia de Software I: a exclusão por correspondência parcial de 29/09 continua valendo; esta verificação mostra
  só que o repositório não a menciona por id, código ou nome próprio. Não foi demonstrada equivalência com ES2 nem
  independência dela.
- Reclassificar qualquer N1, ou reincluir Engenharia de Software I, exige decisão explícita, sabendo destas contagens.
