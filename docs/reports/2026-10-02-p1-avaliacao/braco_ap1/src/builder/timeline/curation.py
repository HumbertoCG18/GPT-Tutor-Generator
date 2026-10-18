"""Curation store para overrides manuais de blocos do cronograma.

Persiste em `course/.timeline_curation.json`, separado do `.timeline_index.json`
(que e regenerado a cada build a partir do SYLLABUS). O builder faz merge por
`block_id` antes de serializar, entao o override sobrevive ao rebuild.

Formato:
    {
      "version": 1,
      "boundary_dates": ["2026-03-19", "2026-04-14"],
      "blocks": {
        "bloco-03": {"manual_kind_override": "holiday"},
        "bloco-07": {"manual_topic_label": "Indução estrutural"},
        "bloco-12": {"manual_unit_slug": "unidade-03-indecidibilidade"}
      }
    }

`boundary_dates` (opcional, curso-scoped, formato "YYYY-MM-DD"): override de
FRONTEIRA na segmentação (`_build_timeline_index`), não de bloco já fechado.
Uma linha cuja data está na lista nunca funde com a anterior — força início
de bloco novo ali, mesmo que a regra textual de fusão diria "mesmo tema".
Precisa ser curso-scoped (não block_uuid-scoped) porque o uuid só existe
depois que os blocos já foram fechados (`reattach_block_uuids`), tarde
demais para influenciar o agrupamento. Ausente/vazio -> raio zero.

Modulo puro: so le/grava/merge campos crus. A re-derivacao de `kind`/topic
(que depende do classifier) acontece em quem chama, evitando ciclo de import.

NOTA: o override de unidade em escopo BLOCO (bloco -> unidade) e persistido em
disco como `manual_unit_slug` (formato historico do .timeline_curation.json,
mantido por compat). Ao fazer merge no bloco em memoria, ele e injetado sob a
chave renomeada `block_manual_unit_slug` para nao colidir com
`FileEntry.manual_unit_slug` (arquivo -> unidade, em manifest.json). Mesmo
conceito, escopos diferentes; o rename desfaz a colisao de nome no bloco.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, Optional

logger = logging.getLogger(__name__)

CURATION_FILENAME = ".timeline_curation.json"
_CURATION_VERSION = 1
_OVERRIDE_FIELDS = (
    "manual_kind_override",
    "manual_topic_label",
    "manual_unit_slug",
    "manual_scope_unit_slugs",
)

# Override em escopo de bloco persistido como `manual_unit_slug`, mas injetado no
# bloco em memoria sob esta chave renomeada (desfaz a colisao com o campo
# entry-scoped `FileEntry.manual_unit_slug`).
_BLOCK_FIELD_RENAMES = {
    "manual_unit_slug": "block_manual_unit_slug",
    "manual_scope_unit_slugs": "block_manual_scope_slugs",
}


def _curation_path(course_dir: Path) -> Path:
    return Path(course_dir) / CURATION_FILENAME


def load_block_curation(course_dir: Path) -> Dict[str, dict]:
    """Retorna {block_id: {campo: valor}}. {} se ausente ou corrompido."""
    path = _curation_path(course_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    blocks = data.get("blocks") if isinstance(data, dict) else None
    return blocks if isinstance(blocks, dict) else {}


def set_block_override(
    course_dir: Path,
    block_id: str,
    field: str,
    value: Optional[str | list],
) -> None:
    """Persiste um override. `value` vazio/None remove o campo (e a entrada
    do bloco, se ficar vazia). Idempotente."""
    if field not in _OVERRIDE_FIELDS:
        raise ValueError(f"campo de curation invalido: {field!r}")
    block_id = str(block_id or "").strip()
    if not block_id:
        return

    path = _curation_path(course_dir)
    data: Dict[str, object] = {"version": _CURATION_VERSION, "blocks": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("blocks"), dict):
                data = loaded
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    blocks: Dict[str, dict] = data.setdefault("blocks", {})  # type: ignore[assignment]
    entry = dict(blocks.get(block_id) or {})
    if value:
        entry[field] = value
    else:
        entry.pop(field, None)
    if entry:
        blocks[block_id] = entry
    else:
        blocks.pop(block_id, None)

    data["version"] = _CURATION_VERSION
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_boundary_dates(course_dir: Path) -> set[str]:
    """Retorna o conjunto de datas ("YYYY-MM-DD") que forcam quebra de bloco
    na segmentacao (`_build_timeline_index`). Chave top-level `boundary_dates`
    no mesmo arquivo de curadoria (curso-scoped, fora do escopo por-bloco:
    a fronteira nao pode ser keyed por block_uuid porque o uuid so existe
    depois que os blocos ja foram fechados). {} se ausente/corrompido/curso
    sem a chave -> raio zero (comportamento hoje preservado)."""
    path = _curation_path(course_dir)
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return set()
    dates = data.get("boundary_dates") if isinstance(data, dict) else None
    if not isinstance(dates, list):
        return set()
    out = set()
    for d in dates:
        s = str(d).strip()
        if not s:
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            # fail-open era SILENCIOSO: data fora do formato nunca casa com
            # period_start e a fronteira pedida simplesmente nao acontece.
            logger.warning("boundary_dates: %r fora do formato YYYY-MM-DD — ignorada", s)
            continue
        out.add(s)
    return out


def apply_block_curation(blocks: Iterable[dict], course_dir: Path) -> int:
    """Merge in-place: injeta os campos `manual_*` nos blocos por id.

    So grava campos crus; a re-derivacao de `kind`/topic e responsabilidade
    de quem chama. Retorna a contagem de blocos afetados. Idempotente.
    """
    curation = load_block_curation(course_dir)
    if not curation:
        return 0
    touched = 0
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        override = (
            curation.get(str(block.get("block_uuid") or ""))
            or curation.get(str(block.get("id") or ""))
        )
        if not override:
            continue
        hit = False
        for field in _OVERRIDE_FIELDS:
            val = override.get(field)
            if val:
                block[_BLOCK_FIELD_RENAMES.get(field, field)] = val
                hit = True
        touched += int(hit)
    return touched
