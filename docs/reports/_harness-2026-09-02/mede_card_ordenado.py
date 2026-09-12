"""RAIZ (read-only): o card do Moodle lido como DOCUMENTO ORDENADO (core_course_get_contents), nao como saco.

Itens da secao em ordem: label DATADO ("Semana dd/mm/aaaa a dd/mm/aaaa: (dd/mm/aaaa): topico; (dd/mm): topico"),
modulo com DATA no nome ("12/03 Processos"), material (resource/folder), url (ignorado).
Regras (uma so, geral):
  * um "run" de labels datados consecutivos = lista de semanas W1..Wk (ES2 intercala: k=1; MF empilha no topo: k=5);
  * os materiais que seguem o run (ate o proximo run) sao alinhados MONOTONICAMENTE a W1..Wk (DP: ordem dos materiais
    nao volta no tempo), score = sobreposicao de tokens (titulo + nome do modulo) com o texto da semana + assinatura SARC
    do bloco daquela data; empate -> semana mais cedo;
  * material com data no proprio nome ancora ali (e ancora os seguintes sem data ate a proxima ancora);
  * secao sem nenhuma ancora -> sem opiniao (mantem a predicao atual).
Data -> bloco: sessao do .timeline_index com aquela data; senao bloco cujo periodo contem a data.
Mede nos golds: predicao 'card ordenado' vs gold vs predicao atual (motor puro), em TODOS e so nos flagados.
"""
import collections, json, re, sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.motor.disambiguator import _toks, _block_signature  # noqa: E402
from src.builder.text.normalize import normalize_match_text  # noqa: E402
from src.builder.sources.moodle import sanitize_folder_name  # noqa: E402
from src.builder.timeline.kinds import NEVER_HOSTS_MATERIAL_KINDS  # noqa: E402
STREAM = '--stream' in sys.argv
SECWEEK = '--secweek' in sys.argv

PULL = Path(__file__).resolve().parent / "moodle_contents"   # <SIG>.json = raw/moodle/contents.json (moodle_pull --dry-run, 02/09)
COPY = GEN / ".ablacao"
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
DATE_FULL = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
DATE_NAME = re.compile(r"^\s*\[?\s*(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b")
ONLY_FLAGGED = "--only-flagged" in sys.argv


def norm(t):
    return " ".join(normalize_match_text(str(t or "")).split())


def bid(b):
    return str(b.get("id") or "")


def hosts(ctx, block_id):
    b = ctx.block_by_ref(block_id) or {}
    k = str(b.get("kind") or "")
    return bool(b) and k not in NEVER_HOSTS_MATERIAL_KINDS and k != "assessment"


def date_to_block(ctx, d: date):
    iso = d.isoformat()
    for b in ctx.blocks:
        if any(str(s.get("date") or "")[:10] == iso for s in (b.get("sessions") or [])):
            return bid(b)
    for b in ctx.blocks:
        ps, pe = str(b.get("period_start") or "")[:10], str(b.get("period_end") or "")[:10]
        if ps and pe and ps <= iso <= pe:
            return bid(b)
    return ""


def blocks_in_range(ctx, d1: date, d2: date):
    a, b = d1.isoformat(), d2.isoformat()
    out = []
    for blk in ctx.blocks:
        ds = [str(s_.get("date") or "")[:10] for s_ in (blk.get("sessions") or [])]
        if any(a <= d <= b for d in ds) and hosts(ctx, bid(blk)):
            out.append(bid(blk))
    return out


def label_weeks(text: str, ctx, year_hint: int):
    """'Semana 04/05/2026 a 08/05/2026: (04/05/2026): logica...' -> [(blocos da semana, texto)]. Sem intervalo: data unica."""
    txt = str(text or "")
    ds = DATE_FULL.findall(txt)
    if not ds:
        return []
    d1 = date(int(ds[0][2]), int(ds[0][1]), int(ds[0][0]))
    d2 = date(int(ds[1][2]), int(ds[1][1]), int(ds[1][0])) if len(ds) > 1 and re.search(r"\d{1,2}/\d{1,2}/\d{4}\s*a\s*\d{1,2}/\d{1,2}/\d{4}", txt) else d1
    if d2 < d1:
        d1, d2 = d2, d1
    blocks = blocks_in_range(ctx, d1, d2)
    if not blocks:
        b = date_to_block(ctx, d1)
        blocks = [b] if b and hosts(ctx, b) else []
    return [(blocks, txt)] if blocks else []


def sig_text(ctx, block_id):
    b = ctx.block_by_ref(block_id) or {}
    return " ".join(sorted(_block_signature(b, ctx))) if b else ""


def align(materials, weeks, ctx):
    """DP monotonico por FLUXO (categoria): materiais (ordem) -> semanas (ordem)."""
    if not weeks or not materials:
        return {}
    if STREAM:
        out = {}
        groups = collections.defaultdict(list)
        for mid, name, stream in materials:
            groups[stream].append((mid, name))
        for g in groups.values():
            out.update(_align(g, weeks, ctx))
        return out
    return _align([(mid, name) for mid, name, _ in materials], weeks, ctx)


def _align(materials, weeks, ctx):
    if not weeks or not materials:
        return {}
    W = [(bl, _toks(txt + " " + " ".join(sig_text(ctx, b) for b in bl))) for bl, txt in weeks]
    M = [(mid, _toks(name)) for mid, name in materials]
    n, k = len(M), len(W)
    NEG = float("-inf")
    dp = [[NEG] * k for _ in range(n)]; back = [[-1] * k for _ in range(n)]
    def sc(i, j):
        return len(M[i][1] & W[j][1]) - 0.001 * j
    for j in range(k):
        dp[0][j] = sc(0, j)
    for i in range(1, n):
        best, bj = NEG, -1
        for j in range(k):
            if dp[i - 1][j] > best + 1e-12:
                best, bj = dp[i - 1][j], j
            if best > NEG:
                dp[i][j] = best + sc(i, j); back[i][j] = bj
    j = max(range(k), key=lambda j: dp[n - 1][j])
    out = {}
    for i in range(n - 1, -1, -1):
        out[M[i][0]] = list(W[j][0])      # blocos da semana escolhida
        j = back[i][j] if i > 0 else j
    return out


def pick_in_week(eid, blocks, ctx, ent_by_id, repo):
    if len(blocks) == 1:
        return blocks[0]
    e = ent_by_id.get(eid)
    if not e:
        return blocks[0]
    from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
    from src.builder.routing.motor.disambiguator import disambiguate
    md = _entry_markdown_text_for_file_map(repo, e) or ""
    refs = [str((ctx.block_by_ref(b) or {}).get("block_uuid") or b) for b in blocks]
    d = disambiguate(e, refs, ctx, md, provider="labels")
    return bid(ctx.block_by_ref(d.block_ref) or {}) or blocks[0]


tot = collections.Counter(); det = []
for sig, nome in REPOS.items():
    cj = PULL / f"{sig}.json"
    if not cj.exists():
        print(f"== {sig}: sem contents.json"); continue
    contents = json.loads(cj.read_text(encoding="utf-8"))
    repo = COPY / nome
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    year = max((int(m.group(3)) for b in ctx.blocks for m in [DATE_FULL.search(str(b.get("period_start") or "").replace("-", "/")[::-1])] if m), default=2026)
    year = int(str(ctx.blocks[0].get("period_start") or "2026")[:4]) if ctx.blocks else 2026
    ents = man["entries"]
    by_label = collections.defaultdict(list); by_fn = collections.defaultdict(list); by_stem = collections.defaultdict(list)
    for e in ents:
        ml = e.get("moodle_label"); ml = ml.get("text", "") if isinstance(ml, dict) else str(ml or "")
        if ml: by_label[norm(ml)].append(e["id"])
        sp = Path(str(e.get("source_path") or ""))
        if sp.name: by_fn[sp.name.lower()].append(e["id"]); by_stem[norm(sp.stem)].append(e["id"])
    preds = load_predictions(repo); labels_gold = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    ent_by_id = {e["id"]: e for e in ents}
    pred_card = {}   # entry id -> bloco pelo card ordenado
    sec_stats = collections.Counter()
    for s in contents:
        mods = s.get("modules") or []
        sec_folder = sanitize_folder_name(str(s.get("name") or ""))
        in_sec = {e["id"] for e in ents if str(e.get("source_section") or "") == sec_folder}
        # sequencia de itens
        items = []   # ("week", [(bloco, topico)]) | ("mat", [entry ids], name) | ("anchor", bloco, [entry ids], name)
        for m in mods:
            mn = m.get("modname"); name = str(m.get("name") or "")
            if mn == "label":
                w = label_weeks(name, ctx, year)
                if w: items.append(("week", w))
                continue
            if mn in ("url", "forum", "assign", "quiz", "page"):
                continue
            ids = [i for i in by_label.get(norm(name), []) if i in in_sec]
            if not ids:
                for ct in m.get("contents") or []:
                    ids += [i for i in by_fn.get(str(ct.get("filename") or "").lower(), []) if i in in_sec]
            if not ids:
                ids = [i for i in by_stem.get(norm(name), []) if i in in_sec]
            ids = list(dict.fromkeys(ids))
            dm = DATE_NAME.match(name)
            if dm:
                dd, mm = int(dm.group(1)), int(dm.group(2))
                try:
                    b = date_to_block(ctx, date(year, mm, dd))
                except ValueError:
                    b = ""
                if b and hosts(ctx, b):
                    items.append(("anchor", [b], ids, name)); continue
            items.append(("mat", ids, name))
        if SECWEEK and not any(it[0] in ("week", "anchor") for it in items):
            wins = set()
            for it in items:
                if it[0] == "mat":
                    for eid in it[1]:
                        for r in (ent_by_id.get(eid, {}).get("temporal_block_window") or []):
                            b = ctx.block_by_ref(str(r))
                            if b and hosts(ctx, bid(b)): wins.add(bid(b))
            order_idx = {bid(b): k for k, b in enumerate(ctx.blocks)}
            wl = sorted(wins, key=lambda x: order_idx.get(x, 999))
            if len(wl) >= 2:
                items.insert(0, ("week", [(wl, "")]))
        # varredura: runs de semanas; materiais seguintes alinhados
        i = 0
        while i < len(items):
            if items[i][0] == "week":
                weeks = []
                while i < len(items) and items[i][0] == "week":
                    weeks += items[i][1]; i += 1
                mats = []
                while i < len(items) and items[i][0] != "week":
                    it = items[i]
                    if it[0] == "anchor":
                        for eid in it[2]: pred_card[eid] = list(it[1])
                        # ancora vira "semana" corrente para os proximos sem data
                        weeks = [(it[1], it[3])]; mats = []
                    else:
                        for eid in it[1]: mats.append((eid, it[2] + " " + str(ent_by_id.get(eid, {}).get("title") or ""), str(ent_by_id.get(eid, {}).get("category") or "")))
                    i += 1
                    # materiais entre ancoras: alinhar ao run corrente
                    if i < len(items) and items[i][0] == "anchor":
                        pred_card.update(align(mats, weeks, ctx)); mats = []
                pred_card.update(align(mats, weeks, ctx))
                sec_stats["secoes com semanas"] += 1
            elif items[i][0] == "anchor":
                it = items[i]
                for eid in it[2]: pred_card[eid] = list(it[1])
                weeks = [(it[1], it[3])]; mats = []; i += 1
                while i < len(items) and items[i][0] == "mat":
                    for eid in items[i][1]: mats.append((eid, items[i][2], str(ent_by_id.get(eid, {}).get("category") or "")))
                    i += 1
                pred_card.update(align(mats, weeks, ctx))
            else:
                i += 1
    if "--debug" in sys.argv and sig in ("MF", "ES2"):
        for s_ in contents:
            names = [str(m.get("name") or "") for m in (s_.get("modules") or [])]
            if not any(eid in pred_card for m in (s_.get("modules") or []) for eid in by_label.get(norm(str(m.get("name") or "")), [])): continue
            print(f"   --- secao '{s_.get('name')}'")
            for m in s_.get("modules") or []:
                name = str(m.get("name") or ""); mn = m.get("modname")
                if mn == "label":
                    w = label_weeks(name, ctx, year)
                    if w: print(f"      [semana] {' | '.join(f'{b}:{t.strip()[:28]}' for b, t in w)}")
                    continue
                if mn in ("url", "forum", "assign", "quiz", "page"): continue
                ids = by_label.get(norm(name), []) or [i for ct in (m.get("contents") or []) for i in by_fn.get(str(ct.get("filename") or "").lower(), [])] or by_stem.get(norm(name), [])
                for eid in ids:
                    e = ent_by_id.get(eid, {}); g = labels_gold.get(eid, "-"); pk = pred_card.get(eid, "-"); pk = pick_in_week(eid, pk, ctx, ent_by_id, repo) if isinstance(pk, list) else pk; pr = preds.get(eid, {}).get("block_id", "-")
                    mark = "" if g == "-" else ("OK " if pk == g else "ERR") + ("" if pr == g else " (motor tb erra)" if pk != g else " (motor acertava)" if pk != pr else "")
                    print(f"      {mark:22} {name[:34]:34} {str(e.get('category') or '')[:16]:16} card={pk:9} motor={pr:9} gold={g}")
    # medir
    fix = brk = same_ok = same_err = nopin = 0
    for eid, gold in labels_gold.items():
        e = ent_by_id.get(eid); p = preds.get(eid)
        if not e or not p: continue
        ok0 = p["block_id"] == gold
        pk = pred_card.get(eid, "")
        if isinstance(pk, list): pk = pick_in_week(eid, pk, ctx, ent_by_id, repo)
        flag = bool(e.get("temporal_block_flag")) or not e.get("temporal_block_id")
        if ONLY_FLAGGED and not flag:
            pk = ""
        if not pk:
            nopin += 1; tot["sem opiniao"] += 1; tot["sem opiniao ok"] += ok0; continue
        ok1 = pk == gold
        if ok1 and not ok0: fix += 1; det.append((sig, eid, "GANHO", p["block_id"], pk, gold))
        elif ok0 and not ok1: brk += 1; det.append((sig, eid, "PERDA", p["block_id"], pk, gold))
        elif ok0: same_ok += 1
        else: same_err += 1; det.append((sig, eid, "err->err", p["block_id"], pk, gold))
    tot.update({"fix": fix, "brk": brk, "same_ok": same_ok, "same_err": same_err, "n": len(labels_gold)})
    print(f"== {sig}: golds={len(labels_gold)} card-ordenado opina em {len(labels_gold) - nopin} | conserta {fix} quebra {brk} ja-certo {same_ok} erra->erra {same_err} | sem opiniao {nopin}")
print(f"\nTOTAL ({'so flagados' if ONLY_FLAGGED else 'todos'}): conserta {tot['fix']}  quebra {tot['brk']}  ja-certo {tot['same_ok']}  erra->erra {tot['same_err']}  sem opiniao {tot['sem opiniao']} (ok hoje {tot['sem opiniao ok']})")
base = sum(1 for _ in det)  # noop
for r in det:
    print(f"  {r[0]:3} {r[1][:44]:44} {r[2]:9} atual={r[3]:9} card={r[4]:9} gold={r[5]}")
