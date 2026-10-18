"""Teste de NÃO-CASCATEAMENTO — a prova real da Fase 1 (identidade estável).

Hipótese sob teste: dividir um bloco over-merged NÃO pode quebrar referências,
porque elas apontam para `block_uuid` (estável por best-overlap de data/token via
`reattach_block_uuids`), não para o id posicional `bloco-NN` — que renumera em
cascata quando um bloco é inserido (a lição do Degrau 2: split de bloco-05
empurrou bloco-06→07 e desalinhou o `.card_block_map.json`).

VERDE  => a identidade aguenta o split sem orfanar nada -> pode-se atacar o cap
          temporal em index.py:699 (Fase 3) com segurança.
VERMELHO => o trabalho restante é a IDENTIDADE, não o cap.

Usa a máquina REAL (reattach_block_uuids + resolve_block_ref) sobre um índice
sintético que reproduz o monstro do IA (bloco-05 = 28 dias) seguido de dois
blocos que SERÃO renumerados pelo split. `mint` é injetado para uuids
determinísticos — sem depender de uuid4/relógio.
"""
from __future__ import annotations

import itertools

from src.builder.timeline.block_identity import reattach_block_uuids
from src.builder.timeline.card_block import resolve_block_ref


def _minter():
    c = itertools.count(1)
    return lambda: f"u{next(c)}"


def _by_uuid(blocks):
    return {str(b.get("block_uuid")): b for b in blocks}


def _resolve(uuid_ref, blocks):
    """'Resolve' = o uuid ainda aponta para ALGUM bloco do índice (não orfanou)."""
    return _by_uuid(blocks).get(str(uuid_ref))


def _pre_split_index():
    """3 blocos: o monstro over-merged (bloco-05, 28d) + busca + agentes."""
    return [
        {
            "id": "bloco-05",
            "period_start": "2026-04-13", "period_end": "2026-05-11",  # 28 dias = o monstro IA
            "topic_text": "aprendizado nao supervisionado agrupamento kmeans hierarquico",
            "topics": ["agrupamento", "kmeans", "hierarquico"],
        },
        {
            "id": "bloco-06",
            "period_start": "2026-05-18", "period_end": "2026-05-22",
            "topic_text": "busca informada heuristica estrela",
            "topics": ["busca", "informada"],
        },
        {
            "id": "bloco-07",
            "period_start": "2026-05-25", "period_end": "2026-05-29",
            "topic_text": "agentes inteligentes ambiente racional",
            "topics": ["agentes", "inteligentes"],
        },
    ]


def _post_split_index():
    """O monstro foi DIVIDIDO em dois (particional + hierárquico). Isso EMPURRA
    os ids posicionais: o antigo bloco-06 vira bloco-07 e o bloco-07 vira
    bloco-08 — exatamente a cascata posicional que o uuid precisa absorver."""
    return [
        {
            "id": "bloco-05",
            "period_start": "2026-04-13", "period_end": "2026-04-24",  # fragmento A
            "topic_text": "agrupamento kmeans particional centroides",
            "topics": ["agrupamento", "kmeans", "particional"],
        },
        {
            "id": "bloco-06",  # fragmento B (NOVO bloco inserido = gatilho da cascata)
            "period_start": "2026-04-27", "period_end": "2026-05-11",
            "topic_text": "agrupamento hierarquico dendrograma aglomerativo",
            "topics": ["agrupamento", "hierarquico", "dendrograma"],
        },
        {
            "id": "bloco-07",  # ERA bloco-06 (busca) — renumerado +1
            "period_start": "2026-05-18", "period_end": "2026-05-22",
            "topic_text": "busca informada heuristica estrela",
            "topics": ["busca", "informada"],
        },
        {
            "id": "bloco-08",  # ERA bloco-07 (agentes) — renumerado +1
            "period_start": "2026-05-25", "period_end": "2026-05-29",
            "topic_text": "agentes inteligentes ambiente racional",
            "topics": ["agentes", "inteligentes"],
        },
    ]


def _setup_split():
    """Minta uuids no pré-split, monta referências por uuid, depois reataca o
    pós-split com o MESMO ledger. Retorna o estado para os asserts."""
    mint = _minter()

    pre = _pre_split_index()
    pre, ledger, _ = reattach_block_uuids(pre, [], has_existing_refs=False, mint=mint)
    u_monstro = pre[0]["block_uuid"]   # bloco-05
    u_busca = pre[1]["block_uuid"]     # bloco-06
    u_agentes = pre[2]["block_uuid"]   # bloco-07

    # Referências persistidas que APONTAM por uuid (computed_block_id + card map).
    computed_block_ids = [u_monstro, u_busca, u_agentes]
    card_block_map = {
        "Semana 9 - ML Aprendizado Nao Supervisionado": {"block_ids": [u_monstro], "source": "labels"},
        "Semana 12 - Busca com Informacao": {"block_ids": [u_busca], "source": "labels"},
    }

    # O SPLIT: reataca o índice pós-split com o ledger existente (refs vivas).
    post = _post_split_index()
    post, ledger, flags = reattach_block_uuids(
        post, ledger, has_existing_refs=True, mint=mint
    )
    return {
        "pre": pre, "post": post, "ledger": ledger, "flags": flags,
        "u_monstro": u_monstro, "u_busca": u_busca, "u_agentes": u_agentes,
        "computed_block_ids": computed_block_ids, "card_block_map": card_block_map,
    }


def test_split_nao_orfana_nenhum_computed_block_id():
    """Todo computed_block_id (uuid) persistido ainda resolve para um bloco do
    índice pós-split — nenhuma referência ficou órfã pela renumeração."""
    s = _setup_split()
    for uuid_ref in s["computed_block_ids"]:
        assert _resolve(uuid_ref, s["post"]) is not None, (
            f"computed_block_id {uuid_ref} orfanou após o split — CASCATA"
        )


def test_split_nao_orfana_card_block_map():
    """Toda entrada do .card_block_map.json (block_ids uuid) ainda resolve."""
    s = _setup_split()
    for card, entry in s["card_block_map"].items():
        for bid in entry["block_ids"]:
            assert _resolve(bid, s["post"]) is not None, (
                f"card '{card}' aponta para {bid} que orfanou após o split"
            )


def test_blocos_nao_divididos_preservam_uuid_apesar_da_renumeracao():
    """O coração da prova: busca e agentes foram RENUMERADOS (bloco-06→07,
    07→08) mas mantêm o MESMO uuid, porque o uuid segue o CONTEÚDO (data+token),
    não a posição. É isto que impede a cascata."""
    s = _setup_split()
    post_by_uuid = _by_uuid(s["post"])

    busca = post_by_uuid.get(s["u_busca"])
    assert busca is not None and busca["id"] == "bloco-07", (
        "busca deveria ter renumerado para bloco-07 mantendo seu uuid original"
    )
    assert "busca" in busca["topic_text"]

    agentes = post_by_uuid.get(s["u_agentes"])
    assert agentes is not None and agentes["id"] == "bloco-08", (
        "agentes deveria ter renumerado para bloco-08 mantendo seu uuid original"
    )
    assert "agentes" in agentes["topic_text"]


def test_id_posicional_cascateia_mas_uuid_nao():
    """Contraste explícito: o ref POSICIONAL 'bloco-06' agora resolve para um
    bloco DIFERENTE (o fragmento hierárquico inserido), enquanto o uuid da busca
    continua apontando para a busca. Prova de que posição é instável e uuid não —
    a razão pela qual a Fase 1 é pré-requisito do cap."""
    s = _setup_split()

    # Posicional: 'bloco-06' antes = busca; depois do split = fragmento hierárquico.
    posicional_06 = resolve_block_ref("bloco-06", s["post"])
    assert posicional_06 != s["u_busca"], (
        "se 'bloco-06' ainda apontasse para a busca, não teria havido renumeração"
    )
    frag_hierarquico = _resolve(posicional_06, s["post"])
    assert frag_hierarquico is not None and "hierarquico" in frag_hierarquico["topic_text"]

    # Uuid: o ref estável da busca segue na busca, onde quer que ela tenha parado.
    assert _resolve(s["u_busca"], s["post"])["topic_text"].startswith("busca")


def test_split_nunca_deleta_ledger():
    """Ledger é append-only: o split só adiciona registros, nunca remove. Os
    uuids pré-split continuam todos no ledger pós-split."""
    s = _setup_split()
    ledger_uuids = {r["uuid"] for r in s["ledger"]}
    for u in (s["u_monstro"], s["u_busca"], s["u_agentes"]):
        assert u in ledger_uuids, f"uuid {u} sumiu do ledger — não é append-only"
