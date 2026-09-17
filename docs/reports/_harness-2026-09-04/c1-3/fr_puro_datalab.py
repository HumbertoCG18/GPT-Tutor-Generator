"""FR sem gold, run C3 (12/09, user: "uma usando o datalab mas sem LLM"), a custo ZERO: o motor pontua `base_markdown` (ordem em
`navigation._entry_markdown_path_for_file_map`: approved > curated > base > advanced), entao o Datalab que o produto ja pagou
(`advanced_markdown` nos 15 PDFs) nunca entrou na atribuicao. Aqui: copia o sandbox da run A, copia os .md do Datalab do produto e
aponta `base_markdown` para eles, reprocessa SEM voter, sem compilar vocab, Gemini bloqueado. `--vocab` acrescenta o vocab LLM do
cache (regime "Datalab + vocab, sem voter"). Isola extracao (pymupdf4llm x Datalab) de vocabulario.
Uso: python -B .../fr_puro_datalab.py [--vocab]"""
import collections
import json
import os
import shutil
import sys
import time
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.utils.helpers  # noqa: F401,E402  (.env)
from src.builder.runtime import gemini_client  # noqa: E402
from src.models.core import SubjectStore  # noqa: E402
import reprocess_assignments as ra  # noqa: E402

VIVO = "--llm-vivo" in sys.argv  # run 3 de verdade: voter VOTA ao vivo (o cache do produto nao serve: blocos do zero tem outros uuids)
VOCAB = "--vocab" in sys.argv or "--llm" in sys.argv or VIVO
VOTER = "--llm" in sys.argv or VIVO  # "Datalab + LLM": vocab do cache + voter
SRC = GEN / ".ablacao" / "FR-rebuild" / "Fundamentos-de-Redes-Tutor"
DST = GEN / ".ablacao" / ("FR-rebuild-C3-llm-vivo" if VIVO else "FR-rebuild-C3-llm" if VOTER else "FR-rebuild-C3-vocab" if VOCAB else "FR-rebuild-C3") / "Fundamentos-de-Redes-Tutor"
PROD = GH / "Fundamentos-de-Redes-Tutor"
calls = collections.Counter()


def _bloqueado(*a, **k):
    calls["gemini_bloqueado"] += 1
    raise RuntimeError("Gemini bloqueado (tripwire)")


if VIVO:
    _real_summarize = gemini_client.GeminiClient.summarize_bundle

    def _summarize_contado(self, *a, **k):
        calls["gemini_chamadas"] += 1
        return _real_summarize(self, *a, **k)

    gemini_client.GeminiClient.summarize_bundle = _summarize_contado  # so o voter chega aqui (vocab e resumos ficam desligados)
else:
    gemini_client.get_gemini_client = lambda config=None: None
    gemini_client.GeminiClient.__init__ = _bloqueado
_orig_merge = ra._merge_profile_flags


def _sem_voter(options, profile):
    _orig_merge(options, profile)
    options["use_llm_voter"] = VOTER  # voter so com --llm, e so pelo cache: qualquer voto novo bate no tripwire e e contado


ra._merge_profile_flags = _sem_voter

if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
prod = {e["id"]: e for e in json.loads((PROD / "manifest.json").read_text(encoding="utf-8"))["entries"]}
man = json.loads((DST / "manifest.json").read_text(encoding="utf-8"))
trocados = 0
for e in man["entries"]:
    p = prod.get(e["id"])
    adv = p.get("advanced_markdown") if p else None
    if not adv or not (PROD / adv).exists():
        continue
    (DST / adv).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(PROD / adv, DST / adv)
    e["advanced_markdown"] = adv
    e["base_markdown"] = adv  # o scorer le base_markdown: aqui ele passa a ler o Datalab
    e["base_backend"] = "datalab"
    trocados += 1
(DST / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
if VOCAB:
    shutil.copy(PROD / "course" / ".glossary_curation.llm.json", DST / "course" / ".glossary_curation.llm.json")
if VOTER and (PROD / "material_curation.json").exists():
    shutil.copy(PROD / "material_curation.json", DST / "material_curation.json")
print(f"[copia] {DST.parent.name}: {trocados} materiais com texto do Datalab como base"
      f"{' + vocab LLM do cache' if VOCAB else ''}{' + cache de votos do produto (voter ligado)' if VOTER else ''}")
store = SubjectStore()
sp = next(store.get(n) for n in store.names() if getattr(store.get(n), "slug", "") == "fundamentos-de-redes-de-computadores")
store.find_by_repo_root = lambda root: sp
t0 = time.time()
ra.reprocess(DST, [], store=store)
print(f"[reprocess] {time.time() - t0:.0f}s · chamadas Gemini bloqueadas: {dict(calls) or 0}")
