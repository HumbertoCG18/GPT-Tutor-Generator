"""Aceite da #52 etapa 2 (MOTOR-08, 05/10): o PRODUTO (src da worktree fix/52-tipo-por-linha, sem patch em memoria)
reproduz por ID (1) as decisoes congeladas do braco P1adjH da W-Y v3 (wy3_..._congelado.json, a2c84ae2) pela cadeia
da referencia 87 e (2) o tipo, a unidade e o id do bloco de cada linha do P1adj nos 8 cursos vivos (wy3 json, A.linhas).
Gold so depois da comparacao (placar informativo). Reusa o wy3 sem altera-lo (sha conferido); sem rede/LLM/build.
Uso: python -B verifica_52_05-10.py --worktree <raiz com o src da mudanca>
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "verifica_52_05-10.json"
WY3 = HERE / "wy3_kind_por_linha_05-10.py"
assert hashlib.sha256(WY3.read_bytes()).hexdigest().startswith("e72ab113"), "wy3 mudou"
spec = importlib.util.spec_from_file_location("wy3", WY3)
V3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V3)                      # le --worktree de sys.argv; main() nao roda
V3.W.PERMITIDOS.add(OUT.resolve())


def main():
    v3 = V3.read(HERE / "wy3_kind_por_linha_05-10.json")
    esperado = {(x["curso"], x["linha"]): [x["bloco_P1adj"], x["tipo_bloco_P1adj"], x["unit_P1adj"]] for x in v3["A"]["linhas"]}
    vivos = []
    for sig, (repo, prof) in V3.W.perfis_vivos().items():
        idx, _ = V3.W.rebuild(repo, prof, False, f"{sig}:produto")
        por_linha = {r: b for b in idx["blocks"] for r in V3.rows_of(b)}
        for (s, i), exp in sorted(esperado.items()):
            b = por_linha.get(i) if s == sig else None
            got = [b["id"], b.get("kind"), b.get("unit_slug")] if b else [None, None, None]
            if s == sig and got != exp:
                vivos.append({"curso": s, "linha": i, "esperado_P1adj": exp, "produto": got})
    idx = {}
    for s in V3.NOMES:
        stored = V3.read(V3.RAIZES[s] / "course/.timeline_index.json")
        prof = V3.W.SimpleNamespace(**V3.read(V3.RAIZES[s] / "_inputs_15-09.json")["profile_input"])
        prod, _ = V3.W.rebuild(V3.RAIZES[s], prof, False, f"C:{s}:produto")
        assert V3.alinhar_uuid(stored, prod), f"segmentacao mudou em {s}"
        idx[s] = prod
    est, dec, prep = V3.rodar_braco("produto", idx)
    cong = V3.read(V3.OUT_CONG)
    mud = V3.mudancas(cong["decisoes"]["P1adjH"], dec)
    res = {"wy3_sha256": hashlib.sha256(WY3.read_bytes()).hexdigest(), "congelado_sha256_decisoes": cong["sha256"],
           "head": V3.subprocess.run(["git", "-C", str(V3.WT), "rev-parse", "--short", "HEAD"], capture_output=True,
                                     text=True).stdout.strip(),
           "replay_ids": sum(len(v) for v in dec.values()), "replay_mudancas_x_P1adjH": mud,
           "vivos_linhas_comparadas": len(esperado), "vivos_divergencias_x_P1adj": vivos, "prep_prova": prep,
           "src_fora_da_worktree": sorted(n for n, m in V3.sys.modules.items() if (n == "src" or n.startswith("src."))
                                          and getattr(m, "__file__", None) and not Path(m.__file__).resolve().is_relative_to(V3.WT))}
    if not mud:
        # ======================= gold so aqui (placar informativo)
        V3.wz.preparar_avaliacao(est, V3.compare, V3.compare.mede, V3.wx)
        pc, _ = V3.wz.avaliar(est, dec)
        res["placar"] = V3.wz.totais(pc)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("replay:", res["replay_ids"], "ids | mudancas x P1adjH:", len(mud), "| vivos:", len(esperado), "linhas, divergencias:",
          len(vivos), "| src fora:", res["src_fora_da_worktree"] or "nenhum", "| placar:", res.get("placar"))
    print("SHA256", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
