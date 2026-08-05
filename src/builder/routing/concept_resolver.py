from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, TypedDict

from src.builder.routing.file_map import (
    _score_block_date_match,
    score_card_evidence_against_entry,
)
from src.builder.routing.sequence import score_sequence_match
from src.builder.routing.thresholds import (
    IDF_WEIGHT,
    confidence_band,
    relative_margin_confidence,
)
from src.builder.text.normalize import normalize_match_text
from src.builder.text.stopwords import TIMELINE_GENERIC_TOKENS, UNIT_GENERIC_TOKENS
from src.builder.timeline.card_block import resolve_block_ref as _rbr
from src.builder.timeline.block_identity import _POSITIONAL_RE as _POS_RE

_STOPWORDS = TIMELINE_GENERIC_TOKENS | UNIT_GENERIC_TOKENS

# Extensoes de arquivo-fonte: sinal de FORMATO, uniforme na unidade -> nao
# discrimina bloco. Tokens >=4 chars (o filtro _concept_tokens dropa os curtos
# ANTES do down-weight); formato nao precisa discriminar a fusao, entao basta
# zerar os que sobrevivem ao filtro (Minor da 2.1: os <4 chars eram inertes).
FORMAT_TOKENS: frozenset = frozenset({"ipynb", "json", "lean"})

# Piso do peso de ferramenta/formato no escopo de bloco: ~0 (nao negativo).
_BLOCK_TOOL_FLOOR: float = 0.0

# Pesos da fusao (spec 4.3). Calibrados por PRINCIPIO, nao por overfit:
# - W_CONCEPT=1.0: um overlap de UM token raro/discriminante (peso IDF ~1.0)
#   vale 1 ponto. E o nucleo.
# - W_LLM=0.85: o voto do LLM (block_match_confidence in [0,1]) entra abaixo de
#   um overlap de conceito FORTE (>=1 token discriminante) -> conceito exato
#   domina o voto LLM errado (colecoes/invariantes/hoare). Mas quando o overlap
#   e ZERO ou EMPATADO (arvores 04==05, intro/listas/classes sem token), o voto
#   LLM (0.85*conf ~ 0.6-0.7) e o unico/maior termo e desempata.
W_CONCEPT: float = 1.0
W_LLM: float = 0.85
# Voto secundario do LLM: fracao do peso do primario (sinal mais fraco).
LLM_SECONDARY_FRAC: float = 0.4
# Card-evidence autoritativo (tier 2): acima disto e ground-truth postado.
CARD_AUTHORITATIVE: float = 0.5
# source_section e a JANELA do cronograma (onde o material foi postado), nao o
# conteudo — para um .thy a secao "Provas por Inducao" cobre 04/05/06 inteiros
# e nao discrimina. Entra com fracao do peso do conteudo (titulo/markdown/
# concepts do Gemini), como hint posicional fraco, nao como conceito de 1a
# classe (senao a secao do cronograma sobrepoe o voto do LLM que LEU o arquivo).
SECTION_CONCEPT_FRAC: float = 0.35

# Alavanca 0 (lessons[].text): tópico da aula daquele DIA (resumo-da-semana do
# professor, indexado por data) reforça o bloco cujas sessões cobrem essa data.
# Casa SÓ o sinal LIMPO do material (moodle_label + título) — casar contra
# markdown/concepts do Gemini regredia o gold (revert anterior). Capado p/ não
# dominar conceito/LLM (anti-envenenamento).
W_LESSON: float = 0.5
LESSON_OVERLAP_CAP: int = 3


def _concept_text(item: object) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item or "")
    parts: List[str] = []
    # BLOCO (.timeline_index.json)
    if "topic_text" in item or "sessions" in item:
        parts.append(str(item.get("topic_text", "") or ""))
        parts.append(str(item.get("primary_topic_label", "") or ""))
        for topic in item.get("topics") or []:
            parts.append(str(topic or ""))
        for session in item.get("sessions") or []:
            if isinstance(session, dict):
                parts.append(str(session.get("label", "") or ""))
        for alias in item.get("aliases") or []:
            parts.append(str(alias or ""))
        return " ".join(p for p in parts if p)
    # UNIDADE (.content_taxonomy.json)
    if "title" in item or "topics" in item:
        parts.append(str(item.get("title", "") or ""))
        for topic in item.get("topics") or []:
            if isinstance(topic, dict):
                parts.append(str(topic.get("label", "") or ""))
                for alias in topic.get("aliases") or []:
                    parts.append(str(alias or ""))
            else:
                parts.append(str(topic or ""))
        return " ".join(p for p in parts if p)
    # ENTRY / texto cru com concepts do Gemini
    for key in ("title", "markdown", "source_section", "text"):
        value = item.get(key)
        if value:
            parts.append(str(value))
    for concept in item.get("concepts") or []:
        parts.append(str(concept or ""))
    return " ".join(p for p in parts if p)


def _concept_tokens(text: str, normalize: Callable[[str], str]) -> set:
    return {
        token
        for token in normalize(text).split()
        if len(token) >= 4 and token not in _STOPWORDS
    }


def score_lesson_match(
    signals: dict,
    block: dict,
    lessons_index: Optional[dict],
    normalize: Callable[[str], str],
) -> float:
    """Reforço data→tópico: tokens do tópico das aulas DESTE bloco (via
    lessons_index[session.date]) ∩ tokens do sinal LIMPO do material
    (moodle_label + título). Capado. 0.0 quando o índice falta ou não casa."""
    by_date = (lessons_index or {}).get("by_date") or {}
    if not by_date:
        return 0.0
    lesson_tokens: set = set()
    for session in block.get("sessions") or []:
        topic = by_date.get(str(session.get("date") or ""))
        if topic:
            lesson_tokens |= _concept_tokens(str(topic), normalize)
    if not lesson_tokens:
        return 0.0
    clean = " ".join(p for p in (
        str(signals.get("moodle_label_text", "") or ""),
        str(signals.get("title_text", "") or ""),
    ) if p)
    clean_tokens = _concept_tokens(clean, normalize)
    overlap = len(clean_tokens & lesson_tokens)
    if overlap <= 0:
        return 0.0
    return W_LESSON * float(min(overlap, LESSON_OVERLAP_CAP))


def concept_token_weights(
    corpus: Sequence[object],
    *,
    scope: str,
    tool_tokens: Optional[set] = None,
    normalize: Optional[Callable[[str], str]] = None,
) -> Dict[str, float]:
    norm = normalize or normalize_match_text
    tools = {t for t in (tool_tokens or set()) if t}
    frequency: Dict[str, int] = {}
    for item in corpus or []:
        for token in _concept_tokens(_concept_text(item), norm):
            frequency[token] = frequency.get(token, 0) + 1

    weights: Dict[str, float] = {}
    for token, freq in frequency.items():
        rarity = 0.0 if token in UNIT_GENERIC_TOKENS else (1.0 / freq)
        weight = 1.0 + IDF_WEIGHT * (rarity - 1.0)
        if scope == "block" and (token in tools or token in FORMAT_TOKENS):
            weight = min(weight, _BLOCK_TOOL_FLOOR)
        weights[token] = weight
    return weights


def concept_vector(
    item: object,
    weights: Dict[str, float],
    *,
    normalize: Optional[Callable[[str], str]] = None,
) -> Dict[str, float]:
    norm = normalize or normalize_match_text
    return {
        token: weights[token]
        for token in _concept_tokens(_concept_text(item), norm)
        if token in weights
    }


class Assignment(TypedDict):
    block_id: str
    unit_slug: str
    subunit_slug: str
    confidence: float
    band: str
    method: str
    signals: dict
    conflict: Optional[dict]


def _block_unit_slug(block: dict) -> str:
    return str(block.get("unit_slug", "") or "")


def _unit_slug(unit: dict) -> str:
    return str(unit.get("slug", "") or unit.get("title", "") or "")


def _topic_unit_for_entry(
    entry_vec: Dict[str, float],
    units: List[dict],
    norm: Callable[[str], str],
) -> str:
    """Unidade que o CONCEITO do material sugeriria pelo plano (overlap do
    vetor de conceito da entry com os topicos de cada unidade). Vazio quando
    nenhuma unidade tem overlap — sem topico-unit nao ha conflito a flagar."""
    if not entry_vec:
        return ""
    best_slug = ""
    best = 0.0
    for unit in units or []:
        unit_tokens = _concept_tokens(_concept_text(unit), norm)
        overlap = sum(w for tok, w in entry_vec.items() if tok in unit_tokens)
        if overlap > best:
            best = overlap
            best_slug = _unit_slug(unit)
    return best_slug if best > 0.0 else ""


def _tool_unit(tool_tokens: set, units: List[dict], norm: Callable[[str], str]) -> str:
    """Unidade cuja descrição contém a ferramenta do material (ex. 'dafny'->u2).

    Derivado das topics da unidade (SEM hardcode de cadeira). A ferramenta é sinal
    de UNIDADE (um Dafny não cabe numa unidade Isabelle), embora não discrimine
    BLOCO dentro da unidade. '' quando a ferramenta não casa nenhuma unidade
    (degradação honesta = sem âncora)."""
    if not tool_tokens:
        return ""
    for unit in units or []:
        if tool_tokens & _concept_tokens(_concept_text(unit), norm):
            return _unit_slug(unit)
    return ""


def _llm_vote(llm_curation: Optional[dict]) -> Dict[str, float]:
    if not llm_curation:
        return {}
    try:
        conf = float(llm_curation.get("block_match_confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf)) or 0.6  # sem confianca explicita: voto medio
    votes: Dict[str, float] = {}
    primary = str(llm_curation.get("primary_block_id") or "").strip()
    if primary:
        votes[primary] = conf
    for sec in llm_curation.get("secondary_block_ids") or []:
        sid = str(sec or "").strip()
        if sid and sid not in votes:
            votes[sid] = conf * LLM_SECONDARY_FRAC
    return votes


def _manual_block_id(entry: dict, blocks: List[dict]) -> str:
    raw = str(entry.get("manual_timeline_block_id") or "").strip()
    if not raw:
        return ""
    ids = {str(b.get("id", "")).strip() for b in blocks or []}
    return raw if raw in ids else ""


def resolve_material_assignment(
    entry: dict,
    blocks: List[dict],
    units: List[dict],
    *,
    signals: dict,
    llm_curation: Optional[dict] = None,
    lessons_index: Optional[dict] = None,
) -> Assignment:
    norm = normalize_match_text
    blocks = list(blocks or [])
    units = list(units or [])

    # Tier 1 (manual): override vence tudo.
    manual = _manual_block_id(entry, blocks)
    if manual:
        winner = next((b for b in blocks if str(b.get("id", "")) == manual), None)
        return Assignment(
            block_id=manual,
            unit_slug=_block_unit_slug(winner) if winner else "",
            subunit_slug="",
            confidence=1.0,
            band=confidence_band(1.0),
            method="manual",
            signals={"manual": manual},
            conflict=None,
        )

    if not blocks:
        return Assignment(
            block_id="", unit_slug="", subunit_slug="", confidence=0.0,
            band=confidence_band(0.0), method="empty", signals={}, conflict=None,
        )

    # Pesos de conceito no ESCOPO de bloco (down-weight de ferramenta/formato da
    # 2.1) sobre os blocos candidatos; vetor de conceito da entry uma vez.
    tool_tokens = {
        tok for tok in str(signals.get("tool_tags_text", "") or "").split() if tok
    }
    weights = concept_token_weights(blocks, scope="block", tool_tokens=tool_tokens, normalize=norm)
    # Vetor de conceito da ENTRY a partir dos SIGNALS ja normalizados pelo funil
    # (title_text traz o split camelCase) + concepts do Gemini = o CONTEUDO.
    # Construir do entry dict cru perderia o split camelCase ("CorrecaoTerminacao"
    # ficaria 1 token, sem casar "correcao"/"terminacao").
    content_text = " ".join(
        p for p in (
            str(signals.get("title_text", "") or ""),
            # alavanca 1: label do recurso Moodle — identidade LIMPA do material
            # (o professor nomeia o tópico, ex. "Floyd-Hoare"→bloco-10). Entra no
            # conteúdo conceitual junto do title/markdown/concepts.
            str(signals.get("moodle_label_text", "") or ""),
            str(signals.get("markdown_text", "") or ""),
            " ".join(str(c or "") for c in (entry.get("concepts") or [])),
        ) if p
    )
    content_vec = concept_vector(content_text, weights, normalize=norm)
    # source_section: hint posicional FRACO (janela do cronograma), so onde nao
    # ja coberto pelo conteudo.
    section_vec = {
        tok: w * SECTION_CONCEPT_FRAC
        for tok, w in concept_vector(
            str(entry.get("source_section", "") or ""), weights, normalize=norm
        ).items()
        if tok not in content_vec
    }
    entry_vec = {**section_vec, **content_vec}

    votes = _llm_vote(llm_curation)
    # Lazy-resolve legacy bloco-NN vote keys to uuid
    if votes and blocks:
        _resolved_votes: Dict[str, float] = {}
        for _k, _v in votes.items():
            if _POS_RE.match(str(_k)):
                _r = _rbr(_k, blocks)
                _k = _r if _r else _k
            _resolved_votes[_k] = _v
        votes = _resolved_votes

    scored: List[tuple] = []
    for block in blocks:
        block_vec = concept_vector(block, weights, normalize=norm)
        overlap = sum(
            min(entry_vec[tok], block_vec[tok])
            for tok in entry_vec.keys() & block_vec.keys()
        )
        bid = str(block.get("block_uuid") or block.get("id") or "")
        llm_term = votes.get(bid, 0.0)
        date_term = _score_block_date_match(signals, block)
        seq_term = score_sequence_match(signals, block)
        card_term = score_card_evidence_against_entry(
            signals, block.get("card_evidence", []) or [], normalize_match_text=norm
        )
        lesson_term = score_lesson_match(signals, block, lessons_index, norm)
        fused = (
            W_CONCEPT * overlap
            + W_LLM * llm_term
            + date_term
            + seq_term
            + card_term
            + lesson_term
        )
        scored.append((block, fused, {
            "concept": round(overlap, 4),
            "llm": round(llm_term, 4),
            "date": round(date_term, 4),
            "sequence": round(seq_term, 4),
            "card": round(card_term, 4),
            "lesson": round(lesson_term, 4),
            "fused": round(fused, 4),
            "authoritative_card": card_term >= CARD_AUTHORITATIVE,
        }))

    # Tier 2 (card/data autoritativo): se ALGUM bloco tem card-evidence forte,
    # ele vence o concept-match. Senao, o fundido (Tier 3) decide. Posicional
    # (Tier 4) e o fallback: empate/tudo-zero -> ordem dos blocos.
    authoritative = [s for s in scored if s[2]["authoritative_card"]]
    pool = authoritative if authoritative else scored
    pool.sort(key=lambda s: s[1], reverse=True)

    winner, best_score, winner_breakdown = pool[0]
    runner_up_score = pool[1][1] if len(pool) > 1 else 0.0

    if authoritative:
        method = "card"
    elif best_score <= 0.0:
        method = "positional"
    else:
        method = "concept-fused"

    confidence = relative_margin_confidence(best_score, runner_up_score)
    if method == "positional":
        confidence = 0.0

    block_unit = _block_unit_slug(winner)
    topic_unit = _topic_unit_for_entry(entry_vec, units, norm)
    tool_unit = _tool_unit(tool_tokens, units, norm)

    # Conflito (spec 4.5/9): bloco-unit != topico-unit (fontes fortes discordam
    # da unidade). O bloco (agendado) vence a unit; o conflito e flagado e a
    # subunit fica RESTRITA a unidade vencedora (nunca de outra unidade).
    conflict: Optional[dict] = None
    if topic_unit and block_unit and topic_unit != block_unit:
        conflict = {
            "kind": "block_unit_vs_topic_unit",
            "block_unit": block_unit,
            "topic_unit": topic_unit,
            "block_id": str(winner.get("id", "")),
        }
        confidence = min(confidence, 0.45)
    # Conflito tool-unit: a ferramenta (.dfy/.thy/.smv) ancora a UNIDADE — um
    # material Dafny num bloco Isabelle e incoerente. Capa a confianca (degradacao
    # honesta), sem mudar o bloco; impede que um label lexicalmente ambiguo
    # ("Tipos Indutivos" -> bloco-04) vire confiante-errado.
    if tool_unit and block_unit and tool_unit != block_unit:
        confidence = min(confidence, 0.45)
        if conflict is None:
            conflict = {
                "kind": "block_unit_vs_tool_unit",
                "block_unit": block_unit,
                "tool_unit": tool_unit,
                "block_id": str(winner.get("id", "")),
            }

    # Subunit restrita a unidade vencedora: esta task nao resolve subunit (e da
    # rota de topico), entao deixa vazio — o invariante e que NUNCA escape a
    # unidade do bloco. A flag de conflito carrega o diagnostico.
    subunit_slug = ""

    return Assignment(
        block_id=str(winner.get("block_uuid") or winner.get("id") or ""),
        unit_slug=block_unit,
        subunit_slug=subunit_slug,
        confidence=confidence,
        band=confidence_band(confidence),
        method=method,
        signals=winner_breakdown,
        conflict=conflict,
    )
