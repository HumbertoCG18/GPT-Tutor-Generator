"""Fase 3 — comportamento de faixa em resolve_unit_block_tags.

DOIS niveis de teste:

1. Wiring band-mapping (stub do select_probable_period_for_entry_fn): controla a
   confianca devolvida e checa SO que confidence_band -> computed_block_band esta
   fiado certo (alta/media). NAO prova o comportamento de "sempre atribui" porque
   o stub ja devolve um period nao-vazio — por isso NAO basta para a claim da
   spec.
2. Integracao com o SCORER REAL (src.builder.engine._select_probable_period_for_entry):
   material FRACO (sem data, titulo generico, unidade ambigua) + >=2 blocos
   instrucionais. O portao best>=0.95 do scorer recusa (period vazio); a spec
   (linhas 92-94/127-130) exige que MESMO assim se atribua o melhor bloco com
   band media/baixa (flag de revisao), nunca orfao quando ha bloco. Orfao so
   quando NAO existe nenhum bloco instrucional.
"""

from src.builder.engine import _select_probable_period_for_entry
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags
from src.builder.routing.thresholds import BAND_HIGH, BAND_LOW


def _entry(entry_id="e1", title="Material"):
    return {
        "id": entry_id,
        "title": title,
        "category": "material-de-aula",
        "file_type": "pdf",
        "source_path": f"/tmp/{entry_id}.pdf",
        "tags": "",
        "manual_tags": [],
        "auto_tags": [],
        "manual_unit_slug": "",
        "manual_timeline_block_id": "",
    }


def _stub_unit_match(slug, confidence, ambiguous=False):
    class M:
        pass
    m = M()
    m.slug = slug
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


def _stub_topic_match(slug="", confidence=0.0, ambiguous=True):
    class M:
        pass
    m = M()
    m.topic_slug = slug
    m.topic_label = slug
    m.unit_slug = ""
    m.confidence = confidence
    m.ambiguous = ambiguous
    m.reasons = []
    return m


# Um bloco instrucional presente no timeline_index (period_label deve casar com
# o period que o stub do scorer devolve, para o id ser resolvido).
_INSTRUCTIONAL_BLOCK = {
    "id": "bloco-01",
    "period_label": "16/03/2026 a 18/03/2026",
    "administrative_only": False,
}


def _run(period_fn_return, *, blocks=(_INSTRUCTIONAL_BLOCK,)):
    entries = [_entry()]
    return resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": list(blocks)},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-01", confidence=0.40, ambiguous=True
        ),
        select_probable_period_for_entry_fn=lambda **kw: period_fn_return,
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )[0]


# --- (1) Wiring band-mapping: SO prova confidence_band -> computed_block_band.
# O stub devolve period nao-vazio, entao isto NAO exercita o "sempre atribui".

def test_wiring_high_confidence_maps_to_band_alta():
    out = _run(("16/03/2026 a 18/03/2026", BAND_HIGH + 0.2, False, []))
    assert out["computed_block_id"] == "bloco-01"
    assert out["computed_block_band"] == "alta"


def test_wiring_medium_confidence_maps_to_band_media():
    midpoint = (BAND_HIGH + BAND_LOW) / 2.0
    out = _run((_INSTRUCTIONAL_BLOCK["period_label"], midpoint, True, []))
    assert out["computed_block_id"] == "bloco-01"
    assert out["computed_block_band"] == "media"


# --- (2) SCORER REAL: a claim de fato da spec (sempre atribui o melhor bloco).

# Material FRACO: sem data, titulo generico, nenhuma pista distintiva. O scorer
# real vai dar best<0.95 -> portao recusa (period vazio). Antes do fix isso
# virava orfao (RED); depois cai no fallback "pega o melhor".
_WEAK_ENTRY = {
    "id": "weak-1",
    "title": "Material",
    "category": "material-de-aula",
    "file_type": "pdf",
    "source_path": "/tmp/weak-1.pdf",
    "tags": "",
    "manual_tags": [],
    "auto_tags": [],
    "manual_unit_slug": "",
    "manual_timeline_block_id": "",
    "manual_subunit_slug": "",
}

# Dois blocos instrucionais reais (rows com conteudo; nenhum casa o material) e
# AMBOS na MESMA unidade — assim o boost/penalidade de unidade incide igual nos
# dois e a margem entre eles fica minima: o material fraco genuinamente nao
# distingue os blocos, exatamente o caso "baixa/media" da spec. (Com unidades
# diferentes, o boost on-unit criaria um vencedor com margem enorme -> "alta",
# que e correto mas nao e o cenario marginal que queremos exercitar aqui.)
_BLOCKS_TWO = [
    {
        "id": "bloco-01",
        "period_label": "09/03/2026 a 11/03/2026",
        "unit_slug": "unidade-01",
        "unit_confidence": 0.9,
        "administrative_only": False,
        "rows": [
            {"index": 1, "date_text": "09/03/2026", "content": "Aula expositiva geral"},
            {"index": 2, "date_text": "11/03/2026", "content": "Aula expositiva geral"},
        ],
    },
    {
        "id": "bloco-02",
        "period_label": "16/03/2026 a 18/03/2026",
        "unit_slug": "unidade-01",
        "unit_confidence": 0.9,
        "administrative_only": False,
        "rows": [
            {"index": 3, "date_text": "16/03/2026", "content": "Aula expositiva geral"},
            {"index": 4, "date_text": "18/03/2026", "content": "Aula expositiva geral"},
        ],
    },
]


def _run_real(blocks):
    return resolve_unit_block_tags(
        [dict(_WEAK_ENTRY)],
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": list(blocks)},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m: _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(
            "unidade-01", confidence=0.40, ambiguous=True
        ),
        # SCORER REAL — injeta todos os callables reais (via engine).
        select_probable_period_for_entry_fn=_select_probable_period_for_entry,
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "material generico sem pistas",
    )[0]


def test_real_scorer_weak_material_still_assigns_block_with_review_band():
    # Material fraco + 2 blocos instrucionais: o portao do scorer recusa, mas a
    # spec exige atribuir o melhor. RED antes do fix (orfao), GREEN depois.
    out = _run_real(_BLOCKS_TWO)
    assert out["computed_block_id"] != "", (
        "material fraco com blocos presentes nao pode virar orfao (spec 92-94/127-130); "
        f"got computed_block_id={out['computed_block_id']!r}"
    )
    assert out["computed_block_id"] in {"bloco-01", "bloco-02"}
    assert out["computed_block_band"] in {"media", "baixa"}, (
        f"baixa confianca deve cair em media/baixa (flag de revisao); "
        f"got band={out['computed_block_band']!r} conf={out['computed_block_confidence']!r}"
    )


def test_real_scorer_orphan_only_when_no_instructional_block():
    # Sem nenhum bloco instrucional -> orfao legitimo: sem id e band fica "".
    out = _run_real([])
    assert out["computed_block_id"] == ""
    assert out["computed_block_band"] == ""
