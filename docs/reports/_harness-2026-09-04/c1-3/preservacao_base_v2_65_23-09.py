"""Replay integral de preservação da base v2 (23/09, Gate 1 da #65). Não relança W-Z nem W-AA.

Reusa o modo `base` do harness do W-Z2 (replay_bloco_21-09 -> replay_unidade_21-09, instrumentação só em memória e
restaurada, fidelidade por ID já provada no W-Z2) com o código ATUAL do worktree, e compara por ID, sem gold:
  - com a captura congelada do W-Z2 (.frzero/wz2_captura_base_23-09.json, sha256_base f941ac33...): registro final inteiro
    (bloco, unidade, razões, subunidade, razões, confiança, cobertura) e também o sha da captura completa;
  - com o congelamento do W-Z (.frzero/wz_congelado_22-09.json, 788e4372...): (bloco, unidade, sub).
Identidade por ID implica o mesmo placar da base v2 (bloco 223/237, unidade 248/284, subunidade primária 86/251), porque a
régua é a mesma. Saída: preservacao_base_v2_65_23-09.json.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True


def main():
    t0 = time.time()
    wz2 = __import__("importlib.util").util
    spec = wz2.spec_from_file_location("wz2", HERE / "wz2_diagnostico_causal_23-09.py")
    wz2 = wz2.module_from_spec(spec)
    spec.loader.exec_module(wz2)
    compare = wz2.load("p_cmp", HERE / "compara_herancas_15-09.py")
    rb = wz2.load("p_rb", HERE / "replay_bloco_21-09.py")
    ru = wz2.load("p_ru", HERE / "replay_unidade_21-09.py")
    wz = wz2.load("p_wz", HERE / "wz_bloco_cobertura_22-09.py")
    nomes = compare.mede.NOMES
    raizes = {sig: wz.root_de(sig, nomes) for sig in nomes}

    estado = {}
    for sig in nomes:
        saved, bloco_novo, decisoes, _ = rb.replay(raizes[sig])
        estado[sig] = {"root": raizes[sig], "saved": saved, "decisoes": decisoes,
                       "feed": [wz2.copy.deepcopy(bloco_novo[i]) for i in bloco_novo]}
    print("bloco ok", round(time.time() - t0), "s", flush=True)
    novo = wz2.rodar("base", estado, ru, compare)

    cong = wz2.read(wz2.CAP_BASE)
    assert cong["sha256_base"].startswith("f941ac33"), cong["sha256_base"]
    wzc = wz2.read(wz2.CONG_WZ)
    assert wzc["sha256_congelamento"].startswith("788e4372"), wzc["sha256_congelamento"]

    por_curso, div_w2, div_wz = {}, [], []
    for sig in nomes:
        antigo, atual = cong["base"][sig], novo[sig]
        ids = sorted(set(antigo) | set(atual))
        finais = [i for i in ids if "final" in antigo.get(i, {}) or "final" in atual.get(i, {})]
        dif = [i for i in finais if antigo.get(i, {}).get("final") != atual.get(i, {}).get("final")]
        div_w2 += [[sig, i] for i in dif]
        dz = []
        for eid, d in wzc["saidas"]["base"][sig].items():
            f = atual.get(eid, {}).get("final") or {}
            if (f.get("bloco"), f.get("unidade"), f.get("sub")) != (d["bloco"], d["unidade"], d["sub"]):
                dz.append(eid)
        div_wz += [[sig, i] for i in dz]
        por_curso[sig] = {"materiais_com_final": len(finais), "divergem_w2": len(dif),
                          "ids_wz": len(wzc["saidas"]["base"][sig]), "divergem_wz": len(dz)}

    git = lambda *a: subprocess.run(["git", *a], capture_output=True, cwd=HERE.parents[3], check=True).stdout  # noqa: E731
    res = {
        "head": git("rev-parse", "HEAD").decode().strip(),
        "sha256_git_diff_worktree_src_tests": wz2.hashlib.sha256(git("diff", "--", "src", "tests")).hexdigest(),
        "sha256_captura_nova": wz2.sha(novo), "sha256_captura_congelada": cong["sha256_base"],
        "captura_identica": wz2.sha(novo) == cong["sha256_base"],
        "por_curso": por_curso, "divergencias_w2": div_w2, "divergencias_wz": div_wz,
        "segundos": round(time.time() - t0),
    }
    (HERE / "preservacao_base_v2_65_23-09.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
