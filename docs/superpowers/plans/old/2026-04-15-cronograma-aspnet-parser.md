# Cronograma ASP.NET Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o achatamento de `parse_html_schedule` por emissão estruturada (uma linha por aula) no formato que `extract_timeline_session_signals` já reconhece, resolvendo `card_evidence = 0` em repositórios regenerados.

**Architecture:** Duas mudanças cirúrgicas: (1) expandir o regex de sessions em `timeline_signals.py` para aceitar em-dash (`—`), marcador de dia da semana e sufixo `⊘`; (2) adicionar detector de cronograma ASP.NET em `helpers.py` com parser dedicado para tabelas `dgAulas`, preservando fallback para o parser genérico existente.

**Tech Stack:** Python 3, BeautifulSoup 4, pytest. Sem dependências novas.

**Spec:** `docs/superpowers/specs/2026-04-15-cronograma-aspnet-parser-design.md`

---

## File Structure

**Arquivos modificados:**
- `src/builder/timeline_signals.py` — expande regex `_SESSION_RE` para aceitar novo formato
- `src/utils/helpers.py` — adiciona `_parse_aspnet_schedule` e wire em `parse_html_schedule`

**Arquivos criados:**
- `tests/test_html_schedule_parser.py` — testes do parser ASP.NET (detecção, saída, fallback, linhas especiais)

**Arquivos ampliados:**
- `tests/test_timeline_signals.py` — casos novos para o formato estruturado (em-dash, dia da semana, sufixo `⊘`, compatibilidade com formato antigo)

Nada novo em schema, UI, ou modelos. Sem migrações.

---

## Task 1: Regex de sessions aceita em-dash e dia da semana opcional

**Files:**
- Modify: `src/builder/timeline_signals.py:18-21` (regex `_SESSION_RE`)
- Test: `tests/test_timeline_signals.py`

Expandir o regex para reconhecer linhas no novo formato `(30/03/2026) SEG — Provas por indução [Aula]` sem quebrar o formato antigo `(30/03/2026): texto`.

- [ ] **Step 1: Escrever teste falhando para formato novo com em-dash**

Adicionar no final de `tests/test_timeline_signals.py`:

```python
def test_session_extractor_accepts_em_dash_and_day_prefix():
    text = "- (30/03/2026) SEG — Provas por indução [Aula]"
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    s = sessions[0]
    assert s["kind"] == "class"
    assert s["date"] == "2026-03-30"
    assert "provas por inducao" in s["label"]


def test_session_extractor_still_accepts_legacy_colon_format():
    text = "(30/03/2026): Provas por indução"
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    assert sessions[0]["date"] == "2026-03-30"
    assert "provas por inducao" in sessions[0]["label"]
```

- [ ] **Step 2: Rodar para confirmar falha**

Run: `python -m pytest tests/test_timeline_signals.py::test_session_extractor_accepts_em_dash_and_day_prefix -v`
Expected: FAIL — sessão não é extraída porque `—` não está no separador.

- [ ] **Step 3: Expandir `_SESSION_RE`**

Editar `src/builder/timeline_signals.py` linhas 18-21, substituindo `_SESSION_RE` por:

```python
_SESSION_RE = re.compile(
    rf"(?:^|[\n;]\s*|:\s*)\s*(?:[-*•]\s*)?\(?\s*(?P<label>(?:{_DATE_RE})|(?:atividade\s+assincrona|assincrona|atividade\s+async|async))\s*\)?\s*(?:[a-z]{{3}}\s+)?\s*[:\-–—]\s*(?P<body>[^;\n]*)",
    re.IGNORECASE,
)
```

Mudanças:
- `(?:[a-z]{3}\s+)?` — dia da semana abreviado opcional (já normalizado para lowercase)
- `[:\-–—]` — aceita `:`, `-`, `–` (en-dash U+2013), `—` (em-dash U+2014)

- [ ] **Step 4: Rodar para confirmar passagem**

Run: `python -m pytest tests/test_timeline_signals.py -v`
Expected: PASS em todos os testes (novos e antigos).

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline_signals.py tests/test_timeline_signals.py
git commit -m "feat(timeline): regex aceita em-dash e dia da semana opcional"
```

---

## Task 2: Filtro `⊘` para linhas ignoradas

**Files:**
- Modify: `src/builder/timeline_signals.py` (função `extract_timeline_session_signals`)
- Test: `tests/test_timeline_signals.py`

Linhas como `(20/04/2026) SEG — Suspensão de aulas [Aula] ⊘` devem ser reconhecidas pelo regex mas descartadas (não viram session nem contribuem para card_evidence).

- [ ] **Step 1: Escrever teste falhando**

Adicionar em `tests/test_timeline_signals.py`:

```python
def test_session_extractor_skips_ignored_marker():
    text = (
        "- (20/04/2026) SEG — Suspensão de aulas [Aula] ⊘\n"
        "- (22/04/2026) QUA — Prova P1 [Prova]"
    )
    sessions = extract_timeline_session_signals(text)
    assert len(sessions) == 1
    assert sessions[0]["date"] == "2026-04-22"
```

- [ ] **Step 2: Rodar para confirmar falha**

Run: `python -m pytest tests/test_timeline_signals.py::test_session_extractor_skips_ignored_marker -v`
Expected: FAIL — ambas as linhas viram session.

- [ ] **Step 3: Implementar filtro**

Em `src/builder/timeline_signals.py`, dentro do loop `for match in _SESSION_RE.finditer(normalized):` (por volta da linha 151), adicionar no início:

```python
    for match in _SESSION_RE.finditer(normalized):
        label_raw = match.group("label").strip()
        body_raw = match.group("body").strip(" \t-:;.,")
        if "⊘" in body_raw:
            continue
        label_norm = _normalize_match_text(label_raw)
```

Mesma proteção no loop `_PREFIXED_SESSION_RE` (linha 118) — adicionar após `body_raw = match.group("body").strip(...)`:

```python
        if match.group("body") and "⊘" in match.group("body"):
            continue
```

- [ ] **Step 4: Rodar para confirmar passagem**

Run: `python -m pytest tests/test_timeline_signals.py -v`
Expected: PASS em todos.

- [ ] **Step 5: Commit**

```bash
git add src/builder/timeline_signals.py tests/test_timeline_signals.py
git commit -m "feat(timeline): ignora sessoes marcadas com sufixo ⊘"
```

---

## Task 3: Detector de cronograma ASP.NET

**Files:**
- Modify: `src/utils/helpers.py:341` (função `parse_html_schedule`)
- Test: `tests/test_html_schedule_parser.py` (criar)

Adicionar função auxiliar `_is_aspnet_schedule(soup) -> bool` que detecta a tabela `dgAulas` ou presença de spans `_lblData`.

- [ ] **Step 1: Criar arquivo de teste com teste falhando**

Criar `tests/test_html_schedule_parser.py`:

```python
from src.utils.helpers import parse_html_schedule


ASPNET_SAMPLE = """
<table id="dgAulas">
  <tbody>
    <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
    <tr>
      <td><span id="dgAulas_ctl02_lblAula">1</span></td>
      <td><span id="dgAulas_ctl02_lblDia">SEG</span></td>
      <td><span id="dgAulas_ctl02_lblData">30/03/2026</span></td>
      <td><span id="dgAulas_ctl02_lblHora">LM<br>19:15 - 20:45</span></td>
      <td><span id="dgAulas_ctl02_lblDescricao">Provas por indução</span></td>
      <td><span id="dgAulas_ctl02_lblAtividade">Aula</span></td>
      <td><span id="dgAulas_ctl02_lblRecursos"></span></td>
    </tr>
  </tbody>
</table>
"""


def test_parse_aspnet_schedule_emits_structured_line():
    result = parse_html_schedule(ASPNET_SAMPLE)
    assert "## Cronograma de Aulas" in result
    assert "- (30/03/2026) SEG — Provas por indução [Aula]" in result


def test_parse_non_aspnet_html_keeps_legacy_table_format():
    html = """
    <table>
      <tr><th>Col1</th><th>Col2</th></tr>
      <tr><td>a</td><td>b</td></tr>
    </table>
    """
    result = parse_html_schedule(html)
    assert result.startswith("| Col1 | Col2 |")
    assert "| a | b |" in result
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_html_schedule_parser.py -v`
Expected: `test_parse_aspnet_schedule_emits_structured_line` FAIL (saída ainda é tabela markdown); `test_parse_non_aspnet_html_keeps_legacy_table_format` PASS.

- [ ] **Step 3: Implementar parser ASP.NET e wire**

Editar `src/utils/helpers.py`, substituindo `parse_html_schedule` (linhas 341-378) por:

```python
def _is_aspnet_schedule(soup) -> bool:
    if soup.find(id="dgAulas"):
        return True
    import re as _re
    if soup.find("span", id=_re.compile(r"_lblData$")):
        return True
    return False


def _aspnet_row_cell(row, suffix: str) -> str:
    import re as _re
    span = row.find("span", id=_re.compile(rf"_lbl{suffix}$"))
    if not span:
        return ""
    return " ".join(span.get_text(" ", strip=True).split())


def _aspnet_row_ignored(row) -> bool:
    style = (row.get("style") or "").lower()
    # Vermelho (suspensao) e cinza-claro (pos-periodo: devolucao, G2)
    return "background-color:red" in style.replace(" ", "") or "background-color:lightgrey" in style.replace(" ", "")


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

        parts = [f"- ({data})"]
        if dia:
            parts.append(dia)
        parts.append(f"— {descricao} [{atividade}]")
        if recursos:
            parts.append(f"@{recursos}")
        if _aspnet_row_ignored(row):
            parts.append("⊘")
        lines.append(" ".join(parts))

    return "\n".join(lines) + "\n"


def parse_html_schedule(html_content: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "Erro: A biblioteca 'beautifulsoup4' não está instalada.\nUse no terminal: pip install beautifulsoup4"

    soup = BeautifulSoup(html_content, "html.parser")

    if _is_aspnet_schedule(soup):
        return _parse_aspnet_schedule(soup)

    table = soup.find("table")
    if not table:
        return "Erro: Nenhuma tabela (<table>) encontrada no HTML fornecido."

    rows = table.find_all("tr")
    if not rows:
        return "Erro: A tabela não possui linhas (<tr>)."

    output = []
    header_cells = rows[0].find_all(["th", "td"])
    headers = [c.get_text(" ", strip=True) for c in header_cells]
    if not headers:
        return "Erro: Tabela sem colunas reconhecíveis."

    output.append("| " + " | ".join(headers) + " |")
    output.append("|" + "|".join(["---"] * len(headers)) + "|")

    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        row_data = []
        for cell in cells:
            text = " ".join(cell.get_text(" ", strip=True).replace("\n", " ").replace("\r", " ").split())
            row_data.append(text)
        if any(row_data):
            output.append("| " + " | ".join(row_data) + " |")

    return "\n".join(output) + "\n"
```

- [ ] **Step 4: Rodar testes**

Run: `python -m pytest tests/test_html_schedule_parser.py -v`
Expected: PASS em ambos os testes.

- [ ] **Step 5: Commit**

```bash
git add src/utils/helpers.py tests/test_html_schedule_parser.py
git commit -m "feat(helpers): parser dedicado para cronograma ASP.NET dgAulas"
```

---

## Task 4: Linhas especiais (suspensão, devolução, recursos de laboratório)

**Files:**
- Test: `tests/test_html_schedule_parser.py` (ampliar)

Cobrir dois casos adicionais: linha com style vermelho (suspensão) → sufixo `⊘`; linha com `Recursos` preenchido → sufixo `@local`.

- [ ] **Step 1: Adicionar testes**

Acrescentar em `tests/test_html_schedule_parser.py`:

```python
ASPNET_WITH_SUSPENSION = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr style="background-color:Red;">
    <td><span id="dgAulas_ctl16_lblAula"></span></td>
    <td><span id="dgAulas_ctl16_lblDia">SEG</span></td>
    <td><span id="dgAulas_ctl16_lblData">20/04/2026</span></td>
    <td><span id="dgAulas_ctl16_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl16_lblDescricao">Suspensão de aulas</span></td>
    <td><span id="dgAulas_ctl16_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl16_lblRecursos"></span></td>
  </tr>
</table>
"""


ASPNET_WITH_RESOURCE = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr>
    <td><span id="dgAulas_ctl13_lblAula">12</span></td>
    <td><span id="dgAulas_ctl13_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl13_lblData">08/04/2026</span></td>
    <td><span id="dgAulas_ctl13_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl13_lblDescricao">Prova Interativa de Teoremas - Isabelle</span></td>
    <td><span id="dgAulas_ctl13_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl13_lblRecursos">Laboratório 409/412</span></td>
  </tr>
</table>
"""


def test_aspnet_suspension_row_gets_ignored_marker():
    result = parse_html_schedule(ASPNET_WITH_SUSPENSION)
    assert "(20/04/2026) SEG — Suspensão de aulas [Aula] ⊘" in result


def test_aspnet_row_with_resource_appends_at_marker():
    result = parse_html_schedule(ASPNET_WITH_RESOURCE)
    assert "@Laboratório 409/412" in result
    assert "— Prova Interativa de Teoremas - Isabelle [Aula]" in result
```

- [ ] **Step 2: Rodar testes**

Run: `python -m pytest tests/test_html_schedule_parser.py -v`
Expected: PASS em todos os 4 testes (implementação do Task 3 já cobre).

- [ ] **Step 3: Commit**

```bash
git add tests/test_html_schedule_parser.py
git commit -m "test(helpers): cobre linhas de suspensao e recursos no parser ASP.NET"
```

---

## Task 5: Teste de integração end-to-end

**Files:**
- Test: `tests/test_html_schedule_parser.py` (ampliar)

Garantir que a saída do parser novo, quando passada ao `extract_timeline_session_signals`, produz sessions válidas com datas corretas. Isso é o elo entre as duas mudanças e o que de fato resolve `card_evidence = 0`.

- [ ] **Step 1: Adicionar teste de integração**

Acrescentar em `tests/test_html_schedule_parser.py`:

```python
from src.builder.timeline_signals import extract_timeline_session_signals


FULL_FIXTURE = """
<table id="dgAulas">
  <tr><td>#</td><td>Dia</td><td>Data</td><td>Hora</td><td>Descrição</td><td>Atividade</td><td>Recursos</td></tr>
  <tr>
    <td><span id="dgAulas_ctl02_lblAula">1</span></td>
    <td><span id="dgAulas_ctl02_lblDia">SEG</span></td>
    <td><span id="dgAulas_ctl02_lblData">30/03/2026</span></td>
    <td><span id="dgAulas_ctl02_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl02_lblDescricao">Provas por indução</span></td>
    <td><span id="dgAulas_ctl02_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl02_lblRecursos"></span></td>
  </tr>
  <tr>
    <td><span id="dgAulas_ctl03_lblAula">2</span></td>
    <td><span id="dgAulas_ctl03_lblDia">QUA</span></td>
    <td><span id="dgAulas_ctl03_lblData">01/04/2026</span></td>
    <td><span id="dgAulas_ctl03_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl03_lblDescricao">Provas por indução: listas e árvores</span></td>
    <td><span id="dgAulas_ctl03_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl03_lblRecursos"></span></td>
  </tr>
  <tr style="background-color:Red;">
    <td><span id="dgAulas_ctl04_lblAula"></span></td>
    <td><span id="dgAulas_ctl04_lblDia">SEG</span></td>
    <td><span id="dgAulas_ctl04_lblData">20/04/2026</span></td>
    <td><span id="dgAulas_ctl04_lblHora">LM</span></td>
    <td><span id="dgAulas_ctl04_lblDescricao">Suspensão de aulas</span></td>
    <td><span id="dgAulas_ctl04_lblAtividade">Aula</span></td>
    <td><span id="dgAulas_ctl04_lblRecursos"></span></td>
  </tr>
</table>
"""


def test_parser_output_feeds_session_extractor():
    syllabus = parse_html_schedule(FULL_FIXTURE)
    sessions = extract_timeline_session_signals(syllabus)

    dates = {s["date"] for s in sessions}
    assert "2026-03-30" in dates
    assert "2026-04-01" in dates
    assert "2026-04-20" not in dates  # suspensao ignorada

    labels = " | ".join(str(s["label"]) for s in sessions)
    assert "provas por inducao" in labels
```

- [ ] **Step 2: Rodar teste**

Run: `python -m pytest tests/test_html_schedule_parser.py::test_parser_output_feeds_session_extractor -v`
Expected: PASS. Se falhar, investigar qual regex não casa e ajustar.

- [ ] **Step 3: Rodar suite completa**

Run: `python -m pytest tests/ -q`
Expected: Todos os testes existentes continuam passando + novos. Se algum teste antigo quebrar, analisar se é regressão real (regex mudou comportamento) ou se o teste precisa atualizar expectativa.

- [ ] **Step 4: Commit**

```bash
git add tests/test_html_schedule_parser.py
git commit -m "test: integracao parse_html_schedule + extract_timeline_session_signals"
```

---

## Task 6: Validação manual no app

**Files:** nenhum arquivo tocado — teste manual com repositório real.

- [ ] **Step 1: Abrir o app**

Run: `python -m src`

- [ ] **Step 2: Validar fluxo**

1. Abrir `SubjectManagerDialog` para uma disciplina que tem HTML ASP.NET do cronograma (ex. `Metodos-Formais-Tutor`).
2. Abrir `HTMLImportDialog`, colar o HTML de exemplo do spec.
3. Confirmar que o campo `syllabus` ficou preenchido com `## Cronograma de Aulas` e linhas `- (DD/MM/YYYY) DIA — título [Atividade]`.
4. Salvar perfil.
5. Menu `Repo → Reprocessar Repositório`.
6. Abrir `course/.timeline_index.json` do repositório gerado e verificar:
   - `sessions` tem entradas (>= número de aulas no cronograma descontando suspensões)
   - `card_evidence` em pelo menos um bloco passa de 0 para > 0

- [ ] **Step 3: Marcar concluído**

Se comportamento estiver correto, o plano está fechado. Se não, voltar ao Task relevante com um teste que capture a falha observada.

---

## Self-Review

**Spec coverage:**
- ✅ Seção 4 (formato de saída): Task 3 emite exatamente esse formato
- ✅ Seção 5 (detecção ASP.NET): Task 3 implementa `_is_aspnet_schedule`
- ✅ Seção 6.1 (`helpers.py`): Task 3
- ✅ Seção 6.2 (`timeline_signals.py`): Tasks 1 e 2
- ✅ Seção 6.3 (testes): Tasks 1, 2, 3, 4, 5
- ✅ Seção 10 critério 1 (saída estruturada): Task 3
- ✅ Seção 10 critério 2 (regressão HTML genérico): Task 3 step 1 (segundo teste)
- ✅ Seção 10 critério 3 (card_evidence > 0 após reprocessar): Task 5 + Task 6
- ✅ Seção 10 critério 4 (suite completa): Task 5 step 3
- ✅ Seção 10 critério 5 (⊘ ignorado): Tasks 2, 4, 5
- ⏭️ Seção 9 (bônus adiados): intencionalmente fora desta fase, conforme spec

**Placeholder scan:** nenhum TBD, TODO, "similar a", "add validation". Todo código aparece inline.

**Type consistency:** funções `_is_aspnet_schedule`, `_aspnet_row_cell`, `_aspnet_row_ignored`, `_parse_aspnet_schedule` usadas em Task 3 — todas definidas no mesmo step. Regex `_SESSION_RE` referenciado em Task 1 e usado em Task 2 — consistente.
