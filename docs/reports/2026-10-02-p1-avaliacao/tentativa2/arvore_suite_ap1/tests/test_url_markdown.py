"""Conversor HTML -> markdown (`text/url_markdown`) usado para HTML como MATERIAL (SYNC S6a, 2026-09-03).

Fixture real: `docs/reports/_harness-2026-09-03/piloto-curvas/Curvas.htm` = pagina do professor de CG
(www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm, Word HTML com comentarios condicionais VML e
`<img src>` sem aspas), capturada em 03/09/2026: 24 imagens locais referenciadas + 3 logos em `<td>`.
Os HTMLs sinteticos abaixo copiam esse contrato (Word: `<!--[if gte vml 1]>...<![endif]-->` seguido de
`<![if !vml]><img ...><![endif]>`)."""
import re
from pathlib import Path

import pytest

from src.builder.text.url_markdown import html_to_structured_markdown, truncate_markdown_blocks

pytest.importorskip("bs4")

CURVAS = Path(__file__).parent.parent / "docs/reports/_harness-2026-09-03/piloto-curvas/Curvas.htm"
CURVAS_URL = "https://www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm"


def _collapse(s):
    return " ".join(str(s).split())


def _convert(html, url=CURVAS_URL, title="Curvas", max_chars=None):
    return html_to_structured_markdown(
        html, url, title, collapse_ws=_collapse,
        truncate_markdown_blocks=lambda b: truncate_markdown_blocks(b, max_chars=max_chars),
    )


def test_truncate_without_ceiling_keeps_every_block():
    blocks = ["x" * 6000] * 3   # 18 000 chars > teto padrao (15 000) das entries url
    assert "> Conteúdo truncado." in truncate_markdown_blocks(blocks)
    assert truncate_markdown_blocks(blocks, max_chars=None) == "\n\n".join(blocks)


def test_word_conditional_comments_do_not_leak_into_markdown():
    html = (
        "<html><body><article><p>Antes "
        '<!--[if gte vml 1]><v:shape id="x"><v:imagedata src="a.gif"/></v:shape><![endif]-->'
        "<![if !vml]><img src=Image2.gif><![endif]> depois.</p></article></body></html>"
    )
    md = _convert(html)
    assert "Antes ![](Image2.gif) depois." in md
    for leak in ("[if gte vml", "v:shape", "if !vml", "endif"):
        assert leak not in md


def test_real_curvas_page_converts_whole_with_24_image_refs_and_no_vml():
    md = _convert(CURVAS.read_text(encoding="utf-8"), url="")
    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
    assert len(refs) == 24
    assert "Curvas.fld/image003.gif" in refs and "Image2.gif" in refs
    assert not any("Logotipos" in r for r in refs)
    assert "[if gte vml" not in md and "endif" not in md
    # Pagina inteira: chega ao ultimo paragrafo e o teto das entries url nao a corta
    # (7 917 chars limpos em 03/09; os 11 179 do piloto incluiam ~3 200 de VML vazado).
    assert md.rstrip().endswith("**FIM.**")
    assert md == _convert(CURVAS.read_text(encoding="utf-8"), url="", max_chars=15000)


def test_local_document_has_no_web_header_lines():
    html = "<html><head><title>Curvas Parametricas</title></head><body><p>texto do professor</p></body></html>"
    md = _convert(html, url="", title="")
    assert md.startswith("# Curvas Parametricas\n")
    for line in ("- URL:", "- Domínio:", "- Capturado em:"):
        assert line not in md
    assert "texto do professor" in md


def test_url_document_keeps_web_header_lines():
    md = _convert("<html><body><p>texto</p></body></html>", url="https://example.com/a", title="A")
    assert "- URL: [https://example.com/a](https://example.com/a)" in md
    assert "- Domínio: `example.com`" in md
    assert "- Capturado em:" in md
