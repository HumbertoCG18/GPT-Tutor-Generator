# Plano: Modo Exercícios — Correção e Feedback de Código do Aluno

**Status**: backlog. Não iniciar sem trigger explícito do usuário.

**Origem**: discussão durante execução de `plans/code-summarization-gemini.md` (Phase 1-8 + UI cleanup). AST parsing e linter foram descartados do escopo da summarization porque não enriquecem o tutor pedagogicamente — mas têm valor real num modo distinto: **revisão e feedback automatizado de código de aluno**.

---

## Objetivo

Quando o aluno submete código de exercício/trabalho, o tutor produz feedback estruturado que mistura:

1. **Sinais determinísticos** (AST + linter) — métricas objetivas, sem custo LLM
2. **Sinais semânticos** (Gemini ou tutor LLM em runtime) — diagnóstico pedagógico

E exibe num formato actionable: "seu código funciona mas tem X problemas estruturais; conceitualmente está confundindo Y; revisa Z da aula N".

## Não-objetivos

- Não substitui o Gemini summarizer atual (Phase 1-8) — esse continua mapeando código a aulas.
- Não é o tutor de runtime (Claude/GPT/Gemini Project) respondendo perguntas livres. É camada pré-tutor que **alimenta contexto** quando o aluno cola código.
- Não rodar build pipeline. Atua **on-demand** numa nova surface (UI "Praticar exercício" ou similar).

---

## Sinais e ferramentas

### AST (Python `ast`, tree-sitter para outras linguagens)

| Sinal | Uso pedagógico |
|---|---|
| Funções definidas, parâmetros, return | "Função `f` declarada mas nunca retorna" |
| Loops + condicionais aninhados | Complexidade ciclomática → "consideraria refatorar" |
| Imports usados vs declarados | Detect dead code |
| Padrões estruturais (recursão, OOP, list comp, async) | Cross-validate conceito esperado da aula |
| Profundidade de aninhamento | Threshold pedagógico |
| LoC por função | Métrica de granularidade |

### Linter (pylint / ruff / black-check)

| Sinal | Uso |
|---|---|
| Naming inconsistente | Feedback estilo |
| Variáveis não usadas | Indica refatoração incompleta |
| Comparações booleanas estranhas (`if x == True`) | Anti-pattern detectável |
| Type hints faltando | Conforme política da matéria |
| Indentação / formatting | Pre-format antes de avaliar lógica |

### Gemini (ou tutor runtime LLM)

| Sinal | Uso |
|---|---|
| Conceitos corretos vs esperados pela aula | "Você usou laço quando a aula pediu recursão" |
| Diagnóstico de bug lógico | Explicação em linguagem natural |
| Sugestão de fix com referência à aula | Linka resposta ao `CRONOGRAMA_DETALHADO.md` |

### Testes (opcional, se aluno fornece input/output esperado)

Rodar código em sandbox isolado, comparar saídas. Score binário pass/fail por caso.

---

## Pipeline proposto

```
Aluno cola código
  ↓
1. AST parse → métricas + features detectadas
  ↓
2. Linter run → lista de issues
  ↓
3. Match contra exercise expected_concepts (do gerador) → gaps/extras
  ↓
4. (opcional) Sandbox run → pass/fail por test case
  ↓
5. Bundle context → Gemini structured output:
     - bug_diagnosis: lista de issues lógicos
     - concept_gaps: conceitos da aula que faltam aplicar
     - suggested_revision: trecho corrigido com explicação
     - referenced_blocks: aulas do CRONOGRAMA pra revisar
  ↓
6. UI mostra report estruturado + link pros blocos do cronograma
```

---

## Surfaces afetadas

### Novo
- `src/builder/runtime/code_review.py` — AST + linter + bundle builder
- `src/builder/runtime/code_review_models.py` — Pydantic schemas (`CodeReviewReport`)
- `src/ui/exercise_panel.py` — surface "Praticar exercício" (textarea + paste + run review)
- `tests/test_code_review_ast.py`, `tests/test_code_review_linter.py`

### Edits
- `src/ui/app.py` — wire tab "🎯 Exercícios" (após "💻 Códigos")
- `src/ui/dialogs.py` — settings: enable code review (flag), linter choice (pylint/ruff/none)
- `src/builder/core/code_summarization.py` — extender schema `CodeSummary` com `expected_concepts: list[str]` quando entry é `codigo-trabalho-aluno` ou `exercicio-*` (alimenta o matcher de gap)

---

## Pré-requisitos antes de iniciar

1. Phase 1-8 do code-summarization estáveis (✅ — commitados)
2. Material-agnostic refactor decidido (afeta como exercícios são modelados — ver `plans/material-agnostic-refactor.md`)
3. Decisão UX: aluno cola código no app, ou tutor runtime (Claude Project) recebe via instrução?
   - Se Claude Project: feature vira **prompt template** + arquivos auxiliares no repo, não Python code
   - Se app local: pipeline acima
4. Categoria de licenças linters: pylint GPL contagia se importado? Ruff é MIT — preferir ruff

---

## Custo estimado

| Componente | Linhas | Tempo | Risco |
|---|---:|---|---|
| AST parse (Python only) | ~150 | 1d | Baixo |
| AST tree-sitter (multi-lang) | ~300 | 3-5d | Médio (deps) |
| Linter wrap (ruff CLI) | ~80 | 0.5d | Baixo |
| Gemini schema + prompt | ~200 | 1d | Baixo |
| UI exercise_panel | ~400 | 2d | Médio |
| Sandbox runner (subprocess + timeout) | ~150 | 1d | Médio (segurança) |
| Integração + testes | ~300 | 2d | Baixo |
| **Total mínimo (Python only, sem sandbox)** | ~1100 | ~5d | Médio |

**Custo Gemini runtime**: ~$0.01 por review (bundle pequeno, schema bounded).

---

## Decisão pendente

Não iniciar até:
- Usuário pedir explicitamente, OU
- Material-agnostic refactor concluir e revelar shape final de `exercise` entries

Quando ativar: refinar este plano com discovery doc (Phase 0) antes de qualquer código, seguindo padrão de `plans/code-summarization-gemini.md`.

---

## Referências cruzadas

- `plans/code-summarization-gemini.md` — feature precursora, define `code_curation.json` e schemas Pydantic reutilizáveis
- `plans/material-agnostic-refactor.md` — afeta modelagem de exercícios
- `.mex/patterns/gemini-code-summarization.md` — pattern reutilizável de lazy Gemini + hash cache
