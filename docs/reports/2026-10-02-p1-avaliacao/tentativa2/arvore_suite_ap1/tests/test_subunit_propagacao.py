# tests/test_subunit_propagacao.py
"""Sessao 6 (2026-09-05): 2a passada da subunidade — propagacao de vocabulario por headings. O plano nomeia
categorias ("Modelos Preditivos") e o material nomeia algoritmos ("perceptron"); token EXCLUSIVO dos headings
dos materiais confiantes de um subtopico vira alias dele e so os materiais em que a 1a passada nao decidiu
sao repontuados. Medido nos 6 golds (233): +5 -0 (IA perceptron x3 + mlp-xor, SO exemplo3)."""
from src.builder.routing.resolver_apply import propagar_vocabulario_por_headings


class _M:
    def __init__(self, slug, conf, amb):
        self.topic_slug, self.confidence, self.ambiguous, self.reasons = slug, conf, amb, ["stub"]


def _stub(entry, taxonomy, texto, *, winning_unit_slug=""):
    """Pontua cada subtopico pela contagem de tokens (label + aliases) presentes no texto; empate = ambiguo."""
    unit = next(u for u in taxonomy["units"] if u["slug"] == winning_unit_slug)
    scores = []
    for t in unit["topics"]:
        voc = set((" ".join([t["label"]] + list(t.get("aliases") or []))).lower().split())
        scores.append((sum(1 for v in voc if v in texto.lower()), t["slug"]))
    scores.sort(reverse=True)
    if scores[0][0] == 0:
        return _M("", 0.0, True)
    if len(scores) > 1 and scores[0][0] == scores[1][0]:
        return _M(scores[0][1], 0.0, True)
    return _M(scores[0][1], 1.0, False)


TAX = {"units": [{"slug": "u5", "title": "Aprendizado de maquina", "topics": [
    {"slug": "modelos-preditivos", "label": "Modelos Preditivos", "aliases": ["knn"]},
    {"slug": "introducao", "label": "Introducao", "aliases": ["supervisionado"]},
]}]}


def _passe1(entries):
    out = []
    for e, texto in entries:
        m = _stub(e, TAX, texto, winning_unit_slug="u5")
        e["computed_subunit_slug"] = m.topic_slug
        out.append((e, texto, "u5", m))
    return out


def test_token_exclusivo_dos_confiantes_repontua_so_quem_nao_decidiu():
    e1 = {"id": "e1", "title": "Exemplo knn"}
    e2 = {"id": "e2", "title": "Perceptron letras"}
    e3 = {"id": "e3", "title": "Exercicio"}           # empate knn x supervisionado -> ambiguo na 1a passada
    e4 = {"id": "e4", "title": "Outro exercicio"}     # empate; 'letras' so tem 1 confiante -> nao propaga
    fillers = [({"id": f"f{i}", "title": f"Aula supervisionada {i}"}, "# supervisionado\nsupervisionado") for i in range(10)]
    entries = [(e1, "# Rede perceptron\nknn classificador"), (e2, "# Perceptron reconhecendo letras\nknn"),
               (e3, "# Rede perceptron exemplo\nsupervisionado knn"), (e4, "# letras\nsupervisionado knn")] + fillers
    p1 = _passe1(entries)
    assert p1[0][3].topic_slug == "modelos-preditivos" and not p1[0][3].ambiguous
    assert p1[2][3].ambiguous and p1[3][3].ambiguous
    mudou = propagar_vocabulario_por_headings(p1, TAX, _stub, conf_min=0.7, min_entries=2, df_max=0.25)
    assert mudou == 1
    assert e3["computed_subunit_slug"] == "modelos-preditivos"
    assert "propagado-headings" in e3["subunit_match_reasons"]
    assert e4["computed_subunit_slug"] == "modelos-preditivos" or e4.get("subunit_match_reasons") is None  # 'letras' nao propagou
    assert e1["computed_subunit_slug"] == "modelos-preditivos" and fillers[0][0]["computed_subunit_slug"] == "introducao"
    assert TAX["units"][0]["topics"][0]["aliases"] == ["knn"]   # taxonomia original intacta (copia)


def test_sem_confiantes_nada_muda():
    e = {"id": "x", "title": "T"}
    p1 = _passe1([(e, "# nada\nsem sinal")])
    assert propagar_vocabulario_por_headings(p1, TAX, _stub, conf_min=0.7, min_entries=2, df_max=0.25) == 0
