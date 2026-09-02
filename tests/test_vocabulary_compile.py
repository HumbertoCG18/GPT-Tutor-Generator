"""Fase 1b (plano 02/09): `compile_course_vocabulary` — vocabulario por curso, 1 chamada
de LLM por unidade COM material, gravado em `course/.glossary_curation.llm.json` (mesmo
formato do loader; `_provenance: llm`). Cache = o proprio arquivo; recompila so com flag.
Sidecar MANUAL (`.glossary_curation.json`) presente = o curso ja tem vocabulario: nao chama.
Sem chamada real: client fake."""
import json
import os
from pathlib import Path

import pytest

from src.builder.artifacts.repo import load_glossary_curation
from src.builder.core.vocabulary_compile import (
    LLM_VOCAB_NAME, Vocab, TopicoTermos, compile_course_vocabulary, filter_terms,
)

TAX = {
    "version": 1, "course_slug": "fr", "course_name": "Fundamentos de Redes",
    "units": [
        {"slug": "unidade-01", "title": "Unidade 01 - Conceitos", "topics": [
            {"slug": "modelos-osi", "label": "Modelos OSI e TCP/IP", "aliases": []},
            {"slug": "conceitos", "label": "Conceitos de redes", "aliases": []},
        ]},
        {"slug": "unidade-02", "title": "Unidade 02 - Aplicacao", "topics": [
            {"slug": "sockets", "label": "Implementação de sockets", "aliases": []},
        ]},
        {"slug": "unidade-03", "title": "Unidade 03 - Sem material", "topics": [
            {"slug": "x", "label": "Topico X", "aliases": []},
        ]},
    ],
}


def _mat(id_, unit, title, md="", cat="aulas"):
    return {"id": id_, "file_type": "pdf", "category": cat, "title": title,
            "computed_unit_slug": unit, "_markdown_text_for_tests": md}


ENTRIES = [
    _mat("aula-01-modelos", "unidade-01", "Aula 01 - Modelos", "# Modelo OSI\n## Camada de Enlace\n## Camada Fisica"),
    _mat("tcp-chat-c", "unidade-02", "TCP Chat C", "# Socket TCP\n## tcp_chat_c"),
    _mat("prova-1", "unidade-01", "Prova 1", "# Modelo OSI", cat="provas"),   # fora de escopo
]


class FakeClient:
    """Devolve por unidade o que o teste programou; conta chamadas e guarda os bundles."""
    model = "fake"

    def __init__(self, respostas=None, erro_em=()):
        self.respostas = respostas or {}
        self.erro_em = set(erro_em)
        self.bundles = []

    def summarize_bundle(self, bundle_text, schema, system_instruction):
        assert schema is Vocab
        self.bundles.append(bundle_text)
        for slug, resp in self.respostas.items():
            if f"UNIDADE: {slug}" in bundle_text or slug in bundle_text:
                if slug in self.erro_em:
                    raise RuntimeError("api down")
                return resp
        return Vocab(topicos=[])


def _resp(**por_label):
    return Vocab(topicos=[TopicoTermos(topico=k, termos=v) for k, v in por_label.items()])


def _repo(tmp_path):
    (tmp_path / "course").mkdir()
    return tmp_path


# --- cache / manual / flag ------------------------------------------------------

def test_sidecar_manual_presente_nao_chama(tmp_path):
    root = _repo(tmp_path)
    (root / "course" / ".glossary_curation.json").write_text('{"Modelos OSI e TCP/IP": {"synonyms": ["osi"]}}', encoding="utf-8")
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace"]})})
    assert compile_course_vocabulary(root, ENTRIES, TAX, c) is None
    assert c.bundles == []
    assert not (root / "course" / LLM_VOCAB_NAME).exists()


def test_llm_json_existente_e_cache(tmp_path):
    root = _repo(tmp_path)
    (root / "course" / LLM_VOCAB_NAME).write_text('{"_provenance": "llm", "Modelos OSI e TCP/IP": {"synonyms": ["osi"]}}', encoding="utf-8")
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace"]})})
    out = compile_course_vocabulary(root, ENTRIES, TAX, c)
    assert c.bundles == []
    assert out["Modelos OSI e TCP/IP"]["synonyms"] == ["osi"]


def test_recompile_ignora_o_cache(tmp_path):
    root = _repo(tmp_path)
    (root / "course" / LLM_VOCAB_NAME).write_text('{"_provenance": "llm", "Modelos OSI e TCP/IP": {"synonyms": ["osi"]}}', encoding="utf-8")
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace"]})})
    out = compile_course_vocabulary(root, ENTRIES, TAX, c, recompile=True)
    assert len(c.bundles) >= 1
    assert out["Modelos OSI e TCP/IP"]["synonyms"] == ["Camada de Enlace"]


def test_sem_client_nao_grava(tmp_path):
    root = _repo(tmp_path)
    assert compile_course_vocabulary(root, ENTRIES, TAX, None) is None
    assert not (root / "course" / LLM_VOCAB_NAME).exists()


# --- chamadas -------------------------------------------------------------------

def test_uma_chamada_por_unidade_com_material(tmp_path):
    root = _repo(tmp_path)
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace"]}),
                    "Unidade 02": _resp(**{"Implementação de sockets": ["Socket TCP"]})})
    compile_course_vocabulary(root, ENTRIES, TAX, c)
    assert len(c.bundles) == 2                       # unidade-03 sem material: nao chama
    assert all("Unidade 03" not in b for b in c.bundles)


def test_bundle_leva_titulo_e_headings_e_exclui_fora_de_escopo(tmp_path):
    root = _repo(tmp_path)
    c = FakeClient()
    compile_course_vocabulary(root, ENTRIES, TAX, c)
    b1 = next(b for b in c.bundles if "Unidade 01" in b)
    assert "Aula 01 - Modelos" in b1 and "Camada de Enlace" in b1
    assert "Prova 1" not in b1                        # categoria provas fora
    assert "* Modelos OSI e TCP/IP" in b1 and "* Conceitos de redes" in b1


def test_fresh_build_sem_unidades_nao_chama_nem_grava(tmp_path):
    root = _repo(tmp_path)
    ents = [dict(e, computed_unit_slug="") for e in ENTRIES]
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["x"]})})
    assert compile_course_vocabulary(root, ents, TAX, c) is None
    assert c.bundles == [] and not (root / "course" / LLM_VOCAB_NAME).exists()


def test_topico_fora_do_plano_e_ignorado(tmp_path):
    root = _repo(tmp_path)
    c = FakeClient({"Unidade 01": _resp(**{"Inventado": ["Camada de Enlace"], "Modelos OSI e TCP/IP": ["Camada Fisica"]})})
    out = compile_course_vocabulary(root, ENTRIES, TAX, c)
    assert "Inventado" not in out
    assert out["Modelos OSI e TCP/IP"]["synonyms"] == ["Camada Fisica"]


def test_erro_numa_unidade_nao_perde_as_outras_e_registra(tmp_path):
    root = _repo(tmp_path)
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace"]}),
                    "Unidade 02": _resp(**{"Implementação de sockets": ["Socket TCP"]})}, erro_em={"Unidade 02"})
    out = compile_course_vocabulary(root, ENTRIES, TAX, c)
    assert out["Modelos OSI e TCP/IP"]["synonyms"] == ["Camada de Enlace"]
    gravado = json.loads((root / "course" / LLM_VOCAB_NAME).read_text(encoding="utf-8"))
    assert gravado["_unidades_com_erro"] == ["unidade-02"]


# --- formato + loader -----------------------------------------------------------

def test_grava_no_formato_do_loader_com_provenance(tmp_path):
    root = _repo(tmp_path)
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace", "Camada Fisica"]})})
    compile_course_vocabulary(root, ENTRIES, TAX, c)
    gravado = json.loads((root / "course" / LLM_VOCAB_NAME).read_text(encoding="utf-8"))
    assert gravado["_provenance"] == "llm"
    assert gravado["Modelos OSI e TCP/IP"] == {"synonyms": ["Camada de Enlace", "Camada Fisica"]}
    assert "Conceitos de redes" not in gravado          # sem termos: nao entra
    cur = load_glossary_curation(root)
    assert cur["modelos osi e tcp/ip"] == ["Camada de Enlace", "Camada Fisica"]
    assert not any(k.startswith("_") for k in cur)      # metadados nao viram termo


def test_loader_funde_manual_e_llm(tmp_path):
    root = _repo(tmp_path)
    (root / "course" / ".glossary_curation.json").write_text('{"_nota": "x", "T": {"synonyms": ["a"]}}', encoding="utf-8")
    (root / "course" / LLM_VOCAB_NAME).write_text('{"_provenance": "llm", "T": {"synonyms": ["b", "a"]}, "U": {"synonyms": ["c"]}}', encoding="utf-8")
    cur = load_glossary_curation(root)
    assert cur == {"t": ["a", "b"], "u": ["c"]}


# --- filtros (decisao C) --------------------------------------------------------

LABELS = {"Modelos OSI e TCP/IP": "unidade-01", "Conceitos de redes": "unidade-01"}


def test_filtro_termo_igual_ao_label_sai():
    out = filter_terms({"Modelos OSI e TCP/IP": ["modelos osi e tcp/ip", "Camada de Enlace"]}, generic=set(), file_names=set())
    assert out["Modelos OSI e TCP/IP"] == ["Camada de Enlace"]


def test_filtro_exclusividade_termo_em_dois_topicos_sai():
    out = filter_terms({"Modelos OSI e TCP/IP": ["Internet", "Camada de Enlace"],
                        "Conceitos de redes": ["internet", "Redes locais"]}, generic=set(), file_names=set())
    assert out == {"Modelos OSI e TCP/IP": ["Camada de Enlace"], "Conceitos de redes": ["Redes locais"]}


def test_filtro_nome_de_arquivo_sai():
    # decisao C (02/09): nome de arquivo e identidade, nao vocabulario (tcp_chat_c, udp_example_java).
    fn = {"tcp chat c", "udp example java"}
    out = filter_terms({"Implementação de sockets": ["tcp_chat_c", "Socket TCP", "UDP Example Java"]}, generic=set(), file_names=fn)
    assert out["Implementação de sockets"] == ["Socket TCP"]


def test_filtro_generico_e_dedupe():
    out = filter_terms({"Modelos OSI e TCP/IP": ["Introdução", "Camada de Enlace", "camada de enlace", ""]},
                       generic={"intro"}, file_names=set())
    assert out["Modelos OSI e TCP/IP"] == ["Camada de Enlace"]


# --- hook na regeneracao --------------------------------------------------------

def test_hook_so_roda_com_flag_e_respeita_kill_switch(tmp_path, monkeypatch):
    from src.builder.ops import pedagogical_regeneration as pr

    chamadas = []
    monkeypatch.setattr(pr, "_resolve_gemini_client", lambda b: FakeClient())
    monkeypatch.setattr("src.builder.core.vocabulary_compile.compile_course_vocabulary",
                        lambda root, entries, tax, client, **k: chamadas.append(k.get("recompile", False)))

    class B:
        root_dir = _repo(tmp_path)
        options = {}

    pr._run_vocabulary_compile_layer(B(), ENTRIES)
    assert chamadas == []                                   # sem flag: nao roda
    B.options = {"compile_vocabulary": True}
    monkeypatch.setenv("TUTOR_NO_VOCAB_COMPILE", "1")
    pr._run_vocabulary_compile_layer(B(), ENTRIES)
    assert chamadas == []                                   # harness: kill switch
    monkeypatch.delenv("TUTOR_NO_VOCAB_COMPILE")
    pr._run_vocabulary_compile_layer(B(), ENTRIES)
    assert chamadas == [False]
    B.options = {"compile_vocabulary": True, "recompile_vocab": True}
    pr._run_vocabulary_compile_layer(B(), ENTRIES)
    assert chamadas == [False, True]


# --- plano com codigo de topico (FR/CG/MF): chave do sidecar = "<codigo> <label>" ------------

PLAN_CODIGOS = """
Unidade de Aprendizagem 1: Conceitos (20%)
1.1 Conceitos de redes de computadores e Internet
1.2 Modelos OSI e TCP/IP
"""
TAX_CODIGOS = {
    "version": 1, "course_slug": "fr", "course_name": "FR",
    "units": [{"slug": "unidade-01", "title": "Unidade 01 — Conceitos", "topics": [
        {"code": "1.1", "slug": "conceitos", "label": "Conceitos de redes de computadores e Internet", "aliases": []},
        {"code": "1.2", "slug": "modelos-osi", "label": "Modelos OSI e TCP/IP", "aliases": []},
    ]}],
}


def test_compile_grava_chave_com_codigo_e_o_glossario_casa(tmp_path):
    """02/09: reprocess real gravou 68 termos no FR e 0 campos mudaram — o glossario chaveava
    "1.2 Modelos OSI e TCP/IP" e o sidecar "Modelos OSI e TCP/IP". A chave leva o codigo (R8:
    termo numerado casa so pelo nucleo exato; "3.1 Conceitos basicos" != "5.1 Conceitos basicos")."""
    from src.builder import engine
    from src.models.core import SubjectProfile
    root = _repo(tmp_path)
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace"]})})
    out = compile_course_vocabulary(root, ENTRIES, TAX_CODIGOS, c)
    assert out["1.2 Modelos OSI e TCP/IP"] == {"synonyms": ["Camada de Enlace"]}
    sp = SubjectProfile(name="FR", slug="fr", teaching_plan=PLAN_CODIGOS)
    text = engine.glossary_md({"course_name": "FR"}, sp, root_dir=root)
    assert "Camada de Enlace" in text
    tax = engine._build_content_taxonomy(PLAN_CODIGOS, "", text)
    by_label = {t["label"]: t for u in tax["units"] for t in u["topics"]}
    assert "Camada de Enlace" in by_label["Modelos OSI e TCP/IP"]["aliases"]
    assert "Camada de Enlace" not in by_label["Conceitos de redes de computadores e Internet"]["aliases"]


def test_chave_preserva_codigo_e_normaliza_marcadores():
    from src.builder.artifacts.repo import _glossary_curation_key as k
    assert k("3.1 Conceitos básicos") != k("5.1 Conceitos básicos")
    assert k("**1.2.** Modelos OSI") == k("1.2 Modelos OSI") == "1.2 modelos osi"
    assert k("2D, 3D (mão direita)") == "2d, 3d (mão direita)"


# --- filtro de IDENTIDADE (02/09: CG — 48 materiais sugados para u01) -------------------------
# A aula 1 do CG enumera as OUTRAS unidades ("Fundamentos Matematicos", "Processo de
# Visualizacao 2D") e o LLM devolveu esses nomes como termos de "Conceitos". Nome de unidade/
# topico e identidade, nao vocabulario (mesma familia do nome de arquivo, decisao C).

TAX_CG = {
    "version": 1, "course_slug": "cg", "course_name": "CG",
    "units": [
        {"slug": "u01", "title": "Unidade 01 — Introdução ao Processamento Gráfico", "topics": [
            {"slug": "conceitos", "label": "Conceitos", "aliases": []},
            {"slug": "areas", "label": "Áreas relacionadas", "aliases": []}]},
        {"slug": "u02", "title": "Unidade 02 — Fundamentos Matemáticos", "topics": [
            {"slug": "geo", "label": "Algoritmos de Geometria Computacional", "aliases": []},
            {"slug": "poligonos", "label": "Algoritmos de polígonos", "aliases": []}]},
        {"slug": "u04", "title": "Unidade de Aprendizagem 4 — Processo de Visualização 2D (10%)", "topics": []},
    ],
}


def test_unit_title_core():
    from src.builder.core.vocabulary_compile import unit_title_core
    assert unit_title_core("Unidade 02 — Fundamentos Matemáticos") == "fundamentos matematicos"
    assert unit_title_core("Unidade de Aprendizagem 4 — Processo de Visualização 2D (10%)") == "processo de visualizacao 2d"


def _ident():
    from src.builder.core.vocabulary_compile import identities_of
    return identities_of(TAX_CG)


def test_identidade_nome_de_outra_unidade_sai():
    out = filter_terms({"Conceitos": ["Fundamentos Matemáticos", "Processo de Visualização 2D", "OpenGL"]},
                       generic=set(), file_names=set(), identities=_ident())
    assert out["Conceitos"] == ["OpenGL"]


def test_identidade_contido_em_label_de_outro_topico_sai():
    out = filter_terms({"Áreas relacionadas": ["Geometria Computacional", "Morfologia Matemática"]},
                       generic=set(), file_names=set(), identities=_ident())
    assert out["Áreas relacionadas"] == ["Morfologia Matemática"]


def test_identidade_contido_no_proprio_label_fica_e_um_token_fica():
    out = filter_terms({"Algoritmos de polígonos": ["Polígonos", "Geometria"],
                        "Algoritmos de Geometria Computacional": ["Plane Sweep"]},
                       generic=set(), file_names=set(), identities=_ident())
    assert out["Algoritmos de polígonos"] == ["Polígonos", "Geometria"]   # 1 token: contencao nao vale
    assert out["Algoritmos de Geometria Computacional"] == ["Plane Sweep"]


# --- _raw + refilter: reaplicar filtros sem nova chamada -------------------------------------

def test_refilter_reaplica_filtros_a_partir_do_raw_sem_chamar(tmp_path):
    root = _repo(tmp_path)
    c = FakeClient({"Unidade 01": _resp(**{"Modelos OSI e TCP/IP": ["Camada de Enlace", "tcp_chat_c"]})})
    out = compile_course_vocabulary(root, ENTRIES, TAX, c)
    assert out["Modelos OSI e TCP/IP"]["synonyms"] == ["Camada de Enlace"]      # tcp_chat_c = nome de arquivo
    assert out["_raw"]["Modelos OSI e TCP/IP"] == ["Camada de Enlace", "tcp_chat_c"]
    n = len(c.bundles)
    ents = [e for e in ENTRIES if e["id"] != "tcp-chat-c"]                       # arquivo sumiu: termo volta
    out2 = compile_course_vocabulary(root, ents, TAX, c, refilter=True)
    assert len(c.bundles) == n
    assert out2["Modelos OSI e TCP/IP"]["synonyms"] == ["Camada de Enlace", "tcp_chat_c"]


def test_hook_passa_refilter(tmp_path, monkeypatch):
    from src.builder.ops import pedagogical_regeneration as pr
    kw = []
    monkeypatch.setattr(pr, "_resolve_gemini_client", lambda b: FakeClient())
    monkeypatch.setattr("src.builder.core.vocabulary_compile.compile_course_vocabulary",
                        lambda root, entries, tax, client, **k: kw.append(k))

    class B:
        root_dir = _repo(tmp_path)
        options = {"compile_vocabulary": True, "refilter_vocab": True}

    pr._run_vocabulary_compile_layer(B(), ENTRIES)
    assert kw == [{"recompile": False, "refilter": True}]
