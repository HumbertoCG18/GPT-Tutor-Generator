"""Produtor deterministico de code_curation.json (determ v3, 11/09): substitui o resumo de codigo por Gemini (camada 3).
Medido em copias: subunidade 142/151 com zips corrigidos, contra 137 do Gemini (c1-3/codigo_determ_puro_e.log)."""
import json
from types import SimpleNamespace

from src.builder.core.code_summarization import (
    load_code_curation, synthesize_all_code_entries, synthesize_code_entry,
)


def _repo(tmp_path):
    root = tmp_path / "repo"
    (root / "course").mkdir(parents=True)
    (root / "code" / "professor").mkdir(parents=True)
    (root / "course" / ".content_taxonomy.json").write_text(json.dumps({"units": [{"slug": "u2", "title": "U2", "topics": [
        {"slug": "filas", "label": "Comunicacao por filas", "aliases": ["RabbitMQ", "Circuit Breaker"]}]}]}), encoding="utf-8")
    (root / "code/professor/roteiro7-rabbitmqconfig.md").write_text(
        "---\nentry_id: x\n---\n# roteiro7/RabbitMQConfig.java\n\n> **Linguagem:** java\n\n```java\n"
        "// configura o circuit breaker fallback\npublic class RabbitMQConfig {\n  Queue historyQueue;\n}\n```\n", encoding="utf-8")
    (root / "code/professor/solto.md").write_text("# solto.py\n```python\nprint(1)\n```\n", encoding="utf-8")
    zipe = {"id": "roteiro7", "file_type": "zip", "category": "codigo-professor", "title": "Roteiro 7", "moodle_label": "Filas",
            "base_markdown": None, "extracted_files": [
                {"title": "roteiro7\\RabbitMQConfig.java", "base_markdown": "code/professor/roteiro7-rabbitmqconfig.md"}]}
    solto = {"id": "solto", "file_type": "code", "category": "codigo-professor", "title": "solto.py",
             "base_markdown": "code/professor/solto.md"}
    (root / "manifest.json").write_text(json.dumps({"entries": [zipe, solto]}), encoding="utf-8")
    return root, zipe, solto


def test_zip_ganha_resumo_com_alias_em_identificador_e_em_frase(tmp_path):
    root, zipe, _ = _repo(tmp_path)
    s = synthesize_code_entry(zipe, root, aliases={"RabbitMQ", "Circuit Breaker"})
    assert s["language"] == "java"
    assert "RabbitMQ" in s["concepts"] and "Circuit Breaker" in s["concepts"]   # alias, nao 'rabbit' + 'config'
    assert s["inferred_title"].startswith("Filas") and "configura o circuit breaker fallback" in s["summary"]


def test_codigo_com_md_proprio_nao_ganha_resumo(tmp_path):
    root, _, solto = _repo(tmp_path)
    assert synthesize_code_entry(solto, root, aliases=set()) is None   # o leitor ja entrega o .md; duplicar piorava o MF


def test_synthesize_all_reescreve_code_curation_e_apaga_resumo_gemini_de_codigo_solto(tmp_path):
    root, _, _ = _repo(tmp_path)
    (root / "code_curation.json").write_text(json.dumps({"version": 1, "entries": {
        "solto": {"summary": {"inferred_title": "gemini"}, "model": "gemini-3.5-flash", "content_hash": "x"}}}), encoding="utf-8")
    cur = synthesize_all_code_entries(SimpleNamespace(root_dir=root))
    assert set(cur["entries"]) == {"roteiro7"}
    assert cur["entries"]["roteiro7"]["model"] == "determ-v3"
    assert "RabbitMQ" in load_code_curation(root)["entries"]["roteiro7"]["summary"]["concepts"]
