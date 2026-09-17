"""Regressões com plano e contrato de sidecar de test_glossary_curation.py."""
import json

import pytest

from scripts import ablacao_rapida
from src.builder import engine
from src.models.core import SubjectProfile
from src.builder.core.course_vocabulary import course_terms_text
from src.builder.extraction import content_taxonomy


PLAN = """
Unidade de Aprendizagem 5: Aprendizado de máquina (30%)
Introdução ao aprendizado de máquina
Paradigmas de aprendizado
Modelos Preditivos
Modelos Descritivos
Métricas de Avaliação
"""


def test_tail_alias_survives_visual_budget(tmp_path):
    course = tmp_path / "course"
    course.mkdir()
    (course / ".glossary_curation.json").write_text(json.dumps({
        "Introdução ao aprendizado de máquina": {"synonyms": [f"sinonimo{i:04d}" for i in range(1800)]},
        "Métricas de Avaliação": {"synonyms": ["marcador-final"]},
    }), encoding="utf-8")
    profile = SubjectProfile(name="IA", slug="ia", teaching_plan=PLAN)
    meta = {"course_name": "IA", "_repo_root": tmp_path}
    visual = engine.glossary_md(meta, profile, root_dir=tmp_path)
    assert "marcador-final" not in visual
    tax = engine._build_file_map_content_taxonomy_from_course(meta, profile, [])
    topic = next(t for u in tax["units"] for t in u["topics"] if t["slug"] == "metricas-de-avaliacao")
    assert "marcador-final" in topic["aliases"]


def test_fresh_copy_rejects_residual_before_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(ablacao_rapida, "GEN", tmp_path)
    src = tmp_path / "source"
    src.mkdir()
    dst = tmp_path / ".frzero" / "run" / "course"
    dst.mkdir(parents=True)
    residue = dst / ".glossary_curation.json"
    residue.write_text("residuo", encoding="utf-8")
    with pytest.raises(FileExistsError):
        ablacao_rapida.sync_fresh(src, dst)
    assert residue.read_text(encoding="utf-8") == "residuo"


def test_fresh_copy_rejects_outside_root(tmp_path, monkeypatch):
    monkeypatch.setattr(ablacao_rapida, "GEN", tmp_path)
    dst = tmp_path / "outside"
    with pytest.raises(ValueError):
        ablacao_rapida.sync_fresh(tmp_path / "source", dst)
    assert not dst.exists()


def test_fresh_copy_copies_source_and_propagates_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(ablacao_rapida, "GEN", tmp_path)
    src = tmp_path / "source"
    src.mkdir()
    (src / "manifest.json").write_text('{"entries": []}', encoding="utf-8")
    dst = tmp_path / ".frzero" / "run"
    ablacao_rapida.sync_fresh(src, dst)
    assert (dst / "manifest.json").read_bytes() == (src / "manifest.json").read_bytes()
    assert list(src.iterdir()) == [src / "manifest.json"]

    def failed_copy(*args):
        raise SystemExit("robocopy falhou (8)")

    failed = tmp_path / ".frzero" / "failed"
    with pytest.raises(SystemExit, match="robocopy falhou"):
        ablacao_rapida.sync_fresh(src, failed, sync_fn=failed_copy)
    with pytest.raises(FileExistsError):
        ablacao_rapida.sync_fresh(src, failed)


def test_fresh_copy_rejects_missing_or_overlapping_source(tmp_path, monkeypatch):
    monkeypatch.setattr(ablacao_rapida, "GEN", tmp_path)
    dst = tmp_path / ".frzero" / "run"
    with pytest.raises(FileNotFoundError):
        ablacao_rapida.sync_fresh(tmp_path / "missing", dst)
    with pytest.raises(ValueError, match="sobrepostos"):
        ablacao_rapida.sync_fresh(tmp_path, dst)
    assert not dst.exists()


def test_consumers_do_not_call_visual_renderer(tmp_path, monkeypatch):
    profile = SubjectProfile(name="IA", slug="ia", teaching_plan=PLAN)
    meta = {"course_name": "IA", "_repo_root": tmp_path}

    def broken_renderer(*args, **kwargs):
        raise AssertionError("consumidor chamou renderizador visual")

    monkeypatch.setattr(engine._repo_artifacts, "glossary_md", broken_renderer)
    tax = engine._build_file_map_content_taxonomy_from_course(meta, profile, [])
    index = engine._build_file_map_unit_index_from_course(meta, profile)
    assert all(t["aliases"] for u in tax["units"] for t in u["topics"])
    assert index


def test_terms_reload_after_curation_change_and_ignore_template(tmp_path):
    profile = SubjectProfile(name="IA", slug="ia", teaching_plan=PLAN)
    terms = engine._course_terms({}, profile, root_dir=tmp_path)
    assert len(terms) == 5
    assert all(t["term"] != "[Termo]" for t in terms)
    assert engine._course_terms({}, None, root_dir=tmp_path) == []
    (tmp_path / "course").mkdir()
    sidecar = tmp_path / "course" / ".glossary_curation.json"
    for synonym in ("primeiro-alias", "segundo-alias"):
        sidecar.write_text(json.dumps({"Modelos Preditivos": {"synonyms": [synonym]}}), encoding="utf-8")
        terms = engine._course_terms({}, profile, root_dir=tmp_path)
        target = next(t for t in terms if t["term"] == "Modelos Preditivos")
        assert synonym in target["synonyms"]
    assert "primeiro-alias" not in target["synonyms"]


def test_repeated_topic_keeps_its_unit():
    # Mesma sintaxe de unidade do plano IA e labels repetidos como no SO.
    profile = SubjectProfile(teaching_plan="""
Unidade de Aprendizagem 1: Fundamentos
Conceitos básicos
Unidade de Aprendizagem 2: Aplicações
Conceitos básicos
""")
    terms = engine._course_terms({}, profile)
    assert len(terms) == 2
    assert terms[0]["term"] == terms[1]["term"]
    assert terms[0]["unit_hint"] != terms[1]["unit_hint"]


def test_structured_catalog_matches_integral_text_and_preserves_manual_tags(tmp_path):
    profile = SubjectProfile(name="IA", slug="ia", teaching_plan=PLAN)
    terms = engine._course_terms({}, profile)
    outputs = []
    profiles = []
    for name, kwargs in (("legacy", {"glossary_text": course_terms_text(terms)}),
                         ("direct", {"glossary_text": "TEXTO VISUAL IGNORADO", "glossary_terms": terms})):
        root = tmp_path / name
        (root / "course").mkdir(parents=True)
        (root / "course" / ".tag_catalog.json").write_text(
            json.dumps({"manual_tags": ["topico:manual"]}), encoding="utf-8",
        )
        outputs.append(content_taxonomy.write_tag_catalog(
            root, course_name="IA", teaching_plan=PLAN, course_map_text="",
            manifest_entries=[], **kwargs,
        ))
        profiles.append(json.loads((root / "course" / ".semantic_profile.generated.json").read_text(encoding="utf-8")))
    assert outputs[0] == outputs[1]
    assert profiles[0] == profiles[1]
    assert "topico:manual" in outputs[1]["tags"]
