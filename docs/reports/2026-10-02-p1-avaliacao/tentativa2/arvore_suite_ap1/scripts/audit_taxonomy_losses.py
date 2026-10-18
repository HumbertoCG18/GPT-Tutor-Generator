"""Audita perda de topicos do PLANO DE ENSINO ate a taxonomia gerada.

Compara, por curso, os topicos numerados do teaching_plan (subjects.json) com os
labels que sobraram em build_content_taxonomy, e aponta o motivo de cada ausencia
(termo de `known_tools` que derrubou o topico, ou falha de captura no parser).

Uso:
    python scripts/audit_taxonomy_losses.py
"""
import sys, json, os, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.builder.extraction import content_taxonomy as ct
from src.builder.extraction.teaching_plan import (
    _parse_units_from_teaching_plan, _normalize_unit_slug, _topic_text)

REPOS = {'sistemas-operacionais':('SO','Sistemas-Operacionais-Tutor'),
         'metodos_formais':('MF','Metodos-Formais-Tutor'),
         'inteligencia-artificial':('IA','Inteligencia-Artifical-Tutor'),
         'engenharia-de-software-ii':('ES2','Engenharia-Software-2-Tutor'),
         'teoria-da-computabilidade-e-complexidade':('TCC','TCC-Tutor')}
GH = Path(r"C:/Users/Humberto/Documents/GitHub")
# captura "N.N[.N] Texto" em qualquer posicao da linha (pega itens colados)
ITEM = re.compile(r"(\d+(?:\.\d+)+)\.?\s+([^\d][^\n]*?)(?=\s+\d+(?:\.\d+)+\.?\s+|$)")

subs = json.loads((Path(os.getenv("APPDATA")) / "GPTTutorGenerator" / "subjects.json").read_text(encoding='utf-8'))
if isinstance(subs, dict): subs = subs.get("subjects", list(subs.values()))
out = []
for s in subs:
    info = REPOS.get(s.get('slug'))
    if not info: continue
    sig, repo_name = info
    repo = GH / repo_name
    plan = s.get('teaching_plan') or ''
    sem_path = repo / "course/.semantic_profile.generated.json"
    sem = json.loads(sem_path.read_text(encoding='utf-8')) if sem_path.exists() else None

    esperado = []
    for raw in plan.splitlines():
        line = ct._collapse_ws(raw.replace('*','').replace('\u200b',''))
        if not re.match(r"^\s*[-\u2022]?\s*\d+(?:\.\d+)+", line): continue
        for code, txt in ITEM.findall(line):
            txt = txt.strip(' .')
            if len(txt) >= 4: esperado.append((code, txt))

    tax = ct.build_content_taxonomy(plan, "", "", semantic_profile=sem,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        topic_text=_topic_text, normalize_unit_slug=_normalize_unit_slug)
    labels_norm = [ct._normalize_match_text(t['label']) for u in tax['units'] for t in u['topics']]

    perdidos = []
    for code, txt in esperado:
        alvo = ct._normalize_match_text(txt)
        if not any(alvo in lab or lab in alvo for lab in labels_norm):
            perdidos.append((code, txt))
    out.append(f"== {sig}: {len(esperado)} topicos no plano | {len(perdidos)} AUSENTES da taxonomia")
    for code, txt in perdidos:
        norm = ct._normalize_match_text(txt)
        def _hits(tool):
            tn = ct._normalize_match_text(tool)
            if not tn:
                return False
            return tn in norm.split() if len(tn) < 4 else tn in norm
        culprit = next((t for t in ((sem or {}).get('known_tools') or []) if _hits(t)), '')
        motivo = f"known_tools['{culprit}']" if culprit else "nao capturado pelo parser"
        out.append(f"     {code:8} {txt[:58]:60} <- {motivo}")
print(chr(10).join(out))
