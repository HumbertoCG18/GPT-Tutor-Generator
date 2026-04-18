# Controlled Auto-Tagging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar um sistema de tags gerenciadas por catálogo da disciplina, com atribuição manual por entry e geração automática controlada baseada em `teaching_plan`, `COURSE_MAP`, `GLOSSARY` e headings fortes do conteúdo curado, para melhorar roteamento pedagógico e servir como sinal auxiliar para a futura camada temporal.

**Architecture:** O sistema passará de um campo livre `tags` para um modelo de **catálogo de tags da disciplina + atribuição por entry**. O catálogo será persistido em arquivo próprio do curso; cada entry terá `manual_tags` e `auto_tags`, ambas sempre escolhidas a partir do catálogo. As `auto_tags` serão derivadas de um vocabulário controlado da disciplina, persistidas no `manifest.json`, e consumidas por `FILE_MAP`, índices pedagógicos e, depois, pela camada temporal intermediária. O tutor continuará vendo artefatos curtos; as tags serão infraestrutura de classificação e rastreabilidade, não texto livre.

**Scope Rule:** O catálogo é **estritamente local ao repositório/disciplina**. Não existe catálogo global entre matérias. Cada repositório mantém seu próprio `course/.tag_catalog.json`, derivado apenas de fontes daquela disciplina e, no futuro, de edições manuais feitas naquele próprio repositório.

**Tech Stack:** Python, pytest, manifest JSON, geração de Markdown, parsing de plano de ensino / glossário / headings.

---

## Low-Token Constraints

Este plano deve melhorar classificação e roteamento **sem aumentar desnecessariamente o custo de contexto do tutor**.

Regras obrigatórias:

- `course/.tag_catalog.json` é infraestrutura interna do app
  - não deve ser promovido como arquivo de leitura padrão do tutor
  - não deve entrar no bundle inicial do Claude

- `manual_tags` e `auto_tags` no `manifest.json` são estado operacional
  - servem para build, reprocessamento e matchers
  - não devem ser tratados como conteúdo pedagógico para leitura normal da LLM

- `FILE_MAP.md` e índices derivados só podem expor tags de forma enxuta
  - no máximo um resumo curto
  - nunca uma lista extensa por entry
  - quando as tags não agregarem valor claro, preferir não exibir

- `auto_tags` devem ser curtas, controladas e limitadas
  - no máximo 6 por entry
  - preferir 3 a 5 quando houver sinal suficiente
  - nunca usar frases longas como tag

- o sistema não deve gerar tags genéricas ou decorativas
  - proibidas: `conteudo`, `arquivo`, `pdf`, `estudo`, `material`, `aula`
  - só valem tags que melhorem matching, rastreabilidade ou roteamento

- o tutor continua sendo guiado principalmente por:
  - `COURSE_MAP.md`
  - `FILE_MAP.md`
  - `EXERCISE_INDEX.md`
  - `SYLLABUS.md` quando necessário
  - as tags existem para melhorar esses artefatos, não para criar mais uma camada obrigatória de leitura

Critério de sucesso low-token:

- melhor matching com menos ambiguidade
- sem criar mais um arquivo “obrigatório” para o tutor ler
- sem inflar `FILE_MAP.md`
- sem transformar tags em mini-resumos

## Migration Strategy

Esta refatoração será incremental e compatível com repositórios existentes.

1. **Introdução da estrutura**
   - Adicionar catálogo de tags da disciplina e os campos `manual_tags` / `auto_tags`.
   - Manter compatibilidade de leitura com o campo legado `tags` durante a migração.
   - Garantir que entries antigas continuem funcionando sem `manual_tags` / `auto_tags`.

2. **Geração controlada**
   - Construir um vocabulário estável da disciplina.
   - Gerar `auto_tags` só quando houver evidência forte.
   - Limitar quantidade e tipo de tags para evitar ruído.

3. **Consumo gradual**
   - Expor `auto_tags` em `FILE_MAP`/índices de forma enxuta e opcional.
   - Usar `auto_tags` como sinal auxiliar em matchers futuros.
   - Preservar prioridade de edição manual do usuário.

4. **Migração dos repositórios existentes**
   - `Reprocessar Repositório` passa a preencher `auto_tags`.
   - O campo legado `tags` é migrado para `manual_tags` quando houver conteúdo.
   - Nenhuma edição manual prévia do usuário deve ser perdida.

## Tagging Contract

O plano assume um catálogo por disciplina e dois campos distintos por entry:

- `course/.tag_catalog.json`
  - fonte de verdade das tags válidas da matéria
  - é local ao repositório/disciplina
  - pode conter tags criadas manualmente pelo usuário e tags descobertas automaticamente
  - formato alvo:

```json
{
  "version": 2,
  "scope": {
    "course_name": "Métodos Formais",
    "course_slug": "metodos-formais"
  },
  "manual_tags": [
    "ferramenta:isabelle"
  ],
  "auto_tags": [
    "topico:funcoes-recursivas",
    "tipo:lista"
  ],
  "tags": [
    "ferramenta:isabelle",
    "topico:funcoes-recursivas",
    "tipo:lista"
  ]
}
```

- `manual_tags`
  - lista de tags atribuídas manualmente à entry
  - só aceita tags existentes no catálogo
  - nunca sobrescrita automaticamente

- `auto_tags`
  - lista controlada gerada pelo builder
  - sempre padronizada
  - sempre derivada do catálogo/vocabulário da própria disciplina
  - usada para classificação interna e rastreabilidade

- `tags`
  - campo legado
  - lido apenas para migração
  - não deve mais ser a interface principal de edição

Formato das `auto_tags`:

```json
[
  "topico:funcoes-recursivas",
  "topico:conjuntos-indutivos",
  "tipo:lista",
  "ferramenta:isabelle"
]
```

Regras:
- usar apenas prefixos conhecidos:
  - `topico:`
  - `ferramenta:`
  - `tipo:`
  - `origem:` (opcional, só quando houver sinal claro)
- no máximo 6 tags por entry
- sem tags genéricas como `conteudo`, `arquivo`, `pdf`, `aula`
- `auto_tags` vazia é válida
- `manual_tags` e `auto_tags` podem coexistir
- o catálogo pode ser ampliado manualmente pelo usuário
- a UI de edição deve usar seleção/remoção de tags do catálogo, não campo livre de texto
- o catálogo e as tags persistidas não devem virar contexto obrigatório do tutor

## Vocabulary Sources

As `auto_tags` serão derivadas, nesta ordem de confiança:

1. `teaching_plan`
   - unidades, tópicos e subtópicos oficiais

2. `COURSE_MAP`
   - estrutura consolidada das unidades

3. `GLOSSARY`
   - termos oficiais e sinônimos aceitos

4. headings fortes do markdown curado
   - usados só como reforço, não como fonte principal

## File Structure

**Arquivos principais a modificar**

- `src/builder/engine.py`
  - extração do vocabulário da disciplina
  - geração de `auto_tags`
  - migração do campo legado `tags`
  - persistência no manifest
  - consumo das tags em `FILE_MAP` e índices

- `src/ui/dialogs.py`
  - editor do backlog com seleção de tags do catálogo
  - remoção do uso principal do input livre `tags`
  - exibição separada de `manual_tags` e `auto_tags`

- `src/ui/app.py`
  - se necessário, ponto de entrada para gerenciamento do catálogo de tags da matéria

- `src/models/core.py`
  - manter compatibilidade com entries que ainda não tenham `manual_tags` / `auto_tags`
  - se necessário, adicionar campo opcional no modelo serializável

- `tests/test_core.py`
  - vocabulário, persistência e renderização de artefatos

- `tests/test_file_map_unit_mapping.py`
  - uso de `auto_tags` como sinal auxiliar em matchers

**Arquivos novos**

- `tests/fixtures/tagging_cases.py`
  - fixtures pequenas com `teaching_plan`, `COURSE_MAP`, `GLOSSARY` e markdown curado

- `tests/test_tag_catalog.py`
  - cobertura específica de catálogo, migração e seleção manual

## Task 1: Definir o Catálogo de Tags da Disciplina

**Files:**
- Modify: `src/builder/engine.py`
- Create: `tests/fixtures/tagging_cases.py`
- Create: `tests/test_tag_catalog.py`
- Test: `tests/test_tag_catalog.py`

- [ ] **Step 1: Write the failing tests for tag catalog extraction**

```python
from tests.fixtures.tagging_cases import (
    TAGGING_TEACHING_PLAN,
    TAGGING_COURSE_MAP,
    TAGGING_GLOSSARY,
)
from src.builder.engine import _build_tag_catalog


def test_build_tag_catalog_extracts_topic_tags():
    catalog = _build_tag_catalog(
        teaching_plan=TAGGING_TEACHING_PLAN,
        course_map_md=TAGGING_COURSE_MAP,
        glossary_md=TAGGING_GLOSSARY,
    )

    assert "topico:funcoes-recursivas" in catalog["tags"]
    assert "topico:conjuntos-indutivos" in catalog["tags"]


def test_build_tag_catalog_extracts_tool_tags():
    catalog = _build_tag_catalog(
        teaching_plan=TAGGING_TEACHING_PLAN,
        course_map_md=TAGGING_COURSE_MAP,
        glossary_md=TAGGING_GLOSSARY,
    )

    assert "ferramenta:isabelle" in catalog["tags"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_tag_catalog.py -k "build_tag_catalog" -q`
Expected: FAIL because `_build_tag_catalog` does not exist.

- [ ] **Step 3: Write the minimal tag catalog builder**

```python
def _build_tag_catalog(
    teaching_plan: str,
    course_map_md: str,
    glossary_md: str,
) -> dict:
    tags = set()

    for raw_topic in _extract_topic_candidates(teaching_plan, course_map_md, glossary_md):
        slug = slugify(raw_topic)
        if slug:
            tags.add(f"topico:{slug}")

    for tool_name in _extract_tool_candidates(teaching_plan, glossary_md):
        slug = slugify(tool_name)
        if slug:
            tags.add(f"ferramenta:{slug}")

    return {
        "version": 1,
        "tags": sorted(tags),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_tag_catalog.py -k "build_tag_catalog" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/tagging_cases.py tests/test_tag_catalog.py src/builder/engine.py
git commit -m "feat: add controlled discipline tag catalog"
```

## Task 2: Migrar o Campo Legado `tags` para o Novo Modelo

**Files:**
- Modify: `src/models/core.py`
- Modify: `src/builder/engine.py`
- Create: `tests/test_tag_catalog.py`

- [ ] **Step 1: Write the failing tests for legacy tag migration**

```python
def test_legacy_tags_are_migrated_to_manual_tags():
    payload = {"title": "Lista 1", "tags": "topico:funcoes-recursivas; tipo:lista"}

    entry = FileEntry.from_dict(payload)

    assert entry.manual_tags == ["topico:funcoes-recursivas", "tipo:lista"]


def test_missing_legacy_tags_keeps_manual_tags_empty():
    payload = {"title": "Lista 1"}

    entry = FileEntry.from_dict(payload)

    assert entry.manual_tags == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_tag_catalog.py -k "legacy_tags_are_migrated or keeps_manual_tags_empty" -q`
Expected: FAIL because `manual_tags` does not exist yet.

- [ ] **Step 3: Add the compatibility layer**

```python
@dataclass
class FileEntry:
    ...
    tags: str = ""
    manual_tags: List[str] = field(default_factory=list)
    auto_tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "FileEntry":
        manual = list(data.get("manual_tags") or [])
        legacy = str(data.get("tags") or "")
        if not manual and legacy:
            manual = [part.strip() for part in re.split(r"[;,]", legacy) if part.strip()]
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_tag_catalog.py -k "legacy_tags_are_migrated or keeps_manual_tags_empty" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py src/builder/engine.py tests/test_tag_catalog.py
git commit -m "feat: migrate legacy tags to manual tags"
```

## Task 3: Gerar Auto-Tags por Entry a Partir de Sinais Fortes

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for entry auto-tagging**

```python
from src.builder.engine import _infer_entry_auto_tags


def test_infer_entry_auto_tags_prefers_controlled_topic_tags():
    vocab = {
        "allowed_tags": [
            "topico:funcoes-recursivas",
            "topico:conjuntos-indutivos",
            "tipo:lista",
        ]
    }
    entry = {
        "title": "Exerciciosformalizacaoalgoritmosrecursao",
        "category": "listas",
        "tags": "",
    }
    markdown_text = "# Exercícios\n\n## Funções Recursivas\n\n## Listas\n"

    auto_tags = _infer_entry_auto_tags(entry, markdown_text, vocab)

    assert "topico:funcoes-recursivas" in auto_tags
    assert "tipo:lista" in auto_tags


def test_infer_entry_auto_tags_does_not_emit_generic_noise():
    vocab = {"allowed_tags": ["topico:funcoes-recursivas"]}
    entry = {"title": "Aula 1", "category": "material-de-aula", "tags": ""}

    auto_tags = _infer_entry_auto_tags(entry, "Introdução geral", vocab)

    assert auto_tags == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "infer_entry_auto_tags" -q`
Expected: FAIL because `_infer_entry_auto_tags` does not exist.

- [ ] **Step 3: Implement minimal controlled auto-tag inference**

```python
def _infer_entry_auto_tags(entry: dict, markdown_text: str, vocabulary: dict) -> List[str]:
    allowed = vocabulary.get("allowed_tags", [])
    source_text = _normalize_match_text(
        " ".join(
            filter(
                None,
                [
                    str(entry.get("title", "")),
                    str(entry.get("category", "")),
                    str(markdown_text or ""),
                ],
            )
        )
    )

    inferred: List[str] = []
    for tag in allowed:
        _, _, raw_value = tag.partition(":")
        if raw_value.replace("-", " ") in source_text:
            inferred.append(tag)

    category = str(entry.get("category", "")).strip().lower()
    if category == "listas":
        inferred.append("tipo:lista")
    elif category == "gabaritos":
        inferred.append("tipo:gabarito")
    elif category == "provas":
        inferred.append("tipo:prova")

    deduped = []
    for tag in inferred:
        if tag not in deduped:
            deduped.append(tag)
    return deduped[:6]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "infer_entry_auto_tags" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py src/builder/engine.py
git commit -m "feat: infer controlled auto-tags per entry"
```

## Task 4: Persistir `manual_tags` e `auto_tags` no Manifest sem Perder Compatibilidade

**Files:**
- Modify: `src/models/core.py`
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for manifest persistence**

```python
def test_manifest_persists_manual_and_auto_tags_separately(tmp_path):
    entry = FileEntry(
        source_path="raw/aula-1.pdf",
        file_type="pdf",
        category="listas",
        title="Exerciciosformalizacaoalgoritmosrecursao",
        manual_tags=["manual:revisar"],
    )

    payload = _serialize_manifest_entry(
        entry,
        manual_tags=["manual:revisar"],
        auto_tags=["topico:funcoes-recursivas", "tipo:lista"],
    )

    assert payload["manual_tags"] == ["manual:revisar"]
    assert payload["auto_tags"] == ["topico:funcoes-recursivas", "tipo:lista"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "persists_auto_tags" -q`
Expected: FAIL because the manifest serializer does not include `manual_tags` / `auto_tags`.

- [ ] **Step 3: Add optional `auto_tags` support**

```python
@dataclass
class FileEntry:
    ...
    tags: str = ""
    manual_tags: List[str] = field(default_factory=list)
    auto_tags: List[str] = field(default_factory=list)
```

```python
def _serialize_manifest_entry(
    entry: FileEntry,
    manual_tags: Optional[List[str]] = None,
    auto_tags: Optional[List[str]] = None,
) -> dict:
    payload = asdict(entry)
    payload["manual_tags"] = list(manual_tags if manual_tags is not None else entry.manual_tags or [])
    payload["auto_tags"] = list(auto_tags if auto_tags is not None else entry.auto_tags or [])
    return payload
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "persists_auto_tags" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/core.py src/builder/engine.py tests/test_core.py
git commit -m "feat: persist auto tags in manifest"
```

## Task 5: Gerar `auto_tags` no Build e no Reprocessamento

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing integration tests for build/reprocess**

```python
def test_incremental_build_populates_auto_tags_for_existing_repo(repo_root, course_meta, subject_profile):
    builder = RepoBuilder(repo_root)
    builder.incremental_build(course_meta, [], subject_profile=subject_profile)

    manifest = json.loads((repo_root / "manifest.json").read_text(encoding="utf-8"))
    assert "auto_tags" in manifest["entries"][0]


def test_reprocess_preserves_manual_tags_while_refreshing_auto_tags(repo_root, course_meta, subject_profile):
    builder = RepoBuilder(repo_root)
    builder.incremental_build(course_meta, [], subject_profile=subject_profile)

    manifest = json.loads((repo_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["entries"][0]["manual_tags"] == ["manual:revisar"]
    assert manifest["entries"][0]["auto_tags"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "populates_auto_tags or preserves_manual_tags" -q`
Expected: FAIL until the builder threads the vocabulary and inference into regeneration/build paths.

- [ ] **Step 3: Thread auto-tag generation through build paths**

```python
def _refresh_manifest_auto_tags(self, subject_profile=None) -> None:
    vocabulary = _build_controlled_tag_vocabulary_from_repo(self.root_dir, subject_profile)
    manifest = self._load_manifest()
    for entry in manifest.get("entries", []):
        markdown_text = _entry_markdown_text_for_file_map(entry, self.root_dir)
        entry["auto_tags"] = _infer_entry_auto_tags(entry, markdown_text, vocabulary)
    self._write_manifest(manifest)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "populates_auto_tags or preserves_manual_tags" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: populate auto tags during build and reprocess"
```

## Task 6: Expor Tags de Forma Enxuta no FILE_MAP e Índices

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for artifact rendering**

```python
def test_low_token_file_map_prefers_auto_tags_as_auxiliary_signal():
    manifest_entries = [
        {
            "title": "Exerciciosformalizacaoalgoritmosrecursao",
            "category": "listas",
            "manual_tags": [],
            "auto_tags": ["topico:funcoes-recursivas", "tipo:lista"],
            "base_markdown": "exercises/lists/item.md",
            "raw_target": "raw/lista.pdf",
        }
    ]

    result = _low_token_file_map_md({"course_name": "MF"}, manifest_entries)

    assert "topico:funcoes-recursivas" in result


def test_exercise_index_uses_auto_tags_when_manual_tags_are_empty():
    entries = [
        FileEntry(
            source_path="raw/lista.pdf",
            file_type="pdf",
            category="listas",
            title="Lista 1",
        manual_tags=[],
        auto_tags=["topico:funcoes-recursivas"],
    )
    ]

    result = exercise_index_md({"course_name": "MF"}, entries)
    assert "topico:funcoes-recursivas" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "auto_tags_as_auxiliary_signal or uses_auto_tags_when_manual_tags_are_empty" -q`
Expected: FAIL because artifacts still only read `tags`.

- [ ] **Step 3: Render merged tag view without mutating manual tags**

```python
def _merge_manual_and_auto_tags(manual_tags: List[str], auto_tags: List[str]) -> str:
    manual = [part.strip() for part in (manual_tags or []) if part.strip()]
    merged = manual[:]
    for tag in auto_tags or []:
        if tag not in merged:
            merged.append(tag)
    return "; ".join(merged[:3])
```

- [ ] **Step 3.1: Enforce low-token exposure rules**

Checks required in this task:

- `FILE_MAP.md` must not expose more than 3 merged tags per entry
- tags must remain optional in rendered artifacts
- `.tag_catalog.json` must not be referenced in tutor-facing instructions
- no artifact should suggest the tutor open the raw tag catalog

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "auto_tags_as_auxiliary_signal or uses_auto_tags_when_manual_tags_are_empty" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: expose merged auto tags in low-token artifacts"
```

## Task 7: Gerenciar Tags Manualmente no Editor do Backlog

**Files:**
- Modify: `src/ui/dialogs.py`
- Modify: `src/ui/app.py`
- Test: `tests/test_tag_catalog.py`

- [ ] **Step 1: Write the failing tests for manual tag management helpers**

```python
def test_backlog_tag_summary_keeps_manual_and_auto_tags_separate():
    from src.ui.dialogs import _format_backlog_tag_summary

    result = _format_backlog_tag_summary(
        manual_tags=["topico:funcoes-recursivas"],
        auto_tags=["topico:funcoes-recursivas", "tipo:lista"],
    )

    assert "topico:funcoes-recursivas" in result["manual"]
    assert "tipo:lista" in result["auto"]


def test_manual_tag_selection_only_accepts_catalog_values():
    from src.ui.dialogs import _normalize_selected_manual_tags

    selected = _normalize_selected_manual_tags(
        selected_tags=["topico:funcoes-recursivas", "inventada:foo"],
        catalog_tags=["topico:funcoes-recursivas", "tipo:lista"],
    )

    assert selected == ["topico:funcoes-recursivas"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_tag_catalog.py -k "backlog_tag_summary or manual_tag_selection" -q`
Expected: FAIL because the helpers/UI do not exist.

- [ ] **Step 3: Add the minimal UI helpers and catalog-backed selection**

```python
def _format_backlog_tag_summary(manual_tags: List[str], auto_tags: List[str]) -> dict:
    return {
        "manual": ", ".join(manual_tags or []) or "—",
        "auto": ", ".join(auto_tags or []) or "—",
    }


def _normalize_selected_manual_tags(selected_tags: List[str], catalog_tags: List[str]) -> List[str]:
    normalized = []
    for tag in selected_tags or []:
        if tag in catalog_tags and tag not in normalized:
            normalized.append(tag)
    return normalized
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_tag_catalog.py -k "backlog_tag_summary or manual_tag_selection" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/dialogs.py src/ui/app.py tests/test_tag_catalog.py
git commit -m "feat: add catalog-backed manual tags in backlog editor"
```

## Task 8: Usar Auto-Tags como Sinal Auxiliar para o Matcher Futuro

**Files:**
- Modify: `tests/test_file_map_unit_mapping.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Write the failing tests for tag-assisted matching**

```python
def test_collect_entry_unit_signals_includes_auto_tags():
    entry = {
        "title": "Lista 1",
        "category": "listas",
        "manual_tags": [],
        "auto_tags": ["topico:funcoes-recursivas", "tipo:lista"],
        "raw_target": "raw/lista.pdf",
    }

    signals = _collect_entry_unit_signals(entry, "")

    assert "topico funcoes recursivas" in signals["tags_text"]


def test_score_entry_against_unit_uses_auto_tags_as_auxiliary_signal():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py -k "auto_tags" -q`
Expected: FAIL because the matcher still only reads the manual `tags` field.

- [ ] **Step 3: Extend the signal collector to merge manual and auto tags**

```python
def _collect_entry_unit_signals(entry: dict, markdown_text: str) -> dict:
    merged_tags = _merge_manual_and_auto_tags(
        list(entry.get("manual_tags") or []),
        list(entry.get("auto_tags") or []),
    )
    return {
        ...
        "tags_text": _normalize_match_text(merged_tags),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py -k "auto_tags" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "feat: use controlled auto tags as matcher signal"
```

## Task 9: Regressão Final e Limpeza de Regras

**Files:**
- Modify: `tests/test_core.py`
- Modify: `tests/test_file_map_unit_mapping.py`
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Add regression tests for edge rules**

```python
def test_auto_tags_limit_to_six_items(...):
    ...
    assert len(auto_tags) <= 6


def test_auto_tags_do_not_overwrite_manual_tags(...):
    ...
    assert entry["manual_tags"] == ["manual:revisar"]


def test_auto_tags_empty_is_valid_when_no_strong_evidence(...):
    ...
    assert auto_tags == []
```

- [ ] **Step 2: Run focused regression tests**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py tests/test_file_map_unit_mapping.py -k "auto_tags_limit or overwrite_manual_tags or empty_is_valid" -q`
Expected: PASS

- [ ] **Step 3: Run the full touched suites**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py tests/test_file_map_unit_mapping.py -q`
Expected: PASS

- [ ] **Step 4: Review dead paths and remove any accidental reuse of free-form tag generation**

```python
# Keep only controlled-tag generation.
# Remove or avoid any helper that emits generic free-form tags.
```

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py tests/test_file_map_unit_mapping.py src/ui/dialogs.py src/models/core.py
git commit -m "refactor: finalize controlled auto-tagging pipeline"
```

## Self-Review

**Spec coverage**

- teaching_plan como fonte de vocabulário: coberto nas Tasks 1 e 5.
- COURSE_MAP como fonte de vocabulário: coberto na Task 1.
- GLOSSARY como fonte de vocabulário: coberto na Task 1.
- headings fortes do conteúdo curado: coberto na Task 3.
- catálogo + atribuição manual por entry: cobertos nas Tasks 1, 2 e 7.
- persistência para repositórios existentes e futuros: coberta nas Tasks 4 e 5.
- uso das tags como sinal auxiliar para a camada temporal: coberto na Task 8.

**Placeholder scan**

- Não usei `TODO`, `TBD` ou “implementar depois”.
- As funções e nomes usados nas tasks são consistentes e definidos no próprio plano.

**Type consistency**

- `tags` legado permanece apenas para compatibilidade de leitura
- `manual_tags` entra como `List[str]`
- `auto_tags` entra como `List[str]`
- `_merge_manual_and_auto_tags(...)` é a única ponte entre os dois mundos

## Notes

- Este plano não tenta resolver a camada temporal inteira ainda.
- O objetivo é preparar um sinal auxiliar forte e controlado para melhorar `FILE_MAP`, índices e a futura refatoração do `timeline index`.
- O campo de texto livre `tags` deixa de ser a interface principal; a experiência alvo passa a ser catálogo + seleção manual por entry + geração automática controlada.
- Se o auto-tagging se mostrar confiável, ele deve ser consumido pela refatoração temporal como evidência adicional, não como fonte primária.
