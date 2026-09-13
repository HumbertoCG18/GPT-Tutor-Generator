"""O que a ablacao do vocabulario REMOVE: a fonte LLM, ou qualquer termo coincidente? (12/09 noite, item do astra)

O regime "cru" veta os aliases cujo `_norm` esta no sidecar `course/.glossary_curation.llm.json`. Mas a taxonomia nao
guarda proveniencia por alias: se um termo esta no sidecar do LLM **e tambem** aparece no plano de ensino, nos headings
dos materiais ou no sidecar manual, vetar por coincidencia de texto tira junto uma contribuicao do PROFESSOR.

Este script mede o tamanho desse veto excessivo: para cada alias vetado, procura o mesmo texto em tres fontes
independentes do LLM.

  PLANO    o texto do plano de ensino da disciplina (subjects.json -> teaching_plan)
  HEADINGS os headings (#, ##, ###) dos markdowns que o motor pontua
  MANUAL   o sidecar de curadoria humana (`course/.glossary_curation.json`)

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/proveniencia_alias_12-09.py
"""
import json
import re
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
ORIG = GEN.parent
sys.path.insert(0, str(GEN))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.utils.helpers import get_app_data_dir  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
H_RE = re.compile(r"^#{1,3}\s+(.+)$", re.M)


def planos():
    d = json.loads((get_app_data_dir() / "subjects.json").read_text(encoding="utf-8"))
    subs = d if isinstance(d, list) else (d.get("subjects") or list(d.values()))
    out = {}
    for s in subs if isinstance(subs, list) else []:
        if isinstance(s, dict):
            out[str(s.get("name") or "")] = str(s.get("teaching_plan") or "")
    return out


def frase_em(texto_norm, frase):
    n = N(frase or "")
    return bool(n) and re.search(r"(^|\s)" + re.escape(n) + r"(\s|$)", texto_norm) is not None


PL = planos()
print(f"{'curso':5} {'aliases vetados':>16} {'tambem no PLANO':>17} {'nos HEADINGS':>14} {'no sidecar MANUAL':>19} "
      f"{'so no LLM':>11}")
tot = {"v": 0, "p": 0, "h": 0, "m": 0, "so": 0}
detalhe = []
for sig, nm in NOMES.items():
    root = ORIG / nm
    llmp = root / "course/.glossary_curation.llm.json"
    if not llmp.exists():
        continue
    d = json.loads(llmp.read_text(encoding="utf-8"))
    vet = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}
    tax = load_internal_content_taxonomy(root)
    vetados = sorted({a for u in tax["units"] for t in u["topics"] for a in (t.get("aliases") or []) if _norm(a) in vet})
    # plano de ensino do curso
    plano = ""
    for nome_curso, tp in PL.items():
        if nome_curso and (nome_curso[:10].lower() in nm.lower().replace("-", " ") or
                           nm.split("-")[0].lower() in nome_curso.lower()):
            plano = tp
            break
    plano_n = N(plano)
    # headings do acervo
    heads = []
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]
    for e in man:
        rel = str(e.get("base_markdown") or "")
        if not rel:
            continue
        p = root / rel
        if p.exists():
            try:
                heads.extend(H_RE.findall(p.read_text(encoding="utf-8", errors="replace"))[:12])
            except Exception:
                pass
    heads_n = N(" | ".join(heads))
    # sidecar manual
    manp = root / "course/.glossary_curation.json"
    manual = set()
    if manp.exists():
        for k, v in json.loads(manp.read_text(encoding="utf-8")).items():
            if not k.startswith("_"):
                manual |= {_norm(s) for s in (v.get("synonyms") or [])}
    p_ = h_ = m_ = so_ = 0
    for a in vetados:
        emp = frase_em(plano_n, a)
        emh = frase_em(heads_n, a)
        emm = _norm(a) in manual
        p_ += emp; h_ += emh; m_ += emm
        if not (emp or emh or emm):
            so_ += 1
        elif emp or emm:
            detalhe.append((sig, a, "plano" if emp else "", "manual" if emm else "", "headings" if emh else ""))
    print(f"{sig:5} {len(vetados):>16} {p_:>17} {h_:>14} {m_:>19} {so_:>11}")
    tot["v"] += len(vetados); tot["p"] += p_; tot["h"] += h_; tot["m"] += m_; tot["so"] += so_
print(f"{'TOT':5} {tot['v']:>16} {tot['p']:>17} {tot['h']:>14} {tot['m']:>19} {tot['so']:>11}")
print()
print(f"VETO EXCESSIVO = alias que esta no sidecar do LLM mas TAMBEM vem de fonte do professor:")
print(f"  pelo PLANO ou pelo sidecar MANUAL (fontes fortes): {len(detalhe)} de {tot['v']}")
print(f"  contando tambem HEADINGS do acervo: {tot['v'] - tot['so']} de {tot['v']}")
print()
print("Os que vem do PLANO ou da CURADORIA MANUAL (o veto tira contribuicao do professor junto):")
for sig, a, p_, m_, h_ in detalhe[:40]:
    print(f"  {sig:4} {a:52} [{' '.join(x for x in (p_, m_, h_) if x)}]")
print()
print("LEITURA: 'so no LLM' e o veto legitimo. O resto e coincidencia de texto — o termo existe no sidecar do LLM E")
print("numa fonte do professor. Vetar por texto remove os dois; vetar por PROVENIENCIA exigiria um campo que a")
print("taxonomia nao tem hoje.")
