"""H7 (read-only): ORDEM DAS SECOES do Moodle como prior estrutural para cards SEM data.

Le raw/moodle/sections.json (moodle_pull --dry-run, raiz temporaria) -> {card: section_index}.
Ancoras = cards cujos entries tem janela por data (providers labels/data/ordinal): faixa
[min_idx, max_idx] dos blocos das janelas. Card sem data (provider topic) com secao s:
    lo = max(max_idx das ancoras com secao < s) ; hi = min(min_idx das ancoras com secao > s)
janela estreitada = janela atual ∩ [lo, hi]; 1 bloco -> janela-1; >1 -> disambiguate() de producao.
Mede: premissa (gold dentro de [lo,hi]?), ganho/perda vs pred atual, e quantos viram janela-1.
"""
import collections, json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GEN = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
from eval_ground_truth import load_labels_csv, load_predictions  # noqa: E402
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from src.builder.routing.motor.disambiguator import disambiguate  # noqa: E402
from src.builder.sources.moodle import sanitize_folder_name  # noqa: E402

COPY = GEN / ".ablacao"
CHAIN = "--chain" in sys.argv
ONLY_FLAGGED = "--only-flagged" in sys.argv
PICKS = {}
PULL = Path(__file__).resolve().parent / "moodle_sections"   # <SIG>.json (moodle_pull --dry-run, 02/09)
REPOS = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
DATED = {"labels", "data", "ordinal"}
UTIL = __import__("re").compile(r"tde|informa|plano|revis|geral|aviso|trabalho|apresenta", __import__("re").I)


def bid(b):
    return str(b.get("id") or "")


tot = collections.Counter(); det = []
for sig, nome in REPOS.items():
    sj = PULL / f"{sig}.json"
    if not sj.exists():
        print(f"== {sig}: sem sections.json em {sj}"); continue
    secs = json.loads(sj.read_text(encoding="utf-8"))
    sec_idx = {sanitize_folder_name(str(s.get("secao") or "")): int(s.get("section") or 0) for s in secs}
    repo = COPY / nome
    man = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    ctx = build_motor_context(repo, str((man.get("course") or {}).get("course_name") or ""))
    order = {bid(b): i for i, b in enumerate(ctx.blocks)}
    ents = {e["id"]: e for e in man["entries"]}
    preds = load_predictions(repo); labels = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv")
    # ancoras por card (TODOS os materiais, nao so golds)
    anch = {}
    for e in man["entries"]:
        card = str(e.get("source_section") or "")
        if not card or UTIL.search(card) or str(e.get("temporal_block_provider") or "") not in DATED:
            continue
        idxs = [order[bid(b)] for b in (ctx.block_by_ref(r) for r in (e.get("temporal_block_window") or [])) if b is not None]
        if not idxs:
            continue
        lo, hi = anch.get(card, (10**9, -1))
        anch[card] = (min(lo, min(idxs)), max(hi, max(idxs)))
    card_win = {}; undated = set()
    for e in man["entries"]:
        c = str(e.get("source_section") or "")
        if c and str(e.get("temporal_block_provider") or "") == "topic" and c not in anch:
            undated.add(c)
            card_win.setdefault(c, set()).update(order[bid(b)] for b in (ctx.block_by_ref(r) for r in (e.get("temporal_block_window") or [])) if b is not None)
    cards_secao = sorted({str(e.get("source_section") or "") for e in man["entries"] if e.get("source_section")}, key=lambda c: sec_idx.get(c, 999))
    print(f"== {sig}: secoes do Moodle (ordem) -> card [ancora]:")
    for c in cards_secao:
        a = anch.get(c); print(f"   s{sec_idx.get(c, '?'):>2} {c[:44]:44} {('bloco-%02d..bloco-%02d' % (a[0]+1, a[1]+1)) if a else '(sem data)'}")
    for eid, gold in labels.items():
        e = ents.get(eid); p = preds.get(eid)
        if not e or not p or str(e.get("temporal_block_provider") or "") != "topic":
            continue
        card = str(e.get("source_section") or ""); s = sec_idx.get(card)
        if s is None:
            tot["card sem secao"] += 1; continue
        if card in anch:
            lo, hi = anch[card]; fonte = "proprio card"
        else:
            lo = max([a[1] for c, a in anch.items() if sec_idx.get(c, 999) < s], default=-1)
            hi = min([a[0] for c, a in anch.items() if sec_idx.get(c, -1) > s], default=10**9)
            fonte = "vizinhos"
            if CHAIN:
                # ordem encadeada entre cards SEM data: os que vem antes (por secao) nao podem passar
                # do min da janela deste; os que vem depois nao podem ficar antes do max deste.
                for c2 in undated:
                    s2 = sec_idx.get(c2, 999)
                    w2 = card_win.get(c2, [])
                    if not w2 or c2 == card: continue
                    if s2 < s: lo = max(lo, min(w2))          # card anterior sem data: comeca antes de mim
                    if s2 > s: hi = min(hi, max(w2))          # card posterior sem data: termina depois de mim
        win = [str(w) for w in (e.get("temporal_block_window") or [])]
        blocks = [b for b in (ctx.block_by_ref(r) for r in win) if b is not None]
        narrowed = [b for b in blocks if lo <= order[bid(b)] <= hi]
        gold_idx = order.get(gold)
        premissa = gold_idx is not None and lo <= gold_idx <= hi
        tot["golds sem data"] += 1; tot["premissa ok"] += premissa
        if ONLY_FLAGGED and not bool(e.get("temporal_block_flag")):
            pick = p["block_id"]; how = "sem efeito"   # decisao confiante: prior nao sobrepoe
        elif not narrowed or len(narrowed) == len(blocks):
            pick = p["block_id"]; how = "sem efeito"
        elif len(narrowed) == 1:
            pick = bid(narrowed[0]); how = "janela-1"
        else:
            md = _entry_markdown_text_for_file_map(repo, e) or ""
            d = disambiguate(e, [str(b.get("block_uuid") or bid(b)) for b in narrowed], ctx, md, provider="topic")
            pick = bid(ctx.block_by_ref(d.block_ref) or {}) or d.block_ref; how = f"disamb {len(blocks)}->{len(narrowed)}"
        ok0, ok1 = p["block_id"] == gold, pick == gold
        if how != "sem efeito": PICKS[f"{sig}|{eid}"] = pick
        tot[how.split()[0]] += 1
        if ok1 and not ok0: tot["ganho"] += 1
        elif ok0 and not ok1: tot["perda"] += 1
        det.append((sig, eid, card[:30], f"[{lo+1},{hi+1 if hi < 10**8 else '∞'}]{fonte[0]}", len(blocks), len(narrowed), how, gold, p["block_id"], pick, premissa, ok0, ok1))
print(f"\nGOLDS em cards sem data: {tot['golds sem data']} | premissa 'secoes seguem o semestre' vale em {tot['premissa ok']} | "
      f"janela-1: {tot['janela-1']} · disamb estreitado: {tot['disamb']} · sem efeito: {tot['sem']}")
print(f"GANHO {tot['ganho']}  PERDA {tot['perda']}  (card sem secao: {tot['card sem secao']})")
print(f"\n{'c':3} {'entry':38} {'card':30} {'faixa':10} {'jan':>3}{'->':>3} {'como':16} {'gold':9} {'pred':9} {'novo':9} prem ok0 ok1")
for r in det:
    print(f"{r[0]:3} {r[1][:38]:38} {r[2]:30} {r[3]:10} {r[4]:>3}{r[5]:>3} {r[6]:16} {r[7]:9} {r[8]:9} {r[9]:9} {str(r[10])[0]:4} {str(r[11])[0]:3} {str(r[12])[0]}")

json.dump(PICKS, open(PULL / "picks_h7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("picks gravados:", len(PICKS))
