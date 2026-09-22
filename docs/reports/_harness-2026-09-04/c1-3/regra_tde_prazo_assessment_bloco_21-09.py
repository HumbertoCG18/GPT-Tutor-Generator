"""W-N V3: UMA variante de regra de BLOCO = V1 + candidata C, patch SO EM MEMORIA.

V3 `tde-prazo+assessment-hospeda`:
  (a) V1 - tier2_due_scope(entry) tambem True quando source_section comeca com
      _TDE_PREFIX (qualquer categoria);
  (b) C  - bloco de kind `assessment` que CONTEM o vencimento pode ancorar. Efeito
      implementado substituindo o atributo de modulo
      `due_window._NON_CONTENT_KINDS` por um frozenset SEM "assessment"
      (review e NON_ACADEMIC_KINDS continuam excluidos). `resolve_due_window`
      le esse global no loop (`:111`), portanto due-contain/due-straddle, band
      (structured->alta, senao media) e flag ficam exatamente as regras reais,
      sem copiar logica.

Reusa replay_bloco_21-09.replay (fase real de bloco, TEMPORAL_KEYS removidas,
voter=None) e replay_unidade_21-09.replay (fase real de unidade/subunidade,
alimentada com as entries JA decididas pela variante). Decisoes congeladas por
sha256 ANTES de carregar o gold. Sem build, rede, LLM ou escrita em src/.
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

from src.builder.routing.motor import apply as motor_apply
from src.builder.routing.motor import due_window as DW
from src.builder.routing.motor.due_window import _TDE_PREFIX

CAMPOS = ("temporal_block_id", "temporal_block_method", "temporal_block_band",
          "temporal_block_flag", "temporal_block_provider")
VAR = "V3-tde-prazo+assessment-hospeda"
VARIANTES = ("base", VAR)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_tde(entry):
    return str(entry.get("source_section") or "").strip().startswith(_TDE_PREFIX)


class V3:
    nome = VAR

    def __enter__(self):
        self.orig_scope = motor_apply.tier2_due_scope
        self.orig_kinds = DW._NON_CONTENT_KINDS
        assert "assessment" in self.orig_kinds, "C pressupoe assessment excluido hoje"
        orig = self.orig_scope
        motor_apply.tier2_due_scope = lambda e: True if is_tde(e) else orig(e)
        DW._NON_CONTENT_KINDS = frozenset(self.orig_kinds - {"assessment"})

    def __exit__(self, *exc):
        motor_apply.tier2_due_scope = self.orig_scope
        DW._NON_CONTENT_KINDS = self.orig_kinds


def snap(entries):
    return {eid: {c: e.get(c) for c in CAMPOS} for eid, e in entries.items()}


def main():
    out = HERE / "regra_tde_prazo_assessment_bloco_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    rb = load("rb_wn", HERE / "replay_bloco_21-09.py")
    ru = load("ru_wn", HERE / "replay_unidade_21-09.py")
    compare = load("cmp_wn", HERE / "compara_herancas_15-09.py")
    mede = compare.mede   # NOMES so; golds() e chamado depois do congelamento

    estado = {}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
                       else ".frzero/pacote_fontes_15-09") / name
        saved, base, dec_base, _ = rb.replay(root)
        fiel = sum(all(saved[i].get(c) == base[i].get(c) for c in CAMPOS) for i in saved)
        assert fiel == len(saved), (sig, "replay de bloco infiel; nao medir variante")
        with V3():
            _, novo, dec_novo, _ = rb.replay(root)
        blocos = {}
        for b in read(root / "course/.timeline_index.json").get("blocks", []):
            for k in (b.get("id"), b.get("block_uuid")):
                if k:
                    blocos[str(k)] = b
        estado[sig] = {"root": root, "saved": saved, "blocos": blocos,
                       "var": {"base": base, VAR: novo},
                       "dec": {"base": dec_base, VAR: dec_novo},
                       "tde": [{"id": eid, "category": e.get("category"),
                                "source_section": e.get("source_section"),
                                "title": e.get("title")}
                               for eid, e in saved.items() if is_tde(e)]}
        print(sig, "bloco ok | TDE:", len(estado[sig]["tde"]), flush=True)

    # --- unidade/subunidade encadeada: so onde o bloco mudou ---
    unid, unid_raw = {}, {}
    for sig, st in estado.items():
        base_entries = st["var"]["base"]
        alvos = {"base": base_entries}
        novo = st["var"][VAR]
        if any(novo[i].get("temporal_block_id") != base_entries[i].get("temporal_block_id")
               for i in base_entries):
            alvos[VAR] = novo
        orig_read = ru.read
        for nome, entries in alvos.items():
            feed = [copy.deepcopy(entries[i]) for i in entries]

            def patched(path, _feed=feed, _orig=orig_read):
                data = _orig(path)
                if Path(path).name == "manifest.json":
                    data = {**data, "entries": _feed}
                return data

            ru.read = patched
            try:
                _, pos, raw = ru.replay(st["root"])
            finally:
                ru.read = orig_read
            unid[(sig, nome)] = pos
            unid_raw[(sig, nome)] = raw
            print(sig, nome, "unidade ok", flush=True)

    # --- congelamento: hash das decisoes ANTES de qualquer gold ---
    congelado = {sig: {nome: snap(st["var"][nome]) for nome in VARIANTES}
                 for sig, st in estado.items()}
    for (sig, nome), pos in unid.items():
        congelado[sig].setdefault("unidade", {})[nome] = {
            i: [pos[i].get("computed_unit_slug"), pos[i].get("computed_subunit_slug")] for i in pos}
    freeze = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True)
                            .encode("utf-8")).hexdigest()
    print("FREEZE", freeze, flush=True)

    # --- risco de C: quem hoje ancora por due-straddle e o que V3 faz com eles ---
    risco = {}
    for sig, st in estado.items():
        base_e, nov_e = st["var"]["base"], st["var"][VAR]
        metodos = collections.Counter(str(e.get("temporal_block_method") or "-")
                                      for e in base_e.values())
        itens = []
        for eid, e in base_e.items():
            if str(e.get("temporal_block_method") or "") != "due-straddle":
                continue
            itens.append({
                "id": eid, "category": st["saved"][eid].get("category"),
                "source_section": st["saved"][eid].get("source_section"),
                "bloco_antes": e.get("temporal_block_id"),
                "bloco_depois": nov_e[eid].get("temporal_block_id"),
                "metodo_depois": nov_e[eid].get("temporal_block_method"),
                "mudou": e.get("temporal_block_id") != nov_e[eid].get("temporal_block_id"),
            })
        risco[sig] = {"metodos_base": dict(metodos),
                      "due_window_base_n": sum(1 for e in base_e.values()
                                               if str(e.get("temporal_block_provider") or "") == "due-window"),
                      "due_straddle_base_n": len(itens),
                      "mudaram_com_C": sum(1 for i in itens if i["mudou"]),
                      "itens": itens}

    # --- avaliacao (gold a partir daqui) ---
    tot = {v: collections.Counter() for v in VARIANTES}
    cursos = {v: {} for v in VARIANTES}
    mudancas, lateral_ids = [], []
    lateral_tot = {v: collections.Counter() for v in VARIANTES}
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
            # placar LATERAL (so reporte): casa por identidade de id quando a
            # regua por caminho nao casou. NAO altera a regua oficial acima.
            lat_eid = eid or (gid if gid in st["saved"] else None)
            if lat_eid:
                gold_por_id[lat_eid] = {"bloco": gb.get(gid), "unidade": sorted(gu.get(gid, [])),
                                        "sub_primario": sorted(gsp.get(gid, [])), "gold_id": gid,
                                        "na_regua": eid is not None}
                if eid is None:
                    lateral_ids.append({"curso": sig, "gold_id": gid, "id": lat_eid})
            for v in VARIANTES:
                pos = unid.get((sig, v), unid.get((sig, "base")))
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
        for v in VARIANTES:
            cursos[v][sig] = dict(c[v])
            tot[v].update(c[v])
        # ids tocados (bloco e/ou unidade/sub), com antes/depois/gold/metodo
        base_e, base_u = st["var"]["base"], unid[(sig, "base")]
        nov_e = st["var"][VAR]
        nov_u = unid.get((sig, VAR), base_u)
        raw_b, raw_n = unid_raw[(sig, "base")], unid_raw.get((sig, VAR), unid_raw[(sig, "base")])
        for eid in base_e:
            db = base_e[eid].get("temporal_block_id") != nov_e[eid].get("temporal_block_id")
            du = (str(base_u[eid].get("computed_unit_slug") or "") != str(nov_u[eid].get("computed_unit_slug") or "")
                  or str(base_u[eid].get("computed_subunit_slug") or "") != str(nov_u[eid].get("computed_subunit_slug") or ""))
            if not (db or du):
                continue
            bd = nov_e[eid].get("temporal_block_id")
            mudancas.append({
                "curso": sig, "variante": VAR, "id": eid, "tde": is_tde(st["saved"][eid]),
                "category": st["saved"][eid].get("category"),
                "source_section": st["saved"][eid].get("source_section"),
                "bloco_antes": compare.predictions(root, base_e[eid])[0],
                "bloco_depois": compare.predictions(root, nov_e[eid])[0],
                "kind_bloco_depois": (st["blocos"].get(str(bd)) or {}).get("kind"),
                "unit_slug_bloco_depois": (st["blocos"].get(str(bd)) or {}).get("unit_slug"),
                "metodo_antes": base_e[eid].get("temporal_block_method"),
                "metodo_depois": nov_e[eid].get("temporal_block_method"),
                "band_depois": nov_e[eid].get("temporal_block_band"),
                "flag_depois": nov_e[eid].get("temporal_block_flag"),
                "provider_depois": nov_e[eid].get("temporal_block_provider"),
                "decisao_depois": st["dec"][VAR].get(eid),
                "unidade_antes": base_u[eid].get("computed_unit_slug"),
                "unidade_depois": nov_u[eid].get("computed_unit_slug"),
                "razoes_unidade_antes": base_u[eid].get("unit_match_reasons"),
                "razoes_unidade_depois": nov_u[eid].get("unit_match_reasons"),
                "conf_unidade_depois": nov_u[eid].get("unit_match_confidence"),
                "conflito_depois": nov_u[eid].get("unit_block_conflict"),
                "scorer_bruto_antes": raw_b.get(eid),
                "scorer_bruto_depois": raw_n.get(eid),
                "sub_antes": base_u[eid].get("computed_subunit_slug"),
                "sub_depois": nov_u[eid].get("computed_subunit_slug"),
                "gold": gold_por_id.get(eid),
                "na_regua": bool(gold_por_id.get(eid, {}).get("na_regua")),
                "delta": {k: [acertos["base"].get(eid, {}).get(k), acertos[VAR].get(eid, {}).get(k)]
                          for k in ("bloco", "unidade", "sub_primaria", "sub_aceita")
                          if acertos["base"].get(eid, {}).get(k) != acertos[VAR].get(eid, {}).get(k)},
            })
        print(sig, {v: dict(c[v]) for v in VARIANTES}, flush=True)

    perdas = {k: [m["id"] for m in mudancas if m["delta"].get(k) == [True, False]]
              for k in ("bloco", "unidade", "sub_primaria", "sub_aceita")}
    ganhos = {k: [m["id"] for m in mudancas if m["delta"].get(k) == [False, True]]
              for k in ("bloco", "unidade", "sub_primaria", "sub_aceita")}
    checks = {
        "bloco_maior_igual_214": tot[VAR]["bloco"] >= 214,
        "bloco": f'{tot[VAR]["bloco"]}/{tot[VAR]["bloco_n"]}',
        "zero_perda_de_bloco": not perdas["bloco"],
        "nenhum_curso_regride_no_bloco": all(cursos[VAR][s].get("bloco", 0) >= cursos["base"][s].get("bloco", 0)
                                             for s in cursos[VAR]),
        "nenhum_curso_regride_na_unidade": all(cursos[VAR][s].get("unidade", 0) >= cursos["base"][s].get("unidade", 0)
                                               for s in cursos[VAR]),
        "nenhum_curso_regride_na_sub": all(
            cursos[VAR][s].get("sub_primaria", 0) >= cursos["base"][s].get("sub_primaria", 0)
            and cursos[VAR][s].get("sub_aceita", 0) >= cursos["base"][s].get("sub_aceita", 0)
            for s in cursos[VAR]),
        "unidade_244_284": (tot[VAR]["unidade"], tot[VAR]["unidade_n"]) == (244, 284),
        "unidade": f'{tot[VAR]["unidade"]}/{tot[VAR]["unidade_n"]}',
        "sub_primaria_84": tot[VAR]["sub_primaria"] == 84,
        "sub_aceita_107": tot[VAR]["sub_aceita"] == 107,
        "sub": f'{tot[VAR]["sub_primaria"]}/{tot[VAR]["sub_aceita"]}/{tot[VAR]["sub_n"]}',
    }
    checks["ACEITE"] = all(checks[k] for k in (
        "bloco_maior_igual_214", "zero_perda_de_bloco", "nenhum_curso_regride_no_bloco",
        "nenhum_curso_regride_na_unidade", "nenhum_curso_regride_na_sub",
        "unidade_244_284", "sub_primaria_84", "sub_aceita_107"))

    report = {
        "head": "9220a57", "variante": VAR, "freeze_sha256_decisoes": freeze,
        "patch": {
            "a_V1": "motor_apply.tier2_due_scope -> True quando source_section comeca com _TDE_PREFIX; senao delega ao original.",
            "b_C": "due_window._NON_CONTENT_KINDS := frozenset(original - {'assessment'}); review e NON_ACADEMIC_KINDS intactos. resolve_due_window le o global no loop (:111), logo due-contain/due-straddle/band/flag ficam as regras reais.",
            "restauracao": "ambos os atributos de modulo restaurados no __exit__.",
        },
        "checks": checks, "perdas": perdas, "ganhos": ganhos,
        "base_reproduzida": {"bloco": f'{tot["base"]["bloco"]}/{tot["base"]["bloco_n"]}',
                             "unidade": f'{tot["base"]["unidade"]}/{tot["base"]["unidade_n"]}',
                             "sub_primaria": tot["base"]["sub_primaria"],
                             "sub_aceita": tot["base"]["sub_aceita"],
                             "bloco_ausente": tot["base"]["bloco_ausente"]},
        "totais": {v: dict(tot[v]) for v in tot}, "cursos": cursos,
        "mudancas": mudancas,
        "risco_due_straddle": risco,
        "placar_lateral_por_identidade": {"totais": {v: dict(lateral_tot[v]) for v in lateral_tot},
                                          "ids_casados_por_identidade": lateral_ids},
        "tde_por_curso": {s: st["tde"] for s, st in estado.items()},
        "scope": "apply_anchor_engine e apply_unit_subunit_fields reais; patch so em atributos de modulo, restaurado; voter=None.",
        "limitations": ["Ausentes permanecem no denominador da regua oficial; placar lateral e informativo.",
                        "Sem build/rebuild, rede ou LLM; sidecar de votos nao usado.",
                        "Unidade so re-rodada onde a variante mudou bloco; demais cursos herdam a base."],
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOTAIS", json.dumps({v: dict(tot[v]) for v in tot}, ensure_ascii=False))
    print("CHECKS", json.dumps(checks, ensure_ascii=False))
    print("LATERAL", json.dumps({v: dict(lateral_tot[v]) for v in lateral_tot}, ensure_ascii=False))
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
