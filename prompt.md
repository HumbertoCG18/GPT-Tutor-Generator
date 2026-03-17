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

## 5. Estado atual — tudo implementado

Todos os bugs críticos desta lista foram corrigidos. O projeto está pronto para uso:

- ✅ `EXAM_INDEX.md` e `EXERCISE_INDEX.md` gerados condicionalmente
- ✅ `COURSE_MAP.md` populado automaticamente via `_parse_units_from_teaching_plan()`
- ✅ `BIBLIOGRAPHY.md` extrai referências do `teaching_plan` automaticamente
- ✅ `GLOSSARY.md` semeia termos dos tópicos extraídos
- ✅ `incremental_build` regenera `INSTRUCOES_CLAUDE_PROJETO.md`, `COURSE_MAP.md`, `GLOSSARY.md`
- ✅ `parse_html_schedule` duplicada removida de `dialogs.py`
- ✅ Referência a `CURRENT_STATE.md` removida do messagebox de sucesso
- ✅ `default_ai_provider` presente no `AppConfig.DEFAULTS`
- ✅ Regex de unidades suporta cabeçalhos Markdown (`### Unidade N —`)
- ✅ 61 testes passando

### Melhorias futuras (não críticas)

- Extração de datas de prova do `syllabus` para popular `EXAM_INDEX`
- Campo de escopo de prova por matéria no `SubjectManagerDialog`
- `today-context.md` gerado automaticamente antes da aula

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