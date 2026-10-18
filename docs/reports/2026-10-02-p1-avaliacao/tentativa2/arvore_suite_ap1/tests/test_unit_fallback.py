"""Tests for unit/block auto-assignment fallbacks from COURSE_MAP.md and .timeline_index.json."""
from __future__ import annotations

import json


def _make_timeline(blocks: list) -> dict:
    return {"version": 3, "blocks": blocks}


class TestDeriveUnitSpecsFromRepo:
    def test_derives_from_timeline_index_and_course_map(self, tmp_path):
        from src.builder.routing.file_map import _derive_unit_specs_from_repo

        course_dir = tmp_path / "course"
        course_dir.mkdir()

        timeline = _make_timeline([
            {
                "id": "bloco-01",
                "unit_slug": "unidade-de-aprendizagem-01",
                "topic_text": "logica formais especificacao",
                "topics": ["logica", "formais"],
                "primary_topic_label": "Introdução a Métodos Formais",
            },
            {
                "id": "bloco-02",
                "unit_slug": "unidade-de-aprendizagem-01",
                "topic_text": "automatos linguagens regulares",
                "topics": ["automatos"],
                "primary_topic_label": "Autômatos Finitos",
            },
            {
                "id": "bloco-03",
                "unit_slug": "unidade-de-aprendizagem-02",
                "topic_text": "logica temporal verificacao",
                "topics": ["verificacao"],
                "primary_topic_label": "Verificação Formal",
            },
        ])
        (course_dir / ".timeline_index.json").write_text(
            json.dumps(timeline), encoding="utf-8"
        )
        (course_dir / "COURSE_MAP.md").write_text(
            "# COURSE_MAP\n\n## Estrutura\n\n"
            "### Unidade de Aprendizagem 01\n- [ ] Tópico\n\n"
            "### Unidade de Aprendizagem 02\n- [ ] Tópico\n",
            encoding="utf-8",
        )

        course_meta = {"_repo_root": tmp_path}
        specs = _derive_unit_specs_from_repo(course_meta)

        assert len(specs) == 2
        titles = [s["title"] for s in specs]
        assert "Unidade de Aprendizagem 01" in titles
        assert "Unidade de Aprendizagem 02" in titles

        ua01 = next(s for s in specs if "01" in s["title"])
        assert "logica" in ua01["extra_signals"]
        assert "formais" in ua01["extra_signals"]
        assert "automatos" in ua01["extra_signals"]

    def test_falls_back_to_timeline_slugs_when_no_course_map(self, tmp_path):
        from src.builder.routing.file_map import _derive_unit_specs_from_repo

        course_dir = tmp_path / "course"
        course_dir.mkdir()

        timeline = _make_timeline([
            {
                "id": "bloco-01",
                "unit_slug": "unidade-01",
                "topic_text": "redes neural profundo",
                "topics": ["redes"],
            },
        ])
        (course_dir / ".timeline_index.json").write_text(
            json.dumps(timeline), encoding="utf-8"
        )
        # Sem COURSE_MAP.md

        course_meta = {"_repo_root": tmp_path}
        specs = _derive_unit_specs_from_repo(course_meta)

        assert len(specs) == 1
        # Título derivado do slug
        assert specs[0]["title"] == "Unidade-01".title() or "-" in specs[0]["title"] or "01" in specs[0]["title"]
        assert "redes" in specs[0]["extra_signals"]

    def test_ignores_placeholder_headings_in_course_map(self, tmp_path):
        from src.builder.routing.file_map import _derive_unit_specs_from_repo

        course_dir = tmp_path / "course"
        course_dir.mkdir()

        # COURSE_MAP com apenas placeholders (sem timeline_index)
        (course_dir / "COURSE_MAP.md").write_text(
            "### Unidade 1 — [Nome da unidade]\n- [ ] Tópico\n\n"
            "### Unidade 2 — [Nome da unidade]\n",
            encoding="utf-8",
        )
        # Sem timeline_index

        course_meta = {"_repo_root": tmp_path}
        specs = _derive_unit_specs_from_repo(course_meta)

        # Placeholders com "[" devem ser ignorados; sem timeline_index → lista vazia
        assert specs == []

    def test_returns_empty_when_no_repo_root(self):
        from src.builder.routing.file_map import _derive_unit_specs_from_repo

        specs = _derive_unit_specs_from_repo({})
        assert specs == []

    def test_returns_empty_when_timeline_has_no_unit_slugs(self, tmp_path):
        from src.builder.routing.file_map import _derive_unit_specs_from_repo

        course_dir = tmp_path / "course"
        course_dir.mkdir()

        # Blocos sem unit_slug
        timeline = _make_timeline([
            {"id": "bloco-01", "unit_slug": "", "topic_text": "topico"},
        ])
        (course_dir / ".timeline_index.json").write_text(
            json.dumps(timeline), encoding="utf-8"
        )

        course_meta = {"_repo_root": tmp_path}
        specs = _derive_unit_specs_from_repo(course_meta)
        assert specs == []
