# Fixture destilada do caso REAL bloco-15/16/17/20 do MF pos-U1
# (docs/reports/2026-08-07-spec-review-unidades.md §A2/A3: empate de CAMINHO
# 4+0+0 vs 3+1+0; matriz real em 2026-08-06-task3-colisao-rotulo-mf.md).
from src.builder.timeline.unit_matcher import assign_units_positional


def _unit(slug, *labels):
    return {"slug": slug, "title": "", "topics": [{"label": l, "aliases": []} for l in labels]}


def _block(bid, topic_text):
    return {"id": bid, "topic_text": topic_text, "sessions": []}


UNITS = [
    _unit("unidade-01", "logica predicados verificacao formal"),
    _unit("unidade-02", "exercicios logica verificacao programas hoare"),
    _unit("unidade-03", "logica temporal modelos verificacao"),
]
BLOCKS = [
    _block("b15", "hoare programas logica"),                                  # aff [1,3,1]
    _block("b16", "exercicios ferramenta logica modelos temporal verificacao"),  # aff [2,3,4]
    _block("b17", "exercicios revisao"),                                      # aff [0,1,0]
    _block("b20", "devolucao provas"),                                        # aff [0,0,0]
]


def test_empate_de_caminho_vence_sinal_concentrado():
    # caminho "ficar": 3+1+0 == caminho "avancar": 4+0+0 -> soma empata;
    # soma de quadrados 9+1 < 16 -> avancar vence
    out = dict(zip([b["id"] for b in BLOCKS], assign_units_positional(BLOCKS, UNITS)))
    assert out["b16"] == ("unidade-03", 0.6)
    assert out["b15"] == ("unidade-02", 0.6)


def test_sem_empate_nada_muda():
    # b17 com 2 tokens de u02 -> ficar (3+2) > avancar (4+0): sem empate,
    # comportamento identico ao atual
    blocks = [
        _block("b15", "hoare programas logica"),
        _block("b16", "exercicios ferramenta logica modelos temporal verificacao"),
        _block("b17", "exercicios hoare revisao"),
    ]
    out = dict(zip([b["id"] for b in blocks], assign_units_positional(blocks, UNITS)))
    assert out["b16"] == ("unidade-02", 0.4)


def test_sem_sinal_nenhum_continua_fallback():
    blocks = [_block("b1", "xyzabc qwerty")]
    assert assign_units_positional(blocks, UNITS) == []
