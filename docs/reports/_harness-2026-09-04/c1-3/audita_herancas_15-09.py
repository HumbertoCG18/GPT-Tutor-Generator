"""Consolida medidas existentes e confere fontes, estrutura temporal e aliases."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from src.builder.extraction.content_taxonomy import collect_strong_heading_candidates

COURSES = {
    "MF": ("Metodos-Formais-Tutor", "cru_fontes_serial_15-09"),
    "SO": ("Sistemas-Operacionais-Tutor", "cru_fontes_15-09"),
    "IA": ("Inteligencia-Artifical-Tutor", "cru_fontes_serial_15-09"),
    "ES2": ("Engenharia-Software-2-Tutor", "cru_fontes_15-09"),
    "TCC": ("TCC-Tutor", "cru_fontes_15-09"),
    "CG": ("Computacao-Grafica-Tutor", "cru_fontes_semhtml_15-09"),
    "FR": ("Fundamentos-de-Redes-Tutor", "cru_fontes_controle_15-09"),
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def describe(root):
    entries = read(root / "manifest.json")["entries"]
    topics = [t for u in read(root / "course/.content_taxonomy.json")["units"] for t in u["topics"]]
    blocks = read(root / "course/.timeline_index.json")["blocks"]
    return {
        "entries": len(entries),
        "base_backends": dict(collections.Counter(str(e.get("base_backend") or "") for e in entries)),
        "base_staging": sum(str(e.get("base_markdown") or "").startswith("staging/") for e in entries),
        "curated_refs": sum(bool(e.get("approved_markdown") or e.get("curated_markdown")) for e in entries),
        "headings": len(collect_strong_heading_candidates(root, entries)),
        "topics": len(topics), "aliases": sum(len(t["aliases"]) for t in topics),
        "zero_alias": sum(not t["aliases"] for t in topics),
        "topic_aliases": {f"{t['unit_slug']}/{t['slug']}": t["aliases"] for t in topics},
        "timeline_structure": [{k: b.get(k) for k in ("id", "period_start", "period_end", "source_rows")} for b in blocks],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cursos", default=",".join(COURSES))
    parser.add_argument("--saida", required=True)
    args = parser.parse_args()
    out = (HERE / args.saida).resolve()
    if out.parent != HERE or out.exists():
        parser.error("saida precisa ser nova e estar em c1-3")
    total, audits = collections.Counter(), {}
    for course in args.cursos.split(","):
        name, arm = COURSES[course]
        old_root = ROOT / ".frzero/implementacao_taxonomia_15-09" / name
        new_root = ROOT / ".frzero" / arm / name
        result = read(new_root / "_build_result_15-09.json")
        assert result.get("completed", True) and not result["calls"], (course, result)
        inputs = read(new_root / "_inputs_15-09.json")
        sources = inputs["inputs"] + inputs["metadata_sources"]
        stash = Path(inputs["stash"])
        candidates = [p / rel for p in (stash, stash.parent)
                      for rel in ("raw/moodle/contents.json", ".moodle_nomes.json")]
        for item in sources:
            assert hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest() == item["sha256"], item["path"]
        measured = read(HERE / f"herancas_{course}_15-09.json")
        counts = measured["summary"][course]["counts"]
        total.update(counts)
        old, new = describe(old_root), describe(new_root)
        same_timeline = old["timeline_structure"] == new["timeline_structure"]
        assert same_timeline, f"regua ordinal precisa revisao em {course}"
        missing_losses = collections.Counter(axis for e in measured["entries"] if not e["matched"] for axis in e["losses"])
        audits[course] = {"root": str(new_root), "build": result, "verified_hashes": len(sources),
                          "metadata_candidates": {str(p): p.is_file() for p in candidates},
                          "before": old, "after": new, "same_timeline": same_timeline,
                          "losses_missing_inputs": dict(missing_losses)}
        print(f"{course}: hashes={len(sources)} timeline_igual={same_timeline} aliases={old['aliases']}->{new['aliases']} headings={old['headings']}->{new['headings']} perdas_ausentes={dict(missing_losses)}")
    payload = {"totals": dict(total), "courses": audits}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(dict(total), ensure_ascii=False))


if __name__ == "__main__":
    main()
