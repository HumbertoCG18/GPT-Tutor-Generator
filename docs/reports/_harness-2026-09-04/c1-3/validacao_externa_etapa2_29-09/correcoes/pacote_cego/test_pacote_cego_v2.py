"""Testes negativos das correções da revisão (pacote-cego-2), só com fixtures sintéticas."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gera_pacote_cego as G  # noqa: E402
from test_pacote_cego import carrega, escreve, fixture, pacote  # noqa: E402,F401

TOKEN_FALSO = "a1b2c3d4" * 4


def fixture_pastas_com_armadilhas(tmp):
    fonte = fixture(tmp, formato="pastas")
    raiz = Path(fonte["moodle_dir"])
    escreve(raiz / "Unidade 1/.env", f"MOODLE_TOKEN={TOKEN_FALSO}\n")
    escreve(raiz / "Unidade 1/config.json", json.dumps({"api": "x"}))
    escreve(raiz / "Unidade 1/anotacoes.txt", "aula1 -> computed_unit_slug: unidade-01\n")
    escreve(raiz / "Unidade 1/slides.pdf", json.dumps({"computed_block_id": "bloco-03"}))   # saída renomeada
    escreve(raiz / "Unidade 2/aula.txt", "Resumo da aula sobre escalonamento.\n")
    escreve(raiz / "Unidade 2/Token Ring e Cookies.pdf", b"%PDF-1.4 token ring")          # nome sensível, arquivo legítimo
    return fonte


def test_pastas_recusa_configuracao_segredo_e_saida_renomeada(tmp_path):
    fonte = fixture_pastas_com_armadilhas(tmp_path)
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    mats = {m["nome_original"]: m for m in carrega(p / "materiais.json")["materiais"]}
    assert mats["anotacoes.txt"]["tipo"] == "recusado" and "motor" in mats["anotacoes.txt"]["motivo"]
    assert mats["slides.pdf"]["tipo"] == "recusado" and "assinatura" in mats["slides.pdf"]["motivo"]
    assert mats["aula.txt"]["adjudicavel"] and mats["Token Ring e Cookies.pdf"]["adjudicavel"]
    assert ".env" not in mats and "config.json" not in mats
    nao_usados = {x["fonte"]: x["motivo"] for x in carrega(p / "pacote_manifesto.json")["fontes_nao_usadas"]}
    assert "configuração ou credencial" in nao_usados["moodle:Unidade 1/.env"]
    assert "configuração ou credencial" in nao_usados["moodle:Unidade 1/config.json"]
    copiados = {q.name.split("__", 1)[-1] for q in (p / "materiais").iterdir()}
    assert copiados == {"aula1.pdf", "lista1.pdf", "aula.txt", "Token Ring e Cookies.pdf"}
    tudo = b"".join(q.read_bytes() for q in p.rglob("*") if q.is_file())
    assert TOKEN_FALSO.encode() not in tudo and b"computed_unit_slug" not in tudo and b"computed_block_id" not in tudo


def test_api_segredo_em_pagina_e_url_com_token(tmp_path):
    fonte = fixture(tmp_path)
    raiz = Path(fonte["moodle_dir"])
    escreve(raiz / "raw/moodle/pages/501-tutorial.html", "<p>use MOODLE_TOKEN=" + "f00d" * 8 + " no script</p>")
    api = carrega(raiz / "raw/moodle/contents.json")
    api[0]["modules"][2]["url"] = "https://moodle.exemplo/mod/url/view.php?id=403&token=" + "beef" * 8 + "&x=1"
    escreve(raiz / "raw/moodle/contents.json", json.dumps(api))
    G.monta(fonte, tmp_path / "pacote")
    p = tmp_path / "pacote"
    assert G.audita(fonte, p) == []
    mats = carrega(p / "materiais.json")["materiais"]
    pagina = next(m for m in mats if m["nome_original"] == "501-tutorial.html")
    assert pagina["tipo"] == "recusado" and "credencial" in pagina["motivo"]
    link = next(m for m in mats if m["tipo"] == "link_externo")
    assert link["url"] == "https://moodle.exemplo/mod/url/view.php?id=403&x=1"
    tudo = b"".join(q.read_bytes() for q in p.rglob("*") if q.is_file())
    assert b"beef" * 8 not in tudo and b"f00d" * 8 not in tudo


def fixture_mesmo_nome(tmp, pastas):
    fonte = fixture(tmp)
    raiz = Path(fonte["moodle_dir"])
    a, b = b"%PDF-1.4 conteudo A", b"%PDF-1.4 conteudo B"
    escreve(raiz / f"stash/{pastas[0]}/slides.pdf", a)
    escreve(raiz / f"stash/{pastas[1]}/slides.pdf", b)
    api = carrega(raiz / "raw/moodle/contents.json")
    for i, sec in enumerate(api):
        sec["modules"].append({"id": 900 + i, "name": f"Slides {i}", "modname": "resource",
                               "contents": [{"type": "file", "filename": "slides.pdf", "filesize": len(a)}]})
    escreve(raiz / "raw/moodle/contents.json", json.dumps(api))
    return fonte


def test_correspondencia_por_nome_e_tamanho_resolvida_pela_secao(tmp_path):
    fonte = fixture_mesmo_nome(tmp_path, ("Geral", "Unidade 1"))
    G.monta(fonte, tmp_path / "pacote")
    assert G.audita(fonte, tmp_path / "pacote") == []
    slides = [m for m in carrega(tmp_path / "pacote/materiais.json")["materiais"] if m["nome_original"] == "slides.pdf"]
    assert sorted((m["ocorrencias"][0]["secao"], len(m["ocorrencias"])) for m in slides) == [("Geral", 1), ("Unidade 1", 1)]
    geral = next(m for m in slides if m["ocorrencias"][0]["secao"] == "Geral")
    assert (tmp_path / "pacote" / geral["arquivo"]).read_bytes() == b"%PDF-1.4 conteudo A"


def test_correspondencia_ambigua_falha_a_geracao(tmp_path):
    fonte = fixture_mesmo_nome(tmp_path, ("Pasta X", "Pasta Y"))
    with pytest.raises(G.AmbiguidadeOrigem):
        G.monta(fonte, tmp_path / "pacote")


def test_procedencia_completa_e_auditada(pacote):
    fonte, p = pacote
    man = carrega(p / "pacote_manifesto.json")
    raiz = Path(fonte["moodle_dir"])
    todos = {"moodle:" + q.relative_to(raiz).as_posix() for q in raiz.rglob("*") if q.is_file()}
    assert todos == {k for k in man["fontes_lidas"] if k.startswith("moodle:")} | {x["fonte"] for x in man["fontes_nao_usadas"]}
    assert all(e["sha256"] for info in man["arquivos"].values() for e in info["origem"].get("entradas", []))
    man["fontes_nao_usadas"] = man["fontes_nao_usadas"][1:]   # some um registro de arquivo não usado
    (p / "pacote_manifesto.json").write_bytes(G.json_bytes(man))
    prob = G.audita(fonte, p)
    assert any("procedência incompleta" in x for x in prob) and any("regeneração" in x for x in prob)


def test_reproduz_o_bypass_da_revisao_e_nao_copia(tmp_path):
    """Cenário da conferência independente: .env, anotação com predição e aula, em formato de pastas."""
    fonte = fixture(tmp_path, formato="pastas")
    raiz = Path(fonte["moodle_dir"])
    escreve(raiz / "Unidade 1/.env", "GEMINI_API_KEY=" + "x" * 39 + "\n")
    escreve(raiz / "Unidade 1/anotacoes.txt", json.dumps({"id": "aula", "computed_subunit_slug": "t1"}))
    escreve(raiz / "Unidade 1/aula.txt", "Conteúdo da aula.\n")
    G.monta(fonte, tmp_path / "pacote")
    assert G.audita(fonte, tmp_path / "pacote") == []
    copiados = {q.name.split("__", 1)[-1] for q in (tmp_path / "pacote/materiais").iterdir()}
    assert ".env" not in copiados and "anotacoes.txt" not in copiados and "aula.txt" in copiados


@pytest.mark.parametrize("nome, dados, recusa", [
    ("a.pdf", b"%PDF-1.7 ok", None), ("a.pdf", b'{"x": 1}', "assinatura"), ("a.docx", b"PK\x03\x04ok", None),
    ("a.docx", b"%PDF", "assinatura"), ("a.exe", b"MZ", "extensão"), ("a.txt", b"texto comum", None),
    ("a.txt", b"x = 'AIza" + b"B" * 35 + b"'", "credencial"), ("a.md", b"winner_score=3.2", "motor"),
    ("a.mp4", b"\x00\x00\x00\x18ftypmp42", None), ("a.mp4", b"not a video", "assinatura"),
])
def test_verifica_material(nome, dados, recusa):
    motivo = G.verifica_material(nome, dados)
    assert (motivo is None) if recusa is None else (recusa in motivo), motivo
