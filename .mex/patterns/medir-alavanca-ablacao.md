---
name: medir-alavanca-ablacao
description: Medir uma alavanca do motor (mudanca de dado ou de regra) nas copias .ablacao ANTES de escrever codigo em src/
last_updated: 2026-09-11
---

# Medir alavanca nas copias `.ablacao` antes de codigo

Lei do projeto: dado antes de codigo; nada regride em regua nenhuma. Toda alavanca (campo do manifest, peso, janela,
regra de banda) e medida numa COPIA, com baseline reproduzido na mesma rodada, antes de tocar `src/`.

## Passos
1. **Ler os consumidores antes de medir.** `grep` de quem le o campo/regra; se o efeito e zero por construcao (ex.: conjunto
   que ja soma os dois campos), diga isso ANTES e meça mesmo assim (C1 item 3: o piso deu 0, o motor regrediu por token perdido).
2. **Baseline na mesma rodada**: `python scripts/motor_puro.py --com-vocab` (5 cursos) e
   `python docs/reports/_harness-2026-09-02/holdout_cg.py <GEN> <GEN>/.ablacao` (CG). Tem que reproduzir o numero do tracker.
3. **Snapshot** de `manifest.json` + `<repo-tutor>/course/.timeline_index.json` + `<repo-tutor>/course/.block_identity.json` das copias
   (`docs/reports/_harness-2026-09-04/c1-3/snapshot.py` antes).
4. **Alavanca por shim, nunca em src/**: envolver `ablacao_rapida.ablate` (dado do manifest) ou monkeypatch da funcao do motor
   (regra), num script no scratchpad; rodar o mesmo `motor_puro` + holdout (`docs/reports/_harness-2026-09-04/c1-3/shim_b.py`).
5. **Diff por entry com veredito do gold** (`diff_b.py antes depois`): bloco (+/-/=), banda/flag, unidade, subunidade. Reportar
   flips positivos E negativos; "0 positivo" fecha a alavanca (entra em NAO fazer do handoff).
6. Registrar: tracker (secao com tabela antes/depois), handoff (COMECE POR, BALANCO, NAO fazer, caixa), `.mex/context/decisions.md`;
   versionar scripts e logs em `docs/reports/_harness-<data>/<item>/` com README.

## Gotchas
- **Reconstrução desde fontes, 15/09:** cópia nova do produto não equivale a
  construção nova. Usar `cru_fontes_15-09.py` para importar stash em destino novo;
  comparar depois por origem única com `compara_herancas_15-09.py`. Manter ausentes
  no denominador completo e publicar também os comuns. Conferir estrutura temporal
  antes de reutilizar gold ordinal. Perfis salvos continuam herança declarada.
  O coletor de títulos ignora `staging/`; aprovação/curadoria herdada pode fornecer
  sinais ausentes na construção local. Não atribuir deltas isoladamente a aliases
  quando texto, metadados e pinos mudaram juntos. HTML exige tripwire mesmo com
  `image_description_source=none`: o caminho de imagens pode tentar Datalab.
- **Regime cru, 15/09:** `.ablacao/` fica congelada. Usar o driver
  `docs/reports/_harness-2026-09-04/c1-3/motor_copia_nova_15-09.py --destino .frzero/<nome-novo>`.
  Ele exige destino novo e usa `sync_fresh`; o `sync` incremental com `robocopy /E`
  preserva arquivos ausentes da origem e não certifica limpeza. Um `_CONFIG_ATUAL.txt`
  correto não prova ausência de resíduos. Falha de cópia inutiliza aquele destino;
  executar novamente com outro nome, sem apagar ou reutilizar a saída parcial.
- **O reprocess chama Gemini** (auto-resumo de codigo e referencias, `_run_auto_code_summarization`) para toda entry cujo hash muda quando a UI tem
  `gemini_auto_summarize` ligado — 60 chamadas nao autorizadas em 05/09 por title := label. Shim SEMPRE com o tripwire de
  `docs/reports/_harness-2026-09-04/c1-3/shim_b.py` e `check_gemini_hoje.py` como pos-check; o tripwire tambem protege a medicao de resumo novo (contaminacao).
- `ab.sync` (robocopy) reescreve o manifest da copia a cada rodada: a alavanca de dado tem que entrar DEPOIS do `ablate`.
- Nao rode duas medicoes em paralelo na mesma copia; em copias diferentes pode, mas o tempo de reprocess deixa de ser comparavel.
- Regua sem gold (subunidade do CG, LR/FR) so lista flips; nao pontua.
- Suite e sentinela nao mudam (src/ intocado); nao os cite como gate da medicao.
