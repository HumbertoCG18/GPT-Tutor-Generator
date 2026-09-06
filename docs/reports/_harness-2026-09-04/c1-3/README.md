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
