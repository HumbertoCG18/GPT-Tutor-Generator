"""O texto que FALTA: quantos materiais dependem de conteudo que existe fora do arquivo (pagina do professor linkada,
video do YouTube sem transcricao) e quanto do erro de subunidade mora neles. 8 tutores + 6 golds, 0 chamadas, 0 rede.
Uso: mede_texto_faltante.py"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
GOLD = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
        "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
TODOS = dict(GOLD, LR="Laboratorio-de-Redes-Tutor", FR="Fundamentos-de-Redes-Tutor")
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402

YT = re.compile(r"(?:youtu\.be/|youtube\.com/watch)", re.I)
LINK = re.compile(r"\]\((https?://[^)\s]+)\)")

print("MATERIAIS QUE DEPENDEM DE TEXTO EXTERNO (8 tutores)")
print(f"{'':4} {'mat':>4} {'com-yt':>7} {'videos':>7} {'pag-prof':>9} {'so-links':>9}  (so-links = texto quase todo em URL)")
TOT = collections.Counter()
DETALHE = {}
for sig, repo in TODOS.items():
    root = GH / repo
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    c = collections.Counter()
    det = {}
    for e in man:
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        links = LINK.findall(md)
        yt = [u for u in links if YT.search(u)]
        prof = [u for u in links if not YT.search(u)]
        # "so links": o texto sem as URLs perde mais da metade do corpo
        limpo = LINK.sub(" ", md)
        so_links = bool(links) and len(limpo) < 0.55 * max(1, len(md))
        c["mat"] += 1
        c["com_yt"] += bool(yt)
        c["videos"] += len(yt)
        c["pag_prof"] += bool(prof)
        c["so_links"] += so_links
        det[e["id"]] = (len(yt), len(prof), so_links, len(md))
    DETALHE[sig] = det
    TOT.update(c)
    print(f"{sig:4} {c['mat']:4} {c['com_yt']:7} {c['videos']:7} {c['pag_prof']:9} {c['so_links']:9}")
print(f"{'TOT':4} {TOT['mat']:4} {TOT['com_yt']:7} {TOT['videos']:7} {TOT['pag_prof']:9} {TOT['so_links']:9}")

print("\nQUANTO DO ERRO DE SUBUNIDADE MORA NESSES MATERIAIS (6 golds)")
gr = collections.defaultdict(lambda: [0, 0])
for sig, repo in GOLD.items():
    man = {e["id"]: e for e in json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    for r in rows:
        e = man.get(r["entry_id"])
        if not e:
            continue
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        ok = str(e.get("computed_subunit_slug") or "") in alvo
        nyt, nprof, so_links, n = DETALHE[sig].get(r["entry_id"], (0, 0, False, 0))
        classe = ("so-links (indice)" if so_links else "tem youtube" if nyt else
                  "tem pagina externa" if nprof else "texto proprio")
        gr[classe][0] += 1
        gr[classe][1] += ok
print(f"   {'classe':22} {'n':>4} {'certos':>7} {'%':>5} {'erros':>6}")
for k, (n, ok) in sorted(gr.items(), key=lambda x: x[1][0] - x[1][1], reverse=True):
    print(f"   {k:22} {n:4} {ok:7} {100 * ok / n:4.0f}% {n - ok:6}")
print(f"   {'TOTAL':22} {sum(v[0] for v in gr.values()):4} {sum(v[1] for v in gr.values()):7}")
