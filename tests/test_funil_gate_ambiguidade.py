"""Fix 2b (Plano B, investigacao 2026-08-05 §CASO 2b): o funil-base aceitava um
palpite de select_probable_period_for_entry com confianca 0.0/ambiguo como
atribuicao dura (content_taxonomy.py:1224 gateava so `if _period:`, ignorando
`_p_ambig` e sem piso de confianca). Corrigido para `if _period and not
_p_ambig and p_conf > 0:` — quando o palpite e ambiguo ou tem confianca zero,
cai no `_best_instructional_block_fallback` (scorer real sobre TODOS os
blocos), que aqui escolhe o bloco com sinal de verdade (block_good) em vez do
bloco cujo period_label so por acaso bateu com o palpite (block_bad, sem
nenhum sinal textual).

`block_method` NAO distingue os dois ramos (ambos gravam "scorer_only" —
verificado por leitura direta do codigo, linhas 1233 e 1248): o sinal
observavel real e QUAL bloco vence e o `computed_block_confidence` (0.0 cego
vs a confianca honesta do scorer real).
"""
from src.builder.extraction.content_taxonomy import resolve_unit_block_tags


def _make_minimal_entry(entry_id: str, title: str) -> dict:
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


def _stub_unit_match(slug="", confidence=0.0, ambiguous=True):
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


# block_bad "ganha" pelo period_label cego (o que o palpite ambiguo devolve);
# sua row nao tem NENHUM sinal textual em comum com a entry. block_good nao
# bate o period_label do palpite, mas sua row repete o titulo da entry, entao
# o scorer real (score_entry_against_timeline_block, via
# _best_instructional_block_fallback) o prefere de verdade. rows[].content e
# obrigatorio: timeline_block_rows_for_scoring devolve [] sem isso e o score
# vira 0.0 pra ambos (empate cego pelo scorer tambem, nao so pelo gate).
BLOCK_BAD = {
    "id": "bloco-01", "block_uuid": "uuid-bad", "period_label": "1 dia . x",
    "topic_text": "", "sessions": [], "rows": [{"content": "conteudo nada a ver aqui"}],
}
BLOCK_GOOD = {
    "id": "bloco-02", "block_uuid": "uuid-good", "period_label": "1 dia . y",
    "topic_text": "grafos coloracao arestas cubicas", "sessions": [],
    "rows": [{"content": "Grafos Coloracao Arestas Cubicas"}],
}


def _run(select_period_return):
    entries = [_make_minimal_entry("e1", "Grafos Coloracao Arestas Cubicas")]
    result = resolve_unit_block_tags(
        entries,
        course_meta={},
        subject_profile=None,
        build_file_map_unit_index_from_course_fn=lambda c, s: [],
        build_file_map_timeline_context_from_course_fn=lambda c, s: {
            "blocks_by_unit": {},
            "unassigned_blocks": [],
            "timeline_index": {"blocks": [BLOCK_BAD, BLOCK_GOOD]},
        },
        iter_content_taxonomy_topics_fn=lambda t: [],
        auto_map_entry_subtopic_fn=lambda e, t, m, winning_unit_slug="": _stub_topic_match(),
        auto_map_entry_unit_fn=lambda e, u, m, ti, learned_unit_boosts=None: _stub_unit_match(),
        select_probable_period_for_entry_fn=lambda **kw: select_period_return,
        resolve_entry_manual_timeline_block_fn=lambda e, tc: None,
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )
    return result[0]


def test_gate_refuses_ambiguous_zero_confidence_guess_and_falls_to_fallback():
    """_p_ambig=True, p_conf=0.0 (a exata forma do bug, investigacao TCC/MF): o
    gate deve RECUSAR o palpite cego (bloco-01, so por period_label) e cair no
    _best_instructional_block_fallback, que escolhe bloco-02 pelo sinal real."""
    entry = _run(("1 dia . x", 0.0, True, None))
    assert entry["computed_block_id"] == "uuid-good", (
        "gate aceitou o palpite ambiguo/conf-zero (bloco-01) em vez de cair "
        "no fallback honesto (bloco-02)"
    )
    assert entry["computed_block_confidence"] > 0.0, (
        "fallback deveria produzir confianca real (relative_margin_confidence "
        "do scorer), nao herdar o 0.0 do palpite recusado"
    )


def test_gate_refuses_non_ambiguous_but_zero_confidence_guess():
    """Caso SO exercicios-p2 medido na investigacao: ambig=False mas conf=0.0
    tambem tem que ser recusado — SO piso de confianca cobre esse caso (o
    guard so-de-ambiguidade nao pega)."""
    entry = _run(("1 dia . x", 0.0, False, None))
    assert entry["computed_block_id"] == "uuid-good"


def test_gate_accepts_confident_unambiguous_guess():
    """Palpite com confianca real e sem ambiguidade continua aceito
    diretamente (comportamento correto preservado, sem re-tuning)."""
    entry = _run(("1 dia . x", 0.4, False, None))
    assert entry["computed_block_id"] == "uuid-bad"
    assert entry["computed_block_confidence"] == 0.4
