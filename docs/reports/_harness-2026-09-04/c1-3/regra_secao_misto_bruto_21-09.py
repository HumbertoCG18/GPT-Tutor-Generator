"""W-E: bloco misto por vencedor bruto e confiabilidade do sinal de seção.

(a), (b), (d), régua e avaliação são idênticos a regra_secao_unidade_21-09.py.
(c') Bloco temporal não vazio com 2+ scorer.slug brutos distintos, considerando
somente scorer não ambíguo e slug não vazio. R' = a+b+c';
R'-sem-corroboração = a+c'. R-sem-misto = a+b é só referência.
Decisões são congeladas por hash antes de carregar gold/adjudicação.
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
ROOT = HERE.parents[3]
DATA = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
EVIDENCE = DATA / "docs/reports/_harness-2026-09-04/c1-3"
sys.path.insert(0, str(ROOT))
from src.builder.routing import file_map as local_file_map

VARIANTS = ("R'", "R'-sem-corroboração", "R-sem-misto")
INHERITED = {"herdada_do_bloco", "reconciliada_do_bloco", "herdada_do_vizinho"}
REPLAY_SHA = "8971a419ca105bb3611a3d53364ab8fe6a523e9fe60f08cdb03db485e62242c8"
RULE_SHA = "2af303fa5ce592c1862afd90837df80d627aa07d40b580bacb2e0328bd7b29ca"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def section_match(section, index, replay):
    signals = {"card_text": replay.normalize_match_text(section)}
    ranking = sorted(
        ((unit["slug"], replay.score_unit(signals, unit)) for unit in index),
        key=lambda item: item[1], reverse=True,
    )
    unique = bool(
        ranking and ranking[0][1] > 0
        and (len(ranking) == 1 or ranking[0][1] > ranking[1][1])
    )
    return {
        "slug": ranking[0][0] if unique else "",
        "ambiguous": not unique,
        "ranking": ranking,
    }


def empty_metrics():
    keys = (
        "alteradas_manifest", "alteradas", "ganhos", "perdas", "saldo",
        "unidade_base", "unidade", "unidade_n", "ausentes",
        "corretas_alteradas", "perdas_adjudicadas", "perdas_fora",
        "bloco", "bloco_n",
    )
    return collections.Counter({key: 0 for key in keys})


def reliability_bucket():
    return {"n": 0, "secao_no_gold": 0, "fracao": None,
            "discorda_resultado": {"secao": 0, "final": 0, "ambos": 0, "nenhum": 0}}


def main():
    out = HERE / "regra_secao_misto_bruto_21-09.json"
    assert not out.exists(), "preservar evidência existente"
    replay_path = EVIDENCE / "replay_unidade_21-09.json"
    rule_path = EVIDENCE / "regra_secao_unidade_21-09.json"
    assert hashlib.sha256(replay_path.read_bytes()).hexdigest() == REPLAY_SHA
    assert hashlib.sha256(rule_path.read_bytes()).hexdigest() == RULE_SHA
    base = read(replay_path)
    assert all(base["checks"].values())
    replay = load("we_replay", EVIDENCE / "replay_unidade_21-09.py")
    assert replay.FM is local_file_map
    assert Path(replay.FM.__file__).resolve().is_relative_to(ROOT)
    compare = load("we_compare", EVIDENCE / "compara_herancas_15-09.py")
    mede = compare.mede
    records = {(row["curso"], str(row["id"])): row for row in base["entries"]}
    datasets, decisions, hashes, mixed_summary = {}, [], {}, {}

    for sig, name in mede.NOMES.items():
        root = DATA / (
            ".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
            else ".frzero/pacote_fontes_15-09"
        ) / name
        manifest_path = root / "manifest.json"
        inputs_path = root / "_inputs_15-09.json"
        entries = read(manifest_path)["entries"]
        profile = read(inputs_path)["profile_input"]
        index = replay.build_index(
            replay._parse_units_from_teaching_plan(profile["teaching_plan"])
        )
        assert index, (sig, "plano sem unidades")
        for path in (manifest_path, inputs_path):
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()

        raw_by_block = collections.defaultdict(set)
        for entry in entries:
            block = str(entry.get("temporal_block_id") or "")
            raw = (records[sig, str(entry["id"])]["scorer"] or {})
            if block and raw.get("slug") and raw.get("ambiguous") is False:
                raw_by_block[block].add(str(raw["slug"]))
        mixed_blocks = {block for block, slugs in raw_by_block.items() if len(slugs) >= 2}
        entries_in_mixed = [
            entry for entry in entries
            if str(entry.get("temporal_block_id") or "") in mixed_blocks
        ]
        mixed_summary[sig] = {
            "blocos": len(mixed_blocks),
            "entradas": len(entries_in_mixed),
            "block_ids": sorted(mixed_blocks),
            "raw_winners_by_block": {
                block: sorted(raw_by_block[block]) for block in sorted(mixed_blocks)
            },
        }

        predicted = {variant: {} for variant in VARIANTS}
        for entry in entries:
            eid = str(entry["id"])
            rec = records[sig, eid]
            before = str(entry.get("computed_unit_slug") or "")
            assert before == rec["gravado"] == rec["replay"]
            match = section_match(str(entry.get("source_section") or ""), index, replay)
            raw = rec["scorer"] or {}
            corroborated = bool(
                match["slug"] and raw.get("slug") == match["slug"]
                and raw.get("ambiguous") is False
            )
            block = str(entry.get("temporal_block_id") or "")
            mixed = bool(block and block in mixed_blocks)
            inherited = any(
                str(reason).split("=", 1)[0] in INHERITED
                for reason in (rec["reasons_gravado"] or [])
            )
            eligible = bool(match["slug"] and inherited and before != match["slug"])
            flags = {
                "R'": eligible and corroborated and mixed,
                "R'-sem-corroboração": eligible and mixed,
                "R-sem-misto": eligible and corroborated,
            }
            for variant, change in flags.items():
                predicted[variant][eid] = match["slug"] if change else before
            decisions.append({
                "curso": sig, "id": eid, "section": entry.get("source_section"),
                "section_match": match, "raw": raw, "before": before,
                "temporal_block_id": block, "mixed_raw": mixed,
                "inherited": inherited, "corroborated": corroborated,
                "eligible": eligible, "changed": flags,
            })
        datasets[sig] = (root, entries, predicted)

    frozen_payload = {"decisions": decisions, "mixed_summary": mixed_summary}
    frozen_decisions_sha = hashlib.sha256(
        json.dumps(frozen_payload, sort_keys=True).encode()
    ).hexdigest()

    # Avaliação começa aqui: gold, adjudicação e acerto não entraram nas decisões.
    adjudicated = mede.adjudicados()
    totals = {variant: empty_metrics() for variant in VARIANTS}
    courses = {variant: {} for variant in VARIANTS}
    changes = {variant: [] for variant in VARIANTS}
    decision_index = {(row["curso"], row["id"]): row for row in decisions}
    evaluated_by_manifest = {}
    reliability = {
        "total": {"cells": {}, "ruler_rows": 0, "absent": 0,
                  "without_unique_section": 0, "included": 0},
        "courses": {},
    }
    cell_names = (
        "herdada_concorda", "herdada_discorda",
        "nao_herdada_concorda", "nao_herdada_discorda",
    )
    reliability["total"]["cells"] = {name: reliability_bucket() for name in cell_names}

    for sig, (root, entries, predicted) in datasets.items():
        ref = DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
        ref_entries = {str(entry["id"]): entry for entry in read(ref / "manifest.json")["entries"]}
        source_index = compare.indexed(entries)
        mapping = {
            entry["entry_id"]: entry["new_id"]
            for entry in read(EVIDENCE / f"herancas_{sig}_15-09.json")["entries"]
        }
        gb, gu = mede.golds(sig)[:2]
        with (EVIDENCE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))

        rel_course = {"cells": {name: reliability_bucket() for name in cell_names},
                      "ruler_rows": 0, "absent": 0,
                      "without_unique_section": 0, "included": 0}
        for row in rows:
            if row["unidade"] == "":
                continue
            rel_course["ruler_rows"] += 1
            reliability["total"]["ruler_rows"] += 1
            eid = row["entry_id"]
            old = ref_entries.get(mapping.get(eid) or "")
            hits = source_index.get(compare.source(old), []) if old else []
            assert len(hits) <= 1, (sig, eid, "origem não única")
            entry = hits[0] if hits else None
            if entry is None:
                rel_course["absent"] += 1
                reliability["total"]["absent"] += 1
                continue
            manifest_id = str(entry["id"])
            decision = decision_index[sig, manifest_id]
            truth = gu[eid]
            before = str(entry.get("computed_unit_slug") or "")
            section = decision["section_match"]["slug"]
            evaluated_by_manifest[sig, manifest_id] = {
                "ruler_id": eid, "gold": list(truth),
                "before_correct": before in truth,
                "section_correct": section in truth if section else False,
            }
            if not section:
                rel_course["without_unique_section"] += 1
                reliability["total"]["without_unique_section"] += 1
                continue
            inherited = "herdada" if decision["inherited"] else "nao_herdada"
            relation = "concorda" if section == before else "discorda"
            cell = f"{inherited}_{relation}"
            rel_course["included"] += 1
            reliability["total"]["included"] += 1
            for bucket in (rel_course["cells"][cell], reliability["total"]["cells"][cell]):
                bucket["n"] += 1
                bucket["secao_no_gold"] += section in truth
                if relation == "discorda":
                    section_ok, final_ok = section in truth, before in truth
                    outcome = ("ambos" if section_ok and final_ok else "secao" if section_ok
                               else "final" if final_ok else "nenhum")
                    bucket["discorda_resultado"][outcome] += 1
        reliability["courses"][sig] = rel_course

        for variant in VARIANTS:
            metrics = empty_metrics()
            metrics["alteradas_manifest"] = sum(
                predicted[variant][str(entry["id"])]
                != str(entry.get("computed_unit_slug") or "")
                for entry in entries
            )
            for row in rows:
                eid = row["entry_id"]
                old = ref_entries.get(mapping.get(eid) or "")
                hits = source_index.get(compare.source(old), []) if old else []
                assert len(hits) <= 1, (sig, eid, "origem não única")
                entry = hits[0] if hits else None
                if row["bloco"] != "":
                    metrics["bloco_n"] += 1
                    if entry:
                        override = {**entry, "computed_unit_slug": predicted[variant][str(entry["id"])]}
                        assert compare.predictions(root, override)[0] == compare.predictions(root, entry)[0]
                        metrics["bloco"] += compare.predictions(root, override)[0] == gb[eid]
                if row["unidade"] == "":
                    continue
                metrics["unidade_n"] += 1
                if entry is None:
                    metrics["ausentes"] += 1
                    continue
                before = str(entry.get("computed_unit_slug") or "")
                after = predicted[variant][str(entry["id"])]
                truth = gu[eid]
                was, now = before in truth, after in truth
                metrics["unidade_base"] += was
                metrics["unidade"] += now
                if before == after:
                    continue
                gain, loss = now and not was, was and not now
                adj = eid in adjudicated
                metrics["alteradas"] += 1
                metrics["corretas_alteradas"] += now
                metrics["ganhos"] += gain
                metrics["perdas"] += loss
                metrics["perdas_adjudicadas"] += loss and adj
                metrics["perdas_fora"] += loss and not adj
                changes[variant].append({
                    "curso": sig, "id": eid, "manifest_id": str(entry["id"]),
                    "before": before, "after": after, "gold": list(truth),
                    "gain": gain, "loss": loss, "adjudicated": adj,
                })
            metrics["saldo"] = metrics["ganhos"] - metrics["perdas"]
            totals[variant].update(metrics)
            courses[variant][sig] = dict(metrics)

    for scope in [reliability["total"], *reliability["courses"].values()]:
        for bucket in scope["cells"].values():
            bucket["fracao"] = bucket["secao_no_gold"] / bucket["n"] if bucket["n"] else None

    assert hashlib.sha256(json.dumps(frozen_payload, sort_keys=True).encode()).hexdigest() == frozen_decisions_sha
    results = {}
    for variant in VARIANTS:
        total = totals[variant]
        assert (total["unidade_base"], total["unidade_n"], total["ausentes"],
                total["bloco"], total["bloco_n"]) == (239, 284, 13, 213, 237)
        assert total["unidade"] == 239 + total["saldo"]
        for metrics in [total, *courses[variant].values()]:
            metrics["precisao"] = (
                metrics["corretas_alteradas"] / metrics["alteradas"]
                if metrics["alteradas"] else None
            )
        results[variant] = {
            "total": dict(total), "courses": courses[variant],
            "changes": changes[variant],
            "losses": [change for change in changes[variant] if change["loss"]],
        }
    assert results["R-sem-misto"]["total"]["unidade"] == 244
    assert results["R-sem-misto"]["total"]["alteradas_manifest"] == 8

    reference_changed = [row for row in decisions if row["changed"]["R-sem-misto"]]
    reference_mixed = [
        {"curso": row["curso"], "manifest_id": row["id"],
         "temporal_block_id": row["temporal_block_id"]}
        for row in reference_changed if row["mixed_raw"]
    ]
    noncorroborated = []
    for row in decisions:
        if not row["eligible"] or row["corroborated"]:
            continue
        evaluated = evaluated_by_manifest.get((row["curso"], row["id"]))
        noncorroborated.append({
            "curso": row["curso"], "manifest_id": row["id"],
            "id": evaluated["ruler_id"] if evaluated else None,
            "before": row["before"], "section": row["section_match"]["slug"],
            "gold": evaluated["gold"] if evaluated else None,
            "before_correct": evaluated["before_correct"] if evaluated else None,
            "section_correct": evaluated["section_correct"] if evaluated else None,
            "mixed_raw": row["mixed_raw"],
        })
    assert len(noncorroborated) == 2

    report = {
        "definitions": __doc__, "head": base["head"],
        "replay_sha256": REPLAY_SHA, "source_rule_sha256": RULE_SHA,
        "decisions_before_gold_sha256": frozen_decisions_sha,
        "input_hashes": hashes, "mixed_raw": mixed_summary,
        "variants": results,
        "reference_changes_in_mixed_raw_blocks": reference_mixed,
        "eligible_not_corroborated": noncorroborated,
        "section_signal_reliability": reliability,
        "decisions": decisions,
        "validation": (
            "asserts: regra-base sha; replay sha; R-sem-misto 244/284 e 8 alterações; "
            "239/284, 13 ausentes, 213/237; 2 elegíveis não corroboradas; "
            "decisões congeladas antes do gold; 0 LLM/rede/build"
        ),
        "limitations": [
            "c' usa scorer bruto do texto, mas a ação continua restrita às três razões herdadas.",
            "Não ambíguo da seção significa máximo positivo único, sem piso/margem do gate de produção.",
            "Scorer bruto do replay já inclui card: corroboração não é evidência independente.",
            "Índice da seção usa só plano, sem enriquecimento de glossário/corpus.",
            "Cursos já estudados; sem ajuste por gold, mas não são holdout novo.",
            "As 13 entradas ausentes permanecem nos denominadores das variantes; não têm sinal de seção observável.",
            "Sem régua de unidade para FR; alterações fora da régua não têm precisão aferível.",
        ],
    }
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "variants": {name: value["total"] for name, value in results.items()},
        "mixed_raw": mixed_summary,
        "reference_changes_in_mixed_raw_blocks": reference_mixed,
        "eligible_not_corroborated": noncorroborated,
        "section_signal_reliability": reliability,
    }, ensure_ascii=False, indent=2))
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
