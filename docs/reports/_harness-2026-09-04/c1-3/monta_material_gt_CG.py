"""3.2 do plano 08/09: gold de unidade do CG no formato dos 5 cursos (`docs/reports/material_gt_<sig>.csv`, lido por
`scripts/eval_eixos.py`; `_load_truth` da regua de unidade ainda le so gold por bloco). PROPOSTO-CLAUDE 11/09, revisado pelo
astra (`c1-3/resposta_codex_astra_gold_unidade_cg.md`), a adjudicar pelo user (mesmo fluxo do gold de subunidade de 05/09).
Oraculo = a estrutura do professor (secao do Moodle `source_section`, cronograma, plano de ensino), nao o motor: a unidade do
produto vem do bloco temporal em 87/93, entao a secao e uma medida independente do mapa bloco -> unidade. Regras, nesta ordem:
  1. secao "Plano de Ensino" (cronograma, plano, playlist) = meta -> todas as unidades (ruling-user 2026-08-19 no SO);
  2. prova resolvida e lista de prova -> unidades que a prova cobre, lidas do conteudo (ruling-user 2026-08-19 no SO);
  3. PENDENTE: o plano de ensino nao decide (OpenGL: nao lista a ferramenta em unidade nenhuma; bundles mistos; label do
     Moodle contradiz o conteudo) -> `status=pendente`, e sem gold = `scorable=no` ate o ruling do user (astra 11/09: nao
     converter inferencia cronologica em erro definitivo, nem usar a decisao do produto como gold);
  4. material com regra propria (POR_MATERIAL): conteudo contradiz a secao, ou secao "Exercicios 2D" que cruza unidades;
  5. SECAO -> unidade. Secao 6 = u04 pelo oraculo (ruling aprovado 06/09), sem `|u05` (astra: a uniao esconderia a distincao);
     nota "plano: u05" so onde o CONTEUDO mostra transformacoes/window-viewport (5.1-5.2), nao por palavra no id
     ("Instanciamento de Primitivas" e 7.2.4 no plano).
`gold_units`: `|` = qualquer uma vale (nao mede cobertura integral). `status`: rotulado | pendente | insuficiente.
0 chamadas. Ordem: bloco temporal, depois id. Uso: python -B docs/reports/_harness-2026-09-04/c1-3/monta_material_gt_CG.py"""
import ast
import collections
import csv
import json
import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(GEN))
from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map as getmd  # noqa: E402
from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy  # noqa: E402

ROOT = GEN.parent / "Computacao-Grafica-Tutor"
COLS = ["entry_id", "title", "category", "card", "posting_date", "text_chars", "evidencia", "pred_unit",
        "unit_do_bloco_temporal", "gold_units", "gold_topics", "scorable", "notas", "status", "gold_fonte"]
PROV = "proposto-claude 2026-09-11: "
RULING_SO = "ruling-user 2026-08-19 (SO)"
SECAO = {  # secao do Moodle -> n da unidade do plano
    "1 - Origens da Computação Gráfica": 1,
    "3 - Fundamentos Matemáticos para Computação Gráfica": 2, "4 - Detecção de Colisão": 2, "5 - Geometria Computacional": 2,
    "6 - Processo de Visualização 2D": 4, "7 - Curvas Paramétricas": 7, "8 - Manipulação de Imagens": 3,
    "9 - Introdução ao Processamento de Imagens": 3, "10 - Segmentação de Imagens": 3, "11 - Morfologia Matemática": 3,
    "12 - Modelagem Geométrica": 7, "13 - Computação Gráfica 3D": 6, "14 - Exercícios sobre Modelagem Geométrica": 7,
    "15 - Remoção de Elementos Ocultos": 6, "16 - Síntese de Imagens Realísticas": 8, "17 - Mapeamento de Texturas": 8,
    "Exercícios de Processamento de Imagens": 3,
}
NOTA_SECAO = {
    "6 - Processo de Visualização 2D": "u04 pelo oraculo (ruling aprovado 06/09)",
    "17 - Mapeamento de Texturas": "plano de ensino 8.4 'Mapeamento de Textura' = u08 (user 11/09: 'Texturas e unidade 8'); produto poe em "
                                   "u04 por colisao de token no bloco-06 (nota aprovada 06/09: BLOCO ERRADO)",
}
# secao 6: onde o conteudo (headings lidos em 11/09) e transformacoes / window-viewport, o plano diz u05; gold fica u04 pelo ruling
NOTA_U05 = {
    "instanciamento": "conteudo: '3 TRANSFORMACOES GEOMETRICAS, translacao, escala' = plano 5.1 (u05 candidato tematico)",
    "transformacoesgeometricas": "conteudo: transformacoes = plano 5.1-5.6 (u05 candidato tematico)",
    "transformacoesgl": "conteudo: transformacoes em OpenGL = plano 5.1-5.6 (u05 candidato tematico)",
    "mapeamento": "conteudo: janela de selecao x exibicao = plano 5.2 window/viewport (u05 candidato tematico)",
    "pagina-com-videos-sobre-mapeamento-9f410e": "videos de mapeamento = plano 5.2 (u05 candidato tematico)",
    "video-sobre-mapeamento-em-opengl-1dad3c": "video de mapeamento = plano 5.2 (u05 candidato tematico)",
    "exercicios-teoricos-sobre-processo-de-visualizacao": "nota aprovada 06/09: window/viewport = plano 5.2 (u05 candidato tematico)",
}
INDETERMINADO = ("animacao-v2", "pagina-com-videos-sobre-instanciamento", "vis2d")  # titulo nao resolve u04 x u05 (astra 11/09)
PENDENTE = {}  # id -> (unidades candidatas, nota); sem unidade = scorable=no ate o ruling do user. Vazio desde os rulings de 11/09.
# Rulings do user, 11/09 noite ("Bundles pelo card 13, exemplo pelo conteudo u3"): bundles mistos rotulam pelo card; label do Moodle
# ('Classe Vetor') perde para o conteudo (.cpp de filtros de imagem).
RULING_1109 = "ruling-user 2026-09-11"
BUNDLE = ([6], RULING_1109 + ": apoio misto rotula pelo card", "bundle misto (2D/3D/Bezier/imagens), card 13 'Computacao Grafica 3D' = u06; "
                                                                "fecha o RULING pendente desde 06/09")
# OpenGL (secao 2): o plano de ensino nao lista a ferramenta; astra 11/09 pediu pendente; RULING do user 11/09: "OpenGL na u1,
# possivelmente na subunidade 1.4 Aplicacoes" (o cronograma segue a ordem do plano: PI e Visao fecham a u03, Colisao e o meio da u02,
# logo a aula 2 esta dentro da u01). Subunidade 1.4 fica em `gold_topics` como possivel; o gold de subunidade (vazio, aprovado 06/09)
# nao muda ate o user confirmar.
OPENGL = ([1], "ruling-user 2026-09-11: OpenGL na u01 (cronograma na ordem do plano)",
          "plano de ensino nao lista OpenGL (so bibliografia); cronograma aula 2 (06/08); ruling do user 11/09: u01, possivelmente 1.4 Aplicacoes")
GOLD_TOPICS = {k: "aplicacoes" for k in ("exercicios", "opengl-cpp", "opengl-py", "openglbasico", "video-com-instrucoes-para-usar-opengl-na-vdi")}
POR_MATERIAL = {  # id -> (unidades, fonte, nota)
    **{k: OPENGL for k in GOLD_TOPICS},
    "opengl3dcpp": BUNDLE, "opengl3dcpp-vdi": BUNDLE,
    "exemplodemanipulacaodeimagens": ([3], RULING_1109 + ": conteudo vence o label do Moodle",
                                      "secao 3 e label 'Classe Vetor' diziam u02; conteudo do .cpp = manipulacao de imagens/filtros = u03 (astra 11/09; "
                                      "ruling do user 11/09)"),
    "texturas-v3": ([8], "conteudo", "texturas + iluminacao = u08 (plano de ensino 8.4; nota aprovada 06/09: UNIDADE ERRADA); a secao 2 OpenGL nao vale aqui"),
    "exercicios-de-geometria-computacional": ([2], "conteudo", "secao 'Exercicios 2D' cruza unidades; matriz de dominancia"),
    "exercicios-sobre-curvas-html": ([7], "conteudo", "secao 'Exercicios 2D' cruza unidades; duplicata de exercicios-sobre-curvas"),
    "exerciciosfundamentosmatematicos": ([2], "conteudo", "secao 'Exercicios 2D' cruza unidades; poligonos e vetores"),
    "resolucao-de-prova-de-computacao-grafica-2d": ([4], RULING_SO + ": prova cobre as unidades da prova",
                                                    "prova 2D resolvida: so transformacoes em OpenGL = u04 pelo oraculo (u05 candidato tematico; "
                                                    "astra 11/09: nao usar u04|u05 para um conteudo so; u02 nao aparece nas questoes)"),
    "resolucao-de-prova-de-computacao-grafica-2d-html": ([4], RULING_SO + ": prova cobre as unidades da prova", "duplicata html da prova 2D"),
    "resolucao-de-prova-de-computacao-grafica-3d": ([6, 7, 8], RULING_SO + ": prova cobre as unidades da prova",
                                                    "prova 3D: iluminacao, sombreamento, z-buffer, projecao, textura, curva"),
    "listadeexercicios2026-1": ([6, 7, 8], RULING_SO + ": lista cobre as unidades da prova",
                                "lista para P2: iluminacao + projecao + modelagem (nota aprovada 06/09)"),
}


def conflito(v):
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except Exception:
            v = ast.literal_eval(v)
    return (v or {}).get("unit", "") if isinstance(v, dict) else ""


tax = load_internal_content_taxonomy(ROOT)
UN = {int(u["slug"].split("-")[1]): u["slug"] for u in tax["units"]}
man = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["entries"]
blocos = json.loads((ROOT / "course/.timeline_index.json").read_text(encoding="utf-8"))["blocks"]
bu = {k: (b.get("unit_slug") or "") for b in blocos for k in (b["id"], b.get("block_uuid", ""))}
sub = {r["entry_id"]: r for r in csv.DictReader((GEN / "docs/reports/subunit_gt_CG.csv").open(encoding="utf-8-sig", newline=""))}


def rotulo(e):
    """-> (unidades, fonte, nota, status) pela ordem das regras do docstring."""
    sec, eid = e.get("source_section") or "", e["id"]
    if sec == "Plano de Ensino":
        return sorted(UN), RULING_SO + ": meta cobre todas as unidades", "meta (cronograma, plano, playlist)", "rotulado"
    hit = POR_MATERIAL.get(eid) or next((v for k, v in POR_MATERIAL.items() if len(k) > 20 and eid.startswith(k)), None)
    if hit:
        return (*hit, "rotulado")
    pend = PENDENTE.get(eid) or next((v for k, v in PENDENTE.items() if eid.startswith(k) and len(k) > 20), None)
    if pend:
        return pend[0], "pendente: candidatos na nota", pend[1], "pendente"
    if sec == "Exercícios 2D" and "processo-de-visualizacao" in eid:
        return [4], "conteudo", "secao 'Exercicios 2D' cruza unidades; u04 pelo oraculo; " + NOTA_U05["exercicios-teoricos-sobre-processo-de-visualizacao"], "rotulado"
    if sec not in SECAO:
        return [], "", "SEM REGRA", "insuficiente"
    nota = NOTA_SECAO.get(sec, "")
    if sec.startswith("6 -"):
        extra = next((v for k, v in NOTA_U05.items() if eid.startswith(k)), "titulo nao resolve u04 x u05" if eid.startswith(INDETERMINADO) else "")
        nota = "; ".join(x for x in (nota, extra) if x)
    return [SECAO[sec]], "secao-moodle", nota, "rotulado"


rows = []
for e in man:
    s = sub.get(e["id"], {})
    uns, fonte, nota, status = rotulo(e)
    texto = conflito(e.get("unit_block_conflict"))
    notas = [n for n in (nota, f"conflito: texto queria {texto}" if texto else "",
                         f"subunit_gt scorable=no: {s.get('notas', '').split(';', 1)[-1].strip()}" if s.get("scorable") == "no" else "",
                         f"unit_conf={float(e.get('unit_match_confidence') or 0):.2f} revisar={e.get('revisar', '')}") if n]
    bloco = e.get("temporal_block_id") or e.get("computed_block_id") or ""
    rows.append({"entry_id": e["id"], "title": e.get("title", ""), "category": e.get("category", ""),
                 "card": s.get("card") or e.get("source_section") or "", "posting_date": s.get("posting_date", ""),
                 "text_chars": len(getmd(ROOT, e) or ""), "evidencia": s.get("evidencia", ""),
                 "pred_unit": e.get("computed_unit_slug", ""), "unit_do_bloco_temporal": bu.get(bloco, ""),
                 "gold_units": "|".join(UN[n] for n in uns) if status == "rotulado" else "",
                 "gold_topics": next((v for k, v in GOLD_TOPICS.items() if e["id"] == k or (len(k) > 20 and e["id"].startswith(k))), ""),
                 "scorable": "yes" if status == "rotulado" else "no", "notas": " · ".join(notas), "status": status,
                 "gold_fonte": PROV + fonte if fonte else "", "_bloco": bloco})
rows.sort(key=lambda r: (r["_bloco"], r["entry_id"]))
out = GEN / "docs/reports/material_gt_CG.csv"
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

pont = [r for r in rows if r["scorable"] == "yes"]
certo = [r for r in pont if r["pred_unit"] in r["gold_units"].split("|")]
print(f"{out.name}: {len(rows)} linhas · status {dict(collections.Counter(r['status'] for r in rows))} · "
      f"produto certo na unidade {len(certo)}/{len(pont)} pontuaveis")
print("fonte:", dict(collections.Counter(r["gold_fonte"].replace(PROV, "")[:34] for r in rows)))
print("== produto ERRA (pred fora do gold, pontuaveis):")
for r in pont:
    if r not in certo:
        print(f"   {r['entry_id'][:44]:44} pred={r['pred_unit'][:11]} gold={r['gold_units'][:40]} | {r['notas'][:70]}")
print("== PENDENTES (ruling do user):")
for r in rows:
    if r["status"] == "pendente":
        print(f"   {r['entry_id'][:44]:44} pred={r['pred_unit'][:11]} | {r['notas'][:120]}")
