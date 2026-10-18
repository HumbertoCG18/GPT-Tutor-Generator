"""Replay integral (CRU-05): decisões por ID com o src de uma worktree, contra a captura congelada da base v2 (W-Z2).

Uso: python -B replay_cru05.py --worktree <raiz> --saida <json>
- O src vem só da worktree: `src.__path__` é fixado nela antes de carregar os módulos de replay (que inserem a raiz da
  principal no sys.path; `src` é pacote de namespace). Dados (.frzero, régua, heranças) são lidos da principal.
- Nada é gravado fora de --saida. Sem rede, sem LLM, sem build.
- Ordem: replay (bloco → unidade/subunidade) → diferenças por ID contra a captura congelada (sem gold) → só então gold,
  para avaliar a base congelada e a execução nos mesmos IDs.
"""
import argparse
import collections
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
    raise AssertionError("rede vedada no replay")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worktree", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--p1", choices=("ligado", "desligado"), required=True)
    p.add_argument("--esperado", required=True, help="JSON {modulo: sha256} exigido antes do gold")
    p.add_argument("--barreira", required=True)
    p.add_argument("--rotulo", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--referencia", help="JSON de uma execução anterior deste runner; compara decisões por ID com ela")
    a = p.parse_args()
    t0 = time.time()
    socket.socket.connect = sem_rede
    socket.create_connection = sem_rede
    sys.dont_write_bytecode = True
    wt = Path(a.worktree).resolve()
    saida = Path(a.saida).resolve()
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
    wx = wz2.load("d_wx", C13 / "wx_regua_corrigida_22-09.py")
    if a.p1 == "ligado":
        import functools
        from src.builder.timeline.index import _divisores_de_frase
        ru.auto_sub = functools.partial(ru.auto_sub, divisores_de_frase=_divisores_de_frase)  # P1 ligado nas duas passadas

    nomes = compare.mede.NOMES
    raizes = {sig: wz.root_de(sig, nomes) for sig in nomes}
    estado = {}
    for sig in nomes:
        saved, bloco_novo, decisoes, _ = rb.replay(raizes[sig])
        estado[sig] = {"root": raizes[sig], "saved": saved, "decisoes": decisoes,
                       "feed": [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    novo = wz2.rodar("base", estado, ru, compare, pontuar=False)

    src_fora = sorted(n for n, m in sys.modules.items()
                      if (n == "src" or n.startswith("src.")) and getattr(m, "__file__", None)
                      and not Path(m.__file__).resolve().is_relative_to(wt))
    normalize_file = str(Path(sys.modules["src.builder.text.normalize"].__file__).resolve())

    cong = wz2.read(wz2.CAP_BASE)
    assert cong["sha256_base"].startswith("f941ac33"), cong["sha256_base"][:16]
    campos = ("bloco", "unidade", "sub")
    mudancas = []
    for sig in sorted(set(novo) | set(cong["base"])):
        for eid in sorted(set(novo.get(sig, {})) | set(cong["base"].get(sig, {}))):
            f_novo = (novo.get(sig, {}).get(eid) or {}).get("final") or {}
            f_cong = (cong["base"].get(sig, {}).get(eid) or {}).get("final") or {}
            if f_novo != f_cong:
                mudancas.append({"curso": sig, "eid": eid, "congelada": {k: f_cong.get(k) for k in campos},
                                 "execucao": {k: f_novo.get(k) for k in campos}})
    n_cong = len(mudancas)
    sha_pre_gold = hashlib.sha256(json.dumps(mudancas, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    print("mudanças por ID contra a captura congelada (sem gold):", len(mudancas), "(antes de --referencia)", flush=True)

    carregados = {n: [str(Path(sys.modules[n].__file__).resolve()), hashlib.sha256(Path(sys.modules[n].__file__).read_bytes()).hexdigest()]
                  for n in ("src.builder.timeline.index", "src.builder.routing.file_map", "src.builder.text.normalize")}
    esperado = json.loads(a.esperado)
    divergente = {n: carregados[n][1] for n in esperado if carregados[n][1] != esperado[n]}
    pre = {"rotulo": a.rotulo, "p1": a.p1, "worktree": str(wt), "carregados": carregados, "src_fora": src_fora,
           "divergente": divergente, "decisoes": {sig: {eid: {k: (r.get("final") or {}).get(k) for k in campos}
                                                       for eid, r in novo[sig].items() if "final" in r} for sig in novo}}
    pre["sha256_decisoes"] = hashlib.sha256(json.dumps(pre["decisoes"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    bar = Path(a.barreira)
    if src_fora or divergente:
        (bar / f"{a.rotulo}.ABORT.json").write_text(json.dumps(pre, ensure_ascii=False, indent=1), encoding="utf-8")
        raise SystemExit(f"identidade divergente/src fora: {divergente} {src_fora}")
    (bar / f"{a.rotulo}.json").write_text(json.dumps(pre, ensure_ascii=False, indent=1), encoding="utf-8")
    print("decisões congeladas", a.rotulo, pre["sha256_decisoes"], "s", round(time.time() - t0), flush=True)
    while len(list(bar.glob("*.json"))) < a.n:
        if list(bar.glob("*.ABORT.json")):
            raise SystemExit("outro braço abortou; sem gold")
        time.sleep(2)
    print("barreira liberada", round(time.time() - t0), flush=True)
    # ======================= gold entra aqui (só avaliação)
    wz.preparar_avaliacao(estado, compare, compare.mede, wx)

    def saidas_de(dec):
        return {sig: {eid: {k: (r.get("final") or {}).get(k) for k in campos} for eid, r in dec[sig].items()
                      if "final" in r} for sig in dec}

    decisoes = saidas_de(novo)
    assert decisoes == pre["decisoes"], "decisões mudaram após gold"
    referencia = saidas_de(cong["base"])
    rotulo_ref = "captura congelada W-Z2 (f941ac33)"
    if a.referencia:
        ref_json = json.loads(Path(a.referencia).read_text(encoding="utf-8"))
        referencia, rotulo_ref = ref_json["decisoes"], f"execução {a.referencia}"
        mudancas = [{"curso": s, "eid": e, "referencia": referencia.get(s, {}).get(e), "execucao": decisoes.get(s, {}).get(e)}
                    for s in sorted(set(decisoes) | set(referencia))
                    for e in sorted(set(decisoes.get(s, {})) | set(referencia.get(s, {})))
                    if decisoes.get(s, {}).get(e) != referencia.get(s, {}).get(e)]
    pc_cong, fl_cong = wz.avaliar(estado, referencia)
    pc_novo, fl_novo = wz.avaliar(estado, decisoes)
    ganhos, perdas = wz.diff_ids(fl_cong, fl_novo)
    res = {"src_sha256": {n: [str(Path(sys.modules[n].__file__).resolve()), hashlib.sha256(Path(sys.modules[n].__file__).read_bytes()).hexdigest()] for n in ("src.builder.timeline.index", "src.builder.routing.file_map", "src.builder.text.normalize")}, "worktree": str(wt), "normalize_carregado": normalize_file, "src_fora_da_worktree": src_fora,
           "captura_congelada": {"arquivo": str(wz2.CAP_BASE), "sha256_base": cong["sha256_base"]},
           "referencia": rotulo_ref, "mudancas_por_id": mudancas, "sha256_mudancas_pre_gold": sha_pre_gold,
           "mudancas_contra_captura_congelada": n_cong,
           "decisoes": decisoes,
           "placar_referencia": {"total": wz.totais(pc_cong), "por_curso": pc_cong},
           "placar_execucao": {"total": wz.totais(pc_novo), "por_curso": pc_novo},
           "ganhos": ganhos, "perdas": perdas, "segundos": round(time.time() - t0)}
    saida.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("src fora da worktree:", src_fora or "nenhum", "| normalize:", normalize_file)
    print("placar referência:", res["placar_referencia"]["total"], "|", rotulo_ref)
    print("placar execução: ", res["placar_execucao"]["total"])
    print("ganhos:", {k: len(v) for k, v in ganhos.items()}, "| perdas:", {k: len(v) for k, v in perdas.items()})
    print("segundos:", res["segundos"])


if __name__ == "__main__":
    main()
