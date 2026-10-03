"""R-META (metadados medidos pelo MoodleClient real) e R-PAGE (HTML principal estrito) no adquire v5. Escritos ANTES das
correções. Sem rede: `http.client.HTTPResponse` real sobre BytesIO como transporte falso."""
import http.client
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adquire as A  # noqa: E402
from test_adquire_v3 import Cliente, conteudo, modulo, rede, secao  # noqa: E402,F401


class _Socket:
    def __init__(self, bruto):
        self.bruto = bruto

    def makefile(self, modo):
        return io.BytesIO(self.bruto)


def http_resp(corpo, content_length=True):
    cab = "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n"
    cab += f"Content-Length: {len(corpo)}\r\n" if content_length else "Connection: close\r\n"
    r = http.client.HTTPResponse(_Socket(cab.encode() + b"\r\n" + corpo))
    r.begin()
    return r


def transporte(monkeypatch, webservice, arquivos=None):
    """webservice: {wsfunction: (corpo, content_length)}; arquivos: {url sem token: bytes}."""
    def urlopen(req, timeout=None):
        if isinstance(req, urllib.request.Request):
            fn = dict(urllib.parse.parse_qsl(req.data.decode()))["wsfunction"]
            corpo, cl = webservice[fn]
            return http_resp(corpo, cl)
        return http_resp((arquivos or {})[str(req).split("?")[0]])

    monkeypatch.setattr(A.urllib.request, "urlopen", urlopen)
    return A.M.MoodleClient("https://m", "tok")


def contents_json(*mods):
    return json.dumps([{"section": 0, "name": "S", "modules": list(mods)}], indent=2).encode()   # indentado


def prepara(tmp_path, monkeypatch, cli, triagem_extra=None, orc=None):
    saida = tmp_path / "saida"
    saida.mkdir()
    tri = {"cursos": [{"id": "1", "nome": "Curso 1", "semestre": "2025/1"}], "ordem_de_download": ["1"], **(triagem_extra or {})}
    (saida / "triagem.json").write_text(json.dumps(tri), encoding="utf-8")
    monkeypatch.setattr(A, "AQUI", saida)
    monkeypatch.setattr(A, "DESTINO", tmp_path / "fontes")
    monkeypatch.setattr(A, "REPO", tmp_path)
    monkeypatch.setattr(A, "cliente", lambda: (cli, "https://m"))
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 100, "bytes_totais_max": 1000, "cursos_baixados_max": 10, **(orc or {})})
    return saida


def inventario(saida):
    return json.loads((saida / "inventario_downloads.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ R-META
def test_metadados_contados_pelo_corpo_recebido_nao_pelo_json_reserializado(tmp_path, monkeypatch):
    mod = {"id": 1, "modname": "resource", "contents": [conteudo("a.txt", "https://m/a", 1)]}
    corpo = contents_json(mod)
    cli = transporte(monkeypatch, {"core_course_get_contents": (corpo, True)}, {"https://m/a": b"a"})
    saida = prepara(tmp_path, monkeypatch, cli, {"bytes_metadados_catalogo": 40})
    A.baixar()
    inv = inventario(saida)
    reserializado = len((tmp_path / "fontes/1/raw/moodle/contents.json").read_bytes())
    assert reserializado != len(corpo)
    assert inv["bytes_metadados"] == 40 + len(corpo)
    assert inv["bytes_transferidos"] == 40 + len(corpo) + 1 and inv["bytes_aceitos"] == 1
    assert not any("metadados" in i for i in inv.get("impedimentos", []))


@pytest.mark.parametrize("content_length, lidos", [(True, 0), (False, 50)], ids=["com-content-length", "sem-content-length"])
def test_metadados_acima_do_orcamento(tmp_path, monkeypatch, content_length, lidos):
    corpo = contents_json({"id": 1, "modname": "resource", "contents": [conteudo("a.txt", "https://m/a", 1)]})
    assert len(corpo) > 50
    cli = transporte(monkeypatch, {"core_course_get_contents": (corpo, content_length)})
    saida = prepara(tmp_path, monkeypatch, cli, {"bytes_metadados_catalogo": 0}, {"bytes_totais_max": 50})
    A.baixar()
    inv = inventario(saida)
    assert inv["cursos"][0]["erro"] == "nao_baixado_orcamento_real:metadados"
    assert inv["bytes_metadados"] == lidos and inv["bytes_transferidos"] == lidos <= 50


@pytest.mark.parametrize("corpo, erro", [(b"{nao e json", "falha:JSONDecodeError"),
                                         (json.dumps({"exception": "x", "errorcode": "e", "message": "m"}).encode(), "falha:RuntimeError")],
                         ids=["json-invalido", "erro-da-api"])
def test_metadados_contados_no_caminho_de_falha(tmp_path, monkeypatch, corpo, erro):
    cli = transporte(monkeypatch, {"core_course_get_contents": (corpo, True)})
    saida = prepara(tmp_path, monkeypatch, cli, {"bytes_metadados_catalogo": 0})
    A.baixar()
    inv = inventario(saida)
    assert inv["cursos"][0]["erro"] == erro and inv["bytes_metadados"] == len(corpo) == inv["bytes_transferidos"]


def test_catalogo_conta_site_info_e_get_users_courses(tmp_path, monkeypatch):
    info = json.dumps({"siteurl": "https://m", "userid": 7}, indent=4).encode()
    cursos = json.dumps([{"id": 5, "fullname": "Espaço institucional", "shortname": "esp"}], indent=4).encode()
    cli = transporte(monkeypatch, {"core_webservice_get_site_info": (info, True), "core_enrol_get_users_courses": (cursos, False)})
    saida = tmp_path / "saida"
    saida.mkdir()
    monkeypatch.setattr(A, "AQUI", saida)
    monkeypatch.setattr(A, "cliente", lambda: (cli, "https://m"))
    monkeypatch.setattr(A, "pastas_anteriores", lambda: set())
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 100, "bytes_totais_max": 1000, "cursos_baixados_max": 10})
    A.catalogo()
    tri = json.loads((saida / "triagem.json").read_text(encoding="utf-8"))
    assert tri["bytes_metadados_catalogo"] == len(info) + len(cursos)


def test_triagem_sem_contagem_do_catalogo_registra_impedimento(tmp_path, monkeypatch):
    corpo = contents_json()
    cli = transporte(monkeypatch, {"core_course_get_contents": (corpo, True)})
    saida = prepara(tmp_path, monkeypatch, cli)
    A.baixar()
    inv = inventario(saida)
    assert inv["bytes_metadados"] == len(corpo) and any("catálogo" in i for i in inv["impedimentos"])


# ------------------------------------------------------------------------------------------------ R-PAGE
def pagina(*conteudos):
    return Cliente({"c": [secao("S", {"id": 9, "modname": "page", "contents": list(conteudos)})]})


def idx(url, **k):
    c = {"type": "file", "filename": "index.html", "filepath": "/", "filesize": 0, "fileurl": url}
    c.update(k)
    return {x: v for x, v in c.items() if v is not None}


def baixa(cli, raiz):
    arquivos = []
    A.baixa_curso(cli, "c", raiz, {"transferidos": 0, "aceitos": 0}, arquivos)
    return arquivos


def test_anexo_html_nao_vira_html_principal(tmp_path, rede):
    rede.update({"u/n": b"<p>notas</p>", "u/i": b"<p>pagina</p>"})
    arquivos = baixa(pagina(conteudo("notas.html", "u/n", 12), idx("u/i")), tmp_path / "c")
    por = {a["arquivo"]: a for a in arquivos}
    assert (por["index.html"]["caminho"], por["index.html"]["papel"]) == ("raw/moodle/pages/9-index.html", "html_principal")
    assert (por["notas.html"]["base"], por["notas.html"]["papel"]) == ("anexos_de_pagina", "anexo_de_pagina")


def test_colisao_com_index_html_de_anexo(tmp_path, rede):
    rede.update({"u/real": b"<p>anexo chamado index</p>", "u/i": b"<p>pagina</p>"})
    arquivos = baixa(pagina(idx("u/real", filesize=26, mimetype="text/html"), idx("u/i")), tmp_path / "c")
    principal = [a for a in arquivos if a.get("papel") == "html_principal"]
    assert len(principal) == 1 and (tmp_path / "c" / principal[0]["caminho"]).read_bytes() == b"<p>pagina</p>"
    assert any(a.get("papel") == "anexo_de_pagina" and a["arquivo"] == "index.html" for a in arquivos)


@pytest.mark.parametrize("conteudos, status", [
    ([idx("u/1"), idx("u/2")], "html_principal_ambiguo"),
    ([idx("u/1", filepath=None)], "html_principal_ausente"),
    ([idx("u/1", filesize=None)], "html_principal_ausente"),
    ([], "html_principal_ausente"),
], ids=["dois-candidatos", "sem-filepath", "sem-filesize", "sem-conteudos"])
def test_zero_ou_varios_candidatos_nao_cobertos_e_no_denominador(tmp_path, rede, conteudos, status):
    rede.update({"u/1": b"<p>1</p>", "u/2": b"<p>2</p>"})
    arquivos = baixa(pagina(*conteudos), tmp_path / "c")
    ocorr = [a for a in arquivos if a.get("papel") == "html_principal"]
    assert [(a["status"], a["modulo_id"]) for a in ocorr] == [(status, "9")]
    assert not (tmp_path / "c/raw/moodle/pages").exists()


# ------------------------------------------------------------------------------------------------ catálogo entre execuções
# Achados do revisor por inspeção (não executados por ele); reproduzidos aqui antes da correção.
INFO = json.dumps({"siteurl": "https://m", "userid": 7}).encode()
CURSOS = json.dumps([{"id": 5, "fullname": "Espaço institucional", "shortname": "esp"}]).encode()


class _Interrompe:
    """Resposta sem Content-Length que entrega um bloco e é interrompida no seguinte."""
    headers = {}

    def __init__(self, corpo):
        self.corpo, self.leituras = corpo, 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, amt=-1):
        self.leituras += 1
        if self.leituras > 1:
            raise KeyboardInterrupt
        return self.corpo[:amt]


def ambiente_catalogo(tmp_path, monkeypatch, respostas, total):
    """respostas: {wsfunction: [fábrica de resposta, ...]} consumidas em ordem; um MoodleClient NOVO por execução."""
    saida = tmp_path / "saida"
    saida.mkdir(exist_ok=True)
    chamadas = []

    def urlopen(req, timeout=None):
        fn = dict(urllib.parse.parse_qsl(req.data.decode()))["wsfunction"]
        chamadas.append(fn)
        return respostas[fn].pop(0)()

    monkeypatch.setattr(A.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(A.M, "_BLOCO_LEITURA", 8)
    monkeypatch.setattr(A, "AQUI", saida)
    monkeypatch.setattr(A, "cliente", lambda: (A.M.MoodleClient("https://m", "tok"), "https://m"))
    monkeypatch.setattr(A, "pastas_anteriores", lambda: set())
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 100, "bytes_totais_max": total, "cursos_baixados_max": 10})
    return saida, chamadas


def registro(saida):
    return json.loads((saida / "metadados_catalogo.json").read_text(encoding="utf-8"))


def test_catalogo_repetido_desconta_o_consumo_anterior(tmp_path, monkeypatch):
    total = len(INFO) + len(CURSOS) + 10
    saida, _ = ambiente_catalogo(tmp_path, monkeypatch, {
        "core_webservice_get_site_info": [lambda: http_resp(INFO), lambda: http_resp(INFO)],
        "core_enrol_get_users_courses": [lambda: http_resp(CURSOS), lambda: http_resp(CURSOS)]}, total)
    A.catalogo()
    with pytest.raises(A.M.OrcamentoExcedido):
        A.catalogo()   # restam 10 bytes: o site_info (Content-Length maior) não é lido
    reg = registro(saida)
    assert reg["bytes_total"] == len(INFO) + len(CURSOS) <= total
    assert [e["erro"] for e in reg["execucoes"]] == [None, "falha:OrcamentoExcedido"]


def test_primeira_execucao_interrompida_parcial_e_segunda_limitada(tmp_path, monkeypatch):
    total = 2 * len(INFO) + 8 + 5
    saida, _ = ambiente_catalogo(tmp_path, monkeypatch, {
        "core_webservice_get_site_info": [lambda: http_resp(INFO), lambda: http_resp(INFO)],
        "core_enrol_get_users_courses": [lambda: _Interrompe(CURSOS), lambda: http_resp(CURSOS)]}, total)
    with pytest.raises(KeyboardInterrupt):
        A.catalogo()
    assert registro(saida)["execucoes"] == [{"bytes": len(INFO) + 8, "erro": "interrompido"}]
    with pytest.raises(A.M.OrcamentoExcedido):
        A.catalogo()   # restam len(INFO) + 5: o site_info cabe, a lista de cursos não
    reg = registro(saida)
    assert reg["bytes_total"] == 2 * len(INFO) + 8 <= total
    assert [e["erro"] for e in reg["execucoes"]] == ["interrompido", "falha:OrcamentoExcedido"]


@pytest.mark.parametrize("onde, bytes_esperados", [("site_info", 8), ("get_users_courses", None)],
                         ids=["durante-site_info", "durante-get_users_courses"])
def test_interrupcao_no_catalogo_registra_os_bytes_e_propaga(tmp_path, monkeypatch, onde, bytes_esperados):
    info = [lambda: _Interrompe(INFO)] if onde == "site_info" else [lambda: http_resp(INFO)]
    saida, _ = ambiente_catalogo(tmp_path, monkeypatch, {
        "core_webservice_get_site_info": info, "core_enrol_get_users_courses": [lambda: _Interrompe(CURSOS)]}, 1000)
    with pytest.raises(KeyboardInterrupt):
        A.catalogo()
    esperado = bytes_esperados if bytes_esperados is not None else len(INFO) + 8
    assert registro(saida) == {"execucoes": [{"bytes": esperado, "erro": "interrompido"}], "bytes_total": esperado}


@pytest.mark.parametrize("conteudo", ["{nao e json", json.dumps({"execucoes": [{"bytes": 5, "erro": None}], "bytes_total": 99}),
                                      json.dumps({"execucoes": [{"bytes": -1, "erro": None}], "bytes_total": -1})],
                         ids=["ilegivel", "total-inconsistente", "bytes-negativos"])
def test_registro_do_catalogo_ilegivel_nao_vira_zero(tmp_path, monkeypatch, conteudo):
    saida, chamadas = ambiente_catalogo(tmp_path, monkeypatch, {}, 1000)
    (saida / "metadados_catalogo.json").write_text(conteudo, encoding="utf-8")
    with pytest.raises(A.RegistroIlegivel):
        A.catalogo()
    assert chamadas == []


def test_baixar_usa_o_registro_do_catalogo_e_nao_a_triagem_antiga(tmp_path, monkeypatch):
    corpo = contents_json()
    cli = transporte(monkeypatch, {"core_course_get_contents": (corpo, True)})
    saida = prepara(tmp_path, monkeypatch, cli, {"bytes_metadados_catalogo": 40})
    (saida / "metadados_catalogo.json").write_text(json.dumps(
        {"execucoes": [{"bytes": 40, "erro": None}, {"bytes": 50, "erro": "interrompido"}], "bytes_total": 90}), encoding="utf-8")
    A.baixar()
    assert inventario(saida)["bytes_metadados"] == 90 + len(corpo)


@pytest.mark.parametrize("conteudo", ["{nao e json", json.dumps({"execucoes": [{"bytes": 10, "erro": None}], "bytes_total": 10})],
                         ids=["ilegivel", "menor-que-a-triagem"])
def test_baixar_com_registro_ilegivel_ou_inconsistente_nao_requisita(tmp_path, monkeypatch, conteudo):
    chamadas = []
    cli = transporte(monkeypatch, {"core_course_get_contents": (contents_json(), True)})
    monkeypatch.setattr(A.urllib.request, "urlopen", lambda *a, **k: chamadas.append(a) or (_ for _ in ()).throw(AssertionError))
    saida = prepara(tmp_path, monkeypatch, cli, {"bytes_metadados_catalogo": 40})
    (saida / "metadados_catalogo.json").write_text(conteudo, encoding="utf-8")
    with pytest.raises(A.RegistroIlegivel):
        A.baixar()
    assert chamadas == [] and not (saida / "inventario_downloads.json").exists()
