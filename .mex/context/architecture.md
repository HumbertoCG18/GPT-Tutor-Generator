---
name: architecture
description: Mapa estável de pacotes, pipeline e motor, no nível de responsabilidade. Fallback quando o Graphify não está disponível; o código decide.
triggers:
  - arquitetura
  - estrutura
  - pacote
  - pipeline
  - motor
  - onde fica
edges:
  - target: context/sessao-nuvem.md
    condition: quando a sessão não tem Graphify, tutores locais ou o laboratório
  - target: context/repo-output.md
    condition: quando o assunto é o repositório-tutor gerado
  - target: context/pdf-pipeline.md
    condition: quando o assunto é extração de PDF
  - target: context/decisions.md
    condition: antes de propor mudança de arquitetura ou do motor
last_updated: 2026-09-24
---

# Arquitetura

Reativado em 24/09/2026. Estava aposentado desde 06/08 em favor do Graphify, mas sessões na
nuvem e agentes sem graphify-out/ (ignorado pelo git) precisam de um mapa. Regra deste arquivo:
só pacote e responsabilidade, sem contagens nem inventário de arquivos, que envelhecem. Com o
Graphify disponível, ele e o código decidem. Conferido em feat/motor-atribuicao @ 26320215.

## Camadas

- **Entrada pela UI**: `app.py` → `src/__main__.py` → `src/ui/app.py` (classe `App`, Tkinter).
  Build e reprocessamento rodam em threads daemon com `progress_callback`. `src/ui/dialogs.py`
  passa de 100 KB. Exceção conhecida à fachada: `dialogs` importa `src/builder/sources` direto.
- **Entrada por script** (`scripts/`): `scripts/build_course.py` segue o mesmo caminho da UI (perfil →
  stash → `RepoBuilder.build`); `scripts/reprocess_assignments.py` roda o build incremental sem backends
  pagos; `scripts/eval_eixos.py` e `scripts/eval_ground_truth.py` medem contra a régua; `scripts/sync_moodle.py`,
  `scripts/rebuild_timeline.py`, `scripts/motor_puro.py` e `scripts/course_probe.py` servem ao motor e ao diagnóstico.
- **Fachada** `src/builder/engine.py`: `RepoBuilder` (cada método delega a ops/*), backends de
  PDF, `BackendSelector`, aliases de compatibilidade e `__all__`. Não recebe lógica nova; o hook
  `scripts/hooks/engine-facade-guard.js` bloqueia `def` novo de nível superior.
- **Modelos** (`src/models/`): `src/models/core.py` tem `FileEntry`, `SubjectProfile` (com `feature_flags`),
  `ProcessingProfile`, `StudentProfile` e `SubjectStore`, que lê subjects.json no diretório de
  dados do app, fora do repositório. `src/models/task_queue.py` e `src/models/tag_profile.py` completam.
- **Utilitários**: `src/utils/helpers.py` concentra escrita atômica (`write_text`,
  `write_json_manifest`: tmp + `os.replace` + `.bak`), o carregador do `.env` e a detecção de CLIs.

### Subpacotes de `src/builder/`

| Pacote | Responsabilidade |
|---|---|
| `src/builder/ops/` | Orquestração: `build_workflow`, `incremental_build`, `entry_processing` (despacho por tipo), `pedagogical_regeneration` (camadas do motor), `assignment_run`, `bootstrap_ops`, `lifecycle_ops`, `task_queue_runner`, `state_ops` |
| `src/builder/routing/` | Roteamento de material: `file_map` (leitura do bloco efetivo), `concept_resolver` e `resolver_apply` (escrevem `computed_*`), `coverage_rules`, `dates`, `sequence`, `thresholds` |
| `src/builder/routing/motor/` | Motor de âncora temporal (D9): `anchor_engine`, `apply`, `card_stream`, `context`, `contracts`, `disambiguator`, `due_window`, `llm_vote`, `metrics`, `window_provider` |
| `src/builder/timeline/` | Cronograma: `index` (índice de blocos), `block_identity` (ledger de UUID), `classifier`, `kinds`, `unit_matcher` (DP posicional bloco → unidade), `card_block`, `curation`, `conflicts`, `signals` |
| `src/builder/extraction/` | Taxonomia e sinais: `content_taxonomy`, `entry_signals`, `teaching_plan`, `image_markdown` |
| `src/builder/artifacts/` | Artefatos do tutor: `navigation`, `prompts`, `pedagogy`, `repo`, `student_state`, `temporal_context`, `cronograma_health`, `build_metrics` |
| `src/builder/core/` | Conteúdo: `code_summarization`, `reference_*`, `html_material`, `source_importers`, `stash_*`, vocabulário |
| `src/builder/pdf/` | Análise, assets, pipeline e escaneados |
| `src/builder/runtime/` | Clientes: `backend_runtime`, `datalab_client`, `gemini_client` |
| `src/builder/sources/` | Moodle e M365 |
| `src/builder/text/` | Normalização, stopwords, tokens |
| `src/builder/vision/` | Ollama, classificador de imagem, evidência de card |
| `src/builder/facade/` | Fábricas dos aliases usados por `src/builder/engine.py` |

## Pipeline

1. **Entrada**: `src/builder/ops/entry_processing.py` despacha por tipo (url, repositório GitHub, html,
   código, zip, pdf, imagem). O loop do build atribui id com dedup e grava o manifest de forma
   atômica a cada entrada. Fontes do professor: Moodle ou M365 (um canal por curso), cronograma
   do SARC (só por URL), plano de ensino (vira taxonomia) e stash local (pasta imediata vira
   `source_section`). Detalhes em [institutional.md](institutional.md).
2. **Extração**: perfil → decisão → escaneado → base (`pymupdf4llm`, `pymupdf`) → avançado
   (Datalab pago, Marker, Docling) → assets. Ordem e fallback em [pdf-pipeline.md](pdf-pipeline.md).
   Texto que o motor pontua segue `approved > curated > base > advanced`
   ([text-chain.md](text-chain.md)).
3. **Pós-build**: FILE_MAP → poda de caches → resumo determinístico de código → descrições de
   imagem → `regenerate_pedagogical_files` → manifest.
4. **Motor** (`src/builder/ops/pedagogical_regeneration.py`, em ordem): novo `assignment_run`; estrutura do
   Moodle; vocabulário por LLM (opt-in); taxonomia; .timeline_index.json e bloco → unidade;
   contexto de avaliações; setup/ e system/; COURSE_MAP.md e GLOSSARY.md; `auto_tags`;
   resíduo por Gemini (opt-in); `apply_concept_resolver` (grava `computed_*`); camada D9 (grava só
   `temporal_*`, por flag); reconciliação de unidade e subunidade contra o bloco temporal;
   `manifest["assignment_run"]`. Camadas opcionais nunca derrubam a regeneração.
5. **Artefatos**: instruções para três LLMs, system/, README, COURSE_MAP.md, GLOSSARY.md e
   índices. Estrutura da saída em [repo-output.md](repo-output.md).

## Regras de leitura do motor

- Bloco efetivo: `temporal_block_id` (D9) > pino manual > `computed_*`
  (`src/builder/routing/file_map.py`, `resolve_effective_block` e `resolve_temporal_block`).
- Cascata do D9 (`src/builder/routing/motor/apply.py`): pino manual > due-window > fora de escopo > cache por
  md5 > engine. Nunca toca `computed_*` nem o pino manual.
- `feature_flags` (padrões em `src/builder/ops/assignment_run.py`): `use_concept_resolver` ligado;
  `use_anchor_engine`, `use_llm_voter`, `compile_vocabulary` e `enable_material_residual`
  desligados. Flag desligada deve dar saída byte-idêntica.
- `bloco-NN` é posicional; referência durável é `block_uuid`. A unidade vem do cabeçalho do plano,
  nunca do prefixo do código do tópico ([institutional.md](institutional.md)).

## Serviços

Gemini (opt-in, `google-genai` com import lazy, chave no config do app ou em `GEMINI_API_KEY`),
Datalab (pago, `DATALAB_API_KEY`), Ollama (local), Moodle e M365 (tokens em moddle/, ignorado),
GitHub (API anônima). Sem chave, cada camada registra fallback e segue. Custos e degradação em
[external-services.md](external-services.md).

## De onde a taxonomia vem (medido em 07/09)

`src/builder/extraction/content_taxonomy.py` (`build_content_taxonomy`) monta a taxonomia de tres fontes, e só três:

- **tópicos**: `parse_units_from_teaching_plan` sobre o plano de ensino (fallback COURSE_MAP).
- **aliases 1**: `_glossary_aliases_for_topic` sobre o <repo-tutor>/GLOSSARY.md, cujos sinônimos vêm do sidecar
  <repo-tutor>/course/.glossary_curation.json.
- **aliases 2**: `collect_strong_heading_candidates`, os headings dos próprios materiais.

**O SARC e o Moodle não entram na taxonomia.** Os labels de sessão do cronograma alimentam só o alinhamento
bloco→unidade (`src/builder/timeline/unit_matcher.py`, `assign_units_positional`); título, label e seção do Moodle entram como sinal no
scorer de entrada e na regra S1b, nunca como alias. O único canal de vocabulário concreto é o sidecar.

Teto medido de cada fonte contra 222 materiais com gold (`docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.log`): o rótulo literal do
plano alcança o subtópico certo em 12% dos materiais, título e label do Moodle em 42%, o label da sessão do SARC em
40%, os headings do material em 37%. Plano, SARC e Moodle juntos chegam a 62%, e 22% dos materiais não são alcançáveis
por fonte nenhuma do professor. O plano de ensino é a fonte mais fraca: ele nomeia a categoria, o material nomeia o
objeto.
