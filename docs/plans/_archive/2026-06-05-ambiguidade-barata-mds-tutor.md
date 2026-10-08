# Ambiguidade Barata nos MDs do Tutor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seis correções pontuais de clareza nos geradores/prompts que o tutor lê (contagem de modos, índice do modo assignment, label de clamp do glossário, remoção de gerador morto, sufixo redundante no FILE_MAP, ordem de navegação contraditória).

**Architecture:** Edições cirúrgicas em `src/builder/artifacts/pedagogy.py`, `repo.py`, `navigation.py`, `prompts.py`. Sem mudança estrutural. Protocolo de fim de sessão fica fora (vai no student_state).

**Tech Stack:** Python 3.13, pytest. `file_map_md`/`glossary_md` testados via `src.builder.engine` (deps injetadas pré-vinculadas). `file_map_md(course_meta, entries)` aceita `course_meta["_unit_index_for_tests"]` e `["_period_index_for_tests"]` (ver `tests/test_file_map_unit_mapping.py`).

**Base:** 887 testes verdes.

---

### Task A: `pedagogy.py` (`modes_md`) — "quatro modos" → "cinco modos"

NOTA-CHAVE: a string da linha 240 vive dentro de `modes_md(course_meta=None,
subject_profile=None)` (def na linha 228), NÃO em `pedagogy_md`. `modes_md`
gera MODES.md. Testes existentes já chamam `modes_md({"course_name": "..."})`
(ver `tests/test_code_review_profiles.py:8`).

**Files:**
- Modify: `src/builder/artifacts/pedagogy.py:240`
- Test: `tests/test_core.py` (nova classe `TestModesMdClarity`)

- [ ] **Step 1: Escrever o teste que falha**

```python
class TestModesMdClarity:
    def test_mode_count_says_five(self):
        from src.builder.artifacts.pedagogy import modes_md
        text = modes_md({"course_name": "Teste"})
        assert "opera em cinco modos" in text
        assert "opera em quatro modos" not in text
```

- [ ] **Step 2: Rodar o teste — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestModesMdClarity::test_mode_count_says_five -v`
Expected: FAIL — "opera em cinco modos" ausente.

- [ ] **Step 3: Implementar**

Em `src/builder/artifacts/pedagogy.py`, trocar:

```
O tutor opera em quatro modos. Cada modo tem objetivo, postura e formato de resposta diferentes.
```

por:

```
O tutor opera em cinco modos. Cada modo tem objetivo, postura e formato de resposta diferentes.
```

- [ ] **Step 4: Rodar o teste — verificar que passa**

Run: `python -m pytest tests/test_core.py::TestModesMdClarity::test_mode_count_says_five -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/pedagogy.py tests/test_core.py
git commit -m "fix(modes): correct mode count from four to five"
```

---

### Task F: `pedagogy.py` (`modes_md`) — modo `assignment` referencia os dois índices

**Files:**
- Modify: `src/builder/artifacts/pedagogy.py:270`
- Test: `tests/test_core.py` (`TestModesMdClarity`)

- [ ] **Step 1: Escrever o teste que falha**

```python
    def test_assignment_mode_points_to_both_indices(self):
        from src.builder.artifacts.pedagogy import modes_md
        text = modes_md({"course_name": "Teste"})
        assert "exercises/EXERCISE_INDEX.md" in text
        assert "assignments/ASSIGNMENT_INDEX.md" in text
```

- [ ] **Step 2: Rodar o teste — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestModesMdClarity::test_assignment_mode_points_to_both_indices -v`
Expected: FAIL — `assignments/ASSIGNMENT_INDEX.md` ausente.

- [ ] **Step 3: Implementar**

Trocar a linha 270:

```
- Consulte `exercises/EXERCISE_INDEX.md` para localizar o exercício no mapa da disciplina
```

por:

```
- Consulte `exercises/EXERCISE_INDEX.md` (listas/práticas) e `assignments/ASSIGNMENT_INDEX.md` (trabalhos) para localizar o item no mapa da disciplina
```

- [ ] **Step 4: Rodar o teste — verificar que passa**

Run: `python -m pytest tests/test_core.py::TestModesMdClarity::test_assignment_mode_points_to_both_indices -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/pedagogy.py tests/test_core.py
git commit -m "fix(modes): assignment mode references both exercise and assignment indices"
```

---

### Task B: `repo.py` — corrigir label de clamp do `glossary_md`

NOTA-CHAVE: o label só apareceria no output via truncamento (`max_chars=14000`
hardcoded), o que é frágil de forçar. O `repo.glossary_md` recebe
`clamp_navigation_artifact_fn` como kwarg injetado — então o teste chama
`repo.glossary_md` direto com um clamp-spy que captura o `label`, determinístico.
Assinatura real (repo.py:1591):
`glossary_md(course_meta, subject_profile=None, *, root_dir=None, manifest_entries=None, parse_units_from_teaching_plan_fn, topic_text_fn, collect_glossary_evidence_fn, find_glossary_evidence_fn, seed_glossary_fields_fn, clamp_navigation_artifact_fn)`.

**Files:**
- Modify: `src/builder/artifacts/repo.py:1658-1662`
- Test: `tests/test_core.py` (nova classe `TestGlossaryClampLabel`)

- [ ] **Step 1: Escrever o teste que falha**

```python
class TestGlossaryClampLabel:
    def test_glossary_clamp_label_is_glossary(self):
        from src.builder.artifacts import repo
        captured = {}
        def spy_clamp(text, *, max_chars, label):
            captured["label"] = label
            return text
        repo.glossary_md(
            {"course_name": "Teste"},
            None,
            parse_units_from_teaching_plan_fn=lambda plan: [],
            topic_text_fn=lambda topic: "",
            collect_glossary_evidence_fn=lambda root_dir: [],
            find_glossary_evidence_fn=lambda term, unit, evidence: "",
            seed_glossary_fields_fn=lambda term, unit, ev: ("", "", ""),
            clamp_navigation_artifact_fn=spy_clamp,
        )
        assert captured["label"] == "course/GLOSSARY.md"
```

- [ ] **Step 2: Rodar o teste — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestGlossaryClampLabel -v`
Expected: FAIL — `captured["label"] == "course/COURSE_MAP.md"`. (Se em vez de
FAIL der ERROR por algum dos stubs de dep ter aridade errada, ajuste a aridade
do lambda ao que o código realmente chama — NÃO mude o código de produção pra
satisfazer o stub.)

- [ ] **Step 3: Implementar**

Em `src/builder/artifacts/repo.py`, no `return` de `glossary_md`, trocar:

```python
    return clamp_navigation_artifact_fn(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )
```

por:

```python
    return clamp_navigation_artifact_fn(
        "\n".join(lines),
        max_chars=14000,
        label="course/GLOSSARY.md",
    )
```

- [ ] **Step 4: Rodar o teste — verificar que passa**

Run: `python -m pytest tests/test_core.py::TestGlossaryClampLabel -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_core.py
git commit -m "fix(glossary): correct clamp label course/COURSE_MAP.md -> course/GLOSSARY.md"
```

---

### Task C: `navigation.py` — remover `render_course_map_md` (código morto)

**Files:**
- Modify: `src/builder/artifacts/navigation.py:288-404` (deletar a função inteira)
- Test: `tests/test_core.py` (`TestDeadCodeRemoval`)

- [ ] **Step 1: Confirmar zero referências (pré-condição)**

Run: `git grep -n "render_course_map_md" -- src/ tests/`
Expected: SÓ a definição em `src/builder/artifacts/navigation.py`. Se houver
qualquer caller em `src/` ou `tests/`, PARE e reporte (a remoção não é segura).

- [ ] **Step 2: Escrever o teste que falha**

```python
class TestDeadCodeRemoval:
    def test_render_course_map_md_is_gone(self):
        import src.builder.artifacts.navigation as nav
        assert not hasattr(nav, "render_course_map_md")
```

- [ ] **Step 3: Rodar o teste — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestDeadCodeRemoval::test_render_course_map_md_is_gone -v`
Expected: FAIL — `render_course_map_md` ainda existe.

- [ ] **Step 4: Implementar — deletar a função**

Remover o bloco inteiro de `def render_course_map_md(` (linha 288) até a última
linha da função (o `return clamp_navigation_artifact(...)` em ~399 e seu
fechamento, terminando antes de `def _emit_support_lines(` na linha 406).
Manter exatamente duas linhas em branco entre o fim de `_get_entry_sections`
(linha 285) e `def _emit_support_lines`. Não tocar em mais nada.

- [ ] **Step 5: Rodar o teste + suíte de navegação**

Run: `python -m pytest tests/test_core.py::TestDeadCodeRemoval::test_render_course_map_md_is_gone -v`
Expected: PASS
Run: `python -m pytest tests/test_file_map_unit_mapping.py -q`
Expected: PASS (nenhuma regressão).

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/navigation.py tests/test_core.py
git commit -m "refactor(navigation): remove dead legacy render_course_map_md generator"
```

---

### Task D: `navigation.py` — remover só o sufixo `_(baixa confiança)_` do FILE_MAP

**Files:**
- Modify: `src/builder/artifacts/navigation.py:764-770`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Construir empiricamente um input que dispara `_(baixa confiança)_`**

O sufixo `_(baixa confiança)_` aparece quando `auto_map_entry_unit` retorna
`match.slug` verdade, `match.ambiguous == False` e `match.confidence < 0.45`.
Para um teste determinístico de integração, monte um `course_meta` com **uma
única unidade** (não ambíguo, pois só há um candidato) e um entry com conteúdo
que casa fracamente (match fraco → confiança baixa). Use o mesmo harness de
`tests/test_file_map_unit_mapping.py::test_file_map_md_omits_period_for_ambiguous_match`
como base (`file_map_md(course_meta, entries)` com `_unit_index_for_tests`).

Rode um probe rápido (script python efêmero) variando o conteúdo/título do entry
até o output atual conter `_(baixa confiança)_`. Documente o input exato no teste.

Se após esforço razoável NÃO conseguir disparar o ramo de forma estável (pode ser
quase inalcançável na prática), PARE e reporte: nesse caso a remoção vira
limpeza pura e o teste deve ser substituído por uma asserção de que o renderer
nunca emite a string `_(baixa confiança)_` num conjunto representativo de entries
(regressão), mais um comentário no código. Reporte qual caminho seguiu.

- [ ] **Step 2: Escrever o teste que falha (com o input do Step 1)**

```python
def test_file_map_md_drops_low_confidence_suffix_keeps_confidence_column():
    course_meta = {
        "course_name": "<...>",
        "_unit_index_for_tests": [ {"title": "<única unidade>", "topics": [...]} ],
        "_period_index_for_tests": { "<slug>": "<período>" },
    }
    entries = [ { "<entry que casa fraco, não-ambíguo>" } ]
    result = file_map_md(course_meta, entries)
    assert "_(baixa confiança)_" not in result   # sufixo removido
    assert "| Baixa |" in result or "Baixa" in result  # coluna Confiança mantém o sinal
```

- [ ] **Step 3: Rodar o teste — verificar que falha**

Run: `python -m pytest "tests/test_file_map_unit_mapping.py::test_file_map_md_drops_low_confidence_suffix_keeps_confidence_column" -v`
Expected: FAIL — `_(baixa confiança)_` presente no output.

- [ ] **Step 4: Implementar**

Trocar (navigation.py:764-770):

```python
            unit = (
                f"{match.slug} _(ambíguo)_"
                if match.slug and match.ambiguous
                else f"{match.slug} _(baixa confiança)_"
                if match.slug and match.confidence < 0.45
                else match.slug
            )
```

por:

```python
            unit = (
                f"{match.slug} _(ambíguo)_"
                if match.slug and match.ambiguous
                else match.slug
            )
```

- [ ] **Step 5: Rodar o teste + os 3 testes do caso ambíguo**

Run: `python -m pytest "tests/test_file_map_unit_mapping.py::test_file_map_md_drops_low_confidence_suffix_keeps_confidence_column" "tests/test_file_map_unit_mapping.py::test_file_map_md_omits_period_for_ambiguous_match" -v`
Expected: PASS (o caso `_(ambíguo)_` permanece intacto).
Run: `python -m pytest tests/test_file_map_unit_mapping.py tests/test_tag_scoring.py -q`
Expected: PASS (nenhum dos testes de `ambíguo` quebra).

- [ ] **Step 6: Commit**

```bash
git add src/builder/artifacts/navigation.py tests/test_file_map_unit_mapping.py
git commit -m "refactor(file-map): drop redundant low-confidence unit suffix (keep ambiguous reason)"
```

---

### Task E: `prompts.py` — alinhar ordem de navegação do contrato estrutural

**Files:**
- Modify: `src/builder/artifacts/prompts.py:26`
- Test: `tests/test_core.py` (nova classe `TestNavOrderContract`)

- [ ] **Step 1: Escrever o teste que falha**

```python
class TestNavOrderContract:
    def test_structural_contract_lists_course_map_first(self):
        from src.builder.artifacts.prompts import _prompt_structural_artifact_contract_lines
        lines = _prompt_structural_artifact_contract_lines()
        first = lines[0]
        assert "COURSE_MAP.md" in first
        # COURSE_MAP deve aparecer antes de FILE_MAP na primeira instrução
        assert first.index("COURSE_MAP.md") < first.index("FILE_MAP.md")
```

- [ ] **Step 2: Rodar o teste — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestNavOrderContract -v`
Expected: FAIL — hoje a linha 0 lista FILE_MAP antes de COURSE_MAP.

- [ ] **Step 3: Implementar**

Em `src/builder/artifacts/prompts.py`, trocar a linha 26:

```python
        "1. Leia `course/FILE_MAP.md` e `course/COURSE_MAP.md` antes de entrar no conteúdo.",
```

por:

```python
        "1. Leia `course/COURSE_MAP.md` e `course/FILE_MAP.md` antes de entrar no conteúdo.",
```

(Não tocar na linha 27 — só nomeia ambos, sem ordem de prioridade.)

- [ ] **Step 4: Rodar o teste — verificar que passa**

Run: `python -m pytest tests/test_core.py::TestNavOrderContract -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/prompts.py tests/test_core.py
git commit -m "fix(prompts): align structural contract nav order to COURSE_MAP first"
```

---

### Task FINAL: Verificação + backlog/ROUTER

**Files:**
- Modify: `docs/superpowers/BACKLOG.md`
- Modify: `.mex/ROUTER.md`

- [ ] **Step 1: Rodar a suíte completa**

Run: `python -m pytest -q`
Expected: PASS, 0 failures.

- [ ] **Step 2: Marcar 🟢 (parcial) no backlog**

Em `docs/superpowers/BACKLOG.md`, no item "Higiene dos MDs do tutor", marcar como
ENTREGUE os bullets 🟢 cobertos (quatro→cinco modos; assignment/exercises;
`render_course_map_md` legado removido; sufixo FILE_MAP; clamp GLOSSARY parcial;
ordem de navegação do contrato) com referência aos commits. Manter abertos:
fim de sessão (vai no student_state), `prompts.py:564` se algo restar, demais 🟡.

- [ ] **Step 3: Atualizar ROUTER**

Em `.mex/ROUTER.md`, seção "Working", adicionar linha curta sobre a rodada de
ambiguidade barata (contagem de modos, índices do modo assignment, label de
clamp do glossário, remoção do gerador morto, sufixo do FILE_MAP, ordem de
navegação).

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/BACKLOG.md .mex/ROUTER.md
git commit -m "docs: mark cheap-ambiguity MD cleanup delivered"
```

---

## Self-Review

**Cobertura do spec:** A→Task A, F→Task F, B→Task B, C→Task C, D→Task D, E→Task E.
G explicitamente fora de escopo. ✔

**Placeholders:** Tasks A, B, E, F têm teste + impl 100% fixos (função/assinatura
confirmadas: linha 240/270 ficam em `modes_md`; `repo.glossary_md` testado com
clamp-spy; `_prompt_structural_artifact_contract_lines` retorna `list[str]`).
Task D é a única com input de RED descoberto empiricamente (depende do scorer),
com fallback explícito (regressão + comentário) e exigência de reportar o
caminho. ✔

**Consistência de tipos:** labels seguem `course/<NOME>.md`.
`file_map_md(course_meta, entries)` é a assinatura dos testes existentes;
`modes_md({"course_name": ...})` idem (`test_code_review_profiles.py`). ✔

**Risco residual:** Task D (RED determinístico). Mitigado pelo fallback no Step 1.
