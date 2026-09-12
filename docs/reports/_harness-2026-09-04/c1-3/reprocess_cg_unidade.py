"""Reprocess REGISTRADO do CG original (curadoria de unidade: pinos nos blocos 06/08/15 + glossario manual + higiene de secao no
gerador). Tripwire de PRODUTO: o voter e construido (cache de votos vale) mas `get_gemini_client` devolve None (cache miss = voto
pulado, contado em no_key) e o construtor do client explode: NENHUMA chamada possivel. Pos-check: 0 resumo de codigo de hoje,
votos no material_curation.json nao crescem. Diff por entry: unidade, bloco, metodo, flag, subunidade. Commit no tutor.
Uso: python reprocess_cg_unidade.py [--dry-run]"""
import json
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
GH = GEN.parent
CG = GH / "Computacao-Grafica-Tutor"
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

GER = subprocess.run(["git", "-C", str(GEN), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", str(GEN), "status", "--short", "--", "src", "tests"], capture_output=True, text=True).stdout.strip()
assert not dirty, f"gerador com src/tests nao commitados:\n{dirty}"


def snap(repo: Path) -> dict:
    es = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))["entries"]
    return {e["id"]: {"unit": str(e.get("computed_unit_slug") or ""), "bloco": str(e.get("temporal_block_ref") or e.get("temporal_block_id") or ""),
                      "met": str(e.get("temporal_block_method") or ""), "flag": bool(e.get("temporal_block_flag")),
                      "sub": str(e.get("computed_subunit_slug") or ""), "band": str(e.get("temporal_block_band") or "")} for e in es}


def votos(repo: Path) -> int:
    p = repo / "material_curation.json"
    return len((json.loads(p.read_text(encoding="utf-8")).get("votes") or {})) if p.exists() else 0


def resumos_hoje(repo: Path) -> int:
    p = repo / "code_curation.json"
    if not p.exists():
        return 0
    return sum(1 for v in (json.loads(p.read_text(encoding="utf-8")).get("entries") or {}).values()
               if str(v.get("generated_at")).startswith(date.today().isoformat()))


before, v0 = snap(CG), votos(CG)
print(f"== CG antes: {len(before)} entries | votos em cache {v0} | flagadas {sum(v['flag'] for v in before.values())} | git sujo: "
      + subprocess.run(["git", "-C", str(CG), "status", "--short"], capture_output=True, text=True).stdout.strip().replace("\n", " ; ")[:200])
if DRY:
    sys.exit(0)
ra.reprocess(CG, [])
after, v1 = snap(CG), votos(CG)
assert resumos_hoje(CG) == 0, "RESUMO DE CODIGO GERADO HOJE — tripwire falhou"
assert v1 == v0, f"votos cresceram {v0} -> {v1} — tripwire falhou"
unit_ch = [(k, before[k]["unit"][8:24], after[k]["unit"][8:24]) for k in before if k in after and before[k]["unit"] != after[k]["unit"]]
bloco_ch = [(k, before[k]["bloco"][:8], after[k]["bloco"][:8]) for k in before if k in after and before[k]["bloco"] != after[k]["bloco"]]
met_ch = Counter(f"{before[k]['met']}->{after[k]['met']}" for k in before if k in after and before[k]["met"] != after[k]["met"])
sub_ch = [(k, before[k]["sub"][:22], after[k]["sub"][:22]) for k in before if k in after and before[k]["sub"] != after[k]["sub"]]
fl = (sum(v["flag"] for v in before.values()), sum(v["flag"] for v in after.values()))
print(f"   unidade mudou {len(unit_ch)}: {unit_ch}")
print(f"   bloco mudou {len(bloco_ch)}: {bloco_ch}")
print(f"   metodo mudou {dict(met_ch)} | flagadas {fl[0]} -> {fl[1]} | subunidade mudou {len(sub_ch)}: {sub_ch[:12]}")
print(f"   votos {v0} -> {v1} | resumos de codigo hoje {resumos_hoje(CG)}")
subprocess.run(["git", "-C", str(CG), "add", "-A"], check=True)
msg = (f"reprocess: curadoria de unidade — pinos bloco-06 u04 / 08 u03 / 15 u07 + glossario manual (texturas, morfologia); gerador {GER} "
       f"(higiene: sinonimo compilado = secao do Moodle nao vira alias) — unidade mudou em {len(unit_ch)}, bloco em {len(bloco_ch)}, "
       f"flagadas {fl[0]} -> {fl[1]}; 0 chamadas Gemini")
r = subprocess.run(["git", "-C", str(CG), "commit", "-q", "-m", msg], capture_output=True, text=True)
out = (r.stdout + r.stderr).strip()
print("   commit:", "nada a commitar" if "nothing to commit" in out else (out[:120] or "ok"),
      "| HEAD", subprocess.run(["git", "-C", str(CG), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip())
