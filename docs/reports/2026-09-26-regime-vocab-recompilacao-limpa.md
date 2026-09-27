# Pré-registro — regime VOCAB, recompilação limpa (VOCAB_LIMPO), 26/09/2026

Autorização: Gate 1 do usuário (26/09), depois da avaliação da Fase 1 (W-AD5: "sinal exploratório observado; candidato
reprovado para integração"; errata em `c1-3/wad5_avaliacao_26-09/errata_final_fase1_26-09.md`).

Autorizado:
- UMA recompilação limpa com o compilador atual (rede só para as chamadas do Gemini);
- os braços da rodada limpa e suas capturas SEM GOLD;
- parar antes da avaliação.

**Não** autorizado:
- avaliar ou ler a régua;
- compilador v2 ou cursos novos;
- mudar `src/`, régua, timeline ou denominadores;
- commit, push, PR ou merge.

Só o bloco NORMATIVO entra no hash (`protocolo_sha`) do congelamento da recompilação.

<!-- NORMATIVO:INICIO -->
## R1. Pergunta e nome

- **Pergunta:** o compilador atual, executado UMA vez com entradas e configuração congeladas e sem sidecar manual,
  produz um vocabulário que mantém o sinal exploratório observado na Fase 1?
- **Não é a pergunta:** "o compilador está livre de ajuste ao benchmark?". Os sete cursos são desenvolvimento
  contaminado; o prompt do compilador tem ajuste histórico nesses cursos. Os sidecars novos não são "não contaminados",
  "independentes" nem "holdout".
- **Braço candidato: VOCAB_LIMPO.** "Limpo" significa só:
  - geração nova;
  - sem sidecar manual no carregamento;
  - sem reutilizar o sidecar LLM histórico;
  - entradas, prompt, modelo, filtros, requests e responses rastreados;
  - nenhuma seleção ou edição orientada pelo gold.

## R2. Compilador congelado (sem mudar uma linha)

- Função `src/builder/core/vocabulary_compile.compile_course_vocabulary`, chamada como o produto a chama
  (`pedagogical_regeneration._run_vocabulary_compile_layer`): `compile_course_vocabulary(root, entries,
  load_internal_content_taxonomy(root), client)`, sem `recompile`/`refilter`.
- Cliente `src/builder/runtime/gemini_client.get_gemini_client(config)`, com a config do usuário
  (`~/.gpt_tutor_config.json`). A chave é lida só para criar o cliente e nunca é gravada, impressa ou hasheada.
- **Modelo:** o `gemini_model` da config (`gemini-3.5-flash`), que é o default do código e o mesmo `_modelo` dos
  sidecars históricos. É um identificador ALIAS: não há versão imutável no código. Registra-se o `model_version`
  devolvido por cada resposta. Limitação declarada: o serviço pode mudar o modelo por trás do alias.
- **Chamada:** `generate_content(model, contents=<bundle da unidade>, config=GenerateContentConfig(system_instruction=
  SYSTEM, response_mime_type="application/json", response_schema=Vocab))`.
  - O prompt de sistema completo (`SYSTEM`), o schema e cada bundle têm hash congelado.
  - O código **não define** temperature, top_p, top_k, max_output_tokens, seed, candidate_count nem configuração de
    raciocínio: valem os defaults do serviço, não observáveis nem versionados (limitação declarada).
  - Não há semente: a geração não é determinística. Por isso há UMA geração oficial.
- **Bundle da unidade** (`_bundle`), por material:
  - título, label Moodle e até 24 headings (60 caracteres cada) do markdown congelado, mais os nomes-base dos membros
    extraídos;
  - corte total em 24.000 caracteres (`MAX_BUNDLE_CHARS`). A chamada IA u05 é cortada no limite, por comportamento do
    produto.
- **Retries (código atual):**
  - até 5 tentativas da MESMA request, só para `ClientError` com 429/`RESOURCE_EXHAUSTED` e para `ServerError` (5xx);
  - espera de 1 s, dobrando, com teto de 60 s;
  - demais erros, e resposta sem `parsed` (fora do schema), não têm retry;
  - esgotado ou sem retry: a unidade entra em `_unidades_com_erro` e fica sem termos;
  - não há timeout no código (default do SDK).
- **Parsing:**
  - `resp.parsed` pelo schema `Vocab` (o SDK valida);
  - o tópico casa pelo label exato, com espaços colapsados; tópico devolvido fora da unidade é ignorado;
  - termos com espaços colapsados; vazios descartados.
- **Normalização, deduplicação e descarte (`filter_terms`, gravados em `_raw` e no sidecar filtrado):**
  - descartados: duplicata, termo = label, termo em mais de um tópico, termo igual ou contido (≥ 2 tokens) em nome de
    outra unidade ou tópico, e termo sem token específico (só genéricos do curso, modo `df`);
  - rótulos meta não recebem termos.
- **Falha definitiva:** unidade sem termos, registrada. Nada é completado à mão.
- **Uma resposta válida pelo protocolo entra mesmo que pareça ruim.** Sem escolher entre várias respostas, sem editar,
  remover ou acrescentar termos, sem mudar prompt, filtros ou parâmetros depois da primeira resposta.
- **Defeito de execução que exija mudar o protocolo:** a rodada para e pede nova autorização. Não se mistura versão.

## R3. Entradas: a partir do CRU congelado

- **Área isolada:** `.frzero/vocab_limpo_26-09/staging/<curso>/`. Os tutores vivos e os manifests históricos não são
  usados como estado de entrada.
- **Materiais:** as mesmas entries e os mesmos bytes congelados usados pelo CRU da Fase 1: manifest e markdown dos
  pacotes, conferidos contra `congelamento_entradas` do congelamento `3fe5d1ff…`.
- **Unidade que agrupa os materiais:** a decisão final de unidade da captura CRU da Fase 1 (sha256 `07a24d96…`),
  aplicada deterministicamente em `computed_unit_slug` de cada entry. Os demais campos ficam inalterados.
- **Taxonomia de partida:** a congelada do CRU (sem sidecar LLM, sem manual; igual ao snapshot CRU).
- **Timeline:** não é lida pelo compilador. As fontes externas não são acessadas (o compilador só lê o markdown do
  staging).
- **Inventário e determinismo:** o ensaio sem rede roda o compilador atual com um cliente falso, duas vezes. Ele fixa a
  lista exata de chamadas (curso, unidade, bundle e seus hashes) e prova que as requests são determinísticas.
- **Conferência na geração:** cada request é conferida contra o inventário ANTES de ser enviada. Divergência aborta a
  rodada.

## R4. Zero gold e rede restrita

- **Durante preparação, ensaio, geração, parsing, sidecars, controles e capturas, as travas proíbem:**
  - leitura de régua, gold e arquivos de avaliação;
  - leitura dos resultados da Fase 1 por ID (`wad5_avaliacao_26-09` e seu espelho) e do tracker;
  - `.env`, a config do usuário (depois de criado o cliente) e os tutores vivos.
- **Nada disso vai ao Gemini:** nem gold, nem predição esperada, nem lista de erros, nem IDs escolhidos por terem errado,
  nem explicação das perdas.
- **Rede SÓ na geração** e só para `generativelanguage.googleapis.com`. Qualquer outro host é violação.
  - Sem busca na web, ConceptNet, Wikipedia, ACM CCS ou Wikidata.
  - Nenhum LLM revisa ou "melhora" as respostas.
  - A rede fica bloqueada no replay e nas capturas.
- **Registro de cada chamada:**
  - curso, unidade, índice, tentativa e timestamps;
  - modelo pedido, `model_version` devolvido e configuração;
  - request integral (bundle e config) e resposta bruta integral;
  - status, erro e resposta parseada;
  - hashes de request e resposta.
  - Tudo local, fora do versionamento.

## R5. Sidecar novo e proveniência

- O sidecar é o `.glossary_curation.llm.json` gerado pelo compilador no staging de cada curso, gravado no namespace
  desta rodada. Nunca se mistura com o `.glossary_curation.llm.json` histórico nem com o `.glossary_curation.json`
  manual, ambos preservados.
- **Proveniência da rodada:** identificador e hash do protocolo; modelo; hash do prompt; hashes das entradas e do
  inventário; unidades cobertas; chamadas e respostas relacionadas; código do compilador (árvore `src/`); data; política
  de parsing e normalização.

## R6. Sanidade sem gold (descritiva; não decide continuar)

- **Verificações:** o sidecar parseia; as chaves apontam para tópicos existentes; não há tópico nem unidade inexistente.
- **Contagens:** termos, duplicatas, termos vazios, normalização, unidades chamadas ou com falha.
- **Carregamento:** manual ausente; sidecar histórico ausente do caminho de carregamento; hashes.
- **Tabela por curso:** tópicos; tópicos com termo novo; termos totais e únicos; chamadas, retries, falhas.
- **Comparação descritiva com o VOCAB_LLM histórico:** tópicos, termos, sobreposição, Jaccard por tópico, termos que
  surgiram e sumiram, variação de aliases. NÃO é critério nem alvo.

## R7. Braços da rodada limpa

- **CRU_LIMPO:** a mesma referência CRU (sem sidecar); precisa reproduzir a referência por ID.
- **VOCAB_LIMPO:** só o sidecar novo (sem manual).
- **CTRL_MAIOR_LIMPO:** as relações efetivas do VOCAB_LIMPO, reendereçadas pelo mesmo mecanismo e critério do
  CTRL_MAIOR da Fase 1 (tópico com mais decisões finais do CRU desta execução; mesmo desempate; colisões registradas).
- **CTRL_ALEAT_LIMPO_1/2/3:** mesmas regras dos aleatórios da Fase 1:
  - sementes 1, 2, 3, `random.Random(f"{semente}|{curso}|{unidade}")`, 2000 tentativas;
  - dentro da unidade, com a distribuição de vagas;
  - primeira permutação válida;
  - mesmas regras de colisão e duplicata e mesma classificação de estados.
- **A única diferença é a origem das relações (VOCAB_LIMPO).** Unidade não pareável é registrada pelo protocolo. Sem
  híbrido com manual, sem novas sementes, sem usar resultados históricos para escolher a distribuição.
- **VOCAB_ATUAL e VOCAB_LLM históricos:** só referência documental externa.

## R8. Captura e avaliador

- **Mesma cadeia real da Fase 1:**
  - mesmo corpus e mesma timeline histórica congelada;
  - mesmo código do motor, configuração, `PYTHONHASHSEED=0` e ambiente controlado;
  - mesma instrumentação da 1ª e 2ª passada;
  - reconstrução da taxonomia pelo produto no braço, com glossário e índice do mesmo braço;
  - sem rede, sem LLM;
  - validador completo.
- **O harness da Fase 1 é copiado e só adaptado nos nomes dos braços, na fonte do sidecar e no mapa de manuais** (nenhum
  manual em nenhum braço).
- **CRU_LIMPO tem de reproduzir a referência por ID antes de aceitar as outras capturas.** Se divergir, para.
- **Avaliador:** cópia do avaliador congelado da Fase 1 com SÓ os nomes dos braços trocados, testada com fixtures
  sintéticas e congelada antes das capturas. Mesmas métricas, denominadores e régua.
- **Veredictos pré-registrados:**
  - **A_limpo:** VOCAB_LIMPO supera CRU_LIMPO, CTRL_MAIOR_LIMPO e cada CTRL_ALEAT_LIMPO na primária total.
  - **B_limpo:** ganho positivo de primária, zero perda de acertos atuais nos três eixos oficiais e nenhum curso
    regredindo.
  - **C_limpo:** mais de 90% por eixo e curso efetivamente avaliado, por contagem exata.
  - Nenhum critério novo depois do gold.

## R9. Limites e parada

- **Pode mostrar:** se uma geração nova e rastreada mantém ou não o sinal na mesma população; se o resultado histórico
  dependia só dos arquivos antigos ou do manual carregado; estabilidade da recompilação.
- **Não pode mostrar:** generalização para disciplinas novas, ausência de overfitting histórico do prompt, independência
  dos sete cursos, nem que > 90% funcionará em produção.
- **Parada antes do gold.** A rodada termina com protocolo, compilador e configuração congelados; requests, responses e
  sidecars rastreados; controles verificados; preflight sem gold; capturas congeladas; avaliador adaptado e testado; e
  relatório com manifestos.
- A avaliação exige Gate próprio.
<!-- NORMATIVO:FIM -->

## Registro (fora do bloco normativo)

Execução em `_harness-2026-09-04/c1-3/vocab_limpo_26-09/`; detalhes em `relatorio_vocab_limpo.md`.

- **Congelamento da recompilação:** `62b45e38750efc300fcc03da89f874def35e611054946d273b52d86d93cff676`.
- **Ensaio:** 26 chamadas previstas; requests determinísticas.
- **Geração oficial única:** 26/26 unidades, 1ª tentativa, 0 falhas, 0 violações; modelo devolvido `gemini-3.5-flash`
  (alias).
- **Sanidade sem gold:** aprovada.
- **Preflight:** 24/24; congelamento da captura `6a0f9652fb8cfaffde15cd9d113705536c7fcc5f9b303474a74438ceee8c0e81`;
  CRU_LIMPO = referência por ID (350/0).
- **Capturas:** seis completas e validadas (14/14 condições).
- **Gold não lido.** Aguardando Gate de avaliação.
