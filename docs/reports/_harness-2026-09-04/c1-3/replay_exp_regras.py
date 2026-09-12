"""Sobre replay_subunidade.py (0 chamadas): duas regras candidatas para filter_terms, medidas antes de tocar produto.
A) ROTULO_REPETIDO: topico cujo rotulo (normalizado) aparece 2+ vezes no curso nao recebe doacao do LLM
   (independente do gold; no SO pega 'estudo de casos' x5 e 'conceitos basicos' x2).
B) SEM_VETO_TITULO: devolve TODOS os termos que filter_terms vetou so pela regra `tn in file_names`.
Uso: python -B replay_exp_regras.py"""
import collections, importlib.util, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
from src.builder.core import vocabulary_compile as vc  # noqa: E402  (rp.load ja fez chdir/sys.path)


def cmp(label, sig, mode, **kw):
    b = rp.evaluate(sig, mode); r = rp.evaluate(sig, mode, **kw)
    print(f"{label:18} {sig:4} {mode:7} {b[:2]} -> {r[:2]}  gain {[k for k in b[2] if not b[2][k] and r[2][k]]}  loss {[k for k in b[2] if b[2][k] and not r[2][k]]}", flush=True)


def rotulo_repetido(tax):
    c = collections.Counter(vc._norm(t["label"]) for u in tax["units"] for t in u["topics"])
    for u in tax["units"]:
        for t in u["topics"]:
            if c[vc._norm(t["label"])] > 1:
                t["aliases"] = [a for a in t["aliases"] if re.match(r"^\d", a)]


def sem_veto_titulo(sig):
    root, entries, tax, _, _ = rp.load(sig)
    vocab = json.loads((Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json").read_text(encoding="utf-8"))
    raw = vocab["_raw"]; generic = vc._generic_tokens(tax); ids = vc.identities_of(tax)
    com = vc.filter_terms(raw, generic=generic, file_names=vc._file_names(entries), identities=ids)
    sem = vc.filter_terms(raw, generic=generic, file_names=set(), identities=ids)
    vetados = {k: [t for t in sem[k] if t not in com.get(k, [])] for k in raw}
    vetados = {k: v for k, v in vetados.items() if v}
    print(f"  vetados so pelo titulo em {sig}: {sum(map(len, vetados.values()))} termos: {vetados}", flush=True)

    def change(t_):
        for u in t_["units"]:
            for t in u["topics"]:
                key = f"{t.get('code', '')} {t['label']}".strip()
                t["aliases"] = list(dict.fromkeys(t["aliases"] + vetados.get(key, [])))
    return change


print("== A) ROTULO_REPETIDO")
for mode in ("sem", "determ", "com"):
    cmp("ROTULO_REPETIDO", "SO", mode, taxmod=rotulo_repetido)
for sig in ("IA", "ES2", "TCC", "MF"):
    cmp("ROTULO_REPETIDO", sig, "determ", taxmod=rotulo_repetido)
print("== B) SEM_VETO_TITULO")
for sig in ("SO", "IA", "ES2", "TCC"):
    tm = sem_veto_titulo(sig)
    for mode in ("determ", "com"):
        cmp("SEM_VETO_TITULO", sig, mode, taxmod=tm)
