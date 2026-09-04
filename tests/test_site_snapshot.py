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


# --- S6d: snapshot segue so a SUBARVORE da pagina e grava o bundle (pagina + imagens) no stash ---

def test_in_subtree_same_dir_and_subdirs_only():
    from scripts.site_snapshot import in_subtree
    base = "https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm"
    assert in_subtree("https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/bezier.htm", base)
    assert in_subtree("https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Extra/x.html", base)
    assert not in_subtree("https://www.inf.pucrs.br/pinho/CG/Aulas/Vis3d/Vis3d.htm", base)      # irmao
    assert not in_subtree("https://www.inf.pucrs.br/pinho/CG/Aulas/", base)                     # pai (indice Aulas/)
    assert not in_subtree("https://www.inf.pucrs.br/pinho/CGII/Exercicios/x.html", base)        # outra cadeira
    assert not in_subtree("https://www.inf.pucrs.br/~manssour/CG/x.html", base)                 # outro professor
    assert not in_subtree("https://outro.host/pinho/CG/Aulas/Curvas/x.htm", base)
    hub = "https://www.inf.pucrs.br/pinho/CGII/Exercicios/RemocaoDeRuido/"
    assert in_subtree("https://www.inf.pucrs.br/pinho/CGII/Exercicios/RemocaoDeRuido/index.html", hub)


def test_save_material_copies_page_bundle_without_orig(tmp_path):
    # Mirror real: raw/site/<host>/pinho/CG/Aulas/Curvas/{Curvas.htm, Curvas.htm.orig, Curvas.fld/imageNNN, Image1.gif}
    # + imagem do mesmo host fora do dir da pagina (Vis3d: ~manssour/CG/projecoes/perspectiva2.png) + imagem de outro host.
    from scripts.site_snapshot import Snapshot
    piloto = Path(__file__).parent.parent / "docs/reports/_harness-2026-09-03/piloto-curvas"
    root = tmp_path / "pull"
    page_dir = root / "raw/site/www.inf.pucrs.br/pinho/CG/Aulas/Curvas"
    (page_dir / "Curvas.fld").mkdir(parents=True)
    html = (piloto / "Curvas.htm").read_bytes()
    (page_dir / "Curvas.htm").write_bytes(html)
    (page_dir / "Curvas.htm.orig").write_bytes(html)
    (page_dir / "Curvas.fld" / "image003.gif").write_bytes((piloto / "images/image003.gif").read_bytes())
    (page_dir / "Image1.gif").write_bytes((piloto / "images/Image1.gif").read_bytes())
    ext = root / "raw/site/www.inf.pucrs.br/~manssour/CG/projecoes"
    ext.mkdir(parents=True)
    (ext / "perspectiva2.png").write_bytes((piloto / "images/image004.png").read_bytes())
    url = "https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm"
    rec = {"url": url, "local": "raw/site/www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm", "card": "7 - Curvas Paramétricas",
           "title": "Computação Gráfica - Curvas Paramétricas",
           "images": ["https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.fld/image003.gif",
                      "https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Image1.gif",
                      "https://www.inf.pucrs.br/%7Emanssour/CG/projecoes/perspectiva2.png",
                      "https://www.cs.uic.edu/~jbell/diagrams/sphere.gif"]}
    snap = Snapshot(root, depth=1, pdf=False)
    dest = snap.save_material(rec, root / "stash")
    bundle = root / "stash" / "7 - Curvas Paramétricas" / "Curvas"
    assert dest == bundle / "Curvas.htm" and dest.read_bytes() == html
    assert (bundle / "Curvas.fld" / "image003.gif").is_file() and (bundle / "Image1.gif").is_file()
    assert (bundle / "perspectiva2.png").is_file()            # mesmo host, fora do dir: entra pelo basename
    assert not (bundle / "sphere.gif").exists()                # outro host: nao capturada no build
    assert not list(bundle.rglob("*.orig"))
