# C1 item 3 — `title` do manifest = `moodle_label` (05/09 tarde, MEDIDO sem LLM; REFUTADO)
- `medicao_a_piso.py` -> `medicao_a_piso.log`: piso sem-llm da travessia (IA/FR/CG) com title := label em MEMORIA (0 chamadas).
- `shim_b.py {antes|title} {puro|holdout}`: envolve `ablacao_rapida.ablate` para reescrever title := label na copia `.ablacao`
  antes do reprocess; roda `motor_puro --com-vocab` (5) ou `holdout_cg.py` (CG). Logs `b_*.log`.
- `snapshot.py` + `diff_b.py antes title` -> `diff_b.log`: flips por entry (bloco com veredito do gold; unidade/sub).
- `leitores_title.py` -> `leitores_title.log`: por leitor de `title` SOZINHO no motor, quantas entries mudam de saida.
- `docs_c1_3.py`: registro no tracker, handoff e decisions (idempotente por assert).
Resultado (rodada limpa): piso 0 flip nos 3; motor puro bloco 186 -> 184/199, 2 confiantes viram flag; sub 82 = 82, unidade e holdout CG iguais. Ver tracker §C1 ITEM 3.
- `simula_sub_card.py {A|B}`: subunidade de codigo pelo card (nome / irmao principal) — refutadas (0/+ 23/-; 0/+ 2/-).
- `simula_idf_sub.py <snapshot_antes>` -> `simula_idf_sub.log`: IDF intra-unidade no scorer de subtopico, em memoria pela rota real — refutado
  (V1 0/0, V2 +1/-5, V2s 0/0); raiz dos 4 do IA e vocabulario do glossario manual.
- **Incidente Gemini:** a 1a rodada da B (`b_title_*.log`, `diff_b.log`) disparou 60 resumos de codigo (config `gemini_auto_summarize`); `shim_b.py`
  ganhou tripwire; rodada limpa em `b_title2_*.log` + `diff_b2.log` (0 chamadas, `check_gemini_hoje.py`). Vale a rodada limpa.
- `simula_propaga_headings.py <snapshot> conf min_entries df_max [orig]` / `_weak.py` (2a passada so nos nao-confiantes) / `_semgold.py` (MF, CG, FR,
  LR: lista o que mudaria): propagacao de vocabulario por headings — gold 82 -> 87/93 (+5/-0) em (0,7; 2; 0,25) weak-only, curada 93/93;
  grades em `simula_propaga_grid*.log`; sem gold MF 6 / CG 9 mudancas (`simula_propaga_semgold_weak.log`). Nao entra sem gold CG/MF.
- `gera_gold_subunidade.py [--write]`: gold de subunidade CG/MF proposto-claude (05/09) -> `docs/reports/subunit_gt_{CG,MF}.csv` +
  revisao em `docs/reports/gold_subunidade_CG_MF_proposta_2026-09-05.md`. Aguarda aprovacao; nao esta em `motor_puro.py`.
- `simula_unidade_sem_alias.py` / `simula_raiz_unidade.py [sec-only]`: mapa bloco->unidade nos 8 com variantes (sem aliases, radicais, higiene por
  secao, vizinho ancorado, exclusividade relaxada) — so a higiene sobrevive (neutra); as outras regridem.
- `reprocess_cg_unidade.py` (tripwire de PRODUTO: voter so com cache, 0 chamadas) -> `reprocess_cg_unidade.log`: 3 reprocess registrados do CG
  (pinos; sinonimo de morfologia; reverso). `determinismo_tripwire.py` -> `determinismo_higiene.log`. `b_higiene_{puro,holdout}.log`: gates pos-higiene.
- `motor_auto.py {puro5|holdout}` -> `auto_*.log`: REGUA AUTOMATICA (motor + voter cacheado, sem pino, sem glossario manual): bloco 192/199, unidade 185/191, sub 82/93, holdout CG 35/35; 0 chamadas.
- `simula_cg_unidade_generico.py`: RF/SG/Z0/DF no mapa bloco->unidade nos 8 (so RF sobrevive). `motor_auto.py` v2: vocab tambem no holdout + cache de votos do produto. Logs `b_rf_*.log`, `auto_rf_*.log`, `determinismo_rf.log`.
- `simula_propaga_headings_6golds.py` (6 golds, filtro de stems genericos) · `simula_alias_sessao_sub.py` (0 efeito) · `reprocess_8_propagacao.py` (registrado, tripwire; pula commit so `updated_at`). Logs `b_prop_*.log`, `auto_prop_*.log`, `determinismo_prop.log`, `reprocess_8_propagacao.log`.
- `shim_codigo.py {sem|determ} {puro|auto|holdout|autoholdout}` -> `codigo_{sem,determ,determ2}_*.log`: camada 3 (resumos de codigo) ablada / substituida por produtor deterministico (v2 = `.md` do bundle): sub 87 -> 71 / 79 / 78, resto igual. `simula_similaridade_nome.py`: Jaccard nome x vocab (27/0/66 em 0,5 com aliases; 9/0/84 so plano).
- `regua_tripwire.py {puro|holdout}` (motor puro --com-vocab / holdout CG com tripwire) + `motor_auto.py` -> `gold6_*.log`: golds CG/MF aprovados 06/09; automatica x 233 = 187 (80,3%), CG 49/82 (puro sem vocab 39), MF 51/58. `docs_c1_3l.py` registra.
- `fila_rendimento.py`: fila `revisar` x golds no produto — camada llm 79 itens / 2 erros (voto de bloco 75/76); conflito 0 erros de unidade; contrafactual P0 200 -> P1 121 (perde 2 de 41).
- `diag_cg_sub.py [CG|MF|...]`: erros de subunidade por causa pela rota real (33 do CG). `simula_cg_sub_levers.py`: H2 higiene estendida (+0/-2, refutada) e D decomposicao de rotulos (+9/-1). `reprocess_8_revisar.py` / `reprocess_8_decomp.py`: reprocess registrados (fila 200 -> 120; sub 15 mudancas). Logs `decomp_*.log` (v1, na taxonomia: cobertura -1), `decomp2_*.log` (v2, 2a passada: gates limpos), `determinismo_decomp.log`.
- `simula_titulo_confiante.py` (T1 +2/-0, T1b +2/-0, T2 0/0) · `reprocess_8_titulo.py`. Logs `titulo_*.log`, `reprocess_8_titulo.log`.
