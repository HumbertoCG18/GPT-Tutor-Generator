"""PISO DA 1a PASSADA (07/09): hoje uma decisao da 1a passada bloqueia a 2a (propagacao por headings) sempre que
`confidence >= 0.7` e nao for ambigua — e `confidence` e MARGEM, nao forca. Por isso um vencedor com `winner_score` 0,91
(ruido) trava a regra melhor. Aqui: distribuicao do winner_score entre acertos e erros dessas decisoes, e o efeito de
exigir um piso de forca para bloquear. Read-only, 0 chamadas. Uso: simula_piso_1a.py"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
_WS = re.compile(r"winner_score=([\d.]+)")
# reasons que indicam que a 2a passada (ou uma regra posterior) JA agiu: a decisao nao foi da 1a passada
POSTERIOR = ("propagado-headings", "rotulo-decomposto", "titulo-nomeia-subtopico", "secao-nomeia-subtopico", "manual")

linhas = []
for sig, repo in REPO.items():
    man = {e["id"]: e for e in json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
        if r["scorable"] != "yes" or r["entry_id"] not in man:
            continue
        e = man[r["entry_id"]]
        reasons = [str(x) for x in (e.get("subunit_match_reasons") or [])]
        if any(p in x for x in reasons for p in POSTERIOR):
            continue                      # decidido depois da 1a passada
        got = str(e.get("computed_subunit_slug") or "")
        if not got or any("ambiguous" in x or x.startswith("empate") or x.startswith("sem-sinal") for x in reasons):
            continue                      # 1a passada nao decidiu: a 2a ja podia agir
        ws = next((float(m.group(1)) for x in reasons if (m := _WS.search(x))), None)
        if ws is None:
            continue
        aceitos = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        linhas.append((ws, got in aceitos, sig, r["entry_id"], got, r["gold_subunit"]))

linhas.sort()
ok = [x for x in linhas if x[1]]
err = [x for x in linhas if not x[1]]
print(f"decisoes da 1a passada que BLOQUEIAM a 2a e tem gold: {len(linhas)} · certas {len(ok)} · erradas {len(err)}")
print(f"  winner_score das CERTAS:  min {ok[0][0]:.2f} · p10 {ok[len(ok)//10][0]:.2f} · mediana {ok[len(ok)//2][0]:.2f}")
print(f"  winner_score das ERRADAS: min {err[0][0]:.2f} · mediana {err[len(err)//2][0]:.2f} · max {err[-1][0]:.2f}")
print("\n  as 12 decisoes de MENOR forca (o piso corta por baixo):")
for ws, acertou, sig, eid, got, gold in linhas[:12]:
    print(f"    {ws:7.2f} {'OK  ' if acertou else 'ERRO'} {sig:4} {eid[:30]:30} {got[-26:]:28} gold={gold[-26:]}")
print("\n  efeito de exigir piso de forca para BLOQUEAR a 2a passada (abaixo do piso, a 2a passada pode agir):")
for piso in (0.5, 1.0, 1.05, 1.5, 2.0, 3.0):
    libera_err = sum(1 for ws, acertou, *_ in linhas if ws < piso and not acertou)
    libera_ok = sum(1 for ws, acertou, *_ in linhas if ws < piso and acertou)
    print(f"    piso {piso:5.2f}: libera {libera_err + libera_ok:3} decisoes para a 2a passada — {libera_err} hoje ERRADAS (chance de ganho), {libera_ok} hoje CERTAS (risco)")
