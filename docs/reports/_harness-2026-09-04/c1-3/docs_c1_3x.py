"""Registro (07/09): de onde vem o texto que o motor le (staging x aprovado), onde o Datalab entra (descricoes de imagem), o pos-processamento da aprovacao (sumario injetado). Args: 1 = resultado do experimento simula_aprovacao (1 linha)."""
import sys
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")
DELTA = (sys.argv + ["?"])[1]


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
anchor = '## CONSOLIDACAO DAS DUPLICACOES DO MOTOR (07/09; user: "vamos antes resolver essas duplicacoes"; inventario em `c1-3/inventario_motor_2026-09-07.md`)'
SEC = f"""## DE ONDE VEM O TEXTO QUE O MOTOR LE — STAGING x APROVADO, ONDE O DATALAB ENTRA, SUMARIO INJETADO (07/09; user: "automatizar a curadoria; o produto nao pode se moldar a uma API paga; medir com os aprovados antes do passo 1")
**Precedencia (medida, `navigation._entry_markdown_path_for_file_map:71`):** `approved_markdown` > `curated_markdown` > `base_markdown` >
`advanced_markdown`. Estado nos 8 (`c1-3/fonte_do_texto.log`): MF le approved 51 + base 2 · SO 38 approved · IA 55 · ES2 27 · TCC 27 ·
**CG le base 76+5 · LR base 7 · FR base 17** (staging = MD nao aprovado no Curator Studio). 305 de 348 materiais tem texto.
**O `advanced_markdown` DO DATALAB NUNCA FOI LIDO PELO MOTOR (achado que corrige a premissa):** os 198 textos aprovados vieram, todos, do `base_markdown`
(**pymupdf4llm**, biblioteca livre) — jaccard de linhas >= 0,9 contra o base e < 0,9 contra o advanced, em 198/198. O Datalab gerou
`advanced_markdown` em 163 entries (MF 34 + marker 9, SO 31, IA 28, ES2 27, TCC 27, CG 21, LR 7, FR 15) e **nenhum desses arquivos entrou no
caminho de atribuicao**. **POREM o Datalab ENTRA no texto do motor por outra porta (correcao 07/09, lembrete do user):** as DESCRICOES DE
IMAGEM sao geradas pelo Datalab (`image_curation.pages[].images[].source == "datalab"`, 2011 imagens nos 8; 3 sem marca no MF) e sao
INJETADAS no markdown lido (`<!-- IMAGE_DESCRIPTION -->`), em ingles. Entao o texto-base e livre (pymupdf4llm) mas 142/305 materiais carregam
prosa do Datalab que pontua no scorer. Trocar o backend muda ESSAS descricoes — medida em `c1-3/ablate_descricoes.py` (remove os blocos e
remede).
**A aprovacao MUDA o texto (dois caminhos divergentes — inconsistencia a decidir):** `_approve_current` (aprovar UM) normaliza refs de imagem,
grava a fonte escolhida, copia e entao aplica `_clean_extraction_noise` (tira numero de pagina, separadores, linhas em branco) +
`_inject_executive_summary` (**insere no TOPO um bloco "## Sumario" com TODOS os headings do documento**). `_approve_all_pending` (aprovar
TODOS) so copia e injeta descricoes de imagem — **nao limpa e nao injeta sumario**. Por isso o estado e desigual: textos lidos com sumario
MF 19/53 · SO 28/38 · IA 25/55 · ES2 24/27 · TCC 26/27 · **CG 0/81 · LR 0/7 · FR 0/17**. Efeito esperado no motor: o lead e capado em 2600
chars (`extract_markdown_lead_text`) e pesa 1,6 por token / 2,8 por frase exata, headings 1,8 / 3,0; o sumario DUPLICA os headings dentro do
lead e pode empurrar o conteudo real para fora dele — mexe em score e, sobretudo, em MARGEM (o gate de `ambiguous` e 0,12 na subunidade e
0,15 na unidade). **Medido (`c1-3/simula_aprovacao.py`, copias em `.ablacao/aprovado/`, tripwire, 0 chamadas):** {DELTA}
**"ZERO LLM/SEM API PAGA" E SEM CHAMADA, NAO SEM INFLUENCIA:** o texto que o motor le contem **descricoes de imagem do Datalab** (bloco
`<!-- IMAGE_DESCRIPTION: ... -->`) em 142 de 305 materiais, em TODOS os cursos: MF 11/53 (186 chars medios) · SO 27/38 (552) · IA 23/55
(1634) · ES2 24/27 (474) · TCC 26/27 (420) · CG 18/81 (760) · LR 3/7 (240) · FR 10/17 (604). O motor nao chama LLM nem Datalab em nenhum regime,
mas o insumo desses materiais ja passou pelo Datalab. Etiqueta honesta: "sem chamada na atribuicao". O regime "sem servico externo em lugar
nenhum" e o de `ablate_descricoes.py`.
**MEDIDO — REMOVER AS DESCRICOES DO DATALAB MELHORA O MOTOR (`c1-3/ablate_descricoes.log`, copias em `.ablacao/sem-descricao/`, tripwire):**
produto com descricoes (hoje) 100% certo **245/288** · bloco 235/237 · unidade 183/190 · sub 193/233 · fila 91 · conf-err 19; **sem** as
descricoes **247/288** · bloco 235/237 · unidade 183/190 · **sub 195/233** · fila 89 · **conf-err 18** (CG 57 -> 59, sub 56 -> 58, conf-err
10 -> 9; TCC fila 7 -> 6; SO 10 -> 9; MF/IA/ES2 iguais). Removidos ~390 mil chars de prosa em ingles. Leitura: a descricao generica do
Datalab ("Three images illustrating smart home appliances") e RUIDO para a atribuicao. **Conclusao de arquitetura (nao "apagar descricao"):**
a descricao serve ao ALUNO (texto do tutor), nao ao scorer — o motor deve pontuar o texto SEM os blocos `IMAGE_DESCRIPTION`, mantendo-os no
markdown entregue. Alavanca barata: filtrar o bloco no `entry_signals` antes de pontuar (a medir com gate).
**Backlog de arquitetura (pedido do user, 07/09):** o produtor da descricao de imagem deve ser ESCOLHIVEL (Datalab | Gemini | Ollama local),
como ja e o backend de extracao; hoje esta fixo no Datalab. Ordem: motor primeiro, depois backends (Marker correto, MinerU) e o seletor de
descricao, com re-medicao nos aprovados.
**Consequencia para as reguas:** a comparacao in-sample (5 cursos) x holdout (CG) confunde DUAS variaveis — "afinado x nao afinado" e
"texto pos-aprovacao x texto cru". So depois de igualar o estado do texto o 67% do CG e comparavel com o 94-100% dos outros.
**Ordem acordada com o user (07/09):** igualar o texto (este experimento) -> passo 1 (ima de headings) -> demais passos. Backlog do user:
automatizar a curadoria de MD e trocar o backend de extracao (Marker correto, MinerU) DEPOIS do motor, com teste nos aprovados.

"""
edit(T, anchor, SEC + anchor)

H = GEN / "docs/reports/_archive/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "**Consolidacao das duplicacoes (07/09, commits",
        "**Texto que o motor le (07/09):** approved > curated > base > advanced; CG/LR/FR leem `staging/` (MD nao aprovado). O `advanced_markdown` do **Datalab nunca foi lido pelo "
        "motor** (198/198 aprovados vieram do pymupdf4llm), mas o Datalab ENTRA pelas descricoes de imagem injetadas no texto lido (142/305). A aprovacao individual injeta um sumario com todos os "
        "headings no topo (o lote nao) — estado desigual, medido em `c1-3/simula_aprovacao.py`. Backlog do user: produtor da descricao escolhivel (Datalab | Gemini | Ollama). "
        "'Sem API paga' = sem chamada, nao sem influencia. Detalhe no tracker §DE ONDE VEM O TEXTO.\n"
        "**Consolidacao das duplicacoes (07/09, commits")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `simula_aprovacao.py` (pos-processamento da aprovacao aplicado em copia + reprocess + medida antes/depois) · log `simula_aprovacao.log` · `fonte_do_texto.log` (precedencia, Datalab, sumario, descricoes por LLM) · `docs_c1_3x.py`.\n", encoding="utf-8")
print("docs ok")
