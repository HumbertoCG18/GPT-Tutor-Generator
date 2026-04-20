# Datalab Image Extraction — Design Spec

**Date:** 2026-04-20
**Status:** Approved

## Objetivo

Habilitar a extração de imagens pela API do Datalab e usá-las como fonte primária no Image Curator, mantendo a extração PyMuPDF como fallback. Descrições de imagens continuam sendo geradas pelo Ollama via Image Curator — nenhuma mudança nesse fluxo.

## Contexto

- `DatalabCloudBackend` atualmente chama a API com `disable_image_extraction=True` e ignora `result.images`
- `_strip_markdown_image_refs` remove todas as refs `![]()` do markdown Datalab antes de salvar — comportamento mantido
- PyMuPDF extrai imagens para `staging/assets/images/{entry_id}/page-NNN-img-NN.png` (step 4/6 do pipeline)
- `resolve_content_images` copia imagens referenciadas + imagens de `images_dir` do manifest para `content/images/`
- Image Curator descobre imagens via `group_images_by_page(content/images/, entry_id)` e usa Ollama para gerar descrições

## Mudanças por arquivo

### `src/models/core.py`

Adicionar campo ao dataclass `BackendRunResult`:

```python
images_dir: Optional[str] = None
```

### `src/builder/engine.py` — `DatalabCloudBackend`

**`_convert_range`:** Mudar `disable_image_extraction=True` → `False`.

**Novo método `_save_datalab_images`:**

```python
def _save_datalab_images(self, images: dict, entry_id: str, root_dir: Path) -> tuple[Path, list[str]]:
    images_dir = root_dir / "staging" / "assets" / "images" / entry_id
    ensure_dir(images_dir)
    saved = []
    for filename, b64_data in images.items():
        try:
            import base64
            img_data = base64.b64decode(b64_data)
            out_path = images_dir / f"datalab-{filename}"
            out_path.write_bytes(img_data)
            saved.append(out_path.name)
        except Exception as e:
            logger.warning("Could not save Datalab image %s: %s", filename, e)
    return images_dir, saved
```

**`_run_single_datalab`:** Após `result, markdown = self._convert_range(...)`:

```python
saved_images = []
if result.images:
    images_dir_path, saved_images = self._save_datalab_images(result.images, ctx.entry_id, ctx.root_dir)
```

Atualizar metadata JSON: `"images_saved": saved_images`, `"disable_image_extraction": False`.

Retornar `BackendRunResult(..., images_dir=safe_rel(images_dir_path, ctx.root_dir) if saved_images else None)`.

**`_run_chunked_datalab`:** Para cada chunk, coletar `result.images` e chamar `_save_datalab_images`. Todas as imagens vão ao mesmo `staging/assets/images/{entry_id}/`. Consolidar lista de `saved_images` para o metadata.

### `src/builder/pdf/pdf_pipeline.py`

Após o bloco do advanced backend (linha ~158-201), se o backend for Datalab e salvou imagens:

```python
# dentro do bloco `if result.status == "ok":` já existente
if result.images_dir and not item.get("images_dir"):
    item["images_dir"] = result.images_dir
```

## Convenção de nomes

| Fonte | Padrão de nome |
|---|---|
| Datalab | `datalab-{filename_da_api}.png` (ex: `datalab-0_Figure_1.png`) |
| PyMuPDF | `page-{NNN}-img-{NN}.{ext}` (ex: `page-001-img-01.png`) |

Ambos no mesmo dir `staging/assets/images/{entry_id}/`. Sem conflito de nomes.

## Casos de borda

- **Datalab retorna `images == {}`:** comportamento idêntico ao atual; `images_dir` não é alterado pelo backend
- **PyMuPDF também extrai (`extract_images=True`):** step 4/6 já seta `item["images_dir"]`; a atualização em pdf_pipeline só ocorre se `images_dir` ainda for None
- **Chunked:** cada chunk salva no mesmo dir; filenames do Datalab incluem índice de figura, sem colisão
- **`_strip_markdown_image_refs`:** mantido — imagens fluem pelo Image Curator, não ficam no markdown

## Fluxo completo

```
Datalab API (disable_image_extraction=False)
  → result.images {filename: base64}
  → _save_datalab_images → staging/assets/images/{entry_id}/datalab-*.png
  → item["images_dir"] atualizado no manifest

resolve_content_images (build/approve)
  → copia staging/assets/images/{entry_id}/*.png → content/images/{entry_id}-*.png

Image Curator
  → group_images_by_page(content/images/, entry_id)
  → mostra datalab-* e page-NNN-img-NN juntos
  → Ollama gera descrições (fluxo inalterado)
```

## Fora de escopo

- Opção por entry para habilitar/desabilitar extração Datalab (YAGNI)
- Fusão automática ou priorização de imagens no Image Curator
- Alteração do fluxo de descrição por Ollama
