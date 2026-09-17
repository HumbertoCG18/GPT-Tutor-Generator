# Handoff: frente "regime cru" do motor de atribuição (16/09/2026)

Continuação de `2026-09-15-handoff-regime-cru.md`. Serve para Claude ou Codex. Escrito pelo Claude no fim de 16/09, a partir
do estado do git, do tracker e do rollout da sessão Codex "Testar cuidados do regime cru" (`~/.codex/sessions/2026/09/14/`:
`rollout-2026-09-14T14-09-41-01a0a0e5-…jsonl` abortada após 1 turno; a sessão real é
`rollout-2026-09-14T14-49-38-01a0a109-…jsonl`, 291 mensagens, 14/09 17:49Z → 15/09 18:07Z, ou seja 14:49 → 15:07 BRT).
"Medido" = rodado, com log no repositório. "Hipótese" = não medido. Horários citados na §3 são os do rollout, em UTC.

## 0. Leia nesta ordem

1. `.mex/AGENTS.md`, `.mex/ROUTER.md`, `.workflow/README.md` e `.workflow/HANDOFF.md` (política de papéis: Fable executa,
   Astra revisa read-only uma vez por tarefa; commit `f535537`).
2. Este arquivo inteiro.
3. `2026-09-15-handoff-regime-cru.md` §3–§11: achados, placar dos regimes, decisões do usuário, defeitos do produto e
   armadilhas de 15/09 **não são repetidos aqui**.
4. `2026-09-14-handoff-codex-regime-cru.md` §3–§9 e §16 sob demanda: meta, leis de processo, alavancas fechadas, as 3 opções.
5. Estado vivo: `docs/reports/pendencias.md`, blocos "(16/09)" e "(15/09)" no topo.

Artefato citado sem pasta mora em `docs/reports/_harness-2026-09-04/c1-3/` (`c1-3/`). Relatório citado sem pasta mora em
`docs/reports/Feitos/`.

## 1. Em uma frase

Nada do motor foi medido em 16/09: o dia fechou a árvore (4 commits, push feito), reorganizou `docs/reports/` e registrou a
política de workflow; a frente continua exatamente onde a sessão Codex parou em 15/09 (categoria prova validada só em replay,
`210 → 213/237`), com as decisões §7 de 15/09 abertas, exceto o commit.

## 2. Estado do repositório (medido em 16/09, fim do dia)

- Branch `feat/motor-atribuicao` = `origin/feat/motor-atribuicao`; árvore limpa após `d495c66`. O push de 16/09 subiu 41 commits.
- **Sessão Codex em paralelo (16/09 23:41 BRT, medido: 3 processos `codex.exe`, tracker regravado às 23:42).** A sessão
  `01a0a824` ("Continuar diagnóstico do handoff") rodou o piloto Fable × Astra (ambos 23/23 e 12/12, sem turno de reparo;
  `Feitos/workflow-medicao-fable-astra_16-09.md`) e fechou a política de papéis. Ela mesma commitou: `f535537` na branch
  (`.workflow/*`, `CLAUDE.md`, `AGENTS.md`, o relatório) e `e551bbf` na `main`, replicado às branches locais, **sem push**
  (`main` fica 2 commits à frente de `origin/main`). O hunk dela no tracker entrou no commit seguinte, do Claude, depois
  que o usuário fechou o Codex.
- Commits de 16/09, em ordem cronológica:

| commit | conteúdo |
|---|---|
| `c392e7c` docs(reports) | reorganização: 40 `git mv` para `Feitos/` e `_archive/`, referências atualizadas, ROUTER (graphify primeiro, CBM fallback), 3 patterns, 15 relatórios `Feitos/*_15-09.md` e `*_16-09.md`, handoff 15/09, ignores |
| `e1133a4` chore(harness) | 748 artefatos: `_codegraph-benchmark/`, `_workflow-audit-2026-09-15/`, 138 novos em `c1-3/` (`*_15-09.*`) |
| `6742ac4` docs(tracker) | ideia futura "renderização de imagens dos materiais no chat" no backlog aberto de produto, marcada NÃO IMPLEMENTAR AGORA |
| `d495c66` feat(glossary) | taxonomia direta: `src/builder/core/course_vocabulary.py`, fiação em `engine`/`facade`/`routing`/`content_taxonomy`, `sync_fresh` em `scripts/ablacao_rapida.py`, `tests/test_glossary_structured.py` |

- Suíte antes do commit de código: **2357 passed, 4 skipped** (`python -m pytest -q`, 16/09, rodada pelo Claude; mesmo número
  do log de 15/09 `c1-3/suite_taxonomia_final_15-09.log`).
- **Gate 2 formal não aconteceu.** O commit `d495c66` foi por ordem do usuário ("commite o que já tem na worktree"). O
  relatório `taxonomia-direta-implementacao_15-09.md` registra revisão local do diff e "sem revisão independente por outro
  LLM". O item 7.1 de 15/09 fecha como commit, não como review.
- Cópias (gitignored, não versionadas): `.motor3eixos/_CONFIG_ATUAL.txt` = `regua (veto=texto, SEM curadoria do
  benchmark=puro)`, 7 cursos; `.frzero/` contém os destinos `*_15-09` do 15/09 §2 mais `contaminantes_motor3eixos_15-09/`.
  Conferi só o arquivo de config e a listagem; conteúdo das cópias não foi verificado em 16/09.
- Graphify: o hook reconstruiu o grafo a cada commit de 16/09 (12.340 nós, 809 comunidades; `~/.cache/graphify-rebuild.log`).
  O item [CODE] "índice Graphify não atualizado" do tracker pode estar vencido: hipótese, conferir com `graphify explain`.

## 3. O que a sessão Codex "Testar cuidados do regime cru" estabeleceu

Resumo do caminho de decisão, na ordem do rollout. Os números completos estão no 15/09 §3; aqui vai o que cada virada
provou e o que o usuário decidiu.

1. **Cuidado 1, contaminação da cópia (14/09 17:53Z → 22:27Z).** A "baseline C" devolveu `235/263/224/186` porque a cópia
   ainda carregava `relacoes_C_14-09.json`. Restaurada como `regua+puro`, deu `222/253/131/103`, não os `142/100` de 14/09.
   A causa só fechou às 22:15Z: `.glossary_curation.json` órfãos em MF (11.511 bytes) e FR (17.152 bytes), preservados por
   `robocopy /E` sem `/MIR`; explicam exatamente MF −15 aceitas/−1 primária e FR +4/+4. Quarentena em
   `.frzero/contaminantes_motor3eixos_15-09/`; restauração idêntica a 14/09, 0 diferenças
   (`c1-3/compara_restauracao_x_14-09_15-09.log`). Lição fixada: `_CONFIG_ATUAL.txt` correto não prova cópia limpa;
   `sync_fresh` nasceu disso.
2. **Cuidado 2, teto do glossário (18:36Z → 20:01Z).** Na cópia ainda contaminada o teto cortava CG (13.933 chars, 8/59 sem
   alias) e FR (13.977, 23/32). Na cópia realmente limpa FR não trunca (9.090 chars, 32/32): **só CG trunca** (51/59).
   Monkeypatch global em `repo.clamp_navigation_artifact` refutado: `repo.py:1852` chama o parâmetro capturado em
   `engine.py:2235`; e o clamp atua duas vezes, porque `pedagogical_regeneration.py:455` gera a taxonomia antes de
   `:547–553` gravar o arquivo. Contraprova: sem o clamp na rota interna, CG `51/59 → 59/59` (`c1-3/teto_taxonomia_CG_15-09.log`).
3. **Decisão do usuário (21:35Z → 23:04Z): "tratar a doença, não o sintoma".** O motor não usar `GLOSSARY.md` como banco de
   dados. Codex mediu o fluxo direto em cópia: `222/253/142/100` nos dois braços, 0 ganhos/0 perdas, glossários −11,47%.
   Ordem adotada: **confiabilidade da régua → correção estrutural → otimização de placar**; o fix não é ganho de placar.
4. **Gate 1 aprovado (15/09 02:52Z)** → TDD (3 vermelhos → 9 verdes), 2357 passed, 0 ganhos/0 perdas nos 316, CG 59/59.
   É o `d495c66` de hoje.
5. **Heranças (03:14Z → 05:08Z).** Cru desde fontes locais `169/234/99/76`. Mecanismo: o coletor de títulos ignora
   `staging/` (`content_taxonomy.py:733`); TCC perde 54 candidatos, aliases 57 → 27.
6. **Metadados Moodle (05:20Z → 05:42Z).** Decisão do usuário: "sempre prefira os MD que vêm do Datalab". Estrutura/semana
   +29/−3 blocos; datas de cards IA 25 → 38 em braço separado; **os braços não somam**; superioridade do Datalab não medida.
7. **Diagnóstico → raiz (15:24Z → 15:56Z).** O usuário recusou duas vezes corrigir o sintoma (regra do SO). A cadeia mostrou
   entrada incompleta (payload Moodle existia nos 7 cursos, o driver carregou só CG/FR), contexto coletivo virando decisão
   individual, e inferência temporal virando autoridade curricular (17/220 divergem do currículo).
8. **Pacote completo de fontes (15:57Z → 17:41Z).** `210/239/108/84`. Raiz das 3 perdas de MF: categoria `provas` por
   substring (`src/utils/helpers.py:682`) desliga o desempate textual.
9. **Categoria prova (18:00Z → 18:07Z, fim da sessão).** Replay `210 → 213/237`, +3/0, controles preservados; unidade e
   subunidade não reavaliadas. Última recomendação do Codex: reconstruir cópia com a categoria corrigida na entrada e
   conferir os 4 eixos.

Tudo acima com 0 chamadas de LLM, sem Astra, sem edição em `src/` fora do Gate 1 aprovado.

## 4. Decisões em aberto (do usuário): herdadas de 15/09 §7, atualizadas

1. ~~Gate 2 e commit da taxonomia direta~~ → commit feito. **Review independente do diff `d495c66`** não foi feita; pela
   política de `f535537` ela é Astra no Codex, read-only, uma chamada; santa-loop/Terra deixou de ser o padrão.
2. Categoria prova: reconstrução em cópia com a categoria corrigida na entrada, medindo unidade e subunidade; só então
   `orch-fix-defect` em `helpers.py:682`.
3. Remedir estrito, A e C do 14/09 §8 sobre `d495c66`: o bloqueio do teto deixou de existir nesse código.
4. Fechar a distância pacote × herdado (15/09 §4): `staging/`, os 23 vínculos sem match, TDE ES2, perdas de unidade ES2.
5. Herdadas de 14/09 §10: meta revista, opção B, certificação do zero para cursos inéditos.

Fora do motor, no topo do tracker: aceite pendente do workflow Claude/Codex/AGY e medição Fable × Astra. A ideia de imagens
no chat (`6742ac4`) é só registro no backlog de produto.

## 5. Próximo passo recomendado (recomendação do Claude, não decisão)

1. Item 4.2 em cópia nova (`c1-3/motor_copia_nova_15-09.py --destino .frzero/<nome-novo>`), só MF mais um controle IA
   pelas 4 avaliações reais, 0 LLM; medir os 4 eixos antes de tocar `helpers.py`. Custo medido do pacote MF em 15/09: 66 min.
2. Item 4.3, remedir C: único jeito de a opção C dizer algo sobre o LLM; informa a meta revista, não o cru.

Contraponto: os 3 positivos da categoria prova eram conhecidos antes da regra e não há holdout; um +3 em replay não autoriza
mudar o importador do produto.

## 6. Armadilhas

- Todas as de 15/09 §9 continuam valendo.
- Duas CLIs escrevendo na mesma árvore ao mesmo tempo (este handoff nasceu assim, §2): antes de commitar o tracker, separar
  por hunk o que é seu; `git status` limpo em um instante não prova que fica limpo no seguinte.
- `docs/reports/` mudou de lugar em 16/09: relatórios encerrados em `Feitos/`, handoffs substituídos em `_archive/`. Caminho
  antigo em prompt ou script fora do repo quebra.
- `.codex/config.toml` continua sendo reescrito pelo Alethe (tracker, bloco HARNESS 10/09): `git checkout` nele antes de
  commitar.
- O código da taxonomia direta agora está commitado: cópias feitas antes de 16/09 (`.frzero/*_15-09`) rodaram o mesmo código,
  só que não versionado; não há diferença de comportamento, mas relatórios de 15/09 falam em "árvore suja" e isso deixou de valer.

## 7. Primeira mensagem sugerida

```
Leia .mex/AGENTS.md, .mex/ROUTER.md, .workflow/README.md, .workflow/HANDOFF.md e
docs/reports/2026-09-16-handoff-regime-cru.md inteiro (o de 15/09 §3–§11 sob demanda).
Confira branch e HEAD antes de tudo; não mude src/ nem rode medição ainda.
Resuma em 5 linhas as decisões em aberto da §4, separando medido de hipótese, e proponha o plano do item 4.2
(cópia nova, MF + controle IA, 0 chamadas de LLM) para eu aprovar antes de rodar.
Astra só como revisor read-only, conforme .workflow/workflow.md.
```
