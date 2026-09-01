"""Regua de SAUDE da subunidade — sem rotulo nenhum.

Nao mede acerto (nao existe gold de subunidade). Mede se o sinal EXISTE:
uma unidade cujo material inteiro cai sempre no mesmo subtopico nao esta
predizendo, esta devolvendo constante.

Tres checagens, todas derivadas do proprio artefato:

  COLAPSO       concentracao do subtopico mais frequente numa unidade com
                material suficiente e mais de um topico disponivel.
  IMA           desequilibrio de ALIASES entre topicos irmaos — e a causa
                upstream do colapso: `_select_supported_taxonomy_topic`
                desempata pela POSICAO na lista quando dois irmaos sao
                igualmente apoiados, entao o topico 1 absorve tudo.
  INTEGRIDADE   subtopico que nao existe na taxonomia (stale) ou que pertence
                a outra unidade.

Uso:
    python scripts/eval_subunit_health.py                # os 5 cursos
    python scripts/eval_subunit_health.py --course IA
    python scripts/eval_subunit_health.py --json
Saida: exit code 1 se houver COLAPSO ou INTEGRIDADE (serve de gate em CI).
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
GITHUB_DIR = ROOT.parent
COURSES = {
    "MF": "Metodos-Formais-Tutor",
    "SO": "Sistemas-Operacionais-Tutor",
    "IA": "Inteligencia-Artifical-Tutor",
    "ES2": "Engenharia-Software-2-Tutor",
    "TCC": "TCC-Tutor",
}

# Uma unidade so e julgada quando ha material e escolha de verdade a fazer.
MIN_ENTRIES = 4
MIN_TOPICOS = 3
# Concentracao a partir da qual o subtopico deixa de ser predicao e vira constante.
LIMITE_COLAPSO = 0.60
# Um topico com mais que isto vezes a MEDIA de aliases dos irmaos e ima.
LIMITE_IMA = 2.5


def _mediana(valores):
    v = sorted(valores)
    if not v:
        return 0.0
    meio = len(v) // 2
    return float(v[meio]) if len(v) % 2 else (v[meio - 1] + v[meio]) / 2.0


def avaliar(sigla: str, repo_name: str) -> dict:
    repo = GITHUB_DIR / repo_name
    manifest_path = repo / "manifest.json"
    tax_path = repo / "course" / ".content_taxonomy.json"
    if not (manifest_path.exists() and tax_path.exists()):
        return {"curso": sigla, "erro": "sem manifest ou taxonomia"}
    entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("entries") or []
    tax = json.loads(tax_path.read_text(encoding="utf-8"))

    dono, aliases_por_unidade, n_topicos = {}, {}, {}
    for unit in tax.get("units") or []:
        u_slug = str(unit.get("slug") or "")
        topicos = unit.get("topics") or []
        n_topicos[u_slug] = len(topicos)
        aliases_por_unidade[u_slug] = {
            str(t.get("slug")): len(t.get("aliases") or []) for t in topicos
        }
        for t in topicos:
            dono.setdefault(str(t.get("slug")), u_slug)

    por_unidade = collections.defaultdict(collections.Counter)
    stale, fora = [], []
    for e in entries:
        sub = str(e.get("computed_subunit_slug") or "").strip()
        if not sub:
            continue
        unit = str(e.get("computed_unit_slug") or "").strip()
        if sub not in dono:
            stale.append((str(e.get("id") or ""), sub))
        elif unit and dono[sub] != unit:
            fora.append((str(e.get("id") or ""), sub, unit))
        if unit:
            por_unidade[unit][sub] += 1

    colapsos, imas = [], []
    for unit, cnt in por_unidade.items():
        total = sum(cnt.values())
        if total < MIN_ENTRIES or n_topicos.get(unit, 0) < MIN_TOPICOS:
            continue
        sub_top, maior = cnt.most_common(1)[0]
        if maior / total >= LIMITE_COLAPSO:
            colapsos.append({"unidade": unit, "subtopico": sub_top, "entries": total,
                             "concentracao": round(maior / total, 2),
                             "distintos": len(cnt), "topicos": n_topicos.get(unit, 0)})
        vals = list((aliases_por_unidade.get(unit) or {}).values())
        if len(vals) >= 2 and max(vals) >= 3:
            med = _mediana(vals) or 0.5
            if max(vals) / med >= LIMITE_IMA:
                campeao = max((aliases_por_unidade[unit]).items(), key=lambda kv: kv[1])
                imas.append({"unidade": unit, "topico": campeao[0], "aliases": campeao[1],
                             "mediana_irmaos": med, "distribuicao": sorted(vals, reverse=True)})
    return {"curso": sigla, "colapsos": colapsos, "imas": imas,
            "stale": stale, "fora_da_unidade": fora,
            "unidades_avaliadas": sum(
                1 for u, c in por_unidade.items()
                if sum(c.values()) >= MIN_ENTRIES and n_topicos.get(u, 0) >= MIN_TOPICOS)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", help="sigla (MF/SO/IA/ES2/TCC); omitido = todos")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    alvos = {args.course.upper(): COURSES[args.course.upper()]} if args.course else COURSES
    resultados = [avaliar(s, r) for s, r in alvos.items()]
    if args.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
    else:
        for r in resultados:
            if r.get("erro"):
                print(f"== {r['curso']}: {r['erro']}")
                continue
            print(f"== {r['curso']}  unidades avaliadas={r['unidades_avaliadas']}")
            for c in r["colapsos"]:
                print(f"   COLAPSO      {c['unidade'][:44]:46} {c['entries']:3} entries -> "
                      f"{c['distintos']} subtopico(s) de {c['topicos']}, "
                      f"{c['concentracao']:.0%} em `{c['subtopico']}`")
            for m in r["imas"]:
                print(f"   IMA          {m['topico'][:44]:46} {m['aliases']} aliases contra "
                      f"mediana {m['mediana_irmaos']:.1f} dos irmaos {m['distribuicao']}")
            for eid, sub in r["stale"]:
                print(f"   STALE        {eid[:44]:46} subtopico `{sub}` nao existe na taxonomia")
            for eid, sub, unit in r["fora_da_unidade"]:
                print(f"   FORA         {eid[:44]:46} `{sub}` pertence a outra unidade (entry em {unit})")
            if not (r["colapsos"] or r["imas"] or r["stale"] or r["fora_da_unidade"]):
                print("   ok")
    grave = any(r.get("colapsos") or r.get("stale") or r.get("fora_da_unidade")
                for r in resultados if not r.get("erro"))
    return 1 if grave else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
