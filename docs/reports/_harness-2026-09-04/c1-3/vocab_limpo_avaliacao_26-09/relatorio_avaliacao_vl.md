# Rodada VOCAB_LIMPO — avaliação sob o protocolo congelado (26/09/2026)

**Rodada VOCAB_LIMPO avaliada sob o protocolo congelado.**

- **Autorização:** Gate de avaliação condicional do usuário (26/09), após revisão independente "APROVADO COM CONDIÇÕES".
- **Objeto:** EXATAMENTE a única geração VOCAB_LIMPO já produzida (congelamento da recompilação `62b45e38…`, capturas
  `6a0f9652…`, `protocolo_sha` `42e52218…`). Nada foi regerado, recapturado ou alterado.
- **Natureza:** recompilação limpa e rastreável sobre os mesmos sete cursos de desenvolvimento. Não é holdout, não é
  independente, não é não contaminada e não é livre de ajuste ao benchmark.
- **Pergunta:** o compilador atual, numa nova geração rastreada sobre os mesmos cursos, manteve sinal exploratório?
  **Sim (A_limpo verdadeiro). O candidato continua reprovado para integração (B_limpo falso: 13 perdas na primária).**
- **Não houve:** chamada ao Gemini, mudança em `src/`, no avaliador, na régua, nos denominadores, nos sidecars ou nas
  capturas; commit, push, PR ou merge.
- Resultado da Fase 1 intacto e não recalculado (CRU 86, VOCAB_LLM 166, VOCAB_ATUAL 171, controles ≤ 82).

Artefatos nesta pasta; espelho em `.frzero/vocab_limpo_avaliacao_26-09/espelho/` (local, ignorado pelo git).

## 1. Condições pré-gold (§§2–6): aprovadas, 98/98, antes de abrir a régua

`valida_pre_gold_vl.py` no ambiente controlado → `validacao_pre_gold_vl.json`, `log_validacao_pre_gold.txt` (saída 0).

- **Tentativa 1 reprovada por defeito do próprio verificador**, não dos artefatos: o check "nenhum segundo conjunto de
  compilação" usava o regex `compila|chamadas`, que casa `congelamento_recompilacao.json`. Evidência preservada
  (`*_tentativa1_regex.*`: log, JSON e script). O check foi trocado por um mais estrito (listagem exata dos 12 itens
  declarados da pasta + nenhum arquivo de chamada ou compilação fora de `chamadas/` em toda a árvore). Nada foi lido da
  régua entre as tentativas.
- **Manifesto geral da rodada:** 279/279 hashes = disco.
- **§2 compilação:**
  - `sha256(compilacao.json)` = `09874d90…`; `id_recompilacao` = `62b45e38…`, recalculado do normativo;
  - `completa` verdadeiro, `abortado` nulo, 0 violações;
  - 26 registros = os 26 curso/unidade do inventário (arquivo e congelamento), sem duplicata;
  - todas na tentativa 1, status ok; por curso 0 retries, 0 erros, 0 unidades com erro;
  - modelo pedido = congelado (`gemini-3.5-flash`) em todas; `model_version` registrado em todas (só `gemini-3.5-flash`);
  - nenhum segundo conjunto de compilação ou chamadas.
- **§3 requests e responses:** 52 arquivos (26 + 26), todos `t1`, nenhum `_t2_`/`_t3_` nem extra; disco = manifesto nos
  dois sentidos; cada hash = manifesto = `compilacao.json`; cada request ↔ registro ↔ inventário (curso, unidade, bundle,
  modelo, schema, system); cada response ↔ registro (`model_version`, `parsed`); 26 `response_id` distintos.
  São a serialização preservada da request e do objeto de resposta disponibilizado pelo SDK.
- **§4 sidecars:** cadeia fechada nos 7 cursos (tabela abaixo). Sem manual na pasta de sidecars, no staging, em qualquer
  palco (congelamento e disco) ou captura. Sidecars históricos intactos (= sanidade = congelamento da Fase 1). O palco do
  VOCAB_LIMPO tem o conteúdo do sidecar gerado (reserializado com `indent=1` pelo harness; hash = congelado) e difere do
  histórico.
- **Mtime (informativo):** os 7 arquivos em `sidecars/` têm mtime 04:29:55Z, 26 s depois do fim da geração. Explicação
  pela fonte: o compilador grava o sidecar no staging (mtime de cada um dentro da janela da geração, hash registrado em
  `compilacao.json`); `sanidade.py` copiou os bytes (`write_bytes(read_bytes())`) às 04:29:55Z, junto com `sanidade.json`.
  Original no staging, `compilacao.json` e cópia têm o mesmo sha256. Nenhuma edição posterior.
- **§5 capturas:** as 6 com caminho esperado, sha256 = manifesto de capturas = manifesto da rodada, `conteudo_sha`
  recalculado, validador histórico/estrutural completo, identidade (braço, modo, esquema, `id_comum`, `insumos_braco`,
  0 violações), 350 materiais = inventário, 341 chamados, os mesmos 9 não chamados, manual ausente. Diretório só com as
  6 deste congelamento; sem falhas. **CRU_LIMPO = referência W-AB por ID: 350 materiais, 0 divergências.** Código,
  intérprete, distribuições, entradas e protocolo = congelados.
- **§6 snapshots e insumos:** 42/42 (6 braços × 7 cursos) taxonomia, índice e palco = congelamento; `insumos_braco`
  recalculados = congelamento = capturas; descritor da régua sem pendências; 38 blobs da régua no índice = congelados,
  sem abrir os arquivos.

### Cadeia dos sidecars (§2 e §4): compilação = sanidade = congelamento da captura = manifesto = disco

| curso | sha256 (5 fontes idênticas) |
|---|---|
| MF | `dab47b687e00e86ece49068f731901591a9b820baf4284be2eb654e43cee1d13` |
| SO | `d355d6402e27303650e2def21ee3c131b97c1c042fc66007fc4bc55c8d5ce1d0` |
| IA | `5a46b6fb9b9d5f9931b9bbe410a3864deb984d0d34e2fa091196610f10cb7283` |
| ES2 | `e5e38cdb313a12be63d1aac80684f34891f2a723cf3f252e204c39551d122457` |
| TCC | `574d08c31a62f002e0299a490a857d71643862e988cb36eab24d62663e33e029` |
| CG | `07575d27521e7feaf83b924d001d618540718418a1ced450e9b0195e42f119cb` |
| FR | `09c747db194703a0d8c741a6328aae2437a42fd24d5c8d86bca90c8fd8ddb1b0` |

## 2. Ressalvas documentais (§7)

Registradas antes da régua em `ressalvas_revisao_vl_26-09.md`: A (resolução de hostname registrada; não é sandbox de
rede), B (controle de leituras em memória; mapa integral não persistido), C (serialização do objeto de resposta do SDK, não
bytes HTTP). Prevalecem sobre as formulações do relatório da rodada, que fica intacto por estar no manifesto.

## 3. Espelho da régua (§8)

`monta_espelho_vl.py` → `espelho_manifesto_vl.json`, `log_espelho.txt` (saída 0).

- Régua: 38 arquivos por `git cat-file blob <blob congelado>`, blob conferido antes de gravar. **Os mesmos 38 blobs da
  Fase 1.**
- Manifests: 7 de referência e 7 salvos (10 caminhos únicos), sha256 = congelamento.
- `avaliador.py` (`6799972f…`) e `comum.py` da rodada, byte a byte, = congelamento = manifesto da rodada.
- Depois de gravar, os 50 arquivos foram relidos do disco e reconferidos (blob/sha256); conjunto exato, sem extras.
- Nenhum EOL normalizado, nenhuma versão nova da régua, avaliador intocado.

## 4. Avaliação (§§9–11) e conferência (§15)

- **Execução original:** avaliador do espelho com `--autorizo-gold` → `avaliacao_vl_1.json`, sha256
  `51cc7318ee610aec74f177c1e1db4ab9833673b949e408501d2070cec495c92f` (saída 0, 1,8 s).
- **Única execução de conferência:** `avaliacao_vl_2_conferencia.json`, **byte-idêntica** (mesmo sha256).
- O próprio avaliador aplica o contrato da régua da Fase 1 e recusaria a avaliação em qualquer violação. Não recusou.
  - Na leitura: bytes = blob congelado, herança com destinos conflitantes = erro, mapeamento de `eid` com unicidade
    obrigatória.
  - Em `valida_regua`: `gold_id` único, o mesmo `eid` nunca em dois itens, `eid` no inventário, primária ⊆ aceita,
    denominadores por curso e total.
  - Em `confere_referencia_cru`: o CRU_LIMPO tem de reproduzir a referência por curso e eixo oficial.
- **Conferência independente** (`confere_resultado_vl.py` → `conferencia_resultado_vl.json`): **20/20**.
  - Placar = registros por ID; soma dos cursos = total; denominadores por curso e total = oficiais.
  - Derivadas e precisões recalculadas por ID; correções − perdas = diferença de acertos.
  - Categorias sobrepostas tratadas como sobrepostas (abstenção → certa ⊆ correção); a partição é a das células.
  - Veredictos refeitos pelos critérios literais do §12 = avaliador. A aceita não entra em B.
  - Depois da avaliação: 279 hashes do manifesto da rodada, espelho e proveniência (`id_comum`, protocolo, avaliador,
    comum, capturas, blobs conferidos) intactos.

### CRU_LIMPO reproduz a referência (§10)

| eixo | MF | SO | IA | ES2 | TCC | CG | FR | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bloco | 60/66 | 36/39 | 41/42 | 27/28 | 26/27 | 33/35 | — | **223/237** |
| unidade | 63/66 | 30/37 | 39/42 | 26/28 | 17/18 | 74/93 | — | **249/284** |
| sub primária | 25/58 | 7/15 | 4/39 | 7/28 | 7/11 | 30/82 | 6/18 | **86/251** |

## 5. Placares

**Bloco:** 223/237 em todos os seis braços, idêntico por curso. Nenhuma saída de bloco mudou.

**Unidade** (cursos iguais ao CRU_LIMPO omitidos; MF 63, SO 30, IA 39, ES2 26, TCC 17 em todos):

| braço | CG (93) | total (284) |
|---|---:|---:|
| CRU_LIMPO | 74 | 249 |
| VOCAB_LIMPO | 75 | 250 |
| CTRL_MAIOR_LIMPO | 74 | 249 |
| CTRL_ALEAT_LIMPO_1 | 75 | 250 |
| CTRL_ALEAT_LIMPO_2 | 74 | 249 |
| CTRL_ALEAT_LIMPO_3 | 75 | 250 |

**Subunidade primária (oficial):**

| braço | MF (58) | SO (15) | IA (39) | ES2 (28) | TCC (11) | CG (82) | FR (18) | total (251) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CRU_LIMPO | 25 | 7 | 4 | 7 | 7 | 30 | 6 | 86 |
| **VOCAB_LIMPO** | 43 | 10 | 36 | 17 | 8 | 44 | 16 | **174** (69,3%) |
| CTRL_MAIOR_LIMPO | 16 | 7 | 4 | 10 | 5 | 23 | 2 | 67 |
| CTRL_ALEAT_LIMPO_1 | 14 | 8 | 15 | 9 | 5 | 26 | 5 | 82 |
| CTRL_ALEAT_LIMPO_2 | 18 | 4 | 8 | 6 | 6 | 27 | 5 | 74 |
| CTRL_ALEAT_LIMPO_3 | 14 | 3 | 13 | 11 | 5 | 30 | 5 | 81 |

**Subunidade aceita (auxiliar, não veta):**

| braço | MF | SO | IA | ES2 | TCC | CG | FR | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CRU_LIMPO | 29 | 8 | 5 | 8 | 9 | 43 | 7 | 109 |
| VOCAB_LIMPO | 49 | 10 | 37 | 18 | 10 | 54 | 17 | 195 |
| CTRL_MAIOR_LIMPO | 29 | 7 | 4 | 12 | 6 | 33 | 5 | 96 |
| CTRL_ALEAT_LIMPO_1 | 17 | 8 | 15 | 10 | 8 | 32 | 6 | 96 |
| CTRL_ALEAT_LIMPO_2 | 21 | 4 | 10 | 8 | 7 | 36 | 6 | 92 |
| CTRL_ALEAT_LIMPO_3 | 21 | 3 | 15 | 12 | 7 | 40 | 5 | 103 |

Tabela completa: `placar_por_curso_vl.csv`.

## 6. Transições contra o CRU_LIMPO (por ID em `transicoes_por_id_vl.csv`)

Categorias sobrepostas, não partição.

| braço | eixo | correções | perdas | erro → outro erro | correta → outra correta | abstenção → certa | abstenção → errada | decisão → vazio | precisão, TODAS as alteradas | precisão, não vazias |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VOCAB_LIMPO | primária | 101 | **13** | 35 | 0 | 23 | 7 | 4 | **101/149** (67,8%) | 100/145 |
| VOCAB_LIMPO | aceita | 97 | 11 | 23 | 18 | 24 | 6 | 4 | 115/149 | 114/145 |
| VOCAB_LIMPO | unidade | 1 | 0 | 2 | 1 | 0 | 0 | 0 | 2/4 | 2/4 |
| VOCAB_LIMPO | bloco | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/0 |
| CTRL_MAIOR_LIMPO | primária | 8 | 27 | 70 | 0 | 2 | 31 | 0 | 8/105 | 8/105 |
| CTRL_ALEAT_LIMPO_1 | primária | 34 | 38 | 97 | 0 | 6 | 24 | 9 | 34/169 | 33/160 |
| CTRL_ALEAT_LIMPO_2 | primária | 22 | 34 | 93 | 0 | 2 | 28 | 8 | 22/149 | 21/141 |
| CTRL_ALEAT_LIMPO_3 | primária | 34 | 39 | 95 | 0 | 3 | 25 | 5 | 34/168 | 33/163 |

**VOCAB_LIMPO, primária por curso** (correções / perdas / saldo): MF 22/4/+18, SO 4/1/+3, IA 33/1/+32, ES2 14/4/+10,
TCC 2/1/+1, CG 16/2/+14, FR 10/0/+10. Nenhum curso regride.

**As 13 perdas da primária** (CRU_LIMPO certo → VOCAB_LIMPO):
- MF `exerciciosespecificacao-respostas` e `exerciciosespecificacao` (linguagens-de-especificacao-e-logicas →
  fundamentos-de-logica-de-primeira-ordem); `exerciciosisabelle` (provadores-de-teoremas →
  especificacao-de-funcoes-recursivas); `verificacaomodelos` (verificacao-de-modelos-model-checking →
  especificacao-de-propriedades-…);
- SO `2403-escalonamento-de-processos` (escalonamento → conceitos-basicos);
- IA `introducao-a-ml` (introducao-ao-aprendizado-de-maquina → paradigmas-de-aprendizado);
- ES2 `roteiro5`, `roteiro6`, `roteiro7`, `roteiro7-history-service` (estudo-de-caso-… → conceito-de-devops);
- TCC `aula-07-maquinas-de-turing-…` (maquinas-de-turing → linguagens-reconheciveis-e-decidiveis);
- CG `slab` (algoritmos-de-geometria-computacional → algoritmos-de-deteccao-e-calculo-de-interseccao);
  `pagina-com-videos-sobre-manipulacao-de-imagens-61ddde` (cores-e-tipos-de-imagens → segmentacao).

**Unidade (4 IDs alterados, todos no VOCAB_LIMPO):** CG `texturas-v3` correção (u01 → u08); CG `exercicios` e IA
`o-que-é-inteligência-artificial-…` erro → outro erro; SO `questoes-do-enade-sobre-sisop` correta → outra correta. Zero
perda de unidade (na Fase 1 o VOCAB_LLM perdia 4 e ficava em 248).

## 7. Geração e seleção (primária, VOCAB_LIMPO contra CRU_LIMPO)

Os 9 meta-materiais sem chamada ficam fora da população da subunidade, sem score inventado. Denominador da escada: 245
linhas avaliadas com gold não vazio (6 com gold vazio à parte).

| degrau | CRU_LIMPO | VOCAB_LIMPO |
|---|---:|---:|
| (a) rótulo existe na taxonomia | 245 | 245 |
| (a) elegível | 229 | 229 |
| (b) score > 0 | 137 | 205 |
| (c) score ≥ 0,05 | 119 | 203 |
| (d) escolhido na 1ª passada | 62 | 167 |
| (e) decisão final correta | 85 | 172 |

| corte | ambos | só CRU | só VOCAB | nenhum |
|---|---:|---:|---:|---:|
| > 0 | 137 | 0 | 68 | 40 |
| ≥ 0,05 | 119 | 0 | 84 | 42 |

**Seleção no subconjunto comum:**

| corte | CRU, 1ª passada | CRU, final | VOCAB, 1ª passada | VOCAB, final |
|---|---:|---:|---:|---:|
| > 0 (137) | 62 | 77 | 103 | 106 |
| ≥ 0,05 (119) | 62 | 75 | 88 | 91 |

**Estados da 1ª passada (251):** CRU decidido 177, empate 43, candidatos com score zero 22, ambígua com slug 6,
abstenção 3; VOCAB decidido 226, empate 8, score zero 3, ambígua com slug 13, abstenção 1.

## 8. Veredictos pré-registrados (§12)

- **A_limpo — VERDADEIRO.** Primária total: VOCAB_LIMPO 174 > CRU_LIMPO 86, CTRL_MAIOR_LIMPO 67, CTRL_ALEAT_LIMPO_1 82,
  _2 74, _3 81. Sinal exploratório; não é significância estatística.
- **B_limpo — NÃO ATENDIDO.** Ganho de primária positivo (+88), bloco e unidade sem perda, nenhum curso regride em
  nenhum eixo oficial, mas **13 perdas na primária** (MF 4, ES2 4, CG 2, SO 1, IA 1, TCC 1). Qualquer perda reprova.
  Texto do avaliador: "sinal exploratório observado; candidato reprovado para integração". Aceita (auxiliar): 11 perdas,
  nenhum curso regride; não entra no veredicto.
- **C_limpo — NÃO ATENDIDO** (acertos × 10 > 9 × n, por eixo e curso avaliado):
  - bloco: atinge nos 6 cursos avaliados;
  - unidade: atinge em MF, IA, ES2 e TCC; não em SO (30/37) nem CG (75/93);
  - primária: **só no IA (36/39)**; não em MF, SO, ES2, TCC, CG nem FR (16/18 = 88,9%);
  - FR sem bloco nem unidade (não aplicável).

## 9. Comparação descritiva com a Fase 1 (não é critério dos veredictos)

| braço | bloco | unidade | primária | aceita | correções / perdas na primária | precisão, todas as alteradas |
|---|---:|---:|---:|---:|---:|---:|
| VOCAB_LLM histórico (Fase 1) | 223 | 248 | 166 | 190 | 87 / 7 | 87/124 |
| VOCAB_ATUAL (proveniência mista) | 223 | 251 | 171 | 197 | — | — |
| **VOCAB_LIMPO** | 223 | 250 | **174** | 195 | 101 / 13 | 101/149 |
| controles Fase 1 | 223 | 248–249 | 67–82 | 84–110 | — | — |
| controles limpos | 223 | 249–250 | 67–82 | 92–103 | — | — |

- Primária por curso, VOCAB_LLM → VOCAB_LIMPO: MF 38 → 43, SO 11 → 10, IA 36 → 36, ES2 18 → 17, TCC 9 → 8, CG 38 → 44,
  FR 16 → 16.
- **As 7 perdas do VOCAB_LLM reaparecem entre as 13 do VOCAB_LIMPO** (MF `exerciciosisabelle`; ES2 `roteiro5/6/7` e
  `roteiro7-history-service`; CG `slab` e `pagina-com-videos-…`), em alguns casos com outro tópico de destino. As 6
  novas: MF 3, SO 1, IA 1, TCC 1. A causa não foi isolada.
- A nova geração difere bastante do histórico nos termos (Jaccard médio por tópico entre 0,10 e 0,69) e chega a um
  placar próximo. Isso não demonstra generalização: os sete cursos são os de desenvolvimento, e o prompt tem ajuste
  histórico neles.

## 10. Limitações

- **Cursos contaminados:** mesmos sete cursos de desenvolvimento; prompt calibrado historicamente no IA. Sem holdout,
  independência, ausência de overfitting histórico ou generalização.
- **Modelo:** alias `gemini-3.5-flash` sem versão imutável; parâmetros de geração nos defaults do serviço; sem semente.
  Uma geração, sem escolha; não reprodutível por nova chamada.
- **Agrupamento:** unidades de agrupamento vindas do CRU (diferença deliberada em relação à compilação histórica); a
  chamada IA u05 cortada nos 24.000 caracteres do produto.
- **Rede, leituras, response:** ressalvas A, B e C (§2 deste relatório).
- **Controles:** 3 sementes aleatórias e 1 controle "maior"; o sinal exploratório A não é teste estatístico.
- **Unidade:** a correção de unidade CG `texturas-v3` aparece nos quatro controles também (em CTRL_MAIOR_LIMPO e
  CTRL_ALEAT_LIMPO_2 compensada pela perda de CG `opengl-cpp`); não é atribuível ao vocabulário gerado.
- **Gold visto:** a partir desta avaliação a régua da rodada foi exposta. Qualquer ajuste de prompt, filtro, alias ou
  seleção dirigido pelas perdas acima fica contaminado e exige Gate novo.
- **Verificador pré-gold:** a tentativa 1 falhou por regex do próprio check (preservada); não houve leitura de régua
  entre as tentativas.

## 11. Próxima decisão recomendada (não executada)

1. **Gate 2 documental** para preservar em commit os artefatos das Fases 1 e limpa (sem conteúdo acadêmico bruto),
   antes de qualquer frente nova.
2. **Validação em cursos novos, nunca vistos**, com o compilador atual congelado e o mesmo protocolo, como próxima
   medição. É o único passo que responde à generalização; mais rodadas nos sete cursos não respondem.
3. Diagnóstico das perdas recorrentes (7 de 7 da Fase 1 reaparecem) só como pesquisa com Gate próprio, registrando que
   o gold já foi visto. Não abrir compilador v2 nem integração no produto antes disso.

## 12. Estado final do worktree

- HEAD `2589ed5a`, sem commit; `src/` e `tests/` sem diff.
- Novos, não versionados: esta pasta `c1-3/vocab_limpo_avaliacao_26-09/`; `.frzero/vocab_limpo_avaliacao_26-09/`
  (espelho, ignorado pelo git).
- Atualizados, não staged: `docs/reports/pendencias.md` (entrada da rodada) e o estado local da frente.
- Index, stashes e alterações alheias preservados.
