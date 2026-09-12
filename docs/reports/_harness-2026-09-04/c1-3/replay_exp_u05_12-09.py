"""12/09: (a) E5 do ES2 em variantes (so 'gateway'; so 'Estudo de caso'), para separar sinonimo real de ajuste ao gold;
(b) E7: o maior aglomerado de erros de subunidade do CG e u04 (9 materiais: transformacoes/instanciamento com gold vazio,
mapeamento com gold sistema-de-coordenadas). O plano tem esses assuntos em u05 (5.1 Transformacoes, 5.2 Mapeamento window/
viewport, 5.3 Pipeline 2D), mas o ruling de 06/09 poe os blocos em u04 e a subunidade so procura dentro da unidade computada.
Mede o que o motor daria se os topicos de u05 fossem candidatos para materiais de u04 (taxonomia com u05 anexada a u04).
Replay com copias sincronizadas (new=False), modo com. 0 chamadas. Uso: python -B .../replay_exp_u05_12-09.py"""
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")

U04 = ["animacao-v2", "instanciamento", "pagina-com-videos-sobre-instanciamento", "transformacoesgeometricas", "transformacoesgl",
       "exercicios-teoricos-sobre-processo-de-visualizacao-2d", "exercicios-teoricos-sobre-processo-de-visualizacao-2d-html",
       "pagina-com-videos-sobre-mapeamento-9f410e", "video-sobre-mapeamento-em-opengl-1dad3c", "mapeamento", "vis2d", "recorte"]


def add_aliases(sig_slug_aliases):
    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                if t["slug"] in sig_slug_aliases:
                    t["aliases"] = list(dict.fromkeys(t.get("aliases", []) + sig_slug_aliases[t["slug"]]))
    return change


def u05_visivel_em_u04(tax):
    u4 = next(u for u in tax["units"] if u["slug"].startswith("unidade-04"))
    u5 = next(u for u in tax["units"] if u["slug"].startswith("unidade-05"))
    for t in u5["topics"]:
        t2 = copy.deepcopy(t)
        t2["unit_slug"] = u4["slug"]
        u4["topics"].append(t2)


def cmp(sig, rot, taxmod):
    b = rp.evaluate(sig, "com", new=False)
    r = rp.evaluate(sig, "com", new=False, taxmod=taxmod)
    g = [k for k in b[2] if not b[2][k] and r[2][k]]
    l = [k for k in b[2] if b[2][k] and not r[2][k]]
    print(f"  {rot:44} {sig:4} {b[0]:3} -> {r[0]:3}  gain {[k[:34] for k in g]}  loss {[k[:34] for k in l]}", flush=True)
    return b, r


print("== E5 ES2 em variantes")
cmp("ES2", "so 'gateway' em 1.5", add_aliases({"estudo-de-caso-arquitetura-orientada-a-microsservicos": ["gateway"]}))
cmp("ES2", "so 'Estudo de caso' em 1.5", add_aliases({"estudo-de-caso-arquitetura-orientada-a-microsservicos": ["Estudo de caso"]}))
cmp("ES2", "'gateway' + 'Estudo de caso'", add_aliases({"estudo-de-caso-arquitetura-orientada-a-microsservicos": ["gateway", "Estudo de caso"]}))
print("== E7 CG: topicos de u05 visiveis para materiais de u04 (gold atual conta u05 como erro; o que importa e para onde vao)")
b, r = cmp("CG", "u05 anexada a u04", u05_visivel_em_u04)
for k in U04:
    kk = next((i for i in r[3] if i == k or i.startswith(k)), None)
    if kk:
        print(f"    {kk[:46]:46} hoje={(b[3].get(kk) or '(vazio)')[:30]:30} com u05={(r[3].get(kk) or '(vazio)')[:34]:34} gold_ok hoje={b[2].get(kk)} com u05={r[2].get(kk)}")
