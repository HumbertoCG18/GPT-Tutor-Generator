# Unit & Subtopic Assignment Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir quatro bugs que impedem a atribuição correta de unidades e subtópicos no FILE_MAP, e adicionar a coluna de subtópico que estava faltando.

**Architecture:** Quatro mudanças cirúrgicas em três arquivos de lógica (`content_taxonomy.py`, `semantic_config.py`, `navigation.py`) seguidas de reprocessamento dos repositórios. Nenhuma mudança de interface pública ou schema — só lógica de scoring e filtragem.

**Tech Stack:** Python 3.11, pytest, repositórios em `C:\Users\Humberto\Documents\GitHub\*-Tutor`

---

## Contexto e causa raiz de cada bug

| # | Bug | Arquivo | Função | Efeito observado |
|---|---|---|---|---|
| B1 | `_looks_like_tool_candidate` usa substring match | `content_taxonomy.py` | `_looks_like_tool_candidate` | "processos" contém "so" → tópico `4.2 Comunicação e sincronização de processos` excluído da taxonomy |
| B2 | `build_content_taxonomy` não filtra noise | `content_taxonomy.py` | `build_content_taxonomy` | "Aulas expositivas...", "Uso de projetor..." viram tópicos e acumulam aliases errados |
| B3 | `_infer_tool_candidates` aceita siglas do curso | `semantic_config.py` | `_infer_tool_candidates` | "SO", "P1", "LM" entram em `known_tools`, amplificando B1 |
| B4 | Coluna Subtópico ausente no FILE_MAP | `navigation.py` | `render_low_token_file_map_md` | `preferred_topic_slug` calculado mas nunca exibido |

---

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `src/builder/extraction/content_taxonomy.py` | Corrige B1 e B2 |
| `src/builder/core/semantic_config.py` | Corrige B3 |
| `src/builder/artifacts/navigation.py` | Corrige B4 |
| `tests/test_tag_catalog.py` | Testes para B1 |
| `tests/test_file_map_unit_mapping.py` | Testes para B2 e B4 |
| `tests/test_semantic_profile.py` | Testes para B3 |

---

## Task 1 — Corrigir `_looks_like_tool_candidate` (B1)

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py:61-65`
- Test: `tests/test_tag_catalog.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao final de `tests/test_tag_catalog.py`:

```python
def test_looks_like_tool_candidate_does_not_match_short_tool_as_substring():
    from src.builder.extraction.content_taxonomy import _looks_like_tool_candidate

    # "so" como known_tool NÃO deve casar com "processos" (substring)
    profile = {"known_tools": ["so"]}
    assert not _looks_like_tool_candidate(
        "Comunicação e sincronização de processos", semantic_profile=profile
    )


def test_looks_like_tool_candidate_matches_short_tool_as_whole_word():
    from src.builder.extraction.content_taxonomy import _looks_like_tool_candidate

    # "so" como known_tool DEVE casar quando aparece como palavra isolada
    profile = {"known_tools": ["so"]}
    assert _looks_like_tool_candidate("Introdução ao SO e seus serviços", semantic_profile=profile)


def test_looks_like_tool_candidate_long_tool_still_uses_substring():
    from src.builder.extraction.content_taxonomy import _looks_like_tool_candidate

    # Ferramenta com 4+ chars continua usando substring (ex: "lean" em "leanpub")
    profile = {"known_tools": ["isabelle"]}
    assert _looks_like_tool_candidate("Prova com Isabelle/HOL", semantic_profile=profile)
```

- [ ] **Step 2: Rodar e confirmar que FALHA**

```
pytest tests/test_tag_catalog.py::test_looks_like_tool_candidate_does_not_match_short_tool_as_substring -v
```

Resultado esperado: `FAILED` (retorna True quando deveria retornar False).

- [ ] **Step 3: Implementar a correção**

Em `src/builder/extraction/content_taxonomy.py`, substituir a função `_looks_like_tool_candidate` (linhas 61-65):

```python
def _looks_like_tool_candidate(text: str, semantic_profile: Optional[dict] = None) -> bool:
    normalized = _normalize_match_text(text)
    effective_profile = merge_semantic_profile(semantic_profile)
    known_tools = list(effective_profile.get("known_tools") or [])
    normalized_tokens = set(normalized.split())
    for tool in known_tools:
        tool_norm = _normalize_match_text(tool)
        if not tool_norm:
            continue
        if len(tool_norm) < 4:
            if tool_norm in normalized_tokens:
                return True
        else:
            if tool_norm in normalized:
                return True
    return False
```

- [ ] **Step 4: Rodar todos os três testes novos**

```
pytest tests/test_tag_catalog.py::test_looks_like_tool_candidate_does_not_match_short_tool_as_substring tests/test_tag_catalog.py::test_looks_like_tool_candidate_matches_short_tool_as_whole_word tests/test_tag_catalog.py::test_looks_like_tool_candidate_long_tool_still_uses_substring -v
```

Resultado esperado: todos os três `PASSED`.

- [ ] **Step 5: Rodar suite completa para checar regressões**

```
pytest tests/ -v --tb=short
```

Resultado esperado: todos passando.

- [ ] **Step 6: Commit**

```
git add src/builder/extraction/content_taxonomy.py tests/test_tag_catalog.py
git commit -m "fix: word-boundary matching for short tool names in _looks_like_tool_candidate"
```

---

## Task 2 — Filtrar noise topics em `build_content_taxonomy` (B2)

**Files:**
- Modify: `src/builder/extraction/content_taxonomy.py:444-461`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao final de `tests/test_file_map_unit_mapping.py`:

```python
def test_build_content_taxonomy_filters_noise_topics_without_code():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
### Unidade 01 — Introdução ao estudo de sistemas operacionais
- [ ] **1.1** Evolução histórica
- [ ] **1.2** Chamadas de sistema
- [ ] Aulas expositivas nas quais se buscará a participação dos alunos em um processo de discussão.
- [ ] Uso de projetor multimídia.
- [ ] Uso de laboratório para elaboração de trabalhos práticos.
- [ ] Nesta unidade deve-se abordar a evolução histórica dos sistemas operacionais.
""".strip(),
        course_map_md="",
        glossary_md="",
    )

    unit = taxonomy["units"][0]
    slugs = [t["slug"] for t in unit["topics"]]

    # Tópicos com código devem estar presentes
    assert "11-evolucao-historica" in slugs
    assert "12-chamadas-de-sistema" in slugs

    # Noise topics sem código devem ter sido filtrados
    noise_slugs = [
        "uso-de-projetor-multimidia",
        "uso-de-laboratorio-para-elaboracao-de-trabalhos-praticos",
    ]
    for noise in noise_slugs:
        assert noise not in slugs, f"Noise topic '{noise}' should have been filtered"

    # Descrição longa (7+ palavras) sem código deve ser filtrada
    long_noise = [s for s in slugs if len(s) > 60]
    assert not long_noise, f"Long noise slug found: {long_noise}"
```

- [ ] **Step 2: Rodar e confirmar que FALHA**

```
pytest tests/test_file_map_unit_mapping.py::test_build_content_taxonomy_filters_noise_topics_without_code -v
```

Resultado esperado: `FAILED` — noise topics estão presentes na taxonomy atual.

- [ ] **Step 3: Implementar a correção**

Em `src/builder/extraction/content_taxonomy.py`, dentro de `build_content_taxonomy` (a partir da linha ~444), adicionar o filtro logo após calcular `topic_code`:

```python
    for unit_title, topics in units:
        unit_slug = normalize_unit_slug(unit_title)
        topic_records = []
        for topic in topics or []:
            current_topic_text = _collapse_ws(_strip_topic_code(topic_text(topic)))
            if not current_topic_text:
                continue
            topic_code = _extract_topic_code(topic_text(topic))
            # Filtrar noise topics: sem código numérico e que não passam na validação
            if not topic_code and not _is_valid_topic_candidate(
                current_topic_text, semantic_profile=semantic_profile
            ):
                continue
            topic_slug = slugify(current_topic_text)
            aliases = _glossary_aliases_for_topic(current_topic_text, unit_title, glossary_terms)
            topic_kind = "subtopic" if topic_code.count(".") >= 2 else "topic"
            topic_records.append(
                {
                    "code": topic_code,
                    "slug": topic_slug,
                    "label": current_topic_text,
                    "aliases": aliases,
                    "kind": topic_kind,
                    "unit_slug": unit_slug,
                }
            )
        result_units.append({"slug": unit_slug, "title": unit_title, "topics": _dedupe_taxonomy_topics(topic_records)})
```

- [ ] **Step 4: Rodar o teste novo**

```
pytest tests/test_file_map_unit_mapping.py::test_build_content_taxonomy_filters_noise_topics_without_code -v
```

Resultado esperado: `PASSED`.

- [ ] **Step 5: Verificar que tópico 4.2 agora aparece (regressão positiva)**

Adicionar ao mesmo arquivo:

```python
def test_build_content_taxonomy_includes_topic_42_comunicacao():
    taxonomy = _build_content_taxonomy(
        teaching_plan="""
### Unidade 03 — Programação concorrente
- [ ] **4.1** Programas multithreads
- [ ] **4.2** Comunicação e sincronização de processos
- [ ] **4.3** Primitivas de sincronização
""".strip(),
        course_map_md="",
        glossary_md="",
    )

    unit = taxonomy["units"][0]
    slugs = [t["slug"] for t in unit["topics"]]
    assert "41-programas-multithreads" in slugs
    assert "42-comunicacao-e-sincronizacao-de-processos" in slugs
    assert "43-primitivas-de-sincronizacao" in slugs
```

```
pytest tests/test_file_map_unit_mapping.py::test_build_content_taxonomy_includes_topic_42_comunicacao -v
```

Resultado esperado: `PASSED` — o tópico 4.2 agora aparece porque B1 (substring match) e B2 (noise filter) foram corrigidos juntos.

- [ ] **Step 6: Suite completa**

```
pytest tests/ -v --tb=short
```

- [ ] **Step 7: Commit**

```
git add src/builder/extraction/content_taxonomy.py tests/test_file_map_unit_mapping.py
git commit -m "fix: filter noise methodology topics from content_taxonomy unit topics"
```

---

## Task 3 — Mínimo de 3 chars para ferramentas inferidas (B3)

**Files:**
- Modify: `src/builder/core/semantic_config.py` (dentro de `_infer_tool_candidates`)
- Test: `tests/test_semantic_profile.py`

- [ ] **Step 1: Localizar a linha a modificar**

Em `src/builder/core/semantic_config.py`, dentro de `_infer_tool_candidates`, encontrar o loop:

```python
    for normalized, count in totals.items():
        raw = display.get(normalized, normalized)
        has_special_shape = (
            any(ch in raw for ch in "+#.")
            or any(ch.isdigit() for ch in raw)
            or any(ch.isupper() for ch in raw[1:])
        )
        if normalized in default_tools:
            accepted.append(normalized)
            continue
        if has_special_shape and count >= 1:
            accepted.append(normalized)
            continue
```

- [ ] **Step 2: Escrever o teste que falha**

Adicionar ao final de `tests/test_semantic_profile.py`:

```python
def test_infer_semantic_profile_excludes_course_abbreviations_from_known_tools():
    profile = infer_semantic_profile(
        course_name="Sistemas Operacionais",
        teaching_plan="""
### Unidade 01 — Introdução
- SO (Sistemas Operacionais) é um software
- Horário: LM 19:15 - 20:45

### Unidade 02 — Processos
- P1 em 07/05/2026
- TP1 entrega 30/04/2026
""",
        course_map_md="",
        glossary_md="",
        strong_headings=[],
    )

    known = profile.get("known_tools", [])
    # Siglas curtas do curso não devem ser ferramentas
    assert "so" not in known, f"'so' should not be a known tool, got: {known}"
    assert "p1" not in known, f"'p1' should not be a known tool"
    assert "lm" not in known, f"'lm' (sala de aula) should not be a known tool"
    assert "tp1" not in known, f"'tp1' should not be a known tool"
```

- [ ] **Step 3: Rodar e confirmar que FALHA**

```
pytest tests/test_semantic_profile.py::test_infer_semantic_profile_excludes_course_abbreviations_from_known_tools -v
```

Resultado esperado: `FAILED` — "so", "p1" etc. estão em `known_tools` atualmente.

- [ ] **Step 4: Implementar a correção**

Em `src/builder/core/semantic_config.py`, dentro de `_infer_tool_candidates`, adicionar o guard de comprimento mínimo no início do loop:

```python
    for normalized, count in totals.items():
        if len(normalized) < 3:
            continue
        raw = display.get(normalized, normalized)
        has_special_shape = (
            any(ch in raw for ch in "+#.")
            or any(ch.isdigit() for ch in raw)
            or any(ch.isupper() for ch in raw[1:])
        )
        if normalized in default_tools:
            accepted.append(normalized)
            continue
        if has_special_shape and count >= 1:
            accepted.append(normalized)
            continue
        if context_hits.get(normalized, 0) >= 1 and count >= 2 and len(normalized) >= 3:
            accepted.append(normalized)
            continue
        if context_hits.get(normalized, 0) >= 2 and count >= 3 and 3 <= len(normalized) <= 18:
            accepted.append(normalized)
```

- [ ] **Step 5: Rodar o teste novo**

```
pytest tests/test_semantic_profile.py::test_infer_semantic_profile_excludes_course_abbreviations_from_known_tools -v
```

Resultado esperado: `PASSED`.

- [ ] **Step 6: Confirmar que ferramentas legítimas de 2 chars (ex: Z3) ainda funcionam via defaults**

Adicionar ao mesmo arquivo:

```python
def test_infer_semantic_profile_short_default_tools_still_accepted():
    # Z3 está nos defaults (base), não precisa ser inferido do corpus
    from src.builder.core.semantic_config import load_semantic_defaults
    defaults = load_semantic_defaults()
    # Z3 pode ter comprimento 2 mas vem dos defaults, não do corpus
    # O teste valida que defaults continuam sendo aceitos independente do tamanho
    profile = infer_semantic_profile(
        course_name="Verificação Formal",
        teaching_plan="Usar Z3 para satisfatibilidade\n",
        course_map_md="",
        glossary_md="",
        strong_headings=["Z3"],
    )
    known = profile.get("known_tools", [])
    assert "z3" in known, f"Z3 (default tool) should be in known_tools, got: {known}"
```

```
pytest tests/test_semantic_profile.py::test_infer_semantic_profile_short_default_tools_still_accepted -v
```

Resultado esperado: `PASSED`.

- [ ] **Step 7: Suite completa**

```
pytest tests/ -v --tb=short
```

- [ ] **Step 8: Commit**

```
git add src/builder/core/semantic_config.py tests/test_semantic_profile.py
git commit -m "fix: require minimum 3 chars for inferred tool candidates to exclude course abbreviations"
```

---

## Task 4 — Adicionar coluna Subtópico ao FILE_MAP (B4)

**Files:**
- Modify: `src/builder/artifacts/navigation.py:583-793`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao final de `tests/test_file_map_unit_mapping.py`:

```python
def test_file_map_md_includes_subtopic_column_in_header():
    profile = SubjectProfile(
        name="Sistemas Operacionais",
        teaching_plan="""
### Unidade 02 — Gerência do Processador
- [ ] **3.2** Escalonamento
- [ ] **3.3** Algoritmos de escalonamento
""".strip(),
    )
    entries = [
        {
            "id": "2604-escalonamento",
            "title": "26.04 Algoritimos de Escalonamento",
            "category": "material-de-aula",
            "auto_tags": ["topico:32-escalonamento"],
        }
    ]
    course_meta = {
        "course_name": "Sistemas Operacionais",
        "_timeline_context_for_tests": {},
    }
    result = file_map_md(course_meta, entries, subject_profile=profile)

    # Cabeçalho deve ter coluna Subtópico
    assert "Subtópico" in result, "FILE_MAP header should contain 'Subtópico' column"


def test_file_map_md_shows_subtopic_label_for_matched_entry():
    profile = SubjectProfile(
        name="Sistemas Operacionais",
        teaching_plan="""
### Unidade 02 — Gerência do Processador
- [ ] **3.2** Escalonamento
""".strip(),
    )
    entries = [
        {
            "id": "2604-escalonamento",
            "title": "Algoritimos de Escalonamento",
            "category": "material-de-aula",
            "auto_tags": ["topico:32-escalonamento"],
        }
    ]
    course_meta = {
        "course_name": "Sistemas Operacionais",
        "_timeline_context_for_tests": {},
    }
    result = file_map_md(course_meta, entries, subject_profile=profile)

    # Deve mostrar o label do subtópico (sem **bold** markdown)
    assert "3.2" in result and "Escalonamento" in result
```

- [ ] **Step 2: Rodar e confirmar que FALHA**

```
pytest tests/test_file_map_unit_mapping.py::test_file_map_md_includes_subtopic_column_in_header tests/test_file_map_unit_mapping.py::test_file_map_md_shows_subtopic_label_for_matched_entry -v
```

Resultado esperado: `FAILED` — coluna não existe.

- [ ] **Step 3: Adicionar import `re` se necessário e construir `topic_labels`**

Em `src/builder/artifacts/navigation.py`, dentro de `render_low_token_file_map_md`, logo após a linha que define `unit_tag_index` (linha ~599), adicionar:

```python
    # Mapa slug → label limpo de cada tópico da taxonomy
    _bold_re = re.compile(r"\*\*([^*]+)\*\*")
    topic_labels: dict = {}
    for _u in content_taxonomy.get("units", []) or []:
        for _t in (_u.get("topics", []) or []):
            _slug = str(_t.get("slug", "") or "")
            _label = str(_t.get("label", "") or "")
            if _slug and _label:
                topic_labels[_slug] = _bold_re.sub(r"\1", _label).strip()
```

Verificar que `import re` já existe no topo do arquivo. Se não existir, adicionar.

- [ ] **Step 4: Atualizar o cabeçalho da tabela**

Substituir as linhas 634-637 em `src/builder/artifacts/navigation.py`:

```python
    lines += [
        "| # | Título | Categoria | Quando abrir | Prioridade | Markdown | Seções | Unidade | Subtópico | Confiança | Período |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
```

- [ ] **Step 5: Adicionar `subtopic_label` na linha de cada entrada**

No loop de entries (a partir da linha ~639), logo após a linha que define `preferred_topic_slug` (após o bloco de unit assignment que termina em ~745), adicionar:

```python
        subtopic_label = topic_labels.get(preferred_topic_slug, "")
```

Substituir a linha de `lines.append` do row principal (linhas 750-753):

```python
        lines.append(
            f"| {i} | {title} | {category} | {entry_usage_hint(entry)} | "
            f"{entry_priority_label(entry)} | {md_cell} | {sections or ''} | "
            f"{unit or ''} | {subtopic_label or ''} | {confidence} | {period or ''} |"
        )
```

- [ ] **Step 6: Atualizar a linha de rastreabilidade para 11 colunas**

Substituir a linha 773 em `src/builder/artifacts/navigation.py`:

```python
            lines.append(f"|  | ↳ rastreabilidade |  | {'; '.join(details)} |  |  |  |  |  |  |  |")
```

- [ ] **Step 7: Atualizar a Legenda**

Substituir o bloco de legenda (linhas 775-788):

```python
    lines += [
        "",
        "## Legenda",
        "",
        "- **Quando abrir**: atalho semântico para reduzir leitura desnecessária.",
        "- **Prioridade**: `alta` costuma merecer contexto antes dos demais.",
        "- **Seções**: principais headers `##` do markdown aprovado/curado.",
        "- **Unidade**: slug da unidade do COURSE_MAP.",
        "- **Subtópico**: label do tópico específico dentro da unidade (ex: `3.2 Escalonamento`).",
        "- **Confiança**: quão confiável está o roteamento de unidade atual.",
        "- **Período**: janela compacta da timeline associada à unidade.",
        "- **Markdown**: `A revisar` indica que o item ainda só tem extração de `staging/`, sem promoção final.",
        "- **Categoria**: tipo do arquivo; não deve ser alterada pelo tutor.",
        "",
    ]
```

- [ ] **Step 8: Rodar os testes novos**

```
pytest tests/test_file_map_unit_mapping.py::test_file_map_md_includes_subtopic_column_in_header tests/test_file_map_unit_mapping.py::test_file_map_md_shows_subtopic_label_for_matched_entry -v
```

Resultado esperado: ambos `PASSED`.

- [ ] **Step 9: Suite completa**

```
pytest tests/ -v --tb=short
```

Resultado esperado: todos passando.

- [ ] **Step 10: Commit**

```
git add src/builder/artifacts/navigation.py tests/test_file_map_unit_mapping.py
git commit -m "feat: add Subtópico column to FILE_MAP showing resolved topic label"
```

---

## Task 5 — Verificação de regressão e reprocessamento dos repositórios

**Files:** Nenhum arquivo de código — verificação manual e execução dos builds.

- [ ] **Step 1: Confirmar que todos os testes passam**

```
pytest tests/ -v --tb=short
```

Resultado esperado: zero falhas.

- [ ] **Step 2: Verificar que taxonomy de SO agora tem tópico 4.2 e não tem noise**

```python
# Rodar no terminal Python interativo ou script ad-hoc:
import sys, json, pathlib
sys.path.insert(0, r'C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator')
from src.builder.engine import _build_file_map_content_taxonomy_from_course
# (usa o repositório de SO para validar end-to-end)
```

Ou simplesmente reprocessar o repositório e inspecionar o `.content_taxonomy.json` gerado — deve conter `42-comunicacao-e-sincronizacao-de-processos` e não deve conter `uso-de-projetor-multimidia`.

- [ ] **Step 3: Reprocessar Sistemas Operacionais**

No repositório `C:\Users\Humberto\Documents\GitHub\Sistemas-Operacionais-Tutor`, executar pedagogical_regeneration (via UI ou CLI do GPT-Tutor-Generator). Verificar:
- `course/.content_taxonomy.json`: 7 unidades, sem noise topics, tópico 4.2 presente
- `manifest.json`: auto_tags sem `ferramenta:de`, `ferramenta:so`
- `course/FILE_MAP.md`: nova coluna Subtópico preenchida corretamente

- [ ] **Step 4: Reprocessar os demais repositórios**

Repetir para: `Engenharia-Software-2-Tutor`, `Inteligencia-Artifical-Tutor`, `Metodos-Formais-Tutor`.

- [ ] **Step 5: Commit final com evidência**

```
git add src/ tests/
git commit -m "fix: complete unit/subtopic assignment pipeline — all repos reprocessed"
```

---

## Self-Review

**Cobertura do spec:**
- B1 (`_looks_like_tool_candidate`): Task 1 ✓
- B2 (noise topics): Task 2 ✓
- B3 (siglas do curso em known_tools): Task 3 ✓
- B4 (coluna Subtópico): Task 4 ✓
- Reprocessamento de repositórios: Task 5 ✓

**Checagem de tipos:**
- `_build_content_taxonomy` é o alias do engine para `build_content_taxonomy` — parâmetro `semantic_profile` já existe na assinatura original ✓
- `topic_labels: dict` populado antes do loop de entries, usado dentro do loop ✓
- Linha de rastreabilidade atualizada de 10 para 11 colunas ✓
- `re` module: navigation.py provavelmente já importa `re`; se não, adicionar no Step 3 da Task 4 ✓

**Sem placeholders:** Todos os steps têm código concreto ✓
