"""HTML salvo no stash como MATERIAL (SYNC S6b, 2026-09-03): `core/html_material.process_html`.

Fixture real (piloto Curvas, 03/09): `docs/reports/_harness-2026-09-03/piloto-curvas/` = `Curvas.htm` (pagina do
professor de CG, www.inf.pucrs.br/pinho/CG/Aulas/Curvas/Curvas.htm), 27 imagens em `images/` (24 referenciadas +
3 logos em <td>) e `datalab_cache.json` = resposta REAL do Datalab (convert_document_to_markdown por imagem):
12 formulas em $$, 9 legendas `![caption](hash)` em ingles, 3 vazias. Os clientes Datalab/Gemini dos testes sao
FALSOS e devolvem esse gold. No mirror real a pagina fica em `Aulas/Curvas/Curvas.htm` com `Curvas.fld/imageNNN`
e irmas; `_stage_curvas` monta esse layout a partir dos `src` do HTML. Paginas sinteticas copiam o contrato do
Moodle (`<meta charset="utf-8"><div class="no-overflow">...`, imagens em `data:image/png;base64`)."""
import base64
import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest

from src.builder import engine as engine_module
from src.builder.core import html_material
from src.builder.core.html_material import process_html
from src.models.core import FileEntry

pytest.importorskip("bs4")

PILOTO = Path(__file__).parent.parent / "docs/reports/_harness-2026-09-03/piloto-curvas"
GOLD = json.loads((PILOTO / "datalab_cache.json").read_text(encoding="utf-8"))
FORMULAS = {"EquacaoHermite.png", "Image1.gif", "Image2.gif", "Image3.gif", "Image4.gif", "Image5.gif",
            "Image6.gif", "Image7.gif", "Image8.gif", "Image9.gif", "Image11.gif", "image007.png"}
LEGENDAS = {"DuasBz3Ptos.gif", "bezier3pontos.gif", "bezier4pontos.gif", "image001.gif", "image002.gif",
            "image004.png", "image005.png", "image006.png", "reta.gif"}
VAZIAS = {"image003.gif", "interpola.gif", "vetor.gif"}
SRC_RE = re.compile(r'<img[^>]*?src\s*=\s*"?([^"\s>]+)', re.I)
PNG_1x1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def _stage_curvas(tmp_path):
    card = tmp_path / "stash" / "7 - Curvas Parametricas"
    card.mkdir(parents=True)
    html = PILOTO / "Curvas.htm"
    shutil.copy(html, card / "Curvas.htm")
    for src in SRC_RE.findall(html.read_text(encoding="utf-8")):
        if src.startswith("http"):
            continue
        dest = card / src
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PILOTO / "images" / Path(src).name, dest)
    return card / "Curvas.htm"


def _page(tmp_path, body, name="Pagina.htm"):
    card = tmp_path / "stash" / "Card"
    card.mkdir(parents=True, exist_ok=True)
    p = card / name
    p.write_text('<meta charset="utf-8"><div class="no-overflow">' + body + "</div>", encoding="utf-8")
    return p


class FakeDatalab:
    def __init__(self, table=None):
        self.table = GOLD if table is None else table
        self.calls = []

    def __call__(self, path):
        self.calls.append(path.name)
        rec = self.table[path.name]
        if "erro" in rec:
            raise RuntimeError(rec["erro"])
        return rec["markdown"]


class FakeGemini:
    def __init__(self, reply=None):
        self.calls, self.reply = [], reply

    def __call__(self, prompt, image_path=None):
        self.calls.append((prompt, image_path))
        if self.reply is not None:
            return self.reply
        if image_path is not None:
            return f"descricao pt de {image_path.name}"
        return "legenda pt: " + prompt.rsplit(":", 1)[-1].strip()[:30]


def _builder(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    return engine_module.RepoBuilder(repo, {}, [], {})


def _entry(html_path):
    return FileEntry(source_path=str(html_path), file_type="html", category="outros",
                     title=html_path.stem, source_section=html_path.parent.name)


def _run(tmp_path, html_path, datalab=None, gemini=None):
    builder = _builder(tmp_path)
    entry = _entry(html_path)
    raw = builder.root_dir / "raw" / "html" / f"{entry.id()}{html_path.suffix.lower()}"
    raw.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(html_path, raw)
    item = process_html(builder, entry, raw,
                        datalab_image_fn=datalab if datalab is not None else FakeDatalab(),
                        gemini_text_fn=gemini if gemini is not None else FakeGemini())
    return builder, item, (builder.root_dir / item["base_markdown"]).read_text(encoding="utf-8")


def test_curvas_end_to_end_formulas_figuras_imagens_e_review(tmp_path):
    datalab, gemini = FakeDatalab(), FakeGemini()
    builder, item, md = _run(tmp_path, _stage_curvas(tmp_path), datalab, gemini)
    repo = builder.root_dir
    assert item["base_markdown"] == "staging/markdown-auto/html/curvas.md"
    assert item["base_backend"] == "html_converter"
    # 12 formulas: LaTeX do Datalab inteiro (fiel, inclusive o erro do professor em Image2.gif) + fonte
    fontes = re.findall(r"<sub>fonte: \[([^\]]+)\]\(content/images/curvas-([^)]+)\)</sub>", md)
    assert {f[0] for f in fontes} == FORMULAS and all(f[0] == f[1] for f in fontes)
    for name in FORMULAS:
        assert GOLD[name]["markdown"].strip() in md
    # 9 legendas traduzidas + 3 vazias descritas
    figuras = re.findall(r"!\[Figura: ([^\]]+)\]\(content/images/curvas-([^)]+)\)", md)
    assert sorted(n for _, n in figuras) == sorted(LEGENDAS | VAZIAS)
    assert "não capturada" not in md and "[if gte vml" not in md and "Capturado em" not in md
    assert "\n\n\n" not in md   # bloco de formula no lugar da ref nao deixa linhas em branco a mais
    # imagens copiadas com o prefixo do entry (unprocess limpa `content/images/<id>-*`)
    copied = sorted(p.name for p in (repo / "content" / "images").iterdir())
    assert copied == sorted(f"curvas-{n}" for n in FORMULAS | LEGENDAS | VAZIAS)
    # toda formula transcrita vai para manual-review/formulas/ (S6c)
    reviews = {p.name for p in (repo / "manual-review" / "formulas").iterdir()}
    assert reviews == {f"curvas-{Path(n).stem}.md" for n in FORMULAS}
    rev = (repo / "manual-review" / "formulas" / "curvas-Image2.md").read_text(encoding="utf-8")
    assert "conferir com o professor" in rev
    assert "content/images/curvas-Image2.gif" in rev
    assert GOLD["Image2.gif"]["markdown"].strip() in rev
    # gasto: 24 Datalab; Gemini = 9 traducoes (so texto) + 3 descricoes (com imagem)
    assert len(datalab.calls) == 24
    assert sum(1 for _, img in gemini.calls if img is None) == 9
    assert sum(1 for _, img in gemini.calls if img is not None) == 3
    assert item["html_images"] == {"total": 24, "formulas": 12, "figuras": 9, "descritas": 3,
                                   "nao_capturadas": 0, "datalab_calls": 24}


def test_second_run_hits_cache_and_is_byte_identical(tmp_path):
    html = _stage_curvas(tmp_path)
    b1, _, md1 = _run(tmp_path, html)
    cache = json.loads((b1.root_dir / "course" / ".image_transcriptions.json").read_text(encoding="utf-8"))
    assert len(cache) == 24
    d2, g2 = FakeDatalab(), FakeGemini()
    _, _, md2 = _run(tmp_path, html, d2, g2)
    assert d2.calls == [] and g2.calls == []
    assert md2 == md1


def test_data_uri_image_is_decoded_to_file_and_sent_to_datalab(tmp_path):
    raw_png = base64.b64decode(PNG_1x1)
    h = hashlib.md5(raw_png).hexdigest()[:8]
    p = _page(tmp_path, f'<p>Questao 1</p><p><img src="data:image/png;base64,{PNG_1x1}"></p>')
    datalab = FakeDatalab({f"pagina-data-{h}.png": {"markdown": "$$x = 1$$"}})
    b, item, md = _run(tmp_path, p, datalab)
    copied = b.root_dir / "content" / "images" / f"pagina-data-{h}.png"
    assert copied.read_bytes() == raw_png
    assert "$$x = 1$$" in md
    assert f"<sub>fonte: [data-{h}.png](content/images/pagina-data-{h}.png)</sub>" in md
    assert "base64" not in md
    assert datalab.calls == [f"pagina-data-{h}.png"]


def test_external_and_missing_images_are_marked_not_captured_without_datalab(tmp_path):
    p = _page(tmp_path, '<p><img src="https://www.cs.uic.edu/~jbell/diagrams/sphere.gif"></p><p><img src="sumida.gif"></p>')
    datalab = FakeDatalab({})
    _, item, md = _run(tmp_path, p, datalab)
    assert "![sphere.gif — não capturada](https://www.cs.uic.edu/~jbell/diagrams/sphere.gif)" in md
    assert "![sumida.gif — não capturada](sumida.gif)" in md
    assert datalab.calls == []
    assert item["html_images"]["nao_capturadas"] == 2


def test_datalab_cap_per_build_stops_new_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(html_material, "HTML_IMAGE_DATALAB_CAP", 1)
    p = _page(tmp_path, '<p><img src="a.gif"></p><p><img src="b.gif"></p>')
    shutil.copy(PILOTO / "images" / "Image1.gif", p.parent / "a.gif")
    shutil.copy(PILOTO / "images" / "Image2.gif", p.parent / "b.gif")
    datalab = FakeDatalab({"a.gif": {"markdown": "$$a$$"}, "b.gif": {"markdown": "$$b$$"}})
    _, item, md = _run(tmp_path, p, datalab)
    assert datalab.calls == ["a.gif"]
    assert "$$a$$" in md
    assert "![b.gif — não capturada (cap 1)](content/images/pagina-b.gif)" in md


def test_datalab_failure_is_not_cached_and_marked_not_captured(tmp_path):
    p = _page(tmp_path, '<p><img src="f.gif"></p>')
    shutil.copy(PILOTO / "images" / "Image1.gif", p.parent / "f.gif")
    b, _, md = _run(tmp_path, p, FakeDatalab({"f.gif": {"erro": "HTTPError: 500"}}))
    assert "![f.gif — não capturada](content/images/pagina-f.gif)" in md
    cache_path = b.root_dir / "course" / ".image_transcriptions.json"
    assert not cache_path.exists() or json.loads(cache_path.read_text(encoding="utf-8")) == {}
    d2 = FakeDatalab({"f.gif": {"markdown": "$$f$$"}})
    _, _, md2 = _run(tmp_path, p, d2)
    assert d2.calls == ["f.gif"] and "$$f$$" in md2


def test_without_gemini_legend_stays_english_and_empty_image_is_not_captured(tmp_path):
    p = _page(tmp_path, '<p><img src="bezier4pontos.gif"></p><p><img src="vetor.gif"></p>')
    for n in ("bezier4pontos.gif", "vetor.gif"):
        shutil.copy(PILOTO / "images" / n, p.parent / n)
    _, item, md = _run(tmp_path, p, FakeDatalab(), FakeGemini(reply=""))
    en = " ".join(re.search(r"!\[([^\]]*)\]", GOLD["bezier4pontos.gif"]["markdown"]).group(1).split())
    assert f"![Figura: {en}](content/images/pagina-bezier4pontos.gif)" in md
    assert "![vetor.gif — não capturada](content/images/pagina-vetor.gif)" in md
    assert item["html_images"] == {"total": 2, "formulas": 0, "figuras": 1, "descritas": 0,
                                   "nao_capturadas": 1, "datalab_calls": 2}


def test_process_entry_copies_html_to_raw_and_delegates(tmp_path, monkeypatch):
    html = _stage_curvas(tmp_path)
    builder = _builder(tmp_path)
    seen = {}

    def fake_process_html(self, entry, raw_target):
        seen["raw"] = raw_target
        return {"base_markdown": "staging/markdown-auto/html/curvas.md"}

    monkeypatch.setattr(engine_module.RepoBuilder, "_process_html", fake_process_html)
    item = builder._process_entry(_entry(html))
    assert item["raw_target"] == "raw/html/curvas.htm"
    assert (builder.root_dir / "raw" / "html" / "curvas.htm").exists()
    assert seen["raw"] == builder.root_dir / "raw" / "html" / "curvas.htm"


def test_resolve_content_images_keeps_formula_images_linked_from_fonte(tmp_path):
    # `resolve_content_images` (build/regeneracao) so via `![...]`: a fonte da formula e link `[x](content/images/...)`
    # e no gate do CG (03/09) as 12 GIFs de formula foram apagadas como "stale" (as 12 figuras sobreviveram).
    builder, _, _ = _run(tmp_path, _stage_curvas(tmp_path))
    builder._resolve_content_images()
    copied = sorted(p.name for p in (builder.root_dir / "content" / "images").iterdir())
    assert copied == sorted(f"curvas-{n}" for n in FORMULAS | LEGENDAS | VAZIAS)


def test_absolute_same_host_image_resolves_by_basename_in_page_dir(tmp_path):
    # ExercicioDuasCores.html (CG) escreve imagens do PROPRIO diretorio como URL absoluta (~pinho/.../x.gif);
    # o bundle do snapshot (S6d) copia pelo basename e aqui a URL absoluta resolve para o arquivo ao lado da pagina.
    p = _page(tmp_path, '<p><img src="https://www.inf.pucrs.br/%7Epinho/CG/Aulas/Img/bezier4pontos.gif"></p>')
    shutil.copy(PILOTO / "images" / "bezier4pontos.gif", p.parent / "bezier4pontos.gif")
    datalab = FakeDatalab()
    _, item, md = _run(tmp_path, p, datalab)
    assert datalab.calls == ["bezier4pontos.gif"]
    assert "![Figura: " in md and "não capturada" not in md
    assert (tmp_path / "repo" / "content" / "images" / "pagina-bezier4pontos.gif").is_file()
