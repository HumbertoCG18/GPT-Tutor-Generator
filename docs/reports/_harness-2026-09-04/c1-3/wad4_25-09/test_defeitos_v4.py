"""W-AD4: um teste por defeito concreto da 3ª revisão adversarial. Resultados esperados escritos à mão.

Fase vermelha: rodados contra o código copiado da v3 (saída em testes_v4_vermelho.txt). Fase verde: contra o código v4.
Sem gold real, sem rede, sem src/ alterado.
"""
import copy
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import avaliador as AV  # noqa: E402
import captura as CP  # noqa: E402
import comum as K  # noqa: E402

INV = {"S": ["e1", "e2"]}


# ------------------------------------------------------------------------------------------- fixtures completas
def congelamento(inventario=INV, **extra):
    normativo = {"inventario": inventario, "codigo": {"helper.py": "a" * 64},
                 "esperado": {"manual": {b: {s: False for s in inventario} for b in K.BRACOS}},
                 "temporais": {s: {".timeline_index.json": "t" * 64} for s in inventario}, **extra}
    insumos = {b: {s: {"palco": {}, "taxonomia_arquivo_sha": "f" * 64, "indice_arquivo_sha": "g" * 64,
                       "taxonomia_sha": f"tax-{b}-{s}", "indice_sha": f"idx-{b}-{s}"} for s in inventario} for b in K.BRACOS}
    return {"normativo": normativo, "id_comum": K.id_congelamento(normativo), "insumos": insumos,
            "insumos_braco": {b: K.sha_json(insumos[b]) for b in K.BRACOS}, "controles": {"bloqueados": []}}


def chamada(sub, unidade="u1", pontuacoes=None):
    return {"unidade_fornecida": unidade, "pontuacoes": pontuacoes if pontuacoes is not None else
            [{"unidade": unidade, "topico": sub or "t0", "score": 0.5}],
            "vencedor": {"unidade": unidade, "topico": sub}, "conf": 0.5, "ambigua": False, "motivos": ["r"]}


def registro(sig, eid, sub, cong, braco="CRU", unidade="u1"):
    return {"curso": sig, "id": eid, "chamado": True, "motivo_nao_chamado": "", "p1": chamada(sub, unidade),
            "chamadas_posteriores": [], "taxonomia_sha": cong["insumos"][braco][sig]["taxonomia_sha"],
            "final": {"bloco": "b1", "unidade": unidade, "sub": sub, "conf_sub": 0.5, "motivos_sub": [], "motivos_unidade": []}}


def captura_valida(cong, braco="CRU", modo="capturar"):
    inv = cong["normativo"]["inventario"]
    cap = {"esquema": K.ESQUEMA_CAPTURA, "braco": braco, "modo": modo, "status": "concluida",
           "congelamento_comum": cong["id_comum"], "insumos_braco": cong["insumos_braco"][braco],
           "violacoes": [], "negados": [], "acessos": {},
           "inventario": {s: sorted(v) for s, v in inv.items()},
           "por_curso": {s: {"taxonomia_sha": cong["insumos"][braco][s]["taxonomia_sha"],
                             "indice_sha": cong["insumos"][braco][s]["indice_sha"], "unidades_motor": []} for s in inv},
           "verificacoes": {"manual_carregado": dict(cong["normativo"]["esperado"]["manual"][braco]),
                            "artefatos_temporais_sha": dict(cong["normativo"]["temporais"]),
                            "taxonomia_congelada_lida": []},
           "decisoes": ({s: {e: registro(s, e, "t1", cong, braco) for e in inv[s]} for s in inv} if modo == "capturar" else {})}
    cap["conteudo_sha"] = K.conteudo_sha(cap)
    return cap


def rehash(cap):
    cap["conteudo_sha"] = K.conteudo_sha(cap)
    return cap


def problemas(cap, cong, braco="CRU", modo="capturar"):
    return K.valida_captura(cap, congelamento=cong, braco=braco, modo=modo)


def test_fixture_completa_e_valida():
    cong = congelamento()
    assert problemas(captura_valida(cong), cong) == []
    assert problemas(captura_valida(cong, modo="carga"), cong, modo="carga") == []


# ------------------------------------------------------------------------------------------- §3 captura
def test_verificacoes_ou_por_curso_ausentes():
    cong = congelamento()
    for campo in ("verificacoes", "por_curso"):
        cap = captura_valida(cong)
        del cap[campo]
        assert problemas(rehash(cap), cong), campo


def test_manual_indevido_no_cru():
    cong = congelamento()
    cap = captura_valida(cong)
    cap["verificacoes"]["manual_carregado"]["S"] = True
    assert any("manual" in p for p in problemas(rehash(cap), cong))


def test_hash_de_taxonomia_ou_indice_errado_com_conteudo_sha_recalculado():
    cong = congelamento()
    cap = captura_valida(cong)
    cap["por_curso"]["S"]["taxonomia_sha"] = "outro"
    assert any("taxonomia" in p for p in problemas(rehash(cap), cong))
    cap = captura_valida(cong)
    cap["por_curso"]["S"]["indice_sha"] = "idx-VOCAB_LLM-S"   # snapshot de outro braço
    assert any("índice" in p for p in problemas(rehash(cap), cong))


def test_curso_ou_id_interno_diferente_das_chaves():
    cong = congelamento()
    cap = captura_valida(cong)
    cap["decisoes"]["S"]["e1"]["id"] = "e2"
    assert any("chave" in p for p in problemas(rehash(cap), cong))


def test_pontuacoes_string_score_nao_finito_candidato_duplicado():
    cong = congelamento()
    casos = {"string": "pontua", "dup": "duplicad", "sem_vencedor": "vencedor", "chamado_str": "booleano"}
    for mut, trecho in casos.items():
        cap = captura_valida(cong)
        r = cap["decisoes"]["S"]["e1"]
        if mut == "string":
            r["p1"]["pontuacoes"] = "t1:0.5"
        elif mut == "dup":
            r["p1"]["pontuacoes"] = [{"unidade": "u1", "topico": "t1", "score": 0.5}, {"unidade": "u1", "topico": "t1", "score": 0.4}]
        elif mut == "sem_vencedor":
            del r["p1"]["vencedor"]
        else:
            r["chamado"] = "sim"
        assert any(trecho in p for p in problemas(rehash(cap), cong)), mut   # hash correto não salva estrutura errada
    cap = captura_valida(cong)
    cap["decisoes"]["S"]["e1"]["p1"]["pontuacoes"][0]["score"] = math.inf
    assert any("finito" in p for p in problemas(cap, cong))


def test_saida_fora_da_taxonomia_nao_e_erro_estrutural():
    cong = congelamento()
    cap = captura_valida(cong)
    cap["decisoes"]["S"]["e1"]["final"]["sub"] = "pino-manual-fora-da-taxonomia"
    cap["decisoes"]["S"]["e1"]["p1"]["vencedor"]["topico"] = "pino-manual-fora-da-taxonomia"
    assert problemas(rehash(cap), cong) == []


def test_captura_nao_cru_em_cache_sem_autorizacao(tmp_path, monkeypatch):
    cong = congelamento()
    monkeypatch.setattr(CP, "CAPS", tmp_path)
    cap = captura_valida(cong, braco="VOCAB_LLM")
    destino = tmp_path / f"capturar_VOCAB_LLM_{cong['id_comum'][:16]}_{cong['insumos_braco']['VOCAB_LLM'][:16]}.json"
    destino.write_text(json.dumps(cap), encoding="utf-8")
    with pytest.raises(CP.Falha, match="não autorizad"):
        CP.roda_worker("VOCAB_LLM", "capturar", cong, K.Travas("teste"))


# ------------------------------------------------------------------------------------------- §2 congelamento
def test_descritor_de_insumos_alterado_sem_atualizar_identificador():
    cong = congelamento()
    cong["insumos"]["CRU"]["S"]["taxonomia_sha"] = "trocado"
    assert any("insumos" in p for p in K.valida_congelamento(cong))


def test_codigo_alterado_depois_do_preflight(tmp_path):
    arq = tmp_path / "helper.py"
    arq.write_bytes(b"x = 1\n")   # bytes: write_text no Windows gravaria \r\n
    cong = congelamento(codigo={"helper.py": K.sha_bytes(b"x = 1\n")})
    assert K.verifica_codigo(cong["normativo"]["codigo"], {"helper.py": arq}) == []
    arq.write_bytes(b"x = 2\n")
    assert K.verifica_codigo(cong["normativo"]["codigo"], {"helper.py": arq})


def test_ambiente_relevante_divergente():
    env = K.ambiente_controlado({"SYSTEMROOT": "C:\\Windows", "GEMINI_API_KEY": "segredo", "UNIT_GENERIC_MODE": "lista"})
    assert "GEMINI_API_KEY" not in env and env["UNIT_GENERIC_MODE"] == "df"
    assert K.verifica_ambiente(env) == []
    ruim = dict(env, UNIT_GENERIC_MODE="lista")
    assert any("UNIT_GENERIC_MODE" in p for p in K.verifica_ambiente(ruim))
    extra = dict(env, DATALAB_API_KEY="x")
    assert any("DATALAB_API_KEY" in p for p in K.verifica_ambiente(extra))
    assert "segredo" not in json.dumps(K.descritor_ambiente(env))


def test_import_de_outra_raiz(tmp_path):
    outra = tmp_path / "outro_checkout" / "src"
    outra.mkdir(parents=True)
    (outra / "modx.py").write_text("y = 1\n", encoding="utf-8")
    import types
    falso = types.ModuleType("src.modx")
    falso.__file__ = str(outra / "modx.py")
    prob = K.verifica_modulos({"src.modx": falso}, raiz=tmp_path / "repo" / "src", arvore={})
    assert prob and "fora da raiz" in prob[0]


def test_validacao_historica_sem_checkout_original(tmp_path):
    cong = congelamento()
    cap = captura_valida(cong)
    assert K.valida_historica(cap, cong) == []
    assert K.valida_historica(cap, congelamento(codigo={"helper.py": "b" * 64}))


# ------------------------------------------------------------------------------------------- §5/§6 leituras e permissões
MODELO = r'''
import json, os, sys
sys.path.insert(0, {here!r})
import comum as K
t = K.Travas("teste")
t.permite("codigo", {base!r}, {prefix!r}, {here!r}, somente_leitura=True)
t.permite("saida", {saida!r})
{config}
t.instala()
try:
{acao}
except Exception:
    pass
t.rehash_leituras()
with open({rel!r}, "w", encoding="utf-8") as fh:
    json.dump([v["tipo"] for v in t.violacoes], fh)
K.encerra(t, ok=True)
'''


def roda(tmp_path, acao, config=""):
    rel = tmp_path / "saida" / "viol.json"
    rel.parent.mkdir(exist_ok=True)
    src = MODELO.format(here=str(HERE), base=sys.base_prefix, prefix=sys.prefix, saida=str(tmp_path / "saida"),
                        config=config, acao="\n".join("    " + x for x in acao.strip().splitlines()), rel=str(rel))
    r = subprocess.run([sys.executable, "-B", "-c", src], capture_output=True, text=True)
    return r.returncode, json.loads(rel.read_text(encoding="utf-8")) if rel.exists() else None, r.stderr


def raiz_comum(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    (raiz / "a.txt").write_text("a", encoding="utf-8")
    return raiz, f"t.permite('comum', {str(raiz)!r}, somente_leitura=True)\nt.congela({str(raiz)!r}, {{'a.txt': K.sha_bytes(b'a')}})"


def test_arquivo_lido_alterado_e_reaberto(tmp_path):
    raiz, cfg = raiz_comum(tmp_path)
    a = str(raiz / "a.txt")
    acao = (f"open({a!r}).read()\n"
            f"with t._abrir_original({a!r}, 'w') as fh: fh.write('b')\n"
            f"open({a!r}).read()")
    rc, viol, err = roda(tmp_path, acao, cfg)
    assert rc == 2 and "insumo_divergente" in viol, (viol, err)


def test_conteudo_restaurado_antes_do_fim_preserva_violacao(tmp_path):
    raiz, cfg = raiz_comum(tmp_path)
    a = str(raiz / "a.txt")
    acao = (f"open({a!r}).read()\nwith t._abrir_original({a!r}, 'w') as fh: fh.write('b')\n"
            f"open({a!r}).read()\nwith t._abrir_original({a!r}, 'w') as fh: fh.write('a')")
    rc, viol, _ = roda(tmp_path, acao, cfg)
    assert rc == 2 and "insumo_divergente" in viol


def test_arquivo_lido_e_removido(tmp_path):
    raiz, cfg = raiz_comum(tmp_path)
    a = str(raiz / "a.txt")
    rc, viol, _ = roda(tmp_path, f"open({a!r}).read()\nos.remove({a!r})", cfg)
    assert rc == 2 and "insumo_desaparecido" in viol


def test_escrita_em_codigo(tmp_path):
    rc, viol, _ = roda(tmp_path, f"open({str(HERE / 'escrita_proibida.tmp')!r}, 'w').write('x')")
    assert rc == 2 and "escrita_em_entrada" in viol
    assert not (HERE / "escrita_proibida.tmp").exists()


def test_permissao_de_subprocesso_fecha_em_excecao():
    t = K.Travas("teste")
    with pytest.raises(RuntimeError):
        with t.comandos({"python.exe", "python"}):
            assert t.comando_permitido(["python", "-c", "0"])
            raise RuntimeError("falha no meio")
    assert not t.comando_permitido(["python", "-c", "0"])
    with t.comandos({"git"}):
        assert not t.comando_permitido(["cmd", "/c", "ver"])


def test_caminho_proibido_como_source_path_na_preparacao(tmp_path):
    t = K.Travas("preparo")
    env = tmp_path / ".env"
    env.write_text("CHAVE=x", encoding="utf-8")
    gold = tmp_path / "material_gt_X.csv"
    gold.write_text("x", encoding="utf-8")
    t.nega(env, "segredos")
    manifestos = {"S": {"entries": [{"id": "e1", "source_path": str(gold)}]}}
    with pytest.raises(K.Violacao):
        CP.externas(manifestos, None, t)
    manifestos = {"S": {"entries": [{"id": "e1", "source_path": str(env)}]}}
    with pytest.raises(K.Violacao):
        CP.externas(manifestos, None, t)
    assert {v["tipo"] for v in t.violacoes} == {"preparo_proibido"}


# ------------------------------------------------------------------------------------------- §8 régua sintética
def estado_regua():
    return {"S": {"rows": [{"entry_id": "g1", "bloco": "x", "unidade": "x", "sub_primario": "x"},
                           {"entry_id": "g2", "bloco": "", "unidade": "", "sub_primario": "x"}],
                  "eid_de": {"g1": "e1", "g2": None},
                  "golds": ({"g1": "b1"}, {"g1": {"u1"}}, {"g1": {"t1"}, "g2": {""}}, {"g1": {"t1"}, "g2": {""}})}}


def test_gid_ausente_versus_none_explicito():
    r = AV.regua_de_estado(estado_regua())
    assert r["S"][1]["eid"] is None
    sem_chave = estado_regua()
    del sem_chave["S"]["eid_de"]["g2"]
    with pytest.raises(K.ErroIntegridade, match="eid_de"):
        AV.regua_de_estado(sem_chave)


def test_origem_ambigua_e_rejeitada():
    saved = {"a": {"id": "a", "source_path": "C:/x/doc.pdf"}, "b": {"id": "b", "source_path": "C:/x/doc.pdf"}}
    ref = {"old1": {"id": "old1", "source_path": "C:/x/doc.pdf"}}
    rows = [{"entry_id": "g1"}]
    with pytest.raises(K.ErroIntegridade, match="ambígua"):
        AV.mapeia_eids(rows, {"g1": "old1"}, ref, saved)


def test_duplicidade_de_eid_e_distribuicao_por_curso(monkeypatch):
    monkeypatch.setattr(K, "DENOMINADORES", {"bloco": 0, "unidade": 0, "sub_primaria": 2})
    monkeypatch.setattr(K, "DENOM_POR_CURSO", {"S": {"bloco": 0, "unidade": 0, "sub_primaria": 1},
                                               "T": {"bloco": 0, "unidade": 0, "sub_primaria": 1}})
    lin = lambda g, e: {"gold_id": g, "eid": e, "bloco": None, "unidade": None, "sub_primaria": {"t"}, "sub_aceita": {"t"}}  # noqa: E731
    inv = {"S": ["e1", "e2"], "T": ["e3"]}
    assert any("mesmo eid" in p for p in AV.valida_regua({"S": [lin("g1", "e1"), lin("g2", "e1")], "T": []}, inv))
    prob = AV.valida_regua({"S": [lin("g1", "e1"), lin("g2", "e2")], "T": []}, inv)   # total 2 certo, curso errado
    assert any("S" in p and "sub_primaria" in p for p in prob)


def test_veredicto_b_nao_veta_por_subunidade_aceita():
    base = {"bloco": {"acertos": 1, "n": 1}, "unidade": {"acertos": 1, "n": 1}, "sub_primaria": {"acertos": 1, "n": 2},
            "sub_aceita": {"acertos": 2, "n": 2}}
    melhor = dict(base, sub_primaria={"acertos": 2, "n": 2}, sub_aceita={"acertos": 1, "n": 2})
    pl = {b: {"S": copy.deepcopy(base), "TOTAL": copy.deepcopy(base)} for b in K.BRACOS}
    pl["VOCAB_LLM"] = {"S": melhor, "TOTAL": melhor}
    comp = {b: {e: {"derivadas": {}} for e in AV.EIXOS} for b in K.BRACOS if b != "CRU"}
    comp["VOCAB_LLM"]["sub_aceita"]["derivadas"] = {"perda": 1}
    v = AV.veredictos(pl, comp, {"S": []})
    assert v["B_integracao"].startswith("sem violação") and v["B_perdas_sub_aceita_auxiliar"] == 1


def test_material_ausente_ou_nao_chamado_sem_elegibilidade_ficticia():
    tax = {"units": [{"slug": "u1", "topics": [{"slug": "t1"}]}]}
    nao_chamado = {"chamado": False, "p1": None, "final": {"bloco": "", "unidade": "u1", "sub": ""}}
    for rec in (None, nao_chamado):
        g = AV.geracao_do_material(rec, {"t1"}, tax)
        assert g["elegivel"] == AV.NA and g["escolhido_1a"] == AV.NA and g["rotulo_existe_na_taxonomia"] is True


def test_worker_recebe_ambiente_declarado_mesmo_com_os_environ_mutado(tmp_path, monkeypatch):
    """Preflight v4, tentativa 1: o import do produto grava TESSDATA_PREFIX no processo principal e o worker herdava."""
    cong = congelamento()
    monkeypatch.setattr(CP, "CAPS", tmp_path)
    monkeypatch.setenv("TESSDATA_PREFIX", "C:/mutado/pelo/produto")
    visto = {}

    def falso(cmd, **kw):
        visto.update(kw)
        return SimpleNamespace(returncode=9, stdout="", stderr="")

    monkeypatch.setattr(CP.subprocess, "run", falso)
    with pytest.raises(CP.Falha):
        CP.roda_worker("CRU", "carga", cong, K.Travas("teste"))
    assert "env" in visto and "TESSDATA_PREFIX" not in visto["env"]
    assert K.verifica_ambiente(visto["env"]) == []


def test_codigo_somente_leitura_na_configuracao_real():
    for travas in (CP.travas_worker("CRU"), CP.travas_principal()):
        assert "codigo" in travas.leitura_so
        p, cat, _ = travas.classifica(CP.DATA / "src" / "qualquer.py")
        assert cat == "codigo"
