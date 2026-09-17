"""Validação end-to-end da pipeline de referências (rede + Gemini REAIS).

Exercita o caminho feliz que os testes unitários nunca cobrem: fetch real
(README do GitHub + texto de doc HTML) -> resumo Gemini real -> mapeamento
determinístico -> persistência em references_curation.json.

Pré-requisitos:
- GEMINI_API_KEY no .env (ou config da UI). Carregado em os.environ no import.
- Rede liberada (api.github.com + docs.python.org).

Uso:
    python scripts/validate_references_e2e.py

Sai 0 se cada referência teve resumo Gemini real preenchido; 1 caso contrário.
Cria tudo em diretório temporário — não polui o repo.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Garante src no path quando rodado da raiz do repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Importar helpers dispara _load_project_env_file (carrega .env em os.environ),
# espelhando o que o build real faz cedo no import.
import src.utils.helpers  # noqa: E402,F401

from src.builder.core.reference_summary import (  # noqa: E402
    load_reference_curation,
    summarize_all_reference_entries,
)
from src.builder.runtime.gemini_client import (  # noqa: E402
    get_gemini_client,
    has_gemini_api_key,
)


class _BuilderStub:
    """Entrada mínima do pipeline: só root_dir é consumido."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir


# Duas referências reais, categorias distintas (ambas processadas).
_REF_ENTRIES = [
    {
        "id": "ref-flask",
        "title": "Flask",
        "category": "referencias",
        "file_type": "github-repo",
        "source_path": "https://github.com/pallets/flask",
    },
    {
        "id": "ref-json-doc",
        "title": "json — JSON encoder and decoder",
        "category": "bibliografia",
        "file_type": "link",
        "source_path": "https://docs.python.org/3/library/json.html",
    },
]

# Índice de unidades realista: as refs devem cair em unidades distintas.
_UNITS = [
    {
        "slug": "web",
        "normalized_title": "desenvolvimento web",
        "topic_phrases": ["desenvolvimento web", "rotas http"],
        "topic_tokens": ["flask", "rotas", "http", "servidor", "aplicacao", "web", "framework"],
        "distinctive_tokens": ["wsgi", "jinja", "blueprint"],
    },
    {
        "slug": "serializacao",
        "normalized_title": "serializacao de dados",
        "topic_phrases": ["serializacao de dados"],
        "topic_tokens": ["json", "serializacao", "dados", "parsing", "encode", "decode", "objeto"],
        "distinctive_tokens": ["dumps", "loads", "schema"],
    },
]


def _progress(idx, total, title, status):
    print(f"  [{idx + 1}/{total}] {status:<8} {title}")


def main() -> int:
    if not has_gemini_api_key(None):
        print("FALHA: GEMINI_API_KEY ausente (.env/ambiente). Configure antes de rodar.")
        return 1

    client = get_gemini_client(None)
    if client is None:
        print("FALHA: get_gemini_client retornou None apesar de chave presente.")
        return 1
    print(f"Client Gemini OK (model={client.model}).")

    with tempfile.TemporaryDirectory(prefix="ref-e2e-") as tmp:
        root = Path(tmp)
        manifest = {"entries": _REF_ENTRIES}
        (root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print("\nRodando pipeline real (fetch + Gemini + mapa + persistência)...")
        summarize_all_reference_entries(_BuilderStub(root), _UNITS, client, progress_cb=_progress)

        curation = load_reference_curation(root)
        entries = curation.get("entries", {})

        print("\n=== references_curation.json ===")
        ok = True
        for eid in (e["id"] for e in _REF_ENTRIES):
            rec = entries.get(eid, {})
            summary = (rec.get("ref_summary") or "").strip()
            concepts = rec.get("ref_concepts") or []
            unit = rec.get("computed_ref_unit") or "(nenhuma)"
            topics = rec.get("computed_ref_topics") or []
            print(f"\n[{eid}]")
            print(f"  unidade : {unit}")
            print(f"  tópicos : {topics}")
            print(f"  conceitos: {concepts}")
            print(f"  resumo  : {summary[:300]}{'...' if len(summary) > 300 else ''}")
            if not summary or not concepts:
                print("  -> SEM resumo/conceitos Gemini (caminho feliz NÃO validado)")
                ok = False

        print("\n" + ("RESULTADO: OK — Gemini real preencheu todas as referências."
                       if ok else "RESULTADO: FALHA — alguma referência ficou sem resumo Gemini."))
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
