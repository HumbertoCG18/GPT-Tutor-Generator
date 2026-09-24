# Handoff 22/09/2026 (noite) — motor: #50 commitada, régua v2 adotada, W-V/W-X/W-Y medidos, repo FR curado para estudo

Sessão Claude Code 8072c4bb (22/09 ~14:00 → ~18:00), coordenador único da frente do motor e da curadoria do FR;
orquestrador claude-fable-5-1, executor de código subagente claude-sonnet-5 (T1, TDD), workers de medição Opus 5
(`Agent`, `model: opus`; effort não atestado), revisão Astra única por diff (Codex `--profile astra`, medium,
read-only). Branch `feat/motor-atribuicao`; HEAD no fim da sessão `09d65fe` (outra sessão, frente do workflow,
fez merge do remoto: `ahead 6, behind 2` de `origin`; meus commits `1a968a2` e `493119e` são ancestrais do HEAD).
Estado local migrado por essa outra sessão para `.workflow/local/` (legado `.workflow-local/` vazio e ignorado):
`timeline-prova2-unidade06-20260922.md` (#50), `wv-importacao-offline-51-20260922.md` (#51),
`wx-regua-corrigida-20260922.md`, `wy-kind-por-linha-52-20260922.md` (#52); `active-task.md` é da campanha
da subunidade (sessão anterior), só recebeu uma nota. Pre-commit com gitleaks ativo desde `d410744`.
Tracker: `docs/reports/pendencias.md` (blocos de 22/09 listados na §3; NÃO commitado, tem alterações de outras
sessões). Handoff anterior: `2026-09-22-handoff-motor-49-claude.md`.

## 1. Pedido vigente, decisões e limites (não reabrir)

- Meta: > 90 % por eixo, acerto total sobre denominador histórico; regime cru (0 LLM, 0 rede, 0 embedding);
  gold só avalia; nada por curso; parâmetros por LOCO; aceite de regra = saldo > 0, 0 perda, nenhum curso regride,
  outros eixos preservados, medido pela fase real (replay integral).
- Gates: issue antes de editar; TDD; Gate 1 antes de implementar; revisão Astra única do diff; Gate 2 antes de
  commit; push/PR/merge exigem autorização própria. Nunca `git add -A`. Não reiniciar claude-mem.
- Decisões do usuário em 22/09 (tarde/noite): aprovou (e) Gate 2 documental W-T/W-U e o Gate 2 da #50; abriu (a)
  importação offline como frente (#51) e (b) régua corrigida como medição; (c) seleção na subunidade e (d) CRU-04
  ficam depois de (a). **Adotou a régua v2** com dois rulings novos: ES2 `microsservicos4/7` → u02; CG 5
  (`animacao-v2`, `instanciamento`, `pagina-com-videos-sobre-instanciamento`, `transformacoesgeometricas`,
  `transformacoesgl`) → u05 pelo conteúdo, sobrepondo o oráculo de 06/09 ("Mantém u05" confirmado depois de saber
  que custa 4 acertos). Regra de tipo de bloco: **aula de dúvidas/atendimento antes de prova = review, hospeda
  material e herda escopo da prova**; fora disso office_hours. Gate 1 da medição do classificador (#52) aprovado.
- Astra 5ª resposta (22/09, registrada em `c1-3/astra_ideias_motor_22-09.md` e no tracker): importação offline
  favorável com transições por material; régua corrigida auditável, histórico congelado; limiar "> 50 % nos 84
  certos" NÃO é aceite de integração; 40 B puros → teto condicional 211/251; CRU-04 alvo MF 60/66 (os 6
  desempates são MF 3, IA 1, CG 2). Três contas que ela pediu foram conferidas por ID: 13 ausentes = 12 links + 1
  PDF (MF `t1-2026-1`); W-U 177 de **179** cobertos (não 178); "4 custos da #48" não são regressões
  (`perdas_novas_vs_47.unidade = []`). O usuário vai trazer um parecer do ChatGPT sobre os achados: tratar como
  o do Astra — validar cada afirmação por ID/artefato antes de aceitar, registrar literal em c1-3 + bloco
  "Validado" no tracker, nada de regra nova sem medição.

## 2. Placar (replay pela fase real, decisões congeladas antes do gold)

| Eixo | #49 régua histórica | #49 régua v2 final | Nova base (v2 + 13 presentes) | W-Y P1 (régua histórica, builds-base) | Mínimo > 90 % |
|---|---:|---:|---:|---:|---:|
| Bloco | 217/237 | 217 | 223/237 | 215 | 214 |
| Unidade | 246/284 | **242** (−4 anotação) | **248/284 (87,3 %)** | 247 | 256 |
| Subunidade primária | 84/251 | 84 | 86 | 85 | 226 |
| Subunidade aceita | 107/251 | 107 | 109 | 108 | — |

Nova base por curso (unidade): MF 63/66, IA 39/42, CG 73/93, SO 30/37, ES2 26/28, TCC 17/18 (FR sem régua).
Anatomia v2 (`c1-3/wt_anatomia_unidade_v2_22-09.{py,json,md}`, congelamento `181b944e…`): 36 erros = bloco certo
mas gold diverge **18** (SO 6 família threads u03 vs u02 herdada; CG 6 = 5 transformações u05 vs u04 + 1; MF 2; IA
2; ES2 1; TCC 1), bloco errado 11 (CG 9, CRU-04), texto vence errado 7 (CG 5), ausentes 0. **Recuperáveis sem
tocar o bloco (scorer bruto = gold): 12** — CG `exercicios-sobre-curvas-html`, `instanciamento`, `transformacoesgl`,
`video-opengl-vdi`; ES2 `azure`; IA `ia-responsavel`, `visao-geral-introducao-e-historico`; MF `eth2`; SO
`3103-threads`, `biblioteca-em-c-pthread`, `laminas-sockets`; TCC `aula-11`. Faltam +8 para 256.

## 3. Feito nesta sessão (tudo conferido pelo coordenador: reexecução, hash, `git status -- src` = 0 salvo o diff pendente)

- **#50 commitada** `493119e` (Gate 2 22/09): "Prova N" vira P<N> no extrator compartilhado (`content_taxonomy.py`),
  dashboard delega e lista unidades da taxonomia ∪ blocos, seção "PROCEDIMENTOS E CRITÉRIOS DE AVALIAÇÃO" lida,
  `_assessment_block_label` reaproveita o extrator. Astra: 0 bloqueantes, 2 avisos corrigidos ("prova 6/11" ≠ P6;
  alias "p final" → PF). 6 arquivos. Tracker: bloco "Commitado (Gate 2) … #50".
- **Gate 2 documental W-T/W-U commitado** `1a968a2` (9 arquivos: 8 `wt_*/wu_*` + `astra_ideias_motor_22-09.md`).
- **W-V (#51)**, `c1-3/wv_importacao_offline_22-09.{py,json,md}` (json `e1aa60ae…`, reexecutado 637 s, idêntico):
  13 ausentes injetados em cópias `.frzero/wv_importacao_22-09/` (MF, IA, CG + `_controle_reprocess`), 0 perda,
  unidade 246 → 252 (+1 é ponte do falso ausente `t1-2026-1`, +5 dos 12 links, 6/13 acertos), bloco 217 → 223.
  **Aceite (≥ 256) não cumprido**; etapa 2 (produto) condicionada a outra fonte de ganho. 7 ids mudam só a
  subunidade de vazia para preenchida sem mudar acerto (efeito da importação, mecanismo não investigado).
- **W-X**, `c1-3/wx_regua_corrigida_22-09.{py,json,md}` (json `ea6c74ec…`, reexecutado 141 s): 52 achados; v2 =
  SO 4 (threads: `conceitos-basicos` → `programas-multithreads`, u02 → u03) + ES2 `microsservicos5` u01 → u02;
  indecidíveis e mantidos documentados. **Adoção aplicada** com `c1-3/wx_adota_v2_22-09.py --apply` (16:31):
  `docs/reports/{material_gt_CG,material_gt_ES2,subunit_gt_SO}.csv` modificados (12 linhas), histórico congelado em
  `c1-3/regua_historica_22-09/`, v2 final em `c1-3/wx_gold_v2_final_22-09/` (json da adoção `6b321e59…`).
- **W-Y (#52)**, `c1-3/wy_kind_por_linha_22-09.{py,json,md}` (json `760d136a…`, reexecutado 570 s, idêntico):
  protótipo P1 do tipo por LINHA (Atividade > marcador com sentido de tipo > forma do rótulo com cue na cabeça >
  prova só com sinal forte > aula; 4 ajustes que os dados exigiram). 0 mudança de segmentação nos 8 cursos; alvos
  corrigidos (IA "Introdução à ML" e FR 01/10 → aula; TCC "Atendimento a dúvidas {kind=g2}" → review; 6 de 9
  dúvidas → review); 17 feriados/suspensões e 4 revisões preservados. Placar 215/247/85/108: perdas só em SO
  (`lista-exercicios-p1` e gabarito saem do bloco-09 gold para o bloco-11 review), ganhos CG `openglbasico`,
  `exercicios`. Lista D de guards/testes obsoletos no relatório.
- **Anatomia v2** (§2) rodada a pedido do usuário depois da adoção.
- **Repo FR** (`C:/Users/Humberto/Documents/GitHub/Fundamentos-de-Redes-Tutor`) curado para estudo, só curadoria +
  reprocesso headless sem rede: bloco-10 "Dúvidas da P1" → review; P1 escopo manual **u01-u04** (o professor disse
  em aula que a P1 vai até a aula de 17/09, dentro da u04), rótulo "P1 — unidades 01 a 03 e unidade 04 até a aula
  de 17/09 (ICMPv4)"; P2 u04-u06; enlace 27/10-03/11 u04 → u05 com tópico; tópicos de 05/11 e 10-12/11; 08/12
  reserved; 11 pinos de material (DNS, sockets, intro camada de rede, IPv4, referências YouTube); lista de revisão
  provas → listas, u01, bloco-10; 2 links "para decidir" importados offline (Piratas → bloco-01/u01, IP Calculator
  → bloco-07/u04); fila `revisar` zerada (2 subunidades fixadas); 33 materiais, 33 com bloco. Registro durável:
  manifest (`manual_*`), `course/.timeline_curation.json`, bloco "Curado: repo FR" no tracker. Repo FR sem commit
  (decisão do usuário). Plano de ensino no perfil ainda diz "P1 = 01-03": a declaração manual prevalece.
- **Código não commitado** (executor sonnet, TDD, testes vermelhos primeiro; aguarda Gate 2): `timeline/index.py`
  `_assessment_date_from_timeline_rows` prefere a linha que É a prova (FR P1 22/09 → 24/09 confirmado);
  `ops/pedagogical_regeneration.py` `_exam_index_text` e `ops/bootstrap_ops.py` sempre reescrevem
  `EXAM_INDEX.md` (antes ficava prova fantasma); + 2 arquivos de teste. 5 arquivos, +93/−7. Suíte: **2420 passam,
  4 pulados, 1 falha pré-existente** (`test_caracterizacao_blocos_atual[FR]`, golden vs repo FR externo).
- Tracker (blocos novos, do topo da zona 22/09): "Commitado (Gate 2) … #50", "Validado: 5ª resposta do Astra",
  "Medido: W-X", "Medido: W-V (#51)", "Aplicado: régua v2 final", "Medido: anatomia v2", "Investigado: tipo de
  bloco decidido por texto", "Medido: W-Y (#52)", "Curado: repo FR"; fila CRU-03 atualizada; ideia na caixa
  (backlog vivo): escopo de prova editável pelo aluno, por unidade ou "até a aula X", com reprocesso automático.
- Issues: #50 (commitada, comentários com pendências e complemento), #51 (etapa 1 medida, não passa), #52 (medição
  entregue; etapa 2 exige Gate 1).

## 4. Pendências, em ordem (todas exigem decisão do usuário)

1. **Gate 2 de código** (5 arquivos acima): commit `fix(timeline)` separado; sem push.
2. **Gate 2 documental de hoje**: 3 CSV da régua + `c1-3/regua_historica_22-09/`, `wx_*` (régua, adoção, gold v2
   e v2 final), `wv_*`, `wy_*`, `wt_anatomia_unidade_v2_*`; commit `docs(motor)`. Tracker e handoffs continuam
   fora por decisão anterior do usuário (dizer se muda).
3. **Adjudicações do W-Y** antes do Gate 1 da etapa 2 (#52): SO `lista-exercicios-p1` (gold bloco-09 aula vs
   review bloco-11); TCC "Oficina de problemas - Entrega T2" (cauda "Entrega Tn" = deliverable?); "Apresentação da
   disciplina" (FR, LR, MF) → overview, perde unidade do DP; TCC "Revisão: Alfabeto…" (review demovida a class
   não deve sair do DP: u02 → u01 hoje).
4. **Gate 1 da próxima medição (W-Z)**: reexecutar `wt_regra_unidade_22-09` (R1 por LOCO, R2) na nova base (v2 +
   13) e medir "texto vence o bloco herdado só quando a unidade do bloco não tem tópico que cubra o conteúdo";
   alvo os 18 "bloco certo, gold diverge" (12 recuperáveis), perdas por ID, 0 src.
5. Parecer do ChatGPT que o usuário vai colar: validar por ID (ver §1), registrar, responder com evidência.
6. Menores: golden da caracterização FR defasado (decisão da campanha dona); `assessment_context` traz
   `declared_unit_numbers` do plano (P1 [1,2,3]) enquanto o escopo manual é u01-04 — informativo, não vai ao aluno;
   SYNC_REPORT do FR ainda lista os 2 links como "para decidir" (relatório estático do sync); regra do motor para
   camada≈nível (unidade 06 do FR) e alias de glossário votando em unidade (T2); W-V: 7 subunidades que mudam com
   a importação (mecanismo).

## 5. Como retomar

1. Ler este handoff, `.workflow/README.md` (estado agora em `.workflow/local/`), os 4 estados listados no topo e
   só os blocos de 22/09 do tracker que a tarefa exigir. Conferir `git log --oneline -12`, `git status --short
   src tests docs/reports/*.csv` (esperado: 5 arquivos de código + 3 CSV modificados) e `origin` (ahead/behind).
2. Não repetir medições: hashes e reexecuções estão nos blocos do tracker e nos JSON; W-V leva ~11 min, W-Y ~9 min,
   W-X ~2 min, anatomia ~1,5 min. Scripts em `docs/reports/_harness-2026-09-04/c1-3/`.
3. Reprocesso headless do FR: `python scripts/reprocess_assignments.py "C:/Users/Humberto/Documents/GitHub/Fundamentos-de-Redes-Tutor"`
   com tripwires de rede/LLM (padrão de `c1-3/repara_paginas_cg.py:18-33`); overrides de bloco por
   `src.builder.timeline.curation.set_block_override(course_dir, block_uuid, campo, valor)`; pinos de material no
   manifest via `write_json_manifest` (`manual_timeline_block_id` uuid, `manual_unit_slug`, `manual_subunit_slug`).
4. Executor T1 = subagente sonnet (TDD); medição = Opus; Astra só no diff de produto; registrar modelo observado.

## 6. Não fazer

- Não commitar sem Gate 2; não `git add -A`; não fazer push/PR/merge; não tocar o tracker/handoffs no commit
  documental sem o usuário dizer.
- Não reverter os 5 do CG para u04 (decisão "Mantém u05"); não reabrir o limiar de 50 % como aceite.
- Não mexer nos golds históricos: `c1-3/regua_historica_22-09/` é a cópia congelada; a vigente é a v2 final.
- Não rodar reprocesso do FR com Datalab/LLM ligados (a lista de revisão tem `processing_mode=high_fidelity`;
  reconverter custaria e não é necessário).
- Não tratar parecer externo (ChatGPT/Astra) como autoridade: validar por ID e artefato antes de mudar rumo.
