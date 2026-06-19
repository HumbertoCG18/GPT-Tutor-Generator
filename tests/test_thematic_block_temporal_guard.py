from datetime import datetime

from src.builder.timeline.index import (
    _rows_belong_to_same_thematic_block,
    MAX_THEMATIC_BLOCK_SPAN_DAYS,
)


def _row(content: str, date_iso: str):
    return {
        "content": content,
        "kind": "class",
        "date_text": date_iso,
        "date_dt": datetime.strptime(date_iso, "%Y-%m-%d") if date_iso else None,
    }


def test_same_theme_close_dates_merges():
    # mesmo tema, datas próximas (2 dias) → funde como antes
    r0 = _row("logica de hoare parte um", "2026-04-27")
    r1 = _row("logica de hoare parte dois", "2026-04-29")
    assert _rows_belong_to_same_thematic_block(r0, r1, current_rows=[r0]) is True


def test_same_theme_span_over_cap_does_not_merge():
    # mesmo tema, mas span do bloco > cap → NÃO funde (quebra o over-merge)
    r0 = _row("logica de hoare parte um", "2026-04-27")
    r_far = _row("logica de hoare revisitada", "2026-06-08")  # 42 dias depois
    assert (r_far["date_dt"] - r0["date_dt"]).days > MAX_THEMATIC_BLOCK_SPAN_DAYS
    assert _rows_belong_to_same_thematic_block(r0, r_far, current_rows=[r0]) is False


def test_span_measured_from_block_start_not_previous_row():
    # span é medido do INÍCIO do bloco (current_rows[0]) até a linha atual
    r0 = _row("logica de hoare um", "2026-04-27")
    r1 = _row("logica de hoare dois", "2026-05-04")   # 7 dias do início
    r2 = _row("logica de hoare tres", "2026-06-08")   # 42 dias do início → corta
    assert _rows_belong_to_same_thematic_block(r0, r2, current_rows=[r0, r1]) is False


def test_missing_date_skips_temporal_guard():
    # sem date_dt nos dois lados → guarda não aplica; funde por overlap como antes
    r0 = {"content": "logica de hoare parte um", "kind": "class", "date_text": "", "date_dt": None}
    r1 = {"content": "logica de hoare parte dois", "kind": "class", "date_text": "", "date_dt": None}
    assert _rows_belong_to_same_thematic_block(r0, r1, current_rows=[r0]) is True
