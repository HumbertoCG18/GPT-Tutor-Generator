"""Validação de schema v4 do `.timeline_index.json` (Fase 6).

- O schema é Draft-07 válido.
- O serializer produz saída que bate no schema (estrutura).
- Fixtures versionados passam schema + gates de saúde (contrato verde).
- Cursos reais (se presentes) validam estrutura via backfill — gate NÃO aplicado
  (artefatos em disco podem estar stale antes de rebuild).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft7Validator  # noqa: E402

from scripts.validate_timeline import (  # noqa: E402
    FIXTURES_GLOB,
    SCHEMA_PATH,
    gate_failures,
    health_report,
    schema_errors,
    validate_file,
)
from src.builder.core.core_utils import persist_enriched_timeline_index  # noqa: E402

import glob  # noqa: E402


# ---------------------------------------------------------------------------
# schema em si
# ---------------------------------------------------------------------------

def test_schema_is_valid_draft7():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)


def test_schema_version_const_is_4():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["properties"]["version"]["const"] == 4


# ---------------------------------------------------------------------------
# fixtures versionados — schema + gates verdes
# ---------------------------------------------------------------------------

_FIXTURES = sorted(glob.glob(FIXTURES_GLOB))


def test_has_at_least_one_fixture():
    assert _FIXTURES, f"nenhum fixture em {FIXTURES_GLOB}"


@pytest.mark.parametrize("path", _FIXTURES, ids=lambda p: Path(p).name)
def test_fixture_passes_schema_and_gates(path):
    ok, msgs = validate_file(Path(path))
    assert ok, f"{path}:\n  " + "\n  ".join(msgs)


@pytest.mark.parametrize("path", _FIXTURES, ids=lambda p: Path(p).name)
def test_fixture_has_no_schema_errors(path):
    index = json.loads(Path(path).read_text(encoding="utf-8"))
    assert schema_errors(index) == []


# ---------------------------------------------------------------------------
# serializer produz v4 válido
# ---------------------------------------------------------------------------

def test_serializer_output_matches_schema():
    # Cutover passo 3: serializador unico (persist_enriched, v4). O kind vem
    # dos builders (finalize_block), nao do serializer — fixture producao-like.
    raw = {
        "version": 3,
        "blocks": [
            {
                "id": "bloco-01",
                "kind": "class",
                "period_start": "2026-03-11",
                "period_end": "2026-03-11",
                "period_label": "1 dia · 11/03/2026",
                "unit_slug": "unidade-01",
                "primary_topic_label": "Lógica",
                "topic_text": "Lógica de predicados",
                "sessions": [{"date": "2026-03-11"}],
                "source_rows": [1],
            }
        ],
    }
    out = persist_enriched_timeline_index(raw)
    assert out["version"] == 4
    assert schema_errors(out) == []


# ---------------------------------------------------------------------------
# cursos reais (skip se ausentes) — estrutura via backfill, sem gate
# ---------------------------------------------------------------------------

_REAL_COURSES = [
    "Engenharia-Software-2-Tutor",
    "Inteligencia-Artifical-Tutor",
    "Metodos-Formais-Tutor",
    "Sistemas-Operacionais-Tutor",
    "TCC-Tutor",
]
_BASE = Path(os.environ.get("TUTOR_COURSES_DIR", r"C:\Users\Humberto\Documents\GitHub"))


@pytest.mark.parametrize("course", _REAL_COURSES)
def test_real_course_structure_validates(course):
    path = _BASE / course / "course" / ".timeline_index.json"
    if not path.exists():
        pytest.skip(f"corpus indisponível: {path}")
    index = json.loads(path.read_text(encoding="utf-8"))
    out = persist_enriched_timeline_index(index)
    errs = schema_errors(out)
    assert errs == [], f"{course} drift de schema:\n  " + "\n  ".join(errs)


@pytest.mark.parametrize("course", _REAL_COURSES)
def test_real_course_passes_health_gates(course):
    """Trava os 100%: cursos reais (pós rebuild+curadoria) passam os gates.
    Skip se o corpus não existir nesta máquina."""
    path = _BASE / course / "course" / ".timeline_index.json"
    if not path.exists():
        pytest.skip(f"corpus indisponível: {path}")
    index = json.loads(path.read_text(encoding="utf-8"))
    fails = gate_failures(health_report(index.get("blocks", [])))
    assert fails == [], f"{course} falha gate:\n  " + "\n  ".join(fails)


# ---------------------------------------------------------------------------
# gates de saúde — lógica pura
# ---------------------------------------------------------------------------

def test_gate_flags_high_unknown():
    blocks = [{"topic_text": "x"}] + [{"topic_text": ""} for _ in range(9)]
    # 9 blocos vazios sem unit -> unknown; 1 com substância curta
    rep = health_report(blocks)
    assert rep["unknown_rate"] > 0.05
    assert any("unknown" in f for f in gate_failures(rep))


def test_gate_passes_clean_blocks():
    blocks = [
        {"kind": "class", "unit_slug": "u1", "primary_topic_label": "t",
         "topic_text": "aula de logica", "sessions": [{"d": 1}]}
        for _ in range(5)
    ]
    rep = health_report(blocks)
    assert gate_failures(rep) == []
