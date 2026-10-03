"""Configuração de rodada do harness genérico (versão `rodada-generica-1`). Só stdlib.

Cursos, caminhos, braços, sementes, denominadores, régua e referências vêm de um JSON de rodada. Nenhum código do
harness genérico contém regra por nome de curso. O arquivo é escolhido pela variável de ambiente `RODADA_CONFIG`
(caminho absoluto ou relativo a esta pasta); sem ela, o import falha: não existe rodada implícita.
"""
import json
import os
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ESQUEMA = "rodada-generica-1"
SIGLA = re.compile(r"^[A-Z][A-Z0-9]{0,9}$")
BRACO = re.compile(r"^[A-Z][A-Z0-9_]{1,39}$")
EIXOS = ("bloco", "unidade", "sub_primaria")


class ConfigInvalida(ValueError):
    pass


def _exige(cond, msg):
    if not cond:
        raise ConfigInvalida(msg)


def valida(cfg):
    """Validação estrutural completa; devolve o próprio cfg. Qualquer desvio é erro (sem valor padrão silencioso)."""
    _exige(cfg.get("esquema") == ESQUEMA, f"esquema != {ESQUEMA}")
    cursos = cfg.get("cursos")
    _exige(isinstance(cursos, list) and cursos, "cursos: lista não vazia")
    siglas = [c.get("sigla") for c in cursos]
    _exige(all(isinstance(s, str) and SIGLA.match(s) for s in siglas) and len(set(siglas)) == len(siglas), "siglas inválidas ou repetidas")
    for c in cursos:
        _exige(set(c) == {"sigla", "tutor", "raiz_pacote", "eixos", "denominadores"}, f"{c.get('sigla')}: campos do curso")
        _exige(set(c["eixos"]) <= set(EIXOS) and "sub_primaria" in c["eixos"], f"{c['sigla']}: eixos")
        _exige(set(c["denominadores"]) == set(EIXOS) and all(isinstance(v, int) and v >= 0 for v in c["denominadores"].values()),
               f"{c['sigla']}: denominadores")
        _exige(all(c["denominadores"][e] == 0 for e in EIXOS if e not in c["eixos"]), f"{c['sigla']}: denominador de eixo não avaliado")
    b = cfg.get("bracos") or {}
    _exige(set(b) == {"cru", "candidato", "controle_maior", "controles_aleatorios"}, "bracos: papéis")
    nomes = [b["cru"], b["candidato"], b["controle_maior"], *[x["nome"] for x in b["controles_aleatorios"]]]
    _exige(all(BRACO.match(n) for n in nomes) and len(set(nomes)) == len(nomes), "bracos: nomes inválidos ou repetidos")
    sementes = [x["semente"] for x in b["controles_aleatorios"]]
    _exige(b["controles_aleatorios"] and all(isinstance(s, int) for s in sementes) and len(set(sementes)) == len(sementes),
           "bracos: sementes inteiras e distintas")
    _exige(isinstance(cfg.get("inventario_esperado"), int) and cfg["inventario_esperado"] > 0, "inventario_esperado")
    ref = cfg.get("referencia_cru")
    _exige(ref is None or (set(ref) == {"arquivo", "placar"} and set(ref["placar"]) == set(siglas)), "referencia_cru")
    r = cfg.get("regua") or {}
    _exige(r.get("tipo") in ("historica", "gold_externo"), "regua.tipo")
    _exige(set(r) == {"tipo", "arquivos", "manifestos", "codigo", "invariancia_bloco"}, "regua: campos")
    _exige(isinstance(r["invariancia_bloco"], bool), "regua.invariancia_bloco")
    for papel, m in r["arquivos"].items():
        _exige(set(m) <= set(siglas), f"regua.arquivos.{papel}: curso fora da rodada")
    if r["tipo"] == "gold_externo":
        _exige(set(r["arquivos"]) == {"gold", "rotulos", "mapa"} and all(set(r["arquivos"][p]) == set(siglas) for p in r["arquivos"]),
               "gold_externo: papéis gold, rotulos e mapa para todos os cursos")
        _exige(not any("bloco" in c["eixos"] for c in cursos), "gold_externo: bloco não é rotulado (pré-registro §6.3)")
        _exige(r["invariancia_bloco"] is True, "gold_externo: invariância de bloco obrigatória")
    for k in ("protocolo", "base_produto", "saida_base", "recompilacao", "sufixo"):
        _exige(isinstance(cfg.get(k), str) and cfg[k], k)
    _exige(isinstance(cfg.get("tutores_proibidos"), list) and isinstance(cfg.get("proibidos"), dict), "proibições")
    _exige(isinstance(cfg.get("esquemas"), dict) and set(cfg["esquemas"]) == {"captura", "congelamento"}, "esquemas")
    f = cfg.get("staging_fonte")
    _exige(isinstance(f, dict) and f.get("tipo") in ("captura_cru", "manifesto_do_build"), "staging_fonte.tipo")
    if f["tipo"] == "captura_cru":
        base = {"tipo", "congelamento", "entradas", "manifesto_capturas", "capturas_dir", "id_comum", "braco_cru", "comum_da_fonte"}
        _exige(base <= set(f) <= base | {"historico_sidecars"}, "staging_fonte (captura_cru): campos")
    else:
        _exige(set(f) == {"tipo", "arvores"} and set(f["arvores"]) == set(siglas), "staging_fonte (manifesto_do_build): arvores por curso")
    return cfg


def carrega(caminho=None):
    caminho = caminho or os.environ.get("RODADA_CONFIG")
    _exige(bool(caminho), "RODADA_CONFIG não definida: não existe rodada implícita")
    p = Path(caminho)
    p = p if p.is_absolute() else AQUI / p
    cfg = json.loads(p.read_text(encoding="utf-8"))
    return valida(cfg), p


CFG, CAMINHO = carrega()
NOMES = {c["sigla"]: c["tutor"] for c in CFG["cursos"]}
CRU = CFG["bracos"]["cru"]
CANDIDATO = CFG["bracos"]["candidato"]
CTRL_MAIOR = CFG["bracos"]["controle_maior"]
CTRL_ALEAT = tuple(x["nome"] for x in CFG["bracos"]["controles_aleatorios"])
SEMENTES = {x["nome"]: x["semente"] for x in CFG["bracos"]["controles_aleatorios"]}
BRACOS = (CRU, CANDIDATO, CTRL_MAIOR, *CTRL_ALEAT)
DENOM_POR_CURSO = {c["sigla"]: dict(c["denominadores"]) for c in CFG["cursos"]}
DENOMINADORES = {e: sum(d[e] for d in DENOM_POR_CURSO.values()) for e in EIXOS}
UNI = frozenset(c["sigla"] for c in CFG["cursos"] if "unidade" in c["eixos"])
REFERENCIA_CRU = (CFG["referencia_cru"] or {}).get("placar") or {}
