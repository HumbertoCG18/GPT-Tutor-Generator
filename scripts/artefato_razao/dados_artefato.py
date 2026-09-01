"""Gera dados.json do artefato Razao dos Blocos (movido do scratch em 31/08; era P2c do handoff).
Uso: python scripts/artefato_razao/dados_artefato.py && python scripts/artefato_razao/patch_razao.py
Saida: razao_dos_blocos.html AO LADO (gitignored) -> publicar no artefato d2ef4eaa via mesma sessao/url."""
import json, csv, re
from pathlib import Path
GH = Path(r"C:/Users/Humberto/Documents/GitHub"); GEN = GH / "GPT-Tutor-Generator"
REPO = {"MF": ("Metodos-Formais-Tutor", "Métodos Formais"), "SO": ("Sistemas-Operacionais-Tutor", "Sistemas Operacionais"), "IA": ("Inteligencia-Artifical-Tutor", "Inteligência Artificial"), "ES2": ("Engenharia-Software-2-Tutor", "Engenharia de Software II"), "TCC": ("TCC-Tutor", "Teoria da Computação"), "CG": ("Computacao-Grafica-Tutor", "Computação Gráfica")}
out = {}
for sig, (rn, nome) in REPO.items():
    repo = GH / rn
    if not (repo / 'manifest.json').exists(): continue
    m = json.load(open(repo / "manifest.json", encoding="utf-8"))
    ti = json.load(open(repo / "course/.timeline_index.json", encoding="utf-8"))["blocks"]
    cbm = json.load(open(repo / "course/.card_block_map.json", encoding="utf-8")) if (repo / "course/.card_block_map.json").exists() else {}
    cur = json.load(open(repo / "course/.timeline_curation.json", encoding="utf-8")) if (repo / "course/.timeline_curation.json").exists() else {}
    pinned_units = {u: v.get("manual_unit_slug") for u, v in (cur.get("blocks") or {}).items() if isinstance(v, dict) and v.get("manual_unit_slug")}
    u2d = {b["block_uuid"]: b["id"] for b in ti}
    blocks = []
    for b in ti:
        blocks.append({"id": b["id"], "uuid": b["block_uuid"], "ini": b.get("period_start"), "fim": b.get("period_end"), "kind": b.get("kind"),
                       "topico": b.get("primary_topic_label") or b.get("topic_text") or "", "unidade": b.get("unit_slug") or "", "unidade_pino": pinned_units.get(b["block_uuid"], ""),
                       "sessoes": [{"data": s.get("date"), "label": s.get("label"), "kind": s.get("kind")} for s in (b.get("sessions") or [])]})
    gold = {}
    gp = GEN / "docs/reports" / f"ground_truth_{sig}.csv"
    if gp.exists():
        for r in csv.DictReader(open(gp, encoding="utf-8-sig")):
            gold[r["id"]] = {"bloco": u2d.get(r["true_block_uuid"], r["true_block_id"]), "scorable": r["scorable"] == "yes"}
    cards = {}
    for k, v in cbm.items():
        if isinstance(v, dict):
            cards[k] = {"source": v.get("source"), "blocos": [u2d.get(x, x) for x in (v.get("block_ids") or [])]}
    entries = []
    for e in m["entries"]:
        tb = e.get("temporal_block_id") or ""
        g = gold.get(e["id"])
        entries.append({"id": e["id"], "titulo": e.get("title") or e["id"], "arquivo": re.split(r"[\/]", str(e.get("source_path") or ""))[-1],
                        "categoria": e.get("category") or "", "card": e.get("source_section") or "", "label": (e.get("moodle_label") or ""), "postagem": e.get("posting_date") or "",
                        "bloco": u2d.get(tb, tb), "metodo": e.get("temporal_block_method") or "", "provider": e.get("temporal_block_provider") or "", "band": e.get("temporal_block_band") or "",
                        "pino": u2d.get(e.get("manual_timeline_block_id") or "", e.get("manual_timeline_block_id") or ""), "unidade": e.get("computed_unit_slug") or "", "unidade_pino": e.get("manual_unit_slug") or "",
                        "subunidade": e.get("computed_subunit_slug") or "", "gold": g["bloco"] if g else "", "scorable": bool(g and g["scorable"])})
    out[sig] = {"nome": nome, "blocos": blocks, "entries": entries, "cards": cards}
    ok = sum(1 for e in entries if e["scorable"] and e["gold"] == e["bloco"]); n = sum(1 for e in entries if e["scorable"])
    print(sig, "blocos", len(blocks), "entries", len(entries), "gold", f"{ok}/{n}", "cards", len(cards), "manual:", sum(1 for c in cards.values() if c["source"] == "manual"))
Path(__file__).with_name("dados.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print("json kb:", len(json.dumps(out, ensure_ascii=False)) // 1024)
