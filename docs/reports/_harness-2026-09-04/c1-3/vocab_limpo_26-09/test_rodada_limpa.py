"""Rodada VOCAB_LIMPO (26/09): testes sintéticos do que muda em relação ao harness congelado da Fase 1. Sem gold, sem rede."""
import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import avaliador as AV  # noqa: E402
import captura as CP  # noqa: E402
import comum as K  # noqa: E402
from test_defeitos_v4 import captura_valida, congelamento  # noqa: E402

W5 = HERE.parent / "wad5_25-09"
NOVOS = {"CRU": "CRU_LIMPO", "VOCAB_LLM": "VOCAB_LIMPO", "CTRL_MAIOR": "CTRL_MAIOR_LIMPO",
         "CTRL_ALEAT_1": "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_2": "CTRL_ALEAT_LIMPO_2", "CTRL_ALEAT_3": "CTRL_ALEAT_LIMPO_3"}


def test_bracos_sementes_manuais_e_liberacao_da_rodada():
    assert K.BRACOS == ("CRU_LIMPO", "VOCAB_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_LIMPO_2",
                        "CTRL_ALEAT_LIMPO_3")
    assert K.SEMENTES == {"CTRL_ALEAT_LIMPO_1": 1, "CTRL_ALEAT_LIMPO_2": 2, "CTRL_ALEAT_LIMPO_3": 3}   # mesmas sementes da Fase 1
    assert all(v is False for m in K.MANUAL_ESPERADO.values() for v in m.values())                    # nenhum manual
    assert K.CAPTURA_LIBERADA == frozenset(K.BRACOS)
    assert "VOCAB_ATUAL" not in K.BRACOS and "VOCAB_LLM" not in K.BRACOS


def test_captura_da_fase1_nao_valida_na_rodada_limpa():
    cong = congelamento()
    cap = captura_valida(cong)
    cap["esquema"] = "wad5-captura-1"
    cap["conteudo_sha"] = K.conteudo_sha(cap)
    assert any("esquema" in p for p in K.valida_captura(cap, congelamento=cong, braco="CRU_LIMPO", modo="capturar"))


def test_travas_proibem_resultados_da_fase1_regua_e_tutores_vivos():
    alvos = [HERE.parent / "wad5_avaliacao_26-09" / "avaliacao_espelho_1.json",
             CP.DATA / ".frzero/wad5_avaliacao_26-09/espelho/docs/reports/subunit_gt_MF.csv",
             CP.DATA / "docs/reports/pendencias.md", CP.DATA / "docs/reports/ground_truth_MF.csv",
             CP.ORIG / "Metodos-Formais-Tutor" / "course" / ".glossary_curation.llm.json"]
    for travas in (CP.travas_worker("VOCAB_LIMPO"), CP.travas_principal()):
        if "preparo" in travas.permitidos:     # no principal, o preparo sai antes de qualquer leitura (P1)
            travas.permitidos.pop("preparo")
            for nome in CP.TUTORES:
                travas.proibe(CP.ORIG / nome, "tutor vivo")
        for alvo in alvos:
            assert travas.classifica(alvo)[1] == "proibido", alvo


def test_fonte_do_vocab_limpo_e_a_recompilacao_congelada():
    assert CP.ADENDO.name == "2026-09-26-regime-vocab-recompilacao-limpa.md"
    assert CP.VL_SIDECARS == CP.DATA / ".frzero/vocab_limpo_26-09/sidecars"
    assert CP.travas_principal().classifica(CP.VL_SIDECARS / "Metodos-Formais-Tutor" / CP.LLM)[1] == "referencia"
    assert CP.BASE == CP.DATA / ".frzero/vocab_limpo_26-09/captura"


def test_adaptador_do_avaliador_e_o_original_com_nomes_trocados():
    original = (W5 / "avaliador.py").read_bytes().decode("utf-8").replace("\r\n", "\n")
    adaptado = (HERE / "avaliador.py").read_bytes().decode("utf-8").replace("\r\n", "\n")
    cab_novo = adaptado.split("Original: avaliador SEPARADO", 1)[0]
    adaptado = adaptado.replace(cab_novo + "Original: avaliador SEPARADO", '"""W-AD4 (25/09): avaliador SEPARADO', 1)
    for velho, novo in NOVOS.items():
        adaptado = adaptado.replace(f'"{novo}"', f'"{velho}"')
    adaptado = adaptado.replace("C_meta_VOCAB_LIMPO", "C_meta_VOCAB_LLM")
    assert adaptado == original


def test_veredictos_do_adaptador_usam_os_bracos_da_rodada():
    base = {"bloco": {"acertos": 1, "n": 1}, "unidade": {"acertos": 1, "n": 1}, "sub_primaria": {"acertos": 1, "n": 2},
            "sub_aceita": {"acertos": 1, "n": 2}}
    melhor = dict(base, sub_primaria={"acertos": 2, "n": 2})
    pl = {b: {"S": copy.deepcopy(base), "TOTAL": copy.deepcopy(base)} for b in K.BRACOS}
    pl["VOCAB_LIMPO"] = {"S": melhor, "TOTAL": melhor}
    comp = {b: {e: {"derivadas": {}} for e in AV.EIXOS} for b in K.BRACOS if b != "CRU_LIMPO"}
    v = AV.veredictos(pl, comp, {"S": []})
    assert v["A_sinal_exploratorio"] is True and set(v["A_detalhe"]) == set(K.BRACOS)
    assert v["B_integracao"].startswith("sem violação") and "C_meta_VOCAB_LIMPO" in v
    pl["CTRL_ALEAT_LIMPO_2"] = {"S": melhor, "TOTAL": melhor}           # empate com um controle: A falso
    assert AV.veredictos(pl, comp, {"S": []})["A_sinal_exploratorio"] is False
