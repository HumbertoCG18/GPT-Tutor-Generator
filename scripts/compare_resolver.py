"""Harness read-only: roda o resolver novo (Fase 2.2) sobre os materiais de um
repo gerado REAL e compara com a resposta do funil (computed_block_id ja no
manifest). NAO escreve no repo, NAO chama API (so le code_curation.json).

Uso:
    python scripts/compare_resolver.py "<repo>" ["<repo2>" ...]
    python scripts/compare_resolver.py            # roda os 5 cursos default

O `signals` e montado pelo MESMO caminho que o BLOCK scorer da producao
(file_map._select_probable_period_for_entry -> collect_entry_unit_signals com
markdown CRU de _entry_markdown_text_for_file_map). Para codigo/zip sem .md o
markdown cai vazio — IGUAL ao funil; NAO injetamos o surrogate
code_curation_signal_text (o funil so o usa na rota de subunit/topico, nunca no
scorer de bloco) e NAO mesclamos known_tools em tool_tags_text (a producao nunca
injeta).

ATENCAO — a comparacao NAO e like-for-like: o resolver le os `concepts` do
Gemini (injetados em entry["concepts"], canal LLM-first-class por design) + o
voto LLM (`summary` da curation: primary/secondary/confidence). O funil (oraculo
= computed_block_id ja no manifest) NAO le esses concepts no scorer de bloco.
Logo: "resolver-COM-concepts-do-LLM vs funil-SEM".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.builder.routing.concept_resolver import resolve_material_assignment  # noqa: E402
from src.builder.routing.resolver_apply import _is_material, assemble_resolver_inputs, load_lessons_index  # noqa: E402
from src.builder.routing.sequence import annotate_class_ordinals  # noqa: E402

DEFAULT_COURSES = [
    "Engenharia-Software-2-Tutor",
    "Inteligencia-Artifical-Tutor",
    "Metodos-Formais-Tutor",
    "Sistemas-Operacionais-Tutor",
    "TCC-Tutor",
]
GITHUB_DIR = Path(r"C:\Users\Humberto\Documents\GitHub")

# Alvos da Fase 2 (brief): id da entry -> bloco que o resolver DEVE eleger.
FIX_TARGETS = {
    "arvores": "bloco-05",
    "intro": "bloco-04",
    "listas": "bloco-05",
    "classes-parte1": "bloco-15",
}
NOREGRESS_TARGETS = {
    "colecoes-arrays": "bloco-13",
    "colecoes-conjuntos": "bloco-13",
    "colecoes-sequences": "bloco-13",
    "invariantes": "bloco-11",
    "terminacao": "bloco-11",
    "hoare": "bloco-10",
    "exercicios-conjuntos": "bloco-13",
}


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _funil_unit(entry: dict) -> str:
    return str(
        entry.get("computed_unit_slug")
        or entry.get("manual_unit_slug")
        or entry.get("unit_slug")
        or ""
    )


def _inject_block_uuids_from_ledger(blocks: List[dict], ledger: List[dict]) -> None:
    """Injeta block_uuid nos blocos do timeline via ledger (display_id_last -> uuid).

    Usado quando o .timeline_index.json ainda nao foi rebuilt com block_uuid
    (ex: MF antes do proximo rebuild). Nao sobrescreve block_uuid ja presente.
    """
    by_display: Dict[str, str] = {
        str(rec.get("display_id_last") or ""): str(rec.get("uuid") or "")
        for rec in (ledger or [])
        if rec.get("display_id_last") and rec.get("uuid")
    }
    for block in blocks:
        if block.get("block_uuid"):
            continue
        display_id = str(block.get("id") or "")
        uuid = by_display.get(display_id)
        if uuid:
            block["block_uuid"] = uuid


def compare_repo(root: Path) -> Optional[dict]:
    manifest = _load_json(root / "manifest.json")
    if not manifest:
        return None
    timeline = _load_json(root / "course" / ".timeline_index.json") or {}
    taxonomy = _load_json(root / "course" / ".content_taxonomy.json") or {}
    curation = _load_json(root / "code_curation.json") or {"entries": {}}

    blocks = list(timeline.get("blocks") or [])
    units = list(taxonomy.get("units") or [])
    if not blocks:
        return {"error": "sem blocos em course/.timeline_index.json"}
    annotate_class_ordinals(blocks)
    lessons_index = load_lessons_index(root)

    # Injeta block_uuid do ledger nos blocos que ainda nao o tem (pre-rebuild).
    ledger_path = root / "course" / ".block_identity.json"
    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            _inject_block_uuids_from_ledger(blocks, ledger if isinstance(ledger, list) else [])
        except Exception:
            pass

    entries = [e for e in (manifest.get("entries") or []) if _is_material(e)]
    rows: List[dict] = []
    for entry in entries:
        entry_id = str(entry.get("id") or "")
        funil_block = str(entry.get("computed_block_id") or "")
        if not funil_block:
            continue
        # assemble_resolver_inputs (DRY): mesma logica do helper de producao.
        # "resolver-COM-concepts-do-LLM vs funil-SEM" — ver caveat no docstring
        # do modulo.
        entry_for_resolver, signals, summary = assemble_resolver_inputs(root, entry, curation)
        assignment = resolve_material_assignment(
            entry_for_resolver,
            blocks,
            units,
            signals=signals,
            llm_curation=summary or None,
            lessons_index=lessons_index,
        )
        rows.append({
            "id": entry_id,
            "funil_block": funil_block,
            "resolver_block": assignment["block_id"],
            "changed": assignment["block_id"] != funil_block,
            "funil_unit": _funil_unit(entry),
            "resolver_unit": assignment["unit_slug"],
            "conflict": assignment["conflict"] is not None,
            "funil_band": str(entry.get("computed_block_band") or ""),
            "resolver_band": assignment["band"],
            "method": assignment["method"],
        })
    return {"rows": rows, "n_blocks": len(blocks), "n_units": len(units)}


def _render_table(rows: List[dict]) -> str:
    head = (
        "| id | funil | resolver | mudou | funil_unit | resolver_unit | "
        "conflito | band f->r |"
    )
    sep = "|" + "|".join(["---"] * 8) + "|"
    out = [head, sep]
    for r in sorted(rows, key=lambda x: (not x["changed"], x["id"])):
        out.append(
            f"| {r['id']} | {r['funil_block']} | {r['resolver_block']} | "
            f"{'SIM' if r['changed'] else '-'} | {r['funil_unit']} | "
            f"{r['resolver_unit']} | {'SIM' if r['conflict'] else '-'} | "
            f"{r['funil_band']}->{r['resolver_band']} |"
        )
    return "\n".join(out)


def _check_targets(rows: List[dict]) -> str:
    by_id: Dict[str, dict] = {r["id"]: r for r in rows}
    lines = ["### Alvos da Fase 2 (corpus real)", "", "**4 que DEVEM mudar (funil errado -> resolver certo):**"]
    for eid, want in FIX_TARGETS.items():
        r = by_id.get(eid)
        if not r:
            lines.append(f"- {eid}: AUSENTE no repo")
            continue
        ok = r["resolver_block"] == want and r["changed"]
        lines.append(
            f"- {eid}: funil={r['funil_block']} resolver={r['resolver_block']} "
            f"(esperado {want}) -> {'OK' if ok else 'FALHOU'}"
        )
    lines.append("")
    lines.append("**6+ que NAO podem regredir (funil ja certo):**")
    for eid, want in NOREGRESS_TARGETS.items():
        r = by_id.get(eid)
        if not r:
            lines.append(f"- {eid}: AUSENTE no repo")
            continue
        ok = r["resolver_block"] == want and not r["changed"]
        lines.append(
            f"- {eid}: funil={r['funil_block']} resolver={r['resolver_block']} "
            f"(esperado {want}, inalterado) -> {'OK' if ok else 'FALHOU'}"
        )
    return "\n".join(lines)


def _summary(rows: List[dict], n_blocks: int, n_units: int) -> str:
    changed = [r for r in rows if r["changed"]]
    conflicts = [r for r in rows if r["conflict"]]
    return (
        f"Materiais: {len(rows)} | Blocos: {n_blocks} | Unidades: {n_units}\n"
        f"Blocos mudados (resolver != funil): {len(changed)}\n"
        f"Conflitos flagados (block-unit != topic-unit): {len(conflicts)}"
    )


_COMPARISON_CAVEAT = (
    "_Comparacao NAO like-for-like: resolver-COM-concepts-do-LLM "
    "(entry[\"concepts\"] do Gemini + voto LLM) vs funil-SEM (o oraculo "
    "computed_block_id nao le esses concepts no scorer de bloco)._"
)


def render_repo(name: str, result: dict) -> str:
    parts = [f"## {name}", ""]
    if result.get("error"):
        parts.append(f"ERRO: {result['error']}")
        return "\n".join(parts)
    rows = result["rows"]
    parts.append(_COMPARISON_CAVEAT)
    parts.append("")
    parts.append(_summary(rows, result["n_blocks"], result["n_units"]))
    parts.append("")
    parts.append(_render_table(rows))
    parts.append("")
    parts.append(_check_targets(rows))
    return "\n".join(parts)


def main(argv: List[str]) -> int:
    repos = argv[1:] if len(argv) > 1 else [str(GITHUB_DIR / c) for c in DEFAULT_COURSES]
    sections: List[str] = []
    for repo in repos:
        root = Path(repo)
        name = root.name
        result = compare_repo(root)
        if result is None:
            print(f"[skip] {name}: sem manifest.json em {root}")
            continue
        section = render_repo(name, result)
        sections.append(section)
        print(section)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))