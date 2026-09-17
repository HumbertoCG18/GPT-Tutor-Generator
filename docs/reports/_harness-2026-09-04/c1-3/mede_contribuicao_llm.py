"""Quanto dos acertos de subunidade do PRODUTO (214/251 em 11/09) vem das duas camadas LLM que sobraram?
Tres regimes nos 8 tutores, em copias (.ablacao/), rota do produto (reprocess_assignments), 0 chamadas (tripwire):
  produto        = tutor como esta (vocab LLM + sidecar do professor + voter em cache + resumo deterministico)
  sem_vocab_llm  = idem sem `course/.glossary_curation.llm.json` (sobra o sidecar manual/professor onde existe)
  sem_llm        = idem sem vocab LLM e sem voter (use_llm_voter=False) = motor deterministico de ponta a ponta
Score contra docs/reports/subunit_gt_<SIGLA>.csv (scorable=yes), 7 cursos com gold, base 251.
Uso: python mede_contribuicao_llm.py [produto|sem_vocab_llm|sem_llm ...]"""
import os
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
COPY = GEN / ".ablacao"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
os.environ["TUTOR_REPOS_ORIG"] = str(GH)

import src.builder.runtime.gemini_client as _gc  # noqa: E402

BLOQUEADAS = []
for _n, _v in list(vars(_gc.GeminiClient).items()):
    if callable(_v) and not _n.startswith("_"):
        def _bloq(self, *a, __n=_n, **k):
            BLOQUEADAS.append(__n)
            raise RuntimeError(f"Gemini bloqueado: {__n}")
        setattr(_gc.GeminiClient, _n, _bloq)

import ablacao_rapida as ab  # noqa: E402
import reprocess_assignments as ra  # noqa: E402

TUTORES = {"CG": "Computacao-Grafica-Tutor", "ES2": "Engenharia-Software-2-Tutor", "FR": "Fundamentos-de-Redes-Tutor",
           "IA": "Inteligencia-Artifical-Tutor", "LR": "Laboratorio-de-Redes-Tutor", "MF": "Metodos-Formais-Tutor",
           "SO": "Sistemas-Operacionais-Tutor", "TCC": "TCC-Tutor"}
GOLD = {s: r for s, r in TUTORES.items() if (GEN / "docs" / "reports" / f"subunit_gt_{s}.csv").exists()}
_merge_orig = ra._merge_profile_flags


def _merge_sem_voter(options, profile):
    _merge_orig(options, profile)
    options["use_llm_voter"] = False


def roda(regime: str) -> dict:
    ra._merge_profile_flags = _merge_sem_voter if regime == "sem_llm" else _merge_orig
    t0 = time.time()
    for sig, repo in TUTORES.items():
        dst = COPY / repo
        (dst / "material_curation.json").unlink(missing_ok=True)   # cache de votos vem fresco do tutor
        ab.sync(GH / repo, dst)
        if regime != "produto":
            (dst / "course" / ".glossary_curation.llm.json").unlink(missing_ok=True)
        ra.reprocess(dst, [])
    res = {}
    for sig, repo in GOLD.items():
        ok, n, prim = ab.score_subunit(COPY, {sig: repo}, GEN)
        res[sig] = (ok, n, prim)
    tot = (sum(v[0] for v in res.values()), sum(v[1] for v in res.values()), sum(v[2] for v in res.values()))
    print(f"[{regime}] {time.time() - t0:.0f}s · " + " · ".join(f"{s} {v[0]}/{v[1]}" for s, v in res.items())
          + f" · TOTAL {tot[0]}/{tot[1]} (primario {tot[2]}) · chamadas bloqueadas ate aqui {len(BLOQUEADAS)}", flush=True)
    return res


regimes = sys.argv[1:] or ["produto", "sem_vocab_llm", "sem_llm"]
out = {r: roda(r) for r in regimes}
if len(out) > 1:
    print("\nresumo (subunidade, base 251):")
    for r, res in out.items():
        print(f"  {r:14} {sum(v[0] for v in res.values())}")
