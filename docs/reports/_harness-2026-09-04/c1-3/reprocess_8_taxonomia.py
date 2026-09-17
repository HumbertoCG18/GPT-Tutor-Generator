"""Reprocess REGISTRADO dos 8 originais com o gerador commitado (07/09): teto de 2 digitos no code do plano (3effde1),
formatacao padronizada de unidade e topico (ba96743) e rotulo de leitura no FILE_MAP (53b1659).
Tripwire de PRODUTO: Gemini bloqueado (voter so com cache; construtor explode). Pos-check por tutor: 0 resumo de codigo
de hoje, votos NAO crescem. Commit no tutor quando algo alem de `updated_at` muda. Uso: reprocess_8_taxonomia.py [--dry-run]
"""
import json
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
sys.path.insert(0, str(GEN))
sys.path.insert(0, str(GEN / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DRY = "--dry-run" in sys.argv
import src.builder.runtime.gemini_client as _gc  # noqa: E402
_gc.get_gemini_client = lambda config=None: None


def _bloqueado(*a, **k):
    raise RuntimeError("Gemini bloqueado neste reprocess (tripwire de produto)")


_gc.GeminiClient.__init__ = _bloqueado
import reprocess_assignments as ra  # noqa: E402

TUTORES = ["Metodos-Formais-Tutor", "Sistemas-Operacionais-Tutor", "Inteligencia-Artifical-Tutor", "Engenharia-Software-2-Tutor",
           "TCC-Tutor", "Laboratorio-de-Redes-Tutor", "Fundamentos-de-Redes-Tutor", "Computacao-Grafica-Tutor"]
GER = subprocess.run(["git", "-C", str(GEN), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(GEN), "status", "--short", "--", "src", "tests"], capture_output=True, text=True).stdout.strip()
assert not dirty, f"gerador com src/tests nao commitados:\n{dirty}"


def snap(repo: Path) -> dict:
    es = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    return {e["id"]: (str(e.get("computed_subunit_slug") or ""), str(e.get("temporal_block_id") or ""),
                      str(e.get("computed_unit_slug") or ""), str(e.get("revisar") or "")) for e in es}


def votos(repo: Path) -> int:
    p = repo / "material_curation.json"
    return len((json.loads(p.read_text(encoding="utf-8")).get("votes") or {})) if p.exists() else 0


def resumos_hoje(repo: Path) -> int:
    p = repo / "code_curation.json"
    if not p.exists():
        return 0
    return sum(1 for v in (json.loads(p.read_text(encoding="utf-8")).get("entries") or {}).values()
               if str(v.get("generated_at")).startswith(date.today().isoformat()))


def topicos(repo: Path) -> int:
    p = repo / "course/.content_taxonomy.json"
    if not p.exists():
        return 0
    return sum(len(u.get("topics") or []) for u in json.loads(p.read_text(encoding="utf-8")).get("units") or [])


tot = Counter()
for name in TUTORES:
    repo = GH / name
    before, v0, t0 = snap(repo), votos(repo), topicos(repo)
    st = subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True).stdout.strip()
    print(f"== {name}: {len(before)} entries · {t0} topicos · votos {v0} · git sujo: {st.count(chr(10)) + 1 if st else 0}", flush=True)
    if DRY:
        continue
    ra.reprocess(repo, [])
    after, v1, t1 = snap(repo), votos(repo), topicos(repo)
    assert resumos_hoje(repo) == 0, f"{name}: RESUMO DE CODIGO GERADO HOJE — tripwire falhou"
    assert v1 == v0, f"{name}: votos cresceram {v0} -> {v1} — tripwire falhou"
    sub = [k for k in before if k in after and before[k][0] != after[k][0]]
    blo = [k for k in before if k in after and before[k][1] != after[k][1]]
    uni = [k for k in before if k in after and before[k][2] != after[k][2]]
    rev = Counter((before[k][3], after[k][3]) for k in before if k in after and before[k][3] != after[k][3])
    print(f"   topicos {t0} -> {t1} | sub mudou {len(sub)} | bloco {len(blo)} | unidade {len(uni)} | revisar mudou {sum(rev.values())} {dict(rev)}", flush=True)
    for k in blo:
        print(f"      bloco: {k[:44]:44} {before[k][1][-12:] or '-':12} -> {after[k][1][-12:] or '-'}", flush=True)
    for k in uni:
        print(f"      unidade: {k[:44]:44} {before[k][2][-30:] or '-':30} -> {after[k][2][-30:] or '-'}", flush=True)
    for k in sub:
        print(f"      sub: {k[:44]:44} {before[k][0][-30:] or '-':30} -> {after[k][0][-30:] or '-'}", flush=True)
    tot["sub"] += len(sub); tot["blo"] += len(blo); tot["uni"] += len(uni); tot["top0"] += t0; tot["top1"] += t1
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    msg = (f"reprocess: taxonomia padronizada (gerador {GER}) — code do plano com teto de 2 digitos, enfase markdown fora "
           f"dos labels, rotulo de leitura '03 - Nome' e '3.5 - Nome' no FILE_MAP; topicos {t0} -> {t1}, "
           f"subunidade mudou {len(sub)}, unidade {len(uni)}, bloco {len(blo)}; 0 chamadas Gemini")
    r = subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    print("   commit:", "nada a commitar" if "nothing to commit" in out else (out[:90] or "ok"), "| HEAD", head, flush=True)
if not DRY:
    print(f"TOTAL 8 tutores: topicos {tot['top0']} -> {tot['top1']} · subunidade {tot['sub']} · unidade {tot['uni']} · bloco {tot['blo']}")
print("[fim]")
