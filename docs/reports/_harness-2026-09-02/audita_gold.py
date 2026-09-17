"""AUDITORIA DO GOLD (read-only): Moodle (posicao do professor) x SARC (cronograma) x gold x motor, lado a lado.

Posicao no Moodle, por material (contents.json da API):
  1. label datado mais proximo ANTES do modulo na secao ("Semana dd/mm/aaaa a dd/mm/aaaa: (dd/mm): topico") -> blocos
     hospedaveis com sessao no intervalo (labels empilhados no topo = uniao das semanas do run);
  2. data no nome do modulo ("12/03 Processos") -> bloco daquela data;
  3. datas no nome da SECAO ("Semana 3 - 16.03 a 20.03") -> blocos no intervalo;
  4. senao: sem posicao datada (card sem data).
Saida: CSV com uma linha por gold (AULA) + resumo: concorda / diverge / sem posicao, e padroes das divergencias.
"""
import collections, csv, json, re, sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.sources.moodle import sanitize_folder_name  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.timeline.kinds import NEVER_HOSTS_MATERIAL_KINDS  # noqa: E402

PULL = Path(__file__).resolve().parent / "moodle_contents"   # <SIG>.json = contents.json
COPY = GEN / ".ablacao"
OUT = Path(__file__).resolve().parent / "auditoria_gold.csv"
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
REF = {"bibliografia", "referencias", "references"}
DATE_FULL = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
DATE_NAME = re.compile(r"^\s*\[?\s*(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b")
SEC_RANGE = re.compile(r"(\d{1,2})[./](\d{1,2})\s*a\s*(\d{1,2})[./](\d{1,2})")


def norm(t):
    return " ".join(normalize_match_text(str(t or "")).split())


def bid(b):
    return str(b.get("id") or "")


def hosts(b):
    k = str(b.get("kind") or "")
    return k not in NEVER_HOSTS_MATERIAL_KINDS and k != "assessment"


def blocks_in_range(ctx, d1, d2):
    a, b_ = d1.isoformat(), d2.isoformat()
    out = []
    for blk in ctx.blocks:
        ds = [str(s.get("date") or "")[:10] for s in (blk.get("sessions") or [])]
        if any(a <= d <= b_ for d in ds) and hosts(blk):
            out.append(bid(blk))
    return out


def sarc_text(ctx, block_id):
    b = ctx.block_by_ref(block_id) or {}
    sess = "; ".join(f"{str(s.get('date') or '')[5:10]} {str(s.get('label') or '')[:38]}" for s in (b.get("sessions") or [])[:3])
    return f"{b.get('kind') or ''} {str(b.get('period_start') or '')[5:10]}..{str(b.get('period_end') or '')[5:10]} | {sess}"


rows = []
for sig, nome in REPOS.items():
    contents = json.loads((PULL / f"{sig}.json").read_text(encoding="utf-8"))
    repo = COPY / nome
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    year = int(str(ctx.blocks[0].get("period_start") or "2026")[:4]) if ctx.blocks else 2026
    order = {bid(b): i for i, b in enumerate(ctx.blocks)}
    ents = man["entries"]; by_id = {e["id"]: e for e in ents}
    preds = load_predictions(repo); gold = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    placement = {}   # eid -> (blocos, fonte, texto_label)
    for s in contents:
        sec_name = str(s.get("name") or ""); sec_folder = sanitize_folder_name(sec_name)
        in_sec = [e for e in ents if str(e.get("source_section") or "") == sec_folder]
        # 3) datas no nome da secao
        sec_blocks = []
        m = SEC_RANGE.search(sec_name)
        mw = re.search(r"semana\s*(\d{1,2})", sec_name, re.I)
        if not m and mw and ctx.blocks:
            from datetime import timedelta
            first_date = min((str(s_.get("date") or "")[:10] for b in ctx.blocks for s_ in (b.get("sessions") or []) if s_.get("date")), default="")
            if first_date:
                d0 = date.fromisoformat(first_date); d0 = d0 - timedelta(days=d0.weekday())
                d1 = d0 + timedelta(days=7 * (int(mw.group(1)) - 1)); d2 = d1 + timedelta(days=6)
                sec_blocks = blocks_in_range(ctx, d1, d2)
                if sec_blocks: sec_name = sec_name + " [semana N do calendario]"
        if m:
            try:
                d1 = date(year, int(m.group(2)), int(m.group(1))); d2 = date(year, int(m.group(4)), int(m.group(3)))
                sec_blocks = blocks_in_range(ctx, min(d1, d2), max(d1, d2))
            except ValueError:
                sec_blocks = []
        run = []          # semanas do run corrente (blocos)
        run_txt = ""
        pending_run = []  # labels consecutivos
        for mod in s.get("modules") or []:
            mn = mod.get("modname"); name = str(mod.get("name") or "")
            if mn == "label":
                ds = DATE_FULL.findall(name)
                if ds:
                    d1 = date(int(ds[0][2]), int(ds[0][1]), int(ds[0][0]))
                    d2 = date(int(ds[1][2]), int(ds[1][1]), int(ds[1][0])) if len(ds) > 1 and re.search(r"\d{4}\s*a\s*\d", name) else d1
                    bl = blocks_in_range(ctx, min(d1, d2), max(d1, d2))
                    if bl:
                        pending_run.append((bl, name[:70]))
                continue
            if mn in ("url", "forum", "assign", "quiz", "page", "label"):
                continue
            if pending_run:
                run = [b for bl, _ in pending_run for b in bl]
                run = list(dict.fromkeys(run)); run_txt = " || ".join(t for _, t in pending_run)
                pending_run = []
            fns = {str(c.get("filename") or "").lower() for c in (mod.get("contents") or [])}
            ids = [e["id"] for e in in_sec if Path(str(e.get("source_path") or "")).name.lower() in fns]
            if not ids:
                stems = {norm(Path(f).stem) for f in fns}
                ids = [e["id"] for e in in_sec if norm(Path(str(e.get("source_path") or "")).stem) in stems]
            if not ids:
                same = [e["id"] for e in in_sec if norm(e.get("moodle_label") if not isinstance(e.get("moodle_label"), dict) else e["moodle_label"].get("text")) == norm(name)]
                n_mod = sum(1 for m2 in (s.get("modules") or []) if norm(m2.get("name")) == norm(name))
                ids = same if (len(same) == 1 or n_mod == 1) else []
            if not ids:
                ids = [e["id"] for e in in_sec if norm(Path(str(e.get("source_path") or "")).stem) == norm(name)]
            dm = DATE_NAME.match(name)
            src = ""; bl = []
            if dm:
                try:
                    b = blocks_in_range(ctx, date(year, int(dm.group(2)), int(dm.group(1))), date(year, int(dm.group(2)), int(dm.group(1))))
                    if b: bl, src = b, f"data no nome ({dm.group(1)}/{dm.group(2)})"
                except ValueError:
                    pass
            if not bl and run:
                bl, src = run, f"label: {run_txt[:60]}"
            if not bl and sec_blocks:
                bl, src = sec_blocks, f"secao: {sec_name[:40]}"
            for eid in ids:
                if eid not in placement:
                    placement[eid] = (bl, src)
    # posicao fraca: irmaos datados do mesmo card (min..max dos blocos) para quem ficou sem posicao
    card_rng = collections.defaultdict(set)
    for eid, (bl, src) in placement.items():
        if bl and not src.startswith("secao:"):
            card_rng[str(by_id.get(eid, {}).get("source_section") or "")].update(bl)
    for e in ents:
        if e["id"] in placement and placement[e["id"]][0]:
            continue
        rng = card_rng.get(str(e.get("source_section") or ""))
        if rng:
            lo, hi = min(order[b] for b in rng), max(order[b] for b in rng)
            bl = [bid(b) for b in ctx.blocks[lo:hi + 1] if hosts(b)]
            placement[e["id"]] = (bl, "irmaos datados do card (faixa)")
    for eid, g in gold.items():
        e = by_id.get(eid)
        if not e:
            continue
        cat = str(e.get("category") or "")
        grupo = "REF" if (cat in REF or e.get("file_type") == "url") else ("BASE" if cat == "cronograma" else "AULA")
        bl, src = placement.get(eid, ([], ""))
        pred = preds.get(eid, {}).get("block_id", "")
        if not bl:
            veredito = "sem posicao datada"
        elif g in bl:
            veredito = "concorda"
        else:
            gi, pi = order.get(g, -1), [order.get(b, -1) for b in bl]
            veredito = "gold DEPOIS da postagem" if gi > max(pi) else "gold ANTES da postagem"
        rows.append({
            "curso": sig, "entry": eid, "grupo": grupo, "categoria": cat, "card": str(e.get("source_section") or ""),
            "posicao_moodle": " ".join(bl), "fonte_posicao": src, "sarc_posicao": " / ".join(sarc_text(ctx, b) for b in bl[:2]),
            "gold": g, "sarc_gold": sarc_text(ctx, g), "motor": pred, "motor_ok": pred == g, "veredito": veredito,
            "label_moodle": str(e.get("moodle_label") or "")[:60], "titulo": str(e.get("title") or "")[:60],
        })

with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
aula = [r for r in rows if r["grupo"] == "AULA"]
c = collections.Counter(r["veredito"] for r in aula)
print(f"AULA: {len(aula)} golds | " + " · ".join(f"{k}: {v}" for k, v in c.most_common()))
print("por curso:", {s: dict(collections.Counter(r["veredito"] for r in aula if r["curso"] == s)) for s in REPOS})
div = [r for r in aula if r["veredito"].startswith("gold ")]
print("\nDIVERGENCIAS gold x posicao do professor (AULA):")
print("por categoria:", dict(collections.Counter(r["categoria"] for r in div)))
print("motor segue: gold", sum(1 for r in div if r["motor_ok"]), "| posicao", sum(1 for r in div if r["motor"] in r["posicao_moodle"].split()), "| nenhum", sum(1 for r in div if not r["motor_ok"] and r["motor"] not in r["posicao_moodle"].split()))
for r in div:
    print(f"\n  {r['curso']} {r['entry']}  [{r['categoria']}]  card={r['card'][:30]!r}  label={r['label_moodle'][:45]!r}")
    print(f"     POSICAO {r['posicao_moodle']:18} <- {r['fonte_posicao'][:70]}")
    print(f"             {r['sarc_posicao'][:150]}")
    print(f"     GOLD    {r['gold']:18} {r['sarc_gold'][:130]}")
    print(f"     motor   {r['motor']} {'= gold' if r['motor_ok'] else ('= posicao' if r['motor'] in r['posicao_moodle'].split() else '')}   -> {r['veredito']}")
print(f"\nCSV: {OUT}")
