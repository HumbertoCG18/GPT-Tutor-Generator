"""Placar consistente (06/09): roda os 3 regimes do motor nas copias com tripwire e tira um SNAPSHOT do manifest de cada
curso por regime, para `placar_100.py` contar, por material, os tres eixos certos ao mesmo tempo.
  regime 'zero'  = motor puro SEM vocab compilado, sem voter, sem curadoria (0 chamadas de LLM em qualquer camada)
  regime 'vocab' = motor puro COM vocab compilado por LLM (1 vez por curso), sem voter, sem curadoria
  regime 'auto'  = vocab + voter com cache do produto, sem curadoria (= tutor novo)
CG: holdout puro e por definicao sem vocab ('zero'); 'auto' pelo motor_auto holdout. Uso: placar_100_runs.py"""
import runpy
import shutil
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
C13 = GEN / "docs/reports/_harness-2026-09-04/c1-3"
SNAP = C13 / "snap_placar"
COPY = GEN / ".ablacao"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (tripwire)")


_gc.GeminiClient.__init__ = _bloqueado
REPOS = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor", "Engenharia-Software-2-Tutor", "TCC-Tutor"]
CG = "Computacao-Grafica-Tutor"


def snap(regime: str, repos: list) -> None:
    d = SNAP / regime
    d.mkdir(parents=True, exist_ok=True)
    for r in repos:
        shutil.copyfile(COPY / r / "manifest.json", d / f"{r}.manifest.json")
        shutil.copyfile(COPY / r / "course/.timeline_index.json", d / f"{r}.timeline.json")
    print(f"[snap] {regime}: {len(repos)} manifests", flush=True)


def run(path: Path, argv: list) -> None:
    sys.argv = [str(path)] + argv
    runpy.run_path(str(path), run_name="__main__")


import motor_puro  # noqa: E402

# auto: as copias JA estao no regime automatico (janela2_auto5 + janela2_auto_holdout): snapshot antes de sobrescrever
snap("auto", REPOS + [CG])
# zero: 5 cursos sem vocab
motor_puro.main([])
snap("zero", REPOS)
# zero: CG holdout puro (sem vocab por definicao)
run(GEN / "docs/reports/_harness-2026-09-02/holdout_cg.py", [str(GEN), str(COPY)])
snap("zero", [CG])
# vocab: 5 cursos com vocab
motor_puro.main(["--com-vocab"])
snap("vocab", REPOS)
print("[fim runs zero+vocab]", flush=True)
