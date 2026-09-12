import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_gold_freshness as ag  # noqa: E402


def test_lista_de_prova_reconhecida_pelo_pair_key():
    assert ag._looks_like_assessment("lista2.pdf", "lista-exercicios-p2") is True


def test_titulo_de_prova_segue_reconhecido():
    assert ag._looks_like_assessment("prova.pdf", "") is True


def test_material_comum_segue_admin_true():
    assert ag._looks_like_assessment("lista2.pdf", "") is False
    assert ag._looks_like_assessment("aula-processos.pdf", "listas-gerais") is False
