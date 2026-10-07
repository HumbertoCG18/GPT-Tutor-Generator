"""Diagnóstico dos erros de subunidade primário nos 7 cursos, sobre os builds existentes; sem build, sem rede.

Cada material com gold de subunidade primário é classificado em: acerto / aceito_nao_primario / vazio / errado
(unidade certa ou errada), com categoria da entrada e evidência do rótulo gold no texto extraído + título +
moodle_label: texto_vazio / rotulo_ausente (0 token do rótulo) / rotulo_generico (só tokens que aparecem em 2+
tópicos do curso) / rotulo_presente (1+ token exclusivo do tópico gold). Autoteste: reproduz o placar 84/251.
"""
import argparse
import collections
import csv
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compare = load("compare_herancas", HERE / "compara_herancas_15-09.py")
mede = compare.mede
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map  # noqa: E402
from src.builder.core.code_summarization import code_curation_signal_text, load_code_curation  # noqa: E402

REF = ".frzero/pacote_fontes_15-09"
NEW = {"MF": ".frzero/pacote_categoria_17-09", "IA": ".frzero/pacote_categoria_17-09"}
PLACAR = {**{c: v["counts"]["sub_primario_after"] for c, v in
             json.loads((HERE / "verificacao_pacote_7cursos_15-09.json").read_text(encoding="utf-8"))["courses"].items()},
          **{c: v["counts"]["sub_primario_novo"] for c, v in
             json.loads((HERE / "verificacao_pacote_categoria_MF_IA_17-09.json").read_text(encoding="utf-8"))["courses"].items()}}
CLASSES = ("acerto", "aceito_nao_primario", "vazio", "errado_unidade_certa", "errado_unidade_errada", "ausente")
EVIDENCE = ("texto_vazio", "rotulo_ausente", "rotulo_generico", "rotulo_presente")


def ascii_lower(text):
    return "".join(c for c in unicodedata.normalize("NFD", str(text or "").lower()) if not unicodedata.combining(c))


def tokens(text, min_len=4):
    return {t for t in re.findall(r"[a-z0-9]+", ascii_lower(text)) if len(t) >= min_len}


def siglas(text):
    """Siglas do rótulo ("DNS", "OSI", "TCP/IP", "3D"): o scorer as aceita apesar de len<4 (index.py:1849,
    short_vocab por LABEL do curso). Sem isto o diagnóstico descartava "DNS" e marcava o erro como genérico (Astra 17/09)."""
    folded = "".join(c for c in unicodedata.normalize("NFD", str(text or "")) if not unicodedata.combining(c))
    return {s.lower() for s in re.findall(r"\b[A-Z][A-Z0-9]{1,3}\b", folded)}


def topic_index(root):
    """slug -> tokens do rótulo+aliases (>=4 chars ou sigla), exclusivos no curso, exclusivos na unidade, unidades."""
    per_slug, units = collections.defaultdict(set), collections.defaultdict(set)
    for unit in compare.read(root / "course/.content_taxonomy.json")["units"]:
        for topic in unit.get("topics", []):
            raw = " ".join([topic.get("label", ""), *topic.get("aliases", [])])
            per_slug[topic["slug"]] |= tokens(raw) | siglas(raw)
            units[topic["slug"]].add(topic.get("unit_slug") or unit["slug"])
    freq = collections.Counter(t for toks in per_slug.values() for t in toks)
    freq_unit = collections.Counter((u, t) for slug, toks in per_slug.items() for u in units[slug] for t in toks)
    return {slug: {"all": toks, "distinct": {t for t in toks if freq[t] == 1},
                   "distinct_unit": {t for t in toks if all(freq_unit[(u, t)] == 1 for u in units[slug])},
                   "units": units[slug]}
            for slug, toks in per_slug.items()}


EMPTY = {"all": set(), "distinct": set(), "distinct_unit": set(), "units": set()}


def evidence(body, present_all, present_distinct):
    return ("texto_vazio" if not body else "rotulo_ausente" if not present_all
            else "rotulo_generico" if not present_distinct else "rotulo_presente")


def classify(sig, root, ref_root, rows, topics):
    ref_by_id = {e["id"]: e for e in compare.read(ref_root / "manifest.json")["entries"]}
    by_source = compare.indexed(compare.read(root / "manifest.json")["entries"])
    mapping = {e["entry_id"]: e["new_id"] for e in compare.read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
    gold_unit, gold_acc, gold_prim = mede.golds(sig)[1], mede.golds(sig)[2], mede.golds(sig)[3]
    # zips/códigos não têm .md: o scorer de subunidade lê o resumo de code_curation.json como sinal léxico
    # (code_summarization.py:295). Sem isto, todo zip apareceria como texto_vazio.
    curation = load_code_curation(root).get("entries", {}) or {}
    for row in rows:
        eid = row["entry_id"]
        old = ref_by_id.get(mapping.get(eid) or "")
        entry = (by_source.get(compare.source(old)) or [None])[0] if old else None
        truth_prim, truth_acc = gold_prim[eid], gold_acc[eid]
        rec = {"curso": sig, "entry_id": eid, "gold_primario": sorted(truth_prim), "gold_aceito": sorted(truth_acc)}
        if entry is None:
            rec.update(classe="ausente", evidencia="", categoria="", file_type="", pred_sub="", pred_unidade="")
            yield rec
            continue
        block, unit, sub = compare.predictions(root, entry)
        markdown = _entry_markdown_text_for_file_map(root, entry).strip()
        code_text = code_curation_signal_text(curation.get(entry["id"], {})).strip()
        body = "\n".join(t for t in (markdown, code_text) if t)
        fonte_texto = {(True, True): "markdown+resumo_codigo", (True, False): "markdown",
                       (False, True): "resumo_codigo", (False, False): "nenhum"}[(bool(markdown), bool(code_text))]
        pool = tokens(" ".join([entry.get("title", ""), entry.get("moodle_label", ""),
                                Path(entry.get("source_path", "")).name, body]), min_len=2)
        gold_all = set().union(*(topics.get(s, EMPTY)["all"] for s in truth_prim))
        gold_distinct = set().union(*(topics.get(s, EMPTY)["distinct"] for s in truth_prim))
        gold_distinct_unit = set().union(*(topics.get(s, EMPTY)["distinct_unit"] for s in truth_prim))
        gold_units = set().union(*(topics.get(s, EMPTY)["units"] for s in truth_prim)) or set(gold_unit.get(eid, ()))
        present_all, present_distinct = gold_all & pool, gold_distinct & pool
        present_distinct_unit = gold_distinct_unit & pool
        pred_present = (topics.get(sub, EMPTY)["all"] & pool) if sub else set()
        if sub in truth_prim:
            classe = "acerto"
        elif sub in truth_acc:
            classe = "aceito_nao_primario"
        elif not sub:
            classe = "vazio"
        else:
            classe = "errado_unidade_certa" if unit in gold_units else "errado_unidade_errada"
        rec.update(classe=classe, evidencia=evidence(body, present_all, present_distinct),
                   evidencia_unidade=evidence(body, present_all, present_distinct_unit),
                   categoria=entry.get("category", ""), file_type=entry.get("file_type", ""), pred_sub=sub,
                   pred_unidade=unit, gold_unidades=sorted(gold_units), fonte_texto=fonte_texto, texto_chars=len(body),
                   tokens_gold=len(gold_all), tokens_gold_exclusivos=len(gold_distinct),
                   tokens_gold_exclusivos_unidade=len(gold_distinct_unit), gold_no_texto=sorted(present_all),
                   gold_exclusivo_no_texto=sorted(present_distinct),
                   gold_exclusivo_unidade_no_texto=sorted(present_distinct_unit), pred_no_texto=sorted(pred_present),
                   titulo=entry.get("title", ""))
        yield rec


def table(title, rows_keys, total, prefix):
    print(title)
    print(" " * 24 + "".join(f"{e:>18}" for e in EVIDENCE) + f"{'soma':>8}")
    for key in rows_keys:
        vals = [total[f"{prefix}:{key}|{e}"] for e in EVIDENCE]
        print(f"{key:24}" + "".join(f"{v:>18}" for v in vals) + f"{sum(vals):>8}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="diagnostico_subunidade_17-09")
    out = HERE / parser.parse_args().saida
    assert out.parent == HERE and not out.with_suffix(".json").exists(), "preservar resultado existente"
    detail, report = [], {}
    for sig, name in mede.NOMES.items():
        ref_root, root = ROOT / REF / name, ROOT / NEW.get(sig, REF) / name
        rows = [r for r in csv.DictReader((HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig"))
                if r["sub_primario"] != ""]
        counts = collections.Counter()
        for rec in classify(sig, root, ref_root, rows, topic_index(root)):
            detail.append(rec)
            counts["n"] += 1
            counts[f"classe:{rec['classe']}"] += 1
            if rec["classe"] not in ("acerto", "ausente"):
                counts[f"erro_evid:{rec['evidencia']}"] += 1
                counts[f"erro_evid_unidade:{rec['evidencia_unidade']}"] += 1
                counts[f"erro_cat:{rec['categoria']}"] += 1
                counts[f"erro_cat_evid:{rec['categoria']}|{rec['evidencia']}"] += 1
                counts[f"erro_classe_evid:{rec['classe']}|{rec['evidencia']}"] += 1
        hits = counts["classe:acerto"]
        assert hits == PLACAR[sig], (sig, hits, PLACAR[sig])
        report[sig] = {"root": root.relative_to(ROOT).as_posix(), "counts": dict(counts)}
        print(f"{sig:4} n={counts['n']:3} acerto={hits:3} "
              + " ".join(f"{c}={counts[f'classe:{c}']}" for c in CLASSES[1:])
              + " | " + " ".join(f"{e}={counts[f'erro_evid:{e}']}" for e in EVIDENCE))
    total = collections.Counter()
    for v in report.values():
        total.update(v["counts"])
    assert (total["n"], total["classe:acerto"]) == (251, 84), (total["n"], total["classe:acerto"])
    print("\nTOTAL n=251 acerto=84 erros=167")
    table("classe x evidencia (erros):", CLASSES[1:], total, "erro_classe_evid")
    cats = sorted({k.split(":")[1].split("|")[0] for k in total if k.startswith("erro_cat_evid:")})
    table("categoria x evidencia (erros):", cats, total, "erro_cat_evid")
    out.with_suffix(".json").write_text(json.dumps({
        "courses": report, "total": dict(total),
        "scope": "diagnostico sobre builds existentes; sem build, sem rede; evidencia = tokens (>=4 chars, sem acento) "
                 "do rotulo+aliases do topico gold no texto+titulo+moodle_label+nome do arquivo"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    fields = ["curso", "entry_id", "classe", "evidencia", "evidencia_unidade", "categoria", "file_type", "pred_sub",
              "gold_primario", "gold_aceito", "pred_unidade", "gold_unidades", "fonte_texto", "texto_chars", "tokens_gold",
              "tokens_gold_exclusivos", "tokens_gold_exclusivos_unidade", "gold_no_texto", "gold_exclusivo_no_texto",
              "gold_exclusivo_unidade_no_texto", "pred_no_texto", "titulo"]
    with out.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for rec in detail:
            writer.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v) for k, v in rec.items()})


if __name__ == "__main__":
    main()
