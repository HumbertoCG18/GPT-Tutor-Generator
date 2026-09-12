"""DESCONTAMINA o GLOSSARY dos 4 cursos cujo sidecar era "proposto-claude a partir de subunit_gt_<curso>".

O sidecar antigo NAO e apagado: vai para `course/.glossary_curation.gold.json` com um cabecalho dizendo o que e, para
poder ser restaurado com um comando. No lugar entra o sidecar gerado so de fontes do professor
(`gera_sidecar_professor.py`: SARC + secao do Moodle + titulo/headings dos materiais da secao).

Medido pela rota real antes de aplicar (`mede_sidecar_professor.log`, 6 cursos, tripwire):
  ATUAL (contaminado) sub 201/233 · conf-err 16 · fila 88
  LIMPO (sem sidecar) sub 135/233 · conf-err 65 · fila 100
  PROF  (professor)   sub 146/233 · conf-err 65 · fila 93
Por curso, LIMPO -> PROF: SO 9->10 · IA 4->4 · ES2 5->15 · TCC 8->8 · MF 51->52 · CG 58->57.
MF e CG nao sao tocados: nunca tiveram sidecar curado, e neles o gerado da +1 e -1 (mudanca sem motivo).

Uso: descontamina_glossary.py [--aplicar]
"""
import json
import os
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
ALVO = {"SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
        "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor"}
APLICAR = "--aplicar" in sys.argv
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.path.insert(0, str(GEN / "docs/reports/_harness-2026-09-04/c1-3"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["TUTOR_REPOS_ORIG"] = str(GH)
os.environ["TUTOR_NO_VOCAB_COMPILE"] = "1"
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado (descontamina_glossary)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402
from gera_sidecar_professor import gera  # noqa: E402

for sig, repo in ALVO.items():
    root = GH / repo
    cur = root / "course/.glossary_curation.json"
    arq = root / "course/.glossary_curation.gold.json"
    novo, st = gera(root)   # gerado ANTES de trocar (a funcao ja ignora os sinonimos do sidecar atual)
    antigo = json.loads(cur.read_text(encoding="utf-8")) if cur.exists() else {}
    n_antigo = len([k for k in antigo if not k.startswith("_")])
    n_novo = len([k for k in novo if not k.startswith("_")])
    print(f"{sig:4} curado {n_antigo} topicos -> professor {n_novo} topicos / {st['sinonimos']} sinonimos")
    if not APLICAR:
        continue
    antigo["_ARQUIVADO"] = (
        "ARQUIVADO em 2026-09-07. Este sidecar foi derivado do GOLD ('proposto-claude a partir de subunit_gt'), o que "
        "invalidava a regua: o motor era medido contra o mesmo gold que originou seu vocabulario. Ablacao pela rota "
        "real: subunidade 86/93 -> 26/93 nos 4 cursos ao remove-lo. NAO restaurar sem decidir explicitamente que o "
        "numero medido passa a ser reportado como contaminado. Substituido por `.glossary_curation.json` gerado de "
        "SARC + Moodle + headings (`c1-3/gera_sidecar_professor.py`).")
    arq.write_text(json.dumps(antigo, ensure_ascii=False, indent=2), encoding="utf-8")
    cur.write_text(json.dumps(novo, ensure_ascii=False, indent=2), encoding="utf-8")
    ra.reprocess(root, [])
    (root / "manifest.json.bak").unlink(missing_ok=True)
    print(f"     aplicado e reprocessado; antigo em {arq.name}")
