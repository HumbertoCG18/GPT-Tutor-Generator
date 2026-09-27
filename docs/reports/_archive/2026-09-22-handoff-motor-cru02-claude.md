# Handoff 22/09/2026 — motor >90 %: bloco atingido, #48 aguardando Gate 2, CRU-02 (subunidade) iniciada

Sessão Claude Code 634847b0 (21/09 13:57 → 22/09 01:40), coordenador único da frente do motor. Branch
`feat/motor-atribuicao`, HEAD `9220a57` (#47). Worktree com diff NÃO commitado da #48 (10 arquivos,
+227/−21 em `src/` e `tests/`) e ~50 arquivos sujos de outras sessões — preservar. Estado local:
`.workflow-local/active-task.md` (extenso; "enxugar" é pendência aprovada e adiada). Tracker:
`docs/reports/pendencias.md`, blocos de 21/09 e 22/09 no topo (fila-campanhas CRU-02/03/04 atualizadas).

## 1. Pedido vigente, decisões e limites (não reabrir)

- Meta: **> 90 % por eixo, separadamente**, acerto total sobre denominador histórico (ausentes e
  abstenções contam como erro), por curso e no total. Meta não é promessa.
- Regime cru: 0 LLM, 0 rede, 0 embedding, máquina fraca; gold só avalia; nada por curso; cursos já
  estudados não são holdout novo; parâmetros por LOCO. Professor pode declarar UMA vez (regime 2, opcional).
- Aceite de regra: saldo > 0, 0 perda entre acertos atuais, nenhum curso regride, outros eixos preservados,
  precisão das decisões novas incluindo abstenção → erro. Medir sempre pela fase real (replay integral,
  2ª passada incluída), nunca por override pós-fase.
- Decisões de 21–22/09: workers = subagentes nativos do Claude Code em **Opus 5** (`Agent`, `model: opus`;
  o worker Claude do Alethe herdaria `claude-fable-5-1[1m]`, padrão global não alterado); Codex ~84 % da
  janela — reservado à **revisão Astra única por diff** (`codex exec --profile astra -c
  model_reasoning_effort=medium --sandbox read-only`, brief por stdin, timeout 600 s, sem retry);
  foco exclusivo no desenvolvimento do motor; `.alethe/` (477 MB, 10 worktrees, 10 branches
  `alethe/agent-job-*`) fica como está; não reiniciar claude-mem.
- Gates: issue antes de editar; TDD (teste vermelho primeiro); Gate 1 antes de implementar; revisão Astra
  do diff; Gate 2 antes de commit; push/PR/merge exigem autorização própria. Nunca `git add -A`.

## 2. Placar (builds 15/17-09, 7 cursos, replay pela fase real)

| Eixo | Base 15/17-09 | HEAD 9220a57 (#47) | Worktree (#47 + #48) | Mínimo > 90 % |
|---|---:|---:|---:|---:|
| Bloco | 213/237 (89,9 %) | 213/237 | **214/237 (90,3 %) — atingido** | 214 |
| Unidade | 239/284 (84,2 %) | 244/284 (85,9 %) | **246/284 (86,6 %)** | 256 (teto 272 sem os 12 links) |
| Subunidade primária | 84/251 (33,5 %) | 84/251 | 84/251 | 226 |
| Subunidade aceita (auxiliar) | 108/251 | 107/251 | 107/251 | — |

Por curso após #48 (bloco / unidade / sub primária): MF 54/66 · 61/66 · 25/58; SO 36/39 · 30/37 · 7/15;
IA 38/42 · 39/42 · 4/39; ES2 27/28 · 25/28 · 7/28; TCC 26/27 · 17/18 · 7/11; CG 33/35 · 74/93 · 28/82;
FR — · — · 6/18. MF é o único curso abaixo de 90 % no bloco.

## 3. Feito nesta sessão

- **#47 commitada** (`9220a57`): seção do Moodle com vencedor único no plano + texto bruto concordante vence
  unidade herdada do bloco (`secao-vence-bloco`). +5 unidade, 0 perda, −1 subunidade aceita (aceito;
  causa: alias de formato `videos` na 2ª passada, `resolver_apply.propagar_vocabulario_por_headings`).
- **#48 implementada, revisada e verificada, SEM commit**: (1) `motor/due_window._NON_CONTENT_KINDS` sem
  `assessment` — prova que contém o vencimento hospeda a entrega (decisão do usuário de 06/09, nunca
  implementada); (2) `motor/apply.py`: seção TDE tenta o prazo antes do fora-de-escopo (sem due segue fora;
  `tier2_due_scope` intacto); (3) `file_map.reconcile_unit_with_block(neighbor_block_id=…)`: bloco sem
  unidade própria não impõe a unidade do vizinho sobre texto gated discordante (`texto-vence-vizinho`).
  Aceite `c1-3/aceite_v4_48_22-09.{py,json}` (sha `f7add8cd437ec194…`) 10/10; revisão Astra sessão
  `01a0c72b-92c2-7e10-bfe1-e57499dba67e` APROVAR COM AJUSTES (3 LOW corrigidos: UI `dialogs.py`,
  comentários, teste de straddle); suíte 2407 passam / 4 pulados / 1 falha pré-existente
  (`test_pdf_markdown::test_respect_actualtext…`, igual no HEAD limpo). Issue #48 aberta.
- Medições (todas em `docs/reports/_harness-2026-09-04/c1-3/`, reexecutadas pelo coordenador, JSON
  idêntico): `replay_bloco_21-09` (fase real de bloco, 10 s, 338/338; sha `dd7483f5d7f26739…`),
  `anatomia_bloco_21-09` (24 erros: 8 desempate `disamb`, 7 janela, 6 ausentes, 3 vazios; risco por
  método), `regra_tde_prazo_bloco_21-09` (V1/V2 refutadas), `regra_tde_prazo_assessment_bloco_21-09` (V3:
  bloco 214 mas unidade −1), `regra_v4_vizinho_nao_vence_texto_21-09` (V4 aprovada, sha `d7bfdcaf15a16b5a…`),
  `replay_unidade_21-09` (fase real de unidade, ~99 s, sha `8971a419ca105bb3…`), `regra_secao_*_21-09`,
  `diag_propagacao_token_{CG,SO}_21-09`, `ausentes_21-09.md`, `pdf_identidade_hash_21-09`.
- Astra (ideias, não revisão): brief `c1-3/brief_astra_motor_90_22-09.md`; três respostas literais em
  `c1-3/astra_ideias_motor_22-09.md`; validação no tracker ("Validado: parecer Astra de ideias (22/09)").
  Respondido com dados: os 8 "faltantes" = os 8 ausentes (7 links YouTube do CG + MF
  `archive-of-formal-proofs-355fb8`), mesmos ids em 17/09 e hoje; teste de teto: indisponíveis 8 +
  bloqueio pela unidade 10 = 18 ≤ 25, mas 5 do CG têm gold fora da taxonomia → teto prático 228/251;
  144 erros restantes estão na unidade certa (31 abstenções, 113 escolha errada).

## 4. Pendências, em ordem

1. **Gate 2 da #48** — o usuário pediu para esclarecer antes de responder (menu de 22/09 ~01:35); não se
   sabe o quê. Perguntar objetivamente e, com o "pode", commitar: 10 arquivos de `src/`/`tests/` + artefatos
   novos de `c1-3/` (`aceite_v4_48_22-09.*`, `anatomia_bloco_21-09.*`, `replay_bloco_21-09.*`,
   `regra_tde_prazo_*`, `regra_v4_*`, `brief_astra_motor_90_22-09.md`, `astra_ideias_motor_22-09.md`), sem
   `pendencias.md`, sem `git add -A`. Mensagem de commit no molde de `9220a57` (`git log -1`).
2. **W-P1 e W-Q (Gate 1 de medição da CRU-02 APROVADO em 22/09 ~01:35)** — disparados às 01:36 e
   interrompidos pelo fim da sessão; nenhum arquivo `c1-3/wp1_*` ou `c1-3/wq_*` foi gravado. Opções:
   retomar pelos ids (SendMessage: `a00797e0bb35b6ccc` W-P1, `a37b2366d08a6e978` W-Q) ou redisparar com os
   mesmos briefs (texto integral no transcript da sessão 634847b0; resumo no item 5). Registrar o novo
   dispatch no estado antes de chamar. Sem Alethe.
3. **W-P2** (depois de conferir W-P1): curva de microdeclarações por prefixos 5/10/20/40 sobre a ordem
   congelada, 2ª passada reconstruída por prefixo, custo = perguntas examinadas + tempo, precisão incluindo
   abstenção → erro, por curso; base `c1-3/replay_subunidade_21-09.py` (asserts 84/251, 243/243).
4. Ideias cru 2–4 do Astra (relações explícitas; papel do trecho; certificado de unidade) esperam o
   residual do W-P1 dizer se há casos suficientes. Ganhos exploratórios 0–12 / 0–6 / 0–8.
5. Frente `regime2-declaracao-20260917` (`.workflow-local/regime2-declaracao-20260917.md`): formulário
   do plano + script gerar/validar, Gate 1 pendente; W-P é a versão mínima dela — não duplicar.
6. Pendências técnicas registradas, cada uma exige Gate 1 próprio: token de formato virando alias na 2ª
   passada (`videos`, provavelmente `pagina`; `MOTOR_GENERIC_STEMS` em `text/stopwords.py:197`); testes
   `test_resolves_backlog_unit_status_*` aninhados em `tests/test_core.py` (~linha 1715, nunca coletados);
   12 links ausentes exigem entrada offline (`moodle_sync.plan_import` existe, harness não a chama; rede
   bloqueada); régua casa por caminho, não por hash (`compara_herancas_15-09.py:25-29`); MF 54/66 no bloco
   (famílias: 3 links, 4 desempates `disamb`, 3 fronteiras `janela-1`).
7. Enxugar `active-task.md` (aprovado, adiado): instruções operacionais → `references/tooling.md` da fonte
   canônica (agent-workflow-lab), invariantes do motor → `.mex/`, distribuir snapshot + manifesto +
   `verify.py`, reduzir o estado ao template. Toca arquivos com alterações de outras sessões: pedir "pode".
8. Menor: a linha do brief do Astra descreve o bloco "vencimento em prova → anterior" (pré-#48); ajustar
   se reenviar. Interface: tarefas concluídas podem aparecer "rodando" (cache do CLI); o processo pesado
   é o chroma do claude-mem, não desta frente.

## 5. Briefs em vigor (resumo fiel; texto integral no transcript 634847b0)

- **W-P1** (`c1-3/wp1_inventario_matriz_22-09.{py,json,md}`): inventário dos 251 com estado atual
  (unidade = manifest + `mudancas_de_unidade` de `aceite_v4_48_22-09.json`); residual em 4 classes com
  sobreposição (`indisponivel`, `bloqueio_unidade`, `gold_fora_da_taxonomia`, `relacao_ausente`,
  `falha_selecao` = `abstencao` | `escolha_errada`); matriz expressão → material → campo → trecho literal
  (≤ 120 c) → unidade sugerida → relações já conhecidas (aliases/labels da taxonomia) → conflitos, incluindo
  materiais certos; expressões = n-gramas 1–3 de título, stem do arquivo, `moodle_label`, headings, 1ª linha
  do resumo de código (sem corpo), só variantes lexicais; ordem das perguntas por cobertura marginal de
  ocorrências SEM gold (congelar seleção/ordem por hash antes de carregar o gold); reportar quantas
  perguntas cobrem 50 %/80 %, conflitos, materiais sem expressão nova. Sem curva.
- **W-Q** (`c1-3/wq_desempate_contrastivo_22-09.{py,json}`): sobre `replay_bloco_21-09.py` com src/ vigente
  (base 214/237): confirmar fórmula do `disamb` (`motor/disambiguator.py`, normalização por tamanho da
  assinatura?); inventário das janelas multicandidatas; regra R-contrastiva (termos exclusivos por candidato;
  trocar só com evidência distintiva contra cada concorrente e vencedor atual sem exclusivo casado); os 8
  erros de desempate (MF `exerciciosdafny2`, `exerciciosnusmv`, `introducao`, `revisao`; IA 2; CG 2);
  contrafactual de comprimento; cadeia para unidade (não regredir 246). Aceite bloco ≥ 215 sem perda.
- **Protocolo do Astra (2ª/3ª respostas)**: reconciliar por ID; cobertura é prioridade, não ganho, e nunca
  autoridade; "depende"/"não associar" legítimos; unidade só sugestão; uma declaração, prefixos com o
  estado daquele orçamento (sem revisão retroativa, aliases/caches reconstruídos); custo = perguntas
  examinadas + tempo; teto ≤ 25 torna a meta possível, não a demonstra; LOCO aninhado; replay integral.

## 6. Como retomar (comandos)

```
git -C C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator status --porcelain -- src tests   # 10 arquivos da #48
.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider                                   # ~50 s; 1 falha pré-existente
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/reports/_harness-2026-09-04/c1-3/aceite_v4_48_22-09.py   # ~130 s; apagar o .json antes (assert not exists)
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/reports/_harness-2026-09-04/c1-3/replay_bloco_21-09.py    # ~10 s (apagar .json antes)
```
Ao conferir saída de worker: reexecutar o script, comparar JSON (byte a byte ou hash canônico com chaves
ordenadas), checar `git status -- src` = 0, copiar nada sem conferir. Heredoc no Git Bash quebra com
aspas: usar `Write` de script + `python arquivo.py`. Builds em `.frzero/` (MF/IA `pacote_categoria_17-09`,
demais `pacote_fontes_15-09`) são gitignored; nunca reconstruir (34–56 min por curso) sem necessidade.

## 7. Não fazer

`git add -A`; push/PR/merge; alterar `src/` sem Gate 1 e teste vermelho; segunda revisão Astra do mesmo diff;
LLM/rede/embedding no cru; usar gold para escolher expressões/regras; excluir ausentes do denominador;
regras por curso; reiniciar claude-mem; apagar `.alethe/`; alterar o modelo global; disparar worker pelo
Alethe (não seleciona modelo). Contadores: `escaladas_automaticas` 1 (#47) e `escaladas_automaticas_48` 1
(#48) — não zerar.
