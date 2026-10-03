"""Gera o exemplo SINTÉTICO do pacote cego para a revisão: monta e audita numa pasta temporária FORA do repositório (o
leitor recusa fontes dentro dele) e copia fonte, pacote e resultado da auditoria para `exemplo_sintetico/`. Nenhum curso
real. Uso: python gera_exemplo_sintetico.py <pasta temporária fora do repo>"""
import json
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import gera_pacote_cego as G  # noqa: E402
import test_pacote_cego as T  # noqa: E402

tmp = Path(sys.argv[1]).resolve()
destino = AQUI / "exemplo_sintetico"
if destino.exists() or tmp.exists():
    sys.exit("destino ou pasta temporária já existe: não sobrescrevo")
fonte = T.fixture(tmp / "fonte")
G.monta(fonte, tmp / "pacote")
prob = G.audita(fonte, tmp / "pacote")
shutil.copytree(tmp, destino)
(destino / "resultado_auditoria.json").write_text(json.dumps({"problemas": prob, "aprovado": not prob,
                                                              "nota": "auditado na pasta temporária de origem"},
                                                             ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("AUDITORIA", "APROVADA" if not prob else "REPROVADA", prob)
