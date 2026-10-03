"""Manifesto da etapa 3: sha256 de cada arquivo desta pasta e das entradas preservadas. Uso: python manifesto_etapa3.py"""
import hashlib
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = next(p for p in AQUI.parents if (p / ".git").exists())
SO_LOCAL = {"exposicao/exposicao_local.json": "nome de curso com texto excedente (nomes de professores); vai a cópia redigida"}
ENTRADAS = ["docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa2_29-09/manifesto_etapa2.json",
            "docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa2_29-09/aquisicao/manifesto_aquisicao.json",
            "docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa2_29-09/aquisicao/inventario_downloads.json",
            "docs/reports/_harness-2026-09-04/c1-3/validacao_externa_etapa2_29-09/aquisicao/fontes_congeladas.json",
            "docs/reports/_harness-2026-09-04/c1-3/validacao_externa_29-09/manifesto_preparacao.json"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    arquivos = {p.relative_to(AQUI).as_posix(): sha(p) for p in sorted(AQUI.rglob("*"))
                if p.is_file() and p.name != "manifesto_etapa3.json" and "__pycache__" not in p.parts}
    man = {"esquema": "manifesto-etapa3-1", "base_evidencia": "bf46d51fc80d1e7dcc62c08cccd0399c056bcbe1",
           "entradas_preservadas": {k: sha(REPO / k) for k in ENTRADAS}, "arquivos": arquivos,
           "fora_da_entrega": SO_LOCAL}
    (AQUI / "manifesto_etapa3.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(arquivos), "arquivos;", len(SO_LOCAL), "só local")


if __name__ == "__main__":
    main()
