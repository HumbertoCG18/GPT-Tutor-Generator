"""FR sem gold (12/09, user: "queria fazer FR sem gold, para ver a precisao do motor puro"): mede um sandbox do FR (rebuild do zero,
0 chamadas) contra as reguas que existem SEM gold de unidade: (a) unidade = a secao explicita do professor no Moodle ("U1 - ...",
"U2 - ..."; 19 de 22 materiais); (b) subunidade = `docs/reports/subunit_gt_FR.csv` (18 pontuaveis; o gold so mede, nunca entrou no
motor); (c) a fila (`revisar`) como detector de erro nos dois eixos. Compara tambem com o produto (vocab LLM + votos em cache).
Uso: python -B .../mede_fr_sem_gold.py [<pasta do sandbox>]   (padrao .ablacao/FR-rebuild/Fundamentos-de-Redes-Tutor)"""
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
GH = GEN.parent
SB = Path(sys.argv[1]) if len(sys.argv) > 1 else GEN / ".ablacao/FR-rebuild/Fundamentos-de-Redes-Tutor"
PROD = GH / "Fundamentos-de-Redes-Tutor"


def unidade_da_secao(sec):
    m = re.match(r"\s*U(\d+)\s*-", str(sec or ""))
    return int(m.group(1)) if m else None


def num(slug):
    m = re.match(r"unidade-0*(\d+)", str(slug or ""))
    return int(m.group(1)) if m else None


sb = {e["id"]: e for e in json.loads((SB / "manifest.json").read_text(encoding="utf-8"))["entries"]}
pr = {e["id"]: e for e in json.loads((PROD / "manifest.json").read_text(encoding="utf-8"))["entries"]}
gs, gp = {}, {}
for r in csv.DictReader((GEN / "docs/reports/subunit_gt_FR.csv").open(encoding="utf-8-sig", newline="")):
    if r["scorable"] == "yes":
        gs[r["entry_id"]] = ({r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))) if r["gold_subunit"] else {""}
        gp[r["entry_id"]] = r["gold_subunit"]  # rotulo primario (astra 12/09: "aceito" e "primario" sao numeros diferentes)
ROT = f"sandbox {SB.parent.name}"  # astra 12/09: rotulo fixo 'motor puro, 0 chamadas' era falso na run viva
sem_status = sum(1 for eid in sb if eid in pr and not pr[eid].get("revisar"))
print(f"{ROT}: {len(sb)} materiais · produto {len(pr)} (pontuado so nos {len(set(sb) & set(pr))} em comum; sem status no produto: {sem_status})")
print(f"{'material':40} {'secao':6} {'unid sb':8} {'unid prod':9} {'sub sb':26} {'sub prod':26} {'gold sub':22} {'revisar sb':10}")
U = {"n": 0, "ok": 0, "conf_ok": 0, "conf_err": 0, "fila_ok": 0, "fila_err": 0, "prim": 0}
S = dict(U); Pu = dict(U); Ps = dict(U)
for eid, e in sb.items():
    p = pr.get(eid, {})
    us, up = e.get("computed_unit_slug") or "", p.get("computed_unit_slug") or ""
    ss, sp = e.get("computed_subunit_slug") or "", p.get("computed_subunit_slug") or ""
    sec = unidade_da_secao(e.get("source_section"))
    fila = (e.get("revisar") or "ok") != "ok"
    fila_p = (p.get("revisar") or "ok") != "ok"
    def conta(d, ok, fila):
        d["n"] += 1; d["ok"] += ok
        d["conf_ok" if ok else "conf_err"] += (not fila); d["fila_ok" if ok else "fila_err"] += fila
    if sec is not None:
        conta(U, num(us) == sec, fila); conta(Pu, num(up) == sec, fila_p)
    if eid in gs:
        conta(S, ss in gs[eid], fila); conta(Ps, sp in gs[eid], fila_p)
        S["prim"] += ss == gp[eid]; Ps["prim"] += sp == gp[eid]
    print(f"{eid[:40]:40} {('U' + str(sec)) if sec else '-':6} {(str(num(us)) if us else '-'):8} {(str(num(up)) if up else '-'):9} "
          f"{(ss or '(vazio)')[:26]:26} {(sp or '(vazio)')[:26]:26} {('/'.join(sorted(gs[eid])) or '(vazio)')[:22] if eid in gs else '-':22} {e.get('revisar') or 'ok'}")


def linha(rot, d, prim=False):
    conf = d["conf_ok"] + d["conf_err"]
    print(f"  {rot:34} acerto {d['ok']}/{d['n']}" + (f" (primario {d['prim']}/{d['n']})" if prim else "") +
          f" · precisao do confiante {d['conf_ok']}/{conf} · erros confiantes {d['conf_err']} · fila {d['fila_ok'] + d['fila_err']} (pega {d['fila_err']} erros)")


print("== unidade contra a secao do professor (U1/U2), sem gold — reproducao do sinal explicito, nao validacao semantica (astra 12/09)")
linha(ROT, U); linha("produto (vocab LLM + 13 votos)", Pu)
print("== subunidade contra subunit_gt_FR (18): 'acerto' aceita as alternativas do gold; 'primario' so o rotulo principal")
linha(ROT, S, prim=True); linha("produto (vocab LLM + 13 votos)", Ps, prim=True)
