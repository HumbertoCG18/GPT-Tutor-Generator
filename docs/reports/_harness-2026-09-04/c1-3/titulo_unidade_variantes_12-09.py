"""A regra do titulo no eixo UNIDADE perde quando sobrepoe sempre. Algum CORTE ganha? (13/09)

`titulo_nomeia_unidade_12-09.log`: sobrepor sempre da saldo -9 no cru (ganha 4, perde 13) e -14 no produto.
Antes de fechar a frente, testo os cortes que fazem sentido sem olhar o gold:

  A  sempre                          (o baseline refutado)
  B  so quando o material esta na FILA         (o motor ja admite duvida)
  C  so quando ha CONFLITO unidade x bloco     (o motor ja sinalizou discordancia)
  D  so quando o token discriminante e DIMENSIONAL (2d/3d) — a familia que motivou o achado
  E  so quando o titulo casa 2+ tokens especificos da unidade sugerida (sinal mais forte)
  F  B ou C  (qualquer sinal de duvida do proprio motor)

Cada corte e medido no CRU e no PRODUTO, com ganhos e perdas NOMINAIS. Um corte so passa se ganhar no cru E nao
regredir o produto.

0 chamadas. Uso: python -B <este arquivo>
"""
import collections
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
from src.builder.routing.revisar import revisar_de  # noqa: E402
from src.builder.text.normalize import normalize_match_text as N  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS  # noqa: E402
from src.models.core import moodle_label_text  # noqa: E402

NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor"}
_COD = re.compile(r"^unidade-\d+-")
_DIM = re.compile(r"^\d+d$")


def toks(s):
    return {t for t in N(s).split() if len(t) >= 2 and not any(t.startswith(g) for g in MOTOR_GENERIC_STEMS)}


def levanta(raiz):
    """Devolve lista de casos: (sig, eid, got, sug, aceitas, na_fila, conflito, n_tokens, dimensional)."""
    out = []
    for sig, nm in NOMES.items():
        p, tp = raiz / nm / "manifest.json", raiz / nm / "course/.content_taxonomy.json"
        if not p.exists() or not tp.exists():
            continue
        gu = carrega_regua_unidade(sig)
        tax = json.loads(tp.read_text(encoding="utf-8"))
        unidades = {str(u.get("slug") or ""): toks(str(u.get("title") or "") + " " +
                                                  _COD.sub("", str(u.get("slug") or "")).replace("-", " "))
                    for u in tax.get("units", []) or []}
        cont = collections.Counter(t for ts in unidades.values() for t in ts)
        esp = {s: {t for t in ts if cont[t] == 1} for s, ts in unidades.items()}
        for e in json.loads(p.read_text(encoding="utf-8"))["entries"]:
            eid = e["id"]
            if eid not in gu:
                continue
            tit = toks(f"{e.get('title') or ''} {moodle_label_text(e) or ''} {eid.replace('-', ' ')}")
            hits = [(s, ts & tit) for s, ts in esp.items() if ts and (ts & tit)]
            if len(hits) != 1:
                continue
            sug, casados = hits[0]
            got = str(e.get("computed_unit_slug") or "")
            if sug == got:
                continue
            out.append(dict(sig=sig, eid=eid, got=got, sug=sug, aceitas=gu[eid],
                            fila=revisar_de(e) in ("duvida", "mudou"),
                            conflito=bool(e.get("unit_block_conflict")),
                            ntok=len(casados), dim=any(_DIM.match(t) for t in casados)))
    return out


CORTES = {
    "A sempre": lambda c: True,
    "B so na fila": lambda c: c["fila"],
    "C so com conflito": lambda c: c["conflito"],
    "D so dimensional (2d/3d)": lambda c: c["dim"],
    "E so com 2+ tokens": lambda c: c["ntok"] >= 2,
    "F fila OU conflito": lambda c: c["fila"] or c["conflito"],
}

for rotulo, raiz in (("CRU", COPIA), ("PRODUTO", ORIG)):
    casos = levanta(raiz)
    print(f"=== {rotulo} — {len(casos)} materiais em que o titulo contradiz o motor ===")
    print(f"  {'corte':28} {'dispara':>8} {'GANHA':>7} {'PERDE':>7} {'ambos err':>10} {'saldo':>7}")
    for nome, f in CORTES.items():
        sel = [c for c in casos if f(c)]
        g = sum(1 for c in sel if c["sug"] in c["aceitas"] and c["got"] not in c["aceitas"])
        p_ = sum(1 for c in sel if c["got"] in c["aceitas"] and c["sug"] not in c["aceitas"])
        amb = len(sel) - g - p_
        print(f"  {nome:28} {len(sel):>8} {g:>7} {p_:>7} {amb:>10} {g - p_:>+7}")
    print()

print("NOMINAIS do corte D (dimensional) no CRU:")
for c in levanta(COPIA):
    if c["dim"]:
        tipo = ("GANHO" if c["sug"] in c["aceitas"] and c["got"] not in c["aceitas"]
                else "PERDA" if c["got"] in c["aceitas"] and c["sug"] not in c["aceitas"] else "ambos errados")
        print(f"  [{tipo:13}] {c['sig']:4} {c['eid']:46}")
        print(f"                  motor={c['got']}")
        print(f"                  titulo={c['sug']}")
