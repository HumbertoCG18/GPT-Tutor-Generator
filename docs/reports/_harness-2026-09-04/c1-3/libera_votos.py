"""Libera os votos do voter que o rollout_camada3.py bloqueou (11/09): reprocessa CG, FR e IA pela rota do produto com o
Gemini LIBERADO so para o voter, contando cada chamada (cap do voter = 20 por rodada, `llm_vote.DEFAULT_CAP`).
Vocabulario continua sem compilar (TUTOR_NO_VOCAB_COMPILE=1); resumo de codigo e deterministico. Esperado: CG 6, FR 3, IA 1.
Uso: python libera_votos.py CG FR IA"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"

import src.builder.runtime.gemini_client as _gc  # noqa: E402

CHAMADAS = []
_orig = _gc.GeminiClient.summarize_bundle


def _contado(self, *a, **k):
    CHAMADAS.append(time.time())
    return _orig(self, *a, **k)


_gc.GeminiClient.summarize_bundle = _contado
for _n, _v in list(vars(_gc.GeminiClient).items()):   # qualquer outro metodo publico continua bloqueado
    if callable(_v) and not _n.startswith("_") and _n != "summarize_bundle":
        def _bloq(self, *a, __n=_n, **k):
            raise RuntimeError(f"Gemini bloqueado: {__n}")
        setattr(_gc.GeminiClient, _n, _bloq)

import reprocess_assignments as ra  # noqa: E402

TUTORES = {"CG": "Computacao-Grafica-Tutor", "FR": "Fundamentos-de-Redes-Tutor", "IA": "Inteligencia-Artifical-Tutor",
           "ES2": "Engenharia-Software-2-Tutor", "LR": "Laboratorio-de-Redes-Tutor", "MF": "Metodos-Formais-Tutor",
           "SO": "Sistemas-Operacionais-Tutor", "TCC": "TCC-Tutor"}


def blocos(repo: Path) -> dict:
    return {e["id"]: e.get("computed_block_id") for e in json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}


for sig in sys.argv[1:]:
    repo = GH / TUTORES[sig]
    antes, n0 = blocos(repo), len(CHAMADAS)
    ra.reprocess(repo, [])
    depois = blocos(repo)
    mudou = [k for k in depois if antes.get(k) != depois.get(k)]
    print(f"[{sig}] chamadas do voter: {len(CHAMADAS) - n0} · blocos que mudaram: {len(mudou)} {mudou[:8]}", flush=True)
print(f"total de chamadas: {len(CHAMADAS)}")
