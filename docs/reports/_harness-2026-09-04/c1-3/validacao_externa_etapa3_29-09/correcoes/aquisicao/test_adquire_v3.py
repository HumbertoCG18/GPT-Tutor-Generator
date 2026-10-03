"""Testes do adquire v3 sem rede: cliente e `urlopen` falsos. Reproduzem os casos da revisão da etapa 2."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adquire as A  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\nimagem"


class Resposta:
    def __init__(self, dados):
        self.dados, self.headers = dados, {"content-type": "application/octet-stream"}

    def read(self, n=-1):
        return self.dados if n is None or n < 0 else self.dados[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Cliente:
    def __init__(self, contents):
        self.contents = contents

    def get_course_contents(self, cid):
        return self.contents[cid]

    def _download_url(self, url):
        return url


def conteudo(nome, url, declarado=1):
    return {"type": "file", "filename": nome, "filepath": "/", "filesize": declarado, "fileurl": url}


def secao(nome, *modulos):
    return {"name": nome, "modules": list(modulos)}


def modulo(mid, modname, *conteudos):
    return {"id": mid, "modname": modname, "contents": list(conteudos)}


@pytest.fixture
def rede(monkeypatch):
    """Servidor falso: url -> bytes ou exceção. Nenhum socket é aberto."""
    respostas = {}

    def urlopen(url, timeout=None):
        v = respostas[url]
        if isinstance(v, BaseException):
            raise v
        return Resposta(v)

    monkeypatch.setattr(A.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 100, "bytes_totais_max": 1000, "cursos_baixados_max": 10})
    return respostas


def sha(b):
    return hashlib.sha256(b).hexdigest()


def test_anexo_de_pagina_fora_da_raiz_tem_referencia_valida(tmp_path, rede):
    """Caso da revisão: ValueError em relative_to e inventário não devolvido."""
    rede.update({"u/a": b"texto a", "u/idx": b"<html>pagina</html>", "u/img": PNG})
    cli = Cliente({"curso": [secao("Geral", modulo(1, "resource", conteudo("a.txt", "u/a")),
                                   modulo(2, "page", conteudo("index.html", "u/idx"), conteudo("imagem.png", "u/img")))]})
    raiz, arquivos = tmp_path / "downloads/curso", []
    A.baixa_curso(cli, "curso", raiz, {"bytes": 0}, arquivos)
    assert [a["status"] for a in arquivos] == ["ok", "ok", "ok"]
    anexo = next(a for a in arquivos if a["arquivo"] == "imagem.png")
    assert (anexo["base"], anexo["caminho"]) == ("anexos_de_pagina", "2-imagem.png")
    assert sha((tmp_path / "downloads/curso_anexos_de_pagina" / anexo["caminho"]).read_bytes()) == anexo["sha256"]
    pagina = next(a for a in arquivos if a["arquivo"] == "index.html")
    assert (pagina["base"], pagina["caminho"]) == ("curso", "raw/moodle/pages/2-index.html")
    assert all(a["filepath"] == "/" for a in arquivos)


def test_limite_por_arquivo_vale_para_bytes_reais(tmp_path, rede, monkeypatch):
    """Caso da revisão: filesize declarado 1, 7 bytes recebidos, limite 5, status ok."""
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 5, "bytes_totais_max": 5, "cursos_baixados_max": 10})
    rede["u/x"] = b"1234567"
    orc, arquivos = {"bytes": 0}, []
    A.baixa_curso(Cliente({"c": [secao("S", modulo(1, "resource", conteudo("x.txt", "u/x", 1)))]}), "c", tmp_path / "c", orc, arquivos)
    assert arquivos[0]["status"] == "acima_do_limite_real" and arquivos[0]["bytes_lidos"] == 6
    assert "caminho" not in arquivos[0] and orc["bytes"] == 0 and not (tmp_path / "c/stash/S/x.txt").exists()


def test_orcamento_total_vale_para_bytes_reais(tmp_path, rede, monkeypatch):
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 10, "bytes_totais_max": 12, "cursos_baixados_max": 10})
    rede.update({"u/1": b"8 bytes!", "u/2": b"8 bytes?"})
    orc, arquivos = {"bytes": 0}, []
    cli = Cliente({"c": [secao("S", modulo(1, "resource", conteudo("1.txt", "u/1")), modulo(2, "resource", conteudo("2.txt", "u/2")))]})
    A.baixa_curso(cli, "c", tmp_path / "c", orc, arquivos)
    assert [a["status"] for a in arquivos] == ["ok", "nao_baixado_orcamento_real"] and orc["bytes"] == 8


def test_falha_local_de_um_arquivo_e_registrada_e_o_curso_continua(tmp_path, rede, monkeypatch):
    rede.update({"u/a": b"a", "u/b": b"b", "u/c": b"c", "u/d": ConnectionResetError("https://x?token=segredo")})
    escreve = Path.write_bytes

    def write_bytes(self, dados):
        if self.name == "b.txt":
            raise OSError("caminho longo demais")
        return escreve(self, dados)

    monkeypatch.setattr(Path, "write_bytes", write_bytes)
    cli = Cliente({"c": [secao("S", *(modulo(i, "resource", conteudo(f"{n}.txt", f"u/{n}")) for i, n in enumerate("abcd")))]})
    arquivos = []
    A.baixa_curso(cli, "c", tmp_path / "c", {"bytes": 0}, arquivos)
    assert [a["status"] for a in arquivos] == ["ok", "falha_local:OSError", "ok", "falha_http:ConnectionResetError"]
    assert "caminho" not in arquivos[1] and "segredo" not in json.dumps(arquivos)


def prepara_baixar(tmp_path, monkeypatch, contents, ordem):
    saida = tmp_path / "saida"
    saida.mkdir()
    (saida / "triagem.json").write_text(json.dumps({"cursos": [{"id": c, "nome": f"Curso {c}", "semestre": "2025/1"} for c in ordem],
                                                    "ordem_de_download": ordem}), encoding="utf-8")
    monkeypatch.setattr(A, "AQUI", saida)
    monkeypatch.setattr(A, "DESTINO", tmp_path / "fontes")
    monkeypatch.setattr(A, "REPO", tmp_path)
    monkeypatch.setattr(A, "cliente", lambda: (Cliente(contents), "https://moodle.exemplo"))
    return saida


def test_falha_posterior_preserva_registros_ja_processados(tmp_path, rede, monkeypatch):
    rede.update({"u/a": b"a", "u/b": b"b", "u/idx": b"<html>p</html>", "u/img": PNG})
    contents = {"1": [secao("S", modulo(1, "resource", conteudo("a.txt", "u/a")), {"id": 2, "modname": "folder", "contents": 5})],
                "2": [secao("S", modulo(3, "resource", conteudo("b.txt", "u/b")),
                            modulo(4, "page", conteudo("index.html", "u/idx"), conteudo("imagem.png", "u/img")))]}
    saida = prepara_baixar(tmp_path, monkeypatch, contents, ["1", "2"])
    A.baixar()
    inv = json.loads((saida / "inventario_downloads.json").read_text(encoding="utf-8"))
    assert inv["concluido"] is True and inv["esquema"] == "inventario-downloads-2"
    c1, c2 = inv["cursos"]
    assert c1["erro"] == "falha:TypeError" and [(a["arquivo"], a["status"]) for a in c1["arquivos"]] == [("a.txt", "ok")]
    assert c2["erro"] is None and len(c2["arquivos"]) == 3
    A.congelar()
    fc = json.loads((saida / "fontes_congeladas.json").read_text(encoding="utf-8"))
    assert fc["cursos"]["2"]["arquivos_ok_conferem"] and fc["cursos"]["2"]["arvore_anexos_de_pagina"] == {"4-imagem.png": sha(PNG)}
    assert fc["cursos"]["1"]["arquivos_ok_conferem"] and fc["cursos"]["2"]["extras_alem_dos_downloads"] == []


def test_interrupcao_deixa_inventario_parcial_marcado(tmp_path, rede, monkeypatch):
    rede.update({"u/a": b"a", "u/b": b"b", "u/c": KeyboardInterrupt()})
    contents = {"1": [secao("S", modulo(1, "resource", conteudo("a.txt", "u/a")))],
                "2": [secao("S", modulo(2, "resource", conteudo("b.txt", "u/b")), modulo(3, "resource", conteudo("c.txt", "u/c")))]}
    saida = prepara_baixar(tmp_path, monkeypatch, contents, ["1", "2"])
    with pytest.raises(KeyboardInterrupt):
        A.baixar()
    inv = json.loads((saida / "inventario_downloads.json").read_text(encoding="utf-8"))
    assert inv["concluido"] is False and inv["parada"] == "interrompido"
    assert [c["erro"] for c in inv["cursos"]] == [None, "interrompido"]
    assert [a["arquivo"] for a in inv["cursos"][1]["arquivos"]] == ["b.txt"]
    with pytest.raises(SystemExit, match="parcial"):
        A.congelar()
