# Limpeza de Tabelas Mortas nos MDs do Tutor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remover placeholders permanentes (`[a preencher]`, seções de padrões/incidência nunca preenchidas, comentário TODO vazando) dos geradores de MD que o tutor lê, corrigir labels de clamp e dropar a coluna `Status` morta do assignment.

**Architecture:** Edições cirúrgicas em `src/builder/artifacts/repo.py` (6 geradores). Branches com entries reais ficam quase byte-idênticos (exceção: coluna `Status` removida); branches vazios viram frase curta de estado; seções placeholder removidas; cada `clamp_navigation_artifact` usa o label do próprio artefato.

**Tech Stack:** Python 3.13, pytest. Geradores testados via `src.builder.engine` (clamp pré-vinculado), exceto `cronograma_detalhado_md` (importado de `src.builder.artifacts.repo`, assinatura `(course_meta, entries, code_curation, timeline_blocks, subject_profile=None)`).

**Base:** 878 testes verdes. `FileEntry` já importado em `tests/test_core.py`.

---

### Task 1: `exam_index_md` — remover seções mortas, frase vazia, label

**Files:**
- Modify: `src/builder/artifacts/repo.py:753-797`
- Test: `tests/test_core.py` (adicionar à classe `TestNewGenerators`)

- [ ] **Step 1: Escrever os testes que falham**

Adicionar em `tests/test_core.py`, dentro de `class TestNewGenerators`:

```python
    def test_exam_index_empty_has_phrase_no_placeholder(self):
        from src.builder.engine import exam_index_md
        r = exam_index_md(self.COURSE_META, [])
        assert "Nenhuma prova mapeada ainda" in r
        assert "[a preencher]" not in r
        assert "Incidência de tópicos por prova" not in r
        assert "Padrões de questão observados" not in r

    def test_exam_index_entries_and_label(self):
        from src.builder.engine import exam_index_md
        r = exam_index_md(self.COURSE_META, [self._e("provas", "P1", ".pdf")])
        assert "P1" in r
        assert "Provas disponíveis" in r
```

- [ ] **Step 2: Rodar os testes — verificar que falham**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_exam_index_empty_has_phrase_no_placeholder tests/test_core.py::TestNewGenerators::test_exam_index_entries_and_label -v`
Expected: FAIL — `[a preencher]`/`Incidência` ainda presentes; frase ausente.

- [ ] **Step 3: Implementar — substituir o corpo do gerador**

Em `src/builder/artifacts/repo.py`, trocar o trecho de `lines.append("| Arquivo | Tipo | Prova ...")` até o `return` final de `exam_index_md` por:

```python
    if entries:
        lines.append("| Arquivo | Tipo | Prova | Observação | Padrão do professor |")
        lines.append("|---|---|---|---|---|")
        for entry in entries:
            tipo = "foto" if entry.category == "fotos-de-prova" else "original"
            lines.append(
                f"| {Path(entry.source_path).name} | {tipo} | {entry.title} "
                f"| {entry.notes or ''} | {entry.professor_signal or ''} |"
            )
    else:
        lines.append("_Nenhuma prova mapeada ainda._")
    lines.append("")

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=12000,
        label="course/EXAM_INDEX.md",
    )
```

(O bloco `lines = [...]` com título/intro/`## Provas disponíveis` permanece inalterado.)

- [ ] **Step 4: Rodar os testes — verificar que passam**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_exam_index_empty_has_phrase_no_placeholder tests/test_core.py::TestNewGenerators::test_exam_index_entries_and_label -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_core.py
git commit -m "refactor(exam-index): drop dead incidence/patterns sections, fix clamp label"
```

---

### Task 2: `assignment_index_md` — dropar coluna Status, frase vazia, remover Padrões, label

**Files:**
- Modify: `src/builder/artifacts/repo.py:800-820`
- Test: `tests/test_core.py` (`TestNewGenerators`)

- [ ] **Step 1: Escrever os testes que falham**

```python
    def test_assignment_index_drops_status_column(self):
        from src.builder.engine import assignment_index_md
        r = assignment_index_md(self.COURSE_META, [self._e("trabalhos", "T1", ".pdf")])
        assert "T1" in r
        assert "Status" not in r
        assert "pendente" not in r

    def test_assignment_index_empty_phrase_no_placeholder(self):
        from src.builder.engine import assignment_index_md
        r = assignment_index_md(self.COURSE_META, [])
        assert "Nenhum trabalho mapeado ainda" in r
        assert "[a preencher]" not in r
        assert "Padrões do professor" not in r
```

- [ ] **Step 2: Rodar os testes — verificar que falham**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_assignment_index_drops_status_column tests/test_core.py::TestNewGenerators::test_assignment_index_empty_phrase_no_placeholder -v`
Expected: FAIL — `Status`/`pendente`/`[a preencher]`/`Padrões do professor` ainda presentes.

- [ ] **Step 3: Implementar**

Trocar o bloco `if entries: ... return clamp_navigation_artifact(...)` de `assignment_index_md` por:

```python
    if entries:
        lines += ["| Arquivo | Título | Unidade |", "|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} | {e.tags or ''} |")
    else:
        lines.append("_Nenhum trabalho mapeado ainda._")
    lines.append("")
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=12000, label="course/ASSIGNMENT_INDEX.md")
```

- [ ] **Step 4: Rodar os testes — verificar que passam**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_assignment_index_drops_status_column tests/test_core.py::TestNewGenerators::test_assignment_index_empty_phrase_no_placeholder tests/test_core.py::TestNewGenerators::test_assignment_index_empty tests/test_core.py::TestNewGenerators::test_assignment_index_entries -v`
Expected: PASS (os 2 testes antigos `test_assignment_index_empty`/`_entries` continuam verdes: asserem "ASSIGNMENT_INDEX" e "T1").

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_core.py
git commit -m "refactor(assignment-index): drop dead Status column, empty phrase, fix clamp label"
```

---

### Task 3: `code_index_md` — remover bloco de patterns (templates a/b), fallback vazio, labels

**Files:**
- Modify: `src/builder/artifacts/repo.py:844-903`
- Test: `tests/test_core.py` (`TestNewGenerators`)

- [ ] **Step 1: Escrever os testes que falham**

```python
    def test_code_index_no_patterns_placeholder_empty(self):
        from src.builder.engine import code_index_md
        r = code_index_md(self.COURSE_META, [])
        assert "[a preencher]" not in r
        assert "Preencha conforme analisar" not in r

    def test_code_index_no_patterns_placeholder_flat(self):
        from src.builder.engine import code_index_md
        r = code_index_md(self.COURSE_META, [self._e("codigo-professor", "linked_list")])
        assert "linked_list" in r
        assert "[a preencher]" not in r
        assert "Preencha conforme analisar" not in r
```

- [ ] **Step 2: Rodar os testes — verificar que falham**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_code_index_no_patterns_placeholder_empty tests/test_core.py::TestNewGenerators::test_code_index_no_patterns_placeholder_flat -v`
Expected: FAIL — `[a preencher]`/`Preencha conforme analisar` presentes nos templates (a) e (b).

- [ ] **Step 3a: Implementar — template (a), trecho `if not prof_entries:` até o `return`**

Trocar (primeira ocorrência, ancorada por `if not prof_entries:`):

```python
        if not prof_entries:
            lines += [profile["code_index_empty"], ""]
        lines += [
            profile["code_index_patterns"],
            "",
            "<!-- Preencha conforme analisar o código -->",
            "- [a preencher]",
            "",
        ]
        result = "\n".join(lines)
        return clamp_navigation_artifact(result, max_chars=14000, label="course/COURSE_MAP.md")
```

por:

```python
        if not prof_entries:
            lines += [profile["code_index_empty"], ""]
        result = "\n".join(lines)
        return clamp_navigation_artifact(result, max_chars=14000, label="course/CODE_INDEX.md")
```

- [ ] **Step 3b: Implementar — template (b), trecho `else:` até o `return`**

Trocar (ancorado por `else:` antes do bloco de patterns):

```python
        else:
            lines += [profile["code_index_empty"], ""]
        lines += [
            profile["code_index_patterns"],
            "",
            "<!-- Preencha conforme analisar o código -->",
            "- [a preencher]",
            "",
        ]
        result = "\n".join(lines)
        return clamp_navigation_artifact(result, max_chars=14000, label="course/COURSE_MAP.md")
```

por:

```python
        else:
            lines += [profile["code_index_empty"], ""]
        result = "\n".join(lines)
        return clamp_navigation_artifact(result, max_chars=14000, label="course/CODE_INDEX.md")
```

- [ ] **Step 3c: Implementar — fallback per-entry**

Trocar:

```python
                conceito = e.professor_signal or "[a preencher]"
```

por:

```python
                conceito = e.professor_signal or ""
```

- [ ] **Step 4: Rodar os testes — verificar que passam**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_code_index_no_patterns_placeholder_empty tests/test_core.py::TestNewGenerators::test_code_index_no_patterns_placeholder_flat tests/test_core.py::TestNewGenerators::test_code_index_professor tests/test_core.py::TestNewGenerators::test_code_index_empty -v`
Expected: PASS (antigos `test_code_index_professor`/`test_code_index_empty` verdes: "linked_list" e "Nenhum arquivo" intactos).

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_core.py
git commit -m "refactor(code-index): drop dead patterns placeholder, empty concept fallback, fix clamp labels"
```

---

### Task 4: `cronograma_detalhado_md` — remover comentário TODO vazando

**Files:**
- Modify: `src/builder/artifacts/repo.py:1042`
- Test: `tests/test_core.py` (nova classe `TestCronogramaDetalhado`)

- [ ] **Step 1: Escrever o teste que falha**

```python
class TestCronogramaDetalhado:
    def test_no_todo_comment_leaks(self):
        from src.builder.artifacts.repo import cronograma_detalhado_md
        from src.models.core import FileEntry
        entry = FileEntry(source_path="/fake/ll.py", file_type="code",
                          category="codigo-professor", title="linked_list")
        curation = {"entries": {entry.id(): {"summary": {"primary_block_id": "b1"}}}}
        blocks = [{"id": "b1", "period_label": "Aula 1", "topics": ["Listas"]}]
        r = cronograma_detalhado_md({"course_name": "ED"}, [entry], curation, blocks)
        assert "TODO (material-agnostic refactor)" not in r
        assert "linked_list" in r
```

(`FileEntry` vem de `src.models.core` — mesmo import já usado em `tests/test_core.py:4239`.)

- [ ] **Step 2: Rodar o teste — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestCronogramaDetalhado::test_no_todo_comment_leaks -v`
Expected: FAIL — `TODO (material-agnostic refactor)` presente no output (uma vez por block).

- [ ] **Step 3: Implementar**

Trocar:

```python
        lines += ["", "<!-- TODO (material-agnostic refactor): PDFs, exercícios, imagens -->", "", "---", ""]
```

por:

```python
        lines += ["", "---", ""]
```

- [ ] **Step 4: Rodar o teste — verificar que passa**

Run: `python -m pytest tests/test_core.py::TestCronogramaDetalhado::test_no_todo_comment_leaks -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_core.py
git commit -m "refactor(cronograma): drop leaking material-agnostic TODO comment"
```

---

### Task 5: `whiteboard_index_md` — frase vazia, remover Padrões pedagógicos, label

**Files:**
- Modify: `src/builder/artifacts/repo.py:1123-1135`
- Test: `tests/test_core.py` (`TestNewGenerators`)

- [ ] **Step 1: Escrever os testes que falham**

```python
    def test_whiteboard_empty_phrase_no_placeholder(self):
        from src.builder.engine import whiteboard_index_md
        r = whiteboard_index_md(self.COURSE_META, [])
        assert "Nenhum registro de quadro ainda" in r
        assert "[a preencher]" not in r
        assert "Padrões pedagógicos" not in r

    def test_whiteboard_entries_no_patterns_section(self):
        from src.builder.engine import whiteboard_index_md
        e = self._e("quadro-branco", "AulaHash", ".png")
        e.professor_signal = "usa colisão linear"
        r = whiteboard_index_md(self.COURSE_META, [e])
        assert "colisão linear" in r
        assert "Padrões pedagógicos" not in r
```

- [ ] **Step 2: Rodar os testes — verificar que falham**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_whiteboard_empty_phrase_no_placeholder tests/test_core.py::TestNewGenerators::test_whiteboard_entries_no_patterns_section -v`
Expected: FAIL — `[a preencher]`/`Padrões pedagógicos` presentes.

- [ ] **Step 3: Implementar**

Trocar o bloco `if entries: ... return clamp_navigation_artifact(...)` de `whiteboard_index_md` por:

```python
    if entries:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |", "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} | {e.tags or ''} | {e.professor_signal or ''} |")
    else:
        lines.append("_Nenhum registro de quadro ainda._")
    lines.append("")
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=12000, label="course/WHITEBOARD_INDEX.md")
```

- [ ] **Step 4: Rodar os testes — verificar que passam**

Run: `python -m pytest tests/test_core.py::TestNewGenerators::test_whiteboard_empty_phrase_no_placeholder tests/test_core.py::TestNewGenerators::test_whiteboard_entries_no_patterns_section tests/test_core.py::TestNewGenerators::test_whiteboard_professor_signal tests/test_core.py::TestNewGenerators::test_whiteboard_empty -v`
Expected: PASS (antigos `test_whiteboard_professor_signal`/`test_whiteboard_empty` verdes).

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_core.py
git commit -m "refactor(whiteboard-index): empty phrase, drop dead patterns section, fix clamp label"
```

---

### Task 6: `exercise_index_md` — remover linha placeholder vazia + atualizar teste existente

**Files:**
- Modify: `src/builder/artifacts/repo.py:2090-2095`
- Test: `tests/test_core.py:4435` (`test_exercise_index_empty_state_stays_short`)

- [ ] **Step 1: Atualizar o teste existente para o novo comportamento**

Em `tests/test_core.py`, trocar o corpo de `test_exercise_index_empty_state_stays_short`:

```python
    def test_exercise_index_empty_state_stays_short(self):
        result = exercise_index_md({"course_name": "Teste"}, [])
        assert "| [a preencher] | | | | | |" in result
        assert "Mapeamento de exercícios por tópico" not in result
```

por:

```python
    def test_exercise_index_empty_state_stays_short(self):
        result = exercise_index_md({"course_name": "Teste"}, [])
        assert "[a preencher]" not in result
        assert "Adicione listas ou provas antigas" in result
        assert "Mapeamento de exercícios por tópico" not in result
```

- [ ] **Step 2: Rodar o teste — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestExerciseIndexLowToken::test_exercise_index_empty_state_stays_short -v`
Expected: FAIL — `[a preencher]` ainda presente no output.

- [ ] **Step 3: Implementar**

Trocar:

```python
    else:
        lines.append("| [a preencher] | | | | | |")
        lines += [
            "",
            "> Adicione listas ou provas antigas para o tutor conseguir sugerir prática com baixo custo de contexto.",
        ]
```

por:

```python
    else:
        lines += [
            "> Adicione listas ou provas antigas para o tutor conseguir sugerir prática com baixo custo de contexto.",
        ]
```

- [ ] **Step 4: Rodar o teste — verificar que passa**

Run: `python -m pytest tests/test_core.py::TestExerciseIndexLowToken::test_exercise_index_empty_state_stays_short -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/repo.py tests/test_core.py
git commit -m "refactor(exercise-index): drop dead [a preencher] row in empty state"
```

---

### Task 7: Verificação final — suíte completa + atualizar backlog/ROUTER

**Files:**
- Modify: `docs/superpowers/BACKLOG.md`
- Modify: `.mex/ROUTER.md`

- [ ] **Step 1: Rodar a suíte completa**

Run: `python -m pytest -q`
Expected: PASS, 0 failures (878 + novos testes). Investigar qualquer regressão (provável fonte: outro teste que asseria os strings removidos).

- [ ] **Step 2: Marcar o grupo 🟠 como entregue no backlog**

Em `docs/superpowers/BACKLOG.md`, no item "Higiene dos MDs do tutor", mover os bullets 🟠 (exam_index 790/794, assignment 822/825, CRONOGRAMA 1049, whiteboard/exercise) para ENTREGUE com referência aos commits desta task; manter 🟡/🟢 como abertos.

- [ ] **Step 3: Atualizar o estado do projeto no ROUTER**

Em `.mex/ROUTER.md`, seção "Working", adicionar linha curta registrando a limpeza de tabelas mortas dos MDs do tutor (labels de clamp corrigidos, placeholders removidos, coluna Status do assignment removida).

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/BACKLOG.md .mex/ROUTER.md
git commit -m "docs: mark dead-table cleanup delivered (group 🟠)"
```

---

## Self-Review

**Cobertura do spec:** 6 geradores do spec → Tasks 1-6. Teste a atualizar (`test_core.py:4437`) → Task 6 Step 1. Labels de clamp → embutidos em Tasks 1,2,3,5. Coluna Status → Task 2. Fallback code_index → Task 3c. ✔ Sem lacunas.

**Placeholders:** todos os steps de código mostram código exato. Comandos com output esperado. ✔

**Consistência de tipos:** frases de estado vazio são strings literais consistentes ("Nenhuma prova mapeada ainda", "Nenhum trabalho mapeado ainda", "Nenhum registro de quadro ainda"). Labels seguem o padrão `course/<NOME>.md`. `code_index_md` mantém `code_index_empty`/`code_index_patterns` do profile — só `code_index_patterns` deixa de ser emitido (não é removido do profile, pra não quebrar outros leitores). ✔

**Risco residual:** Task 3 tem 2 edits idênticos exceto pela linha-âncora (`if not prof_entries:` vs `else:`) — o plano inclui a âncora em cada `old_string` pra garantir unicidade.
