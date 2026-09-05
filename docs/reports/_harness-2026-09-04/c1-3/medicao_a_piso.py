"""Medicao A (C1 item 3): piso sem-llm da travessia com title := moodle_label (fallback title), em memoria, 0 chamadas."""
import sys, json, copy
from pathlib import Path
GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator"); GH = GEN.parent
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import eval_travessia as ev
REPO = {"IA": "Inteligencia-Artifical-Tutor", "FR": "Fundamentos-de-Redes-Tutor", "CG": "Computacao-Grafica-Tutor"}
_orig = ev._materiais
def _mat_title_label(repo):
    ents = copy.deepcopy(_orig(repo)); k = 0
    for e in ents:
        ml = ev._label(e).strip()
        if ml and ml != str(e.get("title") or ""):
            e["title"] = ml; k += 1
    _mat_title_label.k = k
    return ents
for sig, repo in REPO.items():
    gold = ev.load_gold(GEN / "docs/reports" / f"travessia_gt_{sig}.csv")
    ev._materiais = _orig;            antes = ev.rodar(sig, GH / repo, gold)
    ev._materiais = _mat_title_label; depois = ev.rodar(sig, GH / repo, gold)
    print(f"{sig}: titles reescritos={_mat_title_label.k}/{len(_orig(GH / repo))} | hit@1 {antes['hit1']}->{depois['hit1']} | hit@3 {antes['hit3']}->{depois['hit3']} | bloco {antes['bloco_ok']}/{antes['bloco_n']}->{depois['bloco_ok']}/{depois['bloco_n']}")
    for a, d in zip(antes["linhas"], depois["linhas"]):
        if a["escolhido"] != d["escolhido"] or a["hit1"] != d["hit1"] or a["bloco_pred"] != d["bloco_pred"]:
            print(f"   flip [{a['estilo']}] {a['pergunta'][:55]!r} antes={a['escolhido']} depois={d['escolhido']} hit1 {a['hit1']}->{d['hit1']}")
