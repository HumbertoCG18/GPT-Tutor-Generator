"""Snapshot MATERIAL A MATERIAL dos 3 eixos de uma copia do motor (14/09).

Por que existe: o corte do experimento de relacoes explicitas (§38.6) e "sem perder NENHUM acerto em NENHUM eixo". O
`mede_3eixos_12-09.py` so publica agregados, e o `.motor3eixos/` guarda uma configuracao por vez — sem um snapshot por material,
a comparacao braco x baseline so e possivel no eixo subunidade (pelo CSV de erros). Mesma regua do `mede_3eixos_12-09.py`.

Grava CSV: curso, entry_id, bloco (1/0/vazio), unidade (1/0/vazio), sub_aceito, sub_primario, e as predicoes. O marcador
`_CONFIG_ATUAL.txt` vai na 1a linha do log, para nunca comparar snapshot da configuracao errada.

0 chamadas. Uso: python -B snapshot_3eixos_14-09.py --raiz .motor3eixos --saida snapshot_bracoC_14-09.csv
"""
import argparse
import csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("mede3", HERE / "mede_3eixos_12-09.py")
mede3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mede3)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args(argv)
    raiz = Path(a.raiz) if Path(a.raiz).is_absolute() else GEN / a.raiz
    marc = (raiz / "_CONFIG_ATUAL.txt").read_text(encoding="utf-8").splitlines()[0] if (raiz / "_CONFIG_ATUAL.txt").exists() else "(sem marcador)"
    print(f"copia: {raiz} · configuracao: {marc}")
    linhas = []
    for sig, nome in mede3.NOMES.items():
        root = raiz / nome
        if not (root / "manifest.json").exists():
            continue
        ti = {}
        tp = root / "course/.timeline_index.json"
        if tp.exists():
            for b in json.loads(tp.read_text(encoding="utf-8"))["blocks"]:
                ti[b["block_uuid"]] = b["id"]
                ti[b["id"]] = b["id"]
        gb, gu, gs, gsp = mede3.golds(sig)
        for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]:
            eid = e["id"]
            if eid not in gb and eid not in gu and eid not in gs:
                continue
            bloco = ti.get(str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or ""), "")
            uni = str(e.get("computed_unit_slug") or "")
            sub = str(e.get("computed_subunit_slug") or "")
            linhas.append(dict(
                curso=sig, entry_id=eid,
                bloco="" if eid not in gb else int(bloco == gb[eid]),
                unidade="" if eid not in gu else int(uni in gu[eid]),
                sub_aceito="" if eid not in gs else int(sub in gs[eid]),
                sub_primario="" if eid not in gsp else int(sub in gsp[eid]),
                pred_bloco=bloco, pred_unidade=uni, pred_sub=sub))
    out = Path(a.saida) if Path(a.saida).is_absolute() else HERE / a.saida
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    tot = {k: (sum(1 for l in linhas if l[k] == 1), sum(1 for l in linhas if l[k] != "")) for k in ("bloco", "unidade", "sub_aceito", "sub_primario")}
    print("  ".join(f"{k} {c}/{n}" for k, (c, n) in tot.items()))
    print(f"{len(linhas)} materiais gravados em {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
