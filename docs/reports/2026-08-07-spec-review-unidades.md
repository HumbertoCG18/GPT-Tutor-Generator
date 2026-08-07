# Spec-review campanha 2 (Unidades) — verificação com dados reais, 2026-08-07

Revisão delegada pelo user ("provar que tudo que está descrito pode funcionar, nunca assumindo
nada"). READ-ONLY: zero escrita em repo-tutor; taxonomias recomputadas EM MEMÓRIA via montador
canônico (`engine._build_rich_content_taxonomy`) sobre fontes vivas (`subjects.json` mtime
2026-08-04 + manifests pós-rollback); DP real (`assign_units_positional`) sobre blocos reais dos
`.timeline_index.json` em disco. Scripts e JSONs no scratchpad da sessão
(`verify_spec_unidades.py`, `sim_u1_fixed.py`, `sim_desempate.py`, `sim_final.py`).

## Veredito por claim do spec (v1, commit `0fc345e`)

| # | Claim | Veredito |
|---|---|---|
| V1 | Taxonomia MF recomputada tem 3 unidades | **CONFIRMADO** |
| V2 | Tópico-preview sob u01 com aliases ricos (temporal etc.) | **CONFIRMADO — e é DUPLA**: 1.3.1→u03 E 1.3.2 "Verificação de Programas"→u02 (aliases Dafny), ambas sob u01 |
| V3 | Empate u01/u03 no bloco-16 | **CONFIRMADO**: aff real `[4,3,4]` |
| V4 | DP reproduz disco (bloco-16 u02@0.4) | **CONFIRMADO** (byte-igual, 17 candidatos) |
| V5 | "U1 → bloco-16 vai pra u03 conf 0.6" (§4 do spec v1) | **FALSIFICADO** — ver A2 |
| V6 | Perdas MF 3→2 · SO 7→6 · ES2 3→2 · IA 5→3 · TCC 4/4 | **CONFIRMADO** (índice vs parser, 5/5) |
| V7 | Gold keyed por `block_uuid` viável | **CONFIRMADO**: `block_uuid` presente 21/21·21/21·14/14·25/25·31/31 |
| V8 | SO: deadlock no `topic_text` do bloco-05; ordem u07→u05→u07 blocos 10-12 | **CONFIRMADO** (ambas) |
| V9 | Gold ~80 linhas | **CONFIRMADO**: 82 blocos-aula nos 5 cursos |

## Achados (mudam o spec)

**A1 — Título de unidade carrega prefixo; match ingênuo NUNCA casa.** Títulos reais: "Unidade 03
— Verificação de Modelos", "Unidade de Aprendizagem 5 — Aprendizado de máquina", "UNIDADE 02 —
Turing-Computabilidade". Exclusividade tem que casar pelo NÚCLEO do título (strip
`^unidade( de aprendizagem)? N —`), senão o U1 é no-op (provado: 1ª simulação achou 0 colisões).

**A2 — U1 é necessário mas INSUFICIENTE: o empate reaparece no nível de CAMINHO.** Com as 2
colisões mortas (excluídas OU re-atribuídas), aff do bloco-16 vira `[2,3,4]`, mas o DP global
empata de novo: avançar pra u03 = 4+0+0; ficar em u02 = 3+1+0 (a migalha é `exercicios` do
bloco-17-revisão). Tie-break "menor índice" mantém u02@0.4. Simulado nos 2 modos, idêntico.

**A3 — Desempate por sinal concentrado (tie-break lexicográfico `(Σaff, Σaff²)`) RESOLVE, e é
cirúrgico fora do IA.** Resultado por curso (sobre U1):
- **MF**: bloco-16 → **u03@0.6** ✓; únicos outros diffs = bloco-17/20, que `finalize_block`
  limpa depois (disco tem `unit_slug=""` neles) → **1 único diff real de produção, o desejado**.
- **SO/ES2/TCC: 0 diffs** (a alavanca só dispara em empate exato).
- **IA: 14 diffs, colapso pra u05** — NÃO aplicar em IA sem diagnóstico (ver A5).
- Alternativa testada e DESCARTADA: `exercicios` como token genérico — move bloco-16 ✓ mas
  REGRIDE bloco-10 (u02→u01@0.4; lógica de Hoare é u02 no plano) + 4 colaterais.

**A4 — Colisão de rótulo é fenômeno SÓ do MF.** Varredura com o match de núcleo corrigido:
MF 2 colisões · SO 0 · ES2 0 · IA 0 · TCC 0. As perdas de SO/ES2/IA têm OUTROS mecanismos:
- **SO**: U1-only alcança 5/7 (u04-deadlock segue morta — conteúdo absorvido no bloco-05 sob
  u02, anomalia V8; cura = investigação de absorção/segmentação, não de colisão). Extra: o
  recompute muda bloco-12 u07→u05 (a não-monotonicidade do disco é camada stale de rodadas
  sobrepostas; reprocess de cura reescreve coerente — gold decide o certo).
- **ES2**: 0 colisões e u03-testes-de-software nunca vence bloco nenhum — sinal ausente na
  assinatura ou nos blocos; investigação própria.
- **IA**: ver A5.

**A5 — IA viola a premissa monotônica do DP.** O curso ensinou Aprendizado de Máquina (u05 do
plano) NO INÍCIO do semestre (dados/k-NN/clustering, semanas 2-9) e Raciocínio/agentes depois
(Semana-16 `introducao-a-agentes`). `assign_units_positional` exige índice de unidade
não-decrescente na ordem cronológica → u04/u05 podem ser IRRECUPERÁVEIS por DP monotônico neste
curso. Qualquer alavanca global tem que ser gated pra IA; a cura IA começa com HALT de
diagnóstico + ruling de produto (aceitar limitação, modo não-monotônico por curso, ou outra via).

**A6 — Prova extra do U2 (sonda≡produção).** A própria sonda desta revisão (DP puro) diverge do
disco nos blocos que `finalize_block` limpa depois (`unit_slug=""` em revisão/suspensão/evento).
Qualquer gate que não passe pelo pipeline completo mente — reforça U2 como pré-requisito dos
gates de cura.

## Consequências aplicadas no spec (v2, mesmo arquivo)

1. §2: colisão DUPLA no MF + definição de match por núcleo de título (A1) + escopo MF-only (A4).
2. §4 U1: efeito corrigido (mata colisão; NÃO move bloco-16 sozinho — A2).
3. §4 novo **U1b**: desempate por sinal concentrado, gated por curso, IA excluído até
   diagnóstico (A3/A5).
4. §3: não-objetivo "DP intocado" AMENDADO — pesos/estrutura intocados; refinamento de
   tie-break em empate exato é exatamente o U1b (mudança mínima, efeito provado só em empates).
5. §4 U4: mecanismos por curso nomeados (SO absorção; ES2 sinal ausente; IA monotonicidade,
   HALT ruling).
6. §7: aceite do IA condicionado ao ruling de viabilidade (honestidade > meta bonita).
