"""Medicao B (C1 item 3): motor puro (+vocab) nos 5 e holdout CG com title := moodle_label na copia .ablacao.
Uso: shim_b.py {antes|title} {puro|holdout}"""
import sys, json, runpy
from pathlib import Path
GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MODE, TARGET = sys.argv[1], sys.argv[2]
import ablacao_rapida as ab
_ablate = ab.ablate
def ablate(repo, keep_llm_vocab=False):
    n = _ablate(repo, keep_llm_vocab)
    if MODE == "title":
        p = Path(repo) / "manifest.json"; m = json.loads(p.read_text(encoding="utf-8")); k = 0
        for e in m["entries"]:
            ml = e.get("moodle_label"); ml = (ml.get("text", "") if isinstance(ml, dict) else str(ml or "")).strip()
            if ml and ml != str(e.get("title") or ""):
                e["title"] = ml; k += 1
        p.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [title:=label] {Path(repo).name}: {k} titles reescritos", flush=True)
    return n
ab.ablate = ablate
if TARGET == "puro":
    import motor_puro
    sys.exit(motor_puro.main(["--com-vocab"]))
else:
    sys.argv = [str(GEN / "docs/reports/_harness-2026-09-02/holdout_cg.py"), str(GEN), str(GEN / ".ablacao")]
    runpy.run_path(sys.argv[0], run_name="__main__")
