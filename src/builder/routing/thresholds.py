from __future__ import annotations

from dataclasses import dataclass


def margin_confidence(winner: float, runner_up: float, *, k: float) -> float:
    """Confidence por margem: (winner - runner) + winner*k, clamp [0,1].

    Consolida a formula antes duplicada 4x (K=0.18 em 3 lugares, 0.20 em 1).
    """
    raw = (float(winner) - float(runner_up)) + (float(winner) * float(k))
    return min(1.0, max(0.0, raw))


# Score "forte" de bloco: matches genuinos do scorer real ficam >=3.x
# (multiplos sinais somados); calibrado no golden v1 (Task 7/Step 5).
STRONG_SCORE: float = 3.0


def relative_margin_confidence(winner: float, runner_up: float) -> float:
    """Confiança de BLOCO: margem RELATIVA escalada pela força absoluta.

    Substitui margin_confidence SÓ nos caminhos de bloco (a aditiva saturava em
    1.0 com scores 4-8 — 46/56 entries conf=1.0, re-análise 2026-06-11).
    margin_confidence original permanece para unidade/tópico."""
    w = float(winner)
    if w <= 0:
        return 0.0
    rel = (w - max(float(runner_up), 0.0)) / w
    strength = min(1.0, w / STRONG_SCORE)
    return max(0.0, min(1.0, rel * (0.55 + 0.45 * strength)))


# --- Faixas de confianca de atribuicao de bloco -----------------------------
# Escala (P2.1, 2026-06-12): a confianca de bloco vem de
# relative_margin_confidence(best, runner_up) acima — margem relativa
# (best-runner)/best escalada pela forca absoluta (best/STRONG_SCORE). ATENCAO:
# na atribuicao de bloco (content_taxonomy.resolve_unit_block_tags) NAO ha
# portao — sempre se atribui o melhor candidato instrucional ("pega o melhor";
# orfao so quando nao existe bloco instrucional); a confianca baixa e a flag de
# revisao, nunca orfao.
#
# BAND_HIGH = 0.50 — na formula relativa, exige margem relativa >=~0.50 com
#   best forte (>=STRONG_SCORE): vencedor com o DOBRO do runner-up. Validado no
#   golden v1 (12/06): pos-P2.1 os 10 erros sairam todos da banda alta
#   (28 ok / 0 erro na alta), sem recalibrar o cutoff.
# BAND_LOW = 0.20 — margem relativa minima (~20% a frente com best forte, ou
#   mais com best fraco): abaixo disso o vencedor mal supera o runner-up,
#   genuinamente marginal -> "baixa".
BAND_HIGH: float = 0.50
BAND_LOW: float = 0.20


# Pesos do boost de data (file_map._score_block_date_match). DATE_STRONG_BOOST
# mantém o +0.30 original como base calibrável (spec Fase 2). DATE_WEAK_BOOST é
# deliberadamente menor: mês compatível é sinal mais fraco que data
# exata-no-range, então ~1/3 do forte — o suficiente para desempatar sem
# competir com um match exato.
DATE_STRONG_BOOST: float = 0.30
DATE_WEAK_BOOST: float = 0.10


# S2 (P4): escala do IDF por raridade entre blocos CANDIDATOS
# (file_map.block_token_weights). O peso bruto de um token do topic_text é
# 1/df (df = nº de candidatos cujo topic contém o token); o peso EFETIVO é
# 1 + IDF_WEIGHT*(1/df - 1) — interpolação entre "sem IDF" (0.0) e IDF puro
# (1.0). Assim calibrar IDF_WEIGHT não muda o peso de tokens fora do
# vocabulário dos candidatos (sempre 1.0). Calibrado no golden
# Metodos-Formais (T7, sweep 0.3/0.5/0.7/1.0): 1.0 (IDF puro) deu 40/48 vs
# 39/48 das escalas menores, sem regressão e sem confiante-e-errado.
IDF_WEIGHT: float = 1.0


# S4 (P4): sinal de ferramenta entry x topic do bloco
# (file_map.score_entry_against_timeline_block, só nos caminhos de ranking —
# mesmo guard do S2: topic_token_weights is not None). As auto_tags
# `ferramenta:<valor>` do manifest viram ferramentas da entry APENAS quando o
# valor é chave de TOOL_TOKENS — o extrator também emite ruído
# (ferramenta:proposicional, ferramenta:formal, ferramenta:sobre...) que NÃO é
# ferramenta de verdade e é ignorado. Boost quando o topic do bloco contém um
# token da ferramenta da entry; penalidade quando o bloco tem token de OUTRA
# ferramenta do mapa e nenhum da entry (material Isabelle não pertence a bloco
# Dafny). 0.8/0.4 calibrados no golden Metodos-Formais (T9): boost na ordem do
# boost de tópico exato (0.8), penalidade na ordem da de unidade errada (0.45).
TOOL_BOOST: float = 0.8
TOOL_PENALTY: float = 0.4
TOOL_TOKENS: dict = {
    "isabelle": {"isabelle"},
    "dafny": {"dafny"},
    "hoare": {"hoare"},
}

# S4b (P4): ferramenta derivada da EXTENSÃO do arquivo fonte
# (entry_signals.collect_entry_unit_signals, união com as auto_tags
# `ferramenta:`). Os .thy do manifest real NÃO têm ferramenta:isabelle nas
# auto_tags — a extensão é o sinal que sempre existe.
TOOL_EXTENSIONS: dict = {
    ".thy": "isabelle",
    ".dfy": "dafny",
}


# Tetos de confiança por método de atribuição de bloco (P2.2):
# "não há como ter certeza só com léxico" — o teto materializa isso.
# Aplicado em content_taxonomy.resolve_unit_block_tags na consolidação:
# computed_block_confidence = min(conf, METHOD_CAPS[method]). Métodos de
# CÓDIGO (consensus/llm_only, gravados por pedagogical_regeneration) não
# passam por aqui — a confiança deles vive em computed_block_match_confidence.
METHOD_CAPS: dict = {
    "manual": 1.0,
    "review_rule": 0.95,
    "card": 0.85,          # = CARD_SINGLE_CONF (gabarito 1-bloco)
    "card+scorer": 0.80,
    "scorer_only": 0.70,
}


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
    # sinal de sequencia (sequence.score_sequence_match): boost de DESEMPATE
    # quando o ordinal de aula do material casa o class_ordinal do bloco.
    # 0.20 < DATE_STRONG_BOOST(0.30) e < boost de topico(0.48): decide entre
    # blocos de aula adjacentes quando data/topico estao ausentes, sem
    # sobrepor um match forte. Nao rebalanceia thresholds existentes.
    SEQUENCE_BOOST: float = 0.20


T = _Thresholds()
