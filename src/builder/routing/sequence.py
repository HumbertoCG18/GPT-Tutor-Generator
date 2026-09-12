"""Sinal de sequencia: ordinal de aula ("Aula 03") -> bloco da N-esima aula.

Funcoes puras. Operam sobre texto JA normalizado por normalize_match_text
(NFKD->ascii->lower->[a-z0-9 ]->colapsa espacos), entao tokens sao palavras
minusculas separadas por espaco unico. Sem I/O, sem estado.
"""
from __future__ import annotations

import re
from typing import List, Optional

from src.builder.routing.thresholds import T

# Marcador de aula seguido (espaco opcional, p/ casar "aula03" colado) de um
# inteiro de ate 3 digitos com fronteira de palavra apos. A fronteira (\b)
# impede casar ano colado ("aula2024" -> 4 digitos, sem fronteira em 3) e exige
# que o numero termine o token. So "aula"/"encontro" disparam — "lista", "prova",
# "capitulo" nao tem marcador e retornam None.
_LECTURE_ORDINAL_RE = re.compile(r"\b(?:aula|encontro)\s*(\d{1,3})\b")


def extract_lecture_ordinal(text: str) -> Optional[int]:
    """Ordinal de aula do texto normalizado, ou None.

    Pega o numero adjacente ao primeiro marcador de aula. "aula 03 2024" -> 3.
    """
    match = _LECTURE_ORDINAL_RE.search(text or "")
    if not match:
        return None
    return int(match.group(1))


def annotate_class_ordinals(blocks: List[dict]) -> List[dict]:
    """Carimba block["class_ordinal"] = 1,2,3... nos blocos kind=class, na ordem
    em que aparecem em `blocks` (o caller ja entrega ordenado cronologicamente).
    Blocos de outro kind (ou sem kind) recebem class_ordinal=None. Idempotente.
    Muta os dicts in-place (consistente com rows/scores) e retorna a lista.

    Carimba TAMBEM block["session_ordinals"]: os ordinais de ENCONTRO (1 por
    sessao de aula, contagem global cronologica) que este bloco cobre. Motivo:
    o professor numera "Aula N" por ENCONTRO, nao por bloco — um bloco tematico
    pode agrupar varias aulas (TCC bloco-03 = 3 encontros), entao class_ordinal
    desanda a partir do primeiro agrupamento. Medido no TCC: alvo por sessao
    bate o gold em 16/19; por bloco, 1/19.
    """
    counter = 0
    session_counter = 0
    for block in blocks:
        if str(block.get("kind") or "") == "class":
            counter += 1
            block["class_ordinal"] = counter
            n_sessions = len(block.get("sessions") or []) or 1
            block["session_ordinals"] = list(
                range(session_counter + 1, session_counter + 1 + n_sessions)
            )
            session_counter += n_sessions
        else:
            block["class_ordinal"] = None
            block["session_ordinals"] = []
    return blocks


def score_sequence_match(signals: dict, block: dict, *, boost: float = T.SEQUENCE_BOOST) -> float:
    """Boost de desempate quando o ordinal de aula do material casa o
    class_ordinal do bloco. Extrai do title_text; cai para raw_text. Retorna
    `boost` no match, senao 0.0. Inerte quando o material nao tem ordinal ou o
    bloco nao e de aula (class_ordinal None/ausente).
    """
    ordinal = extract_lecture_ordinal(signals.get("title_text", ""))
    if ordinal is None:
        ordinal = extract_lecture_ordinal(signals.get("raw_text", ""))
    if ordinal is None:
        return 0.0
    # Alvo primario: ordinal de ENCONTRO (o professor numera aulas, e um bloco
    # tematico pode cobrir varias). Fallback class_ordinal p/ blocos sem
    # sessions (fixtures minimas) — preserva o comportamento historico.
    session_ordinals = block.get("session_ordinals")
    if session_ordinals:
        return float(boost) if ordinal in session_ordinals else 0.0
    class_ordinal = block.get("class_ordinal")
    if class_ordinal is not None and class_ordinal == ordinal:
        return float(boost)
    return 0.0
