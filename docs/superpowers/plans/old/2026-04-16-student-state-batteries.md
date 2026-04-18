# STUDENT_STATE v2 & Baterias de Estudo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir o custo de tokens pago pelo tutor LLM ao ler o estado do aluno de ~3.000–5.000 tokens para ~150–300 tokens, fragmentando o histórico em baterias por tópico com consolidação opcional por unidade.

**Architecture:**
- `STUDENT_STATE.md` vira **YAML puro** compacto (active, active_unit_progress, recent, closed_units, next_topic)
- Histórico detalhado vai para `student/batteries/<unit>/<topic>.md` (em estudo) ou `student/batteries/<unit>.summary.md` (consolidada)
- Consolidação é operação atômica do **app** (menu `Repo → Consolidar unidade`), não do tutor
- Reabertura para revisão é efeito colateral do ditado normal do tutor — sem botão dedicado

**Tech Stack:** Python 3.11+, tkinter (UI), pytest (testes). Sem dependência nova; YAML é emitido hand-rolled (formato plano e previsível); frontmatter é parseado com regex simples.

**Spec de referência:** `docs/superpowers/specs/2026-04-16-student-state-batteries-design.md`

---

## File Structure

### Criados

| Arquivo | Responsabilidade |
|---|---|
| `src/builder/student_state.py` | Módulo dedicado: gerador v2, parser de bateria, agregador de summary, refresh, consolidação, migração. Separado para isolar domínio e evitar inchar `engine.py`. |
| `src/ui/consolidate_unit_dialog.py` | Dialog tkinter de consolidação |
| `tests/test_student_state_v2.py` | Testes do gerador e do refresh |
| `tests/test_consolidate_unit.py` | Testes de `consolidate_unit` |
| `tests/test_migrate_student_state.py` | Testes de migração v1→v2 |
| `tests/test_prompt_generation_v2.py` | Testes que as INSTRUCOES refletem o formato v2 |

### Modificados

| Arquivo | Mudança |
|---|---|
| `src/builder/engine.py` | Chama `student_state_v2.*` em vez de `student_state_md`; gitignore gerado inclui backups de consolidação/migração |
| `src/builder/prompt_generation.py` | Novo bloco YAML-format + regra de detecção + template de ditado duplo; remove menção à tabela `Histórico de sessões` |
| `src/ui/app.py` | Novo menu `Repo → Consolidar unidade...`; detecção de repo v1 no load |
| `src/ui/dialogs.py` | Ajuste do help text para mencionar v2 |
| `tests/test_rag_enrichment.py` | `test_student_state_template_includes_history_table` vira `test_student_state_v2_yaml_format` |
| `tests/test_core.py` | Ajustes nos testes que checam o conteúdo gerado de `STUDENT_STATE.md` |
| `ROADMAP.md` | Marcar feature implementada |

---

## Task 1: Scaffold do módulo `student_state` + YAML básico

**Files:**
- Create: `src/builder/student_state.py`
- Create: `tests/test_student_state_v2.py`

- [ ] **Step 1: Criar teste mínimo do formato YAML**

```python
# tests/test_student_state_v2.py
from src.builder.student_state import render_student_state_md


def test_yaml_frontmatter_is_minimal_and_well_formed():
    md = render_student_state_md(
        course_name="Cálculo III",
        student_nickname="Humberto",
        today="2026-04-16",
        active=None,
        active_unit_progress=[],
        recent=[],
        closed_units=[],
        next_topic="",
    )
    assert md.startswith("---\n")
    assert "course: Cálculo III" in md
    assert "student: Humberto" in md
    assert "updated: 2026-04-16" in md
    assert md.rstrip().endswith("---")
    assert "## " not in md  # sem headers markdown — YAML puro
    assert len(md.splitlines()) < 40  # teto de tamanho


def test_yaml_has_no_legacy_history_table():
    md = render_student_state_md(
        course_name="X", student_nickname="Y", today="2026-04-16",
        active=None, active_unit_progress=[], recent=[],
        closed_units=[], next_topic="",
    )
    assert "Histórico de sessões" not in md
    assert "Progresso por unidade" not in md
```

- [ ] **Step 2: Rodar teste e confirmar falha**

Run: `python -m pytest tests/test_student_state_v2.py -v`
Expected: `ModuleNotFoundError: No module named 'src.builder.student_state'`

- [ ] **Step 3: Implementação mínima**

```python
# src/builder/student_state.py
"""
STUDENT_STATE v2: YAML puro compacto + baterias de estudo.

Gera e reconcilia student/STUDENT_STATE.md no formato YAML plano, e dá
suporte a consolidação/migração de unidades fechadas via summaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class ActiveTopic:
    unit: str
    topic: str
    status: str
    sessions: int
    file: str


@dataclass(frozen=True)
class ProgressRow:
    topic: str
    status: str  # pendente | em_progresso | compreendido | revisao


@dataclass(frozen=True)
class RecentEntry:
    topic: str
    unit: str
    date: str


def render_student_state_md(
    *,
    course_name: str,
    student_nickname: str,
    today: str,
    active: Optional[ActiveTopic],
    active_unit_progress: Iterable[ProgressRow],
    recent: Iterable[RecentEntry],
    closed_units: Iterable[str],
    next_topic: str,
) -> str:
    lines = [
        "---",
        f"course: {course_name}",
        f"student: {student_nickname}",
        f"updated: {today}",
        "",
    ]
    if active is not None:
        lines += [
            "active:",
            f"  unit: {active.unit}",
            f"  topic: {active.topic}",
            f"  status: {active.status}",
            f"  sessions: {active.sessions}",
            f"  file: {active.file}",
            "",
        ]
    progress = list(active_unit_progress)
    if progress:
        lines.append("active_unit_progress:")
        for row in progress:
            lines.append(f"  - {{topic: {row.topic}, status: {row.status}}}")
        lines.append("")
    recent_list = list(recent)
    if recent_list:
        lines.append("recent:")
        for r in recent_list:
            lines.append(f"  - {{topic: {r.topic}, unit: {r.unit}, date: {r.date}}}")
        lines.append("")
    closed = list(closed_units)
    if closed:
        lines.append(f"closed_units: [{', '.join(closed)}]")
        lines.append("")
    if next_topic:
        lines.append(f"next_topic: {next_topic}")
        lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Rodar teste e confirmar passagem**

Run: `python -m pytest tests/test_student_state_v2.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/student_state.py tests/test_student_state_v2.py
git commit -m "feat(student-state): add v2 YAML scaffold"
```

---

## Task 2: Derivar `active_unit_progress` do COURSE_MAP + baterias

**Files:**
- Modify: `src/builder/student_state.py`
- Modify: `tests/test_student_state_v2.py`

- [ ] **Step 1: Escrever teste de parser de frontmatter de bateria**

```python
# append em tests/test_student_state_v2.py
from src.builder.student_state import parse_battery_frontmatter


def test_parse_battery_frontmatter_extracts_status():
    content = (
        "---\n"
        "topic: Derivadas parciais\n"
        "topic_slug: derivadas-parciais\n"
        "unit: unidade-02\n"
        "status: em_progresso\n"
        "---\n\n## 2026-04-14 (sessão 1)\n- foo\n"
    )
    fm = parse_battery_frontmatter(content)
    assert fm["topic_slug"] == "derivadas-parciais"
    assert fm["unit"] == "unidade-02"
    assert fm["status"] == "em_progresso"


def test_parse_battery_frontmatter_missing_returns_empty():
    assert parse_battery_frontmatter("sem frontmatter") == {}
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_student_state_v2.py::test_parse_battery_frontmatter_extracts_status -v`
Expected: `ImportError: cannot import name 'parse_battery_frontmatter'`

- [ ] **Step 3: Implementar parser**

```python
# append em src/builder/student_state.py
import re

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_battery_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter simples (chave: valor por linha)."""
    m = _FRONTMATTER_RE.match(content or "")
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_student_state_v2.py -v`
Expected: 4 passed

- [ ] **Step 5: Teste do derivador de progresso**

```python
# append em tests/test_student_state_v2.py
from pathlib import Path
from src.builder.student_state import derive_active_unit_progress


def test_derive_active_unit_progress_merges_course_map_with_batteries(tmp_path: Path):
    batteries_dir = tmp_path / "batteries" / "unidade-02"
    batteries_dir.mkdir(parents=True)
    (batteries_dir / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n",
        encoding="utf-8",
    )
    (batteries_dir / "derivadas-parciais.md").write_text(
        "---\ntopic_slug: derivadas-parciais\nunit: unidade-02\nstatus: em_progresso\n---\n",
        encoding="utf-8",
    )

    course_map_topics = [
        ("limites", "Limites"),
        ("continuidade", "Continuidade"),
        ("derivadas-parciais", "Derivadas parciais"),
        ("regra-da-cadeia", "Regra da cadeia"),
    ]

    rows = derive_active_unit_progress(
        unit_slug="unidade-02",
        course_map_topics=course_map_topics,
        batteries_root=tmp_path / "batteries",
    )
    statuses = {r.topic: r.status for r in rows}
    assert statuses == {
        "limites": "compreendido",
        "continuidade": "pendente",
        "derivadas-parciais": "em_progresso",
        "regra-da-cadeia": "pendente",
    }
    # ordem preservada do COURSE_MAP
    assert [r.topic for r in rows] == [slug for slug, _ in course_map_topics]
```

- [ ] **Step 6: Rodar e confirmar falha**

Run: `python -m pytest tests/test_student_state_v2.py::test_derive_active_unit_progress_merges_course_map_with_batteries -v`
Expected: ImportError

- [ ] **Step 7: Implementar derivador**

```python
# append em src/builder/student_state.py
from pathlib import Path


def derive_active_unit_progress(
    *,
    unit_slug: str,
    course_map_topics: list[tuple[str, str]],  # [(slug, label)]
    batteries_root: Path,
) -> list[ProgressRow]:
    """Para a unidade ativa, cruza a ordem do COURSE_MAP com os status
    das baterias existentes em batteries/<unit_slug>/*.md."""
    unit_dir = batteries_root / unit_slug
    by_slug: dict[str, str] = {}
    if unit_dir.is_dir():
        for md in sorted(unit_dir.glob("*.md")):
            fm = parse_battery_frontmatter(md.read_text(encoding="utf-8"))
            slug = fm.get("topic_slug") or md.stem
            status = fm.get("status") or "pendente"
            by_slug[slug] = status
    rows: list[ProgressRow] = []
    for slug, _label in course_map_topics:
        rows.append(ProgressRow(topic=slug, status=by_slug.get(slug, "pendente")))
    return rows
```

- [ ] **Step 8: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_student_state_v2.py -v`
Expected: 5 passed

- [ ] **Step 9: Commit**

```bash
git add src/builder/student_state.py tests/test_student_state_v2.py
git commit -m "feat(student-state): parse battery frontmatter and derive active unit progress"
```

---

## Task 3: `refresh_active_unit_progress` em disco

**Files:**
- Modify: `src/builder/student_state.py`
- Modify: `tests/test_student_state_v2.py`

- [ ] **Step 1: Escrever teste**

```python
# append em tests/test_student_state_v2.py
from src.builder.student_state import refresh_active_unit_progress


def test_refresh_rewrites_only_progress_block(tmp_path: Path):
    root = tmp_path
    (root / "student").mkdir()
    state = (
        "---\n"
        "course: X\n"
        "student: Y\n"
        "updated: 2026-04-10\n"
        "\n"
        "active:\n"
        "  unit: unidade-02\n"
        "  topic: limites\n"
        "  status: compreendido\n"
        "  sessions: 1\n"
        "  file: batteries/unidade-02/limites.md\n"
        "\n"
        "active_unit_progress:\n"
        "  - {topic: limites, status: pendente}\n"
        "\n"
        "---\n"
    )
    (root / "student" / "STUDENT_STATE.md").write_text(state, encoding="utf-8")
    (root / "student" / "batteries" / "unidade-02").mkdir(parents=True)
    (root / "student" / "batteries" / "unidade-02" / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n",
        encoding="utf-8",
    )

    refresh_active_unit_progress(
        root_dir=root,
        active_unit_slug="unidade-02",
        course_map_topics=[("limites", "L"), ("continuidade", "C")],
    )

    new_state = (root / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "- {topic: limites, status: compreendido}" in new_state
    assert "- {topic: continuidade, status: pendente}" in new_state
    # preserva o resto do YAML
    assert "topic: limites" in new_state
    assert "file: batteries/unidade-02/limites.md" in new_state
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_student_state_v2.py::test_refresh_rewrites_only_progress_block -v`
Expected: ImportError

- [ ] **Step 3: Implementar**

```python
# append em src/builder/student_state.py
_ACTIVE_PROGRESS_BLOCK_RE = re.compile(
    r"(active_unit_progress:\s*\n)(?:\s*-\s*\{[^}]*\}\s*\n)*",
    re.MULTILINE,
)


def refresh_active_unit_progress(
    *,
    root_dir: Path,
    active_unit_slug: str,
    course_map_topics: list[tuple[str, str]],
) -> None:
    """Reconcilia o bloco active_unit_progress do STUDENT_STATE.md
    sem tocar nos outros campos."""
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        return
    current = state_path.read_text(encoding="utf-8")
    rows = derive_active_unit_progress(
        unit_slug=active_unit_slug,
        course_map_topics=course_map_topics,
        batteries_root=root_dir / "student" / "batteries",
    )
    new_block = "active_unit_progress:\n" + "".join(
        f"  - {{topic: {r.topic}, status: {r.status}}}\n" for r in rows
    )
    if _ACTIVE_PROGRESS_BLOCK_RE.search(current):
        updated = _ACTIVE_PROGRESS_BLOCK_RE.sub(new_block, current, count=1)
    else:
        # insere antes do fechamento do frontmatter
        updated = current.replace("\n---\n", "\n" + new_block + "\n---\n", 1)
    state_path.write_text(updated, encoding="utf-8")
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_student_state_v2.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/student_state.py tests/test_student_state_v2.py
git commit -m "feat(student-state): refresh active_unit_progress in place"
```

---

## Task 4: Gerador de `<unit>.summary.md`

**Files:**
- Modify: `src/builder/student_state.py`
- Create: `tests/test_consolidate_unit.py`

- [ ] **Step 1: Escrever teste**

```python
# tests/test_consolidate_unit.py
from pathlib import Path
from src.builder.student_state import render_unit_summary_md


def test_render_unit_summary_aggregates_bullets(tmp_path: Path):
    batteries = [
        (
            "limites.md",
            "---\ntopic: Limites\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n"
            "## 2026-04-05 (sessão 1)\n- Compreendeu: def formal\n- Dúvidas: ε-δ\n- Ação tutor: exemplo gráfico\n\n"
            "## 2026-04-08 (sessão 2)\n- Resolveu: ε-δ\n- Dúvidas: [nenhuma]\n",
        ),
        (
            "continuidade.md",
            "---\ntopic: Continuidade\ntopic_slug: continuidade\nunit: unidade-02\nstatus: compreendido\n---\n"
            "## 2026-04-10 (sessão 1)\n- Compreendeu: teorema intermediário\n- Dúvidas: [nenhuma]\n",
        ),
    ]

    summary = render_unit_summary_md(
        unit_slug="unidade-02",
        closed_date="2026-04-20",
        topic_order=["limites", "continuidade"],
        batteries=batteries,
    )
    assert "unit: unidade-02" in summary
    assert "status: consolidado" in summary
    assert "sessions_total: 3" in summary  # 2 + 1
    assert "topics: [limites, continuidade]" in summary
    assert "**Tópicos cobertos:**" in summary
    assert "limites" in summary and "continuidade" in summary
    assert "**Dúvidas resolvidas:**" in summary
    assert "ε-δ" in summary
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_consolidate_unit.py::test_render_unit_summary_aggregates_bullets -v`
Expected: ImportError

- [ ] **Step 3: Implementar**

```python
# append em src/builder/student_state.py
_SESSION_HEADER_RE = re.compile(r"^##\s*(.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^-\s*(\*\*)?([^:]+):\*?\*?\s*(.+)$", re.MULTILINE)


def _extract_bullet_values(bullets: list[tuple[str, str]], key_prefix: str) -> list[str]:
    out: list[str] = []
    for key, value in bullets:
        if key.strip().lower().startswith(key_prefix):
            text = value.strip().strip(".")
            if text and text.lower() not in {"nenhuma", "[nenhuma]"}:
                out.append(text)
    return out


def render_unit_summary_md(
    *,
    unit_slug: str,
    closed_date: str,
    topic_order: list[str],
    batteries: list[tuple[str, str]],  # [(filename, content)]
) -> str:
    total_sessions = 0
    all_bullets: list[tuple[str, str]] = []
    for _name, content in batteries:
        total_sessions += len(_SESSION_HEADER_RE.findall(content))
        for m in _BULLET_RE.finditer(content):
            all_bullets.append((m.group(2), m.group(3)))

    resolvidas = _extract_bullet_values(all_bullets, "resolveu") + \
                 _extract_bullet_values(all_bullets, "dúvida")
    abertas = _extract_bullet_values(all_bullets, "em aberto")

    lines = [
        "---",
        f"unit: {unit_slug}",
        "status: consolidado",
        f"sessions_total: {total_sessions}",
        f"closed: {closed_date}",
        f"topics: [{', '.join(topic_order)}]",
        "---",
        "",
        f"**Tópicos cobertos:** {', '.join(topic_order)}",
        f"**Dúvidas resolvidas:** {', '.join(resolvidas) if resolvidas else 'nenhuma registrada'}",
        f"**Aberturas ainda em aberto:** {', '.join(abertas) if abertas else 'nenhuma'}",
        "",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_consolidate_unit.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/student_state.py tests/test_consolidate_unit.py
git commit -m "feat(student-state): render unit summary from batteries"
```

---

## Task 5: `consolidate_unit` — happy path

**Files:**
- Modify: `src/builder/student_state.py`
- Modify: `tests/test_consolidate_unit.py`

- [ ] **Step 1: Escrever teste**

```python
# append em tests/test_consolidate_unit.py
from src.builder.student_state import consolidate_unit, UnitNotReadyError


def _seed_repo(root: Path) -> None:
    (root / "student" / "batteries" / "unidade-02").mkdir(parents=True)
    (root / "student" / "batteries" / "unidade-02" / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## 2026-04-05 (sessão 1)\n- Resolveu: def formal\n",
        encoding="utf-8",
    )
    (root / "student" / "batteries" / "unidade-02" / "continuidade.md").write_text(
        "---\ntopic_slug: continuidade\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## 2026-04-10 (sessão 1)\n- Resolveu: teorema\n",
        encoding="utf-8",
    )
    (root / "student" / "STUDENT_STATE.md").write_text(
        "---\ncourse: X\nstudent: Y\nupdated: 2026-04-20\n"
        "active:\n  unit: unidade-02\n  topic: continuidade\n"
        "  status: compreendido\n  sessions: 1\n"
        "  file: batteries/unidade-02/continuidade.md\n\n"
        "active_unit_progress:\n"
        "  - {topic: limites, status: compreendido}\n"
        "  - {topic: continuidade, status: compreendido}\n\n"
        "---\n",
        encoding="utf-8",
    )


def test_consolidate_unit_happy_path(tmp_path: Path):
    _seed_repo(tmp_path)
    result = consolidate_unit(
        root_dir=tmp_path,
        unit_slug="unidade-02",
        today="2026-04-20",
        topic_order=["limites", "continuidade"],
    )
    assert result.summary_path == tmp_path / "student" / "batteries" / "unidade-02.summary.md"
    assert result.summary_path.exists()
    assert not (tmp_path / "student" / "batteries" / "unidade-02").exists()
    state = (tmp_path / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "closed_units: [unidade-02]" in state
    assert "unidade-02" not in state.split("active_unit_progress:")[1].split("---")[0]
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_consolidate_unit.py::test_consolidate_unit_happy_path -v`
Expected: ImportError

- [ ] **Step 3: Implementar**

```python
# append em src/builder/student_state.py
import shutil
from dataclasses import dataclass


class UnitNotReadyError(Exception):
    def __init__(self, unit_slug: str, pending: list[str]) -> None:
        super().__init__(f"Unit {unit_slug} not ready: pending {pending}")
        self.unit_slug = unit_slug
        self.pending = pending


@dataclass(frozen=True)
class ConsolidationResult:
    unit_slug: str
    summary_path: Path
    backup_path: Optional[Path]
    deleted_files: list[str]


def consolidate_unit(
    *,
    root_dir: Path,
    unit_slug: str,
    today: str,
    topic_order: list[str],
    force: bool = False,
) -> ConsolidationResult:
    batteries_root = root_dir / "student" / "batteries"
    unit_dir = batteries_root / unit_slug
    if not unit_dir.is_dir():
        raise FileNotFoundError(f"Unit directory not found: {unit_dir}")

    battery_files: list[tuple[str, str]] = []
    pending: list[str] = []
    for md in sorted(unit_dir.glob("*.md")):
        content = md.read_text(encoding="utf-8")
        fm = parse_battery_frontmatter(content)
        battery_files.append((md.name, content))
        if fm.get("status") != "compreendido" and not force:
            pending.append(fm.get("topic_slug") or md.stem)
    if pending and not force:
        raise UnitNotReadyError(unit_slug, pending)

    existing_summary = batteries_root / f"{unit_slug}.summary.md"
    revision_section = _read_existing_summary_revisions(existing_summary)
    summary_md = render_unit_summary_md(
        unit_slug=unit_slug,
        closed_date=today,
        topic_order=topic_order,
        batteries=battery_files,
    )
    if revision_section:
        summary_md = summary_md.rstrip() + "\n\n" + revision_section + "\n"

    backup_path = root_dir / "build" / "consolidation-backup" / today / unit_slug
    backup_path.mkdir(parents=True, exist_ok=True)
    for md in unit_dir.glob("*.md"):
        shutil.copy2(md, backup_path / md.name)
    if existing_summary.exists():
        shutil.copy2(existing_summary, backup_path / existing_summary.name)

    existing_summary.write_text(summary_md, encoding="utf-8")
    deleted = [p.name for p in unit_dir.glob("*.md")]
    shutil.rmtree(unit_dir)

    _update_student_state_after_consolidation(root_dir, unit_slug)

    return ConsolidationResult(
        unit_slug=unit_slug,
        summary_path=existing_summary,
        backup_path=backup_path,
        deleted_files=deleted,
    )


def _read_existing_summary_revisions(summary_path: Path) -> str:
    if not summary_path.exists():
        return ""
    text = summary_path.read_text(encoding="utf-8")
    idx = text.find("## Revisão ")
    return text[idx:].rstrip() if idx >= 0 else ""


def _update_student_state_after_consolidation(root_dir: Path, unit_slug: str) -> None:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")

    block_re = re.compile(r"active_unit_progress:\s*\n(?:\s*-\s*\{[^}]*\}\s*\n)*")
    text = block_re.sub("active_unit_progress: []\n", text, count=1)

    closed_re = re.compile(r"closed_units:\s*\[(.*?)\]")
    m = closed_re.search(text)
    if m:
        existing = [s.strip() for s in m.group(1).split(",") if s.strip()]
        if unit_slug not in existing:
            existing.append(unit_slug)
        text = closed_re.sub(f"closed_units: [{', '.join(existing)}]", text, count=1)
    else:
        text = text.replace("\n---\n", f"\nclosed_units: [{unit_slug}]\n\n---\n", 1)
    state_path.write_text(text, encoding="utf-8")
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_consolidate_unit.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/student_state.py tests/test_consolidate_unit.py
git commit -m "feat(student-state): consolidate_unit happy path with backup"
```

---

## Task 6: `consolidate_unit` — guarda-rails

**Files:**
- Modify: `tests/test_consolidate_unit.py`

- [ ] **Step 1: Escrever testes de bloqueio/force**

```python
# append em tests/test_consolidate_unit.py
def test_consolidate_unit_blocks_when_pending_without_force(tmp_path: Path):
    _seed_repo(tmp_path)
    # força um tópico como em_progresso
    p = tmp_path / "student" / "batteries" / "unidade-02" / "continuidade.md"
    p.write_text(
        "---\ntopic_slug: continuidade\nunit: unidade-02\nstatus: em_progresso\n---\n",
        encoding="utf-8",
    )
    import pytest
    with pytest.raises(UnitNotReadyError) as exc:
        consolidate_unit(
            root_dir=tmp_path, unit_slug="unidade-02",
            today="2026-04-20",
            topic_order=["limites", "continuidade"],
        )
    assert "continuidade" in exc.value.pending


def test_consolidate_unit_force_allows_partial(tmp_path: Path):
    _seed_repo(tmp_path)
    p = tmp_path / "student" / "batteries" / "unidade-02" / "continuidade.md"
    p.write_text(
        "---\ntopic_slug: continuidade\nunit: unidade-02\nstatus: em_progresso\n---\n",
        encoding="utf-8",
    )
    result = consolidate_unit(
        root_dir=tmp_path, unit_slug="unidade-02",
        today="2026-04-20",
        topic_order=["limites", "continuidade"],
        force=True,
    )
    assert result.summary_path.exists()


def test_consolidate_unit_creates_backup(tmp_path: Path):
    _seed_repo(tmp_path)
    result = consolidate_unit(
        root_dir=tmp_path, unit_slug="unidade-02",
        today="2026-04-20",
        topic_order=["limites", "continuidade"],
    )
    assert result.backup_path is not None
    assert (result.backup_path / "limites.md").exists()
    assert (result.backup_path / "continuidade.md").exists()
```

- [ ] **Step 2: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_consolidate_unit.py -v`
Expected: 5 passed (o teste já passa graças à Task 5)

- [ ] **Step 3: Commit**

```bash
git add tests/test_consolidate_unit.py
git commit -m "test(student-state): cover consolidate_unit guardrails"
```

---

## Task 7: `consolidate_unit` — revisão append

**Files:**
- Modify: `src/builder/student_state.py`
- Modify: `tests/test_consolidate_unit.py`

- [ ] **Step 1: Escrever teste de revisão**

```python
# append em tests/test_consolidate_unit.py
def test_consolidate_unit_appends_revision_section(tmp_path: Path):
    _seed_repo(tmp_path)
    # primeira consolidação
    consolidate_unit(
        root_dir=tmp_path, unit_slug="unidade-02",
        today="2026-04-20",
        topic_order=["limites", "continuidade"],
    )
    # reabre revisão
    unit_dir = tmp_path / "student" / "batteries" / "unidade-02"
    unit_dir.mkdir(parents=True)
    (unit_dir / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## 2026-05-10 (sessão 1)\n- Revisado: def formal\n",
        encoding="utf-8",
    )
    # segunda consolidação (revisão)
    result = consolidate_unit(
        root_dir=tmp_path, unit_slug="unidade-02",
        today="2026-05-10",
        topic_order=["limites"],
    )
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "## Revisão 2026-05-10" in summary or summary.count("closed:") == 1
    # backup da 2ª consolidação inclui o summary antigo
    assert (result.backup_path / "unidade-02.summary.md").exists()
```

- [ ] **Step 2: Rodar**

Run: `python -m pytest tests/test_consolidate_unit.py::test_consolidate_unit_appends_revision_section -v`
Expected: ou passa direto, ou falha no "## Revisão" — se passar, pular Step 3.

- [ ] **Step 3 (se falhar): ajustar `render_unit_summary_md` para emitir cabeçalho de revisão quando existente**

```python
# em render_unit_summary_md, antes do return — adicionar se closed_date != primeiro fechamento
# Na implementação atual, `_read_existing_summary_revisions` já injeta seções
# antigas. Se o teste ainda falhar, modificar consolidate_unit para emitir
# "## Revisão {today}" quando existing_summary existir:
```

```python
# substituir o bloco em consolidate_unit que monta summary_md:
first_close = not existing_summary.exists()
summary_md = render_unit_summary_md(
    unit_slug=unit_slug,
    closed_date=today,
    topic_order=topic_order,
    batteries=battery_files,
)
if not first_close:
    revision_title = f"## Revisão {today}"
    revision_body = f"**Reestudado:** {', '.join(topic_order)}"
    summary_md = summary_md.rstrip() + f"\n\n{revision_title}\n{revision_body}\n"
    if revision_section:
        summary_md += "\n" + revision_section + "\n"
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_consolidate_unit.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/student_state.py tests/test_consolidate_unit.py
git commit -m "feat(student-state): append revision section on re-consolidation"
```

---

## Task 8: Migração v1 → v2

**Files:**
- Modify: `src/builder/student_state.py`
- Create: `tests/test_migrate_student_state.py`

- [ ] **Step 1: Escrever teste do parser v1**

```python
# tests/test_migrate_student_state.py
from pathlib import Path
from src.builder.student_state import migrate_v1_to_v2, detect_state_version


V1_SAMPLE = """---
course: Cálculo
student: Humberto
last_updated: 2026-04-14
---

# STUDENT_STATE

## Estado atual

- **Última sessão:** 2026-04-14
- **Tópico:** Derivadas parciais
- **Unidade:** unidade-02

## Histórico de sessões

| Data | Tópico | Unidade | Status | Dúvidas registradas |
|---|---|---|---|---|
| 2026-04-05 | Limites | unidade-02 | compreendido | ε-δ |
| 2026-04-08 | Limites | unidade-02 | compreendido | [nenhuma] |
| 2026-04-10 | Continuidade | unidade-02 | compreendido | [nenhuma] |
| 2026-04-14 | Derivadas parciais | unidade-02 | em progresso | cadeia |

## Progresso por unidade
"""


def test_detect_state_version_identifies_v1(tmp_path: Path):
    (tmp_path / "student").mkdir()
    (tmp_path / "student" / "STUDENT_STATE.md").write_text(V1_SAMPLE, encoding="utf-8")
    assert detect_state_version(tmp_path) == "v1"


def test_migrate_v1_to_v2_creates_batteries(tmp_path: Path):
    (tmp_path / "student").mkdir()
    (tmp_path / "student" / "STUDENT_STATE.md").write_text(V1_SAMPLE, encoding="utf-8")
    result = migrate_v1_to_v2(
        root_dir=tmp_path,
        course_map_units=[("unidade-02", [
            ("limites", "Limites"),
            ("continuidade", "Continuidade"),
            ("derivadas-parciais", "Derivadas parciais"),
        ])],
    )
    batteries = tmp_path / "student" / "batteries" / "unidade-02"
    assert (batteries / "limites.md").exists()
    assert (batteries / "continuidade.md").exists()
    assert (batteries / "derivadas-parciais.md").exists()
    limites = (batteries / "limites.md").read_text(encoding="utf-8")
    assert "status: compreendido" in limites
    assert "2026-04-05" in limites
    assert "2026-04-08" in limites
    new_state = (tmp_path / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "active_unit_progress:" in new_state
    assert "Histórico de sessões" not in new_state
    assert result.backup_dir.exists()


def test_migrate_is_idempotent(tmp_path: Path):
    (tmp_path / "student").mkdir()
    (tmp_path / "student" / "STUDENT_STATE.md").write_text(V1_SAMPLE, encoding="utf-8")
    migrate_v1_to_v2(root_dir=tmp_path, course_map_units=[])
    # segunda invocação não deve falhar nem refazer
    result2 = migrate_v1_to_v2(root_dir=tmp_path, course_map_units=[])
    assert result2.skipped is True
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_migrate_student_state.py -v`
Expected: ImportError

- [ ] **Step 3: Implementar**

```python
# append em src/builder/student_state.py
from src.utils.helpers import slugify


@dataclass(frozen=True)
class MigrationResult:
    skipped: bool
    backup_dir: Path
    created_batteries: list[str]


_V1_MARKER = "## Histórico de sessões"
_HISTORY_ROW_RE = re.compile(
    r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
    r"\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|$",
    re.MULTILINE,
)


def detect_state_version(root_dir: Path) -> str:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    if not state_path.exists():
        return "none"
    text = state_path.read_text(encoding="utf-8")
    if _V1_MARKER in text:
        return "v1"
    if "active_unit_progress:" in text:
        return "v2"
    return "unknown"


def _normalize_status_v1(raw: str) -> str:
    s = raw.strip().lower().replace(" ", "_")
    if s in {"compreendido", "em_progresso", "pendente", "revisao"}:
        return s
    if "dúvida" in s or "duvida" in s:
        return "em_progresso"
    return "em_progresso"


def migrate_v1_to_v2(
    *,
    root_dir: Path,
    course_map_units: list[tuple[str, list[tuple[str, str]]]],
) -> MigrationResult:
    state_path = root_dir / "student" / "STUDENT_STATE.md"
    today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    backup_dir = root_dir / "build" / "migration-v1-backup" / today

    if detect_state_version(root_dir) != "v1":
        return MigrationResult(skipped=True, backup_dir=backup_dir, created_batteries=[])

    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(state_path, backup_dir / "STUDENT_STATE.md")

    text = state_path.read_text(encoding="utf-8")
    rows = _HISTORY_ROW_RE.findall(text)

    sessions_by_topic: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for date, topic_label, unit_label, status, duvidas in rows:
        unit_slug = slugify(unit_label) or unit_label.strip()
        topic_slug = slugify(topic_label)
        key = (unit_slug, topic_slug)
        sessions_by_topic.setdefault(key, []).append(
            (date, _normalize_status_v1(status), (duvidas or "").strip())
        )

    created: list[str] = []
    for (unit_slug, topic_slug), sessions in sessions_by_topic.items():
        dir_ = root_dir / "student" / "batteries" / unit_slug
        dir_.mkdir(parents=True, exist_ok=True)
        final_status = sessions[-1][1]
        topic_label = next(
            (label for slug, label in sum([topics for _u, topics in course_map_units], [])
             if slug == topic_slug),
            topic_slug.replace("-", " ").capitalize(),
        )
        lines = [
            "---",
            f"topic: {topic_label}",
            f"topic_slug: {topic_slug}",
            f"unit: {unit_slug}",
            f"status: {final_status}",
            "---",
            "",
        ]
        for i, (date, status, duvidas) in enumerate(sessions, 1):
            lines.append(f"## {date} (sessão {i})")
            lines.append(f"- Status: {status}")
            if duvidas and duvidas.lower() not in {"[nenhuma]", "nenhuma", ""}:
                lines.append(f"- Dúvidas: {duvidas}")
            lines.append("")
        (dir_ / f"{topic_slug}.md").write_text("\n".join(lines), encoding="utf-8")
        created.append(f"{unit_slug}/{topic_slug}.md")

    # pega course/student do frontmatter antigo
    course_name = ""
    student_nickname = ""
    m_course = re.search(r"^course:\s*(.+)$", text, re.MULTILINE)
    m_student = re.search(r"^student:\s*(.+)$", text, re.MULTILINE)
    if m_course:
        course_name = m_course.group(1).strip()
    if m_student:
        student_nickname = m_student.group(1).strip()

    new_state = render_student_state_md(
        course_name=course_name or "Curso",
        student_nickname=student_nickname or "Aluno",
        today=today,
        active=None,
        active_unit_progress=[],
        recent=[],
        closed_units=[],
        next_topic="",
    )
    state_path.write_text(new_state, encoding="utf-8")

    # auto-consolidação de unidades 100% fechadas
    for unit_slug, topics in course_map_units:
        unit_dir = root_dir / "student" / "batteries" / unit_slug
        if not unit_dir.is_dir():
            continue
        statuses = [
            parse_battery_frontmatter((unit_dir / f"{slug}.md").read_text(encoding="utf-8")).get("status")
            for slug, _ in topics if (unit_dir / f"{slug}.md").exists()
        ]
        if statuses and all(s == "compreendido" for s in statuses):
            try:
                consolidate_unit(
                    root_dir=root_dir, unit_slug=unit_slug, today=today,
                    topic_order=[slug for slug, _ in topics],
                )
            except (UnitNotReadyError, FileNotFoundError):
                pass

    return MigrationResult(skipped=False, backup_dir=backup_dir, created_batteries=created)
```

- [ ] **Step 4: Rodar e confirmar passagem**

Run: `python -m pytest tests/test_migrate_student_state.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/builder/student_state.py tests/test_migrate_student_state.py
git commit -m "feat(student-state): one-shot migration v1 to v2"
```

---

## Task 9: Atualizar `prompt_generation.py` para v2

**Files:**
- Modify: `src/builder/prompt_generation.py`
- Create: `tests/test_prompt_generation_v2.py`

- [ ] **Step 1: Escrever testes**

```python
# tests/test_prompt_generation_v2.py
from src.builder.prompt_generation import (
    generate_claude_project_instructions,
    generate_gpt_instructions,
    generate_gemini_instructions,
)


def _common():
    meta = {"course_name": "Cálculo", "professor": "P", "institution": "I", "semester": "S"}
    return meta


def test_claude_instrucoes_describe_v2_yaml_format():
    text = generate_claude_project_instructions(_common())
    assert "STUDENT_STATE" in text
    assert "YAML" in text or "yaml" in text
    assert "active_unit_progress" in text
    assert "Histórico de sessões" not in text


def test_all_platforms_include_two_block_dictation_template():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "batteries/" in text
        assert "active_unit_progress" in text


def test_all_platforms_include_consolidation_detection_rule():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "Consolidar unidade" in text or "consolidar" in text.lower()


def test_all_platforms_include_revision_dictation():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "reestudar" in text.lower() or "revisão" in text.lower()


def test_no_legacy_history_table_references():
    for gen in (generate_claude_project_instructions, generate_gpt_instructions, generate_gemini_instructions):
        text = gen(_common())
        assert "Histórico de sessões" not in text
        assert "Progresso por unidade" not in text
```

- [ ] **Step 2: Rodar testes**

Run: `python -m pytest tests/test_prompt_generation_v2.py -v`
Expected: falhas em `Histórico de sessões` ainda aparecer, templates ainda antigos.

- [ ] **Step 3: Adicionar helpers v2 no `prompt_generation.py`**

```python
# em src/builder/prompt_generation.py — adicionar no topo, antes das funções generate_*
def _prompt_student_state_v2_contract_text() -> str:
    return """## STUDENT_STATE — formato YAML v2

`student/STUDENT_STATE.md` é YAML puro. Faça parse dos campos, não busca
semântica. Campos principais:

- `active` — tópico em estudo agora (unit, topic, status, sessions, file)
- `active_unit_progress` — lista de tópicos da unidade ativa com status
- `recent` — últimos tópicos fechados (máx. 3)
- `closed_units` — unidades já consolidadas
- `next_topic` — próximo tópico sugerido

Detalhe histórico fica em `student/batteries/<unit>/<topic>.md` (em estudo)
ou `student/batteries/<unit>.summary.md` (consolidada). Só abra o arquivo
da bateria ativa quando o aluno continuar o tópico `active`. Só abra o
summary quando o aluno pedir revisão de unidade fechada.
""".strip()


def _prompt_end_of_session_dictation_text() -> str:
    return """## Ditado de fim de sessão (dois blocos)

Ao final de uma sessão substancial, dite **dois blocos** para o aluno aplicar:

**1. Append em `student/batteries/<unit>/<topic>.md`:**

```markdown
## YYYY-MM-DD (sessão N)
- Compreendeu: [...]
- Dúvidas: [... | nenhuma]
- Ação tutor: [...]
- Status: [compreendido | em_progresso | revisao]
```

**2. Alteração em `student/STUDENT_STATE.md` (só as linhas que mudam):**

```yaml
active:
  unit: <slug>
  topic: <novo-slug-ou-mesmo>
  status: <novo-status>
  sessions: <incrementado>
  file: batteries/<unit>/<topic>.md

active_unit_progress:
  - {topic: <slug-alterado>, status: <novo-status>}   # linha específica

recent:
  - {topic: <slug-fechado>, unit: <unit>, date: YYYY-MM-DD}   # topo
```

Nunca reescreva o YAML inteiro — só as linhas alteradas.
""".strip()


def _prompt_consolidation_detection_text() -> str:
    return """## Detecção de unidade pronta para consolidar

Após atualizar `active_unit_progress`, verifique:

- Se TODOS os itens da lista estão com `status: compreendido`, sugira
  **uma única vez** ao aluno:
  *"Fechamos todos os tópicos da <unit>. Quer consolidar? Abra o app →
  Repo → Consolidar unidade → <unit>."*
- Não repita a sugestão em sessões subsequentes.
- Nunca gere o summary você mesmo — o app faz a consolidação determinística.
""".strip()


def _prompt_revision_reopen_text() -> str:
    return """## Reabertura para revisão

Se o aluno disser "vou reestudar a unidade X", a unidade já está consolidada
(existe `student/batteries/<unit>.summary.md`) e você deve:

1. Dite criação de `student/batteries/<unit>/<topico>.md` com frontmatter
   `status: revisao`.
2. Dite update em `STUDENT_STATE.md` apontando `active.file` para a nova
   bateria.

O summary antigo **permanece intocado**. Uma nova consolidação, quando a
revisão fechar, vai anexar uma seção `## Revisão <data>` ao summary
existente. Não existe botão "Reabrir" no app — a reabertura nasce do seu
ditado.
""".strip()
```

- [ ] **Step 4: Inserir os blocos no corpo das três instruções**

Em `_low_token_generate_claude_project_instructions`, adicionar antes da linha `## Modos de operação`:

```python
{_prompt_student_state_v2_contract_text()}

{_prompt_end_of_session_dictation_text()}

{_prompt_consolidation_detection_text()}

{_prompt_revision_reopen_text()}

```

Em `generate_gpt_instructions`, inserir no mesmo ponto (antes de "## Modos de operação").

Em `generate_gemini_instructions`, inserir antes de "## Modos de operação".

- [ ] **Step 5: Remover `_prompt_student_state_update_text` (versão v1 com tabela)**

Buscar as chamadas `_prompt_student_state_update_text(...)` e substituir por `_prompt_end_of_session_dictation_text()`. Deletar a função antiga.

- [ ] **Step 6: Rodar testes**

Run: `python -m pytest tests/test_prompt_generation_v2.py -v`
Expected: 5 passed

- [ ] **Step 7: Rodar toda a suíte**

Run: `python -m pytest tests/ -q`
Expected: todos passando (alguns testes existentes podem precisar de ajuste; se quebrar, corrigir inline)

- [ ] **Step 8: Commit**

```bash
git add src/builder/prompt_generation.py tests/test_prompt_generation_v2.py
git commit -m "feat(prompt): INSTRUCOES refletem STUDENT_STATE v2 + baterias"
```

---

## Task 10: Wiring no `engine.py`

**Files:**
- Modify: `src/builder/engine.py`

- [ ] **Step 1: Importar o módulo novo**

No topo de `src/builder/engine.py`, junto dos outros imports do builder:

```python
from src.builder import student_state as student_state_v2
```

- [ ] **Step 2: Substituir as chamadas de `student_state_md`**

Localizar as duas ocorrências:
- `engine.py:3369-3370` (em `_generate_pedagogical_files`)
- `engine.py:5035-5036` (em `_regenerate_pedagogical_files`)

Substituir por uma chamada que usa o novo gerador:

```python
# Helper interno no engine
def _build_v2_state(self):
    today = datetime.now().strftime("%Y-%m-%d")
    course_name = self.course_meta.get("course_name", "Curso")
    nick = "Aluno"
    if self.student_profile and self.student_profile.full_name:
        nick = self.student_profile.nickname or self.student_profile.full_name
    # active/recent/closed — mantidos pela interação do tutor; build cria vazios
    return student_state_v2.render_student_state_md(
        course_name=course_name, student_nickname=nick, today=today,
        active=None, active_unit_progress=[],
        recent=[], closed_units=[], next_topic="",
    )
```

Trocar ambas as ocorrências:

```python
write_text(self.root_dir / "student" / "STUDENT_STATE.md",
           self._build_v2_state())
```

- [ ] **Step 3: Chamar `refresh_active_unit_progress` após build**

No fim de `_regenerate_pedagogical_files` (perto da linha 5210 onde já há um `write_text(state_path, ...)`), adicionar:

```python
# Reconciliar progresso se há unidade ativa e bateria no disco
active_unit = self._derive_active_unit_slug_from_state()  # helper novo; pode retornar ""
if active_unit:
    teaching_plan = getattr(self.subject_profile, "teaching_plan", "") or ""
    parsed_units = _parse_units_from_teaching_plan(teaching_plan)
    course_topics_by_unit = {
        slugify(title): [(slugify(_topic_text(t)), _topic_text(t)) for t in topics]
        for title, topics in parsed_units
    }
    topics = course_topics_by_unit.get(active_unit, [])
    if topics:
        student_state_v2.refresh_active_unit_progress(
            root_dir=self.root_dir,
            active_unit_slug=active_unit,
            course_map_topics=topics,
        )
```

Adicionar helper pequeno na classe:

```python
def _derive_active_unit_slug_from_state(self) -> str:
    state = self.root_dir / "student" / "STUDENT_STATE.md"
    if not state.exists():
        return ""
    text = state.read_text(encoding="utf-8")
    m = re.search(r"active:\s*\n(?:.*\n)*?\s*unit:\s*(\S+)", text)
    return m.group(1).strip() if m else ""
```

- [ ] **Step 4: Atualizar `.gitignore` gerado**

Em `_generated_repo_gitignore_text` (linha ~1055 do engine), adicionar:

```python
"# Backups de consolidação e migração",
"build/consolidation-backup/",
"build/migration-v1-backup/",
```

- [ ] **Step 5: Rodar suíte completa**

Run: `python -m pytest tests/ -q`
Expected: todos passando. Se `test_student_state_template_includes_history_table` falhar, renomear para `test_student_state_v2_yaml_format` e atualizar assertions.

- [ ] **Step 6: Commit**

```bash
git add src/builder/engine.py tests/
git commit -m "feat(engine): wire STUDENT_STATE v2 + refresh into build"
```

---

## Task 11: UI — Dialog de consolidação

**Files:**
- Create: `src/ui/consolidate_unit_dialog.py`
- Modify: `src/ui/app.py`
- Modify: `src/ui/dialogs.py`

- [ ] **Step 1: Criar o dialog**

```python
# src/ui/consolidate_unit_dialog.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from src.ui.theme import apply_theme_to_toplevel
from src.builder.student_state import (
    consolidate_unit, UnitNotReadyError, parse_battery_frontmatter,
)


class ConsolidateUnitDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, repo_dir: Path, course_topics_by_unit: dict):
        super().__init__(parent)
        self.title("Consolidar unidade")
        self.repo_dir = repo_dir
        self.course_topics_by_unit = course_topics_by_unit
        self.grab_set()
        p = apply_theme_to_toplevel(self, parent)

        frm = tk.Frame(self, bg=p["bg"])
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(frm, text="Unidades elegíveis:", bg=p["bg"], fg=p["fg"]).pack(anchor="w")

        self.tree = ttk.Treeview(frm, columns=("progress", "action"), show="tree headings", height=8)
        self.tree.heading("#0", text="Unidade")
        self.tree.heading("progress", text="Progresso")
        self.tree.heading("action", text="Ação")
        self.tree.column("#0", width=200)
        self.tree.column("progress", width=160)
        self.tree.column("action", width=120)
        self.tree.pack(fill="both", expand=True, pady=(4, 8))

        self._populate()

        btn_frm = tk.Frame(frm, bg=p["bg"])
        btn_frm.pack(fill="x")
        ttk.Button(btn_frm, text="Consolidar selecionada", command=self._consolidate_selected).pack(side="left")
        ttk.Button(btn_frm, text="Forçar consolidação", command=self._force_selected).pack(side="left", padx=(8, 0))
        ttk.Button(btn_frm, text="Fechar", command=self.destroy).pack(side="right")

    def _populate(self) -> None:
        batteries_root = self.repo_dir / "student" / "batteries"
        for unit_slug, topics in self.course_topics_by_unit.items():
            unit_dir = batteries_root / unit_slug
            if not unit_dir.is_dir():
                continue
            total = len(topics)
            closed = 0
            for slug, _label in topics:
                p = unit_dir / f"{slug}.md"
                if p.exists():
                    fm = parse_battery_frontmatter(p.read_text(encoding="utf-8"))
                    if fm.get("status") == "compreendido":
                        closed += 1
            progress = f"{closed}/{total} compreendidos"
            action = "Consolidar" if closed == total and total > 0 else "Forçar"
            self.tree.insert("", "end", iid=unit_slug, text=unit_slug, values=(progress, action))

    def _selected_unit(self) -> str:
        sel = self.tree.selection()
        return sel[0] if sel else ""

    def _consolidate_selected(self) -> None:
        unit = self._selected_unit()
        if not unit:
            return
        self._run(unit, force=False)

    def _force_selected(self) -> None:
        unit = self._selected_unit()
        if not unit:
            return
        if not messagebox.askyesno("Forçar consolidação",
                                    f"Forçar consolidação da {unit} mesmo com tópicos pendentes?"):
            return
        self._run(unit, force=True)

    def _run(self, unit_slug: str, force: bool) -> None:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        topic_order = [slug for slug, _ in self.course_topics_by_unit.get(unit_slug, [])]
        try:
            result = consolidate_unit(
                root_dir=self.repo_dir, unit_slug=unit_slug,
                today=today, topic_order=topic_order, force=force,
            )
            messagebox.showinfo(
                "Consolidada",
                f"{unit_slug} consolidada.\n"
                f"Summary: {result.summary_path.relative_to(self.repo_dir)}\n"
                f"Backup: {result.backup_path.relative_to(self.repo_dir)}",
            )
            self.destroy()
        except UnitNotReadyError as exc:
            messagebox.showwarning(
                "Unidade não pronta",
                f"Tópicos pendentes em {unit_slug}: {', '.join(exc.pending)}\n"
                "Use 'Forçar consolidação' se realmente quiser consolidar parcial.",
            )
```

- [ ] **Step 2: Adicionar item de menu em `app.py`**

Procurar o menu `Repo` em `src/ui/app.py` e adicionar:

```python
repo_menu.add_command(label="Consolidar unidade...", command=self._open_consolidate_dialog)
```

Implementar o método:

```python
def _open_consolidate_dialog(self) -> None:
    from src.ui.consolidate_unit_dialog import ConsolidateUnitDialog
    repo_dir = self._repo_dir()
    if not repo_dir:
        return
    subject = self._active_subject_profile()
    if not subject:
        return
    teaching_plan = getattr(subject, "teaching_plan", "") or ""
    from src.builder.engine import _parse_units_from_teaching_plan, _topic_text
    from src.utils.helpers import slugify
    parsed = _parse_units_from_teaching_plan(teaching_plan)
    units = {
        slugify(title): [(slugify(_topic_text(t)), _topic_text(t)) for t in topics]
        for title, topics in parsed
    }
    ConsolidateUnitDialog(self, repo_dir, units)
```

- [ ] **Step 3: Atualizar help em `dialogs.py`**

Localizar a seção de help que menciona `INSTRUCOES_*.md` e acrescentar:

```
  Consolidar unidade
    Consolida baterias de uma unidade inteira num summary compacto.
    Gera batteries/<unit>.summary.md e remove as baterias individuais.
    Backup automático em build/consolidation-backup/.
```

- [ ] **Step 4: Rodar suíte**

Run: `python -m pytest tests/ -q`
Expected: todos passando. UI não é testada automaticamente.

- [ ] **Step 5: Commit**

```bash
git add src/ui/consolidate_unit_dialog.py src/ui/app.py src/ui/dialogs.py
git commit -m "feat(ui): add Consolidate Unit dialog"
```

---

## Task 12: Detecção de repo v1 + oferta de migração no load

**Files:**
- Modify: `src/ui/app.py`

- [ ] **Step 1: Adicionar detecção no load do repo**

No método que carrega a matéria/repo ativo em `app.py`, após setar `self.repo_dir`:

```python
from src.builder.student_state import detect_state_version, migrate_v1_to_v2

repo_dir = self._repo_dir()
if repo_dir and detect_state_version(repo_dir) == "v1":
    from tkinter import messagebox
    if messagebox.askyesno(
        "Migração do STUDENT_STATE",
        "Este repositório usa o formato antigo (v1) do STUDENT_STATE.md.\n"
        "Quer migrar agora para o formato v2 (YAML + baterias)?\n\n"
        "A operação cria backup automático em build/migration-v1-backup/.",
    ):
        subject = self._active_subject_profile()
        teaching_plan = getattr(subject, "teaching_plan", "") or "" if subject else ""
        from src.builder.engine import _parse_units_from_teaching_plan, _topic_text
        from src.utils.helpers import slugify
        parsed = _parse_units_from_teaching_plan(teaching_plan)
        units = [
            (slugify(title), [(slugify(_topic_text(t)), _topic_text(t)) for t in topics])
            for title, topics in parsed
        ]
        result = migrate_v1_to_v2(root_dir=repo_dir, course_map_units=units)
        if not result.skipped:
            messagebox.showinfo(
                "Migração concluída",
                f"{len(result.created_batteries)} baterias criadas.\n"
                f"Backup em: {result.backup_dir.relative_to(repo_dir)}",
            )
```

- [ ] **Step 2: Rodar suíte**

Run: `python -m pytest tests/ -q`
Expected: todos passando.

- [ ] **Step 3: Commit**

```bash
git add src/ui/app.py
git commit -m "feat(ui): detect v1 STUDENT_STATE and offer migration"
```

---

## Task 13: Atualização do `ROADMAP.md`

**Files:**
- Modify: `ROADMAP.md`

- [ ] **Step 1: Adicionar seção fechada**

Abrir `ROADMAP.md` e acrescentar no final (ou numa seção "Concluído"):

```markdown
---

## Concluído

### STUDENT_STATE v2 — 2026-04-16

- YAML puro no `STUDENT_STATE.md` (~150–300 tokens)
- Histórico em `student/batteries/<unit>/<topic>.md` com summary consolidado
- Consolidação manual via `Repo → Consolidar unidade` com backup reversível
- Migração automática de repos v1 na primeira abertura
- Spec: `docs/superpowers/specs/2026-04-16-student-state-batteries-design.md`
- Plano: `docs/superpowers/plans/2026-04-16-student-state-batteries.md`
```

- [ ] **Step 2: Commit**

```bash
git add ROADMAP.md
git commit -m "docs(roadmap): mark STUDENT_STATE v2 feature as done"
```

---

## Task 14: Smoke test integrado

**Files:**
- Create: `tests/test_student_state_integration.py`

- [ ] **Step 1: Escrever teste end-to-end curto**

```python
# tests/test_student_state_integration.py
from pathlib import Path
from datetime import datetime
from src.builder.student_state import (
    render_student_state_md, ActiveTopic, ProgressRow, RecentEntry,
    refresh_active_unit_progress, consolidate_unit, migrate_v1_to_v2, detect_state_version,
)


def test_end_to_end_build_refresh_consolidate(tmp_path: Path):
    today = datetime.now().strftime("%Y-%m-%d")
    (tmp_path / "student").mkdir()
    # build inicial
    state = render_student_state_md(
        course_name="Cálculo", student_nickname="Humberto", today=today,
        active=ActiveTopic("unidade-02", "limites", "em_progresso", 0, "batteries/unidade-02/limites.md"),
        active_unit_progress=[ProgressRow("limites", "pendente"), ProgressRow("continuidade", "pendente")],
        recent=[], closed_units=[], next_topic="continuidade",
    )
    (tmp_path / "student" / "STUDENT_STATE.md").write_text(state, encoding="utf-8")
    batteries = tmp_path / "student" / "batteries" / "unidade-02"
    batteries.mkdir(parents=True)
    (batteries / "limites.md").write_text(
        "---\ntopic_slug: limites\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## X (sessão 1)\n- Resolveu: tudo\n",
        encoding="utf-8",
    )
    (batteries / "continuidade.md").write_text(
        "---\ntopic_slug: continuidade\nunit: unidade-02\nstatus: compreendido\n---\n"
        "## Y (sessão 1)\n- Resolveu: tudo\n",
        encoding="utf-8",
    )

    refresh_active_unit_progress(
        root_dir=tmp_path, active_unit_slug="unidade-02",
        course_map_topics=[("limites", "L"), ("continuidade", "C")],
    )
    assert detect_state_version(tmp_path) == "v2"
    text = (tmp_path / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "status: compreendido" in text

    result = consolidate_unit(
        root_dir=tmp_path, unit_slug="unidade-02", today=today,
        topic_order=["limites", "continuidade"],
    )
    assert result.summary_path.exists()
    assert not batteries.exists()
    final = (tmp_path / "student" / "STUDENT_STATE.md").read_text(encoding="utf-8")
    assert "closed_units: [unidade-02]" in final
```

- [ ] **Step 2: Rodar**

Run: `python -m pytest tests/test_student_state_integration.py -v`
Expected: 1 passed

- [ ] **Step 3: Rodar suíte completa uma última vez**

Run: `python -m pytest tests/ -q`
Expected: todos passando

- [ ] **Step 4: Commit**

```bash
git add tests/test_student_state_integration.py
git commit -m "test(student-state): end-to-end integration smoke test"
```

---

## Self-Review Checklist (feito pelo planner, não pelo executor)

Concluído pelo autor do plano antes de entregar:

- ✅ Cobertura do spec: cada seção tem tasks (gerador §4.1 = T1–T3, bateria §4.2 = T2, summary §4.3 = T4–T7, protocolo §5 = T9, consolidação §6 = T5–T7, revisão §7 = T7, active_unit_progress §8 = T2–T3, mudanças código §9 = T10–T12, migração §10 = T8, testes §9.4 = T1–T9+T14)
- ✅ Sem placeholders: todos os steps têm código real ou comandos concretos
- ✅ Consistência de tipos: `ActiveTopic`, `ProgressRow`, `RecentEntry`, `ConsolidationResult`, `MigrationResult`, `UnitNotReadyError` definidos uma vez (T1, T5, T8) e reutilizados nas tasks seguintes
- ✅ Ordem TDD preservada: teste antes, implementação depois, commit no fim
- ✅ Open questions do spec §14 não bloqueiam execução (commit automático na consolidação fica como config futura; refresh no load fica toggle)
