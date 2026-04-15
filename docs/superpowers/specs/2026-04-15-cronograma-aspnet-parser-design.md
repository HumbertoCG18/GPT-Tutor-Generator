# Design — Parser estruturado do cronograma ASP.NET e propagação para `card_evidence`

**Data:** 2026-04-15
**Status:** Proposto
**Autor:** Humberto + Claude Code
**Escopo:** `src/utils/helpers.py`, `src/builder/timeline_signals.py`, testes
**Escopo fora:** schema do `timeline_index`, `SubjectProfile`, UI, Curator Studio, Image Curator

---

## 1. Problema

Os repositórios-tutor atuais têm `timeline_index.version = 3` com `blocks` e `sessions`, mas **`card_evidence = 0` em todos os blocos**. O matcher temporal está consumindo evidência que nunca chega a ser capturada.

Causa raiz: o cronograma que o usuário cola no `HTMLImportDialog` vem de um sistema acadêmico ASP.NET (DataGrid `dgAulas`, não Moodle), em formato **já estruturado** com uma aula por linha. O parser atual `parse_html_schedule` em `src/utils/helpers.py:341` faz `get_text(" ", strip=True)` por célula e achata tudo em tabela markdown plana:

```
9 SEG 30/03/2026 LM 19:15 - 20:45 Provas por indução Aula
```

O extractor `extract_timeline_session_signals` espera padrões como `(DD/MM/YYYY): título` — não casa com a linha achatada. Resultado: `sessions` fica fraca, `card_evidence` fica vazia, e o scorer só consegue casar via blocos agregados.

---

## 2. Dados de entrada (formato real)

O HTML que o usuário cola é uma `<table id="dgAulas">` com estas colunas fixas:

| Coluna | Conteúdo | Relevância |
|--|--|--|
| `#` | número sequencial da aula | baixa (pode estar vazio em eventos) |
| `Dia` | SEG / QUA / etc | média (debug humano) |
| `Data` | `DD/MM/YYYY` | **alta — chave temporal** |
| `Hora` | `LM 19:15 - 20:45` | baixa |
| `Descrição` | título da aula, ex. "Provas por indução" | **alta — sinal temático forte** |
| `Atividade` | `Aula` / `Prova` / `Prova de Substituição` / `Evento Acadêmico` / `Prova de G2` | **alta — classifica tipo** |
| `Recursos` | local, ex. "Laboratório 409/412" | média — sinal de aula prática |

Sinais adicionais preservados no HTML (não extraídos hoje):
- `background-color: Red` → "Suspensão de aulas"
- `background-color: #FFA500` / `#FF8C00` / `#8B0000` → prova ou evento especial
- `background-color: LightGrey` → aulas pós-período normal (devolução, G2)

O cronograma é **snapshot completo** do semestre (não incremental como Moodle). Paste sobrescreve.

---

## 3. Decisão de arquitetura

**Preservar estrutura na serialização**, não na persistência.

O `syllabus` continua sendo `str` no `SubjectProfile` (sem mudança de schema). Mas o texto que vai para o syllabus passa a ser markdown com uma linha por aula, no formato que o extractor de sessões já reconhece (com leve ajuste de regex).

Isso evita:
- Store JSON separado (YAGNI — cronograma não é incremental)
- Campos novos no profile
- Mudança de schema em `timeline_index`
- Qualquer UI nova

E entrega o que falta:
- Par `(data, título)` preservado como unidade
- Tipo de atividade preservado
- Parseabilidade pelo pipeline existente

---

## 4. Formato de saída do syllabus

O novo `parse_html_schedule`, ao detectar cronograma ASP.NET, emite:

```markdown
## Cronograma de Aulas

- (02/03/2026) SEG — Apresentação da disciplina [Aula]
- (04/03/2026) QUA — Introdução a Métodos Formais [Aula]
- (09/03/2026) SEG — Revisão de lógica de predicados, Exercícios [Aula]
- (11/03/2026) QUA — Conjuntos indutivos e equações recursivas [Aula]
- (16/03/2026) SEG — Exercícios [Aula]
- (18/03/2026) QUA — Estudo de caso: listas [Aula]
- (30/03/2026) SEG — Provas por indução [Aula]
- (01/04/2026) QUA — Provas por indução: listas e árvores [Aula]
- (06/04/2026) SEG — Prova Interativa de Teoremas - Isabelle [Aula] @Laboratório 409/412
- (22/04/2026) QUA — Prova P1 [Prova]
- (20/04/2026) SEG — Suspensão de aulas [Aula] ⊘
- (06/07/2026) SEG — Prova P2 [Prova]
- (08/07/2026) QUA — Prova PS [Prova de Substituição]
```

Regras do formato:

- Marcador `- ` (lista) por aula
- `(DD/MM/YYYY)` entre parênteses
- Dia da semana em caixa alta (preserva contexto humano)
- ` — ` separa data+dia do título
- Título conforme `Descrição`
- `[Atividade]` entre colchetes, sempre presente
- ` @local` opcional quando `Recursos` não é vazio
- ` ⊘` sufixo para aulas que o matcher deve ignorar (suspensão, devolução)

---

## 5. Detecção de cronograma ASP.NET

`parse_html_schedule` recebe HTML arbitrário. Precisa decidir entre parser novo e fallback.

**Heurística de detecção** (primeira que casar vence):

1. `soup.find(id="dgAulas")` presente → ASP.NET confirmado
2. Qualquer `<span id="..._lblData">` com data DD/MM/YYYY → ASP.NET confirmado
3. Caso contrário → fallback para parser genérico de tabela (comportamento atual)

Isso garante retrocompatibilidade: quem colar outro tipo de HTML continua com o comportamento antigo.

---

## 6. Mudanças por arquivo

### 6.1 `src/utils/helpers.py`

- **Nova função interna** `_parse_aspnet_schedule(soup) -> str`:
  - itera `<tr>` de `<tbody>` dentro de `#dgAulas` (pulando cabeçalho)
  - para cada linha, lê `_lblData`, `_lblDia`, `_lblDescricao`, `_lblAtividade`, `_lblRecursos` via `find("span", id=re.compile(r"_lbl<Campo>$"))`
  - detecta estilos especiais via `tr.get("style", "")`:
    - `background-color:Red` → suspensão (append `⊘`)
    - `background-color:LightGrey` → pós-período (append `⊘`)
    - demais cores → normal
  - monta linhas no formato definido na seção 4
  - retorna markdown completo com heading `## Cronograma de Aulas`
- **`parse_html_schedule(html_content)` modificado:**
  - tenta detecção ASP.NET primeiro
  - se positivo → retorna saída de `_parse_aspnet_schedule`
  - se negativo → mantém código atual inalterado (fallback genérico)

### 6.2 `src/builder/timeline_signals.py`

Ajustar regex de `extract_timeline_session_signals` para casar o novo formato. Padrão alvo:

```
^[-\s]*\((\d{2}/\d{2}/\d{4})\)(?:\s+[A-ZÇÃÕ]{3})?\s*[—\-:]\s*(.+?)(?:\s*\[([^\]]+)\])?(?:\s+@[^⊘]+)?(?:\s+⊘)?\s*$
```

Grupos capturados:
1. data (obrigatório)
2. título (obrigatório)
3. tipo de atividade (opcional — `Aula`/`Prova`/etc)

**Regras de inclusão:**
- Linha com sufixo `⊘` → parser reconhece mas retorna `ignored=True` (não vira session nem card_evidence)
- Demais → vira `session` normal, com campo novo `activity_type` preenchido quando presente

Separador `[—\-:]` mantém compatibilidade com formato anterior do tipo `(DD/MM/YYYY): título`. Na implementação, verificar regex atual em `timeline_signals.py` e unir/substituir preservando seus casos existentes — todos os testes anteriores de `extract_timeline_session_signals` devem continuar passando sem alteração.

### 6.3 Testes

Novos arquivos/casos:

- `tests/test_html_schedule_parser.py`
  - caso 1: HTML ASP.NET real (fixture do exemplo do Humberto) → verifica saída linha-por-linha
  - caso 2: HTML genérico (tabela não-ASP.NET) → verifica fallback inalterado
  - caso 3: HTML ASP.NET com linhas de suspensão e devolução → verifica sufixo `⊘`
  - caso 4: linha com `Recursos` preenchido → verifica sufixo `@local`

- `tests/test_timeline_signals.py` (existente, ampliar)
  - parse de linha nova `(30/03/2026) SEG — Provas por indução [Aula]` → session válida com `activity_type="Aula"`
  - parse de linha com `⊘` → ignored
  - parse de linha antiga `(30/03/2026): Provas por indução` → continua funcionando

---

## 7. Fluxo do usuário pós-implementação

1. Usuário abre `HTMLImportDialog`, cola o HTML do sistema ASP.NET
2. Dialog chama `parse_html_schedule` → detecta ASP.NET → syllabus ganha listagem estruturada
3. Usuário salva perfil
4. `Repo → Reprocessar Repositório`
5. Pipeline regenera `timeline_index.json`, `FILE_MAP.md`, `COURSE_MAP.md`, `STUDENT_STATE.md`
6. `sessions` ganha 1 entrada por aula; `card_evidence` nos blocos passa de 0 para N
7. Materiais novos (ou re-scoring de materiais existentes) encontram aulas específicas pelo título

Custo: reprocessamento apenas regenera artefatos pedagógicos. Não reprocessa PDFs, LLMs, Datalab.

---

## 8. Compatibilidade

- `timeline_index.version = 3` inalterado (sessions e card_evidence já existem)
- Repos já regenerados continuam válidos (o campo `activity_type` em session é aditivo)
- Profiles existentes continuam sendo carregados normalmente
- `parse_html_schedule` com HTML não-ASP.NET → comportamento idêntico ao atual
- Nenhuma migração de dados necessária

---

## 9. Trabalho fora do escopo desta fase

Intencionalmente adiado (implementar depois se valor justificar):

- **Auto-tag `uso:revisao-prova`** com base em `activity_type="Prova"` + janela temporal. Tag já existe; falta consumidor no builder.
- **Sinal de aula prática** via `Recursos = Laboratório ...` → pode virar bônus no matcher para materiais de código.
- **Campo `activity_type` no `timeline_index`** propagado para FILE_MAP (coluna Tipo).
- **Detecção de outros formatos ASP.NET** (outras faculdades/sistemas com DataGrid diferente).

---

## 10. Critérios de aceitação

1. Colar o HTML de exemplo no `HTMLImportDialog` produz syllabus com 35+ linhas no formato da seção 4
2. `parse_html_schedule` com HTML de tabela genérica produz saída idêntica à versão atual (teste de regressão)
3. Após reprocessar qualquer repo com cronograma ASP.NET, `timeline_index.json` tem `sessions` populadas e `card_evidence > 0` em blocos cuja data bate com aulas
4. Suite completa de testes passa (`python -m pytest tests/ -q`)
5. Linhas marcadas com `⊘` (suspensão, devolução) não aparecem como sessions nem contribuem para card_evidence

---

## 11. Riscos e mitigações

| Risco | Mitigação |
|--|--|
| Regex novo quebra parse de syllabus existentes escritos à mão | Regex aceita formato antigo e novo; testes cobrem ambos |
| Outras faculdades usam DataGrid com IDs diferentes | Fallback preservado; detecção baseada em presença de `_lblData` é genérica |
| Reprocessamento regenera FILE_MAP e usuário perde edições manuais | Documentação já deixa claro que FILE_MAP/COURSE_MAP são regenerados (CLAUDE.md linha "Não editar FILE_MAP ou COURSE_MAP manualmente") |
| Linhas com título vazio ou data inválida | Parser filtra silenciosamente; log warning |
