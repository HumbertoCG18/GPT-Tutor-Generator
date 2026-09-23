# TimelineDashboard — Design Spec

date: 2026-05-12
status: approved

---

## Problema

O mapeamento bloco×arquivo vive espalhado entre `timeline_index.json`, `FILE_MAP.md` e o campo `manual_timeline_block_id` no manifest. Não existe visão única. Para diagnosticar erro de mapeamento o usuário precisa abrir três artefatos e cruzar manualmente. Para corrigir, precisa editar `manifest.json` na mão.

---

## Solução

Nova janela `TimelineDashboard` — Toplevel Tkinter — que exibe o cronograma da disciplina como accordion de blocos, com os arquivos mapeados a cada bloco e dropdown para atribuição manual de `manual_timeline_block_id`.

---

## Decisões de Design

| Decisão | Escolha | Razão |
|---|---|---|
| Layout | Accordion (lista única, blocos expansíveis) | Visão sequencial do semestre; foco em um bloco por vez |
| Atribuição manual | Dropdown por arquivo | Sem D&D — menor custo, suficiente para o caso de uso |
| Tipo de janela | `tk.Toplevel` | Consistente com `RepoDashboard`, `CuratorStudio`, `ImageCurator` |
| Arquivos sem bloco | Seção colapsável no rodapé | Cronograma é foco principal; órfãos são limpeza secundária |
| Leitura de dados | Direta de `manifest.json` + `timeline_index.json` | Sem repassar pelo engine em runtime; testável isolado |

---

## Arquivos Envolvidos

| Arquivo | Tipo | O que muda |
|---|---|---|
| `src/ui/timeline_dashboard.py` | Novo | Toda a implementação da janela |
| `src/ui/app.py` | Modificação cirúrgica | Import + item `📅 Timeline` no menu `🗂 Repo` do backlog toolbar |
| `tests/test_timeline_dashboard_data.py` | Novo | 3 testes de lógica de dados (sem UI) |

Zero toque em `src/builder/`.

---

## Arquitetura

### Classe principal

```python
class TimelineDashboard(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        subject: SubjectProfile,
        enqueue_reprocess_fn: Callable[[], None],
    ): ...
```

`enqueue_reprocess_fn` é injetado por `app.py` — evita importar o app de dentro do dashboard.

### Métodos internos

**`_load_data() -> tuple[list[dict], dict[str, list[dict]], list[dict]]`**

Lê os dois artefatos do disco e devolve:
- `blocks`: lista ordenada de blocos do `timeline_index.json`
- `entries_by_block_id`: `{block_id: [entry, ...]}` — entries cujo `auto_tags` contém `bloco:<block_id>` OU `manual_timeline_block_id == block_id`
- `unmapped`: entries sem nenhum dos dois

Caminhos:
```
repo_root / "manifest.json"
repo_root / "course" / "timeline_index.json"
```

**`_build_accordion()`**

Itera `blocks` em ordem cronológica. Para cada bloco cria um frame colapsável. Ao final adiciona a seção "Sem bloco atribuído".

**`_on_block_assigned(entry_id: str, block_id: str | None)`**

1. Lê `manifest.json`
2. Localiza entry por `id`
3. Seta `manual_timeline_block_id` (ou deleta a chave se `block_id is None`)
4. Salva `manifest.json` com `ensure_ascii=False, indent=2`
5. Revela o botão "🔄 Reprocessar" se ainda oculto

---

## Visual

### Accordion — bloco expandido

```
▼  12/03/2026 — Processos          Unidade 1 · aula          [2 arquivos]
   📄 12.03 Processos.pdf   conf 0.92  🗓 DD.MM   [dropdown ▾]
   🔗 Slides Aula 3         conf 0.74             [dropdown ▾]
```

### Accordion — bloco com gap (laranja)

```
▶  05/05/2026 — Gerência de Memória   Unidade 2 · aula   [⚠ 0 arquivos]
```

### Accordion — bloco ignorado (atenuado)

```
▶  19/05/2026 — Prova 1   prova · ignorado   ⊘
```

### Seção rodapé

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▶  ⚠ Sem bloco atribuído           [3 arquivos]
```

### Dropdown de atribuição

Opções: `✓ <bloco atual> (auto)` · cada bloco disponível · `— remover atribuição`.
Ao selecionar qualquer opção diferente do atual: chama `_on_block_assigned`.

### Toolbar

```
Repositório: ~/repos/so-2026          [🔄 Reprocessar]  [↺ Recarregar]
```

Botão "Reprocessar" oculto no load; aparece após primeira atribuição. Chama `enqueue_reprocess_fn()`.

---

## Cores e Tema

Segue `apply_theme_to_toplevel()` (convenção da UI atual).

| Estado | Cor de destaque |
|---|---|
| Bloco com arquivos | Normal |
| Bloco gap (0 arq) | Laranja `#ffaa44` |
| Bloco ignorado (prova/feriado/revisão) | Atenuado, opacity ~40% |
| Badge DD.MM | Azul `#5aafff` |
| Score alto (≥0.80) | Verde `#7aff7a` |
| Score médio (0.50–0.79) | Azul `#5aafff` |
| Score baixo (<0.50) | Laranja `#ffaa44` |

---

## Tratamento de Erros

Todos os erros são exibidos como label centralizado na janela (sem raise):

| Condição | Mensagem |
|---|---|
| Nenhum repositório selecionado | `"Selecione um repositório com build gerado"` |
| `manifest.json` ausente | `"Build não encontrado — gere o repositório primeiro"` |
| `timeline_index.json` ausente | `"Nenhum cronograma detectado — o SYLLABUS foi carregado?"` |
| JSON inválido | `"Erro ao ler artefatos — veja o log"` |

---

## Testes

Arquivo: `tests/test_timeline_dashboard_data.py`

Testa apenas lógica de dados — sem instanciar widgets Tkinter.

- `test_load_data_separates_mapped_and_unmapped`: fixture manifest + timeline_index → verifica que entries com `bloco:` tag vão para `entries_by_block_id` e entries sem tag/manual vão para `unmapped`
- `test_on_block_assigned_writes_manifest`: chama `_on_block_assigned(entry_id, block_id)` → verifica que `manifest.json` gravado contém `manual_timeline_block_id` correto
- `test_on_block_assigned_none_removes_field`: `_on_block_assigned(entry_id, None)` → campo removido do JSON

---

## Ponto de Entrada no App

Em `src/ui/app.py`, no menu `🗂 Repo` do backlog toolbar:

```python
backlog_repo_menu.add_command(
    label="📅 Timeline",
    command=self._open_timeline_dashboard,
)
```

```python
def _open_timeline_dashboard(self):
    subject = self._get_selected_subject()
    if not subject:
        messagebox.showwarning("Timeline", "Selecione um repositório primeiro.")
        return
    TimelineDashboard(
        self,
        subject=subject,
        enqueue_reprocess_fn=self.enqueue_current_repo_refresh,
    )
```

---

## Fora de Escopo (v1)

- Drag-and-drop entre blocos
- Exportar `TIMELINE_MAP.md` como artefato adicional
- Filtros por unidade ou status
- Edição inline de labels de bloco
