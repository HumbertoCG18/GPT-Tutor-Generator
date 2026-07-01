from src.builder.routing.file_map import reconcile_unit_with_block


def _call(**kw):
    base = dict(
        computed_unit_slug="", unit_confidence=0.0,
        computed_block_id="", block_confidence=0.0,
        block_unit_slug="", block_is_manual=False, has_manual_unit=False,
    )
    base.update(kw)
    return reconcile_unit_with_block(**base)


def test_manual_block_wins_even_over_manual_unit():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=1.0,
        computed_block_id="bloco-2", block_confidence=1.0,
        block_unit_slug="unidade-2", block_is_manual=True, has_manual_unit=True,
    )
    assert unit == "unidade-2"
    assert reasons == ["unidade_do_bloco_manual"]
    assert conflict == {}


def test_manual_unit_without_manual_block_keeps():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=1.0,
        computed_block_id="bloco-2", block_confidence=0.9,
        block_unit_slug="unidade-2", block_is_manual=False, has_manual_unit=True,
    )
    assert unit == "unidade-1"
    assert reasons == []
    assert conflict == {}


def test_auto_no_block_keeps():
    unit, reasons, conflict = _call(computed_unit_slug="unidade-1", unit_confidence=0.8)
    assert unit == "unidade-1"
    assert reasons == [] and conflict == {}


def test_auto_block_without_unit_keeps():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.8,
        computed_block_id="bloco-2", block_confidence=0.9, block_unit_slug="",
    )
    assert unit == "unidade-1"
    assert reasons == [] and conflict == {}


def test_auto_empty_unit_inherits_from_block():
    unit, reasons, conflict = _call(
        computed_unit_slug="", unit_confidence=0.0,
        computed_block_id="bloco-2", block_confidence=0.6, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == ["herdada_do_bloco=bloco-2"]
    assert conflict == {}


def test_auto_agree_keeps():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-2", unit_confidence=0.8,
        computed_block_id="bloco-2", block_confidence=0.6, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == [] and conflict == {}


def test_auto_disagree_block_stronger_reconciles():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.66,
        computed_block_id="bloco-2", block_confidence=0.80, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == ["reconciliada_do_bloco=bloco-2"]
    assert conflict == {}


def test_auto_disagree_unit_stronger_flags_conflict():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.90,
        computed_block_id="bloco-2", block_confidence=0.55, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-1"
    assert reasons == []
    assert conflict == {"unit": "unidade-1", "block_unit": "unidade-2", "block_id": "bloco-2"}
