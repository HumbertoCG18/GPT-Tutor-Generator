# W-V (#51) — importação offline dos ausentes (22/09/2026)

Veredito: unidade ≥ 256/284 sem perda = **NÃO**.
sha256 JSON `e1aa60ae057550863a6c12e583b0da103af0e2aef9ece5ac6304b5c18920e652` · congelamento `8097eaa81141d8bb1e5daef8508a39eb5eafedab967db116ae43defb69656bcc` · tempo 637s · HEAD 493119e.

## Placar (cadeia real rb→ru→régua)

| cenário | bloco | unidade | sub primária | sub aceita |
|---|---|---|---|---|
| antes | 217/237 | 246/284 | 84/251 | 107/251 |
| antes_ponte_estendida | 218/237 | 247/284 | 84/251 | 107/251 |
| controle | 218/237 | 247/284 | 84/251 | 107/251 |
| depois | 223/237 | 252/284 | 86/251 | 109/251 |

Por curso (antes → depois):

| curso | bloco | unidade | sub prim. | sub aceita |
|---|---|---|---|---|
| MF | 56→60/66 | 61→63/66 | 25→25/58 | 29→29/58 |
| SO | 36→36/39 | 30→30/37 | 7→7/15 | 8→8/15 |
| IA | 39→41/42 | 39→39/42 | 4→4/39 | 5→5/39 |
| ES2 | 27→27/28 | 25→25/28 | 7→7/28 | 8→8/28 |
| TCC | 26→26/27 | 17→17/18 | 7→7/11 | 9→9/11 |
| CG | 33→33/35 | 74→78/93 | 28→30/82 | 41→43/82 |
| FR | 0→0/0 | 0→0/0 | 6→6/18 | 7→7/18 |

## Os 13

| curso | gold_id | ação | unidade gold | antes | depois unidade | acertou | bloco previsto (gold) | sub prevista (gold) |
|---|---|---|---|---|---|---|---|---|
| MF | `eth2` | injetado | unidade-02-verificacao-de-programas | ausente | unidade-01-metodos-formais | não | bloco-01 (bloco-01) | abordagens-para-verificacao-formal () |
| MF | `aws-encryption-sdk` | injetado | unidade-02-verificacao-de-programas | ausente | unidade-01-metodos-formais | não | bloco-01 (bloco-01) | abordagens-para-verificacao-formal () |
| MF | `archive-of-formal-proofs-355fb8` | injetado | unidade-01-metodos-formais | ausente | unidade-01-metodos-formais | sim | bloco-01 (bloco-01) | abordagens-para-verificacao-formal (provadores-de-teoremas) |
| MF | `t1-2026-1` | nao_injetado_ja_presente | unidade-01-metodos-formais | ausente | unidade-01-metodos-formais | sim | bloco-11 (bloco-11) | especificacao-de-funcoes-recursivas () |
| IA | `o-que-é-inteligência-artificial-ia-oracle-brasil-43437f` | injetado | unidade-de-aprendizagem-01-visao-geral | ausente | unidade-de-aprendizagem-02-solucao-de-problemas | não | bloco-01 (bloco-01) | problemas-de-otimizacao () |
| IA | `ia-responsável-7c4626` | injetado | unidade-de-aprendizagem-01-visao-geral | ausente | unidade-de-aprendizagem-05-aprendizado-de-maquina | não | bloco-01 (bloco-01) |  () |
| CG | `video-sobre-origens-da-computacao-grafica-806e66` | injetado | unidade-01-introducao-ao-processamento-grafico | ausente | unidade-01-introducao-ao-processamento-grafico | sim | bloco-01 (None) | origens (origens) |
| CG | `video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758` | injetado | unidade-01-introducao-ao-processamento-grafico | ausente | unidade-02-fundamentos-matematicos | não | bloco-02 (None) |  (aplicacoes) |
| CG | `video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e` | injetado | unidade-04-processo-de-visualizacao-2d | ausente | unidade-04-processo-de-visualizacao-2d | sim | bloco-06 (None) | recorte (recorte) |
| CG | `video-sobre-mapeamento-em-opengl-1dad3c` | injetado | unidade-04-processo-de-visualizacao-2d | ausente | unidade-04-processo-de-visualizacao-2d | sim | bloco-06 (None) | recorte (sistema-de-coordenadas-cartesianas) |
| CG | `aula-gravada-975b85` | injetado | unidade-03-processamento-de-imagens-e-visao-computacional | ausente | unidade-06-processo-de-visualizacao-3d | não | bloco-08 (None) | a-matematica-das-projecoes-planares (segmentacao) |
| CG | `video-sobre-prechimento-de-areas-duracao-330-defae7` | injetado | unidade-03-processamento-de-imagens-e-visao-computacional | ausente | unidade-01-introducao-ao-processamento-grafico | não | bloco-01 (None) | areas-relacionadas (segmentacao) |
| CG | `video-sobre-prechimento-de-areas-duracao-1300-d87e5f` | injetado | unidade-03-processamento-de-imagens-e-visao-computacional | ausente | unidade-03-processamento-de-imagens-e-visao-computacional | sim | bloco-07 (None) | cores-e-tipos-de-imagens (segmentacao) |

## Outros ids que mudam

- MF `arvores`: ['bloco-05', 'unidade-01-metodos-formais', ''] → ['bloco-05', 'unidade-01-metodos-formais', 'abordagens-para-verificacao-formal'] (controle ['bloco-05', 'unidade-01-metodos-formais', '']); ok {'bloco': True, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False} → {'bloco': True, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False}; causa: importacao (controle nao muda)
- MF `intro`: ['bloco-05', 'unidade-01-metodos-formais', ''] → ['bloco-05', 'unidade-01-metodos-formais', 'abordagens-para-verificacao-formal'] (controle ['bloco-05', 'unidade-01-metodos-formais', '']); ok {'bloco': False, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False} → {'bloco': False, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False}; causa: importacao (controle nao muda)
- MF `listas`: ['bloco-05', 'unidade-01-metodos-formais', ''] → ['bloco-05', 'unidade-01-metodos-formais', 'abordagens-para-verificacao-formal'] (controle ['bloco-05', 'unidade-01-metodos-formais', '']); ok {'bloco': True, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False} → {'bloco': True, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False}; causa: importacao (controle nao muda)
- MF `provas`: ['bloco-06', 'unidade-01-metodos-formais', ''] → ['bloco-06', 'unidade-01-metodos-formais', 'abordagens-para-verificacao-formal'] (controle ['bloco-06', 'unidade-01-metodos-formais', '']); ok {'bloco': True, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False} → {'bloco': True, 'unidade': True, 'sub_primaria': False, 'sub_aceita': False}; causa: importacao (controle nao muda)
- CG `resolucao-de-prova-de-computacao-grafica-2d`: ['', 'unidade-01-introducao-ao-processamento-grafico', ''] → ['', 'unidade-01-introducao-ao-processamento-grafico', 'origens'] (controle ['', 'unidade-01-introducao-ao-processamento-grafico', '']); ok {'unidade': False} → {'unidade': False}; causa: importacao (controle nao muda)
- CG `resolucao-de-prova-de-computacao-grafica-2d-html`: ['', 'unidade-01-introducao-ao-processamento-grafico', ''] → ['', 'unidade-01-introducao-ao-processamento-grafico', 'origens'] (controle ['', 'unidade-01-introducao-ao-processamento-grafico', '']); ok {'unidade': False} → {'unidade': False}; causa: importacao (controle nao muda)
- CG `resolucao-de-prova-de-computacao-grafica-3d`: ['', 'unidade-01-introducao-ao-processamento-grafico', ''] → ['', 'unidade-01-introducao-ao-processamento-grafico', 'origens'] (controle ['', 'unidade-01-introducao-ao-processamento-grafico', '']); ok {'unidade': False} → {'unidade': False}; causa: importacao (controle nao muda)

## Perdas por eixo

- bloco: nenhuma
- unidade: nenhuma
- sub_primaria: nenhuma
- sub_aceita: nenhuma

## Checks

- baseline_217_246_84_107: True
- builds_base_intocados: True
- repos_reais_intocados: True
- zero_rede_llm: True
- zero_perda: True
- unidade_ge_256_de_284: False

## Campos da entrada real

Mantidos: `id` (identidade (== id do gold)), `title` (identidade), `source_path` (origem), `file_type` (origem), `category` (origem (categoria de entrada)), `source_section` (origem (card Moodle)), `moodle_label` (origem Moodle), `moodle_section_index` (origem Moodle), `moodle_module_index` (origem Moodle), `moodle_week_label` (origem Moodle), `posting_date` (data de origem), `posting_date_created` (data de origem), `tags` (campo do usuario na entrada (vazio nos 12)), `notes` (entrada), `professor_signal` (entrada), `include_in_bundle` (entrada), `relevant_for_exam` (entrada), `processing_mode` (config de extracao), `ocr_language` (config de extracao), `document_profile` (config de extracao), `preferred_backend` (config de extracao), `datalab_mode` (config de extracao), `formula_priority` (config de extracao), `preserve_pdf_images_in_markdown` (config de extracao), `force_ocr` (config de extracao), `extract_images` (config de extracao), `extract_tables` (config de extracao), `page_range` (config de extracao), `effective_profile` (proveniencia de extracao), `base_backend` (proveniencia de extracao), `advanced_backend` (proveniencia de extracao), `document_report` (proveniencia de extracao), `pipeline_decision` (proveniencia de extracao (backend, nao atribuicao)), `extracted_files` (proveniencia de extracao), `clone_error` (proveniencia de extracao (clone falhou na origem)), `base_markdown` (texto (snapshot local)), `advanced_markdown` (texto), `approved_markdown` (texto curado), `curated_markdown` (texto curado), `approved_source_markdown` (proveniencia do texto curado), `approved_at` (data de origem da curadoria de TEXTO), `review_status` (estado da curadoria de TEXTO), `raw_target` (arquivo bruto), `advanced_metadata_path` (proveniencia de extracao)

Descartados: `temporal_block_*` (decisao de bloco do motor (id/metodo/banda/flag/provider/janela)), `computed_*` (decisao do motor (bloco/unidade/subunidade computados)), `manual_*` (pino/curadoria manual (manual_tags/unit/block) ou artefato de revisao (manual_review)), `auto_*` (tags automaticas derivadas de decisoes), `unit_*` (evidencia/conflito da decisao de unidade), `subunit_*` (evidencia da decisao de subunidade), `coverage_*` (cobertura derivada da unidade), `revisar` (fila de revisao derivada das bandas/flags), `unit_slug` (decisao de unidade). Defaults de entrada nova (sem pino): {'manual_tags': [], 'manual_unit_slug': '', 'manual_timeline_block_id': ''}.

## Limitações

- Ponte gold->build: os 13 tem new_id nulo em herancas_<sig>_15-09.json; a regua oficial nao os liga. Depois da importacao, liga pelo id preservado (== gold_id), com origem unica asserida na importacao.
- t1-2026-1 nao foi injetado: o build-base do MF ja tem a entrada com o mesmo id e bytes identicos do PDF (source_path do stash, nao de Downloads); injetar duplicaria o material. Ligado por id tambem em 'antes_ponte_estendida' para separar ganho de ponte de ganho de importacao.
- Entradas injetadas vao ao fim da lista de entries (como uma entrada nova do produto).
- Perfil do reprocess = SubjectStore do repo real + profile_input do build (_inputs_15-09.json), use_llm_voter/compile_vocabulary desligados e TUTOR_NO_VOCAB_COMPILE=1 (mesma politica do build-base).
- Os 4 cursos sem copia (SO, ES2, TCC, FR) usam o baseline em controle e depois.
