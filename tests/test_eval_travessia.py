"""Regua de TRAVESSIA do tutor (02/09): pergunta do aluno -> arquivo/bloco esperado, medida sobre os
indices Markdown que o tutor recebe (COURSE_MAP, SYLLABUS, CRONOGRAMA_DETALHADO, FILE_MAP). LLM so para
MEDIR (baseline), cacheado; piso deterministico por sobreposicao de tokens. Sem chamada real no pytest."""
import json

from scripts.eval_travessia import (
    Resposta, casar, chave_cache, contexto_navegacao, escolher_sem_llm, pontuar, rodar,
)

ENTRIES = [
    {"id": "algoritmo-de-classificacao-k-nn", "title": "Algoritmo de Classificação k-NN", "category": "material-de-aula",
     "raw_target": "raw/pdfs/material-de-aula/algoritmo-de-classificacao-k-nn.pdf", "moodle_label": "Algoritmo de Classificação k-NN",
     "temporal_block_id": "u-5", "computed_subunit_slug": "modelos-preditivos"},
    {"id": "analise-exploratoria-de-dados-exemplo-1", "title": "Análise Exploratória de Dados - Exemplo 1", "category": "codigo-professor",
     "raw_target": "raw/code/analise-exploratoria-de-dados-exemplo-1.ipynb", "moodle_label": "AED exemplo 1",
     "temporal_block_id": "u-4", "computed_subunit_slug": "introducao-ao-aprendizado-de-maquina"},
    {"id": "plano-de-ensino", "title": "Plano de Ensino", "category": "cronograma", "raw_target": "raw/pdfs/cronograma/plano.pdf",
     "temporal_block_id": "u-1", "computed_subunit_slug": ""},
]
BLOCKS = [{"id": "bloco-01", "block_uuid": "u-1"}, {"id": "bloco-04", "block_uuid": "u-4"}, {"id": "bloco-05", "block_uuid": "u-5"}]


# --- casamento esperado/escolha -> ids ------------------------------------------

def test_casar_por_id_titulo_ou_raw():
    assert casar("algoritmo-de-classificacao-k-nn", ENTRIES) == {"algoritmo-de-classificacao-k-nn"}
    assert casar("Classificação k-NN", ENTRIES) == {"algoritmo-de-classificacao-k-nn"}
    assert casar("raw/code/analise-exploratoria-de-dados-exemplo-1.ipynb", ENTRIES) == {"analise-exploratoria-de-dados-exemplo-1"}
    assert casar("k-NN | Plano de Ensino", ENTRIES) == {"algoritmo-de-classificacao-k-nn", "plano-de-ensino"}
    assert casar("nao existe", ENTRIES) == set()


def test_pontuar_hit1_hit3_e_bloco():
    esperado = {"algoritmo-de-classificacao-k-nn"}
    assert pontuar(esperado, ["algoritmo-de-classificacao-k-nn", "plano-de-ensino"]) == (True, True)
    assert pontuar(esperado, ["plano-de-ensino", "algoritmo-de-classificacao-k-nn"]) == (False, True)
    assert pontuar(esperado, ["plano-de-ensino"]) == (False, False)
    assert pontuar(esperado, []) == (False, False)


# --- piso deterministico ------------------------------------------------------------

def test_escolher_sem_llm_rankeia_por_sobreposicao_de_tokens():
    picks = escolher_sem_llm("como funciona o algoritmo k-NN para classificação?", ENTRIES, k=3)
    assert picks[0] == "algoritmo-de-classificacao-k-nn"


# --- contexto e cache -----------------------------------------------------------------

def test_contexto_navegacao_le_os_indices_na_ordem_do_tutor(tmp_path):
    (tmp_path / "course").mkdir()
    for n in ("COURSE_MAP.md", "SYLLABUS.md", "CRONOGRAMA_DETALHADO.md", "FILE_MAP.md"):
        (tmp_path / "course" / n).write_text(f"# {n}\n", encoding="utf-8")
    ctx = contexto_navegacao(tmp_path)
    assert ctx.index("COURSE_MAP") < ctx.index("SYLLABUS") < ctx.index("CRONOGRAMA_DETALHADO") < ctx.index("FILE_MAP")


def test_chave_cache_muda_com_contexto_e_pergunta():
    a = chave_cache("IA", "q1", "ctx")
    assert a == chave_cache("IA", "q1", "ctx")
    assert a != chave_cache("IA", "q1", "ctx2") and a != chave_cache("IA", "q2", "ctx")


# --- rodada com client fake --------------------------------------------------------------

class FakeClient:
    model = "fake"

    def __init__(self):
        self.calls = 0

    def summarize_bundle(self, bundle_text, schema, system_instruction):
        self.calls += 1
        assert schema is Resposta
        if "k-NN" in bundle_text.split("PERGUNTA:")[-1]:
            return Resposta(arquivos=["Algoritmo de Classificação k-NN"], bloco="bloco-05", porque="titulo")
        return Resposta(arquivos=["Plano de Ensino"], bloco="bloco-01", porque="chute")


def test_rodar_mede_e_cacheia(tmp_path):
    (tmp_path / "course").mkdir()
    for n in ("COURSE_MAP.md", "SYLLABUS.md", "CRONOGRAMA_DETALHADO.md", "FILE_MAP.md"):
        (tmp_path / "course" / n).write_text(f"# {n}\n", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps({"entries": ENTRIES}), encoding="utf-8")
    (tmp_path / "course" / ".timeline_index.json").write_text(json.dumps({"blocks": BLOCKS}), encoding="utf-8")
    gold = [{"pergunta": "o que é o algoritmo k-NN?", "esperado": "k-NN", "bloco": "bloco-05", "tipo": "conteudo"},
            {"pergunta": "quando é a prova?", "esperado": "Plano de Ensino", "bloco": "", "tipo": "prova"},
            {"pergunta": "exemplo de análise exploratória", "esperado": "exemplo-1", "bloco": "bloco-04", "tipo": "codigo"}]
    client = FakeClient(); cache = tmp_path / "cache.json"
    r = rodar("IA", tmp_path, gold, client=client, cache_path=cache)
    assert (r["hit1"], r["hit3"], r["n"]) == (2, 2, 3)
    assert r["bloco_ok"] == 1 and r["bloco_n"] == 2          # bloco so conta onde o gold tem bloco
    assert client.calls == 3
    r2 = rodar("IA", tmp_path, gold, client=client, cache_path=cache)
    assert client.calls == 3 and r2["hit1"] == 2             # cache: 0 chamadas novas
    r3 = rodar("IA", tmp_path, gold, client=None, cache_path=None)
    assert r3["modo"] == "sem-llm" and r3["n"] == 3 and r3["hit3"] >= 2


# --- escolha do LLM: casamento fuzzy (o tutor cita o texto do CRONOGRAMA, nao o Titulo) ---

def test_casar_escolha_fuzzy_por_tokens():
    from scripts.eval_travessia import casar_escolha
    ents = ENTRIES + [{"id": "exemplo-2-k-nn-com-iriscsv-mais-completo", "title": "Exemplo 2 k-NN (com IRIS.csv) - mais completo",
                       "category": "codigo-professor", "raw_target": "raw/code/exemplo-2-k-nn.ipynb", "moodle_label": ""}]
    assert casar_escolha("Algoritmo de Classificação k-NN", ents) == "algoritmo-de-classificacao-k-nn"          # exato
    assert casar_escolha("Classificação com o algoritmo k-Nearest Neighbors (k-NN) usando o dataset Iris", ents) == "algoritmo-de-classificacao-k-nn"
    assert casar_escolha("Análise Exploratória de Dados - Exemplo 1.ipynb", ents) == "analise-exploratoria-de-dados-exemplo-1"
    assert casar_escolha("Teoria dos grafos planares", ents) == ""                                                # < limiar: nada
