# Rodada VOCAB_LIMPO — recompilação limpa, braços e capturas SEM GOLD (26/09/2026)

**Rodada VOCAB_LIMPO capturada e congelada. Gold não lido nesta rodada. Aguardando Gate de avaliação.**

- **Autorização:** Gate 1 do usuário (26/09).
- **Pré-registro:** `docs/reports/2026-09-26-regime-vocab-recompilacao-limpa.md` (bloco NORMATIVO, `protocolo_sha`
  `42e52218…`).
- **Código e relatórios:** esta pasta. **Artefatos locais** (fora do versionamento): `.frzero/vocab_limpo_26-09/`.
- **Não houve:**
  - leitura de régua, gold ou resultados da Fase 1 por ID (travas em todos os processos);
  - `--autorizo-gold`, cálculo de acurácia, ganhos, perdas ou veredictos;
  - mudança em `src/`;
  - LLM fora da geração única;
  - commit ou push.

## 1. Errata da Fase 1

`../wad5_avaliacao_26-09/errata_final_fase1_26-09.md` corrige as três formulações (LF × CRLF, calibração no IA,
mudanças de unidade) sem alterar resultados. A Fase 1 segue congelada e intacta: pacote W-AD5, resultados, avaliação
(22 arquivos) e W-AD4 conferidos pelos próprios manifestos.

## 2. Compilador e configuração congelados antes da rede

- **Congelamento da recompilação:** `62b45e38750efc300fcc03da89f874def35e611054946d273b52d86d93cff676`
  (`.frzero/vocab_limpo_26-09/congelamento_recompilacao.json`, sha256 `83f88504…`).
- **Compilador ATUAL, sem mudar uma linha:** `vocabulary_compile.compile_course_vocabulary` (`60c83080…`), chamado como o
  produto chama. Cliente: `gemini_client.get_gemini_client` (`9635f6aa…`).
  - Árvore `src/` `c2c4fe30…`; HEAD `2589ed5a`.
  - SDK google-genai 2.8.0, pydantic 2.12.5, httpx 0.28.1.
- **Modelo:** `gemini-3.5-flash`, da config do usuário, igual ao default do código e ao `_modelo` histórico. É um
  **alias**: cada resposta devolveu `model_version = "gemini-3.5-flash"`, sem versão mais fina.
- **Prompt de sistema completo** (`SYSTEM`, sha256 `99221b05…`) e schema `Vocab` (`49e06e9e…`) estão no congelamento.
- **Parâmetros não definidos no código:** temperature, top_p, top_k, max_output_tokens, seed, candidate_count,
  penalidades, stop, raciocínio e segurança. Valem os defaults do serviço; sem semente.
- **Políticas do código, registradas:**
  - retry: 5 tentativas só em 429/`RESOURCE_EXHAUSTED` e 5xx; espera de 1 s dobrando até 60 s;
  - sem timeout;
  - `parsed=None` vira erro da unidade, sem retry;
  - parsing, normalização, deduplicação e descarte por `filter_terms`;
  - bundle cortado em 24.000 caracteres.

## 3. Entradas: a partir do CRU congelado

- **Staging isolado:** `.frzero/vocab_limpo_26-09/staging/<curso>/`, árvore `040fe431…`.
  - Entries e markdown são os bytes congelados da Fase 1 (hash conferido um a um): 350 entries e 305 markdowns.
  - `computed_unit_slug` = unidade final da captura CRU da Fase 1 (`07a24d96…`). Foram 7 trocas contra o manifest do
    pacote: SO 6, CG 1.
  - A taxonomia é a congelada do CRU.
  - Tutores vivos e sidecars históricos não foram usados.
- **Ensaio sem rede:** o compilador atual rodou com cliente falso, duas vezes.
  - Inventário: **26 chamadas** (MF 3, SO 5, IA 3, ES2 2, TCC 4, CG 7, FR 2), com requests idênticas nas duas rodadas.
  - O staging e o inventário refeitos com a versão final do script são idênticos aos preliminares (`preparo_v0/`).
  - A chamada IA u05 é cortada nos 24.000 caracteres, por comportamento do produto.

## 4. Geração oficial única (`compilacao.json`, `09874d90…`)

- **Execução:** 26/26 unidades, cada uma na 1ª tentativa; 0 retries, 0 falhas, 0 violações; 265 s.
- **Rede:** um único host resolvido (`generativelanguage.googleapis.com`).
- **Arquivos negados:** só o `.env` (tentativa de leitura do produto no import, bloqueada). A chave nunca foi gravada,
  impressa ou hasheada.
- **Conferência:** cada request foi conferida contra o inventário congelado ANTES do envio.
- **Requests e responses brutas:** 52 arquivos em `.frzero/vocab_limpo_26-09/chamadas/`, com hash de cada um em
  `compilacao.json`. São locais: têm conteúdo acadêmico dos cursos.

| curso | # | unidade | chars do bundle | tentativa | status | s | termos na resposta | request | response |
|---|---:|---|---:|---:|---|---:|---:|---|---|
| MF | 0 | unidade-01-metodos-formais | 11483 | 1 | ok | 11.0 | 37 | `e8e660f4322a` | `faade0006ba3` |
| MF | 1 | unidade-02-verificacao-de-programas | 6326 | 1 | ok | 9.0 | 20 | `2149d0e2c01c` | `bd6959357a47` |
| MF | 2 | unidade-03-verificacao-de-modelos | 1520 | 1 | ok | 10.7 | 18 | `bf6b06d8f21a` | `ddcbf4619dd5` |
| SO | 0 | unidade-01-introducao-ao-estudo-de-sistemas-oper… | 4905 | 1 | ok | 8.2 | 16 | `db93689b5e5a` | `5f4172c0cd61` |
| SO | 1 | unidade-02-gerencia-do-processador | 3338 | 1 | ok | 8.1 | 38 | `3b683ddd6e20` | `46101e34262e` |
| SO | 2 | unidade-03-programacao-concorrente | 3618 | 1 | ok | 10.6 | 21 | `0746d166cb67` | `c15c52129f79` |
| SO | 3 | unidade-05-gerencia-de-memoria | 5191 | 1 | ok | 12.8 | 38 | `e68e8acdf150` | `091f26af7191` |
| SO | 4 | unidade-06-gerencia-de-arquivos | 1530 | 1 | ok | 8.5 | 14 | `2e50f2dde6aa` | `92f60b52c377` |
| IA | 0 | unidade-de-aprendizagem-02-solucao-de-problemas | 8726 | 1 | ok | 7.4 | 32 | `84aa646c553b` | `66db01839e24` |
| IA | 1 | unidade-de-aprendizagem-03-raciocinio-planejamen… | 862 | 1 | ok | 5.3 | 10 | `5079bfcbc8fb` | `cb534feb7d61` |
| IA | 2 | unidade-de-aprendizagem-05-aprendizado-de-maquin… | 24000 (cortado) | 1 | ok | 8.9 | 48 | `e1d28fc4f481` | `1f786c951f3b` |
| ES2 | 0 | unidade-01-arquitetura-de-software | 8085 | 1 | ok | 11.5 | 43 | `8e9def5eae52` | `3a0eb82a6e93` |
| ES2 | 1 | unidade-02-integracao-de-desenvolvimento-e-opera… | 7610 | 1 | ok | 11.5 | 20 | `21fbecfa6fce` | `6f0beb37189c` |
| TCC | 0 | unidade-01-conjuntos-enumeraveis-e-funcoes-recur… | 5554 | 1 | ok | 9.3 | 31 | `4d9cfad751fa` | `74ec269b788b` |
| TCC | 1 | unidade-02-turing-computabilidade | 4654 | 1 | ok | 13.5 | 46 | `5a4f63f0ffa0` | `2141dbb78d1e` |
| TCC | 2 | unidade-03-problemas-indecidiveis | 3486 | 1 | ok | 11.0 | 23 | `bec657814637` | `3146fa5cecf5` |
| TCC | 3 | unidade-04-hierarquia-de-classes-de-complexidade | 5735 | 1 | ok | 14.7 | 55 | `2caa2679af9b` | `ee2bc792d028` |
| CG | 0 | unidade-01-introducao-ao-processamento-grafico | 1814 | 1 | ok | 7.0 | 18 | `e379fae7633b` | `5250881a024d` |
| CG | 1 | unidade-02-fundamentos-matematicos | 4702 | 1 | ok | 8.7 | 26 | `9e75189e95db` | `25f356630777` |
| CG | 2 | unidade-03-processamento-de-imagens-e-visao-comp… | 5099 | 1 | ok | 12.3 | 32 | `8097eb994bea` | `277c4800c967` |
| CG | 3 | unidade-04-processo-de-visualizacao-2d | 4003 | 1 | ok | 10.1 | 11 | `7dedc3ee8235` | `a925bfc5917f` |
| CG | 4 | unidade-06-processo-de-visualizacao-3d | 4157 | 1 | ok | 6.7 | 19 | `4ed06c9e867e` | `d33c991924d7` |
| CG | 5 | unidade-07-representacao-e-modelagem-de-objetos | 3206 | 1 | ok | 9.9 | 21 | `71b6f46f8a5d` | `197da1769b9b` |
| CG | 6 | unidade-08-sintese-de-imagens-realisticas | 2338 | 1 | ok | 7.3 | 11 | `cba2a01b9807` | `41f92b837f19` |
| FR | 0 | unidade-01-introducao-a-redes-de-computadores | 2841 | 1 | ok | 7.3 | 38 | `1138ba372b57` | `a8a173488637` |
| FR | 1 | unidade-02-nivel-de-aplicacao | 5112 | 1 | ok | 10.7 | 51 | `6b59ed9f77e2` | `763a0c14c403` |

(Os hashes da tabela são os 12 primeiros hex; os completos estão em `compilacao.json`.)

## 5. Sidecars VOCAB_LIMPO, proveniência e sanidade (sem gold)

- **Sidecars** (`.frzero/vocab_limpo_26-09/sidecars/<curso>/.glossary_curation.llm.json`), sha256: MF `dab47b68…`, SO
  `d355d640…`, IA `5a46b6fb…`, ES2 `e5e38cdb…`, TCC `574d08c3…`, CG `07575d27…`, FR `09c747db…`.
- **Proveniência:**
  - no próprio sidecar: `_provenance`, `_modelo` e `_raw`;
  - na rodada: congelamento `62b45e38…` com protocolo, código, SDK, prompt, schema, entradas, inventário e política,
    mais `compilacao.json` com as chamadas.
- Os sidecars históricos (LLM e manual) não foram tocados.
- **Sanidade** (`sanidade.py`, `sanidade.json` `4d709962…`): **aprovada** em todos os cursos.
  - Parse ok; todas as chaves são tópicos existentes da taxonomia CRU.
  - Sem duplicata, termo vazio ou termo em mais de um tópico.
  - Sem manual no staging.

| curso | tópicos na taxonomia | tópicos com termo | termos | termos únicos | chamadas | retries | falhas |
|---|---:|---:|---:|---:|---:|---:|---:|
| MF | 23 | 19 | 64 | 64 | 3 | 0 | 0 |
| SO | 36 | 13 | 97 | 97 | 5 | 0 | 0 |
| IA | 20 | 12 | 81 | 81 | 3 | 0 | 0 |
| ES2 | 21 | 13 | 57 | 57 | 2 | 0 | 0 |
| TCC | 26 | 23 | 128 | 128 | 4 | 0 | 0 |
| CG | 59 | 36 | 110 | 110 | 7 | 0 | 0 |
| FR | 32 | 8 | 75 | 75 | 2 | 0 | 0 |

**Comparação descritiva com o VOCAB_LLM histórico** (não é critério nem alvo; `sanidade_vocab_limpo.md`):
- Jaccard médio por tópico entre 0,10 (TCC) e 0,69 (FR).
- Termos em comum / só histórico / só limpo (contagens de termos normalizados por curso): MF 42/81/64, SO 53/99/97,
  IA 46/80/81, ES2 37/60/57, TCC 33/96/128, CG 59/83/110, FR 51/53/75. Os dois últimos números são os totais de cada
  sidecar, não exclusivos.
- As unidades usadas para agrupar diferem das históricas (agora vêm do CRU), então a diferença de entrada é esperada.

## 6. Braços, controles e preflight (sem gold)

- **Harness:** cópia do congelado da Fase 1, adaptada por `adapta_rodada.py` com trocas exatas e contadas.
  - Diff real `diff_w5_vl.patch`, +152/−131: nomes dos braços; fonte do sidecar do VOCAB_LIMPO (recompilação congelada;
    tutores vivos não são lidos); nenhum manual; caminhos; proibição dos resultados da Fase 1 por ID.
  - Métricas, controles, sorteio, reconstrução, instrumentação e validação não mudaram.
- **Braços:** CRU_LIMPO, VOCAB_LIMPO, CTRL_MAIOR_LIMPO, CTRL_ALEAT_LIMPO_1/2/3.
  - Mesmas sementes (1, 2, 3) e regras dos controles; relações de origem do VOCAB_LIMPO.
  - Sem VOCAB_ATUAL, sem híbrido.
- **Suíte sintética:** `testes_vl.txt`, **93/93**.
  - 87 herdados com nomes adaptados. O teste que usava "VOCAB_LIMPO" como braço inexistente passou a usar
    "VOCAB_ATUAL". Antes da correção, ele disparou um worker que parou na pré-execução, sem produto nem rede (registro
    em `preparo_v0/`).
  - 6 novos (`test_rodada_limpa.py`): braços, sementes, nenhum manual, liberação; captura da Fase 1 não valida aqui;
    travas proíbem resultados da Fase 1, régua e tutores vivos; fonte do sidecar; **adaptador do avaliador = original
    com só os nomes trocados** (prova estrutural); veredictos com os nomes da rodada.
- **Preflight** (`preflight_vl.{json,md}`, sha256 `9a03a5e6…`): **24/24, saída 0, 430 s**; congelamento da captura
  `6a0f9652fb8cfaffde15cd9d113705536c7fcc5f9b303474a74438ceee8c0e81`.
  - A nos 7 cursos. B no VOCAB_LIMPO só com diferença de ordem de aliases (+56 a +129 aliases por curso, 0 removidos).
    C: identidade = VOCAB_LIMPO (taxonomia e índice).
  - CTRL_MAIOR_LIMPO verificado. Aleatórios verificados: 71 unidades pareadas, 1 identidade sorteada, 6 estruturalmente
    não informativas, nenhuma bloqueada.
  - Nenhum manual; a carga dos 6 braços foi conferida.
  - **CRU_LIMPO = referência W-AB por ID: 350 registros, 0 divergências**, 341 chamados e 9 meta-materiais não
    chamados. Seus insumos são idênticos aos do CRU da Fase 1 (`6689d5f0…`).

## 7. Capturas (`manifesto_capturas_vl.json`, sha256 `875aa946…`)

Comando `--capturar`: 14/14 condições, 1405 s, em sequência, um worker isolado por braço, sem rede. Validador completo
nas seis, e de novo num processo independente. Os mesmos 9 meta-materiais não chamados aparecem em todos os braços, sem
chamada nem score inventados. Nenhuma falha; `capturas/` só contém este congelamento.

| braço | origem | materiais | chamados | não chamados | violações | conteudo_sha | sha256 do arquivo |
|---|---|---:|---:|---:|---:|---|---|
| CRU_LIMPO | reutilizada (preflight) | 350 | 341 | 9 | 0 | `09d384721b68ee9e5b0bfd85a28da2a77b32487bb206c88acba2dbb18a89e2ad` | `67258ddfcf1975b31a441e3846bb443c8cee9cd14caaa568209a184cb701f821` |
| VOCAB_LIMPO | nova | 350 | 341 | 9 | 0 | `fe36d05517f9329551841caf4e39d45f061500149c745630731d757999bedf9e` | `f38feb8b28f661f83c66bac047a7b7d77600157bd6f9e002280a865820209330` |
| CTRL_MAIOR_LIMPO | nova | 350 | 341 | 9 | 0 | `12cbc9d8711dfb0ad1696c1c7bf17fde81033e00e2c3563deda469d77e8b4b14` | `0727dc4807cd94ef3ae4d283bec94192ea6b0232b7bb0162d8d0daeea4828128` |
| CTRL_ALEAT_LIMPO_1 | nova | 350 | 341 | 9 | 0 | `cc277f1de4c16569a273139a6d9860a86fc417a9b6be4936d63078b3b17d8b1e` | `d2a5d885c33f42c5fd4cd38580e4dcefe771e84679bb7e642f5b57055bfa62b6` |
| CTRL_ALEAT_LIMPO_2 | nova | 350 | 341 | 9 | 0 | `e262c2a3d9c7fb380c7c22446ac8f850b42fea5a8d0e2e4625b45e85638d6bbd` | `ed89baf5706ba1f7c1399fa744154ab739d93639a121f2057ef839893a761ab0` |
| CTRL_ALEAT_LIMPO_3 | nova | 350 | 341 | 9 | 0 | `32f2571b328b7545759404c40797bcfa500121c59cbea21161db3ca5ffe04953` | `fe57e7aeff44159e404e4cd4f7635cf55505b56340376faded855656b84530ea` |

## 8. Avaliador da rodada (congelado, NÃO executado)

- `avaliador.py` desta pasta (`6799972f…`, no código congelado da captura) é o avaliador da Fase 1 com SÓ os nomes dos
  braços trocados em `veredictos` e `avalia` (prova estrutural em `test_rodada_limpa.py`).
- Métricas, régua, denominadores e contrato são os mesmos. O descritor da régua (blob IDs) está no congelamento, sem
  pendências.
- **Veredictos pré-registrados:**
  - **A_limpo:** VOCAB_LIMPO supera CRU_LIMPO, CTRL_MAIOR_LIMPO e cada CTRL_ALEAT_LIMPO na primária total;
  - **B_limpo:** ganho de primária, zero perda nos três eixos oficiais, nenhum curso regredindo;
  - **C_limpo:** > 90% por eixo e curso avaliado.
- **Nota para o Gate de avaliação:** a leitura da régua na cópia de trabalho do Windows falha por CRLF (parada da Fase
  1). O procedimento autorizado então foi o espelho endereçado por conteúdo; o Gate de avaliação precisa decidir o
  procedimento desta rodada.

## 9. Limitações

- **Os sete cursos são desenvolvimento contaminado.** O prompt tem ajuste histórico neles (calibrado no IA). A rodada
  não demonstra generalização, ausência de overfitting do prompt, independência nem > 90% em produção.
- **Modelo e parâmetros:**
  - o modelo é um alias sem versão imutável (o serviço devolve o próprio alias);
  - temperature, top_p, top_k, seed e demais parâmetros são defaults não observáveis;
  - sem semente, a geração não é reprodutível. Houve UMA geração oficial, sem escolha.
- **Mudanças no bundle e no agrupamento:**
  - a chamada IA u05 foi cortada no limite do produto (24.000 caracteres);
  - as unidades de agrupamento vêm do CRU, não do estado histórico. É uma diferença deliberada em relação à compilação
    que gerou o VOCAB_LLM.
- **Travas:**
  - na geração, leituras fora das listas foram permitidas e registradas (raiz "sistema" só leitura) para não abortar a
    pilha HTTP; gold, régua, resultados da Fase 1, tutores, `.env` e a config continuaram barrados;
  - as travas não são sandbox.
- **Execuções preliminares** (sem rede; preservadas em `preparo_v0/` com logs):
  - 1º ensaio com permissão de gravação faltando;
  - congelamento v1 nunca usado, refeito depois de corrigir uma permissão de saída que teria marcado violação no fim;
  - teste adaptado que disparou um worker (parou na pré-execução).
- **Suíte:** 93/93 no terminal. O teste herdado de decodificação continua frágil sob `PYTHONIOENCODING=utf-8`, como
  registrado na Fase 1.

## 10. Estado do worktree e preservação

- HEAD `2589ed5a`; `src/` e `tests/` limpos.
- Index: só os 14 renames documentais da limpeza de 25/09. Sem commit.
- Arquivos novos desta rodada, não versionados:
  - pré-registro `2026-09-26-regime-vocab-recompilacao-limpa.md`;
  - pasta `vocab_limpo_26-09/`;
  - errata `wad5_avaliacao_26-09/errata_final_fase1_26-09.md`;
  - tudo em `.frzero/vocab_limpo_26-09/` (ignorado pelo git).
- Histórico intacto, conferido pelos manifestos: Fase 1 (W-AD5, avaliação, espelho), W-AD4 e os sidecars históricos
  (copiados na Fase 1).
- Stashes e alterações alheias preservados.
