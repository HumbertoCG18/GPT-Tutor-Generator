# C1 item 3 — `title` do manifest = `moodle_label` (05/09 tarde, MEDIDO sem LLM; REFUTADO)
- `medicao_a_piso.py` -> `medicao_a_piso.log`: piso sem-llm da travessia (IA/FR/CG) com title := label em MEMORIA (0 chamadas).
- `shim_b.py {antes|title} {puro|holdout}`: envolve `ablacao_rapida.ablate` para reescrever title := label na copia `.ablacao`
  antes do reprocess; roda `motor_puro --com-vocab` (5) ou `holdout_cg.py` (CG). Logs `b_*.log`.
- `snapshot.py` + `diff_b.py antes title` -> `diff_b.log`: flips por entry (bloco com veredito do gold; unidade/sub).
- `leitores_title.py` -> `leitores_title.log`: por leitor de `title` SOZINHO no motor, quantas entries mudam de saida.
- `docs_c1_3.py`: registro no tracker, handoff e decisions (idempotente por assert).
Resultado: piso 0 flip nos 3; motor puro bloco 186 -> 184/199, sub 82 -> 81/93, 2 confiantes viram flag; holdout CG igual. Ver tracker §C1 ITEM 3.
