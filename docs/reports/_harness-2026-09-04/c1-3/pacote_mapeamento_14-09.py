"""PACOTE do mapeamento categoria -> topico: o MESMO insumo para o braco B (declaracao humana) e o braco C (LLM) — 14/09.

Protocolo do astra (revisao da meta, item 3): B e C recebem o mesmo pacote — plano, categorias, termos e trechos originais —,
sem predicoes nem gabarito. So entram categorias com >= 1 relacao admissivel pelo filtro automatico (as outras nao geram
alias em nenhum braco). Ordem fixa: primeira ocorrencia no inventario. Cada categoria tem um `id` estavel.

Saidas (em `pacotes_mapeamento_14-09/`):
  C_<curso>_<lote>.md   lotes de ate LOTE categorias, para o prompt congelado `prompt_C_mapeamento_14-09.md`
  B_<curso>.md          o formulario para o professor responsavel: uma linha por categoria, coluna "codigo do topico ou SEM"
  ids_<curso>.json      id -> categoria_norm (para reconstruir o mapa depois)

0 chamadas. Uso: PYTHONUTF8=1 python -B pacote_mapeamento_14-09.py
"""
import collections
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "pacotes_mapeamento_14-09"
LOTE = 120
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_spec = importlib.util.spec_from_file_location("extrator", HERE / "extrator_relacoes_14-09.py")
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)
BASES = {c: b for c, b in ex.COURSES}
CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]


def main():
    OUT.mkdir(exist_ok=True)
    cats = collections.defaultdict(dict)   # curso -> categoria_norm -> {categoria, termos, trecho}
    for linha in (HERE / "inventario_relacoes_14-09.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(linha)
        if r["curso"] not in CURSOS or not r["admissivel_auto"]:
            continue
        d = cats[r["curso"]].setdefault(r["categoria_norm"], {"categoria": r["categoria"], "termos": [], "trecho": ""})
        if r["termo"] not in d["termos"] and len(d["termos"]) < 4:
            d["termos"].append(r["termo"])
        if not d["trecho"]:
            d["trecho"] = " ".join(r["trecho"].split())[:180]
    so = [c for c in sys.argv[1:] if c in CURSOS]  # 14/09: regerar so os cursos pedidos (a cadeia C le os outros)
    for curso in (so or CURSOS):
        t = json.loads((BASES[curso] / "course/.content_taxonomy.json").read_text(encoding="utf-8-sig"))
        # 14/09: topico SEM code (o IA inteiro) usa o slug como identificador — sem isso o LLM nao tem o que responder
        topicos = [(x.get("code") or x.get("slug"), x["label"]) for u in t["units"] for x in u["topics"] if x.get("kind") == "topic"]
        plano = "\n".join(f"- `{c or '(sem codigo)'}` {l}" for c, l in topicos)
        itens = list(cats[curso].items())
        ids = {}
        linhas_b = [f"# Declaracao do professor — {curso}", "",
                    "Para cada CATEGORIA que voce usou nos materiais, escreva o codigo do topico do plano a que os termos listados "
                    "pertencem, ou SEM. Nao corrija arquivos individuais. Tempo sugerido: ate 30 minutos.", "",
                    "## Topicos do plano", plano, "", "## Categorias", "",
                    "| id | categoria | termos listados sob ela | codigo do topico ou SEM |", "|---|---|---|---|"]
        for i, (cn, d) in enumerate(itens, 1):
            ids[i] = cn
            linhas_b.append(f"| {i} | {d['categoria'][:70]} | {'; '.join(x[:40] for x in d['termos'])} |  |")
        (OUT / f"B_{curso}.md").write_text("\n".join(linhas_b) + "\n", encoding="utf-8")
        (OUT / f"ids_{curso}.json").write_text(json.dumps(ids, ensure_ascii=False, indent=1), encoding="utf-8")
        for n in range(0, len(itens), LOTE):
            corpo = [f"CURSO: {curso}", "", "TOPICOS DO PLANO (use somente estes codigos):", plano, "",
                     f"CATEGORIAS (lote {n // LOTE + 1}):"]
            for i, (cn, d) in enumerate(itens[n:n + LOTE], n + 1):
                corpo.append(f"[{i}] categoria: {d['categoria'][:90]} | termos: {'; '.join(x[:50] for x in d['termos'])} | trecho: {d['trecho']}")
            (OUT / f"C_{curso}_{n // LOTE + 1}.md").write_text("\n".join(corpo) + "\n", encoding="utf-8")
        print(f"{curso}: {len(itens)} categorias · {len(topicos)} topicos · {max(1, -(-len(itens) // LOTE))} lote(s) C")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
