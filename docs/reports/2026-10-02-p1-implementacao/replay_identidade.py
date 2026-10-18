"""Replay integral offline com o src de uma worktree, comparado POR ID com as decisões de uma referência. Sem gold.

Uso: python -B replay_identidade.py --worktree <raiz> --referencia <replay_*.json> --saida <json>
Serve à pré-condição do P1 (#90): com P1 desligado (padrão), decisões idênticas ao braço correspondente.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import socket
import sys
import time
from pathlib import Path

PRINCIPAL = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
C13 = PRINCIPAL / "docs/reports/_harness-2026-09-04/c1-3"


def sem_rede(*a, **k):
    raise AssertionError("rede vedada")


def main():
    p = argparse.ArgumentParser()
    for nome in ("--worktree", "--referencia", "--saida"):
        p.add_argument(nome, required=True)
    a = p.parse_args()
    t0 = time.time()
    socket.socket.connect = sem_rede
    socket.create_connection = sem_rede
    sys.dont_write_bytecode = True
    wt, saida = Path(a.worktree).resolve(), Path(a.saida).resolve()
    if saida.is_relative_to(PRINCIPAL.resolve()):
        raise SystemExit("--saida dentro da árvore principal")
    sys.path.insert(0, str(wt))
    import src
    src.__path__ = [str(wt / "src")]
    spec = importlib.util.spec_from_file_location("wz2", C13 / "wz2_diagnostico_causal_23-09.py")
    wz2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wz2)
    compare = wz2.load("d_cmp", C13 / "compara_herancas_15-09.py")
    rb = wz2.load("d_rb", C13 / "replay_bloco_21-09.py")
    ru = wz2.load("d_ru", C13 / "replay_unidade_21-09.py")
    wz = wz2.load("d_wz", C13 / "wz_bloco_cobertura_22-09.py")
    estado = {}
    for sig in compare.mede.NOMES:
        root = wz.root_de(sig, compare.mede.NOMES)
        saved, bloco_novo, decisoes, _ = rb.replay(root)
        estado[sig] = {"root": root, "saved": saved, "decisoes": decisoes,
                       "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    cap = wz2.rodar("base", estado, ru, compare, pontuar=False)
    decisoes = {s: {e: {k: (r.get("final") or {}).get(k) for k in ("bloco", "unidade", "sub")}
                    for e, r in cap[s].items() if "final" in r} for s in cap}
    ref = json.loads(Path(a.referencia).read_text(encoding="utf-8"))["decisoes"]
    div = [[s, e, ref.get(s, {}).get(e), decisoes.get(s, {}).get(e)] for s in sorted(set(decisoes) | set(ref))
           for e in sorted(set(decisoes.get(s, {})) | set(ref.get(s, {}))) if decisoes.get(s, {}).get(e) != ref.get(s, {}).get(e)]
    src_fora = sorted(n for n, m in sys.modules.items() if (n == "src" or n.startswith("src.")) and getattr(m, "__file__", None)
                      and not Path(m.__file__).resolve().is_relative_to(wt))
    res = {"worktree": str(wt), "referencia": str(Path(a.referencia).resolve()),
           "referencia_sha256": hashlib.sha256(Path(a.referencia).read_bytes()).hexdigest(),
           "src_sha256": {n: hashlib.sha256(Path(sys.modules[n].__file__).read_bytes()).hexdigest()
                          for n in ("src.builder.timeline.index", "src.builder.routing.file_map", "src.builder.text.normalize")},
           "ids": sum(len(v) for v in decisoes.values()), "divergencias": div, "src_fora": src_fora,
           "identico": not div and not src_fora, "decisoes": decisoes, "segundos": round(time.time() - t0)}
    saida.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ids", res["ids"], "| divergências", len(div), "| src fora", src_fora or "nenhum", "| idêntico", res["identico"],
          "| segundos", res["segundos"])
    return 0 if res["identico"] else 1


if __name__ == "__main__":
    sys.exit(main())
