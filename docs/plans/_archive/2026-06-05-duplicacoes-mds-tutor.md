# Consolidação de Duplicações nos MDs do Tutor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar fonte única (constante + helpers) para a sequência pedagógica e o escopo de prova em `src/builder/artifacts/pedagogy.py`, eliminando a contradição das 3 ordens (canônica: Intuição antes de Definição) e a duplicação dos pesos P1/P2/P3.

**Architecture:** Uma constante `PEDAGOGICAL_SEQUENCE` + 4 helpers em `pedagogy.py`. Os 3 geradores (`pedagogy_md`, `modes_md`, `output_templates_md`) passam a derivar dela via concatenação (literais estáticos + `"\n".join(_helper())`), em vez de hardcode.

**Tech Stack:** Python 3.11/3.13, pytest. Geradores importáveis de `src.builder.artifacts.pedagogy`. `modes_md(course_meta=None, subject_profile=None)`, `output_templates_md(course_meta=None, subject_profile=None)`, `pedagogy_md()`.

**Base:** 893 testes verdes. Testes existentes de `tests/test_code_review_profiles.py` cobrem code_review (não afetado).

---

### Task 1: Constante canônica + helpers

**Files:**
- Modify: `src/builder/artifacts/pedagogy.py` (adicionar constante + 4 helpers no topo do módulo, após os imports, antes de `pedagogy_md`)
- Test: `tests/test_core.py` (nova classe `TestPedagogicalSequenceHelpers`)

- [ ] **Step 1: Escrever os testes que falham**

```python
class TestPedagogicalSequenceHelpers:
    def test_sequence_order_intuicao_before_definicao(self):
        from src.builder.artifacts.pedagogy import PEDAGOGICAL_SEQUENCE
        labels = [s["label"] for s in PEDAGOGICAL_SEQUENCE]
        assert labels.index("Intuição") < labels.index("Definição")

    def test_sequence_has_standardized_labels(self):
        from src.builder.artifacts.pedagogy import PEDAGOGICAL_SEQUENCE
        labels = [s["label"] for s in PEDAGOGICAL_SEQUENCE]
        assert labels == [
            "Contexto", "Intuição", "Definição", "Exemplo mínimo",
            "Aplicação", "Erros comuns", "Exercício guiado", "Resumo",
        ]

    def test_full_lines_numbered(self):
        from src.builder.artifacts.pedagogy import _pedagogical_sequence_full_lines
        lines = _pedagogical_sequence_full_lines()
        assert lines[0] == "1. **Contexto** — Por que este conceito existe? Que problema resolve?"
        assert lines[1].startswith("2. **Intuição** — ")
        assert len(lines) == 8

    def test_compact_arrow(self):
        from src.builder.artifacts.pedagogy import _pedagogical_sequence_compact
        c = _pedagogical_sequence_compact()
        assert c == "Contexto → Intuição → Definição → Exemplo mínimo → Aplicação → Erros comuns → Exercício guiado → Resumo"

    def test_template_lines(self):
        from src.builder.artifacts.pedagogy import _pedagogical_sequence_template_lines
        lines = _pedagogical_sequence_template_lines()
        assert lines[0] == "**Contexto:** [contexto em 1-2 frases]"
        assert lines[2] == "**Definição:** [definição precisa, com LaTeX se necessário]"
        assert len(lines) == 8

    def test_exam_scope_rule_lines(self):
        from src.builder.artifacts.pedagogy import _exam_scope_rule_lines
        lines = _exam_scope_rule_lines()
        assert lines[0] == "As provas são cumulativas mas com peso progressivo:"
        assert any("(~70%)" in l and "(~30%)" in l for l in lines)  # P2
        assert any("(~20%)" in l and "(~10%)" in l for l in lines)  # P3
```

- [ ] **Step 2: Rodar — verificar que falham**

Run: `python -m pytest tests/test_core.py::TestPedagogicalSequenceHelpers -v`
Expected: FAIL — ImportError (constante/helpers não existem).

- [ ] **Step 3: Implementar — adicionar no topo de `pedagogy.py` (após imports, antes de `def pedagogy_md`)**

```python
# Fonte única da sequência pedagógica (ordem canônica: Intuição antes de
# Definição, decidido 2026-06-05). PEDAGOGY/MODES/OUTPUT_TEMPLATES derivam daqui.
PEDAGOGICAL_SEQUENCE = [
    {"label": "Contexto",         "full": "Por que este conceito existe? Que problema resolve?", "template": "[contexto em 1-2 frases]"},
    {"label": "Intuição",         "full": "Como pensar sobre isso sem formalismo",              "template": "[analogia ou imagem mental]"},
    {"label": "Definição",        "full": "O que é, em termos precisos",                        "template": "[definição precisa, com LaTeX se necessário]"},
    {"label": "Exemplo mínimo",   "full": "O caso mais simples possível",                       "template": "[exemplo mais simples possível]"},
    {"label": "Aplicação",        "full": "Como aparece na disciplina / em computação",         "template": "[conexão com o conteúdo do curso]"},
    {"label": "Erros comuns",     "full": "O que os alunos costumam confundir",                 "template": "[erro mais comum]"},
    {"label": "Exercício guiado", "full": "Uma pergunta para o aluno aplicar",                  "template": "[pergunta para o aluno aplicar]"},
    {"label": "Resumo",           "full": "Uma frase que captura a essência",                   "template": "[uma frase que captura a essência]"},
]


def _pedagogical_sequence_full_lines() -> list[str]:
    return [f"{i}. **{s['label']}** — {s['full']}" for i, s in enumerate(PEDAGOGICAL_SEQUENCE, 1)]


def _pedagogical_sequence_compact() -> str:
    return " → ".join(s["label"] for s in PEDAGOGICAL_SEQUENCE)


def _pedagogical_sequence_template_lines() -> list[str]:
    return [f"**{s['label']}:** {s['template']}" for s in PEDAGOGICAL_SEQUENCE]


def _exam_scope_rule_lines() -> list[str]:
    return [
        "As provas são cumulativas mas com peso progressivo:",
        "",
        "- **P1** → cobre tudo do início até a P1. Foco total no conteúdo pré-P1.",
        "- **P2** → cobre tudo até a P2. Foco principal no conteúdo entre P1 e P2 (~70%). Conteúdo da P1 ainda cai, mas com menos peso (~30%).",
        "- **P3** → cobre tudo até a P3. Foco principal no conteúdo entre P2 e P3 (~70%). Conteúdo entre P1-P2 cai menos (~20%). Conteúdo pré-P1 cai pouco (~10%).",
    ]
```

- [ ] **Step 4: Rodar — verificar que passam**

Run: `python -m pytest tests/test_core.py::TestPedagogicalSequenceHelpers -v`
Expected: PASS (6 testes).

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/pedagogy.py tests/test_core.py
git commit -m "feat(pedagogy): canonical PEDAGOGICAL_SEQUENCE + exam-scope helpers (single source)"
```

---

### Task 2: `pedagogy_md` deriva da fonte única

**Files:**
- Modify: `src/builder/artifacts/pedagogy.py` (`pedagogy_md`, ~152-225)
- Test: `tests/test_core.py` (nova classe `TestPedagogyMdCanonical`)

- [ ] **Step 1: Escrever os testes que falham**

```python
class TestPedagogyMdCanonical:
    def test_intuicao_before_definicao(self):
        from src.builder.artifacts.pedagogy import pedagogy_md
        t = pedagogy_md()
        assert t.index("**Intuição**") < t.index("**Definição**")

    def test_exam_scope_uses_canonical_rule(self):
        from src.builder.artifacts.pedagogy import pedagogy_md, _exam_scope_rule_lines
        t = pedagogy_md()
        for line in _exam_scope_rule_lines():
            if line:
                assert line in t
        assert "→ foco primário:" not in t  # diagrama ASCII antigo removido
```

- [ ] **Step 2: Rodar — verificar que falham**

Run: `python -m pytest tests/test_core.py::TestPedagogyMdCanonical -v`
Expected: FAIL — ordem atual é Definição→Intuição; diagrama ASCII ainda presente.

- [ ] **Step 3a: Implementar — sequência (substituir os 8 itens hardcoded)**

Trocar:

```
Para cada conceito novo, siga esta sequência:

1. **Contexto** — Por que este conceito existe? Que problema resolve?
2. **Definição** — O que é, em termos precisos
3. **Intuição** — Como pensar sobre isso sem formalismo
4. **Exemplo mínimo** — O caso mais simples possível
5. **Aplicação** — Como aparece na disciplina / em computação
6. **Erros comuns** — O que os alunos costumam confundir
7. **Exercício guiado** — Uma pergunta para o aluno aplicar
8. **Resumo** — Uma frase que captura a essência

## Adaptação de profundidade
```

por (quebra o literal e injeta o helper):

```
Para cada conceito novo, siga esta sequência:

""" + "\n".join(_pedagogical_sequence_full_lines()) + """

## Adaptação de profundidade
```

- [ ] **Step 3b: Implementar — escopo de prova (substituir o diagrama ASCII)**

Trocar:

```
As provas seguem um modelo cumulativo com foco progressivo:

```
P1: cobre TODO o conteúdo do início até a P1
        → foco: 100% no conteúdo pré-P1

P2: cobre TODO o conteúdo do início até a P2
        → foco primário:   conteúdo entre P1 e P2  (~70%)
        → foco secundário: conteúdo pré-P1          (~30%)

P3: cobre TODO o conteúdo do início até a P3
        → foco primário:   conteúdo entre P2 e P3  (~70%)
        → foco secundário: conteúdo entre P1 e P2  (~20%)
        → foco terciário:  conteúdo pré-P1          (~10%)
```

**Regra prática para o tutor:**
```

por:

```
""" + "\n".join(_exam_scope_rule_lines()) + """

**Regra prática para o tutor:**
```

NOTA: depois de 3a+3b, o `return` de `pedagogy_md` vira concatenação de pedaços
de string literal `+ "\n".join(...)`. Confirme que cada `"""` abre/fecha
corretamente e que o módulo importa sem SyntaxError.

- [ ] **Step 4: Rodar — verificar que passam + import sanity**

Run: `python -c "import src.builder.artifacts.pedagogy"`
Expected: sem erro.
Run: `python -m pytest tests/test_core.py::TestPedagogyMdCanonical -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/pedagogy.py tests/test_core.py
git commit -m "refactor(pedagogy-md): derive sequence + exam scope from canonical source"
```

---

### Task 3: `modes_md` deriva da fonte única (study + exam_prep)

**Files:**
- Modify: `src/builder/artifacts/pedagogy.py` (`modes_md`, ~228-302)
- Test: `tests/test_core.py` (nova classe `TestModesMdCanonical`)

- [ ] **Step 1: Escrever os testes que falham**

```python
class TestModesMdCanonical:
    def test_study_format_uses_compact_sequence(self):
        from src.builder.artifacts.pedagogy import modes_md, _pedagogical_sequence_compact
        t = modes_md({"course_name": "Teste"})
        assert _pedagogical_sequence_compact() in t

    def test_exam_scope_uses_canonical_rule(self):
        from src.builder.artifacts.pedagogy import modes_md, _exam_scope_rule_lines
        t = modes_md({"course_name": "Teste"})
        for line in _exam_scope_rule_lines():
            if line:
                assert line in t
```

- [ ] **Step 2: Rodar — verificar que falham**

Run: `python -m pytest tests/test_core.py::TestModesMdCanonical -v`
Expected: FAIL — study format atual é `Contexto → Intuição → Definição → Exemplo → Exercício` (5, sem "mínimo"/"Aplicação"/etc), não bate com o compact canônico.

- [ ] **Step 3a: Implementar — study "Formato de resposta"**

Trocar:

```
**Formato de resposta:**
- Contexto → Intuição → Definição → Exemplo → Exercício

---

## assignment — Resolução de exercício
```

por:

```
**Formato de resposta:**
- """ + _pedagogical_sequence_compact() + """

---

## assignment — Resolução de exercício
```

- [ ] **Step 3b: Implementar — exam_prep escopo**

Trocar:

```
As provas são cumulativas mas com peso progressivo:

- **P1** → cobre tudo do início até a P1. Foco total no conteúdo pré-P1.
- **P2** → cobre tudo até a P2. Foco principal no conteúdo entre P1 e P2 (~70%). Conteúdo da P1 ainda cai, mas com menos peso (~30%).
- **P3** → cobre tudo até a P3. Foco principal no conteúdo entre P2 e P3 (~70%). Conteúdo entre P1-P2 cai menos (~20%). Conteúdo pré-P1 cai pouco (~10%).

**Postura:**
```

por:

```
""" + "\n".join(_exam_scope_rule_lines()) + """

**Postura:**
```

(O helper reproduz exatamente estas linhas — o output de `modes_md` fica
byte-idêntico aqui; o ganho é a fonte única.)

- [ ] **Step 4: Rodar — verificar que passam + code_review intacto**

Run: `python -c "import src.builder.artifacts.pedagogy"`
Run: `python -m pytest tests/test_core.py::TestModesMdCanonical tests/test_code_review_profiles.py -v`
Expected: PASS (incl. os testes de code_review existentes).

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/pedagogy.py tests/test_core.py
git commit -m "refactor(modes-md): derive study sequence + exam scope from canonical source"
```

---

### Task 4: `output_templates_md` deriva da fonte única (study template)

**Files:**
- Modify: `src/builder/artifacts/pedagogy.py` (`output_templates_md`, ~356-386)
- Test: `tests/test_core.py` (nova classe `TestOutputTemplatesCanonical`)

- [ ] **Step 1: Escrever os testes que falham**

```python
class TestOutputTemplatesCanonical:
    def test_study_template_uses_canonical_labels(self):
        from src.builder.artifacts.pedagogy import output_templates_md
        t = output_templates_md({"course_name": "Teste"})
        # rótulos antigos sumiram
        assert "Por que existe:" not in t
        assert "Definição formal:" not in t
        assert "Cuidado com:" not in t
        assert "Agora você:" not in t
        # rótulos canônicos presentes, Intuição antes de Definição
        assert "**Contexto:**" in t
        assert "**Intuição:**" in t
        assert "**Definição:**" in t
        assert t.index("**Intuição:**") < t.index("**Definição:**")
```

- [ ] **Step 2: Rodar — verificar que falha**

Run: `python -m pytest tests/test_core.py::TestOutputTemplatesCanonical -v`
Expected: FAIL — rótulos antigos ("Por que existe", "Definição formal", "Cuidado com", "Agora você") ainda presentes.

- [ ] **Step 3: Implementar — bloco template study**

Trocar:

```
**Por que existe:** [contexto em 1-2 frases]

**Intuição:** [analogia ou imagem mental]

**Definição formal:**
[definição precisa, com LaTeX se necessário]

**Exemplo mínimo:**
[exemplo mais simples possível]

**Como aparece na disciplina:**
[conexão com o conteúdo do curso]

**Cuidado com:**
[erro mais comum]

**Agora você:** [pergunta para o aluno aplicar o conceito]
```

por:

```
""" + "\n\n".join(_pedagogical_sequence_template_lines()) + """
```

- [ ] **Step 4: Rodar — verificar que passa + code_review intacto**

Run: `python -c "import src.builder.artifacts.pedagogy"`
Run: `python -m pytest tests/test_core.py::TestOutputTemplatesCanonical tests/test_code_review_profiles.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/builder/artifacts/pedagogy.py tests/test_core.py
git commit -m "refactor(output-templates): derive study template from canonical sequence"
```

---

### Task 5: Guard DRY + verificação + backlog/ROUTER

**Files:**
- Test: `tests/test_core.py` (`TestPedagogySingleSource`)
- Modify: `docs/superpowers/BACKLOG.md`, `.mex/ROUTER.md`

- [ ] **Step 1: Escrever o guard DRY**

```python
class TestPedagogySingleSource:
    def test_exam_scope_identical_in_pedagogy_and_modes(self):
        from src.builder.artifacts.pedagogy import pedagogy_md, modes_md, _exam_scope_rule_lines
        ped = pedagogy_md()
        mod = modes_md({"course_name": "Teste"})
        for line in _exam_scope_rule_lines():
            if line:
                assert line in ped and line in mod

    def test_sequence_labels_drive_all_three(self):
        from src.builder.artifacts.pedagogy import (
            pedagogy_md, modes_md, output_templates_md, PEDAGOGICAL_SEQUENCE,
        )
        ped = pedagogy_md()
        tpl = output_templates_md({"course_name": "Teste"})
        for s in PEDAGOGICAL_SEQUENCE:
            assert s["label"] in ped
            assert s["label"] in tpl
```

- [ ] **Step 2: Rodar o guard — verificar que passa**

Run: `python -m pytest tests/test_core.py::TestPedagogySingleSource -v`
Expected: PASS (já verde, pois Tasks 2-4 fizeram a derivação).

- [ ] **Step 3: Rodar a suíte completa**

Run: `python -m pytest -q`
Expected: PASS, 0 failures.

- [ ] **Step 4: Atualizar backlog + ROUTER**

Em `docs/superpowers/BACKLOG.md`, no item "Higiene dos MDs do tutor", marcar
ENTREGUE os 🟡 cobertos (sequência pedagógica 3 ordens → fonte única; escopo de
prova P1/P2/P3 → helper único). Manter aberto: 5 modos inline (🟡, rodada
própria); registrar code_review posture e CRONOGRAMA/CODE como não-redundância
(decidido).
Em `.mex/ROUTER.md`, seção "Working", linha curta sobre a fonte única da
sequência pedagógica + escopo de prova.

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py docs/superpowers/BACKLOG.md .mex/ROUTER.md
git commit -m "test+docs: DRY guard for pedagogy single source; mark dup cleanup delivered"
```

---

## Self-Review

**Cobertura do spec:** Componente 1 (sequência) → Tasks 1-4; Componente 2 (escopo
prova) → Tasks 1-3; guard DRY → Task 5. Fora de escopo (5 modos, code_review,
cronograma/code) documentado. ✔

**Placeholders:** todos os Steps têm old→new exato. As edições de geradores são
splits de literal `"""..."""` em concatenação `+ "\n".join(_helper())`. ✔

**Consistência de tipos:** `PEDAGOGICAL_SEQUENCE` = list[dict] com chaves
`label`/`full`/`template`. Helpers retornam `list[str]` (full/template) e `str`
(compact). `_exam_scope_rule_lines` retorna `list[str]` com 6 itens (1 título +
1 vazio + 3 bullets... na verdade 5 itens: título, "", P1, P2, P3) — testes
filtram `if line`. Os testes de import usam os mesmos nomes definidos na Task 1. ✔

**Risco residual:** splits de literal podem desbalancear `"""` se a edição não
casar exatamente — cada Task tem `python -c "import ..."` como sanity antes dos
pytests.
