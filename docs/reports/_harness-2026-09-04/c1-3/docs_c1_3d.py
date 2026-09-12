"""Registro: gold de subunidade CG/MF PROPOSTO (aguarda aprovacao) + bug de colisao de nomes nos zips do MF. Idempotente por assert."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:70], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = """## GOLD DE SUBUNIDADE CG E MF — PROPOSTO-CLAUDE (05/09 tarde, sessao 6; **AGUARDA APROVACAO DO USER**) + BUG: ZIPS DO MF COLIDEM
**Arquivos:** `docs/reports/subunit_gt_CG.csv` (93 materiais, **63 pontuaveis**, 22 com UNIDADE computada errada -> `scorable=no` com a unidade
verdadeira na nota) e `subunit_gt_MF.csv` (66, **58 pontuaveis**, 5 unidade errada); revisao humana em
`docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md` (coluna `ok?`). Gerador: `_harness-2026-09-04/c1-3/gera_gold_subunidade.py`
(regras no docstring). **Ainda NAO entra em `motor_puro.py` (SUBUNIT_GOLD) nem na regua:** gold e humano; entra apos aprovacao.
**Contra o PRODUTO (originais), com a proposta como esta:** CG com-extras 42/63 (primario 30/63) · MF 51/58 (36/58). Rulings pendentes marcados na
nota: (a) bundle de codigo misto rotula pelo card (CG `opengl3dcpp`, `-vdi`)? (b) CG `exemplodemanipulacaodeimagens`: label 'Classe Vetor' x conteudo
processamento de imagens; (c) convencao Dafny: listas 'Programacao e Verificacao com Dafny (X)' = `softwares-de-suporte...` com extra
`verificacao-de-programas`; (d) OpenGL (ferramenta) = subtopico vazio.
**Achado de UNIDADE no CG (22/93, sem gold de unidade):** o card '6 - Processo de Visualizacao 2D' mistura u04 (recorte) e u05 (instanciamento,
mapeamento, transformacoes) e o motor poe tudo em u04 (8 entries); modelagem (csg, modelagem3d, exercicio de extrusao, basico3d x2, pagina de
videos) em u06 em vez de u07 (6); texturas (maptextures, texturas-v3, pagina de videos) em u04/u01 em vez de u08 (3); morfologia (slides, aula
gravada, pagina) em u01 em vez de u03 (3); animacao-v2 e transformacoes em u04 em vez de u05. Candidato a gold de unidade do CG (C5).
**BUG (medido): zips do MF extraidos SEM subpasta -> colisao de nomes.** `raw/code/professor/` e plano (36 arquivos): `colecoes_arrays/ex1.dfy`,
`colecoes_sequences/ex1.dfy`, `invariantes/ex1.dfy`, `terminacao/ex1.dfy` e `tiposindutivos/ex1.dfy` viram UM `ex1.dfy` (o ultimo vence:
`code/professor/ex1.md` tem 'datatype Cor' = tiposindutivos; 'new nat[5]' dos arrays nao existe em lugar nenhum). Resultado: 4 zips (20 .dfy)
perderam o conteudo no tutor e os 5 resumos de codigo dizem 'datatype Cor'; `exemplos.zip` (5 `.smv` do NuSMV) nao gera markdown (extensao
ignorada) e o resumo diz 'Dafny'. Efeito na atribuicao: os flips de bloco do item 3 (`exercicios-conjuntos`, `-arrays`) e os 6 'exemplos' do MF
decidem com texto de OUTRO zip. Correcao: extrair zip preservando `<zip>/<membro>` (ou prefixar pelo id) + aceitar `.smv`; depois re-resumir
(Gemini, quando liberado) e reprocessar o MF. Tag [CODE] · campanha: SYNC/C5 (dado) — decisao do user.

"""
edit(T, "## OS 32 ERROS DO MOTOR PURO POR REGUA, SEM LLM", SEC + "## OS 32 ERROS DO MOTOR PURO POR REGUA, SEM LLM")

H = GEN / "docs/reports/2026-09-05-handoff-fila-campanhas.md"
edit(H, "- **Gold de subunidade do CG (93) e MF (66) proposto-claude para sua aprovacao** (C5): destrava a propagacao de vocabulario (+5 no gold atual)\n"
        "  e da regua a 4 cursos que hoje so listam flips. Custo: revisao humana; 0 LLM.\n",
        "- **APROVAR o gold de subunidade do CG (63 pontuaveis) e MF (58) — PROPOSTO em 05/09 tarde** (`docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md`,\n"
        "  4 rulings marcados). So depois entra em `motor_puro.py` e destrava a medicao da propagacao de vocabulario nos 8 (tracker §GOLD DE SUBUNIDADE CG E MF).\n"
        "- **BUG dos zips do MF (colisao `ex1.dfy` entre 5 zips; `.smv` ignorado): 4 zips sem conteudo no tutor, 5 resumos errados** — corrigir na\n"
        "  extracao (SYNC/C5) e re-resumir quando o Gemini for liberado; decisao de fila sua (tracker, mesma secao).\n")
edit(H, "- **Propagacao de vocabulario por headings para a subunidade (sem LLM):**",
        "- **Zips extraidos sem subpasta colidem nomes** (MF: 5 zips x `ex1.dfy`; `.smv` ignorado) · sim: `<id>/<membro>` na extracao + `.smv` como codigo ·\n"
        "  SYNC/C5 · conteudo certo no tutor e resumo certo por zip (hoje 4 zips do MF mostram o codigo de outro).\n"
        "- **Propagacao de vocabulario por headings para a subunidade (sem LLM):**")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + """
- `gera_gold_subunidade.py [--write]`: gold de subunidade CG/MF proposto-claude (05/09) -> `docs/reports/subunit_gt_{CG,MF}.csv` +
  revisao em `docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md`. Aguarda aprovacao; nao esta em `motor_puro.py`.
""", encoding="utf-8")
print("docs ok")
