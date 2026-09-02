"""Placar por candidato de subunidade — ES2 devops. READ-ONLY."""
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
    _matches_normalized_phrase,
    _normalize_match_text,
    _score_entry_against_taxonomy_topic,
)

REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Users\Humberto\Documents\GitHub\Engenharia-Software-2-Tutor")
ALVO = sys.argv[2] if len(sys.argv) > 2 else "devops"

manifest = json.loads((REPO / "manifest.json").read_text(encoding="utf-8"))
entry = next(e for e in manifest["entries"] if str(e.get("id")) == ALVO)
UNIDADE = sys.argv[3] if len(sys.argv) > 3 else str(entry.get("computed_unit_slug") or "")
cc = REPO / "code_curation.json"
code_curation = json.loads(cc.read_text(encoding="utf-8")) if cc.exists() else {"entries": {}}
_, signals, _ = assemble_resolver_inputs(REPO, entry, code_curation)

taxonomy = load_internal_content_taxonomy(REPO) or {}
topics = [t for t in _iter_content_taxonomy_topics(taxonomy) if t["unit_slug"] == UNIDADE]

print(f"== headings ({len(signals.get('markdown_headings_text',''))} chars, na ordem) ==")
print(signals.get("markdown_headings_text", ""))
print()
print(f"== placar ({len(topics)} candidatos da {UNIDADE}) ==")
placar = sorted(
    ((t, _score_entry_against_taxonomy_topic(signals, t)) for t in topics),
    key=lambda x: -x[1],
)
for t, s in placar:
    print(f"  {s:7.3f}  {t['topic_slug']:42} {t['topic_label'][:50]}")

print()
print("== detalhe dos 2 primeiros: quais campos casam frase (label/slug/alias) ==")
CAMPOS = [
    ("markdown_headings_text", 4.4), ("title_text", 3.8), ("markdown_lead_text", 2.8),
    ("manual_tags_text", 3.0), ("markdown_text", 1.1), ("auto_tags_text", 0.22),
    ("legacy_tags_text", 0.15), ("raw_text", 0.9),
]
for t, s in placar[:2]:
    label = t["topic_label"]
    slug_phrase = t["topic_slug"].replace("-", " ")
    print(f"\n-- {t['topic_slug']} (score {s:.3f}) label={label!r}")
    for campo, w in CAMPOS:
        texto = signals.get(campo, "")
        hits = []
        if label and _matches_normalized_phrase(texto, label, False):
            hits.append(f"label(+{w})")
        if slug_phrase and _matches_normalized_phrase(texto, slug_phrase, False):
            hits.append(f"slug(+{w*0.65:.2f})")
        for alias in t.get("aliases") or []:
            an = _normalize_match_text(alias)
            if an and _matches_normalized_phrase(texto, an, False):
                hits.append(f"alias:{alias[:20]}(+{w*0.82:.2f})")
        if hits:
            print(f"    {campo:24} {' '.join(hits)}")
    generic = set(t.get("generic_tokens") or [])
    short = set(t.get("short_vocab") or [])
    tt = {tok for tok in _normalize_match_text(label).split()
          if (len(tok) >= 4 or tok in short) and tok not in generic}
    tt |= {tok for tok in _normalize_match_text(slug_phrase).split()
           if (len(tok) >= 4 or tok in short) and tok not in generic}
    for alias in t.get("aliases") or []:
        tt |= {tok for tok in _normalize_match_text(alias).split()
               if (len(tok) >= 4 or tok in short) and tok not in generic}
    campos_forte = [("markdown_headings_text", True), ("title_text", True),
                    ("markdown_lead_text", False), ("manual_tags_text", True),
                    ("markdown_text", False), ("auto_tags_text", True),
                    ("legacy_tags_text", False), ("raw_text", True)]
    st = {tok for texto, forte in ((signals.get(c, ""), f) for c, f in campos_forte)
          for tok in texto.split() if len(tok) >= 4 or (forte and tok in short)}
    print(f"    topic_tokens={sorted(tt)}")
    print(f"    overlap     ={sorted(tt & st)}")
