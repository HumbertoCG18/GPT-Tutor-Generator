"""Testes sintéticos do W-AD4 (captura, congelamento, travas, controles e avaliador). Nenhum gold real, nenhuma rede.

Rodar: python -m pytest docs/reports/_harness-2026-09-04/c1-3/wad4_25-09 -q -p no:cacheprovider
Os resultados esperados estão escritos à mão nas fixtures (não são calculados pela função sob teste). Herdados da v3
(test_wad3.py) com fixtures completas; os defeitos da 3ª revisão têm um teste cada em test_defeitos_v4.py.
"""
import copy
import functools
import json
import random
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


# ------------------------------------------------------------------------------------------- fixtures de captura
def congelamento(inventario, **normativo_extra):
    normativo = {"inventario": inventario, "codigo": {"replay_bloco_21-09.py": "a" * 64},
                 "esperado": {"manual": {b: {s: False for s in inventario} for b in K.BRACOS}},
                 "temporais": {s: {".timeline_index.json": "t" * 64} for s in inventario}, **normativo_extra}
    insumos = {b: {s: {"palco": {}, "taxonomia_arquivo_sha": "f" * 64, "indice_arquivo_sha": "g" * 64,
                       "taxonomia_sha": f"tax-{b}-{s}", "indice_sha": f"idx-{b}-{s}"} for s in inventario} for b in K.BRACOS}
    return {"normativo": normativo, "id_comum": K.id_congelamento(normativo), "insumos": insumos,
            "insumos_braco": {b: K.sha_json(insumos[b]) for b in K.BRACOS}, "controles": {"bloqueados": []}}


def registro(sig, eid, sub, *, unidade="u1", bloco="b1", chamado=True, pontuacoes=None, vencedor=None, amb=False):
    r = {"curso": sig, "id": eid, "chamado": chamado, "motivo_nao_chamado": "" if chamado else "manual_subunit",
         "p1": None, "chamadas_posteriores": [], "taxonomia_sha": "",
         "final": {"bloco": bloco, "unidade": unidade, "sub": sub, "conf_sub": 0.5 if chamado else None,
                   "motivos_sub": [], "motivos_unidade": []}}
    if chamado:
        r["p1"] = {"unidade_fornecida": unidade, "pontuacoes": pontuacoes or [],
                   "vencedor": vencedor or {"unidade": unidade, "topico": sub}, "conf": 0.5, "ambigua": amb, "motivos": []}
    return r


def captura(cong, braco, decisoes, modo="capturar"):
    inv = cong["normativo"]["inventario"]
    ins = cong["insumos"][braco]
    for sig, v in decisoes.items():
        for r in v.values():
            r["taxonomia_sha"] = ins[sig]["taxonomia_sha"]
    cap = {"esquema": K.ESQUEMA_CAPTURA, "braco": braco, "modo": modo, "status": "concluida",
           "congelamento_comum": cong["id_comum"], "insumos_braco": cong["insumos_braco"][braco],
           "violacoes": [], "negados": [], "acessos": {},
           "inventario": {s: sorted(v) for s, v in inv.items()},
           "por_curso": {s: {"taxonomia_sha": ins[s]["taxonomia_sha"], "indice_sha": ins[s]["indice_sha"],
                             "unidades_motor": []} for s in inv},
           "verificacoes": {"manual_carregado": dict(cong["normativo"]["esperado"]["manual"][braco]),
                            "artefatos_temporais_sha": copy.deepcopy(cong["normativo"]["temporais"]),
                            "taxonomia_congelada_lida": []},
           "decisoes": decisoes}
    cap["conteudo_sha"] = K.conteudo_sha(cap)
    return cap


def valida(cap, cong, braco="CRU", modo="capturar"):
    return K.valida_captura(cap, congelamento=cong, braco=braco, modo=modo)


INV = {"S": ["e1", "e2"]}


def decisoes_ok():
    return {"S": {"e1": registro("S", "e1", "t1"), "e2": registro("S", "e2", "t2")}}


# ------------------------------------------------------------------------------------------- §2 cache e congelamento
def test_captura_valida_passa():
    cong = congelamento(INV)
    assert valida(captura(cong, "CRU", decisoes_ok()), cong) == []


def test_json_de_outro_braco_em_modo_carga_no_caminho_do_cru_e_rejeitado(tmp_path, monkeypatch):
    cong = congelamento(INV)
    monkeypatch.setattr(CP, "CAPS", tmp_path)
    destino = tmp_path / f"capturar_CRU_{cong['id_comum'][:16]}_{cong['insumos_braco']['CRU'][:16]}.json"
    plantado = captura(cong, "VOCAB_LLM", {}, modo="carga")
    destino.write_text(json.dumps(plantado), encoding="utf-8")
    prob = valida(plantado, cong)
    assert any("braço errado" in p for p in prob) and any("modo errado" in p for p in prob)
    with pytest.raises(CP.Falha, match="captura inválida no caminho esperado"):
        CP.roda_worker("CRU", "capturar", cong, K.Travas("teste"))
    assert json.loads(destino.read_text(encoding="utf-8")) == plantado   # não sobrescreveu a evidência


def test_mudar_so_um_helper_ou_so_um_sidecar_invalida_a_captura():
    cong = congelamento(INV)
    cap = captura(cong, "CRU", decisoes_ok())
    helper = congelamento(INV, codigo={"replay_bloco_21-09.py": "b" * 64})
    assert "congelamento comum divergente" in valida(cap, helper)
    sidecar = copy.deepcopy(cong)
    sidecar["insumos_braco"]["CRU"] = K.sha_json({"palco": {"course/.glossary_curation.llm.json": "c" * 64}})
    assert "insumos do braço divergentes" in valida(cap, sidecar)


def test_conteudo_alterado_status_parcial_e_violacao_sao_rejeitados():
    cong = congelamento(INV)
    cap = captura(cong, "CRU", decisoes_ok())
    alterada = copy.deepcopy(cap)
    alterada["decisoes"]["S"]["e1"]["final"]["sub"] = "tX"
    assert "conteúdo alterado (hash não confere)" in valida(alterada, cong)
    parcial = captura(cong, "CRU", decisoes_ok())
    parcial["status"] = "falhou"
    parcial["conteudo_sha"] = K.conteudo_sha(parcial)
    assert any("status" in p for p in valida(parcial, cong))
    viol = captura(cong, "CRU", decisoes_ok())
    viol["violacoes"] = [{"tipo": "rede"}]
    viol["conteudo_sha"] = K.conteudo_sha(viol)
    assert any("violações" in p for p in valida(viol, cong))


def test_json_invalido_e_id_duplicado_sao_erro_de_integridade(tmp_path):
    ruim = tmp_path / "ruim.json"
    ruim.write_text('{"a": 1,', encoding="utf-8")
    with pytest.raises(K.ErroIntegridade):
        K.carrega_json_estrito(ruim)
    dup = tmp_path / "dup.json"
    dup.write_text('{"decisoes": {"S": {"e1": {}, "e1": {}}}}', encoding="utf-8")
    with pytest.raises(K.ErroIntegridade, match="duplicada"):
        K.carrega_json_estrito(dup)


def test_curso_extra_ausente_registro_incompleto_e_premissa_de_unidade():
    cong = congelamento(INV)
    extra = captura(cong, "CRU", decisoes_ok())
    extra["inventario"]["X"] = ["z"]
    extra["conteudo_sha"] = K.conteudo_sha(extra)
    assert any("extras ['X']" in p for p in valida(extra, cong))
    inc = decisoes_ok()
    del inc["S"]["e2"]["final"]["sub"]
    assert any("final.sub" in p for p in valida(captura(cong, "CRU", inc), cong))
    prem = decisoes_ok()
    prem["S"]["e1"]["p1"]["unidade_fornecida"] = "u9"
    assert any("unidade da 1ª passada != final" in p for p in valida(captura(cong, "CRU", prem), cong))


def test_gravacao_atomica_nao_deixa_parcial(tmp_path):
    destino = tmp_path / "cap.json"
    with pytest.raises(ValueError):
        K.grava_atomico(destino, {"x": float("nan")})
    assert not destino.exists() and not list(tmp_path.glob(".tmp-*"))


def test_git_com_erro_nao_vira_arvore_limpa(tmp_path):
    saida, erro = K.git("rev-parse", "HEAD", cwd=tmp_path)
    assert erro and "saiu" in erro


def test_captura_liberada_exatamente_os_sete_bracos_e_braco_fora_da_lista_rejeitado(tmp_path, monkeypatch):
    # W-AD5 (Gate condicional de 25/09): libera CAPTURA dos sete braços; gold continua bloqueado (teste da régua abaixo).
    assert K.CAPTURA_LIBERADA == frozenset({"CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1",
                                            "CTRL_ALEAT_2", "CTRL_ALEAT_3"}) == frozenset(K.BRACOS)
    monkeypatch.setattr(CP, "CAPS", tmp_path)
    cong = congelamento(INV)
    cong["insumos_braco"]["VOCAB_LIMPO"] = "x"   # braço que o protocolo não prevê
    with pytest.raises(CP.Falha, match="não autorizad"):
        CP.roda_worker("VOCAB_LIMPO", "capturar", cong, K.Travas("teste"))


def test_import_nao_carrega_produto_nem_avaliacao_historica():
    codigo = (f"import sys; sys.path.insert(0, {str(HERE)!r}); import avaliador, captura; "
              "print([m for m in sys.modules if m == 'src' or m.startswith('src.') or 'herancas' in m or 'wx_' in m "
              "or 'wz_' in m or 'mede_' in m or 'eval_' in m])")
    r = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True)
    assert r.stdout.strip() == "[]", r.stderr


# ------------------------------------------------------------------------------------------- §3 travas (processos separados)
MODELO = r'''
import json, socket, sys, types
sys.path.insert(0, {here!r})
import comum as K
t = K.Travas("teste")
t.permite("codigo", {base!r}, {prefix!r}, {here!r})
t.permite("saida", {saida!r})
{config}
t.instala()
try:
{acao}
except Exception:
    pass   # camada intermediária engolindo a exceção
with open({rel!r}, "w", encoding="utf-8") as fh:
    json.dump([v["tipo"] for v in t.violacoes], fh)
K.encerra(t, ok=True, codigo_falha={codigo})
'''


def roda(tmp_path, acao, config="", codigo=2):
    rel = tmp_path / "saida" / "viol.json"
    rel.parent.mkdir(exist_ok=True)
    src = MODELO.format(here=str(HERE), base=sys.base_prefix, prefix=sys.prefix, saida=str(tmp_path / "saida"),
                        config=config, acao="\n".join("    " + x for x in acao.strip().splitlines()), rel=str(rel), codigo=codigo)
    r = subprocess.run([sys.executable, "-B", "-c", src], capture_output=True, text=True)
    return r.returncode, json.loads(rel.read_text(encoding="utf-8")) if rel.exists() else None, r.stderr


def test_controle_sem_violacao_sai_zero(tmp_path):
    (tmp_path / "saida" / "ok.txt").parent.mkdir(exist_ok=True)
    (tmp_path / "saida" / "ok.txt").write_text("x", encoding="utf-8")
    rc, viol, err = roda(tmp_path, f"open({str(tmp_path / 'saida' / 'ok.txt')!r}).read()")
    assert (rc, viol) == (0, []), err


def test_leitura_de_arquivo_proibido_artificial(tmp_path):
    proibido = tmp_path / "saida" / "falso_gt_teste.csv"
    proibido.parent.mkdir(exist_ok=True)
    proibido.write_text("x", encoding="utf-8")
    rc, viol, _ = roda(tmp_path, f"open({str(proibido)!r}).read()")
    assert rc == 2 and viol == ["acesso_proibido"]


def test_leitura_de_palco_de_outro_braco(tmp_path):
    outro = tmp_path / "palcos" / "OUTRO"
    outro.mkdir(parents=True)
    (outro / "s.json").write_text("{}", encoding="utf-8")
    cfg = f"t.permite('braco', {str(tmp_path / 'palcos')!r}, somente_leitura=True)\nt.proibe({str(outro)!r}, 'outro braço')"
    rc, viol, _ = roda(tmp_path, f"open({str(outro / 's.json')!r}).read()", cfg)
    assert rc == 2 and viol == ["acesso_proibido"]


def test_tentativa_de_compilacao(tmp_path):
    cfg = "mod = types.SimpleNamespace(compile_course_vocabulary=lambda *a: 1)\nt.bloqueia_compilador(mod)"
    rc, viol, _ = roda(tmp_path, "mod.compile_course_vocabulary()", cfg)
    assert rc == 2 and viol == ["compilador"]


def test_tentativas_de_rede(tmp_path):
    acao = "try:\n    socket.create_connection(('127.0.0.1', 9))\nexcept Exception:\n    pass\nsocket.socket().connect(('127.0.0.1', 9))"
    rc, viol, _ = roda(tmp_path, acao)
    assert rc == 2 and viol == ["rede", "rede"]


def test_insumo_congelado_divergente_e_nao_congelado(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    (raiz / "a.txt").write_text("a", encoding="utf-8")
    (raiz / "b.txt").write_text("b", encoding="utf-8")
    cfg = f"t.permite('comum', {str(raiz)!r}, somente_leitura=True)\nt.congela({str(raiz)!r}, {{'a.txt': '0' * 64}})"
    rc, viol, _ = roda(tmp_path, f"open({str(raiz / 'a.txt')!r}).read()", cfg)
    assert rc == 2 and viol == ["insumo_divergente"]
    rc, viol, _ = roda(tmp_path, f"open({str(raiz / 'b.txt')!r}).read()", cfg)
    assert rc == 2 and viol == ["insumo_nao_congelado"]


def test_entrada_externa_so_pelo_caminho_exato_e_congelada(tmp_path):
    pasta = tmp_path / "Moodle"
    pasta.mkdir()
    (pasta / "exemplo.zip").write_bytes(b"zip")
    (pasta / "vizinho.zip").write_bytes(b"outro")
    h = K.sha_bytes(b"zip")
    cfg = f"t.congela_arquivos({{{str(pasta / 'exemplo.zip')!r}: {h!r}}})"
    rc, viol, err = roda(tmp_path, f"open({str(pasta / 'exemplo.zip')!r}, 'rb').read()", cfg)
    assert (rc, viol) == (0, []), err
    rc, viol, _ = roda(tmp_path, f"open({str(pasta / 'vizinho.zip')!r}, 'rb').read()", cfg)
    assert rc == 2 and viol == ["fora_da_lista"]
    cfg_ruim = f"t.congela_arquivos({{{str(pasta / 'exemplo.zip')!r}: {'0' * 64!r}}})"
    rc, viol, _ = roda(tmp_path, f"open({str(pasta / 'exemplo.zip')!r}, 'rb').read()", cfg_ruim)
    assert rc == 2 and viol == ["insumo_divergente"]


def test_violacao_capturada_internamente_ainda_reprova(tmp_path):
    fora = tmp_path / "fora.txt"
    fora.write_text("x", encoding="utf-8")
    rc, viol, _ = roda(tmp_path, f"try:\n    open({str(fora)!r}).read()\nexcept Exception:\n    pass")
    assert rc == 2 and viol == ["fora_da_lista"]


def test_negado_por_declaracao_impede_leitura_sem_virar_violacao(tmp_path):
    segredo = tmp_path / "saida" / ".env"
    segredo.parent.mkdir(exist_ok=True)
    segredo.write_text("CHAVE=valor-secreto", encoding="utf-8")
    cfg = f"t.nega({str(segredo)!r}, 'segredos')"
    acao = (f"try:\n    open({str(segredo)!r}).read()\n    raise SystemExit(9)\n"
            "except PermissionError:\n    pass")
    rc, viol, err = roda(tmp_path, acao, cfg)
    assert (rc, viol) == (0, []), err


def test_violacao_so_no_processo_principal_sai_com_erro(tmp_path):
    rc, viol, _ = roda(tmp_path, "t.registra('teste_principal', 'só no principal')", codigo=1)
    assert rc == 1 and viol == ["teste_principal"]


# ------------------------------------------------------------------------------------------- P4 referência
def test_compara_referencia_cursos_ids_e_registros(tmp_path, monkeypatch):
    monkeypatch.setattr(K, "NOMES", {"S": "S-Tutor", "T": "T-Tutor"})
    ref = {"M1": {"S": {"e1": {"bloco": "b", "unidade": "u", "sub": "t"}, "__saved__": {}},
                  "T": {"e9": {"bloco": "b", "unidade": "u"}}}}
    p = tmp_path / "ref.json"
    p.write_text(json.dumps(ref), encoding="utf-8")
    cru = {"decisoes": {"S": {"e1": {"final": {"bloco": "b", "unidade": "u", "sub": "t"}}},
                        "T": {"e9": {"final": {"bloco": "b", "unidade": "u", "sub": "t"}}},
                        "X": {}}}
    prob, difs = CP.compara_referencia(cru, p)
    assert any("captura: cursos ['X']" in x for x in prob)
    assert any("T/e9: registro de referência incompleto" in x for x in prob)
    ausente = {"decisoes": {"S": {"e1": {"final": {"bloco": "b", "unidade": "u", "sub": "t"}}}}}
    prob, _ = CP.compara_referencia(ausente, p)
    assert any("captura: cursos ['T']" in x for x in prob)
    p.write_text('{"M1": {"S": {"e1": {}, "e1": {}}, "T": {}}}', encoding="utf-8")
    with pytest.raises(K.ErroIntegridade, match="duplicada"):
        CP.compara_referencia(cru, p)


# ------------------------------------------------------------------------------------------- §5 instrumentação
def seletor_falso(entry, taxonomy, markdown_text, winning_unit_slug="", *, collect_entry_unit_signals,
                  iter_content_taxonomy_topics, score_entry_against_taxonomy_topic, topic_match_result_factory):
    tops = [t for t in iter_content_taxonomy_topics(taxonomy) if not winning_unit_slug or t["unit_slug"] == winning_unit_slug]
    pont = [(t, score_entry_against_taxonomy_topic({}, t)) for t in tops]
    melhor = max(pont, key=lambda x: x[1]) if pont else None
    return topic_match_result_factory(topic_slug=melhor[0]["topic_slug"] if melhor else "",
                                      unit_slug=melhor[0]["unit_slug"] if melhor else "", confidence=0.123456789012345,
                                      ambiguous=False, reasons=["r" * 300, "segundo"])


def test_instrumentacao_preserva_valores_exatos_identidade_e_decisao():
    sub_orig = functools.partial(seletor_falso, collect_entry_unit_signals=None, iter_content_taxonomy_topics=lambda tx: tx,
                                 score_entry_against_taxonomy_topic=lambda s, t: t["score"],
                                 topic_match_result_factory=SimpleNamespace)
    tax = [{"unit_slug": "u1", "topic_slug": "t", "score": 0.0000004},
           {"unit_slug": "u2", "topic_slug": "t", "score": 0.0499996},
           {"unit_slug": "u2", "topic_slug": "x", "score": 0.05}]
    chamadas, estado = {}, {"sig": "S"}
    sub = CP.instrumenta(sub_orig, chamadas, estado)
    m = sub({"id": "e1"}, tax, "", winning_unit_slug="")
    assert m == sub_orig({"id": "e1"}, tax, "", winning_unit_slug="")          # decisão intacta
    c = chamadas["S"]["e1"][0]
    assert c["unidade_fornecida"] == ""
    assert c["pontuacoes"] == [{"unidade": "u1", "topico": "t", "score": 0.0000004},
                               {"unidade": "u2", "topico": "t", "score": 0.0499996},
                               {"unidade": "u2", "topico": "x", "score": 0.05}]
    assert c["vencedor"] == {"unidade": "u2", "topico": "x"}                    # unidade do vencedor, não a "vazia"
    assert c["conf"] == 0.123456789012345 and c["motivos"] == ["r" * 300, "segundo"]
    sub({"id": "e1"}, tax, "", winning_unit_slug="u1")
    assert [x["unidade_fornecida"] for x in chamadas["S"]["e1"]] == ["", "u1"]  # 2ª chamada registrada à parte
    assert "e2" not in chamadas["S"]                                            # seletor não chamado: sem registro


# ------------------------------------------------------------------------------------------- §6 equivalências e verificação
def tax_de(topicos):
    return {"version": 1, "units": [{"slug": u, "title": u.upper(), "topics": [
        {"slug": s, "label": s, "code": "", "kind": "topic", "unit_slug": u, "aliases": list(al)} for s, al in tops]}
        for u, tops in topicos]}


def test_verifica_controle_reprova_acrescimo_com_remocao():
    sem = tax_de([("u1", [("t1", ["velho"]), ("t2", [])])])
    com = tax_de([("u1", [("t1", ["novo"]), ("t2", [])])])
    r = CP.verifica_controle({("u1", "t1"): ["novo"]}, sem, com)
    assert not r["aprovado"] and any("remoção" in p for p in r["problemas"])


def test_verifica_controle_reprova_mudanca_estrutural():
    sem = tax_de([("u1", [("t1", [])])])
    com = copy.deepcopy(sem)
    com["units"][0]["topics"][0]["label"] = "outro"
    com["units"][0]["topics"][0]["aliases"] = ["a"]
    assert not CP.verifica_controle({("u1", "t1"): ["a"]}, sem, com)["aprovado"]


def test_multiconjunto_igual_nao_e_identidade_ordenada():
    a = tax_de([("u1", [("t1", ["x", "y"])])])
    b = tax_de([("u1", [("t1", ["y", "x"])])])
    sem = tax_de([("u1", [("t1", [])])])
    assert CP.verifica_controle({("u1", "t1"): ["x", "y"]}, sem, b)["aprovado"]   # controle: multiconjunto declarado
    assert a != b                                                                   # identidade C exige ordem: reprova


def test_diagnostico_b_inspeciona_tudo_e_separa_ordem_de_conteudo():
    muitos = [(f"t{i}", ["a", "b"]) for i in range(30)]
    invertidos = [(f"t{i}", ["b", "a"]) for i in range(30)]
    d = CP.diagnostico_b(tax_de([("u1", muitos)]), tax_de([("u1", invertidos)]))
    assert d["somente_ordem_de_aliases"] and d["topicos_so_ordem"] == 30 and d["n_diferencas"] == 60
    d = CP.diagnostico_b(tax_de([("u1", [("t1", ["a"])])]), tax_de([("u1", [("t1", ["b"])])]))
    assert not d["somente_ordem_de_aliases"] and d["topicos_outra_diferenca"] == 1


# ------------------------------------------------------------------------------------------- §8 controles
class RngFixo:
    def __init__(self, fn):
        self.fn = fn

    def shuffle(self, v):
        v[:] = self.fn(v)


def test_identidade_sorteada_nao_e_nao_informativa():
    rels = [("a", ("u", "t1")), ("b", ("u", "t2"))]
    pares, estado, n = CP.embaralha_unidade(rels, [o for _a, o in rels], {}, RngFixo(lambda v: v))
    assert (estado, n, pares) == ("identidade_sorteada", 1, rels)


def test_pareado_estrutural_e_sem_permutacao_no_orcamento():
    rels = [("a", ("u", "t1")), ("b", ("u", "t2"))]
    pares, estado, _ = CP.embaralha_unidade(rels, [o for _a, o in rels], {}, RngFixo(lambda v: v[::-1]))
    assert estado == "pareado" and pares == [("a", ("u", "t2")), ("b", ("u", "t1"))]
    um = [("a", ("u", "t1")), ("b", ("u", "t1"))]
    assert CP.embaralha_unidade(um, [o for _a, o in um], {}, random.Random(1))[1] == "estruturalmente_nao_informativa"
    sem = {("u", "t1"): ["a", "b"], ("u", "t2"): ["a", "b"]}
    _p, estado, n = CP.embaralha_unidade(rels, [o for _a, o in rels], sem, random.Random(1), tentativas=5)
    assert (estado, n) == ("sem_permutacao_valida_no_orcamento", 5)


def test_controle_aleatorio_marca_bloqueio():
    tax = tax_de([("u", [("t1", ["a", "b"]), ("t2", ["a", "b"])])])
    rel = {("u", "t1"): {"add": ["a"], "rem": []}, ("u", "t2"): {"add": ["b"], "rem": []}}
    _atrib, info, bloq = CP.controle_aleatorio(rel, tax, "S", 1)
    assert bloq and info["u"]["estado"] == "sem_permutacao_valida_no_orcamento"


# ------------------------------------------------------------------------------------------- §9 avaliador
def linha(gid, eid, sp=None, sa=None, bloco=None, unidade=None):
    return {"gold_id": gid, "eid": eid, "bloco": bloco, "unidade": unidade, "sub_primaria": sp, "sub_aceita": sa}


REGUA = {"S": [linha("r1", "e1", {"t1"}, {"t1"}), linha("r2", "e2", {"t2"}, {"t2"}), linha("r3", "e3", {"t3"}, {"t3"}),
               linha("r4", "e4", {"t4"}, {"t4"}), linha("r5", "e5", {"t5"}, {"t5", "t6"}), linha("r6", "e6", {"t6"}, {"t6"}),
               linha("r7", "e7", {"t7"}, {"t7"}), linha("r8", "e8", {""}, {""}), linha("r9", None, {"t1"}, {"t1"})]}
INV8 = {"S": [f"e{i}" for i in range(1, 9)]}
SUB_CRU = {"e1": "t1", "e2": "t9", "e3": "t3", "e4": "t8", "e5": "t5", "e6": "", "e7": "", "e8": "t9"}
SUB_LLM = {"e1": "t1", "e2": "t2", "e3": "t9", "e4": "t9", "e5": "t6", "e6": "t6", "e7": "t9", "e8": ""}


def decisoes_de(subs):
    return {"S": {e: registro("S", e, s) for e, s in subs.items()}}


@pytest.fixture
def cenario(monkeypatch):
    monkeypatch.setattr(K, "INVENTARIO_ESPERADO", 8)
    monkeypatch.setattr(K, "DENOMINADORES", {"bloco": 0, "unidade": 0, "sub_primaria": 9})
    monkeypatch.setattr(K, "DENOM_POR_CURSO", {"S": {"bloco": 0, "unidade": 0, "sub_primaria": 9}})
    monkeypatch.setattr(K, "REFERENCIA_CRU", {"S": {"bloco": 0, "unidade": 0, "sub_primaria": 3}})
    cong = congelamento(INV8)
    caps = {b: captura(cong, b, decisoes_de(SUB_CRU)) for b in K.BRACOS}
    caps["VOCAB_LLM"] = captura(cong, "VOCAB_LLM", decisoes_de(SUB_LLM))
    tax = tax_de([("u1", [(f"t{i}", []) for i in range(1, 10)])])
    return cong, caps, {b: {"S": tax} for b in K.BRACOS}


def test_avaliacao_placar_transicoes_precisao_e_veredictos(cenario):
    cong, caps, taxs = cenario
    r = AV.avalia(caps, cong, REGUA, taxs)
    assert r["placar"]["CRU"]["TOTAL"]["sub_primaria"] == {"acertos": 3, "n": 9}
    assert r["placar"]["VOCAB_LLM"]["TOTAL"]["sub_primaria"] == {"acertos": 4, "n": 9}
    assert r["placar"]["VOCAB_LLM"]["TOTAL"]["sub_aceita"] == {"acertos": 5, "n": 9}
    tp = r["comparacoes"]["VOCAB_LLM"]["sub_primaria"]
    assert tp["derivadas"] == {"correcao": 3, "perda": 2, "erro_para_outro_erro": 2, "abstencao_para_certa": 1,
                               "abstencao_para_errada": 1, "decisao_para_vazio": 1}
    assert tp["precisao_alteradas"] == {"num": 3, "den": 7, "valor": 3 / 7}
    assert tp["precisao_alteradas_nao_vazias"] == {"num": 2, "den": 6, "valor": 2 / 6}
    ta = r["comparacoes"]["VOCAB_LLM"]["sub_aceita"]
    assert ta["derivadas"]["correta_para_outra_correta"] == 1 and ta["derivadas"]["perda"] == 1
    assert ta["precisao_alteradas"] == {"num": 4, "den": 7, "valor": 4 / 7}
    igual = r["comparacoes"]["CTRL_MAIOR"]["sub_primaria"]["precisao_alteradas"]
    assert igual == {"num": 0, "den": 0, "valor": "não aplicável"}
    v = r["veredictos"]
    assert v["A_sinal_exploratorio"] is True
    assert v["B_integracao"] == "sinal exploratório observado; candidato reprovado para integração"
    assert v["B_perdas"] == {"bloco": 0, "unidade": 0, "sub_primaria": 2} and v["B_perdas_sub_aceita_auxiliar"] == 1


def test_registros_por_id_sao_a_origem_dos_agregados(cenario):
    cong, caps, taxs = cenario
    r = AV.avalia(caps, cong, REGUA, taxs)
    regs = r["registros"]["VOCAB_LLM"]
    assert len(regs) == 18                                              # 9 linhas x (primária, aceita)
    assert sum(x["certo"] for x in regs if x["eixo"] == "sub_primaria") == 4
    assert {x["gold_id"] for x in regs if x["eixo"] == "sub_primaria" and x["certo"]} == {"r1", "r2", "r6", "r8"}
    tr = r["comparacoes"]["VOCAB_LLM"]["sub_primaria"]
    assert len(tr["registros"]) == sum(tr["celulas"].values()) == 9
    assert [x["gold_id"] for x in tr["registros"] if x["certo_antes"] and not x["certo_depois"]] == ["r3", "r5"]
    quebrado = copy.deepcopy(tr)
    quebrado["derivadas"]["perda"] += 1                                 # agregado que não bate com os registros
    pl = r["placar"]
    assert any("correções − perdas" in p for p in AV.confere_transicoes(quebrado, pl["CRU"], pl["VOCAB_LLM"], "sub_primaria"))
    assert AV.confere_transicoes(tr, pl["CRU"], pl["VOCAB_LLM"], "sub_primaria") == []


def test_cru_que_nao_reproduz_a_referencia_por_curso_recusa(cenario, monkeypatch):
    cong, caps, taxs = cenario
    monkeypatch.setattr(K, "REFERENCIA_CRU", {"S": {"bloco": 0, "unidade": 0, "sub_primaria": 4}})
    with pytest.raises(K.ErroIntegridade, match="S/sub_primaria: CRU 3 != referência 4"):
        AV.avalia(caps, cong, REGUA, taxs)


def test_material_ausente_e_erro_e_registro_ausente_invalida(cenario):
    cong, caps, _ = cenario
    assert AV.acerta("sub_primaria", linha("rx", None, {""}, {""}), None) is False   # ausente nunca vira abstenção certa
    assert AV.acerta("sub_primaria", linha("rx", "e8", {""}, {""}), caps["VOCAB_LLM"]["decisoes"]["S"]["e8"]) is True
    quebrada = copy.deepcopy(caps["CRU"])
    del quebrada["decisoes"]["S"]["e3"]
    with pytest.raises(K.ErroIntegridade):
        AV.registro(quebrada, "S", "e3")


def test_avaliacao_recusa_conjunto_invalido(cenario):
    cong, caps, taxs = cenario
    outro = congelamento(INV8, codigo={"replay_bloco_21-09.py": "f" * 64})
    caps2 = dict(caps)
    caps2["CTRL_MAIOR"] = captura(outro, "CTRL_MAIOR", decisoes_de(SUB_CRU))
    with pytest.raises(K.ErroIntegridade, match="recusada"):
        AV.avalia(caps2, cong, REGUA, taxs)
    sem_braco = {b: c for b, c in caps.items() if b != "CTRL_ALEAT_3"}
    assert any("faltam ['CTRL_ALEAT_3']" in p for p in AV.valida_conjunto(sem_braco, cong))
    bloq = copy.deepcopy(cong)
    bloq["controles"]["bloqueados"] = ["CTRL_ALEAT_1/S"]
    assert any("bloqueados" in p for p in AV.valida_conjunto(caps, bloq))
    regua_dup = {"S": REGUA["S"] + [linha("r1", "e1", {"t1"}, {"t1"})]}
    assert any("duplicado" in p for p in AV.valida_regua(regua_dup, INV8))
    fora = {"S": REGUA["S"][:-1] + [linha("r9", "e99", {"t1"}, {"t1"})]}
    assert any("fora do inventário" in p for p in AV.valida_regua(fora, INV8))
    extra = dict(REGUA, X=[])
    assert any("extras ['X']" in p for p in AV.valida_regua(extra, INV8))


def test_meta_por_contagem_exata():
    pl = {"S": {"bloco": {"acertos": 9, "n": 10}, "unidade": {"acertos": 10, "n": 11}, "sub_primaria": {"acertos": 0, "n": 0}}}
    assert AV.meta(pl, {"S": []}) == {"S": {"bloco": False, "unidade": True, "sub_primaria": "não aplicável"}}


def test_estados_da_selecao():
    base = registro("S", "e", "t1", pontuacoes=[{"unidade": "u1", "topico": "t1", "score": 0.4}])
    assert AV.estado_selecao(base) == "decidido"
    assert AV.estado_selecao(registro("S", "e", "", chamado=False)) == "nao_chamado"
    assert AV.estado_selecao(registro("S", "e", "", pontuacoes=[])) == "chamado_sem_topicos_elegiveis"
    zero = registro("S", "e", "", pontuacoes=[{"unidade": "u1", "topico": "t1", "score": 0.0}])
    assert AV.estado_selecao(zero) == "candidatos_score_zero"
    emp = registro("S", "e", "t1", pontuacoes=[{"unidade": "u1", "topico": "t1", "score": 0.3},
                                               {"unidade": "u1", "topico": "t2", "score": 0.3}])
    assert AV.estado_selecao(emp) == "empate"
    amb = registro("S", "e", "t1", pontuacoes=[{"unidade": "u1", "topico": "t1", "score": 0.3}], amb=True)
    assert AV.estado_selecao(amb) == "ambigua_com_slug"
    assert amb["final"]["sub"] == "t1"   # ambiguidade não vira vazio


def test_score_do_gold_homonimos_limiares_e_unidade_vazia():
    pts = [{"unidade": "u1", "topico": "t", "score": 0.9}, {"unidade": "u2", "topico": "t", "score": 0.0000004}]
    r = registro("S", "e", "x", unidade="u2", pontuacoes=pts)
    assert AV.score_do_gold(r, {"t"}) == 0.0000004
    assert AV.CORTES["maior_que_zero"](0.0000004) and not AV.CORTES["maior_ou_igual_0_05"](0.0000004)
    assert not AV.CORTES["maior_ou_igual_0_05"](0.0499996) and AV.CORTES["maior_ou_igual_0_05"](0.05)
    vazio = registro("S", "e", "x", unidade="", pontuacoes=pts)
    assert AV.score_do_gold(vazio, {"t"}) == 0.9
    assert AV.score_do_gold(registro("S", "e", "", chamado=False), {"t"}) is None


def test_geracao_grupos_e_selecao_no_subconjunto_comum():
    tax = {"S": tax_de([("u1", [("t1", []), ("t2", [])])])}
    regua = {"S": [linha("r1", "e1", {"t1"}, {"t1"}), linha("r2", "e2", {"t2"}, {"t2"}), linha("r3", "e3", {"t2"}, {"t2"})]}
    cru = {"decisoes": {"S": {
        "e1": registro("S", "e1", "t2", pontuacoes=[{"unidade": "u1", "topico": "t1", "score": 0.3},
                                                    {"unidade": "u1", "topico": "t2", "score": 0.4}]),
        "e2": registro("S", "e2", "t1", pontuacoes=[{"unidade": "u1", "topico": "t2", "score": 0.0000004},
                                                    {"unidade": "u1", "topico": "t1", "score": 0.2}]),
        "e3": registro("S", "e3", "", unidade="u9", chamado=False)}}}
    llm = {"decisoes": {"S": {
        "e1": registro("S", "e1", "t1", pontuacoes=[{"unidade": "u1", "topico": "t1", "score": 0.5}]),
        "e2": registro("S", "e2", "t2", pontuacoes=[{"unidade": "u1", "topico": "t2", "score": 0.06}]),
        "e3": registro("S", "e3", "", unidade="u9", chamado=False)}}}
    g = AV.geracao_selecao(cru, llm, regua, tax, tax)
    assert g["grupos"]["maior_que_zero"] == {"ambos": 2, "nenhum": 1}
    assert g["grupos"]["maior_ou_igual_0_05"] == {"ambos": 1, "so_braco": 1, "nenhum": 1}
    s = g["selecao_subconjunto_comum"]["maior_ou_igual_0_05"]
    assert s["CRU"]["final"] == {"num": 0, "den": 1, "valor": 0.0} and s["BRACO"]["final"] == {"num": 1, "den": 1, "valor": 1.0}
    e = g["escada"]["CRU"]
    assert (e["n_avaliadas"], e["a_existe"], e["chamados"], e["a_elegivel"]) == (3, 3, 2, 2)   # e3 não chamado: fora de b-d
    assert e["b_score_pos"] == 2 and e["c_score_ge_0_05"] == 1
    assert g["escada"]["BRACO"]["e_final_correta"] == 2
    e3 = [m for m in g["materiais"] if m["gold_id"] == "r3"][0]["CRU"]
    assert e3["elegivel"] == AV.NA and e3["estado_1a"] == "nao_chamado" and e3["rotulo_existe_na_taxonomia"] is True


def test_regua_de_estado_segue_o_contrato_historico():
    estado = {"S": {"rows": [{"entry_id": "g1", "bloco": "x", "unidade": "x", "sub_primario": "x"},
                             {"entry_id": "g2", "bloco": "", "unidade": "", "sub_primario": "x"}],
                    "eid_de": {"g1": "e1", "g2": None},
                    "golds": ({"g1": "b1", "g2": "b2"}, {"g1": {"u1"}, "g2": {"u2"}},
                              {"g1": {"t1", "t2"}, "g2": {""}}, {"g1": {"t1"}, "g2": {""}})}}
    assert AV.regua_de_estado(estado) == {"S": [
        {"gold_id": "g1", "eid": "e1", "bloco": "b1", "unidade": {"u1"}, "sub_primaria": {"t1"}, "sub_aceita": {"t1", "t2"}},
        {"gold_id": "g2", "eid": None, "bloco": None, "unidade": None, "sub_primaria": {""}, "sub_aceita": {""}}]}
    quebrado = copy.deepcopy(estado)
    del quebrado["S"]["golds"][3]["g1"]
    with pytest.raises(K.ErroIntegridade):
        AV.regua_de_estado(quebrado)


def _regua_sintetica(tmp_path, monkeypatch):
    """Mini-repositório SINTÉTICO com os papéis da régua histórica; nenhum arquivo real é lido."""
    monkeypatch.setattr(AV, "DATA", tmp_path)
    monkeypatch.setattr(K, "NOMES", {"S": "S-Tutor"})
    monkeypatch.setattr(AV, "UNI", frozenset({"S"}))
    arquivos = {
        "ground_truth": ("r/gt.csv", "id,true_block_id,scorable\ng1,b1,yes\ng2,b2,no\n"),
        "gold_units": ("r/gu.csv", "block_uuid,true_unit\n"),
        "material_gt": ("r/mg.csv", "entry_id,gold_units,scorable\ng1,u1|u2,yes\n"),
        "subunit_gt": ("r/sg.csv", "entry_id,scorable,gold_subunit,gold_subunits_extra\ng1,yes,t1,t2;t3\ng2,yes,,\n"),
        "herancas_csv": ("r/h.csv", "entry_id,bloco,unidade,sub_primario\ng1,x,x,x\ng2,,,x\n"),
        "herancas_json": ("r/h.json", json.dumps({"entries": [{"entry_id": "g1", "new_id": "old1"}]})),
    }
    desc = {"arquivos": {}, "pendencias": []}
    for papel, (rel, txt) in arquivos.items():
        (tmp_path / rel).parent.mkdir(exist_ok=True)
        (tmp_path / rel).write_bytes(txt.encode("utf-8"))
        desc["arquivos"][papel] = {"S": {"caminho": rel, "blob_git": K.blob_git(txt.encode("utf-8"))}}
    ref = json.dumps({"entries": [{"id": "old1", "source_path": "C:/x/a.pdf"}]}).encode("utf-8")
    saved = json.dumps({"entries": [{"id": "e1", "source_path": "C:/x/a.pdf"},
                                    {"id": "g2", "source_path": "C:/x/b.pdf"}]}).encode("utf-8")
    for rel, dados in (("ref/manifest.json", ref), ("raiz/manifest.json", saved)):
        (tmp_path / rel).parent.mkdir(exist_ok=True)
        (tmp_path / rel).write_bytes(dados)
    desc["manifestos_referencia"] = {"S": {"caminho": "ref/manifest.json", "sha256": K.sha_bytes(ref)}}
    cong = {"normativo": {"avaliacao": desc, "entradas_comuns": {"S": {"raiz": "raiz"}}}}
    return cong, {"S": {"manifest.json": K.sha_bytes(saved)}}


def test_carregador_local_segue_o_historico_com_bytes_conferidos(tmp_path, monkeypatch):
    cong, entradas = _regua_sintetica(tmp_path, monkeypatch)
    with pytest.raises(PermissionError):
        AV.carrega_regua_historica(cong, entradas)
    regua, prov = AV.carrega_regua_historica(cong, entradas, autorizado=True)
    assert regua == {"S": [
        {"gold_id": "g1", "eid": "e1", "bloco": "b1", "unidade": {"u1", "u2"}, "sub_primaria": {"t1"},
         "sub_aceita": {"t1", "t2", "t3"}},
        {"gold_id": "g2", "eid": "g2", "bloco": None, "unidade": None, "sub_primaria": {""}, "sub_aceita": {""}}]}
    assert prov["mapeamento"]["S"] == {"ponte": ["g2"], "ausentes": []}
    assert set(prov["arquivos_conferidos"]) == {"r/gt.csv", "r/gu.csv", "r/mg.csv", "r/sg.csv", "r/h.csv", "r/h.json"}


def test_carregador_local_recusa_bytes_manifest_e_pendencias_divergentes(tmp_path, monkeypatch):
    cong, entradas = _regua_sintetica(tmp_path, monkeypatch)
    sg = tmp_path / "r/sg.csv"
    sg.write_bytes(sg.read_bytes() + b"g3,yes,t9,\n")
    with pytest.raises(K.ErroIntegridade, match="blob"):
        AV.carrega_regua_historica(cong, entradas, autorizado=True)
    cong, entradas = _regua_sintetica(tmp_path, monkeypatch)
    entradas["S"]["manifest.json"] = "0" * 64
    with pytest.raises(K.ErroIntegridade, match="sha256"):
        AV.carrega_regua_historica(cong, entradas, autorizado=True)
    cong, entradas = _regua_sintetica(tmp_path, monkeypatch)
    cong["normativo"]["avaliacao"]["pendencias"] = ["sem blob no índice do git: r/gt.csv"]
    with pytest.raises(K.ErroIntegridade, match="pendências"):
        AV.carrega_regua_historica(cong, entradas, autorizado=True)


def test_regua_real_bloqueada_sem_autorizacao():
    with pytest.raises(PermissionError):
        AV.carrega_regua_historica()
    r = subprocess.run([sys.executable, "-B", str(HERE / "avaliador.py")], capture_output=True, text=True)
    assert r.returncode == 2 and "não autorizada" in r.stdout
