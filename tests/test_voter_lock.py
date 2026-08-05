"""T4b: lock cross-processo do sidecar do voter (`_cache_lock`, `_persist`/`prune`).

Sem lock, dois "processos" (instancias distintas de LlmVoter, mesmo cache) que
persistem ao mesmo tempo podem clobberar um ao outro: read-merge-write sem
exclusao perde o voto que o outro acabou de gravar. Estes testes travam o
COMPORTAMENTO (merge concorrente nao perde voto) e a mecanica do lock em si
(segundo acquire espera; sentinela orfao e tomado; timeout tem excecao clara).
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import pytest

from src.builder.routing.motor import llm_vote
from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.llm_vote import LlmVoter, SidecarLockTimeout, _cache_lock


def _entry(rid: str) -> dict:
    return {"id": rid, "source_path": "", "title": rid, "source_section": "", "category": "material"}


def _ctx() -> MotorContext:
    blocks = [{"id": "bloco-01", "block_uuid": "uuid-1", "period_start": "2026-03-01",
               "period_end": "2026-03-07", "topic_text": "x", "sessions": []}]
    return MotorContext.from_artifacts(blocks=blocks, card_block_map={},
                                        lessons_index={}, course_name="Curso")


class FakeVotoResp:
    def __init__(self, block_id):
        self.block_id = block_id
        self.confianca = "alta"
        self.justificativa_curta = "j"


class FakeClient:
    model = "fake-model"

    def __init__(self, answers):
        self.answers = list(answers)

    def summarize_bundle(self, bundle_text, schema, system_instruction):
        return self.answers.pop(0)


# ===== mecanica do lock =====

def test_cache_lock_segundo_acquire_espera_o_primeiro_liberar(tmp_path):
    cache = tmp_path / "c.json"
    order = []
    release_evt = threading.Event()
    acquired_evt = threading.Event()

    def holder():
        with _cache_lock(cache, timeout=2.0):
            order.append("a-in")
            acquired_evt.set()
            release_evt.wait(timeout=2.0)
        order.append("a-out")

    t = threading.Thread(target=holder)
    t.start()
    assert acquired_evt.wait(timeout=2.0)

    # segundo acquire (mesma cache) tem que esperar A soltar, nao entrar antes
    def waiter():
        with _cache_lock(cache, timeout=2.0):
            order.append("b-in")

    tb = threading.Thread(target=waiter)
    tb.start()
    time.sleep(0.1)
    assert order == ["a-in"]           # B ainda bloqueado
    release_evt.set()
    t.join(timeout=2.0)
    tb.join(timeout=2.0)
    assert order == ["a-in", "a-out", "b-in"]  # B só entrou depois de A sair


def test_cache_lock_timeout_levanta_excecao_clara(tmp_path):
    cache = tmp_path / "c.json"
    release_evt = threading.Event()

    def holder():
        with _cache_lock(cache, timeout=2.0):
            release_evt.wait(timeout=2.0)

    t = threading.Thread(target=holder)
    t.start()
    time.sleep(0.05)
    try:
        with pytest.raises(SidecarLockTimeout):
            with _cache_lock(cache, timeout=0.2):
                pass
    finally:
        release_evt.set()
        t.join(timeout=2.0)


def test_cache_lock_sentinela_orfao_e_tomado(tmp_path):
    cache = tmp_path / "c.json"
    lock_path = Path(str(cache) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    old = time.time() - 999
    os.utime(lock_path, (old, old))       # simula dono morto ha muito tempo

    entered = []
    with _cache_lock(cache, timeout=1.0, stale_after=5.0):
        entered.append(True)
    assert entered == [True]
    assert not lock_path.exists()         # sentinela liberado ao sair


def test_cache_lock_finally_libera_mesmo_com_excecao(tmp_path):
    cache = tmp_path / "c.json"
    lock_path = Path(str(cache) + ".lock")
    with pytest.raises(RuntimeError):
        with _cache_lock(cache, timeout=1.0):
            raise RuntimeError("boom")
    assert not lock_path.exists()


# ===== comportamento: merge concorrente nao perde voto =====

def test_persist_concorrente_entre_duas_instancias_nao_perde_voto(tmp_path, monkeypatch):
    """RED sem o lock: A e B leem o disco antes de o outro salvar (janela
    alargada via sleep no load) -> o segundo save sobrescreve o voto do
    primeiro. GREEN com o lock: B so le depois de A soltar, entao o merge
    de B ja parte do estado com o voto de A -> os dois sobrevivem."""
    cache = tmp_path / "material_curation.json"
    ctx = _ctx()
    va = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([FakeVotoResp("bloco-01")]))
    vb = LlmVoter({}, cache_path=cache, repo_dir=tmp_path, client=FakeClient([FakeVotoResp("bloco-01")]))

    orig_load = llm_vote.load_material_curation

    def slow_load(path):
        data = orig_load(path)
        time.sleep(0.15)          # alarga a janela entre read e write
        return data

    monkeypatch.setattr(llm_vote, "load_material_curation", slow_load)

    def run(v, rid):
        v.vote(_entry(rid), ["bloco-01"], ctx)

    ta = threading.Thread(target=run, args=(va, "a"))
    tb = threading.Thread(target=run, args=(vb, "b"))
    ta.start()
    time.sleep(0.02)               # B entra enquanto A ja abriu a janela de load
    tb.start()
    ta.join(timeout=5.0)
    tb.join(timeout=5.0)

    final = json.loads(cache.read_text(encoding="utf-8"))["votes"]
    assert set(final) == {"a", "b"}   # nenhum voto perdido
