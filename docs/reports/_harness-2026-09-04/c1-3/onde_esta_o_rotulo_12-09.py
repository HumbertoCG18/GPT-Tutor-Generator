"""O rotulo certo esta escrito no material, e o motor nao viu? (12/09, pergunta do user: "o que precisamos para
aumentar o cru?").

A distincao que decide a alavanca:
  - se o rotulo do gold APARECE no texto que o motor leu e mesmo assim ele errou, o problema e de COMPETICAO
    (outro topico pontuou mais) e a alavanca e o scorer/desempate;
  - se o rotulo NAO aparece, o problema e de VOCABULARIO (o professor escreve "perceptron" e o plano diz
    "Modelos Preditivos") e a alavanca e um lexico que ligue um ao outro.

Mede, para os erros do regime cru, se o LABEL do topico do gold (e cada um dos seus aliases CRUS, isto e, os que
sobrevivem ao corte do sidecar LLM) aparece como frase no texto que o motor pontuou. Usa `frase_no` com a mesma
normalizacao do motor. Tambem separa por token: se nem o label inteiro nem um alias cru aparecem, quantos TOKENS
especificos do label aparecem?

0 chamadas. Nao escreve no produto nem em .ablacao/.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/onde_esta_o_rotulo_12-09.py
"""
import csv
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
import src.builder.timeline.index as ti  # noqa: E402

CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
N = ti._normalize_match_text


def frase_no(texto_norm, frase):
    n = N(frase or "")
    return bool(n) and re.search(r"(^|\s)" + re.escape(n) + r"(\s|$)", texto_norm) is not None


def llm_norms(sig):
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    if not p.exists():
        return set()
    d = json.loads(p.read_text(encoding="utf-8"))
    return {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}


def sem_llm(sig):
    vet = llm_norms(sig)

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in vet]
    return change


def gold_rows(sig):
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


def toks(s):
    return {t for t in N(s).split() if len(t) >= 4 and not any(t.startswith(g) for g in MOTOR_GENERIC_STEMS)}


linhas = []
for sig in CURSOS:
    cru = rp.evaluate(sig, "com", new=False, taxmod=sem_llm(sig), escopo="produto")
    prod = rp.evaluate(sig, "com", new=False, escopo="produto")
    entries = {e["id"]: e for e in cru[6]}
    textos = cru[5]
    # topicos da taxonomia CRUA, por slug
    topo = {}
    for u in cru[7]["units"]:
        for t in u["topics"]:
            topo[t["slug"]] = (t["label"], list(t.get("aliases") or []), u["slug"])
    vet = llm_norms(sig)
    for eid, row in gold_rows(sig).items():
        e = entries.get(eid)
        if e is None:
            continue
        aceitos = ({row["gold_subunit"]} | set(filter(None, row.get("gold_subunits_extra", "").split(";")))
                   if row["gold_subunit"] else {""})
        pred = cru[3].get(eid, "")
        if pred in aceitos:
            continue
        tn = N(textos.get(eid, "") or "")
        alvo = row["gold_subunit"]
        label, aliases, _ = topo.get(alvo, ("", [], ""))
        al_cru = [a for a in aliases if _norm(a) not in vet]
        al_llm = [a for a in aliases if _norm(a) in vet]
        lab_no_texto = frase_no(tn, label)
        alias_cru_no_texto = [a for a in al_cru if frase_no(tn, a)]
        # tokens especificos do label presentes no texto
        tl = toks(label)
        tok_presentes = {t for t in tl if re.search(r"(^|\s)" + re.escape(t) + r"(\s|$)", tn)}
        linhas.append({
            "curso": sig, "entry_id": eid, "gold": alvo,
            "confiante": int(revisar_de(e) not in ("duvida", "mudou")),
            "produto_acerta": int(prod[3].get(eid, "") in aceitos),
            "label_do_gold": label,
            "label_no_texto": int(lab_no_texto),
            "alias_cru_no_texto": ";".join(alias_cru_no_texto),
            "n_alias_cru": len(al_cru), "n_alias_llm": len(al_llm),
            "tokens_label": len(tl), "tokens_no_texto": len(tok_presentes),
            "tokens_presentes": ";".join(sorted(tok_presentes)),
            "texto_vazio": int(not tn),
        })

n = len(linhas)
print(f"ERROS DE ACEITO NO REGIME CRU: {n}")
print()
print("O rotulo do gold esta escrito no texto que o motor leu?")
lab = [r for r in linhas if r["label_no_texto"]]
ali = [r for r in linhas if not r["label_no_texto"] and r["alias_cru_no_texto"]]
tok = [r for r in linhas if not r["label_no_texto"] and not r["alias_cru_no_texto"] and r["tokens_no_texto"]]
nada = [r for r in linhas if not r["label_no_texto"] and not r["alias_cru_no_texto"] and not r["tokens_no_texto"]]
vaz = [r for r in linhas if r["texto_vazio"]]
print(f"  LABEL INTEIRO presente  : {len(lab):3}  ({len(lab)/n:5.1%})  -> competicao: o motor viu e escolheu outro")
print(f"  alias CRU presente      : {len(ali):3}  ({len(ali)/n:5.1%})  -> idem, por alias que sobrevive ao corte")
print(f"  so TOKEN do label       : {len(tok):3}  ({len(tok)/n:5.1%})  -> parcial: parte do rotulo aparece")
print(f"  NADA do rotulo          : {len(nada):3}  ({len(nada)/n:5.1%})  -> vocabulario: o texto nao nomeia o topico")
print(f"  (texto vazio no motor)  : {len(vaz):3}")
print()
print("Mesmo recorte, so os ERROS CONFIANTES:")
cf = [r for r in linhas if r["confiante"]]
for nome, sub in (("LABEL INTEIRO", [r for r in cf if r["label_no_texto"]]),
                  ("alias CRU", [r for r in cf if not r["label_no_texto"] and r["alias_cru_no_texto"]]),
                  ("so TOKEN", [r for r in cf if not r["label_no_texto"] and not r["alias_cru_no_texto"] and r["tokens_no_texto"]]),
                  ("NADA", [r for r in cf if not r["label_no_texto"] and not r["alias_cru_no_texto"] and not r["tokens_no_texto"]])):
    print(f"  {nome:16} {len(sub):3} de {len(cf)}")
print()
print("Por curso (erros de aceito):")
print(f"{'curso':5} {'n':>4} {'label':>6} {'aliasCru':>9} {'soToken':>8} {'NADA':>6}")
for sig in CURSOS:
    s = [r for r in linhas if r["curso"] == sig]
    if not s:
        continue
    print(f"{sig:5} {len(s):>4} "
          f"{sum(r['label_no_texto'] for r in s):>6} "
          f"{sum(1 for r in s if not r['label_no_texto'] and r['alias_cru_no_texto']):>9} "
          f"{sum(1 for r in s if not r['label_no_texto'] and not r['alias_cru_no_texto'] and r['tokens_no_texto']):>8} "
          f"{sum(1 for r in s if not r['label_no_texto'] and not r['alias_cru_no_texto'] and not r['tokens_no_texto']):>6}")
print()
print("Os que o PRODUTO acerta (o vocab LLM resolve), pelo mesmo recorte:")
pa = [r for r in linhas if r["produto_acerta"]]
print(f"  n={len(pa)} · label {sum(r['label_no_texto'] for r in pa)} · "
      f"aliasCru {sum(1 for r in pa if not r['label_no_texto'] and r['alias_cru_no_texto'])} · "
      f"soToken {sum(1 for r in pa if not r['label_no_texto'] and not r['alias_cru_no_texto'] and r['tokens_no_texto'])} · "
      f"NADA {sum(1 for r in pa if not r['label_no_texto'] and not r['alias_cru_no_texto'] and not r['tokens_no_texto'])}")
print()
print("=" * 130)
print("OS QUE O TEXTO NAO NOMEIA DE JEITO NENHUM (alavanca = lexico, nao scorer):")
for r in nada:
    print(f"  {r['curso']:4} {r['entry_id']:46} gold={r['gold']:44} label='{r['label_do_gold']}'")

out = HERE / "onde_esta_o_rotulo_12-09.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
    w.writeheader()
    w.writerows(linhas)
print()
print(f"CSV: {out}")
