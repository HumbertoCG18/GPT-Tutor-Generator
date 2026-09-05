"""gold_score.py — amostragem do gold (canário). SÓ amostra; NÃO pontua.

A pontuação tem um dono único: `scripts/eval_ground_truth.py` (resolve_temporal_block
+ canonicaliza os 2 lados pra bloco-NN; credita os movers da âncora e os pins). Este
arquivo só monta a folha de rotulagem cega, downstream da decisão de rotular.

build_sample(): folha COMPLETA — toda entry do manifest (N=50 no IA cabe bem; mais
limpo que estratificar e nunca deixa unidade de fora). SEM vazar computed_block_id
(anti-circular). Coluna `nota` pré-marca o que merece atenção: suspeitos do pendencias,
clustering escondido pelo bloco-06, e os pares de VERSÃO (mesma aula, dois arquivos —
decisão de dedup é humana, a folha só sinaliza). Colunas `id`/`true_block_id` batem com
o que o eval_ground_truth lê, então a versão rotulada alimenta o scorer direto.

NÃO gera o xlsx de rotulagem (decisão tua; o template já existe).

Uso:
    python scripts/gold_score.py sample --repo C:\\...\\Inteligencia-Artifical-Tutor --out gold_sample_IA.csv
    # depois de rotular true_block_id (em bloco-NN):
    python scripts/eval_ground_truth.py C:\\...\\Inteligencia-Artifical-Tutor gold_sample_IA.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


# --------------------------------------------------------------------------- leitura

def _load_entries(repo: Path) -> list[dict]:
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    return manifest.get("entries", []) if isinstance(manifest, dict) else []


def _eid(e: dict) -> str:
    return str(e.get("id") or "")


def _topic_hint(e: dict) -> str:
    # dica NEUTRA pro humano (conteúdo), nunca o bloco computado.
    for k in ("moodle_label", "source_section", "title", "filename"):
        v = str(e.get(k) or "").strip()
        if v:
            return v
    return ""


# --------------------------------------------------------------------------- anotações (só `nota`, nunca seleção)

# Suspeitos declarados no pendencias (as-of reprocess IA 7561f5c).
SUSPEITOS_A = {
    "introducao-a-ml", "introducaoml-atualizacao2025",          # deslocamento -> bloco-03?
    "artigo-usando-agrupamento",                                # pin suspeito -> bloco-05
    "cap-sobre-algoritmos-geneticos-lacerda-e-outros",          # id real (truncado no draft)
    "algoritmo-genetico",
    "introducao-a-busca-informada", "outros-operadores", "programa-exemplo-ag",  # busca
}
# Clustering não-supervisionado Semana 8+9 (8 ids). 7 roteiam efetivo pro bloco-06
# (suspended, files:False) e somem da vista; o 8º (artigo) some pelo pin ->bloco-05.
ESCONDIDOS_B = {
    "aprendizadonaosupervisionado-agrupamento-parte1",
    "aprendizadonaosupervisionado-agrupamento-parte2",
    "aula-sobre-agrupamento-parte-1-particional",
    "aula-sobre-agrupamento-parte-2-hierarquico",
    "agrupamento-usando-k-means-exemplo-1-ipynb",
    "agrupamento-usando-k-means-exemplo-2-ipynb",
    "artigo-usando-agrupamento",
    "survey-on-clustering",
}
# Pares de VERSÃO (mesma aula, dois arquivos: original Moodle + re-download "nova versão",
# posting_date 2026-02-24 reusado). Não são byte-dups; conteúdo redundante p/ o gold.
#
# NÃO-CIRCULAR (invariante do canário): o par é definido por CONTEÚDO/proveniência —
# título + basename + sufixo de versão (`novaVersao`/`atualizacao2025`) + origem do
# source_path (canônico = original Moodle; alt = re-download Downloads). NUNCA por
# computed_block_id ou qualquer saída de atribuição. Se o par viesse do bloco computado,
# o canário jamais pegaria "mesma aula → blocos diferentes" — que é o que ele vigia.
# Cada tupla é (canônico_Moodle, alt_download).
VERSION_PAIRS = [
    ("mlp", "mlp-novaversao"),
    ("introducao-a-ml", "introducaoml-atualizacao2025"),
]


def _pair_key_map() -> dict[str, str]:
    """{id_membro: id_canônico}. O canônico (Moodle original) mapeia para si mesmo —
    é a chave de colapso do par no eval (par-certo-só-se-ambos)."""
    out: dict[str, str] = {}
    for canon, alt in VERSION_PAIRS:
        out[canon] = canon
        out[alt] = canon
    return out


def _version_note() -> dict[str, str]:
    out: dict[str, str] = {}
    for a, b in VERSION_PAIRS:
        out[a] = f"versao-par: tem alt `{b}`"
        out[b] = f"versao-par: alt de `{a}` (posting reusado)"
    return out


def _nota(eid: str, vnote: dict[str, str]) -> str:
    flags = []
    if eid in SUSPEITOS_A:
        flags.append("suspeito")
    if eid in ESCONDIDOS_B:
        flags.append("clustering-escondido")
    if eid in vnote:
        flags.append(vnote[eid])
    return "; ".join(flags)


# --------------------------------------------------------------------------- folha completa

def build_sample(repo: Path, out: Path) -> None:
    entries = _load_entries(repo)
    vnote = _version_note()
    pkmap = _pair_key_map()

    # folha COMPLETA alinhada ao eval_ground_truth (`id` + `true_block_id`), SEM
    # computed_block_id (cego). `pair_key` (canônico, vazio nos avulsos) é o gancho
    # estruturado do colapso de version-pair no eval. O humano preenche true_block_id
    # em bloco-NN; deixa em branco (ou marca `duvida`) pra excluir do denominador.
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "dica_conteudo", "topico_2_3_palavras", "true_block_id",
                    "pair_key", "nota", "duvida"])
        for e in entries:
            eid = _eid(e)
            w.writerow([eid, _topic_hint(e), "", "", pkmap.get(eid, ""), _nota(eid, vnote), ""])

    n = len(entries)
    n_susp = sum(1 for e in entries if _eid(e) in SUSPEITOS_A)
    n_esc = sum(1 for e in entries if _eid(e) in ESCONDIDOS_B)
    n_ver = sum(1 for e in entries if _eid(e) in vnote)
    print(f"folha completa: {n} entries -> {out}  (suspeitos={n_susp} escondidos={n_esc} "
          f"version-pairs={n_ver}). computed_block_id NÃO incluído (cego).")
    print("pontuar com: python scripts/eval_ground_truth.py <repo> "
          f"{out}  (true_block_id em bloco-NN; em branco = fora do denominador).")


# --------------------------------------------------------------------------- cli

def main() -> None:
    ap = argparse.ArgumentParser(description="folha completa de rotulagem do gold (scorer = eval_ground_truth.py)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--repo", required=True)
    s.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "sample":
        build_sample(Path(a.repo), Path(a.out))


if __name__ == "__main__":
    main()
