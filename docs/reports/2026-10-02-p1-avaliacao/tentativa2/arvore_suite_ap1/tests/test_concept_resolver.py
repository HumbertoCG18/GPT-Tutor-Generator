from src.builder.core.semantic_config import merge_semantic_profile
from src.builder.text.normalize import normalize_match_text
from src.builder.routing.concept_resolver import (
    Assignment,
    concept_token_weights,
    concept_vector,
    resolve_material_assignment,
)


def _known_tool_tokens():
    tools = merge_semantic_profile().get("known_tools") or []
    return {normalize_match_text(tool) for tool in tools if normalize_match_text(tool)}


# Blocos REAIS da unidade-01 do Metodos-Formais (tests/fixtures/eval/
# metodos_formais_golden.json): bloco-04/05 contem "arvores"; "isabelle"
# so aparece no topic_text do bloco-06 (df=1) -> sem o down-weight de
# ferramenta, isabelle vira o token mais "raro" e elege o bloco-06 (o bug).
UNIT1_BLOCKS = [
    {
        "id": "bloco-04",
        "topic_text": "conjuntos indutivos equacoes recursivas arvores",
        "primary_topic_label": "Especificacao de Conjuntos Indutivos",
        "topics": ["conjuntos indutivos equacoes recursivas", "arvores"],
        "aliases": ["conjuntos", "indutivos", "equacoes", "recursivas", "arvores"],
        "sessions": [
            {"label": "conjuntos indutivos e equacoes recursivas aula"},
            {"label": "estudo de caso listas aula"},
            {"label": "estudo de caso arvores aula"},
        ],
    },
    {
        "id": "bloco-05",
        "topic_text": "inducao arvores",
        "primary_topic_label": "Inducao arvores",
        "topics": ["inducao", "inducao arvores"],
        "aliases": ["inducao", "arvores"],
        "sessions": [
            {"label": "provas por inducao aula"},
            {"label": "provas por inducao listas e arvores aula"},
        ],
    },
    {
        "id": "bloco-06",
        "topic_text": "interativa teoremas isabelle",
        "primary_topic_label": "Interativa teoremas isabelle",
        "topics": ["interativa teoremas"],
        "aliases": ["interativa", "teoremas"],
        "sessions": [
            {"label": "provadores de teoremas aula"},
        ],
    },
]


def test_isabelle_bias_guard_block_scope():
    weights = concept_token_weights(
        UNIT1_BLOCKS, scope="block", tool_tokens=_known_tool_tokens()
    )
    # ferramenta uniforme na unidade -> down-weighted a ~0 no escopo de bloco.
    # Isto faz "isabelle" PARAR de eleger o bloco-06.
    assert weights.get("isabelle", 0.0) < 0.01
    # token de TOPICO domina a ferramenta zerada.
    assert weights["arvores"] > weights.get("isabelle", 0.0)
    # "arvores" mantem seu peso IDF positivo (df=2 de 3 -> 0.5 na mecanica
    # espelhada de block_token_weights com IDF_WEIGHT=1.0).
    assert weights["arvores"] > 0.0


def test_tool_discriminates_at_unit_scope():
    # Unidades sinteticas: a ferramenta aparece no texto-de-conceito e
    # DISCRIMINA (Isabelle=u1, Dafny=u2) -> nao deve ser zerada no escopo unit.
    units = [
        {
            "title": "Unidade 01",
            "topics": [
                {"label": "Provadores de teoremas isabelle", "aliases": ["isabelle"]},
            ],
        },
        {
            "title": "Unidade 02",
            "topics": [
                {"label": "Verificacao de programas dafny", "aliases": ["dafny"]},
            ],
        },
    ]
    weights = concept_token_weights(
        units, scope="unit", tool_tokens=_known_tool_tokens()
    )
    # df=1 (so na unidade-01) -> peso IDF cheio (1.0), NAO zerado.
    assert weights.get("isabelle", 0.0) > 0.5


def test_concept_vector_overlap_dedup():
    weights = concept_token_weights(
        UNIT1_BLOCKS, scope="block", tool_tokens=_known_tool_tokens()
    )
    item = {
        "id": "bloco-05",
        "topic_text": "inducao arvores arvores",  # token repetido -> dedup
        "topics": [],
        "aliases": [],
        "sessions": [],
    }
    vector = concept_vector(item, weights)
    # so tokens presentes no item E com peso conhecido.
    assert "arvores" in vector
    assert "inducao" in vector
    assert "isabelle" not in vector
    # dedup: cada token aparece uma vez, com o peso do dict.
    assert vector["arvores"] == weights["arvores"]


def test_assignment_shape_and_stub():
    fields = set(Assignment.__annotations__.keys())
    assert {
        "block_id",
        "unit_slug",
        "confidence",
        "band",
        "method",
        "signals",
        "conflict",
    } <= fields
    # stub: nao wired em producao nesta task (2.1).
    try:
        resolve_material_assignment({}, UNIT1_BLOCKS, [], signals={})
    except NotImplementedError:
        return


def test_pino_manual_em_uuid_vence_tier1():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
        {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
    ]
    entry = {"id": "e1", "manual_timeline_block_id": "u-2"}
    a = resolve_material_assignment(entry, blocks, [], signals={})
    assert a["block_id"] == "u-2"
    assert a["method"] == "manual"
    assert a["confidence"] == 1.0
    assert a["unit_slug"] == "u2"


def test_pino_manual_em_display_segue_valendo():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
        {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
    ]
    entry = {"id": "e1", "manual_timeline_block_id": "bloco-02"}
    a = resolve_material_assignment(entry, blocks, [], signals={})
    assert a["block_id"] == "u-2"          # canonico = uuid do bloco casado
    assert a["method"] == "manual"
    assert a["unit_slug"] == "u2"
