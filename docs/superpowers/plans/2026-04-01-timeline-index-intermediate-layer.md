# Timeline Index Intermediate Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduzir uma camada temporal intermediária interna baseada no cronograma importado para conectar arquivos do `FILE_MAP.md` a blocos temporais prováveis com alta precisão, de forma compatível com repositórios existentes e futuros.

**Architecture:** O cronograma bruto continuará vindo de `SubjectProfile.syllabus` e sendo publicado em `course/SYLLABUS.md`, mas o builder deixará de inferir tempo diretamente no `FILE_MAP`. Em vez disso, ele gerará um índice temporal estruturado interno por blocos (`timeline index`) e reutilizará esse índice para preencher `COURSE_MAP.md` e `FILE_MAP.md`. O índice será persistido em `course/.timeline_index.json` como infraestrutura interna do app, mas não será promovido nas instruções do tutor, preservando a arquitetura low-token.

O matching temporal deverá consumir também os sinais controlados já disponíveis no sistema:
- `manual_tags`
- `auto_tags`
- título/categoria da entry
- headings fortes do markdown

Esses sinais são auxiliares. A fonte temporal continua sendo exclusivamente o cronograma importado.

**Tech Stack:** Python, dataclasses/typed dicts já existentes no builder, pytest, markdown/text parsing, geração de artefatos Markdown/JSON.

---

## Migration Strategy

Esta refatoração **não** será um big-bang rewrite do `FILE_MAP`.

O plano assume explicitamente três fases:

1. **Coexistência controlada**
   - Introduzir o `timeline index` sem apagar imediatamente as heurísticas temporais antigas.
   - Colocar o novo fluxo atrás dos mesmos pontos de entrada de build/reprocessamento.
   - Garantir que testes existentes continuem cobrindo regressões enquanto o caminho novo ganha cobertura.

2. **Cutover**
   - Mover `FILE_MAP.md` e `COURSE_MAP.md` para consumirem o `timeline index` como fonte principal do vínculo temporal.
   - Deixar o caminho antigo apenas como fallback transitório, restrito e mensurável.
   - Validar em repositórios existentes reais antes de considerar a migração concluída.

3. **Remoção do legado**
   - Só remover as heurísticas temporais antigas depois que:
     - os testes do novo fluxo estiverem verdes
     - `Reprocessar Repositório` regenerar corretamente os artefatos
     - os casos reais críticos estiverem estáveis
   - A remoção do legado é um objetivo explícito da etapa final, não uma atividade ad-hoc no meio da implementação.

O estado final esperado é:
- `FILE_MAP.md` sem depender da gambiarra temporal atual
- `COURSE_MAP.md` e `FILE_MAP.md` consumindo a mesma camada intermediária
- heurísticas antigas removidas ou reduzidas a utilitários genéricos ainda úteis
- `Reprocessar Repositório` servindo como mecanismo oficial de migração dos repositórios existentes

## Structural Regeneration Contract

O `timeline index` e os artefatos estruturais relacionados **não podem ficar presos ao processamento de arquivos novos**.

Regra obrigatória:
- tudo que for infraestrutura estrutural do repositório deve ser recalculado dentro de `_regenerate_pedagogical_files(...)`
- isso inclui, no mínimo:
  - `course/.timeline_index.json`
  - `course/COURSE_MAP.md`
  - `course/FILE_MAP.md`
  - `course/.tag_catalog.json`
  - `auto_tags` recalculadas no `manifest.json`

Consequência prática:
- `build()` deve processar arquivos e depois chamar `_regenerate_pedagogical_files(...)`
- `incremental_build()` deve processar apenas os arquivos novos, mas também chamar `_regenerate_pedagogical_files(...)` no final
- `process_single()` deve continuar disparando a regeneração estrutural depois da entry processada
- `Reprocessar Repositório` deve conseguir recalcular toda a camada estrutural mesmo sem rodar novamente os backends pesados

Objetivo:
- repositório novo funciona
- repositório existente com arquivos novos funciona
- repositório existente sem arquivos novos também consegue atualizar a arquitetura estrutural

Isso evita que o `timeline index` ou seus consumidores dependam acidentalmente do caminho “processar novos arquivos”.

## Timeline Index Contract

O plano passa a assumir um contrato explícito e estável para `course/.timeline_index.json`.

Estrutura mínima por bloco:

```json
{
  "version": 1,
  "blocks": [
    {
      "id": "bloco-02",
      "period_start": "2026-03-11",
      "period_end": "2026-03-25",
      "period_label": "11/03/2026 a 25/03/2026",
      "unit_slug": "unidade-01-metodos-formais",
      "unit_confidence": 0.87,
      "topic_text": "definicoes indutivas funcoes recursivas listas arvores exercicios",
      "topics": [
        "definicoes indutivas",
        "funcoes recursivas",
        "listas",
        "arvores"
      ],
      "aliases": [
        "recursao",
        "inducao"
      ],
      "source_rows": [3, 4, 5, 6]
    }
  ]
}
```

Regras:
- `version` é obrigatório.
- `blocks` é obrigatório, mesmo que vazio.
- `unit_slug` pode ser vazio quando o bloco ainda não tiver evidência suficiente.
- `unit_confidence` deve ser um `float` entre `0.0` e `1.0`.
- `topic_text` é texto normalizado para matching, não para exibição humana.
- `source_rows` sempre aponta para as linhas do cronograma original já parseado.
- O tamanho do bloco é **variável**.
- Um bloco não representa “uma semana” nem “uma unidade inteira”; ele representa uma **janela pedagógica coerente**.
- O bloco continua aberto enquanto houver **continuidade temática**.
- Linhas que aprofundam o mesmo núcleo conceitual devem permanecer no mesmo bloco, mesmo quando mudam o subtítulo. Exemplo:
  - `Provas por indução`
  - `Provas por indução: listas e árvores`
  pertencem ao mesmo bloco.
- Um novo bloco só deve ser aberto quando surgir um **novo núcleo de tópico**. Exemplo:
  - `Provas por indução`
  - `Prova interativa de teoremas - Isabelle`
  devem cair em blocos diferentes.
- Linhas genéricas como `Exercícios`, `Revisão` e `Atividade assíncrona` não abrem bloco sozinhas; elas herdam o bloco dominante ao redor.

## Fallback Policy

Quando o cronograma importado for ausente, ilegível ou insuficiente:

- `course/.timeline_index.json` ainda será gerado, mas com `blocks: []`
- `COURSE_MAP.md` continua sendo gerado sem timeline detalhada
- `FILE_MAP.md` continua preenchendo `Unidade` quando possível
- `FILE_MAP.md` deixa `Período` vazio
- o tutor **não** deve ser instruído a “inventar” tempo a partir de outros artefatos

Isso evita loop de heurística em disciplinas com cronograma ruim.

## File Structure

**Arquivos principais a modificar**

- `src/builder/engine.py`
  Responsável pelo parse do cronograma, geração de `SYLLABUS.md`, `COURSE_MAP.md`, `FILE_MAP.md`, e instruções. Esta refatoração deve concentrar aqui a nova camada intermediária temporal.

- `src/utils/helpers.py`
  Utilitários de normalização e slug. Pode precisar de helper temporal/normalização leve, mas só se evitar aumentar a complexidade de `engine.py`.

- `tests/test_core.py`
  Casos de parse do cronograma, timeline por unidade, artefatos gerados e regressões do builder.

- `tests/test_file_map_unit_mapping.py`
  Casos específicos de mapeamento `arquivo -> unidade -> bloco temporal`.

**Arquivos novos**

- `tests/fixtures/syllabus_timeline_cases.py`
  Fixtures pequenas e reutilizáveis com cronogramas reais/sintéticos em português para evitar duplicação de strings longas nos testes.

**Artefato novo**

- `course/.timeline_index.json`
  Índice temporal interno obrigatório, gerado pelo builder, consumido pelo app e ignorado pelo tutor nas instruções.

## Design Decisions

- O cronograma importado continua sendo a única fonte temporal.
- `COURSE_MAP.md` continua sendo a visão pedagógica curta.
- `FILE_MAP.md` continua sendo rastreabilidade curta.
- A nova camada intermediária (`timeline index`) organiza blocos temporais com:
  - período
  - unidade
  - tópicos centrais
  - aliases/tokens úteis
  - linhas de origem do cronograma
- O tutor **não** deve ser instruído a ler o índice temporal diretamente.
- O `FILE_MAP.md` só exibirá `Período` quando houver confiança temporal suficiente.
- O matching `arquivo -> bloco` deve usar os sinais controlados já disponíveis:
  - `manual_tags`
  - `auto_tags`
  - categoria
  - título
  - headings/trechos fortes do markdown
- O sistema pode calcular múltiplos blocos candidatos internamente, mas o `FILE_MAP.md` exibirá no máximo **um** `Período` principal.
- Se os dois melhores candidatos ficarem próximos demais, o `FILE_MAP.md` deixará `Período` vazio.
- Se um bloco do índice estiver sem `unit_slug`, ele ainda poderá participar do matching temporal como candidato auxiliar quando a entry já tiver unidade provável forte. Isso evita perder blocos bons só porque a atribuição `bloco -> unidade` foi conservadora demais.
- O `timeline index` deve ser regenerado tanto em `Criar Repositório` quanto em `Reprocessar Repositório`.
- O caminho estrutural não pode depender da existência de arquivos novos para ser executado.
- A solução precisa funcionar em build novo e em `Reprocessar Repositório`.
- O `timeline index` é persistido sempre, mesmo quando vier vazio.
- O contrato do índice deve ser único e estável para evitar drift entre `COURSE_MAP` e `FILE_MAP`.

## Task 1: Extrair um Modelo Estruturado de Bloco Temporal

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`
- Create: `tests/fixtures/syllabus_timeline_cases.py`

- [ ] **Step 1: Write the failing tests for timeline block extraction**

```python
from tests.fixtures.syllabus_timeline_cases import METODOS_FORMAIS_SYLLABUS
from src.builder.engine import (
    _parse_syllabus_timeline,
    _build_timeline_candidate_rows,
    _build_timeline_index,
)


def test_build_timeline_index_groups_related_rows_into_block():
    timeline = _parse_syllabus_timeline(METODOS_FORMAIS_SYLLABUS)
    candidate_rows = _build_timeline_candidate_rows(timeline)

    index = _build_timeline_index(candidate_rows, unit_index=[])

    assert any(
        block["period_label"] == "11/03/2026 a 25/03/2026"
        for block in index["blocks"]
    )


def test_build_timeline_index_keeps_source_rows_for_debug():
    timeline = _parse_syllabus_timeline(METODOS_FORMAIS_SYLLABUS)
    candidate_rows = _build_timeline_candidate_rows(timeline)

    index = _build_timeline_index(candidate_rows, unit_index=[])

    block = next(block for block in index["blocks"] if block["source_rows"])
    assert isinstance(block["source_rows"][0], int)


def test_build_timeline_index_keeps_thematic_continuation_in_same_block():
    timeline = _parse_syllabus_timeline("""\
| Data | Conteúdo |
|---|---|
| 30/03/2026 | Provas por indução |
| 01/04/2026 | Provas por indução: listas e árvores |
| 06/04/2026 | Prova interativa de teoremas - Isabelle |
| 08/04/2026 | Prova interativa de teoremas - Isabelle |
""")
    candidate_rows = _build_timeline_candidate_rows(timeline)

    index = _build_timeline_index(candidate_rows, unit_index=[])

    assert any(block["period_label"] == "30/03/2026 a 01/04/2026" for block in index["blocks"])
    assert any(block["period_label"] == "06/04/2026 a 08/04/2026" for block in index["blocks"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "timeline_index" -q`
Expected: FAIL with `_build_timeline_index` not defined or wrong structure.

- [ ] **Step 3: Add the minimal timeline index builder**

```python
def _build_timeline_index(candidate_rows: List[Dict[str, object]], unit_index: list) -> dict:
    blocks: List[Dict[str, object]] = []
    current: Optional[Dict[str, object]] = None

    for row in candidate_rows:
        content = str(row.get("content", "")).strip()
        if not content:
            continue

        if current is None:
            current = {
                "id": f"bloco-{len(blocks) + 1:02d}",
                "period_start": "",
                "period_end": "",
                "period_label": row.get("date_text", ""),
                "unit_slug": "",
                "unit_confidence": 0.0,
                "topic_text": "",
                "topics": [],
                "aliases": [],
                "source_rows": [row.get("index", 0)],
                "rows": [row],
            }
            continue

        if _rows_belong_to_same_thematic_block(current["rows"][-1], row):
            current["period_end"] = row.get("date_text", current["period_end"])
            current["source_rows"].append(row.get("index", 0))
            current["rows"].append(row)
            continue

        blocks.append(current)
        current = {
            "id": f"bloco-{len(blocks) + 1:02d}",
            "period_start": "",
            "period_end": "",
            "period_label": row.get("date_text", ""),
            "unit_slug": "",
            "unit_confidence": 0.0,
            "topic_text": "",
            "topics": [],
            "aliases": [],
            "source_rows": [row.get("index", 0)],
            "rows": [row],
        }

    if current is not None:
        blocks.append(current)

    return {"version": 1, "blocks": blocks}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "timeline_index" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/syllabus_timeline_cases.py tests/test_core.py src/builder/engine.py
git commit -m "feat: add structured timeline index builder"
```

## Task 2: Associar Blocos Temporais às Unidades sem Hardcode

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for block-to-unit assignment**

```python
from tests.fixtures.syllabus_timeline_cases import METODOS_FORMAIS_SYLLABUS, METODOS_FORMAIS_UNITS
from src.builder.engine import (
    _parse_syllabus_timeline,
    _build_timeline_candidate_rows,
    _build_file_map_unit_index,
    _build_timeline_index,
)


def test_build_timeline_index_assigns_block_to_matching_unit():
    timeline = _parse_syllabus_timeline(METODOS_FORMAIS_SYLLABUS)
    candidate_rows = _build_timeline_candidate_rows(timeline)
    unit_index = _build_file_map_unit_index(METODOS_FORMAIS_UNITS)

    index = _build_timeline_index(candidate_rows, unit_index=unit_index)

    block = next(block for block in index["blocks"] if "recurs" in block["topic_text"])
    assert block["unit_slug"] == "unidade-01-metodos-formais"


def test_build_timeline_index_normalizes_portuguese_accents():
    timeline = _parse_syllabus_timeline(METODOS_FORMAIS_SYLLABUS)
    candidate_rows = _build_timeline_candidate_rows(timeline)
    unit_index = _build_file_map_unit_index(METODOS_FORMAIS_UNITS)

    index = _build_timeline_index(candidate_rows, unit_index=unit_index)

    assert any(block["unit_slug"] == "unidade-02-verificacao-de-programas" for block in index["blocks"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "assigns_block_to_matching_unit or normalizes_portuguese_accents" -q`
Expected: FAIL with missing `unit_slug` or wrong unit assignment.

- [ ] **Step 3: Implement modular block scoring against unit signals**

```python
def _assign_timeline_block_to_unit(block: Dict[str, object], unit_index: list) -> Optional[dict]:
    topic_text = _normalize_text(" ".join(str(row.get("content", "")) for row in block.get("rows", [])))
    scored = []
    for unit in unit_index:
        score = _score_timeline_row_against_unit(topic_text, unit)
        if score > 0:
            scored.append((unit, score))

    if not scored:
        return None

    scored.sort(key=lambda item: item[1], reverse=True)
    best, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    if best_score <= second_score + 0.15:
        return None
    return best
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "assigns_block_to_matching_unit or normalizes_portuguese_accents" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py src/builder/engine.py
git commit -m "feat: match timeline blocks to units"
```

## Task 3: Reescrever o Contexto Temporal do FILE_MAP para Usar o Índice

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Write the failing tests for file-to-block temporal mapping**

```python
from src.builder.engine import (
    _build_file_map_timeline_context_from_course,
    _infer_file_map_unit_and_period,
)


def test_infer_file_map_period_uses_timeline_block_not_macro_unit_period(course_meta, subject_profile, manifest_entry):
    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    result = _infer_file_map_unit_and_period(manifest_entry, course_meta, subject_profile, context=context)

    assert result["unit_slug"] == "unidade-01-metodos-formais"
    assert result["period_label"] == "11/03/2026 a 25/03/2026"


def test_infer_file_map_period_stays_empty_when_block_match_is_ambiguous(course_meta, subject_profile, ambiguous_entry):
    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    result = _infer_file_map_unit_and_period(ambiguous_entry, course_meta, subject_profile, context=context)

    assert result["period_label"] == ""


def test_infer_file_map_period_uses_controlled_tags_as_auxiliary_signal(course_meta, subject_profile, tagged_entry):
    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    result = _infer_file_map_unit_and_period(tagged_entry, course_meta, subject_profile, context=context)

    assert result["unit_slug"] == "unidade-01-metodos-formais"
    assert result["period_label"] == "11/03/2026 a 25/03/2026"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py -k "timeline_block or ambiguous" -q`
Expected: FAIL because the context still uses the old unit-period shortcut.

- [ ] **Step 3: Refactor FILE_MAP temporal context to consume timeline blocks**

```python
def _build_file_map_timeline_context_from_course(course_meta: dict, subject_profile=None) -> dict:
    timeline = _parse_syllabus_timeline(_resolve_course_syllabus(course_meta, subject_profile))
    unit_index = _build_file_map_unit_index_from_course(course_meta, subject_profile)
    candidate_rows = _build_timeline_candidate_rows(timeline)
    timeline_index = _build_timeline_index(candidate_rows, unit_index=unit_index)

    blocks_by_unit: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for block in timeline_index["blocks"]:
        slug = block.get("unit_slug")
        if slug:
            blocks_by_unit[slug].append(block)

    return {
        "timeline_index": timeline_index,
        "blocks_by_unit": dict(blocks_by_unit),
    }
```

Observações obrigatórias da implementação:
- `_infer_file_map_unit_and_period(...)` deve incorporar `manual_tags` e `auto_tags` como sinal auxiliar do score temporal.
- O matching pode manter 2 ou 3 candidatos internamente para desempate e debug.
- O retorno final para artefatos deve escolher apenas um `period_label`, ou vazio quando ambíguo.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py -k "timeline_block or ambiguous" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_file_map_unit_mapping.py src/builder/engine.py
git commit -m "refactor: drive file map periods from timeline index"
```

## Task 4: Tornar o COURSE_MAP Consumidor do Mesmo Índice Temporal

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for shared timeline index usage**

```python
from src.builder.engine import course_map_md


def test_course_map_uses_same_periods_as_timeline_index(course_meta, subject_profile):
    result = course_map_md(course_meta, subject_profile)

    assert "| Unidade 01  Métodos Formais | 04/03/2026 a 25/03/2026 |" in result
    assert "| Unidade 03  Verificação de Modelos | 15/06/2026 a 24/06/2026 |" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "same_periods_as_timeline_index" -q`
Expected: FAIL because `COURSE_MAP` still computes timeline on a separate path.

- [ ] **Step 3: Route course map timeline generation through the shared timeline index**

```python
def _build_course_timeline_mapping(course_meta: dict, subject_profile=None) -> List[dict]:
    context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    blocks = context.get("timeline_index", {}).get("blocks", [])
    by_unit = defaultdict(list)
    for block in blocks:
        if block.get("unit_slug"):
            by_unit[block["unit_slug"]].append(block)
    return _aggregate_unit_periods_from_blocks(by_unit)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "same_periods_as_timeline_index" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py src/builder/engine.py
git commit -m "refactor: unify course map timeline with shared timeline index"
```

## Task 5: Persistir o Índice Temporal como Infraestrutura Interna Obrigatória

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for internal timeline index persistence**

```python
def test_reprocess_writes_internal_timeline_index(repo_builder, repo_root, course_meta, subject_profile):
    repo_builder._regenerate_pedagogical_files(course_meta, subject_profile)

    timeline_index_path = repo_root / "course" / ".timeline_index.json"
    assert timeline_index_path.exists()


def test_timeline_index_is_not_referenced_in_claude_instructions(course_meta, subject_profile):
    instructions = generate_claude_project_instructions(course_meta, subject_profile)
    assert ".timeline_index.json" not in instructions


def test_empty_timeline_index_is_still_persisted_when_syllabus_is_missing(repo_builder, repo_root, course_meta):
    repo_builder._regenerate_pedagogical_files(course_meta, None)

    payload = json.loads((repo_root / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["blocks"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "timeline_index_path or not_referenced_in_claude_instructions" -q`
Expected: FAIL because the file is not written yet or because the empty-case contract is missing.

- [ ] **Step 3: Write the minimal persistence layer**

```python
def _write_internal_timeline_index(root_dir: Path, timeline_index: dict) -> None:
    write_text(
        root_dir / "course" / ".timeline_index.json",
        json.dumps(timeline_index, ensure_ascii=False, indent=2),
        label="course/.timeline_index.json",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "timeline_index_path or not_referenced_in_claude_instructions" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py src/builder/engine.py
git commit -m "feat: persist internal timeline index for debug and reuse"
```

## Task 6: Fazer o Cutover das Instruções do Tutor

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing tests for low-token instructions**

```python
def test_claude_instructions_keep_map_first_without_promoting_timeline_index(course_meta, subject_profile):
    instructions = generate_claude_project_instructions(course_meta, subject_profile)

    assert "course/COURSE_MAP.md" in instructions
    assert "course/FILE_MAP.md" in instructions
    assert "course/SYLLABUS.md" in instructions
    assert ".timeline_index.json" not in instructions
    assert "preencha a coluna **Unidade** dos itens vazios" not in instructions
    assert "o FILE_MAP já nasce preenchido pelo build" in instructions
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "without_promoting_timeline_index" -q`
Expected: FAIL if the instructions still mandarem o tutor recalcular manualmente o FILE_MAP ou se o novo arquivo interno vazar.

- [ ] **Step 3: Update instructions to describe the new cutover, not the internal file**

```python
lines.extend([
    "- `course/COURSE_MAP.md` mostra ordem e foco por unidade.",
    "- `course/FILE_MAP.md` conecta arquivos a unidades e períodos prováveis.",
    "- `course/SYLLABUS.md` continua sendo a fonte de datas e cronograma.",
    "- O `FILE_MAP.md` já é preenchido automaticamente pelo build; revise só casos marcados como ambíguos ou a revisar.",
])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "without_promoting_timeline_index" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py src/builder/engine.py
git commit -m "docs: align project instructions with internal timeline index"
```

## Task 7: Validar Reprocessamento em Repositórios Existentes

**Files:**
- Modify: `tests/test_core.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing integration test for reprocess**

```python
def test_incremental_build_regenerates_file_map_with_timeline_index(repo_root, course_meta, subject_profile):
    builder = RepoBuilder(repo_root)
    builder.incremental_build(course_meta, [], subject_profile=subject_profile)

    file_map = (repo_root / "course" / "FILE_MAP.md").read_text(encoding="utf-8")
    assert "Período" in file_map
    assert "A revisar" in file_map or "`content/" in file_map

    timeline_index = json.loads((repo_root / "course" / ".timeline_index.json").read_text(encoding="utf-8"))
    assert timeline_index["version"] == 1
    assert timeline_index["blocks"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "incremental_build_regenerates_file_map_with_timeline_index" -q`
Expected: FAIL until all regeneration hooks write the shared timeline index.

- [ ] **Step 3: Thread the shared index through build and reprocess paths**

```python
def _regenerate_pedagogical_files(...):
    timeline_context = _build_file_map_timeline_context_from_course(course_meta, subject_profile)
    _write_internal_timeline_index(self.root_dir, timeline_context["timeline_index"])
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv\Scripts\python -m pytest tests/test_core.py -k "incremental_build_regenerates_file_map_with_timeline_index" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py src/builder/engine.py
git commit -m "test: cover timeline index regeneration for existing repos"
```

## Task 8: Regressão Final e Auditoria de Resíduos

**Files:**
- Modify: `tests/test_core.py`
- Modify: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Add regression cases for the currently problematic examples**

```python
def test_metodos_formais_recursion_material_maps_to_expected_block(...):
    ...
    assert result["period_label"] == "11/03/2026 a 25/03/2026"


def test_ambiguous_specification_exercise_keeps_period_empty_until_evidence_is_strong(...):
    ...
    assert result["period_label"] == ""
```

- [ ] **Step 2: Run focused regression tests**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py tests/test_core.py -k "metodos_formais or ambiguous_specification" -q`
Expected: PASS

- [ ] **Step 3: Run the full suites touched by the refactor**

Run: `.\.venv\Scripts\python -m pytest tests/test_file_map_unit_mapping.py tests/test_core.py -q`
Expected: PASS

- [ ] **Step 4: Review for dead code and remove obsolete direct timeline wiring**

```python
# Remove or inline old branches that compute FILE_MAP periods directly from unit macro periods
# after the shared timeline index is fully adopted.
# Remove old instruction text that still tells the tutor to fill FILE_MAP from scratch.
# Keep only generic helpers that remain useful outside the old temporal path.
```

- [ ] **Step 5: Commit**

```bash
git add tests/test_file_map_unit_mapping.py tests/test_core.py src/builder/engine.py
git commit -m "refactor: finalize shared timeline index adoption"
```

## Self-Review

**Spec coverage**

- Camada intermediária temporal: coberta nas Tasks 1, 2 e 5.
- Compatibilidade com repositórios existentes e futuros: coberta nas Tasks 5 e 7.
- Compatibilidade explícita com `Criar Repositório` e `Reprocessar Repositório`: coberta na seção **Structural Regeneration Contract** e na Task 7.
- Preservação da arquitetura low-token: coberta nas Tasks 5 e 6.
- Integração com sinais controlados de classificação (`manual_tags` / `auto_tags`): coberta na arquitetura e na Task 3.
- Redução de gambiarra no `FILE_MAP`: coberta nas Tasks 3, 4 e 8.
- Estratégia explícita de coexistência → cutover → remoção do legado: coberta na seção **Migration Strategy** e consolidada na Task 8.
- Contrato explícito do índice temporal: coberto na seção **Timeline Index Contract** e exercitado nas Tasks 1 e 5.
- Fallback para cronograma ausente ou ruim: coberto na seção **Fallback Policy** e na Task 5.
- Cutover das instruções do tutor: coberto na Task 6.

**Placeholder scan**

- Não deixei `TODO`, `TBD` ou referências vagas de arquivo.
- O único ponto anteriormente vago (`...` na Task 4) foi substituído por chamada explícita a `_aggregate_unit_periods_from_blocks(...)`.
- Os passos com remoção de código legado estão descritos explicitamente na Task 8.

**Type consistency**

- O plano usa consistentemente:
  - `_build_timeline_index(...)`
  - `_assign_timeline_block_to_unit(...)`
  - `_build_file_map_timeline_context_from_course(...)`
  - `_write_internal_timeline_index(...)`
- O artefato interno previsto é sempre `course/.timeline_index.json`.

## Notes

- O objetivo deste plano não é expor mais um arquivo para a LLM ler, e sim introduzir uma infraestrutura interna do builder para tornar `COURSE_MAP.md` e `FILE_MAP.md` mais precisos.
- Se o índice temporal interno se mostrar estável e muito útil para debug humano, um `TIMELINE_INDEX.md` de inspeção poderá ser considerado depois, mas **não** faz parte deste plano.
