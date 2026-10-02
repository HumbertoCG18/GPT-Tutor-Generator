# Trabalho noturno 30/09/2026 — resumo

Tarefa `noite-20260930-revisao-dossie-sync`, pela Orquestração do Alethe. Coordenador: Claude Code
(`claude-opus-5-5`), sessão `ee4dd19b-7491-4289-baf7-43a7b14dfb38`. Escopo: três frentes (A revisão do delta Moodle,
B dossiê de decisões, C sincronização de `.workflow/`). Nenhum commit, merge, push, rebase ou PR foi feito.

## 1. Resultado em uma tela

| frente | resultado | saída |
|---|---|---|
| **A. Revisão do delta R-META/R-PAGE** | **concluída**. Veredito do revisor: **NÃO APROVAR**, 2 MAJOR, 0 CRITICAL, 0 MINOR. Os dois achados foram reproduzidos pelo coordenador. Nada foi corrigido | `docs/reports/2026-09-30-revisao-delta-rmeta-rpage.md` |
| **B. Dossiê de decisões** | **concluído com uma ressalva**: a seção B2 (motor CRU) veio do worker e foi conferida; a seção B1 (validação externa) foi escrita pelo coordenador, porque o worker dela falhou duas vezes | `docs/reports/2026-09-30-dossie-decisoes-motor.md` |
| **C. Sincronização de `.workflow/`** | **concluída**, sem commit: 8 arquivos modificados, +75/−27 (fonte `f07d786`; ver §6) | `.workflow/` da worktree da noite |

Todas as saídas estão em `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-noite-20260930` (HEAD destacado em
`bf46d51f`), não commitadas.

## 2. O que aconteceu, em ordem

1. Leitura de `references/delegation.md`, `review.md` e `routing.md` da fonte (`agent-workflow-lab`).
2. `alethe_status`: `running = 0`, `queued = 0`, 10 Jobs anteriores encerrados; papéis `reviewer` e `planner-t2`
   presentes, `readOnly = true`, 600 s, ambos codex `gpt-6.1-sol`.
3. Estado persistido: o `active-task.md` anterior foi guardado como `.workflow/local/active-task-ate-20260930.md`
   (sha256 `5e35d62a…`, bytes idênticos) e a tarefa noturna foi registrada em `.workflow/local/active-task.md`
   (classificação T2, `revisao_autorizada`, `escaladas_automaticas`).
4. ~02:20: Frente A delegada (`job-11`); ~02:21: Frente B delegada (`job-12`, `job-13`). Enquanto rodavam, a Frente C
   foi feita.
5. **02:29: o Alethe fechou** (bug do app). `job-11`, `job-12` e `job-13` ficaram `interrupted`, sem resultado.
6. Retomada (~02:57) com autorização do usuário para relançar **uma vez** cada frente. Registrado no estado antes de
   delegar. ~02:59: `job-16` (revisão) e `job-17`/`job-18` (dossiê).
7. ~03:08–03:10: `job-18` e `job-16` entregaram; `job-17` expirou aos 600 s.
8. Conferência, montagem do dossiê e este resumo.

## 3. Jobs

| job | run | papel | modelo observado | duração | resultado |
|---|---|---|---|---:|---|
| `job-11` | `run-06` | `reviewer` | codex `gpt-6.1-sol` | — (`endedAt` nulo; sem duração completa) | `interrupted` pelo fechamento do app; sem resultado |
| `job-12` | `run-07` | `planner-t2` | codex `gpt-6.1-sol` | — | `interrupted`; sem resultado |
| `job-13` | `run-07` | `planner-t2` | codex `gpt-6.1-sol` | — | `interrupted`; sem resultado |
| `job-14` | `run-08` | `reviewer` | codex `gpt-6.1-sol` | 95,2 s | `cancelled` ("cancelled by the lead"); sem resultado |
| `job-15` | `run-09` | `planner-t2` | codex `gpt-6.1-sol` | 75,8 s | `cancelled`; sem resultado |
| **`job-16`** | `run-10` | `reviewer` | codex `gpt-6.1-sol` | **585,6 s** | **`succeeded`**: NÃO APROVAR, 2 MAJOR. 483.313 tokens |
| **`job-17`** | `run-11` | `planner-t2` | codex `gpt-6.1-sol` | **600,0 s** | **`failed` / `timeout`**, sem texto parcial. 465.606 tokens |
| **`job-18`** | `run-11` | `planner-t2` | codex `gpt-6.1-sol` | **494,9 s** | **`succeeded`**: seção B2. 238.899 tokens |

- `plannerId` *(corrigido em 01/10; a versão anterior dizia "de todos: `uH6K…`")*: jobs 11–15 `uH6KXeXmvLUm9gqp5RmjD`
  (sessão noturna, antes do fechamento do app); jobs 16–24 `tsmq_2mmNF81XlNqqmYMe`; jobs 25–28
  `7jEdcaIHSHoGGPv_soJta`. `job-14`/`job-15` estão sob o mesmo `plannerId` da sessão noturna, sem chamada registrada
  que os lance; a origem não foi identificada. `threadId`: `job-16` `01a0f0e4-e75d-75b2-bc5b-dc19125c7892`;
  `job-17` `01a0f0e5-d076-7030-80f4-f8b685de0ba5`; `job-18` `01a0f0e5-d03d-7c50-b3f6-2f4efc1504fd`.
- Todos somente leitura (`readOnly = true`, `hasDiff = false`). O effort não é informado pelo status.
- **`job-14` e `job-15` não foram lançados por nenhuma chamada registrada desta sessão.** Aparecem no status da
  retomada já cancelados. Não entregaram nada e não foram contados como tentativa minha; ficam registrados para
  auditoria.
- Quota do Codex na semana: 17 % no início, 18 % no fim.
- Tentativas consumidas: revisão = 2 (uma interrompida, uma concluída); dossiê B1 = 2 (uma interrompida, uma com
  timeout); dossiê B2 = 2 (uma interrompida, uma concluída). `escaladas_automaticas = 3` no estado (inclui a revisão
  da etapa 3, de 29/09). **Não resta tentativa autorizada em nenhuma frente.**

## 4. Frente A — o que a revisão achou

Arquivo: `docs/reports/2026-09-30-revisao-delta-rmeta-rpage.md` (achados do revisor na íntegra, dados do Job e a
conferência).

1. **MAJOR — `moodle.py:452–455`: bytes de chunk truncado não são contados.** Em resposta chunked cortada no meio de
   um chunk, `bytes_recebidos` registra 0 de 3 bytes e 2 de 5. É o oposto do que o R-META promete para resposta
   incompleta.
2. **MAJOR — `moodle.py:440–444, 461–464`: Content-Length usado mesmo com transporte chunked.** Com os dois cabeçalhos
   juntos, o delta levanta `IncompleteRead` sem limite onde a leitura anterior devolvia `[]`, e com limite aceita `[]`
   de um corpo `[]xxx`.

Conferência do coordenador (medida, em memória, sem escrita): os dois se reproduzem; os dois controles com cabeçalhos
coerentes passam. O segundo achado depende de uma resposta fora do protocolo HTTP; a frequência disso na instância
real não foi medida. Os testes do delta não geram resposta chunked, então os 54/54 não cobrem nenhum dos dois.

Os sha256 dos dois arquivos do delta continuam `24430123…` e `99951fdb…`. Nada foi tocado na árvore principal.

## 5. Frente B — o que ficou pendente e por quê

- **B2 (motor CRU):** entregue por `job-18`. Todos os números foram conferidos contra as linhas citadas do tracker,
  do handoff de 23/09 e do diagnóstico do CRU-05 (tabela no dossiê, §B2.6).
- **B1 (validação externa VOCAB):** o worker falhou nas duas tentativas (interrupção do app e timeout de 600 s, com
  465 mil tokens de leitura e nenhuma seção entregue). O limite era uma relançada; não houve terceira. Para o dossiê
  não ficar pela metade, **a seção B1 foi escrita pelo coordenador** a partir das fontes lidas diretamente, com as
  mesmas quatro partes por decisão e `arquivo:linha`. Ela está marcada no dossiê como sem a segunda opinião do
  planner. Se essa segunda opinião for necessária, é uma nova delegação, com autorização sua. Sugestão para ela
  caber em 600 s: dividir em duas tarefas (D1–D9; R-VIS, R-CC e Gate 2).
- **Achado de fato fora do esperado:** o **Gate 2 da #49 já foi aprovado** em 22/09 ~12:23 e o commit `410592d8`
  está no branch e na referência local de `origin`. O tracker é que ficou desatualizado ("SEM COMMIT", "Gate 2
  pendente").
- **Não conferido** (listado no dossiê): estado da issue #49 e da PR #9 no GitHub (sem rede); o commit `3c8f26d9`
  (W-AC, teto do cru por curso), que não estava entre as fontes; os arquivos de B1 que não foram lidos
  (`relatorio_preparacao.md`, errata, `sugestoes_redacao_p3.md`, JSON de inventário, `.gitleaks.toml`).

## 6. Frente C — sincronização de `.workflow/`

Fonte: `C:/Users/Humberto/Documents/GitHub/agent-workflow-lab` (HEAD `b24b671` na reconferência; os arquivos de
`references/`, `workflow.md` e `task-state.template.md` não tinham alteração local). Cópia byte a byte (`cp` + `cmp`),
sem commit.

**Arquivos alterados na worktree da noite** (`git diff --numstat`):

| arquivo | + | − |
|---|---:|---:|
| `.workflow/workflow.md` | 3 | 3 |
| `.workflow/task-state.template.md` | 4 | 1 |
| `.workflow/references/delegation.md` | 21 | 1 |
| `.workflow/references/review.md` | 5 | 5 |
| `.workflow/references/routing-details.md` | 1 | 1 |
| `.workflow/references/routing.md` | 17 | 5 |
| `.workflow/references/tooling.md` | 17 | 4 |
| `.workflow/manifest.json` | 7 | 7 |
| **total: 8 arquivos** | **75** | **27** |

Números da reconferência de 30/09 ~16:10. A fonte ganhou dois commits à tarde (`bd1ffca`, `fba467c`, HEAD `fba467c`),
e `task-state.template.md` e `references/delegation.md` foram recopiados, com os hashes do manifesto atualizados. Na
madrugada o total era +72/−27.

**Versão-fonte fixada (01/10, depois da revisão do GPT).** A fonte ganhou mais um commit às 17:05 (`f07d786`:
"orçamento no início do brief, sem aviso no meio do turno"), que muda uma linha de `references/delegation.md`. A cópia
foi atualizada. Hoje os 7 arquivos copiados são **byte a byte iguais aos blobs de `f07d786`**, conferido com
`git show f07d786:<arquivo>`:

| arquivo | blob `f07d786` |
|---|---|
| `workflow.md` | `28f3f2fcd72f` |
| `task-state.template.md` | `6629d74d0e6e` |
| `references/delegation.md` | `a48940befebb` |
| `references/review.md` | `c197a13c3410` |
| `references/routing.md` | `14a3165d892c` |
| `references/routing-details.md` | `e6de3b407db8` |
| `references/tooling.md` | `202fcdfb26b7` |

O total segue em 8 arquivos, +75/−27, e o manifesto em 22/23 (`HANDOFF.md`). A cópia anterior era exatamente a de
`fba467c`.

**Pertencimento à árvore do commit (01/10, depois da 2ª revisão do GPT).** O GPT conferiu os 7 blobs pelos bytes,
mas não pôde provar que esses blobs estão nesses caminhos da árvore de `f07d786`. Conferido localmente, com git de
leitura no `agent-workflow-lab`:

- `git cat-file -p f07d786`: tree `c0a87dbb6e1999677841159d590322169807dd9a`, pai `fba467c69fe9eb50bb6c7340e91104c79d5dba2d`,
  assunto "docs(delegation): orcamento no inicio do brief, sem aviso no meio do turno";
- `git ls-tree f07d786` nos 7 caminhos: `workflow.md` `28f3f2fc…`, `task-state.template.md` `6629d74d…`,
  `references/delegation.md` `a48940be…`, `references/review.md` `c197a13c…`, `references/routing.md` `14a3165d…`,
  `references/routing-details.md` `e6de3b40…`, `references/tooling.md` `202fcdfb…`. São os mesmos IDs da tabela.

Para um terceiro verificar sem acesso ao repositório, falta anexar um bundle mínimo do commit. Isso não foi feito.

**Contradições da fonte (achadas pelo GPT), não resolvidas aqui:**

- `references/routing.md:25` escolhe `gpt-6-luna / medium` em T1, mas `:68–69` deixa Luna fora da seleção automática;
- `agents/agy-auditor.md:17` ("única revisão Astra") e `pendencias_workflow.md:20–21` ("Fable executa; Astra revisa")
  coexistem com o revisor por papel de `references/review.md`.

As duas exigem correção na fonte canônica (`agent-workflow-lab`) e nova distribuição, com escopo próprio.

Iguais à fonte e não tocados: `references/campaigns.md`, `capabilities.md`, `delivery.md`, `parallel.md`, `resume.md`,
`services.md`.

**`manifest.json`:** só os 7 hashes dos arquivos copiados mudaram (ordem das chaves e formatação preservadas). Foi
atualizado porque o procedimento da fonte manda ("copiar apenas o arquivo revisado … e atualizar seus hashes no
manifesto") e sem isso o snapshot ficaria incoerente. Se preferir o commit sem o manifesto, basta deixá-lo fora do
`git add`.

**Checks locais:**

- antes de copiar: os 7 arquivos de destino conferiam com o hash do manifesto (sem drift local a sobrescrever);
- depois: os 13 arquivos do escopo são idênticos à fonte (`cmp`), reconferido depois da retomada;
- manifesto: 22 de 23 entradas conferem; a que não confere é `HANDOFF.md`, **drift anterior a esta tarefa** (não
  tocado);
- `git diff --check`: limpo; EOL: LF em todos os arquivos copiados;
- links relativos dos 7 arquivos copiados: 13 conferidos, 0 quebrados.

**Fora do escopo listado, só informado (não copiado):**

- `.workflow/agents/agy-auditor.md` diverge da fonte em 1 linha;
- `.workflow/HANDOFF.md` não confere com o manifesto (drift anterior);
- `.workflow/agents/README.md` tem EOL misto e `evals/research-output.schema.json` não tem EOL final; ambos
  preexistentes.

**Para commitar** (Gate 2 seu), na worktree da noite ou levando os arquivos para o branch que preferir:

```
git add .workflow/workflow.md .workflow/task-state.template.md .workflow/manifest.json \
  .workflow/references/delegation.md .workflow/references/review.md \
  .workflow/references/routing-details.md .workflow/references/routing.md .workflow/references/tooling.md
```

A worktree está em HEAD destacado: o commit precisa de um branch (ou de um `cherry-pick` depois).

## 7. Decisões que você precisa tomar, em ordem

1. **Gate 2 do delta Moodle.** A revisão deu NÃO APROVAR. Recomendo não commitar como está e autorizar a correção dos
   dois achados (Gate 1 para `src/`, teste vermelho com transporte chunked) e uma nova revisão.
2. **Tracker da #49.** O Gate 2 já foi dado e o commit existe. Falta só corrigir o tracker (delta proposto no §8).
3. **Commit da sincronização de `.workflow/`** (Frente C): 8 arquivos, pronto. Decidir também se
   `agents/agy-auditor.md` e `HANDOFF.md` entram numa próxima sincronização.
4. **P3.1 como pacote** (D1, D2, D3, D7, D8 e o enquadramento de D6). Recomendo aprovar a redação, aceitando a marca
   [C] e que o lote de 29/09 fica exploratório.
5. **R-CC.** Recomendo ajustar duas lacunas e aprovar (mudou na verificação da tarde; ver §10).
6. **R-VIS.** Recomendo recusar OLE e MP4 soltos, aceitar imagens com leitura dos metadados e aceitação expressa do
   risco dos pixels, e varrer XMP e base64.
7. **D4, D5, D9.** Recomendo implementar a verificação de `model_version`, fechar a âncora do gitleaks e estender a
   busca de exposição às branches e worktrees locais.
8. **Regime do CRU-02.** Recomendo publicar o teto do cru como posição documental, com a meta registrada como não
   cumprida.
9. **Origem do bloco no CRU-03.** Recomendo uma proposta delimitada para afinidade zero em fronteiras e janelas.
10. **CRU-05.** Recomendo priorizar a normalização dos acentos espaçadores.
11. ~~Opcional: nova delegação da seção B1~~ — feita à tarde, em 6 partes (§10).

Detalhe, opções e evidência de cada uma: `docs/reports/2026-09-30-dossie-decisoes-motor.md`.

## 8. Delta proposto para o tracker (não aplicado)

`docs/reports/pendencias.md` não foi editado. Proposta, para você aplicar ou autorizar:

1. **Linha 45 (CRU-04, bloco `fila-campanhas`):** trocar "#49 implementada e revisada (V1, 217/237 = 91,6 %, 0
   perda), Gate 2 pendente (bloco 'Implementado, aguardando Gate 2 — #49'). dep: integração da #49" por "#49
   commitada `410592d8` (Gate 2 22/09 ~12:23; V1, 217/237 = 91,6 %, 0 perda). dep: integração na `main` (MOTOR-9)".
2. **Linhas 995 e 999 (bloco da #49):** título "Implementado, aguardando Gate 2" → "Commitado `410592d8`"; retirar
   "SEM COMMIT".
3. **Linha 44 (CRU-03):** a frase "meta >90% = 256: só a entrada offline dos 12 links (+13 → 259) cruza sem regra
   nova" descreve um cenário anterior; o handoff de 23/09 já registra os 13 materiais presentes e 248/284. Atualizar
   para o placar v2 (faltam +8; CG +11, SO +4).
4. **Entrada nova em "Concluído" ou na zona da validação externa:** "30/09, revisão independente do delta
   R-META/R-PAGE (`job-16`, papel `reviewer`, codex `gpt-6.1-sol`): NÃO APROVAR, 2 MAJOR (contagem de chunk truncado;
   Content-Length com transporte chunked). Gate 2 do delta não concedido. Relatório:
   `docs/reports/2026-09-30-revisao-delta-rmeta-rpage.md`."
5. **Entrada nova:** "30/09, dossiê de decisões do motor: `docs/reports/2026-09-30-dossie-decisoes-motor.md` (B1
   pelo coordenador; B2 pelo `planner-t2`, `job-18`)."
6. **WF (workflow):** "30/09, snapshot `.workflow/` sincronizado com a fonte `f07d786` (8 arquivos, +75/−27), aguardando Gate
   2."
7. **Delta Moodle (01/10):** "Duas revisões independentes do GPT sobre o delta R-META. 1ª: NÃO APROVAR (M-01, M-02;
   MAJOR documental B1-N1, baseline de `src/`). 2ª: o esboço de correção não basta (P-01 timeout/LineTooLong depois do
   payload; P-02 tamanho de chunk negativo além do teto). Plano revisado em `2026-09-30-noite-resumo.md` §12 com a
   direção do usuário (V1, CL ignorado em chunked, TE não suportado recusado, worktree isolada), aguardando a matriz
   Python e o Gate 1."

## 9. Estado das árvores ao terminar

- **Árvore principal** (`feat/motor-atribuicao`, `bf46d51f`, 6 commits à frente de `origin`, 4 stashes): intocada. Os
  três arquivos modificados continuam os mesmos (`pendencias.md`, `moodle.py`, `test_moodle.py`); sha256 do delta
  conferidos no fim.
- **Única escrita fora da worktree da noite:** `.workflow/local/` da árvore principal (estado da tarefa e a cópia
  datada do estado anterior), como pedido.
- **Worktree da noite:** 8 arquivos modificados em `.workflow/` e 3 relatórios novos não versionados em
  `docs/reports/2026-09-30-*.md`.
- Nenhum experimento, build, replay, rede ou LLM do motor. Gold, pacote cego e `.frzero/` não foram abertos.

## 10. Retomada da tarde (30/09, ~16:05–16:45)

Pedido do usuário: uma nova tentativa, dividida, da verificação da B1; conferir se o caminho 2b cobre os `job-05`/`job-06`;
retomar o roteiro e parar no Gate 2. Autorização registrada no estado antes de delegar (`b1_particionada_autorizada`).

### 10.1 B1 verificada em partes

Uma chamada `alethe_delegate`, papel `planner-t2`, label "NOITE-3009 B1 validação externa (partes)", `run-12`. Cada parte
com no máximo 3 decisões e 5 fontes. D4–D6 somava 6 fontes e foi dividida de novo. A única citação da D7 ao pré-registro
foi conferida na parte que já o lia.

| job | parte | resultado | duração | `askedToWrapUp` |
|---|---|---|---:|:---:|
| `job-19` | D1–D3 | timeout, texto completo entregue | 600,1 s | true |
| `job-20` | D4–D5 (+ C9 da D7) | succeeded | 536,7 s | true |
| `job-21` | D6–D7 | timeout, texto completo entregue | 601,1 s | true |
| `job-22` | D8–D9 | timeout, cortado antes das limitações | 600,4 s | true |
| `job-23` | R-VIS + R-CC | succeeded | 548,3 s | true |
| `job-24` | Gate 2 do delta | timeout, texto completo entregue | 601,1 s | true |

Todos: codex `gpt-6.1-sol`, somente leitura. Nenhuma parte foi relançada. Os textos de `job-20` e `job-23` foram
recuperados do log local da sessão Codex, porque a mensagem final só dizia "a tabela já foi entregue".

**Resultado:**

- 63 afirmações: 56 confirmadas, 3 divergem, 4 sem evidência (2 resolvidas pelo coordenador);
- 12 recomendações: 9 confirmadas, 2 com divergência (D6, D8), 1 sem evidência (R-CC).

O que mudou no dossiê:

- **D8:** E4 e E3 são medidas diferentes. Falhas vão no denominador de E4; E3 conta documentos cobertos.
- **R-CC:** a exclusão por conflito exige também ocorrências em unidades diferentes. A recomendação passou a "ajustar
  duas lacunas e aprovar".
- **D6:** menu ampliado (rota combinada exploratória + prospectiva; aprovar sem aplicar); recomendação passou a (iv).
- **R-VIS:** "só pela assinatura" corrigido para PDF e notebook; contradição do REL:218 registrada.
- **Gate 2 do delta:** entrou a opção "abandonar e retirar o delta". Registrado também que **não commitar não tira o
  delta de execução**: a árvore principal roda com o `_call` modificado.
- **Ressalvas menores:**
  - D1: C_novo com n = 10 exige 10/10;
  - D2: redação do risco;
  - D3: dependência de R-CC;
  - D4: versão ausente também invalida;
  - D5: regex exata do commit `71dff722`;
  - D7: alcance;
  - D9: congelar o escopo antes da busca.
- **Três contradições documentais novas:** P3:5 × P3:135; P3:160 × P3.1:64; REL:218 × REL:169–171.

**Sem validação:** D3 C11 (inferência), D5 C8 (não medido), o código do harness, a configuração atual do gitleaks, o
efeito de qualquer regra no lote e a seção de limitações do `job-22`. Detalhe:
`docs/reports/2026-09-30-b1-verificacao-partes.md`, com os seis textos em anexo.

### 10.2 `job-05`/`job-06` (caminho 2) × caminho 2b (`job-07`/`job-08`)

- `job-05` (W-E: bloco misto por vencedor bruto + confiabilidade do sinal de seção) e `job-06` (W-F: regra dentro da fase
  real + efeito na subunidade) estouraram os 600 s em 21/09 (`run-03`).
- **O caminho 2b sozinho não cobre o que eles fariam.** O W-G (`job-07`) explica o mecanismo da propagação e usa a saída
  do W-F como base; o W-H (`job-08`) mede outra variante ("seção sozinha").
- **A cobertura veio da recuperação feita em 21/09** (`pendencias.md:212–218`):
  - o W-E já tinha gravado script e JSON completos antes do corte (reexecutado: JSON byte-idêntico);
  - o W-F deixou só o script, com o alvo do patch errado; o coordenador trocou o alvo para
    `file_map.reconcile_unit_with_block` e executou (227 s).
  - Artefatos: `c1-3/regra_secao_misto_bruto_21-09.{py,json}` e `c1-3/regra_secao_efeito_subunidade_21-09.{py,json}`.
- **Pergunta por pergunta:**
  - W-E, objetivo 1: R' e R'-sem-corroboração dão 241/284 (+2/−0); o "misto bruto" não discrimina (30 blocos, 200/338
    entradas) (`pendencias.md:220–224`);
  - W-E, objetivo 2: sinal de seção certo em 45/45, com as 4 células (`pendencias.md:225–228`). A quebra por curso está
    no JSON (`section_signal_reliability.courses`, conferida só a existência da chave);
  - W-E, as 2 elegíveis não corroboradas: SO `laminas-sockets…` (`pendencias.md:229–231`) e TCC `aula-06…`, pelo W-H
    (`pendencias.md:263–268`);
  - W-F, perguntas 1–4: todas respondidas (`pendencias.md:234–242`).
- **O que falta, nada que peça decisão:**
  - efeito do R' na subunidade: não medido (`pendencias.md:270`). Valor baixo: o R' perde na unidade para o
    R-sem-misto (241 < 244), e este foi commitado como #47 (`9220a578`, `pendencias.md:1415`);
  - tokens dos `job-05`/`job-06`: não coletados (`pendencias.md:218`);
  - o resultado do W-F é do script corrigido pelo coordenador, não do worker (documentado).

Recomendação: não relançar.

### 10.3 Roteiro retomado

- **Revisão do delta:** concluída de madrugada (`job-16`); nada novo.
- **Dossiê:** B1 verificada e atualizada; B2 inalterada.
- **Sincronização de `.workflow/`:** refeita contra a fonte atual (`fba467c`); 8 arquivos, +75/−27, sem commit (§6).

**Parado no Gate 2.** Nada foi commitado. Aguardam decisão, na ordem do §7:

1. Gate 2 do delta Moodle;
2. correção do tracker da #49;
3. commit da sincronização de `.workflow/`;
4. decisões metodológicas.

Arquivos novos ou alterados à tarde, na worktree da noite:

- `docs/reports/2026-09-30-b1-verificacao-partes.md` (novo);
- `docs/reports/2026-09-30-dossie-decisoes-motor.md` (B1 atualizada);
- este resumo;
- `.workflow/task-state.template.md`, `.workflow/references/delegation.md` e `.workflow/manifest.json` (recopiados).

## 11. Rodada 2 da B1 e troca de coordenação (30/09 ~23:53 → 01/10 ~00:05)

O usuário passou a coordenação da NOITE-3009 para esta sessão; o orquestrador anterior (planner Alethe
`tsmq_2mmNF81XlNqqmYMe`) fica parado. Antes de delegar, o estado e o dossiê foram relidos e a troca foi registrada.

### 11.1 Rodada 2 — `run-13`, papel `planner-t2`, label "NOITE-3009 B1 partes (rodada 2)"

Specs idênticos aos da rodada 1 (sha256 conferido no `orchestrator-jobs.json`). No build novo do Alethe, o orçamento
entra antes do spec, o effort é medium e as menções a plugins no log do worker caíram (indício de que saíram).

*Redação corrigida em 01/10 (revisão do GPT):* nos quatro pares repetidos, o tempo até o término registrado caiu da
média de 600,677 s para 169,657 s. A primeira rodada foi censurada pelo timeout. A segunda registra effort medium; a
primeira não informa effort (`null`). Specs iguais, posição do orçamento e redução de plugins são relatos que o export
do Alethe não reproduz. A hipótese conjunta é razoável, mas a contribuição de cada alteração e a equivalência de
qualidade não foram medidas.

| job novo | refaz | resultado | tempo | antes dos 600 s? | rodada 1 |
|---|---|---|---:|:---:|---|
| `job-25` | `job-19` (D1–D3) | succeeded | 177,6 s | sim | timeout 600,1 s |
| `job-26` | `job-21` (D6–D7) | succeeded | 165,4 s | sim | timeout 601,1 s |
| `job-27` | `job-22` (D8–D9) | succeeded | 167,1 s | sim | timeout 600,4 s, cortado |
| `job-28` | `job-24` (Gate 2) | succeeded | 168,5 s | sim | timeout 601,1 s |

**Nenhum veredito se inverteu.** A D8–D9 chegou completa, e a B1 recebeu duas linhas "Rodada 2":

- D8: formatos fora da allowlist pesam na cobertura, não na acurácia; resolver D8 não autoriza aplicação;
- D9: congelar um escopo verificável; ampliar a busca não muda N1/N0 sozinha; familiaridade do adjudicador ≠
  exposição do motor.

O resto das nuances novas (D1 C_novo global, D3 desenho por ocorrência, Gate 2 corrigido por etapas) ficou no
relatório de verificação, seção "Rodada 2". Não relancei 11, 12, 13, 14, 15 nem 17.

### 11.2 `job-05`/`job-06`: o caminho 2b cobre? Relançar?

- **O caminho 2b (`job-07`/`job-08`) sozinho não cobre** o que `job-05`/`job-06` fariam. Ele mede o mecanismo da
  propagação (W-G) e outra variante (W-H), usando como base a saída do W-F.
- **Mas os entregáveis dos dois já existem**, recuperados pelo coordenador de 21/09 (`pendencias.md:212–245`):
  - o W-E (`job-05`) gravou script e JSON completos antes do corte, e a reexecução saiu byte-idêntica;
  - o W-F (`job-06`) deixou o script; o coordenador corrigiu o alvo do patch e executou.

  Pelo registro do tracker, as perguntas dos dois specs têm resposta, inclusive a quebra por curso
  (`section_signal_reliability.courses` no JSON do W-E). Falta o efeito do R' na subunidade (baixo valor: o R' perde
  para o R-sem-misto, commitado como #47, `9220a578`). *Corrigido em 01/10:* os tokens existem no export atual do
  Alethe (564.588 e 918.011 no total). "Não coletados" vale para a ocasião (21/09).
- **Não relancei.** O relançamento pedido (mesmo spec, papel `planner-t2`) é incompatível com os specs:
  - os dois specs exigem **gravar** script e JSON numa worktree isolada e executar replays (~99 s cada) com o Python
    do projeto;
  - no `orchestrator-jobs.json`, `job-05`/`job-06` tinham `sandbox: workspace-write`, worktree própria e timeout
    **configurado** de 900 s. A duração **observada** foi de ~600 s (600,012 e 600,029 s). A causa da diferença é
    desconhecida;
  - o `planner-t2` é `read-only` e tem 600 s;
  - os specs citam o HEAD `ce02a8f`, que não é mais o do branch.

  *Corrigido em 01/10:* a versão anterior dizia "falha garantida" e "todas as perguntas têm resposta". Isso excede o
  que se pode atestar: o pacote não continha os specs nem os artefatos completos.
- **Para decidir, se ainda quiser:** remedição com papel de escrita e spec atualizado para o HEAD atual. Um timeout
  acima de 600 s exige exceção explícita (`references/delegation.md`, máximo 600 neste contrato). Não recomendo: o
  resultado já existe e a decisão foi fechada pela #47.

### 11.3 Gate 2

Parado no Gate 2. Nada foi commitado. Aguardam decisão, na ordem do §7:

1. Gate 2 do delta Moodle;
2. correção do tracker da #49;
3. commit da sincronização de `.workflow/` (8 arquivos, +75/−27);
4. decisões metodológicas.

## 12. Plano para o próximo Gate (01/10, depois da revisão do GPT)

A revisão independente do GPT (`Codex/2026-10-01/files-mentioned-by-the-user-noite/outputs/Do_Gpt/`) foi incorporada.
Ela tem dois arquivos: `revisao_noite_30-09.md` e `reprodutores_noite_30-09.json`, com 29 casos HTTP offline e 38
citações conferidas. Veredito: **NÃO APROVAR** o delta atual, com dois MAJOR técnicos confirmados e um MAJOR
documental novo (baseline de `src/`).

**Estado conferido antes de planejar:**

- branch `feat/motor-atribuicao`, HEAD `bf46d51f`, 6 commits locais, 4 stashes;
- o delta é o mesmo que foi revisado: `moodle.py` `24430123…`, `test_moodle.py` `99951fdb…`, +193/−1;
- `escaladas_automaticas = 3`; Gate 2 pendente;
- há um `.codex/hooks.json` não versionado de outra sessão, que não foi tocado.

Este handoff não concede Gates. Abaixo está o escopo pronto para aprovação; **nada foi implementado**.

### 12.1 Correção técnica do `MoodleClient` — plano revisado (3ª revisão do GPT, 01/10); pronto para Gate 1, não implementado

**Histórico.**

- A 1ª revisão do GPT confirmou M-01 e M-02.
- O primeiro esboço (`chunked`/`chunk_left` no `except`) foi superado pela 2ª revisão, que achou mais dois MAJOR:
  - **P-01:** `TimeoutError` ou `LineTooLong` depois do payload perde a contagem (A18, A19, A33, A34);
  - **P-02:** tamanho de chunk negativo leva a `read(-1)` (detalhe na tabela de comportamentos, corrigido pela D-02).
- A 3ª revisão (`revisao_direcao_01-10.md`) não achou CRITICAL nem MAJOR novos e deu 5 MINOR (D-01 a D-05), todos
  incorporados abaixo.
- **A V1 é plausível, não validada.** Os defeitos anteriores permanecem. Nenhum desenho novo foi implementado ou
  pré-verificado. Os registros históricos (`reprodutores_*.json`, 169/169 flags conferidos pela 3ª revisão) não foram
  reescritos: uma mudança de oráculo não muda resultado anterior.

**Direção definida pelo usuário em 01/10.** Ela fixa o escopo do Gate 1, mas **não concede o Gate 1**:

1. V1 como desenho inicial, com testes comportamentais dos quatro defeitos. Se falhar: registrar caso, causa e versão
   de Python, e reconsiderar por decisão nova, sem troca automática para a V2.
2. Ignorar o Content-Length em chunked e recusar Transfer-Encoding não suportado antes do corpo, com contrato e testes
   explícitos.
3. Matriz Python definida antes de implementar; restrição de suporte só por decisão expressa.
4. Worktree isolada, árvore principal preservada (inclusive as mudanças alheias e os estados locais). O baseline VOCAB
   segue separado e obrigatório antes da validação externa.
5. Gate 2 sobre o conjunto: REL/ISS autorizados, consumidores conferidos e revisão independente autorizada.
6. Sem meta de quantidade de testes: demonstrar comportamentos, distinguindo reprodutores de defeito e controles.

**Autorizações necessárias, próprias e ainda não dadas:**

1. Gate 1: criação da worktree isolada e edição de `src/builder/sources/moodle.py` e `tests/test_moodle.py` nela. Se
   a D-RUNTIME restringir o suporte, entram também `pyproject.toml` e `.github/workflows/validate-timeline.yml` (D-04);
2. edição de REL/ISS antes do Gate 2;
3. revisão independente do conjunto (`escaladas_automaticas` 3 → 4);
4. integração na árvore principal depois do Gate 2. Merge, se for a operação escolhida, tem autorização própria.

**Requisitos do contrato:**

| id | requisito | origem |
|---|---|---|
| R1 | Todo fragmento de payload que a **aplicação** recebe do `HTTPResponse` é contado e fica em `ultimo_corpo` assim que chega, inclusive quando a leitura seguinte termina em `IncompleteRead`, `TimeoutError`, `LineTooLong` ou outra exceção. Mede o corpo lido pela aplicação (REL:286–288; `moodle.py:425–426`), não o tráfego de rede/TLS. Bytes retidos em buffers inferiores que nenhuma exceção expõe não são presumidos | M-01, P-01 |
| R2 | Nenhum pedido de payload sob limite excede o saldo naquele instante. Tamanho de chunk **negativo** é recusado **antes de qualquer leitura de payload**, com ou sem limite e com ou sem CL. A recusa é `http.client.IncompleteRead` com o parcial já contado, como no oráculo dos reprodutores (A21/A22/A35). A demonstração é a instrumentação, não o contador. **Não é parser estrito:** a linha de tamanho segue o `int(linha, 16)` da stdlib, e as demais tolerâncias de sintaxe ficam declaradas | P-02 |
| R3 | Framing não conta: linha de tamanho, extensões, CRLF e trailers ficam fora do contador e do corpo, inclusive o parcial de CRLF (C16) | C16 |
| R4 | Em resposta chunked, o Content-Length é ignorado na recusa antecipada e na prova de completude | M-02 |
| R5 | Transfer-Encoding presente que não seja `chunked` é recusado antes de ler o corpo. Normalização, listas, cabeçalhos repetidos e tipo de exceção: proposta abaixo, a confirmar antes do Gate 1 (§12.3) | direção 2; A23, A24 |
| R6 | Sem limite, o resultado é o mesmo do `r.read()` nos casos conformes. As tolerâncias de framing da stdlib mantidas pela V1 (A11, A13–A15, A32) e as de sintaxe da linha de tamanho ficam declaradas. Nada é endurecido sem decisão | ISS A6:344–345; P-03 |

**Proposta para o contrato R5** (escolha material, a confirmar no §12.3):

- comparar como a stdlib: `valor.lower() == "chunked"` (`http/client.py:351–352`), sem diferenciar caixa e sem outra
  normalização (`Chunked` continua aceito, como hoje);
- aceitar só um coding, `chunked`;
- recusar listas (`gzip, chunked`), qualquer outro coding (inclusive `identity` e `gzip`) e cabeçalhos
  `Transfer-Encoding` repetidos;
- exceção: `http.client.UnknownTransferEncoding`, que já existe na stdlib (`http/client.py:1496`); não criar classe
  nova;
- a recusa vem antes de qualquer leitura do corpo, sem contar nada.

**Desenho inicial (V1), a demonstrar com os testes:**

- **Fragmento contado antes de avançar no framing.** O `read1` não garante uma única chamada de sistema para toda a
  operação chunked: `_get_chunk_left` pode fazer mais de uma leitura (`http/client.py:697–698`). A propriedade usada é
  outra: com tamanho positivo validado, `_read1_chunked` devolve no máximo um fragmento do chunk corrente sem avançar
  para o próximo, e o candidato conta esse fragmento antes de voltar ao framing.
- **Pré-validação do tamanho.** Antes de cada leitura de payload, obter o estado do chunk e decidir:
  - payload pendente (`chunk_left > 0`): ler `read1(min(pedido, saldo, chunk_left))`;
  - transição (`0`): resolver o framing antes de qualquer leitura de payload;
  - fim (`None`): não ler mais nada;
  - negativo: recusar (R2).

  O ramo de fim fica fora do `min(...)`. Dependência declarada: membros privados `HTTPResponse._get_chunk_left` e
  `chunk_left`, cobertos pela matriz.
- **Parciais de framing.** Um `IncompleteRead.partial` vindo direto de `_get_chunk_left` pode ser CRLF e não entra
  (R3). O `except` atual, que soma `exc.partial`, não pode ser reaproveitado sem distinguir a fase.
- **`from exc`.** A causa fica encadeada. O parcial agregado da exceção externa é o oficial e os consumidores não
  somam a cadeia (A08). Conferir a UI (`dialogs.py:1719`) e o `adquire` v5 antes do aceite.
- **Uso sequencial por instância (M-03):** só documentação, sem lock.
- **Falha da V1:** se algum comportamento abaixo não for alcançado, registrar caso, causa e versão de Python, parar e
  submeter um desenho novo ao usuário.

**Comportamentos que a V1 tem de demonstrar** (riscos inferidos pela 3ª revisão, item 3; reaproveitar casos quando
bastarem):

| ponto | risco | comportamento a demonstrar | casos |
|---|---|---|---|
| chunk terminal | `_get_chunk_left()` pode devolver `None` depois de consumir o chunk 0 e os trailers; `0` também marca o fim de um chunk comum, ainda com framing pendente | distinguir payload pendente, transição e fim; não ler payload nem repetir framing depois do fim. `[]` seguido de zero dá sucesso quando o saldo permite confirmar o fim. Resposta só com o chunk zero tem corpo vazio, e `_call` segue sujeito a `JSONDecodeError` | C02, A01, A02; caso novo "só chunk zero" |
| trailer, linha longa e timeout no framing | obter o próximo tamanho pode ler trailers e lançar `LineTooLong` ou timeout antes de retornar | payload anterior já contado; tamanho, extensões, CRLF e trailers fora do corpo e do contador; tolerâncias mantidas | A18, A19, A33, A34; controle A20 |
| parcial de CRLF | contar o `\r` de um CRLF truncado como payload | `2\r\n[]\r`: corpo `[]`, 2 bytes, sem `\r` | C16, C17, A09, A10 |
| `read1` curto | tratar retorno curto como fim, decrementar `chunk_left` duas vezes ou avançar o framing cedo | continuar depois de retorno curto não vazio, contar o tamanho real uma vez, manter o restante do chunk. A stdlib já decrementa `chunk_left`; o candidato não repete. Incluir chunk maior que o bloco de leitura | C09, M1d, A07; caso novo com transporte curto em chunked |
| timeout no meio do payload | perder ou duplicar fragmentos já entregues | reter exatamente os fragmentos já entregues, propagar o timeout, não zerar nem duplicar | caso novo: retorno curto dentro do chunk e timeout na leitura seguinte |
| sem CL, não chunked | tratar retorno curto como fim; usar `chunk_left` nesse ramo | repetir `read1` até o fim; sucesso com fim confirmado e saldo suficiente; recusa conservadora no saldo exato, sem sondar um byte a mais | C04, C05, C10 |
| CL válido, não chunked | `read1` pode devolver vazio antes do CL sem levantar `IncompleteRead` | C01 com sucesso no saldo exato; C11 com truncamento e parcial; leituras curtas não mudam a completude | C01, C09, C11 |
| saldo exato em chunked | chamar `_get_chunk_left()` depois de esgotar o saldo confirmaria o chunk terminal e mudaria a recusa conservadora | preservar o oráculo histórico de C03 e A31 (recusa no saldo exato) e a ordem saldo → framing | C03, A31 |
| tamanho negativo, inclusive com CL conflitante | chamar `read1` antes de validar leva a `fp.read1(-1)`; ajustar o contador depois não contém a leitura | nenhuma leitura de payload, conferida na operação de baixo nível. Com saldo positivo, a recusa vem da validação do tamanho, não do CL | A21, A22, A35 |

**Comportamentos a demonstrar por defeito.** Stream instrumentado por fase (payload × framing), registrando também as
operações que lançam exceção, e cada abertura de `urlopen`. O helper `_resposta_http` (`test_moodle.py:556`) ganha a
opção chunked e a instrumentação.

A coluna "registro no delta atual" vem dos reprodutores do GPT sobre o delta `24430123…` (CPython 3.11.9; os casos A
também em 3.13.12). O estado real de cada teste é registrado antes da correção.

| comportamento | casos | registro no delta atual | oráculo do candidato |
|---|---|---|---|
| payload de chunk interrompido é contado (M-01) | M1a, M1b, M1c, M1d, A07, A08 | **reproduz defeito** | contador, `ultimo_corpo` e `exc.partial` com o payload; causa presente; sem duplicação nem framing |
| CL não governa resposta chunked (M-02, R4) | M2a, M2b, M2c, A02, A03, A12, A16 | **reproduz defeito** | M2a, M2c, A02, A12, A16: sucesso com o payload. M2b, A03: `OrcamentoExcedido` no saldo, sem pedir payload além dele |
| payload contado antes de falha de framing (P-01) | A18, A19, A33, A34 | **reproduz defeito** (0 de 2 bytes) | exceção propagada (`LineTooLong` ou `TimeoutError`); 2 bytes; `ultimo_corpo` = `[]` |
| tamanho negativo recusado antes do payload (P-02, R2) | A21 | **reproduz defeito:** sem limite, `read(-1)` consumiu **3 bytes** (`[] `) e terminou em `IncompleteRead` | `IncompleteRead` antes de qualquer leitura de payload; 0 bytes; corpo vazio |
| idem, sob limite | A22 | **reproduz defeito:** saldo 2, `read(-1)` consumiu **23 bytes**, **21 além do saldo** | idem |
| idem, com CL conflitante (R4 + R2) | A35 | **reproduz defeito de R4:** zero consumo, mas por recusa **indevida** baseada no CL (`OrcamentoExcedido`). Os 23 bytes são do **esboço anterior**, não do delta | CL ignorado e tamanho negativo recusado antes do payload: `IncompleteRead`, 0 bytes, corpo vazio. A instrumentação tem de mostrar que a validação do tamanho foi alcançada; contador zero sozinho não basta, e o texto da mensagem não é oráculo |
| Transfer-Encoding não suportado recusado antes do corpo (R5) | A23, A24 | **regra nova de contrato:** A23 aceita 2 bytes de `[]xxx` sob CL 2; A24 é tratado como não chunked, consome 12 bytes e dá `JSONDecodeError` | exceção de R5 antes de qualquer leitura do corpo |
| controles de saldo, leitura e erros | C01–C20, R02, A01, A04–A06, A09, A10, A17, A20, A25–A31 | **controle verde** nos observáveis do oráculo histórico; as asserções novas desta seção ainda não foram verificadas | mantém o resultado |
| tolerâncias de framing mantidas na V1 | A11, A13, A14, A15, A32 | **controle verde sob a tolerância declarada** (o oráculo estrito antigo os marcava como falsos; esses flags históricos ficam como estão) | aceita o payload íntegro; o contrato declara a tolerância |
| reentrância (M-03) | R01 | defeito condicional | fora do escopo de código: só documentação |

**Testes existentes reaproveitados:**

| casos | teste | ajuste |
|---|---|---|
| C01: CL no saldo exato → sucesso | `test_call_corpo_exatamente_no_limite_com_termino_confirmado` (`:594`) | — |
| C04, C05 | `test_call_termino_nao_confirmado_nao_ultrapassa_o_orcamento` (`:601`) | — |
| C06 | `test_call_content_length_acima_do_orcamento_nao_le_o_corpo` (`:612`) | zero leituras de corpo |
| C07, C08 | `test_call_orcamento_esgotado_nao_abre_a_requisicao` (`:631`) | zero aberturas; saldo negativo |
| C11 | `test_call_corpo_truncado_conta_e_preserva_o_parcial` (`:621`) | — |
| C13, C15 | `test_call_json_invalido_e_erro_da_api_contam_bytes` (`:640`) | — |
| interrupção entre blocos | `test_call_interrupcao_preserva_a_contagem_dos_blocos_lidos` (`:653`) | — |

Os demais casos entram parametrizados por comportamento, não um teste por ID.

**Asserções (D-05):**

- **em todas as falhas:** tipo da exceção, contador, `ultimo_corpo` e operações realizadas (aberturas e leituras por
  fase, inclusive as que lançaram exceção);
- **`partial` e encadeamento só quando o contrato da exceção os prevê:** `IncompleteRead` reconstruído ou repassado.
  Não se exige essa interface de `TimeoutError`, `LineTooLong`, `JSONDecodeError` ou `OrcamentoExcedido`;
- **pedido ≤ saldo:** só nos pedidos de **payload sob limite**, contra o saldo daquele instante;
- **framing:** instrumentado à parte. Uma `readline` de framing pode pedir mais que o saldo de payload sem violar R2,
  e seus bytes nunca entram no contador.

**Matriz Python (D-RUNTIME, decidir antes do Gate 1):**

| item | situação em 01/10 |
|---|---|
| suporte declarado | `pyproject.toml:6`, `requires-python = ">=3.8"`; CI `.github/workflows/validate-timeline.yml:36`, `python-version: "3.11"` |
| CPython instalados nesta máquina | 3.11.9 (`.venv` e Python311), 3.13.12 (uv), 3.14.3 (launcher `py`) |
| não instalados | 3.8, 3.9, 3.10, 3.12 |
| já executados pelo GPT | 3.11.9 e 3.13.12, sobre o delta e o esboço descartado; nunca sobre a V1 |

A escolha fica com o usuário: as versões concretas (implementação e patch) a validar, e se o suporte declarado se
mantém ou é restringido por decisão expressa. Se restringir, os dois arquivos acima entram no escopo do Gate 1 (D-04).
Se não, nenhuma edição de suporte. Pinar uma versão não elimina P-01 nem P-02.

**Execução, depois do Gate 1 (D-03):**

1. criar a worktree isolada a partir de `bf46d51f`;
2. copiar byte a byte os dois arquivos do delta da árvore principal e conferir o sha256 completo (`244301234d67…`,
   `99951fdbdc2a…`);
3. registrar base, ambiente e versão de Python de cada runtime da matriz;
4. **suíte baseline original**, antes de qualquer mudança de produto ou teste: `python -m pytest tests -q`, no
   3.11.9 (nos demais runtimes, o harness stdlib, conforme o plano noturno), registrando coleta, pulos e falhas com IDs;
5. **inclusão dos testes de comportamento**, sem mudar o produto: rodar de novo e registrar o estado real de cada
   teste contra o delta (vermelho/verde). Separar a mudança de coleta e de falhas causada pelos testes novos do
   baseline original;
6. implementar a V1, sem tocar a árvore principal;
7. **resultado depois da correção:** suíte e testes de comportamento conforme a matriz escolhida (pytest só em
   3.11.9; harness stdlib antes/depois em 3.13.12 e 3.14.3; ver `2026-09-30-plano-noite-correcao-moodle.md`), comparados com os passos 4 e 5,
   na mesma worktree e no mesmo ambiente. Não reconstruir o "antes" de memória nem comparar com placar de outra
   árvore;
8. conferir os consumidores (UI e `adquire` v5) e reexecutar a aquisição v5 offline, em processo separado;
9. documentos autorizados, revisão autorizada e Gate 2.

**Critérios de aceite:**

1. cada comportamento das duas tabelas demonstrado: reprodutores de vermelho para verde (vermelho registrado no
   passo 5), controles verdes, regra nova (R5) com teste próprio; sem meta numérica;
2. a instrumentação prova R2 em todos os casos, inclusive com framing inválido e nas operações que lançaram exceção;
3. suíte comparada entre os passos 4, 5 e 7 (pytest em 3.11.9; harness nos demais runtimes, sem alegar pytest onde
   só houve harness). Cada diferença é identificada e avaliada; explicar uma
   regressão não basta para aceitá-la;
4. matriz conforme a D-RUNTIME, verde nas versões escolhidas;
5. consumidores conferidos e aquisição v5 offline sem regressão;
6. REL §6 (linhas 292 e 299–300) e ISS A2/A6 atualizados **com autorização própria**: contrato R1–R6, tolerâncias da
   V1, R5 e uso sequencial;
7. grafo atualizado (tarefa operacional);
8. revisão independente autorizada sobre o conjunto;
9. Gate 2 sobre o conjunto, sem commit parcial.

**Pendente fora do código:** definir o uso permitido da árvore principal enquanto o Gate 2 está pendente. Ela já usa
o `_call` modificado.

### 12.2 Ajustes documentais

**Feitos nesta retomada** (worktree da noite, sem commit):

- **dossiê:**
  - #49: "registrado como aprovado"; `origin` é referência local, sem fetch;
  - D6: o lote é oportunidade disponível, não exclusividade; confirmação com protocolo congelado antes;
  - D7: o resultado vazio vale para a v2 preservada integralmente;
  - Gate 2: parecer do GPT, armadilha do CRLF, M2c e reentrância;
  - R-CC: redação da lacuna 2; a lacuna 1 depende de escolha do usuário;
  - seção nova "B1 — Dependências e pré-condições de execução": baseline `src/`, R-VIS, R-PAGE, R-CC, D9/D4/D5 e
    precedência v3/v5;
- **resumo:**
  - `plannerId` por faixa de jobs;
  - tempo da rodada 2 sem causa isolada;
  - 900 s configurados × ~600 s observados;
  - tokens dos `job-05`/`job-06` disponíveis;
  - "falha garantida" retirado;
  - versão-fonte do workflow fixada em `f07d786` (blobs na tabela do §6; `delegation.md` recopiada);
- **revisão do delta:** adendo com o parecer do GPT (§8 do relatório).
- **depois da 2ª revisão do GPT (01/10):** §12.1 e §12.3 reescritos (P-01, P-02, P-04, P-05); depois, ajustados à direção
  do usuário (V1 inicial sem troca automática para V2, ignorar CL em chunked, recusar TE não suportado, matriz antes de
  implementar, worktree isolada, comportamentos em vez de contagem de testes);
- **depois da 3ª revisão do GPT (01/10):** D-01 a D-05 incorporados no §12.1 e no §12.3 (A35 sem alternativa;
  números de A21, A22 e A35; ordem da suíte baseline; D-RUNTIME com arquivos condicionais; asserções por contrato);
  comportamentos da V1 explicitados; precisões de R1, R2, R5 e do `read1`; adendos no dossiê e na revisão do delta (§10).
  prova commit/tree do `f07d786` acrescentada ao §6; adendo no relatório da revisão do delta (§9) e no dossiê.

**Pendentes, com autorização própria** (ficam fora da worktree da noite):

- fontes da validação em `c1-3` (não versionadas):
  - P3:5 × P3:135 (escopo de D6);
  - REL:218 (pixels "já aceitos") e REL:195–196 ("só assinatura");
  - REL:292 e REL:299–300 (promessas do R-META);
  - P3:19 ("nenhum limiar alterado": o mínimo por curso foi introduzido);
  - redação de precedência v3/v5;
  - P3.1 §4.2 (sensibilidade do `?`);
- tracker `pendencias.md`: o delta proposto no §8 e as entradas da noite;
- fonte canônica do workflow, em escopo próprio:
  - a contradição de Luna (`routing.md:25` × `:68–69`);
  - as regras Astra/Fable antigas em `agents/agy-auditor.md:17` e `pendencias_workflow.md:20–21`.

### 12.3 Decisões do usuário, em ordem (revisado em 01/10, com a 3ª revisão do GPT)

**Já definidas pelo usuário em 01/10, como direção do escopo** (não são Gates):

- V1 inicial, sem troca automática para a V2;
- ignorar o Content-Length em chunked;
- recusar Transfer-Encoding não suportado antes do corpo;
- matriz antes de implementar;
- worktree isolada, árvore principal preservada;
- baseline VOCAB separado e obrigatório antes da validação externa;
- Gate 2 sobre o conjunto;
- comportamentos em vez de contagem.

O antigo "oráculo do A35" **saiu da lista** (D-01): o R4 já decide que o candidato ignora o CL e recusa o tamanho
negativo antes do payload.

**Pendentes, em ordem:**

1. **D-RUNTIME, antes do Gate 1:**
   - as versões concretas (CPython, patch) a validar. Instaladas hoje: 3.11.9, 3.13.12 e 3.14.3. Não instaladas: 3.8,
     3.9, 3.10 e 3.12;
   - manter `>=3.8` ou restringir o suporte por decisão expressa. Se restringir, `pyproject.toml` e
     `.github/workflows/validate-timeline.yml` entram no escopo do Gate 1 (D-04).

   Não escolhi por você.
2. **Contrato R5**, escolha material apresentada antes do Gate 1. Proposta do §12.1:
   - comparação como na stdlib (`lower() == "chunked"`, sem diferenciar caixa);
   - só `chunked` aceito;
   - listas, outros codings (inclusive `identity`) e cabeçalhos repetidos recusados;
   - exceção `http.client.UnknownTransferEncoding`.

   Confirmar ou ajustar.
3. **Uso permitido da árvore principal** enquanto o Gate 2 está pendente: o delta está ativo nela.
4. **Gate 1 da correção** (escopo 12.1, com os arquivos condicionais da D-RUNTIME): worktree isolada e edição dos
   arquivos nela.
5. **Autorização dos documentos** REL/ISS antes do Gate 2; depois, da revisão independente do conjunto.
6. **Integração na árvore principal depois do Gate 2:** merge, se for a operação escolhida, tem autorização própria.
7. **Baseline de `src/` × congelamento VOCAB** (B1-N1, aberta): árvore de aquisição separada ou emenda metodológica
   explícita, sem atualizar o hash automaticamente. Antes de qualquer validação externa; a correção offline e a
   aquisição v5 de ensaio não liberam aquisição real, motor, gold, P3/P3.1 nem elegibilidade.
8. **Tracker:** #49 e entradas da noite (§8).
9. **Commit do sync de `.workflow/`** (8 arquivos, fonte `f07d786`). As contradições Luna e Astra/Fable ficam para
   escopo próprio.
10. **Metodologia**, sem mudança:
    - P3.1 (D1–D3, D6–D8);
    - R-CC: status da lacuna 1;
    - R-VIS;
    - R-PAGE;
    - D4, D5 e D9.
11. **CRU-02/03/05:** não reabertas.
12. **Ajustes** nas fontes `c1-3` e na fonte do workflow, com escopo próprio.

Este handoff não concede Gates. Parado antes de qualquer implementação. Sem commit.
