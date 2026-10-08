# F5b — Adendo à janela-de-prazo TIER-2 (matching posicional + delivery-window)

**Data:** 2026-08-03 · **Base:** spec `2026-07-22-janela-de-prazo-tier2-design.md` (mantida
onde não contradita) · **Branch:** `feat/motor-atribuicao` · **Head base:** `69f4e13`

## §1 Por que o adendo existe

Medição target executada (2026-08-03): **FAIL 1/8** (piso 4/8), cw=0. Investigação com
evidência da API Moodle (registrada em pendencias 2026-08-03) refutou DUAS premissas da
spec-base:

1. **Nomes de due não têm stem.** Os 2 assigns do card TDE chamam-se ambos "Sala de
   entrega" — matching por stem (D-C) nunca casa → funil. A inferência "t1 ↔ Entrega T1"
   não existe nos dados reais.
2. **Containment (D-A) não é a semântica do gold.** Due real do T2 (06/07) cai DENTRO de
   bloco-18 (dia-único de devolução, sem tópicos) — containment daria confident-wrong.
   Gold corrigido com evidência de submissão (`mod_assign_get_submission_status`):
   t1/t1-thy → bloco-11 (submissão real 2026-05-05; due 06/05 do Moodle CORRETO),
   t2 → bloco-16 confirmado (submissão 2026-06-27).

Decisões do user (2026-08-03): **semântica do trabalho = época de ENTREGA; fonte de
verdade = Moodle** ("geralmente a mais correta"). LlmVoter para trabalhos: testado
one-off (0/3) e DESCARTADO — voter decide por conteúdo, semântica escolhida é entrega.

## §2 Decisões novas

| # | Decisão | Escolha |
|---|---------|---------|
| D-F | Semântica | Trabalho ancora no bloco da ÉPOCA DE ENTREGA (não do conteúdo que exercita). Fonte = due do Moodle. |
| D-G | Matching posicional | Produtor associa cada resource ao assign SEGUINTE na ordem da seção (grupo `label → resources → assign`) e emite `file_dues: {casefold(filename): {due, source}}` por seção. Motor casa entry→due por FILENAME (mesma chave do backfill de seções). Stem matching (D-C) vira FALLBACK — segue válido p/ cursos que nomeiam "Entrega T1". |
| D-H | Janela (substitui D-A/D-B) | Bloco escolhido = **bloco DE CONTEÚDO que CONTÉM o due; senão o último bloco de conteúdo com `period_end <= due`**. Bloco de conteúdo = `topics` não-vazio no timeline index. Nenhum candidato → `None` → funil (D-E intacto). |
| D-I | Band/flag (revisa D-D) | Bloco escolhido CONTÉM o due → band pela fonte (estruturado=alta, named=media), sem flag. Bloco NÃO contém o due (caiu depois do `period_end`, pulou admin/gap) → **media + FLAG** sempre. Preserva cw=0 por construção honesta. |

## §3 Verificação contra o gold corrigido (dados reais já sincados)

- t1/t1-thy: filename `t1_2026_1.pdf`/`T1_2026_1.thy` → grupo do 1º assign TDE → due
  06/05 (estruturado) → blocos de conteúdo com end ≤ 06/05: bloco-11 [06/05..06/05]
  CONTÉM → **bloco-11, alta** = gold ✓.
- t2: `t2_2026_1.pdf` → 2º assign TDE → due 06/07 → bloco-18/17 sem tópicos (fora),
  bloco-16 end 29/06 ≤ 06/07 → **bloco-16, media+FLAG** (não contém) = gold ✓.
- revisao-p1-gabarito: sem due casado → funil → bloco-07 ✓ (o 1/8 de hoje sobrevive).
- Demais 4 rows (plano + 3 bibliografia): fora do alcance por design, funil.

Piso: **4/8, cw=0** (inalterado). Probe `fase5_prova_tier2.py` inalterado.

## §4 Escopo

- **Produtor** (`moodle_labels.py`): `file_dues` posicional por seção, aditivo no card map
  (mesmo merge; `source=="manual"` continua intocável). `assign_dues` continua emitido
  (fallback stem + auditoria).
- **Motor** (`due_window.py`): `_match_due` tenta `file_dues` por filename primeiro, stem
  fallback; `resolve_due_window` implementa D-H/D-I. `tier2_due_scope` INTOCADO (subset
  estrutural preservado).
- **Re-sync + re-medição**: sync headless (padrão do script de 2026-08-03) → probe target.

## §5 Fora de escopo

Tudo da spec-base §7 (bibliografia, plano, eth2) + fórum cross-card (refutado como
fonte) + voter para trabalhos (testado 0/3, descartado).

## §6 Regras herdadas

Régua completa byte-idêntica flag-OFF; 6 probes anteriores intocados; FAIL = resultado
honesto, proibido re-tuning; TDD por task; medição só com auditor de frescor hard=0.
