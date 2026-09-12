"""v2 do espiao de sinais (base: sinais_fragilidade_cru.py desta mesma sessao).

Acrescenta ao v1, sem tocar nele:
  - share_score = s1 / soma dos scores positivos da unidade (o "share do vencedor" por SCORE;
    o v1 so tinha share_unid, que e concentracao de MATERIAIS na subunidade).
  - diag de TODOS os topicos da unidade na chamada que decidiu -> doador/exact_hits/tamanho da
    frase do TOPICO ENTREGUE (nao so do vencedor do score; diferem quando a regra do titulo ou
    a da secao sobrepoem o vencedor).
  - rota: 1a | 2a-propagado | 2a-decomposto | 2a-titulo | 2a-secao | vazio-<motivo>.
0 chamadas de rede (o replay bloqueia socket). Nao escreve no repo nem em .ablacao/.
"""
import csv
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(r"C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3")
OUT = Path(__file__).resolve().parent   # 12/09: saida no proprio harness (era o scratchpad da sessao)
spec = importlib.util.spec_from_file_location("replay", HERE / "replay_subunidade.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)
rp.NAMES.update(CG="Computacao-Grafica-Tutor", FR="Fundamentos-de-Redes-Tutor")
from src.builder.core.vocabulary_compile import _norm  # noqa: E402
from src.builder.routing.revisar import revisar_de  # noqa: E402
from src.builder.text.stopwords import UNIT_GENERIC_TOKENS  # noqa: E402

ti = rp.ti
nm = ti._normalize_match_text
mp = ti._matches_normalized_phrase
CURSOS = ["MF", "SO", "IA", "ES2", "TCC", "CG", "FR"]

FIELDS = [("markdown_headings_text", 4.4), ("title_text", 3.8), ("manual_tags_text", 3.0),
          ("markdown_lead_text", 2.8), ("markdown_text", 1.1), ("raw_text", 0.9),
          ("auto_tags_text", 0.22), ("legacy_tags_text", 0.15)]


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


def diag(signals, topic):
    """Anatomia do casamento frase->campo de UM topico (reproduz o laco de frases do scorer)."""
    label = str(topic.get("topic_label", "") or "").strip()
    topic_slug = str(topic.get("topic_slug", "") or "").strip()
    aliases = [str(a) for a in (topic.get("aliases", []) or []) if str(a).strip()]
    phrases = {}
    if label:
        phrases[nm(label)] = (1.0, label, "label")
    for a in aliases:
        an = nm(a)
        if an and (an not in phrases or phrases[an][0] < 0.82):
            phrases[an] = (0.82, an, "alias")
    if topic_slug:
        sp = topic_slug.replace("-", " ")
        sn = nm(sp)
        if sn and sn not in phrases:
            phrases[sn] = (0.65, sp, "slug")
    phrases.pop("", None)
    hits = []
    for campo, peso in FIELDS:
        txt = signals.get(campo, "")
        for fator, frase, origem in phrases.values():
            if mp(txt, frase, False):
                hits.append((campo, peso, frase, len(nm(frase).split()), origem))
    _generic = set(topic.get("generic_tokens") or []) or UNIT_GENERIC_TOKENS
    _short = set(topic.get("short_vocab") or [])

    def conta(t):
        return len(t) >= 4 or t in _short
    topic_tokens = {t for t in nm(label).split() if conta(t) and t not in _generic}
    for a in aliases:
        topic_tokens.update(t for t in nm(a).split() if conta(t) and t not in _generic)
    sig_tokens = set()
    for campo, _ in FIELDS:
        sig_tokens.update(t for t in signals.get(campo, "").split() if len(t) >= 4 or t in _short)
    overlap = topic_tokens & sig_tokens
    best = max(hits, key=lambda h: h[1]) if hits else None
    return dict(exact_hits=len(hits), frase=int(bool(hits)),
                max_tok_frase=max((h[3] for h in hits), default=0),
                tok_frase_doador=(best[3] if best else 0),
                origem=(best[4] if best else ""),
                doador=(best[0] if best else ""), peso_doador=(best[1] if best else 0.0),
                n_topic_tokens=len(topic_tokens), n_overlap=len(overlap),
                cobertura=(len(overlap) / len(topic_tokens)) if topic_tokens else 0.0,
                n_alias=len(aliases))


VAZIO = dict(exact_hits=0, frase=0, max_tok_frase=0, tok_frase_doador=0, origem="", doador="",
             peso_doador=0.0, n_topic_tokens=0, n_overlap=0, cobertura=0.0, n_alias=0)
REC = {}


def make_spy(chave):
    base = rp.sub

    def spy(entry, tax, texto, winning_unit_slug=""):
        idx = rp.topics(tax)
        if winning_unit_slug:
            idx = [t for t in idx if str(t.get("unit_slug", "") or "") == winning_unit_slug]
        sg = rp.signals(entry, texto)
        scored = sorted(((t, rp.score(sg, t)) for t in idx), key=lambda x: x[1], reverse=True)
        m = base(entry, tax, texto, winning_unit_slug=winning_unit_slug)
        d = {}
        por_slug = {}
        if scored:
            s1 = scored[0][1]
            s2 = scored[1][1] if len(scored) > 1 else 0.0
            soma = sum(s for _, s in scored if s > 0)
            d = dict(diag(sg, scored[0][0]))
            d.update(s1=s1, s2=s2, margem=s1 - s2, razao=(s2 / s1 if s1 > 0 else 1.0),
                     share_score=(s1 / soma if soma > 0 else 0.0),
                     n_pos=sum(1 for _, s in scored if s > 0), n_cand=len(scored),
                     win_slug=str(scored[0][0].get("topic_slug", "") or ""))
            for t, s in scored:
                por_slug[str(t.get("topic_slug", "") or "")] = (dict(diag(sg, t)), s)
        else:
            d = dict(VAZIO)
            d.update(s1=0.0, s2=0.0, margem=0.0, razao=1.0, share_score=0.0, n_pos=0, n_cand=0, win_slug="")
        REC[chave][entry["id"]] = (d, por_slug)
        return m
    return spy


SUB2 = ("propagado-headings", "rotulo-decomposto", "titulo-nomeia-subtopico", "secao-nomeia-subtopico")
rows = []
for sig in CURSOS:
    gold = gold_rows(sig)
    for regime, mod in (("cru", sem_llm(sig)), ("produto", None)):
        REC[(sig, regime)] = {}
        rp.sub, orig = make_spy((sig, regime)), rp.sub
        try:
            r = rp.evaluate(sig, "com", new=False, taxmod=mod, escopo="produto")
        finally:
            rp.sub = orig
        entries = {e["id"]: e for e in r[6]}
        pred, proc = r[3], r[8]
        por_unid = {}
        for eid2 in proc:
            u = entries[eid2].get("computed_unit_slug", "")
            por_unid.setdefault(u, Counter())[pred.get(eid2, "")] += 1
        tam_unid = {u: sum(c.values()) for u, c in por_unid.items()}
        for eid, g in gold.items():
            if eid not in proc:
                rows.append(dict(curso=sig, regime=regime, entry_id=eid, fora_do_escopo=1))
                continue
            e = entries[eid]
            aceitos = ({g["gold_subunit"]} | set(filter(None, g.get("gold_subunits_extra", "").split(";")))
                       if g["gold_subunit"] else {""})
            p = pred.get(eid, "")
            reasons = [str(x) for x in (e.get("subunit_match_reasons") or [])]
            d, por_slug = REC[(sig, regime)][eid]
            d = dict(d)
            sub2 = [x for x in reasons if x in SUB2]
            if sub2:
                rota = "2a-" + sub2[0].split("-")[0]
            elif not p:
                mot = next((x.split()[0].split("(")[0] for x in reasons if not x.startswith("winner_score")), "?")
                rota = "vazio-" + mot
            else:
                rota = "1a"
            dp = por_slug.get(p, (dict(VAZIO), 0.0))
            u = e.get("computed_unit_slug", "")
            n_iguais = por_unid.get(u, {}).get(p, 0)
            d.update({f"pred_{k}": v for k, v in dp[0].items()})
            d.update(pred_score=dp[1], unidade=u, n_mat_unid=tam_unid.get(u, 0), n_iguais=n_iguais,
                     share_unid=n_iguais / max(1, tam_unid.get(u, 0)),
                     curso=sig, regime=regime, entry_id=eid, pred=p, fora_do_escopo=0,
                     aceito=int(p in aceitos), primario=int(p == g["gold_subunit"]),
                     confiante=int(revisar_de(e) not in ("duvida", "mudou")),
                     rota=rota, passada=("2a" if sub2 else "1a"),
                     reasons="|".join(reasons), vazio=int(not p))
            rows.append(d)
    print(f"{sig} ok", file=sys.stderr, flush=True)

cols = ["curso", "regime", "entry_id", "fora_do_escopo", "confiante", "aceito", "primario", "vazio",
        "rota", "passada", "pred", "win_slug", "s1", "s2", "margem", "razao", "share_score",
        "n_pos", "n_cand", "frase", "exact_hits", "max_tok_frase", "tok_frase_doador", "origem",
        "doador", "peso_doador", "n_topic_tokens", "n_overlap", "cobertura", "n_alias",
        "pred_frase", "pred_exact_hits", "pred_max_tok_frase", "pred_tok_frase_doador", "pred_origem",
        "pred_doador", "pred_peso_doador", "pred_n_topic_tokens", "pred_n_overlap", "pred_cobertura",
        "pred_n_alias", "pred_score",
        "unidade", "n_mat_unid", "n_iguais", "share_unid", "reasons"]
out = OUT / "fronteira_sinais_12-09.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
print(f"CSV: {out}  ({len(rows)} linhas)", file=sys.stderr)
