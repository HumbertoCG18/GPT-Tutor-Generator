"""Holdout CG (curso do semestre corrente, gold ground_truth_CG.csv scorable=yes): motor puro (sem curadoria,
sem voter, sem vocab) numa COPIA do CG, com o codigo do gerador em GEN. Uso: holdout_cg.py <GEN> <COPY_DIR> [--no-sync]
Roda igual com o worktree antigo (b0b3b42) e com o HEAD: a diferenca e o efeito dos itens 2-5 num curso NAO usado
para afinar as regras."""
import csv, json, os, sys, time
from pathlib import Path
GEN = Path(sys.argv[1]).resolve(); COPY = Path(sys.argv[2]).resolve(); NOSYNC = "--no-sync" in sys.argv
CURADO = "--curado" in sys.argv   # sem ablacao e COM voter (cache de votos da copia): o numero do produto
GH = Path(r"C:\Users\Humberto\Documents\GitHub"); REPO = "Computacao-Grafica-Tutor"
GOLD = GH / "GPT-Tutor-Generator" / "docs" / "reports" / "ground_truth_CG.csv"
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH); os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"; os.environ["TUTOR_REPOS_COPY"] = str(COPY)
import ablacao_rapida as ab  # noqa: E402
import reprocess_assignments as ra  # noqa: E402
from eval_ground_truth import load_predictions  # noqa: E402
ab.ORIG = GH; ab.COPY_DIR = COPY

def _sem_voter(options, profile):
    for k, v in (getattr(profile, "feature_flags", None) or {}).items():
        options[str(k)] = v
    options["use_llm_voter"] = False
if not CURADO:
    ra._merge_profile_flags = _sem_voter

dst = COPY / REPO
t0 = time.time()
if not NOSYNC:
    ab.sync(GH / REPO, dst)
    if not CURADO:
        n = ab.ablate(dst, keep_llm_vocab=False)
        print(f"[nu] CG: {n} pinos zerados", flush=True)
ra.reprocess(dst, [])
print(f"reprocess: {time.time() - t0:.0f}s")
preds = load_predictions(dst)
man = {e["id"]: e for e in json.loads((dst / "manifest.json").read_text(encoding="utf-8"))["entries"]}
ok = n = conf_err = flagged = 0; errs = []
with GOLD.open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r.get("scorable") != "yes": continue
        eid, g = r["id"].strip(), r["true_block_id"].strip(); n += 1
        p = preds.get(eid, {}).get("block_id", ""); e = man.get(eid, {})
        hit = p == g; ok += hit
        flagged += bool(e.get("temporal_block_flag")) or not e.get("temporal_block_id")
        if not hit:
            if e.get("temporal_block_band") == "alta" and not e.get("temporal_block_flag"): conf_err += 1
            errs.append(f"   {eid[:44]:44} pred={p or '-':9} gold={g:9} {e.get('temporal_block_provider')}/{e.get('temporal_block_method')} flag={e.get('temporal_block_flag')} band={e.get('temporal_block_band')}")
print(f"HOLDOUT CG {'CURADO+LLM' if CURADO else 'motor puro'} ({GEN.name} @ {COPY}): bloco {ok}/{n} | conf-err {conf_err} | flagados/sem bloco {flagged} | metodos: "
      + str(__import__('collections').Counter(str(man[r].get('temporal_block_method') or 'SEM') for r in man)))
print("\n".join(errs))
