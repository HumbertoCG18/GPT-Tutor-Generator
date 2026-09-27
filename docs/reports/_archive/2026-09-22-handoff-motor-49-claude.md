# Handoff 22/09/2026 (tarde) — motor: #48 e #49 commitadas, bloco 91,6 %; CRU-02 medida até o teto da declaração

Sessão Claude Code 60b3a7c4 (22/09 01:50 → 12:40, com dois reinícios do processo: ~02:17 e ~03:15, o segundo
por reboot do PC causado por erro do Codex — alethe-agents issue 202). Coordenador único da frente do motor;
orquestrador claude-fable-5-1 (escolha do usuário), workers Opus 5 (`Agent`, `model: opus`; effort não
atestado), revisão Astra única por diff (Codex `--profile astra`, medium, read-only). Branch
`feat/motor-atribuicao`, HEAD `410592d` (#49). `src/` e `tests/` limpos. Estado local:
`.workflow-local/active-task.md` (extenso, só append; "enxugar" segue pendência aprovada e adiada). Tracker:
`docs/reports/pendencias.md` (fila CRU-02/03/04 e blocos de 22/09; NÃO commitado por decisão do usuário —
tem alterações de outras sessões). Handoff anterior: `2026-09-22-handoff-motor-cru02-claude.md`.

## 1. Pedido vigente, decisões e limites (não reabrir)

- Meta: **> 90 % por eixo, separadamente**, acerto total sobre denominador histórico (ausentes e abstenções
  contam como erro), por curso e no total. Regime cru: 0 LLM, 0 rede, 0 embedding; gold só avalia; nada por
  curso; parâmetros por LOCO; professor pode declarar (regime 2, opcional).
- Aceite de regra: saldo > 0, 0 perda entre acertos, nenhum curso regride, outros eixos preservados, precisão
  das decisões novas incluindo abstenção → erro; medir pela fase real (replay integral), nunca por override.
- Gates: issue antes de editar; TDD; Gate 1 antes de implementar; revisão Astra única do diff; Gate 2 antes de
  commit; push/PR/merge exigem autorização própria. Nunca `git add -A`. Não reiniciar claude-mem; `.alethe/`
  fica como está (MCP do Alethe caiu nesta sessão; workers vão por `Agent`, não pelo Alethe).
- Suspensão do PC: autorizada em 22/09 ~03:13 SÓ com tudo concluído e enquanto o usuário dormia; o PC
  reiniciou sozinho antes; usuário acordado desde 12:10 — autorização esgotada, pedir de novo se necessário.

## 2. Placar (builds 15/17-09, 7 cursos, replay pela fase real)

| Eixo | Base 15/17-09 | #47 (9220a57) | #48 (b726d4c) | **#49 (410592d)** | Mínimo > 90 % |
|---|---:|---:|---:|---:|---:|
| Bloco | 213/237 | 213 | 214 (90,3 %) | **217/237 (91,6 %)** | 214 |
| Unidade | 239/284 | 244 | 246 (86,6 %) | 246/284 | 256 (teto 272 sem os 12 links) |
| Subunidade primária (cru) | 84/251 | 84 | 84 | 84/251 (33,5 %) | 226 |
| Subunidade aceita | 108 | 107 | 107 | 107 | — |

Por curso após #49 (bloco): MF 56/66, SO 36/39, IA 39/42, ES2 27/28, TCC 26/27, CG 33/35. MF é o único
abaixo de 90 % no bloco (84,8 %).

## 3. Feito nesta sessão (tudo conferido pelo coordenador: reexecução + hash + `git status -- src` = 0)

- **#48 commitada** `b726d4c` (Gate 2 22/09 ~01:58): prova hospeda a entrega; seção TDE tenta o prazo; vizinho
  não vence texto discordante. 25 arquivos (10 src/tests + 15 artefatos).
- **#49 commitada** `410592d` (Gate 1 ~03:03, Astra APROVAR COM AJUSTES sessão `01a0c7be-…`, 2 LOW em testes
  tratados, Gate 2 ~12:30): `motor/disambiguator._score` sem o divisor `sqrt(len(sig))`. Aceite
  `c1-3/aceite_v1_49_22-09.{py,json}` 11/11 (sha `2954874c…`): bloco 217/237, exatamente MF `exerciciosnusmv`,
  MF `provas`, IA `algoritmo-de-classificacao-k-nn`; 16 bandas/flags sem trocar bloco. Suíte 2410 passam /
  4 pulados / 1 falha pré-existente (`test_pdf_markdown::test_respect_actualtext…`, igual no HEAD limpo).
  17 arquivos no commit (2 src/tests + 15 artefatos da rodada).
- **Medições da rodada** (todas em `docs/reports/_harness-2026-09-04/c1-3/`, commitadas em `410592d`):
  - W-P1 `wp1_inventario_matriz_22-09.{py,json,md}` (json 8,97 MB, sha `d1650b8a…`; congelamento `114c6f5e…`):
    residual da subunidade = relação ausente 106, falha de seleção 53 (abstenção 6 + escolha errada 47),
    indisponíveis 8, bloqueio pela unidade 10, gold fora da taxonomia 5; 5.517 expressões, só 4,4 % já na
    taxonomia; ordem por cobertura marginal pura seleciona boilerplate.
  - W-Q `wq_desempate_contrastivo_22-09.{py,json}` (sha `f7225583…`): R-contrastiva reprovada (0/0); 18/97
    janelas decididas por comprimento da assinatura (contrafactual do Astra confirmado).
  - W-P2' `wp2_curva_microdeclaracoes_22-09.{py,json,md}` (sha `f3a83039…`; congelamento das 3 ordens
    `38185c12…`): alias por expressão satura em 118/251 (CAP-25, 76 perguntas, 12 perdas); 65–70 % das
    perguntas viram "depende"; CAP-25 domina naive e CAP-50.
  - W-R `wr_normalizacao_score_bloco_22-09.{py,json}` (sha `b2dbf770…`): V1 (sem divisor), V3, V4 passam;
    V1 implementada como #49.
  - W-S `ws_declaracao_por_material_22-09.{py,json,md}` (sha `30faff12…`): guarda de escopo elimina o roubo
    entre irmãos (V-G 127/251); guarda + pergunta por material nos "depende" (V-GM) chega a **213/251
    (84,9 %)** com custo 261 (76 expressão + 185 por material), 1 perda (artefato TCC); teto analítico 211
    sem corrigir 17 bloqueios de unidade.
- Tracker: blocos "Commitado (Gate 2) — #48", "Medido: CRU-02, W-P1", "Medido: CRU-04, W-Q", "Medido:
  CRU-02, W-P2'", "Medido: CRU-04, W-R", "Medido: CRU-02, W-S", "Implementado, aguardando Gate 2 — #49"
  (este último precisa virar "Commitado (Gate 2)" com `410592d` — pendência pequena, item 4.6).

## 4. Pendências, em ordem

1. **Decisão do usuário sobre a CRU-02** (subunidade): (a) aceitar o regime "professor rotula os materiais
   em dúvida" e medir a ordem de perguntas por material mais barata (sem expressão; custo ≈ 1 resposta por
   alvo); (b) atacar antes os 17 bloqueios de unidade (CRU-03: unidade vigente não contém nenhuma primária
   do gold — ES2 3, CG 9, SO 5) porque limitam o teto da subunidade a 211; (c) parar a frente de declaração
   e voltar às ideias cru 2–4 do Astra. Nada implementado; qualquer caminho exige Gate 1 próprio.
2. **Bloco residual** (CRU-04): MF 56/66; dos 8 erros de desempate restam 6 (MF `introducao`, `revisao`,
   `exerciciosdafny2`; IA `analise-exploratoria`; CG `basico3d-cpp`, `-py-zip`) — indistinguíveis ou com
   evidência dos dois lados; V4 (por termos casados) corrigiria `exerciciosdafny2` (medido, não implementado).
3. **Unidade** (CRU-03): 246/284, faltam 10 para 256; 12 links ausentes exigem entrada offline
   (`moodle_sync.plan_import` existe, harness não chama).
4. **Régua**: TCC `aula-06-revisao-alfabeto…` tem gold primário vazio e conta como acerto por abstenção
   (`herancas_TCC_15-09.csv`, `sub_primario=1`, `pred_sub` vazio) — corrigir a régua ou excluir da contagem
   com registro; 5 CG com gold fora da taxonomia.
5. Pendências técnicas anteriores (cada uma com Gate 1 próprio): alias de formato na 2ª passada (`videos`;
   `MOTOR_GENERIC_STEMS`); testes aninhados em `tests/test_core.py` (~linha 1715); régua casa por caminho
   (`compara_herancas_15-09.py:25-29`); entradas com decisão cacheada por `content_key` (`apply.py:117-123`)
   não passam pelo `disambiguate`.
6. Tracker: atualizar o bloco da #49 para "Commitado (Gate 2)" com `410592d` (não feito para não tocar
   `pendencias.md` mais uma vez sem necessidade); enxugar `active-task.md` (aprovado, adiado; pede "pode").

## 5. Como retomar

```
git -C C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator status --porcelain -- src tests   # deve ser vazio
.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider                                   # ~65 s; 1 falha pré-existente
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/reports/_harness-2026-09-04/c1-3/aceite_v1_49_22-09.py   # ~155 s; apagar o .json antes
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/reports/_harness-2026-09-04/c1-3/replay_bloco_21-09.py    # ~10 s (apagar .json antes)
```
Scripts que gravam `tempo_s` (wp2, ws): comparar por hash canônico sem os campos `tempo*` (padrão usado
nesta sessão); os demais são byte-idênticos. Heredoc no Git Bash quebra com apóstrofos desbalanceados
(ex.: "W-P2'"): usar `Write` de script + `python arquivo.py`. Builds em `.frzero/` são gitignored; nunca
reconstruir sem necessidade.

## 6. Não fazer

`git add -A`; push/PR/merge; alterar `src/` sem Gate 1 e teste vermelho; segunda revisão Astra do mesmo
diff; LLM/rede/embedding no cru; gold para escolher expressões/regras; excluir ausentes do denominador;
regras por curso; reiniciar claude-mem; apagar `.alethe/`; suspender/desligar o PC sem autorização nova.
Contadores: `escaladas_automaticas` 1 (#47), `escaladas_automaticas_48` 1, `escaladas_automaticas_49` 1 —
não zerar.

## 7. Adendo 13:40 — CRU-03/CRU-02 após a 4ª resposta do Astra (W-T e W-U medidos e conferidos)

- Decisão do usuário com o Astra: rotulagem pelo professor descartada como requisito de produto; W-S vira
  diagnóstico; conhecimento externo (ex. CS2023) só como regime separado, com decisão própria.
- **W-T** (`c1-3/wt_anatomia_unidade_49_22-09.{py,json,md}`, `wt_regra_unidade_22-09.{py,json}`; reexecutados,
  byte-idênticos): 38 erros de unidade = 13 ausentes (12 links + 1 PDF) + 12 adjudicação (bloco certo, unidade
  do bloco ≠ gold) + 9 dependem do bloco (CRU-04) + 4 texto vence errado (0 regressões da #48: `perdas_novas_vs_47.unidade = []`; conferido por ID em 22/09). Bloqueios de subunidade por (unidade,
  slug) = 10, iguais ao W-P1; os "17" do W-S incluíam 2 já corrigidos pela #48 e 5 do SO que são erro de
  unidade (gold u03) e não de taxonomia. Regras texto-vence-bloco (R1 com τ por LOCO = 0,90; R2 sem
  parâmetro) REPROVADAS: 237/284 e 215/284; a confiança do scorer não ordena a decisão. Único caminho medido
  para a unidade cruzar 90 %: entrada offline dos 12 links (→ 258 ≥ 256; + o PDF MF `t1-2026-1` → 259), Gate 1 de produto/harness.
- **W-U** (`c1-3/wu_cobertura_relacoes_22-09.{py,json,md}`; reexecutado, byte-idêntico): índice de relações
  explícitas do pacote (11.663, sem gold, saídas do motor excluídas) cobre 56/106 "relação ausente" (IA
  27/27, CG 17/37, MF 7/26), 53/53 "falha de seleção", 70/84 certos; 40 B puros exigiriam fonte externa. Mas
  177/179 cobertos (56 + 53 + 70; "178" era erro de soma) têm relação também para tópicos errados (5–19 concorrentes): existência não discrimina;
  mecanismo só com critério de seleção medido antes (precisão > 50 % nos 84 certos, sem gold).
- Régua, pendências novas: SO 4 materiais com gold de unidade u03 e gold de subunidade `conceitos-basicos`
  (só em u02/u04); slug `conceitos-basicos` duplicado entre unidades; TCC `aula-06` gold vazio.
- Não rastreados (aguardam Gate 2): os 8 artefatos wt_*/wu_* e `astra_ideias_motor_22-09.md` (4ª resposta).
- Próximas decisões do usuário: (a) Gate 1 da importação offline dos links (unidade); (b) CRU-04 residual
  (MF 56/66); (c) subunidade: critério de seleção sobre o índice, regime externo ou parar.
