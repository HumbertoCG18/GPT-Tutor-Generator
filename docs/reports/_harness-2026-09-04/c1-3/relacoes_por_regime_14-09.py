"""Gera os arquivos de RELACOES por regime a partir do inventario pre-ancoragem (14/09, protocolo do astra na revisao da meta).

Mesmos candidatos, mesmo filtro, mesmo consumidor em todos os bracos — so muda o mecanismo que liga categoria a topico:
  estrito  pares com `admissivel_auto` e `liga_estrito` valido (nao vazio, nao AMBIGUO)             -> relacoes_estrito_14-09.json
  A        estrito  UNIAO  pares com `admissivel_auto` e `liga_A` valido                              -> relacoes_A_14-09.json
  C        estrito  UNIAO  pares com `admissivel_auto` cuja categoria o LLM mapeou (mapa_C_14-09.json) -> relacoes_C_14-09.json

Filtro unico e automatico (`classify` do extrator congelado): nenhum braco passa por auditoria manual antes do motor — a
auditoria de correcao das relacoes e medida a parte, sem ver o placar. O braco R da §39 usou a auditoria do astra (12 -> 3) e
por isso NAO e comparavel com estes; o `estrito` daqui e a base auto.

Relacao ja contida no rotulo (termo inteiro dentro do rotulo do topico) nao entra: nao acrescenta nada.
Formato de saida = o que `motor_3eixos_12-09.py --relacoes` consome.

0 chamadas. Uso: PYTHONUTF8=1 python -B relacoes_por_regime_14-09.py estrito|A|C
"""
import collections
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_spec = importlib.util.spec_from_file_location("extrator", HERE / "extrator_relacoes_14-09.py")
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)
BASES = {c: b for c, b in ex.COURSES}
CURSOS_MOTOR = {"MF", "SO", "IA", "ES2", "TCC", "CG", "FR"}


def valido(code):
    return bool(code) and code != "AMBIGUO"


def main():
    regime = sys.argv[1] if len(sys.argv) > 1 else ""
    assert regime in ("estrito", "A", "C"), "uso: estrito|A|C"
    mapa_c = {}
    if regime == "C":
        m = json.loads((HERE / "mapa_C_14-09.json").read_text(encoding="utf-8"))
        mapa_c = {(r["curso"], r["categoria_norm"]): r["topic_code"] for r in m["mapeamentos"] if valido(r.get("topic_code"))}
    rotulos = {}
    for c in CURSOS_MOTOR:
        t = json.loads((BASES[c] / "course/.content_taxonomy.json").read_text(encoding="utf-8-sig"))
        rotulos[c] = {(x.get("code") or x.get("slug")): x["label"] for u in t["units"] for x in u["topics"]}
    saida, vistos = [], set()
    por = collections.Counter()
    for linha in (HERE / "inventario_relacoes_14-09.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(linha)
        c = r["curso"]
        if c not in CURSOS_MOTOR or not r["admissivel_auto"]:
            continue
        code = r["liga_estrito"] if valido(r["liga_estrito"]) else ""
        if not code and regime == "A" and valido(r["liga_A"]):
            code = r["liga_A"]
        if not code and regime == "C":
            code = mapa_c.get((c, r["categoria_norm"]), "")
        if not code or code not in rotulos[c]:
            continue
        tn = ex.norm(r["termo"])
        if not tn or f" {tn} " in f" {ex.norm(rotulos[c][code])} ":
            continue
        chave = (c, code, tn)
        if chave in vistos:
            continue
        vistos.add(chave)
        por[c] += 1
        saida.append(dict(curso=c, topic_code=code, categoria=r["categoria"], termo=r["termo"], padrao=r["padrao"],
                          fonte=f"{Path(r['arquivo'].split('#')[0]).name}:{r['linha']}"))
    out = HERE / f"relacoes_{regime}_14-09.json"
    out.write_text(json.dumps({"_nota": f"regime {regime}: gerado por relacoes_por_regime_14-09.py do inventario pre-ancoragem; "
                                        "filtro automatico, sem auditoria manual.", "relacoes": saida},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"regime {regime}: {len(saida)} relacoes -> {out.name} · por curso {dict(por)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
