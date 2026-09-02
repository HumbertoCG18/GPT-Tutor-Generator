# Plano 2026-09-02 — FECHAR O MOTOR: teto estrutural + vocabulario compilado + LLM residual + humano so na duvida

**Origem:** conversa de 01/09 noite -> 02/09 madrugada (sessao dbdc7a63). Numeros-base em
`pendencias.md` ("MOTOR PURO — o numero honesto") e no artifact "Anatomia do Bloco"
(https://claude.ai/code/artifact/ba1de7bf-a802-49fc-b88b-6be358d4b796). Este documento e a FILA
EXECUTAVEL das proximas sessoes; o handoff `2026-09-01d` continua valido para contexto.

## Decisoes do user (02/09, registradas — nao reperguntar)
1. **Pronto** = leitura MINIMA de uma secao de revisao no projeto da cadeira (UI a definir); o aluno
   poe os arquivos, eles se organizam, e ele revisa SO o que o motor marcou como duvida.
2. **LLM**: aceito UMA vez por curso, no build ou no reprocess quando necessario (compilar vocabulario).
3. **Cronograma MANDA sobre a ordem do plano**: o plano diz O QUE se estuda; o cronograma diz a ORDEM,
   e o professor muda a ordem todo semestre. Unidade do bloco segue o cronograma (explicito ou por
   ancora), nunca a monotonia do plano.
4. **Subunidade**: nem todo material precisa ter; multi-tema pode ir ao LLM. Modelo provavel:
   **principal + extras** (confirmar na Fase 4 com dado).
5. **Entradas**: SARC + Moodle + plano em ~95%; o motor tambem le cronograma vindo de ARQUIVO (caminho
   PDF do CG ja existe). `posting_date` (timemodified do Moodle) e SINAL MORTO: 19-21% no gold, CG nem
   tem. Nao usar.
6. **Datalab fica** (md e o caminho de menor consumo de tokens no uso do tutor).
7. **Reutilizar o maximo**: nada de recomecar do zero, salvo se for REALMENTE necessario e matar o
   problema de vez. Veredito: NAO e necessario para as fases 1-4 (a unificacao acontece no dado —
   `topic.aliases` — que as 4 rotas ja leem). Gatilho para o montador unico: uma correcao que precise
   ser refeita em 2 rotas depois da Fase 3.
8. **Vocabulario por LLM**: teste real de precisao/qualidade antes de confiar (Fase 1c).

## Leis (inalteradas) + regua dupla
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · pinar menos · gate: eixos
+ subunit_gt + pytest + sentinela + determinismo + ablacao nu/curado **+ motor puro** (`motor_puro.py`
promovido a `scripts/`) · nada regride em NENHUMA das duas reguas · commits com trailers · [Humberto].
Licao 01/09d: rota de bloco quer sinal ESTRUTURAL; texto semantico espalha (resumo Gemini refutado).

## Alvos por eixo (motor puro -> com LLM residual)
| eixo | hoje puro | alvo puro | com LLM residual | teto conhecido |
|---|---|---|---|---|
| bloco | 158/200 (+4 meta) | ~178/200 | ~198/200 | `azure` (convencao) |
| unidade | 154/191 | ~180/191 | ~190/191 | segue o bloco |
| cobertura | 51/57 | 54/57 | 56/57 | `aws` (teto documentado) |
| subunidade | 26/93 | >= 80/93 (vocab compilado) | ~90/93 primario | tese-vs-instrumento -> LLM multi-tema |
Metrica de PRODUTO (run real, sem gold): **itens "revisar" por 100 materiais** e **votos de LLM por 100
materiais**. Hoje: 33 votos/100 no bloco; "revisar" nao e contado ainda.

---

## FASE 0 — regua e fila de duvidas (1 sessao curta)
**FEITA (02/09, sessao 3)** — ver `pendencias.md` §FASE 0: baseline curada 55.7/100 e motor puro 54.0/100; gatilhos calibrados no gold (conflito 56%, flag:disamb 63%, sem-bloco 100%; janela-1 27% e sub-ambigua 22% sao os fracos). Definicao = decisao B, sem ajuste — o ajuste espera o dado da run FR.
Reuso: `scratchpad/motor_puro.py`, campos `temporal_block_flag`/band, `subunit_match_reasons`
("ambiguous", "empate-exato", "sem-sinal"), `unit_block_conflict`, `manual_review`.
- Promover `motor_puro.py` a `scripts/motor_puro.py` (copias nu + voter OFF + 4 eixos + subunidade).
- Definir `revisar` como CAMPO DERIVADO do manifest (funcao pura, testada): bloco flagado OU sem bloco
  OU subunidade ambigua/empate com >= 2 candidatos fortes OU conflito unidade x bloco. Sem UI ainda —
  a UI (secao de revisao no projeto da cadeira) vem depois e le esse campo.
- `censo_motor_llm.py` -> `scripts/` com a linha "revisar por 100 materiais".
Gate: nenhum (so leitura). Entrega: baseline oficial das 3 metricas nos 8 cursos.

## FASE 1 — vocabulario por curso sem mao (2-3 sessoes) — O MAIOR BURACO
Reuso: heading-enrichment em `content_taxonomy.py` (~600, `_select_supported_taxonomy_topic`,
`heading_sources`), loader/formato de `.glossary_curation.json` (`repo.py` 1649, formato
`{"<Termo>": {"synonyms": [...]}}`), `merge_glossary_synonyms`, client Gemini (`get_gemini_client`),
padrao `summarize_bundle` + schema pydantic (`run_material_residual`).

**1a. Co-heading (deterministico) — medir primeiro.**
- Regra: documento cujo TITULO ou 1o heading e suportado por T (mesmo teste de suporte de hoje) doa os
  DEMAIS headings dele como aliases de T. Filtros: (i) exclusividade — heading que aparece em documentos
  de mais de 1 topico nao doa; (ii) genericos do curso (A2/df) e nome do curso fora; (iii) heading com
  >= 2 tokens especificos (1 token solto e ruido); (iv) so materiais em escopo (nao meta/prova).
- Onde: mesma passada de `heading_sources` em `content_taxonomy.py`; nova funcao pequena ao lado.
- Medicao: taxonomia reconstruida SEM os 4 sidecars manuais (copias .ablacao) -> subunidade nos 93 em
  motor puro. Baseline 26/93. Tambem: quantos aliases/curso nasceram e amostra de 20 para olhar.
- Criterio: >= 60/93 = co-heading vira base e o LLM compila so o resto; < 40/93 = co-heading fica como
  camada (se nao regredir) e o LLM compila tudo.
**1b. Compilacao por LLM (1x por curso).**
- Passo novo no build/reprocess: `compile_course_vocabulary(root)`: para cada topico SEM termo exclusivo
  apos plano + co-heading + rotulos de sessao do SARC, UMA chamada por UNIDADE (nao por topico) com
  prompt ANCORADO: plano da unidade (labels dos topicos) + headings dos materiais ja atribuidos a blocos
  daquela unidade (estrutura, nao semantica) -> schema `{topico: [sinonimos]}`. Grava no MESMO
  `.glossary_curation.json`, com `"_provenance": "llm"` por termo. Se o arquivo existe, NAO chama (cache
  = o proprio sidecar; reprocess so recompila com flag explicita).
- Termos manuais existentes (SO/IA/ES2/TCC) NAO sao sobrescritos; viram referencia do teste 1c.
**1c. Teste real de qualidade (decisao 8 do user).**
- IA (tem sidecar manual = referencia): compilar em copia SEM o manual; comparar termo a termo (precisao =
  termos do LLM que estao no manual ou casam material da unidade; cobertura = termos do manual que o LLM
  achou); subunidade nos 39 do gold com o sidecar do LLM vs 39/39 do manual.
- FR (holdout, sem sidecar): compilar; user le o sidecar (20 entries) e marca certo/errado; subunidade
  passa a taggar > 12/20? `02-modelos` e `06-dhcp` seguem certos?
- Criterio para confiar: precisao >= 80% nos termos e subunidade IA >= 35/39. Abaixo: prompt ancorado
  demais/de menos — ajustar 1x; se nao, LLM so propoe e o humano aprova (volta a curadoria, so que
  assistida).
Gate da fase: curado 93/93 intacto (sidecars manuais seguem la), motor puro sobe, 8 cursos com sidecar
(4 manuais + 4 compilados: CG, FR, LR, MF), sentinela mostra SO taggagens novas em CG/FR/LR/MF.

## FASE 2 — cronograma manda na unidade do bloco (1 sessao)
Reuso: `unit_matcher.py` (ancoras ANCHOR_MIN_MARGIN/STRONG_MARGIN, CONF_*), `_timeline_unit_number_from_text`
(ja le "Conteudo: unidade-01"/"U1"), `assign_units_around_pins`.
- Hierarquia nova: (1) unidade EXPLICITA na linha do cronograma = ancora de 1a classe (conf 0,9);
  (2) ancora lexica forte (margem >= STRONG) = 0,8; (3) ancora normal = 0,6; (4) DP monotonico so
  PREENCHE entre ancoras (fill 0,4), sem limite de desvios — as ancoras podem ser nao-monotonicas
  porque o cronograma manda. `DETOUR_*` some (era a gambiarra da monotonia).
- Medicao: curado 191/191 intacto (obrigatorio) · nu 170/191 -> ? · CG blocos 13/15 -> u07 (eyeball) ·
  sentinela nos 8.
- Risco: ancora lexica ESPURIA de 1 token virando dona de bloco — o filtro "margem >= 1" ja existe;
  medir confiante-errado.

## FASE 3 — bloco estrutural (1-2 sessoes)
Reuso: cascata `_CASCADE` em `window_provider.py`, `_block_named_in_title` (R3), `resolve_exam_prep`,
`_sibling_key`/`_inherit_from_numbered_sibling`, `detect_same_theme_series`.
- **provider_title**: titulo/moodle_label contem TODOS os tokens do topico de exatamente 1 bloco -> janela
  [bloco] (R3 promovido a provider; hoje so age dentro de janela). Alvo: ~9 funis (CG listas, SO enade).
- **provider_series_ordinal**: membros de serie numerada (mesmo card, mesmo radical, numeros 1..n) com
  janela do card de m blocos-aula; se n <= m, membro k -> k-esimo bloco da janela. Premissa medida antes
  no gold (ES2 microsservicos1..7, roteiroN-tema, MF recursao1..3). Se n > m: nao age.
- **prova antiga** (ano no id < ano do calendario) -> `resolve_exam_prep` mesmo com lexical=False.
- **serie confiante nao vota** SO depois do provider de serie existir (senao −1 gold: dafny2).
- Alvo: motor puro bloco 158 -> ~178; votos 33 -> ~12 por 100.

## FASE 4 — LLM residual, cacheado, contado (1 sessao)
Reuso: `LlmVoter` + `material_curation.json` + cap + `round_summary`.
- Bloco: como hoje (so flagado).
- Subunidade multi-tema (decisao 4): quando cobertura N:N >= 2 unidades OU scorer em empate/ambiguo com
  >= 2 candidatos fortes -> LLM escolhe principal (+ extras), grava no mesmo sidecar, conta. Modelo
  **principal + extras** (campo novo `computed_subunit_extras`, lista) — confirmar com o dado dos 2
  tetos (`aula-08`, `roteiro5-conteiners`) e do gold (extras ja existem la).
- Relatorio: votos por 100 materiais (bloco e subunidade) no CRONOGRAMA_HEALTH.

## FASE 5 — run real CG + FR (1 sessao + revisao do user)
Protocolo do handoff 01d: build do zero, zero curadoria, summaries ON, vocabulario compilado, voter ON
com cap e contagem, watchdogs; o user revisa a lista "revisar" (nao o FILE_MAP inteiro) e cada correcao
vira gold-por-fenomeno. Videos do CG: fora. Cronograma do CG vem de arquivo (ja suportado).

## Pergunta pendente (unica)
**Voto do LLM e "duvida resolvida" ou "duvida a confirmar"?** Hoje o voto entra com band media e flag
LIMPA (aceitacao cega). Para a secao de revisao: itens decididos por LLM aparecem como "decidido por
LLM — confira" (mais itens, mais seguro) ou ficam fora (menos itens, o LLM erra ~2%)? Isso define o
tamanho da lista que o aluno ve. Sugestao: aparecem, mas em grupo separado e colapsado.

---

## REFACTOR — veredito (02/09, decisao do user: registrar)
Divida medida: 77 scripts · motor/roteamento ~9.700 linhas em 21 modulos (`timeline/index.py` 2.243,
`file_map.py` 1.440 + copia paralela em `facade/`) · 10 funcoes tokenizadoras (`_toks`, 3x `_tokens`,
`entry_tokens`, `_topic_tokens`, 2x `_stems`, `_topic_support_tokens`, `_tokens_distintivos`,
`_timeline_specific_tokens`) · 21 limiares (9 em `T`, 12 soltos).
**Reescrever o motor: NAO** — nao mata nenhum dos 3 problemas medidos (sinal estrutural, vocabulario,
premissa de monotonia) e arrisca os 199/200. **Consolidacao dirigida em 4 cortes, cada um com gate
"0 campos" na sentinela dos 8: SIM**, intercalada nas fases:
1. `scripts/` 77 -> ~25: `eval/` (reguas oficiais), `watchdogs/`, `ops/` (build/reprocess/pull), arquivar
   one-offs. Risco zero. Pode ser a proxima sessao curta.
2. Limiares soltos -> `T` (movimento puro, meia sessao).
3. Um tokenizador (`text/tokens.py`), estrategia strangler: cada rota chama a funcao unica COM OS SEUS
   parametros atuais (byte-identico, sentinela 0), depois converge parametro a parametro com regua dupla.
   Entra DEPOIS da Fase 1a (a medicao do co-heading define a interface).
4. `timeline/index.py` -> 3 modulos (blocos / scorer de topico / periodos). Ultimo; so navegabilidade.
NAO unificar: os providers de janela — cada um e regra medida no gold; unifica-se a tokenizacao deles.
Candidato a REMOCAO (decidir): `concept_resolver.py` (487 linhas) — o bloco "concept-fused" e sobreposto
pelo temporal em todo entry (`explain_entry` [2] -> resolve_temporal_block SOBREPOE); medir se alguem
ainda consome `computed_block_id` antes de apagar.

## DECISOES EM ABERTO (revisao do plano, 02/09) — na ordem em que travam uma fase
A. **CONTRADICAO a resolver (trava Fase 0/5):** o plano diz "cada correcao vira gold-por-fenomeno, NAO
   pino" — mas uma correcao que nao e aplicada nao muda o que o aluno ve. Proposta: correcao na secao de
   revisao faz AS DUAS coisas — grava override (os campos `manual_*` que ja existem) E registra a linha de
   gold com proveniencia; o motor puro mede sem os overrides. "Pinar menos" passa a significar "o motor
   precisa de menos correcoes", nao "correcoes nao existem".
B. **Voto do LLM na secao de revisao** (trava a definicao de `revisar`, Fase 0): aparece como "decidido
   por LLM — confira" (grupo separado, colapsado) ou fica fora? Sugestao: aparece.
C. **Criterios numericos da Fase 1** (confirmar): co-heading >= 60/93 vira base / < 40 o LLM compila tudo;
   vocabulario por LLM confiavel se precisao >= 80% dos termos e IA >= 35/39; abaixo, LLM propoe e humano
   aprova (curadoria assistida).
D. **Recompilar vocabulario**: gatilho = flag explicita no reprocess (CLI) hoje; botao na UI depois. OK?
E. **Periodos de unidade nao-contiguos (Fase 2):** com o cronograma mandando, u06 pode ter 2 periodos
   (antes e depois de u07 no CG). `_aggregate_unit_periods_from_blocks` hoje colapsa em min/max — decidir
   se COURSE_MAP/SYLLABUS mostram lista de periodos ou o envelope.
F. **Modelo de subunidade multi-tema (Fase 4):** principal + extras (campo `computed_subunit_extras`) —
   confirmar com os 2 tetos e o gold; e o tutor mostra extras?
G. **Ordem da run real (Fase 5):** FR primeiro (20 entries, SARC com cores, sem video, so precisa da
   Fase 1) e CG depois (precisa da Fase 2)? Sugestao: sim.
H. **`concept_resolver`**: manter ou retirar (ver acima). Medir consumidores antes.
I. **Definicao de "candidato forte"** para acionar o LLM na subunidade (Fase 4): score >= X do vencedor?
   Define-se com o dado dos 93 na hora — so registrar que e decisao de medicao, nao de opiniao.

## DECISOES FECHADAS (02/09, uma a uma)
- **A** (aceita): correcao na secao de revisao = override nos `manual_*` existentes E linha de gold com
  proveniencia; motor puro mede sem overrides; "pinar menos" = o motor precisa de menos correcoes.
- **B** (aceita): `revisar` = enum {duvida, llm, ok}. Camada 1 aberta (sem bloco, llm-funil, subunidade
  ambigua, conflito), camada 2 colapsada "decidido por LLM — confira" (LLM-na-janela), camada 3 nao aparece.
  Metrica = camadas 1+2 por 100 materiais.
- **C — MEDIDA (02/09 madrugada), nao mais opiniao:**
  - Co-heading (`scratchpad/coheading.py`, harness validado: nu=26 reproduz o motor puro, manual=83/83):
    variante A (tese por titulo/1o heading) **26 -> 31**; variante B (tese por frase do label no corpo)
    **26 -> 29**. REFUTADO: IA tem 1 documento com tese detectavel — reconhecer que o doc e sobre T exige
    o vocabulario que se quer aprender (ovo e galinha). O dado do curso nao contem "k-NN e modelo
    preditivo" em forma que token leia. Pela regua (< 40): **o LLM compila tudo**; co-heading descartado.
  - Vocabulario por LLM (`scratchpad/compila_vocab_v2.py`, gemini-3.5-flash, 1 chamada por unidade COM
    material; o LLM so classifica titulos/headings/lead dos materiais da unidade nos topicos do plano,
    nao inventa; pos-filtro de exclusividade): **IA 5 -> 34/39 (v1) -> 37/39 (v2 = +titulos, variantes,
    lead 300 chars; o unico ajuste de prompt permitido)** vs manual 39/39 (1 das 2 faltas e rota de
    codigo). Precisao no verificavel (u05) ~80%; os ✗ sao lacunas da referencia ("Mapa auto-organizavel"
    E descritivo). **FR: taggados 12 -> 17/19**; `05-protocolo-dns` corrige para infraestrutura,
    `01-protocolos-de-rede` para conceito-de-protocolo, listas e exemplos ganham tag; `04-camada-de-
    aplicacao` vira vazio honesto (multi-topico). Compilados salvos em `docs/reports/2026-09-02-vocab-
    llm-{IA,FR}.json`. **Pendente: o user le o de FR e marca certo/errado (>= 80% = confia).** Lixo
    visivel a filtrar no compile: nomes de ARQUIVO como termo (`tcp_chat_c`, `udp_example_java`).
  - Consequencia para a Fase 1: 1a (co-heading) SAI; 1b vira `compile_course_vocabulary` com o prompt v2
    + filtro de nome-de-arquivo; 1c = teste do FR pelo user + gate curado/motor puro nos 8.
- **C — APROVADA pelo user (02/09):** FR lido e aceito; os 4 nomes de arquivo (`tcp_chat_c`,
  `tcp_example`, `udp_example_c`, `udp_example_java`) riscados do compilado. Regra que nasce disso para o
  `compile_course_vocabulary`: termo cujo normalizado e igual ao id/titulo de um arquivo do curso NAO
  vira alias (nome de arquivo e identidade, nao conhecimento; os TOKENS do nome ja contam via
  title_text/raw_text). Observacao para a Fase 3 (medir antes): empate entre topico e seu SUBTOPICO
  ("Protocolo TCP" x "Controle de congestionamento TCP", caso `tcp-example`) deveria cair no pai; hoje o
  scorer da +0,04 ao subtopico.
- **D a I: PARADAS a pedido do user (02/09).** Retomar na proxima sessao a partir de D.

## ESTADO ao parar (02/09 madrugada)
Gerador local ate este commit (nao pushed): `e6f847f` `98e3536` `a9687d3` `f166c4e` `bb3a7ec` `aab91a5`
`413ee1e` `9383c84` `097cc52` + este. Tutores: 8 commitados com o reprocess do meta-generica. Copias
`.ablacao`: SO/ES2/TCC em estado nu+voter, IA em motor puro — a proxima `ablacao_rapida` re-sincroniza.
Scratchpad da sessao (promover na Fase 0): `motor_puro.py`, `censo_motor_llm.py`, `disseca_llm.py`,
`coheading.py` (refutado, guardar como prova), `compila_vocab_v2.py` (base do 1b), `sem_llm.py`,
`projeta_regua.py`, `placar_devops.py`.
- **G — fechada (02/09):** run real = **FR primeiro** (so precisa da Fase 1), **CG depois** (precisa da
  Fase 2). Ordena as fases: 0 -> 1 -> run FR -> 2 -> 3 -> 4 -> run CG.
- **D — fechada (02/09):** recompilar vocabulario = flag explicita no reprocess (CLI) por enquanto; botao
  na UI quando a secao de revisao existir. Sem flag, o sidecar existente e cache.
- **E, F, H, I — deliberadamente adiadas (decisao do user 02/09):** decidem-se com o dado da fase que as
  produz (E: Fase 2 nos 8 · F: Fase 4 nos 2 tetos + gold · H: medicao de consumidores de
  `computed_block_id` · I: sweep nos 93). Opinar antes seria o vicio que a campanha combate.
