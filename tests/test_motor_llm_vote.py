"""Testes do TIER 3 (llm_vote): cache, chave de conteudo, seed, serie, voto bounded."""
from __future__ import annotations

import json
from pathlib import Path

from src.builder.routing.motor.llm_vote import (
    content_key,
    detect_same_theme_series,
    import_marco1_seed,
    load_material_curation,
    save_material_curation,
)


def _entry(rid: str, source_path: str = "", title: str = "", section: str = "",
           category: str = "material") -> dict:
    return {"id": rid, "source_path": source_path, "title": title or rid,
            "source_section": section, "category": category}


def test_material_curation_path_segue_convencao_code_curation(tmp_path):
    from src.builder.routing.motor.llm_vote import material_curation_path
    assert material_curation_path(tmp_path) == tmp_path / "material_curation.json"


def test_content_key_gemeos_compartilham_chave(tmp_path: Path):
    (tmp_path / "a.pdf").write_bytes(b"mesmo conteudo")
    (tmp_path / "b.pdf").write_bytes(b"mesmo conteudo")
    k1 = content_key(_entry("e1", "a.pdf"), tmp_path)
    k2 = content_key(_entry("e2", "b.pdf"), tmp_path)
    assert k1 == k2 and len(k1) == 32  # md5 hex


def test_content_key_fallback_id_sem_arquivo(tmp_path: Path):
    assert content_key(_entry("orfao", "nao/existe.pdf"), tmp_path) == "orfao"
    assert content_key(_entry("semsrc"), tmp_path) == "semsrc"


def test_cache_roundtrip_e_corrompido(tmp_path: Path):
    path = tmp_path / "material_curation.json"
    assert load_material_curation(path) == {"version": 1, "votes": {}}
    data = {"version": 1, "votes": {"k": {"block_id": "bloco-01"}}}
    save_material_curation(path, data)
    assert load_material_curation(path) == data
    assert not path.with_suffix(".json.tmp").exists()  # write atomico limpa tmp
    path.write_text("{ nao e json", encoding="utf-8")
    assert load_material_curation(path) == {"version": 1, "votes": {}}


def test_import_marco1_seed_rechaveia_por_conteudo(tmp_path: Path):
    (tmp_path / "x.pdf").write_bytes(b"conteudo X")
    entries = {"rid1": _entry("rid1", "x.pdf"), "rid3": _entry("rid3")}
    seed = {
        "rid1": {"block_id": "bloco-05", "confianca": "alta",
                 "justificativa": "j", "model": "gemini-2.5-flash"},
        "rid2": {"block_id": "bloco-01"},                # entry sumiu: pula
        "rid3": {"block_id": "", "erro": "timeout"},     # voto com erro: pula
    }
    votes = import_marco1_seed(seed, entries, tmp_path)
    key = content_key(entries["rid1"], tmp_path)
    assert set(votes) == {key}
    assert votes[key]["block_id"] == "bloco-05"


def test_serie_same_theme_detecta_membros():
    entries = [
        _entry("d1", title="Exercicios Dafny 1", section="Verificacao"),
        _entry("d2", title="Exercicios Dafny 2", section="Verificacao"),
        _entry("solo", title="Prova Especial 9", section="Outra"),
    ]
    assert detect_same_theme_series(entries) == {"d1", "d2"}


def test_serie_exige_ordinais_distintos_e_card():
    entries = [
        _entry("a1", title="Lista 1", section="Card A"),
        _entry("a2", title="Lista 1", section="Card A"),      # mesmo ordinal: nao
        _entry("b1", title="Lista 1", section=""),            # sem card: nao
        _entry("b2", title="Lista 2", section=""),
    ]
    assert detect_same_theme_series(entries) == set()


def test_serie_exclui_fora_de_escopo_d6():
    entries = [
        _entry("t1", title="TDE 1", section="Verificacao", category="trabalhos"),
        _entry("t2", title="TDE 2", section="Verificacao", category="trabalhos"),
    ]
    assert detect_same_theme_series(entries) == set()


# ===== TASK 3 TESTES =====

from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.llm_vote import (
    MD_PROMPT_CAP, LlmVoter, build_vote_prompt, match_window_ref,
)


def _ctx() -> MotorContext:
    blocks = [
        {"id": "bloco-01", "block_uuid": "uuid-1", "period_start": "2026-03-01",
         "period_end": "2026-03-07", "topic_text": "inducao",
         "sessions": [{"date": "2026-03-02"}]},
        {"id": "bloco-02", "block_uuid": "uuid-2", "period_start": "2026-03-08",
         "period_end": "2026-03-14", "topic_text": "hoare", "sessions": []},
    ]
    return MotorContext.from_artifacts(
        blocks=blocks, card_block_map={},
        lessons_index={"2026-03-02": "inducao em listas"},
        course_name="Metodos Formais")


class FakeVotoResp:
    def __init__(self, block_id, confianca="alta", justificativa_curta="j"):
        self.block_id = block_id
        self.confianca = confianca
        self.justificativa_curta = justificativa_curta


class FakeClient:
    model = "fake-model"

    def __init__(self, answers):
        self.answers = list(answers)
        self.prompts = []

    def summarize_bundle(self, bundle_text, schema, system_instruction):
        self.prompts.append((bundle_text, system_instruction))
        a = self.answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a


def test_build_vote_prompt_conteudo_e_cap():
    ctx = _ctx()
    e = _entry("e1", title="Lista Inducao", section="Card X")
    prompt = build_vote_prompt(e, ["bloco-01", "bloco-02"], ctx, "Z" * 9999)
    assert "Lista Inducao" in prompt
    assert "bloco-01" in prompt and "bloco-02" in prompt
    assert "inducao em listas" in prompt          # roteiro via ctx.lessons_index
    assert prompt.count("Z") == MD_PROMPT_CAP     # trecho capado (protocolo MARCO 1)


def test_match_window_ref_bounded():
    ctx = _ctx()
    win = ["bloco-01", "bloco-02"]
    assert match_window_ref("bloco-02", win, ctx) == "bloco-02"
    assert match_window_ref("uuid-1", win, ctx) == "bloco-01"   # casa por uuid
    assert match_window_ref("bloco-99", win, ctx) is None       # fora da janela
    assert match_window_ref("", win, ctx) is None


def test_voter_cache_hit_nao_chama_api(tmp_path: Path):
    ctx = _ctx()
    (tmp_path / "m.pdf").write_bytes(b"conteudo")
    e = _entry("e1", "m.pdf")
    cache = tmp_path / "cur.json"
    key = content_key(e, tmp_path)
    save_material_curation(cache, {"version": 1, "votes": {
        key: {"block_id": "bloco-02", "confianca": "alta"}}})
    client = FakeClient([])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=client)
    assert voter.vote(e, ["bloco-01", "bloco-02"], ctx) == "bloco-02"
    assert voter.calls == 0 and client.prompts == []
    assert voter.has_vote(e)


def test_voter_chama_api_e_persiste(tmp_path: Path):
    ctx = _ctx()
    e = _entry("e1", title="Lista 1")
    cache = tmp_path / "cur.json"
    client = FakeClient([FakeVotoResp("bloco-01")])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=client)
    assert voter.vote(e, ["bloco-01", "bloco-02"], ctx) == "bloco-01"
    assert voter.calls == 1
    saved = load_material_curation(cache)
    assert saved["votes"]["e1"]["block_id"] == "bloco-01"
    assert saved["votes"]["e1"]["model"] == "fake-model"


def test_voter_voto_fora_da_janela_cacheia_mas_nao_ancora(tmp_path: Path):
    ctx = _ctx()
    e = _entry("e1")
    cache = tmp_path / "cur.json"
    client = FakeClient([FakeVotoResp("bloco-99")])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=client)
    assert voter.vote(e, ["bloco-01"], ctx) is None       # bounded: mantem FLAG
    rec = load_material_curation(cache)["votes"]["e1"]
    assert rec["block_id"] == "bloco-99" and rec["window"] == ["bloco-01"]
    # re-rodada com a MESMA janela: cache hit, sem nova chamada (a pergunta e a mesma)
    voter2 = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([]))
    assert voter2.vote(e, ["bloco-01"], ctx) is None
    assert voter2.calls == 0


def test_voter_reperg_quando_a_janela_muda_e_o_voto_ficou_fora(tmp_path: Path):
    """2026-08-21: o voto e por conteudo, a pergunta e sobre uma janela. IA
    `ag-feito`: voto "bloco-13" (evento) ficou fora de toda janela depois do
    filtro de kind e a entry perdia o temporal para sempre. Janela diferente
    (ou desconhecida: cache legado sem "window") com voto fora -> repergunta
    uma vez e regrava; mesma janela -> cache."""
    ctx = _ctx()
    e = _entry("e1")
    cache = tmp_path / "cur.json"
    # cache LEGADO: voto em bloco-02, sem "window"
    save_material_curation(cache, {"version": 1, "votes": {"e1": {"block_id": "bloco-02"}}})
    client = FakeClient([FakeVotoResp("bloco-01")])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=client)
    assert voter.vote(e, ["bloco-01"], ctx) == "bloco-01"   # reperguntou (janela desconhecida, voto fora)
    assert voter.calls == 1
    rec = load_material_curation(cache)["votes"]["e1"]
    assert rec["block_id"] == "bloco-01" and rec["window"] == ["bloco-01"]
    # mesma janela de novo: cache
    voter2 = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([]))
    assert voter2.vote(e, ["bloco-01"], ctx) == "bloco-01" and voter2.calls == 0
    # voto dentro da janela nova (mesmo que a janela tenha mudado): nao repergunta
    voter3 = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([]))
    assert voter3.vote(e, ["bloco-01", "bloco-02"], ctx) == "bloco-01" and voter3.calls == 0


def test_voter_cap_e_erro(tmp_path: Path):
    ctx = _ctx()
    cache = tmp_path / "cur.json"
    client = FakeClient([FakeVotoResp("bloco-01"), FakeVotoResp("bloco-01")])
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, cap=1, client=client)
    assert voter.vote(_entry("e1"), ["bloco-01"], ctx) == "bloco-01"
    assert voter.vote(_entry("e2"), ["bloco-01"], ctx) is None    # cap estourou
    assert voter.skipped_cap == 1
    # erro de API: nao persiste (proxima rodada re-tenta), errors conta
    client2 = FakeClient([RuntimeError("boom")])
    voter2 = LlmVoter({}, cache_path=tmp_path / "c2.json", repo_dir=tmp_path, client=client2)
    assert voter2.vote(_entry("e3"), ["bloco-01"], ctx) is None
    assert voter2.errors == 1
    assert load_material_curation(tmp_path / "c2.json")["votes"] == {}


def test_voter_sem_janela_nao_vota(tmp_path: Path):
    ctx = _ctx()
    client = FakeClient([FakeVotoResp("bloco-01")])
    voter = LlmVoter({}, cache_path=tmp_path / "c.json", repo_dir=tmp_path, client=client)
    assert voter.vote(_entry("e1"), [], ctx) is None
    assert voter.calls == 0 and client.prompts == []


# ===== TASK 4 TESTES =====


def test_persist_merges_disk_state(tmp_path):
    """Duas instancias no MESMO cache: a segunda nao apaga o voto da primeira
    (last-writer-wins morto; review final F3)."""
    cache = tmp_path / "material_curation.json"
    e1, e2 = _entry("a"), _entry("b")
    ctx = _ctx()
    va = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([FakeVotoResp("bloco-01")]))
    vb = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([FakeVotoResp("bloco-01")]))
    va.vote(e1, ["bloco-01"], ctx)          # persiste voto de e1
    vb.vote(e2, ["bloco-01"], ctx)          # vb carregou ANTES do save de va
    final = json.loads(cache.read_text(encoding="utf-8"))["votes"]
    assert len(final) == 2                   # merge, nao overwrite


def test_error_is_logged_not_swallowed(caplog):
    """Item 4: excecao da API vira WARNING com id da entry e tipo do erro
    (o 404 da F3 so foi visto reproduzindo por fora)."""
    class Boom:
        model = "x"
        def summarize_bundle(self, *a, **k):
            raise RuntimeError("404 model retired")
    v = LlmVoter({}, cache_path=Path("nao-usado.json"), repo_dir=Path("."), client=Boom())
    with caplog.at_level("WARNING"):
        got = v.vote(_entry("a"), ["bloco-01"], _ctx())
    assert got is None and v.errors == 1
    assert any("RuntimeError" in r.message and "404" in r.message for r in caplog.records)


def test_no_key_counter_and_round_summary(tmp_path):
    v = LlmVoter({}, cache_path=tmp_path / "c.json", repo_dir=tmp_path, client=None)
    v._client_loaded = True                  # simula get_gemini_client -> None
    assert v.vote(_entry("a"), ["bloco-01"], _ctx()) is None
    s = v.round_summary()
    assert s["no_key"] == 1 and s["calls"] == 0
    assert set(s) == {"calls", "errors", "skipped_cap", "no_key", "cache_hits"}


def test_prune_removes_orphan_keys(tmp_path):
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps({"version": 1, "votes": {
        "viva": {"block_id": "bloco-01"}, "orfa": {"block_id": "bloco-02"}}}),
        encoding="utf-8")
    v = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([FakeVotoResp("bloco-01")]))
    assert v.prune({"viva"}) == 1
    assert set(json.loads(cache.read_text(encoding="utf-8"))["votes"]) == {"viva"}


def test_prune_preserves_concurrent_vote_from_other_instance(tmp_path):
    """Poda de A nao apaga voto que B persistiu depois do load de A
    (merge-on-save tambem no prune; review T4)."""
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps({"version": 1, "votes": {
        "orfa": {"block_id": "bloco-02"}}}), encoding="utf-8")
    a = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([]))
    b = LlmVoter({}, cache_path=cache, repo_dir=tmp_path,
                 client=FakeClient([FakeVotoResp("bloco-01")]))
    b.vote(_entry("viva_b"), ["bloco-01"], _ctx())   # disco: orfa + viva_b; A so viu orfa
    assert a.prune({"viva_b"}) == 1                  # so orfa e stale
    final = json.loads(cache.read_text(encoding="utf-8"))["votes"]
    assert set(final) == {"viva_b"}                  # voto de B sobrevive


def test_voto_cacheado_segue_o_uuid_quando_o_display_renumera(tmp_path: Path):
    """2026-08-25: um split de bloco renumera os bloco-NN seguintes. O voto
    cacheado "bloco-02" (uuid-2 na epoca) passava a apontar para o bloco que
    HOJE se chama bloco-02 — stale silencioso, sem revotar (IA: 3 entries do
    card Semana 15 trocaram de bloco; o sidecar nao mudou). Identidade = uuid."""
    e = _entry("e1", title="Lista 1")
    cache = tmp_path / "cur.json"
    voter = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([FakeVotoResp("bloco-02")]))
    assert voter.vote(e, ["bloco-01", "bloco-02"], _ctx()) == "bloco-02"
    assert load_material_curation(cache)["votes"]["e1"]["block_uuid"] == "uuid-2"
    # renumeracao: um bloco novo entra antes; uuid-2 passa a chamar-se bloco-03
    depois = MotorContext.from_artifacts(blocks=[
        {"id": "bloco-01", "block_uuid": "uuid-1", "period_start": "2026-03-01", "period_end": "2026-03-04"},
        {"id": "bloco-02", "block_uuid": "uuid-9", "period_start": "2026-03-05", "period_end": "2026-03-07"},
        {"id": "bloco-03", "block_uuid": "uuid-2", "period_start": "2026-03-08", "period_end": "2026-03-14"},
    ], card_block_map={}, lessons_index={})
    voter2 = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([]))
    assert voter2.vote(e, ["bloco-02", "bloco-03"], depois) == "bloco-03"   # o uuid-2, nao o display
    assert voter2.calls == 0
