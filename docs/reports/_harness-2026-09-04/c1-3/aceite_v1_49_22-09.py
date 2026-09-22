"""#49: aceite da V1 (`_score` sem o divisor sqrt(len(sig))) com o src/ REAL, cadeia
bloco -> unidade -> subunidade.

Roda a fase real de bloco (replay_bloco_21-09.replay: apply_anchor_engine, voter=None) com o
src/ atual e alimenta a fase real de unidade/subunidade (replay_unidade_21-09.replay) com as
entries decididas. Base da mudanca = estado da #48 (aceite_v4_48_22-09.json: 214/246/84/107,
3 blocos e 13 unidades alteradas vs manifests gravados, que sao pre-#47). CONTROLE = a formula
antiga (raw / sqrt(len(sig))) aplicada por patch em memoria em disambiguator._score, restaurado
no finally, so para contar bandas/flags que mudam sem trocar o bloco. Gold so na avaliacao.
Sem build, rede ou LLM.
Aceite: bloco 217/237 sem perda; unidade 246/284 sem perda; subunidade primaria 84 e aceita 107
(0 perda nova); nenhum curso regride vs #48; mudam exatamente os 3 blocos medidos no W-R
(wr_normalizacao_score_bloco_22-09.json, V1) e nenhuma unidade alem das da #47/#48; 16 mudancas
de banda/flag sem troca de bloco (4 ficam confiantes, 3 flagadas, 9 so banda), zero id vazio.
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))

from src.builder.routing.motor import disambiguator as D  # noqa: E402

# Medido pelo W-R (V1 em memoria), 22/09: o src/ real tem de tocar exatamente isto.
ESPERADO_BLOCO_49 = {("MF", "exerciciosnusmv"), ("MF", "provas"), ("IA", "algoritmo-de-classificacao-k-nn")}
ESPERADO_BANDA = {"ficou_confiante": 4, "ficou_flagada": 3, "so_banda": 9}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def score_antigo(mat, sig, m, df):
    """Formula de antes da #49 (controle)."""
    if not sig:
        return 0.0
    raw = sum(sig[t] * math.log(1.0 + m / df[t]) for t in sorted(mat & set(sig)))
    return raw / math.sqrt(len(sig))


def main():
    assert D._score.__doc__ and "SEM normalizar" in D._score.__doc__, "src/ real nao esta com a V1"
    ac48 = read(HERE / "aceite_v4_48_22-09.json")
    wr = read(HERE / "wr_normalizacao_score_bloco_22-09.json")
    assert {(m["curso"], m["id"]) for m in wr["ids_que_mudam"]["V1"]} == ESPERADO_BLOCO_49, "W-R diferente do registrado"
    bloco_48 = {(m["curso"], m["id"]) for m in ac48["mudancas_de_bloco"]}
    unid_48 = {(m["curso"], m["id"]) for m in ac48["mudancas_de_unidade"]}
    perda_aceita_47 = {tuple(x) for x in ac48["base_47"]["perda_sub_aceita"]}
    assert len(bloco_48) == 3 and len(unid_48) == 13 and len(perda_aceita_47) == 1, "aceite da #48 diferente do registrado"
    rb = load("aceite49_rb", HERE / "replay_bloco_21-09.py")
    ru = load("aceite49_ru", HERE / "replay_unidade_21-09.py")
    compare = load("aceite49_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    tot = {"antes": collections.Counter(), "depois": collections.Counter()}
    cursos, mud_bloco, mud_unid, bandas = {}, [], [], []
    perdas = {"bloco": [], "unidade": [], "sub_primaria": [], "sub_aceita": []}
    orig_read = ru.read
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved, bloco_novo, _, _ = rb.replay(root)                      # fase real de bloco, src/ atual (V1)
        orig_score = D._score
        D._score = score_antigo
        try:
            _, bloco_ctrl, _, _ = rb.replay(root)                       # controle: formula antiga
        finally:
            D._score = orig_score
        for eid, e in bloco_novo.items():
            c = bloco_ctrl[eid]
            if str(e.get("temporal_block_id") or "") == str(c.get("temporal_block_id") or ""):
                if (e.get("temporal_block_band"), bool(e.get("temporal_block_flag"))) != (c.get("temporal_block_band"), bool(c.get("temporal_block_flag"))):
                    tipo = ("ficou_confiante" if bool(c.get("temporal_block_flag")) and not bool(e.get("temporal_block_flag"))
                            else "ficou_flagada" if not bool(c.get("temporal_block_flag")) and bool(e.get("temporal_block_flag"))
                            else "so_banda")
                    bandas.append({"curso": sig, "id": eid, "tipo": tipo, "banda": [c.get("temporal_block_band"), e.get("temporal_block_band")],
                                   "flag": [bool(c.get("temporal_block_flag")), bool(e.get("temporal_block_flag"))],
                                   "id_vazio": not str(e.get("temporal_block_id") or "")})
        feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

        def patched(path, _feed=feed):                                  # unidade/subunidade sobre o bloco novo
            data = orig_read(path)
            if Path(path).name == "manifest.json":
                data = {**data, "entries": _feed}
            return data

        ru.read = patched
        try:
            _, novo, _ = ru.replay(root)
        finally:
            ru.read = orig_read
        for eid, old in saved.items():
            if str(old.get("temporal_block_id") or "") != str(novo[eid].get("temporal_block_id") or ""):
                mud_bloco.append({"curso": sig, "id": eid, "antes": old.get("temporal_block_id"), "depois": novo[eid].get("temporal_block_id"),
                                  "metodo": novo[eid].get("temporal_block_method"), "banda": novo[eid].get("temporal_block_band")})
            if str(old.get("computed_unit_slug") or "") != str(novo[eid].get("computed_unit_slug") or ""):
                mud_unid.append({"curso": sig, "id": eid, "antes": old.get("computed_unit_slug"), "depois": novo[eid].get("computed_unit_slug")})
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / name / "manifest.json")["entries"]}
        index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gb, gu, gs, gsp = mede.golds(sig)
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = {"antes": collections.Counter(), "depois": collections.Counter()}
        for row in rows:
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            eid = str(hits[0]["id"]) if hits else None
            preds = {"antes": compare.predictions(root, saved[eid]) if eid else None,
                     "depois": compare.predictions(root, novo[eid]) if eid else None}
            ok = {}
            for label, pred in preds.items():
                if row["bloco"] != "":
                    c[label]["bloco_n"] += 1
                    ok[(label, "bloco")] = bool(pred and pred[0] == gb[gid]); c[label]["bloco"] += ok[(label, "bloco")]
                if row["unidade"] != "":
                    c[label]["unidade_n"] += 1
                    ok[(label, "unidade")] = bool(pred and pred[1] in gu[gid]); c[label]["unidade"] += ok[(label, "unidade")]
                if row["sub_primario"] != "":
                    c[label]["sub_n"] += 1
                    ok[(label, "sub_primaria")] = bool(pred and pred[2] in gsp[gid]); c[label]["sub_primaria"] += ok[(label, "sub_primaria")]
                    ok[(label, "sub_aceita")] = bool(pred and pred[2] in gs[gid]); c[label]["sub_aceita"] += ok[(label, "sub_aceita")]
            for eixo in ("bloco", "unidade", "sub_primaria", "sub_aceita"):
                if ok.get(("antes", eixo)) and not ok.get(("depois", eixo)):
                    perdas[eixo].append({"curso": sig, "id": eid, "gold_id": gid})
        cursos[sig] = {k: dict(v) for k, v in c.items()}
        for label in tot:
            tot[label].update(c[label])
        print(sig, dict(c["depois"]), flush=True)

    a, d = tot["antes"], tot["depois"]
    regride = [sig for sig, v in cursos.items()
               if any(v["depois"].get(k, 0) < ac48["cursos"].get(sig, {}).get("depois", {}).get(k, 0)
                      for k in ("bloco", "unidade", "sub_primaria", "sub_aceita"))]
    perdas_novas = {eixo: [p for p in lst if (p["curso"], p["id"]) not in perda_aceita_47 or eixo != "sub_aceita"]
                    for eixo, lst in perdas.items()}
    contagem_bandas = collections.Counter(b["tipo"] for b in bandas)
    checks = {
        "manifests_gravados_sao_pre_47_213_239_84_108": (a["bloco"], a["unidade"], a["sub_primaria"], a["sub_aceita"]) == (213, 239, 84, 108),
        "bloco_217_de_237": (d["bloco"], d["bloco_n"]) == (217, 237),
        "unidade_246_de_284": (d["unidade"], d["unidade_n"]) == (246, 284),
        "sub_primaria_84_e_aceita_107_de_251": (d["sub_primaria"], d["sub_aceita"], d["sub_n"]) == (84, 107, 251),
        "zero_perda_nova_em_todos_os_eixos": not any(perdas_novas.values()),
        "unica_perda_e_a_conhecida_da_47": {(p["curso"], p["id"]) for p in perdas["sub_aceita"]} == perda_aceita_47,
        "nenhum_curso_regride_vs_48": not regride,
        "mudancas_de_bloco_sao_48_mais_v1": {(m["curso"], m["id"]) for m in mud_bloco} == bloco_48 | ESPERADO_BLOCO_49,
        "mudancas_de_unidade_sao_so_as_de_47_e_48": {(m["curso"], m["id"]) for m in mud_unid} == unid_48,
        "bandas_flags_como_no_wr_4_3_9": dict(contagem_bandas) == ESPERADO_BANDA,
        "zero_id_vazio_apos_mudanca_de_banda": not any(b["id_vazio"] for b in bandas),
    }
    report = {"issue": 49, "checks": checks, "totais": {k: dict(v) for k, v in tot.items()}, "cursos": cursos,
              "mudancas_de_bloco": mud_bloco, "mudancas_de_unidade": mud_unid, "bandas_flags_sem_mudar_bloco": bandas,
              "perdas_vs_manifest_gravado": perdas, "perdas_novas_vs_48": perdas_novas, "cursos_que_regridem_vs_48": regride,
              "base_48": {"blocos_alterados": sorted(bloco_48), "unidades_alteradas": sorted(unid_48), "perda_sub_aceita": sorted(perda_aceita_47)}}
    out = HERE / "aceite_v1_49_22-09.json"
    assert not out.exists(), "preservar evidencia existente (apagar antes de reexecutar)"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("TOTAIS", json.dumps(report["totais"], ensure_ascii=False))
    print("MUDANCAS bloco", sorted((m["curso"], m["id"]) for m in mud_bloco))
    print("BANDAS", dict(contagem_bandas))
    print("CHECKS", checks)
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())
    assert all(checks.values()), "aceite NAO cumprido"


if __name__ == "__main__":
    main()
