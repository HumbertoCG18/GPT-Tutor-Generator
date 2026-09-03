"""Campanha SYNC, S1: diff estrutural do contents.json (API) contra o manifest — read-only.

Fixture LR = secoes 4 "[10/08] - Wireshark" e 7 "[31/08] - HTTP" do pull real de 03/09 (`_harness-2026-09-03/pulls/LR/`),
com `timemodified` real dos arquivos. Entries copiam o contrato do manifest do LR (id/source_path/source_section/posting_date).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from src.builder.sources.moodle_sync import sync_diff

FX = json.loads((Path(__file__).parent / "fixtures" / "moodle" / "contents_excerpt.json").read_text(encoding="utf-8"))
LR = FX["LR"]
_LAB1_TM = next(c["timemodified"] for s in LR if s["section"] == 4 for m in s["modules"] for c in m.get("contents", []) if c.get("type") == "file")
_LAB1_DATE = datetime.fromtimestamp(_LAB1_TM, tz=timezone.utc).strftime("%Y-%m-%d")


def _lab1(posting_date=_LAB1_DATE):
    return {"id": "lab-1-wireshark", "source_path": r"C:\stash\lr\[10.08] - Wireshark\Lab 1 - Wireshark.pdf",
            "source_section": "[10.08] - Wireshark", "moodle_label": None, "file_type": "pdf", "category": "material-de-aula",
            "posting_date": posting_date}


def test_module_without_entry_is_new_and_url_modules_are_links_not_materials():
    d = sync_diff([_lab1()], LR)
    assert [n["name"] for n in d["novos"]] == ["Laboratório 04 - HTTP(S)"]
    assert d["novos"][0]["section"] == 7 and d["novos"][0]["files"] == ["Lab 4 - HTTP.html"]
    assert [l["name"] for l in d["links"]] == ["Página do Wireshark"]
    assert d["sumidos"] == [] and d["alterados"] == [] and d["iguais"] == ["lab-1-wireshark"]


def test_entry_matched_by_stem_across_extension_is_unchanged_when_dates_agree():
    assert sync_diff([_lab1()], LR)["iguais"] == ["lab-1-wireshark"]


def test_file_modified_after_posting_date_is_changed():
    d = sync_diff([_lab1(posting_date="2026-08-01")], LR)
    assert [a["id"] for a in d["alterados"]] == ["lab-1-wireshark"]
    assert d["alterados"][0]["timemodified_iso"] == _LAB1_DATE and d["iguais"] == []


def test_entry_without_posting_date_cannot_be_judged_and_stays_unchanged():
    assert sync_diff([_lab1(posting_date="")], LR)["iguais"] == ["lab-1-wireshark"]


def test_entry_with_card_and_no_module_is_missing():
    ghost = {"id": "lab-9", "source_path": r"C:\stash\lr\[10.08] - Wireshark\Lab 9.pdf", "source_section": "[10.08] - Wireshark",
             "moodle_label": None, "file_type": "pdf", "category": "material-de-aula", "posting_date": ""}
    d = sync_diff([_lab1(), ghost], LR)
    assert d["sumidos"] == ["lab-9"] and d["iguais"] == ["lab-1-wireshark"]


def test_entries_without_card_are_out_of_scope():
    url = {"id": "video-abc123", "source_path": "https://youtu.be/x", "source_section": None, "file_type": "url", "category": "references"}
    d = sync_diff([_lab1(), url], LR)
    assert d["sumidos"] == [] and d["fora"] == ["video-abc123"]
