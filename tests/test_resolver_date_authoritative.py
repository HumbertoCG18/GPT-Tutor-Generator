"""Tier 2 do concept_resolver: DATA autoritativa (fecha o gap do comentário
"card/data autoritativo" — só card estava implementado).

Caso real (SO 0704-exemplo-threads-em-java, ruling do user 2026-08-17): o nome
do arquivo carrega a data da aula ("07.04 ..."); o bloco de PROVA vence no
concept-match porque seu topic cobre a união das unidades (atrator). Data
STRONG (dentro do período de um bloco) deve entrar no pool autoritativo como
card-evidence, vencendo o atrator de conceito.
"""
from src.builder.routing.concept_resolver import resolve_material_assignment


def _block(bid, uuid, start, end, kind="class", unit="", topic=""):
    return {
        "id": bid, "block_uuid": uuid, "kind": kind, "unit_slug": unit,
        "period_start": start, "period_end": end,
        "period_label": f"{start}..{end}",
        "primary_topic_label": topic, "topic_text": topic,
        "topics": [topic] if topic else [], "aliases": [],
        "topic_candidates": [], "card_evidence": [], "sessions": [],
        "source_rows": [],
    }


def _signals(title_text):
    return {
        "title_text": title_text,
        "markdown_headings_text": "",
        "markdown_lead_text": "",
        "markdown_text": "",
        "category_text": "",
        "manual_tags_text": "",
        "auto_tags_text": "",
        "legacy_tags_text": "",
        "tags_text": "",
        "raw_text": title_text,
        "tool_tags_text": "",
        "moodle_label_text": "",
        "image_description_text": "",
    }


def test_data_strong_no_periodo_vence_atrator_de_conceito():
    """Entry "07 04 exemplo threads" com conteudo que casa o topic da PROVA
    (uniao de tudo): sem o tier de data, a prova vence; com data autoritativa,
    o bloco da aula de 07/04 vence."""
    aula = _block("bloco-06", "u-aula", "2026-04-07", "2026-04-09",
                  topic="sincronizacao deadlock")
    prova = _block("bloco-12", "u-prova", "2026-05-07", "2026-05-07",
                   kind="assessment",
                   topic="threads java exemplo processos sincronizacao deadlock")
    entry = {"id": "e1", "title": "07.04 Exemplo threads em Java",
             "category": "codigo-professor", "auto_tags": [], "manual_tags": [],
             "tags": ""}

    out = resolve_material_assignment(
        entry, [prova, aula], units=[],
        signals=_signals("07 04 exemplo threads em java"),
    )
    assert out["block_id"] in ("bloco-06", "u-aula"), out
    assert out["method"] == "date"


def test_sem_data_concept_decide_como_antes():
    aula = _block("bloco-06", "u-aula", "2026-04-07", "2026-04-09",
                  topic="sincronizacao deadlock")
    outra = _block("bloco-02", "u-outra", "2026-03-10", "2026-03-12",
                   topic="threads java exemplo")
    entry = {"id": "e2", "title": "Exemplo threads em Java",
             "category": "codigo-professor", "auto_tags": [], "manual_tags": [],
             "tags": ""}

    out = resolve_material_assignment(
        entry, [aula, outra], units=[],
        signals=_signals("exemplo threads em java"),
    )
    assert out["block_id"] in ("bloco-02", "u-outra"), out
    assert out["method"] == "concept-fused"


def test_data_so_no_markdown_nao_e_autoritativa():
    """Data dentro do CONTEUDO (enunciado de trabalho: data de entrega/prova)
    NAO vira tier — 'due nunca decide sozinho' (spec Tier 2 categoria). Segue
    valendo apenas como boost no fused (comportamento pre-existente).
    Casos reais: ES2 t1_2026_1 (03/07 no enunciado) e TCC Trabalho T2 (12/06)."""
    aula = _block("bloco-19", "u-aula", "2026-05-15", "2026-05-22",
                  topic="reducoes np completude trabalho")
    entrega = _block("bloco-25", "u-entrega", "2026-06-12", "2026-06-12",
                     kind="deliverable", topic="entrega")
    entry = {"id": "e4", "title": "Trabalho T2 - Enunciado",
             "category": "trabalhos", "auto_tags": [], "manual_tags": [],
             "tags": ""}
    sig = _signals("trabalho t2 enunciado")
    sig["markdown_text"] = "reducoes np completude entrega ate 12/06 trabalho"

    out = resolve_material_assignment(entry, [aula, entrega], units=[], signals=sig)
    assert out["method"] == "concept-fused"
    assert out["block_id"] in ("bloco-19", "u-aula"), out


def test_data_no_meio_do_titulo_e_autoritativa():
    """Data DD.MM (2 dígitos) em QUALQUER posição do título cru vira tier —
    o separador real sobrevive no texto cru (dates.py _DM_SEP_RE)."""
    aula = _block("bloco-06", "u-aula", "2026-04-07", "2026-04-09",
                  topic="sincronizacao deadlock")
    prova = _block("bloco-12", "u-prova", "2026-05-07", "2026-05-07",
                   kind="assessment",
                   topic="threads java exemplo processos sincronizacao deadlock")
    entry = {"id": "e5", "title": "Exemplo threads em Java 07.04",
             "category": "codigo-professor", "auto_tags": [], "manual_tags": [],
             "tags": ""}

    out = resolve_material_assignment(
        entry, [prova, aula], units=[],
        signals=_signals("exemplo threads em java 07 04"),
    )
    assert out["method"] == "date"
    assert out["block_id"] in ("bloco-06", "u-aula"), out


def test_numero_de_secao_nao_e_data():
    """"Aula 5.4"/"2.1" = numeração de seção (1 dígito) — NUNCA vira tier,
    mesmo que 5.4 mapeasse pra 05/04 dentro de um período."""
    aula = _block("bloco-06", "u-aula", "2026-04-01", "2026-04-09",
                  topic="sincronizacao deadlock")
    outra = _block("bloco-02", "u-outra", "2026-03-10", "2026-03-12",
                   topic="threads java exemplo")
    entry = {"id": "e6", "title": "Aula 5.4 threads em Java",
             "category": "codigo-professor", "auto_tags": [], "manual_tags": [],
             "tags": ""}

    out = resolve_material_assignment(
        entry, [aula, outra], units=[],
        signals=_signals("aula 5 4 threads em java"),
    )
    assert out["method"] == "concept-fused"
    assert out["block_id"] in ("bloco-02", "u-outra"), out


def test_data_fora_de_qualquer_periodo_nao_e_autoritativa():
    """Data year-less que nao cai em periodo nenhum (mes fora): boost fraco/zero
    nao cria pool autoritativo — concept decide."""
    aula = _block("bloco-06", "u-aula", "2026-04-07", "2026-04-09",
                  topic="sincronizacao deadlock")
    outra = _block("bloco-02", "u-outra", "2026-03-10", "2026-03-12",
                   topic="threads java exemplo")
    entry = {"id": "e3", "title": "12.09 Exemplo threads em Java",
             "category": "codigo-professor", "auto_tags": [], "manual_tags": [],
             "tags": ""}

    out = resolve_material_assignment(
        entry, [aula, outra], units=[],
        signals=_signals("12 09 exemplo threads em java"),
    )
    assert out["method"] == "concept-fused"
    assert out["block_id"] in ("bloco-02", "u-outra"), out
