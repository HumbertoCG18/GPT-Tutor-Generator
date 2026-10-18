"""Item 7 F4: badge do motor na linha do material — band autoritativa, não conf."""
from src.ui.timeline_dashboard import _entry_label, motor_badge


def test_motor_badge_band_flag_provider():
    e = {"temporal_block_band": "media", "temporal_block_flag": True,
         "temporal_block_provider": "llm"}
    assert motor_badge(e) == "[media ⚑ llm]"


def test_motor_badge_sem_flag():
    e = {"temporal_block_band": "alta", "temporal_block_provider": "labels"}
    assert motor_badge(e) == "[alta labels]"


def test_motor_badge_vazio_sem_motor():
    assert motor_badge({}) == ""
    assert motor_badge({"computed_block_band": "alta"}) == ""  # conf/computed NÃO vaza


def test_entry_label_anexa_badge():
    e = {"title": "inducao.pdf", "temporal_block_band": "media",
         "temporal_block_provider": "llm"}
    label = _entry_label(e)
    assert "inducao.pdf" in label and "[media llm]" in label
