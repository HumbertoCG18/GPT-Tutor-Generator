# src/builder/artifacts/cronograma_health.py
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from src.builder.timeline.conflicts import detect_timeline_conflicts

# Top-N de blocos candidatos exibidos por material de baixa-confiança. N=3:
# o suficiente para o revisor comparar o vencedor contra as 2 alternativas mais
# próximas sem inflar o relatório; só é computado para materiais já flagados
# (media/baixa), limitando o custo do scorer.
_TOP_N_CANDIDATES = 3

_NON_MATERIAL_CATEGORIES = {"cronograma", "bibliografia", "referencias"}

# Faixas que sinalizam revisão (spec Fase 3/4): material flagado entra na lista
# acionável de baixa-confiança com candidatos top-N.
_REVIEW_BANDS = {"media", "baixa"}


def _entry_block_id(entry: dict, blocks: list | None = None) -> str:
    """Bloco efetivo do material via a FONTE ÚNICA (resolve_effective_block).

    `blocks` (lista do timeline_index) deve ser passada sempre que disponível:
    sem ela, resolve_effective_block não valida o manual id e confia no valor
    cru — divergindo do dashboard quando o manual está stale (spec 138-146,
    213-215). Default None mantém compatibilidade com chamadores que ainda não
    têm a lista (degradam graciosamente).

    Lazy-import: cronograma_health é importado por caminhos do builder que
    file_map também toca; o import tardio evita ciclo (padrão das fases 1-3).
    """
    from src.builder.routing.file_map import resolve_effective_block

    return resolve_effective_block(entry, blocks).block_id


def _entry_block_source(entry: dict, blocks: list | None = None) -> str:
    """"manual"/"auto"/"" do material, via a mesma FONTE ÚNICA.

    `blocks` segue a mesma regra de _entry_block_id: passe-a para que a
    validação do manual id rode (caso contrário um manual stale aparece como
    "manual" em vez de cair no computed "auto").
    """
    from src.builder.routing.file_map import resolve_effective_block

    return resolve_effective_block(entry, blocks).source


def material_coverage(entries: Iterable[dict], blocks: list | None = None) -> dict:
    """% de materiais com bloco, orfaos, por tipo. Read-only.

    `blocks` é threaded para resolve_effective_block validar manual ids stale
    (mesma validação do dashboard); ausente, degrada para o id cru.
    """
    entries = [
        e for e in (entries or [])
        if str(e.get("category") or "").lower() not in _NON_MATERIAL_CATEGORIES
    ]
    total = len(entries)
    with_block = 0
    by_type: dict = defaultdict(lambda: {"total": 0, "with_block": 0})
    for e in entries:
        ftype = str(e.get("file_type") or "pdf").lower()
        by_type[ftype]["total"] += 1
        if _entry_block_id(e, blocks):
            with_block += 1
            by_type[ftype]["with_block"] += 1
    return {
        "total": total,
        "with_block": with_block,
        "orphans": total - with_block,
        "coverage": (with_block / total) if total else 0.0,
        "by_type": {k: dict(v) for k, v in by_type.items()},
    }


def band_distribution(entries: Iterable[dict], blocks: list | None = None) -> dict:
    """Contagem de materiais atribuídos por faixa de confiança (Fase 4).

    Lê computed_block_band (Fase 1/3). Só conta materiais COM bloco atribuído —
    órfãos (band vazia) ficam fora; sua contagem já aparece em material_coverage.
    `blocks` é threaded para validar manual ids stale (vide _entry_block_id).
    """
    dist = {"alta": 0, "media": 0, "baixa": 0}
    for e in entries or []:
        if str(e.get("category") or "").lower() in _NON_MATERIAL_CATEGORIES:
            continue
        if not _entry_block_id(e, blocks):
            continue
        band = str(e.get("computed_block_band") or "").strip()
        if band in dist:
            dist[band] += 1
    return dist


def _blocks_by_material_count(entries, blocks) -> dict:
    counts = {b.get("id"): 0 for b in (blocks or []) if b.get("id")}
    for e in entries or []:
        bid = _entry_block_id(e, blocks)
        if bid in counts:
            counts[bid] += 1
    return counts


def _entry_title(entry: dict) -> str:
    return str(entry.get("title") or entry.get("source_path") or entry.get("id") or "—")


def _top_candidate_blocks(entry: dict, blocks: list, n: int = _TOP_N_CANDIDATES) -> list:
    """Top-N (block_id, score) para um material flagado.

    REUSA score_entry_against_timeline_block (não reimplementa scoring) sobre os
    blocos instrucionais — exatamente o mesmo scorer de _best_instructional_block_fallback
    em content_taxonomy. Lazy-import para evitar ciclo. Computado SÓ para
    materiais já flagados (chamador filtra), limitando o custo.

    Degrada para [] se os blocos não trazem rows (ex.: fixtures mínimas / dados
    sem cronograma scorável) — o relatório ainda lista o material como acionável.
    """
    # D2: predicado unico (filtra admin no runtime; inocuo nos blocos serializados
    # deste artefato, que ja tiveram admin removido no _serialize).
    from src.builder.timeline.index import timeline_block_is_administrative_only
    instructional = [
        b for b in (blocks or [])
        if b.get("id") and not timeline_block_is_administrative_only(b)
    ]
    if not instructional:
        return []
    try:
        from src.builder.routing.file_map import (
            score_entry_against_timeline_block,
            score_card_evidence_against_entry,
        )
        from src.builder.extraction.entry_signals import (
            collect_entry_unit_signals,
            score_text_against_row,
        )
        from src.builder.text.normalize import normalize_match_text
    except Exception:
        return []

    # keep="+-./" replica a tokenização do funil real (content_taxonomy):
    # datas, prefixos de outline e paths são tokens distintivos, e o score
    # daqui precisa ser comparável ao do pipeline. Import da fonte canônica
    # (text/normalize) com o keep explícito, em vez do wrapper privado.
    def _normalize_match_text(text: str) -> str:
        return normalize_match_text(text, keep="+-./")

    markdown_text = ""
    signals = collect_entry_unit_signals(entry, markdown_text)
    preferred_unit = str(entry.get("computed_unit_slug") or "").strip()
    scored = []
    for block in instructional:
        score = score_entry_against_timeline_block(
            signals,
            block,
            normalize_match_text=_normalize_match_text,
            score_text_against_row=score_text_against_row,
            score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
                s, items, normalize_match_text=_normalize_match_text
            ),
            preferred_unit_slug=preferred_unit,
        )
        scored.append((str(block.get("id") or ""), float(score)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:n]


def cronograma_health_md(course_meta: dict, entries: list, blocks: list) -> str:
    rep = material_coverage(entries, blocks)
    dist = band_distribution(entries, blocks)
    name = str((course_meta or {}).get("name") or "Curso")
    lines = [
        f"# CRONOGRAMA_HEALTH — {name}",
        "",
        f"- **Cobertura de material**: {rep['coverage']:.0%} "
        f"({rep['with_block']}/{rep['total']} com bloco)",
        f"- **Órfãos** (sem bloco): {rep['orphans']}",
        "",
        "## Por tipo",
        "",
        "| Tipo | Com bloco | Total |",
        "|---|---|---|",
    ]
    for ftype, v in sorted(rep["by_type"].items()):
        lines.append(f"| {ftype} | {v['with_block']} | {v['total']} |")

    # Distribuição de confiança (Fase 4): lê computed_block_band.
    lines += [
        "",
        "## Distribuição de confiança",
        "",
        "| Faixa | Materiais |",
        "|---|---|",
        f"| alta | {dist['alta']} |",
        f"| media | {dist['media']} |",
        f"| baixa | {dist['baixa']} |",
    ]

    # Lista acionável de baixa-confiança (media/baixa): cada material vira tarefa,
    # com manual/auto + top-N blocos candidatos (scorer reusado).
    materials = [
        e for e in (entries or [])
        if str(e.get("category") or "").lower() not in _NON_MATERIAL_CATEGORIES
        and _entry_block_id(e, blocks)
        and str(e.get("computed_block_band") or "").strip() in _REVIEW_BANDS
    ]
    lines += [
        "",
        "## Materiais de baixa confiança (revisar)",
        "",
    ]
    if not materials:
        lines.append("_nenhum_")
    else:
        for entry in materials:
            band = str(entry.get("computed_block_band") or "").strip()
            source = _entry_block_source(entry, blocks)
            source_label = {"manual": "manual", "auto": "auto"}.get(source, "—")
            conf = float(entry.get("computed_block_confidence") or 0.0)
            effective = _entry_block_id(entry, blocks)
            lines.append(
                f"- **{_entry_title(entry)}** — bloco `{effective}` "
                f"(faixa {band}, conf {conf:.2f}, {source_label})"
            )
            candidates = _top_candidate_blocks(entry, blocks)
            for cand_id, cand_score in candidates:
                lines.append(f"    - candidato `{cand_id}` (score {cand_score:.2f})")

    counts = _blocks_by_material_count(entries, blocks)
    poor = [bid for bid, n in counts.items() if n == 0]
    rich = sorted(((n, bid) for bid, n in counts.items()), reverse=True)[:5]
    lines += [
        "",
        "## Blocos pobres (0 materiais)",
        "",
        (", ".join(poor) if poor else "_nenhum_"),
        "",
        "## Blocos mais ricos",
        "",
    ]
    for n, bid in rich:
        lines.append(f"- {bid}: {n} material(is)")

    conflicts = detect_timeline_conflicts(blocks or [])
    period_by_id = {
        str(b.get("id") or ""): str(b.get("period_label") or "")
        for b in (blocks or [])
    }
    lines += [
        "",
        "## Conflitos de curadoria",
        "",
    ]
    if not conflicts:
        lines.append("_Nenhum conflito de curadoria._")
    else:
        field_labels = {"unit": "unidade", "kind": "kind"}
        for c in conflicts:
            period = period_by_id.get(c["block_id"], "")
            period_part = f" ({period})" if period else ""
            field_label = field_labels.get(c["field"], c["field"])
            lines.append(
                f"- ⚠️ `{c['block_id']}`{period_part} {field_label}: "
                f"manual `{c['manual']}` ≠ auto `{c['auto']}` "
                f"({c['confidence']:.0%})"
            )

    return "\n".join(lines) + "\n"
