---
name: medir-alavanca-ablacao
description: Medir uma alavanca do motor (mudanca de dado ou de regra) nas copias .ablacao ANTES de escrever codigo em src/
last_updated: 2026-09-05
---

# Medir alavanca nas copias `.ablacao` antes de codigo

Lei do projeto: dado antes de codigo; nada regride em regua nenhuma. Toda alavanca (campo do manifest, peso, janela,
regra de banda) e medida numa COPIA, com baseline reproduzido na mesma rodada, antes de tocar `src/`.

## Passos
1. **Ler os consumidores antes de medir.** `grep` de quem le o campo/regra; se o efeito e zero por construcao (ex.: conjunto
   que ja soma os dois campos), diga isso ANTES e meça mesmo assim (C1 item 3: o piso deu 0, o motor regrediu por token perdido).
2. **Baseline na mesma rodada**: `python scripts/motor_puro.py --com-vocab` (5 cursos) e
   `python docs/reports/_harness-2026-09-02/holdout_cg.py <GEN> <GEN>/.ablacao` (CG). Tem que reproduzir o numero do tracker.
3. **Snapshot** de `manifest.json` + `course/.timeline_index.json` + `course/.block_identity.json` das copias
   (`_harness-2026-09-04/c1-3/snapshot.py antes`).
4. **Alavanca por shim, nunca em src/**: envolver `ablacao_rapida.ablate` (dado do manifest) ou monkeypatch da funcao do motor
   (regra), num script no scratchpad; rodar o mesmo `motor_puro` + holdout (`_harness-2026-09-04/c1-3/shim_b.py`).
5. **Diff por entry com veredito do gold** (`diff_b.py antes depois`): bloco (+/-/=), banda/flag, unidade, subunidade. Reportar
   flips positivos E negativos; "0 positivo" fecha a alavanca (entra em NAO fazer do handoff).
6. Registrar: tracker (secao com tabela antes/depois), handoff (COMECE POR, BALANCO, NAO fazer, caixa), `decisions.md`;
   versionar scripts e logs em `docs/reports/_harness-<data>/<item>/` com README.

## Gotchas
- `ab.sync` (robocopy) reescreve o manifest da copia a cada rodada: a alavanca de dado tem que entrar DEPOIS do `ablate`.
- Nao rode duas medicoes em paralelo na mesma copia; em copias diferentes pode, mas o tempo de reprocess deixa de ser comparavel.
- Regua sem gold (subunidade do CG, LR/FR) so lista flips; nao pontua.
- Suite e sentinela nao mudam (src/ intocado); nao os cite como gate da medicao.
