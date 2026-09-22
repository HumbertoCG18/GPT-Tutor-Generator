"""W-M: duas variantes de regra de BLOCO para secao TDE, patch SO EM MEMORIA.

V1 `tde-tenta-prazo`  : tier2_due_scope(entry) tambem True quando source_section
                        comeca com _TDE_PREFIX (qualquer categoria).
V2 `tde-vira-trabalhos`: category := "trabalhos" em memoria para TDE cuja categoria
                        NAO e referencia/cronograma/codigo, antes da cascata.

Reusa replay_bloco_21-09.replay (fase real de bloco) e replay_unidade_21-09.replay
(fase real de unidade/subunidade, alimentada pelas entries JA decididas pela variante).
Decisoes congeladas por sha256 ANTES de carregar o gold. Sem build, rede, LLM ou escrita em src/.
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
from src.builder.routing.motor.anchor_engine import _REFERENCE_CATEGORIES, _META_CATEGORIES
from src.builder.routing.motor.due_window import _TDE_PREFIX

CAMPOS = ("temporal_block_id", "temporal_block_method", "temporal_block_band",
          "temporal_block_flag", "temporal_block_provider")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_tde(entry):
    return str(entry.get("source_section") or "").strip().startswith(_TDE_PREFIX)


def v2_alvo(entry):
    cat = str(entry.get("category") or "").strip().lower()
    return is_tde(entry) and not (cat in _REFERENCE_CATEGORIES or cat in _META_CATEGORIES
                                  or cat.startswith("codigo"))


class V1:
    nome = "V1-tde-tenta-prazo"

    def __enter__(self):
        self.orig = motor_apply.tier2_due_scope
        orig = self.orig
        motor_apply.tier2_due_scope = lambda e: True if is_tde(e) else orig(e)

    def __exit__(self, *exc):
        motor_apply.tier2_due_scope = self.orig


class V2:
    nome = "V2-tde-vira-trabalhos"

    def __enter__(self):
        self.orig = motor_apply.apply_anchor_engine
        orig = self.orig

        def wrapper(entries, *a, **kw):
            for e in entries:
                if v2_alvo(e):
                    e["category"] = "trabalhos"
            return orig(entries, *a, **kw)

        motor_apply.apply_anchor_engine = wrapper

    def __exit__(self, *exc):
        motor_apply.apply_anchor_engine = self.orig


def snap(entries):
    return {eid: {c: e.get(c) for c in CAMPOS} for eid, e in entries.items()}


def main():
    out = HERE / "regra_tde_prazo_bloco_21-09.json"
    assert not out.exists(), "preservar evidencia existente"
    rb = load("rb_wm", HERE / "replay_bloco_21-09.py")
    ru = load("ru_wm", HERE / "replay_unidade_21-09.py")
    compare = load("cmp_wm", HERE / "compara_herancas_15-09.py")
    mede = compare.mede   # NOMES so; golds() e chamado depois do congelamento

    estado = {}   # sig -> {"root", "entries": {variante: {id: entry}}, "decisions": {...}, "tde": [...]}
    for sig, name in mede.NOMES.items():
        root = DATA / (".frzero/pacote_categoria_17-09" if sig in {"MF", "IA"}
                       else ".frzero/pacote_fontes_15-09") / name
        saved, base, dec_base, _ = rb.replay(root)
        fiel = sum(all(saved[i].get(c) == base[i].get(c) for c in CAMPOS) for i in saved)
        assert fiel == len(saved), (sig, "replay de bloco infiel; nao medir variante")
        por_var = {"base": base, "base_dec": dec_base}
        for var in (V1(), V2()):
            with var:
                _, novo, dec, _ = rb.replay(root)
            por_var[var.nome] = novo
            por_var[var.nome + "_dec"] = dec
        tde = [{"id": eid, "category": e.get("category"), "source_section": e.get("source_section"),
                "source_path": e.get("source_path"), "title": e.get("title")}
               for eid, e in saved.items() if is_tde(e)]
        estado[sig] = {"root": root, "saved": saved, "var": por_var, "tde": tde,
                       "v2_alvo": [eid for eid, e in saved.items() if v2_alvo(e)]}
        print(sig, "bloco ok | TDE:", len(tde), "| V2 alvo:", len(estado[sig]["v2_alvo"]), flush=True)

    # --- unidade/subunidade encadeada: so onde pode mudar (V1: cursos com bloco alterado) ---
    unid = {}   # (sig, variante) -> {id: entry}
    for sig, st in estado.items():
        base_entries = st["var"]["base"]
        alvos = {"base": base_entries}
        for nome in (V1.nome, V2.nome):
            novo = st["var"][nome]
            mudou_bloco = any(novo[i].get("temporal_block_id") != base_entries[i].get("temporal_block_id")
                              for i in base_entries)
            if mudou_bloco or (nome == V2.nome and st["v2_alvo"]):
                alvos[nome] = novo
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
                _, pos, _ = ru.replay(st["root"])
            finally:
                ru.read = orig_read
            unid[(sig, nome)] = pos
            print(sig, nome, "unidade ok", flush=True)

    # --- congelamento: hash das decisoes ANTES de qualquer gold ---
    congelado = {sig: {nome: snap(st["var"][nome]) for nome in ("base", V1.nome, V2.nome)}
                 for sig, st in estado.items()}
    for (sig, nome), pos in unid.items():
        congelado[sig].setdefault("unidade", {})[nome] = {
            i: [pos[i].get("computed_unit_slug"), pos[i].get("computed_subunit_slug")] for i in pos}
    freeze = hashlib.sha256(json.dumps(congelado, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    print("FREEZE", freeze, flush=True)

    # --- avaliacao (gold a partir daqui) ---
    VARIANTES = ("base", V1.nome, V2.nome)
    tot = {v: collections.Counter() for v in VARIANTES}
    cursos = {v: {} for v in VARIANTES}
    mudancas, lateral = [], []
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
            if eid:
                gold_por_id[eid] = {"bloco": gb.get(gid), "unidade": sorted(gu.get(gid, [])),
                                    "sub_primario": sorted(gsp.get(gid, [])), "gold_id": gid}
            for v in VARIANTES:
                ent = st["var"][v].get(eid) if eid else None
                pos = unid.get((sig, v), unid.get((sig, "base")))
                uent = pos.get(eid) if eid else None
                pb = compare.predictions(root, ent)[0] if ent else None
                pu = str(uent.get("computed_unit_slug") or "") if uent else None
                ps = str(uent.get("computed_subunit_slug") or "") if uent else None
                if row["bloco"] != "":
                    c[v]["bloco_n"] += 1
                    if ent is None:
                        c[v]["bloco_ausente"] += 1
                    ok = bool(ent) and pb == gb[gid]
                    c[v]["bloco"] += ok
                    acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["bloco"] = ok
                if row["unidade"] != "":
                    c[v]["unidade_n"] += 1
                    ok = bool(uent) and pu in gu[gid]
                    c[v]["unidade"] += ok
                    acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["unidade"] = ok
                if row["sub_primario"] != "":
                    c[v]["sub_n"] += 1
                    okp = bool(uent) and ps in gsp[gid]
                    oka = bool(uent) and ps in gs[gid]
                    c[v]["sub_primaria"] += okp
                    c[v]["sub_aceita"] += oka
                    acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["sub_primaria"] = okp
                    acertos[v].setdefault(eid or f"AUSENTE-{gid}", {})["sub_aceita"] = oka
        for v in VARIANTES:
            cursos[v][sig] = dict(c[v])
            tot[v].update(c[v])
        # ids tocados por variante (bloco e unidade/sub), com antes/depois/gold
        base_e, base_u = st["var"]["base"], unid[(sig, "base")]
        for v in (V1.nome, V2.nome):
            nov_e = st["var"][v]
            nov_u = unid.get((sig, v), base_u)
            for eid in base_e:
                db = base_e[eid].get("temporal_block_id") != nov_e[eid].get("temporal_block_id")
                du = (str(base_u[eid].get("computed_unit_slug") or "") != str(nov_u[eid].get("computed_unit_slug") or "")
                      or str(base_u[eid].get("computed_subunit_slug") or "") != str(nov_u[eid].get("computed_subunit_slug") or ""))
                if not (db or du):
                    continue
                reg = {"curso": sig, "variante": v, "id": eid, "tde": is_tde(st["saved"][eid]),
                       "category": st["saved"][eid].get("category"),
                       "source_section": st["saved"][eid].get("source_section"),
                       "bloco_antes": compare.predictions(root, base_e[eid])[0],
                       "bloco_depois": compare.predictions(root, nov_e[eid])[0],
                       "metodo_antes": base_e[eid].get("temporal_block_method"),
                       "metodo_depois": nov_e[eid].get("temporal_block_method"),
                       "provider_depois": nov_e[eid].get("temporal_block_provider"),
                       "band_depois": nov_e[eid].get("temporal_block_band"),
                       "flag_depois": nov_e[eid].get("temporal_block_flag"),
                       "unidade_antes": base_u[eid].get("computed_unit_slug"),
                       "unidade_depois": nov_u[eid].get("computed_unit_slug"),
                       "sub_antes": base_u[eid].get("computed_subunit_slug"),
                       "sub_depois": nov_u[eid].get("computed_subunit_slug"),
                       "gold": gold_por_id.get(eid),
                       "na_regua": eid in gold_por_id,
                       "delta": {k: [acertos["base"].get(eid, {}).get(k), acertos[v].get(eid, {}).get(k)]
                                 for k in ("bloco", "unidade", "sub_primaria", "sub_aceita")
                                 if acertos["base"].get(eid, {}).get(k) != acertos[v].get(eid, {}).get(k)}}
                mudancas.append(reg)
                if not reg["na_regua"]:
                    lateral.append(reg)
        print(sig, {v: dict(c[v]) for v in VARIANTES}, flush=True)

    checks = {}
    for v in (V1.nome, V2.nome):
        perdas = [m for m in mudancas if m["variante"] == v and m["delta"].get("bloco") == [True, False]]
        checks[v] = {
            "bloco_maior_igual_214": tot[v]["bloco"] >= 214,
            "bloco": f'{tot[v]["bloco"]}/{tot[v]["bloco_n"]}',
            "zero_perda_de_bloco": not perdas,
            "nenhum_curso_regride_no_bloco": all(cursos[v][s].get("bloco", 0) >= cursos["base"][s].get("bloco", 0)
                                                 for s in cursos[v]),
            "nenhum_curso_regride_na_unidade": all(cursos[v][s].get("unidade", 0) >= cursos["base"][s].get("unidade", 0)
                                                   for s in cursos[v]),
            "unidade_244_284": (tot[v]["unidade"], tot[v]["unidade_n"]) == (244, 284),
            "unidade": f'{tot[v]["unidade"]}/{tot[v]["unidade_n"]}',
            "sub_primaria_84": tot[v]["sub_primaria"] == 84,
            "sub_aceita_107": tot[v]["sub_aceita"] == 107,
            "sub": f'{tot[v]["sub_primaria"]}/{tot[v]["sub_aceita"]}/{tot[v]["sub_n"]}',
        }
        checks[v]["ACEITE"] = all(checks[v][k] for k in (
            "bloco_maior_igual_214", "zero_perda_de_bloco", "nenhum_curso_regride_no_bloco",
            "unidade_244_284", "sub_primaria_84", "sub_aceita_107"))

    report = {
        "head": "9220a57", "freeze_sha256_decisoes": freeze, "checks": checks,
        "base_reproduzida": {"bloco": f'{tot["base"]["bloco"]}/{tot["base"]["bloco_n"]}',
                             "unidade": f'{tot["base"]["unidade"]}/{tot["base"]["unidade_n"]}',
                             "sub_primaria": tot["base"]["sub_primaria"], "sub_aceita": tot["base"]["sub_aceita"],
                             "bloco_ausente": tot["base"]["bloco_ausente"]},
        "totais": {v: dict(tot[v]) for v in tot}, "cursos": cursos,
        "mudancas": mudancas, "fora_da_regua": lateral,
        "tde_por_curso": {s: st["tde"] for s, st in estado.items()},
        "v2_alvo_por_curso": {s: st["v2_alvo"] for s, st in estado.items()},
        "scope": "apply_anchor_engine e apply_unit_subunit_fields reais; patch so em atributos de modulo, restaurado; voter=None.",
        "limitations": ["Ausentes permanecem no denominador da regua (t1-2026-1 nao casa por origem).",
                        "Sem build/rebuild, rede ou LLM; sidecar de votos nao usado.",
                        "Unidade so re-rodada onde a variante pode mudar; demais cursos herdam a base."],
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print("TOTAIS", json.dumps({v: dict(tot[v]) for v in tot}, ensure_ascii=False))
    print("CHECKS", json.dumps(checks, ensure_ascii=False))
    print("SHA256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
