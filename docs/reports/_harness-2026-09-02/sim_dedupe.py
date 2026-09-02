"""Simula scorer com dedupe de frases identicas (label/slug/alias) — READ-ONLY.

Frases distintas por normalizacao; se duas viram a mesma string, conta SO a de
maior fator (label 1.0 > alias 0.82 > slug 0.65). Compara placar atual vs
dedupe nos 4 casos da familia.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
sys.path.insert(0, str(ROOT))

import json

from src.builder.engine import _iter_content_taxonomy_topics
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
from src.builder.routing.resolver_apply import assemble_resolver_inputs
from src.builder.timeline.index import (
    UNIT_GENERIC_TOKENS,
    _collapse_ws,
    _matches_normalized_phrase,
    _normalize_match_text,
    _score_entry_against_taxonomy_topic,
)

CAMPOS = [
    ("markdown_headings_text", 4.4), ("title_text", 3.8), ("markdown_lead_text", 2.8),
    ("manual_tags_text", 3.0), ("markdown_text", 1.1), ("auto_tags_text", 0.22),
    ("legacy_tags_text", 0.15), ("raw_text", 0.9),
]


def score_dedupe(signals, topic):
    """Copia do scorer de producao com UMA mudanca: frases dedupe por norma."""
    label = _collapse_ws(str(topic.get("topic_label", "") or ""))
    topic_slug = _collapse_ws(str(topic.get("topic_slug", "") or ""))
    aliases = [str(a) for a in (topic.get("aliases", []) or []) if _collapse_ws(str(a))]
    if not label and not topic_slug and not aliases:
        return 0.0

    # frases por norma -> maior fator vence
    frases = {}
    if label:
        frases[_normalize_match_text(label)] = ("label", 1.0, label)
    for alias in aliases:
        an = _normalize_match_text(alias)
        if an and (an not in frases or frases[an][1] < 0.82):
            frases[an] = ("alias", 0.82, alias)
    if topic_slug:
        sp = topic_slug.replace("-", " ")
        sn = _normalize_match_text(sp)
        if sn and sn not in frases:
            frases[sn] = ("slug", 0.65, sp)
    frases.pop("", None)

    score = 0.0
    exact_hits = 0
    for texto_key, weight in CAMPOS:
        texto = signals.get(texto_key, "")
        for _, fator, frase in frases.values():
            if _matches_normalized_phrase(texto, frase, False):
                score += weight * fator
                exact_hits += 1

    _generic = set(topic.get("generic_tokens") or []) or UNIT_GENERIC_TOKENS
    _short = set(topic.get("short_vocab") or [])

    def _conta(token):
        return len(token) >= 4 or token in _short

    topic_tokens = {t for t in _normalize_match_text(label).split() if _conta(t) and t not in _generic}
    if topic_slug:
        topic_tokens |= {t for t in _normalize_match_text(topic_slug.replace("-", " ")).split()
                         if _conta(t) and t not in _generic}
    for alias in aliases:
        topic_tokens |= {t for t in _normalize_match_text(alias).split() if _conta(t) and t not in _generic}

    campos_forte = [("markdown_headings_text", True), ("title_text", True),
                    ("markdown_lead_text", False), ("manual_tags_text", True),
                    ("markdown_text", False), ("auto_tags_text", True),
                    ("legacy_tags_text", False), ("raw_text", True)]
    signal_tokens = {tok for c, forte in campos_forte for tok in signals.get(c, "").split()
                     if len(tok) >= 4 or (forte and tok in _short)}
    overlap = topic_tokens & signal_tokens
    if not topic_tokens:
        pass
    elif len(topic_tokens) == 1:
        if overlap:
            score += 0.9
    elif len(overlap) >= len(topic_tokens):
        score += 1.4 + (0.22 * len(overlap))
    elif len(overlap) >= 2:
        score += 0.9 + (0.18 * len(overlap))
    elif len(overlap) == 1:
        score += 0.25

    if signals.get("category_text", "") in {"listas", "gabaritos"} and overlap:
        score += 0.08
    if str(topic.get("kind", "") or "") == "subtopic":
        score += 0.04
    if exact_hits == 0 and score > 0.0:
        score *= 0.72
    if exact_hits == 0 and len(overlap) <= 1:
        score *= 0.68
    if signals.get("auto_tags_text", "") and exact_hits == 0 and len(overlap) <= 1:
        score *= 0.88
    if signals.get("legacy_tags_text", "") and exact_hits == 0:
        score *= 0.9
    return score


CASOS = [
    (r"C:\Users\Humberto\Documents\GitHub\Engenharia-Software-2-Tutor", "devops", "conceito-de-devops"),
    (r"C:\Users\Humberto\Documents\GitHub\Engenharia-Software-2-Tutor", "web", "cliente-servidor"),
    (r"C:\Users\Humberto\Documents\GitHub\Engenharia-Software-2-Tutor", "roteiro5-conteiners",
     "estudo-de-caso-integracao-e-implantacao-de-microsservicos"),
    (r"C:\Users\Humberto\Documents\GitHub\Engenharia-Software-2-Tutor", "roteiro5",
     "estudo-de-caso-integracao-e-implantacao-de-microsservicos"),
    (r"C:\Users\Humberto\Documents\GitHub\TCC-Tutor",
     "aula-08-maquinas-de-turing-como-processadoras-de-funcoes", "conjectura-de-church-turing"),
]

for repo_s, alvo, gold in CASOS:
    repo = Path(repo_s)
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    entry = next(e for e in manifest["entries"] if str(e.get("id")) == alvo)
    unidade = str(entry.get("computed_unit_slug") or "")
    cc = repo / "code_curation.json"
    code_curation = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {"entries": {}}
    _, signals, _ = assemble_resolver_inputs(repo, entry, code_curation)
    taxonomy = load_internal_content_taxonomy(repo) or {}
    topics = [t for t in _iter_content_taxonomy_topics(taxonomy) if t["unit_slug"] == unidade]
    atual = sorted(((t["topic_slug"], _score_entry_against_taxonomy_topic(signals, t)) for t in topics),
                   key=lambda x: -x[1])
    novo = sorted(((t["topic_slug"], score_dedupe(signals, t)) for t in topics), key=lambda x: -x[1])
    va, vn = atual[0][0], novo[0][0]
    print(f"\n== {alvo[:45]} (gold={gold})")
    print(f"   atual : {va:55} {'OK' if va == gold else 'ERRO'}")
    print(f"   dedupe: {vn:55} {'OK' if vn == gold else 'ERRO'}")
    for nome, plc in (("atual", atual), ("dedupe", novo)):
        top3 = "  ".join(f"{s}={v:.2f}" for s, v in plc[:3])
        print(f"     {nome:6} top3: {top3}")
