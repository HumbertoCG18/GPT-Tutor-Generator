# Handoff 2026-09-01 — Investigacao profunda dos TOKENS CURTOS (e o resto da fila)

**Para a proxima sessao. Foco decidido pelo user: atacar os casos de tokens curtos a fundo.**
Leia antes: `docs/reports/pendencias.md` — cabecalho "PENDENTE DE VERDADE (2026-09-01a/b)" e o
ESTADO (as-of 2026-09-01b). Handoff anterior: `2026-08-31b-handoff-gate-meta-e-fila-nova.md`.

## Leis da campanha (inalteradas)
Dado real antes de codigo · raiz nunca remendo · tudo pelo motor, LLM = fallback · sem regra por
categoria · sem regra por CURSO · pinar menos · **gate entre passos**: `eval_eixos.py` (bloco/
unidade/cobertura) + `eval_subunit_gt.py` (subunidade; PRIMARIO e o que conta) + `pytest -q` +
`sentinela_manifests.py` vs git HEAD + determinismo (2 reprocess = 0 campos) + `ablacao_rapida.py`
nu e `--curado` · nada avanca com regua pior em QUALQUER eixo · restaurou tutor por git ->
reprocessa · commits com trailers Co-Authored-By + Claude-Session · respostas em portugues
comecando com [Humberto].

## Estado que esta sessao deixou (2026-09-01, tudo verificado e pushed)
- Regua: bloco **199/200 conf-err 0** · unidade **191/191** · cobertura **56/57 F1 0,982** ·
  subunidade **90/93 primario** (erros: ES2 `devops` + `roteiro5` + TCC `aula-08`) / 92/93
  com-extras · pinos 5 · suite **2176** · determinismo 0 nos 8 · **gate curado 6/6 PERFEITO**.
- **8 cursos**: os 6 da bancada + **Lab Redes (6 entries) e Fund. Redes (20 entries) BUILDADOS**
  (P3, 01/09; zero curadoria; remotes privados; Lab SO bloqueado no SARC da 310 — user pega amanha).
- Checkpoint: new-features = `399706e`; main INTOCADA por decisao do user.
- Nesta sessao (nao refazer): fila a-g do handoff anterior · auditoria de dividas (14 vencidos) ·
  campanha pre-P3 (cores/bgcolor + D1 completo + D5 verificado) · levas 1+2 de higiene
  (SUBUNIT_TAG 0.10; B-1 ferramenta so por defaults+override; B-4/5/6/7) · builds P3 · tar.gz no
  import · **short-vocab por curso + headings do scorer 8->24** (a 1a regra nascida do holdout).

## A QUESTAO DOS TOKENS CURTOS — o que ja foi feito (nao refazer)
Fenomeno (medido antes de codar): tokenizadores cortam len<4; o plano de redes SO usa siglas
("Protocolo TCP/UDP/ARP/ICMP", "Modelos OSI e TCP/IP" — nunca por extenso, verificado) e o token
distintivo era invisivel. Escopo nos 8 cursos: FR 8/33 labels, LR 4/11, CG 16/59 (2d/3d/ray/bsp),
TCC (p/np), ES2 (ci/cd), MF (pre/pos), IA (ia), SO 0.
JA IMPLEMENTADO (gerador `2c47356`):
- `short_vocab_from_topic_labels` (text/stopwords, fonte unica): tokens 2-3 chars consagrados por
  LABEL de topico do curso; preposicoes PT nunca (`SHORT_FUNCTION_WORDS_PT`). Carimbado nos topicos
  por `_iter_content_taxonomy_topics` (campo `short_vocab`, mesmo mecanismo do A2).
- Consumo SO no scorer de SUBUNIDADE (`_score_entry_against_taxonomy_topic`): token curto conta em
  topic_tokens sempre; em signal_tokens SO vindo de campo FORTE (headings/titulo/manual_tags/
  auto_tags/raw=nome de arquivo). Corpo (`markdown_text`) e **lead** sao fracos DE PROPOSITO
  (em doc curto o lead engole o corpo — o teste da mencao tardia pegou isso).
- `limit=24` nos headings do scorer de entry (`entry_signals.py:141`; era 8 — slide-deck de 47
  paginas parava no 8o e "TCP/IP" no 17o era invisivel). `strong_headings` da taxonomia seguem 8.
- Gate: reguas identicas; ES2 `web` (familia B, "teto" com 2 desenhos refutados) CONSERTOU para
  cliente-servidor; `devops` flipou para o tema tardio (ver fila). FR: exercicios-dns 0.85.

## FILA DA PROXIMA SESSAO (foco: tokens curtos, na ordem)
1. **`devops` (ES2) — o unico erro NOVO da sessao** (gold `conceito-de-devops`, pred
   `integracao-continua-ci`). Material multi-secao (DEVOPS + GERENCIA DE CONFIG + CI num arquivo):
   com 24 headings, os headings TARDIOS de CI venceram o tema-titulo. CANDIDATO: posicao do heading
   como sinal (1o heading = tese do material; peso decrescente ou primeiro-heading como campo
   proprio). ARMADILHAS mapeadas: (i) o `web` consertou EXATAMENTE porque os headings tardios
   passaram a contar — qualquer desenho de posicao tem que re-medir web+devops+aula-08 JUNTOS
   (aula-08 TCC e a familia "tese vs instrumento", pode se beneficiar do mesmo sinal); (ii) piso/
   peso global e a classe 3x refutada — desenho fino e MEDIDO na regua de 93.
2. **`02-modelos-de-referencia` (FR)** — segue errado (conceitos, conf 0.92 -> 0.12 = quase-empate
   honesto). Duas hipoteses a investigar: (a) label-aspirador "Conceitos de redes de computadores e
   Internet" — "internet" nao entrou nos genericos do curso (A2/df: por que? df so sobre unidades?
   medir); (b) material e multi-tema de verdade (Modelos + Equipamentos de Redes) — pode ser caso
   de gold-por-fenomeno (o user rotula ~8 entries de redes) ou de subunit vazia legitima. SEM-GOLD:
   validacao estrutural ou mini-gold ANTES de regra.
3. **Tokens de 1 char** (re-escopo 01/09: TCC `p` de "Classe P"; CG `b`/`z` de B-Spline/Z-Buffer).
   len>=2 e limite DELIBERADO (1 char solto = ruido). CG ja e carregada pelos vizinhos longos
   ("buffer", "spline" — `elemoculto` flipou para algoritmo-z-buffer 01/09). Investigar SE existe
   erro real causado por eles; se existir, o desenho e BIGRAMA como frase ("classe p", "z buffer"),
   nunca liberar 1 char como token.
4. **Rotas ainda so-longos (mapa completo, expandir APENAS com erro medido):**
   - unidade: `score_entry_against_unit` (file_map.py:280-286, len>=4) + topic_tokens do unit_index
     (file_map.py:111-151);
   - cobertura: `_tokens_distintivos` (coverage_rules.py, len>=3 — `np`/`ip` com 2 ficam fora; de
     olho quando material de PROVA dos cursos de redes chegar: escopo R6/R2 pode precisar);
   - catalogo de tags: `_topic_support_tokens` (content_taxonomy.py:208, len>=4 -> stem5);
   - bloco/disamb: `_toks` do disambiguator.
   Hoje: unidade 191/191 e cobertura 56/57 — zero dano mensuravel; mexer sem alvo = tuning refutado.
5. Resto da fila geral (sem ordem, decisoes do user): Lab SO com o SARC da 310 (build na esteira
   pronta, ~30 min) · merge em main (checkpoint; conflito so README; tira o token M365 do tracking) ·
   P2b-LLM (extracao de questoes) · gap video do T2 · triagem dos 10 suspeitos antigos do
   detecta_headings · gold de bloco do CG (opcional) · campanha web (destino declarado da branch).

## Ferramentas de medicao (todas rapidas; 2 novas promovidas nesta sessao)
- `python scripts/eval_eixos.py` — regua oficial (pula curso sem gold: LR/FR listados fora).
- `python scripts/eval_subunit_gt.py` — **NOVO**: regua de subunidade vs subunit_gt_*.csv
  (com-extras; para primario-apenas, trocar o alvo por {gold} apenas — convencao: PRIMARIO conta).
- `python scripts/sentinela_manifests.py` — **NOVO**: sentinela campo a campo vs git HEAD nos 8.
- `python scripts/ablacao_rapida.py [--curado] --repos MF,SO,IA,ES2,TCC,CG` — nu/curado.
- `python scripts/detecta_duplicatas.py` / `detecta_headings.py` / `eval_subunit_health.py` —
  watchdogs sem gold (cobrem LR/FR por default; health tem falso-positivo conhecido de slug de
  topico duplicado entre unidades — SO `conceitos-basicos` em u02 E u04).
- `python scripts/explain_entry.py <repo> <entry_id>` — cadeia completa de um arquivo.
- placar por candidato de subunidade: harness inline com `_score_entry_against_taxonomy_topic` +
  `collect_entry_unit_signals` (exemplo no historico da sessao 01/09, caso 02-modelos).
- `python scripts/reprocess_assignments.py <repos...>` — reprocess headless deterministico.
