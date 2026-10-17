# Correção V1 do `MoodleClient` — noite de 01/10/2026

**Estado: aguardando Gate 2. Sem commit.** Execução do plano noturno v2
(`GPT-Tutor-Generator-noite-20260930/docs/reports/2026-09-30-plano-noite-correcao-moodle.md`, §2–§5), com Gate 1 do
usuário em 01/10 (~03:15): D-RUNTIME A, R5 confirmado, árvore principal "a" e revisão independente por
`validador-externo`, em uma tentativa. Base técnica: `2026-09-30-noite-resumo.md` §12.1.

## 0. Resultado

1. **Comportamentos.** A V1 alcança todos os comportamentos do §12.1 nos três runtimes do harness (3.11.9, 3.13.12 e
   3.14.3), com o mesmo resultado caso a caso:
   - os 20 defeitos reproduzidos no delta estão corrigidos;
   - os controles seguem verdes;
   - R5 foi implementada como regra nova;
   - as tolerâncias de framing estão declaradas.
2. **Suíte completa (3.11.9).** Nenhuma regressão. As 2 falhas são as mesmas do baseline original e não têm relação
   com o Moodle.
3. **Aquisição v5** (consumidor), executada no lugar contra o candidato: 40 testes aprovados, com a identidade do
   `MoodleClient` provada três vezes e a árvore principal inalterada.
4. **`pyproject.toml`:** `requires-python` passou de `>=3.8` para `>=3.11` (D-RUNTIME A). O CI já usava 3.11.
5. **Mudanças deliberadas de comportamento sem limite** (R2, R4 e R5) estão listadas no §8, para o Gate 2.
6. **Revisão independente** (`validador-externo`, `job-29`): **APROVÁVEL COM AJUSTES**, com 5 MINOR e nenhum
   CRITICAL ou MAJOR (§11). Os ajustes de texto foram aplicados neste relatório depois da revisão. A versão revisada
   está em `registros/relatorio_versao_revisada_s10.md` (sha256 `709419…`). O reforço de oráculo (achado 1) ficou para
   o Gate 2: código e testes não mudaram depois da revisão.

## 1. Escopo e limites

- **Worktree:** `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator-moodle-v1`, branch local `fix/moodle-rmeta-v1`,
  criada pelo usuário a partir de `bf46d51f` e conferida no S1 com `git worktree list` e `git log -1`.
- **Arquivos alterados:** `src/builder/sources/moodle.py`, `tests/test_moodle.py` e `pyproject.toml`.
- **Artefatos:** todos nesta pasta, não versionados:
  - `delta_inicial/`: cópia imutável do delta (+R);
  - `harness_r1_r6.py`;
  - `runner_s7_adquire_v5.py`;
  - `registros/` e `resultados/`.
- **Árvore principal:**
  - única escrita: `.workflow/local/active-task.md`;
  - `git status` final igual ao do S1;
  - fontes v5, etapa 2 e `.frzero/validacao_externa_aquisicao_29-09` fotografados antes e depois do S7, sem
    diferença.
- **O que não houve:**
  - git de escrita (git-lock ativo);
  - rede, instalação de pacote, LLM do motor, motor, gold ou pacote cego;
  - edição de REL, ISS ou tracker.
- **Worker:** só o do S10.

## 2. Hashes

| arquivo | partida | final |
|---|---|---|
| HEAD da worktree | `bf46d51fc80d1e7dcc62c08cccd0399c056bcbe1` | igual |
| `src/builder/sources/moodle.py` | `244301234d671b4ebb990499c96d4f2a6257348d614abcc15ee3e987c12b319b` (delta) | `be9788c3c8b0c88f30dcf67fc373c5f8ffc0ed3a1fdc2350619de8043ed18816` |
| `tests/test_moodle.py` | `99951fdbdc2a2618c3a164ada26e70111a5486e02e00d14e0731f4fcc4be5716` (delta) | `c148166faa7ac3c5e68a0cf6c0ba0b16366620cbb33f28e93ee04134f2eefc3f` |
| `pyproject.toml` | `1c42944c80da81331213608f3dc4d596bc112bb615148a1899538fd20460f436` | `30c8587633fc667e167e7daed9fa9f4e7d44de1b2c91a5cb2c86cae7d1fa3797` |

Os hashes do harness, do runner, dos resultados e deste relatório estão em `hashes_finais.txt`, gerado no S11, depois
da revisão. A revisão viu o manifesto parcial do S10 (`registros/s10_conjunto_revisado_sha256.txt`, 7 entradas). Fontes
v5 da principal, antes e depois: `registros/v5_sha256_antes.txt`, sem mudança.

## 3. Ambiente (S2)

| runtime | executável | pytest | uso |
|---|---|---|---|
| CPython 3.11.9 (MSC v.1938) | `GPT-Tutor-Generator/.venv/Scripts/python.exe` | 9.0.2 | suíte completa, `test_moodle`, harness, runner S7 |
| CPython 3.13.12 (MSC v.1944) | `AppData/Roaming/uv/python/cpython-3.13.12-windows-x86_64-none/python.exe` | ausente | harness; stub `requests` declarado |
| CPython 3.14.3 (MSC v.1944) | `AppData/Local/Python/pythoncore-3.14-64/python.exe` | ausente | harness |

- **SO:** Windows 11 Pro 10.0.26200.
- **Execução:** sempre `-B`, `PYTHONDONTWRITEBYTECODE=1` e `-p no:cacheprovider`; `--basetemp` dentro desta pasta. Ao
  final, nenhum `__pycache__` foi criado na worktree nem na pasta v5.
- **Stdlib:** as funções chunked usadas pela V1 (`read1`, `_read1_chunked`, `_get_chunk_left`,
  `_read_next_chunk_size` e `_read_and_discard_trailer`) são idênticas nos três runtimes. Mudam só `_safe_read` e o
  `amt` negativo de `_read_chunked` em 3.13 e 3.14, que a V1 não usa para payload (conferido por `diff` dos fontes).

## 4. Comandos e códigos de saída

Todos com cwd na worktree, exceto onde indicado.

| passo | comando | saída | registro |
|---|---|---|---|
| S3 | `.venv python -B -m pytest tests -q -p no:cacheprovider -rfEs --basetemp=<art>/tmp_s3` | 1 (2 falhas preexistentes) | `registros/s3_suite_original.txt` |
| S4 | `pytest tests/test_moodle.py` (delta + testes novos) | 1 (33 vermelhos esperados) | — |
| S4 | suíte completa (delta + testes novos) | 1 | `registros/s4_suite_com_testes_novos.txt` |
| S4 | `harness_r1_r6.py --moodle delta_inicial/moodle.py --modo delta`, nos 3 runtimes | 0, 0, 0 | `registros/s4_harness_delta.txt`, `resultados/s4_harness_delta_*.json` |
| S4 | sanidade: o mesmo delta em `--modo candidato` (3.11.9) | **1, como esperado** | `resultados/s4_sanidade_delta_como_candidato_3.11.9.json` |
| S6 | `pytest tests/test_moodle.py` (candidato) | 0 (119 aprovados) | `registros/s6_test_moodle_candidato.txt` |
| S6 | suíte completa (candidato) | 1 (as mesmas 2 falhas) | `registros/s6_suite_candidato.txt` |
| S6 | `harness_r1_r6.py --moodle src/builder/sources/moodle.py --modo candidato`, nos 3 runtimes | 0, 0, 0 | `registros/s6_harness_candidato.txt`, `resultados/s6_harness_candidato_*.json` |
| S7 | `runner_s7_adquire_v5.py --worktree <wt> --principal <principal> --sha-esperado be9788c3… --basetemp <art>/tmp_s7` | 0 | `registros/s7_runner.txt`, `resultados/s7_runner_adquire_v5.json` |
| S8 | `pytest tests --collect-only -q` com o `pyproject` novo | 0 (2528 coletados) | `registros/s8_pyproject_coleta.txt` |

## 5. Suíte completa em três estados (só CPython 3.11.9)

| estado | produto | testes | coletados | aprovados | falhas | pulados |
|---|---|---|---|---|---|---|
| S3 original | delta | originais | 2463 | 2457 | 2 | 4 |
| S4 com testes novos | delta | novos | 2528 | 2489 | 35 | 4 |
| S6 candidato | V1 | novos | 2528 | 2522 | 2 | 4 |

- **Falhas preexistentes**, idênticas nos três estados e sem relação com o Moodle:
  - `test_caracterizacao_blocos_atual.py::test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor]`: baseline golden
    da divisão de blocos;
  - `test_pdf_markdown.py::test_respect_actualtext_tira_a_flag_e_restaura`: premissa sobre o pymupdf instalado.
- **Pulos:** os mesmos 4 nos três estados (conferido por hash da lista).
- **S3 → S4:** mais 65 itens coletados:
  - 63 casos parametrizados em 14 testes, um por comportamento;
  - `test_contrato_todo_caso_pertence_a_um_teste`;
  - `test_call_retencao_do_ultimo_corpo_entre_chamadas` (R02).

  Os 33 vermelhos novos são:
  - 20 defeitos;
  - 4 casos da regra nova R5;
  - 8 controles vermelhos **só** pela asserção nova "causa encadeada", porque o delta usa `from None`;
  - 1 caso novo (`TIMEOUT-PAYLOAD`).

  Nenhum teste preexistente mudou de estado.
- **S4 → S6:** os 33 passam a verde; mais nada muda.

## 6. Comportamentos, antes e depois

**Como os casos são verificados.**

- **Tabela única de casos** (`_CASOS_ORCAMENTO`, em `tests/test_moodle.py`). Instrumentação e oráculos são
  compartilhados: o pytest usa esse código, e o harness o extrai por AST e roda o mesmo código nos três runtimes.
- **Corpo da resposta:** uma sequência de segmentos de framing (`f`), payload (`p`) ou trecho proibido (`x`, que nada
  pode ler). O cliente real lê sobre um `http.client.HTTPResponse` real.
- **Instrumentação do fio** (`_FioCorpo`): registra cada operação depois do cabeçalho (pedido, posição, dados e erro),
  inclusive as que lançam exceção. Ela simula:
  - **timeout:** a partir da posição `corte` nada mais chega, e o que passaria do corte não é entregue;
  - **retorno curto:** `read1_max` encurta o `read1`, como num socket.
- **Oráculos históricos** (os observáveis dos reprodutores): tipo, retorno, contador, `ultimo_corpo`, `partial` e
  aberturas.
- **Oráculos novos:**
  - **R1/R3:** contador e corpo iguais ao payload que o fio entregou;
  - **R2:** cada pedido de payload sob limite fica dentro do saldo do fio, e nenhuma operação toca o trecho proibido;
  - **causa encadeada**, quando contratada;
  - **sem leitura**, quando contratado;
  - **tamanho negativo:** a linha de tamanho foi lida e nada depois;
  - **R6:** sem limite, o corpo é igual ao `r.read()` nos casos de sucesso.

**Por comportamento** (a tabela por caso está em `resultados/tabela_antes_depois.md`):

| comportamento | casos | delta (S4, igual nos 3 runtimes) | V1 (S6, igual nos 3 runtimes) |
|---|---|---|---|
| payload de chunk interrompido é contado (M-01, R1) | M1a, M1b, M1c, M1d, A07, A08 | defeito: contador e `partial` perdem o chunk corrente (ex.: M1a 0 B; M1d 4 de 7 B); sem causa | contado (3, 5, 3, 7, 3 e 6 B); `partial` = corpo; causa encadeada |
| CL não governa chunked (M-02, R4) | M2a, M2b, M2c, A02, A03, A12, A16 | defeito: `IncompleteRead` pelo CL (M2a); recusa antecipada pelo CL (M2c, A02, A12, A16); sucesso indevido sob CL = saldo (M2b, A03) | sucesso com `[]` (M2a, M2c, A02, A12, A16); `OrcamentoExcedido` no saldo, sem pedir além (M2b, A03) |
| payload contado antes de falha de framing (P-01) | A18, A19, A33, A34; controle A20 | defeito: 0 de 2 B em `LineTooLong`/`TimeoutError` | 2 B, corpo `[]`, exceção propagada; A20 verde nos dois |
| tamanho negativo recusado antes do payload (P-02, R2) | A21, A22, A35 | defeito: A21 consome 3 B com `read(-1)`; A22 consome 23 B, pedido acima do saldo e leitura do trecho proibido; A35 recusa indevida pelo CL, sem chegar ao tamanho | `IncompleteRead` com 0 B; a última operação é a leitura da linha `-1`; nada lido depois |
| Transfer-Encoding não suportado (R5, regra nova) | A23, A24, TE-REPETIDO, TE-IDENTITY; controle TE-CAIXA | regra ausente: lê o corpo (A24 dá `JSONDecodeError` com 12 B) | `UnknownTransferEncoding` sem nenhuma operação no corpo; `Chunked` (caixa) continua aceito |
| chunk terminal | C02, A01, SO-ZERO, SO-ZERO-LIMITE | controle verde | verde; só o chunk zero dá corpo vazio e `JSONDecodeError` |
| parcial de CRLF não é payload (R3) | C16, C17, A09 | controle verde no histórico; a asserção nova "causa" falha | verde, com causa |
| `read1` curto | C09, CHUNK-CURTO, CHUNK-MAIOR-QUE-BLOCO | controle verde | verde: continua depois de retorno curto, conta uma vez e mantém o resto do chunk |
| timeout no meio do payload | TIMEOUT-PAYLOAD (novo) | registrado: 0 B, porque o `read` do delta espera o chunk inteiro e, no modelo, nada chega | `TimeoutError` com 2 B (`[1`), exatamente os fragmentos entregues |
| sem CL, não chunked | C04, C05, C10, C12 | controle verde | verde: recusa no saldo exato sem sondar; sucesso com fim confirmado |
| CL válido, não chunked | C01, C11, C19, C20 | controle verde | verde: completude provada pelo CL, inclusive depois de `read1` curto |
| saldo exato em chunked | C03, A31 | controle verde | verde: recusa sem ler o framing seguinte. O oráculo não exige a ausência de operação posterior (achado 1 da revisão), mas as operações registradas em `s6_harness_candidato_*.json` mostram, nos três runtimes, só a linha de tamanho e um `read1(2)`, sem nada depois; o mesmo vale para M2b, A03 e C04 |
| controles de saldo, leitura e erros | C06–C08, C13–C15, C18, A04–A06, A17 | controle verde (C18, A04–A06 e A17 só falham na asserção nova "causa") | verde; C06 e C07/C08 sem operação no corpo; C07/C08 sem abertura |
| tolerâncias da stdlib mantidas | A11, A13, A14, A15, A32 | controle verde sob a tolerância declarada | verde; corpo igual ao `r.read()` |
| retenção do último corpo | R02 | controle verde | verde |

**Não reexecutados por serem idênticos a outro caso:**

- A10 ≡ C16;
- A25 ≡ C07 e A26 ≡ C08;
- A27 ≡ C05;
- A28 a A30 ≡ C13 a C15.

**Ajustes dos testes existentes:** os do plano (zero leituras no C06; zero aberturas e saldo negativo no C07/C08)
estão cobertos pelos casos parametrizados. Os testes existentes não foram alterados, e o `:653` (objeto falso só com
`read`) segue verde.

**R01** (reentrância, M-03): só documentação. Há uma linha no `__init__` sobre o uso sequencial por instância.

## 7. Harness stdlib nos três runtimes

| | 3.11.9 | 3.13.12 | 3.14.3 |
|---|---|---|---|
| delta (cópia imutável) | 20 defeitos reproduzidos, 31 controles verdes, 8 controles com asserção nova vermelha, 4 regra nova ausente, 1 novo; inesperados: 0; exit 0 | idem | idem |
| candidato V1 | 64/64 contrato ok (63 casos + R02); exit 0 | idem | idem |

**Identidade, registrada em cada JSON:**

- executável e versão;
- caminho e sha256 do `http/client.py` da stdlib daquele runtime;
- caminho e sha256 do `moodle.py` carregado, conferidos contra `inspect.getsourcefile(MoodleClient)`;
- sha256 do harness e da fonte dos casos;
- stubs declarados.

O harness:

- sai com código ≠ 0 em divergência inesperada, caso não executado ou identidade inválida;
- recusa `-O`;
- veda `socket.connect` e `create_connection`.

A sanidade (delta em modo candidato) saiu com 1, apontando os 33 casos: o harness não é vazio.

**O que cada evidência cobre:**

- **compatibilidade declarada:** `>=3.11`;
- **suíte completa:** executada só em 3.11.9;
- **harness R1–R6:** 3.11.9, 3.13.12 e 3.14.3;
- **3.12:** dentro do intervalo declarado, não testado.

## 8. Mudanças de comportamento deliberadas, também sem limite (para o Gate 2)

1. **R4.** Em resposta chunked, o Content-Length é ignorado. Antes, chunked com CL maior que o corpo dava
   `IncompleteRead` (M2a); agora dá sucesso.
2. **R2.** Tamanho de chunk negativo agora dá `IncompleteRead` com 0 B. Antes, o `read(-1)` consumia o resto do fio.
3. **R5.** `Transfer-Encoding` presente que não seja exatamente um `chunked` é recusado antes do corpo, com
   `http.client.UnknownTransferEncoding`. A comparação é a da stdlib, `lower()`. A recusa vale para:
   - listas;
   - `identity`, `gzip` e outros codings;
   - cabeçalhos repetidos.

   Também vale sem limite, o que atinge a UI, `scripts/moodle_pull.py` e `scripts/migrate_signals.py`. Antes, a
   resposta era aceita.
4. **Causa encadeada.** `IncompleteRead` reconstruído agora traz `from exc`, em vez de `from None`. Muda a mensagem e o
   traceback; nenhum consumidor lê a cadeia (§9).
5. **Dependência de membros privados da stdlib:**
   - `HTTPResponse._get_chunk_left()` e a semântica de `chunk_left` (> 0 pendente, `None` fim, < 0 inválido);
   - código idêntico nos três runtimes testados;
   - fora deles, sem garantia: motivo da restrição a `>=3.11`. O 3.12 está no suporte declarado, mas não foi testado
     (correção pós-revisão, achado 4).
6. **Objetos de resposta sem `read1`** (falsos de teste) seguem pelo `read`, como no delta, e sem `chunked`.

## 9. Consumidores (S7)

**(a) Leitura:**

- **UI** `src/ui/dialogs.py`:
  - `:1719–1723` captura `Exception` e mostra a mensagem;
  - `:1980` captura `Exception` e registra no log;
- `scripts/moodle_pull.py:337` e `scripts/migrate_signals.py:75` constroem o cliente **sem limite**;
- nenhum consumidor lê `__cause__`/`__context__` nem soma o `partial` da cadeia: o parcial oficial é o da exceção
  externa;
- `UnknownTransferEncoding` é `http.client.HTTPException`, não `RuntimeError`; na UI, cai no `except Exception`.

**(b) Runner, um processo** (`resultados/s7_runner_adquire_v5.json`):

1. **Import:** a worktree vai a `sys.path[0]` e `src.builder.sources.moodle` é importado. Conferido: o arquivo é o da
   worktree e o sha256 é `be9788c3…`.
2. **`adquire.py` carregado do caminho original.** Ele põe a raiz da principal em `sys.path[0]` e reaproveita o módulo
   em cache. Conferido: `adquire.M is M`, e a classe vem do arquivo da worktree.
3. **`pytest.main` na pasta `correcoes/aquisicao/`:**
   - rootdir e configfile da principal (`pyproject.toml`);
   - 40 aprovados.
4. **Identidade conferida de novo** depois do pytest: ok.
5. **Outros módulos `src` carregados** (helpers, patterns, models.core): todos da worktree.
6. **Principal, nas áreas verificadas** (afirmação limitada pela revisão, achado 2):
   - `git status` antes e depois igual ao do S1;
   - sha256 dos 4 fontes v5 iguais;
   - fotos de v5, etapa 2 e `.frzero` sem diferença;
   - `--saida` e `--basetemp` apontaram para esta pasta da worktree (comando no §4);
   - os dois arquivos do delta na principal seguem com os hashes de partida, e o `pendencias.md` está com `c2b89ef2…`
     (hash não registrado no S1).

   Isso não é garantia integral de que nada mudou na principal; essa garantia exigiria proteção de escrita. O runner
   não valida que `--saida` e `--basetemp` fiquem fora da principal. Esse ajuste fica para o Gate 2.

O runner não reexecutou a v5 contra o delta (fora do plano). Os 40 testes passaram contra o candidato.

## 10. Texto proposto para REL e ISS (S9). Não aplicado

**Versões examinadas** (árvore principal, não versionadas, só leitura):

- REL = `docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa3_correcoes_29-09/relatorio_correcoes_etapa3.md`
  (sha256 `6c7d277b131aa71b0560e558c2967e7533db990ac94b114062d1df0b0419f5e5`);
- ISS = `issue_correcoes_etapa3.md`, na mesma pasta (sha256
  `65b563e6ab038f7b8d51051764d8f148c4cccbe77d6204eabc1755cd0f22c1cd`).

**Candidato descrito:** `moodle.py` `be9788c3…`.

**REL §6, linha 292.** Hoje: "O corpo passa a ser lido em blocos, e cada bloco é contado ao chegar." Proposta:

> O corpo é lido por fragmentos (`read1`), e cada fragmento é contado assim que a aplicação o recebe, antes de o
> framing seguinte ser lido (correção V1, 01/10/2026; contrato R1–R6 abaixo).

**REL §6, linhas 299–300.** Hoje: "Os bytes são contados também quando o JSON é inválido, a API devolve erro, a
resposta vem incompleta ou há interrupção entre blocos." Proposta:

> Os bytes são contados também quando o JSON é inválido, a API devolve erro, a resposta vem incompleta (inclusive
> chunk interrompido) ou a leitura seguinte falha (`IncompleteRead`, `TimeoutError`, `LineTooLong` ou interrupção).
>
> **Contrato da leitura do corpo (V1, 01/10/2026):**
>
> - **R1:** todo fragmento de payload recebido pela aplicação é contado e fica em `ultimo_corpo` assim que chega.
> - **R2:** sob limite, nenhum pedido de payload passa do saldo. Tamanho de chunk negativo é recusado com
>   `IncompleteRead` antes de qualquer leitura de payload. A linha de tamanho segue o `int(linha, 16)` da stdlib (não
>   é parser estrito).
> - **R3:** framing (linha de tamanho, extensões, CRLF e trailers) não é contado nem entra no corpo.
> - **R4:** em resposta chunked, o Content-Length é ignorado.
> - **R5:** `Transfer-Encoding` que não seja um único `chunked` (comparação `lower()`, como a stdlib) é recusado antes
>   do corpo, com `http.client.UnknownTransferEncoding`. A recusa inclui listas, outros codings e cabeçalhos repetidos.
> - **R6:** sem limite, o corpo é o mesmo do `r.read()` nos casos conformes.
>
> **Tolerâncias mantidas da stdlib:**
>
> - chunk zero sem CRLF ou sem a linha vazia final;
> - trailer truncado;
> - CRLF depois do chunk não validado.
>
> **Uso:** sequencial por instância. **Dependência:** membros privados `HTTPResponse._get_chunk_left`/`chunk_left`,
> verificados em CPython 3.11.9, 3.13.12 e 3.14.3; suporte declarado `>=3.11`.

**REL §6, linhas 291 e 295** (acréscimo pós-revisão, achado 3; sem isso, o REL contradiz R4):

- linha 291, "`limite_bytes` (`None` = comportamento anterior)" → "`limite_bytes` (`None` = sem limite de bytes)";
- linha 295, "Um Content-Length acima do orçamento restante não é lido." → "Em resposta não chunked, um Content-Length
  acima do orçamento restante não é lido; em chunked, o Content-Length é ignorado (R4)."

**ISS A2, ao final.** Proposta:

> **Atualização 01/10/2026 (V1).** A leitura implementada difere do item 3 desta proposta:
>
> - não usa `r.read(teto)`: lê por `read1`, contando cada fragmento;
> - em chunked, valida o tamanho do próximo chunk antes de ler payload, e o Content-Length é ignorado;
> - recusa `Transfer-Encoding` não suportado antes do corpo.
>
> O contrato R1–R6 está no relatório, §6. Os testes de `tests/test_moodle.py` são por comportamento (casos C, M e A
> dos reprodutores e casos novos), e um harness stdlib roda os mesmos casos em 3.11.9, 3.13.12 e 3.14.3.

**ISS A6, R-META, linhas 344–345.** Hoje: "sem mudança de resultado com `limite_bytes = None`: a suíte do produto de
`test_moodle.py` e a regressão completa `python -m pytest tests -q` verdes". Proposta:

> Sem mudança de resultado com `limite_bytes = None` nos casos conformes (R6). As mudanças deliberadas sem limite são
> as de R2 (tamanho negativo recusado), R4 (CL ignorado em chunked) e R5 (`Transfer-Encoding` não suportado
> recusado), além da causa encadeada no `IncompleteRead`. A suíte do produto de `test_moodle.py` fica verde, e a
> regressão completa `python -m pytest tests -q` não ganha falha nova.

## 11. Revisão independente (S10)

**Execução:**

- `job-29`, `run-14`;
- papel `validador-externo` (Codex `gpt-6-astra`, effort high, somente leitura, 1800 s);
- uma tentativa, `escaladas_automaticas` 3 → 4 registrada antes;
- lançada às ~03:40 e concluída com `succeeded`.

**Versão examinada:** `registros/s10_conjunto_revisado_sha256.txt`:

| arquivo | sha256 (início) |
|---|---|
| `moodle.py` | `be9788c3` |
| `test_moodle.py` | `c148166f` |
| `pyproject.toml` | `30c85876` |
| `relatorio.md` | `70941918` |
| harness | `6bd88478` |
| runner | `aa317074` |
| diff total | `f3345f8f` |

O revisor conferiu os sete hashes.

**Parecer: APROVÁVEL COM AJUSTES.** O revisor não identificou violação funcional de R1–R6 nos caminhos examinados.

O que o revisor verificou:

- reexecutou em memória, no 3.11.9, os 63 casos e sondas extras sem `read1` (leitura curta, `partial` e timeout):
  todos passaram;
- AST das funções privadas idêntica nos três runtimes;
- instrumentação sem leitura ignorada (`readinto` falha explicitamente);
- os 8 controles vermelhos no delta falham só pela causa encadeada;
- `TIMEOUT-PAYLOAD` corretamente classificado como novo;
- identidade do S7 válida;
- números da suíte e do S7 sustentados pelos registros.

**Achados (todos MINOR) e destino:**

| # | achado | destino |
|---|---|---|
| 1 | o oráculo de C03/A31 não prova a ausência de sondagem do framing: o revisor acrescentou em memória leituras do CRLF, do chunk zero e do terminador, e `_confere_caso` devolveu `[]` | **Gate 2.** Teste não alterado depois da revisão. As operações registradas mostram que a V1 não sonda (§6). Correção proposta: em casos de saldo exato, exigir que não haja operação depois do payload que esgota o saldo |
| 2 | "principal inalterada" excede o que o S7 fiscaliza: um arquivo já `M` fora das áreas fotografadas não mudaria o `git status`; e `--saida` apontando para a principal escreveria depois da foto | **Relatório corrigido** (§9: afirmação limitada às áreas verificadas). Validar `--saida`/`--basetemp` no runner fica para o Gate 2 |
| 3 | a proposta de REL mantém "Content-Length acima do orçamento não é lido" e "`None` = comportamento anterior", incompatíveis com R4 (M2c) | **Relatório corrigido** (§10: propostas para as linhas 291 e 295) |
| 4 | o §8 dizia que `>=3.11` "não cobre 3.12"; cobre, só não foi testado | **Relatório corrigido** (§8) |
| 5 | `hashes_finais.txt` citado e inexistente na hora da revisão | **Relatório corrigido** (§2). O arquivo é gerado no S11 |

**Não conferido pelo revisor:**

- execução em 3.12;
- suíte completa em 3.13 e 3.14;
- reexecução do pytest e do S7, porque escrevem arquivos;
- ausência absoluta de alteração na principal.

## 12. Lista do Gate 2

Esta lista não torna o conjunto aprovável automaticamente.

1. **Aceitar o diff** de três arquivos: `resultados/diff_worktree_vs_bf46d51f.diff`. A parte nova sobre o delta está em
   `resultados/diff_v1_sobre_delta_moodle.diff` e `resultados/diff_testes_sobre_delta.diff`.
2. **Aplicar REL e ISS** com autorização própria (texto do §10), reconciliando com a versão examinada pela revisão.
3. **Revisão:** APROVÁVEL COM AJUSTES (§11). Decidir os ajustes pendentes:
   - **achado 1:** reforçar o oráculo de saldo exato (teste) e rodar de novo `test_moodle`, a suíte e o harness;
   - **achado 2:** o runner deve recusar `--saida`/`--basetemp` dentro da principal;
   - **comentário em `moodle.py:425`:** "`None` = sem limite, comportamento anterior" também deixou de ser exato em
     R4/R5. É sugestão do coordenador, não achado da revisão.

   Qualquer mudança de código ou teste reabre a comparação com a versão revisada.
4. **Decidir as mudanças sem limite do §8**, em especial R5 nos scripts e na UI.
5. **Grafo:** conferir e atualizar depois da integração (Graphify). Não feito nesta noite.
6. **Integração e merge,** com autorização própria. A principal ainda tem o delta não commitado nos mesmos dois
   arquivos, além de 6 commits locais e 4 stashes. Integrar a V1 exige reconciliar essas cópias de trabalho.
7. **Artefatos desta pasta:** decidir se são versionados. Os `tmp_*` (basetemp do pytest) foram removidos no S11.
8. **Fica aberto, fora deste escopo:**
   - baseline de `src/` (inclui a falha `caracterizacao_blocos`);
   - premissa do pymupdf;
   - tracker;
   - sync do workflow;
   - metodologia;
   - 3.12, não testado.
