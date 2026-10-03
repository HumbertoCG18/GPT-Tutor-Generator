"""Testes do harness genérico (validação externa, 29/09). Só dados sintéticos; nenhum curso real, gold, rede ou LLM.

Rodar: RODADA_CONFIG=rodada_vl_equivalente.json python -B -m pytest . -q -p no:cacheprovider
A suíte herdada (test_wad4, test_defeitos_v4, test_ajustes_v5) é idêntica byte a byte à da rodada VOCAB_LIMPO.
"""
import ast
import copy
import io
import json
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
VL = HERE.parents[1] / "vocab_limpo_26-09"
sys.path.insert(0, str(HERE))
import avaliador as AV  # noqa: E402
import captura as CP  # noqa: E402
import comum as K  # noqa: E402
import gold_externo as GE  # noqa: E402
import rodada as RD  # noqa: E402
import test_wad4 as T  # noqa: E402

CODIGO_GENERICO = ["comum.py", "captura.py", "avaliador.py", "gold_externo.py", "rodada.py", "limpo.py", "sanidade.py",
                   "roda_controlado.py", "equivalencia.py"]
CURSOS_CONHECIDOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR", "LR", "LSO", "UX"]
BRACOS_VL = ["CRU_LIMPO", "VOCAB_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO", "VOCAB_LLM", "CTRL_ALEAT_1"]


def config_sintetica(tmp, tipo="gold_externo", invariancia=True, **muda):
    cursos = [{"sigla": s, "tutor": f"Curso-{s}-Tutor", "raiz_pacote": f".frzero/pacotes/{s}",
               "eixos": ["unidade", "sub_primaria"], "denominadores": {"bloco": 0, "unidade": 5, "sub_primaria": 4}}
              for s in ("C1", "C2")]
    arquivos = ({p: {s: f"gold/{p}_{s}" for s in ("C1", "C2")} for p in ("gold", "rotulos", "mapa")} if tipo == "gold_externo"
                else {"subunit_gt": {"C1": "x.csv"}})
    cfg = {"esquema": RD.ESQUEMA, "esquemas": {"captura": "ge-captura-1", "congelamento": "ge-congelamento-1"},
           "cursos": cursos, "tutores_proibidos": [],
           "bracos": {"cru": "CRU_X", "candidato": "VOCAB_X", "controle_maior": "CTRL_MAIOR_X",
                      "controles_aleatorios": [{"nome": f"CTRL_ALEAT_X_{i}", "semente": i} for i in (1, 2, 3)]},
           "inventario_esperado": 10, "referencia_cru": None,
           "regua": {"tipo": tipo, "arquivos": arquivos, "manifestos": {}, "codigo": {}, "invariancia_bloco": invariancia},
           "protocolo": "docs/x.md", "base_produto": "0" * 40, "saida_base": ".frzero/x/captura", "recompilacao": ".frzero/x",
           "sufixo": "x", "proibidos": {}, "staging_fonte": {"tipo": "manifesto_do_build", "arvores": {"C1": "0" * 64, "C2": "0" * 64}}}
    cfg.update(muda)
    p = tmp / "rodada.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p, cfg


def roda_equivalencia(pasta, cfg, modo="padrao"):
    env = {k: v for k, v in os.environ.items() if k != "RODADA_CONFIG"}
    if cfg:
        env["RODADA_CONFIG"] = str(cfg)
    r = subprocess.run([sys.executable, "-B", str(HERE / "equivalencia.py"), str(pasta), modo], capture_output=True,
                       text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout


# ------------------------------------------------------------------------------------------- semântica das métricas
def test_metricas_identicas_ao_vocab_limpo_com_qualquer_nome_de_braco(tmp_path):
    """Mesmo cenário: avaliador da rodada VOCAB_LIMPO, genérico com a config equivalente e genérico com outros nomes."""
    vl = roda_equivalencia(VL, None)
    gen = roda_equivalencia(HERE, HERE / "rodada_vl_equivalente.json")
    sint, _ = config_sintetica(tmp_path, tipo="historica", invariancia=False)
    outro = roda_equivalencia(HERE, sint)
    assert vl == gen == outro
    r = json.loads(vl)
    assert r["placar"]["CAND"]["TOTAL"]["sub_primaria"] == {"acertos": 4, "n": 9}   # conferência mínima do cenário


def _funcoes(caminho):
    """Fonte de cada função/classe por nome qualificado (funções internas homônimas não colidem)."""
    texto = Path(caminho).read_text(encoding="utf-8")
    out = {}

    def visita(no, prefixo):
        for filho in ast.iter_child_nodes(no):
            if isinstance(filho, (ast.FunctionDef, ast.ClassDef)):
                nome = prefixo + filho.name
                out[nome] = ast.get_source_segment(texto, filho)
                visita(filho, nome + ".")
            else:
                visita(filho, prefixo)

    visita(ast.parse(texto), "")
    return out


REVERTE = [("(K.CRU, K.CTRL_MAIOR, *K.CTRL_ALEAT)",
            '("CRU_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_LIMPO_2", "CTRL_ALEAT_LIMPO_3")'),
           ('f"C_meta_{K.CANDIDATO}"', '"C_meta_VOCAB_LIMPO"'), ("{K.CANDIDATO}", "VOCAB_LIMPO"), ("{K.CTRL_MAIOR}", "CTRL_MAIOR_LIMPO"),
           ("{K.CRU}", "CRU_LIMPO"), ("e[K.CANDIDATO]", "e['VOCAB_LIMPO']"), ("r[K.CTRL_MAIOR]", "r['CTRL_MAIOR_LIMPO']"),
           ("K.CANDIDATO", '"VOCAB_LIMPO"'), ("K.CTRL_MAIOR", '"CTRL_MAIOR_LIMPO"'), ("K.CRU", '"CRU_LIMPO"'),
           ("veredictos_rodada(pl, comp, regua, capturas)", "veredictos(pl, comp, regua)"),
           ("relações efetivas do candidato", "relações efetivas do VOCAB_LLM"),
           ('f"# Rodada {SUF} — captura dos braços, sem gold"', '"# Rodada VOCAB_LIMPO — captura dos seis braços, sem gold (26/09)"'),
           ('f"# Rodada {SUF} — preflight sem gold"', '"# Rodada VOCAB_LIMPO — preflight sem gold (26/09)"'),
           ('"| curso | A | B candidato só ordem | +candidato | -candidato |"', '"| curso | A | B LIMPO só ordem | +LIMPO | -LIMPO |"')]


def reverte(fonte):
    for a, b in REVERTE:
        fonte = fonte.replace(a, b)
    return fonte


@pytest.mark.parametrize("arquivo, mudadas_esperadas", [
    ("avaliador.py", {"veredictos", "avalia", "main"}),
    ("comum.py", {"valida_captura"}),
    ("captura.py", {"travas_principal", "preflight", "capturar_bracos", "executa", "sidecar_de", "escreve_md"}),
])
def test_so_as_funcoes_declaradas_mudam(arquivo, mudadas_esperadas):
    """Toda função/classe que existe nas duas versões é idêntica, exceto as declaradas (nomes de braço e rodada)."""
    vl, gen = _funcoes(VL / arquivo), _funcoes(HERE / arquivo)
    mudadas = {n for n in set(vl) & set(gen) if vl[n] != gen[n]}
    assert mudadas <= mudadas_esperadas, sorted(mudadas - mudadas_esperadas)
    assert set(vl) <= set(gen), sorted(set(vl) - set(gen))


@pytest.mark.parametrize("arquivo, nomes", [("avaliador.py", ("veredictos", "avalia")),
                                            ("captura.py", ("executa", "sidecar_de", "escreve_md"))])
def test_funcoes_mudadas_so_por_nome_de_braco_ou_rotulo(arquivo, nomes):
    """Revertendo só nomes de braço e rótulos, a função volta a ser byte a byte a da rodada VOCAB_LIMPO."""
    vl, gen = _funcoes(VL / arquivo), _funcoes(HERE / arquivo)
    for nome in nomes:
        assert reverte(gen[nome]) == vl[nome], nome


def test_sem_literal_de_curso_nem_de_braco_da_rodada_anterior():
    for arq in CODIGO_GENERICO:
        texto = (HERE / arq).read_text(encoding="utf-8")
        for t in tokenize.generate_tokens(io.StringIO(texto).readline):
            if t.type != tokenize.STRING or t.string.startswith(('"""', "'''")):
                continue
            for s in CURSOS_CONHECIDOS:
                assert not re.search(rf"(?<![\w-]){s}(?![\w-])", t.string), (arq, t.start[0], t.string[:80])
            assert "-Tutor" not in t.string and not any(b in t.string for b in BRACOS_VL), (arq, t.start[0], t.string[:80])


def test_codigo_congelado_inclui_configuracao_e_gold_externo():
    assert {"rodada.py", "rodada_config.json", "gold_externo.py", "test_generico.py"} <= set(CP.CODIGO)
    assert CP.CODIGO["rodada_config.json"] == RD.CAMINHO
    assert K.ENV_DECLARADO["RODADA_CONFIG"] == str(RD.CAMINHO)
    assert not K.verifica_ambiente(K.ambiente_controlado({"PATH": "x"}))


# ------------------------------------------------------------------------------------------- invariância de bloco
def test_invariancia_de_bloco_so_quando_configurada(tmp_path):
    sint, _ = config_sintetica(tmp_path)
    ok = json.loads(roda_equivalencia(HERE, sint, "invariancia"))["veredictos"]
    mudou = json.loads(roda_equivalencia(HERE, sint, "bloco_mudou"))["veredictos"]
    assert ok["B_integracao"].startswith("sem violação") and ok["B_rodada"] is True and ok["B_mudancas_bloco_por_id"] == []
    assert mudou["B_integracao"].startswith("sem violação") and mudou["B_rodada"] is False
    assert mudou["B_mudancas_bloco_por_id"] == ["S/e5"]
    vl = json.loads(roda_equivalencia(HERE, HERE / "rodada_vl_equivalente.json", "bloco_mudou"))["veredictos"]
    assert "B_rodada" not in vl and "B_mudancas_bloco_por_id" not in vl


# ------------------------------------------------------------------------------------------- configuração
def test_configuracao_invalida_e_recusada(tmp_path):
    _, cfg = config_sintetica(tmp_path)
    RD.valida(copy.deepcopy(cfg))
    ruins = []
    c = copy.deepcopy(cfg); c["cursos"][1]["sigla"] = "C1"; ruins.append(c)
    c = copy.deepcopy(cfg); c["cursos"][0]["denominadores"]["bloco"] = 3; ruins.append(c)
    c = copy.deepcopy(cfg); c["cursos"][0]["eixos"].append("bloco"); ruins.append(c)
    c = copy.deepcopy(cfg); c["regua"]["invariancia_bloco"] = False; ruins.append(c)
    c = copy.deepcopy(cfg); c["bracos"]["controles_aleatorios"][1]["semente"] = 1; ruins.append(c)
    c = copy.deepcopy(cfg); c["bracos"]["candidato"] = "CRU_X"; ruins.append(c)
    c = copy.deepcopy(cfg); del c["regua"]["arquivos"]["mapa"]; ruins.append(c)
    c = copy.deepcopy(cfg); c["extra"] = 1; c["esquema"] = "outro"; ruins.append(c)
    for ruim in ruins:
        with pytest.raises(RD.ConfigInvalida):
            RD.valida(ruim)


def test_sem_configuracao_nao_existe_rodada():
    env = {k: v for k, v in os.environ.items() if k != "RODADA_CONFIG"}
    r = subprocess.run([sys.executable, "-B", "-c", "import rodada"], cwd=HERE, capture_output=True, text=True, env=env)
    assert r.returncode != 0 and "RODADA_CONFIG" in r.stderr


# ------------------------------------------------------------------------------------------- gold externo
ROT = {"unidades": [{"id": "U01", "slug": "u-um"}, {"id": "U02", "slug": "u-dois"}],
       "topicos": [{"id": "U01.T01", "unidade": "U01", "slug": "t-a"}, {"id": "U01.T02", "unidade": "U01", "slug": "t-b"},
                   {"id": "U02.T01", "unidade": "U02", "slug": "t-c"}]}
IDS = ["m000000000001", "m000000000002", "m000000000003", "m000000000004", "m000000000005"]


def csv_gold(linhas):
    return ("\n".join([",".join(GE.CAMPOS)] + [",".join(ln) for ln in linhas]) + "\n").encode("utf-8")


GOLD_OK = [[IDS[0], "avaliado", "U01", "U01.T01", "U01.T01|U01.T02", ""],
           [IDS[1], "avaliado", "U01|U02", "U02.T01", "U02.T01", ""],
           [IDS[2], "meta", "-", "", "", "plano"],
           [IDS[3], "avaliado", "-", "-", "-", ""],
           [IDS[4], "excluido", "", "", "", "ilegível"]]


def test_gold_valido_e_traducao_para_a_regua():
    linhas = GE.le_csv(csv_gold(GOLD_OK))
    assert GE.valida(linhas, IDS, ROT) == []
    mapa = {IDS[0]: ["e1"], IDS[1]: ["e2", "e2b"], IDS[2]: ["e3"], IDS[3]: [], IDS[4]: ["e5"]}
    regua, resumo = GE.regua(linhas, ROT, mapa)
    por = {r["gold_id"]: r for r in regua}
    assert por[IDS[0]] == {"gold_id": IDS[0], "eid": "e1", "bloco": None, "unidade": {"u-um"}, "sub_primaria": {"t-a"},
                           "sub_aceita": {"t-a", "t-b"}}
    assert {f"{IDS[1]}@e2", f"{IDS[1]}@e2b"} <= set(por) and por[f"{IDS[1]}@e2"]["unidade"] == {"u-um", "u-dois"}
    assert por[IDS[2]]["sub_primaria"] is None and por[IDS[2]]["unidade"] == {""}
    assert por[IDS[3]]["eid"] is None and por[IDS[3]]["sub_primaria"] == {""}
    assert IDS[4] not in por
    assert resumo == {"linhas_gold": 5, "excluidos": 1, "ausentes": 1, "replicados": 1}
    assert GE.denominadores(regua) == {"bloco": 0, "unidade": 5, "sub_primaria": 4}
    # a régua traduzida segue o contrato do avaliador (denominadores da config sintética à parte):
    prob = [p for p in AV.valida_regua({"C1": regua}, {"C1": ["e1", "e2", "e2b", "e3", "e5"]})
            if "denominador" not in p and "cursos divergentes" not in p]
    assert prob == []


@pytest.mark.parametrize("mexe, trecho", [
    (lambda g: g[0].__setitem__(3, "U02.T01"), "fora das unidades"),
    (lambda g: g[0].__setitem__(4, "U01.T02"), "não contida"),
    (lambda g: g[0].__setitem__(2, "U09"), "unidade desconhecida"),
    (lambda g: g[2].__setitem__(3, "U01.T01"), "meta exige"),
    (lambda g: g[4].__setitem__(2, "U01"), "excluido exige"),
    (lambda g: g[0].__setitem__(1, "talvez"), "status inválido"),
    (lambda g: g[3].__setitem__(4, "U01.T01"), "'-' em só uma"),
    (lambda g: g.pop(), "diferente dos adjudicáveis"),
    (lambda g: g.append(list(g[0])), "repetido"),
    (lambda g: g[0].__setitem__(4, "U01.T01|U01.T01"), "repetição"),
])
def test_gold_invalido_e_recusado(mexe, trecho):
    g = copy.deepcopy(GOLD_OK)
    mexe(g)
    prob = GE.valida(GE.le_csv(csv_gold(g)), IDS, ROT)
    assert any(trecho in p for p in prob), prob


def test_csv_com_bom_crlf_ou_cabecalho_errado_e_recusado():
    with pytest.raises(GE.GoldInvalido):
        GE.le_csv(b"\xef\xbb\xbf" + csv_gold(GOLD_OK))
    with pytest.raises(GE.GoldInvalido):
        GE.le_csv(csv_gold(GOLD_OK).replace(b"\n", b"\r\n"))
    with pytest.raises(GE.GoldInvalido):
        GE.le_csv(b"material_id,status\n")


def test_ligacao_por_hash_usa_so_campos_permitidos():
    materiais = [{"material_id": IDS[0], "sha256": "a", "adjudicavel": True},
                 {"material_id": IDS[1], "sha256": "b", "adjudicavel": True},
                 {"material_id": IDS[2], "sha256": None, "adjudicavel": False}]
    entradas = [{"id": "e1", "sha256": "a"}, {"id": "e2", "sha256": "a"}]
    assert GE.mapa_por_hash(materiais, entradas) == {IDS[0]: ["e1", "e2"], IDS[1]: []}
    with pytest.raises(GE.GoldInvalido):
        GE.mapa_por_hash(materiais, [{"id": "e1", "sha256": "a", "computed_unit_slug": "u-um"}])


# ------------------------------------------------------------------------------------------- determinismo do CRU
def test_recaptura_do_cru_exige_decisoes_identicas():
    cong = T.congelamento(T.INV8)
    a = T.captura(cong, K.CRU, T.decisoes_de(T.SUB_CRU))
    assert CP.confere_determinismo_cru(a, copy.deepcopy(a)) == []
    b = copy.deepcopy(a)
    b["decisoes"]["S"]["e3"]["final"]["sub"] = "t4"
    assert CP.confere_determinismo_cru(a, b) == ["S/e3: decisão diferente"]
    c = copy.deepcopy(a)
    del c["decisoes"]["S"]["e8"]
    assert "S: IDs diferentes" in CP.confere_determinismo_cru(a, c)



# ------------------------------------------------------------------------------------------- geração (limpo)
FILHO_GRAVADOR = """
import hashlib, sys
sys.path.insert(0, sys.argv[1])
import limpo as L
chamou = []
inv = {"C1": [{"bundle_sha256": hashlib.sha256(b"bundle certo").hexdigest(), "unidade": "u"}], "_schema_sha256": "s"}
g = L.Gravador(lambda **kw: chamou.append(kw), inv, "modelo-congelado")
for contents, modelo in (("bundle errado", "modelo-congelado"), ("bundle certo", "outro-modelo")):
    g.iniciar("C1")
    try:
        g(model=modelo, contents=contents, config=None)
        print("SEM-ABORTO")
    except L.Aborto:
        print("ABORTO")
print("CHAMADAS", len(chamou))
"""


def test_gravador_recusa_request_fora_do_inventario_e_modelo_divergente_antes_da_rede(tmp_path):
    """Com configuração sintética (recompilação em pasta temporária): o gravador aborta ANTES de chamar o SDK."""
    fonte = {"tipo": "captura_cru", "congelamento": "x", "entradas": "x", "manifesto_capturas": "x", "capturas_dir": "x", "id_comum": "0" * 64,
             "braco_cru": "CRU_X", "comum_da_fonte": HERE.relative_to(HERE.parents[5]).as_posix()}
    cfg, _ = config_sintetica(tmp_path, recompilacao=str(tmp_path / "rec"), staging_fonte=fonte)
    filho = tmp_path / "filho.py"
    filho.write_text(FILHO_GRAVADOR, encoding="utf-8")
    env = {**{k: v for k, v in os.environ.items() if k != "RODADA_CONFIG"}, "RODADA_CONFIG": str(cfg)}
    r = subprocess.run([sys.executable, "-B", str(filho), str(HERE)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-1500:]
    assert r.stdout.split() == ["ABORTO", "ABORTO", "CHAMADAS", "0"]
    assert not (tmp_path / "rec").exists()   # nada gravado


def _pacote_sintetico(raiz):
    for rel, dados in {"manifest.json": json.dumps({"entries": [
                           {"id": "e1", "computed_unit_slug": "u-um", "approved_markdown": "content/e1.md"},
                           {"id": "e2", "computed_unit_slug": "u-dois", "approved_markdown": "content/e2.md"}]}),
                       "content/e1.md": "# Aula 1\n", "content/e2.md": "# Aula 2\n",
                       "course/.content_taxonomy.json": json.dumps({"version": 1, "units": []})}.items():
        (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
        (raiz / rel).write_text(dados, encoding="utf-8")


def _roda_staging(tmp_path, arvores):
    cursos = [{"sigla": s, "tutor": f"Curso-{s}-Tutor", "raiz_pacote": str(tmp_path / "pacotes" / s),
               "eixos": ["unidade", "sub_primaria"], "denominadores": {"bloco": 0, "unidade": 2, "sub_primaria": 2}}
              for s in ("C1", "C2")]
    cfg, _ = config_sintetica(tmp_path, cursos=cursos, recompilacao=str(tmp_path / "rec"),
                              staging_fonte={"tipo": "manifesto_do_build", "arvores": arvores})
    env = {**{k: v for k, v in os.environ.items() if k != "RODADA_CONFIG"}, "RODADA_CONFIG": str(cfg), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, "-B", str(HERE / "limpo.py"), "--staging"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def test_staging_de_cursos_novos_usa_o_manifesto_do_build_congelado(tmp_path):
    for s in ("C1", "C2"):
        _pacote_sintetico(tmp_path / "pacotes" / s)
    arvores = {s: K.sha_json(K.arvore(tmp_path / "pacotes" / s)) for s in ("C1", "C2")}
    r = _roda_staging(tmp_path, arvores)
    assert r.returncode == 0, (r.stdout[-800:], r.stderr[-800:])
    reg = json.loads((tmp_path / "rec/staging_manifesto.json").read_text(encoding="utf-8"))
    assert reg["fonte"] == {"tipo": "manifesto_do_build", "arvores": arvores}
    assert {s: (v["entries"], v["unidade_substituida_pelo_cru"], v["markdown_copiados"]) for s, v in reg["cursos"].items()} == \
        {"C1": (2, 0, 2), "C2": (2, 0, 2)}
    novas = json.loads((tmp_path / "rec/staging/Curso-C1-Tutor/manifest_staging.json").read_text(encoding="utf-8"))["entries"]
    assert [e["computed_unit_slug"] for e in novas] == ["u-um", "u-dois"]


def test_staging_recusa_pacote_alterado_depois_do_congelamento(tmp_path):
    for s in ("C1", "C2"):
        _pacote_sintetico(tmp_path / "pacotes" / s)
    arvores = {s: K.sha_json(K.arvore(tmp_path / "pacotes" / s)) for s in ("C1", "C2")}
    (tmp_path / "pacotes/C2/content/e2.md").write_text("# Aula 2 alterada\n", encoding="utf-8")
    r = _roda_staging(tmp_path, arvores)
    assert r.returncode != 0 and "árvore congelada" in (r.stdout + r.stderr)
    assert not (tmp_path / "rec/staging").exists()


def test_modelo_da_rodada_externa_fixa_as_escolhas_do_pre_registro():
    cfg = RD.valida(json.loads((HERE / "rodada_modelo_validacao_externa.json").read_text(encoding="utf-8")))
    assert cfg["bracos"] == {"cru": "CRU_NOVO", "candidato": "VOCAB_NOVO", "controle_maior": "CTRL_MAIOR_NOVO",
                             "controles_aleatorios": [{"nome": f"CTRL_ALEAT_NOVO_{i}", "semente": i} for i in (1, 2, 3)]}
    assert cfg["regua"]["tipo"] == "gold_externo" and cfg["regua"]["invariancia_bloco"] is True
    assert cfg["referencia_cru"] is None and cfg["staging_fonte"]["tipo"] == "manifesto_do_build"
    assert all("bloco" not in c["eixos"] for c in cfg["cursos"])
    assert cfg["protocolo"] == "docs/reports/2026-09-29-regime-vocab-validacao-externa-preregistro.md"
