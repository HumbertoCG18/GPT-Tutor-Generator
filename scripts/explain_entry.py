"""Explica, etapa a etapa, como UM arquivo foi atribuido a bloco/unidade/subunidade.

READ-ONLY. Roda o CAMINHO DE PRODUCAO — os mesmos montadores canonicos que
`resolver_apply.apply_concept_resolver` e `apply_unit_subunit_fields` usam. Isso
nao e detalhe: nesta campanha varias medicoes deram numero errado por remontar o
caminho a mao (faltou `learned_unit_boosts`, faltou o resumo do Gemini, usou
`computed_block_id` cru no lugar de `resolve_temporal_block`). Diferente de
`scripts/trace_motor.py`, que e um PISO com tokenizer proprio e nao mede o motor.

Uso:
    python scripts/explain_entry.py <REPO_ROOT> <entry_id ou pedaco do id/titulo>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.engine import (  # noqa: E402
    _auto_map_entry_subtopic,
    _auto_map_entry_unit,
    _build_file_map_unit_index_from_course,
    _entry_markdown_text_for_file_map,
    _iter_content_taxonomy_topics,
)
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing.concept_resolver import resolve_material_assignment  # noqa: E402
from src.builder.routing.coverage_rules import derive_coverage_units  # noqa: E402
from src.builder.routing.file_map import reconcile_unit_with_block, resolve_temporal_block  # noqa: E402
from src.builder.routing.resolver_apply import (  # noqa: E402
    _is_material,
    assemble_resolver_inputs,
    load_lessons_index,
)
from src.builder.routing.sequence import annotate_class_ordinals  # noqa: E402
from src.builder.routing.thresholds import T  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402
from src.models.tag_profile import build_learned_unit_boosts, load_tag_profile  # noqa: E402

TERMOS = ("concept", "llm", "date", "sequence", "card", "lesson")


def _norm(texto):
    return normalize_match_text(texto, keep="+-./")


def _ctx(repo: Path) -> dict:
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    timeline = json.loads((repo / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocks = annotate_class_ordinals(list(timeline.get("blocks") or []))
    cc = repo / "code_curation.json"
    code_curation = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {"entries": {}}
    profile = SubjectStore().find_by_repo_root(repo)
    course_meta = {**(manifest.get("course") or {}), "_repo_root": repo}
    taxonomy = load_internal_content_taxonomy(repo) or {}
    return {
        "manifest": manifest,
        "blocks": blocks,
        "code_curation": code_curation,
        "unit_index": _build_file_map_unit_index_from_course(course_meta, profile),
        "taxonomy": taxonomy,
        "topic_index": _iter_content_taxonomy_topics(taxonomy),
        "tag_profile": load_tag_profile(repo / "course"),
        "lessons": load_lessons_index(repo),
    }


def _rotulo(block: dict) -> str:
    label = str(block.get("primary_topic_label") or block.get("topic_label") or "")
    return f"{block.get('id')} - {label[:44]}"


def explicar(repo: Path, entry: dict, ctx: dict) -> None:
    eid = str(entry.get("id") or "")
    print("=" * 78)
    print(eid)
    print(f"  titulo   : {entry.get('title')}")
    print(f"  categoria: {entry.get('category')}")
    if not _is_material(entry):
        print("  -> NAO e material: sai do motor antes de qualquer eixo.")
        return

    entry2, signals, summary = assemble_resolver_inputs(repo, entry, ctx["code_curation"])
    print("")
    print("[1] SINAIS montados (o que o motor enxerga)")
    for chave, valor in sorted(signals.items()):
        if isinstance(valor, str) and valor.strip():
            print(f"    {chave:22} {len(valor):6} chars  {valor.strip()[:52]!r}")
        elif not isinstance(valor, str) and valor:
            print(f"    {chave:22} {valor!r}"[:96])
    print(f"    {'llm_curation':22} {'presente' if summary else 'ausente'}")

    atrib = resolve_material_assignment(
        entry2, ctx["blocks"], [], signals=signals,
        llm_curation=summary or None, lessons_index=ctx["lessons"],
    )
    conf_bloco = float(atrib.get("confidence") or 0.0)
    print("")
    print(f"[2] BLOCO (1:1 temporal) - metodo={atrib.get('method')} "
          f"band={atrib.get('band')} conf={conf_bloco:.4f}")
    venc = next((b for b in ctx["blocks"]
                 if str(b.get("block_uuid") or b.get("id")) == str(atrib.get("block_id"))), {})
    print(f"    vencedor: {_rotulo(venc) if venc else atrib.get('block_id')}")
    br = atrib.get("signals") or {}
    termos = "  ".join(f"{t}={float(br.get(t, 0) or 0):+.3f}" for t in TERMOS if t in br)
    if termos:
        print(f"    termos  : {termos}")
    if atrib.get("conflict"):
        print(f"    conflito: {atrib['conflict']}")

    provisorio = {**entry, "computed_block_id": str(atrib.get("block_id") or "")}
    temporal = resolve_temporal_block(provisorio, ctx["blocks"])
    if temporal and temporal != str(atrib.get("block_id") or ""):
        alvo = next((b for b in ctx["blocks"]
                     if str(b.get("block_uuid") or b.get("id")) == temporal), {})
        print(f"    -> resolve_temporal_block SOBREPOE: {_rotulo(alvo) if alvo else temporal}")

    markdown = _entry_markdown_text_for_file_map(repo, entry)
    rec = (ctx["code_curation"].get("entries") or {}).get(eid) or {}
    resumo = code_curation_signal_text(rec) if rec else ""
    texto = markdown
    if resumo:
        texto = f"{markdown}\n\n{resumo}" if markdown else resumo
    print("")
    print(f"[3] TEXTO da rota de unidade: markdown={len(markdown)} chars + "
          f"resumo_gemini={len(resumo)} chars = {len(texto)}")

    manual = str(entry.get("manual_unit_slug") or "").strip()
    if manual:
        slug, conf, ambiguo, motivos = manual, 1.0, False, ["manual"]
    else:
        learned = build_learned_unit_boosts(ctx["tag_profile"], entry) if ctx["tag_profile"] else {}
        match = _auto_map_entry_unit(entry, ctx["unit_index"], texto, ctx["topic_index"],
                                     learned_unit_boosts=learned)
        slug, conf, ambiguo, motivos = match.slug, match.confidence, match.ambiguous, list(match.reasons)
    gated = slug if (not ambiguo and conf >= T.UNIT_TAG) else ""
    print("")
    print(f"[4] UNIDADE 1:1 - scorer={slug or '(vazio)'} conf={conf:.3f} ambiguo={ambiguo}")
    print(f"    gate T.UNIT_TAG={T.UNIT_TAG} -> {gated or 'BARRADO (fica vazio)'}")
    if motivos:
        print(f"    motivos : {motivos[:6]}")

    unidade_do_bloco = str((venc or {}).get("unit_slug") or "").strip()
    pino = str(entry.get("manual_timeline_block_id") or "").strip()
    reconciliado, sufixo, conflito = reconcile_unit_with_block(
        computed_unit_slug=gated,
        unit_confidence=float(conf),
        computed_block_id=str(atrib.get("block_id") or ""),
        block_confidence=conf_bloco,
        block_unit_slug=unidade_do_bloco,
        block_is_manual=bool(pino) and pino in {str(atrib.get("block_id")), str((venc or {}).get("id"))},
        has_manual_unit=bool(manual),
    )
    print(f"    reconcilia com a unidade DO BLOCO ({unidade_do_bloco or 'bloco sem unidade'})"
          f" -> {reconciliado or '(vazio)'}")
    if sufixo or conflito:
        print(f"    {sufixo} {conflito or ''}")

    cobertura = derive_coverage_units(entry, ctx["unit_index"], texto, normalize=_norm,
                                      fallback_unit_slug=gated, topic_index=ctx["topic_index"])
    print("")
    print(f"[5] COBERTURA N:N - {len(cobertura)} unidade(s)")
    for item in cobertura:
        print(f"    regra={str(item.get('rule')):9} conf={float(item.get('confidence') or 0):.2f} "
              f"{item.get('unit_slug')}  topicos={len(item.get('topics') or [])}")

    manual_sub = str(entry.get("manual_subunit_slug") or "").strip()
    print("")
    if manual_sub:
        print(f"[6] SUBUNIDADE - manual: {manual_sub}")
        return
    tm = _auto_map_entry_subtopic(entry, ctx["taxonomy"], texto, winning_unit_slug=reconciliado)
    sub = str(getattr(tm, "topic_slug", "") or "")
    conf_sub = float(getattr(tm, "confidence", 0.0))
    passou = bool(sub and not tm.ambiguous and conf_sub >= T.SUBUNIT_TAG)
    print(f"[6] SUBUNIDADE (candidatos SO da unidade '{reconciliado or 'nenhuma'}')")
    print(f"    scorer={sub or '(vazio)'} conf={conf_sub:.3f} ambiguo={tm.ambiguous}")
    print(f"    gate T.SUBUNIT_TAG={T.SUBUNIT_TAG} -> {sub if passou else 'BARRADO (nao vira tag)'}")


def main(argv: list) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    repo = Path(argv[1])
    alvo = argv[2].lower()
    ctx = _ctx(repo)
    achou = [
        e for e in ctx["manifest"].get("entries") or []
        if alvo in str(e.get("id") or "").lower() or alvo in str(e.get("title") or "").lower()
    ]
    if not achou:
        print(f"nada casa com {alvo!r} em {repo.name}")
        return 1
    for entry in achou[:5]:
        explicar(repo, entry, ctx)
    if len(achou) > 5:
        print(f"\n(+{len(achou) - 5} entries casam; refine o filtro)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
