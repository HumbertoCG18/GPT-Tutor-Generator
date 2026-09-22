"""#48: aceite da V4 com o src/ REAL (sem patch), cadeia bloco -> unidade -> subunidade.

Roda a fase real de bloco (replay_bloco_21-09.replay: apply_anchor_engine, voter=None)
e alimenta a fase real de unidade/subunidade (replay_unidade_21-09.replay) com as
entries ja decididas. "antes" = o que esta gravado nos builds de 15/17-09; "depois" =
o src/ atual. Gold so na avaliacao. Sem build, rede ou LLM.
Aceite: bloco 214/237 sem perda; unidade 246/284 sem perda; subunidade primaria 84 e
aceita 107 (0 perda); nenhum curso regride; exatamente as entradas medidas em
regra_v4_vizinho_nao_vence_texto_21-09 mudam.
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

# Medido pelo W-O (V4 em memoria), 21/09: o src/ real tem de tocar exatamente isto.
ESPERADO_BLOCO = {("MF", "t1-2026-1"), ("MF", "t2-2026-1"), ("ES2", "t1-2026-1")}
ESPERADO_UNIDADE = {("CG", "opengl-cpp"), ("CG", "opengl-py"), ("CG", "openglbasico"), ("CG", "texturas-v3"),
                    ("IA", "future-of-jobs-report-2025")}
# t1/t2 do MF nao mudam de slug em relacao ao gravado (o texto ja decidia sem bloco); com bloco
# novo, a regra "texto-vence-vizinho" e o que os mantem certos (W-O: V3 os perdia).
ESPERADO_TEXTO_VENCE_VIZINHO_MF = {"t1-2026-1": "unidade-01-metodos-formais", "t2-2026-1": "unidade-02-verificacao-de-programas"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    # Os manifests gravados sao ANTERIORES a #47 (commit 9220a57): a base desta mudanca e o
    # estado da #47, lido do seu aceite (244/107, 8 unidades alteradas, 1 perda conhecida de
    # subunidade aceita). Tudo o que a #47 ja mudava e descontado aqui.
    ac47 = read(HERE / "aceite_regra_secao_47_21-09.json")
    ef47 = read(HERE / "regra_secao_efeito_subunidade_21-09.json")
    unid_47 = {(m["curso"], m["id"]) for m in ac47["mudancas_de_unidade"]}
    perda_aceita_47 = {(x["curso"], x["manifest_id"]) for x in ef47["subunit_deltas"]["accepted"]["losses"]}
    assert len(unid_47) == 8 and len(perda_aceita_47) == 1, "aceite da #47 diferente do registrado"
    rb = load("aceite48_rb", HERE / "replay_bloco_21-09.py")
    ru = load("aceite48_ru", HERE / "replay_unidade_21-09.py")
    compare = load("aceite48_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    tot = {"antes": collections.Counter(), "depois": collections.Counter()}
    cursos, mud_bloco, mud_unid, perdas = {}, [], [], {"bloco": [], "unidade": [], "sub_primaria": [], "sub_aceita": []}
    orig_read = ru.read
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved, bloco_novo, _, _ = rb.replay(root)                      # fase real de bloco, src/ atual
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
        if sig == "MF":
            mf_vizinho = {eid: (novo[eid].get("computed_unit_slug"),
                                any(str(r).startswith("texto-vence-vizinho=") for r in (novo[eid].get("unit_match_reasons") or [])))
                          for eid in ESPERADO_TEXTO_VENCE_VIZINHO_MF}
        for eid, old in saved.items():
            if str(old.get("temporal_block_id") or "") != str(novo[eid].get("temporal_block_id") or ""):
                mud_bloco.append({"curso": sig, "id": eid, "antes": old.get("temporal_block_id"), "depois": novo[eid].get("temporal_block_id"),
                                  "metodo": novo[eid].get("temporal_block_method")})
            if str(old.get("computed_unit_slug") or "") != str(novo[eid].get("computed_unit_slug") or ""):
                mud_unid.append({"curso": sig, "id": eid, "antes": old.get("computed_unit_slug"), "depois": novo[eid].get("computed_unit_slug"),
                                 "razoes": novo[eid].get("unit_match_reasons")})
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
    # regressao por curso medida contra o estado da #47 (aceite_regra_secao_47: cursos[sig]["depois"])
    regride = [sig for sig, v in cursos.items()
               if any(v["depois"].get(k, 0) < ac47["cursos"].get(sig, {}).get("depois", {}).get(k, 0)
                      for k in ("bloco", "unidade", "sub_primaria", "sub_aceita"))]
    perdas_novas = {eixo: [p for p in lst if (p["curso"], p["id"]) not in perda_aceita_47 or eixo != "sub_aceita"]
                    for eixo, lst in perdas.items()}
    checks = {
        "manifests_gravados_sao_pre_47_213_239_84_108": (a["bloco"], a["unidade"], a["sub_primaria"], a["sub_aceita"]) == (213, 239, 84, 108),
        "bloco_214_de_237": (d["bloco"], d["bloco_n"]) == (214, 237),
        "unidade_246_de_284": (d["unidade"], d["unidade_n"]) == (246, 284),
        "sub_primaria_84_e_aceita_107_de_251": (d["sub_primaria"], d["sub_aceita"], d["sub_n"]) == (84, 107, 251),
        "zero_perda_nova_em_todos_os_eixos": not any(perdas_novas.values()),
        "unica_perda_e_a_conhecida_da_47": {(p["curso"], p["id"]) for p in perdas["sub_aceita"]} == perda_aceita_47,
        "nenhum_curso_regride_vs_47": not regride,
        "mudancas_de_bloco_sao_as_medidas": {(m["curso"], m["id"]) for m in mud_bloco} == ESPERADO_BLOCO,
        "mudancas_de_unidade_sao_47_mais_v4": {(m["curso"], m["id"]) for m in mud_unid} == ESPERADO_UNIDADE | unid_47,
        "t1_t2_do_MF_mantidos_pelo_texto_vence_vizinho": all(
            mf_vizinho[eid] == (slug, True) for eid, slug in ESPERADO_TEXTO_VENCE_VIZINHO_MF.items()),
    }
    report = {"issue": 48, "checks": checks, "totais": {k: dict(v) for k, v in tot.items()}, "cursos": cursos,
              "mudancas_de_bloco": mud_bloco, "mudancas_de_unidade": mud_unid, "perdas_vs_manifest_gravado": perdas,
              "perdas_novas_vs_47": perdas_novas, "cursos_que_regridem_vs_47": regride,
              "base_47": {"unidades_alteradas": sorted(unid_47), "perda_sub_aceita": sorted(perda_aceita_47)},
              "mf_texto_vence_vizinho": mf_vizinho}
    out = HERE / "aceite_v4_48_22-09.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("TOTAIS", json.dumps(report["totais"], ensure_ascii=False))
    print("MUDANCAS bloco", sorted((m["curso"], m["id"]) for m in mud_bloco))
    print("MUDANCAS unidade", sorted((m["curso"], m["id"]) for m in mud_unid))
    print("CHECKS", checks)
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())
    assert all(checks.values()), "aceite NAO cumprido"


if __name__ == "__main__":
    main()
