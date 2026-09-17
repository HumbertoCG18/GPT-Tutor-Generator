"""TETO da alavanca "titulo do video no lugar do hash": 91% dos 246 links de video no markdown dos 8 tutores tem como
rotulo o ID de 11 chars (`[wpf5FVADpLw](https://youtu.be/wpf5FVADpLw)`) — hash aleatorio ocupando o lugar do titulo.

Mede em memoria, nos 6 golds: troca `[ID](url)` por `[titulo real](url)` no texto que o motor pontua e roda a 1a passada
+ compara com o gravado. Titulos vem do oEmbed publico do YouTube (sem chave, sem LLM), com cache em disco.
Uso: mede_titulo_video.py [--sem-rede]
"""
import collections
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
CACHE = GEN / "docs/reports/_harness-2026-09-04/c1-3/titulos_video.json"
GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
SEM_REDE = "--sem-rede" in sys.argv
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import functools  # noqa: E402

from src.builder import engine as eng  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.routing import file_map as fm  # noqa: E402
from src.builder.timeline.index import TopicMatchResult  # noqa: E402

MDLINK = re.compile(r"\[([A-Za-z0-9_-]{11})\]\((https?://(?:youtu\.be/|www\.youtube\.com/watch\?v=)([A-Za-z0-9_-]{11})[^)\s]*)\)")
sub_fn = functools.partial(fm.auto_map_entry_subtopic, collect_entry_unit_signals=eng._collect_entry_unit_signals,
                           iter_content_taxonomy_topics=eng._iter_content_taxonomy_topics,
                           score_entry_against_taxonomy_topic=eng._score_entry_against_taxonomy_topic,
                           topic_match_result_factory=TopicMatchResult)
titulos = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def titulo(vid: str) -> str:
    if vid in titulos or SEM_REDE:
        return titulos.get(vid, "")
    url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode({"url": f"https://youtu.be/{vid}", "format": "json"})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
            titulos[vid] = str(json.loads(r.read().decode("utf-8")).get("title") or "")
    except Exception:
        titulos[vid] = ""
    time.sleep(0.15)
    return titulos[vid]


CASOS = []
for sig, repo in GOLD.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = load_internal_content_taxonomy(root)
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    for r in rows:
        e = man.get(r["entry_id"])
        if not e:
            continue
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        if not MDLINK.search(md):
            continue
        rec = (code_cur.get("entries") or {}).get(str(e.get("id") or "")) or {}
        resumo = code_curation_signal_text(rec) if rec else ""
        vids = [m[2] for m in MDLINK.findall(md)]
        for v in vids:
            titulo(v)
        novo_md = MDLINK.sub(lambda m: f"[{titulos.get(m.group(3)) or m.group(1)}]({m.group(2)})", md)
        CASOS.append(dict(sig=sig, id=r["entry_id"], entry=e, tax=tax, root=root, nvid=len(vids),
                          alvo={r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";"))),
                          pred=str(e.get("computed_subunit_slug") or ""), unit=str(e.get("computed_unit_slug") or ""),
                          antes=(f"{md}\n\n{resumo}" if md and resumo else (md or resumo)),
                          depois=(f"{novo_md}\n\n{resumo}" if novo_md and resumo else (novo_md or resumo))))
CACHE.write_text(json.dumps(titulos, ensure_ascii=False, indent=0), encoding="utf-8")
achados = sum(1 for v in titulos.values() if v)
print(f"titulos: {achados}/{len(titulos)} recuperados (cache {CACHE.name})")
print(f"materiais de gold com link de video: {len(CASOS)} · videos {sum(c['nvid'] for c in CASOS)}")
base = sum(1 for c in CASOS if c["pred"] in c["alvo"])
print(f"acerto atual nesses: {base}/{len(CASOS)}\n")

print(f"{'':4} {'material':34} {'vid':>4} {'gravado':22} {'1a passada c/ titulo':22} {'gold':22}")
ganha = perde = igual = 0
for c in sorted(CASOS, key=lambda x: (x["sig"], x["id"])):
    m = sub_fn(c["entry"], c["tax"], c["depois"], winning_unit_slug=c["unit"])
    novo = str(m.topic_slug or "")
    ok_antes, ok_dep = c["pred"] in c["alvo"], novo in c["alvo"]
    if novo == c["pred"]:
        igual += 1
        continue
    sinal = "+" if (ok_dep and not ok_antes) else "-" if (ok_antes and not ok_dep) else "~"
    ganha += sinal == "+"
    perde += sinal == "-"
    print(f"{sinal} {c['sig']:3} {c['id'][:34]:34} {c['nvid']:4} {c['pred'][-22:] or '-':22} {novo[-22:] or '-':22} {(list(c['alvo'])[0] or '(vazio)')[-22:]:22}")
print(f"\nsem mudanca {igual} · muda {len(CASOS) - igual} · ganha {ganha} · perde {perde}")
print("NOTA: comparacao contra a 1a passada isolada; a 2a passada e as regras podem mover o resultado final.")
