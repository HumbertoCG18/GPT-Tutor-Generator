"""tipo_of = FILE_TYPE puro (padrao consistente entre cursos).

Bug 2026-07-01: a cascata de keyword no nome fazia 'ProvasIndutivas' (demonstracao
matematica) virar tipo='prova' (exame) e sobrescrevia o file_type correto. Em MF
"prova" = proof, nao exame. tipo deve ser file_type (pdf/codigo/...), nao keyword.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_gold_xlsx import tipo_of


def test_proof_pdf_vira_pdf_nao_prova():
    assert tipo_of({"title": "ProvasIndutivas_EspecificacoesRecursivas", "file_type": "pdf"}) == "pdf"


def test_isabelle_thy_vira_codigo_nao_prova():
    assert tipo_of({"title": "provas", "file_type": "code"}) == "código"


def test_exercicios_pdf_vira_pdf_nao_lista():
    assert tipo_of({"title": "ExerciciosConjuntosIndutivos", "file_type": "pdf"}) == "pdf"


def test_filetypes_basicos():
    assert tipo_of({"file_type": "pdf"}) == "pdf"
    assert tipo_of({"file_type": "zip"}) == "código"
    assert tipo_of({"file_type": "code"}) == "código"
    assert tipo_of({"file_type": "url"}) == "link"
    assert tipo_of({"file_type": "image"}) == "imagem"


def test_sem_filetype_vira_material():
    assert tipo_of({"title": "algo"}) == "material"
