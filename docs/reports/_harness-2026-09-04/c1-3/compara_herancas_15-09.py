"""Avalia depois do build; vínculo por origem única, denominadores congelados."""
import argparse
import collections
import csv
import json
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("mede", HERE / "mede_3eixos_12-09.py")
mede = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mede)
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map

AXES = ("bloco", "unidade", "sub_aceito", "sub_primario")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source(entry):
    value = str(entry.get("source_path") or "")
    if not value or value.startswith(("http://", "https://")):
        return value
    return str(Path(value).resolve()).casefold()


def indexed(entries):
    result = collections.defaultdict(list)
    for entry in entries:
        result[source(entry)].append(entry)
    return result


def predictions(root, entry):
    timeline = root / "course/.timeline_index.json"
    blocks = read(timeline).get("blocks", []) if timeline.exists() else []
    lookup = {str(b["block_uuid"]): b["id"] for b in blocks}
    lookup.update({str(b["id"]): b["id"] for b in blocks})
    block = str(entry.get("manual_timeline_block_id") or entry.get("temporal_block_id") or "")
    return lookup.get(block, block), str(entry.get("computed_unit_slug") or ""), str(entry.get("computed_subunit_slug") or "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=".frzero/implementacao_taxonomia_15-09")
    parser.add_argument("--novo", default=".frzero/cru_fontes_15-09")
    parser.add_argument("--cursos", default=",".join(mede.NOMES))
    parser.add_argument("--saida")
    parser.add_argument("--autoteste", action="store_true")
    args = parser.parse_args()
    baseline = list(csv.DictReader((HERE / "snapshot_implementacao_taxonomia_15-09.csv").open(encoding="utf-8-sig")))
    if args.autoteste:
        checked = 0
        for sig, name in mede.NOMES.items():
            root = ROOT / args.base / name
            entries = {e["id"]: e for e in read(root / "manifest.json")["entries"]}
            gold = mede.golds(sig)
            for row in (r for r in baseline if r["curso"] == sig):
                block, unit, sub = predictions(root, entries[row["entry_id"]])
                for axis, truth, pred in zip(AXES, gold, (block, unit, sub, sub), strict=True):
                    if row[axis] != "":
                        target = truth[row["entry_id"]]
                        actual = pred == target if axis == "bloco" else pred in target
                        assert int(actual) == int(row[axis]), (sig, row["entry_id"], axis)
                checked += 1
        assert checked == 316
        print(f"autoteste: {checked} materiais reproduzem os quatro eixos da baseline")
        return
    if not args.saida:
        parser.error("--saida obrigatoria na comparacao")
    out = HERE / args.saida
    if out.exists() or out.with_suffix(".csv").exists():
        parser.error("saida ja existe")
    details, rows, summary = [], [], {}
    for sig in args.cursos.split(","):
        old_root, new_root = ROOT / args.base / mede.NOMES[sig], ROOT / args.novo / mede.NOMES[sig]
        result = read(new_root / "_build_result_15-09.json")
        if result["calls"]:
            raise AssertionError(f"rede tentada em {sig}: {result['calls']}")
        old_entries = read(old_root / "manifest.json")["entries"]
        new_entries = read(new_root / "manifest.json")["entries"]
        by_id = {e["id"]: e for e in old_entries}
        old_sources, new_sources = indexed(old_entries), indexed(new_entries)
        gold = mede.golds(sig)
        count = collections.Counter()
        changed_fields = collections.Counter()
        for base in (r for r in baseline if r["curso"] == sig):
            eid = base["entry_id"]
            old = by_id[eid]
            key = source(old)
            matches = new_sources.get(key, [])
            matched = bool(key) and len(matches) == 1 and len(old_sources[key]) == 1
            new = matches[0] if matched else {}
            pb, pu, ps = predictions(new_root, new) if matched else ("", "", "")
            row = {**base, "pred_bloco": pb, "pred_unidade": pu, "pred_sub": ps}
            flags = []
            if not matched:
                flags.append("origem_ambigua" if matches else "entrada_ausente")
                count[flags[-1]] += 1
            else:
                count["comuns"] += 1
                for field in ("title", "file_type", "category", "source_section", "moodle_label", "posting_date",
                              "manual_unit_slug", "manual_timeline_block_id", "base_backend"):
                    if old.get(field) != new.get(field):
                        flags.append(field)
                        changed_fields[field] += 1
            before = _entry_markdown_text_for_file_map(old_root, old)
            after = _entry_markdown_text_for_file_map(new_root, new) if matched else ""
            if matched and before != after:
                flags.append("texto_extraido")
                changed_fields["texto_extraido"] += 1
            gains, losses = [], []
            for axis, truth, prediction in zip(AXES, gold, (pb, pu, ps, ps), strict=True):
                if base[axis] == "":
                    row[axis] = ""
                    continue
                target = truth[eid]
                correct = int(matched and (prediction == target if axis == "bloco" else prediction in target))
                old_correct = int(base[axis])
                row[axis] = correct
                count[f"{axis}_n"] += 1
                count[f"{axis}_base"] += old_correct
                count[f"{axis}_novo"] += correct
                if matched:
                    count[f"{axis}_comum_n"] += 1
                    count[f"{axis}_comum_base"] += old_correct
                    count[f"{axis}_comum_novo"] += correct
                if correct > old_correct:
                    gains.append(axis)
                    count[f"{axis}_ganhos"] += 1
                if correct < old_correct:
                    losses.append(axis)
                    count[f"{axis}_perdas"] += 1
            rows.append(row)
            details.append({"curso": sig, "entry_id": eid, "new_id": new.get("id"),
                            "source": key, "matched": matched, "observed_differences": flags,
                            "text_chars": [len(before), len(after)], "gains": gains, "losses": losses,
                            "pred_before": [base["pred_bloco"], base["pred_unidade"], base["pred_sub"]],
                            "pred_after": [pb, pu, ps]})
        count["manifest_base"] = len(old_entries)
        count["manifest_novo"] = len(new_entries)
        count["novas_origens"] = len(set(new_sources) - set(old_sources))
        summary[sig] = {"counts": dict(count), "changed_fields": dict(changed_fields)}
        print(f"{sig}: comuns={count['comuns']} ausentes={count['entrada_ausente']} ambiguos={count['origem_ambigua']} novas_origens={count['novas_origens']}")
        for axis in AXES:
            print(f"  {axis}: base={count[axis+'_base']}/{count[axis+'_n']} novo={count[axis+'_novo']}/{count[axis+'_n']} ganhos={count[axis+'_ganhos']} perdas={count[axis+'_perdas']} | comuns={count[axis+'_comum_base']}->{count[axis+'_comum_novo']}/{count[axis+'_comum_n']}")
        print(f"  diferencas observadas (nao causas isoladas): {dict(changed_fields)}")
    out.write_text(json.dumps({"summary": summary, "entries": details}, ensure_ascii=False, indent=2), encoding="utf-8")
    with out.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
