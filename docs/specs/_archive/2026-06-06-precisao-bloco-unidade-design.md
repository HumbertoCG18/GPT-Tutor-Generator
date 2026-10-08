# Precisão de atribuição bloco→unidade: tipo autoritativo + matcher posicional

> Design doc. Aprovado em 2026-06-06.

## Goal

Reduzir o mismatch sistêmico de unidade nas atribuições do cronograma. Causa
raiz medida: **arquivo→bloco é forte** (bands quase todas "alta"), mas
**bloco→tópico→unidade falha** (~100% dos blocos viram ambíguo/`topic_text_fallback`,
~0 via taxonomia) — então a unidade vem de um scorer-keyword frágil que erra
(ex.: recursivas→turing). O arquivo cai no bloco certo mas **herda a unidade
errada do bloco**.

Duas frentes:
1. **Atividade→kind** (Parte 1): a coluna *Atividade* do SARC marca provas/etc.;
   blocos não-aula saem da atribuição de unidade.
2. **Matcher posicional bloco→unidade** (Parte 2): substitui o caminho frágil por
   afinidade lexical forte (bloco × título+tópicos+aliases da unidade) + preenchimento
   posicional ancorado (unidades em ordem × cronograma cronológico).

## Evidência (investigação 2026-06-06)

Auditoria dos 5 cursos reais:

| curso | topic via taxonomy | topic ambíguo | bands arquivo |
|---|---|---|---|
| Engenharia | 0/12 | 12/12 | 32 alta |
| IA | 0/18 | 18/18 | 16 alta |
| Métodos | 0/18 | 18/18 | 34 alta |
| Sistemas | 2/17 | 16/17 | 25 alta |
| TCC | 6/27 | 21/27 | 20 alta |

Protótipo de afinidade por **token-overlap (sessões+topic_text × título+tópicos da
unidade, com stopwords)** no Métodos resolveu os casos difíceis que o scorer atual
errava: "Lógica de Hoare"→U2, "Correção Parcial"→U2 (overlap 6), "Verificação
modelos lógica temporal"→U3, "Introdução métodos formais"→U1. Blocos sem overlap
("Indução árvores", "Terminação dafny") ficam pro preenchimento posicional.
Conclusão: afinidade-melhor + monotônico-ancorado é o lever; só posicional (com a
afinidade fraca atual) trava e erra.

## Decisões (do brainstorming)

- Abordagem **C**: Atividade→kind (provas) **+** matcher posicional (raiz).
- **(a) Monotônico = anchor-fill suave** (não DP rígido): âncoras (vencedor de
  afinidade com margem) progridem não-decrescente; âncora fora de ordem com
  margem baixa é rebaixada; blocos sem sinal herdam a unidade da âncora anterior,
  limitados pela próxima. Permite repetir unidade e pular unidade vazia.
- **(b) Posicional primário; antigo como fallback estreito** (1 unidade só / sem
  taxonomia ordenada / nenhuma âncora). Override manual sempre acima.
- **(c) Bônus de consistência:** o guard de conflito (`auto_suggested_unit`) passa
  a refletir a sugestão do matcher posicional (não os `topic_candidates`), senão
  dispara falso-conflito.
- **Guard de regressão:** testes unitários + script rebuild-diff nos 5 cursos.

## Arquitetura

Ordem no build de um bloco:
1. Classificar **kind** (override manual > `source_kind` SARC > sessão/texto). A
   Parte 1 garante que provas/etc. têm `source_kind` via Atividade.
2. **Só blocos-aula** (`kind == class`) entram no matcher de unidade.
3. Matcher posicional atribui unidade aos blocos-aula em ordem cronológica.
4. `finalize_block` (já existe) zera unidade de não-aula.

Override manual de unidade (`block_manual_unit_slug`) e de kind continua vencendo.

---

## PARTE 1 — Atividade → kind (Plano 1)

### 1A. `_build_timeline_candidate_rows` deriva kind da coluna Atividade
- `_parse_syllabus_timeline` já expõe a coluna como `row["atividade"]` (header
  "Atividade" da tabela do cronograma). Hoje só é concatenada no content.
- Em `_build_timeline_candidate_rows`: localizar a chave da row que contém
  `"atividade"`; se **não** houver `{kind=...}` explícito no content, mapear o
  valor via `_ATIVIDADE_KIND_MAP` (reuso de `src/utils/helpers.py`:
  prova/avaliacao/exame/teste→assessment, trabalho/entrega→deliverable,
  feriado→holiday, revisao→review; aula/vazio/não-mapeado→class). Setar `row["kind"]`.
- Validação contra `BlockKind` já existe (Task anterior). O `source_kind` agrega
  (mecanismo existente) → `classify_block` → assessment → `finalize_block` tira a
  unidade.
- Reuso: importar `_ATIVIDADE_KIND_MAP` e `_norm_ascii_lower` de
  `src/utils/helpers.py` (confirmar ausência de ciclo: helpers é util de baixo
  nível; `timeline/index.py` já importa de utils em outros pontos). Se houver
  risco de ciclo, mover ambos para um módulo neutro (`src/builder/timeline/_atividade.py`).

### 1B. Testes (TDD)
- candidate row com coluna atividade "Prova" → `kind="assessment"`; "Aula"/vazio →
  `"class"`; "Trabalho" → `"deliverable"`; "Feriado" → `"holiday"`.
- `{kind=...}` explícito vence a Atividade.
- Integração: bloco de prova (Atividade=Prova) → `source_kind=assessment` →
  `classify_block`=assessment.

---

## PARTE 2 — Matcher posicional bloco→unidade (Plano 2)

### 2A. Afinidade `_score_block_unit_affinity(block, unit) -> float`
- Tokens do bloco = normalizar (NFKD, lower, sem acento) `sessions[].label` +
  `topic_text`; filtrar stopwords (de/da/do/e/a/o/para/com/em/…) e tokens curtos
  (<3 chars) e numéricos de ordem ("01"/"02").
- Tokens da unidade = título + labels dos tópicos + aliases dos tópicos, mesma
  normalização/stopwords. **Excluir** tokens genéricos do nome de unidade que não
  discriminam ("unidade", "aprendizagem", "visao", "geral", numerais).
- Afinidade = tamanho da interseção (overlap de tokens). Empate/zero permitido.
- (Mais forte e específico que `_score_timeline_block_against_unit`, que casava
  contra o nome da unidade e confundia "computável"↔"computabilidade".)

### 2B. Alinhamento anchor-fill suave `_assign_units_positional(class_blocks, units) -> list[(slug, conf)]`
- `units` = lista ordenada (taxonomy `units[]` / unit_index, já em ordem).
- `class_blocks` = blocos `kind==class` em ordem cronológica (já date-sorted).
- Para cada bloco: vetor de afinidade por unidade; `winner_idx`, `winner`,
  `runner_up`; margem = winner − runner_up.
- **Âncora** se `winner > 0` e `margem >= ANCHOR_MIN_MARGIN` (constante, ex. 1).
- Passada de ordenação: percorrer blocos em ordem mantendo `cur_idx` (última
  unidade ancorada). Para cada âncora:
  - se `winner_idx >= cur_idx` → aceita, `cur_idx = winner_idx`.
  - se `winner_idx < cur_idx` (fora de ordem): só aceita (e recua `cur_idx`) se a
    margem for **alta** (`>= STRONG_MARGIN`, ex. 3); senão **rebaixa** a âncora
    (vira não-âncora).
- Preenchimento: blocos não-âncora recebem `cur_idx` (unidade da âncora anterior).
  Antes da 1ª âncora, recebem o índice da 1ª âncora (ou unidade 0 se nenhuma).
- Confiança: âncora forte → alta (ex. 0.8); âncora fraca → média (0.6);
  preenchido por posição → baixa (ex. 0.4, marca pra curadoria/health).
- Se **nenhuma âncora** no curso → retorna vazio (sinaliza usar fallback 2D).

### 2C. Wiring no build (`_build_timeline_index`)
- Hoje (por bloco): topic-derive → senão `_assign_timeline_block_to_unit` → senão
  `_vote_unit_from_topic_candidates`.
- Novo: **após** classificar kind de todos os blocos, rodar
  `_assign_units_positional` sobre os blocos-aula; aplicar `unit_slug`/
  `unit_confidence` resultantes. Blocos não-aula: `unit_slug=""` (finalize garante).
- Manter herança de "soft continuation" só se ainda necessária após o posicional
  (provável que vire redundante — remover se o rebuild-diff confirmar).

### 2D. Fallback estreito
- Usar o caminho antigo (topic-derive confiante → keyword → voto) **somente** se:
  curso tem <2 unidades, ou taxonomia sem unidades ordenadas, ou
  `_assign_units_positional` retornou vazio (sem âncora). Caso contrário, o
  posicional é a fonte única.

### 2E. Bônus — guard de conflito consistente
- `auto_suggested_unit` (em `timeline/conflicts.py`) hoje usa `topic_candidates[0]`.
  Passar a refletir a **sugestão do posicional**: a unidade de maior afinidade do
  bloco (com a mesma margem/limiar de âncora). Assim o guard só sinaliza override
  manual que contradiz o que o matcher posicional sugeriria — sem falso-conflito
  pela mudança de fonte.

### 2F. Testes (TDD)
- `_score_block_unit_affinity`: "logica de hoare" casa forte unidade Hoare/U2;
  "verificacao modelos logica temporal" → U3; "introducao metodos formais" → U1;
  "funcoes recursivas primitivas computaveis" → U1 (recursivas), **não** U2-turing.
- `_assign_units_positional`:
  - âncoras fortes em ordem → progressão correta.
  - bloco sem sinal entre duas âncoras U1 → recebe U1 (preenchimento).
  - âncora fraca fora de ordem → rebaixada (não recua a sequência).
  - âncora forte fora de ordem (margem alta) → aceita (recua).
  - nenhuma âncora → retorna vazio.
- `auto_suggested_unit` reflete o posicional (não dispara falso-conflito).

---

## PARTE 3 — Guard de regressão (transversal aos 2 planos)

- Testes unitários acima.
- **Script `scripts/rebuild_diff.py`** (dry-run, não grava): rebuilda os 5 cursos
  reais e imprime, por bloco, deltas de `unit_slug`/`kind` vs o índice gravado
  (antigo → novo), além de um resumo (quantos mudaram, quantos não-aula perderam
  unidade, quantos blocos-aula ganharam unidade nova). Revisão manual antes de
  aceitar/gravar. Skip se um curso não existir na máquina.
- Critério de aceite: deltas coerentes (provas→assessment sem unidade; blocos-aula
  com unidade plausível na progressão), sem regressões óbvias. Casos duvidosos →
  curadoria manual (override) ou ajuste de limiar.

---

## Decomposição

- **Plano 1** — Parte 1 (Atividade→kind). Pequeno, testável, e necessário pra
  excluir não-aula do matcher. Entrega ganho imediato (provas).
- **Plano 2** — Parte 2 (afinidade + anchor-fill + wiring + fallback + bônus guard)
  + Parte 3 (rebuild-diff). Maior; o root fix.

## Fora de escopo

- Embeddings/LLM pra afinidade (token-overlap basta, validado no protótipo).
- Reescrever o scorer arquivo→bloco (está forte — não mexer).
- Re-import do SARC (a Atividade já está na tabela do syllabus).
- Subunidades.

## Riscos

- **Regressão de unidade** nos 5 cursos (mudança de núcleo) → mitigado pelo
  rebuild-diff + fallback estreito + override manual.
- **Limiares** (`ANCHOR_MIN_MARGIN`, `STRONG_MARGIN`, confidências) precisam de
  calibração empírica via rebuild-diff; começar conservador (anchor margin baixo,
  strong alto) e ajustar.
- **Cursos sem âncora** caem no fallback (comportamento atual) — sem piora.
- Stopwords/normalização específicas de PT; reusar a normalização existente do
  projeto onde possível (DRY).
