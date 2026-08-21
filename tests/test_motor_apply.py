# tests/test_motor_apply.py
"""FASE 4 D9: producer do motor — ANCHOR-ONLY, pino manual intocável, TIER 0."""
import copy
import json

from src.builder.routing.motor.apply import TEMPORAL_KEYS, apply_anchor_engine


def _repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".timeline_index.json").write_text(json.dumps({"blocks": [
        {"id": "bloco-01", "block_uuid": "u-1", "period_start": "2026-03-01",
         "sessions": [{"date": "2026-03-02", "label": "inducao estrutural"}]},
        {"id": "bloco-02", "block_uuid": "u-2", "period_start": "2026-03-08",
         "sessions": [{"date": "2026-03-09", "label": "logica de hoare"}]},
    ]}), encoding="utf-8")
    (repo / "course" / ".card_block_map.json").write_text(json.dumps(
        {"card a": {"source": "manual", "block_ids": ["bloco-01", "bloco-02"]}}),
        encoding="utf-8")
    (repo / "course" / ".lessons_index.json").write_text(json.dumps(
        {"by_date": {}}), encoding="utf-8")
    return repo


def _entries():
    return [
        {"id": "e1", "title": "inducao estrutural slides", "category": "materiais",
         "source_section": "card a", "computed_block_id": "u-1"},
        {"id": "pin", "title": "qualquer", "category": "materiais",
         "source_section": "card a", "computed_block_id": "u-1",
         "manual_timeline_block_id": "u-2",
         "temporal_block_id": "stale", "temporal_block_method": "anchor"},
        {"id": "fora", "title": "plano de ensino", "category": "bibliografia",
         "computed_block_id": "u-1"},
    ]


def test_flag_off_e_byte_identico(tmp_path):
    entries = _entries()
    before = copy.deepcopy(entries)
    out = apply_anchor_engine(entries, _repo(tmp_path), "MF", enabled=False)
    assert out == before


def test_pino_manual_nunca_recebe_temporal_e_stale_sai(tmp_path):
    entries = _entries()
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    pin = next(e for e in entries if e["id"] == "pin")
    assert pin["manual_timeline_block_id"] == "u-2"       # verdade humana intacta
    assert all(k not in pin for k in TEMPORAL_KEYS)        # temporal stale removido


def test_anchor_only_computed_intocado_e_temporal_escrito(tmp_path):
    entries = _entries()
    before = copy.deepcopy(entries)
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    for e, b in zip(entries, before):
        assert e.get("computed_block_id") == b.get("computed_block_id")
    e1 = next(e for e in entries if e["id"] == "e1")
    assert e1.get("temporal_block_id") in {"u-1", "u-2"}   # uuid, não display
    assert e1.get("temporal_block_window") == ["bloco-01", "bloco-02"]
    assert "temporal_block_band" in e1 and "temporal_block_provider" in e1


def test_fora_do_motor_nao_ganha_temporal(tmp_path):
    entries = _entries()
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    fora = next(e for e in entries if e["id"] == "fora")
    assert all(k not in fora for k in TEMPORAL_KEYS)       # bibliografia -> funil


def test_pino_manual_invalido_nao_pula_motor_prossegue(tmp_path):
    """review F4 T6: pino manual que NÃO resolve no ctx (id/uuid inexistente)
    não conta como pino válido — _valid_manual_pin=False e o motor prossegue a
    resolução normal em vez de pular a entry (semântica atual, travada com teste)."""
    entries = [
        {"id": "e1", "title": "inducao estrutural slides", "category": "materiais",
         "source_section": "card a", "computed_block_id": "u-1",
         "manual_timeline_block_id": "uuid-que-nao-existe-no-ctx"},
    ]
    apply_anchor_engine(entries, _repo(tmp_path), "MF")
    e1 = entries[0]
    assert e1["manual_timeline_block_id"] == "uuid-que-nao-existe-no-ctx"  # não mexido
    assert e1.get("temporal_block_id") in {"u-1", "u-2"}                  # motor resolveu, não pulou


def _repo_due(tmp_path, blocks, card_map):
    """Repo tmp mínimo p/ testes do provider due-window (TIER 2, Task 4).

    `_repo()` acima é fixo (blocos u-1/u-2 + card map manual); este helper
    parametriza blocks/card_map pros cenários de janela-de-prazo."""
    repo = tmp_path / "repo_due"
    (repo / "course").mkdir(parents=True)
    (repo / "course" / ".timeline_index.json").write_text(
        json.dumps({"blocks": blocks}), encoding="utf-8")
    (repo / "course" / ".card_block_map.json").write_text(
        json.dumps(card_map), encoding="utf-8")
    (repo / "course" / ".lessons_index.json").write_text(
        json.dumps({"by_date": {}}), encoding="utf-8")
    return repo


def test_tier2_due_window_escreve_temporal(tmp_path):
    """Entry trabalhos com due casado ganha temporal_* do provider due-window."""
    repo = _repo_due(
        tmp_path,
        blocks=[{"id": "bloco-15", "block_uuid": "u15",
                 "period_start": "2026-06-01", "period_end": "2026-06-10", "topics": ["t"]}],
        card_map={"TDE Trabalho Discente Efetivo": {"assign_dues": [
            {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"}]}},
    )
    entries = [{"id": "t1-2026-1", "title": "t1 2026 1", "category": "trabalhos",
                "source_section": "TDE Trabalho Discente Efetivo"}]
    out = apply_anchor_engine(entries, repo, "MF", enabled=True, voter=None)
    e = out[0]
    assert e["temporal_block_id"] == "u15"
    assert e["temporal_block_band"] == "alta"
    assert e["temporal_block_provider"] == "due-window"


def test_tier2_sem_due_limpa_temporal_e_vai_pro_funil(tmp_path):
    repo = _repo_due(
        tmp_path,
        blocks=[{"id": "bloco-15", "block_uuid": "u15",
                 "period_start": "2026-06-01", "period_end": "2026-06-10"}],
        card_map={},
    )
    entries = [{"id": "revisao-p1-gabarito", "title": "revisao p1 gabarito",
                "category": "provas", "source_section": "Exercicios de Revisao",
                "temporal_block_id": "stale"}]
    out = apply_anchor_engine(entries, repo, "MF", enabled=True, voter=None)
    assert not out[0].get("temporal_block_id")  # limpo, funil responde


def test_tier2_codigo_tde_sem_due_funil(tmp_path):
    """codigo-* + secao TDE sem due casado -> temporal limpo (funil). NAO discrimina
    o wiring: sec.startswith("TDE") ja torna a entry out-of-scope no caminho legado
    (true-set do tier2_due_scope e subconjunto estrito do is_out_of_disamb_scope —
    re-review F5 T4); o discriminador real da cascata e test_tier2_due_window_escreve_temporal."""
    repo = _repo_due(
        tmp_path,
        blocks=[{"id": "bloco-15", "block_uuid": "u15",
                 "period_start": "2026-06-01", "period_end": "2026-06-10"}],
        card_map={},
    )
    entries = [{"id": "t9-materia-thy", "title": "T9 materia",
                "category": "codigo-professor", "source_section": "TDE Trabalho Discente Efetivo",
                "temporal_block_id": "stale"}]
    out = apply_anchor_engine(entries, repo, "MF", enabled=True, voter=None)
    assert not out[0].get("temporal_block_id")  # limpo, funil responde


def test_pino_manual_vence_due_window(tmp_path):
    repo = _repo_due(
        tmp_path,
        blocks=[{"id": "bloco-15", "block_uuid": "u15",
                 "period_start": "2026-06-01", "period_end": "2026-06-10"}],
        card_map={"TDE Trabalho Discente Efetivo": {"assign_dues": [
            {"name": "Entrega T1", "due": "2026-06-10", "source": "structured"}]}},
    )
    entries = [{"id": "t1-2026-1", "title": "t1 2026 1", "category": "trabalhos",
                "source_section": "TDE Trabalho Discente Efetivo",
                "manual_timeline_block_id": "u15"}]
    out = apply_anchor_engine(entries, repo, "MF", enabled=True, voter=None)
    assert not out[0].get("temporal_block_id")  # pino: motor respeita e limpa temporal


def test_tier0_gemeos_decisao_none_propaga_para_ambos(tmp_path):
    """review F4 T6: quando o motor não acha janela pro 1º gêmeo (funil, decision
    None), o cache por content_key propaga None -> 2º gêmeo também fica sem
    temporal_* (cache honesto: None é uma decisão cacheada como qualquer outra)."""
    repo = _repo(tmp_path)
    twin = repo / "twin2.pdf"
    twin.write_bytes(b"outro conteudo identico")
    entries = [
        {"id": "n1", "title": "artigo externo", "category": "materiais",
         "source_section": "card inexistente", "source_path": "twin2.pdf"},
        {"id": "n2", "title": "artigo externo copia", "category": "materiais",
         "source_section": "card inexistente", "source_path": "twin2.pdf"},
    ]
    apply_anchor_engine(entries, repo, "MF")
    assert all(k not in entries[0] for k in TEMPORAL_KEYS)
    assert all(k not in entries[1] for k in TEMPORAL_KEYS)


def test_tier0_gemeos_md5_mesma_decisao(tmp_path):
    repo = _repo(tmp_path)
    twin = repo / "twin.pdf"
    twin.write_bytes(b"conteudo identico")
    entries = [
        {"id": "g1", "title": "inducao 1", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
        {"id": "g2", "title": "inducao 2", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
    ]
    apply_anchor_engine(entries, repo, "MF")
    assert entries[0].get("temporal_block_id") == entries[1].get("temporal_block_id")


def test_tier0_fora_de_escopo_nao_herda_decisao_do_gemeo_in_scope(tmp_path):
    """review F4 I1: gêmeo md5 fora-de-escopo (bibliografia) processado DEPOIS
    do gêmeo in-scope não deve herdar temporal_* via cache de content_key —
    is_out_of_disamb_scope é atributo da ENTRY, não do conteúdo compartilhado."""
    repo = _repo(tmp_path)
    twin = repo / "twin.pdf"
    twin.write_bytes(b"conteudo identico")
    entries = [
        {"id": "g1", "title": "inducao 1", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
        {"id": "g2-fora", "title": "inducao 2", "category": "bibliografia",
         "source_section": "card a", "source_path": "twin.pdf"},
    ]
    apply_anchor_engine(entries, repo, "MF")
    g1 = next(e for e in entries if e["id"] == "g1")
    fora = next(e for e in entries if e["id"] == "g2-fora")
    assert g1.get("temporal_block_id")                      # in-scope decidido normalmente
    assert all(k not in fora for k in TEMPORAL_KEYS)         # fora-de-escopo NUNCA herda


def test_tier0_in_scope_nao_perde_decisao_apos_gemeo_fora_de_escopo(tmp_path):
    """review F4 I1: ordem inversa — gêmeo fora-de-escopo processado PRIMEIRO não
    pode poluir o cache decided[key]=None e apagar a decisão do gêmeo in-scope."""
    repo = _repo(tmp_path)
    twin = repo / "twin.pdf"
    twin.write_bytes(b"conteudo identico")
    entries = [
        {"id": "g2-fora", "title": "inducao 2", "category": "bibliografia",
         "source_section": "card a", "source_path": "twin.pdf"},
        {"id": "g1", "title": "inducao 1", "category": "materiais",
         "source_section": "card a", "source_path": "twin.pdf"},
    ]
    apply_anchor_engine(entries, repo, "MF")
    g1 = next(e for e in entries if e["id"] == "g1")
    fora = next(e for e in entries if e["id"] == "g2-fora")
    assert g1.get("temporal_block_id")                      # decisão NÃO apagada pelo cache
    assert all(k not in fora for k in TEMPORAL_KEYS)


def test_build_motor_voter_off_por_default(tmp_path):
    from src.builder.ops.pedagogical_regeneration import _build_motor_voter

    class _B:
        options = {}
        root_dir = tmp_path
    assert _build_motor_voter(_B()) is None


def test_build_motor_voter_on_sem_chave_degrada_none(tmp_path, monkeypatch):
    from src.builder.ops import pedagogical_regeneration as pr

    class _B:
        options = {"use_llm_voter": True}
        root_dir = tmp_path
    monkeypatch.setattr(pr.Path, "home", lambda: tmp_path)  # sem config -> sem chave
    # review F4 I2: precedência agora cobre env também (has_gemini_api_key) —
    # delenv garante "sem chave" de verdade, independente do .env local do dev
    # (que carrega GEMINI_API_KEY em os.environ no import de src.utils.helpers).
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert pr._build_motor_voter(_B()) is None


def test_build_motor_voter_chave_via_ambiente_constroi_voter(tmp_path, monkeypatch):
    """review F4 I2: gemini_api_key ausente no config mas presente via
    GEMINI_API_KEY do ambiente -> voter CONSTRUÍDO (precedência real config>env,
    igual à usada por get_gemini_client — não um pré-check que só olha config)."""
    from src.builder.ops import pedagogical_regeneration as pr
    from src.builder.routing.motor.llm_vote import LlmVoter

    class _B:
        options = {"use_llm_voter": True}
        root_dir = tmp_path
    monkeypatch.setattr(pr.Path, "home", lambda: tmp_path)  # sem config no disco
    monkeypatch.setenv("GEMINI_API_KEY", "env-key-123")
    voter = pr._build_motor_voter(_B())
    assert isinstance(voter, LlmVoter)


def test_run_anchor_engine_layer_isola_falha_do_voter(tmp_path, monkeypatch, caplog):
    """Important do review T7: falha de I/O do voter/prune não derruba a regeneração."""
    from src.builder.ops import pedagogical_regeneration as pr

    class _Boom:
        def prune(self, keys):
            raise OSError("sidecar lockado")

    class _B:
        options = {"use_anchor_engine": True, "use_llm_voter": True}
        root_dir = tmp_path
        course_meta = {"course_name": "X"}

    monkeypatch.setattr(pr, "_build_motor_voter", lambda b: _Boom())
    entries = [{"id": "e1", "title": "t", "category": "materiais"}]
    before = copy.deepcopy(entries)  # review F4 T7c: `out == entries` era vácuo (out IS entries,
    # mesma lista mutada in place — a igualdade nunca podia falhar). Compara contra snapshot.
    with caplog.at_level("WARNING"):
        out = pr._run_anchor_engine_layer(_B(), entries)
    assert out == before
    assert any("camada temporal pulada" in r.message for r in caplog.records)


def test_run_anchor_engine_layer_happy_path_sem_warning(tmp_path, monkeypatch, caplog):
    """Sem voter e sem timeline no repo, a camada devolve as entries sem warning."""
    from src.builder.ops import pedagogical_regeneration as pr

    class _B:
        options = {"use_anchor_engine": True}
        root_dir = tmp_path
        course_meta = {"course_name": "X"}

    monkeypatch.setattr(pr, "_build_motor_voter", lambda b: None)
    entries = [{"id": "e1", "title": "t", "category": "materiais"}]
    before = copy.deepcopy(entries)  # review F4 T7c: snapshot p/ comparação não-vácua
    with caplog.at_level("WARNING"):
        out = pr._run_anchor_engine_layer(_B(), entries)
    assert out == before
    assert not [r for r in caplog.records if r.levelname == "WARNING"]


class _VoterFunil:
    """Responde sempre o mesmo bloco; registra a janela que recebeu."""
    def __init__(self, answer):
        self.answer, self.windows = answer, []

    def vote(self, entry, window, ctx, markdown=""):
        self.windows.append((str(entry.get("id")), list(window)))
        return self.answer


def test_llm_funil_escreve_temporal_para_sem_janela_e_provas_sem_due(tmp_path):
    """B-4: entry in-scope sem janela e provas/trabalhos sem due recebem o voto
    do LLM com janela = todos os blocos (method llm-funil). Bibliografia segue
    sem eixo temporal (design do apply_concept_resolver), mesmo com voter."""
    repo = _repo(tmp_path)
    voter = _VoterFunil("bloco-02")
    entries = [
        {"id": "sem-janela", "title": "sem sinal nenhum", "category": "materiais",
         "source_section": "Informacoes Gerais"},
        {"id": "prova-sem-due", "title": "lista p1", "category": "provas",
         "source_section": "Informacoes Gerais"},
        {"id": "fora", "title": "plano de ensino", "category": "bibliografia"},
    ]
    apply_anchor_engine(entries, repo, "MF", voter=voter)
    by = {e["id"]: e for e in entries}
    for eid in ("sem-janela", "prova-sem-due"):
        assert by[eid]["temporal_block_id"] == "u-2", eid
        assert by[eid]["temporal_block_method"] == "llm-funil"
        assert by[eid]["temporal_block_band"] == "media"
        assert by[eid]["temporal_block_flag"] is True
        assert by[eid]["temporal_block_window"] == ["bloco-01", "bloco-02"]
    assert all(k not in by["fora"] for k in TEMPORAL_KEYS)
    assert sorted(eid for eid, _ in voter.windows) == ["prova-sem-due", "sem-janela"]
