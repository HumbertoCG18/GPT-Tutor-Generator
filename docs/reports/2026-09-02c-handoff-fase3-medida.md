# Handoff 2026-09-02c — Fase 1b feita; "o que falta para 200" MEDIDO; proxima = Fase 3 com 3 alavancas medidas

**Leia:** (1) `pendencias.md` §"FASE 1b … MEDICAO" (numeros, escada, alavancas); (2) artifact "Raio-X da Atribuicao"
(https://claude.ai/code/artifact/399626ee-682b-43f8-9987-09c344f6c60f); (3) `2026-09-02-plano-fechar-o-motor.md`.

## Primeiro: dois vereditos do user (nada foi commitado nos tutores)
1. **eth2**: cobertura 56 -> 55/57 com o vocab compilado. Aceitar como teto documentado (como `aws`), ou restringir aliases
   compilados a rota de subunidade? (`tcp-chat-c` no FR e o mesmo fenomeno sem gold.)
2. **Tutores**: 8 repos sujos com o vocab aplicado (4 sidecars `.llm.json` novos, MF/CG/LR/FR reprocessados). Commitar
   (veredito 1 = aceitar) ou `git checkout` + apagar os `.llm.json`. Depois: atualizar os 2 goldens de caracterizacao
   (`tests/_golden/Fundamentos-de-Redes-Tutor__divisao_blocos.json`, `Metodos-Formais-Tutor__casos_chave.json`) de proposito.

## Fase 3 — bloco estrutural, na ordem medida (cada uma: TDD + regua tripla + sentinela + commit)
1. Card generico sem janela -> bloco de apresentacao (irma da `resolve_generic_reference`; +3/0).
2. Ordem das secoes como prior de janela (+7/-1): persistir `section` do Moodle (ler `raw/moodle/sections.json`, que ja esta
   nos 8 repos; no import do stash nao existe — decidir: campo no manifest `source_section_index`, ou leitura do raw no
   `build_motor_context`). Regra medida em `_harness-2026-09-02/mede_ordem_secoes.py --chain --only-flagged`: ancoras so de
   cards de conteudo com janela datada; faixa do proprio card > vizinhos + encadeamento; so estreita decisao FLAGADA.
3. Label/titulo com token unico a 1 bloco da janela decide, so flagados (+2/0).
Gate esperado: motor puro 165 -> ~176/203 (bloco), zero regressao na curada, votos/100 caem (residual 43 = 21/100).
NAO fazer (refutado no gold): serie k-esimo, serie monotonica, prova antiga -> prep, label em decisoes confiantes.

## Depois
Run real do FR (decisao G) com vocab compilado + revisar; Fase 2 (cronograma manda) e entao `recompile_vocab` no CG (o compile
herda as unidades do motor); Fase 4 (LLM residual contado).

## Estado
Gerador `feat/motor-atribuicao`: commits desta sessao ate `86fc9b3` + docs. Tutores: sujos (ver acima). Copias `.ablacao`
dos 5: puro + vocab (sidecars compilados nas copias). `subjects.json`: `compile_vocabulary: true` nos 8.
Harness da sessao em `docs/reports/_harness-2026-09-02/` (mede_alavancas, mede_ordem_secoes, calibra_revisar, moodle_sections/).
