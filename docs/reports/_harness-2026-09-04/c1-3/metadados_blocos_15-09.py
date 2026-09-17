"""Contraste de metadados reais, sem trocar texto ou reextrair documentos."""
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
os.environ["TUTOR_REPOS_ORIG"] = str(ROOT.parent)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load("audit_herancas", HERE / "audita_herancas_15-09.py")
compare = load("compare_herancas", HERE / "compara_herancas_15-09.py")
FIELDS = {
    "controle": (), "datas": ("posting_date", "posting_date_created"),
    "rotulos": ("moodle_label", "source_section"),
    "ordem": ("moodle_section_index", "moodle_module_index", "moodle_week_label"),
}
FIELDS["conjunto"] = FIELDS["datas"] + FIELDS["rotulos"] + FIELDS["ordem"]
FIELDS["datas_cards"] = ()
CALLS = []


def blocked(*args, **kwargs):
    CALLS.append("network")
    raise RuntimeError("REDE BLOQUEADA na medicao de metadados")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def text_hashes(root, entries):
    return {e["id"]: hashlib.sha256(compare._entry_markdown_text_for_file_map(root, e).encode()).hexdigest()
            for e in entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curso", choices=audit.COURSES, required=True)
    parser.add_argument("--braco", choices=FIELDS, required=True)
    parser.add_argument("--rodada", default="integral")
    args = parser.parse_args()
    name, source_arm = audit.COURSES[args.curso]
    src = ROOT / ".frzero" / source_arm / name
    if not args.rodada.isidentifier():
        parser.error("rodada precisa ser um identificador")
    parent = ROOT / ".frzero" / f"metadados_{args.braco}_{args.rodada}_15-09"
    dest = parent / name
    if dest.exists():
        parser.error("destino ja existe; preservar rodada")
    if args.braco != "controle":
        control = read(ROOT / ".frzero" / f"metadados_controle_{args.rodada}_15-09" / name / "_metadados_result_15-09.json")
        assert control["prediction_changes"] == 0 and control["valid"], control
    # Sem raw/zip, incremental_build remove entries: a cópia tem de ser integral.
    shutil.copytree(src, dest)
    manifest = read(dest / "manifest.json")
    before_entries = copy.deepcopy(manifest["entries"])
    before_predictions = {e["id"]: compare.predictions(src, e) for e in before_entries}
    before_text = text_hashes(src, before_entries)
    before_tax = read(src / "course/.content_taxonomy.json")
    inherited = ROOT / ".frzero/implementacao_taxonomia_15-09" / name
    old = compare.indexed(read(inherited / "manifest.json")["entries"])
    new_sources = compare.indexed(before_entries)
    changes = []
    for entry in manifest["entries"]:
        source = compare.source(entry)
        matches = old.get(source, [])
        if not source or len(matches) != 1 or len(new_sources[source]) != 1:
            continue
        for field in FIELDS[args.braco]:
            previous, value = entry.get(field), matches[0].get(field)
            if previous != value:
                changes.append({"id": entry["id"], "field": field, "before": previous, "after": value})
            if field in matches[0]:
                entry[field] = copy.deepcopy(value)
            else:
                entry.pop(field, None)
    write(dest / "manifest.json", manifest)
    if args.braco == "datas_cards":
        from datetime import date
        card_path = inherited / "course/.card_block_map.json"
        source_cards = read(card_path) if card_path.exists() else {}
        target = dest / "course/.card_block_map.json"
        cards = read(target) if target.exists() else {}
        for card, info in source_cards.items():
            if info.get("source") != "labels" or not info.get("dates"):
                continue
            for value in info["dates"]:
                date.fromisoformat(value)
            restored = {"source": "labels", "format": info.get("format", ""),
                        "dates": info["dates"], "block_ids": []}
            if cards.get(card) != restored:
                changes.append({"id": card, "field": "card_dates", "before": cards.get(card), "after": restored})
                cards[card] = restored
        write(target, cards)
    socket.socket.connect = blocked
    socket.create_connection = blocked
    from src.builder.runtime import gemini_client, datalab_client
    gemini_client.get_gemini_client = lambda config=None: None
    gemini_client.GeminiClient.__init__ = blocked
    datalab_client.convert_document_to_markdown = blocked
    import reprocess_assignments as ra
    original_merge = ra._merge_profile_flags

    def merge(options, profile):
        original_merge(options, profile)
        options.update(use_llm_voter=False, compile_vocabulary=False)

    ra._merge_profile_flags = merge
    ra.reprocess(dest, [])
    after_entries = read(dest / "manifest.json")["entries"]
    prediction_changes = sum(compare.predictions(dest, e) != before_predictions[e["id"]] for e in after_entries)
    same_text = text_hashes(dest, after_entries) == before_text
    same_tax = read(dest / "course/.content_taxonomy.json") == before_tax
    same_entries = {e["id"] for e in before_entries} == {e["id"] for e in after_entries}
    result = {"course": args.curso, "arm": args.braco, "calls": CALLS,
              "changed_fields": dict(collections.Counter(c["field"] for c in changes)),
              "changes": changes, "prediction_changes": prediction_changes,
              "same_text": same_text, "same_taxonomy": same_tax, "same_entries": same_entries,
              "valid": same_entries and same_text and same_tax and not CALLS}
    write(dest / "_metadados_result_15-09.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "changes"}, ensure_ascii=False))
    assert result["valid"], "contraste nao isolou metadados"
    if args.braco == "controle":
        assert prediction_changes == 0, "controle divergiu; parar"


if __name__ == "__main__":
    main()
