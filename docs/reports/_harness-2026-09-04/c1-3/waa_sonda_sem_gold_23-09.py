"""Sondagem SEM GOLD da operabilidade do W-AA (23/09): nenhum arquivo de gold é lido.
S: quantos materiais do laço têm >= 2 seções (headings markdown; senão itens numerados no início da linha).
G: quantos recebem >= 1 candidato local = expressão forte do material (W-P1) ligada por relação de SUBORDINAÇÃO (P1 em
   outro material; P4 no plano/ementa do professor) a exatamente 1 tópico da unidade final prevista.
Fontes: captura base congelada do W-Z2 (unidade final, laço), índice documental v2 reconstruído com trecho."""
import collections, importlib.util, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
C13 = Path("C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3")
DATA = C13.parents[3]
sys.path.insert(0, str(DATA))


def load(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


z2 = load("z2s", C13 / "wz2_diagnostico_causal_23-09.py")
wz = load("wzs", C13 / "wz_bloco_cobertura_22-09.py")
wu = load("wus", C13 / "wu_cobertura_relacoes_22-09.py")
wp1 = load("wp1s", C13 / "wp1_inventario_matriz_22-09.py")
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
NOMES = wu.NOMES
cap = json.loads((DATA / ".frzero/wz2_captura_base_23-09.json").read_text(encoding="utf-8"))
base, expr = cap["base"], cap["expressoes"]
raizes = {s: wz.root_de(s, NOMES) for s in NOMES}
_, universo = z2.expressoes_v2(wp1, raizes, NOMES)
indice = z2.indice_documental(wu, raizes, universo)
HEAD = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.M)
ITEM = re.compile(r"^\s{0,3}(\d{1,2})[.)]\s+\S", re.M)
FONTES_P4 = ("_inputs_15-09.json:teaching_plan", "_inputs_15-09.json:syllabus")
out = collections.Counter()
exemplos = []
for sig in NOMES:
    root = raizes[sig]
    ents = {str(e["id"]): e for e in json.loads((root / "manifest.json").read_text(encoding="utf-8"))["entries"]}
    tax = z2.taxonomia_slug_unidades(root)
    for eid, rec in base[sig].items():
        if not isinstance(rec, dict) or not rec.get("no_laco") or not rec.get("sub_1a"):
            continue
        out[(sig, "elegiveis")] += 1
        md = _entry_markdown_text_for_file_map(root, ents[eid]) or ""
        nh, ni = len(HEAD.findall(md)), len(ITEM.findall(md))
        if nh >= 2 or ni >= 2:
            out[(sig, "S_operavel")] += 1
        u = rec["final"]["unidade"]
        locais = set()
        for e in expr[sig].get(eid, []):
            tops = {(r["unit_slug"], r["topico"]) for r in indice.get((sig, e), [])
                    if r["doc"] != "material:" + eid and (r["padrao"] == "P1" and r["doc"].startswith("material:")
                                                          or (r["padrao"] == "P4" and r["doc"] in FONTES_P4))}
            na_unidade = {t for (uu, t) in tops if uu == u}
            if len(na_unidade) == 1:
                locais.add(next(iter(na_unidade)))
        if locais:
            out[(sig, "G_operavel")] += 1
            out[(sig, "G_topicos_locais")] += len(locais)
            if len(exemplos) < 6:
                exemplos.append((sig, eid[:40], sorted(locais)[:3]))
for sig in NOMES:
    print(sig, {k: out[(sig, k)] for k in ("elegiveis", "S_operavel", "G_operavel", "G_topicos_locais")})
print("TOTAL", {k: sum(out[(s, k)] for s in NOMES) for k in ("elegiveis", "S_operavel", "G_operavel", "G_topicos_locais")})
print("exemplos (sem gold):", exemplos)
