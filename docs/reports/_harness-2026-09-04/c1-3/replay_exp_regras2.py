"""Parte 2 (0 chamadas): duas formas de 'rotulo meta' que separam 'estudo de casos' x5 de 'conceitos basicos' x2 no SO,
e o candidato final (rotulo meta + sem veto de titulo) nos 5 cursos x 3 regimes.
C) META_LEXICO: rotulo normalizado igual a um item de um lexico curto (rotulo sem sujeito).
D) REPETIDO_3: rotulo que aparece 3+ vezes no curso.
Uso: python -B replay_exp_regras2.py"""
import collections, importlib.util, json, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
from src.builder.core import vocabulary_compile as vc  # noqa: E402

META = {"estudo de casos", "estudo de caso", "estudos de caso", "introducao", "conceitos", "areas relacionadas",
        "revisao", "exercicios", "referencias", "bibliografia", "conclusao", "consideracoes finais"}


def cmp(label, sig, mode, **kw):
    b = rp.evaluate(sig, mode); r = rp.evaluate(sig, mode, **kw)
    print(f"{label:16} {sig:4} {mode:7} {b[:2]} -> {r[:2]}  gain {[k for k in b[2] if not b[2][k] and r[2][k]]}  loss {[k for k in b[2] if b[2][k] and not r[2][k]]}", flush=True)
    return r[:2]


def _strip(t): t["aliases"] = [a for a in t["aliases"] if re.match(r"^\d", a)]


def meta_lexico(tax):
    for u in tax["units"]:
        for t in u["topics"]:
            if vc._norm(t["label"]) in META: _strip(t)


def repetido_3(tax):
    c = collections.Counter(vc._norm(t["label"]) for u in tax["units"] for t in u["topics"])
    for u in tax["units"]:
        for t in u["topics"]:
            if c[vc._norm(t["label"])] >= 3: _strip(t)


def sem_veto_titulo(sig):
    root, entries, tax, _, _ = rp.load(sig)
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    if not p.exists() or sig == "MF": return lambda t_: None
    raw = json.loads(p.read_text(encoding="utf-8"))["_raw"]; generic = vc._generic_tokens(tax); ids = vc.identities_of(tax)
    com = vc.filter_terms(raw, generic=generic, file_names=vc._file_names(entries), identities=ids)
    sem = vc.filter_terms(raw, generic=generic, file_names=set(), identities=ids)
    vet = {k: [t for t in sem[k] if t not in com.get(k, [])] for k in raw}
    def change(t_):
        for u in t_["units"]:
            for t in u["topics"]:
                key = f"{t.get('code', '')} {t['label']}".strip()
                t["aliases"] = list(dict.fromkeys(t["aliases"] + vet.get(key, [])))
    return change


def candidato(sig):
    sv = sem_veto_titulo(sig)
    def change(tax): meta_lexico(tax); sv(tax)
    return change


print("== C) META_LEXICO e D) REPETIDO_3 no SO, 3 regimes")
for mode in ("sem", "determ", "com"):
    cmp("META_LEXICO", "SO", mode, taxmod=meta_lexico)
    cmp("REPETIDO_3", "SO", mode, taxmod=repetido_3)
print("== C) nos outros cursos (determ)")
for sig in ("IA", "ES2", "TCC", "MF"):
    cmp("META_LEXICO", sig, "determ", taxmod=meta_lexico)
print("== CANDIDATO = META_LEXICO + SEM_VETO_TITULO, 5 cursos x 3 regimes")
tot = {m: [0, 0] for m in ("sem", "determ", "com")}
for sig in ("MF", "SO", "IA", "ES2", "TCC"):
    for mode in ("sem", "determ", "com"):
        r = cmp("CANDIDATO", sig, mode, taxmod=candidato(sig)); tot[mode][0] += r[0]; tot[mode][1] += r[1]
print("TOTAL candidato (com-extras, primario) /151 no replay:", tot, "| base replay: sem 123, determ 125, com 129")
