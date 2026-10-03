"""Cópia redigida da exposição v2, com as funções de ../../validacao_externa_etapa3_29-09/registro/redige_divulgacao.py
(mesma regra; o módulo da etapa 3 é só importado, não alterado). O original fica só local. Uso: python redige_divulgacao_v2.py"""
import hashlib
import importlib.util
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("redige_e3", AQUI.parents[1] / "validacao_externa_etapa3_29-09/registro/redige_divulgacao.py")
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
ORIGINAL = AQUI.parent / "exposicao/exposicao_local_v2.json"
DESTINO = AQUI.parent / "exposicao/exposicao_local_v2_divulgacao.json"


def main():
    antes = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    t, excedentes = R.trocas(json.loads((R.E2 / "catalogo.json").read_text(encoding="utf-8")))
    red = R.redige(json.loads(ORIGINAL.read_text(encoding="utf-8")), t)
    assert not any(x in v or R.re.escape(x) in v for v in R.textos(red) for x in excedentes)
    DESTINO.write_text(json.dumps({"divulgacao": {"original": ORIGINAL.relative_to(AQUI.parents[2]).as_posix(), "original_sha256": antes,
                                                  "regra": "a de redige_divulgacao.py da etapa 3"}, "conteudo": red},
                                  ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    assert antes == hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    print(f"{len(excedentes)} nomes com excedente; cópia redigida gravada; original intacto")


if __name__ == "__main__":
    main()
