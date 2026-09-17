"""Reprocess REGISTRADO dos 8 originais com o gerador commitado (propagacao de vocabulario por headings na subunidade). Tripwire de
PRODUTO (voter so com cache; construtor do client explode). Pos-check por tutor: 0 resumo de codigo de hoje, votos nao crescem.
Diff por entry: subunidade, bloco, unidade, flag. Commit no tutor so se algo alem de `updated_at` mudou (caixa: sem ruido).
Uso: python reprocess_8_propagacao.py [--dry-run]"""
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
    return {e["id"]: (str(e.get("computed_subunit_slug") or ""), str(e.get("temporal_block_ref") or e.get("temporal_block_id") or ""),
                      str(e.get("computed_unit_slug") or ""), bool(e.get("temporal_block_flag")),
                      "propagado-headings" in (e.get("subunit_match_reasons") or [])) for e in es}


def votos(repo: Path) -> int:
    p = repo / "material_curation.json"
    return len((json.loads(p.read_text(encoding="utf-8")).get("votes") or {})) if p.exists() else 0


def resumos_hoje(repo: Path) -> int:
    p = repo / "code_curation.json"
    if not p.exists():
        return 0
    return sum(1 for v in (json.loads(p.read_text(encoding="utf-8")).get("entries") or {}).values()
               if str(v.get("generated_at")).startswith(date.today().isoformat()))


tot = Counter()
for name in TUTORES:
    repo = GH / name
    before, v0 = snap(repo), votos(repo)
    st = subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True).stdout.strip()
    print(f"== {name}: {len(before)} entries | votos {v0} | git sujo: {st.count(chr(10)) + 1 if st else 0}")
    if DRY:
        continue
    ra.reprocess(repo, [])
    after, v1 = snap(repo), votos(repo)
    assert resumos_hoje(repo) == 0, f"{name}: RESUMO DE CODIGO GERADO HOJE — tripwire falhou"
    assert v1 == v0, f"{name}: votos cresceram {v0} -> {v1} — tripwire falhou"
    sub = [(k, before[k][0][:24], after[k][0][:24]) for k in before if k in after and before[k][0] != after[k][0]]
    blo = [k for k in before if k in after and before[k][1] != after[k][1]]
    uni = [k for k in before if k in after and before[k][2] != after[k][2]]
    fl = (sum(v[3] for v in before.values()), sum(v[3] for v in after.values()))
    prop = sum(1 for v in after.values() if v[4])
    print(f"   subunidade mudou {len(sub)} {sub[:10]} | bloco mudou {len(blo)} {blo[:5]} | unidade mudou {len(uni)} {uni[:5]} | flagadas {fl[0]} -> {fl[1]} | propagados {prop}")
    tot["sub"] += len(sub); tot["blo"] += len(blo); tot["uni"] += len(uni); tot["prop"] += prop
    diff = subprocess.run(["git", "-C", str(repo), "diff", "--stat"], capture_output=True, text=True).stdout
    so_updated = (not sub and not blo and not uni and fl[0] == fl[1])
    if so_updated:
        subprocess.run(["git", "-C", str(repo), "checkout", "--", "."], check=True)   # so `updated_at`: sem ruido no historico
        print("   commit: pulado (so updated_at); working tree restaurado")
        continue
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    msg = (f"reprocess: propagacao de vocabulario por headings na subunidade (gerador {GER}) — subunidade mudou em {len(sub)}, "
           f"bloco {len(blo)}, unidade {len(uni)}, flagadas {fl[0]} -> {fl[1]}; 0 chamadas Gemini")
    r = subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    print("   commit:", "nada a commitar" if "nothing to commit" in out else (out[:100] or "ok"),
          "| HEAD", subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip())
if not DRY:
    print(f"TOTAL 8 tutores: subunidade mudou {tot['sub']} | bloco {tot['blo']} | unidade {tot['uni']} | propagados {tot['prop']}")
print("[fim]")
