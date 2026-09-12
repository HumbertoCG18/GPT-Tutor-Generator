# Handoff — sessão de atribuição (17/06) + contexto institucional

date: 2026-06-17
branch: `feat/reconciliar-unit-bloco`
estado: **working tree limpo**; suíte **1368 verde**; golden de bloco (`scripts/eval_assignments.py`) **5/5, confiante-errado 0**.

## Como retomar (nova sessão)
1. Ler `.mex/ROUTER.md` + `.mex/AGENTS.md` (bootstrap + não-negociáveis).
2. **NOVO — ler `.mex/context/institutional.md`** (faculdade PUCRS + plataformas-fonte: Plano de Ensino, OpenSARC/cronograma, Moodle, M365). Evita re-derivar errado o domínio.
3. Ler este handoff + `docs/Overview-Sistema.html` (aba 6 **Pendências** / aba 8 **Concluído** — doc vivo) + handoff anterior `docs/reports/2026-06-16-handoff-atribuicao.md` + spec `docs/superpowers/specs/2026-06-16-correcoes-atribuicao-wave-1-2-design.md`.
4. Prefixar TODA resposta com `[Humberto]` (CLAUDE.md). Caveman mode pode estar ativo. Commits terminam com `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
5. Regra do usuário: **correções gerais na raiz, nunca fix específico por arquivo/cadeira**. Mudança que altera atribuição = **eval-gate** (golden + suíte; censo real é user-side).

## Feito nesta sessão (commits)
- **D2 `administrative_only`** (`085a725`, docs `8f40ca9`): a chave nunca é gravada em prod (runtime não escreve nem remove admin; `_serialize` já remove). Trocado o key-lookup morto pelo predicado real `timeline_block_is_administrative_only` (promovido a público, lê `rows`) nos 4 sites. content_taxonomy/file_map liam o índice **runtime** → blocos admin vazavam como candidatos. Handoff anterior errou ao agrupar file_map como "morto" — é leak real (mesmo timeline_context runtime).
- **P1.5 `auto_suggested_unit`** (`8392450`, docs `034a56d`): investigado — o ramo topic-derive é **VIVO** (não morto). Premissa da spec falsa: posicional só grava `auto_unit_slug` p/ class_candidates com slug; blocos não-aula/herdados/posicional-vazio serializam sem `auto_unit_slug` mas com `topic_candidates`. **Mantido** (conflict-detection/health, golden-safe); só corrigido o comentário stale.
- **P1.3 piso 0.72** (`6f24fc7`, docs `684fb04`): **removido**. Era polegar-na-balança invisível: a band usa a conf CAPADA (scorer_only=0.70); o piso só inflava o `block_confidence` RAW passado a `reconcile_unit_with_block` (bloco define unidade se `block_confidence >= unit_confidence`). Como `unit_confidence` também é `relative_margin_confidence` (idea 1), a comparação é simétrica por design — o piso quebrava só na janela `unit_conf ∈ (0.70, 0.72]`. Rejeitada a opção "reconciliar com a conf capada" (method-cap = teto de display, não evidência → enfraqueceria bloco scorer forte).
- **Contexto institucional** (`6ea8fe0`/`44cb091`/`8c5be82`): novo `.mex/context/institutional.md` (linkado no ROUTER). Cronograma = exportação OpenSARC `Export.aspx?id=<GUID turma>&ano&sem` (parser `_parse_aspnet_schedule`/`dgAulas`, Atividade + cor). Consulta.aspx (read-only do aluno) é página separada, não-fonte. Plano de Ensino SEMPRE presente + **nunca cadeira de 1 unidade** (`m>=2` garantido). Avaliações PUCRS: P1/P2/P3/PS/G2. Card Moodle heterogêneo (semana / título-unidade / Exercícios/Listas/Revisões/TDE).
- **Curadoria unificada** confirmada FEITA (`28cdf8a`): `CurationWorkspace` wired em `app.py:383` (abas Revisão Manual + Imagens). Overview seção 8 flipada de "em andamento" → FEITO + card no Concluído; datas/rodapé do relatório atualizados (17/06).
- **Gap "Evento Academico"** (`939e483`, docs `0e18d01`): `evento → event` no `ATIVIDADE_KIND_MAP` (kind ignorado, igual ao evento por cor darkred). Antes caía em `class` quando a linha SARC não tinha cor → poluía atribuição. **+ UI:** `HTMLImportDialog` aceita só a **URL do SARC** (paste de HTML removido; backend de parse mantido como fallback não-exposto). Decisão do usuário: "manter scraper + só link" (link e paste sempre usaram o MESMO scraper).

## P3.4 "trabalho"→DELIVERABLE — FEITO (unit-aware, 17/06 continuação)
- Token nu `"trabalho"`/`"parte trabalho"` removido de `KIND_KEYWORDS[DELIVERABLE]` (classifier.py) e promovido a **regra gated 3c** em `classify_block`: vira DELIVERABLE só SEM evidência de unidade (`_has_unit_evidence` = `unit_slug`/`auto_unit_slug`/`topic_candidates`). Aula "Trabalho sobre X" com unidade mantém a unidade (CLASS). Bundle G2/PS no `_STRONG_EXAM_RE` (no-op hoje — PS/G2 já vem por `source_kind`; rede de segurança sem source_kind).
- **DESCOBERTA (premissa do handoff furada):** os ÚNICOS blocos com "trabalho" nu nos 5 cursos são apresentações de TP/T (sem unidade, `topic_candidates=[]`) — DELIVERABLE estava CORRETO p/ eles. O drop cego os jogava em CLASS `needs_unit` (2 health-gates RED: IA, SO). A FP que o handoff temia (aula "Trabalho sobre X" com unidade) NÃO aparece em nenhum curso. Decisão do usuário = **unit-aware** (preserva TP→DELIVERABLE + corrige o bug hipotético).
- **MERGED:** IA bloco-16 e SO bloco-08 fundem apresentação + prova (P1/P2) num bloco; sem o curto-circuito da keyword, agora caem em ASSESSMENT via session-exam (3b, hit `p1`/`p2` da regex pré-existente, NÃO do bundle). Não é regressão (assessment e deliverable são `unit=False`). Reforça a dívida **"separar blocos merged"**.
- Eval-gate: suíte **1370 verde**, golden **5/5 confiante-errado 0**.

## PRÓXIMO PASSO (radar restante)
Ranking dos itens do radar por ganho÷esforço (análise no fim da sessão):

1. ✅ **P3.4 — FEITO (unit-aware, ver bloco acima).** Histórico: `KIND_KEYWORDS[DELIVERABLE]` tinha o **token nu "trabalho"** (+"parte trabalho"). Via `_phrase_match`, 1 palavra ≥4 chars = match token-exato → qualquer bloco cujo `topic_text` contenha "trabalho" vira DELIVERABLE → perde a unidade (`KIND_REQUIREMENTS` unit=False). Com TDE/"trabalho" onipresente na PUCRS, é falso-positivo FREQUENTE. **Fix:** dropar o token nu; manter só as frases de entrega ("entrega trabalho", "entrega do trabalho", "entrega final", "submissao final"). NÃO toca a rota SARC autoritativa (Atividade "Trabalho"→source_kind=deliverable). Eval-gate (golden+suíte; censo real). Baixo esforço, alto ganho. **Bundle opcional:** `_STRONG_EXAM_RE` (classifier.py:136) não cobre `G2`/`PS` como abreviação isolada (PUCRS usa) — add trivial ao regex.

2. **🥈 unit×card divergence (match fuzzy nome-unidade × card Moodle):** teoria do usuário — mesmo conceito escrito diferente → match léxico falha. Ganho alto, mas **projeto próprio** (design fuzzy/alias + eval real + cuidado com falso-match), não quick-win.

3. **🥉 P3.1 auto_tags self-confirmation (`index.py:1755,1801`):** o scorer lê as próprias `auto_tags` (`unit:`/`subunit:`/`bloco:` do run anterior) como sinal → auto-confirma a atribuição prévia no retag. Ganho sutil (viés de estabilidade), esforço médio (filtrar os prefixos gerenciados de `auto_tags_text` nos 2 caminhos: loop ponderado + signal_tokens). Eval = censo subunit.

## ADIADO (grande/arriscado — bloco do P2)
- **Fallback keyword ~600 linhas** (`index.py:2205` else + `_assign_timeline_block_to_unit`/`_vote_unit_from_topic_candidates`/`_score_timeline_row_against_unit`): **Alternativa C** decidida — adiar o delete pro P2. Investigado: NÃO é dead-code degenerado. Só dispara quando `assign_units_positional` retorna [] = `m<2` / `n==0` / afinidade-zero. Com plano sempre presente + `m>=2` sempre → `m<2` inalcançável; resta afinidade-zero (rara, Descrição do SARC traz tópico) e n==0 (no-op). Deletar errado = regressão silenciosa em curso degenerado. Tratar junto da unificação de scorers do P2, com **fold-no-posicional** dos sinais que o frágil tem e o posicional não (nº explícito "Unidade N", frases/âncoras) + guard test (posicional nunca [] no golden).
- **Divergência latente `unit_index` × `content_taxonomy`** (interdependente com o fallback): sem teaching_plan, `unit_index` cai em `_derive_unit_specs_from_repo` mas `content_taxonomy["units"]=[]` → as 2 fontes divergem e o fallback vira load-bearing. NÃO exercitado (plano sempre presente). Ou remover `_derive_unit_specs_from_repo` (se nunca-hit) ou dar a content_taxonomy o mesmo fallback. **Investigar antes de mexer no fallback.**
- **P2.1 família de 6 scorers** (refactor grande); **P2.2 basename→source_section helper** (mecânico, só manutenibilidade); **P2.3 2 rotas card→bloco**; **P2.4 predicados kind index×classifier**.

## Eval-gates / validação
- Suíte: `python -m pytest tests -q` (1368).
- Golden de bloco: `python scripts/eval_assignments.py` → 5/5, confiante-errado 0.
- Censo código→bloco (repo real): `python scripts/eval_code_block_census.py <repo>`.
- Censo subunit/bands: retag/reprocesso + comparar distribuição (manual, user-side).

## Pendência USER-SIDE (não-código)
Reprocessar o MF (`C:/Users/Humberto/Documents/GitHub/Metodos-Formais-Tutor`) com o APP REINICIADO → aplica P0 + idea1 + D1 + idea3 + D2 + piso. NÃO re-extrai nem mexe em id (migração já feita). Rodar o censo depois.

## Gotchas
- Hook `code-review-graph` PostCommit imprime traceback cp1252 no Windows — inofensivo, commit funciona.
- `claude-mem` worker pode estar offline (`memory_search` falha com erro de runtime) — ambiental, ignorar.
- MCPs `token-savior`/`code-review-graph` podem estar desconectados → cair pro Grep/Read.
- Overview: server `python -m http.server 8753 --directory docs` → http://localhost:8753/Overview-Sistema.html (estava no ar no fim da sessão).
- Commits de doc viram 1 por fix (code) + 1 (docs vivos: Overview/ROUTER/institutional). Manter o doc vivo atualizado (AGENTS.md non-negotiable).
