"""W-T (CRU-03): duas regras candidatas de unidade, pre-declaradas, medidas pela cadeia REAL.

FAMILIA ATACADA (anatomia do estado #49, `wt_anatomia_unidade_49_22-09.json`): dos 38 erros de unidade,
6 tem o MESMO mecanismo -- razao `reconciliada_do_bloco=<id>`, scorer de texto NAO ambiguo e acima do gate
(`gated_unit != ""`), vencedor bruto == gold, e mesmo assim o bloco venceu porque
`reconcile_unit_with_block` compara `block_confidence=1.0 >= unit_confidence` (file_map.py:802-803).
Sao SO/3103-threads, SO/biblioteca-em-c-pthread, IA/visao-geral-introducao-e-historico,
ES2/microsservicos7, TCC/aula-11-...-halting-problem, CG/exercicios-sobre-curvas-html.
E a mesma clausula que a #48 ja abriu para o vizinho (`texto-vence-vizinho`), aqui estendida ao bloco
com unidade PROPRIA.

REGRAS (escritas ANTES de medir; nenhum parametro ajustado ao gold):
  R2  SEM PARAMETRO. No ramo final de `reconcile_unit_with_block` (bloco decide), se a unidade gated
      nao e vazia (logo o scorer nao foi ambiguo e passou T.UNIT_TAG), o TEXTO vence o bloco:
      reason `texto-vence-bloco=<id>`, conflito registrado. Controle honesto de R1.
  R1  R2 + limiar tau sobre `unit_confidence`: o texto so vence se `unit_confidence >= tau`.
      tau escolhido por LOCO (leave-one-course-out) no grid GRID; reportado por fold.

RISCO PRE-DECLARADO: quantos ACERTOS atuais de unidade passam pela mesma clausula (razao
`reconciliada_do_bloco=`), por curso -- medido e gravado junto.

Patch SO em memoria (`FM.reconcile_unit_with_block`, restaurado no finally). Cadeia real:
`replay_bloco_21-09.replay` -> `replay_unidade_21-09.replay` (que roda unidade E subunidade na fase real,
`apply_unit_subunit_fields`), como no molde `aceite_v1_49_22-09.py`. Gold so na avaliacao, depois do
congelamento por hash. Sem build, rede, LLM, commit.

ACEITE: unidade >= 247/284, 0 perda entre os acertos de unidade, nenhum curso regride, bloco 217/237,
subunidade primaria 84 e aceita 107 preservadas.
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))

from src.builder.routing import file_map as FM  # noqa: E402

GRID = (0.50, 0.60, 0.70, 0.80, 0.90)
BASE = {"bloco": (217, 237), "unidade": (246, 284), "sub_primaria": 84, "sub_aceita": 107, "sub_n": 251}
BASE_CURSOS = {"MF": 61, "SO": 30, "IA": 39, "ES2": 25, "TCC": 17, "CG": 74}   # unidade, estado #49


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fazer_regra(orig, tau):
    """tau=None -> R2 (sem parametro). tau=float -> R1."""
    def regra(**kw):
        slug, reasons, conflict = orig(**kw)
        gated = str(kw.get("computed_unit_slug") or "")
        bloco = str(kw.get("block_unit_slug") or "")
        if not gated or slug != bloco or gated == bloco:
            return slug, reasons, conflict
        if not any(str(r).startswith("reconciliada_do_bloco=") for r in reasons):
            return slug, reasons, conflict
        if tau is not None and float(kw.get("unit_confidence") or 0.0) < tau:
            return slug, reasons, conflict
        bid = str(kw.get("computed_block_id") or "")
        return gated, [f"texto-vence-bloco={bid}"], {"unit": gated, "block_unit": bloco, "block_id": bid}
    return regra


def rodar(estado, ru, compare, regra):
    """Cadeia unidade->subunidade sobre o bloco ja decidido, com a regra em memoria."""
    orig_reconcile = FM.reconcile_unit_with_block
    orig_read = ru.read
    saidas = {}
    if regra is not None:
        FM.reconcile_unit_with_block = regra
    try:
        for sig, v in estado.items():
            feed = [copy.deepcopy(e) for e in v["feed"]]

            def patched(path, _feed=feed):
                data = orig_read(path)
                if Path(path).name == "manifest.json":
                    data = {**data, "entries": _feed}
                return data

            ru.read = patched
            try:
                _, novo, raw = ru.replay(v["root"])
            finally:
                ru.read = orig_read
            saidas[sig] = {eid: {"bloco": compare.predictions(v["root"], e)[0],
                                 "unidade": str(e.get("computed_unit_slug") or ""),
                                 "sub": str(e.get("computed_subunit_slug") or ""),
                                 "reasons": [str(r) for r in e.get("unit_match_reasons") or []]}
                           for eid, e in novo.items()}
    finally:
        FM.reconcile_unit_with_block = orig_reconcile
    return saidas


def avaliar(estado, saidas, compare, mede):
    """Devolve (contagens por curso, acertos/erros por (curso, gold_id) em cada eixo)."""
    por_curso, flags = {}, {}
    for sig, v in estado.items():
        c = collections.Counter()
        for row in v["rows"]:
            gid, eid = row["entry_id"], v["eid_de"].get(row["entry_id"])
            dec = saidas[sig].get(eid) if eid else None
            gb, gu, gs, gsp = v["golds"]
            if row["bloco"] != "":
                c["bloco_n"] += 1
                c["bloco"] += bool(dec and dec["bloco"] == gb[gid])
            if row["unidade"] != "":
                c["unidade_n"] += 1
                ok = bool(dec and dec["unidade"] in gu[gid])
                c["unidade"] += ok
                flags[(sig, gid, "unidade")] = ok
            if row["sub_primario"] != "":
                c["sub_n"] += 1
                okp = bool(dec and dec["sub"] in gsp[gid])
                oka = bool(dec and dec["sub"] in gs[gid])
                c["sub_primaria"] += okp
                c["sub_aceita"] += oka
                flags[(sig, gid, "sub_primaria")] = okp
                flags[(sig, gid, "sub_aceita")] = oka
        por_curso[sig] = dict(c)
    return por_curso, flags


def main():
    compare = load("wtr_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    rb = load("wtr_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wtr_ru", HERE / "replay_unidade_21-09.py")
    out = HERE / "wt_regra_unidade_22-09.json"
    assert not out.exists(), "preservar evidencia existente"

    declaracao = {"familia": __doc__.split("REGRAS")[0].strip(), "regras": __doc__.split("REGRAS")[1].split("RISCO")[0].strip(),
                  "grid_tau": list(GRID), "aceite": __doc__.split("ACEITE:")[1].strip(), "base_49": BASE}
    sha_decl = hashlib.sha256(json.dumps(declaracao, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    print("DECLARACAO", sha_decl, flush=True)

    # fase de bloco, uma vez por curso (nao muda com a regra de unidade)
    estado = {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved, bloco_novo, _, _ = rb.replay(root)
        estado[sig] = {"root": root, "saved": saved, "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
        print("bloco", sig, flush=True)

    # base (#49, sem regra) e as variantes -- decisoes congeladas ANTES do gold
    variantes = {"base": None, "R2": fazer_regra(FM.reconcile_unit_with_block, None)}
    for tau in GRID:
        variantes[f"R1_tau{tau:.2f}"] = fazer_regra(FM.reconcile_unit_with_block, tau)
    saidas = {}
    for nome, regra in variantes.items():
        saidas[nome] = rodar(estado, ru, compare, regra)
        print("rodado", nome, flush=True)
    blob = json.dumps(saidas, ensure_ascii=False, sort_keys=True).encode("utf-8")
    sha_cong = hashlib.sha256(blob).hexdigest()
    print("CONGELAMENTO", sha_cong, flush=True)

    # --------------------------------------------------------------- gold entra aqui
    for sig, v in estado.items():
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig] / "manifest.json")["entries"]}
        index = compare.indexed(list(v["saved"].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            v["rows"] = list(csv.DictReader(stream))
        v["eid_de"] = {}
        for row in v["rows"]:
            old = ref.get(mapping.get(row["entry_id"]) or "")
            hits = index.get(compare.source(old), []) if old else []
            v["eid_de"][row["entry_id"]] = str(hits[0]["id"]) if hits else None
        v["golds"] = mede.golds(sig)

    res = {}
    for nome in saidas:
        pc, fl = avaliar(estado, saidas[nome], compare, mede)
        tot = collections.Counter()
        for c in pc.values():
            tot.update(c)
        res[nome] = {"por_curso": pc, "total": dict(tot), "flags": fl}
        print(nome, {k: tot[k] for k in ("bloco", "bloco_n", "unidade", "unidade_n", "sub_primaria", "sub_aceita", "sub_n")}, flush=True)

    # risco: acertos atuais que passam pela clausula
    risco = collections.Counter()
    for sig, v in estado.items():
        for row in v["rows"]:
            if row["unidade"] == "":
                continue
            eid = v["eid_de"][row["entry_id"]]
            dec = saidas["base"][sig].get(eid) if eid else None
            if dec and any(r.startswith("reconciliada_do_bloco=") for r in dec["reasons"]):
                risco[sig] += 1
                risco["total"] += 1
                if res["base"]["flags"].get((sig, row["entry_id"], "unidade")):
                    risco[f"{sig}_acerto"] += 1
                    risco["total_acerto"] += 1

    # LOCO para tau (so escolha do limiar; nenhum curso e holdout novo)
    taus = [f"R1_tau{t:.2f}" for t in GRID]
    loco = {}
    for fold in mede.NOMES:
        melhor, score = None, -1
        for nome in taus:
            s = sum(res[nome]["por_curso"][s2].get("unidade", 0) for s2 in mede.NOMES if s2 != fold)
            if s > score:
                melhor, score = nome, s
        loco[fold] = {"tau_escolhido": melhor, "unidade_nos_6_de_treino": score,
                      "unidade_no_fold": res[melhor]["por_curso"][fold].get("unidade", 0),
                      "n_no_fold": res[melhor]["por_curso"][fold].get("unidade_n", 0)}
    tau_final = collections.Counter(v["tau_escolhido"] for v in loco.values()).most_common(1)[0][0]

    relatorio = {"declaracao_pre_medicao": declaracao, "sha256_declaracao": sha_decl,
                 "sha256_congelamento_decisoes": sha_cong, "risco_clausula": dict(risco),
                 "loco_por_fold": loco, "tau_final_por_loco": tau_final, "resultados": {}, "aceite": {}}
    base_fl = res["base"]["flags"]
    for nome in ("R2", tau_final):
        tot = res[nome]["total"]
        perdas = {eixo: sorted((k[0], k[1]) for k, ok in base_fl.items() if k[2] == eixo and ok and not res[nome]["flags"].get(k))
                  for eixo in ("unidade", "sub_primaria", "sub_aceita")}
        ganhos = {eixo: sorted((k[0], k[1]) for k, ok in base_fl.items() if k[2] == eixo and not ok and res[nome]["flags"].get(k))
                  for eixo in ("unidade", "sub_primaria", "sub_aceita")}
        tocados = sorted({(sig, eid) for sig in mede.NOMES for eid, d in saidas[nome][sig].items()
                          if d["unidade"] != saidas["base"][sig][eid]["unidade"]})
        sub_tocados = sorted({(sig, eid) for sig in mede.NOMES for eid, d in saidas[nome][sig].items()
                              if d["sub"] != saidas["base"][sig][eid]["sub"]})
        regride = [s for s in BASE_CURSOS if res[nome]["por_curso"][s].get("unidade", 0) < BASE_CURSOS[s]]
        aceite = {
            "unidade_maior_igual_247": tot["unidade"] >= 247,
            "zero_perda_unidade": not perdas["unidade"],
            "nenhum_curso_regride": not regride,
            "bloco_217_237": (tot["bloco"], tot["bloco_n"]) == BASE["bloco"],
            "sub_primaria_84": tot["sub_primaria"] == BASE["sub_primaria"],
            "sub_aceita_107": tot["sub_aceita"] == BASE["sub_aceita"],
        }
        relatorio["resultados"][nome] = {
            "total": tot, "por_curso": res[nome]["por_curso"], "ganhos": ganhos, "perdas": perdas,
            "ids_unidade_tocados": tocados, "ids_subunidade_tocados": sub_tocados,
            "cursos_que_regridem": regride,
        }
        relatorio["aceite"][nome] = aceite
        print("ACEITE", nome, aceite, flush=True)
    relatorio["resultados_todos_os_taus"] = {n: res[n]["total"] for n in res}
    relatorio["por_curso_todos_os_taus"] = {n: res[n]["por_curso"] for n in res}
    out.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print("RISCO", dict(risco))
    print("LOCO", json.dumps(loco, ensure_ascii=False))
    print("SHA256_JSON", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
