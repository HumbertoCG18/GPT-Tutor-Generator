# Handoff 2026-09-02c — Fase 1b feita; "o que falta para 200" MEDIDO; proxima = Fase 3 com 3 alavancas medidas

**Leia:** (1) `pendencias.md` §"FASE 1b … MEDICAO" (numeros, escada, alavancas); (2) artifact "Raio-X da Atribuicao"
(https://claude.ai/code/artifact/399626ee-682b-43f8-9987-09c344f6c60f); (3) `2026-09-02-plano-fechar-o-motor.md`.

## Vereditos do user (02/09 noite)
- **A — FEITO:** tutores commitados com o vocab compilado (MF `61a9104` SO `c81527f` IA `002c169` ES2 `09e3739` TCC `84670e4`
  CG `19472d1` LR `0e3ab1a` FR `64990dc`); goldens de caracterizacao regenerados de proposito (FR bloco-11/30 perdem u03 no
  escopo da prova porque tcp/udp-example mudaram de unidade; MF `introducao` band baixa -> media no resolver de conceito).
  Cobertura de referencia (eth2/aws) = watchdog, nao gate. Foco = material de aula.
- **B — pendente (nao trava):** gold de cobertura de referencias {u02} ou N:N {u01,u02}.
- **C — pendente:** import pela API como caminho principal (token do Moodle no build). O plano revisado assume que sim.

## Fase 3 — bloco estrutural, na ordem medida (cada uma: TDD + regua tripla + sentinela + commit)
1. Card generico sem janela -> bloco de apresentacao (irma da `resolve_generic_reference`; +3/0).
2. Ordem das secoes como prior de janela (+7/-1): persistir `section` do Moodle (ler `raw/moodle/sections.json`, que ja esta
   nos 8 repos; no import do stash nao existe — decidir: campo no manifest `source_section_index`, ou leitura do raw no
   `build_motor_context`). Regra medida em `_harness-2026-09-02/mede_ordem_secoes.py --chain --only-flagged`: ancoras so de
   cards de conteudo com janela datada; faixa do proprio card > vizinhos + encadeamento; so estreita decisao FLAGADA.
3. Label/titulo com token unico a 1 bloco da janela decide, so flagados (+2/0).
4. Tokens curtos consagrados pelo cronograma sobrevivem em `disambiguator._toks` nos dois lados (+4/-2; IA k-NN x4).
5. Card como documento ordenado (semana = faixa de blocos do label; alinhamento monotonico por fluxo; desempate dentro):
   +12/-5 so nos flagados. Depende de importar `contents.json` (API) — decidir onde persistir.
FOCO (decisao do user 02/09): materiais de AULA (189/203 golds) 100% sem LLM; referencias sao contexto. Regua propria:
`_harness-2026-09-02/regua_aula.py` — hoje 152/189, com as 5 alavancas 171/189 (+3 irmaos = ~174). Ver pendencias.md.
Gate esperado: motor puro 165 -> ~183/203 (bloco), AULA 152 -> ~174/189, zero regressao na curada, votos/100 caem (residual 43 = 21/100).
NAO fazer (refutado no gold): serie k-esimo, serie monotonica, prova antiga -> prep, label em decisoes confiantes.

## Depois
Run real do FR (decisao G) com vocab compilado + revisar; Fase 2 (cronograma manda) e entao `recompile_vocab` no CG (o compile
herda as unidades do motor); Fase 4 (LLM residual contado).

## Estado
Gerador `feat/motor-atribuicao`: commits desta sessao ate os goldens (ver log). Tutores: limpos, commitados com o vocab. Copias `.ablacao`
dos 5: puro + vocab (sidecars compilados nas copias). `subjects.json`: `compile_vocabulary: true` nos 8.
Harness da sessao em `docs/reports/_harness-2026-09-02/` (mede_alavancas, mede_ordem_secoes, calibra_revisar, moodle_sections/).

## Regua de TRAVESSIA (criada 02/09 noite; decisao do user: gold agora + 1 baseline; otimizacao so depois da fila do motor)
`scripts/eval_travessia.py` (+ `tests/test_eval_travessia.py`): pergunta do aluno -> arquivo/bloco esperado, medida sobre
os indices que o tutor le (COURSE_MAP, SYLLABUS, CRONOGRAMA_DETALHADO, FILE_MAP), sem abrir materiais. Modos: `--sem-llm`
(piso deterministico) e baseline com Gemini (cache em `docs/reports/_travessia_cache/<SIG>.json`: rerodar = 0 chamadas).
Casamento da escolha do LLM e fuzzy (ele cita o texto do CRONOGRAMA, nao o Titulo). **Falta o gold: o user escreve
`docs/reports/travessia_gt_IA.csv` e `travessia_gt_FR.csv`** (modelos criados; ~15 perguntas cada; separador ';';
esperado = ids ou trechos de titulo separados por '|'). Depois: rodar os dois modos = o "antes"; rerodar apos a Fase 3 = o
"depois". Vetores/grafo so se este numero mostrar perguntas que os indices nao alcancam.
