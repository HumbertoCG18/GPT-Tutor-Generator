"""#47: aceite da regra 'secao corroborada vence unidade herdada do bloco' com o src/ REAL.

Roda a fase real (replay_unidade_21-09.replay) sobre os builds de 15/17-09 com o src/ do
checkout, sem patch, e mede contra a regua. Gold so na avaliacao. Sem build, rede ou LLM.
Aceite: unidade 244/284, 0 perda entre os acertos, nenhum curso regride, bloco 213/237,
subunidade primaria >= 84/251; aceita 107/251 e custo conhecido e aceito pelo usuario.
"""
import collections
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


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    replay = load("aceite_replay", HERE / "replay_unidade_21-09.py")
    compare = load("aceite_compare", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    medido = json.loads((HERE / "regra_secao_unidade_21-09.json").read_text(encoding="utf-8"))
    oito = {(d["curso"], str(d["id"])) for d in medido["decisions"] if d["changed"]["R-sem-misto"]}

    tot = {"antes": collections.Counter(), "depois": collections.Counter()}
    cursos, mudancas, perdas = {}, [], []
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved, novo, _ = replay.replay(root)
        for eid, old in saved.items():
            a, d = str(old.get("computed_unit_slug") or ""), str(novo[eid].get("computed_unit_slug") or "")
            if a != d:
                mudancas.append({"curso": sig, "id": eid, "antes": a, "depois": d, "medida_nas_8": (sig, eid) in oito,
                                 "razoes": novo[eid].get("unit_match_reasons")})
        ref = {str(e["id"]): e for e in json.loads((DATA / ".frzero/pacote_fontes_15-09" / name / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in json.loads((HERE / f"herancas_{sig}_15-09.json").read_text(encoding="utf-8"))["entries"]}
        gb, gu, gs, gsp = mede.golds(sig)
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = {"antes": collections.Counter(), "depois": collections.Counter()}
        for row in rows:
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            for label, entries in (("antes", saved), ("depois", novo)):
                e = entries[str(hits[0]["id"])] if hits else None
                pred = compare.predictions(root, e) if e else None
                if row["bloco"] != "":
                    c[label]["bloco_n"] += 1
                    c[label]["bloco"] += bool(pred and pred[0] == gb[gid])
                if row["unidade"] != "":
                    c[label]["unidade_n"] += 1
                    c[label]["unidade"] += bool(pred and pred[1] in gu[gid])
                if row["sub_primario"] != "":
                    c[label]["sub_n"] += 1
                    c[label]["sub_primaria"] += bool(pred and pred[2] in gsp[gid])
                    c[label]["sub_aceita"] += bool(pred and pred[2] in gs[gid])
            if hits and row["unidade"] != "":
                eid = str(hits[0]["id"])
                was = compare.predictions(root, saved[eid])[1] in gu[gid]
                now = compare.predictions(root, novo[eid])[1] in gu[gid]
                if was and not now:
                    perdas.append({"curso": sig, "id": eid})
        cursos[sig] = {k: dict(v) for k, v in c.items()}
        for label in tot:
            tot[label].update(c[label])
        print(sig, dict(c["depois"]), flush=True)

    a, d = tot["antes"], tot["depois"]
    checks = {
        "base_reproduzida_239_213_84_108": (a["unidade"], a["bloco"], a["sub_primaria"], a["sub_aceita"]) == (239, 213, 84, 108),
        "unidade_244_de_284": (d["unidade"], d["unidade_n"]) == (244, 284),
        "zero_perda_de_unidade": not perdas,
        "nenhum_curso_regride_na_unidade": all(v["depois"].get("unidade", 0) >= v["antes"].get("unidade", 0) for v in cursos.values()),
        "bloco_213_de_237": (d["bloco"], d["bloco_n"]) == (213, 237),
        "sub_primaria_ao_menos_84": d["sub_primaria"] >= 84,
        "mudancas_sao_as_8_medidas": {(m["curso"], m["id"]) for m in mudancas} == oito,
    }
    report = {"issue": 47, "checks": checks, "totais": {k: dict(v) for k, v in tot.items()}, "cursos": cursos,
              "mudancas_de_unidade": mudancas, "perdas_de_unidade": perdas,
              "custo_aceito": "subunidade aceita 108 -> 107 (acoplamento da 2a passada), aceito pelo usuario em 21/09"}
    out = HERE / "aceite_regra_secao_47_21-09.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("TOTAIS", json.dumps(report["totais"], ensure_ascii=False))
    print("MUDANCAS", len(mudancas), "fora das 8 medidas:", [(m["curso"], m["id"]) for m in mudancas if not m["medida_nas_8"]],
          "| das 8 que NAO mudaram:", sorted(oito - {(m["curso"], m["id"]) for m in mudancas}))
    print("CHECKS", checks)
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())
    assert all(checks.values()), "aceite NAO cumprido"


if __name__ == "__main__":
    main()
