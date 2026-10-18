"""#64: registro, por execução da atribuição, do que foi pedido, do que valeu, do que rodou e do fallback.

Gravado em manifest["assignment_run"] a cada regeneração (sobrescreve o da execução anterior);
manifest["options"] segue como registro histórico da criação do repositório e não é tocado.
"""
from __future__ import annotations

from datetime import datetime

from src.builder.routing.file_map import resolve_effective_block

# Default de cada camada quando a flag está ausente das options (fonte única dos gates).
FLAG_DEFAULTS = {
    "use_concept_resolver": True,
    "use_anchor_engine": False,
    "use_llm_voter": False,
    "compile_vocabulary": False,
    "enable_material_residual": False,
}


def new_run(options: dict) -> dict:
    options = options or {}
    return {
        "at": datetime.now().isoformat(timespec="seconds"),
        "requested": {k: options[k] for k in FLAG_DEFAULTS if k in options},
        "effective": {k: bool(options.get(k, default)) for k, default in FLAG_DEFAULTS.items()},
        "executed": {k: False for k in FLAG_DEFAULTS},
        "fallback": {},
        "detail": {},
    }


def mark(run, flag: str, fallback: str = "") -> None:
    """Sem `fallback`: a camada rodou. Com `fallback`: estava ligada e não rodou, pelo motivo dado
    (ignorado para camada desligada)."""
    if run is None:
        return
    if not fallback:
        run["executed"][flag] = True
    elif run["effective"].get(flag):
        run["fallback"][flag] = fallback


def note(run, flag: str, detail: dict, *, partial: bool = False) -> None:
    """Contadores internos da camada; `partial` = rodou, mas parte do trabalho caiu no fallback interno."""
    if run is None:
        return
    run["detail"][flag] = detail
    if partial:
        run["fallback"][flag] = "partial"


def finish_run(run: dict, entries: list, blocks: list) -> dict:
    """Fecha o registro: camada ligada sem marca vira fallback `not_run`; conta a origem do bloco temporal."""
    for flag, on in run["effective"].items():
        if on and not run["executed"][flag]:
            run["fallback"].setdefault(flag, "not_run")
    temporal_key = "temporal_block_id" if run["executed"]["use_anchor_engine"] else "temporal_block_id_previous_run"
    source = {temporal_key: 0, "manual_timeline_block_id": 0, "computed_block_id": 0, "none": 0}
    for entry in entries:
        if str(entry.get("temporal_block_id") or "").strip():
            source[temporal_key] += 1
            continue
        origin = resolve_effective_block(entry, blocks).source
        source[{"manual": "manual_timeline_block_id", "auto": "computed_block_id"}.get(origin, "none")] += 1
    run["block_source"] = source
    return run
