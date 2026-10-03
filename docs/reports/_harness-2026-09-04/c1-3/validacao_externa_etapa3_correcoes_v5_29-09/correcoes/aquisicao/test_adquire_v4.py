"""Contraexemplos da revisão da etapa 3 para o adquire v4, escritos ANTES das correções. Sem rede: cliente falso e
`urlopen` falso; o caso HTTP usa `http.client.HTTPResponse` real sobre um socket falso (BytesIO).

Nomes canônicos (correspondência com os IDs anteriores em ../../relatorio_correcoes_etapa3.md).
"""
import http.client
import io
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adquire as A  # noqa: E402
from test_adquire_v3 import Cliente, conteudo, modulo, prepara_baixar, rede, secao  # noqa: E402,F401


def orc():
    return {"bytes": 0, "transferidos": 0, "aceitos": 0}   # "bytes" só para a v3 rodar e mostrar o defeito


def curso(*mods):
    return Cliente({"c": [secao("S", *mods)]})


def baixa(cli, raiz, o=None):
    o = o if o is not None else orc()
    arquivos = []
    A.baixa_curso(cli, "c", raiz, o, arquivos)
    return arquivos, o


class _Socket:
    def __init__(self, bruto):
        self.bruto = bruto

    def makefile(self, modo):
        return io.BytesIO(self.bruto)


def resposta_http(bruto):
    r = http.client.HTTPResponse(_Socket(bruto))
    r.begin()
    return r


def test_truncated_http_body_regression(tmp_path, rede, monkeypatch):
    """Content-Length 5, corpo 'abc': a v2 recusava (IncompleteRead); a v3 aceitava 3 bytes como ok."""
    bruto = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 5\r\n\r\nabc"
    monkeypatch.setattr(A.urllib.request, "urlopen", lambda url, timeout=None: resposta_http(bruto))
    arquivos, o = baixa(curso(modulo(1, "resource", conteudo("x.txt", "u/x"))), tmp_path / "c")
    assert arquivos[0]["status"] == "falha_http:IncompleteRead"
    assert not (tmp_path / "c/stash/S/x.txt").exists() and o["aceitos"] == 0 and o["transferidos"] == 3


def test_path_traversal(tmp_path, rede):
    rede["u/e"] = b"fuga"
    arquivos, _ = baixa(curso(modulo(1, "resource", conteudo("../../../escaped.txt", "u/e"))), tmp_path / "a/b/c")
    assert arquivos[0]["status"] == "caminho_inseguro" and "caminho" not in arquivos[0]
    assert not any(p.name == "escaped.txt" for p in tmp_path.rglob("*"))


def test_rejected_transfer_budget(tmp_path, rede, monkeypatch):
    """Bytes de resposta recusada (e o byte de sondagem) contam como transferidos."""
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 5, "bytes_totais_max": 10, "cursos_baixados_max": 10})
    rede.update({"u/1": b"1234567", "u/2": b"abc"})
    arquivos, o = baixa(curso(modulo(1, "resource", conteudo("1.txt", "u/1")), modulo(2, "resource", conteudo("2.txt", "u/2"))),
                        tmp_path / "c")
    assert [a["status"] for a in arquivos] == ["acima_do_limite_real", "ok"]
    assert (o["transferidos"], o["aceitos"]) == (6 + 3, 3)
    assert [a["bytes_lidos"] for a in arquivos] == [6, 3]


def test_probe_respects_remaining_budget(tmp_path, rede, monkeypatch):
    """Nunca lê além do orçamento restante, nem o byte de sondagem."""
    monkeypatch.setattr(A, "ORC", {"bytes_por_arquivo_max": 10, "bytes_totais_max": 5, "cursos_baixados_max": 10})
    rede["u/x"] = b"1234567"
    arquivos, o = baixa(curso(modulo(1, "resource", conteudo("x.txt", "u/x"))), tmp_path / "c")
    assert arquivos[0]["status"] == "nao_baixado_orcamento_real"
    assert o["transferidos"] == 5 and o["aceitos"] == 0


def test_partial_write(tmp_path, rede, monkeypatch):
    """Escrita parcial falha: o byte persistido tem referência e conta como transferido."""
    rede["u/x"] = b"12345"
    escreve = Path.write_bytes

    def meia_escrita(self, dados):
        escreve(self, dados[:2])
        raise OSError("disco cheio")

    monkeypatch.setattr(Path, "write_bytes", meia_escrita)
    arquivos, o = baixa(curso(modulo(1, "resource", conteudo("x.txt", "u/x"))), tmp_path / "c")
    r = arquivos[0]
    assert r["status"] == "falha_local:OSError" and o["transferidos"] == 5 and o["aceitos"] == 0
    assert (tmp_path / "c" / r["caminho_parcial"]).read_bytes() == b"12"


@pytest.mark.parametrize("onde", ["escrita_do_parcial", "publicacao_do_arquivo"])
def test_interrupt_after_write(tmp_path, rede, monkeypatch, onde):
    """Interrupção na escrita do parcial ou na publicação: o registro já existe e aponta o que está no disco."""
    rede["u/x"] = b"12345"
    if onde == "escrita_do_parcial":
        escreve = Path.write_bytes

        def corta(self, dados):
            escreve(self, dados[:3])
            raise KeyboardInterrupt

        monkeypatch.setattr(Path, "write_bytes", corta)
    else:
        substitui = os.replace

        def publica(src, dst):   # só a publicação do arquivo; o contents.json publica normalmente
            if str(src).endswith(".parcial"):
                raise KeyboardInterrupt
            return substitui(src, dst)

        monkeypatch.setattr(os, "replace", publica)
    arquivos = []
    with pytest.raises(KeyboardInterrupt):
        A.baixa_curso(curso(modulo(1, "resource", conteudo("x.txt", "u/x"))), "c", tmp_path / "c", orc(), arquivos)
    assert [a["status"] for a in arquivos] == ["gravando"]
    persistidos = {p.relative_to(tmp_path / "c").as_posix() for p in (tmp_path / "c/stash").rglob("*") if p.is_file()}
    assert persistidos and persistidos <= {arquivos[0]["caminho"], arquivos[0]["caminho_parcial"]}


def test_baixar_interrupt_after_write(tmp_path, rede, monkeypatch):
    rede["u/x"] = b"12345"
    escreve = Path.write_bytes

    def corta(self, dados):
        escreve(self, dados)
        if self.name.startswith("x.txt"):
            raise KeyboardInterrupt

    monkeypatch.setattr(Path, "write_bytes", corta)
    saida = prepara_baixar(tmp_path, monkeypatch, {"1": [secao("S", modulo(1, "resource", conteudo("x.txt", "u/x")))]}, ["1"])
    with pytest.raises(KeyboardInterrupt):
        A.baixar()
    inv = json.loads((saida / "inventario_downloads.json").read_text(encoding="utf-8"))
    assert inv["concluido"] is False
    assert [(a["arquivo"], a["status"]) for a in inv["cursos"][0]["arquivos"]] == [("x.txt", "gravando")]
    assert inv["bytes_transferidos"] == 5


@pytest.mark.parametrize("onde", ["escrita_do_temporario", "publicacao"])
def test_inventory_write_interruption(tmp_path, monkeypatch, onde):
    """O checkpoint anterior sobrevive à falha na publicação do próximo."""
    p = tmp_path / "inventario_downloads.json"
    A.grava_json(p, {"versao": 1, "cursos": ["a"] * 20})
    anterior = p.read_bytes()
    if onde == "escrita_do_temporario":
        escreve = Path.write_text

        def corta(self, texto, **k):
            escreve(self, texto[:1], **k)
            raise KeyboardInterrupt

        monkeypatch.setattr(Path, "write_text", corta)
    else:
        monkeypatch.setattr(os, "replace", lambda *a: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        A.grava_json(p, {"versao": 2})
    assert p.read_bytes() == anterior


def test_metadata_outside_budget(tmp_path, rede, monkeypatch):
    """O cliente do produto não expõe os bytes recebidos de core_course_get_contents: impedimento registrado, e o
    tamanho do JSON reserializado não é contado como transferência."""
    rede["u/a"] = b"a"
    saida = prepara_baixar(tmp_path, monkeypatch, {"1": [secao("S", modulo(1, "resource", conteudo("a.txt", "u/a")))]}, ["1"])
    A.baixar()
    inv = json.loads((saida / "inventario_downloads.json").read_text(encoding="utf-8"))
    # v5: o cliente mede os metadados (o falso mede 0); o impedimento que resta é o da triagem pré-v5 sem a contagem
    # do catálogo. A medição real é testada em test_adquire_v5 com o MoodleClient verdadeiro.
    assert (inv["bytes_transferidos"], inv["bytes_aceitos"], inv["bytes_metadados"]) == (1, 1, 0)
    assert any("catálogo" in i for i in inv["impedimentos"])
