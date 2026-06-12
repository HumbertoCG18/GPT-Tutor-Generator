"""Parser de labels temporais dos cards Moodle (formatos A-D do catálogo)."""
from src.builder.sources.moodle_labels import parse_card_dates

def _sec(name, labels=(), modname="label"):
    return {"name": name, "modules": [
        {"modname": modname, "name": "", "description": d} for d in labels]}

_A = """<p>Semana 13/04/2026 a 17/04/2026:</p>
<p>(13/04/2026): Provas em Isabelle, exerc&iacute;cios;</p>
<p>(15/04/2026): Exerc&iacute;cios de revis&atilde;o para P1.</p>
<p>(atividade ass&iacute;ncrona): exerc&iacute;cios.</p>"""

def test_formato_a_extrai_aulas_com_data_completa():
    out = parse_card_dates([_sec("Provas por Indução", [_A])], year=2026)
    card = out["Provas por Indução"]
    assert card["format"] == "A"
    assert "2026-04-13" in card["dates"] and "2026-04-15" in card["dates"]
    assert ("2026-04-13", "2026-04-17") in card["weeks"]
    texts = {l["date"]: l["text"] for l in card["lessons"]}
    assert "revis" in texts["2026-04-15"].lower()

def test_formato_a_ignora_linha_assincrona():
    out = parse_card_dates([_sec("X", [_A])], year=2026)
    assert all(l["date"] for l in out["X"]["lessons"])

def test_formato_a_data_avulsa_fora_do_padrao():
    lbl = "<p>Trabalho Final (03/07/2026):</p>"
    out = parse_card_dates([_sec("TDE", [lbl])], year=2026)
    assert "2026-07-03" in out["TDE"]["dates"]

def test_data_invalida_descartada_sem_excecao():
    lbl = "<p>(30/02/2026): aula fantasma;</p><p>(04/03/2026): real.</p>"
    out = parse_card_dates([_sec("X", [lbl])], year=2026)
    assert out["X"]["dates"] == ["2026-03-04"]

def test_secao_sem_labels_fica_fora():
    out = parse_card_dates([_sec("Threads", [])], year=2026)
    assert "Threads" not in out


def test_formato_b_nome_da_secao_e_roteiro():
    sec = {"name": "Semana 5 -30/03 a 01/04: ML - Aprendizado Supervisionado",
           "modules": [{"modname": "label", "name": "",
                        "description": "<p>Roteiro</p><p>30/03: Rede Perceptron; Exercicios</p><p>01/04: Rede MLP.</p>"}]}
    out = parse_card_dates([sec], year=2026)
    card = out[list(out)[0]]
    assert card["format"] == "B"
    assert "2026-03-30" in card["dates"] and "2026-04-01" in card["dates"]
    assert ("2026-03-30", "2026-04-01") in card["weeks"]

def test_formato_b_tolerante_dia_sem_zero():
    sec = {"name": "Semana 8 - 20/04 a 24/4 - ML", "modules": []}
    out = parse_card_dates([sec], year=2026)
    assert ("2026-04-20", "2026-04-24") in out[list(out)[0]]["weeks"]

def test_formato_c_aula_numerada():
    lbl = "<p>Aula 2 - 05/03</p><p>CONTEÚDO: Contexto da Área</p>"
    sec = {"name": "Fundamentos de IHC/UX",
           "modules": [{"modname": "label", "name": "", "description": lbl}]}
    out = parse_card_dates([sec], year=2026)
    card = out["Fundamentos de IHC_UX"] if "Fundamentos de IHC_UX" in out else out[list(out)[0]]
    assert card["format"] == "C"
    assert "2026-03-05" in card["dates"]

def test_formato_d_semana_ordinal_so_com_ancora():
    sec = {"name": "Semana 7 - Halteproblem und Entscheidungsproblem", "modules": []}
    out = parse_card_dates([sec], year=2026)
    assert list(out) == []          # sem week_anchor -> degrada (fora)
    out2 = parse_card_dates([sec], year=2026, week_anchor="2026-03-02")
    card = out2[list(out2)[0]]
    assert card["format"] == "D"
    # semana 7 = anchor + 6*7 dias: 13/04 a 17/04 (seg-sex)
    assert card["weeks"] == [("2026-04-13", "2026-04-17")]

def test_formato_a_tem_precedencia_sobre_b():
    sec = {"name": "Semana 1 - 02/03 a 06/03 - Intro",
           "modules": [{"modname": "label", "name": "",
                        "description": "<p>(04/03/2026): aula com ano completo.</p>"}]}
    out = parse_card_dates([sec], year=2026)
    assert out[list(out)[0]]["format"] == "A"


from src.builder.sources.moodle_labels import derive_card_block_map

def _blk(bid, start, end, admin=False):
    b = {"id": bid, "period_start": start, "period_end": end}
    if admin:
        b["administrative_only"] = True
    return b

_BLOCKS = [_blk("bloco-03", "2026-03-09", "2026-03-09"),
           _blk("bloco-04", "2026-03-11", "2026-03-25"),
           _blk("bloco-08", "2026-04-20", "2026-04-20", admin=True)]

def test_derive_intersecta_datas_de_aula_com_periodos():
    cards = {"Revisão": {"format": "A", "weeks": [],
                         "dates": ["2026-03-09", "2026-03-11"], "lessons": []}}
    out = derive_card_block_map(cards, _BLOCKS)
    assert out["Revisão"]["block_ids"] == ["bloco-03", "bloco-04"]
    assert out["Revisão"]["source"] == "labels"

def test_derive_ignora_bloco_administrativo():
    cards = {"X": {"format": "A", "weeks": [], "dates": ["2026-04-20"], "lessons": []}}
    assert "X" not in derive_card_block_map(cards, _BLOCKS)

def test_derive_usa_weeks_quando_nao_ha_dates():
    cards = {"D": {"format": "D", "weeks": [("2026-03-09", "2026-03-13")],
                   "dates": [], "lessons": []}}
    out = derive_card_block_map(cards, _BLOCKS)
    assert "bloco-03" in out["D"]["block_ids"] and "bloco-04" in out["D"]["block_ids"]

def test_derive_card_sem_match_fica_fora():
    cards = {"X": {"format": "A", "weeks": [], "dates": ["2027-01-01"], "lessons": []}}
    assert derive_card_block_map(cards, _BLOCKS) == {}
