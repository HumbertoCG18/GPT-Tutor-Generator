"""W-O V4: UMA variante nova = V3 (bloco) + regra de UNIDADE, patch SO EM MEMORIA.

V4 `vizinho-nao-vence-texto`:
  - V3 (bloco, ja medido em regra_tde_prazo_assessment_bloco_21-09.py):
      (a) `motor_apply.tier2_due_scope` True tambem quando `source_section`
          comeca com `_TDE_PREFIX`; (C) `due_window._NON_CONTENT_KINDS` sem
          "assessment".
  - NOVO (unidade): quando o bloco temporal NAO tem unidade propria (`vizinho`
    nao vazio) e o texto gated (`computed_unit_slug` != "" no reconcile, ja
    pos-gate e nao ambiguo por construcao em resolver_apply.py:475) discorda da
    unidade herdada do vizinho, o TEXTO vence: unidade = gated, razao
    `texto-vence-vizinho=<vizinho>`, conflito {unit, block_unit, block_id}.

Como o patch de unidade foi feito (sem tocar src/):
  `resolver_apply.apply_unit_subunit_fields` importa `reconcile_unit_with_block`
  e `unit_of_block_or_neighbor` LOCALMENTE de `src.builder.routing.file_map`
  (:394-396), a cada chamada da fase -> substituir os ATRIBUTOS DE MODULO de
  `file_map` intercepta as duas. `reconcile_unit_with_block` nao recebe
  `vizinho`, entao um wrapper em torno de `unit_of_block_or_neighbor` guarda
  (block_unit, vizinho) da entry corrente numa celula; o wrapper de
  `reconcile_unit_with_block` le essa celula. O loop e sequencial e chama
  vizinho (:501) imediatamente antes do reconcile (:513), sem desvio entre os
  dois, logo a celula esta sempre fresca (mesmo padrao de captura por entry de
  `regra_secao_efeito_subunidade_21-09.py`).
  Precedencia preservada sem reimplementar nada: o wrapper delega ao ORIGINAL e
  so troca o resultado quando o original devolveu EXATAMENTE
  `["reconciliada_do_bloco=<id>"]` — isto e, depois de bloco manual, unidade
  manual, `secao-vence-bloco` (#47), `explicita-vence-bloco` e
  `herdada_do_bloco` terem sido descartados pelo proprio src. Com reconciled !=
  block_unit, o sufixo `herdada_do_vizinho` de resolver_apply.py:524-525 deixa
  de ser acrescentado pelo proprio src. Sem parametro ajustavel.

Reusa replay_bloco_21-09.replay (fase real de bloco, TEMPORAL_KEYS removidas,
voter=None) e replay_unidade_21-09.replay (fase real de unidade/subunidade),
alimentada com as entries JA decididas pela variante de bloco. Decisoes
congeladas por sha256 ANTES de carregar o gold. Sem build, rede, LLM, escrita
em src/, commit ou git add.
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

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[3]
sys.path.insert(0, str(DATA))

from src.builder.routing import file_map as FM
from src.builder.routing.motor import apply as motor_apply
from src.builder.routing.motor import due_window as DW
from src.builder.routing.motor.due_window import _TDE_PREFIX

CAMPOS = ("temporal_block_id", "temporal_block_method", "temporal_block_band",
          "temporal_block_flag", "temporal_block_provider")
V3 = "V3-tde-prazo+assessment-hospeda"
V4 = "V4-V3+vizinho-nao-vence-texto"
VARIANTES = ("base", V3, V4)
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_tde(entry):
    return str(entry.get("source_section") or "").strip().startswith(_TDE_PREFIX)


class PatchBloco:
    """V3: parte (a) + (C). Identico ao medido em W-N."""

    def __enter__(self):
        self.orig_scope = motor_apply.tier2_due_scope
        self.orig_kinds = DW._NON_CONTENT_KINDS
        assert "assessment" in self.orig_kinds, "C pressupoe assessment excluido hoje"
        orig = self.orig_scope
        motor_apply.tier2_due_scope = lambda e: True if is_tde(e) else orig(e)
        DW._NON_CONTENT_KINDS = frozenset(self.orig_kinds - {"assessment"})
        return self

    def __exit__(self, *exc):
        motor_apply.tier2_due_scope = self.orig_scope
        DW._NON_CONTENT_KINDS = self.orig_kinds


class PatchUnidade:
    """V4: regra de unidade, so onde hoje sai reconciliada_do_bloco + herdada_do_vizinho."""

    def __init__(self):
        self.celula = {"vizinho": "", "block_unit": ""}
        self.toques = []

    def __enter__(self):
        self.orig_neigh = FM.unit_of_block_or_neighbor
        self.orig_rec = FM.reconcile_unit_with_block
        assert getattr(self.orig_neigh, "__module__", "") == FM.__name__, "patch sobre original"
        celula, toques = self.celula, self.toques
        orig_n, orig_r = self.orig_neigh, self.orig_rec

        def neigh(block_id, blocks):
            bu, vz = orig_n(block_id, blocks)
            celula["block_unit"], celula["vizinho"] = bu, vz
            return bu, vz

        def rec(**kw):
            reconciled, suffix, conflict = orig_r(**kw)
            vz = celula["vizinho"]
            gated = str(kw["computed_unit_slug"] or "")
            bu = str(kw["block_unit_slug"] or "")
            bid = str(kw["computed_block_id"] or "")
            alvo = list(suffix) == [f"reconciliada_do_bloco={bid}"]
            if (vz and gated and bu and reconciled == bu and alvo
                    and not kw["block_is_manual"] and not kw["has_manual_unit"]):
                toques.append({"vizinho": vz, "block_unit": bu, "block_id": bid,
                               "gated": gated, "conf": kw["unit_confidence"]})
                return (gated, [f"texto-vence-vizinho={vz}"],
                        {"unit": gated, "block_unit": bu, "block_id": bid})
            return reconciled, suffix, conflict

        FM.unit_of_block_or_neighbor = neigh
        FM.reconcile_unit_with_block = rec
        return self

    def __exit__(self, *exc):
        FM.unit_of_block_or_neighbor = self.orig_neigh
        FM.reconcile_unit_with_block = self.orig_rec


def snap(entries):
    return {eid: {c: e.get(c) for c in CAMPOS} for eid, e in entries.items()}


def main():
    out = HERE / "regra_v4_vizinho_nao_vence_texto_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    rb = load("rb_wo", HERE / "replay_bloco_21-09.py")
    ru = load("ru_wo", HERE / "replay_unidade_21-09.py")
    compare = load("cmp_wo", HERE / "compara_herancas_15-09.py")
    mede = compare.mede   # NOMES so; golds() e chamado depois do congelamento

    # ---------- fase de BLOCO: base e V3 (V4 herda o bloco de V3) ----------
    estado = {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
                       else ".frzero/pacote_fontes_15-09") / name
        saved, base, dec_base, _ = rb.replay(root)
        fiel = sum(all(saved[i].get(c) == base[i].get(c) for c in CAMPOS) for i in saved)
        assert fiel == len(saved), (sig, "replay de bloco infiel; nao medir variante")
        with PatchBloco():
            _, novo, dec_novo, _ = rb.replay(root)
        blocos = {}
        for b in read(root / "course/.timeline_index.json").get("blocks", []):
            for k in (b.get("id"), b.get("block_uuid")):
                if k:
                    blocos[str(k)] = b
        estado[sig] = {"root": root, "saved": saved, "blocos": blocos,
                       "var": {"base": base, V3: novo, V4: novo},
                       "dec": {"base": dec_base, V3: dec_novo, V4: dec_novo},
                       "bloco_mudou": any(novo[i].get("temporal_block_id") != base[i].get("temporal_block_id")
                                          for i in base)}
        log(sig, "bloco ok | bloco mudou:", estado[sig]["bloco_mudou"])

    # ---------- fase de UNIDADE/SUBUNIDADE encadeada ----------
    unid, unid_raw, toques = {}, {}, {}
    orig_read = ru.read
    for sig, st in estado.items():
        # base sem patch; V3 sem patch de unidade (reusa base se o bloco nao mudou);
        # V4 sempre re-rodado, porque a regra nova pode agir sem o bloco mudar.
        planos = [("base", st["var"]["base"], None), (V4, st["var"][V4], PatchUnidade)]
        if st["bloco_mudou"]:
            planos.insert(1, (V3, st["var"][V3], None))
        for nome, entries, patch in planos:
            feed = [copy.deepcopy(entries[i]) for i in entries]

            def patched(path, _feed=feed, _orig=orig_read):
                data = _orig(path)
                if Path(path).name == "manifest.json":
                    data = {**data, "entries": _feed}
                return data

            ru.read = patched
            try:
                if patch is None:
                    _, pos, raw = ru.replay(st["root"])
                else:
                    with patch() as p:
                        _, pos, raw = ru.replay(st["root"])
                        toques[sig] = list(p.toques)
            finally:
                ru.read = orig_read
            unid[(sig, nome)] = pos
            unid_raw[(sig, nome)] = raw
            log(sig, nome, "unidade ok | toques:", len(toques.get(sig, [])) if patch else "-")
        if not st["bloco_mudou"]:
            unid[(sig, V3)] = unid[(sig, "base")]
            unid_raw[(sig, V3)] = unid_raw[(sig, "base")]

    # ---------- congelamento: hash das decisoes ANTES de qualquer gold ----------
    congelado = {sig: {nome: snap(st["var"][nome]) for nome in VARIANTES}
                 for sig, st in estado.items()}
    for (sig, nome), pos in unid.items():
        congelado[sig].setdefault("unidade", {})[nome] = {
            i: [pos[i].get("computed_unit_slug"), pos[i].get("computed_subunit_slug")] for i in pos}
    freeze = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True)
                            .encode("utf-8")).hexdigest()
    log("FREEZE", freeze)

    # ---------- avaliacao (gold a partir daqui) ----------
    tot = {v: collections.Counter() for v in VARIANTES}
    cursos = {v: {} for v in VARIANTES}
    lateral_tot = {v: collections.Counter() for v in VARIANTES}
    lateral_ids, lateral_t1 = [], []
    mudancas = []
    for sig, st in estado.items():
        root = st["root"]
        ref = {str(e["id"]): e for e in read(DATA / ".frzero/pacote_fontes_15-09" / mede.NOMES[sig]
                                             / "manifest.json")["entries"]}
        index = compare.indexed(list(st["saved"].values()))
        mapping = {e["entry_id"]: e["new_id"] for e in read(HERE / f"herancas_{sig}_15-09.json")["entries"]}
        gb, gu, gs, gsp = mede.golds(sig)
        with (HERE / f"herancas_{sig}_15-09.csv").open(encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        gold_por_id = {}
        c = {v: collections.Counter() for v in VARIANTES}
        acertos = {v: {} for v in VARIANTES}
        for row in rows:
            gid = row["entry_id"]
            old = ref.get(mapping.get(gid) or "")
            hits = index.get(compare.source(old), []) if old else []
            assert len(hits) <= 1, (sig, gid, "origem nao unica")
            eid = str(hits[0]["id"]) if hits else None
            lat_eid = eid or (gid if gid in st["saved"] else None)
            if lat_eid:
                gold_por_id[lat_eid] = {"bloco": gb.get(gid), "unidade": sorted(gu.get(gid, [])),
                                        "sub_primario": sorted(gsp.get(gid, [])),
                                        "sub_aceito": sorted(gs.get(gid, [])), "gold_id": gid,
                                        "na_regua": eid is not None}
                if eid is None:
                    lateral_ids.append({"curso": sig, "gold_id": gid, "id": lat_eid})
            for v in VARIANTES:
                pos = unid[(sig, v)]
                for escopo, key, cnt in (("regua", eid, c[v]), ("lateral", lat_eid, lateral_tot[v])):
                    ent = st["var"][v].get(key) if key else None
                    uent = pos.get(key) if key else None
                    pb = compare.predictions(root, ent)[0] if ent else None
                    pu = str(uent.get("computed_unit_slug") or "") if uent else None
                    ps = str(uent.get("computed_subunit_slug") or "") if uent else None
                    if row["bloco"] != "":
                        cnt["bloco_n"] += 1
                        if ent is None:
                            cnt["bloco_ausente"] += 1
                        ok = bool(ent) and pb == gb[gid]
                        cnt["bloco"] += ok
                        if escopo == "regua":
                            acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["bloco"] = ok
                    if row["unidade"] != "":
                        cnt["unidade_n"] += 1
                        ok = bool(uent) and pu in gu[gid]
                        cnt["unidade"] += ok
                        if escopo == "regua":
                            acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["unidade"] = ok
                    if row["sub_primario"] != "":
                        cnt["sub_n"] += 1
                        okp = bool(uent) and ps in gsp[gid]
                        oka = bool(uent) and ps in gs[gid]
                        cnt["sub_primaria"] += okp
                        cnt["sub_aceita"] += oka
                        if escopo == "regua":
                            acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["sub_primaria"] = okp
                            acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["sub_aceita"] = oka
                    if escopo == "lateral" and lat_eid == "t1-2026-1":
                        lateral_t1.append({"curso": sig, "variante": v, "gold_id": gid,
                                           "bloco_pred": pb, "unidade_pred": pu, "sub_pred": ps,
                                           "gold": gold_por_id.get(lat_eid)})
        for v in VARIANTES:
            cursos[v][sig] = dict(c[v])
            tot[v].update(c[v])

        # ids tocados: bloco (V3/V4 vs base) e/ou unidade/sub (V4 vs V3, V4 vs base)
        be, bu_, b_raw = st["var"]["base"], unid[(sig, "base")], unid_raw[(sig, "base")]
        v3e, v3u, v3_raw = st["var"][V3], unid[(sig, V3)], unid_raw[(sig, V3)]
        v4e, v4u, v4_raw = st["var"][V4], unid[(sig, V4)], unid_raw[(sig, V4)]

        def uslug(d, i):
            return str(d[i].get("computed_unit_slug") or "")

        def sslug(d, i):
            return str(d[i].get("computed_subunit_slug") or "")

        for eid in be:
            dbloco = be[eid].get("temporal_block_id") != v4e[eid].get("temporal_block_id")
            du43 = uslug(v3u, eid) != uslug(v4u, eid)
            ds43 = sslug(v3u, eid) != sslug(v4u, eid)
            du40 = uslug(bu_, eid) != uslug(v4u, eid)
            ds40 = sslug(bu_, eid) != sslug(v4u, eid)
            if not (dbloco or du43 or ds43 or du40 or ds40):
                continue
            bd = v4e[eid].get("temporal_block_id")
            mudancas.append({
                "curso": sig, "id": eid, "tde": is_tde(st["saved"][eid]),
                "category": st["saved"][eid].get("category"),
                "source_section": st["saved"][eid].get("source_section"),
                "source_path": st["saved"][eid].get("source_path"),
                "muda_bloco_vs_base": dbloco,
                "muda_unidade_vs_V3": du43, "muda_sub_vs_V3": ds43,
                "muda_unidade_vs_base": du40, "muda_sub_vs_base": ds40,
                "bloco_base": compare.predictions(root, be[eid])[0],
                "bloco_V4": compare.predictions(root, v4e[eid])[0],
                "kind_bloco_V4": (st["blocos"].get(str(bd)) or {}).get("kind"),
                "unit_slug_bloco_V4": (st["blocos"].get(str(bd)) or {}).get("unit_slug"),
                "metodo_V4": v4e[eid].get("temporal_block_method"),
                "unidade_base": uslug(bu_, eid), "unidade_V3": uslug(v3u, eid), "unidade_V4": uslug(v4u, eid),
                "razoes_base": bu_[eid].get("unit_match_reasons"),
                "razoes_V3": v3u[eid].get("unit_match_reasons"),
                "razoes_V4": v4u[eid].get("unit_match_reasons"),
                "conf_V4": v4u[eid].get("unit_match_confidence"),
                "conflito_V4": v4u[eid].get("unit_block_conflict"),
                "scorer_bruto_base": b_raw.get(eid), "scorer_bruto_V3": v3_raw.get(eid),
                "scorer_bruto_V4": v4_raw.get(eid),
                "sub_base": sslug(bu_, eid), "sub_V3": sslug(v3u, eid), "sub_V4": sslug(v4u, eid),
                "gold": gold_por_id.get(eid),
                "na_regua": bool(gold_por_id.get(eid, {}).get("na_regua")),
                "delta_vs_base": {k: [acertos["base"].get(eid, {}).get(k), acertos[V4].get(eid, {}).get(k)]
                                  for k in ("bloco", "unidade", "sub_primaria", "sub_aceita")
                                  if acertos["base"].get(eid, {}).get(k) != acertos[V4].get(eid, {}).get(k)},
                "delta_vs_V3": {k: [acertos[V3].get(eid, {}).get(k), acertos[V4].get(eid, {}).get(k)]
                                for k in ("bloco", "unidade", "sub_primaria", "sub_aceita")
                                if acertos[V3].get(eid, {}).get(k) != acertos[V4].get(eid, {}).get(k)},
            })
        log(sig, {v: dict(c[v]) for v in VARIANTES})

    EIXOS = ("bloco", "unidade", "sub_primaria", "sub_aceita")
    perdas = {ref: {k: [f'{m["curso"]}:{m["id"]}' for m in mudancas if m[campo].get(k) == [True, False]]
                    for k in EIXOS}
              for ref, campo in (("vs_base", "delta_vs_base"), ("vs_V3", "delta_vs_V3"))}
    ganhos = {ref: {k: [f'{m["curso"]}:{m["id"]}' for m in mudancas if m[campo].get(k) == [False, True]]
                    for k in EIXOS}
              for ref, campo in (("vs_base", "delta_vs_base"), ("vs_V3", "delta_vs_V3"))}

    def fmt(v):
        return {"bloco": f'{tot[v]["bloco"]}/{tot[v]["bloco_n"]}',
                "unidade": f'{tot[v]["unidade"]}/{tot[v]["unidade_n"]}',
                "sub_primaria": f'{tot[v]["sub_primaria"]}/{tot[v]["sub_n"]}',
                "sub_aceita": f'{tot[v]["sub_aceita"]}/{tot[v]["sub_n"]}',
                "bloco_ausente": tot[v]["bloco_ausente"]}

    checks = {
        "base_reproduz_213_244_84_107": (tot["base"]["bloco"], tot["base"]["unidade"],
                                         tot["base"]["sub_primaria"], tot["base"]["sub_aceita"]) ==
                                        (213, 244, 84, 107),
        "V3_reproduz_214_243_84_107": (tot[V3]["bloco"], tot[V3]["unidade"],
                                       tot[V3]["sub_primaria"], tot[V3]["sub_aceita"]) == (214, 243, 84, 107),
        "bloco_maior_igual_214": tot[V4]["bloco"] >= 214,
        "zero_perda_de_bloco": not perdas["vs_base"]["bloco"],
        "unidade_maior_igual_244": tot[V4]["unidade"] >= 244,
        "zero_perda_de_unidade": not perdas["vs_base"]["unidade"],
        "sub_primaria_maior_igual_84": tot[V4]["sub_primaria"] >= 84,
        "sub_aceita_maior_igual_107": tot[V4]["sub_aceita"] >= 107,
        "zero_perda_de_sub": not perdas["vs_base"]["sub_primaria"] and not perdas["vs_base"]["sub_aceita"],
        "nenhum_curso_regride": all(
            cursos[V4][s].get(k, 0) >= cursos["base"][s].get(k, 0)
            for s in cursos[V4] for k in EIXOS),
        "denominadores": (tot[V4]["bloco_n"], tot[V4]["unidade_n"], tot[V4]["sub_n"]) == (237, 284, 251),
        "V4": fmt(V4),
    }
    checks["ACEITE"] = all(v is True for k, v in checks.items() if isinstance(v, bool))

    report = {
        "head": "9220a57", "variante": V4, "referencias": ["base", V3],
        "freeze_sha256_decisoes": freeze,
        "patch": {
            "bloco_V3": "motor_apply.tier2_due_scope -> True p/ source_section com _TDE_PREFIX; due_window._NON_CONTENT_KINDS := original - {'assessment'}.",
            "unidade_V4": "file_map.unit_of_block_or_neighbor embrulhada p/ capturar (block_unit, vizinho) da entry corrente numa celula; file_map.reconcile_unit_with_block embrulhada, delega ao original e SO troca quando o sufixo devolvido e exatamente ['reconciliada_do_bloco=<id>'] E vizinho!='' E gated!='' E reconciled==block_unit E nao manual -> devolve (gated, ['texto-vence-vizinho=<vizinho>'], conflito). Como resolver_apply importa as duas LOCALMENTE (:394-396) a cada chamada, o patch em atributo de modulo pega. Com reconciled != block_unit, o proprio src deixa de acrescentar herdada_do_vizinho (:524-525).",
            "restauracao": "todos os atributos de modulo restaurados no __exit__ de cada patch.",
        },
        "checks": checks,
        "placar": {v: fmt(v) for v in VARIANTES},
        "perdas": perdas, "ganhos": ganhos,
        "totais": {v: dict(tot[v]) for v in tot}, "cursos": cursos,
        "toques_da_regra_por_curso": toques,
        "mudancas": mudancas,
        "placar_lateral_por_identidade": {"totais": {v: dict(lateral_tot[v]) for v in lateral_tot},
                                          "ids_casados_por_identidade": lateral_ids,
                                          "t1_2026_1": lateral_t1},
        "scope": "apply_anchor_engine e apply_unit_subunit_fields reais; patch so em atributos de modulo, restaurado; voter=None; gold carregado depois do congelamento.",
        "limitations": [
            "Ausentes permanecem no denominador da regua oficial; placar lateral e informativo.",
            "Sem build/rebuild, rede ou LLM; sidecar de votos nao usado.",
            "V3 reusa a unidade da base nos cursos em que o bloco nao mudou (decisao identica por construcao); V4 foi re-rodado nos 7 cursos.",
        ],
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PLACAR", json.dumps({v: fmt(v) for v in VARIANTES}, ensure_ascii=False))
    print("CHECKS", json.dumps(checks, ensure_ascii=False))
    print("PERDAS", json.dumps(perdas, ensure_ascii=False))
    print("GANHOS", json.dumps(ganhos, ensure_ascii=False))
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
