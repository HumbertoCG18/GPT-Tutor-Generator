"""Comparador do gate de frescor: os dois lados normalizam igual.

RED de 2026-08-11 (review final campanha 2): gate dava 3/5 com 6 diffs 100%
artefato — espaço duplo preservado pelo import vs colapsado pelo parse vivo,
e sessão agendada SEM descrição (real no SARC: IA 15/07, SO 16/07) presente
só no lado importado.
"""
from scripts.check_sarc_freshness import parse_live, parse_syllabus


def test_whitespace_duplo_nao_gera_diff():
    live = parse_live("- (18/03/2026) QUA — ML - Abordagem Supervisionada: k-NN [Aula]")
    imported = parse_syllabus(
        "| 3 | QUA | 18/03/2026 | x | ML - Abordagem  Supervisionada: k-NN | Aula |"
    )
    assert live == imported == {
        "2026-03-18": ("ML - Abordagem Supervisionada: k-NN", "Aula")
    }


def test_sessao_sem_descricao_fora_dos_dois_lados():
    # parse_html_schedule descarta a linha vazia do lado vivo; o importado
    # precisa descartar tambem, senao vira falso-stale eterno.
    imported = parse_syllabus("| 41 | QUA | 15/07/2026 | x |  | Aula |")
    assert imported == {}


def test_linha_com_descricao_segue_comparavel():
    imported = parse_syllabus("| 5 | SEG | 09/03/2026 | x | ML - Introdução à ML | Aula |")
    assert imported == {"2026-03-09": ("ML - Introdução à ML", "Aula")}
