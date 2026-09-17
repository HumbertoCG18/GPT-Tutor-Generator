"""O TITULO do material nomeia a UNIDADE, e o motor ignora? (13/09, ataque ao eixo unidade)

Achado que motiva: dos 31 erros de unidade do regime cru, os 10 que o produto acerta tem um padrao visivel —
`resolucao-de-prova-de-computacao-grafica-2d` vai para `unidade-08-sintese-de-imagens` quando existe
`unidade-04-processo-de-visualizacao-2d`; e a versao `-3d` vai para a unidade 2D. O titulo carrega o discriminante e o
motor nao usa.

Este script NAO propoe regra ainda: mede o ALCANCE e a PRECISAO do sinal, que e o que decide se vale virar regra.

  Para cada material, tokeniza o TITULO (+ label do Moodle) e o nome de cada UNIDADE do plano, tira os tokens genericos
  do curso (os que aparecem em 2+ unidades) e pergunta: existe EXATAMENTE UMA unidade cujos tokens especificos aparecem
  no titulo? Se sim, essa unidade e a "sugestao do titulo".

  Publica: em quantos materiais o titulo sugere alguma unidade · quantas vezes a sugestao BATE o gold · quantas vezes ela
  CONTRADIZ a unidade que o motor escolheu · e, dessas, quantas o motor estava errado (ganho potencial) e quantas o motor
  estava certo (perda potencial). Essa razao e o que decide.

0 chamadas; le so os manifests da copia e o gold. Uso: python -B <este arquivo>
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
COPIA = GEN / ".motor3eixos"
ORIG = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import carrega_regua_unidade  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
_COD = re.compile(r"^unidade-\d+-")


def toks(s):
    return {t for t in N(s).split() if len(t) >= 2 and not any(t.startswith(g) for g in MOTOR_GENERIC_STEMS)}


def analisa(raiz, rotulo):
    tot = collections.Counter()
    casos = []
    for sig, nm in NOMES.items():
        p = raiz / nm / "manifest.json"
        tp = raiz / nm / "course/.content_taxonomy.json"
        if not p.exists() or not tp.exists():
            continue
        gu = carrega_regua_unidade(sig)
        tax = json.loads(tp.read_text(encoding="utf-8"))
        unidades = {}
        for u in tax.get("units", []) or []:
            slug = str(u.get("slug") or "")
            nome_un = _COD.sub("", slug).replace("-", " ")
            unidades[slug] = toks(str(u.get("title") or "") + " " + nome_un)
        # token generico do CURSO: aparece em 2+ unidades
        cont = collections.Counter(t for ts in unidades.values() for t in ts)
        especificos = {s: {t for t in ts if cont[t] == 1} for s, ts in unidades.items()}
        for e in json.loads(p.read_text(encoding="utf-8"))["entries"]:
            eid = e["id"]
            if eid not in gu:
                continue
            tot["n"] += 1
            tit = toks(f"{e.get('title') or ''} {moodle_label_text(e) or ''} {eid.replace('-', ' ')}")
            hits = [s for s, ts in especificos.items() if ts and (ts & tit)]
            if len(hits) != 1:
                tot["sem sugestao (0 ou 2+)"] += 1
                continue
            sug = hits[0]
            got = str(e.get("computed_unit_slug") or "")
            aceitas = gu[eid]
            tot["titulo sugere 1 unidade"] += 1
            tot["sugestao BATE o gold"] += int(sug in aceitas)
            if sug == got:
                tot["concorda com o motor"] += 1
                continue
            tot["CONTRADIZ o motor"] += 1
            if got in aceitas and sug not in aceitas:
                tot["  motor certo, titulo errado (PERDA)"] += 1
                casos.append((sig, eid, got, sug, "PERDA"))
            elif sug in aceitas and got not in aceitas:
                tot["  motor errado, titulo certo (GANHO)"] += 1
                casos.append((sig, eid, got, sug, "GANHO"))
            else:
                tot["  ambos errados"] += 1
                casos.append((sig, eid, got, sug, "ambos errados"))
    print(f"=== {rotulo} ===")
    for k in ("n", "titulo sugere 1 unidade", "sugestao BATE o gold", "concorda com o motor", "CONTRADIZ o motor",
              "  motor errado, titulo certo (GANHO)", "  motor certo, titulo errado (PERDA)", "  ambos errados",
              "sem sugestao (0 ou 2+)"):
        print(f"  {k:42} {tot[k]:>4}")
    g = tot["  motor errado, titulo certo (GANHO)"]
    p_ = tot["  motor certo, titulo errado (PERDA)"]
    print(f"  --> saldo se o titulo sobrepusesse sempre: {g - p_:+d}  (ganha {g}, perde {p_})")
    print()
    return casos


casos_cru = analisa(COPIA, "REGIME CRU (copia .motor3eixos)")
casos_prod = analisa(ORIG, "PRODUTO")

print("CASOS NO CRU (o que a regra mexeria), um a um:")
for sig, eid, got, sug, tipo in sorted(casos_cru, key=lambda x: (x[4], x[0])):
    print(f"  [{tipo:14}] {sig:4} {eid:46}")
    print(f"                   motor={got}")
    print(f"                   titulo sugere={sug}")
