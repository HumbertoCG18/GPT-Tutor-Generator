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
    # o texto discordante fica registrado para auditoria, mesmo quando perde
    assert conflict == {"unit": "unidade-1", "block_unit": "unidade-2", "block_id": "bloco-2"}


def test_auto_disagree_bloco_vence_mesmo_com_unidade_forte():
    """2026-08-21: a verdade de unidade e, por construcao, a unidade do bloco
    (ground_truth |><| gold_units). Medido nos 5 cursos (188 entries): scorer
    de texto 130, unidade do bloco temporal 162, bloco + heranca 178 — e o
    scorer nao acrescenta nada por cima do bloco. Comparar confiancas so
    deixava o texto vencer onde ele erra. O conflito segue registrado para
    auditoria, mas a unidade e a do bloco."""
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.90,
        computed_block_id="bloco-2", block_confidence=0.55, block_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == ["reconciliada_do_bloco=bloco-2"]
    assert conflict == {"unit": "unidade-1", "block_unit": "unidade-2", "block_id": "bloco-2"}


def test_unidade_do_bloco_ou_do_vizinho_de_conteudo():
    """Bloco de avaliacao/revisao/entrega nao tem unit_slug por design; a entry
    que cai nele herda do bloco de CONTEUDO anterior (fecha o que veio antes);
    overview herda do proximo (abre o que vem)."""
    from src.builder.routing.file_map import unit_of_block_or_neighbor
    blocks = [
        {"id": "b0", "kind": "overview", "period_start": "2026-03-01"},
        {"id": "b1", "kind": "class", "period_start": "2026-03-08", "unit_slug": "u1"},
        {"id": "b2", "kind": "review", "period_start": "2026-03-15"},
        {"id": "b3", "kind": "assessment", "period_start": "2026-03-22"},
        {"id": "b4", "kind": "class", "period_start": "2026-03-29", "unit_slug": "u2"},
    ]
    assert unit_of_block_or_neighbor("b1", blocks) == ("u1", "")
    assert unit_of_block_or_neighbor("b2", blocks) == ("u1", "b1")
    assert unit_of_block_or_neighbor("b3", blocks) == ("u1", "b1")
    assert unit_of_block_or_neighbor("b0", blocks) == ("u1", "b1")
    assert unit_of_block_or_neighbor("b4", blocks) == ("u2", "")
    assert unit_of_block_or_neighbor("inexistente", blocks) == ("", "")


# --- #47: secao mapeada ao plano, corroborada pelo texto, vence unidade herdada do bloco ---

def test_secao_corroborada_vence_bloco_discordante():
    """2026-09-21 (#47): medido pela fase real nos 7 cursos, unidade 239 -> 244/284,
    0 perda; a secao com vencedor unico no plano acerta 45/45."""
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-3", unit_confidence=0.7,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-2",
        section_unit_slug="unidade-3",
    )
    assert unit == "unidade-3"
    assert reasons == ["secao-vence-bloco=bloco-2"]
    assert conflict == {"unit": "unidade-3", "block_unit": "unidade-2", "block_id": "bloco-2"}


def test_secao_corroborada_vence_heranca_quando_unidade_nao_passou_no_gate():
    unit, reasons, conflict = _call(
        computed_unit_slug="", unit_confidence=0.3,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-2",
        section_unit_slug="unidade-3",
    )
    assert unit == "unidade-3"
    assert reasons == ["secao-vence-bloco=bloco-2"]
    assert conflict == {"unit": "unidade-3", "block_unit": "unidade-2", "block_id": "bloco-2"}


def test_secao_igual_ao_bloco_mantem_a_heranca():
    unit, reasons, conflict = _call(
        computed_unit_slug="", unit_confidence=0.3,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-2",
        section_unit_slug="unidade-2",
    )
    assert unit == "unidade-2"
    assert reasons == ["herdada_do_bloco=bloco-2"]
    assert conflict == {}


def test_bloco_manual_e_unidade_manual_vencem_a_secao():
    unit, reasons, _ = _call(
        computed_unit_slug="unidade-3", unit_confidence=1.0,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-2",
        block_is_manual=True, section_unit_slug="unidade-3",
    )
    assert (unit, reasons) == ("unidade-2", ["unidade_do_bloco_manual"])
    unit, reasons, _ = _call(
        computed_unit_slug="unidade-1", unit_confidence=1.0,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-2",
        has_manual_unit=True, section_unit_slug="unidade-3",
    )
    assert (unit, reasons) == ("unidade-1", [])


def test_sem_bloco_a_secao_nao_dispara():
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-1", unit_confidence=0.8, section_unit_slug="unidade-3",
    )
    assert unit == "unidade-1"
    assert reasons == [] and conflict == {}


def test_unidade_explicita_mantem_o_rotulo_mesmo_com_secao_corroborada():
    """Revisao Astra (#47): explicita e secao ao mesmo tempo — a explicita decide e rotula."""
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-3", unit_confidence=0.95,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-2",
        unit_is_explicit=True, section_unit_slug="unidade-3",
    )
    assert unit == "unidade-3"
    assert reasons == ["explicita-vence-bloco=bloco-2"]
    assert conflict == {"unit": "unidade-3", "block_unit": "unidade-2", "block_id": "bloco-2"}


# --- #48: unidade herdada do vizinho nao vence texto gated discordante ---

def test_texto_gated_vence_unidade_herdada_do_vizinho():
    """Medido nos 7 cursos (21/09): onde o bloco nao tem unidade propria e o texto
    gated discorda da herdada do vizinho, o vizinho acertava 0/5; unidade 244 -> 246."""
    unit, reasons, conflict = _call(
        computed_unit_slug="unidade-3", unit_confidence=0.55,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-1",
        neighbor_block_id="bloco-1",
    )
    assert unit == "unidade-3"
    assert reasons == ["texto-vence-vizinho=bloco-1"]
    assert conflict == {"unit": "unidade-3", "block_unit": "unidade-1", "block_id": "bloco-2"}


def test_vizinho_ainda_vence_texto_vazio_e_bloco_proprio_ainda_vence_texto():
    unit, reasons, conflict = _call(
        computed_unit_slug="", unit_confidence=0.3,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-1",
        neighbor_block_id="bloco-1",
    )
    assert (unit, reasons, conflict) == ("unidade-1", ["herdada_do_bloco=bloco-2"], {})
    unit, reasons, _ = _call(
        computed_unit_slug="unidade-3", unit_confidence=0.9,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-1",
    )
    assert (unit, reasons) == ("unidade-1", ["reconciliada_do_bloco=bloco-2"])


def test_manual_e_explicita_vencem_mesmo_com_vizinho():
    unit, reasons, _ = _call(
        computed_unit_slug="unidade-3", unit_confidence=0.9,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-1",
        block_is_manual=True, neighbor_block_id="bloco-1",
    )
    assert (unit, reasons) == ("unidade-1", ["unidade_do_bloco_manual"])
    unit, reasons, _ = _call(
        computed_unit_slug="unidade-3", unit_confidence=0.95,
        computed_block_id="bloco-2", block_confidence=1.0, block_unit_slug="unidade-1",
        unit_is_explicit=True, neighbor_block_id="bloco-1",
    )
    assert (unit, reasons) == ("unidade-3", ["explicita-vence-bloco=bloco-2"])

