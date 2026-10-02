# Revisão independente do delta R-META/R-PAGE (30/09/2026)

**Veredito do revisor: NÃO APROVAR o commit dos dois arquivos.** 0 CRITICAL, 2 MAJOR, 0 MINOR.

Nada foi corrigido. O delta continua como estava, não commitado, na árvore principal. O Gate 2 é do usuário.

## 1. Identificação

| campo | valor |
|---|---|
| tarefa | trabalho noturno 30/09, Frente A (`.workflow/local/active-task.md`, `noite-20260930-revisao-dossie-sync`) |
| papel | `reviewer` (somente leitura) |
| jobId / runId | `job-16` / `run-10` |
| threadId | ver §6 |
| plannerId | `uH6KXeXmvLUm9gqp5RmjD` |
| modelo observado | ver §6 |
| label | "NOITE-3009 revisão delta R-META/R-PAGE (relançamento)" |
| cwd | `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator` (o delta só existe na árvore principal) |
| branch / HEAD | `feat/motor-atribuicao` / `bf46d51f` |
| diff fixado | `git diff -- src/builder/sources/moodle.py tests/test_moodle.py` (+193/−1) |
| `src/builder/sources/moodle.py` | sha256 `244301234d671b4ebb990499c96d4f2a6257348d614abcc15ee3e987c12b319b` |
| `tests/test_moodle.py` | sha256 `99951fdbdc2a2618c3a164ada26e70111a5486e02e00d14e0731f4fcc4be5716` |

Os dois sha256 foram conferidos pelo coordenador antes da delegação e pelo revisor (`Get-FileHash`). São os mesmos
registrados em 29/09 no `relatorio_correcoes_etapa3.md`, §6.2.

Contrato entregue ao revisor: `issue_correcoes_etapa3.md` (Adendo 2: A2 = R-META, A3 = R-PAGE, A6 = aceite; Adendo 3),
`relatorio_correcoes_etapa3.md` (§6, §6.1, §6.2) e `ESCOPO_REVISAO.md`, todos em
`docs/reports/_harness-2026-09-04/c1-3/`. O revisor não abriu gold, pacote cego gerado, `.frzero/` nem credenciais.

## 2. Tentativas

| tentativa | job | resultado |
|---|---|---|
| 1 (~02:20) | `job-11` / `run-06` | interrompida pelo fechamento do Alethe às 02:29 (bug do app); sem resultado |
| — | `job-14` / `run-08` | consta como `cancelled` aos 95 s ("cancelled by the lead"); não foi lançada por chamada registrada desta sessão; sem resultado |
| 2 (~02:59, relançamento único autorizado pelo usuário) | `job-16` / `run-10` | **concluída (`succeeded`)**; achados abaixo |

`escaladas_automaticas = 3` no estado: 1 da revisão da etapa 3 (29/09), 1 da tentativa interrompida e 1 do
relançamento autorizado. Não há nova revisão autorizada depois desta.

## 3. Achados (texto do revisor)

### MAJOR 1 — `src/builder/sources/moodle.py:452–455`: perde bytes de chunks truncados

O tratamento soma apenas `exc.partial`; no `HTTPResponse` real, parte do payload pode estar no `IncompleteRead` de
`exc.__cause__`.

- **Reproduzido pelo revisor:** `5\r\nabc` registra **0 dos 3 bytes** recebidos; depois de um chunk completo, registra
  **2 de 5**. `ultimo_corpo` e a exceção também perdem esses bytes.
- **Impacto:** a aquisição persiste consumo inferior ao real e libera orçamento indevido para as chamadas seguintes.
- **Correção sugerida (não aplicada):** preservar e contar o parcial do payload da exceção interna, sem duplicar chunks
  nem contar framing, com regressão para os dois casos.

### MAJOR 2 — `src/builder/sources/moodle.py:440–444,461–464`: usa Content-Length mesmo quando o transporte é chunked

O `HTTPResponse` desconsidera esse comprimento quando a resposta é chunked, mas o cliente o usa para validar a
completude.

- **Reproduzido pelo revisor:**
  - chunked completo contendo `[]`, com Content-Length 999, funciona com a leitura anterior (`r.read()`); o delta lança
    `IncompleteRead(..., 997)` **sem limite**;
  - com Content-Length 2, limite 2 e payload chunked `[]xxx`, `_call` aceita `[]` embora o transporte ainda não tenha
    terminado.
- **Impacto:** quebra a compatibilidade sem limite e aceita um fragmento JSON como resposta completa.
- **Correção sugerida (não aplicada):** tratar chunked sem usar Content-Length como prova de término, ou recusar
  explicitamente cabeçalhos conflitantes, cobrindo os dois cenários.

## 4. Respostas às perguntas do brief (texto do revisor)

1. **Contagem correta em todos os caminhos? Não:** achados 1–2. Nos casos exercitados não houve leitura além do saldo
   nem contagem duplicada; leituras curtas continuaram corretamente. `moodle.py:447–464`.
2. **Fronteiras? Parcialmente:** comprimento conhecido exatamente no saldo funciona; sem comprimento, atingir o saldo
   gera recusa conservadora. Limite zero e consumo acima do limite recusam antes da requisição.
   `IncompleteRead.expected` foi correto no truncamento comum, mas o re-raise perde o parcial chunked.
   `moodle.py:452–469`.
3. **Recusa antecipada respeita o contrato? Sim:** sem leitura, `parcial == b""` é coerente. Há divergência nominal com
   o `bytes_lidos` do issue (A2, linha 202); os consumidores inspecionados usam o contador do cliente e não dependem
   desse atributo. `moodle.py:416–418,443–444`; `adquire.py:277–279,398–399`.
4. **Muda algo sem limite? Sim:** achado 2. A UI captura a nova falha, mas deixa de receber uma resposta antes aceita.
   `moodle.py:461–475`; `src/ui/dialogs.py:1719–1723`.
5. **Estado coerente? Sim no uso sequencial, exceto pelo achado 1:** falhas em `urlopen` ou na entrada do `with`
   preservam a última resposta efetivamente lida; JSON inválido e erro da API acontecem depois da contagem. A retenção
   do último corpo é explícita; reentrância concorrente não foi validada. `moodle.py:429–439,474–477`.
6. **Cobertura dos testes novos? Incompleta:** o transporte usa `HTTPResponse` real, mas não gera chunked; faltam as
   regressões dos achados 1–2. A asserção de contador zero não demonstra sozinha a ausência de leitura.
   `tests/test_moodle.py:556–567,612–628`.
7. **Relatório §6 sustentado pelo código? Não integralmente:** as afirmações de compatibilidade sem limite e de
   contagem das respostas incompletas não se sustentam nos cenários reproduzidos.
   `relatorio_correcoes_etapa3.md:292,299–300`.
8. **adquire v5 e R-PAGE (secundário)? Sem bloqueio adicional na inspeção:** saldo comum, `finally` e consumo
   persistido estão conectados corretamente, mas propagam a subcontagem do achado 1. R-PAGE filtra arquivos nos dois
   caminhos; o gerador aplica o filtro antes do predicado. `adquire.py:151–168,272–294,363–373`;
   `gera_pacote_cego.py:591–605`.

## 5. O que o revisor executou e o que foi só inspeção

**Executado:**

- `Get-FileHash` nos dois arquivos: sha256 conferem;
- `git branch --show-current`, `git rev-parse HEAD`, `git diff --numstat`: branch, HEAD e +193/−1 conferem;
- dois comandos `python -B -`, sem arquivos nem rede: executaram em memória as definições extraídas do arquivo fixado
  contra `HTTPResponse` sobre `BytesIO`. Reproduziram os dois achados e verificaram comprimento inválido/zero, leitura
  curta, fronteiras e corpos de 65.536 e 65.539 bytes.

**Só inspeção:** contrato, relatório, testes e consumidores delimitados.

**Limitações declaradas pelo revisor:**

- não executou pytest: a suíte grava em `tmp_path`, incompatível com o requisito de nenhuma escrita;
- não confirmou os resultados históricos das suítes nem a persistência/R-PAGE por execução;
- não revisou integralmente os testes do harness;
- reentrância concorrente não validada.

Nenhum arquivo foi escrito pelo revisor.

## 6. Dados do Job e conferência do coordenador

**Job (alethe_status depois da coleta, ~03:10 de 30/09):**

| campo | valor |
|---|---|
| jobId / runId | `job-16` / `run-10` |
| threadId | `01a0f0e4-e75d-75b2-bc5b-dc19125c7892` |
| papel | `reviewer` |
| modelo observado | codex `gpt-6.1-sol` (effort não informado pelo status), `readOnly = true` |
| resultado | `done` / `succeeded` |
| duração | 585,6 s (orçamento de 600 s) |
| tokens | 483.313 no total (entrada 475.395, dos quais 409.856 em cache; saída 7.918) |
| diff produzido | nenhum (`hasDiff = false`) |

**Conferência do coordenador (medida, somente leitura).** Os dois achados foram reproduzidos de forma independente:
`python -B`, módulo carregado do arquivo fixado por caminho (sem importar o pacote, sem gravar bytecode), transporte
`http.client.HTTPResponse` sobre `BytesIO`, `urlopen` substituído em memória. Python 3.11.9. O sha256 de `moodle.py`
depois da conferência continua `24430123…` e `git status --short src tests` mostra só os dois arquivos do delta.

| caso | payload recebido | delta (`_call`) | leitura anterior (`r.read()`) |
|---|---:|---|---|
| 1a. chunk truncado `5\r\nabc` | 3 bytes | `IncompleteRead(0 bytes read)`, `bytes_recebidos = 0`, `ultimo_corpo = b''` | `IncompleteRead` com `partial = b''`; os 3 bytes estão em `__cause__.partial` |
| 1b. chunk completo de 2 + chunk truncado (3 de 5) | 5 bytes | `IncompleteRead(2 bytes read)`, `bytes_recebidos = 2` | `partial = b'[]'`; `b'abc'` em `__cause__.partial` |
| 2a. chunked completo `[]` com Content-Length 999, sem limite | 2 bytes | `IncompleteRead(2 bytes read, 997 more expected)` | devolve `b'[]'` |
| 2b. chunked `[]xxx` com Content-Length 2 e limite 2 | 5 bytes | devolve `[]`, `bytes_recebidos = 2` | devolve `b'[]xxx'` |
| controle: Content-Length 2, corpo `[]`, sem limite | 2 bytes | devolve `[]`, `bytes_recebidos = 2` | `b'[]'` |
| controle: chunked completo `[]`, sem Content-Length, sem limite | 2 bytes | devolve `[]`, `bytes_recebidos = 2` | `b'[]'` |

Leitura do coordenador, para a decisão do Gate 2 (não é segunda revisão):

- **MAJOR 1 confirmado.** Depende só de uma resposta chunked cortada no meio de um chunk (queda de conexão). O
  contrato (issue, A2; relatório, §6, linhas 299–300) promete contar os bytes "quando a resposta vem incompleta".
  Nesses casos a contagem fica abaixo do recebido: 0 de 3 e 2 de 5.
- **MAJOR 2 confirmado, com uma condição que o revisor não destacou:** os dois cenários exigem uma resposta com
  `Transfer-Encoding: chunked` **e** `Content-Length` ao mesmo tempo, que é uma resposta fora do protocolo HTTP. A
  frequência disso na instância real **não foi medida** (sem rede nesta tarefa). Com cabeçalhos coerentes, os dois
  controles passam.
- Os testes novos de `tests/test_moodle.py` não geram resposta chunked (resposta 6 do revisor), então os 54/54 verdes
  não cobrem nenhum dos dois achados.
- Consequência para os documentos: a frase do relatório de correções, §6, "Os bytes são contados também quando […] a
  resposta vem incompleta" precisa de ressalva para o caso chunked, e "`None` = comportamento anterior" tem a exceção
  do caso 2a.

## 7. O que fica para decisão

1. **Gate 2 do delta Moodle:** com o veredito NÃO APROVAR, o commit dos dois arquivos como estão não tem revisão
   favorável. Opções e recomendação no dossiê (`2026-09-30-dossie-decisoes-motor.md`, seção B1).
2. **Correção dos dois achados:** exige Gate 1 próprio (toca `src/`), teste vermelho primeiro e, pelo contrato de
   revisão, nova autorização explícita para revisar o delta corrigido (a tentativa desta tarefa está consumida).
3. Nenhuma ação foi tomada sobre o `adquire` v5 nem sobre os documentos de 29/09.

## 8. Adendo de 01/10 — revisão independente do GPT

Fonte: `Codex/2026-10-01/files-mentioned-by-the-user-noite/outputs/Do_Gpt/revisao_noite_30-09.md` e
`reprodutores_noite_30-09.json`. A revisão foi feita sobre o pacote `noite_30-09.zip`, com o mesmo sha256 do delta
acima.

- **Os dois MAJOR foram confirmados** em 29 casos offline. O MAJOR 2 continua MAJOR mesmo exigindo cabeçalhos fora
  do protocolo: o prefixo é aceito em silêncio e a compatibilidade expressa regride.
- **Caso novo M2c:** chunked + Content-Length 999 com limite 3. O delta recusa sem ler, embora o payload de 2 bytes
  coubesse.
- **Armadilha para a correção do MAJOR 1 (C16):** com o wire `2\r\n[]\r`, a causa interna traz `\r`, que é framing e
  não payload. Somar `__cause__.partial` às cegas conta 3 em vez de 2.
- **MINOR condicional M-03 (reentrância):** uma chamada aninhada na mesma instância leva o contador a 4 com limite
  3. Uso concorrente real não foi demonstrado. Encaminhamento: declarar uso sequencial por instância.
- **O MAJOR documental novo (B1-N1)** é sobre o congelamento de `src/` na validação VOCAB (POL:9, 18–19). Está no
  dossiê, em "B1 — Dependências e pré-condições".

O plano de correção está no resumo, §12.1. Um esboço foi pré-verificado em memória: 21/21 casos conforme o contrato,
contra 14/21 do delta atual. Nada foi aplicado ao produto.

## 9. Adendo de 01/10 — 2ª revisão independente do GPT

Fonte: `revisao_plano_01-10.md` e `reprodutores_plano_01-10.json`, com 56 cenários em CPython 3.11.9 e 3.13.12. O
pré-check foi reproduzido (14/21 → 21/21), mas o esboço **não** satisfaz todo o contrato:

- **P-01 (MAJOR):** um `TimeoutError` ou `LineTooLong` depois de payload consumido perde a contagem. São 0 de 2
  bytes no delta e no esboço (A18, A19, A33, A34). O defeito já existe no delta atual.
- **P-02 (MAJOR):** tamanho de chunk `-1` leva a `read(-1)`, com 23 bytes lidos e saldo 2 (A22). O esboço amplia o
  caminho quando ignora o CL que antes barrava a resposta (A35).
- **P-03 (MINOR de contrato):** a stdlib tolera framing incompleto ou não validado (A11–A16, A32). É preciso decidir
  entre tolerância e validação estrita, e o tratamento de Transfer-Encoding não suportado (A23, A24).
- **P-04 (MINOR):** o plano listava C01 como recusa; o certo é sucesso no saldo exato conhecido.
- **P-05 (MINOR):** o pré-check não mede `exc.partial`, a cadeia, as leituras nem as aberturas, e não falha por
  `assert`.

O plano foi revisado no resumo, §12.1 e §12.3, com a direção do usuário (01/10):

- V1 como desenho inicial, sem troca automática para a V2;
- CL ignorado em chunked e Transfer-Encoding não suportado recusado antes do corpo;
- matriz Python definida antes de implementar;
- worktree isolada;
- comportamentos a demonstrar, separados entre os que reproduzem defeito e os controles já verdes.

Nada foi implementado.

## 10. Adendo de 01/10 — 3ª revisão independente do GPT

Fonte: `revisao_direcao_01-10.md`. Resultado: nenhum CRITICAL nem MAJOR novo; cinco MINOR (D-01 a D-05). A V1 é
plausível, mas não está validada, e os defeitos acima continuam.

- **Registros históricos:** 169/169 flags conferem; nada foi reescrito.
- **Correção de números (D-02):**
  - A21: sem limite, `read(-1)` consumiu 3 bytes;
  - A22: com saldo 2, consumiu 23 bytes, 21 além do saldo;
  - A35: no delta, zero consumo, mas por recusa indevida baseada no CL. Os 23 bytes do A35 são do esboço anterior.
- **Oráculo do A35 (D-01):** CL ignorado e tamanho negativo recusado antes do payload. O caminho é provado pela
  instrumentação, não só pelo contador zero.
- **Demais ajustes:** suíte baseline antes de mudar o produto (D-03); D-RUNTIME com arquivos condicionais (D-04);
  asserções conforme o contrato de cada exceção (D-05).

Plano: resumo, §12.1 e §12.3. Nada foi implementado.
