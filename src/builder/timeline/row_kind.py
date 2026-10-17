"""Tipo de cada LINHA do cronograma (#52): rotulo cru + sinal do professor, sem heuristica sobre o conteudo do bloco.

Precedencia: Atividade != Aula > marcador {kind=...} com sentido de tipo > forma do rotulo (cue na CABECA,
sem topico depois) > aula. Duvidas/atendimento cuja proxima linha decisiva e prova vira review.
Regras medidas no W-Y v3 (c1-3/wy3_kind_por_linha_05-10.py) com as adjudicacoes do usuario de 05/10.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from src.builder.timeline.classifier import STRONG_EXAM_RE
from src.builder.timeline.kinds import BlockKind
from src.utils.helpers import ATIVIDADE_KIND_MAP, norm_ascii_lower

_FERIADOS = {
    "carnaval", "tiradentes", "corpus christi", "paixao de cristo", "sexta feira santa", "independencia",
    "finados", "proclamacao da republica", "consciencia negra", "nossa senhora aparecida", "natal",
    "pascoa", "dia do trabalho", "dia do trabalhador", "confraternizacao universal",
}
# (kind, regex ancorada na CABECA do rotulo); ordem = prioridade.
_REGRAS_ROTULO = [
    ("holiday", re.compile(r"^feriado\b")),
    ("suspended", re.compile(r"^(suspens\w*|greve|paralisacao|assembleia)\b")),
    ("reserved", re.compile(r"^reserva( tecnica)?$")),
    ("academic_event", re.compile(r"^(semana academica|semana cientifica|evento academico|aula magna|simposio|congresso"
                                  r"|jornada|ciclo de palestras|seminario integrador)\b")),
    ("results", re.compile(r"^(divulgacao|devolucao|devolutiva)\b")),
    ("makeup", re.compile(r"^(reposicao|prova de substituicao|substituicao)\b")),
    ("workshop", re.compile(r"^oficina\b")),
    ("deliverable", re.compile(r"^(entrega|apresentacao) (do |de |da )?(trabalho|t\d|tp\d|tf)\b")),
    ("review", re.compile(r"^(exercicios de )?revisao\b")),
    ("office_hours", re.compile(r"^(aula de duvidas|duvidas|atendimento|plantao|monitoria)\b")),
    # "introducao" sozinha; "apresentacao da disciplina" e aula (adjudicacao 05/10).
    ("overview", re.compile(r"^introducao$|^(plano de ensino|ementa)\b")),
    # cabeca de prova so com sinal forte ("prova de teoremas" e aula).
    ("assessment", re.compile(r"^(prova|avaliacao|exame|p[1-4]|pf|g2|ps)\b")),
    ("planning", re.compile(r"^(planejamento|reuniao|conselho)\b")),
]
_MARCADOR_TRADUZ = {"suspension": BlockKind.SUSPENDED.value, "event": BlockKind.ACADEMIC_EVENT.value}
_MARCADOR_PROVA = {"g2": BlockKind.ASSESSMENT.value, "ps": BlockKind.MAKEUP.value}
_VALIDOS = {k.value for k in BlockKind}
_PULA_ADJ = {BlockKind.HOLIDAY.value, BlockKind.SUSPENDED.value, BlockKind.ACADEMIC_EVENT.value, BlockKind.RESERVED.value}
_PROVA = {BlockKind.ASSESSMENT.value, BlockKind.MAKEUP.value}


def rotulo(text: str) -> str:
    """Rotulo cru normalizado SEM descartar palavra ("ao", "IP" ficam)."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", norm_ascii_lower(str(text or ""))).split())


def tipo_do_rotulo(label: str) -> str:
    for kind, rx in _REGRAS_ROTULO:
        if rx.match(label) and (kind != "assessment" or STRONG_EXAM_RE.search(label)):
            return kind
    return BlockKind.HOLIDAY.value if label in _FERIADOS else BlockKind.CLASS.value


def tipo_da_linha(label: str, marcador: str, atividade: str) -> Tuple[str, bool]:
    """(kind, veio_so_do_rotulo) de uma linha; `label` ja normalizado por `rotulo`, sem o marcador."""
    atividade = norm_ascii_lower(atividade or "")
    if "substituicao" in atividade:
        return BlockKind.MAKEUP.value, False
    for needle, mapped in ATIVIDADE_KIND_MAP.items():
        if needle in atividade:
            return _MARCADOR_TRADUZ.get(mapped, mapped), False
    if marcador:
        if marcador in _MARCADOR_PROVA:
            # g2/ps e periodo: so vira prova com rotulo de prova ou sem rotulo (P1c, adjudicado 05/10)
            if not label or STRONG_EXAM_RE.search(label) or label.startswith("prova"):
                return _MARCADOR_PROVA[marcador], False
            return tipo_do_rotulo(label), False
        if marcador in _MARCADOR_TRADUZ:
            kind = tipo_do_rotulo(label)
            return (kind if kind != BlockKind.CLASS.value else _MARCADOR_TRADUZ[marcador]), False
        if marcador in _VALIDOS:
            return marcador, False
    return tipo_do_rotulo(label), True


def aplica_adjacencia(linhas: List[Dict[str, object]]) -> None:
    """Duvidas/atendimento cuja proxima linha decisiva e prova vira review (`review_duvidas`). In-place.
    Pula linhas vazias, de calendario e outras de duvidas do proprio rotulo (cadeia antes da prova)."""
    for i, linha in enumerate(linhas):
        if linha["kind"] != BlockKind.OFFICE_HOURS.value:
            continue
        proxima = ""
        for p in linhas[i + 1:]:
            if p["vazia"] or p["kind"] in _PULA_ADJ or (p["so_rotulo"] and p["kind"] == BlockKind.OFFICE_HOURS.value):
                continue
            proxima = p["kind"]
            break
        if proxima in _PROVA:
            linha["kind"] = BlockKind.REVIEW.value
            linha["review_duvidas"] = True
