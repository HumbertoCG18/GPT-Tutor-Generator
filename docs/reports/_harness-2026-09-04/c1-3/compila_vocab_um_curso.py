"""Plano 08/09 item 2.4 com insumo b: compila o vocabulario LLM de UM curso bloqueado por sidecar manual.
Sem --chamar e ensaio a seco (0 chamadas): mostra unidades, cap, tamanho dos bundles e o que os zips passam a contribuir.
Com --chamar: renomeia o sidecar manual para .glossary_curation.professor.json SO durante a compilacao (finally devolve),
conta cada summarize_bundle e ABORTA a chamada seguinte se passar do cap (= unidades com material).
Uso: python compila_vocab_um_curso.py SO [--chamar]
     python compila_vocab_um_curso.py SO --refiltrar   # 0 chamadas: reaplica filter_terms sobre _raw, com backup .bak-11-09"""
import collections, json, os, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from src.builder.core import vocabulary_compile as vc  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402

TUTORES = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
           "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor"}
sig = sys.argv[1]; chamar = "--chamar" in sys.argv
root = REPO.parent / TUTORES[sig]
entries = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
tax = load_internal_content_taxonomy(root)
manual = root / "course" / vc.MANUAL_VOCAB_NAME
prof = root / "course" / ".glossary_curation.professor.json"
llm = root / "course" / vc.LLM_VOCAB_NAME
if "--refiltrar" in sys.argv:
    import shutil
    atual = vc._load(llm); assert atual and isinstance(atual.get("_raw"), dict), "sem _raw para refiltrar"
    antes = {k: list(v["synonyms"]) for k, v in atual.items() if isinstance(v, dict) and "synonyms" in v}
    shutil.copy2(llm, llm.with_name(llm.name + ".bak-11-09"))
    novo = vc._write(llm, root, atual["_raw"], entries, tax, modelo=str(atual.get("_modelo") or ""),
                     erros=list(atual.get("_unidades_com_erro") or []), chamadas=0)
    depois = {k: list(v["synonyms"]) for k, v in novo.items() if isinstance(v, dict) and "synonyms" in v}
    for k in sorted(set(antes) | set(depois)):
        saiu = [t for t in antes.get(k, []) if t not in depois.get(k, [])]; entrou = [t for t in depois.get(k, []) if t not in antes.get(k, [])]
        if saiu or entrou: print(f"  {k}: -{saiu} +{entrou}")
    print(f"{sig}: termos {sum(map(len, antes.values()))} -> {sum(map(len, depois.values()))}; backup {llm.name}.bak-11-09")
    sys.exit(0)
assert not llm.exists(), f"{llm.name} ja existe: este script nao recompila"

mats = [e for e in entries if vc._is_material(e) and str(e.get("category") or "").strip().lower() not in vc.OUT_CATS]
por_unidade = collections.defaultdict(list)
for e in mats:
    u = str(e.get("computed_unit_slug") or "").strip()
    if u: por_unidade[u].append(e)
alvo = [u for u in tax.get("units") or [] if [t for t in (u.get("topics") or []) if t.get("label")] and por_unidade.get(u["slug"])]
cap = len(alvo)
print(f"{sig}: {len(mats)} materiais, {len(por_unidade)} unidades com material, {cap} chamadas previstas (cap)")
for u in alvo:
    labels = [" ".join(str(t["label"]).split()) for t in u["topics"] if t.get("label")]
    b = vc._bundle(tax, u, labels, por_unidade[u["slug"]], root)
    zips = [e for e in por_unidade[u["slug"]] if e.get("file_type") == "zip"]
    membros = sum(len(e.get("extracted_files") or []) for e in zips)
    print(f"  {u['slug']:32} mats {len(por_unidade[u['slug']]):3}  zips {len(zips)}  membros {membros:3}  bundle {len(b):5} chars")
if not chamar:
    print("ensaio a seco: 0 chamadas. Para compilar: --chamar"); sys.exit(0)

from src.builder.runtime.gemini_client import get_gemini_client  # noqa: E402
cfg = json.loads((Path.home() / ".gpt_tutor_config.json").read_text(encoding="utf-8"))
client = get_gemini_client(cfg)
assert client is not None, "sem client Gemini (chave?)"

class Contado:
    def __init__(self, inner): self.inner, self.n = inner, 0
    def __getattr__(self, k): return getattr(self.inner, k)
    def summarize_bundle(self, **kw):
        if self.n >= cap: raise RuntimeError(f"cap {cap} atingido: chamada {self.n + 1} abortada")
        self.n += 1
        print(f"  chamada {self.n}/{cap}", flush=True)
        return self.inner.summarize_bundle(**kw)

assert manual.exists() and not prof.exists(), "sidecar manual ausente ou .professor.json ja existe"
manual.rename(prof)
c = Contado(client)
try:
    out = vc.compile_course_vocabulary(root, entries, tax, c)
finally:
    prof.rename(manual)
print(f"chamadas feitas: {c.n}/{cap}; modelo {getattr(client, 'model', '?')}; sidecar manual devolvido: {manual.exists()}")
if out:
    topicos = {k: v["synonyms"] for k, v in out.items() if isinstance(v, dict) and v.get("synonyms")}
    print(f"gravado {llm.name}: {len(topicos)} topicos com termos, {sum(len(v) for v in topicos.values())} termos, erros: {out.get('_unidades_com_erro', [])}")
    for k, v in topicos.items(): print(f"  {k}: {v}")
