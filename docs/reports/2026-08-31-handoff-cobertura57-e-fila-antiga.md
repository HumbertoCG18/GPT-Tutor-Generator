# Handoff 2026-08-31 — Cobertura 57/57 (eth2/aws) e a fila antiga

**Para a proxima sessao. Comecar por P1; P2 na ordem a-f. Nada aqui esta bloqueado.**
Leia antes: `docs/reports/pendencias.md` — secao "PENDENTE DE VERDADE (2026-08-31)" e o cabecalho ESTADO.

## Leis da campanha (inalteradas)
Dado real antes de codigo · raiz nunca remendo · tudo pelo motor, LLM = fallback · sem regra por categoria ·
sem regra por CURSO (4b) · pinar menos · **gate entre passos**: `eval_eixos.py` (4 eixos) + `pytest -q` +
sentinela campo a campo vs `git show HEAD:manifest.json` + determinismo (2 reprocess = 0 campos em 6/6) +
`ablacao_rapida.py` nu e `--curado` · nada avanca com regua pior em QUALQUER eixo · restaurou tutor por git ->
reprocessa (derivados fora do git) · commits com trailers Co-Authored-By + Claude-Session · respostas em
portugues comecando com [Humberto].

## Estado que esta sessao deixou (2026-08-31, tudo verificado)
- Regua curada: bloco 199/200 conf-err 0 · unidade 191/191 · **cobertura 55/57 F1 0,965** · subunidade 87/93 ·
  pinos 5 · card manual 1 (TCC "Semana 12") · suite **2132**.
- Motor nu: bloco 194/200 display conf-err 2 · unidade 134/191 · cobertura 54/57 · pinos 0.
- Gerador `f45fd31`; tutores MF `0157a2c` TCC `f90aa98` IA `60f7271` SO `b4c336c` ES2 `3dbd45d` CG `62c80a0`,
  todos com remote privado e 0/0.
- Serie F da dissecacao TODA executada (F1-F14, menos F6 adiado p/ pos-build e F8 que virou leitura de formula
  ainda nao implementada); decisoes antigas resolvidas (pthread=04 final; prova-1/azure ficam; remotes ok).
- Refutados NESTA sessao (nao retentar sem dado novo): alias Cook-Levin no TCC (bloco 25->24 conf-err 1, 5
  subunits flipam); stem6 global em `_matches_normalized_phrase` (subunidade 87->83, bloco 199->198); stem6 no
  `_score_timeline_unit_phrase` (IA oracle regride, forks nao fecham).

## P1 — Cobertura 55 -> 57: texto para `eth2` e `aws-encryption-sdk` (MF)
Os 2 ultimos erros de cobertura. Fatos:
- Entries `eth2` e `aws-encryption-sdk` do MF: categoria bibliografia, texto **0 chars** (evidencia no gold:
  "(SEM TEXTO — PRECISA MOODLE)"), sao URLs de repos do GitHub postadas no Moodle.
- Gold: `docs/reports/material_gt_MF.csv` — ambos `gold_units=unidade-02-verificacao-de-programas`,
  **provenance=proposto-claude (2026-08-18)**, NAO e ruling do user. eth2 = "Eth2.0 spec in Dafny" (Dafny =
  verificacao ✓ plausivel); aws-encryption-sdk = SDK "formally verified" (u02 plausivel, mas o titulo nao diz).
  **Primeiro passo: pedir ao user que confirme os 2 golds** (custa 1 pergunta; engenharia depois).
- Caminho tecnico (decidir na sessao, com dado): o pipeline ja tem `get_plain`/snapshot (`moodle_pull.py`,
  `site_snapshot.py`) e a classificacao de links; falta o TEXTO dessas paginas chegar ao scorer de
  unidade/cobertura da camada de REFERENCIA. Olhar `reference_navigation.py` (le `coverage_units`) e onde a
  cobertura decide para bibliografia (fallback = `computed_unit_slug`; hoje o scorer roda com texto vazio).
  GitHub repo -> README publico via raw.githubusercontent (sem token) ou title da pagina.
- **Medicao em ~15 s, sem reprocessar**: `python scripts/harness_cobertura.py` (55/57 hoje; erros listados no
  fim). Modo detalhe: `base --detalhe`.
- Gate completo so quando mexer em producao (reprocess 6 + sentinela + ablacao, ~10 min ao todo).

## P2 — Fila antiga, na ordem
a) **Unidade NUA 134/191** (o maior item de motor restante). Raiz conhecida e ja documentada: o DP monotonico
   (`unit_matcher.assign_units_positional`) assume ordem do plano == ordem do calendario; IA ensina ML (u05) em
   marco (inversao local), e a versao curada so fecha 191/191 gracas a pinos de unidade em IA/ES2. Item: DP
   robusto a inversao local (ex.: permitir 1 troca de janela com custo, ou ancoras fortes quebrando a
   monotonicidade em segmentos). Medir com `ablacao_rapida` antes/depois (unidade nua) e manter curado
   191/191 + pinos podendo cair. F5 (marcos "parte N") ja quebra a segmentacao por entregas — nao colidir.
b) **FASE 4** (exercicios/listas/provas antigas, pedido do user em 18/08): destravada — cobertura estavel.
   Reler o pedido original no tracker (secao FILA ACORDADA 24/08, item "FASE 4 original").
c) **Housekeeping**: copiar do scratch desta sessao p/ `scripts/`: `dados_artefato.py` e `patch_razao.py`
   (regeneram o artefato "Razao dos Blocos", claude.ai/code/artifact/d2ef4eaa-3483-412a-9dc8-110b1f9ccacb;
   template `razao_template.html` no mesmo scratch — copiar junto). Scratch da sessao 31/08:
   `C:/Users/Humberto/AppData/Local/Temp/claude/C--Users-Humberto-Documents-GitHub-GPT-Tutor-Generator/822c8c20-18ed-41cf-ab0b-755fe994d517/scratchpad`.
d) **A1 grande** (higiene): P4/desempate do motor de bloco no mesmo `text/normalize.stem6`. Sem numero
   prometido; so com gate completo.
e) **MF 30/66 LLM**: aceito; nao mexer sem medida nova.
f) **Subunidade 6 residuais (IA)**: aguarda decisao do user (glossario por LLM?).

## P3 — Builds pagos (nao fazem parte deste handoff; quando o user autorizar)
Stashes duraveis prontos (copiados do scratch em 31/08):
- `Desktop/Moodle/laboratorio-de-redes-de-computadores/` (stash/ 6 arquivos + .moodle_nomes.json; raw/; links.json)
- `Desktop/Moodle/fundamentos-de-redes-de-computadores/` (stash/ 20 arquivos)
- `Desktop/Moodle/laboratorio-de-sistemas-operacionais/` (stash/ 19 arquivos) — **so buildar com o SARC da
  turma 310** (F14; o link do Moodle e da 330; remap refutado 30/08).
Planos: `Desktop/claude-tutor/*.plano.md` (+ `sarc/*.bin` = exports HTML). Perfis: Lab Redes ja em
subjects.json (95473); FR/Lab SO criar via `build_course.py --args-json` com `--syllabus-url` (F12 valida a
turma: export x shortname) e `--teaching-plan-pdf`. Token Moodle renova sozinho (`scripts/moodle_token.py`,
credenciais em `moddle/.env`, local/gitignored). Ordem sugerida: Lab Redes -> FR -> Lab SO.

## Ferramentas de medicao (todas rapidas)
- `python scripts/eval_eixos.py` — regua oficial 4 eixos (+ `--course SIGLA`).
- `python scripts/harness_cobertura.py [base|final] [--detalhe]` — eixo de cobertura offline, ~15 s.
- `python scripts/eval_entry_unit.py` — scorer de unidade bruto (diagnostico, NAO e a regua).
- `python scripts/ablacao_rapida.py [--curado] --repos MF,SO,IA,ES2,TCC,CG` — nu/curado em copias.
- subunidade: comparar `computed_subunit_slug` do manifest com `docs/reports/subunit_gt_{SO,IA,ES2,TCC}.csv`
  (87/93 hoje; snippet no historico da sessao 31/08).
- sentinela: manifest atual vs `git show HEAD:manifest.json` nos 6 (campos: temporal_block_id/method,
  computed_block_id/method, computed_unit_slug, computed_subunit_slug, confidencias, auto_tags, coverage_units).
