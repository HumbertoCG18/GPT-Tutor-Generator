"""Testes das linhas de apoio (📖 Apoio) emitidas no COURSE_MAP a partir do
índice course_meta["_reference_nav_index"]. RED→GREEN da Task 2."""
from __future__ import annotations

from src.builder.engine import course_map_md
from src.builder.extraction.teaching_plan import _normalize_unit_slug
from src.builder.core.reference_navigation import _topic_key
from src.models.core import SubjectProfile


# Plano no formato markdown reconhecido por parse_units_from_teaching_plan:
# heading "### Unidade N - Título" + bullets "- Tópico".
TEACHING_PLAN = """
### Unidade 1 - Desenvolvimento Web
- Rotas HTTP
- Templates
"""

UNIT_SLUG = _normalize_unit_slug("Unidade 1 - Desenvolvimento Web")


def _make_profile():
    return SubjectProfile(
        name="Desenvolvimento Web",
        slug="desenvolvimento-web",
        syllabus="",
        teaching_plan=TEACHING_PLAN,
    )


def _ref(entry_id, title, type_, concepts, topics):
    return {
        "entry_id": entry_id,
        "title": title,
        "source_path": "",
        "type": type_,
        "concepts": list(concepts),
        "topics": list(topics),
        "unit_slug": UNIT_SLUG,
    }


def _render(by_unit=None, by_topic=None, with_index=True):
    course_meta = {"course_name": "Desenvolvimento Web"}
    if with_index:
        course_meta["_reference_nav_index"] = {
            "by_unit": by_unit or {},
            "by_topic": by_topic or {},
        }
    return course_map_md(course_meta, _make_profile())


def test_support_line_appears_under_topic():
    ref = _ref("e1", "Flask", "repo", ["roteamento"], ["Rotas HTTP"])
    tkey = (UNIT_SLUG, _topic_key("Rotas HTTP"))
    out = _render(by_unit={UNIT_SLUG: [ref]}, by_topic={tkey: [ref]})

    assert "📖 Apoio: Flask (repo)" in out

    lines = out.splitlines()
    # A linha de apoio deve aparecer logo após o bullet "Rotas HTTP".
    topic_idx = next(i for i, ln in enumerate(lines) if "Rotas HTTP" in ln and "[ ]" in ln)
    assert "📖 Apoio: Flask (repo)" in lines[topic_idx + 1]


def test_unit_only_ref_appears_under_unit_header():
    ref = _ref("e1", "Geral", "doc", [], [])
    out = _render(by_unit={UNIT_SLUG: [ref]}, by_topic={})
    assert "📖 Apoio: Geral (doc)" in out


def test_degraded_mode_no_index_is_unchanged():
    empty = _render(by_unit={}, by_topic={}, with_index=True)
    base = _render(with_index=False)
    assert "📖 Apoio" not in base
    # Índice vazio deve produzir saída byte-idêntica ao modo sem índice.
    assert base == empty


def test_cap_two_lines_plus_overflow():
    refs = [
        _ref("e1", "Ref A", "repo", [], ["Rotas HTTP"]),
        _ref("e2", "Ref B", "repo", [], ["Rotas HTTP"]),
        _ref("e3", "Ref C", "repo", [], ["Rotas HTTP"]),
    ]
    tkey = (UNIT_SLUG, _topic_key("Rotas HTTP"))
    out = _render(by_unit={UNIT_SLUG: refs}, by_topic={tkey: refs})

    assert out.count("📖 Apoio:") == 2
    assert "(+1 referência(s) em content/BIBLIOGRAPHY.md)" in out


def test_overflow_ref_still_surfaces_under_other_topic():
    """Regressão: uma ref em overflow sob o tópico A não pode ser suprimida sob
    o tópico B onde ela é a única referência legítima. shown_ids deve deduplicar
    apenas EMISSÕES (head); overflow não marca a ref como mostrada globalmente."""
    e1 = _ref("e1", "Ref1", "repo", [], ["Rotas HTTP"])
    e2 = _ref("e2", "Ref2", "repo", [], ["Rotas HTTP"])
    e3 = _ref("e3", "Ref3", "repo", [], ["Rotas HTTP", "Templates"])

    tkey_rotas = (UNIT_SLUG, _topic_key("Rotas HTTP"))
    tkey_templates = (UNIT_SLUG, _topic_key("Templates"))
    out = _render(
        by_unit={UNIT_SLUG: [e1, e2, e3]},
        by_topic={
            tkey_rotas: [e1, e2, e3],   # e3 faz overflow aqui (cap = 2)
            tkey_templates: [e3],       # e3 é legítima e única aqui
        },
    )

    lines = out.splitlines()

    # Sob "Rotas HTTP": 2 linhas de apoio (Ref1, Ref2) + overflow de +1.
    rotas_idx = next(i for i, ln in enumerate(lines) if "Rotas HTTP" in ln and "[ ]" in ln)
    templates_idx = next(i for i, ln in enumerate(lines) if "Templates" in ln and "[ ]" in ln)
    rotas_block = "\n".join(lines[rotas_idx + 1:templates_idx])
    assert "📖 Apoio: Ref1 (repo)" in rotas_block
    assert "📖 Apoio: Ref2 (repo)" in rotas_block
    assert "(+1 referência(s) em content/BIBLIOGRAPHY.md)" in rotas_block

    # "Templates" DEVE ter uma linha de apoio com Ref3 (e3 é legítima e única aqui).
    templates_block = "\n".join(lines[templates_idx + 1:])
    assert "📖 Apoio: Ref3 (repo)" in templates_block

    # e3 emitida como linha 📖 Apoio exatamente 1 vez (sob Templates), e não
    # reaparece no nível da unidade (topic_anchored a exclui do leftover).
    assert out.count("📖 Apoio: Ref3 (repo)") == 1


def test_prefixed_accented_topic_matches_under_topic_bullet():
    """Regressão E2E: tópico com prefixo numérico + acento ("3.2 Funções de Hash")
    deve casar com a chave JÁ NORMALIZADA do índice ("funcoes de hash") e a linha
    de apoio deve aparecer SOB o bullet do tópico — não solta no fim da unidade.

    Com o bug antigo (_norm_topic), o renderer produzia "3.2 funções de hash" e
    o índice "funcoes de hash" → MISMATCH → ref caía no balde da unidade."""
    from src.builder.core.reference_navigation import _topic_key

    # Segundo tópico ("Colisões") cria um discriminante posicional: com o fix a
    # linha de apoio fica ENTRE "Funções de Hash" e "Colisões"; com o bug ela cai
    # no balde da unidade (leftover), DEPOIS de "Colisões".
    teaching_plan = """
### Unidade 1 - Estruturas
- 3.2 Funções de Hash
- 3.3 Colisões
"""
    profile = SubjectProfile(
        name="Estruturas",
        slug="estruturas",
        syllabus="",
        teaching_plan=teaching_plan,
    )
    unit_slug = _normalize_unit_slug("Unidade 1 - Estruturas")

    # Índice na forma de PRODUÇÃO: computed_ref_topics já normalizado.
    tkey = (unit_slug, _topic_key("Funções de Hash"))  # == (unit_slug, "funcoes de hash")
    assert tkey[1] == "funcoes de hash"
    ref = {"entry_id": "e1", "title": "HashRef", "source_path": "u", "type": "doc",
           "concepts": ["hash"], "topics": ["funcoes de hash"], "unit_slug": unit_slug}
    idx = {"by_unit": {unit_slug: [ref]}, "by_topic": {tkey: [ref]}}

    course_meta = {"course_name": "Estruturas", "_reference_nav_index": idx}
    out = course_map_md(course_meta, profile)

    assert "📖 Apoio: HashRef" in out

    lines = out.splitlines()
    hash_idx = next(
        i for i, ln in enumerate(lines)
        if "Funções de Hash" in ln and "📖 Apoio" not in ln
    )
    colisoes_idx = next(
        i for i, ln in enumerate(lines)
        if "Colisões" in ln and "📖 Apoio" not in ln
    )
    apoio_idx = next(i for i, ln in enumerate(lines) if "📖 Apoio: HashRef" in ln)

    # A linha de apoio deve estar SOB "Funções de Hash" — antes de "Colisões",
    # não solta no fim da unidade.
    assert hash_idx < apoio_idx < colisoes_idx


import json


def test_wiring_builds_index_and_injects(tmp_path):
    """O índice construído de manifest.json + references_curation.json em disco
    deve mapear refs corretamente (contrato usado pelo wiring de pedagogical_regeneration)."""
    from src.builder.core.reference_navigation import build_unit_topic_reference_index
    from src.builder.core.reference_summary import load_reference_curation, write_reference_curation

    root = tmp_path
    (root / "course").mkdir(parents=True, exist_ok=True)
    manifest = {"entries": [
        {"id": "e1", "title": "Flask", "source_path": "https://github.com/pallets/flask",
         "file_type": "github-repo", "category": "referencias"},
    ]}
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    write_reference_curation(root, {"entries": {
        "e1": {"computed_ref_unit": "web", "computed_ref_topics": ["Rotas HTTP"],
               "ref_concepts": ["Flask"], "ref_summary": "x", "content_hash": "h", "matcher_version": 1},
    }})

    entries = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    idx = build_unit_topic_reference_index(entries, load_reference_curation(root))
    assert idx["by_unit"]["web"][0]["entry_id"] == "e1"
    assert ("web", "rotas http") in idx["by_topic"]
