# Handoff — FASE 5 do motor de atribuição (rollout + janela-de-prazo + cutover)

Data: 2026-07-22 · Branch: `feat/motor-atribuicao` (continuamos NELA até o grosso da fase — decisão user) · Head: `6c85e2a`

## §1 Estado: FASE 4 FECHADA

- 11/11 tasks complete, todas Approved em review task-scoped. Código do motor: `8f73084..480231a`.
- Review final whole-branch (fable): **Ready to merge YES** pós fix-wave. Fix-wave (`54e7662..480231a`)
  fechou: **C1** `resolve_temporal_block` resolve uuid→display no chokepoint leitor (producer intocado);
  **I1** TIER 0 não atravessa fronteira de escopo; **I2** voter com precedência real de chave
  (config > `GEMINI_API_KEY` do ambiente).
- **Merge feito: `feat/motor-atribuicao` → `new-features`** (fast-forward `933485d..ad58da6`).
  **DECISÃO USER: main SÓ no fim da refatoração do motor.**
- Suite: **1787 passed / 4 skipped / 0 failed**. Régua agora **6 probes**, todos PASS com baselines:
  fase0 82.8% (48/58)/conten 0/cw 1 · fase1 recall 9/10 · fase2_SO 45.2%/0/0 · fase2_TCC pinos 5/5,
  83.3%/cw 0 · fase3 lift +3, 0 API · fase4 off/computed/pinos/dup True + det 48/58 cw1 + voter
  all-cache 51/58 cw0 calls=0. Pisos da fase4 em FRAÇÃO EXATA (48/58, 51/58 — precedente F1).
- Flags `use_anchor_engine`/`use_llm_voter` (SubjectProfile.feature_flags): **OFF em todos os cursos**.
  Flag-OFF = byte-idêntico (verificado). Ligar = rollout desta fase.

## §2 Piloto flag-ON MF (dry-run em memória, 2026-07-22 — detalhe no pendencias.md)

67 entries → **51 motor** (15 alta/36 media; providers 9 manual/6 labels/36 llm; voter all-cache:
36 hits, 0 chamadas, fila humana 0) + **11 pino manual** (motor respeita e limpa temporal — design) +
**5 TIER-2 fora-de-escopo**. Delta: 42 confirmam funil, **9 divergem** (dafny1/dafny2/revisao =
correções confirmadas por gold; tiposindutivos/exercicioscorrecaoterminacao = erros residuais
conhecidos, band media; provas alta consistente com régua cw=0; 3 sem gold direto).
Balanço: **62/67 com dono certo** já hoje.

## §3 Escopo da FASE 5 (por prioridade)

1. **Janela-de-prazo (TIER 2 do spec)** — provider novo: due-date de trabalhos/provas/TDE → janela
   no(s) bloco(s) da semana da entrega. No MF resolve `t1-2026-1`, `t2-2026-1` (+ `t1-2026-1-thy`
   como companion do t1). Medição própria: 8 rows TIER-2 do gold MF, hoje **1/8 pelo funil** — maior
   upside restante. Semântica a decidir no brainstorm: entrega vs semana da entrega vs straddle;
   cursos sem TDE.
2. **Rollout curso a curso**: (a) **seed do cache F3** — copiar `docs/reports/material_curation_MF.json`
   → `Metodos-Formais-Tutor/material_curation.json` (raiz; sidecar NÃO existe lá; sem seed a 1ª rodada
   re-paga até 20 votos); (b) flip `use_anchor_engine`+`use_llm_voter` no MF (piloto instrumentado);
   (c) reprocess na GUI (ação user) com git do repo-tutor como rede de segurança; (d) validar badges
   no dashboard + health report; (e) expandir SO→TCC→IA→ES2 (sem gold fresco em IA/ES2 = medir antes).
3. **Cutover do legado** (fim da fase): deletar `apply_anchor_placement` + S2 legado do health
   (fallback flag-OFF já preparado na F4 item 8) + flag `use_anchor_placement`. Só depois de todos os
   cursos migrados. Aí sim: merge → main.
4. **Defer-F5 do review whole-branch** (lista completa com razões no pendencias.md e no ledger):
   T1b combo UI stale · T2b load_repo_artifact engole exceção · T3 pend-perpétua janela-1 no fase3 ·
   T4b lock por-processo · T7a double-md5 · T7b e2e do gate · T9a ref "None" · herdados F3
   (parent-dir save, fold acento, casefold, truncamento dry-run, stopwords P4).
5. **Curadoria pontual (user, GUI)**: pino do `revisao-p1-gabarito` (mesmo bloco do `revisao-p1`);
   opcional pino nos 2 erros residuais (tiposindutivos, exercicioscorrecaoterminacao). `plano` =
   funil DELIBERADO (não corrigir).

## §4 Regras não-negociáveis (herdadas, seguem valendo)

- READ-ONLY nos repos-tutor **exceto** o reprocess real autorizado do rollout (git deles = segurança).
- Gold = verdade humana (CSVs só GANHAM coluna; re-rotulagem só com sign-off). Pré-gate
  `audit_gold_freshness.py` antes de QUALQUER medição (exit 0; ZERO_OVERLAP warnings = informativos).
- Medição FAIL = resultado honesto — proibido re-tuning (spec §12 regra 4). Pisos em fração exata.
- Lógica nova SÓ no motor/scripts, NUNCA engine.py; guard AST ativo (test_motor_import_guard).
- google-genai lazy; autoconfiança do voter NUNCA lida; voto bounded à janela.
- UTF-8 shim em scripts novos; nunca commitar `.claude/settings*.json`/`CLAUDE.md` (mudanças locais
  fora de escopo vivem no working tree).
- Respostas começam com "[Humberto]", português, caveman full, parceiro de debate.

## §5 Infra/segredos (mudou hoje)

- `.env` raiz agora SÓ `GEMINI_API_KEY`/`DATALAB_API_KEY`/`DATALAB_BASE_URL`; chaves Moodle moraram
  pra `moddle/.env` (fonte única — elimina token stale vencendo renovação da GUI). `.env.exemple`
  atualizado (`6c85e2a`). `MOODLE_PRIVATE_TOKEN` preservado em `moddle/.env` (zero consumidores).
- Pendência [CODE] leve: `datalab_client` depende de import transitivo de helpers pro `.env`.

## §6 Arquivos-fonte desta continuação

- Ledger SDD: `.superpowers/sdd/progress.md` (histórico integral F0→F4 + piloto + triage).
- Tracker: `docs/reports/pendencias.md` (triage completa do review, piloto, dívidas taggeadas).
- Estado: `.mex/ROUTER.md` · Spec: `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md`
  (§ TIER 2/janela-de-prazo, § cutover) · Plano F4 arquivado: `docs/superpowers/plans/Feitos/`.
- Probes: `scripts/fase{0..4}_*.py` + `scripts/audit_gold_freshness.py`.

## §7 Comando de partida da próxima sessão

Ler este handoff + `.mex/ROUTER.md` + pendencias.md (entradas 2026-07-22). Depois:
**brainstorm da janela-de-prazo** (superpowers:brainstorming — semântica due-date/straddle/cursos
sem TDE são decisões de design abertas) → spec § novo ou adendo → writing-plans → subagent-driven
com a régua de 6 probes como gate de regressão (números IDÊNTICOS; janela-de-prazo ganha probe
próprio nas 8 rows TIER-2 antes de mexer em código — baseline 1/8 primeiro).
