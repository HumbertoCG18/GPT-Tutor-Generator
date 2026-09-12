"""Pergunta do user (08/09): "a atribuicao de unidade tem valor sustentado se nao existir gold?"

A regua sem gold diz que o motor concorda com o professor em 114/122 (CG 44/44, sem gold nenhum). Mas antes de confiar
nisso e preciso CALIBRAR a regua: nos 5 cursos onde o gold TAMBEM existe, quem acerta quando os dois discordam?

Para cada material em que a SECAO do Moodle nomeia uma unidade (o mesmo criterio de `regua_sem_gold.secao_nomeia_unidade`)
E existe gold de unidade, cruza tres coisas: o que o motor gravou, o que a secao diz, e o gold. 0 chamadas.
Uso: calibra_regua_unidade.py
"""
import collections
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
C13 = GEN / "docs/reports/_harness-2026-09-04/c1-3"
COM_GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
            "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor"}
SEM_GOLD = {"CG": "Computacao-Grafica-Tutor", "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.path.insert(0, str(C13))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from regua_sem_gold import secao_nomeia_topico, secao_nomeia_unidade  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402

print("CALIBRACAO — onde a SECAO nomeia a unidade E existe gold, quem acerta?")
print(f"{'':5} {'casos':>6} {'motor=gold':>11} {'secao=gold':>11} {'os dois':>8} {'so motor':>9} {'so secao':>9} {'nenhum':>7}")
T = collections.Counter()
DIVERG = []
for sig, repo in COM_GOLD.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    gu = _load_truth(sig)
    c = collections.Counter()
    for eid, ouro in gu.items():
        e = man.get(eid)
        if not e:
            continue
        sec = secao_nomeia_unidade(e, tax)
        via = "A: secao nomeia a UNIDADE"
        if not sec:
            sec = secao_nomeia_topico(str(e.get("source_section") or ""), tax)[0]
            via = "B: secao nomeia um TOPICO -> unidade dona"
        if not sec:
            continue
        c["n"] += 1
        c[f"{via}|n"] += 1
        c[f"{via}|ok"] += sec == ouro
        m = str(e.get("computed_unit_slug") or "")
        mo, so = m == ouro, sec == ouro
        c["motor"] += mo
        c["secao"] += so
        c["dois"] += mo and so
        c["so_motor"] += mo and not so
        c["so_secao"] += so and not mo
        c["nenhum"] += not mo and not so
        if mo != so:
            DIVERG.append((sig, eid, str(e.get("source_section") or "")[:30], m[8:24], sec[8:24], ouro[8:24], ("MOTOR" if mo else "REGUA") + " | " + via[:1]))
    T.update(c)
    if c["n"]:
        print(f"{sig:5} {c['n']:6} {c['motor']:11} {c['secao']:11} {c['dois']:8} {c['so_motor']:9} {c['so_secao']:9} {c['nenhum']:7}")
print(f"{'TOT':5} {T['n']:6} {T['motor']:11} {T['secao']:11} {T['dois']:8} {T['so_motor']:9} {T['so_secao']:9} {T['nenhum']:7}")
if T["n"]:
    print(f"\n  precisao do MOTOR onde a secao fala: {100 * T['motor'] / T['n']:.0f}%")
    print(f"  precisao da SECAO (a regua sem gold): {100 * T['secao'] / T['n']:.0f}%")

print("\nOS CASOS EM QUE MOTOR E SECAO DIVERGEM (quem o gold da razao):")
for d in DIVERG:
    print(f"  {d[0]:4} {d[1][:30]:30} secao={d[2]:34} motor={d[3]:18} regua={d[4]:18} gold={d[5]:18} -> {d[6]}")

print("\nCOBERTURA DA REGUA SEM GOLD NOS CURSOS SEM GOLD DE UNIDADE:")
for sig, repo in SEM_GOLD.items():
    root = GH / repo
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    tax = load_internal_content_taxonomy(root)
    n = fala = conc = 0
    cA, cB = [0, 0], [0, 0]
    for e in man:
        if not str(e.get("computed_unit_slug") or ""):
            continue
        n += 1
        sa = secao_nomeia_unidade(e, tax)
        sb = secao_nomeia_topico(str(e.get("source_section") or ""), tax)[0] if not sa else ""
        sec = sa or sb
        if sec:
            fala += 1
            conc += sec == str(e.get("computed_unit_slug") or "")
            if sa:
                cA[0] += 1; cA[1] += sa == str(e.get("computed_unit_slug") or "")
            else:
                cB[0] += 1; cB[1] += sb == str(e.get("computed_unit_slug") or "")
    print(f"  {sig:4} materiais com unidade={n:3} · a regua fala em {fala:3} ({100 * fala / max(1, n):3.0f}%) · "
          f"concordam {conc}/{fala}  [caminho A (confiavel): {cA[1]}/{cA[0]} · caminho B (refutado 07/09): {cB[1]}/{cB[0]}]")
