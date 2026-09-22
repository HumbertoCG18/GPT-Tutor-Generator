"""W-L: anatomia dos 24 erros de BLOCO por entrada. So le manifests gravados; nao reexecuta o motor.

Gold entra SO para rotular certo/errado (mede.golds(sig)[0]); nunca como entrada de regra.
Ausentes permanecem no denominador (237).
"""
import collections
import csv
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope  # noqa: E402
from src.builder.routing.motor.due_window import tier2_due_scope  # noqa: E402
from src.builder.routing.motor.window_provider import extract_date_in_name  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compare = load("compare_wl", HERE / "compara_herancas_15-09.py")
mede = compare.mede
read = compare.read

DATE_ANY_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}\b")
WEEK_RE = re.compile(r"semana", re.I)
ORDINAL_RE = re.compile(r"(?:^|[^0-9a-z])(?:aula|roteiro|lista|lab|exerc|unidade|u|cap)[a-z]*[ _-]?(\d{1,2})(?!\d)", re.I)
LINK_TYPES = {"url", "github-repo", "link", "youtube", "site"}


def signals(entry):
    """Sinais presentes na ENTRY (nao usa gold). Diz o que existia, nao o que foi usado."""
    section = str(entry.get("source_section") or "")
    title = str(entry.get("title") or "")
    eid = str(entry.get("id") or "")
    date_name = extract_date_in_name(entry)
    ordinal = ORDINAL_RE.search(eid) or ORDINAL_RE.search(title)
    return {
        "data_no_nome": f"{date_name[0]:02d}/{date_name[1]:02d}" if date_name else "",
        "secao_com_data": bool(DATE_ANY_RE.search(section)),
        "secao_com_semana": bool(WEEK_RE.search(section)),
        "posting_date": str(entry.get("posting_date") or ""),
        "ordinal": ordinal.group(1) if ordinal else "",
        "categoria": str(entry.get("category") or ""),
        "escopo_prazo": bool(tier2_due_scope(entry)),
        "fora_de_escopo_disamb": bool(is_out_of_disamb_scope(entry)),
        "source_section": section,
    }


def alavanca(rec):
    """Hipotese de regra candidata (NAO medida) que tocaria a entrada, e a chave do risco."""
    s = rec["sinais"]
    if rec["classe"] == "ausente":
        if rec["eh_link"]:
            return "ingestao-link", "fora do denominador casado"
        # Existe no pacote com o mesmo id e ja sai VAZIO la: casar a origem nao converteria em acerto.
        s = rec.get("sinais_no_pacote") or s
        if rec.get("existe_no_pacote_por_id") and not rec.get("previsto_por_id") and s["fora_de_escopo_disamb"]:
            return "fora-de-escopo", "fora_de_escopo_disamb"
        return "casamento-origem", "fora do denominador casado"
    if rec["classe"] == "vazio":
        if s["escopo_prazo"]:
            return "prazo-sem-due", "escopo_prazo"
        if s["fora_de_escopo_disamb"]:
            return "fora-de-escopo", "fora_de_escopo_disamb"
        return "funil-piso", "engine-None"
    if s["data_no_nome"]:
        return "data-no-nome-vence", "data_no_nome"
    if s["secao_com_data"] or s["secao_com_semana"]:
        return "secao-datada-vence", "secao_datada"
    if s["escopo_prazo"]:
        return "prazo-vence", "escopo_prazo"
    if abs(rec["distancia"] or 99) == 1:
        return f"fronteira-{rec['metodo'] or 'sem-metodo'}", f"metodo:{rec['metodo']}|{rec['banda']}"
    return f"revisar-{rec['metodo'] or 'sem-metodo'}", f"metodo:{rec['metodo']}|{rec['banda']}"


def risk_key_match(entry, key):
    s = signals(entry)
    if key == "data_no_nome":
        return bool(s["data_no_nome"])
    if key == "secao_datada":
        return s["secao_com_data"] or s["secao_com_semana"]
    if key == "escopo_prazo":
        return s["escopo_prazo"]
    if key == "fora_de_escopo_disamb":
        return s["fora_de_escopo_disamb"]
    if key.startswith("metodo:"):
        method, band = key[len("metodo:"):].split("|")
        return str(entry.get("temporal_block_method") or "") == method and str(entry.get("temporal_block_band") or "") == band
    return False


def main():
    out = HERE / "anatomia_bloco_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    errors, corrects, por_curso = [], [], {}
    for sig, name in mede.NOMES.items():
        ref = ROOT / ".frzero/pacote_fontes_15-09" / name
        root = ROOT / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved = {str(e["id"]): e for e in read(root / "manifest.json")["entries"]}
        blocks = read(root / "course/.timeline_index.json")["blocks"]
        order = {str(b["id"]): i for i, b in enumerate(blocks)}
        by_id = {str(b["id"]): b for b in blocks}
        uuid_to_id = {str(b["block_uuid"]): str(b["id"]) for b in blocks}
        uuid_to_id.update({str(b["id"]): str(b["id"]) for b in blocks})
        ref_entries = {str(e["id"]): e for e in read(ref / "manifest.json")["entries"]}
        base_entries = {str(e["id"]): e
                        for e in read(ROOT / ".frzero/implementacao_taxonomia_15-09" / name / "manifest.json")["entries"]}
        source_index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gold_b, gold_u = mede.golds(sig)[0], mede.golds(sig)[1]
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = collections.Counter()
        for row in rows:
            if row["bloco"] == "":
                continue
            eid = row["entry_id"]
            old = ref_entries.get(mapping.get(eid) or "")
            hits = source_index.get(compare.source(old), []) if old else []
            assert len(hits) <= 1, (sig, eid, "origem nao unica")
            entry = hits[0] if hits else None
            truth = gold_b[eid]
            c["n"] += 1
            if entry is None:
                c["ausente"] += 1
                orig = old or base_entries.get(eid) or {}   # identidade original: baseline de 15-09
                homonimo = saved.get(eid)                   # mesmo id no pacote, origem diferente
                eh_link = (str(orig.get("file_type") or "").lower() in LINK_TYPES
                           or str(orig.get("source_path") or "").startswith(("http://", "https://")))
                errors.append({
                    "curso": sig, "entry_id": eid, "classe": "ausente", "metodo": "", "banda": "", "flag": None,
                    "provider": "", "janela": [], "previsto": "", "gold": truth, "distancia": None, "sentido": "",
                    "computed_block_id": "", "computed_acertaria": None, "computed_metodo": "",
                    "unidade_errada": None, "title": str(orig.get("title") or ""),
                    "file_type": str(orig.get("file_type") or ""), "categoria": str(orig.get("category") or ""),
                    "source_path": str(orig.get("source_path") or ""), "eh_link": eh_link,
                    "existe_no_pacote_por_id": homonimo is not None,
                    "previsto_por_id": compare.predictions(root, homonimo)[0] if homonimo else "",
                    "metodo_por_id": str((homonimo or {}).get("temporal_block_method") or ""),
                    "sinais": signals(orig),
                    "sinais_no_pacote": signals(homonimo) if homonimo else None,
                    "degrau": ("link nunca ingerido: nao existe entry no pacote, nenhuma regra de bloco o alcanca"
                               if eh_link else
                               "existe no pacote com o mesmo id, mas source_path mudou e a regua nao casa a origem"),
                })
                continue
            pred = compare.predictions(root, entry)[0]
            ok = pred == truth
            c["certo"] += ok
            if ok:
                corrects.append({"curso": sig, "entry_id": eid, "id": str(entry["id"]),
                                 "metodo": str(entry.get("temporal_block_method") or ""),
                                 "banda": str(entry.get("temporal_block_band") or ""), "entry": entry})
                continue
            computed = uuid_to_id.get(str(entry.get("computed_block_id") or ""), "")
            di = order.get(pred), order.get(truth)
            dist = (di[0] - di[1]) if (di[0] is not None and di[1] is not None) else None
            unit_ok = None
            if row["unidade"] != "" and eid in gold_u:
                unit_ok = str(entry.get("computed_unit_slug") or "") not in gold_u[eid]
            rec = {
                "curso": sig, "entry_id": eid, "id": str(entry["id"]),
                "classe": "vazio" if pred == "" else ("vizinho±1" if dist in (1, -1) else "distante"),
                "metodo": str(entry.get("temporal_block_method") or ""),
                "banda": str(entry.get("temporal_block_band") or ""),
                "flag": entry.get("temporal_block_flag"),
                "provider": str(entry.get("temporal_block_provider") or ""),
                "janela": entry.get("temporal_block_window") or [],
                "janela_ids": [uuid_to_id.get(str(r), str(r)) for r in (entry.get("temporal_block_window") or [])],
                "previsto": pred, "gold": truth, "distancia": dist,
                "sentido": "" if not dist else ("gold anterior" if dist > 0 else "gold posterior"),
                "gold_kind": str(by_id.get(truth, {}).get("kind") or ""),
                "gold_unit_slug": str(by_id.get(truth, {}).get("unit_slug") or ""),
                "computed_block_id": computed, "computed_acertaria": bool(computed) and computed == truth,
                "computed_metodo": str(entry.get("computed_block_method") or ""),
                "unidade_errada": unit_ok, "title": str(entry.get("title") or ""),
                "file_type": str(entry.get("file_type") or ""), "sinais": signals(entry),
                "manual_pin": str(entry.get("manual_timeline_block_id") or ""),
            }
            if rec["classe"] == "vazio":
                s = rec["sinais"]
                rec["degrau"] = ("apply.py:92-94 due-window sem casar e resolve_unscoped None (hipotese)"
                                 if s["escopo_prazo"] else
                                 "apply.py:97-104 is_out_of_disamb_scope -> temporal limpo (hipotese)"
                                 if s["fora_de_escopo_disamb"] else
                                 "apply.py:117-119 engine.resolve None (funil-piso) (hipotese)")
            else:
                rec["degrau"] = ""
            # Separa erro de DESEMPATE (gold estava entre os candidatos) de janela que nao contem o gold.
            rec["gold_na_janela"] = truth in rec["janela_ids"] if rec["janela_ids"] else None
            rec["alavanca"], rec["chave_risco"] = alavanca(rec)
            errors.append(rec)
        por_curso[sig] = dict(c)
    for rec in errors:
        if rec["classe"] == "ausente":
            rec["alavanca"], rec["chave_risco"] = alavanca(rec)

    # (4) risco por metodo+banda: quantas entradas CERTAS hoje compartilham o metodo/banda, por curso.
    risco_metodo = collections.defaultdict(lambda: collections.Counter())
    for item in corrects:
        risco_metodo[(item["metodo"], item["banda"])][item["curso"]] += 1
        risco_metodo[(item["metodo"], item["banda"])]["TOTAL"] += 1
    metodos_com_erro = {(r["metodo"], r["banda"]) for r in errors if r["classe"] != "ausente"}

    # alavancas: tocadas = erros que ela cobre; em risco = certas hoje que a chave tambem atinge.
    alavancas = {}
    for rec in errors:
        a = alavancas.setdefault(rec["alavanca"], {"tocadas": 0, "entradas": [], "chaves": set(), "em_risco": 0,
                                                   "risco_por_curso": collections.Counter()})
        a["tocadas"] += 1
        a["entradas"].append(f"{rec['curso']}:{rec['entry_id']}")
        a["chaves"].add(rec["chave_risco"])
    for name, a in alavancas.items():
        seen = set()
        for item in corrects:
            if item["entry_id"] in seen:
                continue
            if any(risk_key_match(item["entry"], k) for k in a["chaves"]):
                a["em_risco"] += 1
                a["risco_por_curso"][item["curso"]] += 1
                # pino manual vence a cascata (apply.py:78-80): essas certas nao dependem do degrau.
                a["em_risco_com_pino_manual"] = a.get("em_risco_com_pino_manual", 0) + bool(
                    str(item["entry"].get("manual_timeline_block_id") or "").strip())
                seen.add(item["entry_id"])
        a["chaves"] = sorted(a["chaves"])
        a.setdefault("em_risco_com_pino_manual", 0)
        a["risco_por_curso"] = dict(a["risco_por_curso"])
        a["razao_tocadas_por_risco"] = round(a["tocadas"] / a["em_risco"], 2) if a["em_risco"] else None

    classes = collections.Counter(r["classe"] for r in errors)
    por_metodo = collections.Counter(f"{r['metodo'] or '-'}/{r['banda'] or '-'}" for r in errors if r["classe"] != "ausente")
    total = collections.Counter()
    for c in por_curso.values():
        total.update(c)
    checks = {
        "bloco_213_237": total["certo"] == 213 and total["n"] == 237,
        "ausentes_6": classes["ausente"] == 6,
        "vizinho_8": classes["vizinho±1"] == 8,
        "distante_7": classes["distante"] == 7,
        "vazio_3": classes["vazio"] == 3,
        "MF_53_66": por_curso["MF"]["certo"] == 53 and por_curso["MF"]["n"] == 66,
        "ausentes_links_5_de_6": sum(r["eh_link"] for r in errors if r["classe"] == "ausente") == 5,
    }
    for rec in errors:
        rec.pop("entry", None)
    report = {
        "head": "9220a57", "escopo": "Diagnostico read-only sobre manifests de 15/17-09; nenhum build, rede ou LLM.",
        "checks": checks, "total": dict(total), "por_curso": por_curso, "classes": dict(classes),
        "por_metodo_banda_erros": dict(por_metodo),
        "risco_por_metodo_banda": {f"{m}/{b}": dict(v) for (m, b), v in sorted(risco_metodo.items())
                                   if (m, b) in metodos_com_erro},
        "alavancas": {k: v for k, v in sorted(alavancas.items(), key=lambda kv: -kv[1]["tocadas"])},
        "erros": sorted(errors, key=lambda r: (r["curso"], r["entry_id"])),
        "limitacoes": [
            "Metodo/banda/provider/janela sao os campos GRAVADOS; o degrau exato da cascata nao e persistido.",
            "Degrau dos vazios e HIPOTESE derivada de tier2_due_scope/is_out_of_disamb_scope avaliados agora sobre a entry gravada.",
            "Alavancas sao hipoteses NAO medidas: 'tocadas' e 'em risco' sao contagens, nao ganho.",
            "computed_block_id e o scorer de conceito; a regua de bloco nao o usa. 'computed_acertaria' e contrafactual de campo, nao de execucao.",
        ],
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print("CHECKS", checks)
    print("TOTAL", dict(total), "CLASSES", dict(classes))
    print("POR_CURSO", por_curso)
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
