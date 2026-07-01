"""S2 (P4): sinais do scorer de bloco — IDF por raridade entre blocos candidatos.

block_token_weights(blocks) dá peso 1/df a cada token do topic_text dos
candidatos; score_entry_against_timeline_block(topic_token_weights=...) usa
esses pesos para pontuar título/markdown/tags contra o topic do bloco. Com
weights=None o comportamento é EXATAMENTE o anterior (paridade — chamadores
que não passam o kwarg, ex. cronograma_health, não mudam)."""
from functools import partial

from src.builder.extraction.entry_signals import (
    collect_entry_unit_signals,
    normalize_match_text,
    score_text_against_row,
)
from src.builder.routing.file_map import (
    block_token_weights,
    score_card_evidence_against_entry,
    score_entry_against_timeline_block,
)
from src.builder.text.normalize import normalize_match_text as _normalize_match_text_base

# Normalize com keep="+-./", como usa content_taxonomy._normalize_match_text
_normalize_keep = partial(_normalize_match_text_base, keep="+-./")


def _pblock(bid, topic, start, end, sessions=None, unit="unidade-02-verificacao-de-programas"):
    """Shape de bloco PERSISTIDO (.timeline_index.json) — cf. tests/test_eval_golden_real.py."""
    session_labels = sessions if sessions is not None else [topic]
    return {
        "id": bid, "period_start": start, "period_end": end,
        "period_label": f"{start}..{end}", "kind": "class",
        "unit_slug": unit, "unit_confidence": 0.8,
        "primary_topic_slug": topic.replace(" ", "-"),
        "primary_topic_label": topic, "primary_topic_confidence": 0.8,
        "topic_ambiguous": False, "topic_candidates": [],
        "topic_text": topic, "topics": [topic],
        "aliases": [], "card_evidence": [],
        "sessions": [{"label": label, "date": start} for label in session_labels],
        # ints = índices do cronograma (shape real persistido): força o scorer
        # a sintetizar rows a partir das sessions, como em produção.
        "source_rows": list(range(len(session_labels))),
    }


def _blocks_metodos_formais():
    """Geometria real do golden Metodos-Formais (b10/b13/b15): os tokens raros
    arrays/sequencias/conjuntos vivem no topic_text do b13; o b15 ganha hoje
    por superfície (2 rows 'exercicios aula' + tokens comuns logica/programas/dafny)."""
    b10 = _pblock(
        "bloco-10", "logica hoare", "2026-04-27", "2026-05-04",
        sessions=["logica de hoare aula", "logica de hoare aula", "exercicios aula"],
    )
    b13 = _pblock(
        "bloco-13", "logica programas dafny colecoes arrays sequencias conjuntos",
        "2026-05-13", "2026-05-25",
        sessions=[
            "logica de programas dafny aula",
            "logica de programas colecoes dafny arrays aula",
            "logica de programas colecoes dafny sequencias aula",
            "logica de programas colecoes dafny conjuntos aula",
        ],
    )
    b15 = _pblock(
        "bloco-15", "logica programas orientacao objetos dafny ghosts autocontrato",
        "2026-06-01", "2026-06-10",
        sessions=[
            "logica de programas orientacao a objetos dafny ghosts autocontrato aula",
            "exercicios aula",
            "logica de programas orientacao a objetos dafny ghosts autocontrato aula",
            "exercicios aula",
        ],
    )
    return b10, b13, b15


def _score(entry, markdown, block, *, weights=None, unit_slug="unidade-02-verificacao-de-programas"):
    signals = collect_entry_unit_signals(entry, markdown)
    kwargs = {}
    if weights is not None:
        kwargs["topic_token_weights"] = weights
    return score_entry_against_timeline_block(
        signals,
        block,
        normalize_match_text=normalize_match_text,
        score_text_against_row=score_text_against_row,
        score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
            s, items, normalize_match_text=normalize_match_text
        ),
        preferred_unit_slug=unit_slug,
        **kwargs,
    )


def _entry(title, category="listas", auto_tags=None):
    return {"id": "e1", "title": title, "category": category,
            "manual_tags": [], "auto_tags": list(auto_tags or []), "tags": ""}


def test_token_raro_decide_entre_blocos():
    """'arrays' aparece no topic de 1 bloco; 'logica/programas/dafny' em 2+.
    Entry de exercícios sobre arrays em Dafny tem que pontuar o b13 (dono do
    token raro) acima do b15, que hoje vence por superfície (rows 'exercicios')."""
    b10, b13, b15 = _blocks_metodos_formais()
    entry = _entry("ExerciciosDafny2")
    markdown = "exercicios programacao e verificacao com dafny arrays metodos sobre arrays"
    weights = block_token_weights([b10, b13, b15])
    score_13 = _score(entry, markdown, b13, weights=weights)
    score_15 = _score(entry, markdown, b15, weights=weights)
    assert score_13 > score_15


def test_idf_pesa_token_por_raridade():
    b10, b13, b15 = _blocks_metodos_formais()
    weights = block_token_weights([b10, b13, b15])
    # hoare só no b10; arrays só no b13 -> peso cheio
    assert weights["hoare"] == 1.0
    assert weights["arrays"] == 1.0
    # dafny em 2 dos 3 candidatos -> 1/2
    assert abs(weights["dafny"] - 0.5) < 1e-9
    # tokens do nome do curso/área (UNIT_GENERIC_TOKENS) -> raridade ZERO:
    # estão em todo markdown via header, não distinguem bloco nenhum
    assert weights["logica"] == 0.0
    assert weights["programas"] == 0.0
    # tokens curtos (<4) e numéricos ficam fora
    assert "de" not in weights


def test_entry_hoare_prefere_bloco_hoare():
    """Plano T7/Step 1: entry 'logica de hoare triplas precondicao' tem que
    pontuar o bloco do hoare acima dos blocos verbosos com 'logica'."""
    b10, b13, b15 = _blocks_metodos_formais()
    entry = _entry("LogicaDeHoare", category="material-de-aula")
    markdown = "logica de hoare triplas precondicao"
    weights = block_token_weights([b10, b13, b15])
    score_10 = _score(entry, markdown, b10, weights=weights)
    assert score_10 > _score(entry, markdown, b13, weights=weights)
    assert score_10 > _score(entry, markdown, b15, weights=weights)


def test_weights_none_mantem_score_anterior():
    """Paridade: sem o kwarg (chamadores legados, ex. cronograma_health) e com
    topic_token_weights=None o score é IDÊNTICO."""
    b10, b13, b15 = _blocks_metodos_formais()
    entry = _entry("ExerciciosDafny2")
    markdown = "exercicios programacao e verificacao com dafny arrays"
    signals = collect_entry_unit_signals(entry, markdown)
    for block in (b10, b13, b15):
        kwargs = dict(
            normalize_match_text=normalize_match_text,
            score_text_against_row=score_text_against_row,
            score_card_evidence_against_entry_fn=lambda s, items: score_card_evidence_against_entry(
                s, items, normalize_match_text=normalize_match_text
            ),
            preferred_unit_slug="unidade-02-verificacao-de-programas",
        )
        sem_kwarg = score_entry_against_timeline_block(signals, block, **kwargs)
        com_none = score_entry_against_timeline_block(
            signals, block, topic_token_weights=None, **kwargs
        )
        assert sem_kwarg == com_none


def test_score_text_against_row_none_e_pesos_um_sao_identicos():
    """score_text_against_row: token_weights=None == pesos todos 1.0 (paridade
    da mecânica de pesos no nível da função)."""
    tokens = ["logica", "hoare", "triplas"]
    base = score_text_against_row("logica de hoare", tokens)
    assert score_text_against_row("logica de hoare", tokens, token_weights=None) == base
    assert score_text_against_row(
        "logica de hoare", tokens, token_weights={t: 1.0 for t in tokens}
    ) == base


def test_block_token_weights_usa_normalize_do_call_site():
    """Token divergente pelo normalize: "pre-condicao" com keep="+-./" é 1 token
    (12 chars, sem divisão), mas com o canônico vira "pre condicao" — "pre" (<4)
    é filtrado, só "condicao" entra.

    Cenário: 3 blocos, todos com "pre-condicao" no topic_text.
    Com normalize=_normalize_keep, o token "pre-condicao" aparece em df=3 →
    peso = 1/3 < 1.0 (IDF amortece).
    Sem o fix (normalize canônico), "pre-condicao" NÃO aparece no dict →
    default seria 1.0 (IDF escapa).
    """
    topic = "verificacao pre-condicao pos-condicao invariante"
    blocks = [
        _pblock(f"b{i}", topic, f"2026-0{i+1}-01", f"2026-0{i+1}-14")
        for i in range(3)
    ]
    weights_keep = block_token_weights(blocks, normalize=_normalize_keep)
    # Com o normalize correto, "pre-condicao" deve estar no dict com df=3 -> peso 1/3
    assert "pre-condicao" in weights_keep, (
        "BUG: 'pre-condicao' ausente — normalize canônico dividiu em 'pre'(filtrado)+'condicao'; "
        "IDF escapa (default 1.0) em vez de amortecer"
    )
    expected = 1.0 + 1.0 * (1.0 / 3.0 - 1.0)  # IDF_WEIGHT=1.0, df=3
    assert abs(weights_keep["pre-condicao"] - expected) < 1e-9

    # Canônico NÃO deve ter o token com hífen (ele vai para "condicao")
    weights_canonical = block_token_weights(blocks)
    assert "pre-condicao" not in weights_canonical


# --- S4 (P4): sinal de ferramenta entry x topic do bloco ---------------------

_U1 = "unidade-01-metodos-formais"


def _blocks_unidade1():
    """Geometria do erro real `provas`/`t1` no golden Metodos-Formais: b05
    (inducao em arvores) vence hoje materiais Isabelle de título neutro; b06 é
    o bloco do Isabelle."""
    b05 = _pblock(
        "bloco-05", "inducao arvores", "2026-03-30", "2026-04-06",
        sessions=["inducao estrutural arvores aula", "exercicios aula"],
        unit=_U1,
    )
    b06 = _pblock(
        "bloco-06", "interativa teoremas isabelle", "2026-04-08", "2026-04-15",
        sessions=["prova interativa de teoremas isabelle aula", "exercicios aula"],
        unit=_U1,
    )
    return b05, b06


def test_ferramenta_isabelle_puxa_bloco_isabelle():
    """Entry com auto_tag ferramenta:isabelle e título neutro: o bloco cujo
    topic contém o token da ferramenta (b06) tem que vencer o b05, e o ganho
    da tag no b06 tem que ser >= TOOL_BOOST (os canais legados de auto_tags
    sozinhos dão bem menos — sem S4 esta margem NÃO fecha)."""
    from src.builder.routing.thresholds import TOOL_BOOST

    b05, b06 = _blocks_unidade1()
    entry = _entry("exemplos", auto_tags=["ferramenta:isabelle"])
    weights = block_token_weights([b05, b06])
    score_05 = _score(entry, "", b05, weights=weights, unit_slug=_U1)
    score_06 = _score(entry, "", b06, weights=weights, unit_slug=_U1)
    assert score_06 > score_05
    sem_tag_06 = _score(_entry("exemplos"), "", b06, weights=weights, unit_slug=_U1)
    assert score_06 - sem_tag_06 >= TOOL_BOOST


def test_ferramenta_conflitante_penaliza():
    """Entry ferramenta:isabelle vs bloco de OUTRA ferramenta do mapa (dafny):
    o score COM a tag tem que sair menor que o score SEM a tag (penalidade)."""
    bloco_dafny = _pblock(
        "bloco-12", "terminacao introducao dafny", "2026-05-11", "2026-05-12",
        sessions=["terminacao introducao dafny aula"],
    )
    weights = block_token_weights([bloco_dafny])
    com_tag = _score(
        _entry("exemplos", auto_tags=["ferramenta:isabelle"]),
        "", bloco_dafny, weights=weights,
    )
    sem_tag = _score(_entry("exemplos"), "", bloco_dafny, weights=weights)
    assert com_tag < sem_tag


def test_ferramenta_sem_weights_nao_dispara():
    """Guard do S2: chamadores legados (sem topic_token_weights) não veem o
    sinal de ferramenta. Cenário de PENALIDADE (entry isabelle vs bloco dafny):
    os canais legados de auto_tags não casam nada neste topic, então sem o
    kwarg o score com/sem a tag é IDÊNTICO — a penalidade não vaza."""
    bloco_dafny = _pblock(
        "bloco-12", "terminacao introducao dafny", "2026-05-11", "2026-05-12",
        sessions=["terminacao introducao dafny aula"],
    )
    com_tag = _score(_entry("exemplos", auto_tags=["ferramenta:isabelle"]), "", bloco_dafny)
    sem_tag = _score(_entry("exemplos"), "", bloco_dafny)
    assert com_tag == sem_tag


def test_ferramenta_por_extensao_thy_sem_auto_tags():
    """S4b: .thy SEM auto_tags ferramenta: deriva isabelle da EXTENSÃO do
    source_path — os .thy do manifest real não têm ferramenta:isabelle."""
    entry = _entry("intro")
    entry["source_path"] = "x/intro.thy"
    signals = collect_entry_unit_signals(entry, "")
    assert "isabelle" in signals["tool_tags_text"].split()


def test_ferramenta_por_extensao_dfy_via_raw_target():
    """S4b: a extensão também vale via raw_target (o harness do eval só
    repassa raw_target) e .dfy mapeia para dafny."""
    entry = _entry("exemplos")
    entry["raw_target"] = "Exemplos.DFY"
    signals = collect_entry_unit_signals(entry, "")
    assert "dafny" in signals["tool_tags_text"].split()


def test_ferramenta_extensao_uniao_com_auto_tags_dedupada():
    """União dos dois sinais, dedupada: auto_tag isabelle + .thy não duplica;
    extensão fora do mapa (.pdf) não acrescenta nada."""
    entry = _entry("intro", auto_tags=["ferramenta:isabelle"])
    entry["source_path"] = "x/intro.thy"
    signals = collect_entry_unit_signals(entry, "")
    assert signals["tool_tags_text"].split().count("isabelle") == 1
    entry_pdf = _entry("intro")
    entry_pdf["source_path"] = "x/intro.pdf"
    assert "tool" not in collect_entry_unit_signals(entry_pdf, "")["tool_tags_text"]
    assert collect_entry_unit_signals(entry_pdf, "")["tool_tags_text"] == ""


def test_extensao_thy_puxa_bloco_isabelle_fim_a_fim():
    """Cenário real t1/provas: entry .thy de título neutro, SEM auto_tags,
    entre b05 (inducao arvores) e b06 (interativa teoremas isabelle) —
    isabelle vence pela extensão (mesmo shape do teste da T9)."""
    b05, b06 = _blocks_unidade1()
    entry = _entry("provas")
    entry["source_path"] = "Provas por Inducao/provas.thy"
    weights = block_token_weights([b05, b06])
    score_05 = _score(entry, "", b05, weights=weights, unit_slug=_U1)
    score_06 = _score(entry, "", b06, weights=weights, unit_slug=_U1)
    assert score_06 > score_05


def test_ferramenta_fora_do_mapa_ignorada():
    """ferramenta:proposicional não é ferramenta de verdade (ruído do
    extrator) — fora de TOOL_TOKENS, não dá boost nem penalidade."""
    b05, b06 = _blocks_unidade1()
    weights = block_token_weights([b05, b06])
    entry = _entry("exemplos", auto_tags=["ferramenta:proposicional"])
    entry_sem = _entry("exemplos")
    for block in (b05, b06):
        com = _score(entry, "", block, weights=weights, unit_slug=_U1)
        sem = _score(entry_sem, "", block, weights=weights, unit_slug=_U1)
        # auto_tags_text muda (canal 0.12), mas "ferramenta proposicional" não
        # casa topic nenhum destes blocos -> score idêntico
        assert com == sem
