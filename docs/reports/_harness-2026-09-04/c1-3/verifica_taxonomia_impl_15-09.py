"""Compara cobertura e derivados semânticos; não executa o motor."""
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--novo", required=True)
    args = parser.parse_args()
    base, new = ROOT / args.base, ROOT / args.novo
    for course in sorted(new.iterdir()):
        if not (course / "manifest.json").is_file():
            continue
        old = base / course.name
        tax = read(course / "course/.content_taxonomy.json")
        topics = [t for u in tax["units"] for t in u["topics"]]
        covered = sum(bool(t.get("aliases")) for t in topics)
        print(f"{course.name}: aliases={covered}/{len(topics)}")
        for artifact in (".tag_catalog.json", ".semantic_profile.generated.json"):
            left = read(old / "course" / artifact)
            right = read(course / "course" / artifact)
            keys = sorted(k for k in left.keys() | right.keys() if left.get(k) != right.get(k))
            print(f"  {artifact}: campos_diferentes={keys}")
            for key in keys:
                print(f"    {key}: base={left.get(key)} novo={right.get(key)}")
        previous = {e["id"]: e for e in read(old / "manifest.json")["entries"]}
        current = {e["id"]: e for e in read(course / "manifest.json")["entries"]}
        if previous.keys() != current.keys():
            raise AssertionError(f"inventario de materiais mudou: {course.name}")
        for field in ("auto_tags", "computed_unit_slug", "computed_subunit_slug", "temporal_block_id"):
            changed = [eid for eid, entry in current.items() if entry.get(field) != previous[eid].get(field)]
            print(f"  manifest.{field}: {len(changed)} alteracoes")
            for eid in changed:
                print(f"    {eid}: {previous[eid].get(field)} -> {current[eid].get(field)}")


if __name__ == "__main__":
    main()
