# Handoff — pronto para PASSO 3 da campanha 3 (flip + deleção do funil legado)

date: 2026-08-17
branch: `feat/motor-atribuicao` (HEAD `b4d119d`)
sessão anterior: F4 (unit/subunit no motor) + passo 2 (C1 pinos + gaps 1.2/1.3) — FLIP DESTRAVADO

## Boot da nova sessão (ordem)

1. `mem-search` (regra global) · ler `.mex/ROUTER.md` · ler este handoff · tracker
   `docs/reports/pendencias.md` (header + "Mapa de deleção do cutover" ~linha 302 + os dois
   Concluído de 2026-08-17 e 2026-08-14-F4).
2. Insumos do flip: `docs/reports/2026-08-14-f4-medicao-unit-motor.md` (metodologia sandbox +
   limitações) · auditoria `docs/reports/2026-08-14-auditoria-enxame.md` §1 itens 1.4/1.5/1.6
   (scripts condenados + mapa de deleção de testes) · spec motor
   `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` §7 FASE 5.
3. Planos executados (referência de interface): `docs/superpowers/plans/2026-08-14-fase4-unit-subunit-motor.md`
   e `docs/superpowers/plans/2026-08-17-passo2-gaps-flip.md`.

## Estado verificado (as-of 2026-08-17, HEAD b4d119d)

- Suite: **1952 passed / 1 skipped / 0 failed**. Sentinelas casos-chave: 0 diff. Régua MF:
  **50/57 (87.7%)**.
- Rollout anchor: 5/5 cursos `use_anchor_engine` ON. **`use_concept_resolver`: OFF em produção
  nos 5** — o flip deste passo é ELE.
- Pré-condições do flip TODAS fechadas (passo 2, commits `636f299..d319477`):
  C1 pinos uuid+display no Tier 1 ✓ · 1.3 resync tag `bloco:` no swap D1 ✓ · 1.2 teste de
  integração da cadeia ✓.
- Flag-ON já produz o contrato COMPLETO da UI (F4): bloco (apply_concept_resolver) + unit/subunit
  (apply_unit_subunit_fields, reconciliados contra o bloco do motor).
- Medição F4 (só MF, sandbox): golds unit 12/14 BEFORE=AFTER; 12/67 entries com unit divergente
  (11 rastreiam bloco motor≠legado — território F3; 1 só-conflict); subunit 11/67 = correção por
  design (restrição à unidade FINAL). SEM medição de: outros 4 cursos, sobrevivência de pinos
  (fix veio depois), diff global de computed por entry.
- Working tree: sujeira pré-existente que NÃO é nossa — não tocar sem ruling:
  `gold_units_rotular.xlsx`, `.claude/*`, `CLAUDE.md`, `AGENTS.md` (raiz), `.gitattributes`, `.codex/`.

## PASSO 3 — ordem imposta

**1º — MEDIÇÃO PRÉ-FLIP nos 5 cursos (sandbox, read-only).** Por curso (MF/SO/ES2/IA/TCC),
cópia em scratchpad + regeneração flag-ON (mecânica do relatório F4):
- `scripts/eval_units.py` com `tests/fixtures/eval/gold_units_<curso>.csv` — gate: **5/5 cursos
  sem regressão BEFORE→AFTER**.
- **Sobrevivência de pinos** (régua NOVA, condição do GO da review final F4): contar
  `manual_timeline_block_id` no manifest de cada curso e verificar `computed_block_id == pino`
  pós-apply — gate: **100% dos pinos honrados** (o fix C1 está commitado mas nunca foi medido
  em curso real).
- `rebuild_diff` 0 por curso + delta de `computed_block_id` por entry (a medição F4 não fez;
  eval_units é cego a mudança de bloco).
- Calibração M7 (tracker): reconcile compara confiança do motor vs scorer legado de unidade —
  se a medição mostrar inversões de desempate em escala, decidir cap/normalização ANTES do flip.

**2º — FLIP (default ON do concept_resolver).** Eval-gated pela medição do 1º. Flag por curso
vive em `subjects.json` (`%APPDATA%/GPTTutorGenerator/`); o DEFAULT vive na leitura de
`builder.options` — flip = default True + flags por curso conforme medição. Protocolo do
projeto: mudança que MOVE atribuição → snapshot antes de reprocess, medir antes/depois.
**Sentinelas VÃO diffar — é o sinal esperado do flip: revisar caso a caso e re-versionar
conscientemente, não temer** (mesma regra do handoff da campanha).

**3º — DELEÇÃO por LISTA NOMEADA** (tracker "Mapa de deleção do cutover", itens 1-8; resoluções
TRAVADAS 2026-07-03 — não re-decidir):
- Símbolos que MORREM: `score_entry_against_timeline_block`/`block_token_weights` (S2),
  `TOOL_*` (S4), `select_probable_period_for_entry`, `_best_instructional_block_fallback`,
  `_card_scoped_block`, `_serialize_timeline_index` (item 6, + testes fantasma listados),
  família R4/R6 (item 7). FICAM: `score_card_evidence_against_entry`, `_score_block_date_match`,
  `card_block.py` inteiro, cadeia topic-labels de index.py (VIVA — só o ramo fallback de unidade
  morre, index.py:2207-2215).
- `resolve_unit_block_tags` morre — **PORTAR a limpeza `_NO_TIMELINE_CATEGORIES`
  (content_taxonomy.py:1137-1147) pro caminho do motor no MESMO commit** (dependência registrada
  no fecho da F4).
- Scripts no MESMO commit da deleção: aposentar `scripts/retag_manifest.py` +
  `scripts/eval_assignments.py` (1.4; régua oficial = `eval_ground_truth.py`).
- `cronograma_health.py:114-181` fallback S2 (1.6/item 1 do mapa): portar pro scoring do
  concept_resolver ou aposentar — decisão desta fase.
- Testes em 3 lotes (1.5 REESCOPADO): (a) `test_temporal_block_wire.py` cortar linhas 68-197,
  MANTER 198-285; (b) apagar em bloco os 4 puros (911 linhas: test_resolve_unit_block_tags,
  test_funil_gate_ambiguidade, test_resolve_unit_block_band, test_card_block_assignment) e,
  ANTES de apagar `test_block_scorer_signals.py`, MOVER os 3 testes S4b (linhas ~273-301, única
  cobertura extensão→ferramenta) pra `test_entry_signals_materials.py`; (c)
  `test_file_map_unit_mapping.py` (2032 linhas) = auditoria função-a-função obrigatória.
- Item 8 do mapa junto: (a) bump v3→v4 quebra `test_persist_enriched_serializer.py` de propósito
  — atualizar junto; (b) unificar vocabulário exam + import privado `_STRONG_EXAM_RE`; (c) W1
  adota `engine._build_rich_content_taxonomy`; (d) W2 `--write` passa a escrever
  `.content_taxonomy.json`; (e) warning de degradação silenciosa.
- Guard test da fase 0 (pacote do motor proibido de importar condenados) deve continuar verde
  durante toda a deleção.

**Gates de cada etapa**: suite verde + régua MF ≥ 50/57 + golds unit 5/5 cursos + pinos 100% +
`rebuild_diff` 0 + sentinelas com diff revisado/re-versionado conscientemente.

## Dívidas ABERTAS relevantes (tracker, não misturar sem decisão)

- M4-M8 da review final F4 (item [CODE] "Dívidas menores"): M7 (calibração cross-escala) é o
  único que pode PRECISAR entrar no 1º (ver acima); M4/M5/M6/M8 são oportunistas.
- 2.7 signal_token_set (trilho eval-gated próprio) · 2.13 smoke tests · 3.1-3.3 estruturais ·
  campanha web (backlog no fim do tracker) — TODOS fora do passo 3.

## Lições operacionais (das sessões F4/P2)

- SDD com mix de modelos: **haiku** pra implementer quando o brief carrega o código completo,
  **sonnet** pra reviews/re-reviews e tasks de integração, review FINAL de branch em modelo
  topo (user escolheu **Opus** na F4; fable foi interrompido por custo). UMA fix wave pra review
  final, nunca um fixer por finding.
- Teste "característica" (deve passar de primeira): instruir o implementer a NÃO ajustar asserts
  se falhar — falha = bug real, BLOCKED. Reviewer pode provar não-vacuidade com mutação
  temporária REVERTIDA (funcionou 2x).
- Briefs via `task-brief`, report em arquivo, resposta curta — contexto do controlador dura a
  campanha inteira.
- Hook `code-review-graph` crasha com `UnicodeEncodeError` cp1252 em TODO commit — conhecido,
  não-bloqueante, ignorar (catalogado no tracker). Hook graphify re-builda sozinho no commit.
- Pinos manuais: `eval_units` NÃO os enxerga (mede unit por bloco) — toda medição de flip precisa
  da régua de pinos explícita. Foi um Critical descoberto tarde na F4; não repetir.
