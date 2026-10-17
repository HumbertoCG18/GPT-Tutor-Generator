"""CRU-03: medição de sinal (seção do Moodle) nos blocos de afinidade zero. Pré-registro: preregistro-cru03-medicao.md
(sha256 36eed38b…, selado antes desta execução). Sem gold, sem replay, sem mudar decisão de produção.

Uso: python -B mede_cru03.py --worktree <src da base> --decisoes replay_base.json --rastro diag_rastro_base.json --saida <json>
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path

PRINCIPAL = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator")
C13 = PRINCIPAL / "docs/reports/_harness-2026-09-04/c1-3"


def sem_rede(*a, **k):
    raise AssertionError("rede vedada")


def main():
    p = argparse.ArgumentParser()
    for nome in ("--worktree", "--decisoes", "--rastro", "--saida"):
        p.add_argument(nome, required=True)
    a = p.parse_args()
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
    wz = wz2.load("d_wz", C13 / "wz_bloco_cobertura_22-09.py")

    decisoes = json.loads(Path(a.decisoes).read_text(encoding="utf-8"))["decisoes"]
    rastro = json.loads(Path(a.rastro).read_text(encoding="utf-8"))
    assert rastro["fidelidade"] == "integral"
    cap = rastro["captura_wz2"]

    inventario, tabela = [], []
    for sig in compare.mede.NOMES:
        root = wz.root_de(sig, compare.mede.NOMES)
        blocos, _ = wz2.decompor_dp(root)
        secao_crua = {str(e.get("id")): str(e.get("source_section") or "")
                      for e in json.loads((root / "manifest.json").read_text(encoding="utf-8")).get("entries", [])}
        por_bloco = collections.defaultdict(list)
        for eid, d in decisoes.get(sig, {}).items():
            if d.get("bloco"):
                por_bloco[d["bloco"]].append(eid)
        for bid, b in blocos.items():
            linha = {"curso": sig, "bloco": bid, "ordem": b["ordem"], "posicao": b["posicao"], "classe": b["classe"],
                     "fiel": b["fiel"], "unidade_dp": b["dp_recomputado"], "mecanismo": b["mecanismo"]}
            inventario.append(linha)
            if b["classe"] != "sem_sinal":
                continue
            mats = sorted(por_bloco.get(bid, []))
            secoes = [str(((cap.get(sig, {}).get(e) or {}).get("unidade_bruta") or {}).get("secao") or "") for e in mats]
            compat = sorted({s for s in secoes if s})
            unica = compat[0] if len(compat) == 1 else None
            tabela.append({**linha, "periodo": b["periodo"], "rotulo": b["rotulo"], "n_materiais": len(mats),
                           "n_com_secao": sum(1 for s in secoes if s),
                           "section_slug_por_material": dict(zip(mats, secoes)),
                           "secao_crua_por_material": {e: secao_crua.get(e, "") for e in mats},
                           "compativeis": compat,
                           "cardinalidade": "0" if not compat else ("1" if len(compat) == 1 else ">1"),
                           "concordancia": "ausente" if unica is None and not compat else
                                           ("multipla" if unica is None else ("concorda" if unica == b["dp_recomputado"] else "conflita"))})

    def resumo(chave):
        r = collections.defaultdict(collections.Counter)
        for t in tabela:
            if t["fiel"]:
                r[t[chave]][f"card_{t['cardinalidade']}"] += 1
                r[t[chave]][t["concordancia"]] += 1
                r[t[chave]]["blocos"] += 1
        return {k: dict(v) for k, v in sorted(r.items())}

    tab_bytes = json.dumps(tabela, ensure_ascii=False, sort_keys=True).encode("utf-8")
    res = {"preregistro_sha256": "36eed38b7ee3bcfdbd911fa9dc57fd211c94b8fcc9f2b4c75ad56291629ed37e",
           "worktree": str(wt), "decisoes": str(Path(a.decisoes).resolve()), "rastro": str(Path(a.rastro).resolve()),
           "reconciliacao_wz2": {"candidatos": len(inventario), "sem_sinal": sum(1 for i in inventario if i["classe"] == "sem_sinal"),
                                 "historico_wz2": "50/125", "nao_fieis": sum(1 for i in inventario if not i["fiel"])},
           "resumo_por_posicao": resumo("posicao"), "resumo_por_curso": resumo("curso"),
           "tabela_sha256": hashlib.sha256(tab_bytes).hexdigest(), "tabela": tabela, "inventario": inventario}
    saida.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("candidatos", res["reconciliacao_wz2"], "| tabela", res["tabela_sha256"][:16])
    print("por posição:", json.dumps(res["resumo_por_posicao"], ensure_ascii=False))
    print("por curso:", json.dumps(res["resumo_por_curso"], ensure_ascii=False))


if __name__ == "__main__":
    main()
