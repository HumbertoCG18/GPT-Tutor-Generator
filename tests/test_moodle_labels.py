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
