"""Estado do motor em 08/09, para fechar a campanha e abrir a proxima. 0 chamadas.

Responde, com dado, as 3 perguntas do user:
  1. "unidade esta 100% (190/190) e bloco quase (235/237)?" -> mostra tambem QUANTO do universo o gold cobre
  2. "o que significa fila e sem bloco?"                    -> anatomia da fila por motivo
  3. "quais arquivos estao sem bloco?"                      -> lista, com categoria/secao e se e 'honesto' ou duvida
Uso: estado_08_09.py
"""
import collections
import csv as _csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
TODOS = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor", "ES2": "Engenharia-Software-2-Tutor",
         "TCC": "TCC-Tutor", "MF": "Metodos-Formais-Tutor", "CG": "Computacao-Grafica-Tutor",
         "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from eval_entry_unit import _load_truth  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from src.builder.routing.resolver_apply import _is_material  # noqa: E402
from src.builder.routing.revisar import _sem_bloco_honesto, motivos_de, revisar_de  # noqa: E402

print("1) QUANTO DO UNIVERSO CADA REGUA COBRE  (o '100%' vale dentro do gold, nao no repo inteiro)")
print(f"{'':5} {'materiais':>10} {'gold bloco':>11} {'gold unidade':>13} {'gold subunid':>13}")
TG = collections.Counter()
for sig, repo in TODOS.items():
    man = [e for e in json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]]
    mats = [e for e in man if _is_material(e)]
    try:
        gb = len(load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv"))
    except Exception:
        gb = 0
    gu = len(_load_truth(sig)) if sig in UNI else 0
    p = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    gs = len([r for r in _csv.DictReader(p.open(encoding="utf-8-sig", newline="")) if r["scorable"] == "yes"]) if p.exists() else 0
    TG["mat"] += len(mats)
    TG["gb"] += gb
    TG["gu"] += gu
    TG["gs"] += gs
    print(f"{sig:5} {len(mats):10} {gb:11} {gu:13} {gs:13}")
print(f"{'TOT':5} {TG['mat']:10} {TG['gb']:11} {TG['gu']:13} {TG['gs']:13}")
print(f"      cobertura do gold: bloco {100 * TG['gb'] / TG['mat']:.0f}% · unidade {100 * TG['gu'] / TG['mat']:.0f}% · subunidade {100 * TG['gs'] / TG['mat']:.0f}%")

print("\n2) ANATOMIA DA FILA  (fila = 'duvida' + 'mudou'; um material pode disparar 2+ motivos)")
FILA = collections.Counter()
MUD = collections.Counter()
POR = {}
for sig, repo in TODOS.items():
    man = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    c = collections.Counter()
    nd = nm = 0
    for e in man:
        if not e.get("revisar"):
            continue
        ms = motivos_de(e)
        if ms:
            nd += 1
            c.update(ms)
        elif revisar_de(e) == "mudou":
            nm += 1
    FILA.update(c)
    MUD[sig] = nm
    POR[sig] = (nd, nm, len([e for e in man if _is_material(e)]))
    print(f"  {sig:4} duvida={nd:3} mudou={nm:3}  {dict(c.most_common())}")
print(f"\n  {'motivo':22} {'n':>4}   o que quer dizer")
EXPL = {
    "conflito": "o texto do material diz uma unidade e o bloco diz outra (o bloco decide; fica o registro)",
    "sub-ambigua": "dois ou mais subtopicos empataram acima do limiar",
    "sub-empate": "empate EXATO de score entre subtopicos",
    "flag:disamb": "o bloco saiu de um desempate, nao de sinal direto",
    "flag:due-straddle": "a data de entrega cai entre dois blocos",
    "sem-bloco": "nao caiu em nenhum bloco do cronograma E nao e categoria fora do eixo temporal",
}
for k, v in FILA.most_common():
    print(f"  {k:22} {v:4}   {EXPL.get(k, '')}")
print(f"  {'mudou (sync)':22} {sum(MUD.values()):4}   decisao confiante que se moveu na ultima sincronizacao; a proxima limpa se nada mover")
tot_d = sum(v[0] for v in POR.values())
tot_m = sum(v[1] for v in POR.values())
tot_mat = sum(v[2] for v in POR.values())
print(f"\n  FILA = {tot_d} duvida + {tot_m} mudou = {tot_d + tot_m} em {tot_mat} materiais = {100 * (tot_d + tot_m) / tot_mat:.1f} por 100")

print("\n3) MATERIAIS SEM BLOCO HOJE")
print(f"{'':4} {'material':38} {'categoria':18} {'secao':26} {'situacao'}")
n_hon = n_duv = 0
for sig, repo in TODOS.items():
    man = json.loads((GH / repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    for e in man:
        if not _is_material(e):
            continue
        if str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or "").strip():
            continue
        hon = _sem_bloco_honesto(e)
        n_hon += hon
        n_duv += not hon
        print(f"{sig:4} {e['id'][:38]:38} {str(e.get('category') or '-')[:18]:18} {str(e.get('source_section') or '-')[:26]:26} "
              f"{'fora do eixo temporal (nao e pendencia)' if hon else 'DUVIDA: deveria ter bloco'}")
print(f"\n  {n_hon} fora do eixo temporal por desenho · {n_duv} sao duvida de verdade")
