from __future__ import annotations

from dataclasses import dataclass


def margin_confidence(winner: float, runner_up: float, *, k: float) -> float:
    """Confidence por margem: (winner - runner) + winner*k, clamp [0,1].

    Consolida a formula antes duplicada 4x (K=0.18 em 3 lugares, 0.20 em 1).
    """
    raw = (float(winner) - float(runner_up)) + (float(winner) * float(k))
    return min(1.0, max(0.0, raw))


@dataclass(frozen=True)
class _Thresholds:
    # tags gerenciadas (content_taxonomy.resolve_unit_block_tags)
    UNIT_TAG: float = 0.65
    SUBUNIT_TAG: float = 0.60
    BLOCO_TAG: float = 0.50
    # bloco -> unidade (timeline._assign_timeline_block_to_unit)
    BLOCK_UNIT_MIN_WINNER: float = 1.0
    BLOCK_UNIT_MIN_GAP: float = 0.35
    # voto de unidade (timeline._vote_unit_from_topic_candidates)
    VOTE_DOMINANCE: float = 0.60
    VOTE_MIN_SCORE: float = 0.10
    # K da formula de margem (padrao). Topico usa 0.20 historicamente.
    MARGIN_K: float = 0.18
    MARGIN_K_TOPIC: float = 0.20
    # cobertura de material (Fase 4, gate opcional)
    MATERIAL_COVERAGE_MIN: float = 0.70


T = _Thresholds()
