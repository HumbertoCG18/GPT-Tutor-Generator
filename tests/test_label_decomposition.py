# tests/test_label_decomposition.py
"""Sessao 6 (2026-09-06): partes do rotulo composto do plano viram aliases na 2a passada da subunidade
(`resolver_apply._partes_de_rotulo`, dentro de `propagar_vocabulario_por_headings`). O plano nomeia a frase
('Bezier e Algoritmo de Casteljau'); o material nomeia a parte ('bezier-cpp'); o scorer casa frases inteiras.
Medido nos 6 golds (233) pela 1a passada: +9 -1; pela 2a passada so os nao-confiantes mudam."""
from src.builder.routing.resolver_apply import _partes_de_rotulo, propagar_vocabulario_por_headings
from src.builder.timeline.index import _label_parts


class _M:
    def __init__(self, slug, conf, amb):
        self.topic_slug, self.confidence, self.ambiguous, self.reasons = slug, conf, amb, ["stub"]


def _stub(entry, taxonomy, texto, *, winning_unit_slug=""):
    """Conta frases (label + aliases, normalizadas de forma simples) presentes no texto; empate = ambiguo."""
    unit = next(u for u in taxonomy["units"] if u["slug"] == winning_unit_slug)
    scores = []
    for t in unit["topics"]:
        frases = [t["label"]] + list(t.get("aliases") or [])
        scores.append((sum(1 for f in frases if f.lower() in texto.lower()), t["slug"]))
    scores.sort(reverse=True)
    if scores[0][0] == 0:
        return _M("", 0.0, True)
    if len(scores) > 1 and scores[0][0] == scores[1][0]:
        return _M(scores[0][1], 0.0, True)
    return _M(scores[0][1], 1.0, False)


TAX = {"units": [
    {"slug": "u7", "title": "Representação e modelagem de objetos", "topics": [
        {"slug": "bezier-e-algoritmo-de-casteljau", "label": "Bezier e Algoritmo de Casteljau", "aliases": []},
        {"slug": "hermite", "label": "Hermite", "aliases": []},
    ]},
    {"slug": "u2", "title": "Fundamentos matematicos", "topics": [
        {"slug": "algoritmos-de-geometria-computacional", "label": "Algoritmos de Geometria Computacional", "aliases": []},
        {"slug": "algoritmos-de-poligonos", "label": "Algoritmos de Poligonos", "aliases": []},
    ]},
    {"slug": "u7b", "title": "Gerencia de entrada e saida", "topics": [
        {"slug": "dispositivos-de-entrada-e-saida", "label": "Dispositivos de entrada e saida", "aliases": []},
        {"slug": "drivers", "label": "Drivers dos dispositivos", "aliases": []},
    ]},
]}
UNITS = {u["slug"]: u for u in TAX["units"]}


def _passe1(entries):
    out = []
    for e, texto, unit in entries:
        m = _stub(e, TAX, texto, winning_unit_slug=unit)
        e["computed_subunit_slug"] = m.topic_slug
        out.append((e, texto, unit, m))
    return out


def test_label_parts():
    assert _label_parts("Bezier e Algoritmo de Casteljau", set()) == ["Bezier", "Algoritmo de Casteljau"]
    assert _label_parts("Algoritmos de Geometria Computacional", {"algoritmos"}) == ["Geometria Computacional"]
    assert _label_parts("Algoritmos de Geometria Computacional", set()) == []
    assert _label_parts("Hermite", set()) == []


def test_partes_exclusivas_no_curso_e_dentro_do_teto_de_df():
    fillers = [({"id": f"f{i}"}, f"aula {i} sobre hermite", "u7") for i in range(8)]
    p1 = _passe1([({"id": "b"}, "codigo bezier em C++", "u7"), ({"id": "g"}, "exercicios de geometria computacional", "u2"),
                  ({"id": "s"}, "buffer de saida do driver", "u7b")] + fillers)
    partes = _partes_de_rotulo(UNITS, p1, df_max=0.25)
    assert partes[("u7", "bezier-e-algoritmo-de-casteljau")] == {"Bezier", "Algoritmo de Casteljau"}
    assert partes[("u2", "algoritmos-de-geometria-computacional")] == {"Geometria Computacional"}   # cabeca 'algoritmos' generica (2 rotulos)
    # 'saida' esta no titulo da unidade "Gerencia de entrada e saida": nao nomeia o subtopico -> fora
    assert "saida" not in {p.lower() for p in partes.get(("u7b", "dispositivos-de-entrada-e-saida"), set())}
    assert "Dispositivos de entrada" in partes[("u7b", "dispositivos-de-entrada-e-saida")]


def test_parte_acima_do_teto_de_df_nao_entra():
    fillers = [({"id": f"f{i}"}, f"bezier aula {i}", "u7") for i in range(8)]   # 'bezier' em 9/9 materiais
    p1 = _passe1([({"id": "b"}, "codigo bezier em C++", "u7")] + fillers)
    assert "Bezier" not in _partes_de_rotulo(UNITS, p1, df_max=0.25).get(("u7", "bezier-e-algoritmo-de-casteljau"), set())


def test_segunda_passada_usa_a_parte_so_onde_a_primeira_nao_decidiu():
    e_vazio = {"id": "b"}
    e_conf = {"id": "h"}
    fillers = [({"id": f"f{i}"}, f"aula {i} de hermite", "u7") for i in range(8)]
    p1 = _passe1([(e_vazio, "codigo bezier em C++", "u7"), (e_conf, "bezier e hermite lado a lado", "u7")] + fillers)
    assert p1[0][3].topic_slug == "" and p1[0][3].ambiguous          # 1a passada: nada casa a frase inteira
    assert p1[1][3].topic_slug == "hermite" and not p1[1][3].ambiguous
    mudou = propagar_vocabulario_por_headings(p1, TAX, _stub, conf_min=0.7, min_entries=2, df_max=0.25)
    assert mudou == 1
    assert e_vazio["computed_subunit_slug"] == "bezier-e-algoritmo-de-casteljau"
    assert "rotulo-decomposto" in e_vazio["subunit_match_reasons"]
    assert e_conf["computed_subunit_slug"] == "hermite"              # decisao confiante nunca e sobreposta
    assert TAX["units"][0]["topics"][0]["aliases"] == []             # taxonomia original intacta (copia)


def test_titulo_que_nomeia_outro_subtopico_vence_decisao_confiante():
    """CG 'Exercicios de geometria computacional': corpo cheio de 'Vetor/Pontos/Retas' (entidades-geometricas, confiante),
    titulo nomeia a parte 'Geometria Computacional' de "Algoritmos de Geometria Computacional" e nao nomeia o vencedor."""
    tax = {"units": [{"slug": "u2", "title": "Fundamentos matematicos", "topics": [
        {"slug": "algoritmos-de-geometria-computacional", "label": "Algoritmos de Geometria Computacional", "aliases": []},
        {"slug": "algoritmos-de-poligonos", "label": "Algoritmos de Poligonos", "aliases": []},
        {"slug": "entidades-geometricas", "label": "Entidades geometricas", "aliases": ["Vetores"]},
    ]}]}
    e = {"id": "ex", "title": "Exercicios de geometria computacional"}
    e2 = {"id": "ex2", "title": "Exercicios de geometria computacional sobre entidades geometricas"}   # titulo nomeia o vencedor: fica
    fillers = [({"id": f"f{i}", "title": f"Aula {i}"}, f"vetores {i}", "u2") for i in range(8)]
    entries = [(e, "vetores vetores vetores", "u2"), (e2, "vetores vetores", "u2")] + fillers
    p1 = []
    for ent, texto, unit in entries:
        m = _stub(ent, tax, texto, winning_unit_slug=unit)
        ent["computed_subunit_slug"] = m.topic_slug
        p1.append((ent, texto, unit, m))
    assert e["computed_subunit_slug"] == "entidades-geometricas" and not p1[0][3].ambiguous
    mudou = propagar_vocabulario_por_headings(p1, tax, _stub, conf_min=0.7, min_entries=2, df_max=0.25)
    assert mudou == 1
    assert e["computed_subunit_slug"] == "algoritmos-de-geometria-computacional"
    assert "titulo-nomeia-subtopico" in e["subunit_match_reasons"]
    assert e2["computed_subunit_slug"] == "entidades-geometricas"
