"""Ataque a subunidade (12/09, user: "vamos atacar a precisao do confiante e a subunidade no produto"): experimentos de
CURADORIA por topico (aliases no sidecar manual, 0 codigo de motor) medidos no replay com as copias `.ablacao/` sincronizadas
com o produto (new=False) e o produtor deterministico do produto. Cada experimento: ganhos e perdas por material nos 7 cursos.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/replay_exp_curadoria_12-09.py"""
import collections
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core import code_summarization as cs  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
# experimento -> {(sigla, slug do topico): [aliases novos]}
EXP = {
    "E1 CG 4.1 mapeamento": {("CG", "sistema-de-coordenadas-cartesianas"): ["Mapeamento", "Window e Viewport", "Janela de Seleção e Janela de Exibição"]},
    "E2 CG 6.2 camera": {("CG", "conceito-de-camera-sintetica"): ["gluLookAt", "ModelView", "posição do observador", "câmera"]},
    "E3 CG 6.1 pipeline": {("CG", "pipeline-de-visualizacao-3d"): ["Visualização 3D", "pipeline"]},
    "E4 CG 7.1.1 curvas": {("CG", "representacao-de-curvas-parametricas"): ["Curvas Paramétricas", "curvas"],
                           ("CG", "catmull-rom"): ["Catmull-Rom"], ("CG", "bezier-e-algoritmo-de-casteljau"): ["Bézier", "Casteljau"]},
    "E5 ES2 1.5 estudo de caso": {("ES2", "estudo-de-caso-arquitetura-orientada-a-microsservicos"): ["Estudo de caso", "microsservicos", "gateway"]},
    "E6 MF 1.3.3 provadores": {("MF", "provadores-de-teoremas"): ["Isabelle/HOL", "Archive of Formal Proofs", "provador", "theory"]},
    "E1+E2+E3+E4": {("CG", "sistema-de-coordenadas-cartesianas"): ["Mapeamento", "Window e Viewport", "Janela de Seleção e Janela de Exibição"],
                    ("CG", "conceito-de-camera-sintetica"): ["gluLookAt", "ModelView", "posição do observador", "câmera"],
                    ("CG", "pipeline-de-visualizacao-3d"): ["Visualização 3D", "pipeline"],
                    ("CG", "representacao-de-curvas-parametricas"): ["Curvas Paramétricas", "curvas"],
                    ("CG", "catmull-rom"): ["Catmull-Rom"], ("CG", "bezier-e-algoritmo-de-casteljau"): ["Bézier", "Casteljau"]},
}


def taxmod(sig, extras):
    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                if (sig, t["slug"]) in extras:
                    t["aliases"] = list(dict.fromkeys(t.get("aliases", []) + extras[(sig, t["slug"])]))
    return change


def synth_produto(sig):
    als = set(cs.course_aliases(Path(".ablacao") / rp.NAMES[sig]))

    def synth(e, root):
        s = cs.synthesize_code_entry(e, root, als)
        return {"summary": s} if s else {}
    return synth


MODE = "com"  # resumos do code_curation.json do produto (determ-v3 gravado): replay = produto
base = {}
for sig in CURSOS:
    base[sig] = rp.evaluate(sig, MODE, new=False, synth=synth_produto(sig))
print("base (replay = produto):", {s: f"{base[s][0]}/{len(base[s][2])}" for s in CURSOS}, "total", sum(base[s][0] for s in CURSOS))
for nome, extras in EXP.items():
    cursos = sorted({s for s, _ in extras})
    tot = collections.Counter()
    for sig in cursos:
        r = rp.evaluate(sig, MODE, new=False, synth=synth_produto(sig), taxmod=taxmod(sig, extras))
        b = base[sig]
        g = [k for k in b[2] if not b[2][k] and r[2][k]]
        l = [k for k in b[2] if b[2][k] and not r[2][k]]
        tot["g"] += len(g); tot["l"] += len(l)
        print(f"  {nome:26} {sig:4} {b[0]:3} -> {r[0]:3}  gain {[k[:36] for k in g]}  loss {[k[:36] for k in l]}", flush=True)
    print(f"{nome:28} liquido {tot['g'] - tot['l']:+d} (ganha {tot['g']}, perde {tot['l']})", flush=True)
