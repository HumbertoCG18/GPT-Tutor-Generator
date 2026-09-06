"""Reprocess REGISTRADO dos 8 originais com o gerador commitado (secao do Moodle decide onde nada decidiu, S1b, 2a passada). Tripwire de PRODUTO
(voter so com cache; construtor do client explode). Pos-check por tutor: 0 resumo de codigo de hoje, votos nao crescem, bloco/unidade/
unidade NAO mudam; a subunidade pode (listada por entry). Commit no tutor se algo alem de `updated_at` mudou. Uso: reprocess_8_secao.py [--dry-run]"""
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
                      str(e.get("computed_unit_slug") or ""), bool(e.get("temporal_block_flag")), str(e.get("revisar") or "")) for e in es}


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
    print(f"== {name}: {len(before)} entries | votos {v0} | git sujo: {st.count(chr(10)) + 1 if st else 0}", flush=True)
    if DRY:
        continue
    ra.reprocess(repo, [])
    after, v1 = snap(repo), votos(repo)
    assert resumos_hoje(repo) == 0, f"{name}: RESUMO DE CODIGO GERADO HOJE — tripwire falhou"
    assert v1 == v0, f"{name}: votos cresceram {v0} -> {v1} — tripwire falhou"
    sub = [k for k in before if k in after and before[k][0] != after[k][0]]
    blo = [k for k in before if k in after and before[k][1] != after[k][1]]
    uni = [k for k in before if k in after and before[k][2] != after[k][2]]
    rev = Counter((before[k][4], after[k][4]) for k in before if k in after and before[k][4] != after[k][4])
    fila0 = sum(1 for v in before.values() if v[4] in ("duvida", "llm", "mudou"))
    fila1 = sum(1 for v in after.values() if v[4] in ("duvida", "llm", "mudou"))
    print(f"   revisar mudou {sum(rev.values())} {dict(rev)} | fila {fila0} -> {fila1} | sub mudou {len(sub)} {sub[:5]} | bloco {len(blo)} {blo[:5]} | unidade {len(uni)} {uni[:5]}", flush=True)
    assert not blo and not uni, f"{name}: bloco/unidade mudaram num reprocess que so devia mudar a subunidade"
    for k in sub:
        print(f"      sub: {k[:44]:44} {before[k][0][-30:] or '-':30} -> {after[k][0][-30:] or '-'}", flush=True)
    tot["rev"] += sum(rev.values()); tot["fila0"] += fila0; tot["fila1"] += fila1; tot["sub"] += len(sub)
    if not rev and not sub:
        subprocess.run(["git", "-C", str(repo), "checkout", "--", "."], check=True)   # so `updated_at`: sem ruido no historico
        print("   commit: pulado (so updated_at); working tree restaurado")
        continue
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    msg = (f"reprocess: secao do Moodle decide subunidade indecisa (gerador {GER}) — subunidade mudou em {len(sub)}, revisar em {sum(rev.values())}, "
           f"fila {fila0} -> {fila1}; bloco/unidade iguais; 0 chamadas Gemini")
    r = subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    print("   commit:", "nada a commitar" if "nothing to commit" in out else (out[:100] or "ok"),
          "| HEAD", subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(), flush=True)
if not DRY:
    print(f"TOTAL 8 tutores: subunidade mudou {tot['sub']} | revisar mudou {tot['rev']} | fila {tot['fila0']} -> {tot['fila1']}")
print("[fim]")
