"""Diagnóstico da parada da avaliação (26/09): bytes do disco x blob do índice. NÃO lê conteúdo da régua.

- código histórico (não é régua): compara blob dos bytes do disco, e sem CRLF, com o blob do índice;
- régua: só metadados (tamanho no disco x tamanho do blob no object store; git status).
"""
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATA = AQUI.parents[4]
sys.path.insert(0, str(AQUI.parent / "wad5_25-09"))
import comum as K  # noqa: E402

os.chdir(DATA)
cong = K.carrega_json_estrito(".frzero/wad5_25-09/congelamento.json")
desc = cong["normativo"]["avaliacao"]
CRLF, LF = b"\r\n", b"\n"
print("core.autocrlf =", subprocess.run(["git", "config", "core.autocrlf"], capture_output=True, text=True).stdout.strip())
print("== código histórico (não é régua): disco x índice")
for caminho, blob in desc["codigo_historico_blob"].items():
    b = Path(caminho).read_bytes()
    st = subprocess.run(["git", "status", "--porcelain", "--", caminho], capture_output=True, text=True).stdout.strip()
    igual, n_crlf, igual_lf = K.blob_git(b) == blob, b.count(CRLF), K.blob_git(b.replace(CRLF, LF)) == blob
    print(f"  {Path(caminho).name:30} bytes==blob: {igual} | CRLF no disco: {n_crlf} | sem CRLF==blob: {igual_lf} | "
          f"git status: {st or 'limpo'}")
print("== régua: só metadados (nenhum conteúdo lido)")
difs, total = [], 0
for papel, m in desc["arquivos"].items():
    for s, it in m.items():
        total += 1
        tam_disco = os.stat(it["caminho"]).st_size
        tam_blob = int(subprocess.run(["git", "cat-file", "-s", it["blob_git"]], capture_output=True, text=True).stdout.strip())
        if tam_disco != tam_blob:
            difs.append(f"{papel}/{s}:+{tam_disco - tam_blob}")
print(f"  tamanho no disco != tamanho do blob: {len(difs)} de {total}")
print("  ", difs)
st = subprocess.run(["git", "status", "--porcelain", "--",
                     *[it["caminho"] for m in desc["arquivos"].values() for it in m.values()]],
                    capture_output=True, text=True).stdout.strip()
print("  git status dos arquivos da régua:", st or "todos limpos (conteúdo normalizado = índice)")
