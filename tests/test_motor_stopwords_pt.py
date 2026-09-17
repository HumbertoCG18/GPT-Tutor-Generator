import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.motor.disambiguator import _toks


def test_palavras_funcao_pt_nao_sao_tokens():
    # 'nao' era o unico discriminante do cw aula-01 (investigacao 2026-08-05 §2a)
    toks = _toks("conjuntos enumeraveis e nao enumeraveis")
    assert "nao" not in toks
    assert "conjuntos" in toks and "enumeraveis" in toks


def test_lista_conservadora_completa():
    for w in ("nao", "sim", "com", "sem", "por", "dos", "das", "nos", "nas", "uma", "que"):
        assert w not in _toks(f"conteudo {w} conteudo"), w


def test_tokens_de_dominio_preservados():
    toks = _toks("verificacao de modelos logica temporal")
    assert {"verificacao", "modelos", "logica", "temporal"} <= toks
