"""C1 item 1, passo 1 (read-only): projeta o FILE_MAP 'completo e magro' nos 8 tutores a partir das linhas JA renderizadas
(larguras reais por coluna) e do manifest (todos os materiais, labels do Moodle). Variantes: ATUAL sem clamp; MAGRO = sem linha
de rastreabilidade (vai para FILE_MAP_TRACE.md) + Secoes <= 3 headers/80 chars + titulo = moodle_label (fallback title)."""
import json, re, statistics, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GH = Path("..")
T = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor", "Engenharia-Software-2-Tutor",
     "TCC-Tutor", "Laboratorio-de-Redes-Tutor", "Fundamentos-de-Redes-Tutor", "Computacao-Grafica-Tutor"]
SEC_MAX_H, SEC_MAX_CH = 3, 80
def label_of(e):
    ml = e.get("moodle_label"); ml = ml.get("text") if isinstance(ml, dict) else ml
    return str(ml or "").strip()
def cap_sections(s):
    parts = [p for p in re.split(r"\s{2,}", s.strip()) if p]
    out = "  ".join(parts[:SEC_MAX_H])
    return out[:SEC_MAX_CH]
tot = {"atual": 0, "magro": 0, "trace": 0, "n": 0, "titulo_muda": 0}
print(f"{'tutor':26} {'N':>3} | {'linha':>5} {'rastr':>5} {'secoes':>6} | {'ATUAL':>7} {'MAGRO':>7} {'TRACE':>6} | cabe80K  titulo->label")
for name in T:
    R = GH / name
    es = json.load(open(R / "manifest.json", encoding="utf-8"))["entries"]
    fm = (R / "course/FILE_MAP.md").read_text(encoding="utf-8").splitlines()
    rows = [l for l in fm if re.match(r"\| \d+ \|", l)]
    traces = [l for l in fm if "↳ rastreabilidade" in l]
    header = sum(len(l) + 1 for l in fm if not (re.match(r"\| \d+ \|", l) or "↳ rastreabilidade" in l))
    cols = [[c.strip() for c in r.split("|")[1:-1]] for r in rows]
    row_len = statistics.mean(len(r) for r in rows); tr_len = statistics.mean(len(t) for t in traces) if traces else 0
    sec_len = statistics.mean(len(c[6]) for c in cols); sec_cap = statistics.mean(len(cap_sections(c[6])) for c in cols)
    title_len = statistics.mean(len(c[1]) for c in cols)
    labels = [label_of(e) or str(e.get("title") or "") for e in es]
    lab_len = statistics.mean(len(x) for x in labels)
    n = len(es)
    atual = header + n * (row_len + 1) + len(traces) / max(len(rows), 1) * n * (tr_len + 1)
    magro = header + n * (row_len - sec_len + sec_cap - title_len + lab_len + 1)
    trace = 400 + len(traces) / max(len(rows), 1) * n * (tr_len + 1)
    muda = sum(1 for e in es if label_of(e) and label_of(e) != str(e.get("title") or ""))
    for k, v in (("atual", atual), ("magro", magro), ("trace", trace), ("n", n), ("titulo_muda", muda)): tot[k] += v
    print(f"{name[:26]:26} {n:3} | {row_len:5.0f} {tr_len:5.0f} {sec_len:6.0f} | {atual/1024:6.1f}K {magro/1024:6.1f}K {trace/1024:5.1f}K | {'sim' if magro <= 80*1024 else 'NAO':7}  {muda}/{n}")
print(f"{'TOTAL':26} {tot['n']:3} | {'':5} {'':5} {'':6} | {tot['atual']/1024:6.1f}K {tot['magro']/1024:6.1f}K {tot['trace']/1024:5.1f}K | titulo muda {tot['titulo_muda']}/{tot['n']}")
# distribuicao das Secoes: quantas linhas renderizadas passam de 80 chars / de 3 headers (dado real, so nas linhas que existem)
allsec = []
for name in T:
    fm = (GH / name / "course/FILE_MAP.md").read_text(encoding="utf-8").splitlines()
    allsec += [[c.strip() for c in r.split("|")[1:-1]][6] for r in fm if re.match(r"\| \d+ \|", r)]
print(f"Secoes nas {len(allsec)} linhas renderizadas: >80 chars {sum(1 for s in allsec if len(s) > 80)} | >3 headers {sum(1 for s in allsec if len([p for p in re.split(chr(32)*2 + '+', s) if p]) > 3)} | vazias {sum(1 for s in allsec if not s)} | max {max(len(s) for s in allsec)} chars")
