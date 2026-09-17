"""Regressao de unidade (11/09 -> defeito 12/09): a unidade do bloco temporal vem de `_assign_timeline_block_to_topic`
(topic_text do bloco x label + aliases de cada topico). Mede, com a funcao REAL do motor e 0 chamadas, o que o bloco-09 do SO
('comunicacao entre processos pipes filas') e o bloco-02 do CG ('introducao opengl') recebem hoje e sob taxonomias alternativas
(ablacoes pedidas pelo astra em 12/09). No fim, VERIFICA o estado corrigido: SO bloco-09 = u03, CG bloco-02 = u01 — falha
enquanto a curadoria (veto das 2 doacoes em 3.1 do SO; 'OpenGL' em 1.4 do CG) nao estiver aplicada.
Uso: python -B docs/reports/_harness-2026-09-04/c1-3/mede_regressao_unidade_bloco.py [--sem-check]"""
import copy
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(GEN))
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy as L  # noqa: E402
from src.builder.timeline.index import _assign_timeline_block_to_topic as assign  # noqa: E402
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics  # noqa: E402

GH = GEN.parent


def bloco(repo, bid):
    return next(b for b in json.loads((GH / repo / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"] if b["id"] == bid)


def mede(rot, tax, blk):
    cands, r = assign(blk, topics(tax), tax)
    top = [(c["unit_slug"][:11], c["topic_label"][:26], c["score"]) for c in cands[:3]]
    print(f"  {rot:58} -> unit={r.unit_slug[:11] or '(nenhuma)':11} topico={r.topic_label[:28]:28} conf={r.confidence:.2f} {r.reasons} | top3={top}")
    return r.unit_slug


def edita(tax, code, remover=(), adicionar=()):
    t = copy.deepcopy(tax)
    for u in t["units"]:
        for tp in u["topics"]:
            if tp.get("code") == code:
                tp["aliases"] = [a for a in tp.get("aliases", []) if a not in remover] + list(adicionar)
    return t


print("== SO bloco-09 'comunicacao entre processos pipes filas' (07/09: u03; 11/09: u02)")
so = L(GH / "Sistemas-Operacionais-Tutor")
b9 = bloco("Sistemas-Operacionais-Tutor", "bloco-09")
so_hoje = mede("hoje", so, b9)
mede("sem 'Comunicacao entre Processos' e 'Pipes' em 3.1", edita(so, "3.1", remover=("Comunicação entre Processos", "Pipes")), b9)
mede("so 'Comunicacao entre Processos' fora de 3.1", edita(so, "3.1", remover=("Comunicação entre Processos",)), b9)
mede("so 'Pipes' fora de 3.1", edita(so, "3.1", remover=("Pipes",)), b9)
print("== CG bloco-02 'introducao opengl' (07/09: u01 via 1.2 Conceitos com OpenGL; 11/09: sem unidade -> herda bloco-03 u02)")
cg = L(GH / "Computacao-Grafica-Tutor")
b2 = bloco("Computacao-Grafica-Tutor", "bloco-02")
cg_hoje = mede("hoje", cg, b2)
mede("OpenGL e OpenGL 3D de volta em 1.2 Conceitos (07/09)", edita(cg, "1.2", adicionar=("OpenGL", "OpenGL 3D")), b2)
mede("so 'OpenGL' em 1.4 Aplicacoes (ruling do user 11/09)", edita(cg, "1.4", adicionar=("OpenGL",)), b2)
if "--sem-check" not in sys.argv:
    assert so_hoje.startswith("unidade-03"), f"SO bloco-09 devia ser u03, esta {so_hoje or '(nenhuma)'}"
    assert cg_hoje.startswith("unidade-01"), f"CG bloco-02 devia ser u01, esta {cg_hoje or '(nenhuma)'}"
    print("ok: SO bloco-09 = u03 e CG bloco-02 = u01 com a taxonomia de hoje")
