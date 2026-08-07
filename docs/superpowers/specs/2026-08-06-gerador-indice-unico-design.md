# Spec — Gerador de índice único (campanha unificação, subprojeto 1/3)

data: 2026-08-06 · aprovado pelo user nesta sessão (abordagem A aprofundada + varredura por
agentes; condições do user: não quebrar o sistema/progresso, NUNCA ASSUMIR, deleção física de
legado só no cutover). Ordem da campanha aprovada: **Índice → Unidades → SO**.

## 1. Problema

O TCC re-flip (tentativa 3, 2026-08-06) falhou porque `scripts/reprocess_assignments.py` e
`scripts/rebuild_timeline.py rebuild_course` produzem `.timeline_index.json` DIVERGENTES para o
mesmo repo: bloco-13 do TCC sai `kind=class` num e `kind=assessment` no outro (acc 84.2→78.9,
audit hard 0→1). Terceira aparição da família dual-source. Varredura por 3 agentes read-only
(2026-08-06) catalogou **12 riscos da família (R1-R12)** e confirmou a causa-raiz por
reprodução A/B.

## 2. Causa-raiz (CONFIRMADA, reproduzida end-to-end com persist=False)

Cadeia exata (file:line da varredura):

1. Produção passa `manifest_entries` à taxonomia (`pedagogical_regeneration.py:398-402`);
   `rebuild_course` passa `content_taxonomy=None` (`rebuild_timeline.py:67`) → `index.py:1363`
   reconstrói com `manifest_entries=None` → `collect_strong_heading_candidates` devolve `[]`.
2. COM entries: headings reais ("Problema da Correspondência de Post", "Halting Problem - O
   Problema da Parada") viram ALIASES do tópico `prova-da-indecidibilidade-do-problema-da-parada`
   → score do bloco-13 contra o tópico salta **0.122 → 1.037** → cruza gate
   (`index.py:1977-1990`) → `primary_topic_label = "Prova da Indecidibilidade do Problema da
   Parada"` (`index.py:2177`).
3. `classify_block` inclui `primary_topic_label` no texto (`classifier.py:105-107`) e a keyword
   **`prova`** de `KIND_KEYWORDS[ASSESSMENT]` (`classifier.py:93`) casa (`:221`) → bloco vira
   `assessment` → `finalize_block` zera `unit_slug` (`index.py:59-61`).
4. Reprodução A/B: `taxonomy=None → class` · `taxonomy+entries → assessment`. Vizinhos 12/14
   estáveis nos dois. Byte a byte o sintoma do re-flip.

**Verdade do bloco-13**: AULA. SARC linha 15 (SYLLABUS.md:28): `24/04/2026 · "Problema da
Correspondência de Post" · Atividade="Aula"`. "Prova" no rótulo do plano = demonstração
matemática, não exame — MESMA classe semântica da colisão "Verificação de Modelos" do MF
(preview 1.3.1). O caminho de sessão tem guard (`_STRONG_EXAM_RE`, `classifier.py:131`); o
caminho de keyword NÃO tem. `rebuild` só acertava por acidente (taxonomia empobrecida).

Fato estrutural que barateia o fix (agente 1): só existem **2 write-sites** do índice (W1
`pedagogical_regeneration.py:421-424`; W2 `rebuild_timeline.py:99-101`), ambos usando o MESMO
construtor (`_build_file_map_timeline_context_from_course`, `index.py:1349`) e o MESMO
serializador (`persist_enriched_timeline_index`, `core_utils.py:14-37`). Curation e
post-transforms aplicados IGUAL nos dois (`index.py:1472,1478`). **A divergência é 100% de
INSUMO, não de etapa.**

## 3. Objetivo e não-objetivos

**Objetivo**: os dois caminhos geram índice byte-idêntico dado o mesmo repo/perfil; bloco-13
class nos dois; TCC re-flip PASS → 5/5 flag-ON.

**Não-objetivos (ficam FORA, com destino registrado no tracker):**
- R2 (render de FILE_MAP com `persist=True` escreve ledger/manifest/curation no meio do build —
  `navigation.py:525-529` + `teaching_timeline.py:93-95`) e R3 (bootstrap vs regenerate
  escrevem os mesmos .md com insumos diferentes) → itens [CODE] próprios, trilho separado.
- R4 (`compare_resolver` injeta uuids que a produção não injeta), R5 (`eval_assignments`
  contexto sintético; já LEGADO-NÃO-USAR), R6 (2º produtor de `.card_block_map.json` no mesmo
  script) → morrem no cutover (lista já travada).
- R7 (4 loaders de índice com fallbacks distintos), R9 (`scan_existing_block_refs` lê nível
  errado do manifest — guard cego), R11 (dashboard escreve manifest não-atômico), R12 (join de
  data truncado vs não-truncado entre `disambiguator.py:68` e `llm_vote.py:227-229`) →
  minors-batch/subprojeto SO.
- **Deleção física de qualquer legado → cutover** (condição do user). Este subprojeto só
  CONDENA com guard, nunca deleta.

## 4. Design (4 componentes + 1 quick-win de régua)

**C1 — Guard anti-falso-exame no classifier (PRIMEIRO, pré-requisito).** Keyword de
`ASSESSMENT` casada em texto vindo de taxonomia/plano (`primary_topic_label`, `topics`) só
classifica assessment se satisfizer o padrão forte (família `_STRONG_EXAM_RE`: `\bp[1-4]\b`,
`\bpf\b`, `\bg2\b`, `\bps\b`, "prova N", "prova final"...), nunca `prova`/`teste` nus —
"Prova da Indecidibilidade" e "teste de mesa" são conteúdo. Fontes NÃO-plano (Atividade SARC,
source_kind, session labels já guardadas) mantêm comportamento atual intocado. TDD com o
bloco-13 real: RED = taxonomy+entries→assessment hoje; GREEN = class. SEM C1, o C2 flipa o
bloco-13 nos dois caminhos (piora provada pela reprodução A/B).

**C2 — Montador único de insumos.** Helper único que monta a taxonomia COM `manifest_entries`
(o que a produção já faz) e é usado pelos dois write-paths e pelas sondas: `rebuild_timeline`,
`rebuild_diff`, `retag_manifest` deixam de passar `content_taxonomy=None`. Assinatura/portas
exatas decididas no plano lendo o código real (NUNCA ASSUMIR: verificar cada caller e o que
`manifest_entries` deve conter — entries vivas filtradas, `pedagogical_regeneration.py:394`).

**C3 — Serializador fantasma CONDENADO (não deletado).** `_serialize_timeline_index`
(`index.py:813-866`, v4, filtra admin, força kind — ZERO callers de produção; testes validam
ELE enquanto produção grava v3): testes migram para validar `persist_enriched_timeline_index`;
guard test proíbe uso do fantasma fora de testes legados marcados; entrada na lista nomeada de
deleção do cutover. Hardcode `version=3` vs `TIMELINE_INDEX_VERSION=4` (`core_utils.py:35`)
fica DOCUMENTADO e intocado neste subprojeto — mudar version exige varredura de consumidor
(risco fora de escopo).

**C4 — Paridade de proteção no W2.** `UnitsShrinkError` guard (hoje só W1,
`pedagogical_regeneration.py:415-420`) passa a valer no caminho `rebuild_course --write`.

**C5 — Quick-win de régua (R8):** `fase5_prova_tier2._effective_display` ignora
`manual_timeline_block_id` (probe mede o oposto da produção em entry pinada; produção:
`resolve_temporal_block`→fallback manual vence). Fix de ~3 linhas + re-run — pré-condição de
medição honesta do TCC re-flip. Baseline re-capturado ANTES do fix para comparar efeito.

## 5. Protocolo de segurança (condições do user)

1. **Nunca assumir**: toda afirmação de comportamento vem de leitura de código citada ou
   medição; o plano abre com verificação das premissas dos agentes que ainda não foram
   medidas por mim (ex.: contradição já achada — agente 1 inferiu `teaching_plan` TCC vazio a
   partir do `.content_taxonomy.json` residual; FALSO: len=5801 no subjects.json e taxonomia
   construiu com 57 headings no agente 3).
2. **Ordem obrigatória**: C1 (guard, TDD) → C5 (régua honesta) → C2 (unificação) → C3/C4.
   Cada task com régua própria; C2 só entra com C1 verde.
3. **Réguas em cada passo**: suite completa + 7 probes byte-idênticos (exceto mudanças
   INTENCIONAIS medidas e listadas) + `audit_gold_freshness` hard=0 nos 5 + `rebuild_diff`
   W1×W2 = **zero diff nos 5 cursos** (o aceite central do subprojeto).
4. **Nada escreve em repo-tutor sem backup completo** (tracked + gitignored, sha256) — rede
   provada 2× nesta sessão.
5. **FAIL de gate = parar + diagnosticar + rollback; NUNCA re-tuning pós-hoc** (spec §12 do
   motor, regra vigente).
6. Repos-tutor read-only durante C1-C4; única escrita real é o TCC re-flip final, gated.

## 6. Aceite (nesta ordem)

1. C1: teste bloco-13 GREEN (class com taxonomia rica); zero regressão na suite; 7 probes
   byte-idênticos.
2. C5: fase5 re-medida com precedência de pino correta; delta documentado (se houver).
3. C2: `rebuild_diff` W1×W2 zero diff nos 5 cursos; sondas (`retag`/`rebuild_diff`) produzem
   taxonomia idêntica à produção.
4. C3: testes migrados verdes; guard de condenação ativo; fantasma na lista do cutover.
5. C4: guard de encolhimento dispara em W2 (teste sintético).
6. **TCC re-flip**: rito completo (backup → flip → reprocess → gates a-d + funil 0 drift +
   fase2-TCC PASS 84.2%/cw0 + audit hard=0 + votos 16→16) → commit → **5/5 flag-ON**.
7. Tracker atualizado: R2-R12 registrados com evidência e destino; entrada Concluído.

## 7. Riscos nomeados

- Unificar insumos muda taxonomia das sondas → números de sonda podem mexer; tratar como
  MEDIÇÃO (diff pré/pós por curso), não surpresa; qualquer mudança além do esperado = parar.
- C1 muda classificação de blocos em outros cursos se algum bloco dependia de `prova` nu
  vindo do plano — `rebuild_diff` nos 5 cursos ANTES/DEPOIS do C1 mede exatamente isso;
  mudanças viram lista explícita para ruling (esperado: zero fora do TCC bloco-13, MAS NÃO
  ASSUMIDO — medido).
- Gold TCC `aula-14` (true=bloco-13) permanece válido: class é a verdade (SARC Atividade="Aula").
- `version` v3/v4 intocado; qualquer leitor que hoje dependa do formato v3 continua vendo v3.

## 8. Evidência de suporte (resumo dos 3 agentes, 2026-08-06)

Inventário completo R1-R12 com file:line registrado nos outputs dos agentes desta sessão e
condensado aqui: R1 dois serializadores (v3 prod / v4 só-testes, filtro admin, kind forçado,
**ids posicionais deslocam entre formatos** — `.bak` do TCC é v4/23 blocos vs vivo v3/31);
R2 FILE_MAP render → escritas colaterais persist=True; R3 bootstrap×regenerate mesmos .md
insumos diferentes; R4 harness injeta uuid; R5/R6 eval_assignments contexto sintético + 2º
produtor de card map; R7 4 loaders fallbacks distintos; R8 fase5 sem precedência de pino;
R9 guard de refs lê nível errado; R10 taxonomia com/sem entries (a causa-raiz); R11 manifest
não-atômico no dashboard; R12 join de data truncado vs cru dentro do motor.
