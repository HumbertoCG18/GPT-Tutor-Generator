"""Cópias redigidas para divulgação (etapa 3, 29/09). Os originais NÃO são tocados (sha256 conferido antes e depois).

Texto excedente dentro de campo permitido do catálogo (turmas, semestre, modalidade, nomes de professores depois do
nome da disciplina) é cortado em todo valor de texto, inclusive na forma escapada usada como padrão de busca.
Uso: python redige_divulgacao.py
"""
import hashlib
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
E2 = AQUI.parents[1] / "validacao_externa_etapa2_29-09/aquisicao"
ALVOS = {E2 / "catalogo.json": AQUI / "catalogo_divulgacao.json",
         E2 / "triagem.json": AQUI / "triagem_divulgacao.json",
         AQUI.parent / "exposicao/exposicao_local.json": AQUI.parent / "exposicao/exposicao_local_divulgacao.json"}
EXCEDENTE = re.compile(r"\s+-\s+(?=Turmas?\b|\d{4}/\d|Modalidade\b|Profs?\b)")
MARCA = " [texto excedente omitido]"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def trocas(catalogo):
    """({original: redigido}, [excedentes]); inclui a forma escapada (padrão de busca)."""
    t, excedentes = {}, []
    for c in catalogo["cursos"]:
        partes = EXCEDENTE.split(c["nome"], 1)
        if len(partes) == 2:
            excedentes.append(partes[1])
            t[c["nome"]] = partes[0] + MARCA
            t[re.escape(c["nome"])] = re.escape(partes[0]) + MARCA
    return dict(sorted(t.items(), key=lambda kv: -len(kv[0]))), excedentes


def redige(o, t):
    if isinstance(o, dict):
        return {k: redige(v, t) for k, v in o.items()}
    if isinstance(o, list):
        return [redige(x, t) for x in o]
    if isinstance(o, str):
        for velho, novo in t.items():
            o = o.replace(velho, novo)
    return o


def textos(o):
    if isinstance(o, dict):
        return [t for v in list(o.values()) + list(o) for t in textos(v)]
    if isinstance(o, list):
        return [t for x in o for t in textos(x)]
    return [o] if isinstance(o, str) else []


def main():
    antes = {p: sha(p) for p in ALVOS}
    t, excedentes = trocas(json.loads((E2 / "catalogo.json").read_text(encoding="utf-8")))
    for orig, dest in ALVOS.items():
        red = redige(json.loads(orig.read_text(encoding="utf-8")), t)
        texto = json.dumps({"divulgacao": {"original": orig.relative_to(AQUI.parents[2]).as_posix(), "original_sha256": antes[orig],
                                           "regra": "texto após ' - Turma(s)|AAAA/S|Modalidade|Prof(s)' no nome cortado"},
                            "conteudo": red}, ensure_ascii=False, indent=1) + "\n"
        assert not any(x in v or re.escape(x) in v for v in textos(red) for x in excedentes), dest
        dest.write_text(texto, encoding="utf-8", newline="\n")
    assert antes == {p: sha(p) for p in ALVOS}, "original alterado"
    print(f"{len(excedentes)} nomes com excedente; {len(ALVOS)} cópias redigidas; originais intactos")


if __name__ == "__main__":
    main()
