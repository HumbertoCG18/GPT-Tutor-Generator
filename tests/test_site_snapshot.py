"""Passo 1 do holdout CG: deteccao de encoding e normalizacao do snapshot (bytes no formato real do site)."""
from pathlib import Path

from scripts.site_snapshot import detect_encoding, local_path, normalize_html


def test_bom_utf16_vence_header_e_meta():
    raw = "\ufeff<html><head><meta http-equiv=Content-Type content=\"text/html; charset=unicode\"></head><body>Cronograma</body></html>".encode("utf-16")
    assert detect_encoding(raw, "utf-8") == "utf-16"
    assert "Cronograma" in raw.decode(detect_encoding(raw, None))


def test_meta_charset_vence_header_e_word_unicode_vira_utf16():
    assert detect_encoding(b'<html><head><meta charset="iso-8859-1"></head>', "utf-8") == "iso-8859-1"
    assert detect_encoding(b'<meta http-equiv=Content-Type content="text/html; charset=unicode">', None) == "utf-16"


def test_sem_bom_sem_meta_usa_header_depois_cp1252():
    assert detect_encoding(b"<html><body>x</body></html>", "utf-8") == "utf-8"
    assert detect_encoding(b"<html><body>x</body></html>", None) == "cp1252"
    assert detect_encoding(b'<meta charset="nao-existe">', None) == "cp1252"


def test_normalize_html_deixa_um_unico_meta_utf8():
    out = normalize_html('<html><head><meta http-equiv=Content-Type content="text/html; charset=windows-1252"><title>t</title></head><body>é</body></html>')
    assert out.count("charset") == 1 and '<meta charset="utf-8">' in out and "windows-1252" not in out
    assert normalize_html("<p>sem head</p>").startswith('<meta charset="utf-8">')


def test_local_path_espelha_host_e_caminho(tmp_path: Path):
    assert local_path(tmp_path, "https://www.inf.pucrs.br/pinho/CG/") == tmp_path / "www.inf.pucrs.br" / "pinho" / "CG" / "index.html"
    assert local_path(tmp_path, "https://www.inf.pucrs.br/pinho/CG/Aulas/GeomComp/Dominancia/Domina.html").name == "Domina.html"
