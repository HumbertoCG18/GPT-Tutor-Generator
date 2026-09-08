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
- `coerencia_moodle.py [--lista]`: regua sem gold (posicao do professor no Moodle) x bloco do produto nos 8 — 188/195 coerentes, 7 incoerentes = Moodle quebrado, CG/LR/FR 0 posicoes. `fila_rendimento.py` ganhou P3/P4/P5. Log `coerencia_moodle.log`.
- `simula_secao_sub.py` (S1 +5/-3, S1b +3/-0, S2 +5/-13) · `reprocess_8_secao.py`. Logs `secao_*.log`, `reprocess_8_secao.log`, `determinismo_secao.log`.
- `rebuild_fr.py [--dry-run] [--fresh]`: FR do zero em `.ablacao/FR-rebuild/` pelo caminho da UI, 0 chamadas (tripwire Gemini + Datalab, vocab off); compara com o produto. Log `rebuild_fr.log`.
- `rebuild_fr_b.py --fresh` (run B, Gemini contado, Datalab bloqueado) · `reprocess_8_explicita.py`. Logs `rebuild_fr_a2.log`, `rebuild_fr_b.log`, `explicita_*.log`, `reprocess_8_explicita.log`.
- `reprocess_8_janela.py`; logs `janela_*.log` (v1, conf-err 1 no MF), `janela2_*.log` (fix), `rebuild_fr_a3.log`, `rebuild_fr_a4.log`, `reprocess_8_janela.log`, `determinismo_janela.log`.
- `placar_100_runs.py` (snapshots por regime em `snap_placar/`, gitignored) + `placar_100.py` (placar por material: 100% certo por regime) · `repara_paginas_cg.py [--dry-run]` (reparo registrado das 16 paginas do Moodle do CG, 0 chamadas) · `docs_c1_3t.py`. Logs `placar_100_runs.log`, `placar_cg_zero.log`, `placar_cg_auto.log`, `audita_gold_pos_reparo.log` (auditoria identica a de 06/09).
- `diag_zero.py [zero|vocab|auto]` (decomposicao dos materiais que nao estao 100% por eixo e causa) · logs `diag_zero.log`, `diag_zero_texto.log` (onde o nome do subtopico do gold aparece).
- `simula_cerca_provas.py` (cerca de provas: escopo do plano x data no SARC, estatico nos snapshots zero + FR do zero) · log `simula_cerca_provas.log`.
- `placar_100_gold_es2.log` (placar com o gold do ES2 corrigido pelo oraculo) · `docs_c1_3u.py`.
- `placar_100_gold_mf.log` (placar com o gold do T2 do MF no bloco da P2) · `docs_c1_3v.py`.
- `mede_salas.py` (salas de entrega dos 8 cursos pela API x SARC; nunca imprime o token) · log `mede_salas.log` · `salas_api.json` (gitignored).
- `fila_zero.py [zero|auto]` (fila do regime por motivo, rendimento, erros confiantes) · `posicao_duvidas_zero.py` (duvidas de bloco x posicao do professor) · logs `fila_zero*.log`, `posicao_duvidas_zero.log`.
- `zero_diff.py --base|--check` (gate do refactor: 1 reprocess nas copias COM staging x referencia do dia; 0 = comportamento preservado) · logs `zero_diff_*.log`, `tier*_pytest.log` · `inventario_motor_2026-09-07.md` · `docs_c1_3w.py`.
- `simula_aprovacao.py` (pos-processamento da aprovacao aplicado em copia + reprocess + medida antes/depois) · log `simula_aprovacao.log` · `fonte_do_texto.log` (precedencia, Datalab, sumario, descricoes por LLM) · `docs_c1_3x.py`.
- `reprocess_8_taxonomia.py` (reprocess registrado da taxonomia padronizada nos 8) · logs `reprocess_8_taxonomia.log`, `formatacao_taxonomia.log`, `anomalias_numeracao.log`, `numeracao_plano.log`, `unidade_vazia_sub_cheia.log` · `gera_tabela_cenarios.py` + `dados_cenarios.json` (matriz por cenario).
- `mede_pai_filho.py [regime]` (parentesco dos erros de subunidade) e `simula_pai_filho.py` (a regra em 8 configuracoes) · logs homonimos.
- `simula_piso_1a.py` (distribuicao de forca das decisoes que bloqueiam a 2a passada) e `mede_piso_grade.py` (grade do piso pela rota real, 6 cursos x 5 pisos) · logs homonimos.
- `mede_filtro_descricao.py` (efeito do filtro pela rota real) · log homonimo. ATENCAO: importar `simula_aprovacao` EXECUTA o experimento dele (falta guard `__main__`) — o log traz duas rodadas, a segunda e a valida.
- Diagnostico do gargalo (07/09): `diag_gargalo.py` (38 erros por causa x evidencia + anatomia da fila), `mede_classe_material.py` (acerto por classe de insumo), `mede_atribuir_vazio.py` (curva do piso + atratores), `simula_titulo_completo.py`, `simula_indice.py`, `mede_texto_faltante.py`, `mede_titulo_video.py` (+ cache `titulos_video.json`, 183 titulos do oEmbed publico). Logs homonimos.
- ES2 (07/09): `mede_prova_fronteira.py` (H1 refutada: 3 a favor, 25 contra), `mede_alias_ambiguo.py` (7 aliases ambiguos em 663, nenhum decide bloco), `corrige_curadoria_es2.py` (correcao medida na copia), `aplica_correcao_es2.py` (aplicada no produto), `ablate_curadoria_gold.py` (**circularidade: 86/93 -> 26/93**). Logs homonimos.
- `mede_fontes_do_professor.py` (teto de cada fonte: plano 12%, SARC 40%, titulo/Moodle 42%, nenhuma 22%) · log homonimo.
- Descontaminacao (07/09): `mede_sarc_posicional.py` (alinhamento aula->topico, 47%), `mede_doacao_secao.py` (secao do Moodle: 19/76 secoes nomeiam, 78% de acerto onde cobre), `gera_sidecar_professor.py` (gerador sem gold), `mede_sidecar_professor.py` (rota real: 201 -> 135 -> 146), `descontamina_glossary.py --aplicar`, `mede_fontes_do_professor.py --limpo`. Logs homonimos.
