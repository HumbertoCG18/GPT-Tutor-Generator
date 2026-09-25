# Regime separado VOCAB para a subunidade — desenho, sem execução (24/09/2026)

Pedido do usuário em 24/09, depois da publicação do teto do cru (`2026-09-24-teto-regime-cru.md`): desenhar um regime
separado, com sinal novo para a subunidade, decisão própria e guarda contra ajuste ao benchmark. **Nada foi executado.** O
cru publicado não muda; este regime é medido e decidido à parte.

## 1. Por que este sinal

- O teto do cru esbarra numa relação que o pacote do professor não traz: vocabulário do material (algoritmos,
  ferramentas, termos em inglês) → rótulo-categoria do plano (W-Z2 §6; teto `2026-09-24-teto-regime-cru.md` §3).
- O único caminho que já **forneceu** essa relação e moveu o placar foi o vocabulário compilado por LLM:
  - braço V (13/09): +18 termos em 2 tópicos do IA levaram o IA de 5/39 a 38/39, com 0 regressão;
  - FR construído do zero: 6/18 → 16/18;
  - regime VOCAB inteiro (12/09): subunidade aceita 220/251, contra 142 no cru da época.
  Esses números são da régua v1 e de outra base; **não se comparam com o placar de hoje**.
- O caminho de conhecimento externo sem LLM (ConceptNet) foi reprovado em 23/09 (86 → 77). O próprio relatório pede uma
  fonte com sentidos de domínio explícitos.
- O que o usuário já decidiu e não se reabre: LLM/API são opcionais no produto; embedding conta como LLM; a máquina é fraca
  (nada de modelo local pesado); rotulação pelo professor não volta.

## 2. O que existe hoje (inventário, 24/09)

- **Compilador:** `src/builder/core/vocabulary_compile.py` (273 linhas), chamado por
  `ops/pedagogical_regeneration.py:_run_vocabulary_compile_layer`.
  - Opt-in pela flag de curso `compile_vocabulary`, ligada nos 8 perfis; `recompile_vocab` e `refilter_vocab` como
    opções; `TUTOR_NO_VOCAB_COMPILE=1` desliga.
  - Faz cerca de 1 chamada Gemini por unidade e grava `course/.glossary_curation.llm.json`, com `_provenance`, `_modelo`,
    `_nota` e `_raw`.
- **Sidecars LLM** nos tutores: CG 22 tópicos/83 termos, ES2 13/60, FR 8/53, IA 15/80, LR 3/8, MF 17/81, SO 17/99,
  TCC 19/96.
- **Sidecars manuais** (`.glossary_curation.json`): CG 4/5, ES2 2/22, IA 2/21, SO 4/11, TCC 3/7. **Proveniência mista:** o
  tracker (12–13/09) registra entradas escolhidas medindo contra a régua, como ES2 `gateway`, CG curvas, o pino de
  OpenGL e o veto do SO. O loader funde os dois arquivos.
- **Defeitos do compilador, registrados em 13/09** (linhas daquela data; conferidas em 24/09 as de `:226` e `:246`):
  1. o arquivo manual bloqueia toda a compilação (`vocabulary_compile.py:227`);
  2. o cache é a mera existência do arquivo, sem chave de conteúdo (`:230`);
  3. sem unidade prevista, não compila (`:245`), e a unidade prevista exclui destinos (`:240-261`);
  4. `_raw` não guarda o bundle, a citação nem a versão do prompt (`:197`).
- **Desenho v2 proposto em 13/09 e não implementado:** a unidade adquirida deixa de ser a palavra e passa a ser uma relação
  com evidência, `{term, topic_key, relation, evidence:[{entry_id, field, quote}]}`. A unidade prevista organiza os lotes,
  mas não exclui destinos. Termo compartilhado fica pendente.

## 3. Contrato proposto do regime

1. **Sinal:** relação termo → tópico compilada por LLM (Gemini via `google-genai`, com imports lazy), uma vez por curso,
   com versão de prompt e de modelo e cache por chave de conteúdo. Temperatura 0, bundle e resposta brutos guardados.
2. **Sem benchmark na cadeia:**
   - nenhum gold, régua ou erro medido entra no prompt, na escolha de tópicos ou na filtragem;
   - o sidecar manual de proveniência mista fica **em quarentena** no regime; só entra, se entrar, como braço à parte;
   - nada por curso, arquivo ou ID.
3. **Congelamento:** os sidecars do regime são gerados, recebem sha256 e ficam congelados antes de qualquer avaliação. A
   geração precisa de rede e é um passo separado e auditado; a medição roda offline sobre os sidecars congelados.
4. **Geração separada da seleção** (lição do piloto de 23/09): mede-se primeiro quanto o regime põe o gold entre os
   candidatos. Só depois, a seleção e a 2ª passada. Na 2ª passada, a elegibilidade para doar vocabulário é informada à
   parte.
5. **Integração:** pelo canal de aliases que já existe (sem campo novo); a taxonomia alimenta também a unidade, então os
   três eixos são medidos.

## 4. Medição proposta (pré-registro; cada fase com Gate próprio)

**Fase 1 — remedir o que existe, sem mudar `src`.** Replays reais na régua v2 congelada, gold só depois do congelamento:

| braço | vocabulário | para quê |
|---|---|---|
| CRU | nenhum (base atual: 223 / 249 / 86) | referência |
| VOCAB-atual | sidecars LLM + manuais de hoje | número do produto atual na régua v2, com proveniência mista declarada |
| VOCAB-LLM | só os sidecars LLM de hoje (manual em quarentena) | isola o efeito do LLM |
| VOCAB-limpo | recompilação limpa com o compilador atual (prompt versionado, sem manual) | regime reproduzível; exige rede, com autorização |
| controle "maior unidade" | termos do LLM atribuídos ao tópico com mais materiais da unidade | separa relação real de reforço da classe majoritária |
| controle aleatório | mesmos termos em tópicos sorteados da unidade, sementes fixas | piso do acaso |

Métricas: bloco, unidade e subunidade primária e aceita, por curso; ganhos e perdas por ID; precisão das decisões
alteradas; geração (gold entre os candidatos) separada da seleção; efeito da 2ª passada.

**Fase 2 — compilador v2 (relação com evidência).** Mudança em `src`, com Gate 1 próprio e só se a fase 1 mostrar que
VOCAB-limpo supera claramente os controles. Inclui a ablação obrigatória de 13/09: adição × substituição dos aliases
auto-doados (`content_taxonomy.py`, citado em 13/09 na linha 603; hoje deslocado).

**Validação da generalização.** Os 7 cursos estão contaminados: já foram vistos com gold e têm entradas manuais escolhidas
pelo benchmark. Medir neles serve de diagnóstico, não de prova. Para afirmar que o regime passa de 90% num curso novo, o
cálculo de 13/09 pede cerca de 300 materiais em 6 cursos novos: 279/300 (93%) passa no teste unilateral contra 90%; 270/300
só atinge a meta pontual. O gold desses cursos serve só para avaliar; não é rotulação no produto.

## 5. Aceite do regime (proposto)

- A meta é a mesma do marco: mais de 90% por eixo e por curso.
- Até lá, VOCAB-limpo precisa superar o CRU e os dois controles na subunidade primária, sem piorar bloco nem unidade.
- A fase 2 só é aberta se VOCAB-limpo tiver saldo positivo, nenhum curso regredindo e ganho acima do controle "maior
  unidade".
- Relatar sempre, por curso: abstenções, ausentes no denominador e decisões alteradas com precisão.

## 6. Riscos

- **Contaminação:** o viés das escolhas manuais pode se misturar ao efeito do LLM. A quarentena e o braço VOCAB-LLM isolam
  isso.
- **Relação certa × termo reconhecido:** o termo pode apontar o tópico errado (`crossover` em busca × otimização).
  Controles e precisão por decisão.
- **Não determinismo e deriva de modelo:** mitigados por prompt e modelo versionados, bundle e resposta guardados e
  congelamento por sha.
- **Custo e rede:** por volta de 50 chamadas por recompilação dos 7 cursos (1 por unidade). É passo separado, fora do
  harness, que continua offline.
- **Amostra pequena:** FR (18) e LR (6) validam o procedimento, não a acurácia.

## 7. Decisões do usuário antes de qualquer execução

1. Aceitar o vocabulário compilado por LLM como regime separado, rotulado e opcional no produto, e não como o cru.
2. Autorizar a fase 1 sem rede (CRU, VOCAB-atual, VOCAB-LLM e os controles sobre os sidecars existentes).
3. Autorizar, à parte, a recompilação limpa (VOCAB-limpo): rede, chamadas Gemini e orçamento.
4. Destino dos sidecars manuais de proveniência mista no produto: manter, pôr em quarentena ou remover.
5. Validação em cursos novos: se, quais e quem anota o gold de avaliação.

**Decisões do usuário (24/09):**
1. Regime aceito como separado, rotulado e opcional.
2. Fase 1 autorizada: sem rede e sem `src`.
3. VOCAB-limpo só depois da Fase 1, com nova autorização.
4. Sidecars manuais mantidos no produto; no regime ficam em quarentena e entram só no braço VOCAB-atual.
5. Validação em cursos novos: não decidida.
