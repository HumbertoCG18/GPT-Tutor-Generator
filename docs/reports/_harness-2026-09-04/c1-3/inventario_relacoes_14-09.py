"""INVENTARIO de relacoes locais explicitas ANTES da ancoragem, e as ligacoes categoria -> topico por regime (14/09).

Correcao do astra na revisao da meta: as 25 candidatas da §39 foram emitidas DEPOIS de a categoria casar exatamente com um topico
(`extrator_relacoes_14-09.py`, `matched = anchors.get(norm(category), [])`). O que o professor escreveu e nao casou nunca foi
guardado. Este inventario reaproveita o extrator CONGELADO sem edita-lo (importa `scan`, `classify`, `strip_images`, `norm`,
`anchor_names`, `COURSES`, `FORBIDDEN`) e muda so o mecanismo que liga categoria a topico.

LIGACOES (mesmos candidatos, mesmo filtro, mesmo universo de topicos `kind=topic` do extrator):
  estrito  igualdade normalizada com um nome de ancora (`anchor_names`); ambiguo e rejeitado — reproduz a §39
  A        regra lexical fraca, CONGELADA como o astra especificou (brief 13, item 3A):
           1) tenta a igualdade de `anchor_names`; exata ambigua e rejeitada;
           2) senao, tokens de `norm` sem SOMENTE estas palavras: a o as os de da do das dos e em para por com um uma modelo
              modelos tarefa tarefas;
           3) token casa por igualdade ou por prefixo comum de >= 7 caracteres;
           4) TODO token restante do rotulo precisa casar com algum token da categoria; rotulo sem tokens e rejeitado;
           5) aceita so se UM topico do curso inteiro passar; sem desempate por score, unidade predita ou frequencia de erro.

Saidas: `inventario_relacoes_14-09.jsonl` (um par categoria->termo por linha, com as duas ligacoes) e o resumo no log.
Nao le gold, analise de erro, sidecar, glossario nem predicao — as mesmas proibicoes do extrator.

0 chamadas. Uso: PYTHONUTF8=1 python -B docs/reports/_harness-2026-09-04/c1-3/inventario_relacoes_14-09.py
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

STOP_A = set("a o as os de da do das dos e em para por com um uma modelo modelos tarefa tarefas".split())
PREFIXO_MIN = 7


def _casa_token(t_rot, toks_cat):
    for t in toks_cat:
        if t == t_rot:
            return True
        n = 0
        for x, y in zip(t, t_rot):
            if x != y:
                break
            n += 1
        if n >= PREFIXO_MIN:
            return True
    return False


def liga_A(categoria_norm, topicos):
    """Devolve (topico ou None, motivo). Regra congelada — nao ajustar depois de ver o resultado."""
    exatos = [t for t in topicos if categoria_norm in set(ex.anchor_names(t["label"]))]
    if len(exatos) == 1:
        return exatos[0], "A:exato"
    if len(exatos) > 1:
        return None, "A:exato_ambiguo"
    toks_cat = [x for x in categoria_norm.split() if x not in STOP_A]
    if not toks_cat:
        return None, "A:categoria_sem_tokens"
    passam = []
    for t in topicos:
        for nome in set(ex.anchor_names(t["label"])):
            toks_rot = [x for x in nome.split() if x not in STOP_A]
            if toks_rot and all(_casa_token(tr, toks_cat) for tr in toks_rot):
                passam.append(t)
                break
    if len(passam) == 1:
        return passam[0], "A:lexical"
    return None, ("A:lexical_ambiguo" if passam else "A:sem_topico")


def documentos(base):
    """Mesmas fontes e mesma ordem do extrator congelado."""
    entries = json.loads((base / "manifest.json").read_text(encoding="utf-8-sig"))["entries"]
    fontes, meta = {}, []
    cm = base / "course/COURSE_MAP.md"
    if cm.exists():
        fontes[str(cm)] = cm
    for i, e in enumerate(entries):
        for k in ("source_section", "moodle_label"):
            v = e.get(k)
            if isinstance(v, str) and v.strip():
                meta.append((str(base / "manifest.json") + "#entries/" + str(i) + "/" + k, v))
        for k in ("approved_markdown", "curated_markdown", "base_markdown"):
            v = e.get(k)
            if not isinstance(v, str) or not v:
                continue
            p = (base / v).resolve()
            if not p.is_relative_to(base) or ex.FORBIDDEN.search(str(p)) or p.suffix.lower() != ".md":
                continue
            if p.exists():
                fontes[str(p)] = p
                break
    docs = []
    for nome, p in sorted(fontes.items()):
        try:
            docs.append((nome, ex.strip_images(p.read_text(encoding="utf-8-sig"))))
        except (OSError, UnicodeError, ValueError):
            pass
    return docs + meta


def main():
    out = HERE / "inventario_relacoes_14-09.jsonl"
    resumo = {}
    with out.open("w", encoding="utf-8") as f:
        for curso, base in ex.COURSES:
            base = base.resolve()
            tax = base / "course/.content_taxonomy.json"
            if not tax.exists():
                continue
            topicos = [{k: t.get(k, "") for k in ("label", "code", "kind", "unit_slug")}
                       for u in json.loads(tax.read_text(encoding="utf-8-sig"))["units"] for t in u["topics"]
                       if t.get("kind") == "topic"]
            ancoras = collections.defaultdict(list)
            for t in topicos:
                for k in set(ex.anchor_names(t["label"])):
                    if k:
                        ancoras[k].append(t)
            c = collections.Counter()
            cats, cats_estrito, cats_A = set(), set(), set()
            vistos = set()
            for arquivo, texto in documentos(base):
                for categoria, termo, padrao, linha, trecho in ex.scan(texto.splitlines()):
                    cn = ex.norm(categoria)
                    chave = (arquivo, linha, cn, ex.norm(termo))
                    if not cn or chave in vistos:
                        continue
                    vistos.add(chave)
                    adm, motivo = ex.classify(termo, trecho)
                    est = ancoras.get(cn, [])
                    lig_e = est[0]["code"] if len(est) == 1 else ("AMBIGUO" if est else "")
                    tA, mA = liga_A(cn, topicos)
                    lig_a = tA["code"] if tA else ""
                    c["pares"] += 1
                    c["pares_admissiveis"] += adm
                    cats.add(cn)
                    if lig_e and lig_e != "AMBIGUO":
                        cats_estrito.add(cn)
                        c["pares_adm_estrito"] += adm
                    if lig_a:
                        cats_A.add(cn)
                        c["pares_adm_A"] += adm
                        if not lig_e or lig_e == "AMBIGUO":
                            c["pares_adm_A_NOVOS"] += adm
                    f.write(json.dumps(dict(curso=curso, categoria=categoria, categoria_norm=cn, termo=termo, padrao=padrao,
                                            arquivo=arquivo, linha=linha, trecho=trecho, admissivel_auto=adm, motivo=motivo,
                                            liga_estrito=lig_e, liga_A=lig_a, motivo_A=mA), ensure_ascii=False) + "\n")
            c["categorias"] = len(cats)
            c["categorias_ligadas_estrito"] = len(cats_estrito)
            c["categorias_ligadas_A"] = len(cats_A)
            c["categorias_A_novas"] = len(cats_A - cats_estrito)
            resumo[curso] = dict(c)
    print(f"{'curso':7} {'categorias':>10} {'lig.estrito':>11} {'lig.A':>6} {'A novas':>8} {'pares':>6} {'adm':>5} {'adm estr':>9} {'adm A':>6} {'adm A NOVOS':>12}")
    for curso, c in resumo.items():
        print(f"{curso:7} {c.get('categorias', 0):>10} {c.get('categorias_ligadas_estrito', 0):>11} {c.get('categorias_ligadas_A', 0):>6} "
              f"{c.get('categorias_A_novas', 0):>8} {c.get('pares', 0):>6} {c.get('pares_admissiveis', 0):>5} "
              f"{c.get('pares_adm_estrito', 0):>9} {c.get('pares_adm_A', 0):>6} {c.get('pares_adm_A_NOVOS', 0):>12}")
    print(f"\nDetalhe em {out.name}. 'adm' = filtro automatico `classify` do extrator; a auditoria humana/astra vem depois.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
