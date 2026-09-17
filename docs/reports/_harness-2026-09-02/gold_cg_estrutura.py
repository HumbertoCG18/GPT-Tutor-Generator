"""Item 2: gold de BLOCO do CG derivado da ESTRUTURA (secoes numeradas do Moodle <-> blocos de aula do SARC),
para o user revisar. A auditoria de 02/09 mostrou que a posicao do professor = verdade (148/148); o CG nao tem
labels datados, mas tem secoes tematicas numeradas ("3 - Fundamentos Matematicos…") que casam o topico do SARC.
Regra: secao -> bloco(s) de AULA cujo topic_text partilha >= 2 tokens especificos com o titulo da secao (ou 1 token
raro); materiais da secao -> esse bloco. Exatamente 1 bloco = scorable yes; 0 ou 2+ = scorable no + nota.
Saida: docs/reports/ground_truth_CG.csv (mesmas colunas dos outros) + resumo."""
import csv, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GEN))
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.sources.moodle import sanitize_folder_name  # noqa: E402

repo = GEN.parent / "Computacao-Grafica-Tutor"
contents = json.loads((Path(__file__).resolve().parent / "moodle_contents" / "CG.json").read_text(encoding="utf-8"))
tl = json.loads((repo / "course/.timeline_index.json").read_text(encoding="utf-8"))
man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
STOP = {"para", "com", "de", "do", "da", "dos", "das", "em", "e", "a", "o", "ao", "computacao", "grafica", "introducao", "exercicios", "atividades", "sobre"}


def toks(t):
    return {x for x in normalize_match_text(str(t or "")).split() if len(x) >= 3 and x not in STOP}


blocks = [b for b in tl["blocks"] if str(b.get("kind") or "") in ("class", "overview")]
bt = {b["id"]: toks(str(b.get("topic_text") or "") + " " + str(b.get("primary_topic_label") or "")) for b in blocks}
# df dos tokens entre blocos (token raro = discriminante)
df = {}
for s in bt.values():
    for t in s:
        df[t] = df.get(t, 0) + 1
rows, resumo = [], []
mats = {str(e.get("source_section") or ""): [] for e in man["entries"]}
for e in man["entries"]:
    if e.get("file_type") == "pdf" or e.get("category"):
        mats[str(e.get("source_section") or "")].append(e)
for s in contents:
    name = str(s.get("name") or "")
    m = re.match(r"^\s*(\d{1,2})\s*-\s*(.+)$", name)
    if not m:
        continue
    folder = sanitize_folder_name(name)
    ents = mats.get(folder, [])
    st = toks(m.group(2))
    cands = []
    for bid, s_ in bt.items():
        inter = st & s_
        score = sum(2 if df.get(t, 9) == 1 else 1 for t in inter)
        if len(inter) >= 2 or (len(inter) == 1 and len(st) == 1):   # 1 token so decide se o titulo da secao e 1 token
            cands.append((score, bid, sorted(inter)))
    cands.sort(reverse=True)
    top = [c for c in cands if c[0] == cands[0][0]] if cands else []
    escolha = top[0][1] if len(top) == 1 else ""
    resumo.append((m.group(1), m.group(2)[:40], len(ents), [(c[1], c[0], c[2]) for c in cands[:3]], escolha))
    for e in ents:
        bl = next((b for b in tl["blocks"] if b["id"] == escolha), None) if escolha else None
        rows.append({"id": e["id"], "material": Path(str(e.get("source_path") or "")).name, "true_block_id": escolha,
                     "computed_block_id": "", "temporal_block_id": "", "pair_key": "", "provenance": "estrutura:secao-moodle->topico-sarc (proposto-claude 02/09, REVISAR)",
                     "scope": "clean", "data_real": (str(bl.get("period_start") or "")[5:10] if bl else ""),
                     "scorable": "yes" if escolha else "no",
                     "discriminante": "no", "true_block_uuid": (bl.get("block_uuid") if bl else ""),
                     "nota": "" if escolha else ("secao sem bloco casado" if not cands else f"ambiguo: {[c[1] for c in top]}")})
out = GEN / "docs/reports/ground_truth_CG.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("secao -> candidatos (bloco, score, tokens) -> escolha")
for r in resumo:
    print(f"  {r[0]:>2} {r[1]:40} mats={r[2]:>2} {r[3]} -> {r[4] or '(nao)'}")
ok = sum(1 for r in rows if r["scorable"] == "yes")
print(f"\n{out}: {len(rows)} materiais de secoes numeradas, {ok} com bloco unico (scorable yes), {len(rows) - ok} para revisar")
