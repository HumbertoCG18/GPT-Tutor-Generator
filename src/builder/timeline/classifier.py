"""Classificador unico de blocos do cronograma.

`classify_block(block) -> BlockKind` consolida toda heuristica de deteccao
(antes espalhada em `_timeline_row_is_review_or_assessment` + audit script + UI).

Determinista: keywords + regex em ordem de prioridade. Sem LLM.
Mais especifico bate primeiro. Excecao critica: bloco de apresentacao do
plano de ensino NUNCA cai em assessment mesmo contendo "avaliacao".
"""

from __future__ import annotations

import re
from typing import Iterable, List, Mapping, Pattern, Tuple, Union

from src.builder.text.normalize import normalize_match_text
from .kinds import BlockKind


def _norm(text: str) -> str:
    # Delega para a fonte unica; sem em-dash->hyphen e sem fix de typo porque
    # o comportamento historico do classifier deixa — virar espaco via regex.
    return normalize_match_text(text, em_dash_to_hyphen=False, fix_typos=False)


# Excecao: se qualquer um destes termos aparecer, kind=CLASS mesmo se
# bater keyword de outro tipo. Pega caso "apresentacao do plano de ensino +
# avaliacao do curso" (IA bloco-01) e similares.
CLASS_INTRO_TERMS: Tuple[str, ...] = (
    "apresentacao",
    "plano de ensino",
    "plano ensino",
    "cronograma da disciplina",
    "ementa",
)


KeywordSpec = Union[str, Pattern[str]]


def _phrase_match(needle: str, hay: str, hay_tokens: set) -> bool:
    """Substring se multi-palavra, token-exato se 1 palavra (>=4 chars)."""
    needle = needle.strip()
    if not needle or not hay:
        return False
    if " " in needle:
        return needle in hay
    if len(needle) < 4:
        return needle in hay_tokens
    return needle in hay_tokens


KIND_KEYWORDS: List[Tuple[BlockKind, List[KeywordSpec]]] = [
    (BlockKind.HOLIDAY, [
        "feriado", "carnaval", "natal", "pascoa", "corpus",
        "tiradentes", "independencia", "finados", "consciencia negra",
        "aparecida", "nossa senhora",
    ]),
    (BlockKind.SUSPENDED, [
        "suspensao", "suspenso", "suspensa", "greve",
        "paralisacao", "assembleia",
    ]),
    (BlockKind.MAKEUP, [
        "substituicao", "reposicao",
    ]),
    (BlockKind.ACADEMIC_EVENT, [
        "evento academico", "semana academica", "semana cientifica",
        "simposio", "congresso", "jornada", "ciclo de palestras",
        "seminario integrador",
    ]),
    (BlockKind.RESULTS, [
        "divulgacao", "devolucao", "devolutiva",
    ]),
    (BlockKind.DELIVERABLE, [
        "entrega trabalho", "entrega final", "entrega do trabalho",
        "submissao final",
    ]),
    (BlockKind.WORKSHOP, [
        "oficina", "lancamento", "kick off", "kickoff",
    ]),
    (BlockKind.OFFICE_HOURS, [
        "atendimento", "duvidas", "plantao", "monitoria",
    ]),
    (BlockKind.PLANNING, [
        "planejamento", "reuniao", "conselho",
    ]),
    (BlockKind.RESERVED, [
        "reserva tecnica", "reserva",
    ]),
    (BlockKind.ASSESSMENT, [
        re.compile(r"\bp[1-4]\b"),
        re.compile(r"\bpf\b"),
        "prova", "avaliacao", "exame", "recuperacao",
        "substitutiva", "teste",
    ]),
    (BlockKind.REVIEW, [
        "revisao",
    ]),
]


def _content_text(block: Mapping[str, object]) -> str:
    """Campos de CONTEUDO pedagogico (sem period_label, que e so calendario)."""
    parts: List[str] = []
    for key in ("topic_text", "primary_topic_label"):
        val = block.get(key)
        if isinstance(val, str) and val:
            parts.append(val)
    topics = block.get("topics")
    if isinstance(topics, list):
        parts.extend(str(t) for t in topics if t)
    return " ".join(parts)


def _session_text(block: Mapping[str, object]) -> str:
    """Labels crus das sessoes (texto original das linhas do cronograma)."""
    sessions = block.get("sessions")
    if not isinstance(sessions, list):
        return ""
    parts: List[str] = []
    for sess in sessions:
        if isinstance(sess, Mapping):
            label = sess.get("label")
            if isinstance(label, str) and label:
                parts.append(label)
    return " ".join(parts)


# Sinal forte de prova nas sessoes: P1-P4, PF, G2, PS, "prova N", "prova final".
# "prova" sozinho NAO basta ("prova de teoremas" = demonstracao, nao exame).
_STRONG_EXAM_RE = re.compile(r"\bp[1-4]\b|\bpf\b|\bg2\b|\bps\b|\bprova\s+\d+\b|\bprova\s+final\b")


def _session_exam_or_review(session_hay: str) -> Union[BlockKind, None]:
    """Reclassifica por label de sessao quando o conteudo curado nao decide.

    So para blocos sem unidade (provas/revisoes nao tem unidade pedagogica).
    `correcao` indica AULA de correcao de prova (CLASS), nao a prova -> ignora.
    """
    if not session_hay or "correcao" in session_hay:
        return None
    if _STRONG_EXAM_RE.search(session_hay):
        return BlockKind.ASSESSMENT
    if "revisao" in session_hay.split():
        return BlockKind.REVIEW
    return None


def _text_of(block: Mapping[str, object]) -> str:
    """Conteudo + period_label. Usado no matching de keywords (feriado etc.
    podem vir no rotulo do periodo)."""
    label = block.get("period_label")
    label_str = label if isinstance(label, str) else ""
    return f"{_content_text(block)} {label_str}".strip()


def _has_unit_evidence(block: Mapping[str, object]) -> bool:
    """Bloco tem sinal de unidade (slug atribuido ou candidatos de topico)."""
    if block.get("unit_slug") or block.get("auto_unit_slug"):
        return True
    cands = block.get("topic_candidates")
    return isinstance(cands, list) and bool(cands)


def classify_block(block: Mapping[str, object]) -> BlockKind:
    """Retorna BlockKind. Manual override vence; depois source_kind (SARC); senao texto/sessao."""
    override = block.get("manual_kind_override")
    if isinstance(override, str):
        try:
            return BlockKind(override)
        except ValueError:
            pass

    # Hint autoritativo do SARC (Atividade/cor). Vence texto/sessao/unidade,
    # perde so para o override manual acima.
    source = block.get("source_kind")
    if isinstance(source, str) and source:
        try:
            return BlockKind(source)
        except ValueError:
            pass

    hay_content = _norm(_content_text(block))
    hay_all = _norm(_text_of(block))
    has_unit = bool(block.get("unit_slug"))
    has_topic = bool(block.get("primary_topic_label"))
    session_hay = _norm(_session_text(block))

    # 1. Apresentacao/introducao/plano de ensino -> OVERVIEW (academica, sem
    #    unidade). Vence keyword (ex.: "plano de ensino e avaliacao" nao vira
    #    assessment). So dispara em conteudo intro generico/curto.
    if hay_content:
        if any(term in hay_content for term in CLASS_INTRO_TERMS):
            return BlockKind.OVERVIEW
        content_tokens = set(hay_content.split())
        if "introducao" in content_tokens and len(content_tokens) <= 2:
            return BlockKind.OVERVIEW

    # 2. Sem conteudo real: com unit ainda e aula; sem unit, sessao pode revelar
    #    prova/revisao (topico reduzido a stopword); senao slot reservado/vazio.
    if not hay_content:
        # Sessao com sinal forte de prova (P1-P4/PF/"prova N") ou "revisao"
        # vence a unidade propagada: bloco sem conteudo curado cuja sessao diz
        # "exercicios de revisao"/"prova p1" e revisao/prova mesmo que a
        # inferencia de unidade de vizinhos tenha preenchido um slug.
        sess_kind = _session_exam_or_review(session_hay)
        if sess_kind is not None:
            return sess_kind
        if has_unit:
            return BlockKind.CLASS
        return BlockKind.RESERVED if hay_all else BlockKind.UNKNOWN

    # 3. Keywords (sobre conteudo + period_label).
    hay_tokens = set(hay_all.split())
    for kind, specs in KIND_KEYWORDS:
        for spec in specs:
            if isinstance(spec, re.Pattern):
                if spec.search(hay_all):
                    return kind
            else:
                if _phrase_match(spec, hay_all, hay_tokens):
                    return kind

    # 3b. Conteudo curado nao bateu keyword. Sem unidade, o label cru da sessao
    #     ainda pode indicar prova/revisao real (ex.: topic_text "para").
    if not has_unit:
        sess_kind = _session_exam_or_review(session_hay)
        if sess_kind is not None:
            return sess_kind

    # 3c. "trabalho"/TP sem evidencia de unidade = apresentacao/entrega de
    #     trabalho (atravessa unidades) -> DELIVERABLE. Com unit_slug/candidatos
    #     "trabalho" e so o tema de uma aula -> CLASS abaixo (mantem unidade).
    #     Gated p/ nao roubar unidade de aula que cita "trabalho" (P3.4).
    if "trabalho" in hay_tokens and not _has_unit_evidence(block):
        return BlockKind.DELIVERABLE

    if has_unit or has_topic:
        return BlockKind.CLASS
    # 4. Substancia em CONTEUDO (>=8 chars OU >=2 tokens) sugere aula real sem
    #    unit/topic mapeados ainda (Phase 3/4 resolve depois). period_label NAO
    #    conta — datas nao sao conteudo. Fragmento curto -> UNKNOWN.
    content_tokens = set(hay_content.split())
    if len(hay_content) >= 8 or len(content_tokens) >= 2:
        return BlockKind.CLASS
    return BlockKind.UNKNOWN
