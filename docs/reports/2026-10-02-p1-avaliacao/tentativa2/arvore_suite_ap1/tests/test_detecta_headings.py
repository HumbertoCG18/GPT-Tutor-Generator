"""Nucleo de matching do detector de headings: contencao nos DOIS sentidos
(caso real ES2 `devops`: heading "DevOps" e mais curto que o label "Conceito
de DevOps" e nao casava na versao so label-no-heading), com piso de chars
para nao casar por token estrutural curto."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from detecta_headings import _casa, audita_curso
from src.builder.text.normalize import normalize_match_text


def test_casa_nos_dois_sentidos():
    label = normalize_match_text("Conceito de DevOps")
    assert _casa(label, normalize_match_text("DevOps"), 5)          # heading curto contido no label
    assert _casa(label, normalize_match_text("O Conceito de DevOps na pratica"), 5)  # label contido
    assert not _casa(normalize_match_text("Web"), label, 5)         # contido < min_chars nao casa
    assert not _casa("", label, 5)


def _repo(tmp_path: Path, md: str, atribuida: str) -> Path:
    repo = tmp_path / "X-Tutor"
    (repo / "content").mkdir(parents=True)
    (repo / "course").mkdir()
    (repo / "content" / "e1.md").write_text(md, encoding="utf-8")
    (repo / "manifest.json").write_text(json.dumps({"entries": [{
        "id": "e1", "computed_unit_slug": "u1", "computed_subunit_slug": atribuida,
        "base_markdown": "content/e1.md",
    }]}), encoding="utf-8")
    (repo / "course" / ".content_taxonomy.json").write_text(json.dumps({"units": [{
        "slug": "u1", "topics": [
            {"slug": "cliente-servidor", "label": "Arquitetura Cliente-Servidor"},
            {"slug": "serverless", "label": "Arquitetura Serverless"},
        ],
    }]}), encoding="utf-8")
    return repo


def test_flaga_irma_em_heading_com_atribuida_ausente(tmp_path):
    # Caso real ES2 `web`: headings citam cliente-servidor, atribuida=serverless.
    repo = _repo(tmp_path, "# Arquitetura Cliente-Servidor\n\ncorpo\n", "serverless")
    suspeitos = audita_curso(repo, 5)
    assert [s["id"] for s in suspeitos] == ["e1"]
    assert suspeitos[0]["irmas_em_heading"] == ["cliente-servidor"]


def test_nao_flaga_quando_atribuida_aparece_em_heading(tmp_path):
    md = "# Arquitetura Serverless\n\n# Arquitetura Cliente-Servidor\n"
    repo = _repo(tmp_path, md, "serverless")
    assert audita_curso(repo, 5) == []
