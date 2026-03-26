# Image Curator com LLaVA Local — Design Spec

**Data:** 2026-03-25
**Status:** Aprovado

---

## Resumo

Adicionar ao Academic Tutor Repo Builder uma etapa de curadoria e descrição automática de imagens extraídas de PDFs, usando LLaVA 7B via Ollama local, para que o conteúdo visual seja acessível aos 3 LLMs tutores (Claude, GPT, Gemini) como texto indexável nos markdowns.

## Problema

Durante a extração PDF → markdown via pymupdf4llm, imagens são substituídas por referências de caminho (`![](content/images/...)`). Nenhuma das 3 plataformas LLM resolve esses caminhos — o conteúdo visual (diagramas, tabelas, fórmulas) fica invisível para o tutor.

## Restrições

- Sem API externa paga — usar modelo Vision open-source local
- Compatível com Claude Projects, ChatGPT custom GPT e Gemini Gems
- Manutenível via git push
- Hardware disponível: RTX 4050 Mobile (6GB VRAM)

## Solução Escolhida

**Abordagem B — Ollama + LLaVA 7B** com curadoria semi-automática.

Modelo LLaVA 7B (~4.5GB VRAM) rodando via Ollama local, com pré-classificação por heurísticas e curadoria manual por página antes da geração de descrições.

**Independente de backend de extração:** o Image Curator opera sobre `content/images/`, que é o destino final consolidado por `_resolve_content_images()`. Funciona igualmente para PDFs processados via pymupdf4llm, Docling ou Marker — todos geram imagens referenciadas que são consolidadas nesse diretório.

---

## Componentes

### 1. Image Curator (nova tela — `src/ui/image_curator.py`)

**Acesso:** botão "Image Curator" na tela principal, ao lado do "Curator Studio".

**Layout:**

```
┌─────────────────────────────────────────────────────────┐
│ Image Curator — [Nome da Matéria]                       │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  Lista de    │  Painel de imagens da página selecionada │
│  entries     │                                          │
│  (por PDF)   │  ┌──────────┐  ┌──────────┐             │
│              │  │ img1.png │  │ img2.png │             │
│  Página 1    │  │ [tipo ▼] │  │ [tipo ▼] │             │
│  Página 2    │  │ ☑ incluir│  │ ☐ ignorar│             │
│  Página 3    │  └──────────┘  └──────────┘             │
│  ...         │                                          │
│              │  Status: 3/5 imagens selecionadas        │
├──────────────┴──────────────────────────────────────────┤
│ [Pré-classificar]  [Gerar Descrições]  [Fechar]        │
└─────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Lista entries com imagens à esquerda, expandíveis por página
- Painel direito com thumbnails clicáveis (amplia), dropdown de tipo, checkbox incluir/ignorar
- `include_page: false` para ignorar página inteira de uma vez
- Botão "Pré-classificar": heurísticas automáticas
- Botão "Gerar Descrições": dispara LLaVA para imagens marcadas

**Tipos de imagem:**

| Tipo | Uso |
|------|-----|
| `diagrama` | Árvores de prova, fluxogramas, sistemas formais |
| `tabela` | Tabelas-verdade, tabelas de composição |
| `fórmula` | Expressões matemáticas, lógicas |
| `código` | Snippets de código, pseudocódigo |
| `genérico` | Qualquer conteúdo visual relevante |
| `decorativa` | Logos, backgrounds, ícones (ignorada) |

**Pré-classificação automática (heurísticas):**
- Imagem < 5KB ou < 50px em qualquer dimensão → `decorativa`
- Aspect ratio > 6:1 → `decorativa` (barra, header)
- Poucas cores únicas (≤8) → `decorativa` (ícone, fundo sólido)
- Restante → `genérico` (usuário refina)

### 2. Integração Ollama (`src/builder/engine.py`)

**Runtime:** Ollama local, HTTP POST para `http://localhost:11434/api/generate`

**Sem dependência externa nova** — usa urllib/requests já disponível no projeto.

**Verificação de disponibilidade:** antes de gerar descrições, checa se Ollama está rodando e se `llava:7b` está disponível. Mensagem clara ao usuário com instruções se não estiver.

**Prompts especializados (português):**

| Tipo | Prompt (resumo) |
|------|-----------------|
| `diagrama` | "Descreva a estrutura deste diagrama academicamente. Identifique nós, relações, hierarquia e regras representadas. Use notação formal quando possível." |
| `tabela` | "Transcreva esta tabela fielmente em formato markdown. Preserve cabeçalhos, valores e alinhamento." |
| `fórmula` | "Transcreva esta fórmula/expressão matemática em LaTeX. Se houver contexto visual (setas, anotações), descreva-o." |
| `código` | "Transcreva este código exatamente como aparece. Identifique a linguagem se possível." |
| `genérico` | "Descreva o conteúdo desta imagem de forma detalhada e academicamente útil." |
| `decorativa` | Não processada |

**Contexto de página:** ao gerar a descrição de uma imagem, o sistema extrai o texto markdown da mesma página do PDF e o passa como contexto adicional no prompt do LLaVA. Isso permite que informações presentes no texto ao redor (definições, rótulos, ordem de enumeração, nomes de variáveis) sejam refletidas na descrição, produzindo descrições mais fiéis e permitindo reprodução como SVG pelo tutor.

**Execução:** em thread com callback via `after()` (padrão existente no projeto).

### 3. Persistência (`manifest.json`)

Novo campo `image_curation` por entry, organizado por página:

```json
{
  "entry_id": "logicaproposicional-sintaxe",
  "source_file": "Logica-Proposicional-Sintaxe.pdf",
  "image_curation": {
    "status": "described",
    "curated_at": "2026-03-25T14:30:00",
    "pages": {
      "6": {
        "include_page": true,
        "images": {
          "page_6_Figure_1.png": {
            "type": "diagrama",
            "include": true,
            "description": "Árvore de prova mostrando que 4 ∈ ℕ...",
            "described_at": "2026-03-25T14:32:00"
          },
          "page_6_Figure_2.png": {
            "type": "tabela",
            "include": true,
            "description": "Tabela-verdade para conjunção...",
            "described_at": "2026-03-25T14:32:05"
          }
        }
      },
      "7": {
        "include_page": false,
        "images": {}
      }
    }
  }
}
```

**Estados:** `pending` → `curated` → `described`

**Reprocessamento:** ao reprocessar um PDF, compara imagens no disco com chaves no manifest. Imagens novas entram como pending, removidas são limpas.

### 4. Injeção no build

Durante build (completo ou incremental):

1. Lê `image_curation` de cada entry
2. Para imagens com `include: true` e `description` preenchida, injeta blockquote antes da referência `![]()`
3. Formato:

```markdown
<!-- IMAGE_DESCRIPTION: page_6_Figure_1.png -->
<!-- Tipo: diagrama -->
> **[Descrição de imagem]** Árvore de prova mostrando que 4 ∈ ℕ.
> Nó raiz: 4 ∈ ℕ (regra Suc) → 3 ∈ ℕ (regra Suc) → 2 ∈ ℕ (regra Suc)
> → 1 ∈ ℕ (regra Suc) → 0 ∈ ℕ (axioma Zero)
<!-- /IMAGE_DESCRIPTION -->

![](content/images/page_6_Figure_1.png)
```

4. Se já existe bloco `IMAGE_DESCRIPTION` anterior, substitui (permite re-geração)
5. Imagens com `include: false` ficam sem descrição

**Por que blockquote:** comentários HTML podem ser invisíveis para algumas LLMs. Blockquote com bold é texto visível indexável pelas 3 plataformas.

### 5. Suporte a repositórios existentes

- Image Curator lê imagens já em `content/images/`
- Mapeia ao entry/página pelo padrão do filename (`page_X_Figure_Y.png`)
- Não exige reprocessamento do PDF — só curadoria + rebuild
- Imagens sem número de página no nome vão para grupo "Página desconhecida"

---

### 6. Instrução de reprodução SVG no tutor Claude

O arquivo `INSTRUCOES_CLAUDE_PROJETO.md` ganha uma regra para que o Claude reproduza diagramas como SVG interativo a partir dos blocos `[Descrição de imagem]`, consultando o contexto da página para fidelidade. Validado experimentalmente com diagrama de enumeração diagonal de Cantor — reprodução fiel após descrição textual + contexto de página.

---

## Fora de escopo

- OCR separado (LLaVA já faz leitura de texto)
- Upload direto de imagens nas plataformas LLM
- Base64 inline no markdown
- Edição manual de descrições na UI (adição futura possível)

## Dependências externas

- **Ollama** — runtime local para modelos, instalação simples (instalador + `ollama pull llava:7b`)
- **LLaVA 7B** — modelo Vision, ~4.5GB VRAM, cabe na RTX 4050 Mobile

## Fluxo completo

```
PDF → process_single() → extrai imagens (já existe)
         ↓
Image Curator (nova tela) → pré-classifica → usuário seleciona tipo + aprova/rejeita por página
         ↓
"Gerar Descrições" (LLaVA via Ollama) → salva no manifest
         ↓
Build (completo/incremental) → injeta descrições nos markdowns
         ↓
Repositório com texto acessível para Claude, GPT e Gemini
```
