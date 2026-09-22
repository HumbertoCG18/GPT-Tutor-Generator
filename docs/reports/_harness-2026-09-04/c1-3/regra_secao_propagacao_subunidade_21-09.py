"""Abla as duas decisoes CG da regra de secao dentro da fase real."""
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

from src.builder.routing import file_map as LOCAL_FM  # noqa: E402
from src.builder.routing import resolver_apply as LOCAL_RA  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay_with_patch(replay, root, overrides):
    """Monkeypatch apenas a reconciliacao; scorer e restante da fase sao reais."""
    original_auto = replay.auto_unit
    original_reconcile = replay.FM.reconcile_unit_with_block
    current, hit = {}, set()

    def traced_auto(entry, *args, **kwargs):
        match = original_auto(entry, *args, **kwargs)
        current.update(id=str(entry["id"]), slug=str(match.slug or ""), ambiguous=bool(match.ambiguous))
        return match

    def section_wins(**kwargs):
        base = original_reconcile(**kwargs)
        eid = current.pop("id", None)
        target = overrides.get(eid)
        if target is None:
            return base
        assert current.pop("slug") == target["raw_slug"] == target["after"]
        assert current.pop("ambiguous") is False
        assert base[0] == target["before"] and base[0] != target["after"]
        assert not kwargs["block_is_manual"] and not kwargs["has_manual_unit"]
        hit.add(eid)
        block_id, block_unit = kwargs["computed_block_id"], kwargs["block_unit_slug"]
        conflict = ({"unit": target["after"], "block_unit": block_unit, "block_id": block_id}
                    if block_id and block_unit and block_unit != target["after"] else {})
        return target["after"], [f"secao-vence-bloco={block_id}"], conflict

    replay.auto_unit = traced_auto
    replay.FM.reconcile_unit_with_block = section_wins
    try:
        result = replay.replay(root)
    finally:
        replay.auto_unit = original_auto
        replay.FM.reconcile_unit_with_block = original_reconcile
    assert hit == set(overrides), ("overrides nao exercidos", sorted(set(overrides) - hit))
    return result


def main():
    out = HERE / "regra_secao_propagacao_subunidade_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    replay_path = EVIDENCE / "replay_unidade_21-09.py"
    rule_path = EVIDENCE / "regra_secao_unidade_21-09.json"
    replay = load("wg_replay", replay_path)
    compare = load("wg_compare", EVIDENCE / "compara_herancas_15-09.py")
    assert replay.FM is LOCAL_FM and replay.RA is LOCAL_RA

    decisions = json.loads(rule_path.read_text(encoding="utf-8"))["decisions"]
    overrides = {
        str(d["id"]): {
            "before": d["before"],
            "after": d["section_match"]["slug"],
            "raw_slug": d["raw"]["slug"],
        }
        for d in decisions if d["curso"] == "CG" and d["changed"]["R-sem-misto"]
    }
    assert set(overrides) == {
        "maptextures",
        "pagina-com-videos-sobre-mapeamento-de-texturas-07bbe3",
    }
    root = DATA / ".frzero/pacote_fontes_15-09" / compare.mede.NOMES["CG"]
    saved, baseline, raw = replay.replay(root)
    assert all(str(saved[e].get("computed_unit_slug") or "") == str(baseline[e].get("computed_unit_slug") or "") for e in saved)

    runs = {}
    for patched_id in overrides:
        _, patched, patched_raw = replay_with_patch(replay, root, {patched_id: overrides[patched_id]})
        assert raw == patched_raw
        changes = []
        for eid, before in baseline.items():
            after = patched[eid]
            old_sub = str(before.get("computed_subunit_slug") or "")
            new_sub = str(after.get("computed_subunit_slug") or "")
            if old_sub != new_sub:
                changes.append({
                    "manifest_id": eid,
                    "before": old_sub,
                    "after": new_sub,
                    "unit_changed": str(before.get("computed_unit_slug") or "") != str(after.get("computed_unit_slug") or ""),
                    "before_reasons": before.get("subunit_match_reasons") or [],
                    "after_reasons": after.get("subunit_match_reasons") or [],
                })
        runs[patched_id] = {
            "subunit_changes": changes,
            "collateral_subunit_changes": [x for x in changes if not x["unit_changed"]],
        }

    report = {
        "head": "ce02a8f47285c30c16f12b131bdf86c46dcba64e",
        "course": "CG",
        "patches": runs,
        "input_hashes": {str(p): sha256(p) for p in (replay_path, rule_path, root / "manifest.json")},
        "limitations": ["Somente CG; blocos congelados; patch em memoria; sem gold, rede, LLM, build ou escrita em src/."],
    }
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v["collateral_subunit_changes"] for k, v in runs.items()}, ensure_ascii=False, indent=2))
    print("SHA256", sha256(out))


if __name__ == "__main__":
    main()
