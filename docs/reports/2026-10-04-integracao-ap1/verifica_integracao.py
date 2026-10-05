"""Integração A+P1 (#89/#90): replay integral com o callback de subunidade da PRODUÇÃO, comparado por ID com uma referência.

Uso: python -B verifica_integracao.py --worktree <raiz> --referencia <json com "decisoes"> --saida <json> --rotulo <r>
- Derivado de tentativa2/replay_t2.py (avaliação congelada de 02/10), com três diferenças:
  1. `ru.auto_sub` recebe `src.builder.engine._auto_map_entry_subtopic` (callback real, sem partial experimental);
  2. sem barreira entre braços (um processo por árvore; a guarda de ABORT da barreira não existe aqui);
  3. aborta ANTES do gold se houver src fora da worktree ou qualquer decisão diferente da referência.
- Dados (.frzero, régua, heranças) vêm da principal; nada é gravado fora de --saida. Sem rede, sem LLM, sem build.
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
MODULOS = ("src.builder.text.normalize", "src.builder.timeline.index", "src.builder.routing.file_map",
           "src.builder.facade.file_map", "src.builder.routing.resolver_apply", "src.builder.engine")
CAMPOS = ("bloco", "unidade", "sub")


def sem_rede(*a, **k):
    raise AssertionError("rede vedada no replay")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worktree", required=True)
    p.add_argument("--referencia", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--rotulo", required=True)
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
    from src.builder.engine import _auto_map_entry_subtopic
    ru.auto_sub = _auto_map_entry_subtopic   # callback real: o mesmo objeto vai à 1a e à 2a passada
    callback_kw = sorted(_auto_map_entry_subtopic.keywords)

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
    carregados = {n: [str(Path(sys.modules[n].__file__).resolve()), sha(sys.modules[n].__file__)] for n in MODULOS}

    def saidas_de(dec):
        return {sig: {eid: {k: (r.get("final") or {}).get(k) for k in CAMPOS} for eid, r in dec[sig].items()
                      if "final" in r} for sig in dec}

    decisoes = saidas_de(novo)
    sha_dec = hashlib.sha256(json.dumps(decisoes, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    ref_path = Path(a.referencia).resolve()
    referencia = json.loads(ref_path.read_text(encoding="utf-8"))["decisoes"]
    mudancas = [{"curso": s, "eid": e, "referencia": referencia.get(s, {}).get(e), "execucao": decisoes.get(s, {}).get(e)}
                for s in sorted(set(decisoes) | set(referencia))
                for e in sorted(set(decisoes.get(s, {})) | set(referencia.get(s, {})))
                if decisoes.get(s, {}).get(e) != referencia.get(s, {}).get(e)]
    n_ids = sum(len(v) for v in decisoes.values())
    res = {"rotulo": a.rotulo, "worktree": str(wt), "carregados": carregados, "src_fora_da_worktree": src_fora,
           "callback_keywords": callback_kw, "referencia": {"arquivo": str(ref_path), "sha256": sha(ref_path)},
           "ids_execucao": n_ids, "ids_referencia": sum(len(v) for v in referencia.values()),
           "mudancas_por_id": mudancas, "sha256_decisoes": sha_dec, "decisoes": decisoes}
    print(a.rotulo, "| ids:", n_ids, "| mudanças por ID (sem gold):", len(mudancas), "| src fora:", src_fora or "nenhum",
          "| callback:", callback_kw, flush=True)
    if src_fora or mudancas:
        res["abortado"] = "src fora da worktree" if src_fora else "decisões diferentes da referência; gold não consultado"
        saida.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        raise SystemExit(res["abortado"])
    # ======================= gold entra aqui (só placar)
    wz.preparar_avaliacao(estado, compare, compare.mede, wx)
    assert saidas_de(novo) == decisoes, "decisões mudaram após gold"
    pc, _ = wz.avaliar(estado, decisoes)
    res["placar"] = {"total": wz.totais(pc), "por_curso": pc}
    res["segundos"] = round(time.time() - t0)
    saida.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("placar:", res["placar"]["total"], "| segundos:", res["segundos"])


if __name__ == "__main__":
    main()
