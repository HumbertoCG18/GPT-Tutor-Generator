# tests/test_glossary_evidencia.py
"""Evidencia do glossario (2026-08-26). Censo nos 5 cursos ANTES: 73/132 definicoes
genericas, 49 "de esta unidade", 10 com lixo (texto do plano / TOC do EXEC_SUMMARY).
(1) docs META (plano/programa/apresentacao) saem da evidencia — por CONTEUDO, citam
quase todos os titulos de unidade; (2) o bloco EXEC_SUMMARY sai antes de extrair
frases/headings; (3) "Conceito central desta unidade"."""
import json

from src.builder import engine
from src.models.core import SubjectProfile

PLAN = """
Unidade 01: Introdução ao estudo de sistemas operacionais
1.2 Chamadas de sistema

Unidade 02: Gerência do Processador
3.2 Escalonamento
"""


def _repo(tmp_path):
    cur = tmp_path / "content" / "curated"; cur.mkdir(parents=True); (tmp_path / "course").mkdir()
    (cur / "plano-de-ensino.md").write_text(
        "# Plano de Ensino\nCONTEÚDOS: Unidade 01: Introdução ao estudo de sistemas operacionais. "
        "Chamadas de sistema são apresentadas no plano. Unidade 02: Gerência do Processador. Escalonamento.\n",
        encoding="utf-8")
    (cur / "aula-syscalls.md").write_text(
        "<!-- EXEC_SUMMARY_START -->\n## Sumário\n> *Leia antes de varrer o arquivo.*\n- **Chamadas de sistema em Linux**\n<!-- EXEC_SUMMARY_END -->\n"
        "# Chamadas de sistema em Linux\n\nAs chamadas de sistema são a interface pela qual um processo solicita serviços ao núcleo do sistema operacional.\n",
        encoding="utf-8")
    entries = [{"id": "plano-de-ensino", "title": "Plano de Ensino", "curated_markdown": "content/curated/plano-de-ensino.md"},
               {"id": "aula-syscalls", "title": "Chamadas de sistema", "curated_markdown": "content/curated/aula-syscalls.md"}]
    return tmp_path, entries


def test_doc_meta_e_exec_summary_nao_viram_definicao(tmp_path):
    root, entries = _repo(tmp_path)
    sp = SubjectProfile(name="SO", slug="so", teaching_plan=PLAN)
    text = engine.glossary_md({"course_name": "SO"}, sp, root_dir=root, manifest_entries=entries)
    bloco = text.split("## 1.2 Chamadas de sistema")[1].split("## ")[0]
    assert "interface pela qual um processo solicita serviços" in bloco   # evidencia real
    assert "CONTEÚDOS" not in bloco and "Plano de Ensino" not in bloco      # plano nao e evidencia
    assert "Sumário" not in bloco and "Leia antes" not in bloco             # TOC injetado nao e evidencia


def test_generico_diz_desta_unidade():
    sp = SubjectProfile(name="SO", slug="so", teaching_plan=PLAN)
    text = engine.glossary_md({"course_name": "SO"}, sp)
    assert "de esta unidade" not in text
    assert "Conceito central desta unidade" in text


def test_headings_e_ruido_de_extracao_nao_sao_definicao(tmp_path):
    cur = tmp_path / "content" / "curated"; cur.mkdir(parents=True); (tmp_path / "course").mkdir()
    (cur / "aula-escalonamento.md").write_text(
        "# Escalonamento de Processos\n## Definição (1)\n## Definição (2)\n## Troca de Contexto\n"
        "{0}------------------------------------------------ # Escalonamento de Processos Miguel Gomes Xavier Sistemas Operacionais 2026\n"
        "Curta.\n",
        encoding="utf-8")
    entries = [{"id": "aula-escalonamento", "title": "Escalonamento", "curated_markdown": "content/curated/aula-escalonamento.md"}]
    sp = SubjectProfile(name="SO", slug="so", teaching_plan=PLAN)
    text = engine.glossary_md({"course_name": "SO"}, sp, root_dir=tmp_path, manifest_entries=entries)
    bloco = text.split("## 3.2 Escalonamento")[1].split("## ")[0]
    assert "Definição (1)" not in bloco and "----" not in bloco and "Miguel" not in bloco
    assert "Conceito central" in bloco   # sem frase real -> generico honesto
