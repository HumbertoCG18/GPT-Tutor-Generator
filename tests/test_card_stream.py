"""Fase 3b (item 3): o card do Moodle lido como DOCUMENTO ORDENADO = provider de janela ("card").

Blocos: shape conferido em `Metodos-Formais-Tutor/course/.timeline_index.json` (03/09/2026): id, block_uuid,
kind ('class'/'assessment'), period_start/end, primary_topic_label, topic_text, sessions[{id,date,kind,label}].
Entries: campos do manifest real (moodle_section_index/module_index/week_label gravados pela Fase 3a; textos
de label no formato MF/ES2 "Semana dd/mm/aaaa a dd/mm/aaaa: (dd/mm/aaaa): topico" e SO "dd/mm Topico").
"""
import json

from src.builder.routing.motor.anchor_engine import AnchorEngine
from src.builder.routing.motor.card_stream import card_windows
from src.builder.routing.motor.contracts import MotorContext


def _block(n, date, label, topic, kind="class"):
    return {"id": f"bloco-{n:02d}", "block_uuid": f"uuid-{n:02d}", "kind": kind, "period_start": date, "period_end": date,
            "primary_topic_label": topic, "topic_text": topic.lower(),
            "sessions": [{"id": f"bloco-{n:02d}-sessao-{date}", "date": date, "kind": kind, "label": label}]}


BLOCKS = [
    _block(3, "2026-03-16", "sintaxe da logica proposicional", "Logica proposicional sintaxe"),
    _block(4, "2026-03-23", "semantica da logica proposicional", "Logica proposicional semantica"),
    _block(5, "2026-03-30", "inducao estrutural", "Inducao"),
    _block(6, "2026-04-06", "prova p1", "Prova P1", kind="assessment"),
]
W1 = "Semana 16/03/2026 a 20/03/2026: (16/03/2026): sintaxe da logica proposicional"
W2 = "Semana 23/03/2026 a 27/03/2026: (23/03/2026): semantica da logica proposicional"


def _ctx(card_block_map=None):
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=card_block_map or {}, lessons_index={},
                                       course_name="Metodos Formais")


def _e(eid, label, idx, week, cat="material-de-aula", sec="Logica"):
    return {"id": eid, "title": label, "category": cat, "file_type": "pdf", "source_section": sec,
            "moodle_label": label, "moodle_section_index": 5, "moodle_module_index": idx, "moodle_week_label": week}


def test_single_dated_week_label_gives_blocks_of_that_week():
    assert card_windows([_e("a", "Exercicios", 1, W1)], _ctx()) == {"a": ["bloco-03"]}


def test_run_of_weeks_aligns_materials_in_order_by_tokens():
    ents = [_e("s", "Sintaxe", 1, W1 + " || " + W2), _e("m", "Semantica", 2, W1 + " || " + W2)]
    assert card_windows(ents, _ctx()) == {"s": ["bloco-03"], "m": ["bloco-04"]}


def test_streams_align_independently_by_category():
    # sem fluxos, "Semantica" (1o) puxaria "Sintaxe" (2o) para a mesma semana pela monotonia
    ents = [_e("l1", "Semantica", 1, W1 + " || " + W2, cat="listas"), _e("a1", "Sintaxe", 2, W1 + " || " + W2)]
    assert card_windows(ents, _ctx()) == {"l1": ["bloco-04"], "a1": ["bloco-03"]}


def test_dated_module_name_without_year_uses_modal_year():
    assert card_windows([_e("x", "23/03 Semantica", 1, "23/03 Semantica")], _ctx()) == {"x": ["bloco-04"]}


def test_week_range_drops_blocks_that_never_host_material():
    week = "Semana 30/03/2026 a 06/04/2026: (30/03/2026): inducao; (06/04/2026): prova"
    assert card_windows([_e("i", "Inducao", 1, week)], _ctx()) == {"i": ["bloco-05"]}


def test_entry_without_week_label_or_position_has_no_window():
    ents = [_e("n", "Nada", 1, ""), {"id": "v", "title": "Velho", "category": "material-de-aula", "source_section": "Logica"}]
    assert card_windows(ents, _ctx()) == {}


def _engine_ctx():
    return _ctx({"Logica": {"block_ids": ["bloco-03", "bloco-04"], "source": "labels"}})


def test_engine_uses_card_window_when_decision_is_flagged():
    ctx = _engine_ctx()
    entry = _e("ex", "Exercicios", 3, W2)
    base = AnchorEngine().resolve(entry, ctx)
    assert base is not None and base.flag and base.provider == "labels"   # precondicao: janela [03, 04] sem token = duvida
    ctx._card_windows_cache = {"ex": ["bloco-04"]}
    d = AnchorEngine().resolve(entry, ctx)
    # estrutura estreitou (bloco da semana), texto nao confirmou (sem token discriminante) -> fica flagado
    assert (d.block_ref, d.provider, d.method, d.band, d.flag) == ("bloco-04", "card", "janela-1", "media", True)


def test_engine_card_window_is_confident_only_with_discriminant_token():
    # sem janela alguma (card "Outro" fora do card_block_map) + card [04] + token "semantica" so no bloco 04
    ctx = _ctx()
    ctx._card_windows_cache = {"ex2": ["bloco-04"]}
    d = AnchorEngine().resolve(_e("ex2", "Exercicios de semantica", 3, W2, sec="Outro"), ctx)
    # confiante (sem flag), mas banda "media": precisao medida das decisoes do card = 8/11
    assert (d.block_ref, d.provider, d.method, d.band, d.flag) == ("bloco-04", "card", "janela-1", "media", False)


def test_engine_keeps_confident_decision_over_card():
    ctx = _engine_ctx()
    ctx._card_windows_cache = {"sem": ["bloco-03"]}
    d = AnchorEngine().resolve(_e("sem", "Logica proposicional semantica", 3, W1), ctx)
    assert (d.block_ref, d.provider, d.flag) == ("bloco-04", "labels", False)


def test_engine_card_window_fills_missing_window():
    ctx = _ctx()
    entry = _e("solto", "Exercicios", 3, W2, sec="Outro")
    assert AnchorEngine().resolve(entry, ctx) is None   # precondicao: sem card_block_map, sem data, sem topico = funil
    ctx._card_windows_cache = {"solto": ["bloco-04"]}
    d = AnchorEngine().resolve(entry, ctx)
    assert (d.block_ref, d.provider, d.flag) == ("bloco-04", "card", True)   # bloco pela estrutura, duvida honesta


def test_apply_computes_card_windows_from_the_entries(tmp_path):
    from src.builder.routing.motor.apply import apply_anchor_engine
    (tmp_path / "course").mkdir()
    (tmp_path / "course" / ".timeline_index.json").write_text(json.dumps({"blocks": BLOCKS}), encoding="utf-8")
    ents = [_e("ex", "Exercicios", 3, W2, sec="Outro")]
    ents[0]["source_path"] = str(tmp_path / "ex.pdf")
    apply_anchor_engine(ents, tmp_path, "Metodos Formais")
    assert ents[0]["temporal_block_provider"] == "card"
    assert ents[0]["temporal_block_id"] == "uuid-04"


class _Voter:
    def __init__(self, ref):
        self.ref, self.calls = ref, []

    def vote(self, entry, window, ctx, markdown=""):
        self.calls.append(list(window))
        return self.ref


def test_engine_card_never_preempts_the_llm_vote():
    # curada (03/09): card antes do voter estreitava para 1 bloco, o LLM nao votava e a regua caiu 199 -> 187
    ctx = _engine_ctx()
    ctx._card_windows_cache = {"ex": ["bloco-04"]}
    voter = _Voter("bloco-03")
    d = AnchorEngine(voter=voter).resolve(_e("ex", "Exercicios", 3, W2), ctx)
    assert (d.block_ref, d.provider, d.method, d.flag) == ("bloco-03", "llm", "llm", False)
    assert voter.calls == [["bloco-03", "bloco-04"]]   # votou na janela ORIGINAL, nao na do card


def test_engine_card_acts_when_the_voter_has_no_answer():
    ctx = _engine_ctx()
    ctx._card_windows_cache = {"ex": ["bloco-04"]}
    d = AnchorEngine(voter=_Voter(None)).resolve(_e("ex", "Exercicios", 3, W2), ctx)
    assert (d.block_ref, d.provider, d.flag) == ("bloco-04", "card", True)


def test_engine_keeps_original_provider_when_card_agrees_and_stays_flagged():
    # SO curado (03/09): data/janela-1 flagada e card com o MESMO bloco -> 8 entries so trocavam o nome do provider
    ctx = _ctx()
    entry = _e("d", "23/03 Exercicios", 3, "23/03 Exercicios", sec="Outro")
    base = AnchorEngine().resolve(entry, ctx)
    assert (base.block_ref, base.provider, base.flag) == ("bloco-04", "data", True)   # precondicao
    ctx._card_windows_cache = {"d": ["bloco-04"]}
    d = AnchorEngine().resolve(entry, ctx)
    assert (d.block_ref, d.provider, d.flag) == ("bloco-04", "data", True)


# --- Fase 3b, item 4: secao 0 do Moodle (area geral do curso) sem sinal temporal -> bloco de apresentacao ---

def _geral(eid, title, sec_idx):
    e = _e(eid, title, 2, "", sec="Informações Gerais")
    e["moodle_section_index"] = sec_idx
    return e


def test_general_section_without_window_goes_to_first_class_block():
    d = AnchorEngine().resolve(_geral("programa", "Programa", 0), _ctx())
    assert (d.block_ref, d.provider, d.method, d.band, d.flag) == ("bloco-03", "secao-geral", "secao-geral", "media", False)


def test_non_general_section_without_window_stays_funil():
    assert AnchorEngine().resolve(_geral("programa", "Programa", 5), _ctx()) is None


def test_general_section_with_a_window_follows_the_cascade():
    # secao 0 COM janela (card_block_map labels [03, 04]) e titulo que nomeia o bloco 04: a cascata decide, nao a secao 0
    e = _e("sem", "Logica proposicional semantica", 2, "", sec="Logica"); e["moodle_section_index"] = 0
    d = AnchorEngine().resolve(e, _engine_ctx())
    assert (d.block_ref, d.provider) == ("bloco-04", "labels")


# --- ancora datada (modulo "dd/mm Topico") = FAIXA da secao para os modulos sem data; texto decide dentro dela ---

def test_undated_module_after_anchors_gets_the_section_anchor_range_not_the_last_anchor():
    ents = [_e("a1", "16/03 Sintaxe", 1, "16/03 Sintaxe"),                    # ancora propria -> so o seu bloco
            _e("a2", "23/03 Semantica", 2, "23/03 Semantica"),                # ancora propria
            _e("ex", "Exemplos de sintaxe", 3, "23/03 Semantica")]            # sem data: herda o texto da ultima ancora
    out = card_windows(ents, _ctx())
    assert out["a1"] == ["bloco-03"] and out["a2"] == ["bloco-04"]
    assert out["ex"] == ["bloco-03", "bloco-04"]   # faixa da secao; o disambiguator decide pelo texto ("sintaxe" -> 03)


def test_entry_with_its_own_date_in_the_title_keeps_its_own_block_even_without_moodle_label():
    # SO curado (03/09): "14 04 Troca de Mensagens" (M365, moodle_label vazio) caiu na faixa [06, 07] e regrediu 199 -> 198
    e = _e("t", "23 03 Semantica", 2, "23/03 Semantica"); e["moodle_label"] = ""
    ents = [_e("a1", "16/03 Sintaxe", 1, "16/03 Sintaxe"), e]
    assert card_windows(ents, _ctx())["t"] == ["bloco-04"]
