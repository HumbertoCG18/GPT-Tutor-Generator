# Handoff: sessão de 30/09 a 02/10 (Moodle V1, CRU-05/CRU-03, Fase 0 e P1 do pontuador)

**Sessão:** Claude Code `ee4dd19b-7491-4289-baf7-43a7b14dfb38`.
**Escrito em:** 02/10/2026, ~02:50.
**Commits desta sessão:** nenhum. Tudo está em worktrees, sem commit, ou em arquivos não versionados.
**Estado vivo:** `.workflow/local/active-task.md` (tarefa `motor-20261001-cru05-cru03`, com a tarefa do Moodle citada
abaixo dela). O registro de campanhas `.workflow/campanhas.json`, criado por outra sessão (`812d19cf`), já mapeia este
trabalho em MOODLE-V1-01..04 e MOTOR-00..09.

## 1. Retomada em 5 passos

1. Ler este handoff e o `active-task.md`. Não refazer medições: todas estão seladas por hash e listadas no §6.
2. Conferir as árvores:
   - a principal está na branch **`dev`** (HEAD `812d19cf`) e mantém sem commit o delta antigo do Moodle
     (`src/builder/sources/moodle.py`, `tests/test_moodle.py`), além do `pendencias.md` editado;
   - as 4 worktrees desta sessão partem de `bf46d51f` (§2).
3. **P1 (MOTOR-01):** o próximo Gate é a **avaliação congelada dos quatro braços** (§3.4). Nada a fazer antes dela.
4. **Moodle (MOODLE-V1-01):** espera o Gate 2. A opção 1 (ajustes dos achados 1 e 2 + revisão Astra da diferença) foi
   autorizada e **pausada** pelo usuário.
5. Decisões antigas ainda abertas: §5.

## 2. Árvores e worktrees

| local | branch / HEAD | conteúdo desta sessão | estado |
|---|---|---|---|
| `GPT-Tutor-Generator` (principal) | `dev` @ `812d19cf` (outra sessão) | `.workflow/local/active-task.md`; `docs/reports/pendencias.md` (bloco CRU + entrada "Medido … (01/10)"); este handoff | sem commit |
| `GPT-Tutor-Generator-moodle-v1` | `fix/moodle-rmeta-v1` @ `bf46d51f` | V1 do `MoodleClient` + `pyproject.toml` (≥ 3.11); `docs/reports/2026-10-01-correcao-moodle-v1/` | aguardando Gate 2 |
| `GPT-Tutor-Generator-cru05` | `fix/cru05-acentos-espacadores` @ `bf46d51f` | correção dos acentos (#89, **reprovada**); `docs/reports/2026-10-01-cru05-cru03/` (diagnósticos, Fase 0, contratos do P1, `replay_base.json`) | não integrar |
| `GPT-Tutor-Generator-p1` | `feat/cru-p1-frases-compartilhadas` @ `bf46d51f` | P1 (#90), desligado por padrão; `docs/reports/2026-10-02-p1-implementacao/` | pronto para o Gate da avaliação |
| `GPT-Tutor-Generator-noite-20260930` | detached @ `bf46d51f` | resumo, dossiê, revisão do delta e plano da noite de 30/09; `.workflow/` sincronizado com `f07d786` | src/tests intocados; serve de "base sem acentos" |

## 3. O que foi feito, por frente

### 3.1 Moodle V1 (MOODLE-V1-01), noite de 01/10

- **Plano v2 executado por inteiro, S0 a S11** (`noite-20260930/docs/reports/2026-09-30-plano-noite-correcao-moodle.md`).
  - V1 em `_le_resposta`: `read1` contando cada fragmento, pré-validação do chunk, CL ignorado em chunked, R5 antes
    do corpo.
  - Harness stdlib 64/64 em 3.11.9, 3.13.12 e 3.14.3, idêntico caso a caso.
  - Suíte sem regressão nova.
  - `adquire` v5: 40 verdes, rodados no lugar, com a identidade do `MoodleClient` provada.
- **Revisão `validador-externo`** (`job-29`): **APROVÁVEL COM AJUSTES**, com 5 MINOR. Os de texto foram corrigidos; os
  achados 1 (oráculo do saldo exato C03/A31) e 2 (runner aceita saída na principal) ficaram para o Gate 2.
- **Opção 1** (ajustar os achados 1 e 2 + revisão Astra só da diferença): autorizada e depois **pausada**. Só foram
  congeladas as versões revisadas, em `registros/revisada_s10/`.
- **Relatório:** `moodle-v1/docs/reports/2026-10-01-correcao-moodle-v1/relatorio.md`. A lista do Gate 2 está no §12.
- O registro (MOODLE-V1-02) já lista a reconciliação da cópia antiga do delta na principal.

### 3.2 Vídeos do Moodle de CG (pedido avulso, concluído)

- `Desktop/cg_videos_moodle.md`: Moodle ao vivo, curso 95106 (2026/2), 01/10. São 277 itens e 273 links únicos. Os
  vídeos de Instanciamento e da Resolução da Prova A são novos em relação à cópia de 04/09.
- O token foi lido de `moddle/.env` sem ser impresso.

### 3.3 Motor: CRU-05 e CRU-03 (MOTOR-02 e MOTOR-03, concluídas)

- **CRU-05 (#89), acentos espaçadores** em `normalize_match_text`.
  - A correção está certa como texto, mas **foi reprovada no replay integral**: subunidade primária 86 → 85, com 1
    perda (TCC aula-10).
  - Revisão GPT Pro (`Desktop/para-gpt/Do_Gpt/revisao_cru05_01-10.md`): opção 2.
  - Diagnóstico instrumentado (par com fidelidade integral, sem gold):
    - foi refutada **só** a hipótese específica de propagação de "reconhecíveis/decidíveis";
    - a 1ª divergência dos 6 materiais está no texto do próprio material;
    - a participação das passadas não foi quantificada;
    - o acerto da aula-10 dependia do texto fragmentado.
- **CRU-03, sinal de seção nos blocos de afinidade zero.** Pré-registro selado; resultado 0/80 para o detector
  `section_slug` (125 candidatos e 50 de afinidade zero, como no W-Z2). Encerrada. Isso não prova ausência de toda
  informação nas seções; os aliases EN/PT não foram medidos.
- **Referência de medição vigente:** `cru05/.../replay_base.json` (sha256 `e024d396…`), 223/237 · 249/284 · 86/251,
  com o `src` de `bf46d51f` sem acentos.
  - A captura W-Z2 `f941ac33` fica histórica: difere em 1 material do CG (unidade e subunidade).
  - **MOTOR-00 (pronta):** versionar essa referência, que hoje só existe na worktree `cru05`.
- **Tracker** (`pendencias.md`, autorizado): bloco CRU com a referência, CRU-02(b) documental, CRU-03 encerrada,
  CRU-05 com o resultado, e a entrada "Medido: CRU-05 … (01/10)" logo depois de `fila-campanhas-end`. As 37 linhas
  alheias do bloco VOCAB de 29/09 foram preservadas.

### 3.4 Proposta do pontuador → Fase 0 → P1 (MOTOR-01, em execução)

- **Proposta:** `cru05/.../proposta-pontuador-termos-pouco-discriminantes.md`. Investiga termos pouco
  discriminantes, separando a frequência entre tópicos (F_top) da frequência entre materiais (F_mat).
- **Fase 0:** medição descritiva em MF, SO, IA, ES2 e TCC, sem gold. Pré-registro `68ff436f…`; fidelidade integral
  (1536/1536 pares, 231/231 capturas).
  - **Leitura fixada:** "sensibilidade demonstrada; benefício ainda desconhecido". O "ganha força" fica como saída
    histórica do critério, com ressalvas.
  - **Números corretos:** entre os 158 materiais com vencedor, o vencedor muda em 57/158 = 36,1 %, dos quais 47
    esvaziamentos e **10 trocas de tópico (6,3 %)**. As frases compartilhadas só pesam no SO e no TCC.
  - R_top **não** é P1. O **P2 está suspenso**, sem redesenho.
  - Relatório: `cru05/.../relatorio-fase0-pontuador.md`.
- **Contrato do P1:** `cru05/.../fase1-p1-desenho-congelado-v2.md` (sha256 `d30980a3…`; a v1 `b10b3361…` segue
  somente leitura).
  - **Regra:** acerto de frase = peso × fator / F_top, com F_top contado sobre os concorrentes da chamada. A divisão é
    só no acerto; uma palavra única com menos de 4 caracteres fica com F_top = 0 e nunca acerta.
  - **Escopo:** só a componente de frases do seletor da subunidade, nas duas passadas.
  - **Exemplos:** E1–E7 e E4b, conferidos com o pontuador real.
  - **§5** fixa a avaliação.
- **Implementação #90** (worktree `p1`): `index.py` com `_frases_do_topico` extraída, `_divisores_de_frase` e o
  parâmetro `divisores_frase`; `file_map.auto_map_entry_subtopic` com o parâmetro `divisores_de_frase=None`.
  - **Nenhum chamador de produção liga o P1.**
  - Diff de 2 arquivos, +48/−22, mais `tests/test_p1_frases_compartilhadas.py` (não rastreado).
  - Testes: vermelho → **14/14** verdes. A mutação "contar chaves" é detectada.
  - Suíte: **2461 aprovados** (2447 da base + 14) e as mesmas 2 falhas da base.
  - **Replay com P1 desligado × `e024d396`: 350/350 idênticos**, sem gold.
  - Revisão `reviewer` (`job-30`): **SEM BLOQUEADOR**. Os 2 MINOR de cobertura foram fechados no reforço dos testes.
  - Relatório: `p1/docs/reports/2026-10-02-p1-implementacao/relatorio-p1-implementacao.md`.
- **Próximo Gate (do usuário): avaliação congelada, uma tentativa, pelo §5 do contrato v2.**
  - **Braços:**
    - base (`e024d396`);
    - A (src da `cru05`);
    - P1 (src da `p1` com o P1 ligado);
    - A+P1 (exige uma árvore com os dois diffs).
  - **Garantia de escopo:** bloco e unidade idênticos por ID ao braço sem P1 correspondente.
  - **Aceite de integração:** ganho positivo na subunidade primária, zero perda por ID em cada eixo, nenhum curso
    regride, suíte limpa.
  - **Relato separado:**
    - desenvolvimento (MF, SO, IA, ES2, TCC);
    - CG/FR, descritivo, com exposição declarada;
    - cursos novos, que hoje não existem. Passar nos 7 não demonstra generalização.
  - **Detalhe técnico para o runner:** o replay usa `ru.auto_sub` (`replay_unidade_21-09.py`). Para ligar o P1 nas duas
    passadas, basta trocar `ru.auto_sub` por um `partial` com `divisores_de_frase=_divisores_de_frase`. O resolver
    resolve `auto_sub` em tempo de chamada, como confirmou o `job-30`.
  - Ressalva do contrato: o P1 **não** deve recuperar a aula-10.

## 4. Decisões do usuário nesta sessão (resumo)

- **VOCAB = 1a com ajuste.** O teste independente usa só cursos novos elegíveis; as 8 N0 baixadas são candidatas.
  CG/FR entram só como avaliação adicional e descritiva. **Desenvolvimento** = MF, SO, IA, ES2 e TCC (semestre
  passado); CG e FR são deste semestre, mas já influenciaram o desenvolvimento.
- **CRU-02(b)** como posição documental: limites observados dos mecanismos examinados, sem impossibilidade universal.
- O P1 só avança com Gate a cada fase. Nenhuma revisão LLM nova sem pedido.

## 5. Abertas, fora das frentes acima

- **Da noite de 30/09** (`noite-20260930/docs/reports/2026-09-30-noite-resumo.md`, §7 e §8):
  - commit da sincronização de `.workflow/` (8 arquivos, fonte `f07d786`);
  - D1–D9, R-VIS e R-CC do dossiê (`2026-09-30-dossie-decisoes-motor.md`).
- **Inconsistência no registro de campanhas:** a MOTOR-07 diz "#49: Gate 2 (217/237, sem commit registrado)", mas a
  #49 **está commitada**: `410592d8`, de 22/09, contida em `dev`, `feat/motor-atribuicao` e nas 3 branches desta
  sessão.
- **Falhas preexistentes da suíte**, iguais em todas as execuções:
  - `test_caracterizacao_blocos_atual[Fundamentos-de-Redes-Tutor]` (baseline golden);
  - `test_pdf_markdown::test_respect_actualtext_tira_a_flag_e_restaura` (premissa do pymupdf).

## 6. Índice de evidências (hash, sha256 inicial)

| artefato | hash |
|---|---|
| `replay_base.json` (referência vigente) | `e024d396` |
| `replay_candidato.json` (#89) | — (ver `relatorio-cru05.md`) |
| pré-registro do CRU-03 / Fase 0 | `36eed38b` / `68ff436f` |
| contrato P1 v1 / v2 | `b10b3361` / `d30980a3` |
| P1: `index.py` / `file_map.py` / teste | `28894d0a` / `6ad4f70b` / `90746e83` |
| `replay_identidade.py` (runner do replay sem gold) | `5c223221` |
| Moodle V1: `moodle.py` / `test_moodle.py` / `pyproject.toml` | `be9788c3` / `c148166f` / `30c85876` |
| revisão GPT Pro do CRU-05 (cópia nos artefatos) | `16c92d06` |

## 7. Lições operacionais

- **Git Bash no Windows:**
  - heredocs com aspas ou barras quebram; o melhor é escrever scripts num arquivo do scratchpad e rodar de lá;
  - `PYTHONIOENCODING=utf-8` evita `UnicodeEncodeError` no console;
  - os arquivos do repositório são CRLF: preservar ao editar.
- **git-lock:** uma trava ativa bloqueia **o comando inteiro** em que aparece um git de escrita, inclusive o que vem
  antes no mesmo comando.
- **Replays:**
  - ~140–200 s cada; com instrumentação pesada (`pontuar=True`), ~1160 s;
  - os módulos de replay ficam na principal (`c1-3/`, não versionados) e fixam `src.__path__` na worktree;
  - conferir sempre `src_fora_da_worktree`.
- **Pré-registro:** definir "mudança de argmax" separando troca de tópico de esvaziamento. Contar "vazio" como mudança
  inflou o critério da Fase 0.
- **Alethe:** `alethe_check` com `timeoutMs` em torno de 55000; esperas mais longas, em background. Papéis de revisão
  exigem `status: delegando` e `escaladas_automaticas` ≥ 1 no estado (hook `delegate-gate`).
