# System-Wide Token Optimization Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir sistematicamente o consumo de tokens do tutor web e dos projetos gerados, priorizando contexto curto, roteável e reaplicável via reprocessamento em repositórios já existentes.

**Architecture:** A abordagem é `map-first` e `evidence-light`: o build passa a gerar artefatos de navegação compactos, glossário e descrições visuais curtas, e o tutor web passa a consultar primeiro esses arquivos de alto sinal antes de abrir markdowns longos. A otimização deve ocorrer no pipeline de build, no reprocessamento e nos arquivos de instruções, para que repositórios antigos possam ser atualizados sem reextração completa.

**Tech Stack:** Python 3.11, pipeline local do `RepoBuilder`, Markdown, JSON (`manifest.json`, `bundle.seed.json`), Tkinter UI para ajuda/status, pytest.

---

## File Structure

**Core generation**
- Modify: `src/builder/engine.py`
  Responsibility: centralizar heurísticas low-token para `FILE_MAP.md`, `COURSE_MAP.md`, `GLOSSARY.md`, `bundle.seed.json`, injeção de descrições de imagem, seleção de evidência curta e reprocessamento.

**UI / help / product communication**
- Modify: `src/ui/app.py`
  Responsibility: mensagens de build/reprocessamento e affordances de UX que expliquem reaplicação da arquitetura low-token.
- Modify: `src/ui/dialogs.py`
  Responsibility: Central de Ajuda e documentação visível no app para explicar a estratégia de contexto econômico.

**Tests**
- Modify: `tests/test_core.py`
  Responsibility: cobertura do build/reprocessamento low-token, seleção de bundle, glossário enriquecido, regeneração de mapas.
- Modify: `tests/test_image_curation.py`
  Responsibility: garantir que descrições visuais compactas e supressão de redundância não regrediram.

**Docs**
- Modify: `README.md`
  Responsibility: explicar a arquitetura low-token, o papel de `Reprocessar Repositório` e como o Claude deve navegar o projeto.
- Modify: `docs/superpowers/specs/2026-03-25-image-curator-design.md`
  Responsibility: marcar/alinhar observações arquiteturais para não contradizer a estratégia atual.
- Modify: `docs/superpowers/plans/2026-03-31-claude-token-optimization-architecture.md`
  Responsibility: registrar implementação concluída / follow-ups, se necessário.

**Generated repo artifacts affected**
- Regenerated: `course/FILE_MAP.md`
- Regenerated: `course/COURSE_MAP.md`
- Regenerated: `course/GLOSSARY.md`
- Regenerated: `INSTRUCOES_CLAUDE_PROJETO.md`
- Regenerated: `build/claude-knowledge/bundle.seed.json`

## Task 1: Formalizar o orçamento de contexto do projeto

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_file_map_and_course_map_stay_compact():
    manifest_entries = [
        {"entry_id": "a", "title": "Slides A", "category": "material-de-aula", "base_markdown": "content/curated/a.md"},
        {"entry_id": "b", "title": "Lista 1", "category": "listas", "base_markdown": "content/curated/b.md"},
    ]
    file_map = file_map_md({"course_name": "Teste"}, manifest_entries)
    course_map = course_map_md({"course_name": "Teste"}, subject_profile=None)
    assert "quando abrir" in file_map.lower()
    assert len(file_map) < 12000
    assert len(course_map) < 12000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_file_map_and_course_map_stay_compact -v`
Expected: FAIL porque o teste ainda não existe ou o contrato compacto ainda não está explicitamente coberto.

- [ ] **Step 3: Write minimal implementation**

```python
def _assert_low_token_budget(text: str, *, hard_cap: int) -> str:
    compact = (text or "").strip()
    if len(compact) <= hard_cap:
        return compact
    return compact[: hard_cap - 24].rstrip() + "\n\n> Conteúdo truncado."
```

Aplicar esse helper apenas onde fizer sentido para artefatos de navegação, nunca em markdown curado completo.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_file_map_and_course_map_stay_compact -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "test: codify compact context budget for routing artifacts"
```

## Task 2: Melhorar a coleta de evidência curta para o glossário

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_glossary_uses_curated_heading_and_manifest_title_as_evidence(tmp_path):
    curated_dir = tmp_path / "content" / "curated"
    curated_dir.mkdir(parents=True)
    (curated_dir / "subareas.md").write_text(
        "# Subáreas e disciplinas afins\n\n"
        "## Relação com outras áreas\n"
        "A IA se conecta a estatística, otimização, robótica e ciência de dados.",
        encoding="utf-8",
    )
    manifest = {"entries": [{"title": "Subáreas e disciplinas afins", "base_markdown": "content/curated/subareas.md"}]}
    docs = _collect_glossary_evidence(tmp_path, manifest_entries=manifest["entries"])
    evidence = _find_glossary_evidence("Subáreas e disciplinas afins", "Unidade de Aprendizagem 1 — Visão Geral", docs)
    assert "estatística" in evidence.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_glossary_uses_curated_heading_and_manifest_title_as_evidence -v`
Expected: FAIL porque a coleta atual só usa corpo curto e não aproveita suficientemente headings e títulos do manifest.

- [ ] **Step 3: Write minimal implementation**

```python
def _collect_glossary_evidence(root_dir: Optional[Path], manifest_entries: Optional[List[dict]] = None) -> List[Dict[str, str]]:
    ...
    docs.append({
        "title": title,
        "headings": headings[:10],
        "manifest_title": manifest_title,
        "text": body[:4000],
    })
```

```python
def _find_glossary_evidence(term: str, unit_title: str, docs: List[Dict[str, str]]) -> str:
    haystack = " ".join([
        doc.get("manifest_title", ""),
        doc.get("title", ""),
        " ".join(doc.get("headings", [])),
        doc.get("text", ""),
    ]).lower()
```

Regra: usar apenas a melhor sentença curta; nunca concatenar múltiplos trechos.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_glossary_uses_curated_heading_and_manifest_title_as_evidence -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: enrich glossary evidence with headings and manifest titles"
```

## Task 3: Evitar desperdício por definições repetidas ou longas demais no glossário

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_glossary_definition_from_evidence_stays_short_and_deduplicated():
    evidence = "Subáreas e disciplinas afins. Subáreas e disciplinas afins conectam IA a estatística e robótica."
    definition = _refine_glossary_definition_from_evidence(
        "Subáreas e disciplinas afins",
        "visão geral",
        evidence,
    )
    assert definition.startswith("Subáreas e disciplinas afins conectam")
    assert definition.count("Subáreas e disciplinas afins") == 1
    assert len(definition) < 220
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_glossary_definition_from_evidence_stays_short_and_deduplicated -v`
Expected: FAIL porque a limpeza atual ainda pode repetir o título ou aceitar sentenças ruins.

- [ ] **Step 3: Write minimal implementation**

```python
def _normalize_glossary_sentence(term: str, sentence: str) -> str:
    sent = _collapse_ws(sentence)
    sent = re.sub(rf"^(?:{re.escape(term)}[\s:.-]+)+", "", sent, flags=re.IGNORECASE)
    return f"{term} {sent}".strip()
```

Usar esse normalizador antes de retornar a sentença final, e reimpor limite de tamanho.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_glossary_definition_from_evidence_stays_short_and_deduplicated -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "fix: normalize glossary definitions derived from evidence"
```

## Task 4: Passar o manifest atual para o pipeline de glossário no build e no reprocessamento

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_incremental_build_rewrites_glossary_with_manifest_aware_evidence(tmp_path):
    repo = tmp_path / "repo"
    ensure_dir(repo / "content" / "curated")
    write_text(repo / "content" / "curated" / "subareas.md", "# Subáreas e disciplinas afins\n\nA IA se conecta a estatística.")
    manifest = {
        "course": {"course_name": "IA"},
        "options": {},
        "entries": [{"title": "Subáreas e disciplinas afins", "base_markdown": "content/curated/subareas.md"}],
    }
    builder = RepoBuilder(repo, manifest["course"], [], {}, subject_profile=SubjectProfile(teaching_plan=LEARNING_UNIT_PLAN))
    builder._regenerate_pedagogical_files(manifest)
    glossary = (repo / "course" / "GLOSSARY.md").read_text(encoding="utf-8")
    assert "estatística" in glossary.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_incremental_build_rewrites_glossary_with_manifest_aware_evidence -v`
Expected: FAIL enquanto `_regenerate_pedagogical_files()` não repassa `manifest["entries"]` para o glossário.

- [ ] **Step 3: Write minimal implementation**

```python
write_text(
    self.root_dir / "course" / "GLOSSARY.md",
    glossary_md(
        self.course_meta,
        self.subject_profile,
        root_dir=self.root_dir,
        manifest_entries=manifest.get("entries", []),
    ),
)
```

Aplicar o mesmo contrato tanto em `build()` quanto em `_regenerate_pedagogical_files()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_incremental_build_rewrites_glossary_with_manifest_aware_evidence -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "feat: make glossary regeneration manifest-aware"
```

## Task 5: Compactar melhor os artefatos de roteamento sem perder navegabilidade

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_bundle_seed_contains_selection_policy_and_not_full_content():
    manifest = {"entries": [{"title": "Slides", "category": "material-de-aula", "include_in_bundle": True}]}
    payload = build_bundle_seed_payload({"course_name": "Teste"}, manifest)
    assert "selection_policy" in payload
    assert "full_markdown" not in json.dumps(payload, ensure_ascii=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_bundle_seed_contains_selection_policy_and_not_full_content -v`
Expected: FAIL se o contrato ainda não estiver fixado por teste.

- [ ] **Step 3: Write minimal implementation**

```python
payload["selection_policy"] = {
    "strategy": "high-signal-low-token",
    "max_initial_items": max_items,
    "prefer_exam_relevant": True,
    "prefer_material_base": True,
    "exclude_full_text": True,
}
```

Garantir que `bundle.seed.json` carregue apenas caminho, score e razões, nunca conteúdo extenso.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_bundle_seed_contains_selection_policy_and_not_full_content -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py tests/test_core.py
git commit -m "test: lock bundle seed into low-token metadata only"
```

## Task 6: Enxugar instruções do tutor para o fluxo `map-first`

**Files:**
- Modify: `src/builder/engine.py`
- Test: `tests/test_core.py`
- Modify: `README.md`
- Modify: `src/ui/dialogs.py`

- [ ] **Step 1: Write the failing test**

```python
def test_claude_instructions_start_with_map_first_navigation():
    result = generate_claude_project_instructions({"course_name": "Teste"})
    assert "Comece por `course/COURSE_MAP.md`" in result
    assert "Abra markdowns longos apenas quando necessário" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_claude_instructions_start_with_map_first_navigation -v`
Expected: FAIL se a redação atual ainda não explicita o fluxo com precisão suficiente.

- [ ] **Step 3: Write minimal implementation**

```python
instructions = instructions.replace(
    "Leia o repositório.",
    "Comece por `course/COURSE_MAP.md`, depois `student/STUDENT_STATE.md`, depois `course/FILE_MAP.md`. Abra markdowns longos apenas quando necessário."
)
```

Atualizar os textos equivalentes no README e na ajuda do app, sem duplicar explicações longas.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_claude_instructions_start_with_map_first_navigation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/builder/engine.py src/ui/dialogs.py README.md tests/test_core.py
git commit -m "docs: align tutor instructions with map-first low-token flow"
```

## Task 7: Validar o reprocessamento como mecanismo oficial de retrofit low-token

**Files:**
- Modify: `tests/test_core.py`
- Modify: `src/ui/app.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

```python
def test_incremental_build_reapplies_low_token_outputs_without_new_entries(tmp_path):
    repo = make_existing_repo(tmp_path)
    builder = make_repo_builder_for_existing_repo(repo)
    builder.incremental_build()
    assert (repo / "course" / "FILE_MAP.md").exists()
    assert (repo / "course" / "GLOSSARY.md").exists()
    assert (repo / "build" / "claude-knowledge" / "bundle.seed.json").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_incremental_build_reapplies_low_token_outputs_without_new_entries -v`
Expected: FAIL se algum artefato ainda não for regenerado de forma estável.

- [ ] **Step 3: Write minimal implementation**

```python
message = (
    "Reprocessar Repositório reaplica mapas, glossário, bundle inicial e instruções "
    "na arquitetura low-token atual, sem exigir nova extração completa dos PDFs."
)
```

Colocar essa mensagem em `src/ui/app.py` e refletir o mesmo contrato no README.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_incremental_build_reapplies_low_token_outputs_without_new_entries -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/app.py README.md tests/test_core.py
git commit -m "docs: position reprocess as low-token retrofit path"
```

## Task 8: Medir regressão simples de volume textual nos artefatos-chave

**Files:**
- Modify: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

```python
def test_low_token_artifacts_remain_small_on_sample_course():
    sp = SubjectProfile(name="IA", slug="ia", teaching_plan=LEARNING_UNIT_PLAN, syllabus=SYLLABUS_TABLE)
    file_map = file_map_md({"course_name": "IA"}, SAMPLE_MANIFEST_ENTRIES)
    course_map = course_map_md({"course_name": "IA"}, sp)
    glossary = glossary_md({"course_name": "IA"}, sp)
    assert len(file_map) < 16000
    assert len(course_map) < 16000
    assert len(glossary) < 20000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core.py::test_low_token_artifacts_remain_small_on_sample_course -v`
Expected: FAIL se algum artefato crescer demais durante as melhorias.

- [ ] **Step 3: Write minimal implementation**

```python
# Nenhuma feature nova aqui; ajustar geração apenas se algum artefato passar do teto.
# Se necessário, cortar listagens excessivas ou normalizar textos repetidos.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core.py::test_low_token_artifacts_remain_small_on_sample_course -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_core.py src/builder/engine.py
git commit -m "test: guard low-token artifact size ceilings"
```

## Task 9: Reprocessar repositórios reais de validação

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-03-31-claude-token-optimization-architecture.md`

- [ ] **Step 1: Write the validation checklist**

```markdown
1. Reprocessar `Inteligencia-Artifical-Tutor`
2. Reprocessar `Metodos-Formais-Tutor`
3. Abrir `course/GLOSSARY.md`, `course/FILE_MAP.md`, `course/COURSE_MAP.md`
4. Confirmar definições sem placeholder, bundle seletivo e instruções map-first
```

- [ ] **Step 2: Run the validation commands**

Run:

```bash
python -m pytest tests/test_core.py -q
```

Expected: PASS

Depois, no app:
1. Abrir a matéria
2. Clicar `Reprocessar Repositório`
3. Inspecionar os artefatos gerados

- [ ] **Step 3: Record observed outcomes**

```markdown
- Glossário sem placeholders
- Artefatos regenerados sem reextração completa
- Instruções orientando leitura por mapas primeiro
- Bundle inicial sem texto bruto longo
```

- [ ] **Step 4: Update docs**

Registrar no README e no plano anterior que a validação em repositórios reais foi concluída.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/plans/2026-03-31-claude-token-optimization-architecture.md
git commit -m "docs: record low-token validation on existing repos"
```

## Self-Review

**Spec coverage:** O plano cobre geração de mapas compactos, glossário enriquecido sem inflar contexto, bundle seletivo, instruções `map-first`, reaplicação via reprocessamento e validação em repositórios já existentes.

**Placeholder scan:** Não há `TODO`, `TBD` ou referências vagas; cada task aponta arquivos, testes, comandos e mudanças mínimas.

**Type consistency:** O plano usa consistentemente `glossary_md(..., root_dir=..., manifest_entries=...)`, `RepoBuilder.incremental_build()`, `manifest["entries"]`, `FILE_MAP.md`, `COURSE_MAP.md`, `GLOSSARY.md` e `bundle.seed.json`.

Plan complete and saved to `docs/superpowers/plans/2026-03-31-system-wide-token-optimization-architecture.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
