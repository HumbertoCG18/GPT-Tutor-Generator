# Cronograma ASP.NET — Classificação por cor + correções de matching

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Usar cor da linha HTML como sinal autoritativo de tipo de aula; propagar `ignored` ao scorer de blocos; corrigir exclusão de `bibliografia`/`references` do cronograma; tornar `manual_timeline_block_id` robusto.

**Architecture:** Parser ASP.NET lê `background-color` → mapeia para `kind` + `ignored` → emite `{kind=X}` + `⊘` no syllabus → `_build_timeline_index` parseia e propaga para rows → scorer descarta rows ignoradas. Fix paralelo em `navigation_artifacts.py` para skip de categorias de referência, e fallback em `_resolve_entry_manual_timeline_block` para casar `bloco-N` por índice.

**Tech Stack:** Python, BeautifulSoup, pytest.

---

### Task 1: Mapa de cores no parser ASP.NET

**Files:**
- Modify: `src/utils/helpers.py` (função `_parse_aspnet_schedule` e helper novo `_aspnet_row_kind`)
- Test: `tests/test_html_schedule_parser.py`

- [ ] **Step 1: Escrever testes falhantes**

Adicionar ao final de `tests/test_html_schedule_parser.py`:

```python
ASPNET_COLOR_SAMPLES = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr style="background-color:#FFA500;">
    <td><span id="dgAulas_ctl10_lblAula">15</span></td>
    <td><span id="dgAulas_ctl10_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl10_lblData">22/04/2026</span></td>
    <td><span id="dgAulas_ctl10_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl10_lblDescricao">Prova P1</span></td>
    <td><span id="dgAulas_ctl10_lblAtividade">Prova</span></td>
    <td><span id="dgAulas_ctl10_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:#FF8C00;">
    <td><span id="dgAulas_ctl37_lblAula">37</span></td>
    <td><span id="dgAulas_ctl37_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl37_lblData">08/07/2026</span></td>
    <td><span id="dgAulas_ctl37_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl37_lblDescricao">Prova PS</span></td>
    <td><span id="dgAulas_ctl37_lblAtividade">Prova de Substituição</span></td>
    <td><span id="dgAulas_ctl37_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:#8B0000;">
    <td><span id="dgAulas_ctl25_lblAula">25</span></td>
    <td><span id="dgAulas_ctl25_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl25_lblData">27/05/2026</span></td>
    <td><span id="dgAulas_ctl25_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl25_lblDescricao">SE Day</span></td>
    <td><span id="dgAulas_ctl25_lblAtividade">Evento Acadêmico</span></td>
    <td><span id="dgAulas_ctl25_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:#FFFF00;">
    <td><span id="dgAulas_ctl20_lblAula">20</span></td>
    <td><span id="dgAulas_ctl20_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl20_lblData">10/06/2026</span></td>
    <td><span id="dgAulas_ctl20_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl20_lblDescricao">Apresentação de trabalho</span></td>
    <td><span id="dgAulas_ctl20_lblAtividade">Trabalho</span></td>
    <td><span id="dgAulas_ctl20_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:LightGrey;">
    <td><span id="dgAulas_ctl39_lblAula"></span></td>
    <td><span id="dgAulas_ctl39_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl39_lblData">15/07/2026</span></td>
    <td><span id="dgAulas_ctl39_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl39_lblDescricao">Prova G2</span></td>
    <td><span id="dgAulas_ctl39_lblAtividade">Prova de G2</span></td>
    <td><span id="dgAulas_ctl39_lblRecursos"></span></td>
  </tr>
</table>
"""


def test_aspnet_color_exam_emits_kind_exam_no_ignore():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "— Prova P1 [Prova] {kind=exam}" in result
    assert "Prova P1 [Prova] {kind=exam} ⊘" not in result


def test_aspnet_color_ps_emits_kind_ps_ignored():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "{kind=ps} ⊘" in result


def test_aspnet_color_event_emits_kind_event_ignored():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "— SE Day [Evento Acadêmico] {kind=event} ⊘" in result


def test_aspnet_color_assignment_emits_kind_assignment_no_ignore():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "{kind=assignment}" in result
    assert "{kind=assignment} ⊘" not in result


def test_aspnet_color_g2_emits_kind_g2_ignored():
    result = parse_html_schedule(ASPNET_COLOR_SAMPLES)
    assert "— Prova G2 [Prova de G2] {kind=g2} ⊘" in result


def test_aspnet_class_row_omits_kind_token():
    # Row sem cor especial não deve poluir syllabus com {kind=class}
    result = parse_html_schedule(ASPNET_SAMPLE)
    assert "{kind=" not in result
```

- [ ] **Step 2: Rodar testes — devem falhar**

```
python -m pytest tests/test_html_schedule_parser.py -v
```

Esperado: 6 testes novos falhando.

- [ ] **Step 3: Adicionar mapa de cores e helper em `helpers.py`**

Localizar `_parse_aspnet_schedule` em `src/utils/helpers.py`. Antes da função, adicionar:

```python
_ASPNET_COLOR_KIND_MAP = {
    "red": ("suspension", True),
    "#ff0000": ("suspension", True),
    "lightgrey": ("g2", True),
    "#d3d3d3": ("g2", True),
    "#ffa500": ("exam", False),
    "orange": ("exam", False),
    "#ff8c00": ("ps", True),
    "darkorange": ("ps", True),
    "#8b0000": ("event", True),
    "darkred": ("event", True),
    "#ffff00": ("assignment", False),
    "yellow": ("assignment", False),
}


def _aspnet_row_kind(row) -> tuple[str, bool]:
    """Return (kind, ignored) derived from row background-color. Default: ('class', False)."""
    style = (row.get("style") or "").lower().replace(" ", "")
    import re as _re
    match = _re.search(r"background-color:([^;]+)", style)
    if not match:
        return ("class", False)
    color = match.group(1).strip().rstrip(";")
    return _ASPNET_COLOR_KIND_MAP.get(color, ("class", False))
```

Remover `_aspnet_row_ignored` antigo (substituído por `_aspnet_row_kind`).

- [ ] **Step 4: Atualizar `_parse_aspnet_schedule` para emitir `{kind=X}` + `⊘`**

Substituir loop por:

```python
def _parse_aspnet_schedule(soup) -> str:
    table = soup.find(id="dgAulas") or soup.find("table")
    if not table:
        return "Erro: Tabela de cronograma ASP.NET nao encontrada."
    lines = ["## Cronograma de Aulas", ""]
    for row in table.find_all("tr"):
        data = _aspnet_row_cell(row, "Data")
        descricao = _aspnet_row_cell(row, "Descricao")
        if not data or not descricao:
            continue
        dia = _aspnet_row_cell(row, "Dia")
        atividade = _aspnet_row_cell(row, "Atividade") or "Aula"
        recursos = _aspnet_row_cell(row, "Recursos")
        kind, ignored = _aspnet_row_kind(row)

        parts = [f"- ({data})"]
        if dia:
            parts.append(dia)
        parts.append(f"— {descricao} [{atividade}]")
        if recursos:
            parts.append(f"@{recursos}")
        if kind != "class":
            parts.append(f"{{kind={kind}}}")
        if ignored:
            parts.append("⊘")
        lines.append(" ".join(parts))
    return "\n".join(lines) + "\n"
```

- [ ] **Step 5: Rodar testes do parser — devem passar**

```
python -m pytest tests/test_html_schedule_parser.py -v
```

Esperado: todos os 11 testes do arquivo passando (5 originais + 6 novos).

- [ ] **Step 6: Rodar suite completa**

```
python -m pytest tests/ -q
```

Esperado: todos passando.

- [ ] **Step 7: Commit**

```
git add src/utils/helpers.py tests/test_html_schedule_parser.py
git commit -m "feat(schedule): classify ASP.NET rows by background color"
```

---

### Task 2: Propagar `kind` para `timeline_signals`

**Files:**
- Modify: `src/builder/timeline_signals.py`
- Test: `tests/test_timeline_signals.py`

- [ ] **Step 1: Escrever testes falhantes**

Adicionar em `tests/test_timeline_signals.py`:

```python
def test_session_extractor_parses_kind_and_skips_ignored_kinds():
    text = """
- (22/04/2026) QUA — Prova P1 [Prova] {kind=exam}
- (08/07/2026) QUA — Prova PS [Prova de Substituição] {kind=ps} ⊘
- (15/07/2026) QUA — Prova G2 [Prova de G2] {kind=g2} ⊘
- (27/05/2026) QUA — SE Day [Evento Acadêmico] {kind=event} ⊘
- (30/03/2026) SEG — Provas por indução [Aula]
"""
    sessions = extract_timeline_session_signals(text)
    dates = {s["date"] for s in sessions}
    # ignored kinds removidos
    assert "2026-07-08" not in dates
    assert "2026-07-15" not in dates
    assert "2026-05-27" not in dates
    # exam (não ignored) preservado
    assert "2026-04-22" in dates
    assert "2026-03-30" in dates
```

- [ ] **Step 2: Rodar e verificar falha**

```
python -m pytest tests/test_timeline_signals.py::test_session_extractor_parses_kind_and_skips_ignored_kinds -v
```

Esperado: fail (⊘ já filtra, mas `kind=event` sem `⊘` no texto atual não seria filtrado; esse teste verifica que `⊘` sozinho basta). Se passar, avançar.

- [ ] **Step 3: Garantir robustez — verificar que `{kind=X}` não quebra regex existentes**

Rodar:
```
python -m pytest tests/test_timeline_signals.py -v
```

Se algum teste quebrar por causa do token `{kind=...}` no body, ajustar regex `_SESSION_RE` em `timeline_signals.py` para não consumir `{` como parte do body. Simples: adicionar `{` à classe de caracteres excluídos em `body` (`[^;\n{]*`).

- [ ] **Step 4: Commit**

```
git add src/builder/timeline_signals.py tests/test_timeline_signals.py
git commit -m "test(timeline): validate kind/ignored propagation from syllabus"
```

---

### Task 3: `_build_timeline_index` consome `kind` e marca rows ignoradas

**Files:**
- Modify: `src/builder/timeline_index.py`
- Test: `tests/test_timeline_signals.py` ou novo `tests/test_timeline_index_kind.py`

- [ ] **Step 1: Localizar onde rows são construídas em `_build_timeline_index`**

```
grep -n "def _build_timeline_index\|row\[" src/builder/timeline_index.py | head -40
```

Identificar o ponto onde cada row recebe campos (`date_text`, `title`, etc).

- [ ] **Step 2: Escrever teste**

Criar `tests/test_timeline_index_kind.py`:

```python
from src.builder.timeline_index import _build_timeline_index


def test_build_timeline_index_marks_ignored_rows_from_kind():
    candidate_rows = [
        {"date_text": "30/03/2026", "title": "Provas por indução", "kind": "class"},
        {"date_text": "22/04/2026", "title": "Prova P1", "kind": "exam"},
        {"date_text": "20/04/2026", "title": "Suspensão", "kind": "suspension", "ignored": True},
    ]
    index = _build_timeline_index(candidate_rows, unit_index=[])
    blocks = index.get("blocks", [])
    # Nenhum bloco deve ter row ignorada ativa no scoring
    for block in blocks:
        for row in block.get("rows", []):
            if row.get("date_text") == "20/04/2026":
                assert row.get("ignored") is True
```

- [ ] **Step 3: Garantir propagação em `_build_timeline_index`**

Se a função já preserva campos arbitrários das rows, teste passa sem mudanças. Se descarta, propagar `kind` e `ignored` ao emitir row final.

Rodar:
```
python -m pytest tests/test_timeline_index_kind.py -v
```

- [ ] **Step 4: Parsear `{kind=X}` quando row vem de texto, não de dict**

No caminho onde rows são derivadas do syllabus (texto), adicionar extração de `{kind=(\w+)}` do título e setar `row["kind"]` e `row["ignored"] = kind in {"suspension","g2","ps","event"}`. Remover o token do título antes de armazenar.

Referência no engine.py: procurar uso de `candidate_rows` que vem de syllabus parsing. Se extrator de rows usa regex do syllabus, adicionar captura opcional de `{kind=X}`.

- [ ] **Step 5: Commit**

```
git add src/builder/timeline_index.py tests/test_timeline_index_kind.py
git commit -m "feat(timeline): propagate kind/ignored from syllabus rows"
```

---

### Task 4: Scorer descarta rows ignoradas

**Files:**
- Modify: `src/builder/engine.py` (funções `_score_entry_against_timeline_block` e `_score_entry_against_timeline_sessions` perto de `engine.py:6077`)
- Test: `tests/test_file_map_unit_mapping.py` ou novo

- [ ] **Step 1: Teste**

Criar teste que monta bloco com row `ignored=True` e verifica que score não considera seu título.

- [ ] **Step 2: Implementar filtro**

Em `_score_entry_against_timeline_block`, onde itera `block.get("rows", [])`, pular `row.get("ignored")`. Se depois do filtro não sobra row, retornar score=0.

Em `_score_entry_against_timeline_sessions`, confirmar que sessions já foram filtradas por `⊘` no extractor (Task 2 confirma).

- [ ] **Step 3: Adicionar blocos compostos só de ignored ao admin-only pool**

Em `_timeline_block_is_administrative_only`, se todas as rows têm `ignored=True`, retornar True.

- [ ] **Step 4: Commit**

```
git add src/builder/engine.py tests/test_file_map_unit_mapping.py
git commit -m "fix(matching): skip ignored rows in timeline block scoring"
```

---

### Task 5: `bibliografia` / `references` sem unidade nem período

**Files:**
- Modify: `src/builder/navigation_artifacts.py` (linha ~636)
- Test: `tests/test_file_map_unit_mapping.py`

- [ ] **Step 1: Teste**

Adicionar:

```python
def test_file_map_skips_timeline_for_reference_categories():
    from src.builder.navigation_artifacts import build_file_map_row  # ou função correta
    entry = {"title": "Ref X", "category": "references", "tags": "main"}
    row = build_file_map_row(entry, course_meta={"_repo_root": None}, unit_index=[...], ...)
    assert "unidade-" not in row.unit  # ou row.unit == "curso-inteiro" / ""
    assert row.period == ""
```

Ajustar conforme API real da função.

- [ ] **Step 2: Implementar**

Substituir em `navigation_artifacts.py:636`:

```python
_NO_TIMELINE_CATEGORIES = {"cronograma", "bibliografia", "referencias", "references"}
if category in _NO_TIMELINE_CATEGORIES:
    unit = "curso-inteiro"
    skip_timeline = True
else:
    unit = ""
    skip_timeline = False
```

Envolver o bloco de auto-map de unidade e atribuição de `period` em `if not skip_timeline:`. Forçar `period = ""` antes do return quando `skip_timeline`.

- [ ] **Step 3: Rodar testes**

```
python -m pytest tests/test_file_map_unit_mapping.py -v
```

- [ ] **Step 4: Commit**

```
git add src/builder/navigation_artifacts.py tests/test_file_map_unit_mapping.py
git commit -m "fix(file-map): exclude reference categories from timeline mapping"
```

---

### Task 6: Fallback `bloco-N` por índice em `_resolve_entry_manual_timeline_block`

**Files:**
- Modify: `src/builder/engine.py` (engine.py:8032)
- Test: novo `tests/test_manual_timeline_block_resolution.py`

- [ ] **Step 1: Teste**

```python
def test_resolve_manual_block_falls_back_to_nth_instructional_block():
    timeline_context = {
        "timeline_index": {
            "blocks": [
                {"id": "bloco-auto-001", "administrative_only": False, "unit_slug": "u1"},
                {"id": "bloco-auto-002", "administrative_only": True, "unit_slug": "u1"},
                {"id": "bloco-auto-003", "administrative_only": False, "unit_slug": "u1"},
                {"id": "bloco-auto-004", "administrative_only": False, "unit_slug": "u1"},
                {"id": "bloco-auto-005", "administrative_only": False, "unit_slug": "u1"},
            ]
        }
    }
    from src.builder.engine import _resolve_entry_manual_timeline_block
    entry = {"manual_timeline_block_id": "bloco-04", "unit_slug": "u1"}
    resolved = _resolve_entry_manual_timeline_block(entry, timeline_context)
    # 4º bloco instrucional (pulando o administrative_only index 1)
    assert resolved["id"] == "bloco-auto-005"
```

- [ ] **Step 2: Implementar**

```python
def _resolve_entry_manual_timeline_block(entry, timeline_context):
    raw = str(entry.get("manual_timeline_block_id") or "").strip()
    if not raw:
        return None
    blocks = list(((timeline_context or {}).get("timeline_index") or {}).get("blocks", []) or [])
    for block in blocks:
        if str(block.get("id", "")).strip() == raw:
            return block
    import re
    m = re.match(r"bloco-(\d+)$", raw)
    if m:
        n = int(m.group(1))
        entry_unit = str(entry.get("unit_slug") or entry.get("manual_unit_slug") or "").strip()
        instructional = [
            b for b in blocks
            if not b.get("administrative_only")
            and (not entry_unit or str(b.get("unit_slug", "")).strip() == entry_unit)
        ]
        if 1 <= n <= len(instructional):
            return instructional[n - 1]
    return None
```

- [ ] **Step 3: Rodar**

```
python -m pytest tests/test_manual_timeline_block_resolution.py -v
```

- [ ] **Step 4: Commit**

```
git add src/builder/engine.py tests/test_manual_timeline_block_resolution.py
git commit -m "feat(timeline): fallback manual block resolution by N index"
```

---

### Task 7: Validação final

- [ ] **Step 1: Rodar suite inteira**

```
python -m pytest tests/ -q
```

Esperado: todos passando.

- [ ] **Step 2: Usuário reprocessa Métodos Formais no app**

Humberto abre o app, cola o HTML atualizado, salva perfil, `Repo → Reprocessar Repositório`.

- [ ] **Step 3: Validar FILE_MAP**

- `FormalizacaoAlgoritmos_Recursao3` deve ter Período dentro de `02/03 a 13/04/2026`
- Entries `bibliografia` / `references` devem ter coluna Unidade vazia ou `curso-inteiro` e Período vazio
- Nenhum entry deve ter Período em datas `⊘` (13/07, 15/07, 20/04, 27/05, 08/07)

- [ ] **Step 4: Merge final**

Sem PR (trabalho direto em `main` seguindo padrão da Fase 1).
