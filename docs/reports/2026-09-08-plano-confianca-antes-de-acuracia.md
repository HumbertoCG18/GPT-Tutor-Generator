# Plano — confiança antes de acurácia

last_updated: 2026-09-08 (reescrito depois da atualização dos artefatos)
Entrada: `docs/reports/pendencias.md` (tracker vivo) · `.mex/context/audit-2026-09-07.md` (memória) ·
harness `docs/reports/_harness-2026-09-04/c1-3/`
Artefatos: [Placar](https://claude.ai/code/artifact/231d161b-96dc-4061-84a1-cdb8e0ec91de) ·
[Matriz](https://claude.ai/code/artifact/4ddad807-e2fe-4ede-a3ca-c175916f7ca6)

---

## 1. A tese, e por que esta ordem

O gold nunca foi insumo do motor. Ele mede. O que o motor tem de próprio para saber se acertou é a **confiança**, que
vira a fila de revisão. Medido em 08/09 (`c1-3/calibra_fila_como_regua.log`):

| eixo | precisão do confiante | leitura |
|---|---|---|
| unidade | **157/157 = 100%** | um curso novo já dispensa gold de unidade |
| bloco | 177/178 = 99,4% | idem, na prática |
| **subunidade** | **117/181 = 64,6%** | **64 materiais saem errados sem aviso** |

Subir acurácia com a confiança mentindo aumenta os acertos **e** os erros silenciosos. Produto que erra calado é pior
que produto que pergunta: o aluno não tem como saber que aquele material está no lugar errado. **Confiança primeiro.**

Isso também é o que responde ao objetivo de fundo: *a atribuição não deve depender de gold feito à mão*. Na unidade já
não depende. Na subunidade, o caminho não é remover o gold, é usá-lo **uma vez** para descobrir onde a confiança mente;
depois disso a confiança viaja sozinha para cursos novos.

**O que não fazer:** automatizar a criação do gold a partir do Moodle e do SARC. Medido: a régua construída dessas
fontes acerta 39/44 onde o motor acerta 44/44 — um gold automático teria introduzido 5 erros no SO. Não se mede um
instrumento com uma cópia pior dele mesmo.

---

## 2. Estado de partida (08/09, produto em disco, Gemini bloqueado)

| medida | valor |
|---|---|
| materiais 100% certos | 199/288 |
| bloco | 235/237 |
| unidade | 190/190 |
| subunidade | **161/251** |
| fila | 96 em 348 = 27,6 por 100 |
| **erros confiantes** | **64** |

**Cobertura do gold:** bloco 68% do repositório, unidade 55%, subunidade 72%. CG (93 materiais) e LR (7) não têm gold
de unidade nenhum; LR não tem gold de bloco.

**Regimes** (`c1-3/mede_sem_voto_llm.log`, base antiga de 233 na subunidade):

| regime | 100% certos | bloco | unidade | subunidade | fila |
|---|---|---|---|---|---|
| produto | 199/288 | 235/237 | 190/190 | 146/233 | 91 |
| sem o voto de LLM | 184/288 | 221/237 | 188/190 | 143/233 | 136 |
| zero LLM | 165/288 | 222/237 | 188/190 | 121/233 | 143 |

O voto de LLM vale 14 no bloco e 2 na unidade. Sem ele o motor não erra mais, **desiste mais**.

---

## FASE 1 — HONESTIDADE DA CONFIANÇA

**Objetivo:** que o motor mande para a fila o que hoje entrega calado.
**Régua:** `calibra_fila_como_regua.py`, precisão do confiante por eixo.
**Gate de saída:** precisão do confiante da subunidade **≥ 90%**, sem regressão em bloco e unidade, com o crescimento
da fila declarado e aceito pelo user.

### 1.1 Diagnosticar os 64 erros confiantes · 0 chamadas
Cruzar, para cada um: score do vencedor, margem para o segundo, origem do sinal (rótulo do plano, alias de heading,
alias compilado), tamanho do texto, classe do insumo. Só medição, sem código de motor.
Hipótese de trabalho, **não medida**: margem alta vindo de alias longo casando por acaso em texto curto.

### 1.2 Calibrar o limiar · 0 chamadas
Varrer o limiar de **confiança/margem** contra o gold, medindo os dois lados: quantos erros confiantes somem e quanto a
fila cresce. O gold entra **uma vez**, aqui.
**Ressalva registrada:** piso sobre o *score* já foi refutado em 07/09 (todo piso perde). Este item é sobre outra
grandeza. Se também não houver corte útil, o item morre e vira registro.

### 1.3 Fazer a decisão fraca cair na fila
Só se 1.2 achar ponto. Regra no motor, com gate zero-diff, teste e reprocess registrado nos 8.

---

## FASE 2 — ACURÁCIA

Começa com a Fase 1 fechada. Os três primeiros itens não gastam chamada.

### 2.1 Propagação por similaridade — **+5 medido** · 0 chamadas
Material indeciso depois da 1ª e da 2ª passada herda a subunidade do vizinho mais similar entre os que o motor decidiu
com confiança. Similaridade = Jaccard dos tokens distintivos, dentro da unidade.
`simula_propaga_similaridade.log`: regime atual 135 → 140, ganha 6 perde 1, piso 0,05–0,10.

### 2.2 Filtro mais duro no vocabulário compilado — **+2 medido** · 0 chamadas
Cortar termo doado cujo núcleo aparece no vocabulário ou nos materiais de outra unidade, e recusar doação a tópico de
rótulo meta ("Áreas relacionadas", "Conceitos", "Introdução").
`triagem_vocab_llm.log`: a unidade 01 do CG custa 2 pontos hoje; outras 3 chamadas são neutras.

### 2.3 `conflito` — 48 itens, metade da fila, nunca atacado · 0 chamadas
Quando o texto aponta uma unidade e o bloco aponta outra, o bloco vence por desenho e o desacordo só vira registro.
Há gold de unidade em 190 materiais para arbitrar quem acerta nesses casos. **Medir antes de mexer.**

### 2.4 Ligar o compilador de vocabulário nos 4 cursos bloqueados · 16 chamadas
SO 6 + IA 4 + ES2 2 + TCC 4, uma vez, depois cache.
Exige duas coisas: **liberar o Gemini** (decisão aberta do user) e tirar o sidecar do professor da frente
(`vocabulary_compile.py:222` não compila quando existe sidecar manual).
Referência de 02/09 citada no próprio código: este prompt levou o IA de 5 para 37/39.

---

## FASE 3 — COBERTURA DA RÉGUA

### 3.1 Incluir o FR no conjunto padrão · 0 chamadas
`subunit_gt_FR.csv` tem 18 materiais pontuáveis que nunca entraram em nenhuma medição desta campanha; o FR faz 15/18.
Todo script do harness que hoje usa 6 cursos passa a usar 7. **Sem isso, todo absoluto publicado continua incompleto.**

### 3.2 Gold de unidade para o CG
93 materiais, 27% do repositório, hoje sem régua nenhuma nesse eixo. A confirmação independente pelo professor cobre só
17% deles (16 de 93); no FR ela é zero, porque os 19 acordos são circulares. É o único jeito de fechar a pergunta
"a unidade se sustenta fora do gold?".

---

## 3. Decisões abertas que travam trabalho

| item | o que trava |
|---|---|
| **Liberar o Gemini** | Fase 2.4 inteira, recompilar o vocabulário do CG, `gemini_auto_summarize` |
| **Qual camada LLM cortar** para ficar em duas | decisão de arquitetura aberta desde 06/09 |
| **Push/merge** dos ~965 commits locais | nada técnico; é decisão de fronteira |
| **Posição da C7 (imagens)** na fila de campanhas | ordenação |
| Revisão da fila do CG (`revisar_queue.md`) | trabalho humano |
| Correção da extração dos zips | bug conhecido: CG 168 nomes colidem entre 14 zips |

## 4. Campanha formal

Pela fila do tracker: **C1 TRAVESSIA** é a única aberta, **C3 provas/listas** é a próxima, e estão estacionadas
C7 imagens, C2 bibliografia, C4 limpa, C5 dívidas de dados, C6 web.
Este plano não é campanha nova: é o conteúdo do que fazer no motor. Os itens 1.x e 2.1–2.3 continuam a C1; os 3.x
continuam a C5.

## 5. Estado dos artefatos publicados (08/09)

| artefato | ação |
|---|---|
| **Placar do Motor** | reescrito: o estado de 08/09 vem primeiro, o histórico de 06/09 fica abaixo marcado como tal |
| **Matriz de Atribuição** | coluna `produto` regenerada do disco; nota explicando a descontaminação. As colunas `zero`, `vocab` e `auto` continuam vindo de snapshots de 06/09 |
| **Gold × Moodle × SARC** · **Razão dos Blocos** | aviso datado de 08/09 com link para o Placar |
| **Raio-X** · **Anatomia do Bloco** | **não tocados.** Já se declaram como leitura de 01–02/09 e já linkam o Placar; a nota interna de 06/09 deles cita números superados. Reescrevê-los à mão arriscaria corromper os diagramas SVG. Regenerar exige refazer as medições daquelas páginas |

## 6. Regras que valem em todos os itens

- Dado antes de código: nenhuma alavanca entra sem medição prévia pela rota real.
- Gate zero-diff, teste e reprocess registrado nos 8 tutores em toda mudança de motor.
- Gold só mede, nunca decide, e nunca vira insumo. Entrou duas vezes e foi retirado em 07 e 08/09.
- SARC e Moodle acima do gold quando divergirem.
- Ao publicar qualquer número de subunidade, dizer a base (251) e o regime.
- Nada é empurrado para `main` sem ordem explícita.
