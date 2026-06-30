# Handoff — Motor de Atribuição: do design à implementação

date: 2026-06-29
branch: `feat/block-stable-id`
status: design FECHADO (D0-D12 + SÍNTESE). Próximo: spec → plano → implementação SubAgent-Driven.
fonte-de-verdade do design: `docs/reports/2026-06-28-motor-atribuicao-decisoes.md` (D0-D12, Falsificação F-MF, SÍNTESE)

> Este handoff NÃO repete o log de decisões. Ele orienta quem vai escrever o spec,
> o plano e executar a refatoração. Leia o log de decisões inteiro antes do spec.

---

## 1. Objetivo (1 parágrafo)

Generalizar o motor de atribuição `material → bloco da timeline` que hoje é **IA-only**
(`anchor_placement`, parse de data-de-seção) para um motor **plugável, mode-aware** que
resolve os 5 cursos com sinais heterogêneos (IA: data-de-seção; MF/ES2: roteiro; TCC:
"Semana N"; SO: só tópico). Meta de prazo: motor **praticamente pronto até o próximo
semestre** pra testar o LLM tutor de verdade.

## 2. A forma do motor (resumo da SÍNTESE; detalhe no log)

```
AnchorEngine.resolve(entry, ctx):
  TIER 1  pino manual (D1)                     → bloco final, FIM (escape hatch raro)
  TIER 2  roteamento por categoria (D6):
            trabalho   → janela-de-prazo (assign_due; S5 EXISTE)
            revisão    → bloco de revisão (review_rule EXISTE)
            senão      → WindowProvider(seção) → janela; Disambiguator dentro (D3)
                         gate de margem (D4): confiante→ancora; empate/silêncio→FLAG
  TIER 3  se FLAGGED → voto LLM (Gemini, cacheado) → ainda incerto → FLAG humano (D8)
  SAÍDA   escreve temporal_block_id ANCHOR-ONLY. Funil (computed) = piso intacto.
          Cascata efetiva: temporal > manual > computed.
```

`WindowProvider` universal = `card_block_map[source_section]` (D5). SO ganha um 2º
provider (filename-date + section-topic, D10). `Disambiguator` é compartilhado.

## 3. Restrições NÃO-NEGOCIÁVEIS (carregam do design + AGENTS.md)

- **NÃO commita.** O usuário separa mudanças à mão. CC nunca commita sem pedido explícito.
- **Mutação de dado vivo = ação do USER na GUI** (deletar pino, reprocessar). CC só
  prepara/valida arquivos mortos. Tudo que CC roda sozinho é **READ-ONLY** (probes só
  leem JSON e imprimem; nunca mutam manifest).
- **ANCHOR-ONLY:** o motor escreve só `temporal_block_id`, nunca toca `computed` (piso do funil).
- **GUI "sem bloco atribuído" = sem PIN, não sem placement.** NÃO preencher à mão.
- Lógica nova vai em `src/builder/routing/`, NUNCA em `engine.py` (facade — não-negociável).
  Imports de submódulos focados, nunca de `engine.py`.
- Gemini = `google-genai` (`from google import genai`), **lazy dentro do método**, nunca
  no topo do módulo. Anti-pattern a grep: `google.generativeai`, `genai.GenerativeModel`.
- `code_curation.json` = artefato gerado (não-fonte). Prune stale antes de ler, write atômico.
- Antes de chamar `mcp__code-review-graph__*` ou `mcp__token-savior__*`: `ToolSearch select:<name>`
  pra carregar o schema, senão `InputValidationError`.
- Arquivamento de concluídos + tracker `docs/reports/2026-06-21-pendencias.md` sempre atualizado.
- Idioma PT-BR. Sem emoji/em-dash/fluff em output de código/doc.

## 4. Âncoras de código (onde o motor vive / o que reusar)

| O quê | Arquivo:símbolo | Papel na refatoração |
|---|---|---|
| Ponto de substituição | `pedagogical_regeneration.py` `apply_anchor_placement` (passo 5) | `AnchorEngine` SUBSTITUI isto |
| Motor atual (a evoluir) | `src/builder/routing/anchor_placement.py` `resolve_placement:258`, `apply_anchor_placement:344` | já é feature-flagged/additive/temporal-only — base do motor |
| WindowProvider (janela) | `moodle_labels.py` `derive_card_block_map:152`, `build_lesson_topic_index:253` | card_block_map[seção] = janela universal (D5) |
| Disambiguator (scoring) | `concept_resolver.py` `resolve_material_assignment:256`, `score_lesson_match:106` | reusar SCORING bounded à janela; NÃO o overwrite do `resolver_apply` |
| Sinais de entrada | `entry_signals.py` `collect_entry_unit_signals:80`; `resolver_apply.py` `assemble_resolver_inputs:65` | título+markdown+tags+ext do material |
| Cascata de bloco | `file_map.py` `resolve_temporal_block:617` | temporal>manual>computed (preservar) |
| kind do bloco (SARC) | `index.py` kind classification `267-309` | D2-soft (não hard-filter) |
| Voto LLM (já existe) | `pedagogical_regeneration.py` `run_material_residual:44` → `summarize_residual_materials` → `primary_block_id`; `code_curation` (Gemini) | TIER 3: mudar escopo "órfão" → "órfão OU flagged", cache em code_curation.json |
| Categorias de janela | `content_taxonomy.py` funil `:1129`; `ASSIGN_WINDOW_CATEGORIES` (S5); `review_rule`/`review_list_block_for_entry` | D6: trabalho→prazo, revisão→bloco-revisão |
| Feature flags | `SubjectProfile.feature_flags` (`use_anchor_placement`) | flag por-curso; IA/MF primeiro |

> Use `token-savior`/`code-review-graph` (find_symbol/get_minimal_context) pra confirmar
> assinaturas atuais antes de editar — números de linha podem ter drift.

## 5. O que JÁ está construído (read-only, não tocar como produção)

- `scripts/crosscheck_IA.py` — detector de anomalia-de-dado (D11), TDD, 8 testes.
- `tests/test_crosscheck_IA.py` — passando.
- `scripts/trace_motor.py` — trace read-only do motor proposto (janela + disambiguator).
- `docs/reports/ground_truth_IA.csv` — régua IA (derivada por `build_ground_truth_IA.py`).
- `tests/fixtures/eval/metodos_formais_golden.json` — golden MF (régua de validação).
- Shim Windows: `sys.stdout.reconfigure(encoding="utf-8")` no topo de scripts (cp1252 quebra em ç/→).

## 6. Evidência empírica que o spec/plano DEVE preservar

- **C1:** card-window contém a verdade **100%** (47/47 IA temporal ∈ janela; 46/46 MF). → motor bounded alcança a verdade.
- **C2:** bloco admin venceu material real **0×**. → D2-soft (conteúdo evita admin) basta; não precisa hard-filter de kind.
- **Teto determinístico ~57-65%** no multi-bloco. Resíduo = **séries de mesmo-tema** (ExerciciosDafny1-5) — vocab compartilhado afoga a palavra discriminante. LLM é o lever (D8).
- **Cross-check audita DADO, não janela:** auditar janela com roteiro-unbounded = 11/11 falso-alarme. Cross-check só vale no sem-janela (anomalia: duplicata/mis-file).

## 7. MARCO 1 do protótipo (a MAIOR suposição não-provada)

**O lift do LLM (D8) é DESENHADO, não testado.** Antes de construir o motor inteiro:

> **Rodar Gemini no conjunto FLAGGED do MF** (≤20 chamadas, cap já existe) e **medir o
> lift** sobre o teto determinístico ~65%. Se o voto LLM resolve a série same-theme
> (ExerciciosDafny OO → bloco-15), D8 segura. Se não, repensar antes de investir no wiring.

Barato e decisivo. É o primeiro teste de código da fase de implementação.

## 8. Caminho de execução (o que o usuário pediu)

1. **Spec** — `docs/superpowers/specs/2026-06-29-motor-atribuicao-design.md`.
   Consolida D0-D12 + SÍNTESE em requisitos verificáveis (contratos `WindowProvider`/
   `Disambiguator`/`AnchorEngine`, invariantes ANCHOR-ONLY, critérios de aceite por tier).
   Invocar skill `writing-plans` parte do spec.
2. **Plano de implementação** — fases pequenas, TDD (RED-GREEN-REFACTOR), com checkpoints.
   Ordem sugerida: (0) MARCO 1 prova-LLM → (1) contrato+WindowProvider card_block_map +
   Disambiguator read-only provado vs gold MF → (2) gate de margem D4 calibrado →
   (3) escalada LLM D8 wiring+cache → (4) integração D9 (substitui apply_anchor_placement,
   funil intacto, sem-regressão vs gold) → (5) rollout D10 (IA+MF → TCC/ES2 → SO provider novo).
3. **Implementação SubAgent-Driven** — skill `subagent-driven-development`: cada tarefa
   independente do plano vira um subagente, com review checkpoints. Reusar `concept_resolver`
   scoring; NÃO reinventar.

## 9. Critério de DONE / validação

- **Sem-regressão** vs gold (IA `ground_truth` + MF `golden`) — NÃO byte-paridade com o anchor
  velho (o disambiguator PODE melhorar). Re-baseline consciente de `test_caracterizacao`.
- Testes `test_anchor_placement`/`test_temporal_block_wire` substituídos pelos do motor novo (TDD).
- Gate verde (golden/eval/pytest, sem drift) → arquivar plano+spec+report em `Feitos/` (`git mv`).
- Atualizar `docs/Overview-Sistema.html` (overview vivo) + `pendencias.md`.

## 10. Sub-investigações NÃO-bloqueantes (não seguram o spec)

- **Plano de ensino** parseável → enriquece D3 passo 2 (tópico→semana).
- **SARC kind/cor** consistente entre professores (SO/TCC têm SARC importado?).
- **Janela por tópico p/ SO** (seção-tópico ↔ bloco-tópico) — detalhe na fase SO.
- **Extração de ordinal-no-nome** ("Dafny5") — gap menor, não a solução principal.
