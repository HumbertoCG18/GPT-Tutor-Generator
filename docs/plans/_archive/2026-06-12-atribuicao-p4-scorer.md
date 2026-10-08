# P4 — Limpeza do Subsistema + 5 Sinais no Scorer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Matar código morto/duplicado e os 3 "segundos cérebros" restantes (Fase 0), depois adicionar 5 sinais ao scorer de bloco medindo no golden após cada um (meta: 36/48 → ≥43/48, confiante-e-errado 0, `logicadehoare`→bloco-10).

**Architecture:** Fase 0 = deletar mortos + unificar helpers + fonte única nos artefatos/UI (golden tem que ficar IDÊNTICO, exceto a unificação do normalize que é medida isolada). Fase 1 = um sinal por task com commit próprio e MEDIR (bisect fácil): CamelCase → IDF → tamanho de topic → ferramenta → janela de assign.

**Tech Stack:** Python 3.13, pytest. MEDIR = `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json`.

**Spec:** `docs/superpowers/specs/2026-06-12-atribuicao-p4-scorer-design.md`
**Inventários:** sessão 12/06 — funções (5 mortos/9 dup/6 suspeitos) + fluxos (#1-#7).

**Fatos do código:**
- Scorer de bloco: `score_entry_against_timeline_block` (src/builder/routing/file_map.py:816-888) monta `runtime_block` com rows + chama `score_timeline_block` (:752); sinais da entry vêm de `collect_entry_unit_signals` (src/builder/extraction/entry_signals.py).
- Funil: `resolve_unit_block_tags` (content_taxonomy.py:944+); card scoped em :845-867; fallback :786-840.
- Golden/harness do P0; baseline atual EXATO: 36/48 (75.0%), confiante-e-errado 0, erros conhecidos listados pelo harness.
- Branch: feat/reconciliar-unit-bloco. Pre-commit imprime UnicodeEncodeError cp1252 inofensivo (commit passa; confirmar com `git log -1 --oneline`).
- REGRA DE OURO da Fase 0: rodar o harness ANTES e DEPOIS de cada task — diff de erros tem que ser VAZIO (exceto Task 3, medida isolada). Se mudar: parar, investigar, reportar.

---

## FASE 0 — LIMPEZA

### Task 1: Deletar os 5 mortos (spec 0.A)

**Files:** Delete/Modify: `src/builder/extraction/entry_signals.py:119` (função `extract_date_prefix_signal`), `tests/test_date_prefix_signal.py` (deletar), `scripts/backfill_source_section.py` (deletar), `scripts/eval_cards.py` + `tests/test_eval_cards.py` (deletar), `src/builder/routing/thresholds.py:111` (`MATERIAL_COVERAGE_MIN`) + assert em `tests/test_routing_thresholds.py`, `src/utils/helpers.py:706-712` + `src/ui/theme.py:94` (flag `processing_profiles_seeded_v2`).

- [ ] **Step 1:** `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json > before.txt` (guardar baseline)
- [ ] **Step 2:** Para CADA item acima: grep do nome em src/ e scripts/ (confirmar zero call sites de produção SOBRANDO — o inventário pode ter envelhecido), deletar função/arquivo/flag + teste correspondente. Na flag: LER helpers.py:700-715 e theme.py:90-98 antes — remover a flag E o no-op que a consome, sem quebrar o startup (se a remoção não for trivialmente segura, reportar e pular o item).
- [ ] **Step 3:** `python -m pytest -q` → verde (menos os testes deletados). `python scripts/eval_assignments.py tests/fixtures/eval/metodos_formais_golden.json > after.txt` → diff before/after VAZIO.
- [ ] **Step 4:** Commit: `chore(score): remove codigo morto do subsistema de atribuicao (5 itens)`

### Task 2: Unificar helpers e constantes (spec 0.B itens 2-6)

**Files:** Modify: `src/builder/artifacts/navigation.py:614` (importa `_NO_TIMELine_CATEGORIES`... usar o nome real `_NO_TIMELINE_CATEGORIES` de content_taxonomy), `src/builder/timeline/index.py` (`_signal_token_set`:93 → importa de content_taxonomy OU move pra módulo neutro `entry_signals`; fórmula inline :1973 → `margin_confidence(..., k=T.MARGIN_K_TOPIC)`; defaults de `_vote_unit_from_topic_candidates` :2036-2037 → `T.VOTE_MIN_SCORE`/`T.VOTE_DOMINANCE`), `src/builder/extraction/entry_signals.py:43`/`content_taxonomy.py:42` (`_extract_markdown_headings` — uma definição), `content_taxonomy.py:1158` (`0.65`→`T.UNIT_TAG`), `:1040` (`0.60`→`T.SUBUNIT_TAG`), `:848` (`CARD_SINGLE_CONF = METHOD_CAPS["card"]`), `src/builder/routing/file_map.py:908-909` (`DATE_STRONG_BOOST`/`DATE_WEAK_BOOST` → thresholds.py, importados).

- [ ] **Step 1:** Baseline before.txt (harness).
- [ ] **Step 2:** Item a item, LENDO o contexto real de cada linha (números podem ter mudado): mover/importar/substituir. Helpers movidos: escolher o módulo de menor acoplamento (evitar ciclos de import — content_taxonomy importa entry_signals? verificar; se ciclo, criar/usar módulo neutro existente tipo text/normalize ou routing/thresholds pra constantes).
- [ ] **Step 3:** Testes: os existentes cobrem os call sites; adicionar 1 teste de paridade por unificação onde houver risco (ex.: `test_margin_topic_usa_thresholds`: index._assign... produz mesmo valor que antes com k=0.20). Suíte verde + harness diff VAZIO.
- [ ] **Step 4:** Commit: `refactor(score): unifica helpers/constantes duplicados (6 itens, golden identico)`

### Task 3: Unificar `normalize_match_text` (spec 0.B.1 — ÚNICA task que pode mudar números)

**Files:** Modify: `src/builder/extraction/content_taxonomy.py:26` (cópia DIVERGENTE: preserva `+-./`), `src/builder/vision/card_evidence.py:12`, `src/builder/extraction/image_markdown.py:45`, `src/builder/timeline/signals.py:36` → todos re-importam de `src/builder/text/normalize.py`.

- [ ] **Step 1:** Investigar a divergência: `git log -p --follow -- src/builder/extraction/content_taxonomy.py | grep -B5 -A15 "def _normalize_match_text"` (ou ler o blame da função) + comparar comportamento: a cópia preserva `+-./` — casos reais que mudariam: "c++", "1.2", "isabelle/hol", datas "11/03". Rodar um diff de tokenização sobre os topic_texts do timeline real de MF com as duas versões e listar diferenças.
- [ ] **Step 2:** DECISÃO (documentar no commit): se as diferenças forem relevantes (datas/versões), a fonte única ganha parâmetro `keep: str = ""` (`normalize_match_text(text, keep="+-./")`) e o call site da taxonomy usa o parâmetro; senão, unificar seco. As outras 3 cópias: verificar com grep se são byte-idênticas à fonte — se sim, trocar por import direto.
- [ ] **Step 3:** Suíte completa + HARNESS COM MEDIÇÃO (esta task PODE mudar o golden): se acurácia cair, investigar caso a caso; se subir ou igual, registrar. Qualquer mudança de erro listada no commit.
- [ ] **Step 4:** Commit: `refactor(text): normalize_match_text unificado (4 copias mortas; divergencia=<decisao>)`

### Task 4: Fonte única nos artefatos e UI (fluxos #1, #2, #3, #7)

**Files:** Modify: `src/builder/artifacts/navigation.py:626-658` (coluna UNIDADE do FILE_MAP), `src/ui/dialogs.py:4117-4190, 4255-4290, 4344-4358, 4704-4747`.

- [ ] **Step 1:** Baseline harness + ler os 4 trechos INTEIROS antes de mexer.
- [ ] **Step 2 (navigation):** A coluna Unidade/Subtópico para de recomputar (`auto_map_entry_subtopic`+`derive_unit_from_topic_match`+`auto_map_entry_unit` saem): unidade = `entry.get("computed_unit_slug")` (+ sufixo `_(ambíguo)_` morre ou deriva de `unit_match_reasons` se a UI precisar); subtópico = `entry.get("computed_subunit_slug")` (campo existe no manifest). Plumbing local órfão removido. A coluna Confiança: usar `unit_match_confidence` da entry (campo existe) via o helper atual `infer_unit_confidence` se ele aceitar — LER e adaptar minimamente.
- [ ] **Step 3 (dialogs #3):** `_resolve_backlog_unit_status`/`_resolve_backlog_timeline_status` param de fazer regex na célula do FILE_MAP: lêem `entry.get("computed_unit_slug")`/`entry.get("computed_block_id")` direto (a entry está disponível no contexto — confirmar lendo; se o diálogo só tem a row do FILE_MAP, buscar a entry no manifest pelo id da row).
- [ ] **Step 4 (dialogs #2+#7):** DELETAR `_score_serialized_timeline_block` (scorer reimplementado, pesos divergentes) e o lookup período→re-score: o bloco do backlog = `computed_block_id` → lookup direto no `.timeline_index.json`. ~80 linhas mortas.
- [ ] **Step 5:** Testes: navigation tem testes (test_file_map_unit_mapping.py) — atualizar esperados SE o novo comportamento divergir (justificar: artefato espelha manifest). UI: `python -c "import src.ui.dialogs"` + teste de unidade pros helpers novos se o rig permitir. Suíte verde + harness diff VAZIO (o golden não passa por navigation/UI — deve ficar idêntico).
- [ ] **Step 6:** Commit: `fix(fonte-unica): FILE_MAP unidade + UI backlog leem computed_* (3 segundos cerebros mortos)`

### Task 5: MEDIR Fase 0 + registrar dívidas

- [ ] **Step 1:** Harness final da fase: deve estar idêntico ao baseline pré-Task-1 (exceto mudanças documentadas da Task 3). Suíte completa.
- [ ] **Step 2:** Registrar no plano-mestre (seção dívidas): #4 cronograma_health top-N com markdown vazio; #5 retag sem `_content_taxonomy` (inputs degradados vs pipeline); #6 índices lendo `e.tags` legado. Commit: `docs(plano-mestre): fase 0 do P4 fechada (golden identico) + dividas de fluxo`

---

## FASE 1 — SINAIS (um por task; MEDIR e commitar cada um)

### Task 6: S1 — CamelCase nos títulos

**Files:** Modify: `src/builder/text/normalize.py` (helper novo), `src/builder/extraction/entry_signals.py` (aplicação nos títulos). Test: `tests/test_camel_case_split.py` (criar).

- [ ] **Step 1: Testes que falham:**

```python
from src.builder.text.normalize import split_camel_case

def test_camel_case_basico():
    assert split_camel_case("LogicaDeHoare") == "Logica De Hoare"

def test_camel_case_com_digito():
    assert split_camel_case("LogicaDeHoare2") == "Logica De Hoare 2"

def test_sigla_pura_preservada():
    assert split_camel_case("IHC") == "IHC"
    assert split_camel_case("P1") == "P1"

def test_snake_e_espacos_intactos():
    assert split_camel_case("logicaProposicional_semantica") == "logica Proposicional_semantica"

def test_texto_normal_intacto():
    assert split_camel_case("provas por inducao") == "provas por inducao"
```

- [ ] **Step 2:** FAIL → implementar:

```python
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=\d)")


def split_camel_case(text: str) -> str:
    """Insere espaço em fronteiras minúscula→Maiúscula e letra→dígito.

    "LogicaDeHoare2" → "Logica De Hoare 2". Siglas puras (IHC, P1) intactas.
    Pré-processamento de TÍTULO antes do normalize (P4/S1) — não mexe na fonte
    única normalize_match_text."""
    return _CAMEL_BOUNDARY.sub(" ", text or "")
```

(ATENÇÃO: `(?<=[A-Za-z])(?=\d)` quebra "P1"→"P 1" — o teste exige "P1" intacto. Ajustar: fronteira letra→dígito só quando precedida de minúscula: `(?<=[a-z])(?=\d)`. Rodar os testes e calibrar a regex até os 5 passarem COMO ESCRITOS.)

- [ ] **Step 3:** Aplicação: em entry_signals, no(s) ponto(s) onde o TÍTULO da entry entra nos sinais (ler `collect_entry_unit_signals` e os builders de texto de título), envolver: `normalize_match_text(split_camel_case(title))`. SÓ título — não markdown, não tags.
- [ ] **Step 4:** Suíte + MEDIR. Esperado: `logicadehoare`/`logicadehoare2` ganham match exato "logica de hoare" → puxa bloco-10/11; medir unidade também (título alimenta unit signals — se a acurácia de unidade do golden ou a suíte regredirem, restringir o split ao caminho temporal e reportar).
- [ ] **Step 5:** Commit: `feat(score): S1 camelcase nos titulos (placar no corpo)`

### Task 7: S2 — IDF/raridade no scorer de bloco

**Files:** Modify: `src/builder/routing/file_map.py` (score do topic_text dentro de `score_entry_against_timeline_block` e/ou `score_timeline_block` — ler primeiro onde o topic_text pontua: :867-872 usa `score_text_against_row` sobre topic_tokens). Test: `tests/test_block_scorer_signals.py` (criar).

- [ ] **Step 1: Teste que falha** (comportamento, com blocos persistidos — reusar `_pblock` de tests/test_eval_golden_real.py):

```python
def test_token_raro_decide_entre_blocos():
    """'hoare' aparece em 1 bloco; 'logica' em 3. Entry sobre hoare tem que
    pontuar o bloco do hoare acima dos verbosos com 'logica'."""
    # blocos: b10 topic "logica de hoare"; b13 topic "logica programas dafny
    # colecoes arrays sequencias conjuntos"; b15 topic "logica programas
    # orientacao objetos dafny ghosts autocontrato"
    # entry/título+markdown: "logica de hoare triplas precondicao"
    # assert score(b10) > score(b13) e score(b10) > score(b15)
```

(Implementer escreve o corpo com a assinatura real do scorer — mesma mecânica do teste de T1/P0 `test_scoring_direto_funciona_com_bloco_persistido`. O assert é o COMPORTAMENTO; hoje falha — b13/b15 vencem por superfície.)

- [ ] **Step 2:** Implementar: função `block_token_weights(blocks) -> dict` (token → 1/df sobre os topic_texts dos blocos CANDIDATOS, mesma forma de file_map.py:136-140), computada no início do ranking (em `select_probable_period_for_entry` e no fallback — UMA vez por entry, não por bloco) e aplicada na pontuação do topic_text (peso multiplicativo no match de token). Constante de escala em thresholds.py (`IDF_WEIGHT` — começar 1.0 e calibrar no golden).
- [ ] **Step 3:** Suíte + MEDIR. Esperado: dafny2-4 voltam pro 13 (tokens raros "arrays/sequencias/conjuntos"); logicadehoare consolida 10.
- [ ] **Step 4:** Commit: `feat(score): S2 idf por raridade entre blocos candidatos (placar no corpo)`

### Task 8: S3 — Normalização por tamanho do topic

**Files:** Modify: `src/builder/routing/file_map.py` (mesmo trecho do S2). Test: `tests/test_block_scorer_signals.py` (append).

- [ ] **Step 1: Teste que falha:**

```python
def test_topic_verboso_nao_vence_por_superficie():
    """Topic com 10 tokens casando 3 não pode bater topic com 3 tokens casando 3."""
    # b_curto topic "logica de hoare" (3 tokens, casa 3)
    # b_verboso topic "logica programas dafny colecoes arrays sequencias conjuntos hoare aula extra" (casa 3-4 por acaso)
    # entry: "logica de hoare"
    # assert score(b_curto) > score(b_verboso)
```

- [ ] **Step 2:** Implementar: dividir a contribuição agregada do topic_text por `sqrt(len(topic_tokens))` (constante `TOPIC_LEN_NORM` em thresholds.py se precisar de ajuste fino). SÓ a parcela do topic — rows/sessions/datas intactas.
- [ ] **Step 3:** Suíte + MEDIR (atenção a regressões nos casos hoje certos por topic verboso "legítimo" — bloco-04 tem topic médio).
- [ ] **Step 4:** Commit: `feat(score): S3 normalizacao por tamanho do topic (placar no corpo)`

### Task 9: S4 — Sinal de ferramenta

**Files:** Modify: `src/builder/routing/file_map.py` (boost/penalidade no score do bloco), `src/builder/routing/thresholds.py` (constantes + mapa). Test: `tests/test_block_scorer_signals.py` (append).

- [ ] **Step 1: Testes que falham:**

```python
def test_ferramenta_isabelle_puxa_bloco_isabelle():
    # entry auto_tags ["ferramenta:isabelle"], título neutro "exemplos"
    # b05 topic "inducao arvores" vs b06 topic "interativa teoremas isabelle"
    # assert score(b06) > score(b05)

def test_ferramenta_conflitante_penaliza():
    # entry ferramenta:isabelle vs bloco topic "terminacao introducao dafny"
    # score com penalidade < score sem a tag (montar os 2 cenários)
```

- [ ] **Step 2:** Implementar: extrair `ferramenta:` das auto_tags da entry (signals já carregam tags — ler `collect_entry_unit_signals` pra ver onde; senão, adicionar ao dict de signals). Constantes em thresholds.py: `TOOL_BOOST` (+, começar 0.8), `TOOL_PENALTY` (−, começar 0.4), `TOOL_TOKENS = {"isabelle": {"isabelle"}, "dafny": {"dafny"}, "hoare": {"hoare"}}` (mapa mínimo, extensível). Boost quando token da ferramenta da entry ∈ topic do bloco; penalidade quando o bloco tem token de OUTRA ferramenta do mapa e nenhum da entry.
- [ ] **Step 3:** Suíte + MEDIR. Esperado: `provas`.thy → bloco-06; t1 ainda errado (precisa S5).
- [ ] **Step 4:** Commit: `feat(score): S4 sinal de ferramenta entry x topic (placar no corpo)`

### Task 10: S5 — Janela de assign (trabalhos)

**Files:** Modify: `src/builder/sources/moodle_labels.py` (extração da cascata de deadline), `src/builder/sources/moodle.py` (persistência junto do card map no import), `src/builder/extraction/content_taxonomy.py` (restrição no funil), `src/builder/timeline/card_block.py` (se o lookup precisar expor o assign_due). Test: `tests/test_moodle_labels.py` (append) + `tests/test_block_method_caps.py`-style pro funil.

- [ ] **Step 1: Testes que falham (extração):**

```python
def test_assign_duedate_estruturado():
    sec = {"name": "TDE", "modules": [
        {"modname": "assign", "name": "Sala de entrega",
         "dates": [{"label": "Vencimento:", "timestamp": 1778122740, "dataid": "duedate"}]}]}
    out = extract_assign_deadlines([sec])
    assert out["TDE"] == "2026-05-06"

def test_deadline_no_nome_do_forum():
    sec = {"name": "Verificação de Programas", "modules": [
        {"modname": "forum", "name": "Sala de Entrega (10/06)", "dates": []}]}
    out = extract_assign_deadlines([sec], year=2026)
    assert out[list(out)[0]] == "2026-06-10"

def test_assign_tem_precedencia_sobre_nome():
    # seção com assign.dates E forum com data no nome → vale o assign
    ...

def test_sem_fonte_sem_deadline():
    sec = {"name": "X", "modules": [{"modname": "forum", "name": "Forum geral"}]}
    assert extract_assign_deadlines([sec]) == {}
```

- [ ] **Step 2:** Implementar `extract_assign_deadlines(contents, year=0) -> {secao_sanitizada: iso_date}` em moodle_labels.py (cascata: assign.dates[duedate] → regex `\((\d{1,2}/\d{1,2}(?:/\d{4})?)\)` no name de assign/forum com nome contendo "entrega" → nada; timestamp via `datetime.fromtimestamp(...).date().isoformat()`). Persistência: no bloco do card map em `import_moodle_courses`, a entrada do card ganha `"assign_due": "<iso>"` quando houver (merge preserva manual como sempre — entrada manual sem assign_due ganha o campo? NÃO: manual é intocado; o assign_due vai só em entradas labels OU num dict separado retornado — decisão: campo opcional nas entradas derived; documentar).
- [ ] **Step 3: Restrição no funil (teste estilo method_caps com card map em tempdir):** entry de categoria em `{"trabalhos"}` (e código cujo card tem assign_due) com card sem gabarito de blocos: candidatos do scorer = blocos de aula com `period_start < assign_due` do card da entry (via source_section → card map). Teste: 2 blocos (um antes, um depois do due) + entry trabalho → o de depois NUNCA vence mesmo com score maior. Implementação em resolve_unit_block_tags: filtrar `instructional_blocks` quando a entry é trabalho e há assign_due. NUNCA decidir só pelo due (heurística reprovada — citar no comentário).
- [ ] **Step 4:** Suíte + MEDIR. Esperado: t1-2026-1 ×2 → restrição até 06/05 + conteúdo Isabelle (S4) → bloco-06.
- [ ] **Step 5:** Commit: `feat(score): S5 janela de assign restringe blocos de trabalho (placar no corpo)`

### Task 11: Fechamento — MEDIR final, retag real, placar

- [ ] **Step 1:** `python -m pytest -q` (verde) + MEDIR final. Meta: ≥43/48, confiante-e-errado 0, zero regressão nos casos certos pré-P4. `logicadehoare` → bloco-10 (aceite emblemático).
- [ ] **Step 2:** Regenerar card map/golden se a Task 10 mudou o formato (`build_golden_metodos_formais.py` — merge preserva decisões) e re-medir.
- [ ] **Step 3:** Retag no repo real: `python -m scripts.retag_manifest "C:\Users\Humberto\Documents\GitHub\Metodos-Formais-Tutor" --subject "Metodos-Formais" --write` — registrar mudanças de bloco e a distribuição de bands nova (espera-se as 9 baixas caírem pra 2-4).
- [ ] **Step 4:** Placar no plano-mestre (linha P4) + decisão sobre o que restou. Commit final: `feat(p4): scorer com 5 sinais fechado (placares no plano-mestre)`

---

## Self-review (na escrita)

- Spec Fase 0.A → Task 1; 0.B.2-6 → Task 2; 0.B.1 → Task 3; fluxos #1/#2/#3/#7 da
  segunda varredura → Task 4; dívidas #4/#5/#6 → Task 5. S1-S5 → Tasks 6-10;
  fechamento/metas → Task 11.
- Tasks 7-10 têm testes com corpo parcial (`...`/comentários): o COMPORTAMENTO está
  especificado em cada um; a mecânica (assinaturas reais do scorer/rig) o implementer
  adapta lendo os módulos citados — padrão que funcionou nas tasks 8/10 do ciclo anterior.
- Regra de ouro explícita: harness antes/depois em TODA task da Fase 0 (diff vazio),
  e MEDIR+commit por sinal na Fase 1.
- Tipos consistentes: `split_camel_case(str)->str`; `block_token_weights(blocks)->dict`;
  `extract_assign_deadlines(contents, year=0)->dict`; constantes novas SEMPRE em
  thresholds.py (IDF_WEIGHT, TOPIC_LEN_NORM, TOOL_BOOST, TOOL_PENALTY, TOOL_TOKENS).
