# Adendo v3 ao pré-registro do regime VOCAB — Fase 1, cadeia de congelamento fechada (25/09/2026)

Substitui, para a medição, o adendo v2 (`2026-09-25-regime-vocab-adendo-fase1-v2.md`, preservado sem alteração, com a v3
do harness em `_harness-2026-09-04/c1-3/wad3_25-09/`). Motivo: a 3ª revisão adversarial (25/09) apontou três bloqueios:
1. o congelamento não era conferido contra o código e o ambiente efetivamente executados;
2. o validador de captura aceitava registros que não satisfaziam todos os invariantes;
3. o avaliador dependia de carregadores e mapeamentos fora da cadeia de congelamento.

Também pediu correções delimitadas: leituras externas, configuração do ambiente e rastreabilidade das métricas.

Autorizado nesta etapa (Gate 1 restrito W-AD4): corrigir, testar com dados sintéticos, reexecutar os preflights sem
gold e recapturar só o CRU. **Não** autorizado: capturar os seis braços não-CRU, ler ou avaliar contra a régua real,
recompilar, usar rede, LLM ou embeddings, mudar `src/`, testes de produção, sidecars, defaults, régua ou regras do motor,
commit, push, PR ou merge.

Só o bloco entre os marcadores NORMATIVO entra no hash do congelamento (`protocolo_sha`). O registro fica fora dele.

<!-- NORMATIVO:INICIO -->
## N1. Resultado e fases

- **Nome:** "efeito do vocabulário sobre a cadeia de atribuição, condicionado à timeline histórica congelada". Não é
  reprodução integral do produto com vocabulário.
- **Fases separadas:** (1) Fase 1 histórica offline; (2) recompilação limpa, com autorização de rede própria;
  (3) compilador v2; (4) validação em cursos novos, não autorizada.
- Os 7 cursos são desenvolvimento contaminado. 218/251 é limite diagnóstico das fontes examinadas, não impossibilidade
  universal. 279/300 não comprova generalização.

## N2. Entradas, injeção e equivalências

- **Pacotes:** os 7 congelados (MF, IA e CG em `.frzero/wv_importacao_22-09/`; SO, ES2, TCC e FR em
  `.frzero/pacote_fontes_15-09/`). LR fora.
- **Timeline:** histórica e congelada, idêntica em todos os braços, sem recálculo. Os artefatos temporais
  (`.timeline_index.json`, `.card_block_map.json`, `.lessons_index.json`) de cada curso têm hash no congelamento; a
  captura registra o hash de todos os presentes, e ele tem de ser igual ao congelado.
- **Taxonomia:** nos braços com sidecar, reconstrução do produto (`engine._build_rich_content_taxonomy`) com o carregador
  do glossário no palco do braço; no CRU, a congelada. O glossário do índice de unidade é o do mesmo braço.
- **A, B, C e D:** como no adendo v2 (A: sem sidecar == congelada, com ordem, e falha interrompe; B: diagnóstico integral
  "só ordem de aliases" × "outra"; C: `_IDENTIDADE` reproduz VOCAB_LLM na taxonomia ordenada e no índice; D: controles
  sem mudança estrutural, sem remoção, adições iguais ao pretendido como multiconjunto).
- **Identidade:** tópico = (curso, unidade, tópico); nunca `topic_slug` isolado.
- **Entradas externas** (`source_path` absoluto dos manifests, fora dos pacotes):
  - cada caminho passa pelas proibições ANTES de ser lido ou hasheado; gold, `.env` ou caminho negado/proibido
    interrompe a preparação (`preparo_proibido`) e nunca é autorizado por aparecer em `source_path`;
  - congeladas uma a uma pelo caminho exato, somente leitura; o resto das pastas continua fora da lista.
- **Conferência de leitura:** TODA abertura de insumo (comum, externo, braço, referência) confere o hash em disco contra
  o congelado (ou contra a 1ª leitura, quando o arquivo não tem hash congelado próprio). Arquivo lido, alterado e
  reaberto é violação, mesmo que o conteúdo seja restaurado depois. Ao final, tudo o que foi lido é relido: arquivo
  desaparecido ou alterado é violação.

## N3. Congelamento, captura e reúso

- **Congelamento comum** (`id_comum` = sha256 de {esquema `wad4-congelamento-1`, parte normativa}):
  - hash deste bloco normativo;
  - hashes de `captura.py`, `comum.py`, `avaliador.py`, `test_wad4.py`, `test_defeitos_v4.py` e dos helpers
    `replay_bloco_21-09.py` e `replay_unidade_21-09.py`;
  - produto: base pretendida `2589ed5a…` e hash POR ARQUIVO de toda a árvore `src/`;
  - intérprete: executável, versão, plataforma, flags, `pycache_prefix` e hash da lista de distribuições;
  - caminhos: raiz do repositório e início do `sys.path`;
  - ambiente: valores dos parâmetros declarados (N4) e só os NOMES das variáveis de sistema herdadas;
  - árvores dos 7 pacotes (por arquivo), entradas externas (por arquivo), artefatos temporais por curso;
  - referências (captura W-AB) e inventário (350 IDs);
  - descritor da avaliação (N7): caminhos explícitos e blob IDs, lidos do índice do git sem abrir os arquivos da régua;
  - expectativas: mapa de manuais, braços liberados, denominadores.
- **Insumos por braço:** palco, snapshots de taxonomia e de índice (arquivo e conteúdo), fora do `id_comum`, com hash
  próprio (`insumos_braco`). O congelamento valida as duas ligações (normativo → `id_comum`; descritor → `insumos_braco`).
- **Código executado = código validado** (estratégia):
  - todo processo se relança com o ambiente montado do zero, `-B` e `-X pycache_prefix=<área vazia isolada>`: o
    bytecode é sempre compilado do fonte, e a área de cache tem de estar vazia;
  - intérprete, flags, `pycache_prefix`, `sys.path` inicial, código do harness e árvore `src/` são conferidos contra o
    congelamento ANTES de qualquer import do produto;
  - depois dos imports, cada módulo `src.*` carregado tem origem (`__file__`) dentro da raiz e hash igual ao congelado,
    e os helpers vêm dos caminhos declarados;
  - no fim, código e `src/` são conferidos de novo;
  - qualquer divergência interrompe; o congelamento nunca é atualizado para aceitar divergência.
- **Captura** (`wad4-captura-1`): a validação tira todas as expectativas do congelamento, nunca da própria captura. Rejeita:
  - esquema, braço, modo, status, `id_comum` ou insumos errados; violações; negados ausentes;
  - leitura fora das categorias permitidas ou de estado de outro braço;
  - `conteudo_sha` que não confere (ou valor não finito);
  - inventário, `por_curso` ou `verificacoes` ausentes ou divergentes: taxonomia e índice por curso iguais aos snapshots
    do braço, manual carregado igual ao mapa congelado, temporais iguais aos congelados, braço não-CRU sem leitura da
    taxonomia congelada, carga sem decisões;
  - registros fora do contrato (N5).
- **Reúso:** a autorização do braço é conferida antes de lançar, antes de ler cache e antes de aceitar. Nome de arquivo
  nunca basta; captura inválida no caminho esperado interrompe, sem sobrescrever. Gravação atômica; falhas em `falhas/`.
- **Validação histórica:** uma captura antiga é validada só com artefatos imutáveis (captura + congelamento), sem exigir o
  checkout original.

## N4. Violações, travas e ambiente

- **Violação:** gold (padrões de nome), palco ou snapshot de outro braço, tutor vivo depois do preparo, fora da lista,
  escrita em área somente leitura (código incluído), insumo divergente, não congelado, desaparecido ou alterado durante a
  execução, caminho proibido na preparação, rede, subprocesso não nomeado, compilador de vocabulário, captura não
  autorizada. Toda violação fica registrada mesmo quando uma camada engole a exceção; status de falha, nenhuma captura
  gravada, diagnóstico sem conteúdo de gold nem segredo, saída ≠ 0.
- **Subprocesso:** permissão temporária e NOMINAL (`git` no P0, o próprio intérprete para os workers), fechada mesmo em
  exceção.
- **Alcance real:** `builtins.open`/`io.open`, socket (`connect`, `connect_ex`, `create_connection`, `getaddrinfo`),
  `subprocess.Popen` e o compilador. Não cobre `os.open`, `mmap`, `io.open_code` (imports) nem extensões C: o código
  importado é conferido à parte (N3). Não é sandbox.
- **Ambiente declarado** (todos os processos; nada mais do terminal é herdado além das variáveis de sistema do Windows,
  registradas só pelo nome): `PYTHONHASHSEED=0` (condição do experimento: ordem determinística de conjuntos),
  `TUTOR_NO_VOCAB_COMPILE=1`, `TUTOR_NO_CODE_SYNTH=1`, `UNIT_GENERIC_MODE=df` (o default do código, explícito),
  `PYTHONIOENCODING=utf-8`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`. Variável não declarada no processo =
  divergência e parada. Nenhum valor secreto é salvo, impresso ou hasheado.
- **Negado por declaração (não é violação):** `.env` da raiz. Pode conter segredos **e configuração**; não é lido (a
  trava impede a leitura sem ler o conteúdo e registra em `negados`). O carregador do produto
  (`src/utils/helpers._load_project_env_file`) não sobrescreve variáveis já presentes; as leituras de ambiente do `src/`
  que afetam o caminho medido estão no ambiente declarado. A equivalência com as medições históricas é empírica: a
  reprodução do CRU por ID.
- **Manual esperado:** no VOCAB_ATUAL, só CG, ES2, IA, SO e TCC; nos demais, nenhum.
- Os workers nunca leem tutores vivos. O cache do módulo `platform` é aquecido antes das travas (no Windows, a 1ª
  consulta executa `ver`).

## N5. Captura por material

Registrados por material:
- curso e ID, iguais às chaves externas;
- `chamado` (booleano) e motivo obrigatório quando não chamado (`manual_subunit`, `nao_material`, `sem_bloco`,
  `nao_identificado`);
- 1ª chamada: unidade fornecida (texto); pontuações como lista de registros (unidade, tópico, score numérico finito),
  sem candidato duplicado; vencedor com identidade (unidade, tópico); confiança finita; ambiguidade booleana; motivos;
- chamadas posteriores, cada uma com a mesma estrutura;
- decisão final completa: bloco, unidade e sub (texto), `conf_sub` (número finito ou nulo), motivos;
- hash da taxonomia usada, igual ao do curso no braço.

Premissa: a unidade da 1ª passada é igual à final. Saída fora da taxonomia (pino manual) não é erro estrutural.

## N6. Controles

Como no adendo v2: CTRL_MAIOR (concentração na classe majoritária do CRU desta execução) e CTRL_ALEAT_1/2/3 (sementes
1, 2, 3; `random.Random(f"{semente}|{curso}|{unidade}")`; 2000 tentativas; primeira permutação válida; estados
`estruturalmente_nao_informativa`, `identidade_sorteada`, `pareado`, `sem_permutacao_valida_no_orcamento`, que bloqueia).
Sem novas sementes, braços ou significância.

## N7. Avaliador (script separado e congelado antes da captura)

- **Ordem:** conferir o código do avaliador e do `comum.py` contra o congelamento, validar congelamento, entradas e
  capturas; só então ler a régua, por uma porta única com `--autorizo-gold`.
- **Proveniência da régua:** caminhos EXPLÍCITOS no congelamento, iguais aos que a resolução histórica escolhe hoje:
  `ground_truth_*` e `gold_units_*` do histórico, `material_gt` de CG e ES2 e `subunit_gt` de SO da pasta
  `wx_gold_v2_final_22-09`, o resto de `docs/reports`, e a herança `herancas_*_15-09.{csv,json}`. Cada arquivo é conferido
  pelo blob git ANTES de ser interpretado, e os bytes interpretados são os conferidos. Manifests de referência são
  conferidos pelo sha256, e os salvos pela árvore congelada.
- **Carregadores:** cópias locais identificadas (origem de cada uma no avaliador), sem importar os módulos históricos.
  Diferenças declaradas:
  - origem com mais de uma entrada no manifest salvo = erro (a histórica usava a primeira);
  - id com blocos conflitantes ou herança com destinos conflitantes = erro.
- **Régua validada:** cursos iguais ao inventário; `gold_id` único; o mesmo `eid` não pode servir a dois `gold_id`; `eid`
  dentro do inventário; tipos; primária ⊆ aceita; denominadores POR CURSO e totais:

  | curso | bloco | unidade | sub primária |
  |---|---:|---:|---:|
  | MF | 66 | 66 | 58 |
  | SO | 39 | 37 | 15 |
  | IA | 42 | 42 | 39 |
  | ES2 | 28 | 28 | 28 |
  | TCC | 27 | 18 | 11 |
  | CG | 35 | 93 | 82 |
  | FR | 0 | 0 | 18 |
  | **total** | **237** | **284** | **251** |

- **Referência do CRU por curso** (a recaptura, com a régua lida, tem de reproduzi-la; senão a avaliação é recusada):
  bloco MF 60, SO 36, IA 41, ES2 27, TCC 26, CG 33 (223); unidade MF 63, SO 30, IA 39, ES2 26, TCC 17, CG 74 (249);
  sub primária MF 25, SO 7, IA 4, ES2 7, TCC 7, CG 30, FR 6 (86).
- **Linha sem decisão de mapeamento** (gold_id ausente de `eid_de`) = erro; `eid` nulo explícito = material ausente, que
  conta como erro. Registro ausente para `eid` presente invalida a avaliação.
- **Régua histórica exata:** bloco por igualdade; unidade, primária e aceita por pertinência; `{""}` = vazio correto.
- **Rastreabilidade:** um registro por (material, eixo) é a origem de todo agregado; transições também por ID; as somas
  (células = registros = n; correções − perdas = diferença de acertos) são conferidas e a divergência recusa o resultado. O
  resultado leva a proveniência: hashes das capturas, congelamento, protocolo, avaliador, `comum.py`, taxonomias, arquivos
  da régua conferidos, mapeamento (ponte e ausentes) e hash da régua efetiva.
- **Geração:** escada por material. (a) o rótulo existe na taxonomia (com o número de ocorrências). Material ausente ou não
  chamado tem elegibilidade, score e escolha "não aplicável"; a unidade final nunca serve de premissa. (b)–(d) só entre
  os chamados, com denominador próprio; (e) final correto. Grupos e seleção no subconjunto comum como no v2.
- **Transições, precisão e meta:** como no v2 (partição por certo/vazio antes e depois e mudou; precisão sobre todas as
  alteradas, "não aplicável" com zero; meta por contagem exata).
- **Veredictos:** A: VOCAB_LLM > CRU, CTRL_MAIOR e cada aleatório na primária total. B: sem perdas e sem regressão por
  curso nos TRÊS eixos oficiais (bloco, unidade, primária); a subunidade aceita é auxiliar, relatada à parte, e não veta.
  Se A for verdadeiro e B falhar: "sinal exploratório observado; candidato reprovado para integração". C: mais de 90% por
  eixo oficial e curso avaliado.
- Nenhuma margem, limiar ou teste de significância depois dos resultados.

## N8. Autorização

`CAPTURA_LIBERADA` = {CRU}. Captura dos seis braços e leitura da régua real exigem autorização própria (Gate de
captura e Gate de avaliação); testes verdes e preflight aprovado não liberam nada automaticamente.
<!-- NORMATIVO:FIM -->

## Registro (fora do bloco normativo)

Execução em `_harness-2026-09-04/c1-3/wad4_25-09/`; detalhes em `matriz_achados_v4.md`.

- **Testes sintéticos:** 68/68 (`testes_v4.txt`). Fase vermelha contra o código v3: `testes_v4_vermelho.txt`.
- **Preflight v4, tentativa 1:** parou antes de capturar. O import do produto grava `TESSDATA_PREFIX` e o worker herdava
  o ambiente mutado. Foi corrigido com teste; a evidência está preservada.
- **Preflight v4, tentativa 2:** 23/23, saída 0, 247 s.
- **Congelamento comum:** `b3254509f4efcf700a6d5f0f5a3488c9bfb1b41f0765081f1560f48d175da8ef`. Hashes em
  `manifesto_congelamento_v4.json`.
- **CRU recapturado:** igual à referência W-AB por ID (350/0); 341 chamados e 9 não chamados (meta-materiais).
- **Carga dos 7 braços:** válida. Não houve captura completa dos seis braços nem avaliação.
