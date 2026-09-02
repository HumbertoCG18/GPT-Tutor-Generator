# Handoff 2026-09-02 — EXECUTAR o plano "fechar o motor": Fase 0 + Fase 1b, depois run real do FR

**Para a proxima sessao. Leia nesta ordem:**
1. `docs/reports/2026-09-02-plano-fechar-o-motor.md` — decisoes do user, fases, alvos, decisoes fechadas
   (A, B, C, D, G) e adiadas (E, F, H, I). E a fonte unica do "o que fazer".
2. `docs/reports/pendencias.md` secao "MOTOR PURO — o numero honesto" — os numeros-base.
3. Artifact "Anatomia do Bloco" (https://claude.ai/code/artifact/ba1de7bf-a802-49fc-b88b-6be358d4b796)
   secoes 6-7 — dissecacao dos 117 votos e estado do produto.
Handoffs anteriores (`01c`, `01d`) valem como contexto; NAO reabrir a fila deles.

## Leis (inalteradas) + regua dupla
Dado antes de codigo · raiz nunca remendo · sem regra por categoria/curso · gate: eixos + subunit_gt +
pytest + sentinela + determinismo + ablacao nu/curado **+ motor puro** · nada regride em nenhuma regua ·
commits com trailers · [Humberto]. Licao 01/09d: rota de bloco quer sinal ESTRUTURAL. Licao 02/09: co-heading
nao atravessa o buraco semantico (26 -> 31); nome de arquivo e identidade, nao vocabulario.

## Estado ao comecar (tudo pushed em 02/09)
Gerador `feat/motor-atribuicao` @ `c1df27b` · tutores: MF `a4c00d4` SO `32f94e0` IA `90431d6` ES2 `5789e7b`
TCC `2f0fe9c` CG `870ea15` LR `f87a1c3` FR `62e57f0` (todos com o reprocess do meta-generica).
Regua curada: bloco 199/200 · unidade 191/191 · cobertura 56/57 · subunidade 93/93 com-extras / 91/93
primario · suite 2178 · votos LLM 109 nos 8 (33/100 no bloco). Motor puro: 158/200 · 154/191 · 51/57 ·
26/93. Copias `.ablacao` em estado misto — rodar `ablacao_rapida` (nu) antes de medir qualquer coisa nelas.

## O QUE FAZER (na ordem; cada item termina com gate + commit + tracker)

### Fase 0 — regua e campo `revisar` (sessao curta)
1. Promover do scratchpad para `scripts/`: `motor_puro.py` (regua oficial do produto: copias nu + voter OFF +
   4 eixos + subunidade), `censo_motor_llm.py` (motor x LLM por eixo, acerto por metodo, "revisar por 100").
   Os arquivos estao em `C:\Users\Humberto\AppData\Local\Temp\claude\...\dbdc7a63-...\scratchpad\` — se o
   scratchpad sumiu, reescrever a partir da descricao no tracker (ambos < 120 linhas).
2. `revisar` = funcao pura + testada, enum {duvida, llm, ok}: `duvida` = sem bloco OU `llm-funil` OU
   subunidade ambigua/empate OU `unit_block_conflict`; `llm` = `temporal_block_method == "llm"`; `ok` = resto.
   Gravar no manifest (campo derivado, recalculado no reprocess) e contar no `censo`.
3. Baseline oficial das 3 metricas nos 8 (curado, motor puro, revisar/100). Registrar no tracker.

### Fase 1b — `compile_course_vocabulary` (2 sessoes)
Base pronta: `scratchpad/compila_vocab_v2.py` (prompt v2 = topicos da unidade + TITULO/LABEL/HEADINGS/lead
300 chars dos materiais da unidade; schema `{topicos: [{topico, termos}]}`; gemini-3.5-flash via
`get_gemini_client`; pos-filtro exclusividade + termo != label + token especifico). Resultados: IA 5 -> 37/39,
FR 12 -> 17/19 taggados; compilados de referencia em `docs/reports/2026-09-02-vocab-llm-{IA,FR}.json`.
1. Passo de build/reprocess: se `course/.glossary_curation.json` NAO existe -> compila (1 chamada por
   unidade COM material) e grava no MESMO formato do loader (`{"<Termo do plano>": {"synonyms": [...]}}`) com
   `"_provenance": "llm"` e `_nota`. Existe -> cache; recompila SO com flag explicita (`--recompile-vocab`,
   decisao D). Sidecars manuais de SO/IA/ES2/TCC NAO sao tocados.
2. Filtros obrigatorios no compile: termo == label fora · termo em > 1 topico fora (exclusividade) ·
   **termo cujo normalizado == id/titulo de arquivo do curso fora** (decisao C) · genericos do curso fora.
3. Teste TDD do compile com client fake (schema, filtros, cache, flag). Sem chamada real no pytest.
4. Gate: curado 93/93 intacto (manuais seguem) · motor puro nos 4 com gold (o compilado entra nas copias
   nu? NAO: motor puro mede SEM sidecar por definicao — registrar a regua "puro + vocab compilado" como
   3a linha, e essa e a que o produto entrega) · sentinela nos 8: novas tags SO em CG/FR/LR/MF · determinismo
   (cache faz o reprocess ser 0 campos).
5. Rodar o compile de verdade em CG, FR, LR, MF (4 cursos, ~3 chamadas cada). Olhar os sidecars (o user ja
   aprovou o do FR; os outros 3 ele ve na secao de revisao — ou aqui, se quiser).

### Run real do FR (decisao G: FR primeiro)
Protocolo do handoff 01d: `build_course` do zero em copia limpa, zero curadoria, summaries ON, vocabulario
compilado, voter ON com cap e CONTAGEM, watchdogs. Entregar ao user a lista `revisar` (camadas duvida + llm)
com bloco/unidade/subunidade de cada item. Cada correcao = override + linha de gold-por-fenomeno (decisao A).
Metricas: revisar/100, votos/100, correcoes/100.

### Depois: Fase 2 (cronograma manda) -> Fase 3 (bloco estrutural) -> Fase 4 (LLM residual) -> run CG.
E/F/H/I se decidem com o dado dessas fases (ver plano).

## Cortes de refactor (intercalar; cada um com sentinela 0 campos)
1. `scripts/` 77 -> ~25 (eval/ watchdogs/ ops/; arquivar one-offs) — pode ser a proxima sessao curta.
2. Limiares soltos -> `T`. 3. Um tokenizador (strangler), DEPOIS da Fase 1b. 4. `timeline/index.py` em 3.
Candidato a remocao: `concept_resolver.py` (decisao H, medir consumidores de `computed_block_id`).

## Ferramentas (scratchpad desta sessao — promover as duas primeiras na Fase 0)
`motor_puro.py` · `censo_motor_llm.py` · `disseca_llm.py` (+csv) · `compila_vocab_v2.py` (base do 1b) ·
`coheading.py`/`coheading_b.py` (refutados; guardar como prova) · `sem_llm.py` · `projeta_regua.py` ·
`placar_devops.py` · `anatomia-do-bloco.html`.
