"""Higiene do topic_text agregado (Task 2b, campanha 2 FIX3): linha
NAO-letiva (suspensao/feriado/recesso) mesclada num bloco de aula nao pode
vazar pro topic_text/topicos agregados de `_extract_timeline_topics`. As
sessions do bloco ficam intactas (auditoria/GUI) -- so a agregacao filtra.

Fixture do bloco misto copia o contrato real (IA .timeline_index.json,
bloco-06, uuid 17ea65f3-5f84-47c7-9357-e090ee1f80ed, conferido em disco
2026-08-10): content reconstruido a partir do `session.label` persistido
(o content bruto da linha do cronograma nao e persistido no indice; o label
e determinismo puro do mesmo pipeline de normalizacao, confirmado batendo
com o topic_text real gravado antes deste fix)."""
from src.builder.timeline.index import _extract_timeline_topics


def test_ia_bloco06_topic_text_nao_vaza_suspensao():
    rows = [
        {"content": "suspensao de aulas aula"},
        {"content": "ml abordagem nao supervisionada k means exercicios aula"},
        {"content": "ml abordagem nao supervisionada hierarquico exercicios analise de resultados aula"},
    ]
    topics, aliases, topic_text = _extract_timeline_topics(rows)
    assert "suspensao" not in topic_text.split()
    assert "suspensao" not in topics
    # topicos reais das 2 aulas continuam presentes
    assert "supervisionada" in topic_text.split()
    assert "hierarquico" in topic_text.split()


def test_bloco_so_aulas_topic_text_identico_sem_linha_admin():
    # Nao-regressao: bloco sem nenhuma linha administrativa nao muda em nada.
    rows = [
        {"content": "ml abordagem nao supervisionada k means exercicios aula"},
        {"content": "ml abordagem nao supervisionada hierarquico exercicios analise de resultados aula"},
    ]
    before = _extract_timeline_topics(rows)
    assert "suspensao" not in before[2]
    assert before[2] == "abordagem supervisionada means hierarquico analise resultados"


def test_bloco_100_por_cento_administrativo_mantem_topic_text():
    # Nao-regressao critica: bloco de feriado PURO (SO bloco-04/06/15 reais)
    # continua com topic_text="feriado" -- e esse texto que hoje alimenta o
    # classifier (keyword HOLIDAY via topic_text). Filtrar aqui tambem
    # quebraria a classificacao de feriado.
    rows = [{"content": "feriado aula"}]
    topics, aliases, topic_text = _extract_timeline_topics(rows)
    assert topic_text == "feriado"
