"""Alavancas do CG no replay (0 chamadas), produtor deterministico do PRODUTO (code_summarization.synthesize_code_entry):
  base = como esta em producao
  L1   = labels dos topicos entram no conjunto de aliases (hoje so aliases + sinonimos do vocab LLM)
  L2   = alias sem espaco igual a uma PARTE CamelCase de identificador do codigo (desenhaBezier -> Bezier)
  L3   = zip com .md proprio tambem sintetiza a partir dos membros (hoje devolve None)
Regua: 5 cursos (151) + CG (82). Uso: python -B replay_exp_cg.py"""
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES["CG"] = "Computacao-Grafica-Tutor"
from src.builder.core import code_summarization as cs  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG"]
from src.builder.core.vocabulary_compile import _norm  # noqa: E402
META_CG = {"conceitos", "areas relacionadas"}


def meta_cg(tax):
    """M1: rotulo meta do CG ("1.2 Conceitos" recebia OpenGL/OpenGL 3D do LLM; "1.3 Areas relacionadas" recebia Manipulacao de
    Imagens/Morfologia) nao recebe doacao: fica so o alias com codigo. Mesma regra de META_LABELS ja medida no SO."""
    for u in tax["units"]:
        for t in u["topics"]:
            if _norm(t["label"]) in META_CG:
                t["aliases"] = [a for a in t["aliases"] if re.match(r"^\d", a)]



def aliases_de(root: Path, labels: bool) -> set:
    als = set(cs.course_aliases(root))
    if labels:
        for u in load_internal_content_taxonomy(root).get("units", []):
            for t in u.get("topics", []):
                lab = " ".join(str(t.get("label") or "").split())
                if len(lab) >= 4:
                    als.add(lab)
    return als


def synth_factory(sig: str, labels=False, camel=False, zip_md=False):
    als = aliases_de(Path(".ablacao") / rp.NAMES[sig], labels)

    def synth(e, root):
        e2 = dict(e)
        if zip_md and e.get("file_type") == "zip" and e.get("base_markdown"):
            e2["base_markdown"] = None
        s = cs.synthesize_code_entry(e2, root, als)
        if s is None:
            return {}
        if camel:
            raw = " ".join(md for _, md in cs._bundle_md(e2, root))
            parts = {p.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_]*", raw) for p in cs._CAMEL.split(w) if len(p) >= 4}
            hits = sorted(a for a in als if " " not in a and a.lower() in parts and a not in s["concepts"])
            s = dict(s, concepts=s["concepts"] + hits)
        return {"summary": s}
    return synth


CONFIGS = [("base", {}), ("L1 labels", {"labels": True}), ("L2 camel", {"camel": True}), ("L3 zip-md", {"zip_md": True}),
           ("M1 meta", {"meta": True}), ("M1+L2", {"meta": True, "camel": True}), ("M1+L2+L3", {"meta": True, "camel": True, "zip_md": True})]
tot = {n: [0, 0] for n, _ in CONFIGS}
for sig in CURSOS:
    base = rp.evaluate(sig, "determ", synth=synth_factory(sig))
    linha = f"{sig:4} base {base[0]:3}/{sum(1 for _ in base[2]):<3}"
    tot["base"][0] += base[0]; tot["base"][1] += base[1]
    for nome, kw in CONFIGS[1:]:
        kw = dict(kw); meta = kw.pop("meta", False)
        r = rp.evaluate(sig, "determ", synth=synth_factory(sig, **kw), taxmod=meta_cg if meta else None)
        tot[nome][0] += r[0]; tot[nome][1] += r[1]
        g = [k for k in base[2] if not base[2][k] and r[2][k]]; l = [k for k in base[2] if base[2][k] and not r[2][k]]
        linha += f" | {nome} {r[0]:3} (+{len(g)} -{len(l)})"
        if g or l:
            print(f"    {sig} {nome}: gain {g} loss {l}", flush=True)
    print(linha, flush=True)
print("\nTOTAL 6 cursos (com-extras, primario):", {n: tuple(v) for n, v in tot.items()})
