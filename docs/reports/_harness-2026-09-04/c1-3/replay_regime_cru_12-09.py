"""Partida para 'melhorar o cru' (12/09, user): regua dos 7 cursos (251) no replay sincronizado com o produto (modo com, new=False),
em tres regimes de taxonomia: produto (aliases como estao: codigo + plano + manual + LLM) · SEM LLM (tira os sinonimos que vieram do
`course/.glossary_curation.llm.json`: cru + curadoria humana) · SO CODIGO (fica so o alias com codigo de outline: o mais cru possivel).
Imprime acerto aceito e primario por curso e a lista de erros do regime SEM LLM (o insumo do diagnostico). 0 chamadas.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/replay_regime_cru_12-09.py"""
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]


def llm_norms(sig):
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    if not p.exists():
        return set()
    d = json.loads(p.read_text(encoding="utf-8"))
    return {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}


def sem_llm(sig):
    vet = llm_norms(sig)

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in vet]
    return change


def so_codigo(tax):
    for u in tax["units"]:
        for t in u["topics"]:
            t["aliases"] = [a for a in t.get("aliases", []) if re.match(r"^\d", a)]


tot = {}
erros = []
for sig in CURSOS:
    b = rp.evaluate(sig, "com", new=False)
    s = rp.evaluate(sig, "com", new=False, taxmod=sem_llm(sig))
    c = rp.evaluate(sig, "com", new=False, taxmod=so_codigo)
    n = len(b[2])
    for k, r in (("produto", b), ("sem_llm", s), ("so_codigo", c)):
        tot.setdefault(k, [0, 0, 0]); tot[k][0] += r[0]; tot[k][1] += r[1]; tot[k][2] += n
    print(f"{sig:4} n={n:3} produto {b[0]:3} ({b[1]:3} prim) · sem LLM {s[0]:3} ({s[1]:3} prim) · so codigo {c[0]:3} ({c[1]:3} prim)", flush=True)
    for k in b[2]:
        if not s[2][k]:
            erros.append((sig, k, s[3].get(k) or "(vazio)", b[3].get(k) or "(vazio)", b[2][k]))
print("TOTAL /251:", {k: f"{v[0]} aceito · {v[1]} prim" for k, v in tot.items()})
print(f"== erros do regime SEM LLM: {len(erros)} (produto certo em {sum(1 for e in erros if e[4])} deles)")
print(f"{'curso':4} {'material':46} {'sem LLM':30} {'produto':30} produto_ok")
for sig, k, pred, prod, ok in erros:
    print(f"{sig:4} {k[:46]:46} {pred[:30]:30} {prod[:30]:30} {ok}")
