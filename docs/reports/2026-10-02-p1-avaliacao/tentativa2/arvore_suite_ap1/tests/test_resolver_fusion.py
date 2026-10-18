"""Oraculo da Task 2.2: fusao de sinais + tiers + confianca/conflito.

Dados REAIS do censo do Metodos-Formais (tests/fixtures/eval/
metodos_formais_golden.json + censo code_curation 17/06). As fixtures sao os
blocos reais (topic_text/unit_slug/sessions/period) e os entries reproduzem o
que o funil ve hoje (title via split_camel_case, source_section, extensao ->
ferramenta) + o voto do LLM (primary/secondary/confidence) do censo.

Eixo do teste (spec 4.3): quando o overlap de conceito e FORTE, ele domina o
voto do LLM (mesmo quando o LLM erra); quando o conceito e fraco/empatado, o
voto do LLM desempata.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.builder.core.semantic_config import merge_semantic_profile
from src.builder.text.normalize import normalize_match_text, split_camel_case
from src.builder.routing.concept_resolver import resolve_material_assignment


_GOLDEN = json.loads(
    (Path(__file__).parent / "fixtures" / "eval" / "metodos_formais_golden.json").read_text(
        encoding="utf-8"
    )
)
_BLOCKS_BY_ID = {b["id"]: b for b in _GOLDEN["timeline"]["blocks"]}


def _tool_tokens():
    return {
        normalize_match_text(t)
        for t in (merge_semantic_profile().get("known_tools") or [])
        if normalize_match_text(t)
    }


def _instructional_blocks():
    return [
        b
        for b in _GOLDEN["timeline"]["blocks"]
        if b.get("unit_slug") and str(b.get("kind") or "") == "class"
    ]


def _units():
    # Unidades do plano (slug + tokens), suficiente para o resolver mapear
    # unit do bloco e detectar conflito bloco-unit != topico-unit.
    return [
        {"slug": "unidade-01-metodos-formais", "title": "Especificacao e prova",
         "topics": [{"label": "conjuntos indutivos"}, {"label": "inducao arvores"},
                    {"label": "provadores interativos teoremas isabelle"}]},
        {"slug": "unidade-02-verificacao-de-programas", "title": "Verificacao de programas",
         "topics": [{"label": "logica de hoare"}, {"label": "correcao parcial total terminacao"},
                    {"label": "invariantes de laco"}, {"label": "dafny colecoes arrays"},
                    {"label": "orientacao a objetos dafny ghosts"}]},
        {"slug": "unidade-03-verificacao-de-modelos", "title": "Verificacao de modelos",
         "topics": [{"label": "model checking logica temporal"}]},
    ]


def _signals(title, source_section="", raw_target="", markdown=""):
    # Reproduz o subconjunto de collect_entry_unit_signals que a fusao consome.
    ext_tool = ""
    suffix = Path(raw_target).suffix.lower()
    if suffix == ".thy":
        ext_tool = "isabelle"
    elif suffix == ".dfy":
        ext_tool = "dafny"
    return {
        "title_text": normalize_match_text(split_camel_case(title)),
        "markdown_text": normalize_match_text(markdown),
        "markdown_headings_text": "",
        "markdown_lead_text": "",
        "category_text": "",
        "manual_tags_text": "",
        "auto_tags_text": "",
        "tool_tags_text": ext_tool,
        "legacy_tags_text": "",
        "tags_text": "",
        "raw_text": normalize_match_text(raw_target),
        "combined_text": normalize_match_text(" ".join([split_camel_case(title), source_section, markdown])),
        "image_description_text": "",
    }


def _entry(title, source_section="", raw_target="", concepts=None):
    return {
        "title": title,
        "source_section": source_section,
        "raw_target": raw_target,
        "concepts": concepts or [],
    }


def _llm(primary, *, confidence=0.8, secondary=None):
    return {
        "primary_block_id": primary,
        "secondary_block_ids": list(secondary or []),
        "block_match_confidence": confidence,
    }


def _resolve(title, *, section="", raw="", llm=None, concepts=None, blocks=None):
    return resolve_material_assignment(
        _entry(title, section, raw, concepts),
        blocks if blocks is not None else _instructional_blocks(),
        _units(),
        signals=_signals(title, section, raw),
        llm_curation=llm,
    )


# ----------------------------------------------------------------------------
# DEVE CORRIGIR (censo: Gemini certo, funil escreve o errado por viel de
# ferramenta/forma; o resolver de conceito + voto LLM deve corrigir).
# ----------------------------------------------------------------------------
def test_fix_arvores_thy_picks_05_concept_tie_llm_breaks():
    # concept empata 04==05 (token "arvores"); ferramenta isabelle NAO elege
    # o 06 (down-weight da 2.1); o voto LLM (05) desempata.
    a = _resolve("arvores", section="Provas por Inducao", raw="arvores.thy", llm=_llm("bloco-05"))
    assert a["block_id"] == "bloco-05"
    assert a["unit_slug"] == "unidade-01-metodos-formais"


def test_fix_intro_thy_picks_04_concept_absent_llm_carries():
    # title "intro" nao gera token de conceito; overlap 0 em todo bloco ->
    # o voto LLM (04) carrega a decisao.
    a = _resolve("intro", section="Provas por Inducao", raw="intro.thy", llm=_llm("bloco-04"))
    assert a["block_id"] == "bloco-04"


def test_fix_listas_thy_picks_05_concept_absent_llm_carries():
    a = _resolve("listas", section="Provas por Inducao", raw="listas.thy", llm=_llm("bloco-05"))
    assert a["block_id"] == "bloco-05"
    # listas era o confiante-errado band-alta do funil; aqui nao deve eleger 06.
    assert a["block_id"] != "bloco-06"


def test_fix_classes_parte1_picks_15_unit02_no_section_llm_only():
    # sem source_section, sem token de conceito; SO o voto LLM (15) decide,
    # e a unidade vem do bloco vencedor (unidade-02, nao a 03 do funil).
    a = _resolve("classes_parte1", section="", raw="classes_parte1.zip",
                 llm=_llm("bloco-15"),
                 blocks=[_BLOCKS_BY_ID[b] for b in ("bloco-11", "bloco-12", "bloco-13", "bloco-15", "bloco-16")])
    assert a["block_id"] == "bloco-15"
    assert a["unit_slug"] == "unidade-02-verificacao-de-programas"


# ----------------------------------------------------------------------------
# NAO PODE REGREDIR (funil acerta hoje; concept exato deve VENCER um voto LLM
# errado).
# ----------------------------------------------------------------------------
def test_noregress_colecoes_arrays_13_concept_beats_wrong_llm():
    a = _resolve("colecoes_arrays", section="Verificacao de Programas", raw="colecoes_arrays.zip",
                 llm=_llm("bloco-04", confidence=0.85))
    assert a["block_id"] == "bloco-13"


def test_noregress_colecoes_conjuntos_13():
    a = _resolve("colecoes_conjuntos", section="Verificacao de Programas", raw="colecoes_conjuntos.zip",
                 llm=_llm("bloco-04", confidence=0.85))
    assert a["block_id"] == "bloco-13"


def test_noregress_invariantes_11_concept_beats_wrong_llm():
    a = _resolve("invariantes", section="Verificacao de Programas", raw="invariantes.zip",
                 llm=_llm("bloco-04", confidence=0.85))
    assert a["block_id"] == "bloco-11"


def test_noregress_hoare_10_concept_beats_wrong_llm():
    a = _resolve("hoare", section="Verificacao de Programas", raw="hoare.zip",
                 llm=_llm("bloco-11", confidence=0.85))
    assert a["block_id"] == "bloco-10"


def test_noregress_exercicios_conjuntos_13_llm_agrees():
    a = _resolve("exercicios_conjuntos", section="Verificacao de Programas", raw="exercicios_conjuntos.zip",
                 llm=_llm("bloco-13", confidence=0.8))
    assert a["block_id"] == "bloco-13"


def test_noregress_terminacao_11():
    # concept empata 11==12 ("terminacao"); o voto LLM erra (04). Sinal de
    # desempate principiado: o bloco que TAMBEM casa "correcao/parcial/laco"
    # (o material de terminacao do plano vive com correcao parcial/total).
    a = _resolve("CorrecaoTerminacao", section="Verificacao de Programas",
                 raw="CorrecaoTerminacao.pdf", llm=_llm("bloco-04", confidence=0.7))
    assert a["block_id"] == "bloco-11"


# ----------------------------------------------------------------------------
# DEVE FLAGAR CONFLITO (block-unit != topic-unit; subunit nao escapa).
# ----------------------------------------------------------------------------
def test_conflict_logicadehoare_block_u1_topic_u2():
    # "logica de hoare" e topico da unidade-02 no PLANO, mas o bloco agendado
    # (bloco-10) esta na unidade-01 (SARC). bloco vence a unit (proposta 9),
    # mas o conflito tem de ser FLAGADO e a subunit nunca pode ser de u2.
    a = _resolve("LogicaDeHoare", section="Verificacao de Programas",
                 raw="LogicaDeHoare.pdf", llm=_llm("bloco-11", confidence=0.6))
    assert a["block_id"] == "bloco-10"
    assert a["unit_slug"] == "unidade-01-metodos-formais"
    assert a["conflict"] is not None
    # subunit (se atribuida) NUNCA pode ser de outra unidade.
    sub = a.get("subunit_slug") or ""
    assert sub == "" or "unidade-02" not in str(a["conflict"].get("topic_unit", ""))  # documenta a unit do topico


def test_no_conflict_when_block_and_topic_units_agree():
    # colecoes -> bloco-13 (u2) e o topico tambem e u2: SEM conflito.
    a = _resolve("colecoes_arrays", section="Verificacao de Programas", raw="colecoes_arrays.zip",
                 llm=_llm("bloco-13", confidence=0.8))
    assert a["block_id"] == "bloco-13"
    assert a["conflict"] is None


# ----------------------------------------------------------------------------
# Confianca + tiers
# ----------------------------------------------------------------------------
def test_manual_override_wins_all_tiers():
    a = _resolve("qualquer", section="", raw="x.pdf", llm=_llm("bloco-13"),
                 blocks=_instructional_blocks())
    # injeta override manual via entry
    a = resolve_material_assignment(
        {"title": "qualquer", "manual_timeline_block_id": "bloco-06"},
        _instructional_blocks(), _units(),
        signals=_signals("qualquer"), llm_curation=_llm("bloco-13"),
    )
    assert a["block_id"] == "bloco-06"
    assert a["method"] == "manual"
    assert a["confidence"] >= 0.99


def test_moodle_label_drives_block_via_concept():
    # alavanca 1: entry com title generico ("exemplos", sem token), mas o
    # moodle_label "Logica de Floyd-Hoare" casa o topic_text do bloco-10 -> o
    # overlap elege o 10 mesmo com o voto LLM errado (11).
    blocks = [_BLOCKS_BY_ID[b] for b in ("bloco-10", "bloco-11", "bloco-13")]
    sig = _signals("exemplos", raw_target="exemplos.zip")
    sig["moodle_label_text"] = normalize_match_text("Exemplos (Logica de Floyd-Hoare)")
    a = resolve_material_assignment(
        _entry("exemplos", raw_target="exemplos.zip"),
        blocks, _units(), signals=sig, llm_curation=_llm("bloco-11", confidence=0.6))
    assert a["block_id"] == "bloco-10"


def test_tool_unit_conflict_caps_confidence():
    # alavanca tool->unit: um .dfy (dafny=u2) que vence um bloco de u1 (Isabelle)
    # é conflito de UNIDADE pela ferramenta -> banda capada (não-alta), mesmo o
    # label "Tipos Indutivos" empurrando lexicalmente p/ bloco-04 (u1). Degradação
    # honesta: o bloco fica, mas a confiança cai (não vira confiante-errado).
    blocks = [_BLOCKS_BY_ID[b] for b in ("bloco-04", "bloco-13")]
    sig = _signals("tiposindutivos", source_section="Verificacao de Programas",
                   raw_target="tiposindutivos.dfy")
    sig["moodle_label_text"] = normalize_match_text("Exemplos (Tipos Indutivos)")
    a = resolve_material_assignment(
        _entry("tiposindutivos", raw_target="tiposindutivos.dfy"),
        blocks, _units(), signals=sig, llm_curation=_llm("bloco-04", confidence=0.85))
    assert a["block_id"] == "bloco-04"          # label+LLM elegem o 04 (u1)
    assert a["band"] != "alta"                  # mas tool dafny (u2) conflita -> capa
    assert a["conflict"] is not None
    assert a["conflict"].get("kind") == "block_unit_vs_tool_unit"


def test_confidence_band_present_and_consistent():
    a = _resolve("colecoes_arrays", section="Verificacao de Programas", raw="colecoes_arrays.zip",
                 llm=_llm("bloco-13", confidence=0.85))
    assert a["band"] in {"alta", "media", "baixa"}
    assert 0.0 <= a["confidence"] <= 1.0
