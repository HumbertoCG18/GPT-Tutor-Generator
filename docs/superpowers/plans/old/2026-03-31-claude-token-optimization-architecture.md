# Claude Token Optimization Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir o consumo de tokens no Claude Web por meio de uma arquitetura de navegação enxuta, menos redundância no repositório e artefatos regeneráveis via `Reprocessar Repositório`.

**Architecture:** O repositório passa a ter uma camada explícita de “contexto de alto sinal e baixo custo”, gerada a partir do `manifest.json` e dos arquivos curados já existentes. Em vez de adicionar documentação redundante, o pipeline deve enxugar `FILE_MAP`, `COURSE_MAP`, `bundle.seed.json` e instruções do projeto para funcionarem como roteadores de contexto, além de deduplicar/atenuar repetição visual e textual. Todas as mudanças devem ser regeneráveis por `RepoBuilder.incremental_build()` sem exigir reprocesar PDFs crus.

**Tech Stack:** Python 3.11, tkinter/ttk, JSON persistence, pathlib, pytest, markdown generation no `RepoBuilder`.

---

## Estrutura de Arquivos

### Novos arquivos

- `tests/test_token_optimization.py`
  Testes da nova arquitetura de compressão de contexto: deduplicação de imagem, mapas enxutos, bundle seletivo e artefatos Claude-friendly.

### Arquivos a modificar

- `src/builder/engine.py`
  Coração da mudança. Deve gerar artefatos mais econômicos, reduzir redundância e tornar a arquitetura aplicável por reprocessamento.

- `src/ui/app.py`
  UX do `Reprocessar Repositório` e status associado à nova arquitetura de baixo token.

- `src/ui/dialogs.py`
  Central de Ajuda e textos de UX explicando a estratégia de contexto enxuto.

- `src/ui/image_curator.py`
  Aplicar regras de repetição/descrição econômica que influenciam o custo final do contexto.

- `README.md`
  Documentar a estratégia de baixo consumo de tokens e o uso com Claude Web.

- `docs/CHATGPT_HANDOFF_PROMPT.md`
  Atualizar o handoff técnico para refletir a arquitetura nova e o uso de `Reprocessar Repositório`.

---

## Princípios Arquiteturais

1. `Reprocessar Repositório` deve ser suficiente para aplicar a nova arquitetura a repositórios já existentes.
2. `FILE_MAP.md` e `COURSE_MAP.md` devem virar roteadores curtos, não duplicações do conteúdo.
3. O bundle inicial do Claude deve ser mais seletivo e menor.
4. Descrições de imagem devem ser úteis, mas compactas.
5. Duplicatas visuais/textuais não devem amplificar contexto sem necessidade.
6. Novos artefatos só são aceitos se substituírem leitura de arquivos grandes, não se apenas adicionarem mais contexto.

---

### Task 1: Medir e formalizar o que é “contexto caro” no repositório

**Files:**
- Create: `tests/test_token_optimization.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Escrever o teste base de detecção de redundância textual em FILE_MAP**

```python
from src.builder.engine import file_map_md


def test_file_map_stays_short_and_route_oriented():
    entries = [
        {
            "title": "Aula 01",
            "category": "material-de-aula",
            "base_markdown": "content/curated/aula01.md",
            "advanced_markdown": "staging/markdown-auto/marker/aula01.md",
            "tags": "unidade-1",
            "source_path": "raw/pdfs/aula01.pdf",
            "include_in_bundle": True,
            "relevant_for_exam": True,
        }
    ]
    result = file_map_md({"course_name": "IA"}, entries)

    assert "quando usar" in result.lower() or "uso" in result.lower()
    assert "conteúdo completo do arquivo" not in result.lower()
```

- [ ] **Step 2: Rodar o teste para garantir que falha ou não cobre o comportamento novo**

Run: `pytest tests/test_token_optimization.py::test_file_map_stays_short_and_route_oriented -v`

Expected: FAIL ou output insuficiente para a arquitetura desejada.

- [ ] **Step 3: Adicionar helper de classificação de custo/contexto**

```python
def classify_context_cost(entry: dict) -> str:
    category = entry.get("category", "")
    if category in {"provas", "gabaritos", "listas"}:
        return "high-value"
    if category in {"referencias", "bibliografia"}:
        return "low-priority"
    return "medium"
```

- [ ] **Step 4: Escrever teste de prioridade de contexto**

```python
from src.builder.engine import classify_context_cost


def test_classify_context_cost_prioritizes_exam_material():
    assert classify_context_cost({"category": "provas"}) == "high-value"
    assert classify_context_cost({"category": "bibliografia"}) == "low-priority"
```

- [ ] **Step 5: Rodar a suíte inicial**

Run: `pytest tests/test_token_optimization.py -q`

Expected: PASS para os helpers básicos.

- [ ] **Step 6: Commit**

```bash
git add tests/test_token_optimization.py src/builder/engine.py
git commit -m "test: define baseline for low-token repository architecture"
```

### Task 2: Enxugar o FILE_MAP para atuar como roteador de contexto

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_token_optimization.py`

- [ ] **Step 1: Escrever o teste da nova forma do FILE_MAP**

```python
def test_file_map_prefers_short_routing_fields():
    entries = [
        {
            "title": "Aula 01",
            "category": "material-de-aula",
            "tags": "unidade-1",
            "base_markdown": "content/curated/aula01.md",
            "advanced_markdown": None,
            "source_path": "raw/pdfs/aula01.pdf",
            "include_in_bundle": True,
            "relevant_for_exam": True,
        }
    ]
    result = file_map_md({"course_name": "IA"}, entries)

    assert "| Quando usar |" in result
    assert "| Prioridade |" in result
    assert "raw/pdfs/aula01.pdf" in result
```

- [ ] **Step 2: Implementar colunas curtas e sem duplicação**

```python
lines.append("| Título | Categoria | Unidade | Prioridade | Quando usar | Arquivo |")
```

Regras:
- uma linha por entry
- sem repetir resumo longo do documento
- incluir apenas pista curta de uso
- favorecer `approved_markdown`/`curated_markdown` antes de `base_markdown`/`advanced_markdown`

- [ ] **Step 3: Adicionar heurística “quando usar”**

```python
def file_usage_hint(entry: dict) -> str:
    category = entry.get("category", "")
    if category == "provas":
        return "consultar em revisão para prova e padrões de cobrança"
    if category == "gabaritos":
        return "usar para resolução e comparação de resposta"
    if category == "material-de-aula":
        return "usar para teoria e exemplos da unidade"
    return "consultar sob demanda"
```

- [ ] **Step 4: Rodar testes do FILE_MAP**

Run: `pytest tests/test_token_optimization.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_token_optimization.py
git commit -m "feat: turn file map into low-token context router"
```

### Task 3: Enxugar o COURSE_MAP para alto sinal sem virar apostila paralela

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_token_optimization.py`

- [ ] **Step 1: Escrever teste do COURSE_MAP compacto**

```python
from src.builder.engine import course_map_md


def test_course_map_focuses_on_structure_not_full_content():
    result = course_map_md(
        {
            "course_name": "IA",
            "syllabus": "Semana 1: Introdução\nSemana 2: Busca",
            "teaching_plan": "Conteúdos: IA, busca, ML",
        },
        [],
    )

    assert "tópicos centrais" in result.lower()
    assert "materiais prioritários" in result.lower()
```

- [ ] **Step 2: Ajustar COURSE_MAP para 4 blocos curtos**

Blocos recomendados:
- visão da disciplina
- unidades/tópicos centrais
- relação com provas/listas/trabalhos
- materiais prioritários

Evitar:
- copiar o plano de ensino inteiro
- repetir cronograma completo em prosa longa

- [ ] **Step 3: Rodar teste**

Run: `pytest tests/test_token_optimization.py -q`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/builder/engine.py tests/test_token_optimization.py
git commit -m "feat: compress course map for low-token navigation"
```

### Task 4: Tornar o bundle do Claude agressivamente seletivo

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_token_optimization.py`

- [ ] **Step 1: Escrever teste de bundle seletivo**

```python
def test_bundle_seed_prioritizes_high_value_entries(tmp_path):
    from src.builder.engine import RepoBuilder

    manifest = {
        "generated_at": "2026-03-31T03:00:00",
        "entries": [
            {"title": "Prova 1", "category": "provas", "include_in_bundle": True, "relevant_for_exam": True},
            {"title": "Bibliografia", "category": "bibliografia", "include_in_bundle": True, "relevant_for_exam": False},
        ],
    }
    selected = RepoBuilder._select_bundle_entries(manifest["entries"])

    assert selected[0]["title"] == "Prova 1"
```

- [ ] **Step 2: Extrair o seletor puro de entries do bundle**

```python
@staticmethod
def _select_bundle_entries(entries: list[dict]) -> list[dict]:
    def score(entry):
        value = 0
        if entry.get("relevant_for_exam"):
            value += 5
        if entry.get("category") in {"provas", "gabaritos", "listas"}:
            value += 4
        if entry.get("category") in {"bibliografia", "referencias"}:
            value -= 2
        return value

    selected = [e for e in entries if e.get("include_in_bundle")]
    return sorted(selected, key=score, reverse=True)[:25]
```

- [ ] **Step 3: Aplicar o seletor no `_write_bundle_seed()`**

```python
selected = self._select_bundle_entries(manifest["entries"])
```

- [ ] **Step 4: Rodar testes**

Run: `pytest tests/test_token_optimization.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_token_optimization.py
git commit -m "feat: make claude bundle seed selective and compact"
```

### Task 5: Reduzir custo de descrições de imagem no contexto final

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `src/ui/image_curator.py`
- Test: `tests/test_image_curation.py`
- Test: `tests/test_token_optimization.py`

- [ ] **Step 1: Escrever teste de descrição enxuta**

```python
from src.builder.engine import RepoBuilder


def test_inject_image_descriptions_prefers_short_variant():
    markdown = "![](content/images/img.png)"
    curation = {
        "pages": {
            "2": {
                "include_page": True,
                "images": {
                    "img.png": {
                        "type": "diagrama",
                        "include": True,
                        "description": "Descrição completa muito longa...",
                        "short_description": "Diagrama com fluxo principal do perceptron.",
                    }
                }
            }
        }
    }
    result = RepoBuilder.inject_image_descriptions(markdown, curation)
    assert "fluxo principal do perceptron" in result
```

- [ ] **Step 2: Adicionar `short_description` ao modelo de curadoria**

No `Image Curator`, ao salvar:

```python
images_data[fname] = {
    "type": ...,
    "include": ...,
    "description": existing.get("description"),
    "short_description": existing.get("short_description") or existing.get("description"),
    "described_at": existing.get("described_at"),
}
```

- [ ] **Step 3: Usar a forma curta na injeção do markdown**

```python
desc_text = img_data.get("short_description") or img_data.get("description")
```

- [ ] **Step 4: Definir política de compressão**

Ao gerar `short_description`, usar:
- 1 a 3 frases
- sem cadeia de pensamento
- sem repetir texto óbvio do slide
- foco no que a imagem acrescenta

- [ ] **Step 5: Rodar testes**

Run: `pytest tests/test_image_curation.py tests/test_token_optimization.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py src/ui/image_curator.py tests/test_image_curation.py tests/test_token_optimization.py
git commit -m "feat: use compact image descriptions for final context"
```

### Task 6: Deduplicar repetição visual no contexto final sem apagar assets

**Files:**
- Modify: `src/ui/image_curator.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_image_curation.py`
- Test: `tests/test_token_optimization.py`

- [ ] **Step 1: Escrever teste de deduplicação de descrição entre páginas consecutivas**

```python
def test_duplicate_image_descriptions_are_not_injected_twice():
    from src.builder.engine import RepoBuilder

    markdown = "\n".join([
        "![](content/images/img-a.png)",
        "![](content/images/img-b.png)",
    ])
    curation = {
        "pages": {
            "23": {"include_page": True, "images": {"img-a.png": {"include": True, "description": "Mesmo conteúdo", "duplicate_hash": "abc"}}},
            "24": {"include_page": True, "images": {"img-b.png": {"include": True, "description": "Mesmo conteúdo", "duplicate_hash": "abc"}}},
        }
    }
    result = RepoBuilder.inject_image_descriptions(markdown, curation)
    assert result.count("Mesmo conteúdo") == 1
```

- [ ] **Step 2: Persistir metadados de duplicata exata**

No `Image Curator`, ao detectar duplicata por hash:

```python
duplicate_info[img.name] = {
    "hash": digest,
    "pages": pages,
    "other_pages": other_pages,
    "count": len(occurrences),
}
```

E ao salvar a curadoria, persistir `duplicate_hash` quando houver.

- [ ] **Step 3: Pular duplicatas exatas na injeção final**

```python
seen_duplicate_hashes = set()
...
dup_hash = img_data.get("duplicate_hash")
if dup_hash and dup_hash in seen_duplicate_hashes:
    continue
if dup_hash:
    seen_duplicate_hashes.add(dup_hash)
```

- [ ] **Step 4: Rodar testes**

Run: `pytest tests/test_image_curation.py tests/test_token_optimization.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/image_curator.py src/builder/engine.py tests/test_image_curation.py tests/test_token_optimization.py
git commit -m "feat: avoid repeated exact image descriptions in final context"
```

### Task 7: Ajustar as instruções do Claude para navegação econômica

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_token_optimization.py`

- [ ] **Step 1: Escrever teste da política de leitura econômica**

```python
def test_claude_instructions_prefer_maps_before_long_files():
    from src.builder.engine import generate_claude_project_instructions

    text = generate_claude_project_instructions(
        {"course_name": "IA"},
        None,
        None,
        "claude",
        repo_ready=True,
    )

    assert "Comece por `course/COURSE_MAP.md`" in text
    assert "Abra arquivos longos apenas quando necessário" in text
```

- [ ] **Step 2: Alterar as instruções do projeto**

Inserir explicitamente:
- começar por `COURSE_MAP.md`
- usar `FILE_MAP.md` para localizar material
- abrir markdowns longos apenas sob demanda
- priorizar `approved_markdown`/`curated_markdown`
- evitar reler bibliografia/referências inteiras sem necessidade

- [ ] **Step 3: Rodar testes**

Run: `pytest tests/test_token_optimization.py -q`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/builder/engine.py tests/test_token_optimization.py
git commit -m "feat: teach claude low-token repository navigation"
```

### Task 8: Garantir que `Reprocessar Repositório` aplica tudo aos repositórios antigos

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `src/ui/app.py`
- Test: `tests/test_token_optimization.py`

- [ ] **Step 1: Escrever teste de reprocessamento só com manifest existente**

```python
def test_incremental_build_regenerates_low_token_artifacts_without_new_entries(tmp_path):
    from src.builder.engine import RepoBuilder

    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "manifest.json").write_text('{"entries":[],"generated_at":"2026-03-31T04:00:00"}', encoding="utf-8")

    builder = RepoBuilder(repo, {"course_name": "IA"}, [], {})
    builder.incremental_build()

    assert (repo / "course" / "FILE_MAP.md").exists()
    assert (repo / "course" / "COURSE_MAP.md").exists()
    assert (repo / "build" / "claude-knowledge" / "bundle.seed.json").exists()
```

- [ ] **Step 2: Garantir que incremental_build regenera todos os artefatos derivados**

Verificar em `incremental_build()` e `_regenerate_pedagogical_files()`:
- `bundle.seed.json`
- `FILE_MAP.md`
- `COURSE_MAP.md`
- instruções LLM
- qualquer nova métrica/rota de contexto criada neste plano

- [ ] **Step 3: Atualizar o texto de confirmação do reprocessamento**

Em [app.py](C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator\src\ui\app.py):

```python
"Isso vai regenerar todos os arquivos pedagógicos e otimizações de contexto "
"(instruções, maps, bundle, compressão de contexto) com o código atual."
```

- [ ] **Step 4: Rodar testes**

Run: `pytest tests/test_token_optimization.py tests/test_core.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/ui/app.py tests/test_token_optimization.py tests/test_core.py
git commit -m "feat: make repository reprocess apply low-token architecture"
```

### Task 9: Atualizar ajuda, README e handoff

**Files:**
- Modify: `src/ui/dialogs.py`
- Modify: `README.md`
- Modify: `docs/CHATGPT_HANDOFF_PROMPT.md`

- [ ] **Step 1: Atualizar a Central de Ajuda**

Adicionar seções curtas:
- “Arquitetura de baixo consumo de tokens”
- “Como usar com Claude Web”
- “Quando usar Reprocessar Repositório”

Remover qualquer sugestão implícita de que o Claude deva começar lendo tudo.

- [ ] **Step 2: Atualizar README**

Adicionar:
- como o app reduz tokens
- papel de `FILE_MAP`, `COURSE_MAP` e `bundle.seed.json`
- reprocessamento compatível com repos antigos
- papel do `Image Curator` na redução de redundância

- [ ] **Step 3: Atualizar handoff**

Refletir:
- mapas enxutos
- bundle seletivo
- instruções de leitura econômica
- reprocessamento como mecanismo de rollout

- [ ] **Step 4: Verificação textual**

Run: `rg -n "ler tudo|todo o repositório|contexto completo|Importação rápida" README.md docs src\\ui\\dialogs.py`

Expected:
- nada incentivando leitura indiscriminada do repo
- docs alinhados com a nova arquitetura

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py README.md docs/CHATGPT_HANDOFF_PROMPT.md
git commit -m "docs: explain low-token claude web workflow"
```

### Task 10: Integração final e validação de regressão

**Files:**
- Modify: `src/builder/engine.py`
- Modify: `src/ui/app.py`
- Modify: `src/ui/dialogs.py`
- Modify: `src/ui/image_curator.py`
- Test: `tests/test_token_optimization.py`
- Test: `tests/test_core.py`
- Test: `tests/test_image_curation.py`

- [ ] **Step 1: Rodar suíte final**

Run: `pytest tests/test_token_optimization.py tests/test_core.py tests/test_image_curation.py -q`

Expected: todos PASS

- [ ] **Step 2: QA manual do fluxo de rollout**

Checklist manual:
1. Abrir um repositório já existente.
2. Clicar `Reprocessar Repositório`.
3. Validar que `FILE_MAP.md`, `COURSE_MAP.md`, `bundle.seed.json` e instruções foram regenerados.
4. Conferir que os arquivos estão mais curtos e orientados à navegação.
5. Conferir que o `Image Curator` não injeta descrições repetidas desnecessárias.
6. Conferir que o Claude Web pode começar pelos maps e pelas instruções sem abrir materiais grandes de imediato.

- [ ] **Step 3: Commit**

```bash
git add src/builder/engine.py src/ui/app.py src/ui/dialogs.py src/ui/image_curator.py tests/test_token_optimization.py tests/test_core.py tests/test_image_curation.py README.md docs/CHATGPT_HANDOFF_PROMPT.md
git commit -m "feat: ship low-token claude web repository architecture"
```

## Self-Review

### Spec coverage

- Baixo consumo de tokens: coberto nas Tasks 2, 3, 4, 5, 6 e 7.
- Evitar arquivos extras inúteis: tratado nos princípios e nas Tasks 2, 3 e 7.
- Compatibilidade com `Reprocessar Repositório`: coberto explicitamente na Task 8.
- Aplicação a repositórios já formados: coberta na Task 8 e validada na Task 10.

### Placeholder scan

- Não há `TODO`, `TBD` ou “fazer depois”.
- Cada task tem arquivos, comandos e objetivo técnico claro.
- Os helpers e comportamentos novos têm nomes concretos.

### Type consistency

- `manifest["entries"]` continua sendo a fonte principal.
- `FILE_MAP.md`, `COURSE_MAP.md`, `bundle.seed.json` e instruções continuam derivados.
- `Reprocessar Repositório` continua passando por `incremental_build()`.

## Execução Recomendada

Melhor ordem:
1. Task 1
2. Task 2
3. Task 3
4. Task 4
5. Task 7
6. Task 8
7. Task 5
8. Task 6
9. Task 9
10. Task 10

Essa ordem prioriza primeiro a arquitetura de navegação/token, depois o rollout por reprocessamento, e só então os refinamentos de imagem e documentação.
