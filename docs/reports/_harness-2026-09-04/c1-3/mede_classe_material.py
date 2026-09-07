"""Onde o erro de subunidade MORA: acerto por classe de material (tamanho do texto que o motor pontua, categoria,
fonte do arquivo, tem PDF/imagem). 6 golds, produto em disco, 0 chamadas. Uso: mede_classe_material.py"""
import collections
import csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
REPOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor"}
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder import engine as eng  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text  # noqa: E402

CASOS = []
for sig, repo in REPOS.items():
    root = GH / repo
    man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    cc = root / "code_curation.json"
    code_cur = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {}
    rows = [r for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]
    for r in rows:
        e = man.get(r["entry_id"])
        if not e:
            continue
        md = eng._entry_markdown_text_for_file_map(root, e) or ""
        rec = (code_cur.get("entries") or {}).get(str(e.get("id") or "")) or {}
        resumo = code_curation_signal_text(rec) if rec else ""
        t = f"{md}\n\n{resumo}" if md and resumo else (md or resumo)
        alvo = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
        src = str(e.get("source_url") or e.get("url") or "")
        arq = str(e.get("source_path") or e.get("path") or e.get("filename") or "")
        ext = Path(arq).suffix.lower() or ("(url)" if src else "(sem arquivo)")
        CASOS.append(dict(sig=sig, id=r["entry_id"], ok=str(e.get("computed_subunit_slug") or "") in alvo,
                          n=len(t), cat=str(e.get("category") or "?"), ext=ext,
                          video=bool("youtu" in src.lower() or "video" in r["entry_id"].lower()),
                          aprovado=bool(e.get("approved_markdown") or e.get("curated_markdown"))))


def tabela(titulo, chave, ordem=None):
    print(f"\n{titulo}")
    g = collections.defaultdict(list)
    for c in CASOS:
        g[chave(c)].append(c)
    print(f"   {'grupo':28} {'n':>4} {'certos':>7} {'%':>5}  erros por curso")
    for k in (ordem or sorted(g, key=lambda x: -len(g[x]))):
        if k not in g:
            continue
        v = g[k]
        ok = sum(1 for c in v if c["ok"])
        err = collections.Counter(c["sig"] for c in v if not c["ok"])
        print(f"   {str(k):28} {len(v):4} {ok:7} {100 * ok / len(v):4.0f}%  {dict(err.most_common()) if err else ''}")


FAIXAS = [(0, 500), (500, 1500), (1500, 3000), (3000, 8000), (8000, 20000), (20000, 10 ** 9)]


def faixa(c):
    for lo, hi in FAIXAS:
        if lo <= c["n"] < hi:
            return f"{lo}-{hi if hi < 10 ** 8 else '+'} chars"
    return "?"


tot = len(CASOS)
print(f"233 scorable -> {sum(1 for c in CASOS if c['ok'])}/{tot}")
tabela("POR TAMANHO DO TEXTO QUE O MOTOR PONTUA", faixa, [f"{lo}-{hi if hi < 10 ** 8 else '+'} chars" for lo, hi in FAIXAS])
tabela("POR CATEGORIA", lambda c: c["cat"])
tabela("POR EXTENSAO / FONTE", lambda c: c["ext"])
tabela("VIDEO (url youtube ou id com 'video')", lambda c: "video" if c["video"] else "nao-video")
tabela("APROVADO NO CURATOR STUDIO", lambda c: "aprovado" if c["aprovado"] else "staging")
tabela("CG isolado: tamanho", lambda c: faixa(c) if c["sig"] == "CG" else None,
       [f"{lo}-{hi if hi < 10 ** 8 else '+'} chars" for lo, hi in FAIXAS])
