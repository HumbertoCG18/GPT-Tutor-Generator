# Handoff 2026-09-08 — PONTO DE ENTRADA: revisar o plano "confiança antes de acurácia" antes de executar

Único handoff vivo. Substitui `2026-09-05b-handoff-fila-campanhas.md` (que passa a ser histórico).
**Leia nesta ordem:** (1) este arquivo; (2) `docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` — o plano a
revisar; (3) `pendencias.md`, seções datadas 07 e 08/09; (4) `.mex/context/audit-2026-09-07.md`.
Rode `mem-search` para as sessões de 07 e 08/09.

> **A primeira coisa da próxima sessão é REVISAR O PLANO com o user, não executá-lo.**

---

## 1. O que aconteceu em 07 e 08/09, em uma frase

Descobrimos que **parte da acurácia do motor vinha do próprio gold**, tiramos essa contaminação, e o placar caiu. Caiu
porque a régua ficou honesta, não porque o motor piorou — no mesmo período o regime sem LLM nenhum **subiu**.

---

## 2. Estado ao terminar (08/09, tudo commitado, NADA pushed)

### Réguas no produto (Gemini bloqueado por tripwire em todas as medições)
| medida | valor |
|---|---|
| materiais 100% certos | **199/288** |
| bloco | **235/237** |
| unidade | **190/190** |
| subunidade | **161/251** |
| fila | 96 em 348 = **27,6 por 100** |
| **erros confiantes** | **64** |

### Cobertura do gold — o "100%" vale onde há régua
| eixo | gold cobre | do repositório | onde não há régua |
|---|---|---|---|
| bloco | 237 de 348 | 68% | LR inteiro; parte do CG |
| unidade | 190 de 348 | **55%** | **CG (93), LR (7) e FR (22) não têm gold de unidade** |
| subunidade | 251 de 348 | 72% | LR inteiro |

### Os três regimes (`c1-3/mede_sem_voto_llm.log`; base antiga de 233 na subunidade)
| regime | 100% certos | bloco | unidade | subunidade | fila |
|---|---|---|---|---|---|
| produto | 199/288 | 235/237 | 190/190 | 146/233 | 91 |
| sem o voto de LLM | 184/288 | 221/237 | **188/190** | 143/233 | 136 |
| zero LLM | 165/288 | 222/237 | 188/190 | 121/233 | 143 |

### Tutores (HEADs)
MF `3584f89` · SO `c0718a5` · IA `0858418` · ES2 `8cfaf2b` · TCC `73fe7b0` · LR `ae5fead` · FR `7468cd8` · CG `c56b6cb`.
Gerador: `feat/motor-atribuicao` @ `f00c443`, ~965 commits locais, suite 2337.

---

## 3. Os achados desta sessão (o que o plano precisa saber)

### 3.1 CIRCULARIDADE — o mais sério
Quatro dos seis cursos com gold (SO, IA, ES2, TCC) tinham em `course/.glossary_curation.json` um vocabulário cujo
cabeçalho dizia **"proposto-claude a partir de subunit_gt"**. Esses sinônimos viram alias da taxonomia, que é o sinal de
maior peso da subunidade — o motor era medido contra o mesmo gold que originou seu vocabulário.
**Ablação pela rota real** (`ablate_curadoria_gold.log`): subunidade **86/93 → 26/93** nesses quatro cursos
(IA 39/39 → 4/39, ES2 21/28 → 5/28, SO 15/15 → 9/15, TCC 11/11 → 8/11). Bloco e unidade não mudam.
**Feito:** os quatro arquivos foram arquivados em `.glossary_curation.gold.json` (restauráveis) e substituídos por um
gerado só de fontes do professor. Tutores SO `c0718a5` · IA `0858418` · ES2 `8cfaf2b` · TCC `73fe7b0`.

### 3.2 ES2 corrigido na causa — unidade foi a 190/190
Seis materiais da seção "Microsserviços" estavam na unidade errada por **dois** dados de curadoria derivados do gold:
1. `.timeline_curation.json` **pinava o bloco-04** na unidade 02 desde 10/08 (commit `b06b264`, "4 pinos gold-backed").
   O pino contradiz os dois golds atuais.
2. `.glossary_curation.json` punha `service discovery`, `name server`, `service registry`, `API gateway`, `gateway` sob
   2.7 ("integração e IMPLANTAÇÃO"), dando ao bloco-04 afinidade u02=3 × u01=0 no DP posicional.
**As duas correções são necessárias**: só os sinônimos não muda nada (o pino sobrepõe o DP); só o pino não basta.
Justificativa independente do gold: o rótulo do professor separa 1.5 "ARQUITETURA" de 2.7 "implantação", e o cronograma
põe discovery (10/04) e api gateway (17/04) antes da P1 (08/05). Aplicado em `ea0701f`: unidade 21/28 → **28/28**,
subunidade 21 → 27/28, zero perdas.

### 3.3 O compilador de vocabulário por LLM JÁ EXISTE e está desligado em 4 cursos
`src/builder/core/vocabulary_compile.py` (Fase 1b): **1 chamada por unidade com material**, resultado em
`course/.glossary_curation.llm.json` (arquivo separado; o loader funde os dois), com cache. O LLM **não decide
atribuição** — classifica títulos e headings dos materiais nos tópicos DO PLANO. Não é circular: não vê gold.
Já roda em **MF, CG, LR e FR** (gemini-3.5-flash). Amostra do CG: `1.1 Origens ← WHIRLWIND, SAGE, Sketchpad`.
**Não roda em SO/IA/ES2/TCC** porque `vocabulary_compile.py:222` não compila quando existe sidecar manual — e o arquivo
que ocupava esse lugar era o derivado do gold. **O sidecar do professor gerado em 07/09 ocupa o mesmo arquivo e bloqueia
igual.**
**Quanto vale** (`ablate_vocab_llm.log`, 0 chamadas): MF 51→47/58, CG 58→48/82, soma **109→95/140**. Bloco e unidade não
mudam. **Correção importante: MF e CG nunca foram "sem vocabulário". O CG sem vocabulário nenhum é 59%, não 71%.**
**Custo de ligar nos 4:** SO 6 + IA 4 + ES2 2 + TCC 4 = **16 chamadas, uma vez**, depois cache.

### 3.4 A confiança do motor por eixo — é isto que ordena o plano
`calibra_fila_como_regua.log`: "num curso novo, sem gold, quanto do que o motor entrega confiante está certo?"
| eixo | precisão do confiante | recall da fila |
|---|---|---|
| unidade | **157/157 = 100%** | não há erro |
| bloco | 177/178 = 99,4% | 1/2 |
| **subunidade** | **117/181 = 64,6%** | 26/90 = 29% |
**Para a unidade, um curso novo já dispensa gold.** Para a subunidade não: 64 materiais saem errados sem aviso.

### 3.5 A unidade fora do gold se sustenta? Parcialmente
`regua_sem_gold.py` compara o motor com o professor. Ela tem **dois caminhos e só um presta**:
- **A** — a seção nomeia a unidade: confiável.
- **B** — a seção nomeia um tópico e a régua assume a unidade dona: **erra 5 de 5 divergências**, todas no SO, e o gold
  dá razão ao motor nas cinco. (O mesmo caminho já fora refutado como regra do motor em 07/09.)
**Calibração onde as duas réguas existem (44 materiais): motor 44/44, régua 39/44.** O motor é melhor que a régua sem
gold — ela serve para confirmar, nunca para corrigir.
**Cobertura independente:** CG **16 de 93 (17%)**; FR **zero** (os 19 acordos são circulares); LR zero.
Apoio indireto do CG: o bloco bate com o assunto do cronograma em 58/59.

### 3.6 De onde a taxonomia vem × de onde deveria vir
`build_content_taxonomy` tem três fontes e só três: **tópicos** do plano; **aliases** do GLOSSARY (que vem do sidecar);
**aliases** dos headings dos materiais. **O SARC não entra na taxonomia** (alimenta só o alinhamento bloco→unidade) e
**o Moodle também não** (entra como sinal no scorer). O único canal de vocabulário concreto é o sidecar.
Teto de cada fonte em 222 materiais (`mede_fontes_do_professor.log`):
| fonte | alcança o subtópico certo |
|---|---|
| **plano de ensino (rótulo literal)** | **27 = 12%** (IA 0%, MF 7%, ES2 7%, CG 21%, SO 27%) |
| título + label do Moodle | 94 = 42% |
| SARC (label da aula) | 88 = 40% |
| headings do material | 82 = 37% |
| plano + SARC + Moodle | 138 = 62% |
| **nenhuma fonte do professor** | **48 = 22%** — o piso duro sem LLM |
**O plano é a fonte mais fraca**: nomeia a categoria, e o material nomeia o objeto.

### 3.7 O gerador de vocabulário sem gold (feito, mediu 146/233)
`gera_sidecar_professor.py`: a **seção do Moodle** que nomeia exatamente um tópico recebe o vocabulário dos materiais
dela (título, label, headings); o **label da aula do SARC** que nomeia um tópico doa os tokens restantes. Filtros:
boilerplate acadêmico, df > 15%, token que já nomeia outro tópico, e **concentração ≥ 80% das ocorrências na seção que
doa** (foi este que tirou "slides", "página", "vídeos").
Medido: **201/233 (gold) → 135/233 (sem sidecar) → 146/233 (professor)**. Por curso, limpo → professor:
ES2 5→15, SO 9→10, MF 51→52, IA 4→4, TCC 8→8, CG 58→57.
**Onde não funciona, e por quê:** IA 4/39 antes e depois. Ligar "K-Means" a "Modelos Descritivos" é conhecimento de
domínio, e esse mapa não existe no plano, nem no SARC, nem no Moodle.

### 3.8 A restrição unidade → subunidade já existe
`routing/file_map.py:184`: `auto_map_entry_subtopic` filtra o índice de tópicos por `winning_unit_slug`. É absoluta.
Consequência: **errar a unidade torna a subunidade inalcançável** — hoje 4 dos 77 erros de subunidade.

### 3.9 O Moodle NÃO dá a unidade "na maioria das vezes"
Medido em 190 materiais: a seção nomeia a unidade correta em **43 (23%)**, o label em 12 (6%), o bloco em **190 (100%)**.
Quando a seção arrisca, acerta **43/43** — precisão altíssima, cobertura baixa; por isso entra como override explícito.
**A descrição usual está invertida: o SARC dá a UNIDADE** (cronograma → blocos → DP posicional → o bloco decide) **e o
Moodle dá o QUANDO** (a data do label coloca o arquivo no bloco).

### 3.10 A unidade não é livre de LLM (ressalva que muda o placar)
**96 dos 348 materiais (28%) tiveram o BLOCO decidido por voto de LLM** (`routing/motor/llm_vote.py`, TIER 3, cache por
md5, `temporal_block_provider=llm`). O reprocess com tripwire **reusa o voto em cache** em vez de rechamar.
Mas o impacto é pequeno: sem o voto, a unidade cai só de 190 para **188**. O custo do voto está na **fila** (91 → 136) e
nos materiais sem bloco. **Sem voto o motor não erra mais, desiste mais.**

### 3.11 Anatomia da fila (96 = 74 dúvida + 22 mudou)
| motivo | n | significado |
|---|---|---|
| **conflito** | **48** | o texto aponta uma unidade e o bloco aponta outra. O bloco decide por desenho. **Metade da fila, nunca atacado** |
| sub-ambígua | 13 | 2+ subtópicos empataram acima do limiar |
| sub-empate | 10 | empate exato de score |
| flag:disamb | 9 | o bloco saiu de um desempate |
| due-straddle | 1 | entrega entre dois blocos |
| mudou | 22 | decisão confiante que se moveu na última sync (só CG). Transitório |

### 3.12 Duas correções de erro meu, para não se repetirem
- **A régua de subunidade é 251, não 233.** `subunit_gt_FR.csv` tem 18 materiais pontuáveis que nunca entraram em
  medição nenhuma desta campanha. FR faz **15/18**. Os deltas medidos continuam válidos (mesma base dos dois lados),
  mas os absolutos publicados até 08/09 estavam incompletos.
- **Material sem bloco de verdade é 1, não 7.** Contar `temporal_block_id` vazio sem olhar `manual_timeline_block_id`
  infla em 6 materiais do MF que têm pino. O único é `IA / prova-1-2024-02`, categoria `provas`, seção TDE — fora do
  eixo temporal por desenho, **não é pendência**.

### 3.13 O gargalo é o INSUMO, não a regra (medido em 07/09)
| classe | n | acerto |
|---|---|---|
| `.pdf` | 109 | **94%** |
| `.zip` (código) | 35 | 66% |
| `.html` (páginas-índice) | 37 | **62%** |
| material com link de YouTube | 28 | **57%** |
| texto próprio | 184 | 88% |
Confundimento desfeito: aprovado 93% × staging 71% **não é causal** — dentro do CG, aprovado 50% e staging 72%.
55% do erro de subunidade é material que **não tem uma subunidade única** (9 gold vazio, 12 páginas-índice).

---

## 4. NÃO FAZER — refutado por medição nesta sessão
| alavanca | resultado |
|---|---|
| Agrupar arquivos por palavras-chave para **substituir** o scorer | teto 65% com oráculo; real 85/233, pior que 114 por arquivo. Componentes conexas degeneram (IA vira 1 grupo de 39) |
| Título do vídeo no lugar do hash (91% dos 246 links são ID de 11 chars) | 183/183 títulos recuperados do oEmbed; **ganha 0, perde 2**. Mais texto do corpo PIORA: o índice fala dos filhos |
| Piso de score no resultado final | todo piso perde; melhor piso = 0 |
| Título com vocabulário completo | teto 3/38, saldo 0 |
| Página-índice decidida pelo cabeçalho | teto 6/38; melhor +2 com 17 mudanças |
| Triagem da chamada de LLM por sinal determinístico | o sinal **não prediz**: MF-01 tem 7% de sinal fraco e vale −4; MF-03 tem 50% e vale 0 |
| "A prova é fronteira de unidade" | 3 a favor, 25 contra, 8 avaliações neutras |
| Alias ambíguo entre tópicos como alavanca | 7 em 663, nenhum decide bloco |
| Automatizar o gold a partir de Moodle + SARC | erro de categoria: a régua dessas fontes acerta 39/44 onde o motor acerta 44/44 |
| **(07/09)** regra pai × filho · piso de força na 1ª passada · seção → unidade dona · zero-pad no título · número na chave | todas refutadas |

## 5. O que ENTROU nesta sessão
| mudança | onde | efeito medido |
|---|---|---|
| Descrição de imagem fora do texto que o scorer pontua | `44ed407` | +2 materiais; sub 193 → 195 |
| Pino do bloco-04 do ES2 removido + 5 sinônimos movidos de 2.7 para 1.5 | ES2 `ea0701f` | unidade 21/28 → 28/28 |
| GLOSSARY descontaminado nos 4 cursos + gerador sem gold | `baab4ac` + 4 tutores | régua honesta: 201 → 146/233 |

---

## 5b. DECISÕES JÁ TOMADAS pelo user em 08/09 — não reabrir

### Gemini LIBERADO, com protocolo de contenção
Gasto: `vocabulary_compile`, **1 chamada por unidade com material** = SO 6 + IA 4 + ES2 2 + TCC 4 = **16, uma vez**.
1. Um curso por vez, conferindo o contador logado (`vocab: <curso> — N chamada(s)`); se N passar do número de unidades
   do curso, **parar**.
2. `TUTOR_NO_VOCAB_COMPILE=1` continua em todo script de medição.
3. O voter **não** é rechamado (96 votos em cache por md5; `DEFAULT_CAP = 20` como rede).
4. `gemini_auto_summarize` continua desligado (incidente de 05/09: 60 arquivos re-resumidos).
5. Pós-check: contar chamadas do dia antes e depois e registrar no tracker.
6. O sidecar do professor sai da frente por **renomeação**, nunca apagando.

### A próxima campanha é a C5 DÍVIDAS DE DADOS, não a C3
Medido em `compara_c3_c5.log`: **C3 cobre 71 materiais (20%) e carrega 8 dos 92 erros (9%)**, com taxa de erro de 14%
contra 34% no resto — é já a parte mais saudável do repositório. A C5 tem defeito com tamanho medido (**32 dos 35 zips**
com colisão de nome de conteúdo; 99 nomes: CG 60, ES2 29, MF 10), a dívida de régua (**122 materiais sem gold de
unidade**) e o gargalo do insumo (pdf 94% × html 62% × vídeo 57%).
**Ressalva registrada:** o ganho de acurácia de corrigir esses defeitos **não foi medido**. É a aposta melhor
fundamentada, não uma certeza.
**Dois números meus corrigidos no caminho:** "43 sem texto" era **1** (42 são código com resumo); a contagem de
colisões de zip antes incluía duplicatas dentro do mesmo zip e dotfiles.

## 6. Decisões ABERTAS do user (travam trabalho)
| item | o que trava |
|---|---|
| **Qual camada LLM cortar** para ficar em duas | decisão de arquitetura aberta desde 06/09 |
| **Push/merge** dos ~965 commits locais | decisão de fronteira |
| **Posição da C7 (imagens)** na fila | ordenação |
| Revisão da fila do CG (`revisar_queue.md`) | trabalho humano |
| Correção da extração dos zips | CG 168 nomes colidem entre 14 zips; ES2 38; MF 10; `.smv` ignorado |

---

## 7. FILA DE CAMPANHAS — e qual seria a próxima

### Aberta
**C1 TRAVESSIA.** O plano de 08/09 (Fases 1 e 2.1–2.3) é o conteúdo dela. A travessia final e o item 4 dependem de LLM.

### Próxima, pela ordem registrada em 03/09
**C3 PROVAS, LISTAS E TRABALHOS.**

### Estacionadas
C7 imagens · C2 bibliografia · C4 limpa · C5 dívidas de dados · C6 web.

### DECIDIDO em 08/09: a próxima é a C5 (fundamento medido em §5b)
A ordem de 03/09 punha a C3. Os dados mostraram que a C3 é já a parte mais saudável do repositório: 20% dos materiais
e 9% dos erros. As três candidatas, com o dado que as sustenta:

1. **C5 DÍVIDAS DE DADOS, promovida.** O gargalo medido é o insumo: PDF 94%, HTML 62%, vídeo 57%. E há bugs conhecidos
   com tamanho medido: 168 colisões de nome em 14 zips do CG, `.smv` ignorado, páginas do Moodle. Além disso o gold de
   unidade do CG (93 materiais, 27% do repositório) vive aqui. **É a campanha que ataca a causa, não o sintoma.**
2. **C7 IMAGENS.** O custo real de API é o Datalab por página, não o voter. Há um caminho medido para baratear a página
   HTML (Ollama primeiro: 105 → 34 chamadas). Entra se o critério for custo.
3. **C3 provas/listas**, como registrado. Entra se o critério for cobertura de categorias.

**Decidido: C5 antes de C3.** Todo ganho de motor que sobrou é de segunda ordem (2 a 5 pontos), enquanto o insumo
responde por diferenças de 30 pontos entre classes de material — e a C3 não tem massa de erro para justificar
prioridade.

---

## 8. Leis (reafirmadas)
- **Gold só mede, nunca decide — e nunca vira insumo.** Entrou duas vezes (sidecar de sinônimos, pino de bloco) e foi
  retirado em 07 e 08/09.
- **SARC e Moodle acima do gold** quando divergirem.
- Dado antes de código: nenhuma alavanca entra sem medição prévia pela rota real.
- Gate zero-diff, teste e reprocess registrado nos 8 em toda mudança de motor.
- Ao publicar número de subunidade, dizer a base (**251**) e o regime.
- Nada é pushed sem ordem explícita.
- Tokens nunca impressos. `.claude/settings.local.json` nunca em stage.

## 9. Ferramentas desta sessão (`docs/reports/_harness-2026-09-04/c1-3/`)
`diag_gargalo.py` (38 erros por causa × evidência + anatomia da fila) · `mede_classe_material.py` ·
`mede_atribuir_vazio.py` · `mede_fontes_do_professor.py [--limpo]` · `ablate_curadoria_gold.py` ·
`gera_sidecar_professor.py` · `mede_sidecar_professor.py` · `descontamina_glossary.py --aplicar` ·
`ablate_vocab_llm.py` · `triagem_vocab_llm.py` · `mede_cluster_keywords.py` · `mede_vizinho_keywords.py` ·
`simula_propaga_similaridade.py` · `mede_moodle_da_unidade.py` · `mede_sem_voto_llm.py` · `estado_08_09.py` ·
`calibra_regua_unidade.py` · `calibra_fila_como_regua.py` · `corrige_curadoria_es2.py` · `aplica_correcao_es2.py`.
**Todos com log homônimo — e os `.log` estão no `.gitignore`, existem só nesta máquina.** Os scripts são versionados,
então tudo é reproduzível; a evidência bruta, não.

## 10. Artefatos publicados
| artefato | estado |
|---|---|
| [Placar do Motor](https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de) | **atualizado 08/09**: estado de hoje no topo, histórico de 06/09 abaixo |
| [Matriz de Atribuição](https://claude.ai/code/artifact/4ddad807-e2fe-4ede-a3ca-c175916f7ca6) | **atualizada 08/09**: coluna `produto` regenerada; `zero`/`vocab`/`auto` de snapshots de 06/09 |
| [Gold × Moodle × SARC](https://claude.ai/code/artifact/f53542b1-9061-4034-a1f3-e86ce001a81f) · [Razão dos Blocos](https://claude.ai/code/artifact/d2ef4eaa-3483-412a-9dc8-110b1f9ccacb) | aviso datado de 08/09 |
| [Raio-X](https://claude.ai/code/artifact/399626ee-682b-43f8-9987-09c344f6c60f) · [Anatomia do Bloco](https://claude.ai/code/artifact/ba1de7bf-a802-49fc-b88b-6be358d4b796) | **não tocados** — declaram-se leitura de 01–02/09 e linkam o Placar; a nota interna de 06/09 deles cita números superados. Têm SVG desenhado à mão: regenerar exige refazer as medições daquelas páginas |
