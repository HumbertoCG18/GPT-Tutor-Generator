"""SIMULACAO da regra PAI x FILHO (07/09), antes de qualquer codigo no motor: quando o texto cobre VARIOS FILHOS do mesmo
pai com forca comparavel, o material e sobre o conjunto -> sobe para o PAI. Mede ganho/perda nos 6 golds, variando o
limiar de "forca comparavel". Read-only, 0 chamadas. Uso: simula_pai_filho.py"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.extraction.entry_signals import collect_entry_unit_signals  # noqa: E402
from src.builder.timeline.index import _score_entry_against_taxonomy_topic, _iter_content_taxonomy_topics  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
LIMIARES = [(l, m) for l in (0.6, 0.8) for m in (2, 3, 4)]   # (forca relativa, minimo de irmaos fortes)


def pai_de(code: str) -> str:
    partes = str(code or "").strip().rstrip(".").split(".")
    return ".".join(partes[:-1]) if len(partes) > 1 else ""


for limiar, min_irmaos in LIMIARES:
    TOT = Counter()
    detalhe = []
    for sig, repo in REPO.items():
        root = GH / repo
        man = {e["id"]: e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
        tax = json.loads((root / "course/.content_taxonomy.json").read_text(encoding="utf-8"))
        topicos = list(_iter_content_taxonomy_topics(tax) or [])
        por_slug = {t["topic_slug"]: t for t in topicos}
        code_de = {t["slug"]: str(t.get("code") or "").strip().rstrip(".") for u in tax.get("units") or [] for t in u.get("topics") or []}
        slug_por_code = {v: k for k, v in code_de.items() if v}
        for r in csv.DictReader((GEN / "docs/reports" / f"subunit_gt_{sig}.csv").open(encoding="utf-8-sig", newline="")):
            if r["scorable"] != "yes" or r["entry_id"] not in man:
                continue
            e = man[r["entry_id"]]
            got = str(e.get("computed_subunit_slug") or "")
            if not got:
                continue
            code_got = code_de.get(got, "")
            pai = pai_de(code_got)
            slug_pai = slug_por_code.get(pai, "")
            if not slug_pai or slug_pai not in por_slug:
                continue
            # irmaos = topicos cujo pai e o mesmo
            irmaos = [s for s, c in code_de.items() if c and pai_de(c) == pai and s != got]
            if not irmaos:
                continue
            texto = _entry_markdown_text_for_file_map(root, e) or ""
            sinais = collect_entry_unit_signals(e, texto)
            def score(slug):
                t = por_slug.get(slug)
                return _score_entry_against_taxonomy_topic(sinais, t, stem_fallback=True) if t else 0.0
            s_got = score(got)
            if s_got <= 0:
                continue
            fortes = [s for s in irmaos if score(s) >= limiar * s_got]
            if len(fortes) < min_irmaos:
                continue
            aceitos = {r["gold_subunit"]} | set(filter(None, r["gold_subunits_extra"].split(";")))
            antes_ok, depois_ok = got in aceitos, slug_pai in aceitos
            TOT["agiria"] += 1
            TOT["ganha"] += (not antes_ok) and depois_ok
            TOT["perde"] += antes_ok and (not depois_ok)
            TOT["neutro"] += antes_ok == depois_ok
            if antes_ok != depois_ok:
                detalhe.append(f"{'GANHA' if depois_ok else 'PERDE'} {sig} {r['entry_id'][:30]:30} {code_got:8}({len(fortes)} irmaos fortes) -> pai {pai:6} | gold {r['gold_subunit'][:26]}")
    print(f"limiar {limiar:.0%} + >= {min_irmaos} irmaos fortes: agiria em {TOT['agiria']:3} · ganha {TOT['ganha']:2} · perde {TOT['perde']:2} · neutro {TOT['neutro']:3}")
    for d in detalhe[:8]:
        print("     ", d)
