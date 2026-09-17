"""Proveniência das perdas já medidas; não escolhe entradas para os braços."""
import collections
import argparse
import hashlib
import importlib.util
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("meta_driver", HERE / "metadados_blocos_15-09.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
ROOT = driver.ROOT


def md_source(root, entry):
    run = root / str(entry.get("advanced_metadata_path") or "__absent__")
    asset = root / str(entry.get("advanced_asset_dir") or "__absent__")
    candidates = []
    if run.is_file() and driver.read(run).get("backend") == "datalab":
        for key in ("advanced_markdown", "approved_source_markdown"):
            path = root / str(entry.get(key) or "__absent__")
            if path.is_file() and "datalab" in path.parts:
                candidates = [path]
                break
        if not candidates and asset.is_dir():
            candidates = sorted(asset.rglob("*.md"))
    provider = "datalab" if candidates else "fallback_sem_prova_datalab"
    if not candidates:
        for key in ("approved_markdown", "curated_markdown", "base_markdown", "advanced_markdown"):
            path = root / str(entry.get(key) or "__absent__")
            if path.is_file():
                candidates = [path]
                break
    files = []
    for path in candidates:
        assert path.resolve().is_relative_to(root.resolve())
        data = path.read_bytes()
        text = data.decode("utf-8-sig", errors="replace")
        fm = re.match(r"\A---\s*\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
        keys = re.findall(r"^([A-Za-z_][\w-]*):", fm[1], re.M) if fm else []
        files.append({"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                      "frontmatter_keys": keys})
    return {"provider": provider, "files": files,
            "note": "frontmatter do app nao prova metadado extraido do PDF"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--originais", action="store_true")
    parser.add_argument("--saida", default="inventario_metadados_perdas_15-09.json")
    args = parser.parse_args()
    out = (HERE / args.saida).resolve()
    assert out.parent == HERE
    assert not out.exists(), "preservar inventario existente"
    records, summary = [], {}
    fields = (*driver.FIELDS["conjunto"], "manual_timeline_block_id", "manual_unit_slug", "category")
    for course, (name, arm) in driver.audit.COURSES.items():
        old_root = ROOT / ".frzero/implementacao_taxonomia_15-09" / name
        new_root = ROOT / ".frzero" / arm / name
        old = {e["id"]: e for e in driver.read(old_root / "manifest.json")["entries"]}
        new = {e["id"]: e for e in driver.read(new_root / "manifest.json")["entries"]}
        product_root = ROOT.parent / name
        product = driver.compare.indexed(driver.read(product_root / "manifest.json")["entries"]) if args.originais else {}
        measured = driver.read(HERE / f"herancas_{course}_15-09.json")
        counts = collections.Counter()
        for item in measured["entries"]:
            if not item["matched"] or "bloco" not in item["losses"]:
                continue
            a, b = old[item["entry_id"]], new[item["new_id"]]
            differences = {k: [a.get(k), b.get(k)] for k in fields if a.get(k) != b.get(k)}
            md = md_source(old_root, a)
            if args.originais and md["provider"] != "datalab":
                source = driver.compare.source(a)
                matches = product.get(source, [])
                if len(matches) == 1:
                    original_md = md_source(product_root, matches[0])
                    if original_md["provider"] == "datalab":
                        md = original_md
            counts["perdas"] += 1
            counts[md["provider"]] += 1
            counts.update(differences.keys())
            records.append({"course": course, "entry_id": a["id"], "new_id": b["id"],
                            "differences": differences, "md_source": md,
                            "before": item["pred_before"], "after": item["pred_after"]})
        summary[course] = dict(counts)
        print(course, dict(counts))
    assert len(records) == 50, len(records)
    driver.write(out, {"summary": summary, "losses": records})


if __name__ == "__main__":
    main()
