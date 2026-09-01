from types import SimpleNamespace

from src.builder.routing.thresholds import T

from src.builder.routing.resolver_apply import apply_unit_subunit_fields

BLOCKS = [
    {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1"},
    {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "u2"},
]

def _entry(**kw):
    e = {"id": "e1", "file_type": "pdf", "computed_block_id": "u-2",
         "computed_block_confidence": 0.8, "computed_block_method": "concept-fused",
         "auto_tags": ["unit:velha", "outra:tag"]}
    e.update(kw)
    return e

def _fns(unit_match):
    return dict(
        auto_map_entry_unit_fn=lambda e, ui, md, ti, learned_unit_boosts=None: unit_match,
        auto_map_entry_subtopic_fn=lambda e, tax, md, winning_unit_slug="": SimpleNamespace(
            topic_slug="", topic_label="", unit_slug="", confidence=0.0, ambiguous=True, reasons=[]),
        build_file_map_unit_index_from_course_fn=lambda cm, sp: [{"slug": "u1"}, {"slug": "u2"}],
        iter_content_taxonomy_topics_fn=lambda tax: [],
        entry_markdown_text_for_file_map_fn=lambda root, e: "",
    )

def test_unit_reconciliada_contra_bloco_do_motor():
    # unidade auto (u1, conf 0.7) discorda do bloco NOVO (u-2 -> u2) com block_conf 0.8
    # block_conf >= unit_conf: reconcilia pro bloco, reason "reconciliada_do_bloco=u-2".
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=0.7, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"
    assert "reconciliada_do_bloco=bloco-02" in out[0]["unit_match_reasons"]   # id display do bloco
    assert out[0]["unit_block_conflict"] == {"unit": "u1", "block_unit": "u2", "block_id": "bloco-02"}
    assert out[0]["unit_match_confidence"] == 0.7

def test_bloco_vence_unidade_forte_e_registra_conflito():
    """2026-08-21: a unidade e a do bloco; o texto forte discordante vira so
    registro de conflito (auditoria), nao decisao."""
    e = _entry(computed_block_confidence=0.5)
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"
    assert out[0]["unit_block_conflict"] == {"unit": "u1", "block_unit": "u2", "block_id": "bloco-02"}


def test_bloco_temporal_vence_o_computed_na_unidade():
    """A ancora (temporal_block_id) e o bloco que a regua mede; a unidade tem
    que vir dele, nao do computed_block_id do scorer de conceito."""
    e = _entry(computed_block_id="u-1", temporal_block_id="u-2", temporal_block_band="alta")
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"


def test_bloco_sem_unidade_herda_do_vizinho_de_conteudo():
    blocks = [
        {"id": "bloco-01", "block_uuid": "u-1", "unit_slug": "u1", "kind": "class", "period_start": "2026-03-01"},
        {"id": "bloco-02", "block_uuid": "u-2", "unit_slug": "", "kind": "assessment", "period_start": "2026-03-08"},
    ]
    e = _entry(computed_block_id="u-2")
    m = SimpleNamespace(slug="", confidence=0.0, ambiguous=True, reasons=[])
    out = apply_unit_subunit_fields([e], blocks, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u1"
    assert any(r.startswith("herdada_do_vizinho=bloco-01") for r in out[0]["unit_match_reasons"])

def test_gate_unit_tag_e_espelho_de_tags():
    # conf < T.UNIT_TAG -> slug gated vazio -> herda a do bloco; tag unit: espelha o
    # resultado. Confianca RELATIVA ao threshold: o valor foi recalibrado em
    # 2026-08-18 (0.65 -> 0.50) e o teste nao pode depender do numero.
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=T.UNIT_TAG - 0.1, ambiguous=False, reasons=["fraca"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"          # herdada_do_bloco
    assert "unit:u2" in out[0]["auto_tags"]
    assert "unit:velha" not in out[0]["auto_tags"]
    assert "outra:tag" in out[0]["auto_tags"]            # prefixo não-gerenciado preservado

def test_manual_unit_tem_precedencia():
    e = _entry(manual_unit_slug="uman")
    m = SimpleNamespace(slug="u1", confidence=0.2, ambiguous=True, reasons=[])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "uman"
    assert out[0]["unit_match_reasons"] == ["manual"]
    assert out[0]["unit_match_confidence"] == 1.0

def test_nao_material_e_sem_bloco_ficam_intocados():
    sem_bloco = {"id": "e2", "file_type": "pdf", "computed_block_id": "", "auto_tags": []}
    nao_material = {"id": "e3", "file_type": "url", "auto_tags": []}
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=[])
    out = apply_unit_subunit_fields([sem_bloco, nao_material], BLOCKS, {}, None, None, {}, **_fns(m))
    assert "computed_unit_slug" not in out[0]
    assert "computed_unit_slug" not in out[1]

def test_unit_fraca_nunca_vence_bloco_mesmo_com_block_conf_menor():
    # conf < T.UNIT_TAG: gate zera o slug ANTES do reconcile -> herda a
    # unidade do bloco, sem conflito espurio (semantica do legado).
    e = _entry(computed_block_confidence=0.3)
    m = SimpleNamespace(slug="u1", confidence=T.UNIT_TAG - 0.1, ambiguous=False, reasons=["fraca"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"
    assert "herdada_do_bloco=bloco-02" in out[0]["unit_match_reasons"]   # id display do bloco
    assert out[0]["unit_block_conflict"] == {}

def test_subunit_gated_e_best_effort():
    e = _entry()
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])
    fns = _fns(m)
    # Confianca RELATIVA ao threshold (recalibrado 0.60 -> 0.10 em 01/09):
    # abaixo do gate a tag nao aparece, mas o computed best-effort persiste.
    fns["auto_map_entry_subtopic_fn"] = lambda e_, tax, md, winning_unit_slug="": SimpleNamespace(
        topic_slug="t-fraco", topic_label="", unit_slug="u2",
        confidence=T.SUBUNIT_TAG - 0.05, ambiguous=False, reasons=["topico"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **fns)
    assert out[0]["computed_subunit_slug"] == "t-fraco"          # best-effort persiste
    assert not any(t.startswith("subunit:") for t in out[0]["auto_tags"])  # gate segura a tag

def test_subunit_restrita_a_unidade_reconciliada():
    seen = {}
    e = _entry()
    m = SimpleNamespace(slug="u1", confidence=0.5, ambiguous=False, reasons=[])  # gated vazio -> herda u2
    fns = _fns(m)
    def _sub(e_, tax, md, winning_unit_slug=""):
        seen["unit"] = winning_unit_slug
        return SimpleNamespace(topic_slug="t1", topic_label="", unit_slug="u2",
                               confidence=0.9, ambiguous=False, reasons=[])
    fns["auto_map_entry_subtopic_fn"] = _sub
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **fns)
    assert seen["unit"] == "u2"                                   # restrição usa a unidade FINAL
    assert "subunit:t1" in out[0]["auto_tags"]

def test_manual_subunit_tem_precedencia():
    e = _entry(manual_subunit_slug="sman")
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_subunit_slug"] == "sman"
    assert out[0]["subunit_match_confidence"] == 1.0
    assert "subunit:sman" in out[0]["auto_tags"]

def test_pino_manual_de_bloco_da_unidade_do_bloco_mesmo_com_method_trocado():
    # attach pode reescrever computed_block_method p/ consensus; o pino
    # manual_timeline_block_id continua valendo como bloco manual no reconcile.
    e = _entry(manual_timeline_block_id="u-2", computed_block_method="consensus")
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_unit_slug"] == "u2"
    assert "unidade_do_bloco_manual" in out[0]["unit_match_reasons"]
    assert out[0]["unit_block_conflict"] == {}


def test_apply_concept_resolver_honra_pino_uuid():
    from src.builder.routing.resolver_apply import apply_concept_resolver
    e = {"id": "e1", "file_type": "pdf", "computed_block_id": "u-1",
         "manual_timeline_block_id": "u-2", "auto_tags": ["bloco:bloco-01"]}
    out = apply_concept_resolver([e], list(BLOCKS), [], {}, None)
    assert out[0]["computed_block_id"] == "u-2"          # pino vence o scorer
    assert out[0]["computed_block_method"] == "manual"
    assert out[0]["computed_block_confidence"] == 1.0
    assert "bloco:bloco-02" in out[0]["auto_tags"]       # espelho display resync

def test_cadeia_motor_unit_descreve_bloco_pos_apply():
    # 1.2 (auditoria): unit fields nao podem descrever o bloco ANTIGO.
    # Pino move e1 de u-1 pra u-2; a unidade final deve ser a de u-2.
    from src.builder.routing.resolver_apply import apply_concept_resolver
    e = {"id": "e1", "file_type": "pdf", "computed_block_id": "u-1",
         "manual_timeline_block_id": "u-2", "auto_tags": ["unit:u1", "bloco:bloco-01"]}
    entries = apply_concept_resolver([e], list(BLOCKS), [], {}, None)
    m = SimpleNamespace(slug="u1", confidence=0.9, ambiguous=False, reasons=["score"])
    out = apply_unit_subunit_fields(entries, BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_block_id"] == "u-2"
    assert out[0]["computed_unit_slug"] == "u2"          # unidade do bloco NOVO (pino manual)
    assert "unidade_do_bloco_manual" in out[0]["unit_match_reasons"]
    assert out[0]["unit_block_conflict"] == {}
    assert "unit:u2" in out[0]["auto_tags"] and "unit:u1" not in out[0]["auto_tags"]


def test_resumo_de_codigo_alimenta_a_rota_de_UNIDADE_tambem():
    """Zip/codigo nao tem .md: o unico sinal e o resumo do Gemini.

    O BLOCO ja recebia via `entry["concepts"]` e a SUBUNIDADE via `sub_md`; a
    UNIDADE decidia com texto VAZIO — 25 de 233 materiais dos 5 cursos (11%).
    Medido 2026-08-19: 129 -> 133 acertos na regua entry->unidade.
    """
    visto = {}

    def _captura_markdown(entry_, units_, markdown_, topic_index_=None, **kw):
        visto["unidade"] = markdown_
        return SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])

    e = _entry()
    fns = _fns(SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[]))
    fns["auto_map_entry_unit_fn"] = _captura_markdown
    curation = {"entries": {e["id"]: {"summary": {
        "inferred_title": "Implementacao de Microsservicos com Spring Cloud",
        "concepts": ["Service Discovery", "Feign Client", "Circuit Breaker"],
    }}}}

    apply_unit_subunit_fields([e], BLOCKS, {}, None, None, curation, **fns)

    texto = visto.get("unidade") or ""
    assert "Service Discovery" in texto or "Microsservicos" in texto, (
        f"resumo do codigo nao chegou na rota de unidade: {texto!r}"
    )


def test_meta_material_por_categoria_zera_subunit():
    # Item (a) 2026-08-31, espelho da regra A da cobertura: doc meta (cronograma)
    # descreve o curso INTEIRO — nao pertence a subunidade nenhuma. Caso real:
    # SO/TCC plano-de-ensino (subunit indevida evolucao-historica).
    e = _entry(category="cronograma")
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])
    fns = _fns(m)
    fns["auto_map_entry_subtopic_fn"] = lambda e_, tax, md, winning_unit_slug="": SimpleNamespace(
        topic_slug="t-indevido", topic_label="", unit_slug="u2",
        confidence=0.9, ambiguous=False, reasons=["topico"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **fns)
    assert out[0]["computed_subunit_slug"] == ""
    assert any(r.startswith("meta-material") for r in out[0]["subunit_match_reasons"])
    assert not any(t.startswith("subunit:") for t in out[0]["auto_tags"])


def test_meta_material_por_conteudo_zera_subunit():
    # Braco por CONTEUDO (categoria nao basta: SO `programa` e categoria
    # "outros" mas cita todas as unidades — mesmo arquivo do plano-de-ensino).
    from pathlib import Path
    e = _entry(category="outros")
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])
    fns = _fns(m)
    fns["build_file_map_unit_index_from_course_fn"] = lambda cm, sp: [
        {"slug": "u1", "normalized_title": "gerencia de processos"},
        {"slug": "u2", "normalized_title": "gerencia de memoria"},
    ]
    fns["entry_markdown_text_for_file_map_fn"] = lambda root, e_: (
        "EMENTA: gerencia de processos e gerencia de memoria"
    )
    fns["auto_map_entry_subtopic_fn"] = lambda e_, tax, md, winning_unit_slug="": SimpleNamespace(
        topic_slug="t-indevido", topic_label="", unit_slug="u2",
        confidence=0.9, ambiguous=False, reasons=["topico"])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, Path("."), {}, **fns)
    assert out[0]["computed_subunit_slug"] == ""
    assert any(r.startswith("meta-material") for r in out[0]["subunit_match_reasons"])


def test_manual_subunit_vence_gate_de_meta():
    e = _entry(category="cronograma", manual_subunit_slug="sman")
    m = SimpleNamespace(slug="u2", confidence=0.9, ambiguous=False, reasons=[])
    out = apply_unit_subunit_fields([e], BLOCKS, {}, None, None, {}, **_fns(m))
    assert out[0]["computed_subunit_slug"] == "sman"
