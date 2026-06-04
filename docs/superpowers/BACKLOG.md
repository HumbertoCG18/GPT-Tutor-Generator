# Backlog de Melhorias — branch new-features

last_updated: 2026-06-04

Itens propostos durante o thread de precisão de atribuição (jun/2026). Cada um tem
contexto suficiente pra retomar sem reabrir a discussão. Ordem = prioridade sugerida.

## Estado atual

**Entregue nesta branch:**
- **#1 Harness de avaliação** — `scripts/eval_assignments.py` + gate `tests/test_eval_assignments.py`. Mede acurácia arquivo→bloco pelo scorer real contra gold set.
- **#2 Sinal de sequência** — `src/builder/routing/sequence.py`. "Aula 03" → boost +0.20 no 3º bloco `kind=class`. Só marcadores `aula`/`encontro`.

- **Referências como contexto do tutor** — ENTREGUE. 8 tasks TDD (`src/builder/core/reference_content.py`, `reference_topic.py`, `reference_summary.py`; campos `ref_*` em `FileEntry`; surfacing em `bibliography_md`; wiring em `build_workflow`). Busca conteúdo leve sem clone (README via API GitHub / texto via `url_markdown`), resumo Gemini lazy, mapeamento determinístico a unidade/tópico, cache `references_curation.json`.
  **2 defeitos reais achados na revisão final do wiring (Task 8), corrigidos:**
  1. `27f5d80` — batch de referência estava **após** `if client is None: return` em `_run_auto_code_summarization`. Sem `gemini_api_key`, as referências não eram mapeadas — contrariava o modo degradado do spec ("sem Gemini → mapeia por texto"). Fix: resumo de código fica Gemini-gated; enriquecimento de referência roda com `client` possivelmente `None`.
  2. `0b1683f` — `summarize_all_reference_entries` grava os campos `ref_*` no `manifest.json` em disco, mas o build segurava um `manifest` em memória stale; a regeneração pedagógica renderizava dele e a escrita final o sobrescrevia, perdendo os campos. Fix: reload do manifest pós-enriquecimento (espelha o reload pós-prune).

---

### Chave Gemini via `.env` (`GEMINI_API_KEY`)
**Status:** RESOLVIDO nesta branch (`7e0d1a9`).
**Resumo do gap:** o client Gemini lia a chave só de `config.get("gemini_api_key")` (`~/.gpt_tutor_config.json`, via UI) — `GEMINI_API_KEY` no `.env` era ignorado, ao contrário do `DATALAB_API_KEY`. Code summary **e** enriquecimento de referência ficavam mudos sem mexer na UI.
**Fix entregue:** `_resolve_gemini_key` (`gemini_client.py`) com precedência **config (UI) > `GEMINI_API_KEY` do `.env`/ambiente**; `has_gemini_api_key`/`get_gemini_client` reescritos sobre ele. `.env` já carrega em `os.environ` no import (`helpers._load_project_env_file`). TDD: `tests/test_gemini_key_source.py` (6 casos). 858 testes verdes.
**Follow-up aberto:** dialog de settings (`dialogs.py`) podia exibir dica "ou defina `GEMINI_API_KEY` no `.env`" igual ao DATALAB. Cosmético, UI — fora do escopo do fix.

---

## Parados

### Verbosidade do manifest.json — `to_dict` serializa todos os defaults
**Status:** RESOLVIDO nesta branch (rodada de refatoração). Plano `docs/superpowers/plans/2026-06-04-refator-manifest-referencias.md`.
- **Opção 2 (ref_* → curation-only):** campos `ref_*` removidos do `FileEntry`; `bibliography_md` lê de `references_curation.json` por `entry.id()` (espelha `code_health_md`); batch grava só a curation; hack de reload do manifest removido. (`088f7f3`, `4ada78a`, `98155b4`)
- **Opção 1 (omit-defaults global):** `FileEntry.to_dict` omite campos iguais ao default; required sempre presentes; `from_dict` tolera ausentes (round-trip seguro). (`2a9436a`)
- Follow-up aberto: auditar consumidores diretos do manifest.json (dashboard/JS) que assumam todas as chaves presentes. Suíte (846) verde não acusou nenhum em Python.

_Histórico do problema (resolvido):_
**Resumo:** `FileEntry.to_dict()` é `dataclasses.asdict(self)` — serializa os ~35 campos em **toda** entry, inclusive os iguais ao default. Cada PDF/código carrega `ref_summary:"", ref_concepts:[], computed_ref_unit:"", computed_ref_topics:[]` (~95 bytes mortos/entry) + dezenas de knobs de processamento (`datalab_mode`, `ocr_language`, `force_ocr`, `extract_tables`, `unit_match_reasons`, …) repetidos. Os 4 campos `ref_*` são adição marginal; a raiz é o dump flat de todos os defaults.
**Duas saídas (ortogonais à feature, não implementar sem decisão):**
1. **Omit-defaults global:** `to_dict` omite campos iguais ao default. Encolhe **toda** entry. `from_dict` já tolera chaves ausentes (filtra para campos válidos, default preenche) e leitores usam `.get` — round-trip seguro, mas auditar consumidores diretos do JSON (dashboard/JS).
2. **Mover `ref_*` para `references_curation.json` apenas** (como os resumos de **código**, que vivem só em `code_curation.json`, não no manifest). Remove 4 campos de toda entry **e** elimina o hack de reload do manifest. Exige `bibliography_md` ler da curation em vez dos objetos entry. Mais consistente com o padrão de código, porém refatora Task 6/7/8.
**Recomendação:** opção 2 para `ref_*` (consistência + remove o reload), opção 1 como item separado de higiene geral do manifest.

### #3 — Decay de distância de data + fix de virada de ano
**Status:** desenhado, NÃO implementado. Valor medido ≈ 0 nos dados reais.
**Resumo:** trocar o boost binário de data (`_score_block_date_match`, `file_map.py`) por decay linear: in-range = 0.30; fora = `0.10 * (1 − dist/30)`, clamp 0, `max` sobre as datas do material. Distância real em dias mata o bug `start.month <= dt.month <= end.month` (quebra na virada de ano). Virada de ano vira **propriedade de segurança** (data com ano errado → distância enorme → 0, nunca boost espúrio), não feature.
**Por que parou:** investigação nos 5 repos reais mostrou ~98% dos materiais já em band "alta", 1 media + 1 baixa em ~127. O decay ataca a faixa media/baixa (vão entre blocos), que quase não existe. Reabrir só se aparecer reposição/data-fora-da-grade que erre.
**Calibração já decidida:** linear, horizonte 30 dias (vão semanal cabe folgado).

### #4 — Piso de winner absoluto na confidence band
**Status:** proposto, não desenhado em detalhe.
**Resumo:** `confidence_band` (thresholds.py) deriva a faixa só da margem (`margin_confidence`). Dois "média" podem ter qualidade diferente. Misturar a magnitude absoluta do winner na band força revisão de matches fracos-mas-não-ambíguos.
**Por que parou:** baixa prioridade — dados reais quase todos "alta".

### Horário (cadência de aula) — processar o field do gerenciador
**Status:** investigado, valor real menor que o esperado.
**Resumo:** `SubjectProfile.schedule` ("Seg/Qua 10:15-11:55", `core.py:160`) é só texto de exibição (prompts + README), nunca parseado. Parsear → dias de aula destravaria: validar datas extraídas, horizonte adaptativo pro #3, distinguir aula vs reposição.
**Por que parou:** a killer-app (gerar a sequência canônica de datas) está **bloqueada por dados** — não há calendário acadêmico estruturado (feriados só vêm do texto do cronograma; `semester` é string livre) — **e é redundante**: o cronograma já carrega as datas reais das aulas. Ganho restante é modesto. Campo `schedule` está vazio em todos os 5 repos reais.

### Conserto do clone completo de repo GitHub
**Status:** RESOLVIDO nesta branch (`2d3081b`).
**Resumo do bug:** `process_github_repo` (`source_importers.py`) forçava branch `main` → repos com default `master`/outro falhavam (`Remote branch main not found`). Repos grandes falhavam no checkout por long-path do Windows (`Filename too long`). Resultado: 8/8 referências com `extracted_files=0`.
**Fix entregue:** `_detect_default_branch` via `git ls-remote --symref HEAD` (tags ainda pinam branch explícito; vazio → default detectado; fallback `main` seguro) + clone roda com `git -c core.longpaths=true`. TDD: `tests/test_github_clone_branch.py` (6 casos). Destrava análise de código de repo GitHub e fetch profundo de referência.
**Follow-up aberto:** `prompts.py:484` ainda monta o raw URL do **repo de saída do próprio tutor** com `/main` fixo (`raw.githubusercontent.com/.../main`). Mecanismo distinto (sem clone; é o repo que o tutor gera) e sem fonte de branch disponível no `subject_profile` — repo de saída quase sempre é `main`. Tratar só quando houver um campo de branch no perfil.

### Validação end-to-end da pipeline de referências
**Status:** RESOLVIDO nesta branch. Harness `scripts/validate_references_e2e.py`.
**O que rodou:** pipeline real (`summarize_all_reference_entries`) contra repo temporário com 2 refs reais — `github.com/pallets/flask` (github-repo) + `docs.python.org/3/library/json.html` (doc URL) — `GEMINI_API_KEY` do `.env`, Gemini `gemini-2.5-flash` de verdade. Resultado: fetch real OK (README via API GitHub + HTML via `html_to_structured_markdown`), resumo + conceitos Gemini preenchidos (PT-BR), mapeamento determinístico **correto e distinto** (flask→`web`, json→`serializacao`), persistência em `references_curation.json` OK.
**Achado real:** `google-genai` (declarado em `pyproject.toml:25`) **não estava instalado** no venv ativo. A degradação era silenciosa — `summarize_reference` engole o `ImportError`, loga `[ReferenceSummary] falha: google-genai não instalado` e segue com resumo vazio. Build não falha, ninguém percebe sem ler log. Resolvido instalando (`google-genai 2.8.0`); revalidado caminho feliz.
**Follow-up aberto:** não validado o render final em `BIBLIOGRAPHY.md` num build completo (harness para no curation). Modo degradado (sem chave/SDK) já coberto por teste unitário. Considerar um warning mais visível quando o SDK falta mas a chave está presente (hoje é só log de erro por entry).

### Higiene dos MDs do tutor (audit 2026-06-04)
**Status:** auditado, NÃO corrigido. Achados de 4 auditores paralelos sobre os geradores
de MD que o tutor lê. **Nenhuma mecânica de tags antiga sobrou** — mas há dessincronização,
tabelas mortas, duplicação e ambiguidade. Ordenado por gravidade. A redundância da tabela
de relevância da BIBLIOGRAPHY **não** entra aqui — vai junto do Approach C.

**🔴 Grave (engana o tutor):**
- `repo.py:50-65` PROGRESS_SCHEMA dessincronizado do student_state v2: status `não iniciado/com dúvidas/concluído` vs real `pendente/em_progresso/compreendido/revisao`; campo `last_updated` vs real `updated`; path `student/PROGRESS_SCHEMA.md` (deletado como obsoleto) vs gravado em `build/`. Schema descreve vocabulário que o gerador nunca emite. Template "Atualização sugerida" (markdown) não bate com o YAML+baterias do v2.
- `prompts.py:484` `/main` hardcoded no raw URL do repo de saída (já listado em "Conserto do clone").

**🟠 Tabelas mortas / ruído lido pelo tutor (gasta token + confunde):**
- `repo.py:746` bibliography: colunas `Acessível` (sempre "sim") + `Incidência em prova` (sempre "—"). [coberto pela limpeza do Approach C]
- `repo.py:790,794` exam_index: `Incidência P1/P2/P3` + `Padrões de questão` sempre `[a preencher]`.
- `repo.py:822,825` assignment: `Status` sempre "pendente"; `Padrões` `[a preencher]`.
- `repo.py:1049` comentário `<!-- TODO (material-agnostic refactor) -->` vazando no output do CRONOGRAMA lido pelo tutor.
- whiteboard/exercise: `Padrões pedagógicos` / linhas `[a preencher]` permanentes.

**🟡 Duplicação (risco de divergência ao editar):**
- `pedagogy.py:192-224 vs 286-302` lógica de escopo de prova (P1/P2/P3, pesos) escrita 2x (pedagogy_md + modes_md).
- sequência pedagógica em **3 ordens divergentes** (PEDAGOGY 8 passos / MODES 5 / OUTPUT_TEMPLATES outra) — `pedagogy.py:251-256,362-386` + prompts.
- `prompts.py` 5 modos redefinidos inline nas 3 variantes (Claude/GPT/Gemini) **e** em MODES.md.
- `pedagogy.py:323-353 vs 462-489` postura code_review em modes_md e output_templates_md.
- `repo.py:1019` CRONOGRAMA_DETALHADO vs CODE_INDEX (por bloco); `cronograma_health` vs CODE_HEALTH (cobertura/órfãos) sobrepõem.

**🟢 Ambiguidade / labels:**
- `pedagogy.py:240` "opera em **quatro** modos" mas lista **cinco**.
- `pedagogy.py:260` modo `assignment` opera sobre `exercises/` — funde lista vs trabalho (`assignments/`).
- `repo.py:756,803,827,1142,1694` labels de clamp errados (BIBLIOGRAPHY/EXAM/ASSIGNMENT/WHITEBOARD/GLOSSARY rotulados como COURSE_MAP/FILE_MAP). [756 corrigido no Approach C]
- `prompts.py:564` ordem de navegação contraditória entre variantes + contrato map-first (FILE_MAP vs COURSE_MAP qual 1º).
- `navigation.py:731` FILE_MAP: sufixo `(ambíguo)`/`(baixa confiança)` na célula Unidade duplica a coluna Confiança.
- `prompts.py:84` "sessão substancial" indefinido; 2 protocolos de fim de sessão concorrentes (bloco importável vs ditado), formatos de data divergentes (`DD-MM-YY` vs `YYYY-MM-DD`).
- `navigation.py:283` `render_course_map_md` é gerador COURSE_MAP **legado paralelo** (fora do caminho ativo, que é `render_low_token_course_map_md`); candidato a remoção.

**Recomendação de ataque:** 🔴 PROGRESS_SCHEMA primeiro (sincronizar com v2). Depois 🟠 tabelas mortas (remoção barata, ganho de token). 🟡 duplicação exige decidir fonte canônica por tópico (mais trabalho). Cada grupo é um plano TDD curto.

### Token GitHub (rate limit)
**Status:** follow-up da spec de referências.
**Resumo:** API anônima do GitHub = 60 req/h por IP. v1 vai sem token (cache por hash protege, volume normal por matéria é baixo). Adicionar token opcional (config) sobe pra 5.000/h — necessário só se processar muitas matérias em lote.

### Referências — Approach C (injeção no contexto do tutor)
**Status:** extensão futura da spec atual.
**Resumo:** além da `BIBLIOGRAPHY.md`, fiar as referências no contexto de unidade/tópico que o tutor carrega, pra a referência aparecer sozinha quando o aluno está naquele tópico. Mais ambicioso, mais arquivos. Depois do v1 (que só surfacea + mapeia).

### Medição de correção com ground-truth
**Status:** proposto como forma de validar se mais precisão vale a pena.
**Resumo:** band = confiança, não correção verificada. "alta" pode estar confiante e errado. Rotular ground-truth de 1 repo real (ex.: IA) e rodar o harness contra ele mediria correção de fato, não só confiança. Diz se há trabalho de precisão que ainda valha.
