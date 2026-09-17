"""Registro final da sessao 6: curadoria de unidade do CG + higiene; tracker, decisions, README; arquiva o handoff 2026-09-05 (git mv fora)."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:70], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
edit(T, "**Ponto de entrada = `2026-09-05-handoff-fila-campanhas.md`.** **Ponto de entrada = handoff `2026-09-05-handoff-fila-campanhas.md`**",
        "**Ponto de entrada = handoff `docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md`** (sessao 6; o de 05/09 manha esta em `_archive/`)")
SEC = """## CURADORIA DE UNIDADE DO CG + HIGIENE DO VOCAB (05/09 tarde, sessao 6, FEITO; CG `2c5e01e`, gerador `e0c433c`)
**Codigo (`e0c433c`, `load_glossary_curation`):** sinonimo COMPILADO por LLM igual a nome de secao do Moodle (sem numeracao) nao vira alias; manual fica.
Teste `tests/test_glossary_curation.py::test_sinonimo_compilado_igual_a_secao_do_moodle_nao_entra`. Remove exatamente os 3 do CG; 0 nos outros.
**Curadoria (CG `.timeline_curation.json`, pelo oraculo):** pinos de unidade bloco-06 -> u04 (SARC 7-8 e secao 6 'Processo de Visualizacao 2D'),
bloco-08 -> u03 (SARC 12 entre processamento de imagens e exercicios), bloco-15 -> u07 (SARC 21 entre curvas e visualizacao 3D). Glossario manual do CG
so com `_nota`: o sinonimo 'Morfologia Matematica' em '3.5 Segmentacao' (`ee4c276`) rotulou o bloco-08 como Segmentacao e moveu 4 materiais de
segmentacao do bloco-07 (aula certa, 01-03/09) para o 08 — REVERTIDO em `2c5e01e` (lei nova: sinonimo manual nunca renomeia bloco).
**Reprocess registrado (`c1-3/reprocess_cg_unidade.py`, tripwire de produto: voter so com cache):** unidade mudou 9 (morfologia x3 -> u03, modelagem x6 ->
u07), bloco 0, flagadas 15 = 15, votos 42 = 42, 0 resumo de codigo; subunidade mudou 10 (csg -> geometria-solida-construtiva-csg, exercicio de
modelagem -> tecnicas-de-modelagem-3d ...). **CG unidade: 22/93 erradas -> 1** (`texturas-v3`: sem bloco, u01 por conteudo; u08 sem termo no GLOSSARY.md,
que para em 7.1.2) + 2 por erro de BLOCO (maptextures e pagina de videos no bloco-06 pela colisao 'mapeamento'; flagadas, voter decide). Os 10 do
bloco-06 sao u04 pelo oraculo (o plano poe transformacoes/instanciamento em u05: gold de subunidade vazio para 5, mapeamento -> sistema-de-coordenadas).
**Gates (todos com tripwire, 0 chamadas):** motor puro +vocab 186/199 conf-err 1 · 183/191 · 53/57 · sub 82/93 (iguais) · holdout CG 31/35 conf-err 0
flag 14 (igual) · curada 198/199 conf-err 0 · 191/191 · 55/57 (igual) · sentinela 0/8 · suite 2325 · censo revisar/100 58,3 ('mudou' 13) votos 35,9 ·
determinismo pos-higiene: DETERMINISMO_PLACEHOLDER.
**Gold de subunidade v2 (proposto, aguarda aprovacao):** CG 93 materiais, **82 pontuaveis** (1 unidade errada + 2 bloco errado + 8 meta), produto acerta
49/82 com extras (36 primario); MF 66, 58 pontuaveis, 51/58 (36). Revisao: `gold_subunidade_CG_MF_proposta_2026-09-05.md`; atribuicoes do CG por entry:
`docs/reports/Feitos/2026-09-05-cg-atribuicoes.md`. Alavancas genericas no motor para a unidade: 5 medidas e refutadas (ver §CG 22/93 abaixo e NAO fazer do handoff).

"""
edit(T, "## GOLD DE SUBUNIDADE CG E MF — PROPOSTO-CLAUDE", SEC + "## GOLD DE SUBUNIDADE CG E MF — PROPOSTO-CLAUDE")

D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### CG: unidade pela camada humana (pinos de bloco pelo oraculo) + higiene generica do vocab compilado; sinonimo manual nunca renomeia bloco

**Date:** 2026-09-05
**Status:** Active
**Decision:** As 22/93 unidades erradas do CG se resolvem com (a) higiene generica no loader do glossario — sinonimo compilado por LLM igual a nome de secao do Moodle nao vira alias (`e0c433c`) — e (b) pinos de unidade nos blocos 06 (u04), 08 (u03) e 15 (u07), derivados do SARC/Moodle, o mesmo mecanismo dos outros 7 tutores. Nenhuma regra nova no mapa bloco->unidade. Sinonimo manual e vocabulario de SUBtopico e nunca pode renomear um bloco.
**Reasoning:** Raiz medida: o compilador de vocabulario pendurou nomes de secao ('Morfologia Matematica', 'Manipulacao de Imagens', 'Mapeamento de Texturas') nos topicos genericos de u01 e o mapa, o scorer e o rotulo do bloco-08 seguiam a secao errada; a ordem do professor (u04 -> u07 -> u03 -> u07 -> u06) inverte o plano e a DP monotonica so aceita um desvio. Cinco alavancas genericas medidas nos 8 e refutadas: sem aliases 183 -> 136/191; radicais saldo 0; vizinho ancorado 183 -> 163; exclusividade relaxada 179; higiene sozinha neutra. O sinonimo 'Morfologia' em '3.5 Segmentacao' rotulou o bloco-08 e moveu 4 materiais do bloco certo: revertido.
**Consequences:** CG `2c5e01e`: unidade 22 -> 1 errada (+2 por erro de bloco flagado); todas as reguas iguais (motor puro 186/199, holdout 31/35, curada 198/199); 0 chamadas Gemini (tripwire de produto). Dividas de dados novas (C5): GLOSSARY.md do CG para em 7.1.2 (u08 sem termo); zips do MF colidem nomes; gold de unidade do CG.
"""
assert "CG: unidade pela camada humana" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + """
- `simula_unidade_sem_alias.py` / `simula_raiz_unidade.py [sec-only]`: mapa bloco->unidade nos 8 com variantes (sem aliases, radicais, higiene por
  secao, vizinho ancorado, exclusividade relaxada) — so a higiene sobrevive (neutra); as outras regridem.
- `reprocess_cg_unidade.py` (tripwire de PRODUTO: voter so com cache, 0 chamadas) -> `reprocess_cg_unidade.log`: 3 reprocess registrados do CG
  (pinos; sinonimo de morfologia; reverso). `determinismo_tripwire.py` -> `determinismo_higiene.log`. `b_higiene_{puro,holdout}.log`: gates pos-higiene.
""", encoding="utf-8")
print("docs ok")
