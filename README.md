<div align="center">
  <h1>🎓 GPT Tutor Generator</h1>
  <p>Construa a base de conhecimento estruturada e o prompt ideal para criar o seu tutor acadêmico personalizado no ChatGPT.</p>
</div>

---

O **GPT Tutor Generator** (anteriormente *Academic Tutor Repo Builder*) é uma aplicação Desktop completa que automatiza a transformação de PDFs acadêmicos, slides de aula, cronogramas HTML e Links Web em um repositório interligado em Markdown, desenhado perfeitamente para servir como base de conhecimento (Knowledge Base) para LLMs.

Na sua versão 3, a ferramenta adota um design moderno, suporte nativo a temas do sistema (Modo Escuro), gerenciamento de "Perfis" de matéria e Aluno, e geração automática do **System Prompt** ideal para colar no GPT.

## ✨ Principais Funcionalidades

### 1. Perfis Inteligentes
- **Matérias (Subject Profiles):** Salve os detalhes (Nome, Professor, Slug, Semestre) e nunca mais preencha repetidamente. Selecionar uma matéria auto-preenche toda a interface e constrói o metadado.
- **Aluno (Student Profile):** Preencha sua personalidade de aprendizado, nível técnico e semestre. O sistema injetará essas diretrizes de ensino diretamente no Tutor.

### 2. Importação e Extração Multicanal
- **PDFs e Imagens:** Usa múltiplos OCRs e backends (PyMuPDF, docling, marker). Extrai texto, tabelas limpas e preserva imagens nativamente para Markdown.
- **HTML de Cronogramas:** Cole a tabela gigante do seu portal acadêmico (Moodle, Blackboard) e o sistema parseia numa tabela limpa em Markdown.
- **Links Web & Documentação:** Importe links! O programa faz *scraping* automático, limpa códigos/CSS e converte o site diretamente para Markdown referenciado.

### 3. Pipeline de Decisão (Backends em Camadas)
A extração não é cega. Baseado na quantidade de texto, equações e imagens da página, a ferramenta aplica:
- `quick`: Rápido e focado em texto via camada base.
- `high_fidelity`: Para documentos repletos de matemática/fórmulas em LaTeX usando OCRs avançados.
- `manual_assisted`: Extração super detalhada de recortes que demanda revisão final.
- `auto`: A IA interna avalia se o arquivo é um scan, uma lista de exercícios pesada em layout ou só slides gerais.

### 4. Gerador Automático de Prompt do GPT
Ao gerar o repositório, o programa compila a ementa da matéria, o estilo de aula do professor, o nível de conhecimento do aluno e emite o arquivo `INSTRUCOES_DO_GPT.txt`. Apenas copie e cole no Custom GPT da OpenAI.

## 🚀 Como Iniciar

### Pré-requisitos
Ter o Python 3.9+ instalado:
```bash
pip install -r requirements.txt
```
*Extensões Mínimas Recomendadas:*
```bash
pip install pymupdf pymupdf4llm pdfplumber
```
*Extensões Avançadas (Matemática e Fórmulas):*
Instale o pacote `docling` ou `marker-pdf`.

### Rodando o App
Basta abrir o terminal na pasta e executar:
```bash
python academic_tutor_repo_builder_v3.py
```

## 🧠 Fluxo de Criação do Seu Tutor

1. Abra o programa, clique em **👤 Aluno** e preencha como você quer que o Tutor te ensine.
2. Em **📚 Matéria ativa**, crie e salve a matéria atual que você quer estudar.
3. Arraste PDFs, Cole Links *(🔗 Adicionar Link)* ou Importe Cronogramas da Web.
4. Categorize se os arquivos são "Gabaritos", "Anotações", "Listas de Exercício".
5. Clique em **🚀 Criar Repositório**.
6. Acesse a pasta criada. Veja que arquivos difíceis ficam em `manual-review`. 
7. Vá no **ChatGPT**, clique em *Create a GPT*.
8. Copie as configurações geras em `INSTRUCOES_DO_GPT.txt` e faça upload da pasta `content`. Seu tutor particular está vivo!

---
*Este aplicativo cuida do "trabalho sujo" de desconstruir formatações horríveis de PDFs, deixando você e a IA se preocuparem apenas em estudar.*
