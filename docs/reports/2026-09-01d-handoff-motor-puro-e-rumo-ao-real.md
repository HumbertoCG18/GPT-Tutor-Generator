# Handoff 2026-09-01d — MOTOR PURO medido, dissecacao do LLM, e o rumo para a primeira run real (CG + FR)

**Para a proxima sessao. Leia antes:** `docs/reports/pendencias.md` secoes "MOTOR PURO — o numero
honesto (2026-09-01d)" e "TOKENS CURTOS — CAMPANHA FECHADA (2026-09-01c)". Handoff anterior (tokens
curtos, ainda valido): `2026-09-01c-handoff-tokens-curtos-fechados.md`. Artifact visual:
"Anatomia do Bloco" (https://claude.ai/code/artifact/ba1de7bf-a802-49fc-b88b-6be358d4b796) —
secoes 1-6: o que e um bloco, o que entra, cascata arquivo->bloco com contagens, o que desce, por que o
gargalo e ali, dissecacao dos 117 votos.

## Leis da campanha (inalteradas) + 1 licao nova
Dado real antes de codigo · raiz nunca remendo · tudo pelo motor, LLM = fallback · sem regra por
categoria/curso · pinar menos · gate entre passos (eixos + subunit_gt + pytest + sentinela + determinismo +
ablacao nu/curado) · nada avanca com regua pior em QUALQUER eixo · commits com trailers · [Humberto].
**Licao 01/09d:** a rota TEMPORAL (bloco) quer sinal ESTRUTURAL (card, data, ordinal, irmao, titulo);
texto semantico a mais (resumo Gemini) ESPALHA vocabulario por varios blocos e piora 3 eixos. Toda ideia
de "enriquecer o texto" para o bloco nasce refutada ate provar exclusividade por bloco.

## O que esta sessao mediu (nao refazer — esta tudo no tracker)
1. **Motor puro** (sem curadoria E sem voter, `scratchpad/motor_puro.py`): bloco 158/200 (79%), unidade
   154/191 (81%), cobertura 51/57, **subunidade 26/93**. A subunidade vive dos `.glossary_curation.json`
   escritos a mao em SO/IA/ES2/TCC (IA 39 -> 6/39 sem eles). CG/FR/LR/MF nao tem sidecar.
2. **Censo motor x LLM** (`scratchpad/censo_motor_llm.py`): 325 materiais nos 8; bloco 62% motor / 28%
   LLM-na-janela / 8% LLM-funil (agora 26 -> 18 funil); unidade e subunidade 100% motor mas unidade herda
   do bloco. Sem voter: 155/200. Gold por metodo: motor deterministico 126/126, llm 61/62, funil 7/7.
3. **Dissecacao dos 117** (`scratchpad/disseca_llm.py` + `.csv`): 6 causas com contagens e gold; tabela
   dos sinais que o sistema ja tem e nao usa no bloco (artifact secao 6).
4. **CG**: z-buffer OK (`elemoculto` 0,43, `exemplozbuffer` 0,86). Familia curvas/Bezier/modelagem ERRADA
   de unidade: blocos 13 e 15 carregam u06, taxonomia poe em u07; `unit_confidence 0,4` = preenchido por
   posicao. Raiz = `unit_matcher.py` DP monotonico com UMA janela de desvio; CG tem duas inversoes
   (u04<->u03 em 25/08->01/09; u07 dentro de u06 em outubro). ~10 entries (unidade + subunidade com conf
   falsa 0,98). NAO e token.
5. **Regras faceis**: meta-generica FEITA (`f166c4e`, −8 votos, reguas identicas). Resumo Gemini na rota
   temporal REFUTADO e revertido (numeros no tracker). Prova antiga -> prep, serie confiante, ordinal de
   serie, provider de titulo, aliases na assinatura: NAO feitas, com veredito/risco no tracker.

## Estado verificado (local, nao pushed — user decide)
Regua: bloco 199/200 conf-err 0 · unidade 191/191 · cobertura 56/57 F1 0,982 · subunidade 93/93 com-extras
/ 91/93 primario · suite 2178 · determinismo 8/8 · ablacao nu identica (bloco 194/200, unidade 170/191,
cobertura 54/57) · curado 6/6 (conferir o resultado do ultimo run no historico; rodou apos o R1).
Gerador: `e6f847f` dedupe · `98e3536` artefato · `a9687d3` docs · `f166c4e` meta-generica · (+ este
handoff). Tutores: os 8 com reprocess do meta-generica a commitar (so `temporal_block_method` dos planos).
Copias `.ablacao`: ficaram no estado da ultima ablacao (sync na proxima rodada).

## RUMO: primeira run real com CG e Fundamentos de Redes (decisao do user, 01/09 noite)
O user quer usar o tutor de verdade, com CG e FR, dependendo o minimo de API de LLM. O que a medicao diz
que precisa acontecer ANTES, na ordem:
1. **Dicionario por curso sem mao humana.** Sem `.glossary_curation.json`, subunidade e ~28%. Duas rotas,
   ambas a MEDIR no holdout (CG/FR) contra validacao estrutural ou mini-gold do user (~8 entries por curso):
   (a) LLM compila o sidecar UMA vez por curso (1 chamada por unidade, cacheado, revisavel — troca 100+
   votos por materiais por ~9 chamadas por curso, e o artefato fica legivel no repo); (b) deterministico:
   headings dos materiais agrupados pelo bloco ESTRUTURAL (data/card) viram sinonimos candidatos do topico
   do bloco (`topic_candidates[0]`), com filtro de exclusividade (heading que aparece em 1 bloco so). (b) e
   o desenho que respeita a licao 01/09d; (a) e o pragmatico. Recomendo medir (b) primeiro por 1 sessao;
   se nao chegar perto do sidecar manual, (a).
2. **CG: 2 janelas de desvio no DP de unidade** (`unit_matcher.py`, DETOUR_COST/DETOUR_MIN_GAIN iguais,
   K=2). Gate nos 5 + eyeball dos blocos 13/15 do CG (esperado u07). Sem isso a run real do CG nasce com
   ~10 entries erradas em unidade e subunidade.
3. **Reduzir votos onde e regra** (na ordem de evidencia): prova antiga -> prep (+2) · provider de titulo
   (~9 funis; CG "exercicios de geometria computacional" <-> bloco-05) · ordinal de serie (medir premissa).
   Aliases na assinatura do bloco: SO com exclusividade por bloco (mesma familia do resumo refutado).
4. **Protocolo da run real** (sem gold): `build_course` CLI do zero, zero curadoria, `gemini_auto_summarize`
   ON (code summaries: CG 17, FR 4 entries — cache, uma vez), voter ON com cap e CONTAGEM registrada;
   watchdogs (`eval_subunit_health`, `detecta_duplicatas`, `detecta_headings`, `sentinela_manifests`);
   o user revisa `course/FILE_MAP.md` e cada correcao vira linha de gold-por-fenomeno (nao pino). Metrica
   de sucesso = correcoes do user por 100 materiais, e votos de LLM por 100 materiais. Videos do CG: fora.
5. **Custo de API do builder** (censo no tracker): Datalab por pagina e o maior custo real; voter e code
   summaries sao cacheados e baratos. Se o objetivo e "zero API", o alvo e o Datalab (pymupdf4llm/Marker
   local ja existem no pipeline), nao o voter.

## Ferramentas desta sessao (scratchpad; promover se a proxima usar)
`placar_devops.py` (placar por candidato) · `projeta_regua.py` (regua projetada sob scorer alternativo) ·
`censo_motor_llm.py` (motor x LLM por eixo + acerto por metodo) · `sem_llm.py` (copias sem voter) ·
`motor_puro.py` (copias nu + sem voter + subunidade) · `disseca_llm.py` (causa por material decidido por
LLM, csv) · `anatomia-do-bloco.html` (artifact).
