# Handoff — Reforma do sistema de atribuição (continuar daqui)

date: 2026-06-11
branch atual: `feat/reconciliar-unit-bloco` (criada de `new-features`; NÃO mergeada)

## Contexto do projeto

GPT-Tutor-Generator: app Python/tkinter que converte material de curso (Moodle/PDFs/código)
em repositórios Markdown para tutores LLM. Objetivo do usuário: **automatizar — o caminho
AUTO é o principal e deve ser preciso; o manual é correção de exceção** quando o aluno
revisa o backlog e acha erro.

## O que foi feito nesta sessão (tudo commitado)

### 1. Feature F1 — reconciliar unidade × bloco (COMPLETA, na branch)

Bloco autoritativo da unidade. 6 commits (`163a44a`..`66171d9`), suíte 1218 verde,
review duplo por task + review final end-to-end aprovado:
- `FileEntry.unit_block_conflict: dict` (src/models/core.py, após source_section).
- Helper puro `reconcile_unit_with_block` (src/builder/routing/file_map.py, após
  resolve_effective_block): bloco MANUAL com unidade vence tudo; manual_unit sem bloco
  manual mantém; auto: unit vazio herda do bloco, discordância → bloco vence se
  block_conf ≥ unit_conf, senão mantém unidade forte + grava conflito.
- Ligado em `resolve_unit_block_tags` (src/builder/extraction/content_taxonomy.py,
  substituiu a herança parcial antiga).
- Editor (src/ui/dialogs.py): origem da unidade derivada de unit_match_reasons
  (sufixos unidade_do_bloco_manual / reconciliada_do_bloco= / herdada_do_bloco=),
  aviso de conflito, combo "Unidade manual" desabilitado sob bloco manual, aviso de
  subunidade órfã (loader `_load_subunit_unit_map`, slug canônico via
  `_normalize_unit_slug`).
- Pendente: usuário queria TESTAR no app antes de decidir merge em new-features.

### 2. Diagnóstico completo da atribuição (motivou tudo que segue)

`docs/reports/2026-06-11-diagnostico-atribuicao.md` — 4 investigações paralelas +
avaliação empírica no repo real `C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor`
(matéria "Metodos-Formais" no SubjectStore; stash Moodle em
`C:/Users/Humberto/Desktop/Moodle/metodos-formais-para-computacao`, organizado POR SEÇÃO).

Números-chave (49 entries de material avaliadas):
- Erro de bloco: 8/49 (16.3%). **100% dos erros em entries SEM source_section**
  (29.6% sem seção; 0% com seção → o gabarito card_block_map funciona quando dispara).
- Scorer léxico puro sem gabarito: 59.2% de acerto.
- Confiança NÃO calibrada: 46/54 entries com conf=1.0; 7 dos 8 erros com conf 1.0
  "alta" (margin_confidence clampa em 1.0 com scores ~4-8 → margem estoura sempre).
- Caso emblemático: LogicaDeHoare.pdf → bloco-13 (esperado bloco-10, 27/04–04/05,
  topic "logica hoare"), conf 1.0.
- Causa raiz: a seção Moodle se perde no caminho stash→import→manifest (raw/pdfs é
  por CATEGORIA; backfill é script manual que nunca rodou); sem source_section,
  `_card_scoped_block` retorna vazio e o gabarito nunca é consultado.
- Scorer fraco: overlap absoluto de tokens sem raridade (IDF) — "logica" vale igual
  a "hoare"; sem noção de ferramenta (intro.thy Isabelle → bloco "introducao dafny");
  título CamelCase vira 1 token ("logicadehoare").
- Bugs pontuais: B1 categoria `references` (EN) fura _NO_TIMELINE_CATEGORIES (PT-only,
  content_taxonomy.py:961); B2 card bonus possivelmente somado 2× (file_map.py:795+874);
  B3 scripts/eval_assignments.py colapsa com índice persistido (espera `rows`, índice
  tem `sessions` → 49/49 erro espúrio); B4 1 entry com unit u02 + bloco u01; B5 ids
  duplicados no manifest (t1-2026-1, introducao 2×).

### 3. Discussão arquitetural ("vale a pena 2 cérebros?")

Conclusão: não são cérebros rivais, é um FUNIL — manual → prior (seção/gabarito
RESTRINGE 21 blocos a 1-3) → scorer (RANQUEIA dentro) → Gemini (VOTA, só código).
Defeito real: estágio 1 desliga em silêncio quando seção falta, e a confiança não
diz quem decidiu. Cortar qualquer um seria regressão comprovada (0/22 com prior;
59% sem). Generalizar `computed_block_method` pra todas as entries.

### 4. Plano-mestre (AGUARDANDO APROVAÇÃO DO USUÁRIO)

`docs/reports/2026-06-11-plano-mestre-atribuicao.md` — 5 fases, cada uma com ciclo
próprio (brainstorm → spec → plano → subagents → eval) e critério de aceite:
- **P0 — Medição primeiro**: consertar B3 (harness) + golden set versionado das 49
  entries com bloco esperado; métrica padrão (acurácia geral/com-seção/sem-seção/
  % confiante-e-errado). Aceite: reproduz os 8 erros conhecidos.
- **P1 — Seção automática**: backfill de source_section no pipeline (não script
  manual), todo caminho de import preenche quando derivável, degradação visível
  (method scorer_only + teto de conf + aviso no editor). Aceite: erro sem-seção <10%.
- **P2 — Calibrar confiança + method em todas as entries**: margem relativa em vez
  de absoluta, teto por método (scorer_only ≤ ~0.7, card 0.85, manual 1.0). Aceite:
  confiante-e-errado <20% dos erros.
- **P3 — Higiene**: bugs B1, B2, B4, B5.
- **P4 — Scorer melhor** (último de propósito): IDF simples por raridade entre
  blocos, sinal de ferramenta (.thy=Isabelle vs Dafny), tokenizar CamelCase.
  Aceite: scorer puro 59% → ≥80% no golden set.
- Placar no doc para atualizar a cada fase (baseline: 83.7% geral / 70.4% sem seção).

### 5. Ultrareview

Lançado na branch → main (95 arquivos), FALHOU por timeout de 30 min na nuvem.
Decisão sugerida: não bloquear nisso; ultrareview de escopo menor após merge.

## Próximo passo imediato

1. Usuário aprovar (ou ajustar) o plano-mestre.
2. Começar **P0**: brainstorm curto → spec → plano → execução via
   superpowers:subagent-driven-development (implementer Sonnet pra tasks mecânicas,
   review duplo por task — spec compliance depois qualidade — + review final).
3. Decisão pendente paralela: merge de `feat/reconciliar-unit-bloco` → `new-features`
   (usuário queria testar no app primeiro; reprocessar/retag aplica os campos novos —
   `scripts/retag_manifest.py` re-roda só o resolve_unit_block_tags, rápido).

## Convenções da sessão (manter)

- CAVEMAN MODE full ativo (respostas terse PT-BR; código/commits/segurança normais).
- Toda resposta começa com "[Humberto]" (CLAUDE.md do projeto manda; ver arquivo).
- Workflow por feature: superpowers:brainstorming (perguntas 1 por vez, AskUserQuestion)
  → spec em docs/superpowers/specs/ → writing-plans em docs/superpowers/plans/ →
  subagent-driven-development → atualizar relatório do sistema.
- Relatório do sistema: docs/reports/2026-06-09-relatorio-sistema.html (atualizar
  após cada entrega; servidor local em localhost:8000 pode estar rodando).
- Princípio do usuário: a cada adição, uma limpeza em seguida.
- Pre-commit hook imprime UnicodeEncodeError cp1252 inofensivo — commit passa.
- Commits co-autorados: Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>.
- Pendências antigas (fila depois da reforma): limpeza da UI do editor (F2/F4 —
  esconder campos vazios pra não-código, compactar dump do bloco, deduplicar 3
  painéis de override), specs antigas citando attach_block_rationale (nome morto),
  flag morta processing_profiles_seeded_v2.

## Arquivos-âncora

- Diagnóstico: docs/reports/2026-06-11-diagnostico-atribuicao.md
- Plano-mestre: docs/reports/2026-06-11-plano-mestre-atribuicao.md
- Spec F1: docs/superpowers/specs/2026-06-11-reconciliar-unit-bloco-design.md
- Plano F1: docs/superpowers/plans/2026-06-11-reconciliar-unit-bloco.md
- Matcher: src/builder/extraction/content_taxonomy.py (resolve_unit_block_tags ~935),
  src/builder/routing/file_map.py (scorer, reconcile_unit_with_block, thresholds em
  routing/thresholds.py)
- Sinais: src/builder/core/stash_import.py, src/builder/sources/moodle.py (backfill
  :140/:344), src/builder/timeline/card_block.py (gabarito)
- Harness: scripts/eval_assignments.py (quebrado, B3), scripts/retag_manifest.py
- Editor: src/ui/dialogs.py (BacklogEntryEditDialog ~1995)
