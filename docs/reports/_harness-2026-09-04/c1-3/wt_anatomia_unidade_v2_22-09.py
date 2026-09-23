"""W-T v2 (22/09): anatomia dos erros de unidade na NOVA base — régua v2 final adotada (wx_adota_v2) + os 13 ausentes
presentes (cópias do W-V em .frzero/wv_importacao_22-09 para MF, IA e CG; demais cursos nos builds-base).

Mesma cadeia real e mesmas classes do wt_anatomia_unidade_49_22-09.py (bloco -> unidade via replay_bloco_21-09 ->
replay_unidade_21-09; decisões congeladas por sha256 ANTES de carregar qualquer gold). Diferenças:
  - raízes: MF/IA/CG lidas de .frzero/wv_importacao_22-09/<curso> (13 materiais injetados pelo W-V);
  - ponte por id preservado quando herancas_*_15-09.json tem new_id nulo (os 13 ausentes), como fez o W-V;
  - golds pela régua v2 FINAL (c1-3/wx_gold_v2_final_22-09/ + histórico para o resto), via wx_regua_corrigida.golds_de;
    registra também o placar sob a régua vigente em docs/reports (deve coincidir depois do --apply).
Sem build, rede, LLM; sem tocar src/, tests/ nem os builds. Decisão do usuário 22/09: "espera o W-Y e reexecuta a anatomia".
"""
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

T0 = time.time()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
REP = DATA / "docs/reports"
FINAL = HERE / "wx_gold_v2_final_22-09"
WV = DATA / ".frzero/wv_importacao_22-09"
OUT_JSON = HERE / "wt_anatomia_unidade_v2_22-09.json"
OUT_MD = HERE / "wt_anatomia_unidade_v2_22-09.md"
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
    por_unidade, por_slug = collections.defaultdict(set), collections.defaultdict(set)
    for unit in read(root / "course/.content_taxonomy.json").get("units", []) or []:
        u = str(unit.get("slug") or "")
        for t in unit.get("topics", []) or []:
            s = str(t.get("slug") or "")
            if s:
                por_unidade[u].add(s)
                por_slug[s].add(u)
    return por_unidade, por_slug


def base_root(sig, nomes):
    return DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"} else ".frzero/pacote_fontes_15-09") / nomes[sig]


def root_de(sig, nomes):
    alt = WV / nomes[sig]
    return alt if (alt / "manifest.json").exists() else base_root(sig, nomes)


def avalia(sig, estado, congelado, compare, golds, herancas_rows, ref, mapping):
    """Mesma avaliação do W-T, com ponte por id preservado para os ausentes do herancas."""
    saved, novo, root = estado["saved"], estado["novo"], estado["root"]
    index = compare.indexed(list(saved.values()))
    gb, gu, gs, gsp = golds
    por_unidade, por_slug = taxonomia_por_unidade(root)
    c, erros, bloqueios = collections.Counter(), [], []
    for row in herancas_rows:
        gid = row["entry_id"]
        old = ref.get(mapping.get(gid) or "")
        hits = index.get(compare.source(old), []) if old else []
        eid = str(hits[0]["id"]) if hits else None
        ponte = False
        if eid is None and gid in novo:          # ausente no herancas, presente na nova base: id preservado (W-V)
            eid, ponte = gid, True
        dec = congelado.get(eid) if eid else None
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
                    "curso": sig, "gold_id": gid, "entry_id": eid, "ponte_por_id": ponte, "classe": classe,
                    "bloco_pred": pb, "bloco_gold": gb.get(gid, ""), "bloco_ok": bloco_ok,
                    "unidade_pred": pu, "unidade_gold": sorted(gu[gid]), "regua_ambigua": len(gu[gid]) > 1,
                    "reasons": reasons, "conflict": (dec or {}).get("conflict") or {},
                    "scorer_bruto": bruto.get("slug"), "scorer_conf": bruto.get("confidence"),
                    "scorer_ambiguo": bruto.get("ambiguous"),
                    "bruto_acertaria": bool(bruto.get("slug") and bruto.get("slug") in gu[gid]),
                    "titulo": (saved.get(eid) or novo.get(eid) or {}).get("title") if eid else None,
                })
                c[f"cls_{classe}"] += 1
        if row["sub_primario"] != "":
            c["sub_n"] += 1
            c["sub_primaria"] += bool(dec and ps in gsp[gid])
            c["sub_aceita"] += bool(dec and ps in gs[gid])
            prim = {s for s in gsp[gid] if s}
            if prim:
                c["bloq_n"] += 1
                if dec and not {s for s in prim if s in por_unidade.get(pu, set())}:
                    bloqueios.append({"curso": sig, "gold_id": gid, "entry_id": eid, "unidade_vigente": pu,
                                      "gold_primario": sorted(prim),
                                      "unidades_do_gold": sorted({u for s in prim for u in por_slug.get(s, set())}),
                                      "sub_predita": ps})
    return c, erros, bloqueios


def main():
    compare = load("wtv2_cmp", HERE / "compara_herancas_15-09.py")
    mede = compare.mede
    wx = load("wtv2_wx", HERE / "wx_regua_corrigida_22-09.py")
    rb = load("wtv2_rb", HERE / "replay_bloco_21-09.py")
    ru = load("wtv2_ru", HERE / "replay_unidade_21-09.py")
    orig_read = ru.read
    nomes, uni = mede.NOMES, mede.UNI
    raizes = {sig: root_de(sig, nomes) for sig in nomes}
    for sig in ("MF", "IA", "CG"):
        assert raizes[sig].parent == WV, f"{sig}: cópia do W-V ausente em {WV}"

    # fase real, sem gold
    estado = {}
    for sig in nomes:
        root = raizes[sig]
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
        print("cadeia", sig, len(novo), root.parent.name, flush=True)
    congelado = {sig: {eid: {"bloco": compare.predictions(v["root"], e)[0],
                             "unidade": str(e.get("computed_unit_slug") or ""),
                             "sub": str(e.get("computed_subunit_slug") or ""),
                             "reasons": [str(r) for r in e.get("unit_match_reasons") or []],
                             "conflict": e.get("unit_block_conflict") or {},
                             "raw": v["raw"].get(eid)}
                       for eid, e in v["novo"].items()}
                 for sig, v in estado.items()}
    sha_cong = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    print("CONGELAMENTO", sha_cong, flush=True)

    # avaliação: gold entra aqui (v2 final; e vigente em docs/reports para conferência)
    resultado = {}
    for rotulo, base in (("v2_final", FINAL), ("vigente_docs_reports", REP)):
        tot, por_curso, erros, bloqueios = collections.Counter(), {}, [], []
        for sig in nomes:
            ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / nomes[sig] / "manifest.json")["entries"]}
            mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
            with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
                rows = list(csv.DictReader(stream))
            c, err, bloq = avalia(sig, estado[sig], congelado[sig], compare, wx.golds_de(sig, base, uni), rows, ref, mapping)
            por_curso[sig] = dict(c)
            tot.update(c)
            erros += err
            bloqueios += bloq
        resultado[rotulo] = {"totais": dict(tot), "cursos": por_curso, "erros": erros, "bloqueios": bloqueios,
                             "classes": dict(collections.Counter(e["classe"] for e in erros)),
                             "classes_por_curso": {sig: dict(collections.Counter(e["classe"] for e in erros if e["curso"] == sig)) for sig in nomes},
                             "recuperaveis_sem_tocar_bloco": sorted((e["curso"], e["gold_id"]) for e in erros if e["bruto_acertaria"]),
                             "bloqueios_por_curso": dict(collections.Counter(b["curso"] for b in bloqueios))}
        print(rotulo, dict(tot), flush=True)
        print("  classes", resultado[rotulo]["classes"], flush=True)
    r2 = resultado["v2_final"]
    report = {"escopo": __doc__, "raizes": {sig: str(p.relative_to(DATA)) for sig, p in raizes.items()},
              "sha256_congelamento_decisoes": sha_cong, "resultado": resultado,
              "regua_vigente_igual_v2_final": resultado["vigente_docs_reports"]["totais"] == r2["totais"],
              "segundos": round(time.time() - T0, 1)}
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    t = r2["totais"]
    L = ["# W-T v2 — anatomia da unidade na nova base (régua v2 final + 13 presentes), 22/09", "",
         f"Raízes: MF/IA/CG em `.frzero/wv_importacao_22-09/`, demais em builds-base. Congelamento `{sha_cong[:16]}…`.", "",
         "| eixo | acertos | n |", "|---|---|---|",
         f"| bloco | {t.get('bloco')} | {t.get('bloco_n')} |", f"| unidade | {t.get('unidade')} | {t.get('unidade_n')} |",
         f"| sub primária | {t.get('sub_primaria')} | {t.get('sub_n')} |", f"| sub aceita | {t.get('sub_aceita')} | {t.get('sub_n')} |", "",
         f"Régua vigente em docs/reports dá o mesmo placar: {'sim' if report['regua_vigente_igual_v2_final'] else 'NÃO (aplicar --apply do wx_adota_v2)'}", "",
         "## Erros de unidade por classe", "", "| classe | total | " + " | ".join(nomes) + " |", "|---|---|" + "---|" * len(nomes)]
    for cls, n in sorted(r2["classes"].items(), key=lambda kv: -kv[1]):
        L.append(f"| {cls} | {n} | " + " | ".join(str(r2["classes_por_curso"][s].get(cls, 0)) for s in nomes) + " |")
    L += ["", "## Erros (id, classe, gold → previsto, bloco ok, razões)", ""]
    for e in sorted(r2["erros"], key=lambda e: (e["curso"], e["classe"], e["gold_id"])):
        L.append(f"- {e['curso']} `{e['gold_id']}` [{e['classe']}{', ponte' if e['ponte_por_id'] else ''}]: {'|'.join(e['unidade_gold'])} → {e['unidade_pred'] or '∅'}; bloco {'ok' if e['bloco_ok'] else 'ERRADO'} ({e['bloco_pred'] or '∅'} vs {e['bloco_gold']}); bruto={e['scorer_bruto']} conf={e['scorer_conf']}; {', '.join(e['reasons'])[:120]}")
    L += ["", f"Recuperáveis sem tocar o bloco (scorer bruto acertaria): {len(r2['recuperaveis_sem_tocar_bloco'])} — {r2['recuperaveis_sem_tocar_bloco']}",
          f"Bloqueios de subunidade: {len(r2['bloqueios'])} {r2['bloqueios_por_curso']}", f"Tempo: {report['segundos']} s"]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("OK", OUT_JSON.name, hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()[:16], report["segundos"], "s", flush=True)


if __name__ == "__main__":
    main()
