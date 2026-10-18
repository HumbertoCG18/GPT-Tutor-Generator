import json
from pathlib import Path

from src.builder.routing.motor.contracts import MotorContext
from src.builder.routing.motor.anchor_engine import AnchorEngine, is_out_of_disamb_scope
from src.utils.helpers import norm_ascii_lower

GOLD = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "eval" / "metodos_formais_golden.json"


def _load_ctx_and_cases():
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    ctx = MotorContext.from_artifacts(
        blocks=data["timeline"]["blocks"],  # gold embute blocos em timeline.blocks (mesmo shape de test_resolver_fusion.py)
        card_block_map=data["card_block_map"],
        lessons_index={},  # gold não embute lessons_index; session-label vem de sessions[].label
        course_name=str(data.get("subject") or ""),
    )
    return ctx, data["cases"]


def _has_window(ctx, section) -> bool:
    key = norm_ascii_lower(str(section or ""))
    norm = {norm_ascii_lower(str(k)): v for k, v in ctx.card_block_map.items()}
    info = norm.get(key) or {}
    return bool(info.get("block_ids"))


def _entry_of(case):
    # mapeia o case do gold para o shape que o motor lê
    return {
        "title": case.get("title", ""),
        "category": case.get("category", ""),
        "source_section": case.get("source_section_real", ""),
        "moodle_label": case.get("moodle_label", ""),
        "auto_tags": case.get("auto_tags", []),
    }


def _scored_cases(ctx, cases):
    """Cases mensuráveis: têm expected_block_id, não são excluídos/D6, e têm janela."""
    out = []
    for c in cases:
        if not c.get("expected_block_id"):
            continue
        entry = _entry_of(c)
        if is_out_of_disamb_scope(entry):
            continue
        if not _has_window(ctx, entry["source_section"]):
            continue
        out.append((c, entry))
    return out


def test_gold_has_scorable_windowed_cases():
    ctx, cases = _load_ctx_and_cases()
    assert len(_scored_cases(ctx, cases)) >= 8  # sanidade: há casos de janela pra medir


def test_contencao_100_pct_quando_ancora():
    ctx, cases = _load_ctx_and_cases()
    fora = []
    eng = AnchorEngine()
    for c, entry in _scored_cases(ctx, cases):
        d = eng.resolve(entry, ctx, markdown=c.get("markdown", ""))
        if d is None:
            continue  # funil não viola contenção
        if c["expected_block_id"] not in d.window:
            fora.append((entry["title"], c["expected_block_id"], d.window))
    assert not fora, f"verdade FORA da janela (contenção quebrada): {fora}"


def test_confiante_errado_zero():
    ctx, cases = _load_ctx_and_cases()
    eng = AnchorEngine()
    confiante_errado = []
    for c, entry in _scored_cases(ctx, cases):
        d = eng.resolve(entry, ctx, markdown=c.get("markdown", ""))
        if d is None:
            continue
        if d.band == "alta" and d.block_ref != c["expected_block_id"]:
            confiante_errado.append((entry["title"], d.block_ref, c["expected_block_id"]))
    assert not confiante_errado, f"confiante-e-errado (band alta): {confiante_errado}"


def test_janela_unitaria_coloca_e_nao_flaga():
    ctx, cases = _load_ctx_and_cases()
    eng = AnchorEngine()
    for c, entry in _scored_cases(ctx, cases):
        d = eng.resolve(entry, ctx, markdown=c.get("markdown", ""))
        if d is not None and len(d.window) == 1:
            assert d.flag is False
            assert d.block_ref == c["expected_block_id"], (entry["title"], d.block_ref)
