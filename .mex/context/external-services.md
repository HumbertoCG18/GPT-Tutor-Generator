---
name: external-services
description: Todo serviço externo do sistema (pago ou local) — Gemini, Datalab, Ollama, Moodle, M365 — onde cada um é chamado, sob qual flag, e o que acontece quando falta. Carregue antes de mexer em custo, em backend de extração, em descrição de imagem, ou ao responder "isso depende de API paga?".
triggers:
  - "datalab"
  - "gemini"
  - "ollama"
  - "marker"
  - "mineru"
  - "docling"
  - "api paga"
  - "custo"
  - "open source"
  - "backend de extração"
  - "descrição de imagem"
  - "vision"
edges:
  - target: context/text-chain.md
    condition: when the question is which text the motor reads and where descriptions land
  - target: context/pdf-pipeline.md
    condition: when the question is the PDF backend selection mechanics
  - target: patterns/ollama-vision.md
    condition: when working on the vision client itself
last_updated: 2026-09-07
---

# Serviços Externos

Auditado por leitura de código em 07/09/2026 (dois levantamentos independentes) + contagem nos manifests dos 8 tutores.
Contrato e pontos de acoplamento; números vivos ficam no tracker.

## Quem é quem

| serviço | módulo | custo | chave | ativo hoje |
|---|---|---|---|---|
| **Datalab** | `runtime/datalab_client.py` | **pago** (crédito por página) | `DATALAB_API_KEY`, só via env/.env (não há campo na UI) | sim, dominante |
| **Gemini** | `runtime/gemini_client.py` | **pago** | `config["gemini_api_key"]` > `GEMINI_API_KEY` | sim, tudo opt-in e default OFF |
| **Ollama** | `vision/ollama_client.py` | local — **mas o modelo default é cloud** | `ollama signin` se cloud | só pela UI (Image Curator) |
| Moodle WS, MS Graph, GitHub API, git clone | `sources/moodle.py`, `sources/m365.py`, `core/reference_content.py` | gratuitos | token do aluno / device code | sim |

Não há uso de OpenAI, Anthropic, Azure, Mistral, Cohere ou HuggingFace em `src/`.

## Dependência de API paga por eixo

| eixo | depende de pago hoje? | alternativa local existe? |
|---|---|---|
| **Texto do material (PDF → markdown)** | não obrigatoriamente | **sim, completa**: pymupdf4llm/pymupdf (base), docling CLI, docling_python, marker (avançado). Sem `DATALAB_API_KEY` o seletor nem oferece Datalab. |
| **Descrição de imagem** | **sim quando `image_description_source == "datalab"`** | sim (Ollama `describe_image`), **mas só pela UI, nunca no build**, e o modelo default é cloud |
| **Fórmulas em PDF** | não | sim (Ollama `extract_to_latex`, marker/docling com enrich-formula) |
| **Fórmulas em página HTML** | **sim, sem saída** | **não** — `core/html_material.py:45` faz uma chamada Datalab paga **por imagem** (cap 400/build); sem chave a imagem vira `![… — não capturada]`. É o acoplamento pago mais duro do sistema. |
| **Vocabulário (sinônimos)** | não (opt-in, default OFF) | sim: sidecar manual `course/.glossary_curation.json` vence tudo |
| **Voto de bloco** | não (opt-in, default OFF) | sim, é o default: `voter=None` dá saída byte-idêntica ao motor determinístico |
| **Resumo de código** | não (opt-in, default OFF) | **parcial**: `assign_code_to_block` é local e determinístico, mas hoje só roda dentro do bloco que exige o Gemini (`core/code_summarization.py:409`) |

## Seleção de provedor de descrição — já existe, com limites

- Config `image_description_source`, default `"ollama"`, valores aceitos **apenas** `["ollama", "datalab"]` (`ui/theme.py:114`, combo em `ui/dialogs.py:409`).
- `"datalab"`: as captions vêm junto da conversão (`engine.py:857 _extract_datalab_captions`), gravadas em `image_curation.pages[].images[]` com `source: "datalab"`. **Único lugar que escreve o campo `source`.**
- `"ollama"`: `vision/ollama_client.py:294 describe_image`, chamado **só** por `ui/image_curator.py` (botões "Descrever" e "Gerar Descrições"), que **só aparecem quando a fonte não é datalab**. Não grava `source` — descrição do Ollama é indistinguível de descrição digitada à mão.
- Não há Gemini nessa chave, embora `GeminiClient.generate_text(prompt, image_path=)` seja multimodal e já descreva figura no caminho HTML.
- **Em nenhum dos dois modos o build automático gera descrição**: no modo datalab vêm de carona na conversão; no modo ollama dependem de clique humano.

Para atender "escolher entre Datalab, Gemini e Ollama" faltam três coisas, todas pequenas: aceitar `"gemini"` na chave, chamar o provedor no build (não só na UI), e gravar `source` nos três caminhos.

## Onde a descrição acaba

`extraction/image_markdown.py:286` injeta o bloco `<!-- IMAGE_DESCRIPTION: … -->` **em todos os markdowns da entry que existirem** (`approved`, `curated`, `base`, `advanced`), logo antes da linha da imagem, e remove a referência `![…]()` correspondente (`:267`). Como o motor lê `approved > curated > base`, a descrição sempre entra no texto pontuado. Medido: piora a atribuição (ver `context/text-chain.md` §4).

## Fallbacks (o que acontece quando falta)

- **Gemini ausente** → `get_gemini_client` devolve `None`; voter mantém FLAG (não chuta), vocabulário não compila, resumo de código não roda, referência degrada para mapeamento por texto. Nada quebra.
- **Datalab ausente** → `DatalabCloudBackend.available()` é `False` e o seletor cai para marker/docling/pymupdf, todos locais. Em runtime, erro do Datalab é registrado e a build segue com o `base_markdown`. Exceção: imagens de HTML ficam sem transcrição, sem alternativa.
- **Ollama ausente** → a ação da UI aborta com erro; se o modelo cloud não estiver disponível, troca sozinho para `qwen3-vl:8b` local (`ollama_client.py:180`). Cuidado: em lote, o texto de erro vira a própria descrição no manifest e **é injetado no markdown**.

## Armadilhas conhecidas (verificadas, não corrigidas)

1. `ui/theme.py:89-93` reescreve ativamente o modelo de visão local `qwen3-vl:8b` para `qwen3-vl:235b-cloud` a cada load. Quem configura local perde a escolha.
2. `core/html_material.py:27` cap de 400 chamadas Datalab por build; ao estourar, as imagens seguintes viram `![… — não capturada (cap 400)]` sem erro nem linha no relatório.
3. `core/code_summarization.py:409`: o matcher local está dentro do try que exige o client. Espelhar o padrão de `core/reference_summary.py` (rodar com `client=None`) daria atribuição de código sem API paga.
