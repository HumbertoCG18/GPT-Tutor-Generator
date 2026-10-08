# Aquisição Moodle — histórico consolidado

Síntese criada em 2026-10-08 na limpeza de Markdown. Não é estado vivo nem norma nova; as três fontes continuam
intactas no lugar. O estado vivo está no [handoff de 02/10](2026-10-02-handoff-motor-p1-moodle-claude.md), na worktree
`GPT-Tutor-Generator-moodle-v1` (branch `fix/moodle-rmeta-v1`, relatório fora da `dev`, com WIP) e em
`.workflow/campanhas.json` (campanha `MOODLE-V1`, linhas 14–65).

## Linha do tempo

| Data | Documento | Papel | O que estabeleceu | Superado por |
|---|---|---|---|---|
| 2026-09-30 | [revisão do delta R-META/R-PAGE](2026-09-30-revisao-delta-rmeta-rpage.md) | Revisão independente do delta (`reviewer`, `job-16`) mais três adendos de 01/10 (GPT) | Veredito NÃO APROVAR o commit dos 2 arquivos: 0 CRITICAL, 2 MAJOR (`revisao:3`). Adendos: casos novos M2c, P-01, P-02 e ajustes D-01 a D-05 (`revisao:177-227`) | Plano de 01/10 (abaixo); a conclusão da V1 está na worktree `moodle-v1`. Não é aceite da V1 |
| 2026-10-01 | [plano de execução noturna](2026-09-30-plano-noite-correcao-moodle.md) | Proposta v2 de correção V1 em worktree isolada | Escopo, S0–S11, matriz Python e proibições. Declara-se proposta e não concede Gate (`plano:3-7`) | Execução relatada no handoff (`handoff:36-41`); o relatório da V1 está na worktree `moodle-v1` |
| 2026-10-02 | [handoff motor/P1/Moodle](2026-10-02-handoff-motor-p1-moodle-claude.md) | Handoff de campanha, **vivo** | Resume a execução da V1 e aponta o Gate 2 pendente (`handoff:27,44-46`) | Nada; é a fonte de continuação |

## Resultados e achados

Cada resultado vale só na sua régua. Não somar entre linhas.

| Data | Base | Denominador | Valor | Fonte |
|---|---|---|---|---|
| 2026-09-30 | Delta `bf46d51f`, `_call`, CPython 3.11.9, revisor e coordenador | chunk truncado `5\r\nabc`, 3 bytes recebidos | 0 contados (`bytes_recebidos = 0`) | `revisao:49,139,134` |
| 2026-09-30 | idem | chunk completo de 2 + truncado, 5 bytes recebidos | 2 contados | `revisao:50,140` |
| 2026-09-30 | idem | chunked `[]` com Content-Length 999, sem limite | `IncompleteRead(2 bytes read, 997 more expected)`; a leitura anterior devolvia `b'[]'` | `revisao:61-62,141` |
| 2026-09-30 | Testes novos do delta | 54 testes | 54 verdes, nenhum gera resposta chunked | `revisao:155-156` |
| 2026-10-01 | 1ª revisão GPT, pacote com o mesmo sha256 do delta | 29 casos offline | 2 MAJOR confirmados | `revisao:171-176` |
| 2026-10-01 | Esboço pré-verificado em memória, §12.1 do resumo | 21 casos | 21/21 conformes; delta 14/21 | `revisao:186-187` |
| 2026-10-01 | 2ª revisão GPT, CPython 3.11.9 e 3.13.12 | 56 cenários | esboço não satisfaz o contrato: P-01 (0 de 2 bytes, A18/A19/A33/A34) e P-02 (23 lidos, saldo 2, A22) | `revisao:191-197` |
| 2026-10-01 | 3ª revisão GPT, registros históricos | 169 flags | 169/169 conferem; 5 MINOR | `revisao:216-219` |
| 2026-10-01 (noite) | V1 em `moodle-v1`, harness stdlib em 3.11.9, 3.13.12 e 3.14.3 | 64 casos | 64/64, idêntico caso a caso | `handoff:39` |
| 2026-10-01 (noite) | `adquire` v5, no lugar, 3.11.9 | testes de `correcoes/aquisicao/` | 40 verdes, identidade do `MoodleClient` provada | `handoff:40-41` |

Contexto sem número comparável:

- Revisão `validador-externo` (`job-29`) da V1: APROVÁVEL COM AJUSTES, 5 MINOR; os achados 1 (oráculo C03/A31) e 2
  (runner aceita saída na principal) ficaram para o Gate 2 (`handoff:42-44`).
- Suíte da V1 "sem regressão nova" (`handoff:40`). A fonte não traz contagem. O plano exigia reportar a suíte só em
  3.11.9 e separada do harness (`plano:102-103`).
- Frequência real de resposta com `chunked` e `Content-Length` juntos: não medida (`revisao:152-154`).
- Reentrância concorrente: não validada (`revisao:84,113`). Encaminhamento do GPT: declarar uso sequencial (`revisao:181-182`).
- `moodle.py` mais antigo (`244301234d67…`) e V1 (`be9788c3`) são hashes de versões distintas (`revisao:21`, `handoff:153`).

Divergências entre fontes:

1. Papel da revisão da V1: o plano previa `reviewer` (`plano:86`); o handoff registra `validador-externo` (`handoff:42`).
2. Estado da V1: o handoff diz "aguardando Gate 2" (`handoff:27`) e "pausada" (`handoff:44`); `campanhas.json` marca
   `MOODLE-V1-01` como "em execução" (`campanhas.json:31`), com `atualizado_em` 2026-10-03 (`campanhas.json:25`).
3. O plano se declara "proposta, aguardando Gate 1" (`plano:3`); o handoff diz que foi "executado por inteiro"
   (`handoff:36`). O plano foi superado pela execução, não corrigido.
4. A revisão registra `escaladas_automaticas = 3` (`revisao:39`); o plano previa 3 → 4 se houvesse S10 (`plano:28`).
   Não é conflito, mas o valor depende do momento.

## O que não está decidido aqui

- A V1 é avaliada na worktree própria `GPT-Tutor-Generator-moodle-v1`; esta síntese não a aceita nem a rejeita.
- A revisão de 30/09 não é aceite da V1: o veredito dela vale para o delta antigo (`revisao:3,163-164`).
- Gate 2 (commit e PR para `dev`): `MOODLE-V1-04` está bloqueada (`campanhas.json:55-62`).
- Reconciliar a cópia antiga do delta na pasta principal: `MOODLE-V1-02` pronta (`campanhas.json:36-39`).
- Validação externa do pacote e do `adquire` v3: `MOODLE-V1-03` proposta (`campanhas.json:45-48`).
- Tolerância contra validação estrita do framing e Transfer-Encoding: P-03 (`revisao:198-199`). O plano fixou a direção
  (`revisao:204-210`); o resultado final não é verificado aqui.

## Onde continuar

1. Ler o [handoff de 02/10](2026-10-02-handoff-motor-p1-moodle-claude.md), §1 e §3.1.
2. Ler `docs/reports/2026-10-01-correcao-moodle-v1/relatorio.md` na worktree
   `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-moodle-v1` (lista do Gate 2 no §12, segundo `handoff:46`).
3. Conferir o estado atual em `.workflow/campanhas.json`, campanha `MOODLE-V1`.
