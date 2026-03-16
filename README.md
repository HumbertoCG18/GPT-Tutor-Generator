<div align="center">
  <h1>🎓 Academic Tutor Repo Builder V3</h1>
  <p>Construa a base de conhecimento estruturada para criar seu tutor acadêmico personalizado no <strong>Claude Projects</strong>.</p>
</div>

---

O **Academic Tutor Repo Builder V3** é uma aplicação Desktop completa que automatiza a transformação de PDFs acadêmicos, slides de aula, cronogramas HTML e links web em um repositório interligado em Markdown — projetado para servir como base de conhecimento para um tutor acadêmico baseado no **Claude** (claude.ai).

Cada repositório gerado é conectado a um **Projeto no Claude.ai**, onde o Claude atua como tutor com política pedagógica estruturada: ensina conceitos, guia exercícios, prepara para provas e acompanha o progresso do aluno sessão a sessão.

---

## ✨ Principais Funcionalidades

### 1. Perfis Inteligentes com Fila Persistente
- **Matérias:** Salve professor, horário, semestre e cronograma. A fila de arquivos pendentes é salva automaticamente por matéria — ao reabrir o app, o estado anterior é restaurado.
- **Aluno:** Defina seu estilo de aprendizado. O tutor no Claude usará essas preferências em todas as respostas.

### 2. Importação e Extração Multicanal
- **PDFs e Imagens:** Múltiplos backends de OCR (PyMuPDF, Docling, Marker). Extrai texto, tabelas e imagens.
- **HTML de Cronogramas:** Cole o HTML do portal acadêmico (Moodle, Blackboard) e converta em Markdown limpo automaticamente.
- **Links Web:** Importe URLs — o app faz scraping e converte para Markdown referenciado.

### 3. Pipeline de Extração em Camadas
- `quick` — apenas camada base (rápido)
- `high_fidelity` — base + avançada (fórmulas, tabelas complexas)
- `manual_assisted` — base + avançada + revisão humana guiada
- `auto` — detecta o tipo do documento e decide automaticamente

### 4. Processamento Individual
- Botão **⚡ Processar** — processa um arquivo por vez sem precisar rodar o build completo
- Botão **🗑 Limpar Processamento** — remove um item processado do repositório e do manifest

### 5. Geração Automática do Tutor Claude
Ao criar o repositório, o app gera automaticamente:

| Arquivo | Função |
|---|---|
| `INSTRUCOES_CLAUDE_PROJETO.md` | System prompt para colar no Claude Project |
| `system/TUTOR_POLICY.md` | Regras de comportamento do tutor |
| `system/PEDAGOGY.md` | Estrutura pedagógica de explicação |
| `system/MODES.md` | Modos: study, assignment, exam_prep, class_companion |
| `system/OUTPUT_TEMPLATES.md` | Templates de resposta por modo |
| `course/COURSE_MAP.md` | Mapa pedagógico (preencher manualmente) |
| `course/GLOSSARY.md` | Terminologia da disciplina (preencher manualmente) |
| `student/STUDENT_STATE.md` | Estado atual do aluno — atualizar após cada sessão |
| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |

### 6. Auto-Categorização por IA
Configure uma chave OpenAI ou Gemini em ⚙ Configurações para categorizar PDFs automaticamente com base no plano de ensino da matéria.

---

## 🚀 Como Iniciar

### Pré-requisitos
Python 3.9+ instalado. Instale as dependências:

```bash
pip install -r requirements.txt
```

Backends avançados (opcional, para fórmulas e OCR):
```bash
pip install docling
pip install marker-pdf
```

### Rodando o App

**Windows:**
```
run.bat
```
ou
```
run.ps1
```

**Qualquer plataforma:**
```bash
python app.py
```

---

## 🧠 Fluxo Completo — Do PDF ao Tutor

### No app
1. Clique em **📝 Gerenciar** e crie o perfil da matéria (professor, horário, cronograma HTML, plano de ensino PDF)
2. Clique em **👤 Aluno** e defina seu estilo de aprendizado
3. Selecione a matéria no menu suspenso
4. Adicione PDFs, imagens e links (use **⚡ Importação rápida** para vários arquivos)
5. Clique em **✨ Auto-Categorizar** (se tiver API key configurada)
6. Clique em **🚀 Criar Repositório**
7. Acesse a pasta criada e revise `manual-review/` no **🖌 Curator Studio**
8. Promova o conteúdo curado para `content/`, `exercises/` e `exams/`
9. Preencha `course/COURSE_MAP.md` e `course/GLOSSARY.md` com os tópicos da disciplina

### No GitHub
10. Crie um repositório para a disciplina e faça push

### No Claude.ai
11. Crie um **Projeto** no claude.ai com o nome da disciplina
12. Em Settings → GitHub, conecte o repositório da disciplina
13. No campo **Instructions** do Projeto, cole o conteúdo de `INSTRUCOES_CLAUDE_PROJETO.md`
14. Inicie uma conversa — o tutor está pronto

### Durante o semestre
15. Após cada sessão de estudo, peça ao Claude para gerar o bloco de atualização do `STUDENT_STATE.md`
16. Faça commit e push — na próxima sessão, o tutor lembra do seu progresso

---

## 📁 Estrutura Gerada

```
{slug-da-materia}/
├── INSTRUCOES_CLAUDE_PROJETO.md   ← colar no Claude Project
├── system/                         ← política pedagógica do tutor
├── course/                         ← identidade, mapa, cronograma, glossário
├── student/                        ← estado e perfil do aluno
├── content/                        ← material curado
├── exercises/                      ← listas de exercícios
├── exams/                          ← provas anteriores
├── raw/                            ← PDFs e imagens originais
├── staging/                        ← extração automática (para revisão)
├── manual-review/                  ← checklists de revisão humana
└── build/claude-knowledge/         ← bundle para upload manual
```

---

*O app cuida do trabalho de processar PDFs. O Claude cuida do trabalho de ensinar.*