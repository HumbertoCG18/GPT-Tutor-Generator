from pathlib import Path

from src.builder.artifacts.student_state import (
    apply_manual_import_to_student_state,
    build_course_unit_topic_index,
    parse_student_state_manual_import,
    save_manual_import_battery,
    validate_manual_import_selection,
)


def test_build_course_unit_topic_index_returns_unit_and_topic_slugs():
    subject = type(
        "Subject",
        (),
        {
            "teaching_plan": "\n".join(
                [
                    "Unidade 1 - Limites",
                    "- Definicao de limite",
                    "- Continuidade",
                ]
            )
        },
    )()

    index = build_course_unit_topic_index(subject)

    assert index[0]["unit_slug"] == "unidade-01-limites"
    assert index[0]["topics"][0]["topic_slug"] == "definicao-de-limite"
    assert index[0]["topics"][0]["topic_label"] == "1.1 - Definicao de limite"
    assert index[0]["topics"][1]["topic_label"] == "1.2 - Continuidade"


def test_build_course_unit_topic_index_returns_empty_without_teaching_plan():
    subject = type("Subject", (), {"teaching_plan": ""})()
    assert build_course_unit_topic_index(subject) == []


def test_build_course_unit_topic_index_formats_nested_topics_with_dots():
    subject = type(
        "Subject",
        (),
        {
            "teaching_plan": "\n".join(
                [
                    "Unidade 2 - Verificacao",
                    "2.1. Hoare",
                    "2.1.1. Pre e Pos Condicoes",
                ]
            )
        },
    )()

    index = build_course_unit_topic_index(subject)

    assert index[0]["topics"][0]["topic_label"] == "2.1 - Hoare"
    assert index[0]["topics"][1]["topic_label"] == "2.1.1 - Pre e Pos Condicoes"


def test_parse_student_state_manual_import_reads_frontmatter_and_body():
    raw = """---
unit: unidade-01-limites
unit_title: Unidade 1 - Limites
topic: definicao-de-limite
topic_title: Definicao de limite
status: em_progresso
date: 22-04-26
time: 14-35
next_topic: continuidade
---

## Resumo
Conteudo estudado.
"""

    parsed = parse_student_state_manual_import(raw)

    assert parsed["unit_slug"] == "unidade-01-limites"
    assert parsed["topic_slug"] == "definicao-de-limite"
    assert parsed["status"] == "em_progresso"
    assert "Conteudo estudado." in parsed["body"]


def test_parse_student_state_manual_import_defaults_missing_date_time():
    raw = """---
unit: unidade-01-limites
topic: definicao-de-limite
status: compreendido
---
texto
"""

    parsed = parse_student_state_manual_import(raw, now_text=("22-04-26", "14-35"))

    assert parsed["date"] == "22-04-26"
    assert parsed["time"] == "14-35"


def test_save_manual_import_battery_creates_new_topic_file(tmp_path: Path):
    payload = {
        "unit_slug": "unidade-01-limites",
        "unit_title": "Unidade 1 - Limites",
        "topic_slug": "definicao-de-limite",
        "topic_title": "Definicao de limite",
        "status": "em_progresso",
        "date": "22-04-26",
        "time": "14-35",
        "next_topic": "continuidade",
        "body": "## Resumo\nConteudo estudado.\n",
    }
    save_manual_import_battery(tmp_path, payload)

    created = tmp_path / "student" / "batteries" / "unidade-01-limites" / "definicao-de-limite.md"
    text = created.read_text(encoding="utf-8")
    assert "topic_slug: definicao-de-limite" in text
    assert "## 22-04-26 14-35 (sessao 1)" in text


def test_save_manual_import_battery_appends_existing_topic_file(tmp_path: Path):
    target = tmp_path / "student" / "batteries" / "unidade-01-limites"
    target.mkdir(parents=True)
    existing = target / "definicao-de-limite.md"
    existing.write_text(
        "\n".join(
            [
                "---",
                "topic: Definicao de limite",
                "topic_slug: definicao-de-limite",
                "unit: unidade-01-limites",
                "status: em_progresso",
                "---",
                "",
                "## 21-04-26 10-00 (sessao 1)",
                "- Status: em_progresso",
                "",
            ]
        ),
        encoding="utf-8",
    )

    payload = {
        "unit_slug": "unidade-01-limites",
        "unit_title": "Unidade 1 - Limites",
        "topic_slug": "definicao-de-limite",
        "topic_title": "Definicao de limite",
        "status": "compreendido",
        "date": "22-04-26",
        "time": "14-35",
        "next_topic": "",
        "body": "## Resumo\nConteudo estudado.\n",
    }
    save_manual_import_battery(tmp_path, payload)

    text = existing.read_text(encoding="utf-8")
    assert "## 22-04-26 14-35 (sessao 2)" in text
    assert text.count("(sessao") == 2


def test_apply_manual_import_to_student_state_updates_active_and_recent(tmp_path: Path):
    state_path = tmp_path / "student" / "STUDENT_STATE.md"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        "\n".join(
            [
                "---",
                "course: Calculo",
                "student: Humberto",
                "updated: 21-04-26",
                "",
                "active:",
                "  unit: unidade-00-anterior",
                "  topic: anterior",
                "  status: pendente",
                "  sessions: 1",
                "  file: student/batteries/unidade-00-anterior/anterior.md",
                "",
                "active_unit_progress:",
                "  - {topic: definicao-de-limite, status: pendente}",
                "",
                "recent:",
                "  - {topic: anterior, unit: unidade-00-anterior, date: 21-04-26}",
                "",
                "next_topic: continuidade",
                "",
                "---",
                "",
            ]
        ),
        encoding="utf-8",
    )
    battery_dir = tmp_path / "student" / "batteries" / "unidade-01-limites"
    battery_dir.mkdir(parents=True)
    battery = battery_dir / "definicao-de-limite.md"
    battery.write_text(
        "\n".join(
            [
                "---",
                "topic: Definicao de limite",
                "topic_slug: definicao-de-limite",
                "unit: unidade-01-limites",
                "status: em_progresso",
                "---",
                "",
                "## 22-04-26 14-35 (sessao 1)",
                "- Status: em_progresso",
                "",
            ]
        ),
        encoding="utf-8",
    )

    payload = {
        "unit_slug": "unidade-01-limites",
        "topic_slug": "definicao-de-limite",
        "status": "em_progresso",
        "date": "22-04-26",
        "time": "14-35",
        "next_topic": "continuidade",
    }

    apply_manual_import_to_student_state(
        tmp_path,
        payload=payload,
        battery_rel_path="student/batteries/unidade-01-limites/definicao-de-limite.md",
        course_map_topics=[("definicao-de-limite", "Definicao de limite"), ("continuidade", "Continuidade")],
    )

    text = state_path.read_text(encoding="utf-8")
    assert "unit: unidade-01-limites" in text
    assert "topic: definicao-de-limite" in text
    assert "file: student/batteries/unidade-01-limites/definicao-de-limite.md" in text
    assert "updated: 22-04-26" in text
    assert "- {topic: definicao-de-limite, unit: unidade-01-limites, date: 22-04-26}" in text


def test_validate_manual_import_selection_rejects_unknown_topic():
    course_index = [
        {
            "unit_slug": "unidade-01-limites",
            "unit_title": "Unidade 1 - Limites",
            "topics": [{"topic_slug": "definicao-de-limite", "topic_title": "Definicao de limite"}],
        }
    ]

    errors = validate_manual_import_selection(
        unit_slug="unidade-01-limites",
        topic_slug="continuidade",
        course_index=course_index,
    )

    assert errors == ["topic_slug"]
