"""Roda um comando Python no ambiente controlado da medição (comum.ambiente_controlado + -B + pycache vazio isolado) e
grava o log. Uso: python roda_controlado.py <log> <script> [args...]. Não imprime valores do ambiente."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "wad5_25-09"))
import comum as K  # noqa: E402

PYCACHE = AQUI.parents[4] / ".frzero/wad5_avaliacao_26-09/pycache_vazio"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
log, args = Path(sys.argv[1]), sys.argv[2:]
PYCACHE.mkdir(parents=True, exist_ok=True)
cmd = [sys.executable, "-B", "-X", f"pycache_prefix={PYCACHE}", *args]
t0 = time.time()
r = subprocess.run(cmd, env=K.ambiente_controlado(os.environ), capture_output=True, text=True, encoding="utf-8", errors="replace")
cab = {"comando": cmd, "saida": r.returncode, "segundos": round(time.time() - t0, 1), "ambiente": K.descritor_ambiente(K.ambiente_controlado(os.environ)),
       "pycache_vazio_depois": not any(PYCACHE.rglob("*"))}
log.write_text(json.dumps(cab, ensure_ascii=False, indent=1) + "\n--- stdout\n" + r.stdout + "\n--- stderr\n" + r.stderr, encoding="utf-8")
print(r.stdout[-4000:], r.stderr[-3000:], f"\n[saida={r.returncode}, {cab['segundos']} s, log={log.name}]", sep="")
sys.exit(r.returncode)
