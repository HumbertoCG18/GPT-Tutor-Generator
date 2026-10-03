"""Testes do cegamento do pacote de adjudicação, só com fixtures sintéticas (nenhum curso real é lido)."""
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gera_pacote_cego as G  # noqa: E402

PLANO = """# Plano de Ensino

## Nº DA UNIDADE: 01
CONTEÚDO: Fundamentos de sistemas embarcados
1.1. Conceitos básicos de sistemas embarcados
1.2. Ferramentas de desenvolvimento cruzado

## Nº DA UNIDADE: 02
CONTEÚDO: Acionadores de dispositivos
2.1. Interface entre núcleo e dispositivo
2.2. Módulos carregáveis do núcleo

## BIBLIOGRAFIA
"""
PROIBIDO = {"computed_unit_slug": "unidade-02-acionadores-de-dispositivos", "computed_block_id": "bloco-03",
            "subunit_match_confidence": 0.9, "subunit_match_reasons": ["winner_score=3.2"]}


def escreve(p, dados):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(dados if isinstance(dados, bytes) else dados.encode("utf-8"))


def fixture(tmp, formato="api"):
    raiz = tmp / "Moodle" / "curso-sintetico"
    aula1, lista1, pagina = b"%PDF-1.4 aula 1 bytes", b"%PDF-1.4 lista 1 bytes", b"<html><body>Tutorial</body></html>"
    if formato == "api":
        escreve(raiz / "stash/Geral/aula1.pdf", aula1)
        escreve(raiz / "stash/Unidade 1/aula1.pdf", aula1)   # v3: cada módulo baixado na pasta da sua seção
        escreve(raiz / "stash/Unidade 1/lista1.pdf", lista1)
        escreve(raiz / "raw/moodle/pages/501-tutorial.html", pagina)
        conteudo = lambda nome, n: {"type": "file", "filename": nome, "filepath": "/", "filesize": n, "fileurl": "x",
                                    "author": "Professor Fulano", "userid": 42, "license": "allrightsreserved"}
        api = [
            {"section": 0, "name": "Geral", "summary": "<p>G1 = (TP1+TP2)/2</p>", "id": 1, "visible": 1, "modules": [
                {"id": 401, "name": "Aviso", "modname": "label", "description": "<b>Aula 1 - 05/03</b>", "author": "x"},
                {"id": 402, "name": "Aula 1", "modname": "resource", "contents": [conteudo("aula1.pdf", len(aula1))]},
                {"id": 403, "name": "Site do livro", "modname": "url", "url": "https://exemplo.org/livro"},
                {"id": 404, "name": "Fórum", "modname": "forum"}]},
            {"section": 1, "name": "Unidade 1", "summary": "", "modules": [
                {"id": 405, "name": "Aula 1 (de novo)", "modname": "resource", "contents": [conteudo("aula1.pdf", len(aula1))]},
                {"id": 406, "name": "Lista 1", "modname": "resource", "contents": [conteudo("lista1.pdf", len(lista1))]},
                {"id": 501, "name": "Tutorial", "modname": "page"},
                {"id": 407, "name": "Trabalho", "modname": "assign", "contents": [conteudo("enunciado.pdf", 999)]}]}]
        escreve(raiz / "raw/moodle/contents.json", json.dumps(api, ensure_ascii=False))
        # gerados pelo produto (com campos de predição): nunca podem entrar
        escreve(raiz / "raw/moodle/labels.json", json.dumps([{"cmid": 401, "texto": "x", **PROIBIDO}]))
        escreve(raiz / "links.json", json.dumps([{"nome": "Aula 1", "sinal": "u01", "destino": "x", **PROIBIDO}]))
        escreve(raiz / "manual-review/links.md", "computed_unit_slug: unidade-01")
        escreve(raiz / "stash/.moodle_nomes.json", json.dumps(PROIBIDO))
    else:
        escreve(raiz / "Unidade 1/aula1.pdf", aula1)
        escreve(raiz / "Unidade 1/_ARQUIVOS_DO_CARD.txt", "Arquivos presentes neste card:")
        escreve(raiz / "Unidade 2/lista1.pdf", lista1)
    # tutor vizinho com saídas do motor
    escreve(tmp / "Curso-Sintetico-Tutor/manifest.json", json.dumps({"entries": [{"id": "aula1", **PROIBIDO}]}))
    escreve(tmp / "plano/plano.pdf", b"%PDF-1.4 plano")
    escreve(tmp / "plano/plano.md", PLANO)
    return {"sigla": "SIN", "nome": "Curso Sintético", "moodle_dir": str(raiz), "plano_arquivo": str(tmp / "plano/plano.pdf"),
            "plano_texto": str(tmp / "plano/plano.md")}


def carrega(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def regrava_manifesto(pacote):
    """Atualiza o sha256 no manifesto depois de adulterar, para isolar a detecção pelos outros controles."""
    m = carrega(pacote / "pacote_manifesto.json")
    for rel in m["arquivos"]:
        if (pacote / rel).is_file():
            m["arquivos"][rel]["sha256"] = G.sha_b((pacote / rel).read_bytes())
    (pacote / "pacote_manifesto.json").write_bytes(G.json_bytes(m))


@pytest.fixture
def pacote(tmp_path):
    fonte = fixture(tmp_path)
    G.monta(fonte, tmp_path / "pacote")
    return fonte, tmp_path / "pacote"


def test_gera_audita_e_so_contem_fonte_bruta_permitida(pacote):
    fonte, p = pacote
    assert G.audita(fonte, p) == []
    mats = carrega(p / "materiais.json")["materiais"]
    tipos = sorted((m["tipo"], m["adjudicavel"]) for m in mats)
    assert tipos == [("arquivo", True), ("arquivo", True), ("arquivo_sem_fonte_local", False), ("link_externo", False),
                     ("pagina", True)]
    aula = next(m for m in mats if m["nome_original"] == "aula1.pdf")
    assert len(aula["ocorrencias"]) == 2          # mesmo arquivo em duas seções = um material
    textos = {q.name: q.read_text(encoding="utf-8", errors="ignore") for q in p.rglob("*") if q.suffix in {".json", ".csv", ".md"}}
    todo = "".join(textos.values())
    for proibido in ("computed_", "subunit_match", "winner_score", "sinal", "destino", "Professor Fulano", "userid", "license"):
        assert proibido not in todo, proibido   # v2: conteúdo proibido em lugar nenhum, nem no manifesto
    sem_manifesto = "".join(v for k, v in textos.items() if k != "pacote_manifesto.json")
    ignorados = {x["fonte"] for x in carrega(p / "pacote_manifesto.json")["fontes_nao_usadas"]}
    for nome in ("labels.json", "links.json", "manual-review", ".moodle_nomes.json"):
        assert nome not in sem_manifesto, nome   # v2: o NOME do ignorado só aparece no registro de procedência
        assert any(nome in f for f in ignorados), nome
    arquivos = {q.relative_to(p).as_posix() for q in p.rglob("*") if q.is_file()}
    assert not any("moodle_nomes" in a or a.endswith("labels.json") for a in arquivos)
    gold = (p / "gold_modelo.csv").read_text(encoding="utf-8").splitlines()
    assert gold[0] == ",".join(G.CAMPOS_GOLD) and len(gold) == 1 + 3


def test_rotulos_sao_so_do_plano_e_sem_alias(pacote):
    _, p = pacote
    r = carrega(p / "rotulos.json")
    assert [u["id"] for u in r["unidades"]] == ["U01", "U02"]
    assert [t["id"] for t in r["topicos"]] == ["U01.T01", "U01.T02", "U02.T01", "U02.T02"]
    assert r["unidades"][1]["slug"] == "unidade-02-acionadores-de-dispositivos"
    assert all("aliases" not in t for t in r["topicos"])


def test_deterministico(tmp_path):
    fonte = fixture(tmp_path)
    a, b = G.monta(fonte, tmp_path / "a"), G.monta(fonte, tmp_path / "b")
    assert a == b and (tmp_path / "a/pacote_manifesto.json").read_bytes() == (tmp_path / "b/pacote_manifesto.json").read_bytes()


def test_leitor_recusa_saidas_do_motor_e_gerados_do_produto(tmp_path):
    fonte = fixture(tmp_path)
    raiz = Path(fonte["moodle_dir"])
    leitor = G.Leitor([raiz, tmp_path])
    for proibido in (raiz / "raw/moodle/labels.json", raiz / "links.json", raiz / "manual-review/links.md",
                     raiz / "stash/.moodle_nomes.json", tmp_path / "Curso-Sintetico-Tutor/manifest.json"):
        with pytest.raises(G.AcessoNegado):
            leitor.le(proibido)
    escreve(tmp_path / ".frzero/x/captura.json", "{}")
    escreve(raiz / "course/.content_taxonomy.json", "{}")
    escreve(raiz / "x.glossary_curation.llm.json", "{}")
    for proibido in (tmp_path / ".frzero/x/captura.json", raiz / "course/.content_taxonomy.json"):
        with pytest.raises(G.AcessoNegado):
            leitor.le(proibido)
    with pytest.raises(G.AcessoNegado):
        G.Leitor([raiz]).le(tmp_path / "plano/plano.md")   # fora das raízes declaradas


def test_auditoria_pega_chave_proibida_injetada(pacote):
    fonte, p = pacote
    m = carrega(p / "materiais.json")
    m["materiais"][0]["computed_unit_slug"] = "unidade-01-fundamentos-de-sistemas-embarcados"
    (p / "materiais.json").write_bytes(G.json_bytes(m))
    regrava_manifesto(p)
    prob = G.audita(fonte, p)
    assert any("allowlist" in x for x in prob) and any("regeneração" in x for x in prob)


def test_auditoria_pega_predicao_renomeada_em_campo_permitido(pacote):
    fonte, p = pacote
    m = carrega(p / "materiais.json")
    m["materiais"][0]["ocorrencias"][0]["secao"] = "Unidade 2"   # campo permitido, valor adulterado (predição disfarçada)
    (p / "materiais.json").write_bytes(G.json_bytes(m))
    regrava_manifesto(p)
    prob = G.audita(fonte, p)
    assert prob and all("allowlist" not in x for x in prob) and any("regeneração" in x for x in prob)


def test_auditoria_pega_padrao_de_motor_em_valor(pacote):
    fonte, p = pacote
    r = carrega(p / "rotulos.json")
    r["topicos"][0]["rotulo"] = "bloco-03 conceitos"
    (p / "rotulos.json").write_bytes(G.json_bytes(r))
    regrava_manifesto(p)
    assert any("padrão de predição" in x for x in G.audita(fonte, p))


def test_auditoria_pega_arquivo_extra_e_bruto_adulterado(pacote):
    fonte, p = pacote
    (p / "materiais" / "extra.txt").write_text("computed_block_id: bloco-01", encoding="utf-8")
    alvo = next((p / "materiais").glob("*lista1.pdf"))
    alvo.write_bytes(b"%PDF adulterado")
    prob = G.audita(fonte, p)
    assert any("fora do manifesto" in x for x in prob) and any("sha256 != manifesto" in x for x in prob)


def test_plano_sem_unidades_recusa(tmp_path):
    fonte = fixture(tmp_path)
    Path(fonte["plano_texto"]).write_text("# Plano\nsem unidades\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="sem unidades"):
        G.monta(fonte, tmp_path / "pacote")


def test_destino_existente_recusa(pacote, tmp_path):
    fonte, p = pacote
    with pytest.raises(FileExistsError):
        G.monta(fonte, p)


def test_formato_de_pastas_sem_api(tmp_path):
    fonte = fixture(tmp_path, formato="pastas")
    G.monta(fonte, tmp_path / "pacote")
    assert G.audita(fonte, tmp_path / "pacote") == []
    est = carrega(tmp_path / "pacote/moodle_estrutura.json")
    assert est["formato"] == "pastas" and [s["nome"] for s in est["secoes"]] == ["Unidade 1", "Unidade 2"]
    assert not any("ARQUIVOS_DO_CARD" in q.name for q in (tmp_path / "pacote").rglob("*"))


def test_trava_de_repositorio_e_por_componente_do_caminho(tmp_path):
    """Pasta com "GPT-Tutor-Generator" DENTRO do nome (ex.: scratchpad) é permitida; componente de tutor ou do repo não."""
    ok = tmp_path / "C--Users-x-GitHub-GPT-Tutor-Generator" / "fonte.pdf"
    escreve(ok, b"%PDF")
    assert G.Leitor([tmp_path]).le(ok) == b"%PDF"
    for ruim in (tmp_path / "Curso-X-Tutor" / "a.pdf", tmp_path / "GPT-Tutor-Generator" / "a.pdf",
                 tmp_path / "GPT-Tutor-Generator-issue-14" / "a.pdf"):
        escreve(ruim, b"%PDF")
        with pytest.raises(G.AcessoNegado):
            G.Leitor([tmp_path]).le(ruim)
