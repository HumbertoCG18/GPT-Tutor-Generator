# HANDOFF — Academic Tutor Repo Builder V3
> Cole este prompt no Claude Code para transferir contexto completo do projeto.

---

## 1. O que é este projeto

**Academic Tutor Repo Builder V3** — aplicação desktop Python/tkinter que transforma PDFs acadêmicos em repositórios de conhecimento curado, conectados a um **Projeto no Claude.ai** que atua como tutor acadêmico personalizado.

O repositório do gerador está em: https://github.com/HumbertoCG18/GPT-Tutor-Generator

Leia o `LLM.md` na raiz — ele foi atualizado e contém a arquitetura completa atual.

---

## 2. Contexto crítico: migração de ChatGPT → Claude

O projeto foi iniciado pensando no **ChatGPT Custom GPT** como destino. Durante o desenvolvimento, decidimos migrar para **Claude Projects** como plataforma principal. Essa migração está **parcialmente concluída** no código — a maior parte das referências ao ChatGPT foi removida, mas podem existir resíduos.

**O que já foi migrado:**
- `INSTRUCOES_DO_GPT.txt` → `INSTRUCOES_CLAUDE_PROJETO.md`
- `build/gpt-knowledge/` → `build/claude-knowledge/`
- `generate_system_prompt()` → `generate_claude_project_instructions()` (com alias de compatibilidade)
- Geração automática de arquivos pedagógicos: `TUTOR_POLICY.md`, `PEDAGOGY.md`, `MODES.md`, `OUTPUT_TEMPLATES.md`, `COURSE_MAP.md`, `GLOSSARY.md`, `STUDENT_STATE.md`, `PROGRESS_SCHEMA.md`, `BIBLIOGRAPHY.md`

---

## 3. Arquitetura modular atual

```
src/
├── __main__.py              # Entry point
├── builder/
│   └── engine.py            # Pipeline de extração + geradores pedagógicos
├── models/
│   └── core.py              # DataClasses: FileEntry, SubjectProfile, etc.
├── services/
│   └── llm.py               # Auto-categorização via OpenAI/Gemini
└── ui/
    ├── app.py               # Janela principal
    ├── curator_studio.py    # Editor de revisão manual
    ├── dialogs.py           # Todos os diálogos modais
    └── theme.py             # ThemeManager + AppConfig
```

---

## 4. Funcionalidades já implementadas

### Pipeline de extração
- 4 backends: `pymupdf4llm`, `pymupdf`, `docling`, `marker`
- Profiling automático de PDFs (detecta math_heavy, scanned, exam_pdf, etc.)
- Seleção inteligente de backend por modo e perfil
- Extração de imagens, tabelas e page previews
- Geração de checklists de revisão manual

### UI
- Fila de arquivos **persistente por matéria** (salva em `SubjectProfile.queue`)
- Botão **⚡ Processar** — chama `RepoBuilder.process_single(entry)` — processa item a item
- Botão **🗑 Limpar Processamento** — chama `RepoBuilder.unprocess(entry_id)` — remove arquivos gerados e retira do manifest
- Build incremental (detecta repositório existente)
- Auto-categorização por LLM antes do build
- Curator Studio para revisão de Markdown com preview de imagens
- Markdown Preview com filtro por PDFs (via manifest.json)

### Geração de repositório
- Estrutura completa de diretórios
- Todos os arquivos pedagógicos gerados automaticamente
- `manifest.json` como log completo de processamento
- `SOURCE_REGISTRY.yaml` como índice de fontes
- `bundle.seed.json` para upload manual ao Claude

---

## 5. Bugs conhecidos e pendências

### 🔴 Críticos (podem quebrar em runtime)

**A.** `modes_md()` e `pedagogy_md()` em `engine.py` referenciam `exams/EXAM_INDEX.md`, mas esse arquivo **nunca é gerado**. O Claude vai procurar o arquivo, não encontrar e improvisar — comportamento indesejado.
```python
# Em pedagogy_md():
"Ao explicar um tópico, verifique `exams/EXAM_INDEX.md`:"
# Arquivo não existe → adicionar gerador exam_index_md() e exercise_index_md()
```

**B.** `app.py` ainda exibe mensagem de sucesso pós-build mencionando `CURRENT_STATE.md`:
```python
"CURRENT_STATE.md foi regenerado.\nPróximo passo: dar push no GitHub."
# Esse arquivo não existe no sistema — remover ou corrigir
```

**C.** `parse_html_schedule` está duplicada em `src/utils/helpers.py` E em `src/ui/dialogs.py`. A de `dialogs.py` pode divergir — deve ser removida de lá e importada de `helpers`.

**D.** Diretório `student/` duplicado em `_create_structure()` do engine:
```python
dirs = [
    ...
    "student",   # linha ~440
    ...
    "student",   # duplicado — não quebra (mkdir é idempotente) mas é ruído
]
```

### 🟡 Importantes (limitam o tutor)

**E.** `EXAM_INDEX.md` e `EXERCISE_INDEX.md` não são gerados. São os arquivos que permitem ao tutor saber incidência por tópico e mapear exercícios. Precisam de geradores (`exam_index_md()`, `exercise_index_md()`) e serem chamados em `_write_root_files()`.

**F.** `COURSE_MAP.md` é gerado como template vazio. Quando o `teaching_plan` do `SubjectProfile` está preenchido (plano de ensino extraído do PDF), o gerador poderia extrair as unidades e populá-lo automaticamente. Hoje essa informação existe mas não é usada.

**G.** `BIBLIOGRAPHY.md` é gerado mas só inclui entradas da categoria `"bibliografia"`. Quando o `teaching_plan` contém referências bibliográficas (como no plano de ensino de Métodos Formais que tem 8 referências), elas poderiam ser extraídas automaticamente.

**H.** `LLM.md` e `README.md` foram atualizados na sessão atual mas **ainda não foram commitados**. Verificar se estão atualizados no repositório.

### 🟢 Melhorias desejadas

**I.** O `INSTRUCOES_CLAUDE_PROJETO.md` não inclui a lógica de escopo de provas diretamente — ela está em `PEDAGOGY.md` e `MODES.md`. Seria bom ter uma seção resumida também nas instruções principais para garantir que o tutor a aplique mesmo sem consultar os arquivos secundários.

**J.** Após o build, o app limpa a fila (`self.entries = []`). Isso é correto para o build completo, mas no `process_single` o item já é removido da fila individualmente em `_on_single_processed_success`. Verificar se não há double-removal.

**K.** O `incremental_build` atualiza `BIBLIOGRAPHY.md` mas não regenera `INSTRUCOES_CLAUDE_PROJETO.md` nem os arquivos pedagógicos. Se o aluno atualizar o perfil da matéria após o primeiro build, as instruções ficam desatualizadas.

---

## 6. Lógica pedagógica do tutor (para referência)

### Modos de operação
- `study` — ensinar conceito do zero
- `assignment` — guiar exercício sem entregar resposta
- `exam_prep` — revisão com foco em incidência e padrões
- `class_companion` — suporte rápido durante aula

### Escopo das provas (lógica cumulativa com peso progressivo)
```
P1 → 100% conteúdo pré-P1
P2 → ~70% conteúdo entre P1-P2 + ~30% pré-P1
P3 → ~70% conteúdo entre P2-P3 + ~20% P1→P2 + ~10% pré-P1
```
Essa lógica está em `PEDAGOGY.md`, `MODES.md` e `OUTPUT_TEMPLATES.md`.

### Arquivos que o tutor consulta (em ordem de prioridade)
1. `student/STUDENT_STATE.md` — sempre, antes de qualquer resposta
2. `system/TUTOR_POLICY.md` — regras de comportamento
3. `system/MODES.md` — identificar modo da sessão
4. `course/COURSE_MAP.md` — ordem dos tópicos
5. `course/SYLLABUS.md` — datas e provas
6. `exams/EXAM_INDEX.md` — incidência por tópico ← **não existe ainda**
7. `exercises/EXERCISE_INDEX.md` — mapa de exercícios ← **não existe ainda**

---

## 7. Contexto sobre o repositório de disciplina

Para testar, existe o plano de ensino e cronograma da disciplina **Métodos Formais para Computação** (PUCRS, prof. Júlio Pereira Machado, 2026/01):

- **P1:** 22/04/2026 — cobre Unidade 1 (lógica, conjuntos indutivos, Isabelle)
- **P2:** 06/07/2026 — cobre Unidades 2+3 (Lógica de Hoare, Dafny, model checking)
- Ferramentas: Isabelle, Dafny, TLA+, NuSMV/nuXmv
- **Atenção:** O plano formal diz "P1 = Unidades 1+2" mas o cronograma mostra que Unidade 2 começa após a P1. O repositório usa o cronograma como verdade.

---

## 8. O que fazer primeiro

Sugestão de ordem de trabalho:

1. **Ler** `LLM.md`, `src/builder/engine.py` e `src/ui/app.py` para entender o estado atual
2. **Corrigir bug C** — remover `parse_html_schedule` duplicada de `dialogs.py`, importar de `helpers`
3. **Corrigir bug D** — remover `student/` duplicado em `_create_structure()`
4. **Corrigir bug B** — remover referência a `CURRENT_STATE.md` no messagebox de sucesso
5. **Implementar E** — criar `exam_index_md()` e `exercise_index_md()` em `engine.py` e chamar em `_write_root_files()`
6. **Corrigir A** — atualizar `pedagogy_md()` e `modes_md()` para não referenciar arquivos que não existem, ou gerar os arquivos (fazer E primeiro)
7. **Implementar K** — regenerar `INSTRUCOES_CLAUDE_PROJETO.md` e arquivos pedagógicos no `incremental_build()`
8. **Avaliar F** — extrair unidades do `teaching_plan` para popular `COURSE_MAP.md` automaticamente

---

## 9. Dependências e ambiente

```bash
pip install pymupdf pymupdf4llm pdfplumber Pillow python-dotenv
pip install pytest  # para testes
# opcionais:
pip install docling marker-pdf
pip install openai google-genai  # para auto-categorização
```

```bash
python -m pytest tests/ -v  # rodar testes
python app.py               # rodar o app
```

---

## 10. Filosofia do projeto (não alterar)

- PDF é material bruto → Markdown curado é conhecimento operacional
- GitHub é a fonte da verdade → não depende de um único chat
- Claude é a camada pedagógica → não é depósito de tudo
- Separar conteúdo / tutor / aluno / build em camadas distintas
- Projetar para reuso → cada disciplina usa o mesmo template