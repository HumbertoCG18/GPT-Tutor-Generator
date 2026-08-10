"""TDD para override de FRONTEIRA por data (T9c, cura SO).

Rows reais do SO (SYLLABUS.md, colunas Data/Descrição), reimportando o
parser real (`_parse_syllabus_timeline` + `_build_timeline_candidate_rows`)
em vez de reimplementar a lógica "de memória". Cobre os 2 casos da
investigação T9b:
  - bloco-03 (10-31/03, 7 aulas): hoje 1 bloco só; deve partir em
    [10-17/03] + [19-31/03] com boundary 2026-03-19.
  - bloco-05 (07-16/04, 4 aulas): hoje 1 bloco só; deve partir em
    [07-09/04] + [14-16/04] com boundary 2026-04-14.
"""

from __future__ import annotations

from src.builder.timeline.index import (
    _build_timeline_candidate_rows,
    _build_timeline_index,
    _parse_syllabus_timeline,
)

# bloco-03 real (SO, 10-31/03, 7 aulas) e bloco-05 real (SO, 07-16/04, 4
# aulas) isolados cada um em sua própria tabela — mesma fatia que
# `_build_timeline_index` recebe já contígua no curso real, sem o feriado
# de 02/04 no meio (que já quebra bloco-03/bloco-05 hoje via kind
# standalone; irrelevante para o mecanismo de boundary sob teste aqui).
_SYLLABUS_BLOCO03 = """
| # | Dia | Data | Hora | Descrição | Atividade | Recursos |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | TER | 10/03/2026 | LM 19:15 - 20:45 | Histórico e evolução dos sistemas operacionais | Aula |  |
| 4 | QUI | 12/03/2026 | LM 19:15 - 20:45 | Estruturas dos sistemas operacionais, processos, chamadas de sistema | Aula |  |
| 5 | TER | 17/03/2026 | LM 19:15 - 20:45 | Estruturas dos sistemas operacionais, processos, chamadas de sistema | Aula |  |
| 6 | QUI | 19/03/2026 | LM 19:15 - 20:45 | Gerência do processador, processos, chamadas de sistema, escalonamento | Aula |  |
| 7 | TER | 24/03/2026 | LM 19:15 - 20:45 | Gerência do processador, processos, chamadas de sistema, escalonamento | Aula |  |
| 8 | QUI | 26/03/2026 | LM 19:15 - 20:45 | Gerência do processador, threads e exclusão mútua | Aula |  |
| 9 | TER | 31/03/2026 | LM 19:15 - 20:45 | Gerência do processador, threads e exclusão mútua | Aula |  |
"""

_SYLLABUS_BLOCO05 = """
| # | Dia | Data | Hora | Descrição | Atividade | Recursos |
| --- | --- | --- | --- | --- | --- | --- |
| 10 | TER | 07/04/2026 | LM 19:15 - 20:45 | Gerência do processador, sincronização e deadlock | Aula |  |
| 11 | QUI | 09/04/2026 | LM 19:15 - 20:45 | Gerência do processador, sincronização e deadlock | Aula |  |
| 12 | TER | 14/04/2026 | LM 19:15 - 20:45 | Especificação TP1; Gerência do processador, sincronização e deadlock | Aula |  |
| 13 | QUI | 16/04/2026 | LM 19:15 - 20:45 | Especificação TP1; Gerência do processador, sincronização e deadlock | Aula |  |
"""


def _candidate_rows(syllabus_md: str):
    timeline = _parse_syllabus_timeline(syllabus_md)
    return _build_timeline_candidate_rows(timeline)


def _dates(block):
    return [r["date_dt"].strftime("%Y-%m-%d") for r in block["rows"]]


def test_bloco03_merges_to_one_block_without_boundary_dates():
    """Baseline atual (sem override): as 7 linhas de bloco-03 viram 1 bloco só."""
    rows = _candidate_rows(_SYLLABUS_BLOCO03)
    blocks = _build_timeline_index(rows, unit_index=[])["blocks"]
    assert len(blocks) == 1
    assert len(blocks[0]["rows"]) == 7


def test_bloco05_merges_to_one_block_without_boundary_dates():
    """Baseline atual (sem override): as 4 linhas de bloco-05 viram 1 bloco só."""
    rows = _candidate_rows(_SYLLABUS_BLOCO05)
    blocks = _build_timeline_index(rows, unit_index=[])["blocks"]
    assert len(blocks) == 1
    assert len(blocks[0]["rows"]) == 4


def test_boundary_date_splits_bloco03_into_u01_u02_slices():
    """Com boundary_dates={19/03}: bloco-03 parte em [10-17/03] + [19-31/03]."""
    rows = _candidate_rows(_SYLLABUS_BLOCO03)
    blocks = _build_timeline_index(
        rows, unit_index=[], boundary_dates={"2026-03-19"}
    )["blocks"]
    assert len(blocks) == 2
    assert _dates(blocks[0]) == ["2026-03-10", "2026-03-12", "2026-03-17"]
    assert _dates(blocks[1]) == ["2026-03-19", "2026-03-24", "2026-03-26", "2026-03-31"]


def test_boundary_date_splits_bloco05_into_deadlock_tp1_slices():
    """Com boundary_dates={14/04}: bloco-05 parte em [07-09/04] + [14-16/04]."""
    rows = _candidate_rows(_SYLLABUS_BLOCO05)
    blocks = _build_timeline_index(
        rows, unit_index=[], boundary_dates={"2026-04-14"}
    )["blocks"]
    assert len(blocks) == 2
    assert _dates(blocks[0]) == ["2026-04-07", "2026-04-09"]
    assert _dates(blocks[1]) == ["2026-04-14", "2026-04-16"]


def test_boundary_dates_none_is_equivalent_to_absent():
    """Raio zero: boundary_dates=None (curso sem a chave) == comportamento atual."""
    rows = _candidate_rows(_SYLLABUS_BLOCO03)
    without_kw = _build_timeline_index(rows, unit_index=[])
    with_none = _build_timeline_index(rows, unit_index=[], boundary_dates=None)
    assert len(without_kw["blocks"]) == len(with_none["blocks"]) == 1


def test_boundary_dates_empty_set_is_equivalent_to_absent():
    """Raio zero: boundary_dates=set() também não força nada."""
    rows = _candidate_rows(_SYLLABUS_BLOCO03)
    blocks = _build_timeline_index(rows, unit_index=[], boundary_dates=set())["blocks"]
    assert len(blocks) == 1
