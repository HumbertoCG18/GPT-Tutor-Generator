"""Manifesto das correções pós-revisão: sha256 de cada arquivo desta pasta. Uso: python manifesto_correcoes_etapa3.py"""
import hashlib
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SO_LOCAL = {"exposicao/exposicao_local_v2.json": "nome de curso com texto excedente (nomes de professores); vai a cópia redigida"}


def main():
    arquivos = {p.relative_to(AQUI).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(AQUI.rglob("*"))
                if p.is_file() and p.name != "manifesto_correcoes_etapa3.json" and "__pycache__" not in p.parts}
    (AQUI / "manifesto_correcoes_etapa3.json").write_text(json.dumps(
        {"esquema": "manifesto-correcoes-etapa3-1", "arquivos": arquivos, "fora_da_divulgacao": SO_LOCAL},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(arquivos), "arquivos")


if __name__ == "__main__":
    main()
