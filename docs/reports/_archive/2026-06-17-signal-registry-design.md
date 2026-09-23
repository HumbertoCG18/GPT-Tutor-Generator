# Signal-registry de atribuição — design (extensão, não reescrita)

date: 2026-06-17
status: design (pré-implementação)
relacionado: resolver de conceito (Fases 1-3), `docs/superpowers/specs/2026-06-17-resolver-atribuicao-conceito-design.md`, `.mex/context/institutional.md`

## Problema

A precisão de atribuição arquivo→bloco/unidade está limitada por **sinais que existem mas o sistema descarta ou não captura**, não por falta de algoritmo. Medido no gold de código do MF: o resolver erra 6/17, e 3-4 desses erros somem se a gente usar pistas que o professor já forneceu (label do recurso, resumo-da-semana data→tópico) e que o pipeline joga fora.

Regra do usuário (não-negociável): **correção GERAL na raiz, nunca fix por arquivo/cadeira**. Logo a solução não é "usar o resumo da semana do MF", e sim um mecanismo genérico que aproveita QUALQUER pista disponível, degradando honestamente quando ela falta (nem todo professor faz resumo, alguns põem data no nome, outros no label).

## Constatação central: o fusor já existe

`concept_resolver.resolve_material_assignment` (`src/builder/routing/concept_resolver.py`) **já é um fusor multi-sinal com degradação honesta**: funde concept + llm + date + sequence + card, com tiers (manual>card>concept>posicional), `relative_margin_confidence` e detecção de conflito (band-cap 0.45). Está wired atrás da flag `use_concept_resolver` (default OFF) via `resolver_apply.apply_concept_resolver` no `pedagogical_regeneration.py:359`.

**Portanto este design é EXTENSÃO, não reescrita:** adicionar extratores de sinal opcionais + termos pesados no fusor que já existe. Sem paradigma novo, sem big-bang.

## Arquitetura

### Contrato do extrator
Cada pista é um extrator puro e OPCIONAL:
```
extractor(entry, course_context) -> {value: str|tokens, confidence: float} | None
```
- Retorna `None` quando a pista não existe (professor não fez resumo, sem data no nome, etc.) — **skip honesto**, igual ao formato-E do `moodle_labels`.
- `confidence` reflete a CONFIABILIDADE da fonte, não a presença (label do professor > data de storage do OneDrive).
- Nunca load-bearing: ausência = menos um termo na fusão = band mais baixa + flag, NUNCA chute confiante errado.

### As 3 famílias de pista (genéricas, não-MF)
| família | extratores (cada um opcional) | responde |
|---|---|---|
| identidade do material | moodle_label, title, filename, extensão/ferramenta (.dfy/.thy/.smv), concepts do Gemini, texto | o que É |
| posição/quando | source_section (pasta-card), data no nome (DD.MM), Moodle `timemodified` (postagem), Graph/Drive date (fallback fraco), assign_due | onde/quando |
| estrutura do curso | resumo-da-semana `lessons[]` (data→tópico), cronograma SARC (bloco→data+tópico+rows/sessions), card_block_map | mapa |

O fusor casa pistas do material (família 1+2) contra a estrutura do curso (família 3), pesando por confiabilidade.

### Pontos de plug (concretos)
1. **Novo canal de sinal** → 1 chave nova no dict de `collect_entry_unit_signals` (`src/builder/extraction/entry_signals.py:80-132`). Backward-compat: scorers leem por chave via `.get(k,"")`, ignoram ausente. Zero quebra.
2. **Novo termo no fusor** → 1 termo na fórmula de fusão do `concept_resolver` (`fused = W_CONCEPT*overlap + W_LLM*llm + date + seq + card + <novo>`), com TETO de peso.
3. **Índice de estrutura do curso** → consumir o que `moodle_labels` já parseia e DESCARTA (`lessons[].text`): construir um índice `data→tópico` (course-level) que (a) refina o `topic_text` do bloco/sessão e (b) vira um sinal de match material→sessão.

### As alavancas como instâncias do registry
- **Alavanca 0 — `lessons[].text` (resumo-da-semana):** maior ROI, parser pronto (`moodle_labels.py` formatos A-E), só falta o consumidor (índice data→tópico). O `derive_card_block_map` hoje usa só `dates` e dropa o `text`.
- **Alavanca 1 — `moodle_label`:** capturar o `<span instancename>` (= `mod.get("name")` em `moodle.py:130`, disponível mas não persistido). Campo NOVO `moodle_label` (NUNCA sobrescrever `title` — pesa forte no scorer, risco golden) + canal `moodle_label_text`.
- **Alavanca 2 — `source_section` dos zips:** quase de graça — `_section_from_source_path` já existe (`entry_processing.py:32`, commit 8d8915a); repos antigos só precisam de backfill do `source_section` vazio a partir do `source_path` parent.
- **Alavanca 3 — seleção por sessão (assigned_session_id):** infra de `rows`/`sessions` (data+Descrição por aula) já existe no `.timeline_index.json`; falta extrair a data do material + selecionar a row, não só o range do bloco.
- **Posting_date:** Moodle `timemodified` (já no payload de `core_course_get_contents`, dropado em `iter_section_files`) como sinal de data; Graph/Drive `createdDateTime`/`createdTime` só como fallback para arquivos OneDrive-only (via `m365.py`, que já é cliente Graph).

## Contrato de degradação honesta (invariante)
- Sinal ausente → termo ausente → band mais baixa + flag de revisão. Nunca atribuição confiante errada.
- Cada canal tem TETO de peso (anti-envenenamento por sinal ruim).
- O fusor já flaga conflito (bloco-unit ≠ tópico-unit) e capa a confiança — pista nova que briga com as outras vira conflito + band baixa, não erro confiante.

## Eval-gate (cross-curso, obrigatório por canal)
Toda pista nova que altera atribuição:
- golden PDF `eval_assignments.py` = **5/5, confiante-errado 0** (invariante).
- gold de código `eval_code_block_gold.py` — resolver ≥ funil, confiante-errado ≤ funil.
- `rebuild_diff.py` nos 5 cursos — diffs explicáveis; **pista que melhora MF mas regride outro curso NÃO entra**.
- suíte `pytest -q` verde.
- flag `use_concept_resolver` controla o caminho; canais novos entram primeiro no resolver (atrás da flag), nunca direto no funil.

## Non-goals
- NÃO reescrever o funil. O funil de bloco legado é DELETADO (não refatorado) na Fase 3.4, após o resolver vencer o gate.
- UNIDADE continua no funil/posicional (cutover de unidade é Fase 4).
- NÃO tocar GOLDEN: `assign_units_positional`, `_build_timeline_index`, review rule, garantia flag-OFF byte-idêntica.
- Sem hardcode de cadeira ("se MF então"). Só extratores genéricos + pesos.

## Mapa de reúso (da investigação 2026-06-17)
- REUSAR (espinha): `concept_resolver` (fusor) + `resolver_apply` (wire) + `collect_entry_unit_signals` (dict) + timeline `index` (rows/sessions) + `moodle_labels` (parser) + `text/normalize`+`text/stopwords`.
- GOLDEN (não tocar): `assign_units_positional`, `_build_timeline_index`, review rule, golden 5-PDF, flag-OFF.
- DELETAR (Fase 3.4, pós-gate): `score_entry_against_timeline_block` S2 (`block_token_weights`), S4 (`TOOL_*`), `select_probable_period_for_entry` (gate), `_best_instructional_block_fallback`, 2 rotas card→bloco.
- FOLD (barato, eval-gated): 3 scorers de unidade dup; `_normalize_match_text` ×4 → `text/normalize`; `_tokens`+stopwords (card_block vs unit_matcher); `_extract_markdown_headings` ×2.

## Ordem proposta (cada uma eval-gated)
1. **Alavanca 2** (source_section zips) — menor risco, já codada, só backfill.
2. **Alavanca 0** (lessons[].text → índice data→tópico) — maior ROI, parser pronto.
3. **Alavanca 1** (moodle_label) — campo+canal novo, golden-gated.
4. **Alavanca 3 / posting_date** — seleção por sessão + data do material.

Cada alavanca: extrator + chave no dict + termo no fusor + eval-gate cross-curso. Provadamente geral antes de codar.

## Decisões abertas (pro implementador)
- Onde mora o índice data→tópico (course_meta runtime vs `.timeline_index.json` serializado)?
- `moodle_label` em repos via stash antigo: o label se perdeu no download → re-import via API ou aceitar ausência (degradação).
- Peso/teto inicial de cada canal novo: tracejar com fixtures do golden real, não overfitar ao MF (mesma disciplina da Fase 2.2).
