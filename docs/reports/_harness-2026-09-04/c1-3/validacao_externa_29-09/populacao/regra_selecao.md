# Regra de seleção da população (validação externa do regime VOCAB, 29/09/2026)

Fonte única da regra: as declarações no topo de `enumera_candidatos.py` (sha256 no `populacao_candidata.json`). Este
texto só as descreve. A regra foi fixada antes de qualquer contagem e não usa predição, score ou resultado do motor.

## Universo de candidatos

Todas as fontes locais de disciplina encontradas por listagem de pastas (nomes e estrutura, nunca conteúdo do motor):
- `~/Desktop/Moodle/<disciplina>/`: downloads do Moodle (11 pastas: os sete cursos de desenvolvimento, LR, LSO, UX e
  `computacao-grafica-raw`, que é parte do CG);
- `~/OneDrive/Aulas-PUCRS/<disciplina>/`: pastas do aluno (Cálculo 1, Fundamentos da Programação, Introdução à
  Computação, Matemática Discreta, Metodologia Científica);
- `~/Desktop/MetodosAnaliticos/`: projeto do aluno;
- planos avulsos em `~/Desktop/claude-tutor/` (FR, LR, LSO), usados só como fonte de plano.

Candidatos conhecidos sem fonte local (não entram na tabela): "Prática em Pesquisa" (2026/1) e a disciplina online de
2026/2, citadas pelo usuário em 28/08.

## Nível de exposição (evidência no commit fixo `bf46d51f`, anterior a esta preparação)

| nível | definição | tratamento |
|---|---|---|
| N3 | curso de desenvolvimento, com gold e régua | excluído |
| N2 | tutor construído e processado pelo motor | fora da população principal; no máximo smoke test descritivo (LR) |
| N1 | citado no repositório (código, testes, planos, relatórios ou commits) sem N2/N3 | só piloto externo, nunca generalização |
| N0 | nenhuma citação encontrada | generalização |

N1 é conservador: qualquer menção conta, inclusive incidental. Menções incidentais conhecidas: IC (logs de travessia
do CG), MD (conteúdo do Moodle do MF) e MSA (inventários). Nenhuma delas muda a elegibilidade, que falha por plano.

## Critérios estruturais

- **E2:** plano de ensino disponível localmente (arquivo com "plano" no nome dentro da fonte, ou plano avulso declarado).
- **E3:** pelo menos 10 materiais potencialmente adjudicáveis. Adjudicáveis = arquivos de material únicos por sha256 +
  módulos `url` do `contents.json`, menos arquivos cujo nome indica plano, cronograma, ementa ou apresentação da
  disciplina. Arquivos gerados pelo produto (`links.json`, `manual-review/`, `raw/moodle/*.json`, `raw/site/`,
  `stash/.moodle_nomes.json`, `_ARQUIVOS_DO_CARD.txt`) não contam.
- **E4:** pelo menos 90% dos adjudicáveis com fonte local congelável (links externos não são congeláveis).

## Seleção

- Generalização: todos os N0 que cumprem E2, E3 e E4. Piloto externo: idem para N1.
- Mais elegíveis que o orçamento (6 cursos por população): ordem crescente de
  `sha256("vocab-validacao-externa-2026-09-29|<sigla>")`, e entram os 6 primeiros. Nenhuma escolha manual.
- Mínimo da generalização: 3 cursos e 100 adjudicáveis no total. Abaixo disso, a validação de generalização não
  começa (tratamento no pré-registro, §5).

## Resultado da aplicação (29/09)

| população | cursos | observação |
|---|---|---|
| generalização | nenhum | nenhum N0 cumpre E2; mínimo não atingido |
| piloto externo | nenhum | LSO falha em E4 (21 de 28 com fonte local = 75%); UX falha em E2 (card do plano vazio no download) |
| smoke descritivo | LR | 11 adjudicáveis; tutor já processado pelo motor |

**Sensibilidade (informativa, não altera a regra):** o LSO entraria no piloto com E4 ≥ 75%. Mudar o limiar agora,
depois de ver as contagens, seria grau de liberdade pós-hoc; qualquer mudança precisa da revisão independente antes do
Gate 1.
