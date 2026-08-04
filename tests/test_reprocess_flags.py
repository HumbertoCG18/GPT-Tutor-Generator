import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import reprocess_assignments as ra  # noqa: E402


def test_apply_flags_marca_true_e_preserva_options():
    opts = {"image_format": "png"}
    ra._apply_flags(opts, ["use_anchor_engine", "use_llm_voter"])
    assert opts["use_anchor_engine"] is True
    assert opts["use_llm_voter"] is True
    assert opts["image_format"] == "png"


def test_apply_flags_vazio_nao_muda_nada():
    opts = {"a": 1}
    ra._apply_flags(opts, [])
    assert opts == {"a": 1}


def test_parse_argv_com_flags():
    flags, pats = ra._parse_argv(["--flags", "use_anchor_engine,use_llm_voter", "C:/x"])
    assert flags == ["use_anchor_engine", "use_llm_voter"]
    assert pats == ["C:/x"]


def test_parse_argv_sem_flags_e_retrocompativel():
    flags, pats = ra._parse_argv(["C:/x", "C:/y"])
    assert flags == []
    assert pats == ["C:/x", "C:/y"]
