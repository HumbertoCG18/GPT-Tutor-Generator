"""Testa que CODE_INDEX, CRONOGRAMA_DETALHADO e CODE_HEALTH agrupam por
computed_block_id (funil), e nao por primary_block_id (Gemini).
"""
from src.models.core import FileEntry
from src.builder.artifacts import repo


def _blocks():
    return [
        {"id": "bloco-05", "period_label": "Semana 5", "primary_topic_label": "Hoare", "topics": [], "unit_slug": "u1"},
        {"id": "bloco-12", "period_label": "Semana 12", "primary_topic_label": "Dafny", "topics": [], "unit_slug": "u2"},
    ]


def _code_entry():
    # computed_block_id = bloco-05 (funil); Gemini diria bloco-12
    return FileEntry.from_dict({
        "id": "c1", "title": "Hoare demo", "file_type": "zip",
        "category": "codigo-professor", "source_path": "code/hoare.zip",
        "computed_block_id": "bloco-05",
    })


def _curation():
    return {"entries": {"c1": {"summary": {
        "primary_block_id": "bloco-12",
        "secondary_block_ids": [],
        "concepts": ["Hoare"], "inferred_title": "Hoare demo",
        "language": "dafny", "pedagogical_role": "exemplo",
    }}}}


def _noop_clamp(text, *, max_chars, label):
    return text


def _noop_profile(course_meta, subject_profile):
    return {
        "code_index_intro": "",
        "code_index_review_line": "",
        "code_index_empty": "",
        "code_index_section": "",
    }


def test_code_index_groups_by_computed_block():
    md = repo.code_index_md(
        {"course_name": "MF"},
        [_code_entry()],
        None,
        code_curation=_curation(),
        timeline_blocks=_blocks(),
        code_review_profile_fn=_noop_profile,
        clamp_navigation_artifact=_noop_clamp,
    )
    assert "Semana 5" in md            # agrupado sob o bloco do funil
    assert "Semana 12" not in md       # NAO sob o bloco do Gemini


def test_cronograma_groups_primary_by_computed_block():
    md = repo.cronograma_detalhado_md(
        {"course_name": "MF"}, [_code_entry()], _curation(), _blocks(),
    )
    # a entry aparece como codigo primario sob Semana 5, nao Semana 12
    bloco5_section = md.split("## Semana 12")[0]
    assert "Hoare demo" in bloco5_section


def test_code_health_counts_computed_block():
    md = repo.code_health_md(
        {"course_name": "MF"}, [_code_entry()], _curation(), _blocks(),
    )
    # 1 codigo, vinculado via computed_block_id -> com_block=1, orfaos=0
    assert "Vinculados a aula: **1" in md
    assert "resumo sem aula): **0" in md
