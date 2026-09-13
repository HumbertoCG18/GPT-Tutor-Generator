"""CONGELA OS SIDECARS POR ENTRADA E PROVENIENCIA (13/09, passo que as duas corridas do astra nomearam).

Motivo: eu publiquei que "a unica dependencia de gold que sobra e o prompt v2". O astra mostrou, e eu verifiquei,
que o sidecar que o regime cru conserva (`course/.glossary_curation.json`) tem PROVENIENCIA MISTA: parte veio do
script de 07/09 (fontes do professor, sem gold), parte foi acrescentada em 12/09 MEDINDO CONTRA A REGUA
(`_nota`: "E5 so 'gateway' +1, 0 perdas", "E4 curvas +2, 0 perdas"), e parte e ruling do usuario ou veto.

Este script NAO altera nada. Ele produz o registro congelado, por ENTRADA e por TERMO:

  congela_sidecars_13-09.csv   curso, arquivo, topico, termo, classe de proveniencia, fonte declarada, nota
  congela_sidecars_13-09.log   o placar por classe, e a lista nominal do que foi selecionado pelo benchmark

CLASSES (derivadas do metadado que a propria entrada carrega, nao de julgamento meu):
  auto-professor   `_origem` presente e sem `_nota` de intervencao: gerado por `gera_sidecar_professor.py` (07/09)
  benchmark        `_nota` da entrada diz que a curadoria foi MEDIDA no replay/regua antes de entrar
  ruling-user      `_nota` da entrada cita ruling/decisao do usuario
  veto             campo `veto` (remocao, nao adicao)
  llm-compilado    veio de `.glossary_curation.llm.json` (1 chamada por unidade, `vocabulary_compile.py`)
  sem-metadado     nenhum dos acima: proveniencia NAO identificavel -> e a classe que o astra manda parar em cima

0 chamadas. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/congela_sidecars_13-09.py
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
ORIG = GEN.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor", "LR": "Laboratorio-de-Redes-Tutor"}

# O que, no texto da nota, denuncia que a entrada passou por medicao contra a regua antes de ser publicada.
MEDIDO = re.compile(r"\bmedid[oa]\b|\breplay\b|\bGate 1\b|\+\d+\s*\(|0 perdas", re.I)
RULING = re.compile(r"\bruling\b|\(user[,)]|\bdo user\b|\buser,", re.I)


def classifica(topico_meta, nota_arquivo):
    """A classe sai do metadado da ENTRADA; a nota do ARQUIVO so entra quando a entrada nao diz nada."""
    nota = str(topico_meta.get("_nota") or "")
    if nota:
        if MEDIDO.search(nota):
            return "benchmark", nota
        if RULING.search(nota):
            return "ruling-user", nota
        return "sem-metadado", nota
    if topico_meta.get("_origem"):
        return "auto-professor", ""
    if MEDIDO.search(nota_arquivo) or RULING.search(nota_arquivo):
        # a nota e do arquivo inteiro (CG): a entrada herda, mas fica marcada como herdada
        return ("benchmark" if MEDIDO.search(nota_arquivo) else "ruling-user"), "(nota do ARQUIVO) " + nota_arquivo[:200]
    return "sem-metadado", ""


def main():
    linhas = []
    for sig, nome in NOMES.items():
        for arq, rotulo in ((".glossary_curation.json", "manual/cru"), (".glossary_curation.llm.json", "llm")):
            p = ORIG / nome / "course" / arq
            if not p.exists():
                continue
            d = json.loads(p.read_text(encoding="utf-8"))
            nota_arq = str(d.get("_nota") or "")
            for topico, v in d.items():
                if topico.startswith("_") or not isinstance(v, dict):
                    continue
                if rotulo == "llm":
                    classe, nota = "llm-compilado", ""
                else:
                    classe, nota = classifica(v, nota_arq)
                origem = v.get("_origem") or {}
                for termo in (v.get("synonyms") or []):
                    linhas.append(dict(curso=sig, arquivo=rotulo, topico=topico, termo=termo, classe=classe,
                                       fonte_declarada=";".join(origem.get(termo, [])), nota=nota[:400]))
                for termo in (v.get("veto") or []):
                    linhas.append(dict(curso=sig, arquivo=rotulo, topico=topico, termo=termo, classe="veto",
                                       fonte_declarada="", nota=nota[:400]))

    out = Path(__file__).with_suffix(".csv")
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["curso", "arquivo", "topico", "termo", "classe", "fonte_declarada", "nota"])
        w.writeheader()
        w.writerows(linhas)

    print(f"CONGELADO: {len(linhas)} pares (topico, termo) em {out.name}\n")
    print(f"{'classe':18} {'termos':>7} {'topicos':>8} {'cursos':>7}   onde")
    por = collections.defaultdict(list)
    for r in linhas:
        por[r["classe"]].append(r)
    for classe in ("auto-professor", "benchmark", "ruling-user", "veto", "sem-metadado", "llm-compilado"):
        rs = por.get(classe) or []
        if not rs:
            continue
        tops = {(r["curso"], r["topico"]) for r in rs}
        cursos = sorted({r["curso"] for r in rs})
        print(f"{classe:18} {len(rs):>7} {len(tops):>8} {len(cursos):>7}   {','.join(cursos)}")

    print("\nO SIDECAR QUE O REGIME CRU CONSERVA, por curso e classe:")
    cru = [r for r in linhas if r["arquivo"] == "manual/cru"]
    m = collections.Counter((r["curso"], r["classe"]) for r in cru)
    classes = sorted({c for _, c in m})
    print(f"  {'curso':6} " + " ".join(f"{c:>15}" for c in classes))
    for sig in NOMES:
        if not any(k[0] == sig for k in m):
            continue
        print(f"  {sig:6} " + " ".join(f"{m[(sig, c)]:>15}" for c in classes))

    print("\nNOMINAL — o que entrou no 'cru' DEPOIS de ser medido contra a regua (a classe que quebra a premissa):")
    for r in cru:
        if r["classe"] in ("benchmark", "ruling-user", "veto"):
            print(f"  [{r['classe']:12}] {r['curso']:4} {r['topico'][:44]:46} {r['termo'][:26]:28} {r['nota'][:110]}")

    n_sem = len([r for r in cru if r["classe"] == "sem-metadado"])
    print(f"\nSEM PROVENIENCIA IDENTIFICAVEL no sidecar do cru: {n_sem} termos")
    print("  (o passo 1 do astra manda PARAR se houver artefato sem origem identificavel)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
