"""W-K: replay em memoria da decisao de BLOCO temporal (motor D9); gold so na avaliacao."""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
EVIDENCE = DATA / "docs/reports/_harness-2026-09-04/c1-3"
sys.path.insert(0, str(ROOT))

from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
from src.builder.routing.motor import apply as motor_apply

CAMPOS = ("temporal_block_id", "temporal_block_method", "temporal_block_band",
          "temporal_block_flag", "temporal_block_provider")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay(root):
    """Roda a fase real com as chaves temporais removidas (decisao nao ve a resposta)."""
    manifest = read(root / "manifest.json")
    original = manifest["entries"]
    entries = copy.deepcopy(original)
    for entry in entries:
        for field in motor_apply.TEMPORAL_KEYS:
            entry.pop(field, None)
    decisions: dict = {}
    write = motor_apply._write_temporal

    def traced(entry, decision, ctx):   # captura o AnchorDecision sem alterar src/
        decisions[str(entry["id"])] = asdict(decision)
        write(entry, decision, ctx)

    motor_apply._write_temporal = traced
    try:
        motor_apply.apply_anchor_engine(
            entries, root, str(manifest["course"]["course_name"]), enabled=True, voter=None,
            markdown_fn=lambda e: _entry_markdown_text_for_file_map(root, e) or "")
    finally:
        motor_apply._write_temporal = write
    return ({str(e["id"]): e for e in original}, {str(e["id"]): e for e in entries}, decisions,
            hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest())


def main():
    out = HERE / "replay_bloco_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    compare = load("compare_wk", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    total, courses, divergences, records, manifests = collections.Counter(), {}, [], [], {}
    for sig, name in mede.NOMES.items():
        ref = DATA / ".frzero/pacote_fontes_15-09" / name
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved, replayed, decisions, digest = replay(root)
        manifests[sig] = {"root": str(root), "sha256": digest}
        c = collections.Counter()
        for eid, entry in saved.items():
            pred = replayed[eid]
            iguais = {campo: entry.get(campo) == pred.get(campo) for campo in CAMPOS}
            c["manifest_n"] += 1
            c["id_fiel"] += iguais["temporal_block_id"]
            c["cinco_campos_fiel"] += all(iguais.values())
            for campo, ok in iguais.items():
                c[f"diverge_{campo}"] += not ok
            record = {"curso": sig, "id": eid, "source_path": entry.get("source_path"),
                      "gravado": {campo: entry.get(campo) for campo in CAMPOS},
                      "replay": {campo: pred.get(campo) for campo in CAMPOS},
                      "computed_block_id": entry.get("computed_block_id"),
                      "computed_block_method": entry.get("computed_block_method"),
                      "manual_timeline_block_id": entry.get("manual_timeline_block_id"),
                      "decision_replay": decisions.get(eid)}
            records.append(record)
            if not all(iguais.values()):
                divergences.append({**record, "campos": [k for k, v in iguais.items() if not v],
                                    "local": "src/builder/routing/motor/apply.py:57-122"})
        # Regua: gold so aqui. Casamento baseline->pacote por origem unica; ausentes contam erro.
        ref_entries = {str(e["id"]): e for e in read(ref / "manifest.json")["entries"]}
        source_index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(EVIDENCE / f"herancas_{sig}_15-09.json")["entries"]}
        gold = mede.golds(sig)[0]
        with (EVIDENCE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            if row["bloco"] == "":
                continue
            old = ref_entries.get(mapping.get(row["entry_id"]) or "")
            hits = source_index.get(compare.source(old), []) if old else []
            assert len(hits) <= 1, (sig, row["entry_id"], "origem nao unica")
            c["bloco_n"] += 1
            if not hits:
                c["bloco_ausente"] += 1
                continue
            entry = hits[0]
            truth = gold[row["entry_id"]]
            c["bloco_gravado"] += compare.predictions(root, entry)[0] == truth
            c["bloco_replay"] += compare.predictions(root, replayed[str(entry["id"])])[0] == truth
        courses[sig] = dict(c)
        total.update(c)
        print(sig, dict(c), flush=True)
    checks = {
        "bloco_replay_213_237": total["bloco_replay"] == 213 and total["bloco_n"] == 237,
        "bloco_gravado_213_237": total["bloco_gravado"] == 213 and total["bloco_n"] == 237,
        "ausentes_6": total["bloco_ausente"] == 6,
        "id_fiel_100_porcento": total["id_fiel"] == total["manifest_n"],
        "cinco_campos_fiel_100_porcento": total["cinco_campos_fiel"] == total["manifest_n"],
    }
    report = {"head": "9220a57", "checks": checks, "total": dict(total), "courses": courses,
              "manifests": manifests, "divergences": divergences, "entries": records,
              "scope": "Fase real apply_anchor_engine importada de src/, TEMPORAL_KEYS removidas antes da decisao; voter=None.",
              "inputs": ["manifest (identidade, categoria, datas, source_section, pinos manuais, content_key/md5)",
                         "course/.timeline_index.json (blocos, janelas, card_block_map via build_motor_context)",
                         "Markdown referenciado (_entry_markdown_text_for_file_map)"],
              "limitations": ["Nao mede regra candidata; sem build/rebuild, sem rede, sem LLM.",
                              "Ausentes permanecem no denominador da regua.",
                              "Sidecar de votos nao usado (voter=None) — fiel ao build medido, nao ao build com LLM."]}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOTAL", dict(total))
    print("ASSERTS", checks)
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())
    assert all(checks.values()), "Infidelidade localizada no JSON; nao usar para medir regra candidata."


if __name__ == "__main__":
    main()
