"""Duvidas de BLOCO do regime zero (flag:disamb, disamb-curto, sem-bloco) x POSICAO DO PROFESSOR no Moodle (placement_of de
coerencia_moodle.py: label datado, data no nome, secao-semana, faixa dos irmaos). Quantas a posicao resolve sozinha (bloco unico) e se
coincide com o gold. Read-only, 0 chamadas. Uso: posicao_duvidas_zero.py"""
import collections
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
C13 = GEN / "docs/reports/_harness-2026-09-04/c1-3"
SNAP = C13 / "snap_placar/zero"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
src = (C13 / "coerencia_moodle.py").read_text(encoding="utf-8")
ns = {"__name__": "coerencia_lib", "__file__": str(C13 / "coerencia_moodle.py")}
exec(src.split("TOT = collections.Counter()")[0], ns)  # so as definicoes (placement_of, bid, hosts, REPOS, ...)
placement_of, bid = ns["placement_of"], ns["bid"]
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.revisar import motivos_de, revisar_de  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
BLOCO_MOTIVOS = ("flag:disamb", "flag:disamb-curto", "sem-bloco", "flag:due-straddle")
TOT = collections.Counter(); EX = collections.defaultdict(list)
for sig, repo in REPO.items():
    man = json.loads((SNAP / f"{repo}.manifest.json").read_text(encoding="utf-8"))
    ti = {}
    for b in json.loads((SNAP / f"{repo}.timeline.json").read_text(encoding="utf-8"))["blocks"]:
        ti[b["block_uuid"]] = b["id"]; ti[b["id"]] = b["id"]
    course_name = str((man.get("course") or {}).get("course_name") or "")
    ctx = build_motor_context(GH / repo, course_name)
    place = placement_of(sig, repo, man, ctx)
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    c = collections.Counter()
    for e in man["entries"]:
        r = revisar_de(e)
        ms = motivos_de(e) or []
        duvida_bloco = r == "duvida" and any(m in BLOCO_MOTIVOS for m in ms)
        eid = e["id"]; atual = ti.get(str(e.get("temporal_block_id") or ""), "")
        gold = gb.get(eid)
        err_conf = (r != "duvida") and gold is not None and atual != gold
        if not duvida_bloco and not err_conf:
            continue
        grupo = "duvida de bloco" if duvida_bloco else "ERRO CONFIANTE de bloco"
        c[f"{grupo}: itens"] += 1
        bl, fonte = place.get(eid, ([], "sem posicao"))
        bl = list(dict.fromkeys(bl or []))
        if not bl:
            c[f"{grupo}: sem posicao"] += 1; k = "sem posicao"
        elif len(bl) == 1:
            k = "posicao UNICA"
            c[f"{grupo}: posicao UNICA"] += 1
            if gold is not None:
                c[f"{grupo}: unica = gold"] += (bl[0] == gold); c[f"{grupo}: unica != gold"] += (bl[0] != gold)
            c[f"{grupo}: unica = atual"] += (bl[0] == atual)
        else:
            k = f"posicao com {len(bl)} blocos"
            c[f"{grupo}: posicao multipla"] += 1
            if gold is not None:
                c[f"{grupo}: multipla contem gold"] += (gold in bl)
            win = [ti.get(w, w) for w in (e.get("temporal_block_window") or [])]
            c[f"{grupo}: multipla estreita a janela"] += (len(win) > len(bl))
        if len(EX[grupo]) < 5:
            EX[grupo].append(f"{sig}:{eid[:24]} {k} ({fonte}) atual={atual} gold={gold} pos={bl[:4]}")
    TOT.update(c)
    print(f"[{sig}] " + " · ".join(f"{k.split(': ', 1)[1]}={v}" for k, v in sorted(c.items()) if k.startswith("duvida")) +
          "  || conf-err: " + " · ".join(f"{k.split(': ', 1)[1]}={v}" for k, v in sorted(c.items()) if k.startswith("ERRO")))
print("\n[TOTAL zero]")
for k, v in sorted(TOT.items()):
    print(f"  {k:48} {v}")
for g, xs in EX.items():
    print(f"\nexemplos {g}:", *xs, sep="\n   ")
