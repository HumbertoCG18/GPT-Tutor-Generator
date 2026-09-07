"""Gera a tabela ARQUIVO x CENARIO (bloco, unidade, subunidade) para o artefato. Cenarios:
  oraculo   = SARC/Moodle/cronograma (o professor; nenhuma informacao criada pelo aluno)
  gold      = o gold que o user construiu
  zero      = motor puro, sem vocab, sem voter, sem curadoria
  vocab     = motor puro + vocab compilado (1 chamada de LLM por curso)
  auto      = vocab + voter com cache (regime de um tutor novo)
  produto   = automatica + curadoria humana
  sem-desc  = produto sem os blocos de descricao de imagem do Datalab no texto
Saida: dados.json ao lado (para o HTML do artefato). Read-only. Uso: gera_tabela_cenarios.py"""
import collections
import csv
import json
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
C13 = GEN / "docs/reports/_harness-2026-09-04/c1-3"
SNAP = C13 / "snap_placar"
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
src = (C13 / "regua_sem_gold.py").read_text(encoding="utf-8")
ns = {"__name__": "regua_lib", "__file__": str(C13 / "regua_sem_gold.py")}
exec(src.split('REGIMES = {"produto": GH}')[0], ns)
placement_of = ns["placement_of"]
secao_nomeia_unidade, secao_nomeia_topico, bloco_por_assunto = ns["secao_nomeia_unidade"], ns["secao_nomeia_topico"], ns["bloco_por_assunto_da_secao"]
from src.builder.routing.motor.context import build_motor_context  # noqa: E402
from eval_ground_truth import load_labels_csv  # noqa: E402
from eval_entry_unit import _load_truth  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402

REPO = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
        "LR": "Laboratorio-de-Redes-Tutor", "FR": "Fundamentos-de-Redes-Tutor"}
UNI = {"MF", "SO", "IA", "ES2", "TCC"}
CEN = {
    "zero": lambda repo: (SNAP / "zero" / f"{repo}.manifest.json", SNAP / "zero" / f"{repo}.timeline.json"),
    "vocab": lambda repo: (SNAP / "vocab" / f"{repo}.manifest.json", SNAP / "vocab" / f"{repo}.timeline.json"),
    "auto": lambda repo: (SNAP / "auto" / f"{repo}.manifest.json", SNAP / "auto" / f"{repo}.timeline.json"),
    "produto": lambda repo: (GH / repo / "manifest.json", GH / repo / "course/.timeline_index.json"),
    "sem-desc": lambda repo: (GEN / ".ablacao/sem-descricao" / repo / "manifest.json", GEN / ".ablacao/sem-descricao" / repo / "course/.timeline_index.json"),
}


def curto(s, n=42):
    s = str(s or "")
    return s if len(s) <= n else s[-n:]


linhas = []
for sig, repo in REPO.items():
    prod = GH / repo
    man_prod = json.loads((prod / "manifest.json").read_text(encoding="utf-8"))
    tax_p = prod / "course/.content_taxonomy.json"
    tax = json.loads(tax_p.read_text(encoding="utf-8")) if tax_p.exists() else {}
    ctx = build_motor_context(prod, str((man_prod.get("course") or {}).get("course_name") or ""))
    place = placement_of(sig, repo, man_prod, ctx)
    gb = load_labels_csv(GEN / "docs/reports" / f"ground_truth_{sig}.csv") if (GEN / "docs/reports" / f"ground_truth_{sig}.csv").exists() else {}
    gu = _load_truth(sig) if sig in UNI else {}
    gs = {}
    p_sub = GEN / "docs/reports" / f"subunit_gt_{sig}.csv"
    if p_sub.exists():
        for r in csv.DictReader(p_sub.open(encoding="utf-8-sig", newline="")):
            if r["scorable"] == "yes":
                gs[r["entry_id"]] = r["gold_subunit"] or "(vazio)"
    # dados de cada cenario
    dados = {}
    for cen, fn in CEN.items():
        mp, tp = fn(repo)
        if not Path(mp).exists():
            continue
        man = {e["id"]: e for e in json.loads(Path(mp).read_text(encoding="utf-8"))["entries"]}
        ti = {}
        for b in json.loads(Path(tp).read_text(encoding="utf-8"))["blocks"]:
            ti[b["block_uuid"]] = b["id"]; ti[b["id"]] = b["id"]
        dados[cen] = (man, ti)
    for e in man_prod["entries"]:
        eid = e["id"]
        bl, fonte = place.get(eid, ([], ""))
        bl = list(dict.fromkeys(bl or []))
        if not bl:
            alvo = bloco_por_assunto(e.get("source_section"), ctx.blocks)
            if alvo:
                bl, fonte = alvo, "assunto da secao x cronograma"
        row = {
            "curso": sig, "id": eid, "titulo": str(e.get("title") or "")[:70],
            "secao": str(e.get("source_section") or "")[:44], "categoria": str(e.get("category") or ""),
            "oraculo_bloco": "/".join(bl[:3]) + ("+" if len(bl) > 3 else ""), "oraculo_fonte": fonte,
            "oraculo_unidade": curto(secao_nomeia_unidade(e, tax) or ""),
            "oraculo_sub": curto(secao_nomeia_topico(e.get("source_section"), tax)[1] or ""),
            "gold_bloco": gb.get(eid, ""), "gold_unidade": curto(gu.get(eid, "")), "gold_sub": curto(gs.get(eid, "")),
            "revisar": revisar_de(e),
        }
        for cen, (man, ti) in dados.items():
            x = man.get(eid)
            if not x:
                row[cen] = ["", "", ""]
                continue
            row[cen] = [
                ti.get(str(x.get("manual_timeline_block_id") or x.get("temporal_block_id") or ""), ""),
                curto(x.get("computed_unit_slug") or ""),
                curto(x.get("computed_subunit_slug") or ""),
            ]
        linhas.append(row)
out = C13 / "dados_cenarios.json"
out.write_text(json.dumps(linhas, ensure_ascii=False), encoding="utf-8")
c = collections.Counter(r["curso"] for r in linhas)
print(f"{len(linhas)} materiais · {dict(c)} · {out} ({out.stat().st_size // 1024} KB)")
