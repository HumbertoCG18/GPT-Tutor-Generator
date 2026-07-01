# Handoff — Spec do Motor de Atribuição (AnchorEngine)

date: 2026-07-01
branch de trabalho: `feat/motor-atribuicao` (criada de `new-features@933485d`, pushed com tracking)
contexto: continua de `2026-06-29-handoff-motor-atribuicao-impl.md`. Design D0-D13 travado + D8 VALIDADO com número.
status: marco de medição 100% FECHADO. Próximo passo = **spec** (`writing-plans`) → plano → implementação subagent-driven.

---

## 0. TL;DR pro chat novo

- **Régua completa 5/5**: gold human-confirmado + eval oficial nos 5 cursos (baselines abaixo). O "MAIOR GARGALO" do tracker caiu.
- **MARCO 0/1 executados**: ordinal-no-nome MORTO por medição; len-norm +6.5pp grátis; voto LLM 3/18→8/18 no flagged; **gargalo real = recall do gate D4**. D8 refinado no log de decisões.
- **Higiene de dado feita**: poda TCC (shadowing do importer descoberto), pairs md5 nos 5, curadoria bloco-06 IA (gate verde), colisão de id morta.
- **Git em 3 camadas** (decisão do user): `feat/*` → `new-features` (integração) → `main` (só quando motor 100%). Tudo commitado e pushado; suíte 1661 verde.
- **Próximo**: escrever `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` consolidando D0-D13 + os achados medidos desta sessão (seção 4).

## 1. Disciplina (não negociável — persiste)

- **NÃO commita sem pedido explícito.** (Nesta sessão o user autorizou; a regra continua por padrão.)
- **Mutação do vivo = ação do USER na GUI** (reprocessar, deletar). CC prepara/valida arquivos mortos; exceções só com autorização explícita por caso (precedentes: manifest TCC, curation IA).
- Probes/scripts de CC = READ-ONLY nos repos-tutor.
- Lógica nova em `src/builder/routing/`, NUNCA `engine.py`. Gemini = `google-genai` lazy (`from google import genai`).
- ANCHOR-ONLY: motor escreve `temporal_block_id`; funil (`computed`) = piso intacto. Cascata `temporal>manual>computed`.
- Tracker `docs/reports/2026-06-21-pendencias.md` sempre atualizado; concluído vai pra `Feitos/`.
- PT-BR; UTF-8 shim em todo script novo (console cp1252).

## 2. Git — estado exato

- `main`: intocada (será destino só com motor 100%).
- `new-features`: recebeu merge `--no-ff` `933485d` (identidade estável + gold 5/5 + provas). Pushed.
- `feat/block-stable-id`: fechada e pushed (`99aae02` último). Não trabalhar mais nela.
- `feat/motor-atribuicao`: **branch de trabalho do spec**, == new-features hoje. Pushed com tracking.
- Repos-tutor: commits do reprocess (TCC poda, IA curadoria) ficam com o user.
- `.claude/settings.local.json` modificado local, não commitar.

## 3. Baselines oficiais (a régua que o motor tem que bater)

Eval com colapso de par (`pair_key`), HALTs com sign-off do user, as-of 2026-07-01:

| Curso | Baseline | Assinatura do erro |
|---|---|---|
| IA | **86.4%** (38/44) | 6/6 off-by-one fronteira; única com âncora |
| MF | **63.6%** (42/66) | 12/24 adjacente; 1 órfão |
| TCC | **56.0%** (14/25) | pós-poda; re-referenciado |
| ES2 | **50.0%** (14/28) | 12/14 miss de tópico |
| SO | **47.4%** (18/38) | 17/20 miss de tópico; band alta = moeda ao ar |

Critério de DONE (inalterado): sem-regressão vs gold; IA não pode cair.

## 4. Entradas MEDIDAS pro spec (o ouro desta sessão — nada disso estava no design de 28/06)

1. **len-norm na assinatura do bloco**: dividir score por `sqrt(|sig|)` deu **+6.5pp** (53.2→59.7% no escopo MF). O "sumidouro bloco-11" era assinatura verbosa, não semântica. Vai no scoring do Disambiguator.
2. **Gate D4 = lever DOMINANTE** (promovido de "fase 2"): proxy τ=0.25 pegou só 15/26 erros; 11 confiante-e-errado ficaram cegos pro LLM. Fase própria com número (recall do gate), antes de gastar mais em votante.
3. **Voto LLM**: escopo = "flagged OU membro de série same-theme"; **ignorar autoconfiança do LLM** (disse "alta" 18/18, acertou 8). Converte confusão-semântica (sintaxe/semântica 4/4), NÃO converte grão-de-semana (Dafny1, indução 05↔06). Cache sidecar; cap=20; `gemini-2.5-flash` via `get_gemini_client` (chave na config ✓).
4. **Ordinal-no-nome: NÃO implementar como sinal de posição.** Linear = lift 0; DP-monotone = lift NEGATIVO (importa erro do vizinho). Fica só como tie-break soft se sobrar tempo — nunca como base.
5. **WindowProvider por curso é 1ª CLASSE, não rollout tardio.** Cobertura de card-window hoje: IA 90% · MF 90% · ES2 86% · **TCC 26%** · **SO 0%**. Sem provider próprio (SO topic/filename-date; TCC parse "Semana N"), o motor = funil pra 62 materiais.
6. **Lesson-matching fino** (herança do A1, superseded): card "Verificação de Programas" MF (14 lessons, blocos 10-15) é onde tudo ainda erra (hoare, tiposindutivos, dafny1-2). Requisito do Disambiguator real; o probe usou roteiro cru.
7. **Dup-divergence é real e medido**: cópias byte-idênticas caíram em blocos diferentes (TCC aula-06 em 3 blocos; SO plano/programa PASS/FAIL). Motor deve tratar md5-gêmeos como UMA decisão.
8. **Apoio/bibliografia FORA do motor** (decisão do user): categoria bibliografia/references/cronograma fica no funil, sem voto LLM (MARCO 1: 0/3, chamada desperdiçada). Entra na refatoração de ingestão futura (item no tracker), junto com o **sweep de shadowing** (entry morta bloqueava import da fonte viva — mecanismo descoberto na poda TCC).
9. **D6-roteados provados necessários**: T1/T2 do MF têm temporal ERRADO hoje (bloco-05/02 vs true 15/16) — a janela-de-prazo (`assign_due`, S5 existe) é quem resolve; categoria `trabalhos`/`provas`/seção TDE nunca entram no disambiguator.

## 5. Fontes de verdade (ler nesta ordem antes do spec)

1. `docs/reports/2026-06-28-motor-atribuicao-decisoes.md` — D0-D13 + SÍNTESE + **"Validação EXECUTADA" no D8** (números do MARCO 0/1).
2. Este handoff (seção 4).
3. `docs/reports/2026-06-21-pendencias.md` — tracker vivo (baselines, superseded, cobertura de janela).
4. `scripts/marco0_prova_deterministica.py` + `scripts/marco1_voto_llm.py` — provas reproduzíveis; sidecars `marco0_flagged_MF.json`/`marco1_votes_MF.json`.
5. Âncoras de código: tabela do handoff 29/06 (§4) segue válida (`anchor_placement.py`, `moodle_labels.py:derive_card_block_map`, `concept_resolver.py:score_lesson_match`, `file_map.py:resolve_temporal_block`, `entry_signals.py`).

## 6. Caminho de execução

1. **Spec** — `docs/superpowers/specs/2026-07-01-motor-atribuicao-spec.md` (skill `writing-plans` a partir do spec). Contratos `WindowProvider`/`Disambiguator`/`AnchorEngine`, invariantes ANCHOR-ONLY, critérios de aceite por tier, **fases com número** (ordem sugerida atualizada): (0) contrato+WindowProvider card_block_map + Disambiguator com len-norm, provado vs gold MF read-only → (1) gate D4 calibrado COM MEDIÇÃO DE RECALL → (2) providers SO/TCC → (3) escalada LLM (escopo ampliado, cache) → (4) integração D9 (substitui `apply_anchor_placement`) → (5) rollout + cutover 3.4.
2. **Plano** — fases pequenas, TDD, checkpoints.
3. **Implementação subagent-driven** — reusar scoring do `concept_resolver`; NÃO reinventar.
4. MARCO 1 **já foi feito** — não repetir a prova-LLM; os votos estão cacheados.

## 7. Gotchas / pendências laterais (não seguram o spec)

- **TCC perdeu 2 arquivos** na poda (referência Karp, weighted-max-cut) — só existiam no stash antigo; recuperáveis do backup `manifest.pre-poda16-*.bak.json` + git do repo.
- **IA "poda de 13 stale" no tracker = provavelmente morto** (IA hoje: 62 entries, 0 stash antigo). Verificação barata pendente.
- **NFD dotless-i (P4)**: ids TCC com U+0131 continuam (`aula-10-linguagens-reconhecıveis...`); pairs copiou byte-a-byte. Fix NFC no import = refatoração de ingestão.
- **eval_ground_truth keyed-por-id**: colisão de id foi RESOLVIDA no TCC, mas a fragilidade do dict permanece — se surgir nova colisão, uma linha some silenciosa.
- Goldens de caracterização re-baselinados conscientemente (`99aae02`) — drift de dado dos reprocess, evals inalterados.
- `revisao-p1-gabarito` MF: D6-revisão com temporal correto hoje; entrou como roteado na prova (não no disambiguator).

## 8. Comando de partida da nova sessão

> Leia `docs/reports/2026-07-01-handoff-spec-motor.md` e o log de decisões
> `2026-06-28-motor-atribuicao-decisoes.md` (inteiro). Branch `feat/motor-atribuicao`.
> Escreva o spec do AnchorEngine consolidando D0-D13 + seção 4 do handoff.
