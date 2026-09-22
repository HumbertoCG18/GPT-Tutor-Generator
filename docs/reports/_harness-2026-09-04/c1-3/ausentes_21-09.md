# W-A — ausentes: diagnóstico de 21/09/2026

## Resultado

**12 links não são materializados pela entrada stash-only; o PDF é falso ausente por identidade de caminho.** O PDF `t1_2026_1.pdf` está no pacote, com o mesmo ID e bytes da baseline, mas outro `source_path`. Não houve build, replay do motor, rede, chamada adicional de LLM, alteração em `src/`, stage ou commit. Gold não alimentou nenhum processamento.

Checkout examinado: `alethe/agent-job-01`, HEAD `ce02a8f47285c30c16f12b131bdf86c46dcba64e`, árvore inicialmente limpa. Rota: pesquisa/diagnóstico read-only, T2 pelo cruzamento ingestão/manifest/atribuição; execução local pelo trabalhador já designado, sem delegação adicional. Skills consultadas: systematic-debugging e graphify-windows. Não existe `graphify-out` nem `.workflow-local/active-task.md` neste worktree; estrutura confirmada diretamente no código, sem gerar índice. Nenhum gate de implementação/commit foi exercido.

## 1. Onde os links deixam de entrar

- `src/builder/sources/moodle.py:145-158`, `iter_section_files`: só aceita `contents[].type == "file"` (linha 151). Módulos com conteúdo `type="url"` não viram arquivos dessa lista.
- `src/builder/core/stash_import.py:67-96`, `scan_stash_cards`: percorre exclusivamente `root.rglob("*")` e arquivos físicos. `_classify_file_type` (39-58) reconhece PDF/imagem/ZIP/HTML/código; não cria `url` nem `github-repo`, nem expande o conteúdo de `links.json`. Metadados lidos pelo scan: `.moodle_nomes.json` (77-83).
- `build_stash_entries`, no mesmo arquivo:126-157, só transforma `scan.items` em `FileEntry`. Herda título do stem, seção do card e moodle_label; não descobre links.
- `docs/reports/_harness-2026-09-04/c1-3/cru_fontes_15-09.py:69-85` define stash pelo perfil e constrói entries só desse scan, com conjunto de caminhos existentes vazio. Linha 108 esvazia a queue; 119-120 passa as entries ao builder. Não é o filtro de backlog da UI.
- `pacote_fontes_15-09.py:32-49,58-62` reutiliza esse construtor e acrescenta captura Moodle/backfills. Em `src/builder/sources/moodle.py:577-589,619-626`, os backfills percorrem entries já existentes; não criam as entradas ausentes. Ter `contents.json` no pacote não basta.
- `src/builder/ops/build_workflow.py:52-70` inicia manifest vazio e acrescenta resultados de entries habilitadas processadas. **Não existe rejeição global de links no manifest:** `src/builder/ops/entry_processing.py:65-75` aceita explicitamente `url` e `github-repo`.

Há uma rota própria reutilizável: `src/builder/sources/moodle_sync.py:174-197`, `plan_import`, converte links com `acao="referencia"` em `FileEntry` (título e seção), separa `review`, ignora outras ações/URL vazia e deduplica URLs. O harness acima não chama essa rota. Ela cria referências URL, não reproduz automaticamente a importação especializada `github-repo`.

## 2. PDF: entrou, mas a régua não o casa

Em `herancas_MF_15-09.json:851-856`, a origem avaliada é `c:\users\humberto\downloads\t1_2026_1.pdf`.

Nos artefatos persistidos fora deste worktree, lidos apenas como evidência:

- `.frzero/pacote_fontes_15-09/Metodos-Formais-Tutor/_inputs_15-09.json:3` registra stash `C:\Users\Humberto\Desktop\Moodle\metodos-formais-para-computacao`.
- Mesmo arquivo:310-315 inclui `TDE Trabalho Discente Efetivo\t1_2026_1.pdf`, tipo `pdf`, categoria `outros`, seção TDE; não consta nos skipped.
- `.frzero/implementacao_taxonomia_15-09/Metodos-Formais-Tutor/manifest.json:3081`: source em Downloads.
- `.frzero/pacote_fontes_15-09/Metodos-Formais-Tutor/manifest.json:4252`: source no stash. Ambos têm ID `t1-2026-1`.

**Medido nesta investigação:** SHA-256 dos dois `raw_target` e do PDF atual do stash é idêntico: `3783080014067b612e18b262863fc8b78df61ecea7af4580543461ad8dce6cf6`. O hash também coincide com o inventário persistido. O caminho Downloads atualmente não existe; isso não prova sua ausência na data do build.

Causa da classificação: `compara_herancas_15-09.py:25-35` normaliza o caminho completo, sem equivalência por hash; 94-103 exige origem única igual e grava `entrada_ausente` se não há match. Logo, não é extensão rejeitada (`.pdf` é aceito em `stash_import.py:44-45`), filtro ou falha de extração deste PDF. É **ausência da origem exata da baseline**. A homonímia com `t1_2026_1.thy` não explica o caso: o PDF foi encontrado e seus bytes conferidos.

Os caminhos `.frzero/...` desta seção e da tabela abaixo são relativos a `C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator`, não ao worktree isolado.

## 3. As 13 entradas classificadas como ausentes

IDs e ausência vêm dos JSONs versionados `herancas_{curso}_15-09.json`; tipo exato vem do manifest da baseline. Títulos/seções dos links abaixo vêm da captura bruta do pacote, casada por **igualdade exata** de `contents[].fileurl`, sem usar gold. Data é `timemodified` em UTC, não necessariamente data da aula. H = arquivo `herancas_{curso}_15-09.json` no diretório deste relatório; C = `.frzero/pacote_fontes_15-09/<curso>/raw/moodle/contents.json`.

| Curso | ID | Tipo | Título na fonte | Seção; data bruta UTC | Evidência |
|---|---|---|---|---|---|
| CG | `video-sobre-origens-da-computacao-grafica-806e66` | url | Vídeo sobre Origens da Computação Gráfica | 1 - Origens da Computação Gráfica; 2021-02-24 | H:1830; C:656 |
| CG | `video-com-instrucoes-para-usar-opengl-na-vdi-da-pucrs-3a8758` | url | Vídeo com instruções para usar OpenGL na VDI da PUCRS | 2 - Biblioteca OpenGL; 2025-03-04 | H:1860; C:873 |
| CG | `video-sobre-o-algoritmo-de-recorte-por-subdivisao-binaria-db7e2e` | url | Vídeo sobre o Algoritmo de Recorte por Subdivisão Binária | 6 - Processo de Visualização 2D; 2020-09-29 | H:1890; C:1950 |
| CG | `video-sobre-mapeamento-em-opengl-1dad3c` | url | Vídeo sobre MAPEAMENTO em OpenGL | 6 - Processo de Visualização 2D; 2020-09-29 | H:1920; C:2117 |
| CG | `aula-gravada-975b85` | url | Aula gravada | 11 - Morfologia Matemática; 2020-03-25 | H:1948; C:3808 |
| CG | `video-sobre-prechimento-de-areas-duracao-330-defae7` | url | Vídeo sobre Prechimento de Áreas (Duração 3:30) | Exercícios de Processamento de Imagens; 2022-03-07 | H:1978; C:4006 |
| CG | `video-sobre-prechimento-de-areas-duracao-1300-d87e5f` | url | Vídeo sobre Prechimento de Áreas (Duração: 13:00) | Exercícios de Processamento de Imagens; 2022-03-07 | H:2004; C:4052 |
| IA | `o-que-é-inteligência-artificial-ia-oracle-brasil-43437f` | url | O que é IA? | Semana 1 - 02/03 a 06/03 - Plano de Ensino e Introdução a IA; 2025-07-28 | H:50; C:1410 |
| IA | `ia-responsável-7c4626` | url | IA Responsável | Semana 1 - 02/03 a 06/03 - Plano de Ensino e Introdução a IA; 2025-07-28 | H:79; C:1502 |
| MF | `eth2` | github-repo | Motivação: Formal Verification of the Ethereum 2.0 (GitHub) | Introdução a Métodos Formais; 2026-02-27 | H:58; C:1062 |
| MF | `aws-encryption-sdk` | github-repo | Motivação: AWS Encryption SDK (Dafny) | Introdução a Métodos Formais; 2026-02-27 | H:86; C:1200 |
| MF | `archive-of-formal-proofs-355fb8` | url | Archive of Formal Proofs - Repositório para Isabelle | Provas por Indução; 2026-03-29 | H:114; C:3322 |
| MF | `t1-2026-1` | pdf | t1_2026_1 | TDE Trabalho Discente Efetivo; 2026-04-15 | H:851; manifest pacote:4252 |

## 4. Sinais disponíveis e o que falta

**Fatos sustentados:** os 12 URLs constam na captura Moodle com título e seção (linhas C da tabela). CG tem seções temáticas; IA tem uma seção semanal com intervalo explícito; MF tem seções temáticas. Os timestamps de CG/IA são antigos e não devem ser promovidos automaticamente a datas da aula de 2026. Na baseline, os 12 links não têm posting_date; os sete CG têm source_section, enquanto os dois IA e três MF não têm. A captura bruta oferece mais estrutura que esses manifests históricos.

O motor possui consumidores para esses sinais: `src/builder/routing/motor/window_provider.py:23-42` consulta seção/card no card_block_map; `window_provider.py:353-363` procura data no prefixo de título/label/card/basename. `src/builder/routing/motor/disambiguator.py:54-56` usa título, moodle_label e Markdown. Para unidade, `src/builder/extraction/entry_signals.py:151-168` fornece título/headings/texto/categoria; `src/builder/routing/file_map.py:474-486,522-568` pontua e sinaliza ambiguidade. Referência sem card ainda possui tratamento próprio (`src/builder/routing/motor/apply.py:105-108`); ausência de data não implica necessariamente abstenção.

Os registros históricos `herancas_*` mostram pred_before não vazio para bloco/unidade nos 13 casos, mas isso NÃO mede resultado do pacote com links incluídos: a baseline contém outras heranças/textos. Não usar esses resultados como autorização para copiar atribuições.

O PDF já fornece sinal real no pacote: título `t1_2026_1`, seção `TDE Trabalho Discente Efetivo`, label `Definição`, posting_date `2026-04-15`; documento reporta 2 páginas e 3029 caracteres. Seu manifest registra `computed_unit_slug=unidade-01-metodos-formais`, `computed_block_method=concept-fused`, mas não `temporal_block_id`. A régua lê `manual_timeline_block_id` ou `temporal_block_id`, não `computed_block_id` (`compara_herancas_15-09.py:39-45`). Assim, mesmo reconhecendo identidade por bytes, não se pode conceder automaticamente acerto de bloco nem unidade. A baseline registra unidade-02 e temporal por prazo; categoria mudou de trabalhos para outros. A causalidade individual dessa mudança não foi testada aqui.

**Necessário para inclusão futura, sem implementação:**

1. Materializar os 12 links a partir de inventário bruto autorizado (por exemplo, a rota existente `plan_import`), passando as entries ao builder e preservando URL/título/seção. Decidir explicitamente se os dois GitHub são referência ou importação de repositório.
2. Definir uma entrada offline para texto/captura dos links. Apenas acrescentar `FileEntry(url)` ao build atual tentaria rede: `src/builder/ops/url_and_cleanup.py:71-98` faz urlopen; em erro produz título/URL, não conteúdo do vídeo. `src/builder/core/source_importers.py:275-308` processa URL e consulta/clona GitHub. O harness bloqueia conexão em `cru_fontes_15-09.py:50-55`; portanto adição ingênua não satisfaz o contrato zero-rede.
3. Para o PDF, não há necessidade de reimportá-lo. Qualquer futura equivalência de avaliação entre origens precisa de contrato auditável de identidade (hash e unicidade), mantendo denominadores e gold reservado à avaliação. Não modificar placares retroativamente por ID/título apenas.
4. Só uma avaliação posterior autorizada pode determinar abstenção/acerto dos links com esses sinais. Nenhuma execução desse contrafactual foi feita.

## Hipóteses e limitações

- Hipótese: títulos temáticos e seções de CG/MF, e a semana explícita de IA, podem fornecer janelas/sinais úteis. Não foi medido se cruzariam limiares ou se resolveriam conflitos. `Aula gravada` depende especialmente da seção/texto; seu título isolado é pouco informativo.
- Não há fundamento para afirmar que as 13 seriam corretas, nem que as 12 URLs cairiam todas em abstenção. Inclusão, identidade e acerto são problemas distintos.
- Permanecem os denominadores 237/284 e a regra de ausência da régua original. Os placares 213/237 e 239/284 informados no brief não foram recalculados aqui. 219/237 e 252/284 continuam somente teto aritmético informado, não ganho medido; agora há evidência de que um dos 13 já entrou fisicamente.
- Hashes foram medidos nos artefatos persistidos atuais; não houve reconstrução histórica. JSONs de heranças são do cru de 15/09; a presença física do PDF foi adicionalmente confirmada no pacote de 15/09. Não foi inspecionado o build de 17/09 nem repetida a avaliação dos sete cursos.
- A ausência de graphify-out impediu consulta estrutural por grafo; não foi criado índice. Nenhum arquivo além deste relatório foi criado intencionalmente; conferência final por git status/diff. Investigação encerrada no escopo autorizado.
