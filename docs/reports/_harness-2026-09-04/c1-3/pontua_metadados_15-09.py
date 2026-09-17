"""Pontua braços concluídos contra a reconstrução, com denominadores congelados."""
import argparse
import collections
import csv
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("meta_driver", HERE / "metadados_blocos_15-09.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cursos", default="ES2,IA")
    parser.add_argument("--bracos", default="controle,datas,rotulos,ordem,conjunto")
    parser.add_argument("--saida", required=True)
    args = parser.parse_args()
    out = (HERE / args.saida).resolve()
    assert out.parent == HERE and not out.exists()
    totals, details = {}, []
    for course in args.cursos.split(","):
        name, _ = driver.audit.COURSES[course]
        rows = list(csv.DictReader((HERE / f"herancas_{course}_15-09.csv").open(encoding="utf-8-sig")))
        mapping = {e["entry_id"]: e["new_id"] for e in driver.read(HERE / f"herancas_{course}_15-09.json")["entries"]}
        gold = driver.compare.mede.golds(course)
        for arm in args.bracos.split(","):
            root = driver.ROOT / ".frzero" / f"metadados_{arm}_integral_15-09" / name
            result = driver.read(root / "_metadados_result_15-09.json")
            assert result["valid"] and not result["calls"], result
            entries = {e["id"]: e for e in driver.read(root / "manifest.json")["entries"]}
            count = collections.Counter()
            for row in rows:
                entry = entries.get(mapping[row["entry_id"]])
                block, unit, sub = driver.compare.predictions(root, entry) if entry else ("", "", "")
                flips = {}
                for axis, truth, prediction in zip(driver.compare.AXES, gold, (block, unit, sub, sub), strict=True):
                    if row[axis] == "":
                        continue
                    target = truth[row["entry_id"]]
                    correct = int(entry is not None and (prediction == target if axis == "bloco" else prediction in target))
                    old = int(row[axis])
                    count[f"{axis}_n"] += 1
                    count[f"{axis}_before"] += old
                    count[f"{axis}_after"] += correct
                    count[f"{axis}_gains"] += correct > old
                    count[f"{axis}_losses"] += correct < old
                    if correct != old:
                        flips[axis] = [old, correct]
                if flips:
                    details.append({"course": course, "arm": arm, "entry_id": row["entry_id"], "flips": flips})
            if arm == "controle":
                assert not any(count[f"{a}_{kind}"] for a in driver.compare.AXES for kind in ("gains", "losses"))
            totals[f"{course}/{arm}"] = dict(count)
            print(f"{course}/{arm}: " + " | ".join(f"{a} {count[a+'_before']}->{count[a+'_after']}/{count[a+'_n']} +{count[a+'_gains']}/-{count[a+'_losses']}" for a in driver.compare.AXES))
    driver.write(out, {"counts": totals, "flips": details})


if __name__ == "__main__":
    main()
