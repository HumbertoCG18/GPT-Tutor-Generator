# P2 — Resolver único de atribuição em espaço de conceito (design)

date: 2026-06-17
status: **spec / design**. Eval-gated. Plano de execução (`*-plan`) a escrever depois de aprovado.
branch: `feat/reconciliar-unit-bloco`
relacionado: handoff `docs/reports/2026-06-17-handoff-atribuicao.md`; contexto `.mex/context/institutional.md`; censo `scripts/eval_code_block_census.py`.

---

## 1. Contexto e motivação

A atribuição material→bloco→unidade hoje é um **acúmulo de sistemas paralelos** que cresceram um sobre o outro:

- scorer léxico (`file_map.score_entry_against_timeline_block`) — overlap de tokens entry↔bloco, com sinais S2 (IDF `block_token_weights`), S4 (ferramenta `TOOL_BOOST=0.8`/`TOOL_PENALTY=0.4`), data, sequência;
- `card_block_map` (2 rotas: card→datas→bloco e card-scoped scorer);
- matcher posicional de unidade (`assign_units_positional`);
- fallback keyword ~600 linhas (`index.py` else + `_assign_timeline_block_to_unit`/`_vote_unit_from_topic_candidates`/`_score_timeline_row_against_unit`) — adiado do P1;
- voto do LLM (Gemini `code_curation`: `primary_block_id` + concepts + confiança), fundido por um **gate cru** D1 (`attach_block_summary_fields`): adota o Gemini só quando `sem source_section E band baixa`.

Esses sistemas **discordam** e são arbitrados por gates pontuais. A dívida nomeada no radar (P2 "família de 6 scorers", 🥈 "unit×card fuzzy", P1 "fallback") é toda **a mesma raiz**.

### Evidência concreta (censo código→bloco no MF, 17/06)

`scripts/eval_code_block_census.py` no Métodos-Formais expôs o padrão. Em `code_curation.json` o **Gemini acertou** o bloco (semântico), mas o **funil escreveu o errado**:

| entry | Gemini `primary_block_id` (certo) | funil `computed_block_id` | bloco real do funil | causa |
|---|---|---|---|---|
| arvores.thy | bloco-05 (Indução árvores) | **bloco-06** | "Interativa teoremas **Isabelle**" | `TOOL_BOOST` +0.8: tool=isabelle casa o topic do 06 |
| intro.thy | bloco-04 (Conjuntos indutivos) | **bloco-06** | idem | idem |
| listas.thy | bloco-05 (Indução listas) | **bloco-06** | idem | idem (band **alta** → confiante-errado) |
| classes-parte1 | bloco-15 (OO Dafny classes) | **bloco-16** | "Verificação de Modelos" | sem source_section; scorer/posicional erra; arrasta unit→unidade-03 + subunit errado |

**Os 4 são `llm_only`/band média-alta** → o gate D1 (`sem-seção E band-baixa`) NÃO adota o Gemini correto → o bloco errado do funil fica.

Por outro lado, nos **cardless de faixa do meio o funil GANHOU do Gemini 6/7** (colecoes-arrays/conjuntos/sequencias→bloco-13, invariantes/terminacao→bloco-11, hoare→bloco-10), porque o Gemini tem viés de ancorar em **bloco-04** por keyword ("conjuntos"). Lição: **nem o funil nem o LLM sozinho bastam** — cada um erra num eixo (o funil super-pesa ferramenta/forma; o LLM ancora por keyword). Precisam ser **um modelo só** que combine os sinais e meça discriminância no nível certo.

### Censo subunit/bands (17/06): divergência timeline × plano na UNIDADE

`scripts/eval_subunit_census.py` no MF (pós-reprocess, **confirmado não-stale** — idêntico ao pré): cobertura subunit 27/60, band alta 40 / media 8 / baixa 9, e **7 subunit FORA da unidade** (viola a restrição do P0.2). Todos são `entry=unidade-01` com subunit de um tópico que o **Plano de Ensino** lista na unidade-02/03 (`logica-de-hoare`, `correcao-parcial-e-total`, `pre-e-pos-condicoes`, `softwares-...`). Causa: o **cronograma SARC** agenda Hoare/correção/etc. na janela da unidade-01 (a entry herda `unit` do BLOCO), mas o Plano agrupa esses tópicos na unidade-02/03 (a subunit vem do TÓPICO do plano) → **a unidade do bloco e a unidade do tópico-no-plano DIVERGEM** e a subunit escapa da unidade vencedora. É a divergência `unit_index`×`content_taxonomy` / timeline×plano vista no concreto — o resolver tem de **flagar o conflito** (bloco-unit ≠ tópico-unit), não atribuir silenciosamente uma subunit de outra unidade. (+1 slug stale `21-logica-de-hoare` = bug de normalização de slug do subunit, fix separado.)

### Por que o "quick-win" de down-weight de ferramenta NÃO resolve isolado

O sinal de ferramenta **já existe e é deliberado** (P4, S4): `TOOL_BOOST=0.8` premia o bloco cujo `topic_text` contém o token da ferramenta da entry. O bug é que **bloco-06 se chama "Isabelle"** e a ferramenta é **uniforme na unidade-01 inteira** (04/05/06 são todos Isabelle) → não discrimina bloco, mas o boost age como se discriminasse. O IDF (S2) não corrige porque mede df sobre `topic_text` (isabelle aparece só no 06 → "raro" → favorecido), não sobre o uso real da ferramenta na unidade. Reduzir `TOOL_BOOST` é re-tunar uma constante deliberada (risco de regredir o P4) e é um tweak específico. **Decisão (17/06): dobrar a recalibração do sinal de ferramenta dentro deste resolver**, onde a discriminância é medida no nível certo.

---

## 2. Objetivos / não-objetivos

**Objetivos**
- Um **resolver único** material→bloco e material→unidade, sobre uma **representação compartilhada por conceito**, substituindo a família de scorers + 2 rotas de card + fallback keyword + gate D1.
- Discriminância de token medida no **nível certo** (ferramenta/forma uniforme na unidade ≠ sinal).
- LLM (concepts + bloco sugerido) como **sinal de 1ª classe**, fundido, não gate band-restrito.
- Confiança honesta do modelo único; discordância card×conceito vira **conflito flagado**, não pick silencioso.
- Migração **eval-gated**, sem regressão no gabarito.

**Não-objetivos**
- Não muda a rota **autoritativa do SARC** (`source_kind`, kind do bloco) nem o P3.4 (KIND de cronograma).
- Não introduz dependência de LLM em runtime sem chave (degrada para léxico+card como hoje).
- Não re-treina nada; usa concepts já extraídos pelo Gemini no `code_curation`.

---

## 3. Princípios de design

- **A. Resolver único, representação compartilhada.** Uma função resolve (material→bloco, material→unidade) num só espaço de features. Mata os 6 scorers / 2 rotas de card / fallback.
- **B. Espaço de CONCEITO, não tokens de superfície.** Material e bloco/unidade representados por conceitos pedagógicos normalizados (taxonomia do plano + `concepts` do Gemini), não tokens crus.
- **B'. Discriminância no nível certo.** Token de **ferramenta/formato** (`known_tools` do semantic_profile; extensões .thy/.dfy/.zip) e termos uniformes na unidade recebem peso por **discriminância real**: IDF medido sobre o conjunto certo (uniforme na unidade → ~0). Resolve o viés Isabelle→06 SEM hardcode e SEM constante mágica.
- **C. Conceito do LLM como sinal de 1ª classe.** O Gemini lê o conteúdo e nomeia conceito + bloco + confiança — melhor sinal de "do que TRATA". Funde como voto ponderado no resolver (não gate `band-baixa`).
- **D. Precedência por TIERS explícitos.** `manual` > `card/data autoritativo` (postado-sob-semana = ground truth) > `concept-match misto (léxico+LLM)` > `posicional`. Acaba o special-case `sem-seção E band-baixa`.
- **E. Confiança do modelo único.** Band reflete concordância entre sinais; discordância (card-bloco × conceito-bloco, ou funil × LLM) **derruba a band e vira conflito flagado** (`unit_block_conflict`/health). `listas` deixaria de ser confiante-errado band-alta.
- **F. Migração eval-gated.** Roda atrás de golden + censo código→bloco + `rebuild_diff` nos 5 cursos; prova ≥ atual e ↓ confiante-errado ANTES de cortar e deletar o legado.

---

## 4. Arquitetura proposta

```
resolve_material_assignment(entry, blocks, units, *, signals, llm_curation) -> Assignment
  Assignment = {block_id, unit_slug, confidence, band, method, signals_breakdown, conflict?}
```

**4.1 Representação (princípio B).** Para entry e para cada bloco/unidade, montar um **vetor de conceito** a partir de:
- entry: título, markdown, `source_section`, tags, e (se houver) `concepts` do Gemini;
- bloco: `topic_text` + labels de sessão + `primary_topic_label`/aliases da taxonomia;
- unidade: título + tópicos + aliases do plano de ensino.

Normalização canônica única (consolidar `_normalize_match_text` / `normalize_match_text` / `_norm`). Stopwords unificadas (consolidar `_TIMELINE_GENERIC_TOKENS` / `UNIT_GENERIC_TOKENS` / `_STOPWORDS` / `card_block._STOP`).

**4.2 Peso por discriminância (princípio B').** Peso de cada token = função de IDF medida no **escopo correto**:
- para escolher BLOCO dentro de uma unidade: df sobre os blocos **daquela unidade** → token uniforme na unidade (ex. "isabelle" em 04/05/06) ≈ 0; token raro (ex. "arvores" só no 05) alto.
- para escolher UNIDADE: ferramenta PODE discriminar (Isabelle=u1, Dafny=u2) → df sobre unidades. Mesma máquina, escopo diferente.

Isto substitui S2 (IDF sobre `topic_text` só) e S4 (`TOOL_BOOST` constante): a ferramenta deixa de ser boost fixo e passa a valer pela discriminância medida.

**4.3 Fusão de sinais (princípio C).** Score do candidato = soma ponderada de:
- overlap de conceito (léxico, com pesos 4.2);
- **voto do LLM** (`primary_block_id`/`secondary_block_ids` + `block_match_confidence`) como termo ponderado — não gate;
- data (`_score_block_date_match`), sequência (`score_sequence_match`) — mantidos;
- card-evidence.

**4.4 Precedência por tiers (princípio D).** O resolver aplica tiers explícitos; dentro do tier de concept-match, a fusão 4.3 decide. Card/data autoritativo vence concept-match; manual vence tudo.

**4.5 Confiança e conflito (princípio E).** `relative_margin_confidence(best, runner_up)` sobre o score fundido (reusa `thresholds`). **Discordância entre fontes fortes derruba a confiança** e emite `unit_block_conflict`/flag de health — em vez de um pick silencioso de band alta (caso `listas`).

---

## 5. O que substitui / deleta (fim da dívida)

- `file_map.score_entry_against_timeline_block` + S2/S4 + `select_probable_period_for_entry` + `_best_instructional_block_fallback` → **resolver único**.
- 2 rotas card→bloco (`_card_scoped_block` + `card_block_map` direto) → 1 tier autoritativo.
- `attach_block_summary_fields` gate D1 (`sem-seção E band-baixa`) → LLM vira sinal fundido.
- fallback keyword ~600 linhas (P1 adiado) → deletado com **fold dos sinais que ele tinha e o posicional não** (nº explícito "Unidade N", frases/âncoras) no resolver.
- divergência latente `unit_index` × `content_taxonomy` (`_derive_unit_specs_from_repo`) → uma fonte de unidade só.
- 6 normalizadores/stopwords ×N → consolidados.
- 🥈 unit×card fuzzy → cai no mesmo espaço de conceito (match unit↔card por conceito, não nome literal).

---

## 6. Casos de teste / evidência (gate de aceitação)

**Devem CORRIGIR (Gemini certo, funil errado hoje):**
- arvores.thy → bloco-05 (não 06); intro.thy → bloco-04; listas.thy → bloco-05; classes-parte1 → bloco-15 (unidade-02, não unidade-03).

**Não podem REGREDIR (funil certo hoje, Gemini errado):**
- colecoes-arrays/conjuntos/sequencias → bloco-13; invariantes/terminacao → bloco-11; hoare → bloco-10; exercicios-conjuntos → bloco-13.

**Invariantes globais:**
- golden de bloco `scripts/eval_assignments.py` = **5/5, confiante-errado 0** (nunca regredir).
- censo código→bloco: confiante-errado **não sobe**; idealmente os 4 acima migram pro bloco do Gemini.
- `scripts/rebuild_diff.py` nos 5 cursos: diffs explicáveis, nenhum flip ruim de unidade.
- suíte `python -m pytest tests -q` verde.
- **subunit dentro da unidade (P0.2):** `scripts/eval_subunit_census.py` — nenhum "subunit FORA da unidade" silencioso. Onde bloco-unit ≠ tópico-unit (os 7 casos MF: Hoare/correção/pré-pós/tipos-indutivos), o resolver **flaga conflito** e restringe a subunit à unidade vencedora; nunca atribui subunit de outra unidade. Sem slug stale (`21-logica-de-hoare`).

---

## 7. Migração faseada (eval-gated)

1. **Consolidação não-comportamental:** unificar normalize/stopwords numa base; cobrir com guard tests (byte-idêntico). Sem mudança de saída.
2. **Resolver atrás de flag:** implementar o resolver de conceito (4.1–4.5) em paralelo ao funil atual; comparar via censo + rebuild-diff nos 5 cursos. Sem cutover.
3. **Cutover do bloco:** quando o resolver ≥ funil no gabarito + ↓ confiante-errado, trocar o caminho de bloco. Deletar S2/S4/scorers/2 rotas.
4. **Cutover da unidade + fold do fallback:** mover unidade pro resolver; deletar fallback keyword ~600 linhas + `_derive_unit_specs_from_repo` (resolvendo a divergência latente). Guard: posicional nunca [] no golden.
5. **Limpeza:** remover normalizadores/predicados duplicados restantes.

Cada fase roda atrás dos gates da seção 6.

---

## 8. Riscos e mitigações

- **Regressão do gabarito / do P4 (S4).** Mitiga: fases atrás de golden + censo + rebuild-diff; cutover só com ≥ atual. S4 não é "removido às cegas" — é substituído por discriminância medida, validada nos casos arvores/listas.
- **df no escopo certo precisa de dados de curso.** A discriminância de ferramenta por unidade exige o conjunto de blocos da unidade no momento do score — disponível (timeline index + unit_index). Documentar a dependência.
- **Dependência de reprocess.** O censo reflete o repo gerado; rodar sempre com o app reiniciado pós-mudança (senão dados stale). Vide handoff (pendência user-side).
- **LLM ausente (sem chave).** O resolver degrada para léxico+card (sinal LLM = 0), como hoje.

---

## 9. Questões em aberto

- Calibração dos pesos de fusão (4.3): aprender do gabarito vs fixar por princípio?
- Blocos MERGED (apresentação+prova, ex. IA bloco-16 / SO bloco-08): resolver no agrupamento (`_rows_belong_to_same_thematic_block`) antes, ou o resolver lida com bloco multi-kind? (dívida correlata "separar blocos merged").
- `concepts` do Gemino: usar embeddings/alias-map ou só overlap normalizado de conceito? (começar simples = overlap; embeddings é evolução).
- **Divergência timeline×plano na unidade (7 casos MF):** quando o bloco (SARC) e o tópico (plano) discordam da unidade, quem vence a `unit` da entry? Proposta: o **bloco** (agendado/postado) vence a unidade, o conflito é **flagado**, e a subunit fica **restrita à unidade vencedora** (nunca de outra unidade). Validar no `eval_subunit_census` pós-resolver (alvo: 0 subunit fora da unidade).
