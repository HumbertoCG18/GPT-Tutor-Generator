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
        # D2: bloco administrativo se sinaliza pelas rows (sinal real), nao pela
        # chave morta administrative_only que o runtime nunca escreve.
        b["rows"] = [{"content": "Feriado"}]
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


# --- merge_card_block_map (Task 4: manual sobrepoe) ---
from src.builder.sources.moodle_labels import merge_card_block_map

def test_merge_manual_sobrepoe_auto():
    existing = {"Revisão": {"block_ids": ["bloco-02"], "source": "manual"}}
    derived = {"Revisão": {"block_ids": ["bloco-03"], "source": "labels", "format": "A", "dates": []},
               "Novo": {"block_ids": ["bloco-05"], "source": "labels", "format": "A", "dates": []}}
    out = merge_card_block_map(existing, derived)
    assert out["Revisão"]["block_ids"] == ["bloco-02"]      # manual intocado
    assert out["Novo"]["block_ids"] == ["bloco-05"]

def test_merge_labels_antigo_e_atualizado():
    existing = {"X": {"block_ids": ["bloco-01"], "source": "labels"}}
    derived = {"X": {"block_ids": ["bloco-02"], "source": "labels", "format": "A", "dates": []}}
    assert merge_card_block_map(existing, derived)["X"]["block_ids"] == ["bloco-02"]

def test_merge_entrada_manual_sem_derivacao_sobrevive():
    existing = {"So Manual": {"block_ids": ["bloco-07"], "source": "manual"}}
    assert merge_card_block_map(existing, {})["So Manual"]["block_ids"] == ["bloco-07"]


# --- extract_assign_deadlines (Task 10 / S5: janela de assign) ---
from src.builder.sources.moodle_labels import extract_assign_deadlines

def test_assign_duedate_estruturado():
    sec = {"name": "TDE", "modules": [
        {"modname": "assign", "name": "Sala de entrega",
         "dates": [{"label": "Vencimento:", "timestamp": 1778122740, "dataid": "duedate"}]}]}
    out = extract_assign_deadlines([sec])
    assert out["TDE"] == "2026-05-06"

def test_deadline_no_nome_do_forum():
    sec = {"name": "Verificação de Programas", "modules": [
        {"modname": "forum", "name": "Sala de Entrega (10/06)", "dates": []}]}
    out = extract_assign_deadlines([sec], year=2026)
    assert out[list(out)[0]] == "2026-06-10"

def test_assign_tem_precedencia_sobre_nome():
    # seção com assign.dates E forum com data no nome → vale o assign
    sec = {"name": "TDE", "modules": [
        {"modname": "forum", "name": "Sala de Entrega (10/06)", "dates": []},
        {"modname": "assign", "name": "Sala de entrega",
         "dates": [{"label": "Vencimento:", "timestamp": 1778122740, "dataid": "duedate"}]}]}
    out = extract_assign_deadlines([sec], year=2026)
    assert out["TDE"] == "2026-05-06"

def test_sem_fonte_sem_deadline():
    sec = {"name": "X", "modules": [{"modname": "forum", "name": "Forum geral"}]}
    assert extract_assign_deadlines([sec]) == {}


# --- build_lesson_topic_index (alavanca 0: indice course-level data->topico) ---
from src.builder.sources.moodle_labels import build_lesson_topic_index

def test_index_mapeia_data_para_topico_da_lesson():
    out = build_lesson_topic_index([_sec("Provas por Indução", [_A])], year=2026)
    assert out["version"] == 1
    by_date = out["by_date"]
    assert "Provas em Isabelle" in by_date["2026-04-13"]
    assert "revis" in by_date["2026-04-15"].lower()

def test_index_data_sem_texto_fica_fora():
    # data avulsa (LOOSE, sem ': texto') entra em dates mas NAO vira lesson texto
    out = build_lesson_topic_index([_sec("TDE", ["<p>(03/07/2026)</p>"])], year=2026)
    assert "2026-07-03" not in out["by_date"]

def test_index_secao_sem_sinal_by_date_vazio():
    out = build_lesson_topic_index([_sec("Threads", [])], year=2026)
    assert out == {"version": 1, "by_date": {}}

def test_index_colisao_de_data_concatena_textos():
    s1 = _sec("Card A", ["<p>(04/03/2026): Tema A.</p>"])
    s2 = _sec("Card B", ["<p>(04/03/2026): Tema B.</p>"])
    out = build_lesson_topic_index([s1, s2], year=2026)
    txt = out["by_date"]["2026-03-04"]
    assert "Tema A" in txt and "Tema B" in txt


# --- captação robusta: resumo DENTRO do card com data SEM ANO (90% dos casos) ---
def test_index_year_less_semana_dentro_parens():
    # (11/05): topico + "Semana DD/MM a DD/MM" DENTRO do card (sem ano)
    s = _sec("Verificacao de Programas",
             ["Semana 11/05 a 15/05:\n(11/05): Introducao ao Dafny;\n(13/05): Arrays em Dafny."])
    idx = build_lesson_topic_index([s], year=2026)["by_date"]
    assert "Introducao" in idx.get("2026-05-11", "")
    assert "Arrays" in idx.get("2026-05-13", "")

def test_index_year_less_semana_dentro_sem_parens():
    s = _sec("Verificacao de Programas",
             ["Semana 11/05 a 15/05:\n11/05: Introducao ao Dafny;\n13/05: Arrays em Dafny."])
    idx = build_lesson_topic_index([s], year=2026)["by_date"]
    assert "Introducao" in idx.get("2026-05-11", "")
    assert "Arrays" in idx.get("2026-05-13", "")

def test_index_year_less_semana_no_nome_parens():
    # semana no NOME do card + lessons em parênteses sem ano (formato B paren-opcional)
    s = _sec("Semana 5 - 11/05 a 15/05 - Dafny",
             ["(11/05): Introducao ao Dafny;\n(13/05): Arrays em Dafny."])
    idx = build_lesson_topic_index([s], year=2026)["by_date"]
    assert "Introducao" in idx.get("2026-05-11", "")
