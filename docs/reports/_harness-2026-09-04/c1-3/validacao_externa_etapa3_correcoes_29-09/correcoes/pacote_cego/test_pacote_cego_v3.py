"""Testes das correções da etapa 3 (pacote-cego-3), só com fixtures sintéticas. Reproduzem os casos da revisão."""
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gera_pacote_cego as G  # noqa: E402
from test_pacote_cego import carrega, escreve, fixture, pdf_valido, regrava_manifesto  # noqa: E402


def zip_bytes(membros, cifrado=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, dados in membros.items():
            z.writestr(nome, dados)
    b = buf.getvalue()
    if cifrado:   # zipfile não grava cifrado: liga o bit 0 do flag no cabeçalho local e no diretório central
        for assinatura, pos in ((b"PK", 6), (b"PK", 8)):
            i = b.index(assinatura) + pos
            b = b[:i] + bytes([b[i] | 1]) + b[i + 1:]
    return b


DOCX_OK = {"[Content_Types].xml": "<Types/>", "_rels/.rels": "<Relationships/>", "word/media/image1.png": b"\x89PNG img",
           "word/document.xml": "<w:document><w:t>Escalonamento de processos</w:t></w:document>",
           "docProps/core.xml": "<cp:coreProperties/>"}   # v4: fonte embutida é binário opaco (recusa no teste v4)


# ---------------------------------------------------------------- (a) plano passa pela política de cegamento
@pytest.mark.parametrize("arquivo, dados, motivo", [
    ("plano_texto", "# Plano\n\n## Nº DA UNIDADE: 01\nCONTEÚDO: X\ncomputed_unit_slug: unidade-01\n", "motor"),
    ("plano_texto", "# Plano\nMOODLE_TOKEN=" + "ab12" * 8 + "\n", "credencial"),
    ("plano_arquivo", json.dumps({"computed_block_id": "bloco-03"}), "assinatura"),   # saída renomeada para .pdf
], ids=["texto-motor", "texto-credencial", "arquivo-renomeado"])
def test_plano_com_predicao_ou_segredo_nao_gera_pacote(tmp_path, arquivo, dados, motivo):
    fonte = fixture(tmp_path)
    escreve(Path(fonte[arquivo]), dados)
    with pytest.raises(G.PlanoRecusado, match=motivo):
        G.monta(fonte, tmp_path / "pacote")
    assert not (tmp_path / "pacote").exists()


def test_auditoria_verifica_o_plano_entregue(tmp_path):
    fonte = fixture(tmp_path)
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    escreve(p / "plano/plano_texto.md", "Unidade 1\nwinner_score=3.2\n")
    regrava_manifesto(p)
    assert any(x.startswith("plano/plano_texto.md: texto com assinatura") for x in G.audita(fonte, p))


# ---------------------------------------------------------------- (b) política de membros de contêineres
CASOS_MEMBROS = [
    ("a.zip", zip_bytes({"aula.pdf": pdf_valido("ok"), "notas/lista.txt": "Exercícios"}), None),
    ("a.zip", zip_bytes({"anotacoes.txt": "aula1 -> computed_unit_slug: u01"}), "motor"),
    ("a.zip", zip_bytes({"proj/.env": "X=1"}), "configuração"),
    ("a.zip", zip_bytes({"../fora.txt": "x"}), "inseguro"),
    ("a.zip", zip_bytes({"C:/fora.txt": "x"}), "inseguro"),
    ("a.zip", zip_bytes({"ferramenta.exe": b"MZ"}), "executável"),
    ("a.zip", zip_bytes({"slides.pdf": json.dumps({"computed_block_id": "x"})}), "assinatura"),
    ("a.zip", zip_bytes({"main.go": "package main"}), "allowlist"),
    ("a.zip", zip_bytes({"aula.pdf": b"%PDF-1.4 ok"}, cifrado=True), "cifrado"),
    ("a.zip", zip_bytes({"zeros.txt": b"\x00" * 5_000_000}), "bomba"),
    ("a.zip", zip_bytes({"in.zip": zip_bytes({"x.md": "subunit_match=1"})}), "motor"),
    ("a.zip", zip_bytes({"in.zip": zip_bytes({"in2.zip": zip_bytes({"x.txt": "ok"})})}), "profundidade"),
    ("a.docx", zip_bytes(DOCX_OK), None),
    ("a.docx", zip_bytes({**DOCX_OK, "word/document.xml":   # v4: XML bem formado (duas raízes = "XML ilegível")
                          "<w:document><w:t>computed_</w:t><w:t>unit_slug</w:t></w:document>"}), "motor"),
    ("a.docx", zip_bytes({**DOCX_OK, "word/embeddings/oleObject1.bin": b"\xd0\xcf"}), "opaco"),   # v4: binário opaco
    ("a.docx", zip_bytes({**DOCX_OK, "word/vbaProject.bin": b"\xd0\xcf"}), "macro"),
    ("a.xlsx", zip_bytes({"xl/sharedStrings.xml": "<t>GEMINI_API_KEY=abc</t>"}), "credencial"),
    ("a.pptx", zip_bytes({"ppt/embeddings/p.xlsx": zip_bytes({"xl/x.xml": "<t>winner_score</t>"})}), "motor"),
    ("a.odt", zip_bytes({"mimetype": "application/vnd.oasis.opendocument.text", "content.xml": "<text:p>Aula</text:p>"}), None),
    ("a.pdf", b"%PDF-1.7 << /Type /EmbeddedFile >>", "ilegível"),   # v4: não abre; anexo real em test_pacote_cego_v4
]


@pytest.mark.parametrize("nome, dados, recusa", CASOS_MEMBROS,
                         ids=[f"{i:02d}-{n}-{r or 'aceito'}" for i, (n, _, r) in enumerate(CASOS_MEMBROS)])
def test_politica_de_membros(nome, dados, recusa):
    motivo = G.verifica_material(nome, dados)
    assert (motivo is None) if recusa is None else (motivo and recusa in motivo), motivo


def test_zip_real_com_conteudo_proibido_nao_e_entregue(tmp_path):
    """Caso da revisão: ZIP válido era copiado sem examinar os membros."""
    fonte = fixture(tmp_path, formato="pastas")
    raiz = Path(fonte["moodle_dir"])
    proibido = zip_bytes({"aula.txt": "Conteúdo", "anotacoes.txt": json.dumps({"computed_subunit_slug": "t1"})})
    escreve(raiz / "Unidade 1/material.zip", proibido)
    escreve(raiz / "Unidade 1/codigos.zip", zip_bytes({"exemplo.py": "print('ok')"}))
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    mats = {m["nome_original"]: m for m in carrega(p / "materiais.json")["materiais"]}
    assert mats["material.zip"]["tipo"] == "recusado" and "anotacoes.txt" in mats["material.zip"]["motivo"]
    assert mats["codigos.zip"]["adjudicavel"]
    tudo = b"".join(q.read_bytes() for q in p.rglob("*") if q.is_file())
    assert proibido not in tudo


# ---------------------------------------------------------------- (c) ligação Moodle -> arquivo
def test_candidato_unico_em_outra_secao_nao_e_ligado(tmp_path):
    """Caso da revisão: pasta pedida "Secao B", devolvido stash/Secao A/slides.pdf."""
    fonte = fixture(tmp_path)
    raiz = Path(fonte["moodle_dir"])
    slides = pdf_valido("slides")
    escreve(raiz / "stash/Secao A/slides.pdf", slides)
    api = carrega(raiz / "raw/moodle/contents.json")
    api.append({"section": 2, "name": "Secao B", "summary": "", "modules": [
        {"id": 950, "name": "Slides", "modname": "resource",
         "contents": [{"type": "file", "filename": "slides.pdf", "filesize": len(slides)}]}]})
    escreve(raiz / "raw/moodle/contents.json", json.dumps(api))
    a = {"rel": "stash/Secao A/slides.pdf", "sha": G.sha_b(slides)}
    assert G.resolve_origem({"filename": "slides.pdf", "filesize": len(slides)}, "Secao B",
                            {("slides.pdf", len(slides)): [a]}) == (None, "origem_nao_confirmada")
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    doc = [m for m in carrega(p / "materiais.json")["materiais"] if m["nome_original"] == "slides.pdf"]
    assert sorted((m["tipo"], m["adjudicavel"], m["ocorrencias"][0]["secao"], m["ocorrencias"][0]["modulo"]) for m in doc) == [
        ("arquivo", True, "Secao A", ""), ("origem_nao_confirmada", False, "Secao B", "Slides")]
    lig = carrega(p / "pacote_manifesto.json")["fontes_lidas"]["moodle:stash/Secao A/slides.pdf"]["ligacao"]
    assert lig == ["sem_modulo"]


def fixture_inventario(tmp):
    """API + inventário da aquisição; o módulo 405 tem arquivo de mesmo nome e tamanho, bytes diferentes, na mesma seção."""
    fonte = fixture(tmp)
    raiz = Path(fonte["moodle_dir"])
    escreve(raiz / "stash/Unidade 1/405/aula1.pdf", pdf_valido("aula 1 BYTES"))   # colisão gravada na pasta do módulo
    api = carrega(raiz / "raw/moodle/contents.json")
    api[1]["modules"][2]["contents"] = [{"type": "file", "filename": "tutorial.html", "filepath": "/", "filesize": 0},
                                        {"type": "file", "filename": "figura.png", "filepath": "/", "filesize": 10}]
    escreve(raiz / "raw/moodle/contents.json", json.dumps(api))

    def reg(mid, modname, arquivo, caminho=None, status="ok"):
        r = {"secao": "", "modulo_id": str(mid), "modname": modname, "arquivo": arquivo, "tamanho_api": 0, "status": status}
        if caminho:
            b = (raiz / caminho).read_bytes()
            r.update(caminho=caminho, sha256=G.sha_b(b), bytes=len(b))
        return r

    inv = {"esquema": "inventario-downloads-1", "cursos": [{"id": "999", "arquivos": [
        reg(402, "resource", "aula1.pdf", "stash/Geral/aula1.pdf"),
        reg(403, "url", "Site do livro", status="link_externo"),
        reg(405, "resource", "aula1.pdf", "stash/Unidade 1/405/aula1.pdf"),
        reg(406, "resource", "lista1.pdf", "stash/Unidade 1/lista1.pdf"),
        reg(407, "assign", "enunciado.pdf", status="tipo_inesperado"),
        reg(501, "page", "tutorial.html", "raw/moodle/pages/501-tutorial.html"),
        {**reg(501, "page", "figura.png"), "base": "anexos_de_pagina", "caminho": "501-figura.png", "status": "ok"}]}]}
    escreve(tmp / "aquisicao/inventario_downloads.json", json.dumps(inv))
    return fonte, {"inventario": str(tmp / "aquisicao/inventario_downloads.json"), "curso_id": "999"}


def test_sem_inventario_nome_e_tamanho_ficam_ambiguos(tmp_path):
    fonte, _ = fixture_inventario(tmp_path)
    with pytest.raises(G.AmbiguidadeOrigem):
        G.monta(fonte, tmp_path / "pacote")


def test_proveniencia_da_aquisicao_decide_a_ligacao(tmp_path):
    fonte, inv = fixture_inventario(tmp_path)
    fonte.update(inv, inventario_sha256=G.sha_b(Path(inv["inventario"]).read_bytes()))   # v4: sha esperado
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    mats = carrega(p / "materiais.json")["materiais"]
    por_ocorr = {(m["ocorrencias"][0]["modulo"], m["tipo"]): m for m in mats}
    assert (p / por_ocorr[("Aula 1 (de novo)", "arquivo")]["arquivo"]).read_bytes() == pdf_valido("aula 1 BYTES")
    assert (p / por_ocorr[("Aula 1", "arquivo")]["arquivo"]).read_bytes() == pdf_valido("aula 1 bytes")
    enunciado = por_ocorr[("Trabalho", "arquivo_nao_adquirido")]
    assert not enunciado["adjudicavel"] and enunciado["motivo"] == "aquisição: tipo_inesperado"
    anexo = por_ocorr[("Tutorial", "anexo_de_pagina")]
    assert not anexo["adjudicavel"] and anexo["nome_original"] == "figura.png"
    assert por_ocorr[("Tutorial", "pagina")]["adjudicavel"]
    man = carrega(p / "pacote_manifesto.json")
    assert man["fontes_lidas"]["aquisicao:inventario_downloads.json"]["papel"] == "inventario_aquisicao"
    assert man["fontes_lidas"]["moodle:stash/Unidade 1/405/aula1.pdf"]["ligacao"] == ["inventario_aquisicao"]
    assert {x["fonte"]: x["motivo"] for x in man["fontes_nao_usadas"]}["moodle:stash/Unidade 1/aula1.pdf"] == \
        "cópia idêntica de material já incluído"


@pytest.mark.parametrize("adultera, erro", [
    (lambda raiz, inv: escreve(raiz / "stash/Unidade 1/lista1.pdf", pdf_valido("lista 1 BYTES")), "sha256 diferente"),
    (lambda raiz, inv: inv["cursos"][0]["arquivos"].pop(3), "0 registros"),
    (lambda raiz, inv: inv["cursos"][0].update(id="000"), "sem o curso"),
    (lambda raiz, inv: inv.update(esquema="inventario-downloads-2", concluido=False), "parcial"),
    (lambda raiz, inv: inv["cursos"][0]["arquivos"][3].update(base="anexos_de_pagina"), "ausente na fonte"),
], ids=["sha-divergente", "sem-registro", "sem-curso", "parcial", "base-errada"])
def test_divergencia_de_proveniencia_falha_a_geracao(tmp_path, adultera, erro):
    fonte, inv_ref = fixture_inventario(tmp_path)
    fonte.update(inv_ref)
    inv = carrega(inv_ref["inventario"])
    adultera(Path(fonte["moodle_dir"]), inv)
    escreve(Path(inv_ref["inventario"]), json.dumps(inv))
    fonte["inventario_sha256"] = G.sha_b(Path(inv_ref["inventario"]).read_bytes())   # v4: isola a checagem do caso
    with pytest.raises(G.DivergenciaProveniencia, match=erro):
        G.monta(fonte, tmp_path / "pacote")
