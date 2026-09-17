"""Predicado admin-only sobre rows ignoradas (D2 — vivo no index/health).

Os testes do scorer legado (_score_entry_against_timeline_block descartando
rows ignoradas) morreram com o funil no cutover passo 3.
"""

from src.builder.timeline.index import timeline_block_is_administrative_only


def test_administrative_only_true_when_all_rows_ignored():
    block = {
        "rows": [
            {"content": "Prova PS", "ignored": True},
            {"content": "SE Day", "ignored": True},
        ]
    }
    assert timeline_block_is_administrative_only(block) is True


def test_administrative_only_ignores_ignored_rows_when_mixed():
    # One ignored + one pure-instructional → not administrative-only.
    block = {
        "rows": [
            {"content": "Prova PS", "ignored": True},
            {"content": "Provas por inducao", "ignored": False},
        ]
    }
    assert timeline_block_is_administrative_only(block) is False
