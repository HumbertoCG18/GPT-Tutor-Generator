"""SARC POSICIONAL: o experimento do astra (handoff 12/09 §12.4), finalmente medido.

REGRA (literal do desenho): o material herda o subtopico que a sessao do SARC do seu BLOCO nomeia, restrito aos
topicos da UNIDADE congelada do material. Abstencao por identificacao insuficiente, tres motivos:
  so-o-pai            a sessao nomeia um topico que TEM filhos na mesma unidade (codigo de outline prefixo)
  multiplos           a sessao nomeia 2+ topicos
  sessoes-discordantes  as sessoes do bloco produzem candidatos diferentes
(+ um quarto motivo que o desenho nao nomeia mas existe: 'nenhum', a sessao nao nomeia topico algum)

CONTROLE (nao circular): material -> bloco -> unidade vem CONGELADO do manifest; o braco tratamento so escreve
`computed_subunit_slug` / `subunit_match_reasons`. Nenhuma subunidade nova volta para o bloco. Materiais com
`manual_timeline_block_id` saem em recorte separado.

Dois bracos x dois regimes (cru = sem sinonimos do sidecar LLM; produto = taxonomia como esta), escopo="produto",
7 cursos, base 251. 0 chamadas de rede (socket bloqueado no replay).

Variantes medidas (a escolha entre elas e o unico parametro -> por isso o holdout LOCO no fim):
  A  SOBREPOE  a decisao propria do material sempre que o SARC identifica  (a regra literal do astra)
  B  SO PREENCHE quando a decisao propria ficou VAZIA

Uso: python -B <este arquivo>
"""
import collections
import copy
import csv
import importlib.util
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
HERE = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator\docs\reports\_harness-2026-09-04\c1-3")
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)  # faz os.chdir para a raiz do repo e bloqueia socket
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")

from src.builder.core.vocabulary_compile import _norm  # noqa: E402
from src.builder.routing.resolver_apply import _frase_no_texto, _secao_nomeia_subtopico  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402
from src.builder.text.normalize import normalize_match_text as NM  # noqa: E402
from src.builder.text.patterns import SECTION_NUM_PREFIX_RE as NUMRE  # noqa: E402
from src.builder.text.stopwords import MOTOR_GENERIC_STEMS as GENSTEMS  # noqa: E402
from src.builder.timeline.index import _iter_content_taxonomy_topics as topics  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]
SARC_REASON = "sarc-posicional"


def sem_llm(sig):
    p = Path("..") / rp.NAMES[sig] / "course/.glossary_curation.llm.json"
    vet = set()
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        vet = {_norm(v) for k, e in d.items() if not k.startswith("_") for v in e.get("synonyms", [])}

    def change(tax):
        for u in tax["units"]:
            for t in u["topics"]:
                t["aliases"] = [a for a in t.get("aliases", []) if _norm(a) not in vet]
    return change


def gold_rows(sig):
    p = Path(f"docs/reports/subunit_gt_{sig}.csv")
    return {r["entry_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if r["scorable"] == "yes"}


# ---- o detector: MESMO criterio de `_secao_nomeia_subtopico`, mas devolvendo a LISTA de topicos nomeados -------
def _toks(text, generic):
    return {t for t in NM(text).split() if len(t) >= 4 and t not in generic
            and not any(t.startswith(g) for g in GENSTEMS)}


def hits_nomeados(texto, tops):
    sec = NM(NUMRE.sub("", str(texto or "")))
    if not sec:
        return []
    out = []
    for t in tops:
        generic = set(t.get("generic_tokens") or [])
        frases = [NM(x) for x in [t.get("topic_label") or ""] + list(t.get("aliases") or [])]
        if any(f and (_frase_no_texto(sec, f) or _frase_no_texto(f, sec)) for f in frases):
            out.append(t["topic_slug"])
            continue
        st, lt = _toks(sec, generic), _toks(t.get("topic_label") or "", generic)
        if st and lt and (st <= lt or lt <= st):
            out.append(t["topic_slug"])
    return list(dict.fromkeys(out))


def filhos_de(tops):
    """slug -> filhos na MESMA unidade pelo codigo de outline ('7.1.1' e pai de '7.1.1.1')."""
    cod = {t["topic_slug"]: str(t.get("topic_code") or "").strip() for t in tops}
    ch = collections.defaultdict(set)
    for s, c in cod.items():
        if not c:
            continue
        for s2, c2 in cod.items():
            if s2 != s and c2 and c2.startswith(c + "."):
                ch[s].add(s2)
    return ch


def sarc_do_bloco(sessions, tops):
    """(slug_decidido, motivo, detalhe). motivo == 'decide' quando identifica."""
    ch = filhos_de(tops)
    cands, motivos, det = set(), [], []
    for s in sessions:
        lab = str(s.get("label") or "")
        hs = hits_nomeados(lab, tops)
        # controle de fidelidade: com exatamente 1 hit o detector tem que bater com o do motor
        assert (hs[0] if len(hs) == 1 else "") == _secao_nomeia_subtopico({"source_section": lab}, tops, GENSTEMS)
        if not hs:
            motivos.append("nenhum")
            continue
        if len(hs) > 1:
            pai_1filho = [y for y in hs if ch.get(y) and (ch[y] & set(hs))]
            motivos.append("multiplos-pai+1filho" if (len(pai_1filho) == 1 and len(hs) == 2) else "multiplos")
            det.append((str(s.get("id") or ""), lab[:90], "MULTI:" + "+".join(hs)))
            continue
        y = hs[0]
        if ch.get(y):
            motivos.append("so-o-pai")
            det.append((str(s.get("id") or ""), lab[:90], "PAI:" + y))
            continue
        cands.add(y)
        det.append((str(s.get("id") or ""), lab[:90], y))
    if len(cands) == 1:
        return next(iter(cands)), "decide", det
    if len(cands) > 1:
        return "", "sessoes-discordantes", det
    for m in ("so-o-pai", "multiplos", "multiplos-pai+1filho", "nenhum"):
        if m in motivos:
            return "", m, det
    return "", "bloco-sem-sessao", det


CAMPOS = ("computed_subunit_slug", "subunit_match_reasons", "subunit_match_confidence")


def placar(entries_by_id, gold):
    a = p = conf = cok = 0
    errs, oks = [], []
    for eid, row in gold.items():
        e = entries_by_id.get(eid)
        pred = str((e or {}).get("computed_subunit_slug") or "")
        aceitos = ({row["gold_subunit"]} | set(filter(None, (row.get("gold_subunits_extra") or "").split(";")))
                   if row["gold_subunit"] else {""})
        ok = pred in aceitos
        a += ok
        p += (pred == row["gold_subunit"])
        if e is not None and revisar_de(e) == "ok":
            conf += 1
            if ok:
                cok += 1
                oks.append(eid)
            else:
                errs.append(eid)
    return {"aceito": a, "primario": p, "confiantes": conf, "conf_ok": cok, "conf_err": len(errs),
            "errs": errs, "oks": oks, "n": len(gold)}


# ---- roda -----------------------------------------------------------------------------------------------------
REGIMES = {"cru": True, "produto": False}
res = {}          # (regime, braco) -> {sig: placar}
detalhes = []     # CSV por material
abst = {}         # regime -> Counter de motivos (por MATERIAL do gold)
pinos = collections.defaultdict(list)
unidade_contestada = collections.Counter()

for sig in CURSOS:
    gold = gold_rows(sig)
    root = Path(".ablacao") / rp.NAMES[sig]
    tl = json.loads((root / "course/.timeline_index.json").read_text(encoding="utf-8"))
    blocos = {}
    for b in tl["blocks"]:
        for k in (str(b.get("id") or ""), str(b.get("block_uuid") or "")):
            if k:
                blocos[k] = b.get("sessions") or []

    for reg, cru in REGIMES.items():
        r = rp.evaluate(sig, "com", new=False, taxmod=(sem_llm(sig) if cru else None), escopo="produto")
        entries, tax, processados = r[6], r[7], r[8]
        by_id = {e["id"]: e for e in entries}
        por_unidade = collections.defaultdict(list)
        for t in topics(tax):
            por_unidade[str(t.get("unit_slug") or "")].append(t)
        todos_tops = [t for ts in por_unidade.values() for t in ts]

        base = {e["id"]: {k: copy.deepcopy(e.get(k)) for k in CAMPOS} for e in entries}
        ctrl = placar(by_id, gold)
        eixo_fixo = {e["id"]: (str(e.get("computed_unit_slug") or ""), str(e.get("manual_timeline_block_id") or ""),
                               str(e.get("temporal_block_id") or "")) for e in entries}

        # proposta do SARC por (bloco, unidade), cacheada
        cache = {}
        prop = {}
        for e in entries:
            if e["id"] not in processados:
                continue
            bid = str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or "")
            uni = str(e.get("computed_unit_slug") or "")
            key = (bid, uni)
            if key not in cache:
                cache[key] = sarc_do_bloco(blocos.get(bid, []), por_unidade.get(uni, []))
            prop[e["id"]] = cache[key]
            if str(e.get("manual_timeline_block_id") or "").strip():
                pinos[sig].append(e["id"])

        if reg == "cru":
            c = abst.setdefault("cru", collections.Counter())
        else:
            c = abst.setdefault("produto", collections.Counter())
        for eid in gold:
            if eid in prop:
                c[prop[eid][1]] += 1
            else:
                c["fora-do-escopo"] += 1

        # eixo unidade latente: o SARC do bloco nomeia 1 topico de OUTRA unidade?
        if reg == "cru":
            for eid in gold:
                e = by_id.get(eid)
                if e is None:
                    continue
                bid = str(e.get("manual_timeline_block_id") or e.get("temporal_block_id") or "")
                uni = str(e.get("computed_unit_slug") or "")
                fora = set()
                for s in blocos.get(bid, []):
                    for y in hits_nomeados(str(s.get("label") or ""), todos_tops):
                        tt = next((t for t in todos_tops if t["topic_slug"] == y), None)
                        if tt and str(tt.get("unit_slug") or "") != uni:
                            fora.add(y)
                if fora:
                    unidade_contestada[sig] += 1

        snap = {}
        for variante in ("A", "B"):
            for e in entries:
                for k in CAMPOS:
                    e[k] = copy.deepcopy(base[e["id"]][k])
            mudou = 0
            for e in entries:
                y, motivo, _ = prop.get(e["id"], ("", "fora-do-escopo", []))
                if motivo != "decide" or not y:
                    continue
                atual = str(e.get("computed_subunit_slug") or "")
                if variante == "B" and atual:
                    continue
                if y == atual:
                    continue
                reasons = [str(x) for x in (e.get("subunit_match_reasons") or [])]
                e["computed_subunit_slug"] = y
                e["subunit_match_reasons"] = [x for x in reasons
                                              if x != "ambiguous" and not x.startswith("empate-exato")] + [SARC_REASON]
                mudou += 1
            trat = placar(by_id, gold)
            res[(reg, variante)] = res.get((reg, variante), {})
            res[(reg, variante)][sig] = trat
            res[(reg, variante)][sig]["mudou"] = mudou
            for e in entries:  # eixos bloco/unidade nao podem ter mudado
                assert eixo_fixo[e["id"]] == (str(e.get("computed_unit_slug") or ""),
                                              str(e.get("manual_timeline_block_id") or ""),
                                              str(e.get("temporal_block_id") or "")), e["id"]
            snap[variante] = {eid: (str((by_id.get(eid) or {}).get("computed_subunit_slug") or ""),
                                    int(by_id.get(eid) is not None and revisar_de(by_id[eid]) == "ok"))
                              for eid in gold}
            restore = base
        for e in entries:  # volta ao estado do CONTROLE antes de montar o detalhe
            for k in CAMPOS:
                e[k] = copy.deepcopy(restore[e["id"]][k])
        for eid, row in gold.items():
            e = by_id.get(eid)
            y, motivo, det = prop.get(eid, ("", "fora-do-escopo", []))
            aceitos = ({row["gold_subunit"]} | set(filter(None, (row.get("gold_subunits_extra") or "").split(";")))
                       if row["gold_subunit"] else {""})
            pc = str(base[eid]["computed_subunit_slug"] or "") if eid in base else ""
            pa, ca = snap["A"][eid]
            pb, cb = snap["B"][eid]
            detalhes.append({
                "curso": sig, "regime": reg, "entry_id": eid,
                "pino_manual": int(bool(str((e or {}).get("manual_timeline_block_id") or "").strip())),
                "unidade": str((e or {}).get("computed_unit_slug") or ""),
                "bloco": str((e or {}).get("manual_timeline_block_id") or (e or {}).get("temporal_block_id") or ""),
                "gold_primario": row["gold_subunit"], "gold_extras": row.get("gold_subunits_extra", ""),
                "pred_controle": pc, "pred_A": pa, "pred_B": pb,
                "aceito_controle": int(pc in aceitos), "aceito_A": int(pa in aceitos), "aceito_B": int(pb in aceitos),
                "prim_controle": int(pc == row["gold_subunit"]), "prim_A": int(pa == row["gold_subunit"]),
                "prim_B": int(pb == row["gold_subunit"]),
                "conf_controle": int(e is not None and revisar_de(e) == "ok"), "conf_A": ca, "conf_B": cb,
                "sarc_slug": y, "sarc_motivo": motivo,
                "sarc_sessoes": " || ".join(f"{i}::{lab}::{v}" for i, lab, v in det)[:400],
            })
        for e in entries:  # deixa o objeto no estado do controle (higiene)
            for k in CAMPOS:
                e[k] = copy.deepcopy(restore[e["id"]][k])
        res[(reg, "ctrl")] = res.get((reg, "ctrl"), {})
        res[(reg, "ctrl")][sig] = ctrl
    print(f"{sig} ok", flush=True)


def agrega(d):
    t = {k: sum(d[s][k] for s in CURSOS) for k in ("aceito", "primario", "confiantes", "conf_ok", "conf_err", "n")}
    return t


N = agrega(res[("cru", "ctrl")])["n"]
print()
print(f"=== SARC POSICIONAL — base {N}, 7 cursos, escopo=produto ===")
print()
hdr = f"{'regime/braco':22} {'aceito':>12} {'primario':>12} {'cobertura':>12} {'aceito/conf':>12} {'erros conf':>11} {'entrega':>12}"
print(hdr)
for reg in ("cru", "produto"):
    for br, nome in (("ctrl", "CONTROLE"), ("A", "SARC-A sobrepoe"), ("B", "SARC-B preenche")):
        t = agrega(res[(reg, br)])
        print(f"{reg + ' ' + nome:22} {t['aceito']:4} {t['aceito']/N:6.1%} {t['primario']:4} {t['primario']/N:6.1%} "
              f"{t['confiantes']:4} {t['confiantes']/N:6.1%} {t['conf_ok']/max(1,t['confiantes']):11.1%} "
              f"{t['conf_err']:11} {t['conf_ok']:4} {t['conf_ok']/N:6.1%}")
    print()

print("=== POR CURSO (aceito ctrl -> A -> B | primario | erros confiantes) ===")
for reg in ("cru", "produto"):
    print(f"-- {reg}")
    print(f"{'curso':5} {'n':>4} {'aceito c/A/B':>18} {'primario c/A/B':>18} {'errconf c/A/B':>16} {'entrega c/A/B':>16} {'mudou A/B':>10}")
    for sig in CURSOS:
        c, a, b = res[(reg, "ctrl")][sig], res[(reg, "A")][sig], res[(reg, "B")][sig]
        print(f"{sig:5} {c['n']:>4} {c['aceito']:>5}/{a['aceito']:<4}/{b['aceito']:<6} "
              f"{c['primario']:>5}/{a['primario']:<4}/{b['primario']:<6} "
              f"{c['conf_err']:>4}/{a['conf_err']:<3}/{b['conf_err']:<5} "
              f"{c['conf_ok']:>4}/{a['conf_ok']:<3}/{b['conf_ok']:<5} {a['mudou']:>4}/{b['mudou']:<4}")
    print()

for V in ("A", "B"):
    print(f"=== GANHOS E PERDAS NOMINAIS (aceito), variante {V} ===")
    for reg in ("cru", "produto"):
        for sig in CURSOS:
            g = [d for d in detalhes if d["curso"] == sig and d["regime"] == reg
                 and d[f"aceito_{V}"] > d["aceito_controle"]]
            pr = [d for d in detalhes if d["curso"] == sig and d["regime"] == reg
                  and d[f"aceito_{V}"] < d["aceito_controle"]]
            if not g and not pr:
                continue
            print(f"  [{reg}] {sig}: +{len(g)} / -{len(pr)}")
            for d in g:
                print(f"     GANHA {d['entry_id']:44} {d['pred_controle'] or '(vazio)'} -> {d['sarc_slug']}")
            for d in pr:
                print(f"     PERDE {d['entry_id']:44} {d['pred_controle'] or '(vazio)'} -> {d['sarc_slug']}"
                      f"   (gold {d['gold_primario'] or '(vazio)'})")
    print()

print("=== O QUE O SARC DECIDE x o que o material ja dizia (gold, variante A) ===")
print(f"{'regime':9} {'decide':>7} {'concorda':>9} {'discorda':>9} {'  discorda e SARC certo':>24} {'ctrl certo':>11} {'ambos errados':>14}")
for reg in ("cru", "produto"):
    ds = [d for d in detalhes if d["regime"] == reg and d["sarc_motivo"] == "decide"]
    conc = [d for d in ds if d["sarc_slug"] == d["pred_controle"]]
    disc = [d for d in ds if d["sarc_slug"] != d["pred_controle"]]
    sarc_ok = [d for d in disc if d["aceito_A"] and not d["aceito_controle"]]
    ctrl_ok = [d for d in disc if d["aceito_controle"] and not d["aceito_A"]]
    ambos = [d for d in disc if not d["aceito_controle"] and not d["aceito_A"]]
    print(f"{reg:9} {len(ds):>7} {len(conc):>9} {len(disc):>9} {len(sarc_ok):>24} {len(ctrl_ok):>11} {len(ambos):>14}")
print("(concordancia apoiada na MESMA sessao nao conta como confirmacao independente — astra §12.4)")
print()

print("=== ABSTENCAO DA REGRA, por motivo (materiais do gold) ===")
for reg in ("cru", "produto"):
    c = abst[reg]
    tot = sum(c.values())
    print(f"-- {reg} (total {tot})")
    for m, v in c.most_common():
        print(f"   {m:26} {v:>4}  {v/max(1,tot):5.1%}")
print()

print("=== EIXOS BLOCO E UNIDADE ===")
print("Assert por entry passou: nenhum campo de bloco/unidade muda entre os bracos (o tratamento so escreve subunidade).")
print("Unidade LATENTE contestada (o SARC do bloco nomeia topico de OUTRA unidade), por curso:",
      dict(unidade_contestada), "total", sum(unidade_contestada.values()))
print()
print("=== PINOS MANUAIS (recorte separado) ===")
for sig, ids in pinos.items():
    no_gold = [i for i in ids if i in gold_rows(sig)]
    print(f"  {sig}: {len(set(ids))} materiais com manual_timeline_block_id; no gold: {len(set(no_gold))} {sorted(set(no_gold))}")
print()

# ---- holdout leave-one-course-out sobre a UNICA escolha de parametro (A x B) -----------------------------------
print("=== HOLDOUT leave-one-course-out (escolha A x B por saldo = dC - k*dE) ===")
for reg in ("cru", "produto"):
    for k in (1, 2, 4):
        linhas = []
        for fold in CURSOS:
            outros = [s for s in CURSOS if s != fold]
            best, bestv = None, None
            for br in ("A", "B"):
                dC = sum(res[(reg, br)][s]["conf_ok"] - res[(reg, "ctrl")][s]["conf_ok"] for s in outros)
                dE = sum(res[(reg, br)][s]["conf_err"] - res[(reg, "ctrl")][s]["conf_err"] for s in outros)
                v = dC - k * dE
                if bestv is None or v > bestv:
                    best, bestv = br, v
            dCf = res[(reg, best)][fold]["conf_ok"] - res[(reg, "ctrl")][fold]["conf_ok"]
            dEf = res[(reg, best)][fold]["conf_err"] - res[(reg, "ctrl")][fold]["conf_err"]
            linhas.append((fold, best, bestv, dCf, dEf, dCf - k * dEf))
        pos = sum(1 for l in linhas if l[5] > 0)
        print(f"-- {reg} k={k}: generaliza (saldo>0) em {pos}/7 folds; soma fora da amostra "
              f"{sum(l[5] for l in linhas):+d}")
        for f, br, v, dC, dE, s in linhas:
            print(f"     fold {f:4} escolhe {br}  (saldo dentro {v:+4})  fora: dC {dC:+3} dE {dE:+3} saldo {s:+4}")
    print()

out = OUT / "sarc_posicional_12-09.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(detalhes[0].keys()))
    w.writeheader()
    w.writerows(detalhes)
print(f"CSV: {out}  ({len(detalhes)} linhas = 251 x 2 regimes)")
