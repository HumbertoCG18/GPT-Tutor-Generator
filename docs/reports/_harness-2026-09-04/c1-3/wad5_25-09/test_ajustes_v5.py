"""W-AD5: reprodutores dos dois ajustes pedidos pela revisão independente do W-AD4. Resultados esperados escritos à mão.

Fase vermelha: rodados contra cópias byte a byte do código revisado (congelamento b3254509…) → testes_v5_vermelho.txt.
Fase verde: contra o código W-AD5. Só arquivos temporários; nenhuma fonte real é apagada; o ambiente real não é mudado
(a lista de distribuições é simulada).
"""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import captura as CP  # noqa: E402
import comum as K  # noqa: E402
from test_defeitos_v4 import captura_valida, congelamento  # noqa: E402  (fixtures completas herdadas)

# ------------------------------------------------------------------------------------------- ajuste 1
MODELO = r'''
import json, os, sys
sys.path.insert(0, {here!r})
import comum as K
t = K.Travas("teste")
t.permite("codigo", {base!r}, {prefix!r}, {here!r}, somente_leitura=True)
t.permite("saida", {saida!r})
t.permite("comum", {raiz!r}, somente_leitura=True)
t.congela({raiz!r}, {congelado!r})
t.instala()
try:
{acao}
except Exception:
    pass   # consumidor que engole a exceção
t.rehash_leituras()   # conferência final do worker
with open({rel!r}, "w", encoding="utf-8") as fh:
    json.dump([v["tipo"] for v in t.violacoes], fh)
K.encerra(t, ok=True)
'''


def raiz_congelada(tmp_path):
    """Raiz comum sintética com a.txt e b.txt congelados."""
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    (raiz / "a.txt").write_bytes(b"a")
    (raiz / "b.txt").write_bytes(b"b")
    return raiz, {"a.txt": K.sha_bytes(b"a"), "b.txt": K.sha_bytes(b"b")}


def roda(tmp_path, raiz, congelado, acao):
    rel = tmp_path / "saida" / "viol.json"
    rel.parent.mkdir(exist_ok=True)
    src = MODELO.format(here=str(HERE), base=sys.base_prefix, prefix=sys.prefix, saida=str(tmp_path / "saida"),
                        raiz=str(raiz), congelado=congelado, rel=str(rel),
                        acao="\n".join("    " + x for x in acao.strip().splitlines()))
    r = subprocess.run([sys.executable, "-B", "-c", src], capture_output=True, text=True)
    return r.returncode, json.loads(rel.read_text(encoding="utf-8")) if rel.exists() else None, r.stderr


def test_a_congelado_ausente_antes_da_1a_leitura_com_filenotfound_capturado(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    (raiz / "a.txt").unlink()   # some ANTES da primeira leitura
    acao = f"try:\n    open({str(raiz / 'a.txt')!r}).read()\nexcept FileNotFoundError:\n    pass"
    rc, viol, err = roda(tmp_path, raiz, cong, acao)
    assert rc == 2 and "insumo_desaparecido" in viol, (rc, viol, err)


def test_a2_congelado_substituido_por_pasta(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    (raiz / "a.txt").unlink()
    (raiz / "a.txt").mkdir()    # existe, mas não é arquivo utilizável
    rc, viol, err = roda(tmp_path, raiz, cong, f"open({str(raiz / 'a.txt')!r}).read()")
    assert rc == 2 and "insumo_desaparecido" in viol, (rc, viol, err)


def test_b_consumidor_so_consulta_exists_is_file(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    (raiz / "a.txt").unlink()
    acao = f"if not os.path.exists({str(raiz / 'a.txt')!r}) or not os.path.isfile({str(raiz / 'a.txt')!r}):\n    pass"
    rc, viol, err = roda(tmp_path, raiz, cong, acao)
    assert rc == 2 and viol.count("insumo_desaparecido") == 1, (rc, viol, err)


def test_b2_conferencia_de_inventario_antes_do_worker(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    (raiz / "b.txt").unlink()
    (raiz / "a.txt").write_bytes(b"A")
    t = K.Travas("teste")
    t.congela(raiz, cong)
    prob = t.confere_congelados()
    assert len(prob) == 2 and any("b.txt" in p for p in prob) and any("a.txt" in p for p in prob)
    assert sorted(v["tipo"] for v in t.violacoes) == ["insumo_desaparecido", "insumo_divergente"]


def test_c_congelado_nunca_aberto_some_durante_a_execucao(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    acao = f"open({str(raiz / 'a.txt')!r}).read()\nos.remove({str(raiz / 'b.txt')!r})"
    rc, viol, err = roda(tmp_path, raiz, cong, acao)
    assert rc == 2 and viol == ["insumo_desaparecido"], (rc, viol, err)


def test_c2_congelado_nunca_aberto_alterado_durante_a_execucao(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    acao = f"with t._abrir_original({str(raiz / 'b.txt')!r}, 'w') as fh:\n    fh.write('B')"
    rc, viol, err = roda(tmp_path, raiz, cong, acao)
    assert rc == 2 and viol == ["insumo_divergente"], (rc, viol, err)


def test_d_entradas_congeladas_intactas_passam(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    rc, viol, err = roda(tmp_path, raiz, cong, f"open({str(raiz / 'a.txt')!r}).read()")
    assert (rc, viol) == (0, []), err


def test_e_opcional_nunca_congelado_ausente_segue_a_politica_existente(tmp_path):
    raiz, cong = raiz_congelada(tmp_path)
    acao = f"try:\n    open({str(raiz / 'opcional.json')!r}).read()\nexcept FileNotFoundError:\n    pass"
    rc, viol, err = roda(tmp_path, raiz, cong, acao)
    assert (rc, viol) == (0, []), err


# ------------------------------------------------------------------------------------------- ajuste 2
def processo_falso(monkeypatch, tmp_path, dist_atual, **interprete):
    """Todos os demais parâmetros de verifica_processo iguais ao congelado; só as distribuições variam (simuladas)."""
    pyc = tmp_path / "pyc"
    pyc.mkdir()
    monkeypatch.setattr(CP, "PYCACHE", pyc)
    monkeypatch.setattr(CP, "sys", SimpleNamespace(
        flags=SimpleNamespace(dont_write_bytecode=1, no_user_site=1), pycache_prefix=str(pyc),
        path=[str(CP.HERE), str(CP.DATA)], executable="python-fixo", version="3.x-fixo"))
    monkeypatch.setattr(K, "verifica_ambiente", lambda env: [])
    monkeypatch.setattr(K, "verifica_codigo", lambda esperado, arquivos, _abrir=None: [])
    monkeypatch.setattr(K, "arvore", lambda *a, **k: {"m.py": "h"})
    monkeypatch.setattr(CP, "distribuicoes", lambda: list(dist_atual))
    return {"normativo": {"interprete": {"executavel": "python-fixo", "versao": "3.x-fixo", **interprete},
                          "codigo": {}, "produto": {"src_arquivos": {"m.py": "h"}}}}


def test_2c_assinatura_correta_passa(tmp_path, monkeypatch):
    cong = processo_falso(monkeypatch, tmp_path, ["pkg==1.0"], distribuicoes_sha=K.sha_json(["pkg==1.0"]))
    assert CP.verifica_processo(cong) == []


def test_2a_assinatura_divergente_reprova(tmp_path, monkeypatch):
    cong = processo_falso(monkeypatch, tmp_path, ["pkg==2.0"], distribuicoes_sha=K.sha_json(["pkg==1.0"]))
    assert any("distribuições" in p for p in CP.verifica_processo(cong))


@pytest.mark.parametrize("valor", [None, "", "abc", 123, "G" * 64, K.sha_json(["pkg==1.0"]).upper()])
def test_2b_assinatura_invalida_reprova(tmp_path, monkeypatch, valor):
    cong = processo_falso(monkeypatch, tmp_path, ["pkg==1.0"], distribuicoes_sha=valor)
    assert any("distribuições" in p for p in CP.verifica_processo(cong))
    assert cong["normativo"]["interprete"]["distribuicoes_sha"] == valor   # o esperado não é preenchido


def test_2b_assinatura_ausente_reprova(tmp_path, monkeypatch):
    cong = processo_falso(monkeypatch, tmp_path, ["pkg==1.0"])
    assert any("distribuições" in p for p in CP.verifica_processo(cong))
    assert "distribuicoes_sha" not in cong["normativo"]["interprete"]


def test_2d_assinatura_muda_entre_inicio_e_fim_captura_nao_aceita(tmp_path, monkeypatch):
    cong = congelamento(interprete={"distribuicoes_sha": K.sha_json(["pkg==1.0"])})
    monkeypatch.setattr(CP, "CAPS", tmp_path / "capturas")
    monkeypatch.setattr(CP, "FALHAS", tmp_path / "falhas")
    (tmp_path / "capturas").mkdir()
    atual = {"lista": ["pkg==1.0"]}
    monkeypatch.setattr(CP, "distribuicoes", lambda: list(atual["lista"]))
    destino = tmp_path / "capturas" / f"capturar_CRU_{cong['id_comum'][:16]}_{cong['insumos_braco']['CRU'][:16]}.json"

    def worker_falso(cmd, **kw):   # o worker grava uma captura estruturalmente válida; as distribuições mudam no meio
        destino.write_text(json.dumps(captura_valida(cong)), encoding="utf-8")
        atual["lista"] = ["pkg==2.0"]
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(CP.subprocess, "run", worker_falso)
    with pytest.raises(CP.Falha, match="distribuições"):
        CP.roda_worker("CRU", "capturar", cong, K.Travas("teste"))
    assert not destino.exists()                                  # não fica no caminho de reúso
    assert list((tmp_path / "falhas").glob("rejeitada_*.json"))  # preservada como falha


def test_2d_fim_do_worker_confere_distribuicoes(tmp_path, monkeypatch):
    cong = processo_falso(monkeypatch, tmp_path, ["pkg==2.0"], distribuicoes_sha=K.sha_json(["pkg==1.0"]))
    assert any("distribuições" in p for p in CP.verifica_fim(cong))
