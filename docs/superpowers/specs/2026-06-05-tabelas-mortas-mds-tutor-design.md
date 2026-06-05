# Limpeza de tabelas mortas nos MDs do tutor — Design

last_updated: 2026-06-05

## Contexto

Auditoria de 2026-06-04 (4 auditores paralelos sobre os geradores de MD que o
tutor lê) identificou tabelas mortas e ruído de placeholder em
`src/builder/artifacts/repo.py`. São seções desenhadas como template de
preenchimento manual ("Preencha após revisar cada prova"), mas o sistema é
build-time automático — ninguém preenche. Ficam `[a preencher]` permanente,
gastam token e enganam o tutor (sugerem dado que não existe).

Item de backlog: "Higiene dos MDs do tutor (audit 2026-06-04)", grupo 🟠.
A redundância da tabela de relevância da BIBLIOGRAPHY já saiu junto do Approach C.

## Objetivo

Remover placeholders permanentes que o tutor lê como dado fantasma; branches
vazios viram frase curta; labels de clamp corrigidos para o nome do próprio
artefato. Tabelas data-driven (live) ficam intactas.

## Princípio

- Onde há entries reais → output quase byte-idêntico (exceção: coluna `Status`
  removida do assignment).
- Onde não há entries → frase curta de estado vazio, não tabela placeholder.
- Seções de "padrões"/"incidência" que nunca recebem dado → removidas.
- Cada artefato usa seu próprio nome na nota de truncamento (`clamp`).

## Mudanças por gerador (`src/builder/artifacts/repo.py`)

### 1. `exam_index_md` (753-797)
- KEEP: tabela "Provas disponíveis" (data-driven de entries).
- REMOVE: seção "Incidência de tópicos por prova" (777-786, linha fixa
  `| [a preencher] | | | | | |`).
- REMOVE: seção "Padrões de questão observados" (787-789, só comentário HTML).
- Branch sem provas (entries vazio): frase `_Nenhuma prova mapeada ainda._`.
- Label clamp: `course/FILE_MAP.md` → `course/EXAM_INDEX.md`.

### 2. `assignment_index_md` (800-820)
- DROP coluna `Status` (header + célula sempre "pendente").
- Tabela live vira `| Arquivo | Título | Unidade |`.
- Branch vazio: frase `_Nenhum trabalho mapeado ainda._` (sem linha placeholder).
- REMOVE: seção "Padrões do professor" (818, `- [a preencher]`).
- Label clamp: `course/FILE_MAP.md` → `course/ASSIGNMENT_INDEX.md`.

### 3. `code_index_md` — templates (a) e (b) (844-903)
- REMOVE: bloco `code_index_patterns` + `<!-- Preencha... -->` + `- [a preencher]`
  (853-859 no template a; 895-901 no template b).
- Fallback per-entry: `e.professor_signal or "[a preencher]"` → `e.professor_signal or ""` (882).
- Label clamp: `course/COURSE_MAP.md` → `course/CODE_INDEX.md` (861, 903).
- Template (c) (grouped Phase-3) não tem placeholder morto — não muda.

### 4. CRONOGRAMA detalhado (1042)
- REMOVE: comentário `<!-- TODO (material-agnostic refactor): PDFs, exercícios, imagens -->`.
- Mantém o separador `---` e a estrutura restante.

### 5. `whiteboard_index_md` (1123-1135)
- KEEP: tabela live (data-driven).
- Branch vazio: frase `_Nenhum registro de quadro ainda._` (sem linha placeholder).
- REMOVE: seção "Padrões pedagógicos" (1133, `- [a preencher]`).
- Label clamp: `course/FILE_MAP.md` → `course/WHITEBOARD_INDEX.md`.

### 6. `exercise_index_md` (2070-2098)
- KEEP: tabela live (data-driven) + nota de orientação (2094).
- Branch vazio: remove linha `| [a preencher] | | | | | |` (2091); mantém só a
  nota de orientação que já existe (2094).
- Label já correto (`exercises/EXERCISE_INDEX.md`).

## Teste a atualizar

- `tests/test_core.py:4437` (`test_exercise_index_empty_state_stays_short`):
  hoje afirma `"| [a preencher] | | | | | |" in result`. Trocar para asserir a
  ausência da linha placeholder e a presença da nota de orientação.

## Estratégia de implementação

TDD por gerador (RED no novo formato esperado → GREEN removendo o morto).
~6 tasks curtas, uma por gerador. Cada task: escreve/ajusta teste do novo
output, vê falhar, remove o placeholder, vê passar, commit.

Base: 878 testes verdes.

## Fora de escopo

- 🟡 Duplicação (escopo de prova 2x, sequência pedagógica em 3 ordens, 5 modos
  inline) — exige decidir fonte canônica, item de higiene maior.
- 🟢 Ambiguidade de labels ("quatro modos" lista cinco, `render_course_map_md`
  legado) — item separado.
- `prompts.py:484` `/main` hardcoded — tratado no item de clone GitHub.
- Sincronização PROGRESS_SCHEMA — vai no refactor do student_state.
