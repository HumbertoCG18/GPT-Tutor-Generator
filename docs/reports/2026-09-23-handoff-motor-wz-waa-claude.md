# Handoff 23/09/2026 — motor: W-Z, diagnóstico causal (W-Z2), W-AA executado e reprovado, issues #63–#65 do D9, régua v2 commitada

Sessão Claude Code 843a75cb (22/09 ~20:30 → 23/09 ~13:00), coordenador único da frente do motor. Modelo: claude-fable-5-1
até a manhã de 23/09; depois **claude-opus-5-5 [1M], effort xhigh, por escolha do usuário** (`/model`, `/effort`). Medições
executadas pelo próprio agente ativo (sem worker separado; desvio do precedente Opus-worker registrado nos estados). Sem
revisão Astra (só medição e documentos). Branch `feat/motor-atribuicao`, HEAD `14f0e08d`, **ahead 2** de `origin` (os dois
commits documentais desta sessão; sem push). Antes deles outra sessão fez merge de PRs no branch (`e5e55e16`, #59/#60).
Handoff anterior: `2026-09-22-handoff-motor-fr-regua-claude.md`. Tracker: `docs/reports/pendencias.md` (blocos de 23/09 no
topo da zona; alterado e **não commitado** por decisão anterior do usuário).

## 1. Pedido vigente, decisões e limites (não reabrir)

- Meta: > 90 % em bloco, unidade e subunidade **primária**, separadamente, por curso e no total; regime cru (0 LLM, 0 rede,
  0 embedding); gold só avalia; nada por curso/arquivo/ID; parâmetros por LOCO; aceite de integração = ganho positivo, zero
  perda de acerto atual (sem lista protegida por gold), nenhum curso regride, outros eixos preservados, replay integral.
  Precisão nos acertos atuais não é aceite. Subunidade aceita é auxiliar.
- **Rotulação pelo professor não volta como requisito do produto.** Conhecimento externo só como regime separado, com decisão
  própria. Não reabrir as variantes de precedência bloco × texto (R1–R4 reprovadas no W-Z; família fechada).
- Pedidos do usuário de 23/09 chegaram como texto colado e estão registrados literalmente em `c1-3/wz2_pedido_usuario_23-09.md`,
  `c1-3/waa_pedido_reformulacao_23-09.md`, `c1-3/waa_pedido_execucao_23-09.md`. Autorizações dadas e já cumpridas: diagnóstico
  causal (W-Z2), desenho e execução do W-AA, abrir as 3 issues do D9, Gate 2 documental dos artefatos de 22–23/09.
- **D9:** não habilitar votador, vocabulário ou LLM/rede como consequência de habilitar o D9; preservar as escolhas do usuário;
  padrão de matéria nova é decisão explícita. Não remover o fallback do resolvedor antigo nem mudar defaults sem proposta e
  replay próprios. Abrir issue não autoriza implementar.
- **Régua CG:** não decidir pelos resultados do oráculo ou do W-AA; régua congelada; correção só como versão separada.
- Sem push, PR ou merge sem autorização própria. Nunca `git add -A`.

## 2. Placar (base v2 = régua v2 final + 13 materiais presentes; congelamento W-Z2 `f941ac33…`)

| curso | bloco | unidade | sub primária | sub aceita | mínimo >90 % (bloco / unidade / sub) |
|---|---:|---:|---:|---:|---|
| MF | 60/66 | 63/66 | 25/58 | 29 | 60 / 60 / 53 |
| SO | 36/39 | 30/37 | 7/15 | 8 | 36 / **34** / 14 |
| IA | 41/42 | 39/42 | 4/39 | 5 | 38 / 38 / 36 |
| ES2 | 27/28 | 26/28 | 7/28 | 8 | 26 / 26 / 26 |
| TCC | 26/27 | 17/18 | 7/11 | 9 | 25 / 17 / 10 |
| CG | 33/35 | 73/93 | 30/82 | 43 | 32 / **84** / 74 |
| FR | — | — | 6/18 | 7 | — / — / 17 |
| total | **223/237** | **248/284** | **86/251** | 109 | 214 / 256 / 226 |

Bloco cumpre em todos (MF exatamente no mínimo). Unidade falta +8 (CG +11, SO +4). Subunidade falta +140 (+144 por curso).

## 3. Feito nesta sessão (artefatos em `docs/reports/_harness-2026-09-04/c1-3/`, commitados em `14f0e08d`)

- **W-Z** (`wz_bloco_cobertura_22-09.*`, json `fbbd6e83…`, congelamento `788e4372…`): R2 219, R1 τ-LOCO 241 (+3/−10), R3/R4
  de cobertura 237 (+1/−12); todas reprovadas; subunidade cai em todas. Três execuções (1ª morta por memória; 2ª quebrou no
  dump; 3ª = 2ª byte a byte).
- **W-Z2 diagnóstico causal** (`wz2_diagnostico_causal_23-09.{py,json}` + `_anexo.md`; relatório
  `docs/reports/2026-09-23-diagnostico-causal-tres-eixos.md`). Reexecução de conferência completa, idêntica.
  - Gold **por bloco** existe (`tests/fixtures/eval/gold_units_{MF,SO,IA,ES2,TCC}.csv`) e casa com os blocos dos builds por
    data exata. DP posicional acerta 51/56 blocos; erros = 2 preenchimentos em fronteira (ES2 bloco-07, TCC bloco-10), 2 na
    janela de desvio do IA, 1 cabeçalho (SO bloco-06, gold u04). 40 % dos blocos-candidatos têm afinidade zero.
  - Régua de unidade: 134/284 derivados do bloco-gold, 150 por material (62 decisão do usuário, 60 seção do Moodle no CG).
    Compensação bloco > texto é real: 27 dos 37 acertos julgados por gold por material.
  - Reconciliação dos 18: origem 5, homogeneidade 7, indeterminado 6 (CG sem gold por bloco).
  - Subunidade (165 erros): não geração 76 (F6 65 relação fora do índice + F7 11 não encontrada), seleção 67 (F4b 33, F8 23,
    F4a 8, F5 3), unidade 17, identidade 5 (régua CG). Oráculo de unidade: 86 → 92 (8 correções, 2 perdas; +5 por conteúdo).
    Oráculo de bloco: unidade +4, sub +2, zero no CG/SO. Teto do pacote com unidade oráculo: CG 69/82 (84,1 %).
  - 4 erros de unidade do CG vêm do **fallback do resolvedor antigo** (`computed_block_id`) quando o D9 não dá bloco temporal.
- **W-AA** (desenho `docs/reports/2026-09-23-waa-desenho.md`, marcado como executado; resultado
  `docs/reports/2026-09-23-waa-resultado.md`; dados `waa_selecao_geracao_23-09.{py,json,md}`, json `00aea77b…`,
  congelamento dos braços `b265091e…`): S = primário por função da seção + extensão; G = candidato local por subordinação
  (P1/P4) exclusivo na unidade. Base 86 → **A (S) 83**, **B' (G) 76**, **B (G+S) 73**; nenhum braço passa. S quase não age
  (2,7 % das seções têm papel auxiliar marcado; trocou 9/341). Os ganhos de G no IA são **colisões de radical** com um artigo
  em inglês ("generalização"~"General Terms"), não relação categoria → algoritmo. Conclusão limitada aos mecanismos testados.
- **Régua CG (5 subunidades vazias)**: evidência por material no relatório do W-AA, sem decisão (vazio intencional sob u04;
  inconsistência de migração para u05; `instanciamento`/`transformacoesgl` incompletos sob u05; `transformacoesgeometricas` e
  página de instanciamento ambíguos 5.x × 7.2.4; `animacao-v2` pode seguir vazio).
- **D9 no fluxo real** (reprodutor isolado `waa_iso_d9_fluxo_real_23-09.{py,json}`, APPDATA temporário, diálogo real, rede
  bloqueada): matéria criada pela UI roda só o resolvedor antigo; **salvar a matéria no diálogo apaga `feature_flags`**;
  `options` do manifest não refletem a execução. Issues abertas: **#63** (flags apagadas), **#64** (options × execução;
  `reprocess_assignments.py` diverge da UI), **#65** (padrão do D9 + fallback). Nada implementado.
- **Gate 2 documental** (autorizado): `9cfdf2c7` régua v2 (3 CSV + `regua_historica_22-09/` + `wx_*`); `14f0e08d`
  medições/relatórios 22–23/09. Fora: tracker, handoffs, `.mex/ROUTER.md`, arquivos de 17/09, `src/`, testes.

## 4. Pendências, em ordem (todas exigem decisão do usuário)

1. **Direção da subunidade** depois do W-AA: (a) regime separado de conhecimento externo (relação termo → tópico, com guarda
   contra ajuste ao benchmark); (b) aceitar e publicar o teto do cru por curso; (c) outro mecanismo sobre o pacote só com
   fonte de sinal nova (W-U, W-Z2 e W-AA mostram relação existente mas ambígua, e papel não marcado).
2. **Régua CG** (5 casos): decidir vazio × tópico da u05 × ambíguo; se corrigir, versão separada e reavaliar baseline.
3. **Gate 1 das issues #63 e #64** (prioridade do usuário) e **decisão da #65**.
4. **Gate 2 de código pendente desde 22/09**: `fix(timeline)` em 5 arquivos (`timeline/index.py`, `ops/pedagogical_regeneration.py`,
   `ops/bootstrap_ops.py`, 2 testes; `git diff src tests` sha256 `0aae020a…`); commit separado, sem push.
5. Adjudicações do W-Y (#52) antes do Gate 1 da etapa 2: SO `lista-exercicios-p1`; TCC "Oficina… Entrega T2"; "Apresentação da
   disciplina" (FR/LR/MF); TCC "Revisão: Alfabeto…".
6. Se o tracker, os handoffs e o `.mex/ROUTER.md` entram em algum commit (decisão anterior: fora).
7. Push/PR do branch (ahead 2).

## 5. Como retomar

1. Ler este handoff; estados em `.workflow/local/wz-bloco-cobertura-20260922.md` e `wz2-diagnostico-causal-20260923.md`
   (o segundo cobre W-Z2, W-AA, issues e commits); blocos do tracker "Medido: W-AA", "Planejado: W-AA", "Medido: W-Z2",
   "Medido: W-Z". Conferir `git log --oneline -5`, `git status --short src tests` (esperado: 5 arquivos da #50-fix) e ahead/behind.
2. Não repetir medições: W-Z ~72 min; W-Z2 ~20 min; W-AA ~12 min. Capturas congeladas em `.frzero/` (`wz_congelado_22-09.json`,
   `wz2_captura_base_23-09.json`, `wz2_captura_oraculos_23-09.json`, `waa_captura_bracos_23-09.json`); os scripts aceitam
   `--reavaliar` (reavaliação em segundos, sem refazer replays). `.frzero/` é ignorado pelo git.
3. Harness: `replay_bloco_21-09` → `replay_unidade_21-09`; patches só em memória, restaurados no `finally`; gold só depois do
   congelamento por sha256. Serializar JSON só com chaves string (o W-Z quebrou no dump por chave-tupla).
4. Memória: a 1ª execução do W-Z foi morta pelo Claude Code por memória baixa com a sessão ociosa; rodar replays longos com a
   máquina livre.

## 6. Não fazer

- **Não salvar matérias no Gerenciador de Matérias** até a #63 ser corrigida: apaga as flags dos 8 cursos
  (`{"use_anchor_engine": true, "use_llm_voter": true, "compile_vocabulary": true}` em `%APPDATA%/GPTTutorGenerator/subjects.json`).
- Não implementar S, G, correções do D9 ou mudança de default sem Gate 1; não remover o fallback antigo sem replay.
- Não reabrir precedência bloco × texto, pai × filho, H2 (localização em título/heading) ou rotulação pelo professor.
- Não tratar os 14 ganhos de G no IA como evidência de relação categoria → algoritmo (são colisões de radical).
- Não alterar a régua durante medições; não decidir a régua do CG pelo oráculo ou pelo W-AA.
- Não commitar sem Gate 2; não `git add -A`; não push/PR/merge sem autorização.
- Não tratar parecer externo (ChatGPT/GPT-6 Pro/Astra) como autoridade: validar por ID e artefato antes de mudar rumo.
