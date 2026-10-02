# Plano de execução noturna — correção do `MoodleClient` (V1)

**Estado: proposta, aguardando as respostas do §1 e o Gate 1.** Versão 2 (01/10/2026), com a revisão final do GPT
(`NÃO PRONTO` por um único bloqueio, F-01, mais quatro ajustes não bloqueantes, F-02 a F-05). Todos foram
incorporados; segundo a própria revisão, o F-01 resolve o bloqueio sem outra rodada documental. Base técnica: o
`2026-09-30-noite-resumo.md`, §12.1 (requisitos R1–R6, comportamentos e aceite) e §12.3 (decisões). Este documento não
concede Gate nenhum.

**Objetivo da noite.** Chegar de manhã com a V1 implementada numa worktree isolada, testada e comparada com o delta
atual.

**Fora da noite:**

- commit e merge;
- revisão independente sem autorização;
- qualquer mudança de conteúdo na árvore principal.

O Gate 2 é de manhã, sobre o conjunto.

## 1. Para lançar: responda estes itens

| # | decisão | opções | recomendação |
|---|---|---|---|
| 1 | **Matriz Python (D-RUNTIME)** | **A)** pytest completo em 3.11.9 (`.venv`); harness stdlib dos comportamentos R1–R6 em 3.13.12 e 3.14.3; suporte declarado **restringido para `>=3.11`** (`pyproject.toml:6`). O CI (`validate-timeline.yml:36`) já usa 3.11 e só é registrado como conferido. A exclui 3.8–3.10, mas **continua abrangendo 3.12**, que não foi testada. **B)** a mesma matriz, mantendo `>=3.8`, com 3.8, 3.9, 3.10 e 3.12 declarados como não validados. **C)** instalar runtimes e pytest: exige rede, fora da noite | **A.** A V1 depende de membros privados do `http.client`, verificáveis só nas versões testadas, e o projeto roda em 3.11. Restringir é decisão sua, expressa; nenhuma das opções valida todas as versões do intervalo declarado |
| 2 | **Contrato R5** (Transfer-Encoding) | confirmar a proposta: comparação como a stdlib (`lower() == "chunked"`); listas, outros codings e cabeçalhos repetidos recusados antes do corpo; exceção `http.client.UnknownTransferEncoding`. Ou ajustar | confirmar |
| 3 | **Árvore principal durante a pendência** | **a)** não usar sincronização nem aquisição Moodle pela árvore principal até o Gate 2; **b)** uso livre | **a** |
| 4 | **Gate 1** | autorizar o escopo do §2 | — |
| 5 | **Revisão independente nesta noite** (opcional) | **sim:** uma tentativa, papel `reviewer` do Alethe, no fim, sobre o conjunto real (§3, S10), com `escaladas_automaticas` 3 → 4. **Não:** a noite para antes, e a revisão fica pendente | sim |

**Texto para autorizar** (copie, preencha os colchetes e mande):

> Autorizo o Gate 1 da correção Moodle V1 conforme `2026-09-30-plano-noite-correcao-moodle.md` (versão 2), §2–§5.
> D-RUNTIME: [A/B]. R5: confirmado. Árvore principal: [a/b]. Revisão independente nesta noite: [sim/não] (se sim, uma
> única tentativa, papel `reviewer`, sem retry). Exceções admitidas: o arquivo de estado da tarefa é a única escrita
> de conteúdo na árvore principal; os metadados de git da worktree e da branch local são consequência da operação
> autorizada. Sem commit, merge, push, rede de aquisição, instalação de pacotes, LLM do motor, motor, gold ou alteração
> de conteúdo da árvore principal. Gate 2 de manhã.

## 2. Escopo autorizado pelo Gate 1

- **Worktree isolada:** `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-moodle-v1`, criada com `git worktree
  add` a partir de `bf46d51f`, em branch local nova `fix/moodle-rmeta-v1`. Nada vai para `origin`. A criação escreve
  metadados administrativos no `.git` compartilhado; nada além disso fora da worktree.
- **Arquivos editáveis na worktree:**
  - `src/builder/sources/moodle.py` e `tests/test_moodle.py`: o delta atual copiado byte a byte e conferido por
    sha256 (`244301234d67…`, `99951fdbdc2a…`), depois a V1;
  - `pyproject.toml`, só se a D-RUNTIME for A (uma linha);
  - artefatos da noite em `docs/reports/2026-10-01-correcao-moodle-v1/`: relatório, harness stdlib, runner do S7,
    cópia imutável do delta inicial e resultados. Não versionados até o Gate 2.
- **Leitura sem escrita na árvore principal:**
  - os testes de `docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa3_correcoes_v5_29-09/correcoes/aquisicao/`
    são executados **no lugar** pelo runner do S7, porque o `adquire.py:56` exige `.git` como **diretório** e o
    `adquire.py:57` lê a etapa 2 por caminho relativo. Numa worktree, `.git` é arquivo, e uma cópia não funcionaria;
  - o resto da principal: os 3 arquivos modificados, os 6 commits locais, os 4 stashes, `.codex/hooks.json`, REL e
    ISS, o tracker, a fonte do workflow e o gold.
- **Única escrita de conteúdo na principal:** o arquivo de estado da tarefa (`.workflow/local/active-task.md`).
- **Interpretadores, por caminho absoluto e só para leitura:**
  - `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/.venv/Scripts/python.exe` (3.11.9, com pytest), com o cwd
    na worktree. O `pyproject` tem `pythonpath = ["."]`, então o `src` importado é o da worktree;
  - 3.13.12: `C:/Users/Humberto/AppData/Roaming/uv/python/cpython-3.13.12-windows-x86_64-none/python.exe`;
  - 3.14.3: `C:/Users/Humberto/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

  Nenhum ambiente é criado ou copiado, e nenhum pacote é instalado.
- **Execução:** sempre com `-B` / `PYTHONDONTWRITEBYTECODE=1` e `-p no:cacheprovider`. Diretórios temporários dentro
  da pasta de artefatos (`--basetemp`). Transportes sintéticos, sem rede.
- **REL/ISS:** a noite escreve só o **texto proposto**, com identificação de versão. A aplicação pede autorização
  própria, de manhã.

## 3. Sequência

Cada passo registra comando, cwd, executável, código de saída e resultado no relatório, e atualiza o arquivo de
estado.

| passo | ação | registro | para se |
|---|---|---|---|
| S0 | conferir HEAD `bf46d51f`, os hashes do delta, `git status` da principal, `alethe_status` sem Job em andamento e quota | estado inicial | qualquer divergência |
| S1 | criar a worktree e a branch; copiar os dois arquivos do delta; conferir sha256; guardar uma **cópia imutável do delta inicial** na pasta de artefatos | hashes | hash diferente |
| S2 | registrar ambiente: caminhos e versões exatas dos três interpretadores, versão do pytest, SO | tabela de ambiente | interpretador ausente |
| S3 | **suíte original**, antes de mudar teste ou produto: `<.venv> -B -m pytest tests -q -p no:cacheprovider -rfEs --basetemp=<artefatos>/tmp_s3` no cwd da worktree | coleta, aprovados, falhas e pulos, com IDs | não roda |
| S4 | escrever os testes de comportamento em `tests/test_moodle.py` (stream instrumentado por fase; helper chunked), sem mudar o produto. Rodar `tests/test_moodle.py` e a suíte em 3.11.9. Escrever o **harness stdlib** (requisitos abaixo) e rodá-lo **contra a cópia imutável do delta** em 3.11.9, 3.13.12 e 3.14.3 | estado real de cada teste e de cada caso do harness contra o delta (defeito reproduzido, controle verde, regra nova); mudança de coleta causada pelos testes novos | controle que deveria estar verde falha sem explicação; o harness não carrega a classe real |
| S5 | implementar a V1 em `_le_resposta`/`_call`: `read1` com contagem por fragmento; pré-validação do tamanho do chunk (pendente, transição, fim, negativo); CL ignorado em chunked; R5 antes do corpo | diff | — |
| S6 | depois da correção: `tests/test_moodle.py` e suíte completa em 3.11.9; harness stdlib contra o candidato em 3.11.9, 3.13.12 e 3.14.3; comparar com S3 e S4 | antes/depois por comportamento e por runtime | **comportamento não alcançado; regressão nova; ou diferença de suíte não identificada e avaliada.** Explicar não autoriza aceitar uma regressão. Distinguir falha preexistente, coleta nova e regressão |
| S7 | **consumidores (F-01):** (a) ler `src/ui/dialogs.py:1719–1723`, que captura `Exception`; (b) rodar o runner do S7 (abaixo) sobre os testes de `correcoes/aquisicao/`, em 3.11.9, offline, em processo próprio | sha256 de `adquire.py`, `test_adquire_v3.py`, `test_adquire_v4.py` e `test_adquire_v5.py` antes e depois; identidade do `MoodleClient` usado; resultado dos testes | **identidade divergente ou indeterminável** (exit ≠ 0, sem fallback); arquivo da principal alterado; regressão; o harness exigir mudar fonte congelado ou escrever fora do escopo |
| S8 | se a D-RUNTIME for A: `pyproject.toml:6` → `>=3.11`; rodar a coleta de novo; registrar o CI como conferido e sem alteração | diff | — |
| S9 | escrever no relatório o texto proposto para REL §6 e ISS A2/A6 (contrato R1–R6, tolerâncias da V1, R5, uso sequencial), identificando a versão | texto | — |
| S10 | **só se autorizado (§1, item 5):** uma revisão `reviewer` sobre o **conjunto real**: diff da worktree, arquivos novos não rastreados (inclusive o harness e o runner), resultados de S3–S8 e texto proposto de REL/ISS. Brief autocontido | `jobId`, `runId`, modelo, achados, versões examinadas | falha ou timeout consomem a tentativa, sem retry; registrar "revisão independente pendente" |
| S11 | hashes finais (candidato, testes, harness, runner, resultados) e relatório final; estado `aguardando_gate2`. Parar | — | — |

**Requisitos do harness stdlib (F-02):**

- **Identidade:** executável e versão exata; caminho resolvido e sha256 do `moodle.py` efetivamente carregado (cópia
  imutável do delta em S4, candidato em S6); hash do próprio harness. Usa a classe real e o `HTTPResponse` da stdlib
  daquele runtime, sem reimplementar a V1. Stubs, se houver, só para dependências ausentes, declarados e sem
  substituir o cliente nem o transporte.
- **Oráculos:** por comportamento, a entrada, o esperado e o obtido: tipo ou retorno, contador, corpo,
  `partial`/causa quando contratados, pedidos e retornos por fase e número de aberturas. Cobre os comportamentos e as
  tolerâncias do §12.1, inclusive os casos novos, sem omissão silenciosa.
- **Resultado processável:** divergência inesperada, caso não executado ou falha do harness dá exit ≠ 0. Asserções
  ativas, sem `-O`. No baseline do delta, os defeitos esperados são registrados como tais; no candidato, o contrato
  tem de passar.
- **Isolamento:** transportes sintéticos, rede real vedada, saídas só na pasta de artefatos.
- **No relatório, três coisas separadas:** a compatibilidade declarada, a suíte completa executada (só 3.11.9) e os
  runtimes com o harness de R1–R6 (3.11.9, 3.13.12 e 3.14.3).

**Runner do S7 (F-01)**, um processo, nenhuma cópia dos fontes v5:

1. pôr a raiz da worktree em `sys.path[0]` e importar `src.builder.sources.moodle`. Conferir que o `__file__` é o
   `moodle.py` da worktree e que o sha256 é o do candidato;
2. carregar o `adquire.py` da v5 do seu caminho original. Ele insere a raiz da principal no `sys.path`, mas
   `src.builder.sources.moodle` já está em `sys.modules`, então reaproveita o módulo da worktree;
3. **conferir no próprio processo** que `adquire.M` é o mesmo objeto de módulo, que `adquire.M.MoodleClient` vem do
   arquivo da worktree e que o sha256 confere;
4. rodar `pytest.main` nos testes de `correcoes/aquisicao/`, com o mesmo módulo em `sys.modules`, `-p
   no:cacheprovider`, `--basetemp` na pasta de artefatos e `PYTHONDONTWRITEBYTECODE=1`;
5. repetir a conferência de identidade ao final;
6. sair com código ≠ 0 se a identidade divergir ou não puder ser determinada, ou se algum teste falhar.

Os sha256 dos fontes v5 e o `git status` da principal são comparados antes e depois, para provar que nada mudou ali.

**Condições de parada gerais.** Em qualquer uma: registrar e parar a frente, sem contornar.

- a V1 não alcança um comportamento do §12.1: registrar caso, causa e runtime, e **não trocar para a V2**;
- qualquer passo exigiria rede de aquisição, instalar pacote, LLM do motor, escrever conteúdo na principal ou editar
  REL/ISS;
- quota esgotada: salvar o estado e parar.

## 4. Proibido nesta noite

- Commit (inclusive na branch local nova), merge, push ou PR.
- Rede de aquisição, instalação de pacote, LLM do motor, motor, gold, P3/P3.1, elegibilidade e aquisição real. A
  única chamada a modelo admitida é a revisão do S10, se o item 5 for "sim".
- Escrever conteúdo na árvore principal (exceto o arquivo de estado), editar REL/ISS, o tracker ou a fonte do
  workflow.
- Trocar para a V2, atualizar o baseline VOCAB ou o hash esperado.
- Lançar workers além da revisão do S10.

## 5. O que estará pronto de manhã

1. a worktree `GPT-Tutor-Generator-moodle-v1` com a V1 e os testes, sem commit;
2. a pasta `docs/reports/2026-10-01-correcao-moodle-v1/` da worktree, com:
   - os hashes de partida e finais;
   - o ambiente;
   - comandos, cwd, executáveis e códigos de saída;
   - a suíte em três estados (original, com os testes novos, depois da correção);
   - o estado antes e depois **por comportamento**: defeitos reproduzidos e corrigidos, controles que seguiram verdes
     e R5 como regra nova, sem placar numérico;
   - o harness nos três runtimes;
   - os consumidores e a identidade provada no S7;
   - o texto proposto de REL/ISS;
   - o parecer da revisão, se autorizada; senão, "revisão independente pendente";
3. a lista do Gate 2. Ela **não** torna o conjunto aprovável automaticamente, e inclui:
   - aplicar REL/ISS com autorização própria, reconciliando com a versão que a revisão examinou;
   - revisão pendente, se não houve ou falhou;
   - aceitar o diff (dois arquivos e, se A, o `pyproject.toml`);
   - conferir e atualizar o grafo;
   - integração e merge, com autorização própria;
   - o que continua aberto: baseline de `src/`, tracker, sync do workflow e metodologia.

## 6. Quem executa

- **O coordenador** (Claude Code), direto na worktree: a implementação fica no agente ativo, como manda o workflow.
- **Workers:** só a revisão do S10, se autorizada.
- **Tempo:** não estimado; as condições de parada valem a qualquer momento.
