from src.builder.artifacts import repo


def _blocks_with_sessions():
    return [
        {
            "id": "bloco-04",
            "period_label": "Semana 11/03",
            "primary_topic_label": "Especificações Indutivas",
            "topics": ["conjuntos indutivos"],
            "unit_slug": "unidade-01",
            "sessions": [
                {"id": "s1", "date": "2026-03-11", "kind": "class",
                 "label": "conjuntos indutivos e equacoes recursivas", "signals": []},
                {"id": "s2", "date": "2026-03-18", "kind": "class",
                 "label": "estudo de caso listas", "signals": []},
            ],
        },
        {
            "id": "bloco-09",
            "period_label": "Semana 22/04",
            "primary_topic_label": "",
            "topics": [],
            "unit_slug": "unidade-01",
            "sessions": [
                {"id": "s3", "date": "2026-04-22", "kind": "assessment",
                 "label": "prova p1", "signals": []},
            ],
        },
    ]


def test_render_lists_sessions_by_date_with_weekday():
    md = repo.cronograma_detalhado_md({"course_name": "MF"}, [], {}, _blocks_with_sessions())
    assert "### Sessões" in md
    assert "qua 11/03" in md          # 2026-03-11 é quarta
    assert "estudo de caso listas" in md
    assert "qua 18/03" in md


def test_render_marks_assessment_session():
    md = repo.cronograma_detalhado_md({"course_name": "MF"}, [], {}, _blocks_with_sessions())
    assert "⏱" in md
    assert "prova p1" in md


def test_render_block_without_sessions_omits_section():
    blocks = [{"id": "b1", "period_label": "Aula 1", "topics": [], "sessions": []}]
    md = repo.cronograma_detalhado_md({"course_name": "ED"}, [], {}, blocks)
    assert "### Sessões" not in md


def test_render_session_with_empty_date_does_not_crash():
    blocks = [{
        "id": "b1", "period_label": "Aula 1", "topics": [],
        "sessions": [{"id": "s", "date": "", "kind": "async", "label": "atividade ead", "signals": []}],
    }]
    md = repo.cronograma_detalhado_md({"course_name": "ED"}, [], {}, blocks)
    assert "atividade ead" in md
    assert "(sem data)" in md


def _blk(bid, label, topic_text, sess_label, date):
    return {"id": bid, "kind": "class", "period_label": f"Semana {date[8:]}/{date[5:7]}", "period_start": date,
            "primary_topic_label": label, "topic_text": topic_text, "topics": [], "unit_slug": "unidade-01",
            "sessions": [{"id": f"s-{bid}", "date": date, "kind": "class", "label": sess_label, "signals": []}]}


def test_titulo_de_bloco_repetido_ganha_qualificador_so_na_colisao():
    """C1 item 2 (05/09): 6 dos 8 cursos tem blocos-aula com o mesmo label (16 blocos, 33 materiais); o LLM le o
    CRONOGRAMA_DETALHADO para o "quando" e trocou bloco-02 por bloco-20 no FR ("Modelos OSI e TCP/IP" x2). Em colisao,
    o titulo ganha o topic_text do bloco; sem colisao, nada muda."""
    blocks = [
        _blk("bloco-06", "Modelos OSI e TCP/IP", "camada transporte", "camada de transporte udp tcp aula", "2026-09-03"),
        _blk("bloco-07", "Endereçamento", "camada rede enderecamento", "camada de rede enderecamento ip aula", "2026-09-10"),
        _blk("bloco-22", "Modelos OSI e TCP/IP", "camada fisica sockets", "camada fisica e raw sockets aula", "2026-11-10"),
    ]
    md = repo.cronograma_detalhado_md({"course_name": "FR"}, [], {}, blocks)
    heads = [l for l in md.splitlines() if l.startswith("## ")]
    assert heads[0].endswith("— Modelos OSI e TCP/IP · Camada transporte")
    assert heads[2].endswith("— Modelos OSI e TCP/IP · Camada fisica sockets")
    assert heads[1].endswith("— Endereçamento")            # sem colisao: intacto


def test_titulo_repetido_com_mesmo_topic_text_usa_a_sessao():
    # SO "Paginacao" x2: topic_text igual, sessoes diferentes -> qualifica pela 1a sessao
    blocks = [
        _blk("bloco-13", "Paginação", "paginacao", "paginacao conceitos aula", "2026-05-12"),
        _blk("bloco-16", "Paginação", "paginacao", "paginacao exercicios aula", "2026-05-21"),
    ]
    heads = [l for l in repo.cronograma_detalhado_md({"course_name": "SO"}, [], {}, blocks).splitlines() if l.startswith("## ")]
    assert heads[0].endswith("— Paginação · Paginacao conceitos aula")
    assert heads[1].endswith("— Paginação · Paginacao exercicios aula")


def test_bloco_nao_aula_repetido_nao_ganha_qualificador():
    # feriado/entrega/evento repetem label por natureza; qualificar seria ruido ("Feriado · Feriado aula")
    a = _blk("bloco-05", "Feriado", "feriado", "feriado aula", "2026-04-21"); a["kind"] = "holiday"
    b = _blk("bloco-08", "Feriado", "feriado", "feriado aula", "2026-05-01"); b["kind"] = "holiday"
    heads = [l for l in repo.cronograma_detalhado_md({"course_name": "SO"}, [], {}, [a, b]).splitlines() if l.startswith("## ")]
    assert all(h.endswith("— Feriado") for h in heads)
