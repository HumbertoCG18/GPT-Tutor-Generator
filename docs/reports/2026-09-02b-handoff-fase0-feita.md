> **SUPERADO em 02/09 (noite) por `2026-09-02c-handoff-fase3-medida.md`** — Fase 1b FEITA; ver 2026-09-02c. Vale so como contexto.

# Handoff 2026-09-02b — Fase 0 FEITA; proxima sessao = Fase 1b (`compile_course_vocabulary`)

**Leia nesta ordem:** (1) `pendencias.md` §"FASE 0 — regua oficial + fila `revisar`" (numeros + calibracao);
(2) `2026-09-02-handoff-executar-plano.md` §Fase 1b e §Run real do FR (a fila segue de la, sem mudanca);
(3) `2026-09-02-plano-fechar-o-motor.md` (decisoes fechadas A-D, G; E/F/H/I adiadas ao dado).

## O que esta sessao entregou
- `scripts/motor_puro.py` (regua oficial, 135 s) e `scripts/censo_motor_llm.py` (+ "revisar por 100" +
  anatomia dos gatilhos; `TUTOR_REPOS_DIR` mede nas copias). `_harness-2026-09-02/calibra_revisar.py` = regua
  da fila (gatilho x erro no gold); rodar a cada fase.
- `src/builder/routing/revisar.py` (`revisar_de`, `motivos_de`), campo `revisar` gravado nos 8 manifests
  (tutores commitados), `FileEntry.revisar`, sentinela vigia. Suite 2201.
- Baseline: curada 55.7/100 (duvida 113 + llm 68 de 325) · motor puro 54.0/100 (5 c/ gold) · motor puro
  161/200 · 158/191 · 51/57 · 26/93.
- Bug de raiz: `find_by_repo_root` nao casava caminho relativo -> `UnitsShrinkError` no reprocess. Corrigido.

## O que o dado disse (nao reabrir sem dado novo)
- Decisao B valida no motor puro: sem-bloco 100%, flag:disamb 63%, sub-empate 57%, conflito 56%.
- Fracos: flag:janela-1 27% (janela-1 nunca vota, ninguem limpa a flag) e sub-ambigua 22%. Decidir com a run FR.
- Conflito so e sinal enquanto o bloco erra; depois da Fase 3 remedir (tende a virar ruido de 20% da fila).
- Recall da fila: bloco 32/39 (7 escapam = alvos da Fase 3), unidade 27/33, **subunidade 35/67** (32 escapam
  por vocabulario = exatamente o buraco da Fase 1b).

## Proximo passo (Fase 1b) — protocolo inalterado do handoff `executar-plano`
Base `_harness-2026-09-02/compila_vocab_v2.py`; cache = sidecar existente; `--recompile-vocab`; filtros
(label, exclusividade, nome-de-arquivo, genericos); TDD com client fake; gate = curado 93/93 + motor puro +
regua "puro + vocab compilado" (3a linha) + sentinela (novas tags SO em CG/FR/LR/MF) + determinismo. Depois:
`calibra_revisar.py .ablacao` de novo — a subunidade tem que deixar de escapar.

## Estado
Gerador `feat/motor-atribuicao` (commits desta sessao no log) · tutores: 8 commitados com o campo `revisar`
(hashes no log de cada repo) · copias `.ablacao` dos 5 em motor puro (sincronizadas hoje).
