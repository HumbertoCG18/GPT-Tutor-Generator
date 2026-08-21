"""Kinds que nunca hospedam material saem da janela do motor (2026-08-21).

Medido nos 200 golds de bloco dos 5 cursos: nenhum bloco-gold e feriado,
atendimento, oficina ou evento academico. TCC `aula-17`: card manual
"Semana 12" = [oficina, aula de Cook-Levin]; o slide ia para a oficina.
"""
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.window_provider import drop_never_hosts, resolve_window
from src.builder.routing.motor.anchor_engine import AnchorEngine
from src.builder.timeline.kinds import NEVER_HOSTS_MATERIAL_KINDS


def _ctx():
    blocks = [
        {"id": "bloco-20", "kind": "academic_event", "period_start": "2026-05-27"},
        {"id": "bloco-21", "kind": "workshop", "period_start": "2026-05-29",
         "sessions": [{"date": "2026-05-29", "label": "oficina de problemas entrega"}]},
        {"id": "bloco-22", "kind": "class", "period_start": "2026-06-03",
         "sessions": [{"date": "2026-06-03", "label": "teorema cook levin"}]},
        {"id": "bloco-23", "kind": "holiday", "period_start": "2026-06-05"},
    ]
    cbm = {"Semana 12 - NP-completude": {"source": "manual", "block_ids": ["bloco-21", "bloco-22"]},
           "So oficina": {"source": "manual", "block_ids": ["bloco-21"]}}
    return MotorContext.from_artifacts(blocks=blocks, card_block_map=cbm, lessons_index={})


def test_conjunto_medido():
    assert {"holiday", "office_hours", "workshop", "academic_event"} <= NEVER_HOSTS_MATERIAL_KINDS
    # aparecem no gold: seguem elegiveis
    assert not ({"class", "overview", "assessment", "review", "deliverable", "suspended"} & NEVER_HOSTS_MATERIAL_KINDS)


def test_janela_do_card_perde_a_oficina_e_vira_janela_1():
    ctx = _ctx()
    win, prov = resolve_window({"title": "Aula 17 - NP-Completude", "source_section": "Semana 12 - NP-completude"}, ctx)
    assert (win, prov) == (["bloco-22"], "manual")
    d = AnchorEngine().resolve({"title": "Aula 17 - NP-Completude", "source_section": "Semana 12 - NP-completude",
                                "category": "material-de-aula"}, ctx)
    assert d.block_ref == "bloco-22" and d.method == "janela-1"


def test_janela_so_de_kinds_proibidos_fica_como_esta():
    ctx = _ctx()
    assert drop_never_hosts(["bloco-21"], ctx) == ["bloco-21"]
    win, _ = resolve_window({"title": "x", "source_section": "So oficina"}, ctx)
    assert win == ["bloco-21"]


def test_funil_exclui_feriado_e_evento():
    class _V:
        def __init__(self): self.windows = []
        def vote(self, entry, window, ctx, markdown=""):
            self.windows.append(list(window)); return window[0]
    v = _V()
    AnchorEngine(voter=v).resolve_funnel({"id": "e", "category": "material-de-aula"}, _ctx())
    assert v.windows == [["bloco-22"]]


def test_janela_so_com_ref_fantasma_cai_no_llm_funil():
    """card_block_map com uuid obsoleto: a janela existe mas nenhum ref resolve.
    'Funil honesto' e o llm-funil (janela = blocos elegiveis do curso), nao
    None — IA `ag-feito-em-aula` perdia o temporal inteiro."""
    ctx = MotorContext.from_artifacts(
        blocks=[{"id": "bloco-12", "kind": "class", "period_start": "2026-05-18"},
                {"id": "bloco-13", "kind": "academic_event", "period_start": "2026-05-27"}],
        card_block_map={"Semana 13": {"source": "labels", "block_ids": ["uuid-obsoleto", "bloco-13"]}},
        lessons_index={})
    entry = {"id": "ag", "category": "codigo-professor", "source_section": "Semana 13", "title": "AG feito em aula"}
    assert AnchorEngine().resolve(entry, ctx) is None          # sem voter: limpo, como antes

    class _V:
        def __init__(self): self.windows = []
        def vote(self, entry, window, ctx, markdown=""):
            self.windows.append(list(window)); return window[0]
    v = _V()
    d = AnchorEngine(voter=v).resolve(entry, ctx)
    assert d is not None and d.method == "llm-funil" and d.block_ref == "bloco-12"
    assert v.windows == [["bloco-12"]]                          # evento fora do funil tambem
