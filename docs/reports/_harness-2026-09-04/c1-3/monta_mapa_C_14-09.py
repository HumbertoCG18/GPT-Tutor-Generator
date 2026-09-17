"""Monta `mapa_C_14-09.json` a partir das respostas do braco C (LLM via agy), aplicando as regras congeladas do prompt (14/09).

Regras (fixadas antes de ler qualquer resposta):
  - vale a PRIMEIRA resposta de cada lote; nao ha nova tentativa;
  - resposta invalida, vazia, fora do schema, `denied_actions` nao vazio -> todas as categorias do lote ficam SEM;
  - `topic_code` que nao existe entre os topicos `kind=topic` do curso -> SEM (conta como codigo inventado);
  - id ausente na resposta -> SEM.
Publica, por curso: categorias, mapeadas, SEM, codigos inventados, lotes invalidos, tokens gastos.

0 chamadas. Uso: PYTHONUTF8=1 python -B monta_mapa_C_14-09.py
"""
import collections
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAC = HERE / "pacotes_mapeamento_14-09"
RESP = HERE / "respostas_C_14-09"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_spec = importlib.util.spec_from_file_location("extrator", HERE / "extrator_relacoes_14-09.py")
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)
BASES = {c: b for c, b in ex.COURSES}
CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]


def main():
    mapas, resumo = [], {}
    for curso in CURSOS:
        ids = {int(k): v for k, v in json.loads((PAC / f"ids_{curso}.json").read_text(encoding="utf-8")).items()}
        t = json.loads((BASES[curso] / "course/.content_taxonomy.json").read_text(encoding="utf-8-sig"))
        codigos = {(x.get("code") or x.get("slug")) for u in t["units"] for x in u["topics"] if x.get("kind") == "topic"}
        c = collections.Counter(categorias=len(ids))
        escolha = {}
        for arq in sorted(x for x in RESP.glob(f"C_{curso}_*.json") if "." not in x.stem):  # 14/09: ignora C_*.FALHOU-*.json arquivados
            c["lotes"] += 1
            try:
                env = json.loads(arq.read_text(encoding="utf-8"))
                c["tokens"] += int((env.get("usage") or {}).get("total_tokens") or 0)
                if env.get("denied_actions"):
                    raise ValueError("denied_actions")
                r = env.get("response")
                d = json.loads(r) if isinstance(r, str) else r
                for m in d["mapeamentos"]:
                    escolha[int(m["id"])] = str(m.get("topic_code") or "").strip()
            except Exception as e:  # lote invalido: tudo SEM
                c["lotes_invalidos"] += 1
                print(f"  lote invalido {arq.name}: {type(e).__name__}: {str(e)[:80]}")
        for i, cn in ids.items():
            code = escolha.get(i, "")
            if not code:
                c["id_ausente"] += 1
                code = "SEM"
            elif code != "SEM" and code not in codigos:
                c["codigo_inventado"] += 1
                code = "SEM"
            c["SEM" if code == "SEM" else "mapeadas"] += 1
            mapas.append(dict(curso=curso, categoria_norm=cn, topic_code="" if code == "SEM" else code))
        resumo[curso] = dict(c)
    (HERE / "mapa_C_14-09.json").write_text(json.dumps({"_nota": "mapa do braco C (LLM via agy, prompt congelado)",
                                                        "resumo": resumo, "mapeamentos": mapas}, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    for curso, c in resumo.items():
        print(f"{curso:4} categorias {c.get('categorias', 0):>4} · mapeadas {c.get('mapeadas', 0):>4} · SEM {c.get('SEM', 0):>4} · "
              f"codigo inventado {c.get('codigo_inventado', 0):>3} · id ausente {c.get('id_ausente', 0):>3} · "
              f"lotes {c.get('lotes', 0)} (invalidos {c.get('lotes_invalidos', 0)}) · tokens {c.get('tokens', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
