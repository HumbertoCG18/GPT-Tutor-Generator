# Plano: Image Curator UX — Tipo por imagem + Geração em fila + Confirmação de injeção

**Data:** 2026-04-18  
**Branch sugerida:** `feature/image-curator-type-queue`  
**Arquivo central:** `src/ui/image_curator.py`

---

## Contexto

O fluxo atual do Image Curator tem três problemas de UX:

1. **Tipo não persiste na navegação** — o usuário seleciona o tipo da imagem mas, ao navegar para outra entry no treeview, o tipo volta a "genérico" porque `_on_tree_select` não chama `_save_curation` antes de trocar.
2. **Dois caminhos para LaTeX** — existe um botão "Extrair LaTeX" por imagem E o tipo "extração-latex" no combobox. O usuário quer um único caminho: definir o tipo como "extração-latex" e deixar "Gerar Descrições" rotear para o método correto.
3. **Injeção silenciosa** — `_inject_all_image_descriptions_from_manifest` é chamada no Curator Studio na aprovação (curator_studio.py:934, 1169, 1201-1203), mas o usuário não recebe feedback de qual arquivo foi alvo. A confirmação precisa aparecer logo após a geração.

**Fora de escopo:** remoção da geração do arquivo "Base" (decidir posteriormente).

---

## Phase 0 — Discovered APIs (não executar — já feito)

### Padrões de referência a citar nas fases seguintes

```python
# _generate_descriptions — linhas 1337-1453 (image_curator.py)
# Ponto de roteamento atual (linha 1401):
desc = client.describe_image(img_path, img_type, page_context=page_ctx)
# Alternativa para extração-latex (já existe em OllamaClient):
desc = client.extract_to_latex(img_path, page_context=page_ctx)

# _save_curation — linhas 1156-1207
# Lê self._image_widgets (dict fname -> {type_var, include_var})
# Seguro chamar antes de _show_images substituir os widgets

# _on_tree_select — linhas 545-577
# Chama _show_images sem salvar o estado atual primeiro

# _inject_all_image_descriptions_from_manifest — linhas 143-193
# Assinatura: (repo_dir: Path, manifest: dict) -> None
# Alvo: approved_markdown > curated_markdown > base_markdown > advanced_markdown
# Retorna None — não retorna contagem; ler `seen_targets` antes/depois para diff

# Botão "Pré-classificar" toolbar: _build_ui linhas 250-251
# Botão "Extrair LaTeX" por imagem: _show_images linhas 733-735
```

---

## Phase 1 — Remover botões obsoletos

**Objetivo:** remover UI clutter. Manter os métodos como dead code (não deletar).

### Tarefas

**1.1 — Remover botão "Pré-classificar" do toolbar**

Em `src/ui/image_curator.py`, `_build_ui()` linhas 250-251:

```python
# REMOVER estas linhas:
ttk.Button(
    toolbar, text="Pré-classificar", command=self._preclassify
).pack(side="right", padx=5)
```

**1.2 — Remover botão "Extrair LaTeX" de cada card**

Em `_show_images()` linhas 733-735:

```python
# REMOVER estas linhas:
ttk.Button(
    btn_frame, text="Extrair LaTeX",
    command=lambda fn=fname, ip=img_path: self._extract_latex_single(fn, ip),
).pack(side="left", padx=(0, 4))
```

**1.3 — NÃO remover** os métodos `_preclassify()` e `_extract_latex_single()` — mantê-los como dead code para eventual reuso.

### Verificação

```bash
python -m pytest tests/test_image_curation.py -v
# Verificar manualmente: abrir Image Curator, confirmar que os botões sumiram
# Confirmar que "Gerar Descrições" ainda aparece no toolbar
```

### Anti-patterns

- Não remover `_preclassify()` ou `_extract_latex_single()` do código
- Não alterar `IMAGE_TYPES` — "extração-latex" deve permanecer como tipo válido

---

## Phase 2 — Auto-salvar tipo ao navegar

**Objetivo:** quando o usuário troca a entry no treeview, o tipo selecionado para cada imagem deve ser salvo antes da navegação.

### Tarefa 2.1 — Chamar `_save_curation` no início de `_on_tree_select`

Em `src/ui/image_curator.py`, `_on_tree_select()` linha 545:

```python
def _on_tree_select(self, event=None):
    # ADICIONAR como primeira linha útil, antes de qualquer lógica de seleção:
    self._save_curation()   # persiste tipo/include da page atual antes de trocar
    # ... resto do método existente ...
```

**Por que funciona:** `_save_curation` lê `self._image_widgets` (que ainda aponta para os widgets da entry antiga) e `self._current_entry` / `self._current_page` (também ainda apontam para a seleção anterior). A troca de seleção acontece depois, dentro do mesmo método.

**Cuidado:** `_save_curation` tem guard `if not self._current_entry or self._current_page is None: return` — é seguro chamar mesmo na primeira seleção (entry nula → retorna imediatamente).

### Verificação

```bash
# Smoke test manual:
# 1. Abrir Image Curator, selecionar entry com imagens
# 2. Alterar tipo de uma imagem para "tabela"
# 3. Clicar em outra entry no treeview
# 4. Voltar para a entry original
# 5. Confirmar que o tipo "tabela" foi preservado
python -m pytest tests/test_image_curation.py -v
```

### Anti-patterns

- Não adicionar um `<<ComboboxSelected>>` binding por widget — geraria uma write por interação e conflito com `_image_widgets` parcialmente construído
- Não chamar `_load_manifest()` na troca — isso perderia edições não salvas

---

## Phase 3 — Gerar Descrições: roteamento por tipo + confirmação de injeção

**Objetivo:** (a) quando o tipo for "extração-latex", chamar `extract_to_latex` em vez de `describe_image`; (b) após a geração, injetar imediatamente no markdown alvo e mostrar messagebox confirmando qual arquivo foi atingido.

### Tarefa 3.1 — Rotear por tipo em `_generate_descriptions`

Em `_generate_descriptions()` linha 1401 (dentro do loop de background thread):

```python
# SUBSTITUIR:
desc = client.describe_image(img_path, img_type, page_context=page_ctx)

# POR:
if img_type == "extração-latex":
    desc = client.extract_to_latex(img_path, page_context=page_ctx)
else:
    desc = client.describe_image(img_path, img_type, page_context=page_ctx)
```

Referência: `extract_to_latex(self, image_path: Path, page_context: str) -> str` já existe em `OllamaClient` (linhas 316-331 de `src/builder/ollama_client.py`). Assinatura sem `img_type`.

### Tarefa 3.2 — Injetar e confirmar após geração

Ainda em `_generate_descriptions()`, na callback `_finish()` que roda via `self.after(...)` após o thread terminar (em torno da linha 1432-1447):

```python
# ADICIONAR após o status_var.set(...) de conclusão:
injected_paths = _inject_for_current_entry(self.repo_dir, self._current_entry)
if injected_paths:
    targets = ", ".join(p.name for p in injected_paths)
    messagebox.showinfo(
        "Descrições geradas",
        f"{generated} descrição(ões) gerada(s).\n"
        f"Injetadas em: {targets}\n\n"
        "Na aprovação do Curator Studio a injeção será repetida "
        "automaticamente na fonte correta.",
    )
else:
    messagebox.showinfo(
        "Descrições geradas",
        f"{generated} descrição(ões) gerada(s).\n"
        "Nenhum markdown alvo encontrado ainda — "
        "a injeção ocorrerá ao aprovar no Curator Studio.",
    )
```

**Implementar helper `_inject_for_current_entry`** como função privada de módulo (não método), logo abaixo de `_inject_all_image_descriptions_from_manifest`. Ele injeta as descrições **e** remove as referências `![](path)` das imagens já descritas:

```python
def _inject_for_current_entry(repo_dir: Path, entry: dict) -> list[Path]:
    """Inject descriptions + strip image path refs for a single entry; return modified paths."""
    if not entry:
        return []
    modified = []
    curation = entry.get("image_curation") or {}
    for key in ("approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"):
        rel = str(entry.get(key) or "").strip()
        if not rel:
            continue
        path = repo_dir / rel
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            new_text = _low_token_inject_image_descriptions(
                text, curation,
                desc_block_re=_IMAGE_DESC_BLOCK_RE,
                image_heading=_image_curation_heading_label,
            )
            new_text = _strip_described_image_refs(new_text, curation)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                modified.append(path)
        except Exception as exc:
            logger.warning("Could not inject into %s: %s", path, exc)
    return modified
```

### Tarefa 3.3 — Remover referências `![](path)` de imagens já descritas

**Racional:** `![](content/images/revisao-_page_21_Picture_1.png)` é ruído para a LLM — o tutor não consegue abrir a imagem. A descrição injetada é o conteúdo útil; o caminho só tem valor no Image Curator (aba de visualização no backlog). Logo, depois de injetar a descrição, o `![](...)` do mesmo arquivo deve ser removido do markdown.

**Implementar helper `_strip_described_image_refs`**, logo acima de `_inject_for_current_entry`:

```python
_IMAGE_REF_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

def _strip_described_image_refs(text: str, curation: dict) -> str:
    """Remove ![...](path) refs for images that already have injected descriptions."""
    described_fnames: set[str] = set()
    for page_data in (curation.get("pages") or {}).values():
        for fname, img_data in (page_data.get("images") or {}).items():
            if img_data.get("description"):
                described_fnames.add(fname)
    if not described_fnames:
        return text

    def _sub(m: re.Match) -> str:
        fname = Path(m.group(2)).name
        return "" if fname in described_fnames else m.group(0)

    text = _IMAGE_REF_RE.sub(_sub, text)
    # Collapse blank lines left by removed refs (máx 2 consecutivos)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text
```

**Nota:** a função remove o `![](...)` inline (não a linha inteira), para não cortar texto adjacente em parágrafos. Linhas que ficam completamente vazias após a remoção são colapsadas pelo segundo regex.

**Também adicionar a mesma chamada em `_inject_all_image_descriptions_from_manifest`** (linha ~183), para que a remoção aconteça também na aprovação via Curator Studio:

```python
# Após a chamada _low_token_inject_image_descriptions existente:
new_text = _strip_described_image_refs(new_text, curation)
```

### Verificação

```bash
python -m pytest tests/test_image_curation.py -v -k "inject or describe or latex"
# Novo teste a criar (ver Phase 4):
# test_generate_descriptions_routes_latex_type
```

### Anti-patterns

- Não chamar `_inject_all_image_descriptions_from_manifest` passando o manifest completo — injeta em TODAS as entries e é lento; usar só a entry atual
- Não bloquear a thread principal no inject — a chamada acima acontece na callback `_finish()` (já no thread principal via `after()`), mas é rápida para uma entry

---

## Phase 4 — Testes

**Objetivo:** cobrir o roteamento por tipo e a lógica de injeção pontual.

### Tarefa 4.1 — Teste de roteamento por tipo

Em `tests/test_image_curation.py`, adicionar:

```python
def test_generate_descriptions_routes_extração_latex(tmp_path, monkeypatch):
    """When image type is 'extração-latex', extract_to_latex must be called, not describe_image."""
    from unittest.mock import MagicMock, patch
    # ...
    # Verificar que client.extract_to_latex é chamado quando img_type == "extração-latex"
    # e client.describe_image é chamado para outros tipos
```

Padrão de mock: ver testes existentes em `tests/test_image_curation.py` que já mockam `OllamaClient` — copiar a fixture de setup.

### Tarefa 4.2 — Teste de `_inject_for_current_entry`

```python
def test_inject_for_current_entry_targets_advanced_markdown(tmp_path):
    from src.ui.image_curator import _inject_for_current_entry
    # Criar advanced_markdown com placeholder de imagem
    # Chamar _inject_for_current_entry com entry contendo descriptions
    # Verificar que o arquivo foi modificado e o path retornado
```

### Tarefa 4.3 — Teste de `_strip_described_image_refs`

```python
def test_strip_described_image_refs_removes_only_described(tmp_path):
    from src.ui.image_curator import _strip_described_image_refs

    curation = {
        "pages": {
            "1": {
                "images": {
                    "fig1.png": {"description": "Diagrama de blocos", "type": "diagrama"},
                    "fig2.png": {"description": None, "type": "genérico"},
                }
            }
        }
    }
    text = (
        "## Seção\n\n"
        "Texto antes.\n\n"
        "![Figura 1](content/images/fig1.png)\n\n"
        "Texto entre.\n\n"
        "![](content/images/fig2.png)\n\n"
        "Texto depois.\n"
    )
    result = _strip_described_image_refs(text, curation)
    # fig1 tem descrição — referência deve sumir
    assert "fig1.png" not in result
    # fig2 NÃO tem descrição — referência deve permanecer
    assert "fig2.png" in result
    # Texto preservado
    assert "Texto antes." in result
    assert "Texto depois." in result
    # Sem triplas linhas em branco
    assert "\n\n\n" not in result
```

### Verificação final

```bash
python -m pytest tests/ -v
# Confirmar: todos os testes passando
# Confirmar: nenhum "Extrair LaTeX" ou "Pré-classificar" nos logs de UI
```

---

## Resumo de mudanças por arquivo

| Arquivo | Mudanças |
|---|---|
| `src/ui/image_curator.py` | Remover 2 botões; adicionar `_save_curation()` em `_on_tree_select`; rotear por tipo em `_generate_descriptions`; adicionar `_strip_described_image_refs` + `_inject_for_current_entry`; messagebox de confirmação |
| `tests/test_image_curation.py` | 2 novos testes (roteamento + injeção pontual) |

**Fora do escopo desta iteração:** remoção da geração do arquivo "Base" — decidir fluxo later.
