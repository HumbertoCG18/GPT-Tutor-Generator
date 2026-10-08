# Design — Importador de plano de ensino auto-detect (Moodle)

date: 2026-06-18
branch: `feat/reconciliar-unit-bloco`
status: design aprovado pelo usuário (pendente review do spec escrito)

## Problema

O `teaching_plan` (Ementa, Objetivos, Unidades, Avaliação, Bibliografia) é a
fonte das unidades programáticas que `_parse_units_from_teaching_plan`
(`src/builder/extraction/teaching_plan.py`) converte em unidades → timeline
blocks → cronograma. Hoje a captura é **manual e só para PDF**: o botão
"Extrair PDF" (`dialogs.py`) lê um PDF do plano via pymupdf4llm e preenche o
campo `teaching_plan`.

Mas o professor pode postar o plano em **duas formas** no Moodle, e o sistema
não captura a segunda automaticamente:

- **PDF** — um módulo `resource` com um `.pdf` (ex.: MF/ES2/TCC "Plano de
  Ensino" → `plano.pdf`; SO "Programa" → `4637H-04.pdf`).
- **Card/página** — um módulo `page` (ex.: IA "Programa da Disciplina"), exibido
  num modal do Moodle. O conteúdo completo do plano está no **arquivo
  `index.html`** do módulo `page`, **não** no campo `description` (que guarda só
  o blurb "Contém ementa, objetivos, unidades programáticas, forma de avaliação
  e bibliografia").

Como temos acesso à API do Moodle (`core_course_get_contents`, já chamada no
import), dá para detectar qual forma o curso usa e importar o plano
automaticamente, sem trabalho manual.

## Evidência (probe read-only via API Moodle, 2026/1)

`core_course_get_contents` por curso, procurando o módulo do plano:

| Curso | Forma | Módulo (modname / name / arquivo) |
|---|---|---|
| IA (93156) | card/`page` | `page` "Programa da Disciplina" → conteúdo em `index.html` (description = só blurb, 157 chars) |
| MF (92717) | PDF | `resource` "Plano de Ensino" → `plano.pdf` |
| ES2 (92714) | PDF | `resource` "Plano de Ensino" → `plano.pdf` |
| TCC (93728) | PDF | `resource` "Plano de Ensino" → `Plano de Ensino-3.pdf` |
| SO (92854) | PDF | `resource` "Programa" → `4637H-04.pdf` |

**Falsos positivos observados** (a detecção PRECISA excluí-los): módulos cujo
nome contém "programa" como substring mas NÃO são o plano —
`programa-exemplo AG`, `Programas-exemplo: HC, SA`, `Exemplo de programa com
k-NN`, `Exercícios - programação e verificação com Dafny`, `Integer Programming
0/1` (códigos/exercícios); e `label`s de cronograma semanal ("Semana
16/03/2026 a 20/03/2026: …") cujo `description` contém as palavras
ementa/bibliografia por acaso.

## Objetivo

Detectar e importar **automaticamente** o plano de ensino do Moodle no import,
cobrindo as duas formas (PDF-resource e card/`page`), reproduzindo sem trabalho
manual o "Extrair PDF" e adicionando o caso do card. Preenche o `teaching_plan`
**só se vazio** (fill-if-empty) — nunca sobrescreve um plano já editado à mão.

## Não-objetivos

- NÃO refazer a captura/entendimento de **referências/bibliografia** (rework
  separado, spec própria — sinalizado pelo usuário).
- NÃO mudar `_parse_units_from_teaching_plan` — ele já cobre os formatos
  "Unidade de Aprendizagem N:" e "N° DA UNIDADE:" (verificado: IA parseia 5
  unidades).
- NÃO tocar a atribuição/pilha de precedência. A mudança é aditiva ao campo
  `teaching_plan` e só age quando ele está vazio.

## Design

### 1. `find_teaching_plan_source(contents) -> dict | None` — detector PURO

`src/builder/sources/moodle.py`. Sem rede; recebe o retorno de
`core_course_get_contents`. Varre os módulos e retorna o melhor candidato:

```
{"kind": "pdf" | "page", "name": str, "fileurl": str, "filename": str}
```

ou `None` se nenhum casar.

**Regra de detecção (precisão é o ponto):**
- Conjunto canônico de nomes, comparado por **igualdade normalizada** (casefold +
  trim de espaços/acentos colapsados), **NUNCA substring**:
  `{"plano de ensino", "programa da disciplina", "programa"}`.
- Filtro por modname:
  - **pdf**: `modname == "resource"` E o módulo tem um arquivo `.pdf` em
    `contents` (`type == "file"`). `fileurl`/`filename` vêm desse arquivo.
  - **page**: `modname == "page"` E o módulo tem um arquivo `index.html` (ou o
    primeiro arquivo `.html`) em `contents`. `fileurl`/`filename` vêm dele.
- A igualdade ancorada + o filtro de modname excluem todos os falsos positivos
  do probe (substrings "programa-exemplo"/"programação"/"Integer Programming" não
  são iguais a um nome canônico; `label`s não são `page` nem `resource`).
- **Prioridade** quando há mais de um candidato: por nome
  `"plano de ensino"` > `"programa da disciplina"` > `"programa"`; em empate de
  nome, `pdf` > `page`. (Caso de coexistência page+pdf é raro; nenhum dos 5
  cursos atuais tem.)

### 2. `extract_teaching_plan_markdown(client, source) -> str` — extrator

`src/builder/sources/moodle.py`. Baixa o conteúdo e converte para markdown:
- `kind == "page"`: baixa o `index.html` (via `client._download_url(fileurl)`)
  e converte com `html_to_structured_markdown` (`src/builder/text/url_markdown.py`,
  já existente). Import **function-local** (lazy), padrão do projeto.
- `kind == "pdf"`: baixa o `.pdf` (valida magic bytes como `download_course`) e
  extrai com pymupdf4llm (mesmo backend do "Extrair PDF"). Import function-local.

Retorna `""` em falha (download/redirect HTML/extração vazia) — nunca propaga
exceção que quebre o import.

### 3. Wiring no import — fill-if-empty

No fluxo de `import_moodle_courses` (`src/builder/sources/moodle.py`), que já
chama `get_course_contents(cid)`:
1. `src = find_teaching_plan_source(contents)`.
2. Se `src` e o `SubjectProfile.teaching_plan` está **vazio/whitespace**:
   `md = extract_teaching_plan_markdown(client, src)`; se `md.strip()`,
   `sp.teaching_plan = md` (o store já auto-salva via `store.add`).
3. Log: kind + nome do módulo capturado, ou "plano não detectado".
   Nunca sobrescreve `teaching_plan` já preenchido (manual/PDF anterior).

### 4. Tratamento de erro

- Nenhum match → mantém `teaching_plan` atual + log.
- `page` sem `index.html`/`.html` → fallback para o `description` do módulo + log
  (degrada para o blurb, melhor que nada; o parser simplesmente acha 0 unidades).
- Download falha / magic-bytes / redirect M365-HTML no PDF → `""`, não seta, log.
- `html_to_structured_markdown` ou pymupdf retorna vazio → não sobrescreve, log.

## Data flow

```
import → get_course_contents(cid)
       → find_teaching_plan_source(contents)
       → (se achou E teaching_plan vazio) extract_teaching_plan_markdown
       → sp.teaching_plan = md (fill-if-empty)
       → _parse_units_from_teaching_plan (já existente) → unidades
       → timeline blocks → cronograma
```

## Testes (TDD)

`tests/test_teaching_plan_source.py` (novo):
- `find_teaching_plan_source` acha as 3 formas reais (fixtures sintéticas de
  `core_course_get_contents`): `page` "Programa da Disciplina"+index.html;
  `resource` "Plano de Ensino"+plano.pdf; `resource` "Programa"+x.pdf.
- `find_teaching_plan_source` **rejeita** os falsos positivos do probe: módulo
  `resource` "programa-exemplo AG"+zip; "Exercícios - programação … Dafny";
  "Integer Programming 0/1"; `label` "Semana 16/03 …" com ementa/bibliografia no
  description. Retorno esperado: `None` (ou o candidato canônico se coexistir).
- Prioridade: curso com `resource` "Plano de Ensino" + `page` "Programa da
  Disciplina" → escolhe o "plano de ensino"/pdf.
- `extract_teaching_plan_markdown`: HTML de exemplo (modal-body) → markdown com
  headings preservados (mock/stub do download); PDF mínimo → markdown (mock do
  extrator pymupdf). Falha de download → `""`.
- Integração fill-if-empty: `teaching_plan` já preenchido → NÃO sobrescreve;
  vazio → seta; o markdown resultante parseia em N>0 unidades via
  `_parse_units_from_teaching_plan`.

Suíte existente (`test_moodle.py`, `test_moodle_labels.py`) verde.

## Eval-gate

- Os 5 cursos atuais JÁ têm `teaching_plan` preenchido → fill-if-empty é **no-op**
  para eles → `rebuild_diff` **idêntico** ao baseline (ES2 7 / IA 20 / SO 13 /
  MF 1 / TCC 0). O caminho novo só dispara para cursos com `teaching_plan` vazio
  (futuros) e nos testes sintéticos.
- `python scripts/eval_assignments.py`: golden 5/5, cw 0.
- `python -m pytest tests -q`: verde (baseline + novos testes).

## File structure

- `src/builder/sources/moodle.py` (modify): `find_teaching_plan_source` (puro),
  `extract_teaching_plan_markdown` (usa client + imports lazy), wiring fill-if-empty
  em `import_moodle_courses`.
- `tests/test_teaching_plan_source.py` (create): detector + extrator + integração.
- Reuso sem alterar: `html_to_structured_markdown` (`text/url_markdown.py`),
  `_parse_units_from_teaching_plan` (`extraction/teaching_plan.py`),
  pymupdf4llm (backend de PDF).

## Riscos

- "Programa" (nome genérico, usado pelo SO) é aceito por **igualdade exata** +
  `resource`+`.pdf` — risco baixo de falso positivo (os falsos do probe não são
  exatamente "Programa"); logar o que foi capturado para auditoria.
- Conteúdo do `page` vive no `index.html` (arquivo), não no `description` — o
  extrator precisa baixar o arquivo, não ler o campo. Coberto pelo fallback se o
  arquivo faltar.
- Re-import futuro com `teaching_plan` já preenchido nunca re-captura
  (fill-if-empty) — intencional; recaptura manual fica para o "Extrair PDF" ou um
  follow-up.
