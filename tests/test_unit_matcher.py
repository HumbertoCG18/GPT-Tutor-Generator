"""Matcher posicional bloco->unidade: afinidade token-overlap + anchor-fill."""

import json as _json
from pathlib import Path as _Path


def _unit(slug, title, *topic_labels):
    return {"slug": slug, "title": title,
            "topics": [{"label": t, "aliases": []} for t in topic_labels]}


def _block(*session_labels, topic_text=""):
    return {"sessions": [{"label": s} for s in session_labels], "topic_text": topic_text}



def test_serializer_keeps_auto_unit_slug():
    from src.builder.timeline.index import _serialize_timeline_index
    blk = {"id": "b", "kind": "class", "unit_slug": "u1", "auto_unit_slug": "u1",
           "period_start": "2026-03-01", "period_end": "2026-03-01"}
    out = _serialize_timeline_index({"version": 4, "blocks": [blk]})
    assert out["blocks"][0].get("auto_unit_slug") == "u1"


from src.builder.timeline.unit_matcher import assign_units_positional

UNITS3 = [
    _unit("u1", "Alfa", "alfa primeiro tema", "alfa segundo tema"),
    _unit("u2", "Beta", "beta terceiro tema", "beta quarto tema"),
    _unit("u3", "Gama", "gama quinto tema", "gama sexto tema"),
]


def test_positional_strong_anchors_in_order():
    blocks = [_block("alfa primeiro"), _block("beta terceiro"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert [s for s, _ in out] == ["u1", "u2", "u3"]


def test_positional_fills_no_signal_block_between_anchors():
    # meio sem sinal -> herda a unidade da ancora anterior (u1)
    blocks = [_block("alfa primeiro"), _block("xyz sem sinal"), _block("alfa segundo")]
    out = assign_units_positional(blocks, UNITS3)
    assert [s for s, _ in out] == ["u1", "u1", "u1"]


def test_positional_weak_out_of_order_anchor_demoted():
    # bloco 2 tem leve sinal de u1 mas vem depois de u2 -> rebaixado, segue u2
    blocks = [_block("beta terceiro tema"), _block("alfa"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[0][0] == "u2" and out[2][0] == "u3"
    assert out[1][0] == "u2"  # nao recua pra u1 (ancora fraca rebaixada)


def test_positional_empty_when_no_anchor():
    blocks = [_block("xyz"), _block("qwe")]
    assert assign_units_positional(blocks, UNITS3) == []


def test_positional_empty_when_single_unit():
    assert assign_units_positional([_block("alfa")], [UNITS3[0]]) == []


def test_positional_pre_first_anchor_blocks_get_first_unit():
    # ancora so no ultimo bloco -> blocos anteriores herdam a 1a unidade, nao a do anchor
    blocks = [_block("xyz sem sinal"), _block("gama quinto")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[0][0] == "u1"   # primeira unidade (curso comeca no inicio)
    assert out[1][0] == "u3"   # ancora


def test_positional_strong_out_of_order_dp_prefers_global_optimum():
    # DP global (substitui o anchor-fill guloso): bloco0 tem leve sinal de u3
    # (aff [1,1,3]) e bloco1 tem sinal FORTE de u1 (aff [4,1,1]). Sob a restricao
    # monotonica, o otimo global e u1/u1 (soma 5) -- o bloco forte domina e puxa o
    # fraco anterior pra baixo, em vez de travar o cursor em u3 como o guloso fazia.
    # Esta e exatamente a robustez a ancora espuria que o DP introduz.
    blocks = [_block("gama quinto tema"), _block("alfa primeiro tema segundo")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[0][0] == "u1"
    assert out[1][0] == "u1"


def test_positional_dp_resists_spurious_early_high_unit():
    # bloco0 fraco numa unidade tardia; blocos seguintes fortes na unidade do meio
    # -> DP mantem os fortes na unidade certa (nao trava na tardia). Caso real TCC:
    # turing (aff forte u2) nao deve virar u4 por uma ancora espuria anterior.
    blocks = [_block("gama"), _block("beta terceiro quarto"), _block("beta terceiro quarto")]
    out = assign_units_positional(blocks, UNITS3)
    assert out[1][0] == "u2"
    assert out[2][0] == "u2"


def test_tokens_expands_e_s_abbreviation_before_filtering():
    # Causa-raiz SO: label SARC "Gerencia de E/S" normaliza pra "gerencia de e s";
    # "e"/"s" isolados (1 char) sao descartados pelo filtro len>=3 -> sessoes de
    # E/S ficam sem nenhum token de "entrada"/"saida" pra casar com a unidade-07.
    # Fix: bigrama "e s" (2 tokens de 1 char adjacentes) expande pra
    # "entrada saida" ANTES do filtro de tamanho.
    from src.builder.timeline.unit_matcher import _tokens
    toks = _tokens("gerencia de e s")
    assert "entrada" in toks and "saida" in toks
    assert "e" not in toks and "s" not in toks  # letras soltas continuam descartadas


def test_tokens_e_s_expansion_does_not_touch_unrelated_text():
    # Nao-regressao: texto sem a abreviacao mantem tokens identicos.
    from src.builder.timeline.unit_matcher import _tokens
    assert _tokens("gerencia de memoria virtual") == {"gerencia", "memoria", "virtual"}
    assert _tokens("chamadas de sistema") == {"chamadas", "sistema"}


def test_real_so_e_s_sessions_overlap_unidade07_after_expansion():
    # Assinatura real da unidade-07 (SO .content_taxonomy.json, conferido em disco
    # 2026-08-10): titulo "Unidade 07 - Gerencia de entrada e saida" + topicos
    # "Dispositivos de entrada e saida"/"Controladores dos dispositivos"/etc.
    # Blocos reais (SO .timeline_index.json, bloco-16/17, conferidos em disco):
    # sessao unica com label "gerencia de e s"/"gerencia de e s aula".
    from src.builder.timeline.unit_matcher import _block_tokens, _unit_tokens

    u07 = {
        "slug": "unidade-07-gerencia-de-entrada-e-saida",
        "title": "Unidade 07 \u2013 Ger\u00eancia de entrada e sa\u00edda",
        "topics": [
            {"label": "**2.1** Dispositivos de entrada e sa\u00edda", "aliases": []},
            {"label": "**2.2** Controladores dos dispositivos", "aliases": []},
            {"label": "**2.3** _Drivers_ dos dispositivos", "aliases": []},
            {"label": "**2.4** Estudo de casos", "aliases": []},
        ],
    }
    u05 = {
        "slug": "unidade-05-gerencia-de-memoria",
        "title": "Unidade 05 \u2013 Ger\u00eancia de Mem\u00f3ria",
        "topics": [{"label": "**6.2** Mem\u00f3ria virtual", "aliases": []}],
    }
    bloco16 = {"sessions": [{"label": "gerencia de e s"}], "topic_text": "gerencia enunciado"}
    bloco17 = {"sessions": [{"label": "gerencia de e s aula"}], "topic_text": "gerencia"}

    for block in (bloco16, bloco17):
        overlap_u07 = _block_tokens(block) & _unit_tokens(u07)
        overlap_u05 = _block_tokens(block) & _unit_tokens(u05)
        assert len(overlap_u07) >= 2, f"overlap fraco com u07: {overlap_u07}"
        assert len(overlap_u07) > len(overlap_u05), (
            f"u07 ({overlap_u07}) deveria vencer u05 ({overlap_u05}) sem empate"
        )


def test_real_so_bloco16_17_positional_unit_is_unidade07():
    # Sonda canonica (regra U2 da campanha): mesmo caminho de rebuild_diff.py.
    import os
    from src.models.core import SubjectStore
    import scripts.course_probe as course_probe
    base = os.environ.get("TUTOR_COURSES_DIR", r"C:\Users\Humberto\Documents\GitHub")
    repo = _Path(base) / "Sistemas-Operacionais-Tutor"
    if not repo.exists():
        import pytest
        pytest.skip("corpus indisponivel")
    sp = SubjectStore().get("Sistemas Operacionais")
    idx = course_probe.compute_production_index(sp)
    # Chave por uuid, nao por id posicional (bloco-NN desloca a cada split de
    # curadoria -- licao do drift do gold MF, mesmo motivo do gold_units_*.csv
    # ser keyed por block_uuid). uuids reais das 2 sessoes de E/S do SO.
    by_uuid = {b.get("block_uuid"): b for b in idx["blocks"]}
    for uuid in ("2455cd0a-52aa-4753-bf07-df6bbc8a0408", "b6a5d63d-a959-485e-961e-94dbb7749dad"):
        b = by_uuid[uuid]
        assert b.get("auto_unit_slug") == "unidade-07-gerencia-de-entrada-e-saida", (
            f"{uuid} ({b.get('id')}): auto_unit_slug={b.get('auto_unit_slug')!r}"
        )


def test_real_metodos_hoare_unit_sane():
    import os
    from src.models.core import SubjectStore
    import src.builder.engine as engine
    base = os.environ.get("TUTOR_COURSES_DIR", r"C:\Users\Humberto\Documents\GitHub")
    repo = _Path(base) / "Metodos-Formais-Tutor"
    if not repo.exists():
        import pytest
        pytest.skip("corpus indisponivel")
    sp = SubjectStore().get("Metodos-Formais")
    cm = _json.loads((repo / "manifest.json").read_text(encoding="utf-8")).get("course", {})
    ctx = engine._build_file_map_timeline_context_from_course({**cm, "_repo_root": repo}, sp, content_taxonomy=None)
    blocks = ctx["timeline_index"]["blocks"]
    hoare = next((b for b in blocks if "hoare" in (b.get("primary_topic_label") or "").lower()), None)
    if hoare:
        assert "verificacao-de-programas" in (hoare.get("unit_slug") or "")


def test_positional_confidence_is_fill_when_assigned_not_argmax():
    # bloco0: argmax=u3 (aff=3), mas tambem toca u1 (aff=2) e u2 (aff=1).
    # bloco1: argmax=u1 (aff=4). DP prefere u1/u1 (soma 6) sobre u3/u3 (soma 4).
    # -> bloco0 atribuido a u1 com afinidade 2 (positiva, nao eh o argmax u3).
    # BUG atual: usa margem global (top1-top2=2) e row[u1]=2>0 -> CONF_ANCHOR (0.6).
    # FIX correto: assigned != argmax -> CONF_FILL (0.4).
    from src.builder.timeline.unit_matcher import CONF_FILL, CONF_ANCHOR, CONF_STRONG
    blocks = [_block("gama quinto tema alfa"), _block("alfa primeiro segundo tema")]
    out = assign_units_positional(blocks, UNITS3)
    slugs = [s for s, _ in out]
    confs = [c for _, c in out]
    # bloco0 deve ser atribuido a u1 (nao ao seu argmax u3)
    assert slugs[0] == "u1", f"esperado u1, obtido {slugs[0]}"
    # bloco0 tem argmax em u3, nao u1 -> deve receber CONF_FILL
    assert confs[0] == CONF_FILL, (
        f"bloco0 atribuido a nao-argmax deveria ter CONF_FILL={CONF_FILL}, "
        f"obtido {confs[0]} (CONF_ANCHOR={CONF_ANCHOR}, CONF_STRONG={CONF_STRONG})"
    )
