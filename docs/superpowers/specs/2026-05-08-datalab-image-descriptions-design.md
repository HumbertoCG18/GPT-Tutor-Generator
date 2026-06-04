# Design: Fonte de Descrições de Imagem (DataLab vs Ollama)

**Data:** 2026-05-08
**Branch:** new-features
**Escopo:** `src/ui/theme.py`, `src/ui/app.py`, `src/builder/engine.py`, `src/builder/runtime/datalab_client.py`, `src/ui/image_curator.py`
**Status:** Não implementado

---

## Contexto

O Image Curator atualmente usa exclusivamente o Ollama para gerar descrições de imagens extraídas de PDFs. O DataLab, utilizado na conversão de documentos, tem suporte nativo a captions (`disable_image_captions=False`), mas essa feature está desativada em todas as chamadas do engine. Este design habilita o DataLab como fonte alternativa de descrições, gerando-as na etapa de conversão em vez de em runtime via Ollama.

---

## Objetivo

1. Adicionar configuração global `image_description_source` ("ollama" | "datalab").
2. Quando "datalab": ativar captions na conversão, extrair e armazenar no manifest, e mudar o ImageCurator para modo leitura.
3. Quando "ollama": comportamento atual inalterado.

---

## Arquitetura

### 1. Configuração — `AppConfig` em `theme.py`

Novo campo:
```python
image_description_source: str = "ollama"  # "ollama" | "datalab"
```

Não reutilizar `vision_backend`: aquele campo controla qual modelo de visão usar em runtime; este novo controla *quando* as descrições são geradas. Semânticas independentes.

### 2. Settings UI — `app.py`

No painel de configurações onde já ficam `vision_backend` e `vision_model`, adicionar:

- **Label:** "Fonte de descrições de imagem"
- **Combobox:** `["Ollama (local)", "DataLab (na conversão)"]`
- **Nota:** "DataLab gera descrições durante a conversão do PDF. Reprocesse os documentos após mudar esta opção."

### 3. Engine — `engine.py` + `datalab_client.py`

#### 3a. Ativação de captions

As três chamadas a `convert_document_to_markdown()` em `engine.py` passam hoje `disable_image_captions=True` fixo. Mudar para:

```python
disable_image_captions=(config.image_description_source != "datalab")
```

#### 3b. Extração das captions — `_extract_datalab_captions(markdown, entry_id, repo_root)`

Nova função chamada após a conversão DataLab quando captions estão ativas. Responsabilidades:

1. Parsear o markdown com regex `!\[([^\]]*)\]\(([^)]+)\)` para extrair `(caption, filename)`.
2. Para cada imagem, gravar no manifest `image_curation` o mesmo formato que o Ollama usa, com campo adicional `"source": "datalab"`:

```json
{
  "description": "texto da caption",
  "source": "datalab",
  "described_at": "2026-05-08T12:00:00"
}
```

3. Marcar status como `"described"` automaticamente (sem interação no curator).
4. Imagens sem caption do DataLab: gravar `description: ""` e `source: "datalab"` para que o curator identifique a origem.

### 4. ImageCurator — `image_curator.py`

#### Modo DataLab (`config.image_description_source == "datalab"`)

**Desativado:**
- Botão de captura de região (crop mode) — oculto completamente
- Botões "Gerar descrição" e "Gerar todas" — ocultos
- Combobox de tipo de imagem — somente leitura

**Exibido:**
- Cards das imagens com a descrição DataLab inline
- Imagens sem caption: placeholder em itálico *"Sem descrição do DataLab"*
- Banner no topo: *"Modo DataLab — descrições geradas na conversão. Reprocesse para atualizar."*

**Entry nunca processada com DataLab captions** (processada antes da mudança de configuração): banner amarelo *"Este documento foi processado sem captions do DataLab. Reprocesse para obter as descrições."*

**Edição manual:** permitida — o usuário pode editar a descrição no campo de texto mesmo em modo DataLab. O campo `source` permanece `"datalab"` após edição (não rastrear override).

#### Modo Ollama (padrão)

Comportamento atual inalterado.

---

## Fluxo de dados

```
Configuração: image_description_source = "datalab"

Build (engine.py)
  → convert_document_to_markdown(disable_image_captions=False)
  → DataLab retorna markdown com ![caption](img.png)
  → _extract_datalab_captions(markdown, entry_id, repo_root)
  → manifest["image_curation"][page][image]["description"] = caption
  → manifest["image_curation"][page][image]["source"] = "datalab"
  → status = "described"

ImageCurator abre
  → detecta image_description_source == "datalab"
  → oculta controles de geração e captura
  → exibe descrições do manifest em modo leitura
  → banner informativo no topo
```

---

## O que não muda

- `vision_backend`, `vision_model`, `ollama_base_url`: sem alterações.
- Pipeline de injeção de descrições no markdown final (`image_resolution.py`, `image_markdown.py`): sem alterações — consome `description` do manifest independente de `source`.
- Estrutura do manifest `image_curation`: sem alterações de schema, apenas adição do campo `source`.
- Modo Ollama: comportamento atual 100% preservado.

---

## Casos de borda

- **Sem chave DataLab configurada**: o engine já valida isso antes de chamar o DataLab; não há risco de chamada com captions sem autenticação.
- **Caption vazia no DataLab** (DataLab não identificou conteúdo): `description: ""`, curator exibe placeholder.
- **Troca de "datalab" para "ollama" sem reprocessar**: curator volta ao modo Ollama e mostra as imagens para geração via Ollama — as descrições DataLab já salvas no manifest são preservadas mas ignoradas pelo modo Ollama.
- **Imagens capturadas manualmente (crop)** em documentos processados antes da troca: essas imagens não têm `source: "datalab"` e ficam sem descrição em modo DataLab; o usuário precisará reprocessar ou editar manualmente.
