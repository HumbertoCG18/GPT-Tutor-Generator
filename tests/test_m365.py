from src.builder.sources.m365 import (
    parse_onedrive_path, subfolder_for, select_for_subject,
)

_BASE = "https://brpucrs-my.sharepoint.com/personal/10070245_pucrs_br/Documents/Documentos"

def test_parse_onedrive_path_segments():
    segs = parse_onedrive_path(f"{_BASE}/metodosformais/dafny/hoare.zip")
    assert segs[-3:] == ["metodosformais", "dafny", "hoare.zip"]

def test_subfolder_for_uses_immediate_subfolder():
    assert subfolder_for(f"{_BASE}/metodosformais/dafny/hoare.zip", "metodosformais") == "dafny"
    assert subfolder_for(f"{_BASE}/metodosformais/logica_programas/Hoare.pdf", "metodosformais") == "logica_programas"

def test_subfolder_for_root_file_is_default():
    assert subfolder_for(f"{_BASE}/metodosformais/plano.pdf", "metodosformais") == "_geral"

def test_select_for_subject_filters_by_substring():
    items = [
        {"web_url": f"{_BASE}/metodosformais/dafny/a.pdf"},
        {"web_url": f"{_BASE}/engenhariadesoftware2/b.pdf"},
        {"web_url": "https://outlook.office.com/owa/?x=AttachmentId"},
    ]
    out = select_for_subject(items, "metodosformais")
    assert len(out) == 1 and "dafny" in out[0]["web_url"]

def test_select_for_subject_empty_filter_returns_nothing():
    assert select_for_subject([{"web_url": "x"}], "") == []

from src.builder.sources.m365 import match_card

_SECTIONS = ["Introdução a Métodos Formais", "Provas por Indução",
             "Verificação de Programas", "Plano de Ensino"]

def test_match_card_matches_by_normalized_tokens():
    assert match_card("introducao", _SECTIONS) == ("Introdução a Métodos Formais", True)
    assert match_card("correcao_provasinducao", _SECTIONS)[1] is True
    assert match_card("logica_programas", _SECTIONS) == ("Verificação de Programas", True)

def test_match_card_falls_back_to_new_card_when_no_match():
    card, matched = match_card("dafny", _SECTIONS)
    assert matched is False and card == "dafny"
