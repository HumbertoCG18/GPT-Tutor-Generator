from __future__ import annotations

import re
from datetime import date

__all__ = ["extract_dates"]

# Ordem importa: padrões COM ano vêm antes dos year-less para que a varredura
# consuma o span completo (ex.: "12/03/2025" não deve reaparecer como o
# year-less "12/03"). ISO é o único month-first; os demais são day-first
# (DD.MM, convenção brasileira — herdada do regex DD.MM original do scorer).
#
# Separadores: as formas COM ano (_DMY) ainda toleram espaço porque o ano de 4
# dígitos as desambigua. Os year-less se dividem em dois casos:
#   * separador REAL `[.\-/]` (_DM_SEP_RE): "12.03"/"12/03"/"12-03" — o ponto/
#     barra/traço é intencional, então casa em qualquer posição.
#   * ESPAÇO (_DM_SPACE_RE): só casa ANCORADO no início do texto. Motivo: os
#     scorers passam texto JÁ normalizado (normalize_match_text colapsa "12.03"
#     -> "12 03"); uma data real de material vive no INÍCIO do título/arquivo
#     ("12 03 processos"), mas pares de números no MEIO da prosa são subcapítulo
#     /versão ("capitulo 5 12", "versao 2 10 1") e NÃO são datas. Ancorar o caso
#     espaço mata esses falso-positivos (que aplicavam o boost +0.30 mais forte)
#     preservando datas reais — espelha o blast radius do antigo regex `^DD MM`.
_SEP = r"[.\-/ ]"
_REAL_SEP = r"[.\-/]"
_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DMY_RE = re.compile(rf"(?<!\d)(\d{{1,2}}){_SEP}(\d{{1,2}}){_SEP}(\d{{4}})(?!\d)")
# Year-less com separador real, em qualquer posição. Guards contra a forma de
# VERSÃO de 3+ partes ("2.10.1"), que não tem ano de 4 dígitos e portanto não é
# consumida pelo _DMY: rejeitamos o match se ele for PRECEDIDO por dígito+sep
# (`(?<!\d.)...` — é a cabeça "2." de "2.10.1") OU SEGUIDO por sep+dígito
# (`(?!{_REAL_SEP}\d)` — é o tail ".1"). Assim nem "2.10" nem "10.1" emitem data.
_DM_SEP_RE = re.compile(
    rf"(?<!\d)(?<!\d.)(\d{{1,2}}){_REAL_SEP}(\d{{1,2}})(?!\d)(?!{_REAL_SEP}\d)"
)
# Year-less separado por ESPAÇO: ancorado no início do texto (^), com \s à
# direita ou fim — só dispara para "DD MM ..." no começo, nunca no meio da prosa.
_DM_SPACE_RE = re.compile(r"^(\d{1,2}) (\d{1,2})(?!\d)(?! \d)")


def _safe_date(year: int, month: int, day: int) -> date | None:
    # Datas inválidas (ex.: 32.13) são puladas, nunca levantam — o chamador
    # (scorer) não deve quebrar por causa de um nome de arquivo malformado.
    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_dates(text: str, *, default_year: int | None = None) -> list[date]:
    """Extrai todas as datas reconhecíveis de ``text``, em qualquer posição.

    Reconhece ISO ``YYYY-MM-DD``, ``DD.MM.YYYY``/``DD/MM/YYYY``/``DD-MM-YYYY``
    e os year-less ``DD.MM``/``DD/MM``/``DD-MM`` (day-first, convenção BR).

    Para os year-less, o ano é assumido como ``default_year`` (o ano do curso,
    derivado do período do bloco pelo chamador). Quando nenhum ano está
    disponível — nem no texto nem em ``default_year`` — o match year-less é
    PULADO em vez de chutar um ano: um boost de data baseado num ano arbitrário
    seria pior que ausência de sinal (cairia no match textual existente, que é
    o comportamento atual preservado; cf. spec, bordas "texto sem data").

    Determinístico, sem rede. Datas inválidas são ignoradas. O resultado é
    deduplicado preservando a ordem de aparição.
    """
    if not text:
        return []

    found: list[date] = []
    consumed: list[tuple[int, int]] = []  # spans já casados por padrões com ano

    def _overlaps(start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in consumed)

    for match in _ISO_RE.finditer(text):
        dt = _safe_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if dt:
            found.append(dt)
        consumed.append(match.span())

    for match in _DMY_RE.finditer(text):
        if _overlaps(*match.span()):
            continue
        dt = _safe_date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        if dt:
            found.append(dt)
        consumed.append(match.span())

    if default_year is not None:
        for year_less_re in (_DM_SEP_RE, _DM_SPACE_RE):
            for match in year_less_re.finditer(text):
                if _overlaps(*match.span()):
                    continue
                dt = _safe_date(default_year, int(match.group(2)), int(match.group(1)))
                if dt:
                    found.append(dt)

    # Dedup preservando ordem (resultado precisa ser determinístico e estável).
    seen: set[date] = set()
    ordered: list[date] = []
    for dt in found:
        if dt not in seen:
            seen.add(dt)
            ordered.append(dt)
    return ordered
