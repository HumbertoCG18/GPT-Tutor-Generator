from __future__ import annotations

from dataclasses import dataclass


def margin_confidence(winner: float, runner_up: float, *, k: float) -> float:
    """Confidence por margem: (winner - runner) + winner*k, clamp [0,1].

    Consolida a formula antes duplicada 4x (K=0.18 em 3 lugares, 0.20 em 1).
    """
    raw = (float(winner) - float(runner_up)) + (float(winner) * float(k))
    return min(1.0, max(0.0, raw))


# --- Faixas de confianca de atribuicao de bloco (Fase 3) ------------------
# Escala: a confianca de bloco vem de margin_confidence(best, runner_up,
# k=MARGIN_K=0.18), ja clampada em [0,1]. ATENCAO: na atribuicao de bloco
# (content_taxonomy.resolve_unit_block_tags) NAO ha mais portao — sempre se
# atribui o melhor candidato instrucional (spec "pega o melhor"; orfao so quando
# nao existe bloco instrucional). O portao best>=0.95 do scorer (file_map.py:1098)
# continua valendo apenas para o roteamento do FILE_MAP em navigation.py; quando
# ele recusa, o resolver cai no fallback "pega o melhor". Logo a confianca de uma
# atribuicao pode ser baixa de proposito (best fraco e/ou margem minima sobre o
# runner_up ~ best*0.18 ~= 0.17), e e exatamente isso que a band media/baixa
# sinaliza para revisao.
#
# BAND_HIGH = 0.50 — alinhado ao piso de tag de bloco existente (BLOCO_TAG=0.50):
#   uma atribuicao com gap claro (gap>=0.35, o limiar de "nao-ambiguo" usado no
#   scorer) e best~1.0 produz confianca ~0.35 + 0.18 = 0.53, caindo em "alta".
#   Reusa a calibracao ja validada do scale de tags, sem rebalancear nada.
# BAND_LOW = 0.20 — logo acima do piso estrutural (~0.17) que toda atribuicao
#   cruza; abaixo disso o melhor candidato mal supera o runner-up (margem
#   minima), genuinamente marginal -> "baixa". Espelha, na escala comprimida por
#   k, o corte "baixa confianca" (<0.45) ja exibido em file_map (render de slug).
# Nao rebalanceamos os thresholds existentes — apenas ADICIONAMOS estas duas
# constantes de faixa + o helper abaixo.
BAND_HIGH: float = 0.50
BAND_LOW: float = 0.20


def confidence_band(confidence: float) -> str:
    """Mapeia uma confianca de atribuicao em faixa textual.

    Fronteiras (HIGH inclusivo, LOW inclusivo, ou seja media = [LOW, HIGH)):
      - confidence >= BAND_HIGH            -> "alta"
      - BAND_LOW  <= confidence < BAND_HIGH -> "media"
      - confidence <  BAND_LOW             -> "baixa"
    """
    c = float(confidence)
    if c >= BAND_HIGH:
        return "alta"
    if c >= BAND_LOW:
        return "media"
    return "baixa"


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
    # roteamento entry->unidade (file_map.auto_map_entry_unit)
    # UNIT_MATCH_REL_MARGIN: gate de margem RELATIVA — winner deve superar o
    #   runner_up em >=15% para nao ser ambiguo (valor historico ja em uso).
    # UNIT_MATCH_MIN_WINNER: piso ABSOLUTO de score do vencedor. Sem ele, um
    #   winner fraco (ex.: 0.41 de um unico token "estado" acidental) com
    #   runner_up ~0 produz rel_margin~1.0 e passa por confiante. Um match
    #   genuino fica >=4.x (multiplos topicos/tokens), entao 0.5 separa ruido
    #   de sinal sem rebaixar matches reais.
    UNIT_MATCH_REL_MARGIN: float = 0.15
    UNIT_MATCH_MIN_WINNER: float = 0.5
    # cobertura de material (Fase 4, gate opcional)
    MATERIAL_COVERAGE_MIN: float = 0.70


T = _Thresholds()
