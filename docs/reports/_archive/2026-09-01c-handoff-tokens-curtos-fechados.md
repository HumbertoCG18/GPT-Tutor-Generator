# Handoff 2026-09-01c — TOKENS CURTOS FECHADOS (fila 1-4 vencida); proxima sessao escolhe da fila geral

**Sessao noturna 01/09. As 4 entradas da fila do handoff anterior
(`2026-09-01-handoff-tokens-curtos.md`) foram vencidas. Regua de subunidade no RECORDE:
93/93 com-extras · 91/93 primario.** Leia antes: `docs/reports/pendencias.md`, secao
"TOKENS CURTOS — CAMPANHA FECHADA (2026-09-01c)".

## Leis da campanha (inalteradas)
Dado real antes de codigo · raiz nunca remendo · tudo pelo motor, LLM = fallback · sem regra por
categoria · sem regra por CURSO · pinar menos · **gate entre passos**: `eval_eixos.py` +
`eval_subunit_gt.py` (PRIMARIO conta) + `pytest -q` + `sentinela_manifests.py` vs git HEAD +
determinismo (2 reprocess = 0 campos novos) + `ablacao_rapida.py` nu e `--curado` · nada avanca
com regua pior em QUALQUER eixo · commits com trailers · respostas em portugues com [Humberto].

## O que esta sessao fez (nao refazer)

### 1. devops (ES2) — FECHADO com dedupe de frases (`e6f847f`)
- **Hipotese posicional do handoff anterior REFUTADA pela familia** (medicao antes de codigo):
  aula-08 (TCC) tem o instrumento (maquinas de turing) no TITULO e 1o heading, gold conjectura
  4.6 vs 35.0 (gap 7.5x); roteiro5-conteiners tem "container" no titulo. Posicao de heading
  REFORCARIA esses dois erros e so ajudaria o devops. Nao ha sinal posicional que conserta a
  familia — os 2 restantes sao teto SEMANTICO (tese vs instrumento), extras legitimos no gold.
- **Raiz real do devops: double-dip label==slug.** "Integracao continua (CI)" normaliza IGUAL a
  slug-phrase "integracao continua ci" -> a MESMA frase contava label+slug (1.65x por campo) vs
  0.82x de alias do "Conceito de DevOps" (label com meta-palavra nunca casa como frase). CI
  colhia 5.4 pontos falsos. Dedupe: frases por forma normalizada, maior fator vence
  (label 1.0 > alias 0.82 > slug 0.65). `src/builder/timeline/index.py`
  `_score_entry_against_taxonomy_topic`.
- **Limiar de ambiguidade reancorado 0.15 -> 0.12** (`T.SUBUNIT_AMBIG_MARGIN`, thresholds.py; era
  hardcoded em `auto_map_entry_subtopic`). O dedupe deflaciona a ESCALA (margens eram calibradas
  sobre a inflacao): devops rel 0.136 e web rel 0.133 cairiam em ambiguo. PROJETADO nos 93 antes
  de codar (`scratchpad/projeta_regua.py`): flip unico = devops ERRO->OK, zero colateral nas 82
  linhas fieis (11 rotas code_curation sao infieis no sim; o reprocess real confirmou).
- ATENCAO: web (cliente-servidor) passa com folga de 0.013 sobre o limiar — se um dia regredir,
  o caso e um deck-survey multi-tema honesto (camadas/servicos/serverless), gold cliente-servidor.

### 2. 02-modelos-de-referencia (FR) — FECHADO com o fix do token-artefato (`98e3536`)
- Hipotese (a) do handoff (label-aspirador / "internet" generico) MORTA com df medido:
  "internet" esta em 1/6 unidades do FR (0.17 < 0.4) — distintivo legitimo da u01; o df por
  unidades esta correto, nao mexer.
- Hipotese (b) (multi-tema) MORTA pelos headings: o deck e 100% modelos de referencia
  (osi 10x, tcp ip 6x, modelos 4x). Validacao estrutural, sem mini-gold.
- **Raiz real: slugify funde "TCP/IP" -> "tcpip"**, token que NUNCA existe no texto normalizado
  ("tcp ip") -> bonus de cobertura-total nunca disparava (4/5 cobertos, o 5o era o artefato) e o
  label-aspirador ganhava com 2/2 migalhas (conceitos+internet). Fix: fusao de 2-3 tokens
  adjacentes de label/alias que nao e token proprio fica fora de topic_tokens.
- Escopo MEDIDO nos 8 cursos: 2 topicos, ambos FR (tcpip, clienteservidor) — zero contato com a
  regua de 93. Sentinela do fix: 4 campos, SO FR, o unico slug flipado = o alvo
  (modelos-osi-e-tcpip conf 0.193 nao-ambiguo). Teste TDD:
  `test_auto_map_entry_subtopic_artefato_de_slugify_nao_bloqueia_cobertura_total` (o cenario
  sintetico precisa de 3+ unidades E course_name para o df nao engolir o vocabulario — pegadinha
  documentada no teste).

### 3-4. Fechados por lei (sem erro medido, sem alvo)
- 1 char (TCC `p`, CG `b`/`z`): regua 93/93, vizinhos longos carregam. Bigrama-frase segue sendo
  o desenho SE um erro real surgir.
- Rotas so-longos (unidade/cobertura/catalogo/disamb): 191/191 e 56/57 — mapa completo segue no
  handoff anterior, gatilho de expansao = erro medido.

### Bonus sem gold (eyeball, todos neutro-ou-melhor)
FR `06-protocolo-dhcp` desambiguou -> dns-dhcp-snmp-nat (correto) · TCC `aula-17`
cook-levin -> reducao-polinomial (tese do deck; cook-levin era secao tardia — mesma forma do
devops) · MF `introducao` -> exemplos-de-aplicacoes (Ariane/Therac/FDIV) · MF
`exercicios-conjuntos`: ruido 0.1 antes e depois (pre-requisito; tag arbitraria nas duas versoes).
Golden TCC casos-chave atualizado DE PROPOSITO: band aula-01 baixa->media (mesmo bloco, mais
margem, veio do dedupe). Pegadinha de gate: rodar `pytest` DEPOIS do reprocess — a caracterizacao
le os manifests vivos.

## Estado verificado (tudo local, NADA pushed ainda — user decide push)
- Regua: bloco 199/200 conf-err 0 · unidade 191/191 · cobertura 56/57 F1 0,982 · subunidade
  **93/93 com-extras / 91/93 primario** · suite **2177** · determinismo 8/8 · ablacao nu identica
  ao baseline 31/08 · curado 6/6 PERFEITO.
- Commits: gerador `e6f847f` (dedupe+limiar) + `98e3536` (artefato+teste+golden+tracker vem em
  cima) · tutores: MF `1a13b8e` SO `c230b2f` IA `9456acc` ES2 `f499c67` TCC `be62f36` CG `fb25324`
  LR `8201c80` FR `6c26414`.
- Restam 2 erros primario (extras legitimos): ES2 roteiro5-conteiners e TCC aula-08 — teto
  semantico "tese vs instrumento", instrumento no titulo. Sem desenho token-based que os alcance;
  candidato futuro = LLM fallback ou gold-por-fenomeno, decisao do user.

## FILA DA PROXIMA SESSAO (geral, decisoes do user, sem ordem imposta)
- Lab SO com o SARC da 310 (esteira pronta, ~30 min).
- Merge em main (checkpoint; conflito so README; tira o token M365 do tracking).
- P2b-LLM (extracao de questoes) · gap video do T2 · triagem dos 10 suspeitos do
  detecta_headings · gold de bloco do CG (opcional) · campanha web (destino da branch).

## Ferramentas (inalteradas + 1 nova no scratchpad)
As de sempre (`eval_eixos`, `eval_subunit_gt`, `sentinela_manifests`, `ablacao_rapida`,
`explain_entry`, `reprocess_assignments`, watchdogs). No scratchpad da sessao ficaram
`placar_devops.py` (placar por candidato com detalhe de frases/tokens) e `projeta_regua.py`
(projecao da regua de 93 sob scorer alternativo SEM tocar producao — promover a scripts/ se a
proxima sessao mexer de novo no scorer).
