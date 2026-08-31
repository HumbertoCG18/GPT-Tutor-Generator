"""Nucleo char-level do detector de duplicatas: a normalizacao que iguala
extracoes divergentes do MESMO documento (caso real SO plano-de-ensino vs
programa: ****x**** vs **x**, descricoes de imagem, ancoras {N}---)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from detecta_duplicatas import _texto_normalizado


def _repo_com_md(tmp_path: Path, conteudos: dict) -> Path:
    repo = tmp_path / "X-Tutor"
    (repo / "content").mkdir(parents=True)
    entries = []
    for eid, md in conteudos.items():
        rel = f"content/{eid}.md"
        (repo / rel).write_text(md, encoding="utf-8")
        entries.append({"id": eid, "base_markdown": rel})
    (repo / "manifest.json").write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return repo


def test_extracoes_divergentes_do_mesmo_doc_normalizam_igual(tmp_path):
    base = "EMENTA: Conceitos de sistemas operacionais. Processos e threads. " * 8
    a = f"# Sumário\n<!-- EXEC_SUMMARY -->\n- ****{base}****\n{{0}}------------------\n"
    b = (f"# Sumário\n- **{base}**\n{{1}}------------------\n"
         "> **[Descrição de imagem]** Brasão da PUCRS\n"
         "<!-- IMAGE_DESCRIPTION_ORPHANS -->\nlixo de outro material\n")
    repo = _repo_com_md(tmp_path, {"a": a, "b": b})
    ta = _texto_normalizado(repo, {"id": "a", "base_markdown": "content/a.md"})
    tb = _texto_normalizado(repo, {"id": "b", "base_markdown": "content/b.md"})
    assert ta and ta == tb


def test_documentos_diferentes_nao_colidem(tmp_path):
    a = "EMENTA: sistemas operacionais, processos, escalonamento e memoria. " * 8
    b = "Roteiro de laboratorio: configure o container e suba o compose. " * 8
    repo = _repo_com_md(tmp_path, {"a": a, "b": b})
    ta = _texto_normalizado(repo, {"id": "a", "base_markdown": "content/a.md"})
    tb = _texto_normalizado(repo, {"id": "b", "base_markdown": "content/b.md"})
    assert ta != tb
