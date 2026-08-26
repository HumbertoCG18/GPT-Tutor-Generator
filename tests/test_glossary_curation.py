# tests/test_glossary_curation.py
"""Alavanca (iii) da subunidade (2026-08-25): sinonimos curados em
`course/.glossary_curation.json` entram no GLOSSARY.md gerado e viram alias
do topico na taxonomia. O .md e derivado (regravado a cada build); a
taxonomia consome o TEXTO gerado — curadoria no .md morria no proximo build."""
import json

from src.builder import engine
from src.builder.artifacts.repo import merge_glossary_synonyms
from src.models.core import SubjectProfile

PLAN = """
Unidade de Aprendizagem 5: Aprendizado de máquina (30%)
Introdução ao aprendizado de máquina
Paradigmas de aprendizado
Modelos Preditivos
Modelos Descritivos
Métricas de Avaliação
"""


def _repo(tmp_path, curation):
    (tmp_path / "course").mkdir()
    (tmp_path / "course" / ".glossary_curation.json").write_text(json.dumps(curation, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_merge_sem_repetir_e_sem_marcador_vazio():
    assert merge_glossary_synonyms("modelos supervisionados", ["perceptron", "Modelos Supervisionados", "k-NN"]) == "modelos supervisionados, perceptron, k-NN"
    assert merge_glossary_synonyms("—", ["k-means"]) == "k-means"
    assert merge_glossary_synonyms("—", []) == "—"


def test_curadoria_entra_no_glossario_gerado_e_vira_alias_do_topico(tmp_path):
    root = _repo(tmp_path, {"Modelos Preditivos": {"synonyms": ["perceptron", "árvore de decisão"]},
                            "Modelos Descritivos": {"synonyms": ["k-means"]}})
    sp = SubjectProfile(name="IA", slug="ia", teaching_plan=PLAN)
    text = engine.glossary_md({"course_name": "IA"}, sp, root_dir=root)
    assert "**Sinônimos aceitos:** modelos supervisionados, perceptron, árvore de decisão" in text
    tax = engine._build_content_taxonomy(PLAN, "", text)
    by_slug = {t["slug"]: t for u in tax["units"] for t in u["topics"]}
    assert "perceptron" in by_slug["modelos-preditivos"]["aliases"]
    assert "k-means" in by_slug["modelos-descritivos"]["aliases"]
    assert "perceptron" not in by_slug["modelos-descritivos"]["aliases"]


def test_sem_sidecar_e_byte_identico(tmp_path):
    sp = SubjectProfile(name="IA", slug="ia", teaching_plan=PLAN)
    (tmp_path / "course").mkdir()
    assert engine.glossary_md({"course_name": "IA"}, sp, root_dir=tmp_path) == engine.glossary_md({"course_name": "IA"}, sp)
