# Handoff — rumo aos 100% nos três eixos (bloco · unidade · subunidade)

Sessão `a109e4cc` — **20/08 (noite) → 21/08**. Continua a campanha do motor; **substitui**
`2026-08-20-handoff-fechamento-campanha-motor.md` como estado corrente. Tracker vivo: `pendencias.md`
(seções `2026-08-20e` … `2026-08-21e`).

---

## Boot da nova sessão

1. Ler este arquivo inteiro. Depois `pendencias.md`, seções datadas 2026-08-21 (B-1…B-6, D-1…D-5,
   U-1, K-1…K-3).
2. `python scripts/eval_eixos.py` — a régua dos três eixos pelo estado gravado. Tem que imprimir
   **bloco 186/200 · unidade 178/188 · cobertura 46/57 F1 0,847 · pinos 11**. Se não bater, alguém
   reprocessou com código diferente — `git log` nos 5 repos-tutor antes de qualquer coisa.
3. `git status` nos 6 repos: **tudo commitado**, árvores limpas. No gerador, `07c95dc` é o commit
   deste handoff; HEAD pode estar à frente por commits **só de `docs/`** — isso não é deriva de
   estado, confira com `git log --oneline 07c95dc..HEAD --name-only`. Repos-tutor: MF `0e5d6d6` · SO `a86cd7c` · IA `def08ba` · ES2 `460c997` · TCC `5a4eb53`.
   **Push (24/08):** gerador, MF, IA e TCC estão sincronizados com `origin`. **SO e ES2 não têm
   remote nenhum** (`git remote -v` vazio) — existem só em disco local, sem backup. Criar os repos
   e ligar o `origin` é decisão do user (visibilidade pública/privada); não foi feito.
4. Suíte: `python -m pytest -q` → **2002 passed / 1 skipped**. Sentinelas (`tests/_golden/`) estão
   regravadas para o estado atual.
5. **NÃO reprocessar sem motivo.** Reprocess é ponto fixo; mas o voto do LLM varia entre rodadas
   (cache congela o primeiro) e a ordem de chaves do JSON alterna — diff de manifest ≠ mudança.

---

## As leis desta campanha (o user as fixou; não negociar)

1. **Dado real antes de código.** Toda hipótese vira medição antes de virar patch. Nesta sessão
   **9 hipóteses foram refutadas pela medição** (lista no fim) — cada uma teria sido um commit errado.
2. **Raiz, nunca remendo isolado.** "Corrigir o caso X" não existe; existe "a regra que produziu X
   está errada para a classe inteira". Se um fix só vale para uma entry, é pino ou curadoria — não
   código.
3. **Tudo pelo motor; LLM o mínimo.** O LLM é desempate dentro de uma janela, nunca o primeiro
   degrau. Cada voto retirado tem que manter a acurácia (medido: 81 → 61 votos, 185/200 igual).
4. **Sem motor por categoria.** Regras são gerais (kind, card, série, referência); medem-se em tudo
   e leem-se por categoria. A ordem de ataque do user: material-de-aula → listas → … mas com uma
   cascata só.
5. **Pinar menos.** Pino que o motor reproduz é pino a apagar (30 → 11). Curadoria de **card** cobre
   um cluster; pino cobre uma entry.

---

## Estado verificado (as-of 2026-08-21, `scripts/eval_eixos.py`)

| eixo | total | por curso | observação |
|---|---|---|---|
| **bloco** | **186/200 = 93%** | MF 64/66 · SO 31/38 · IA 43/43 · ES2 23/28 · TCC 25/25 | confiante-e-errado **1** (`azure`, custo aceito) · funil 0/0 |
| **unidade** | **178/188 = 94,7%** | MF 65/66 · SO 29/35 · IA 42/42 · ES2 24/27 · TCC 18/18 | **os 10 erros SÃO os erros de bloco** — não há erro próprio do eixo |
| **cobertura N:N** | **46/57, F1 0,847** | ES2 19/19 · TCC 3/3 · IA 3/3 · SO 14/19 · MF 7/13 | sem-predição 0 |
| **subunidade** | sem gold | censo `eval_subunit_health.py` (régua fraca) | plano categórico × material algorítmico |

Decisores temporais (226 entries): janela-1 **94** · llm 61 · llm-funil 28 · disamb 25 ·
ref-generica 5 · due 3. Pinos manuais: **11** (11/11 certos).

Por categoria no bloco: material-de-aula **86/89** · codigo-professor 52/59 · listas 24/26 ·
trabalhos 6/7 · bibliografia 6/7 · gabaritos 3/4 · provas 2/2 · cronograma 4/4.

---

## O que mudou nesta sessão (21 commits desde `419aaff`)

### Eixo de bloco — o motor decide mais e o LLM menos
- **B-1 régua**: `eval_ground_truth` media o bloco temporal com a banda do scorer de conceito. A
  "banda invertida" (media 78% < baixa 85%) era artefato. Agora banda e `source` são do método que
  decidiu; relatório tem "Por fonte". `9d2fcbe`
- **B-4 llm-funil** (mudança de spec §12): sem janela, o LLM vota com janela = blocos do curso.
  Funil 6/26 → 13/26, 0 regressões. `2902f3e`
- **B-5** bibliografia/references/cronograma/apoio entram na cascata (12/14 tinham pino). `ab7e844`
- **B-6 menos pinos**: `resolve_generic_reference` (ref sem card → 1º bloco overview/class, 4/5 no
  gold); trabalhos/provas sem due percorrem a cascata (card manual cobre cluster — TCC "Semana 14 -
  Apresentações T2" → 5 entries); 13 pinos redundantes + 2 errados apagados. `6b0d639`
- **D-2 gate D4 relido**: `s1>0, s2=0` com discriminante é confiante (era "sem competição = sem
  evidência"). **−22 votos, mesma acurácia.** Stems genéricos +`disciplina/estudo/caso/trabalho`.
  **D-3** trabalhos/provas não passam pelo desempate léxico (`lexical=False`). `799b45f`
- **O-1** aula de correção não conta como encontro no ordinal (`aula-16` do TCC). `2619b78`
- **K-1 prior de kind**: 0 golds em feriado/atendimento/oficina/evento → saem de toda janela
  (`kinds.NEVER_HOSTS_MATERIAL_KINDS`). **K-2** janela só com ref fantasma → llm-funil. **K-2b**
  voto cacheado grava a janela; repergunta se cair fora de janela diferente. `c5fc0b5`

### Eixo de unidade — virou função do bloco
- **U-1**: a verdade de unidade é *por construção* a unidade do bloco verdadeiro. Medido: scorer de
  texto 130 · unidade do bloco temporal 162 · **bloco + herança do vizinho 178** · só bloco 178 —
  o texto não acrescenta nada. **Raiz 1 (ordem)**: a fase de unidade rodava ANTES da camada
  temporal e reconciliava contra `computed_block_id` (scorer de conceito). Movida para depois.
  **Raiz 2 (precedência)**: `reconcile` deixava o texto forte vencer o bloco; agora o bloco decide,
  o texto vira `unit_block_conflict`. Bloco sem `unit_slug` (prova/revisão/entrega/overview) herda
  do vizinho de conteúdo (`file_map.unit_of_block_or_neighbor`). `301e442`
- Cobertura subiu de carona: 44 → 46/57, F1 0,811 → 0,847.

### Taxonomia / plano
- `_is_valid_topic_candidate` (filtro de heading) era aplicado ao CONTEÚDOS do plano e rejeitava
  27/127 tópicos legítimos (marcador `ed` em "pr**ed**itivos"); o IA perdia "Modelos Preditivos".
  `04e691b` · checkbox `- [ ]` escondia numeração e deixava metodologia virar tópico. `5e4be0e`

---

## Para chegar a 100% — o que resta, classificado (decisões do USER, não código)

### Bloco (14 erros) e unidade (os mesmos)

**Gold a revisar (6) — evidência contra o rótulo:**

| entry | gold | motor | evidência |
|---|---|---|---|
| MF `t2-2026-1` | 16 | 18 | due da sala de entrega T2 = **06/07**; 18 é o último bloco de conteúdo antes. Gold = "postagem", contra a convenção fixada para o T2 do TCC (entrega). |
| SO `exercicios` | 03 "Comunicação e sincronização" | 04 "Escalonamento" | card "Gerência de Processos CPU"; conteúdo = algoritmos de escalonamento. |
| SO `lista-p1`, `lista-p1-gabarito` | 09 (última aula antes da P1) | 12 (dia da P1) | as `lista-p2` do **mesmo curso** têm gold = dia da P2. Gold inconsistente; escolher UMA convenção. |
| MF `eth2` | 12 | 01 | regra B-6 aprovada pelo user; 100% exige gold 01 ou pino. |

**Curadoria de card, 1 ato por cluster (4 entries):** em `SO/course/.card_block_map.json`,
`"Threads": {"source":"manual","block_ids":["bloco-03","bloco-06"]}` (3 `exemplo-threads`; o pino
`biblioteca-pthread` tem gold 03 — a janela deixa o voto decidir) e `"Introdução aos Sistemas
Operacionais": {"source":"manual","block_ids":["bloco-02"]}` (`definicao-e-historico`).

**Sem sinal no dado (5):** ES2 `roteiro2/4/5/7` + `azure`. Card "Microsserviços" = unidade inteira
(10 blocos); o cronograma **não nomeia laboratórios** (0 de 20 sessões); código sem markdown. 100%
aqui = dado novo (sessões do cronograma nomeando os roteiros, ou `lessons_index` curado) ou
curadoria por entry. **Refutado:** provider de ordinal-dentro-do-card (7/19 vs LLM 15/19, D-4).

Com os 6 golds e as 2 curadorias: **bloco ≈ 195/200**, unidade acompanha. Os 5 do ES2 são dado.

### Cobertura N:N (11 erros em 57)
Não foi atacada nesta sessão além do que veio de carona. SO 14/19 e MF 7/13 concentram. Caminho:
`scratchpad/consenso_card.py` (refutado, +1) mostrou que `rule: card` já é 179/258 das unidades —
o teto do card está colhido. Os erros restantes precisam de leitura caso a caso com
`scripts/explain_entry.py <repo> <id>` ([5] COBERTURA) contra `material_gt_<C>.csv`.

### Subunidade (sem gold)
- **Não há régua de acerto.** `eval_subunit_health.py` mede concentração (COLAPSO), e concentração
  não é erro (TCC u02 → `maquinas-de-turing` está certo). Primeiro passo obrigatório: **gold de
  subunidade** — rotular ~40 entries (IA u05, SO u01/u02, TCC u01/u02) em `subunit_gt_<C>.csv`.
- **Hipótese a medir antes de código** (mesma lógica do U-1): a subunidade deveria vir do
  **`primary_topic_slug` do bloco temporal** (o tópico que o cronograma dá ao bloco), com o scorer
  de texto só para blocos sem tópico. Se o gold confirmar, é a mesma correção de raiz do eixo de
  unidade.
- **Refutado 3×:** mexer nos aliases da taxonomia (H1 cortar eco, H2 cortar absorção pelo nome
  da unidade, H3 excluir o próprio heading) — todos pioram unidade E esvaziam subunidade. Os
  headings dos materiais SÃO o vocabulário dos tópicos; não tocar.
- IA u05: plano categórico ("Modelos Preditivos") × material algorítmico (árvore, k-NN,
  perceptron); glossário com 0 termos de ML; polaridade ("não supervisionado" ⊃ "supervisionado")
  impede ponte léxica. Decisão (b): fica como está até haver gold.

---

## Ferramentas (o que usar, e as armadilhas)

| ferramenta | mede | armadilha |
|---|---|---|
| `scripts/eval_eixos.py` | **os 3 eixos pelo estado gravado** (novo) | não re-roda scorer: reprocessar antes |
| `scripts/eval_ground_truth.py <repo> <csv>` | bloco, por band E por fonte | — |
| `scripts/eval_entry_unit.py` | **scorer de unidade ISOLADO** (55%) | número que deixou de importar; a unidade vem do bloco |
| `scripts/eval_coverage.py <repo> <csv>` | camada de **referência** | para material dá 0/0 — use `eval_eixos.py` |
| `scripts/eval_subunit_health.py` | concentração de subunidade | concentração ≠ erro |
| `scripts/explain_entry.py <repo> <id>` | **uma entry, etapa a etapa, pelo caminho de produção** | a ferramenta certa para "por que X foi para Y" |
| `scripts/reprocess_assignments.py <repo>` | reprocess headless; lê `feature_flags` de `subjects.json` | os 5 perfis têm `use_anchor_engine` + `use_llm_voter` |

Reverter produção: `git checkout -- .` no repo-tutor (`manifest.json.bak` fica ao lado).
Sentinela mudou por mudança legítima: apagar `tests/_golden/<Repo>__casos_chave.json`, rodar o
teste 2× (1ª cria e pula, 2ª compara) — **só depois de ver o diff campo a campo** (o handoff de
20/08 tem o snippet; diff tem que ser só do campo que a mudança explica).

---

## Erros meus nesta sessão (para não repetir)

- **Li o rodapé da suíte errado** e reportei "verde" com 1 teste quebrado (`04e691b` subiu assim).
  Ler `grep -E "passed|failed"` do output, nunca o `[exited with code 0]` do wrapper.
- **Afirmei "12 das 14 têm gold vazio"** sem olhar — eram 12 pinos manuais. O número errado teria
  bloqueado uma decisão certa (B-5). Conferir o campo antes de inferir.
- Heredoc com f-string e `\` dentro da expressão → `SyntaxError`; e `grep -P`/`\s` no Git Bash
  não existe. Para scripts, `Write`; para grep, a ferramenta Grep.
- Três hipóteses sobre alias (H1–H3) consumiram meia sessão antes de eu questionar o
  enquadramento ("eco"). Após 2 refutações, parar e reler o problema — a regra do skill.

## Hipóteses refutadas pela medição (não retentar)

consenso por card na cobertura (+1/57) · alias-eco H1/H2/H3 · "Prova N → N-ésimo assessment"
(2/8) e "revisão antes da prova" (4/8) · data explícita no texto (2/50) · gate de df global na
exclusividade · resumo de código no disambiguator (não move o total) · ordinal-dentro-do-card
(7/19) · P4 com card temático no SO (+1/−4) · liberar trabalhos pela janela manual sem `lexical=
False` (t1-enunciado → aula do conteúdo).

---

## ADENDO 2026-08-24 — a fila virou acordo, e a Fase 0 já foi executada

A "fila sugerida" abaixo foi **revisada com o user em 24/08** e vive agora em
`pendencias.md`, seção `## FILA ACORDADA COM O USER (2026-08-24)` — é ela que manda.
Três mudanças em relação ao que está escrito no fim deste arquivo:

1. **Fase 0 (limpeza de morto) foi executada** e não aparecia nesta fila. Régua byte-idêntica,
   suíte 2001/1 (o −1 é o teste da função removida). Detalhe em `pendencias.md`.
2. **A meta "100%" é inalcançável no dado atual** — os 5 roteiros do ES2 exigem cronograma
   nomeando os laboratórios (0 de 20 sessões nomeiam). O teto real é **≈195/200**; o título
   deste handoff engana.
3. **A ordem foi invertida por argumento de alavanca:** o gold de subunidade (Fase 2) desbloqueia
   ~6 itens do tracker de uma vez, contra ~9 entries dos 6 golds. Os 6 golds mudam a RÉGUA, não o
   sistema. Fazer os dois é barato; a dúvida é só qual primeiro, e é decisão do user.

Achado novo registrado no tracker: o diálogo de reprovar arquivo **promete apagar o PDF bruto e
não apaga** (`reject` não toca `raw_target`). Decisão pendente — implementar ou corrigir o texto.

## Fila sugerida para a próxima sessão (SUPERSEDED pelo adendo acima)

1. **User decide os 6 golds** (tabela acima) e aprova as 2 curadorias de card do SO → reprocessar
   SO/MF → `eval_eixos.py` → esperado bloco ≈ 195/200.
2. **Gold de subunidade** (~40 entries) → só então medir "subunidade = tópico do bloco".
3. Cobertura: os 11 erros com `explain_entry.py`, um a um, antes de qualquer regra.
4. Higiene (não bloqueia): uuid obsoleto no `card_block_map` do IA (regeneração do mapa deveria
   invalidar refs mortos); `block_identity.py:329` reescreve `manual_timeline_block_id` (uuid ↔
   display) a cada reprocess; ordem de chaves do JSON do manifest alterna entre rodadas.
5. ES2 roteiros: só com dado (cronograma nomeando laboratórios). Decisão do user.
