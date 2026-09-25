"""W-AB, conferência da implementação do M1 em src (24/09): replay real sem patch deve ser igual, por ID, ao braço M1
congelado em .frzero/wab_captura_bracos_24-09.json (bloco, unidade, subunidade, em todos os materiais dos 7 cursos).
Sem gold, build, rede, LLM ou commit. Uso: python wab_verifica_m1_src_24-09.py
"""
import collections
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(DATA))
OUT = HERE / "wab_verifica_m1_src_24-09.json"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    wab = load("wabv", HERE / "wab_unidade_fallback_fronteiras_24-09.py")
    compare = load("wabv_cmp", HERE / "compara_herancas_15-09.py")
    rb = load("wabv_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wabv_ru", HERE / "replay_unidade_21-09.py")
    wz = load("wabv_wz", HERE / "wz_bloco_cobertura_22-09.py")
    nomes = compare.mede.NOMES
    raizes = {s: wz.root_de(s, nomes) for s in nomes}
    cap = json.loads(wab.CAP_WAB.read_text(encoding="utf-8"))
    atual = wab.rodar("base_atual", raizes, rb, ru, compare, {})  # sem patch: src com o M1
    c, difs = collections.Counter(), []
    for sig in nomes:
        for eid, r in cap["M1"][sig].items():
            if eid == "__saved__":
                continue
            a = atual[sig].get(eid) or {}
            for eixo in ("bloco", "unidade", "sub"):
                if a.get(eixo) == r[eixo]:
                    c[f"{eixo}_igual"] += 1
                else:
                    c[f"{eixo}_diverge"] += 1
                    difs.append({"curso": sig, "material": eid, "eixo": eixo, "m1": r[eixo], "src": a.get(eixo)})
    razao = sum(1 for sig in nomes for eid, a in atual[sig].items()
                if eid != "__saved__" and any(str(x).startswith("texto-vence-fallback=") for x in a["razoes_unidade"]))
    out = {"escopo": __doc__, "captura_wab_sha256": cap["sha256_bracos"], "contagens": dict(c), "divergencias": difs,
           "materiais_com_razao_texto_vence_fallback": razao, "identico": not difs}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("contagens", "materiais_com_razao_texto_vence_fallback", "identico")}),
          hashlib.sha256(OUT.read_bytes()).hexdigest()[:16])


if __name__ == "__main__":
    main()
