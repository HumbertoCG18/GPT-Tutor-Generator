from pathlib import Path

from src.builder.artifacts.student_state import detect_state_version, migrate_v1_to_v2


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
        course_map_units=[(
            "unidade-02",
            [
                ("limites", "Limites"),
                ("continuidade", "Continuidade"),
                ("derivadas-parciais", "Derivadas parciais"),
            ],
        )],
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
    assert "active_unit_progress:" in new_state or "course:" in new_state
    assert "Histórico de sessões" not in new_state
    assert result.backup_dir.exists()


def test_migrate_is_idempotent(tmp_path: Path):
    (tmp_path / "student").mkdir()
    (tmp_path / "student" / "STUDENT_STATE.md").write_text(V1_SAMPLE, encoding="utf-8")
    migrate_v1_to_v2(root_dir=tmp_path, course_map_units=[])
    result2 = migrate_v1_to_v2(root_dir=tmp_path, course_map_units=[])
    assert result2.skipped is True
