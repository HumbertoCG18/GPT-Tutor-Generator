"""Prova dinamica do achado 2 da revisao job-33 (05/10): durante o replay do braco P1adjH do wy3, alguma leitura de
course/.timeline_index.json chega ao disco por fora da injecao (MCTX.load_repo_artifact / ru.read)?
Reusa o wy3 sem altera-lo (mesmas funcoes; sha conferido), envolve io.open/builtins.open so durante o replay e registra
cada abertura do indice com o primeiro chamador fora de io/pathlib/json. Esperado: so o comparador
(compara_herancas_15-09.predictions, uuid -> id com uuid alinhado). Confere tambem que as decisoes reproduzem o
congelado da v3 (a2c84ae2). Sem gold, rede, LLM ou escrita fora da saida.
Uso: python -B wy3_prova_leitores_05-10.py --worktree <raiz com o src da dev>
"""
import builtins
import collections
import hashlib
import importlib.util
import io
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "wy3_prova_leitores_05-10.json"
WY3 = HERE / "wy3_kind_por_linha_05-10.py"
assert hashlib.sha256(WY3.read_bytes()).hexdigest().startswith("e72ab113"), "wy3 mudou"
spec = importlib.util.spec_from_file_location("wy3", WY3)
V3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V3)                      # le --worktree de sys.argv; main() nao roda (nome != __main__)
V3.W.PERMITIDOS.add(OUT.resolve())

LEITURAS = []
ORIG_OPEN = io.open


def chamador():
    for f in reversed(traceback.extract_stack()[:-2]):
        if not any(x in f.filename for x in ("pathlib", "\\json\\", "/json/", "wy3_prova_leitores")):
            return f"{Path(f.filename).name}:{f.lineno}:{f.name}"
    return "?"


def open_rastreado(file, *a, **k):
    if Path(str(file)).name == ".timeline_index.json":
        LEITURAS.append({"arquivo": str(file), "chamador": chamador()})
    return ORIG_OPEN(file, *a, **k)


def main():
    idx, skip = {}, {}
    for s in V3.NOMES:
        stored = V3.read(V3.RAIZES[s] / "course/.timeline_index.json")
        prof = V3.W.SimpleNamespace(**V3.read(V3.RAIZES[s] / "_inputs_15-09.json")["profile_input"])
        adj, _, _, _, skip[s] = V3.rebuild_adj(V3.RAIZES[s], prof, f"C:{s}:adj")
        assert V3.alinhar_uuid(stored, adj), s
        idx[s] = adj
    V3.SKIP_H.update(skip)
    io.open = builtins.open = open_rastreado
    try:
        _, dec, _ = V3.rodar_braco("P1adjH", idx, V3.prep_h)
    finally:
        io.open = builtins.open = ORIG_OPEN
    cong = V3.read(V3.OUT_CONG)
    iguais = dec == cong["decisoes"]["P1adjH"]
    por_chamador = collections.Counter(x["chamador"] for x in LEITURAS)
    fora = {c: n for c, n in por_chamador.items() if not c.startswith("compara_herancas_15-09.py")}
    res = {"wy3_sha256": hashlib.sha256(WY3.read_bytes()).hexdigest(), "congelado_sha256_decisoes": cong["sha256"],
           "decisoes_P1adjH_iguais_ao_congelado": iguais, "leituras_do_indice_por_chamador": dict(por_chamador),
           "leituras_fora_do_comparador": fora, "skip_H": skip}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("decisoes = congelado:", iguais, "| leituras por chamador:", dict(por_chamador), "| fora do comparador:", fora or "nenhuma")
    print("SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
