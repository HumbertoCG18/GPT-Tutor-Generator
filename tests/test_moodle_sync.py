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


# --- S2: plano de import do delta (puro; I/O fica no scripts/sync_moodle.py --apply) ---
from src.builder.core.stash_import import StashItem, StashScanResult  # noqa: E402
from src.builder.sources.moodle_sync import plan_import  # noqa: E402

FR_LINKS = json.loads((Path(__file__).parent.parent / "docs/reports/_harness-2026-09-03/pulls/FR/links.json").read_text(encoding="utf-8"))
NOMES = {"[10.08] - Wireshark/Lab 1 - Wireshark.pdf": "Laboratório 1 - Wireshark", "[31.08] - HTTP/Lab 4 - HTTP.pdf": "Laboratório 04 - HTTP(S)"}


def _scan(extra=()):
    items = [StashItem(r"C:\stash\lr\[10.08] - Wireshark\Lab 1 - Wireshark.pdf", "[10.08] - Wireshark", "pdf", "material-de-aula"),
             StashItem(r"C:\stash\lr\[31.08] - HTTP\Lab 4 - HTTP.pdf", "[31.08] - HTTP", "pdf", "material-de-aula"), *extra]
    return StashScanResult(items=items, skipped=[r"C:\stash\lr\[31.08] - HTTP\extra.htm"])


def test_plan_adds_only_the_new_module_with_its_moodle_label():
    plan = plan_import(sync_diff([_lab1()], LR), LR, _scan(), FR_LINKS, [_lab1()], nomes=NOMES)
    assert [e.source_path for e in plan.add] == [r"C:\stash\lr\[31.08] - HTTP\Lab 4 - HTTP.pdf"]
    assert plan.add[0].source_section == "[31.08] - HTTP" and plan.add[0].moodle_label == "Laboratório 04 - HTTP(S)"
    assert plan.ignorados == ["extra.htm"] and plan.prune == [] and plan.readd == []


def test_plan_turns_reference_links_into_url_entries_and_keeps_review_apart():
    plan = plan_import(sync_diff([_lab1()], LR), LR, _scan(), FR_LINKS, [_lab1()], nomes=NOMES)
    assert sorted(e.title for e in plan.links) == ["Entre a origem e o destino um panorama dos bloqueios na internet brasileira (Apresentação de estudo)", "O Triunfo dos Nerds (Documentário)"]
    assert all(e.file_type == "url" and e.category == "references" and e.source_section == "Sugestão de Conteúdo Online" for e in plan.links)
    assert [r["nome"] for r in plan.review] == ["Piratas do Vale do Silício (Filme)"]


def test_plan_does_not_duplicate_a_link_already_in_the_manifest():
    url = {"id": "o-triunfo-x", "source_path": "https://www.youtube.com/watch?v=XlCaiD5VQRU", "source_section": None, "file_type": "url", "category": "references"}
    plan = plan_import(sync_diff([_lab1(), url], LR), LR, _scan(), FR_LINKS, [_lab1(), url], nomes=NOMES)
    assert [e.source_path for e in plan.links] == ["https://www.youtube.com/watch?v=bO_oUjersHI"]


def test_plan_prunes_or_marks_missing_entries_by_flag():
    ghost = {"id": "lab-9", "source_path": r"C:\stash\lr\[10.08] - Wireshark\Lab 9.pdf", "source_section": "[10.08] - Wireshark", "file_type": "pdf", "category": "material-de-aula", "posting_date": ""}
    diff = sync_diff([_lab1(), ghost], LR)
    assert plan_import(diff, LR, _scan(), [], [_lab1(), ghost], nomes=NOMES).prune == ["lab-9"]
    p = plan_import(diff, LR, _scan(), [], [_lab1(), ghost], nomes=NOMES, prune_removed=False)
    assert p.prune == [] and p.mark == ["lab-9"]


def test_plan_readds_changed_entries_from_their_stash_file():
    diff = sync_diff([_lab1(posting_date="2026-08-01")], LR)
    plan = plan_import(diff, LR, _scan(), [], [_lab1(posting_date="2026-08-01")], nomes=NOMES)
    assert plan.readd == ["lab-1-wireshark"]
    assert sorted(Path(e.source_path).name for e in plan.add) == ["Lab 1 - Wireshark.pdf", "Lab 4 - HTTP.pdf"]


# --- S3: diff de decisoes, marca "mudou, confira", SYNC_REPORT ---
from src.builder.routing.revisar import DUVIDA, MUDOU, OK, revisar_de  # noqa: E402
from src.builder.sources.moodle_sync import decision_diff, mark_sync_changes, render_sync_report, snapshot_decisions  # noqa: E402


def _mat(eid, block, flag=False, unit="unidade-01", sub="", method="janela-1", **extra):
    e = {"id": eid, "category": "material-de-aula", "file_type": "pdf", "source_section": "[10.08] - Wireshark",
         "temporal_block_id": block, "temporal_block_method": method, "temporal_block_flag": flag,
         "computed_unit_slug": unit, "computed_subunit_slug": sub}
    e.update(extra)
    return e


def test_revisar_mudou_only_for_confident_decisions_that_moved():
    assert revisar_de(_mat("a", "u-01", sync_changed="bloco: bloco-02 -> bloco-03 (sync 2026-09-03)")) == MUDOU
    assert revisar_de(_mat("b", "u-01", flag=True, sync_changed="bloco: bloco-02 -> bloco-03 (sync 2026-09-03)")) == DUVIDA
    assert revisar_de(_mat("c", "u-01")) == OK


def test_decision_diff_lists_moved_added_and_removed():
    before = snapshot_decisions([_mat("a", "u-02"), _mat("b", "u-03", sub="s1"), _mat("gone", "u-04")])
    after = [_mat("a", "u-05"), _mat("b", "u-03", sub="s2"), _mat("new", "u-06")]
    d = decision_diff(before, after)
    assert d["added"] == ["new"] and d["removed"] == ["gone"]
    assert [(m["id"], m["campo"], m["antes"], m["depois"]) for m in d["moved"]] == [("a", "bloco", "u-02", "u-05"), ("b", "subunidade", "s1", "s2")]


def test_decision_diff_is_empty_when_nothing_changed():
    ents = [_mat("a", "u-02"), _mat("b", "u-03")]
    d = decision_diff(snapshot_decisions(ents), ents)
    assert d == {"moved": [], "added": [], "removed": []}


def test_mark_sync_changes_sets_and_clears_the_flag_and_recomputes_revisar():
    ents = [_mat("a", "u-05", sync_changed="velho"), _mat("b", "u-03", sync_changed="velho"), _mat("c", "u-01", flag=True)]
    moved = [{"id": "a", "campo": "bloco", "antes": "u-02", "depois": "u-05"}]
    mark_sync_changes(ents, moved, when="2026-09-03")
    assert ents[0]["sync_changed"] == "bloco: u-02 -> u-05 (sync 2026-09-03)" and ents[0]["revisar"] == MUDOU
    assert "sync_changed" not in ents[1] and ents[1]["revisar"] == OK
    assert ents[2]["revisar"] == DUVIDA


def test_sync_report_has_the_four_sections():
    diff = {"novos": [{"section": 7, "module_index": 0, "modname": "resource", "name": "Laboratório 04 - HTTP(S)", "files": ["Lab 4 - HTTP.html"]}],
            "alterados": [], "sumidos": [], "iguais": ["lab-1-wireshark"], "links": [], "fora": []}
    dd = {"moved": [{"id": "lab-1-wireshark", "campo": "bloco", "antes": "bloco-02", "depois": "bloco-03"}], "added": ["lab-4-http"], "removed": []}
    md = render_sync_report(diff, dd, when="2026-09-03", curso="Laboratório de Redes", ignorados=["extra.htm"], review=[{"nome": "Página do Wireshark", "url": "https://www.wireshark.org/"}])
    for s in ("# SYNC 2026-09-03", "Laboratório 04 - HTTP(S)", "lab-4-http", "lab-1-wireshark", "bloco-02 -> bloco-03", "extra.htm", "Página do Wireshark"):
        assert s in md


def test_plan_ignores_dotfiles_in_ignorados():
    scan = _scan(); scan.skipped.append(r"C:\stash\lr\.moodle_nomes.json")
    assert plan_import(sync_diff([_lab1()], LR), LR, scan, [], [_lab1()], nomes=NOMES).ignorados == ["extra.htm"]


# --- entries url (referencias vindas de links.json) casam pelo URL do modulo `url`, nunca viram "sumidas" por engano ---

def _url_entry(url, eid="pagina-do-wireshark-abc123"):
    return {"id": eid, "source_path": url, "file_type": "url", "category": "references", "source_section": "[10.08] - Wireshark"}


def test_url_entry_with_card_is_kept_when_its_link_module_still_exists():
    # FR 03/09: a 2a sync REMOVEU as 2 entries de video criadas na 1a — entries url com card nao casavam modulo nenhum
    d = sync_diff([_lab1(), _url_entry("https://www.wireshark.org/")], LR)
    assert d["sumidos"] == [] and "pagina-do-wireshark-abc123" in d["iguais"]


def test_url_entry_is_missing_only_when_the_link_left_the_moodle():
    d = sync_diff([_lab1(), _url_entry("https://gone.example/", eid="gone-1")], LR)
    assert d["sumidos"] == ["gone-1"]
