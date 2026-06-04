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

### Token GitHub (rate limit)
**Status:** follow-up da spec de referências.
**Resumo:** API anônima do GitHub = 60 req/h por IP. v1 vai sem token (cache por hash protege, volume normal por matéria é baixo). Adicionar token opcional (config) sobe pra 5.000/h — necessário só se processar muitas matérias em lote.

### Referências — Approach C (injeção no contexto do tutor)
**Status:** extensão futura da spec atual.
**Resumo:** além da `BIBLIOGRAPHY.md`, fiar as referências no contexto de unidade/tópico que o tutor carrega, pra a referência aparecer sozinha quando o aluno está naquele tópico. Mais ambicioso, mais arquivos. Depois do v1 (que só surfacea + mapeia).

### Medição de correção com ground-truth
**Status:** proposto como forma de validar se mais precisão vale a pena.
**Resumo:** band = confiança, não correção verificada. "alta" pode estar confiante e errado. Rotular ground-truth de 1 repo real (ex.: IA) e rodar o harness contra ele mediria correção de fato, não só confiança. Diz se há trabalho de precisão que ainda valha.
