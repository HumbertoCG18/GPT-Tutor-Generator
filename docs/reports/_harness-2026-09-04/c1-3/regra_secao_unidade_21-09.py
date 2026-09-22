"""W-C: definições pré-declaradas antes de carregar gold; três variantes apenas.

(a) Seção específica: source_section normalizado, somente em card_text, pontua
contra títulos/tópicos do teaching_plan via build_file_map_unit_index e
score_entry_against_unit (mesmas funções/injeções do replay). Máximo positivo
estritamente único; zero/empate = ambíguo. Sem piso de confiança ou margem
ajustável; não usa o gate parametrizado de auto_map_entry_unit. Sem aliases
derivados dos materiais, número explícito, título do arquivo ou tags da entrada.
Seção genérica/semanal sem vencedor único não dispara.
(b) Corroboração: scorer.slug bruto do replay igual ao vencedor da seção,
slug não vazio e scorer.ambiguous falso. Não usar gravado como texto bruto.
(c) Misto: definição histórica REUTILIZADA de
PRINCIPAL/docs/reports/_harness-2026-09-04/c1-3/texto_vence_cortes_13-09.py:48-55:
2+ computed_unit_slug não vazios distintos entre entradas do mesmo
temporal_block_id não vazio, antes de qualquer override. NÃO são slugs brutos.
(d) Ação: razões herdada_do_bloco/reconciliada_do_bloco/herdada_do_vizinho,
unidade final diferente da seção; substituir só computed_unit_slug em memória.
R = a+b+c; R-sem-misto = a+b; R-sem-corroboração = a+c.
Sem parâmetros ajustados: cada curso é o fold de avaliação sem treinamento.
Gold é carregado só depois de TODAS as decisões; pertinência ao conjunto aceito.
Precisão = decisões alteradas corretas / alteradas com régua de unidade.
Adjudicados = mede.adjudicados(); ausentes continuam nos denominadores.
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
VARIANTS = ("R", "R-sem-misto", "R-sem-corroboração")
INHERITED = {"herdada_do_bloco", "reconciliada_do_bloco", "herdada_do_vizinho"}
EXPECTED = "8971a419ca105bb3611a3d53364ab8fe6a523e9fe60f08cdb03db485e62242c8"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def section_match(section, index, replay):
    signals = {"card_text": replay.normalize_match_text(section)}
    ranking = sorted(((u["slug"], replay.score_unit(signals, u)) for u in index),
                     key=lambda item: item[1], reverse=True)
    unique = bool(ranking and ranking[0][1] > 0 and
                  (len(ranking) == 1 or ranking[0][1] > ranking[1][1]))
    return {"slug": ranking[0][0] if unique else "", "ambiguous": not unique,
            "ranking": ranking}


def main():
    out = HERE / "regra_secao_unidade_21-09.json"
    assert not out.exists(), "preservar evidência existente"
    base_path = EVIDENCE / "replay_unidade_21-09.json"
    assert hashlib.sha256(base_path.read_bytes()).hexdigest() == EXPECTED
    base = read(base_path)
    assert all(base["checks"].values())
    replay = load("wc_replay", EVIDENCE / "replay_unidade_21-09.py")
    # Import local src before compare can prepend the principal checkout.
    assert replay.FM is local_file_map and Path(replay.FM.__file__).resolve().is_relative_to(ROOT)
    compare = load("wc_compare", EVIDENCE / "compara_herancas_15-09.py")
    mede = compare.mede
    records = {(r["curso"], str(r["id"])): r for r in base["entries"]}
    datasets, decisions, hashes = {}, [], {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
                       else ".frzero/pacote_fontes_15-09") / name
        manifest_path = root / "manifest.json"
        inputs_path = root / "_inputs_15-09.json"
        entries = read(manifest_path)["entries"]
        profile = read(inputs_path)["profile_input"]
        index = replay.build_index(replay._parse_units_from_teaching_plan(profile["teaching_plan"]))
        assert index, (sig, "plano sem unidades")
        for path in (manifest_path, inputs_path):
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        by_block = collections.defaultdict(set)
        for entry in entries:
            block, unit = str(entry.get("temporal_block_id") or ""), str(entry.get("computed_unit_slug") or "")
            if block and unit:
                by_block[block].add(unit)
        predicted = {v: {} for v in VARIANTS}
        for entry in entries:
            eid = str(entry["id"])
            rec = records[sig, eid]
            before = str(entry.get("computed_unit_slug") or "")
            assert before == rec["gravado"] == rec["replay"]
            match = section_match(str(entry.get("source_section") or ""), index, replay)
            raw = rec["scorer"] or {}
            corroborated = bool(match["slug"] and raw.get("slug") == match["slug"] and
                                raw.get("ambiguous") is False)
            mixed = len(by_block.get(str(entry.get("temporal_block_id") or ""), set())) > 1
            inherited = any(str(r).split("=", 1)[0] in INHERITED for r in (rec["reasons_gravado"] or []))
            eligible = bool(match["slug"] and inherited and before != match["slug"])
            flags = {"R": eligible and corroborated and mixed,
                     "R-sem-misto": eligible and corroborated,
                     "R-sem-corroboração": eligible and mixed}
            for variant, change in flags.items():
                predicted[variant][eid] = match["slug"] if change else before
            decisions.append({"curso": sig, "id": eid, "section": entry.get("source_section"),
                              "section_match": match, "raw": raw, "before": before,
                              "mixed": mixed, "inherited": inherited, "corroborated": corroborated,
                              "changed": flags})
        datasets[sig] = (root, entries, predicted)
    # Evaluation starts here: no gold, adjudication or correctness entered the rules.
    frozen_decisions_sha = hashlib.sha256(json.dumps(decisions, sort_keys=True).encode()).hexdigest()
    adjudicated = mede.adjudicados()
    totals = {v: collections.Counter() for v in VARIANTS}
    courses = {v: {} for v in VARIANTS}
    changes = {v: [] for v in VARIANTS}
    keys = ("alteradas_manifest", "alteradas", "ganhos", "perdas", "saldo", "unidade_base",
            "unidade", "unidade_n", "ausentes", "corretas_alteradas", "perdas_adjudicadas",
            "perdas_fora", "bloco", "bloco_n")
    for sig, (root, entries, predicted) in datasets.items():
        ref = DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
        ref_entries = {str(e["id"]): e for e in read(ref / "manifest.json")["entries"]}
        source_index = compare.indexed(entries)
        mapping = {e["entry_id"]: e["new_id"] for e in read(EVIDENCE / f"herancas_{sig}_15-09.json")["entries"]}
        gb, gu = mede.golds(sig)[:2]
        with (EVIDENCE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        for variant in VARIANTS:
            c = collections.Counter({key: 0 for key in keys})
            c["alteradas_manifest"] = sum(predicted[variant][str(e["id"])] != str(e.get("computed_unit_slug") or "") for e in entries)
            for row in rows:
                eid = row["entry_id"]
                old = ref_entries.get(mapping.get(eid) or "")
                hits = source_index.get(compare.source(old), []) if old else []
                assert len(hits) <= 1, (sig, eid, "origem não única")
                entry = hits[0] if hits else None
                if row["bloco"] != "":
                    c["bloco_n"] += 1
                    if entry:
                        override = {**entry, "computed_unit_slug": predicted[variant][str(entry["id"])]}
                        assert compare.predictions(root, override)[0] == compare.predictions(root, entry)[0]
                        c["bloco"] += compare.predictions(root, override)[0] == gb[eid]
                if row["unidade"] == "":
                    continue
                c["unidade_n"] += 1
                if entry is None:
                    c["ausentes"] += 1
                    continue
                before = str(entry.get("computed_unit_slug") or "")
                after = predicted[variant][str(entry["id"])]; truth = gu[eid]
                was, now = before in truth, after in truth
                c["unidade_base"] += was; c["unidade"] += now
                if before == after:
                    continue
                gain, loss = now and not was, was and not now
                adj = eid in adjudicated
                c["alteradas"] += 1; c["corretas_alteradas"] += now
                c["ganhos"] += gain; c["perdas"] += loss
                c["perdas_adjudicadas"] += loss and adj; c["perdas_fora"] += loss and not adj
                changes[variant].append({"curso": sig, "id": eid, "manifest_id": str(entry["id"]),
                                         "before": before, "after": after, "gold": list(truth),
                                         "gain": gain, "loss": loss, "adjudicated": adj})
            c["saldo"] = c["ganhos"] - c["perdas"]
            totals[variant].update(c)
            courses[variant][sig] = dict(c)
    assert hashlib.sha256(json.dumps(decisions, sort_keys=True).encode()).hexdigest() == frozen_decisions_sha
    results = {}
    for variant in VARIANTS:
        c = totals[variant]
        assert (c["unidade_base"], c["unidade_n"], c["ausentes"], c["bloco"], c["bloco_n"]) == (239, 284, 13, 213, 237)
        assert c["unidade"] == 239 + c["saldo"]
        for metrics in [c, *courses[variant].values()]:
            metrics["precisao"] = metrics["corretas_alteradas"] / metrics["alteradas"] if metrics["alteradas"] else None
        results[variant] = {"total": dict(c), "courses": courses[variant], "changes": changes[variant],
                            "losses": [x for x in changes[variant] if x["loss"]]}
        if c["saldo"] > 0 and c["perdas"] == 0 and all(x["saldo"] >= 0 for x in courses[variant].values()):
            results[variant]["aceite_referencia"] = "PASSA"
        print(variant, json.dumps(results[variant], ensure_ascii=False), flush=True)
    report = {"definitions": __doc__, "head": base["head"], "baseline_sha256": EXPECTED,
              "decisions_before_gold_sha256": frozen_decisions_sha, "input_hashes": hashes,
              "variants": results, "decisions": decisions,
              "validation": "asserts: 239/284, 13 ausentes, 213/237, decisões congeladas; 0 LLM/rede/build",
              "limitations": ["Misto histórico usa unidades finais: pode ser degenerado pela reconciliação.",
                              "Não ambíguo da seção significa máximo positivo único, sem piso/margem do gate de produção.",
                              "Scorer bruto do replay já inclui card: corroboração não é evidência independente.",
                              "Índice da seção usa só plano, sem enriquecimento de glossário/corpus.",
                              "Cursos já estudados; sem ajuste por gold, mas não são holdout novo.",
                              "Sem régua de unidade para FR; alterações fora da régua não têm precisão aferível."]}
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
