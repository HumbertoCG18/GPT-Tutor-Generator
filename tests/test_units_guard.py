"""Fio subject_profile — Task 4 (fix round 1): guard "unidade nunca encolhe em silencio".

v2 mede o ENCOLHIMENTO REAL do indice prestes a ser persistido (novo vs existente em
disco), nao mais o proxy antigo (parsed==0 E existente>=2) -- o proxy disparava mesmo
quando o fallback repo-derived preservava as unidades (fluxo legitimo "reprocessar sem
perfil"). Ver CONTROLLER RULING / fix round 1 no task-4-report.md.

Fixtures SINTETICAS apenas (nenhum repo real tocado, per constraint da task).
Cobre: (a)/(a2)/(b)/(c) o guard em pedagogical_regeneration.py; (d) scripts/verify_units.py
FAIL em perda nova vs baseline / WARN+exit0 em perda ja conhecida; (e) aviso alto
do fallback _derive_unit_specs_from_repo (file_map.py).
"""
from __future__ import annotations

import json
import logging

import pytest

from src.builder.ops.pedagogical_regeneration import (
    UnitsShrinkError,
    _guard_units_not_silently_lost,
)
from src.builder.routing.file_map import _derive_unit_specs_from_repo


def _write_index(root_dir, unit_slugs):
    course_dir = root_dir / "course"
    course_dir.mkdir(parents=True, exist_ok=True)
    blocks = [
        {"id": f"bloco-{i:02d}", "unit_slug": slug, "auto_unit_slug": slug}
        for i, slug in enumerate(unit_slugs, start=1)
    ]
    (course_dir / ".timeline_index.json").write_text(
        json.dumps({"version": 3, "blocks": blocks}), encoding="utf-8"
    )


def _index_dict(unit_slugs):
    return {
        "version": 3,
        "blocks": [
            {"id": f"bloco-{i:02d}", "unit_slug": slug, "auto_unit_slug": slug}
            for i, slug in enumerate(unit_slugs, start=1)
        ],
    }


class TestGuardUnitsNotSilentlyLost:
    def test_a_fires_on_shrink_with_parsed_zero(self, tmp_path):
        """(a) indice existente 3 slugs -> novo indice 2 slugs, parser 0 -> UnitsShrinkError
        com nome do curso (o incidente real de agosto: 3->2 sem subject_profile)."""
        root_dir = tmp_path / "repo"
        _write_index(root_dir, ["unidade-01", "unidade-02", "unidade-03"])
        new_index = _index_dict(["unidade-01", "unidade-02"])

        with pytest.raises(UnitsShrinkError) as excinfo:
            _guard_units_not_silently_lost(root_dir, "Metodos Formais", 0, new_index)

        assert "Metodos Formais" in str(excinfo.value)

    def test_a2_does_not_fire_when_new_index_preserves_count(self, tmp_path):
        """(a2) parser 0 (sem perfil) MAS o novo indice preserva as mesmas unidades do
        existente (fallback repo-derived reconstruiu certo) -> nao dispara. Fluxo real:
        botao "Reprocessar Repositorio" sem subject_profile (app.py)."""
        root_dir = tmp_path / "repo"
        _write_index(root_dir, ["unidade-01", "unidade-02"])
        new_index = _index_dict(["unidade-01", "unidade-02"])

        _guard_units_not_silently_lost(root_dir, "TCC", 0, new_index)  # nao levanta

    def test_b_does_not_fire_on_brand_new_repo_without_index(self, tmp_path):
        """(b) repo novo sem .timeline_index.json + parser [] -> nao dispara (nada pra encolher)."""
        root_dir = tmp_path / "repo"
        root_dir.mkdir(parents=True, exist_ok=True)
        new_index = _index_dict([])

        _guard_units_not_silently_lost(root_dir, "Curso Novo", 0, new_index)  # nao levanta

    def test_c_does_not_fire_with_parser_positive_even_if_count_drops(self, tmp_path, caplog):
        """(c) parser>0 (plano de ensino presente) e o novo indice tem MENOS unidades que o
        existente -> reducao AUTORADA (usuario editou o plano), nao dispara -- so loga info."""
        root_dir = tmp_path / "repo"
        _write_index(root_dir, ["unidade-01", "unidade-02", "unidade-03"])
        new_index = _index_dict(["unidade-01", "unidade-02"])

        with caplog.at_level(logging.INFO, logger="src.builder.ops.pedagogical_regeneration"):
            _guard_units_not_silently_lost(root_dir, "Curso Editado", 2, new_index)  # nao levanta

        assert any(
            "reduziram de 3 para 2" in rec.message for rec in caplog.records
        ), [rec.message for rec in caplog.records]


class TestDeriveUnitSpecsFromRepoWarnsLoud:
    def test_logs_warning_when_fallback_reached(self, caplog):
        """(e) fallback loga aviso alto sempre que alcancado (mesmo sem repo_root)."""
        with caplog.at_level(logging.WARNING, logger="src.builder.routing.file_map"):
            _derive_unit_specs_from_repo({})

        messages = [rec.message for rec in caplog.records]
        assert any(
            "unidades derivadas do repo gerado, nao do plano de ensino" in m
            for m in messages
        ), messages


# ---------------------------------------------------------------------------
# (d) scripts/verify_units.py — FAIL em perda nova, WARN+exit0 em perda conhecida
# ---------------------------------------------------------------------------

TEACHING_PLAN_3_UNITS = """
Unidade 1 - Introducao
- topico um

Unidade 2 - Estruturas
- topico dois

Unidade 3 - Avancado
- topico tres
"""


def _make_repo_with_loss(tmp_path, name, plan_text, index_slugs):
    repo_root = tmp_path / name
    curated = repo_root / "content" / "curated"
    curated.mkdir(parents=True, exist_ok=True)
    (curated / "plano.md").write_text(plan_text, encoding="utf-8")
    _write_index(repo_root, index_slugs)
    return repo_root


class TestVerifyUnitsScript:
    def test_new_loss_not_in_baseline_fails(self, tmp_path, monkeypatch):
        from scripts import verify_units

        # SubjectStore real nao deve enxergar este repo sintetico -> cai no
        # fallback plano.md (monkeypatch garante isolamento de qualquer
        # subjects.json real do usuario).
        monkeypatch.setattr(
            verify_units.SubjectStore, "find_by_repo_root", lambda self, repo_root: None
        )

        repo_root = _make_repo_with_loss(
            tmp_path, "Curso-Novo-Tutor", TEACHING_PLAN_3_UNITS,
            ["unidade-01-introducao"],  # perde unidade-02 e unidade-03
        )
        baseline_path = tmp_path / "units_baseline.json"
        baseline_path.write_text(json.dumps({"courses": {}}), encoding="utf-8")

        exit_code = verify_units.main(
            ["--baseline", str(baseline_path), str(repo_root)]
        )

        assert exit_code != 0

    def test_known_loss_in_baseline_warns_and_exits_zero(self, tmp_path, monkeypatch, capsys):
        from scripts import verify_units

        monkeypatch.setattr(
            verify_units.SubjectStore, "find_by_repo_root", lambda self, repo_root: None
        )

        repo_root = _make_repo_with_loss(
            tmp_path, "Curso-Conhecido-Tutor", TEACHING_PLAN_3_UNITS,
            ["unidade-01-introducao"],  # perde unidade-02 e unidade-03
        )
        baseline_path = tmp_path / "units_baseline.json"
        baseline_path.write_text(
            json.dumps(
                {
                    "courses": {
                        "Curso-Conhecido-Tutor": {
                            "parser_n": 3,
                            "index_n": 1,
                            "missing_slugs": [
                                "unidade-02-estruturas",
                                "unidade-03-avancado",
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        exit_code = verify_units.main(
            ["--baseline", str(baseline_path), str(repo_root)]
        )
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "WARN" in out
