from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope

BLOCKS = [
    {"id": "bloco-01", "period_start": "2026-03-02", "topic_text": "introducao"},
    {"id": "bloco-02", "period_start": "2026-03-04", "topic_text": "logica predicados"},
    {"id": "bloco-05", "period_start": "2026-04-06", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-06", "label": "inducao estrutural"}]},
    {"id": "bloco-06", "period_start": "2026-04-13", "topic_text": "provas inducao",
     "sessions": [{"date": "2026-04-13", "label": "inducao arvores"}]},
]
CBM = {
    "Provas por Indução": {"block_ids": ["bloco-05", "bloco-06"], "source": "manual"},
    "Bibliografia-Livros": {"block_ids": [], "source": "manual"},
}


def _ctx():
    return MotorContext.from_artifacts(blocks=BLOCKS, card_block_map=CBM, lessons_index={})


def test_bibliografia_routes_out_of_motor():
    assert is_out_of_disamb_scope({"category": "bibliografia"}) is True
    eng = AnchorEngine()
    assert eng.resolve({"category": "bibliografia", "source_section": "Bibliografia-Livros"}, _ctx()) is None


def test_d6_trabalho_prova_tde_out_of_disambiguator():
    assert is_out_of_disamb_scope({"category": "trabalhos"}) is True
    assert is_out_of_disamb_scope({"category": "provas"}) is True
    assert is_out_of_disamb_scope({"source_section": "TDE 3 - entrega"}) is True
    assert is_out_of_disamb_scope({"category": "material"}) is False


def test_no_window_returns_none_funil():
    eng = AnchorEngine()
    assert eng.resolve({"category": "material", "source_section": "Card Sem Janela"}, _ctx()) is None


def test_multiblock_window_runs_disambiguator_and_sets_provider():
    eng = AnchorEngine()
    d = eng.resolve(
        {"category": "material", "source_section": "Provas por Indução",
         "title": "Prova por indução em árvores"},
        _ctx(),
    )
    assert d is not None
    assert d.block_ref == "bloco-06"      # session-label 'arvores' discrimina
    assert d.provider == "manual"
    assert d.method == "disamb"


def test_janela_com_ref_fantasma_nao_vira_confianca():
    """Ref obsoleto no card_block_map (drift) não pode virar confiança "alta"
    sem evidência de token. Janela com 2 refs onde só 1 resolve deve cair no
    scoring normal (1 bloco resolvível => s2=0 => flagado/media), não no
    fast-path janela-1. Janela 100% fantasma (nenhum ref resolve) => funil."""
    ctx = MotorContext.from_artifacts(
        blocks=BLOCKS,
        card_block_map={
            **CBM,
            "Janela Fantasma": {"block_ids": ["bloco-05", "bloco-fantasma"], "source": "manual"},
            "Janela Toda Fantasma": {"block_ids": ["bloco-x", "bloco-y"], "source": "manual"},
        },
        lessons_index={},
    )
    eng = AnchorEngine()

    d = eng.resolve(
        {"category": "material", "source_section": "Janela Fantasma",
         "title": "Prova por indução"},
        ctx,
    )
    assert d is not None
    assert d.band != "alta"
    assert d.flag is True

    assert eng.resolve(
        {"category": "material", "source_section": "Janela Toda Fantasma",
         "title": "Qualquer coisa"},
        ctx,
    ) is None


# TIER 3 Tests (FASE 3 Task 4)
from src.builder.routing.motor.contracts import AnchorDecision, MotorContext
from src.builder.routing.motor import anchor_engine as ae


class _FakeVoter:
    def __init__(self, answer):
        self.answer = answer
        self.seen = []
        self.calls = 0

    def vote(self, entry, window, ctx, markdown=""):
        self.calls += 1
        self.seen.append(str(entry.get("id")))
        return self.answer


def _tier3_ctx():
    return MotorContext.from_artifacts(
        blocks=[{"id": "bloco-01"}, {"id": "bloco-02"}],
        card_block_map={}, lessons_index={})


def _stub_cascade(monkeypatch, *, flag: bool, band: str = "baixa"):
    monkeypatch.setattr(ae, "resolve_window",
                        lambda e, c: (["bloco-01", "bloco-02"], "topic"))
    monkeypatch.setattr(
        ae, "disambiguate",
        lambda e, w, c, m, provider="": AnchorDecision(
            block_ref="bloco-01", conf=0.9 if band == "alta" else 0.2,
            band=band, flag=flag, window=list(w)))


def test_tier3_flagged_voto_valido_ancora_media(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter).resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert d.block_ref == "bloco-02"
    assert d.band == "media" and d.flag is False
    assert d.provider == "llm" and d.method == "llm"
    assert voter.seen == ["e1"]


def test_tier3_voto_none_mantem_flag(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    d = ae.AnchorEngine(voter=_FakeVoter(None)).resolve(
        {"id": "e1", "category": "m"}, _tier3_ctx())
    assert d.block_ref == "bloco-01" and d.flag is True and d.provider == "topic"


def test_tier3_sem_voter_byte_identico(monkeypatch):
    _stub_cascade(monkeypatch, flag=True)
    d0 = ae.AnchorEngine().resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert d0.block_ref == "bloco-01" and d0.flag is True and d0.band == "baixa"


def test_tier3_nao_flagado_fora_de_serie_nao_vota(monkeypatch):
    _stub_cascade(monkeypatch, flag=False, band="alta")
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter).resolve({"id": "e1", "category": "m"}, _tier3_ctx())
    assert voter.seen == [] and d.block_ref == "bloco-01" and d.band == "alta"


def test_tier3_membro_de_serie_vota_mesmo_sem_flag(monkeypatch):
    _stub_cascade(monkeypatch, flag=False, band="alta")
    voter = _FakeVoter("bloco-02")
    d = ae.AnchorEngine(voter=voter, series_ids={"e1"}).resolve(
        {"id": "e1", "category": "m"}, _tier3_ctx())
    assert voter.seen == ["e1"]
    assert d.block_ref == "bloco-02" and d.band == "media" and d.provider == "llm"


def _ctx_janela_unica():
    return MotorContext.from_artifacts(
        blocks=BLOCKS,
        card_block_map={**CBM, "aula unica": {"block_ids": ["bloco-01"], "source": "manual"}},
        lessons_index={},
    )


def test_janela_1_nao_entra_no_voto_mesmo_em_serie():
    """D4×janela-1 (decisão D-A, 10/07): voto com 1 candidato desflaga sem
    informação nova. |janela|==1 fica FORA do escopo do voter; a decisão
    determinística (e o FLAG, se houver) sobrevive pra fila humana."""
    ctx = _ctx_janela_unica()          # card 'aula unica' -> ['bloco-01']
    entry = {"id": "e1", "title": "Aula 3", "source_section": "aula unica",
             "category": "materiais"}
    voter = _FakeVoter("bloco-01")
    eng = AnchorEngine(voter=voter, series_ids={"e1"})
    d = eng.resolve(entry, ctx)
    assert d is not None and d.block_ref
    assert voter.calls == 0            # janela-1: voter NUNCA chamado
    assert d.provider != "llm" and d.method != "llm"
