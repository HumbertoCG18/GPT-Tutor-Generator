---
name: text-chain
description: Cadeia do TEXTO de um material — da extração ao markdown que o motor pontua e que o aluno lê. Carregue antes de mexer em curadoria de MD, Curator Studio, aprovação, descrições de imagem, ou em qualquer medição de acurácia do motor (o estado do texto muda o insumo).
triggers:
  - "staging"
  - "approved_markdown"
  - "base_markdown"
  - "advanced_markdown"
  - "curator studio"
  - "aprovar markdown"
  - "curadoria de MD"
  - "qual texto o motor lê"
  - "descrição de imagem"
  - "IMAGE_DESCRIPTION"
  - "sumário executivo"
edges:
  - target: context/pdf-pipeline.md
    condition: when the question is which backend produced the markdown
  - target: patterns/ollama-vision.md
    condition: when the question is who generates image descriptions
  - target: context/repo-output.md
    condition: when the question is the final shape of the tutor repo
last_updated: 2026-09-07
---

# Cadeia do Texto

Auditado por leitura de código + medição nos 8 tutores em 07/09/2026 (`docs/reports/_harness-2026-09-04/c1-3/fonte_do_texto.log`).
Esta cadeia não estava documentada em lugar nenhum — nem aqui, nem em `docs/Overview-Sistema.html` — e custou uma sessão inteira de
redescoberta. Estado vivo e números ficam no tracker; aqui só o contrato.

## 1. Qual arquivo o motor pontua

Fonte única da resolução: `src/builder/artifacts/navigation.py:71 _entry_markdown_path_for_file_map`.

Precedência, primeiro que existir vence:

```
approved_markdown  >  curated_markdown  >  base_markdown  >  advanced_markdown
```

O mesmo helper alimenta `_entry_markdown_text_for_file_map` (`navigation.py:84`), que é o texto consumido por
`extraction/entry_signals.py` e, por ele, por todo o scorer de unidade/subunidade. **`advanced_markdown` é o último da fila: na prática
nunca é lido**, porque todo material com PDF tem `base_markdown`.

## 2. Os quatro estados de um material

| campo | quem escreve | onde vive | backend típico |
|---|---|---|---|
| `base_markdown` | build, extração base | `staging/markdown-auto/` (ou `content/`, `code/`, `exercises/` conforme categoria) | `pymupdf4llm` (livre), `html_converter`, `url_fetcher` |
| `advanced_markdown` | build, extração avançada | `staging/` | `datalab` (pago), `marker`, `docling` |
| `approved_markdown` = `curated_markdown` | Curator Studio, ao aprovar | `content/curated/`, `exercises/lists/`, `exams/past-exams/` | cópia da fonte escolhida na GUI |

`staging/` = **material que nunca foi aprovado na GUI**. Não é erro nem pendência de build: é o estado natural de quem não passou pelo
Curator Studio. Medido em 07/09: MF 2 · CG 76 · LR 7 · FR 17 ainda em staging; SO/IA/ES2/TCC 100% aprovados.

## 3. O que a aprovação faz com o texto (dois caminhos DIVERGENTES)

`src/ui/curator_studio.py`:

- **Aprovar UM** (`_approve_current:1345`): normaliza refs de imagem → grava a fonte escolhida → copia para o destino → aplica
  `_clean_extraction_noise` (tira número de página, separador, linha em branco extra) → aplica `_inject_executive_summary`
  (**insere no topo um bloco `<!-- EXEC_SUMMARY_START --> ## Sumário` com TODOS os headings do documento**). Ambas em
  `src/builder/artifacts/navigation.py:182,230`.
- **Aprovar TODOS** (`_approve_all_pending:1105`): apenas `shutil.copy2` + injeção de descrições de imagem. **Não limpa e não injeta
  sumário.**

Consequência: "aprovado" não é um estado único — o texto final depende de qual botão foi usado. Medido: materiais com sumário injetado
MF 19/53 · SO 28/38 · IA 25/55 · ES2 24/27 · TCC 26/27 · CG/LR/FR 0.

**Impacto no motor: nenhum, medido.** `c1-3/simula_aprovacao.py` aplicou o pós-processamento em cópia dos 6 cursos com gold e reprocessou:
bloco, unidade e subunidade idênticos (245/288 → 245/288); só a fila de revisão sobe 3. O sumário duplica headings dentro do lead (capado em
2600 chars por `extract_markdown_lead_text`), mas não move decisão.

## 4. Por que o Datalab nunca entrou no eixo de atribuição

Duas portas, e o resultado é diferente em cada uma:

1. **Porta do texto: fechada por desenho.** O Curator Studio monta o dropdown de fontes em ordem fixa Base → Avançado → Template
   (`_build_source_list:718`) e pré-seleciona o primeiro (`curator_studio.py:687`, comentário no código: *"Auto-select best source (prefer
   base markdown, then advanced, then template)"*). Aprovar sem trocar o dropdown promove a **base**. Medido: **198 de 198** textos
   aprovados nos 5 cursos têm jaccard de linhas ≥ 0,9 contra o `base_markdown` e < 0,9 contra o `advanced_markdown`. Não foi falta de
   aprovação; foi o default da GUI.
2. **Porta da imagem: aberta.** As descrições de imagem são geradas pelo **Datalab** durante o build
   (`image_curation.pages[].images[].source == "datalab"`, 2011 imagens nos 8 tutores) e **injetadas no markdown que o motor lê**, como
   bloco `<!-- IMAGE_DESCRIPTION: … -->` (`src/builder/extraction/image_markdown.py:10`). Presentes em 142 de 305 materiais, em inglês,
   até 1634 chars. O Ollama também sabe descrever (`src/builder/vision/ollama_client.py:294 describe_image`), mas hoje só entra pelo Image
   Curator na UI — **não há seleção de provedor no build**.

**Medido (`c1-3/ablate_descricoes.py`): remover as descrições MELHORA a atribuição** — produto 245 → 247/288 materiais 100% certos,
subunidade 193 → 195/233, erros confiantes 19 → 18, fila 91 → 89. A descrição genérica em inglês é ruído para o scorer.
Conclusão de arquitetura: a descrição serve ao **aluno**, não ao scorer — o motor deve pontuar o texto sem esses blocos, mantendo-os no
markdown entregue.

## 5. Regras ao medir acurácia

- Toda cópia para medição/gate precisa incluir `staging/`: sem ela, LR/CG/FR/parte do MF reprocessam **sem texto** e o número mente.
  (O `docs/reports/_harness-2026-09-02/determinismo.py` tinha esse furo; `c1-3/zero_diff.py` copia `staging/`.)
- "Sem LLM" / "sem API paga" descreve **as chamadas do motor**, não o insumo: 142/305 materiais carregam prosa do Datalab no texto.
  O regime realmente livre é o de `ablate_descricoes.py`.
- Comparar in-sample (5 cursos) com holdout (CG) é legítimo quanto ao texto: o estado de aprovação não muda os eixos (§3).
