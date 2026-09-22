"""W-T (CRU-03 unidade): anatomia dos 38 erros de unidade no estado #49 + bloqueios de subunidade.

Cadeia REAL bloco -> unidade (molde de `aceite_v1_49_22-09.py` linhas 55-110): `replay_bloco_21-09.replay`
alimenta `replay_unidade_21-09.replay` via patch de `ru.read` do manifest. Avaliacao pela regua
`compara_herancas_15-09` (`mede.golds`). Gold SO na avaliacao, carregado DEPOIS do congelamento por hash
das decisoes. Sem build, rede, LLM (voter=None), sem tocar src/ nem tests/.

CLASSES DE ERRO DE UNIDADE (pre-declaradas, ordem de desempate = a ordem abaixo):
  ausente                                entrada nao esta no pacote (origem nao casa) -> nenhuma predicao
  abstencao                              unidade final vazia
  herdada_do_bloco_errado                razao veio do bloco (herdada_do_bloco=/reconciliada_do_bloco=/
                                         unidade_do_bloco_manual/herdada_do_vizinho=) E o bloco predito != gold de bloco
  herdada_do_bloco_certo_mas_gold_diverge  idem, mas o bloco predito == gold de bloco (regua ou bloco multiunidade)
  texto_vence_errado                     razao de texto/secao/vizinho (secao-vence-bloco=, explicita-vence-bloco=,
                                         texto-vence-vizinho=) ou nenhuma razao de bloco (o scorer manteve) e unidade != gold
  regua_ambigua                          FLAG paralela: gold com > 1 unidade aceita e predicao fora (reportada por fora,
                                         sem tirar o erro da classe mecanica)

BLOQUEIO DE SUBUNIDADE = a unidade vigente no estado #49 nao contem NENHUM slug do gold primario, casando
por (unidade, slug) na taxonomia `<root>/course/.content_taxonomy.json`. Slug duplicado em mais de uma
unidade e reportado em separado.
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))

RAZOES_DE_BLOCO = ("herdada_do_bloco=", "reconciliada_do_bloco=", "unidade_do_bloco_manual", "herdada_do_vizinho=")
RAZOES_DE_TEXTO = ("secao-vence-bloco=", "explicita-vence-bloco=", "texto-vence-vizinho=")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def taxonomia_por_unidade(root):
    """(unidade_slug -> set(topic slug))  e  (topic slug -> set(unidade_slug))."""
    p = root / "course/.content_taxonomy.json"
    por_unidade, por_slug = collections.defaultdict(set), collections.defaultdict(set)
    if not p.exists():
        return por_unidade, por_slug
    for unit in read(p).get("units", []) or []:
        u = str(unit.get("slug") or unit.get("unit_slug") or "")
        for topic in unit.get("topics", []) or []:
            s = str(topic.get("slug") or "")
            u2 = str(topic.get("unit_slug") or u)
            if s:
                por_unidade[u2].add(s)
                por_slug[s].add(u2)
    return por_unidade, por_slug


def main():
    compare = load("wt_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    rb = load("wt_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wt_ru", HERE / "replay_unidade_21-09.py")
    orig_read = ru.read

    # ---------------------------------------------------------------- fase real, SEM gold
    estado = {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / name
        saved, bloco_novo, _, _ = rb.replay(root)
        feed = [copy.deepcopy(bloco_novo[i]) for i in bloco_novo]

        def patched(path, _feed=feed):
            data = orig_read(path)
            if Path(path).name == "manifest.json":
                data = {**data, "entries": _feed}
            return data

        ru.read = patched
        try:
            _, novo, raw = ru.replay(root)
        finally:
            ru.read = orig_read
        estado[sig] = {"root": root, "saved": saved, "novo": novo, "raw": raw}
        print("cadeia", sig, len(novo), flush=True)

    # congelamento das decisoes ANTES de ver o gold
    congelado = {sig: {eid: {"bloco": compare.predictions(v["root"], e)[0],
                             "unidade": str(e.get("computed_unit_slug") or ""),
                             "sub": str(e.get("computed_subunit_slug") or ""),
                             "reasons": [str(r) for r in e.get("unit_match_reasons") or []],
                             "conflict": e.get("unit_block_conflict") or {},
                             "raw": v["raw"].get(eid)}
                       for eid, e in v["novo"].items()}
                 for sig, v in estado.items()}
    blob = json.dumps(congelado, ensure_ascii=False, sort_keys=True).encode("utf-8")
    sha_congelamento = hashlib.sha256(blob).hexdigest()
    print("CONGELAMENTO", sha_congelamento, flush=True)

    # ---------------------------------------------------------------- avaliacao (gold entra aqui)
    tot = collections.Counter()
    erros, por_curso = [], {}
    bloqueios, bloq_amb = [], []
    for sig, v in estado.items():
        root, saved, novo = v["root"], v["saved"], v["novo"]
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig] / "manifest.json")["entries"]}
        index = compare.indexed(list(saved.values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gb, gu, gs, gsp = mede.golds(sig)
        por_unidade, por_slug = taxonomia_por_unidade(root)
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        c = collections.Counter()
        for row in rows:
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            eid = str(hits[0]["id"]) if hits else None
            dec = congelado[sig].get(eid) if eid else None
            pb = dec["bloco"] if dec else ""
            pu = dec["unidade"] if dec else ""
            ps = dec["sub"] if dec else ""
            if row["bloco"] != "":
                c["bloco_n"] += 1
                c["bloco"] += bool(dec and pb == gb[gid])
            if row["unidade"] != "":
                c["unidade_n"] += 1
                acerto = bool(dec and pu in gu[gid])
                c["unidade"] += acerto
                if not acerto:
                    reasons = dec["reasons"] if dec else []
                    de_bloco = any(str(r).startswith(RAZOES_DE_BLOCO) or str(r) in RAZOES_DE_BLOCO for r in reasons)
                    de_texto = any(str(r).startswith(RAZOES_DE_TEXTO) for r in reasons)
                    bloco_ok = bool(dec and pb == gb.get(gid))
                    if dec is None:
                        classe = "ausente"
                    elif not pu:
                        classe = "abstencao"
                    elif de_bloco and not de_texto:
                        classe = "herdada_do_bloco_errado" if not bloco_ok else "herdada_do_bloco_certo_mas_gold_diverge"
                    else:
                        classe = "texto_vence_errado"
                    bruto = (dec or {}).get("raw") or {}
                    erros.append({
                        "curso": sig, "gold_id": gid, "entry_id": eid, "classe": classe,
                        "bloco_pred": pb, "bloco_gold": gb.get(gid, ""), "bloco_ok": bloco_ok,
                        "unidade_pred": pu, "unidade_gold": sorted(gu[gid]),
                        "regua_ambigua": len(gu[gid]) > 1,
                        "reasons": reasons, "conflict": (dec or {}).get("conflict") or {},
                        "scorer_bruto": bruto.get("slug"), "scorer_conf": bruto.get("confidence"),
                        "scorer_ambiguo": bruto.get("ambiguous"),
                        "bruto_acertaria": bool(bruto.get("slug") and bruto.get("slug") in gu[gid]),
                        "source_path": (saved.get(eid) or {}).get("source_path") if eid else None,
                        "titulo": (saved.get(eid) or {}).get("title") if eid else None,
                    })
                    c[f"cls_{classe}"] += 1
            if row["sub_primario"] != "":
                c["sub_n"] += 1
                c["sub_primaria"] += bool(dec and ps in gsp[gid])
                c["sub_aceita"] += bool(dec and ps in gs[gid])
                prim = {s for s in gsp[gid] if s}
                if prim:
                    c["bloq_n"] += 1
                    na_unidade = {s for s in prim if s in por_unidade.get(pu, set())}
                    if dec and not na_unidade:
                        dup = sorted(s for s in prim if len(por_slug.get(s, set())) > 1)
                        fora = sorted(s for s in prim if not por_slug.get(s))
                        reg = {"curso": sig, "gold_id": gid, "entry_id": eid,
                               "unidade_vigente": pu, "gold_primario": sorted(prim),
                               "unidades_do_gold": sorted({u for s in prim for u in por_slug.get(s, set())}),
                               "slug_duplicado": dup, "slug_fora_da_taxonomia": fora,
                               "sub_predita": ps}
                        bloqueios.append(reg)
                        if dup:
                            bloq_amb.append(reg)
        por_curso[sig] = dict(c)
        tot.update(c)
        print(sig, dict(c), flush=True)

    # ---------------------------------------------------------------- reconciliacao com W-P1 e W-S
    wp1 = read(HERE / "wp1_inventario_matriz_22-09.json")
    ws = read(HERE / "ws_declaracao_por_material_22-09.json")
    set_wp1 = {(m["curso"], m["entry_id"]) for m in wp1["materiais"] if "bloqueio_unidade" in (m.get("classes") or [])}
    set_ws = {(d["curso"], d["gold_id"]) for d in ws["teto_analitico"]["detalhe"] if d.get("causa") == "bloqueio_pela_unidade"}
    set_wt = {(b["curso"], b["gold_id"]) for b in bloqueios}
    reconc = {
        "wt_total": len(set_wt), "wp1_total": len(set_wp1), "ws_total": len(set_ws),
        "wt_e_wp1_e_ws": sorted(set_wt & set_wp1 & set_ws),
        "so_no_wt": sorted(set_wt - set_wp1 - set_ws),
        "wt_e_ws_sem_wp1": sorted((set_wt & set_ws) - set_wp1),
        "wt_e_wp1_sem_ws": sorted((set_wt & set_wp1) - set_ws),
        "no_wp1_fora_do_wt": sorted(set_wp1 - set_wt),
        "no_ws_fora_do_wt": sorted(set_ws - set_wt),
        "dependem_de_slug_duplicado": sorted({(b["curso"], b["gold_id"]) for b in bloq_amb}),
    }

    checks = {
        "bloco_217_de_237": (tot["bloco"], tot["bloco_n"]) == (217, 237),
        "unidade_246_de_284": (tot["unidade"], tot["unidade_n"]) == (246, 284),
        "sub_primaria_84_aceita_107_de_251": (tot["sub_primaria"], tot["sub_aceita"], tot["sub_n"]) == (84, 107, 251),
        "erros_de_unidade_sao_38": len(erros) == 38,
    }
    report = {
        "escopo": __doc__,
        "sha256_congelamento_decisoes": sha_congelamento,
        "checks": checks,
        "totais": dict(tot),
        "cursos": por_curso,
        "classes": dict(collections.Counter(e["classe"] for e in erros)),
        "classes_por_curso": {sig: dict(collections.Counter(e["classe"] for e in erros if e["curso"] == sig))
                              for sig in mede.NOMES},
        "recuperaveis_sem_tocar_bloco": sorted((e["curso"], e["gold_id"]) for e in erros if e["bruto_acertaria"]),
        "regua_ambigua_flag": sorted((e["curso"], e["gold_id"]) for e in erros if e["regua_ambigua"]),
        "erros": erros,
        "bloqueios_subunidade": bloqueios,
        "bloqueios_por_curso": dict(collections.Counter(b["curso"] for b in bloqueios)),
        "reconciliacao": reconc,
        "limitacoes": [
            "scorer_bruto = saida de auto_map_entry_unit (pre-reconciliacao, pos-scorer); o ranking completo pre-gate nao e persistido.",
            "Ausentes permanecem no denominador. Gold carregado depois do congelamento por hash.",
        ],
    }
    out = HERE / "wt_anatomia_unidade_49_22-09.json"
    assert not out.exists(), "preservar evidencia existente"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CHECKS", checks)
    print("CLASSES", report["classes"])
    print("BLOQUEIOS", len(bloqueios), report["bloqueios_por_curso"])
    print("RECONC", {k: (len(v) if isinstance(v, list) else v) for k, v in reconc.items()})
    print("SHA256_JSON", hashlib.sha256(out.read_bytes()).hexdigest())
    assert checks["bloco_217_de_237"] and checks["unidade_246_de_284"], "estado #49 NAO reproduzido"


if __name__ == "__main__":
    main()
