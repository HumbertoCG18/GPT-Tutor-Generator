"""`revisar` — campo DERIVADO do manifest (Fase 0 do plano 02/09, decisao B).

Fila de revisao que o aluno ve no projeto da cadeira (UI depois; le este campo).
Funcao pura sobre o entry GRAVADO; recalculada a cada reprocess em
`resolver_apply.apply_unit_subunit_fields` (so materiais, `_is_material`).

  duvida  camada 1, aberta:  sem bloco (em escopo) | bloco flagado (inclui
          llm-funil) | subunidade ambigua/empate | conflito unidade x bloco
  mudou   camada 1b, "mudou, confira" (SYNC 03/09): decisao confiante que se moveu numa
          sincronizacao (campo `sync_changed`, gravado por moodle_sync.mark_sync_changes;
          a sync seguinte limpa se nada mover de novo)
  llm     camada 2, colapsada "decidido por LLM — confira": voto na janela
  ok      nao aparece

Metrica de produto = (duvida + llm) por 100 materiais (`scripts/censo_motor_llm.py`).
"Sem bloco" honesto (nao e duvida): categorias sem eixo temporal
(_NO_TIMELINE_CATEGORIES) e secao TDE (fora de escopo do motor).
"""
from __future__ import annotations

from src.builder.extraction.content_taxonomy import _NO_TIMELINE_CATEGORIES
from src.builder.routing.motor.anchor_engine import _TDE_PREFIX

DUVIDA, MUDOU, LLM, OK = "duvida", "mudou", "llm", "ok"


def _sem_bloco_honesto(entry: dict) -> bool:
    cat = str(entry.get("category") or "").strip().lower()
    sec = str(entry.get("source_section") or "").strip()
    return cat in _NO_TIMELINE_CATEGORIES or sec.startswith(_TDE_PREFIX)


def _subunidade_em_duvida(entry: dict) -> bool:
    if str(entry.get("manual_subunit_slug") or "").strip():
        return False
    reasons = [str(r) for r in (entry.get("subunit_match_reasons") or [])]
    return any(r == "ambiguous" or r.startswith("empate-exato") for r in reasons)


def motivos_de(entry: dict) -> list:
    """Gatilhos de `duvida` disparados, na ordem de checagem (anatomia da fila:
    censo e UI mostram POR QUE). Entry = material. [] = nenhum."""
    m = []
    pino = str(entry.get("manual_timeline_block_id") or "").strip()
    bloco = pino or str(entry.get("temporal_block_id") or "").strip()
    if not bloco and not _sem_bloco_honesto(entry):
        m.append("sem-bloco")
    if bool(entry.get("temporal_block_flag")):
        m.append("flag:" + str(entry.get("temporal_block_method") or ""))
    if entry.get("unit_block_conflict"):
        m.append("conflito")
    if _subunidade_em_duvida(entry):
        reasons = [str(r) for r in (entry.get("subunit_match_reasons") or [])]
        m.append("sub-empate" if any(r.startswith("empate-exato") for r in reasons) else "sub-ambigua")
    return m


def revisar_de(entry: dict) -> str:
    """Entry = material (o chamador filtra com `_is_material`)."""
    if motivos_de(entry):
        return DUVIDA
    if str(entry.get("sync_changed") or "").strip():
        return MUDOU
    if str(entry.get("temporal_block_method") or "") == "llm":
        return LLM
    return OK
